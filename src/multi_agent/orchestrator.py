"""多 Agent 编排器：将复杂任务分解并分配给专门的 Agent"""
import anthropic
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from .. import config

load_dotenv(Path(__file__).parent.parent.parent / ".env")


class SubAgent:
    """子 Agent：专注于特定领域的轻量 Agent"""

    def __init__(self, name: str, role: str, system_prompt: str, tools: list = None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.client = anthropic.Anthropic()
        self.model = config.get("llm.model", "claude-sonnet-4-20250514")

    def run(self, task: str, context: str = "") -> str:
        prompt = task
        if context:
            prompt = f"参考上下文：\n{context}\n\n任务：{task}"

        messages = [{"role": "user", "content": prompt}]
        kwargs = dict(
            model=self.model,
            max_tokens=config.get("llm.max_tokens", 2048),
            system=self.system_prompt,
            messages=messages,
        )
        if self.tools:
            kwargs["tools"] = self.tools

        response = self.client.messages.create(**kwargs)

        return "".join(b.text for b in response.content if hasattr(b, "text"))


class Orchestrator:
    """编排器：分解任务 → 分配子 Agent → 聚合结果"""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = config.get("llm.model", "claude-sonnet-4-20250514")
        self.agents: Dict[str, SubAgent] = {}
        self.execution_log: List[Dict] = []
        self._register_default_agents()

    def _register_default_agents(self):
        self.agents["analyst"] = SubAgent(
            name="analyst",
            role="数据分析师",
            system_prompt="你是数据分析师，擅长解读数据、发现趋势和异常。给出的分析要有数据支撑，结论清晰。",
        )
        self.agents["retriever"] = SubAgent(
            name="retriever",
            role="信息检索员",
            system_prompt="你是信息检索专家，擅长从文档中提取关键信息并整理归纳。回答要准确，标注来源。",
        )
        self.agents["reporter"] = SubAgent(
            name="reporter",
            role="报告撰写员",
            system_prompt="你是报告撰写专家，擅长将数据和分析结果整理成结构清晰、易读的报告。使用 Markdown 格式。",
        )

    def register_agent(self, agent: SubAgent):
        self.agents[agent.name] = agent

    def run(self, task: str) -> Dict[str, Any]:
        """执行复杂任务：分解 → 分配 → 执行 → 聚合"""
        self.execution_log = []

        # 1. 任务分解
        plan = self._plan(task)
        self.execution_log.append({"phase": "planning", "result": plan})

        # 2. 按计划执行子任务
        results = {}
        for step in plan.get("steps", []):
            agent_name = step.get("agent", "analyst")
            sub_task = step.get("task", "")
            depends_on = step.get("depends_on", [])

            # 收集依赖结果作为上下文
            context_parts = [results[dep] for dep in depends_on if dep in results]
            context = "\n---\n".join(context_parts)

            agent = self.agents.get(agent_name)
            if agent:
                result = agent.run(sub_task, context)
                step_id = step.get("id", agent_name)
                results[step_id] = result
                self.execution_log.append({
                    "phase": "execution",
                    "agent": agent_name,
                    "task": sub_task,
                    "result": result[:500],
                })

        # 3. 聚合最终结果
        final = self._aggregate(task, results)
        self.execution_log.append({"phase": "aggregation", "result": final[:500]})

        return {
            "response": final,
            "execution_log": self.execution_log,
            "sub_results": results,
        }

    def _plan(self, task: str) -> dict:
        """用 LLM 分解任务"""
        prompt = f"""请将以下任务分解为子任务，分配给合适的 Agent。

可用 Agent：
- analyst：数据分析师，擅长数据解读和趋势分析
- retriever：信息检索员，擅长文档检索和信息提取
- reporter：报告撰写员，擅长整理报告

任务：{task}

请用 JSON 格式返回，示例：
{{"steps": [
  {{"id": "step1", "agent": "retriever", "task": "检索相关数据定义", "depends_on": []}},
  {{"id": "step2", "agent": "analyst", "task": "分析数据趋势", "depends_on": ["step1"]}},
  {{"id": "step3", "agent": "reporter", "task": "生成分析报告", "depends_on": ["step1", "step2"]}}
]}}

只返回 JSON，不要其他内容。"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        # 提取 JSON
        import json
        try:
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except json.JSONDecodeError:
            return {"steps": [
                {"id": "step1", "agent": "analyst", "task": task, "depends_on": []},
            ]}

    def _aggregate(self, original_task: str, results: Dict[str, str]) -> str:
        """聚合子任务结果"""
        context = ""
        for step_id, result in results.items():
            context += f"\n### {step_id} 的结果：\n{result}\n"

        prompt = f"""原始任务：{original_task}

各子任务的执行结果：
{context}

请综合以上结果，生成最终的完整回答。要求：
- 整合所有子任务的发现
- 结构清晰，逻辑连贯
- 用中文回答"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=config.get("llm.max_tokens", 2048),
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text
