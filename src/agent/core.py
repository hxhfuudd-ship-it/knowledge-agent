"""Agent 核心：ReAct 循环 - 感知、思考、行动、观察"""
import logging
import anthropic
from pathlib import Path
from dotenv import load_dotenv

from ..tools.base import ToolRegistry
from ..tools.sql_tool import SQLTool
from ..tools.calculator_tool import CalculatorTool
from ..tools.file_tool import FileReadTool, FileListTool
from ..tools.python_tool import PythonTool
from ..tools.search_tool import SearchTool
from ..tools.chart_tool import ChartTool
from ..rag.rag_tool import RAGSearchTool, RAGIndexTool
from ..skills.base import SkillRegistry
from ..skills.data_analysis import DataAnalysisSkill
from ..skills.sql_expert import SQLExpertSkill
from ..skills.report_gen import ReportGenSkill
from ..skills.doc_qa import DocQASkill
from ..memory.short_term import ShortTermMemory
from ..memory.long_term import LongTermMemory
from ..memory.episodic import EpisodicMemory
from ..memory.working import WorkingMemory
from .. import config

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent.parent.parent / ".env")

BASE_SYSTEM_PROMPT = """你是一个数据分析助手，可以帮助用户查询和分析数据。

你的能力：
1. 查询 SQLite 数据库（包含部门、员工、产品、客户、订单等数据）
2. 执行数学计算
3. 读取知识库文档（数据字典、业务规则等）
4. 语义检索知识库（通过 RAG 检索数据字典、业务规则、分析方法等）
5. 执行 Python 代码片段（数据处理、格式转换等）
6. 生成数据图表（柱状图、折线图、饼图）
7. 搜索网络信息（当知识库无法回答时）

工作原则：
- 先理解用户意图，必要时先用 rag_search 检索相关知识
- 如果涉及业务指标计算（如 GMV、复购率），先检索业务规则确认计算方法
- 生成准确的 SQL 查询，只用 SELECT
- 对查询结果进行分析和解读，给出有价值的洞察
- 如果不确定表结构，用 rag_search 搜索数据字典
- 需要数据可视化时，用 create_chart 生成图表
- 用中文回复用户
"""


class Agent:
    def __init__(self, model=None, max_iterations=None):
        self.client = anthropic.Anthropic()
        self.model = model or config.get("llm.model", "claude-sonnet-4-20250514")
        self.max_iterations = max_iterations or config.get("agent.max_iterations", 10)
        self.registry = ToolRegistry()
        skill_strategy = config.get("agent.skill_match", "hybrid")
        self.skill_registry = SkillRegistry(match_strategy=skill_strategy)
        self.conversation = []
        self.tool_call_log = []

        max_messages = config.get("memory.short_term_max_messages", 20)
        self.short_term = ShortTermMemory(max_messages=max_messages)
        self.long_term = LongTermMemory()
        self.episodic = EpisodicMemory()
        self.working = WorkingMemory()

        self._register_default_tools()
        self._register_default_skills()

    def _register_default_tools(self):
        for tool_cls in [SQLTool, CalculatorTool, FileReadTool, FileListTool,
                         PythonTool, SearchTool, ChartTool,
                         RAGSearchTool, RAGIndexTool]:
            self.registry.register(tool_cls())

    def _register_default_skills(self):
        for skill_cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
            self.skill_registry.register(skill_cls())

    def _build_system_prompt(self, user_message):
        parts = [BASE_SYSTEM_PROMPT]

        if self.short_term.summary:
            parts.append("\n早期对话摘要：\n%s" % self.short_term.summary)

        memories = self.long_term.recall(user_message, top_k=3)
        if memories:
            mem_text = "\n".join("- %s" % m["content"] for m in memories if m["relevance"] > 0.1)
            if mem_text:
                parts.append("\n相关记忆：\n%s" % mem_text)

        episodic_ctx = self.episodic.get_context_string(n=3)
        if episodic_ctx:
            parts.append("\n%s" % episodic_ctx)

        task_ctx = self.working.get_task_context()
        if task_ctx:
            parts.append("\n当前任务状态：\n%s" % task_ctx)

        matched_skill = self.skill_registry.match(user_message)
        if matched_skill:
            parts.append("\n当前激活 Skill: %s\n%s" % (matched_skill.name, matched_skill.system_prompt))

        return "\n".join(parts)

    def _call_llm(self, messages, system_prompt=None):
        return self.client.messages.create(
            model=self.model,
            max_tokens=config.get("llm.max_tokens", 4096),
            system=system_prompt or BASE_SYSTEM_PROMPT,
            tools=self.registry.to_claude_tools(),
            messages=messages,
        )

    def _execute_tool(self, name, input_data):
        tool = self.registry.get(name)
        if not tool:
            return "未知工具: %s" % name
        try:
            return tool.execute(**input_data)
        except Exception as e:
            logger.error("工具 %s 执行失败: %s", name, e)
            return "工具执行错误: %s" % e

    def chat(self, user_message):
        """处理用户消息，返回 {"response": str, "tool_calls": list, "skill": str|None}"""
        self.conversation.append({"role": "user", "content": user_message})
        self.short_term.add("user", user_message)
        self.tool_call_log = []

        self._trim_conversation()

        system_prompt = self._build_system_prompt(user_message)
        matched_skill = self.skill_registry.match(user_message)

        messages = list(self.conversation)

        try:
            for _ in range(self.max_iterations):
                response = self._call_llm(messages, system_prompt)

                if response.stop_reason == "end_turn":
                    text = self._extract_text(response)
                    self._save_assistant_turn(text)
                    self._record_episode(user_message, text)
                    return self._build_result(text, matched_skill)

                if response.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = self._process_tool_calls(response)
                    messages.append({"role": "user", "content": tool_results})
                    continue

                break

            text = self._extract_text(response)
            self._save_assistant_turn(text)
            return self._build_result(text or "抱歉，处理过程过于复杂，请简化你的问题。", matched_skill)
        except anthropic.APIError as e:
            logger.error("API 调用失败: %s", e)
            error_msg = "API 调用失败，请检查网络和 API Key 配置。"
            self._save_assistant_turn(error_msg)
            return self._build_result(error_msg, matched_skill)

    def _process_tool_calls(self, response):
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = self._execute_tool(block.name, block.input)
                self.tool_call_log.append({
                    "tool": block.name,
                    "input": block.input,
                    "output": result,
                })
                self.working.add_step("调用 %s" % block.name, result[:200])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        return tool_results

    def _save_assistant_turn(self, text):
        self.conversation.append({"role": "assistant", "content": text})
        self.short_term.add("assistant", text)

    def _record_episode(self, user_message, response_text):
        if response_text:
            summary = "用户问: %s → %s" % (user_message[:50], response_text[:80])
            self.episodic.add_episode(
                summary,
                {"tools_used": [tc["tool"] for tc in self.tool_call_log]},
            )

    def _build_result(self, text, matched_skill):
        return {
            "response": text,
            "tool_calls": self.tool_call_log,
            "skill": matched_skill.name if matched_skill else None,
        }

    def save_memory(self, content, category="general"):
        self.long_term.save(content, category=category)

    def get_memory_stats(self):
        return {
            "short_term": len(self.short_term),
            "long_term": self.long_term.count(),
            "episodic": len(self.episodic.episodes),
        }

    def reset(self):
        self.conversation = []
        self.tool_call_log = []
        self.short_term.clear()
        self.working.clear()

    def chat_stream(self, user_message):
        """流式处理用户消息，yield 中间事件和最终结果"""
        self.conversation.append({"role": "user", "content": user_message})
        self.short_term.add("user", user_message)
        self.tool_call_log = []
        self._trim_conversation()

        system_prompt = self._build_system_prompt(user_message)
        matched_skill = self.skill_registry.match(user_message)
        messages = list(self.conversation)

        try:
            for _ in range(self.max_iterations):
                collected_text = ""
                tool_blocks = []

                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=config.get("llm.max_tokens", 4096),
                    system=system_prompt or BASE_SYSTEM_PROMPT,
                    tools=self.registry.to_claude_tools(),
                    messages=messages,
                ) as stream:
                    for event in stream:
                        if hasattr(event, "type"):
                            if event.type == "content_block_delta":
                                if hasattr(event.delta, "text"):
                                    collected_text += event.delta.text
                                    yield {"type": "token", "content": event.delta.text}

                    response = stream.get_final_message()

                if response.stop_reason == "end_turn":
                    text = self._extract_text(response)
                    self._save_assistant_turn(text)
                    self._record_episode(user_message, text)
                    yield {"type": "done", "result": self._build_result(text, matched_skill)}
                    return

                if response.stop_reason == "tool_use":
                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = self._process_tool_calls(response)
                    for tc in self.tool_call_log[-len(tool_results):]:
                        yield {"type": "tool_call", "tool": tc["tool"], "input": tc["input"], "output": tc["output"]}
                    messages.append({"role": "user", "content": tool_results})
                    continue

                break

            text = self._extract_text(response)
            self._save_assistant_turn(text)
            yield {"type": "done", "result": self._build_result(text or "抱歉，处理过程过于复杂，请简化你的问题。", matched_skill)}
        except anthropic.APIError as e:
            logger.error("API 调用失败: %s", e)
            error_msg = "API 调用失败，请检查网络和 API Key 配置。"
            self._save_assistant_turn(error_msg)
            yield {"type": "error", "result": self._build_result(error_msg, matched_skill)}

    def _trim_conversation(self):
        max_turns = config.get("memory.short_term_max_messages", 20)
        if len(self.conversation) > max_turns:
            self.conversation = self.conversation[-max_turns:]

    @staticmethod
    def _extract_text(response):
        parts = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(parts)
