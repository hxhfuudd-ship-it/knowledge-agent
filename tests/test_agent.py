"""Agent 集成测试（不调用真实 API，测试工具注册和结构）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.base import ToolRegistry
from src.tools import SQLTool, CalculatorTool, FileReadTool, FileListTool, PythonTool, SearchTool, ChartTool
from src.agent.core import Agent
from src.llm.models import LLMResponse, ToolCall
from src.skills.base import SkillRegistry
from src.skills.data_analysis import DataAnalysisSkill
from src.skills.sql_expert import SQLExpertSkill
from src.skills.report_gen import ReportGenSkill
from src.skills.doc_qa import DocQASkill


class FakeEmbedder:
    def embed_query(self, text):
        return self.embed_texts([text])[0]

    def embed_texts(self, texts):
        return [self._embed(t) for t in texts]

    @staticmethod
    def _embed(text):
        text_lower = text.lower()
        groups = [
            ["分析", "业绩", "经营", "销售", "统计", "趋势", "数据", "指标", "洞察"],
            ["查询", "sql", "数据库", "表", "select", "join"],
            ["报告", "月报", "周报", "总结", "汇报", "报表"],
            ["文档", "知识", "规则", "定义", "怎么算", "如何", "来源"],
        ]
        vec = [1.0 if any(token.lower() in text_lower for token in group) else 0.0 for group in groups]
        if not any(vec):
            vec[0] = 0.01
        return vec


def _use_fake_embedder(reg):
    reg._embedder = FakeEmbedder()
    return reg


class FakeLLM:
    model = "fake-model"

    def __init__(self):
        self.calls = 0

    def chat(self, messages, system=None, tools=None, max_tokens=None):
        self.calls += 1
        if self.calls == 1:
            return LLMResponse(
                text="",
                tool_calls=[ToolCall(id="call_1", name="calculator", input={"expression": "1 + 2"})],
                stop_reason="tool_use",
                usage={"input_tokens": 10, "output_tokens": 1, "total_tokens": 11},
            )
        assert any(m.get("role") == "tool" and "3" in m.get("content", "") for m in messages)
        return LLMResponse(
            text="计算结果是 3",
            stop_reason="end_turn",
            usage={"input_tokens": 8, "output_tokens": 5, "total_tokens": 13},
        )

    @staticmethod
    def build_assistant_message(response):
        return {"role": "assistant", "content": response.text}

    @staticmethod
    def format_tool_result(tool_call_id, content):
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}

    @staticmethod
    def format_tool_results(tool_results):
        return tool_results


class NoopLongTermMemory:
    def recall(self, query, top_k=3):
        return []


class NoopEpisodicMemory:
    def __init__(self):
        self.episodes = []

    def get_context_string(self, n=3):
        return ""

    def add_episode(self, summary, details=None):
        self.episodes.append({"summary": summary, "details": details or {}})


class NoopWorkingMemory:
    def __init__(self):
        self.steps = []

    def get_task_context(self):
        return ""

    def add_step(self, step, result=None):
        self.steps.append((step, result))

    def clear(self):
        self.steps = []


class NoopShortTermMemory:
    summary = ""

    def __init__(self):
        self.messages = []

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})

    def clear(self):
        self.messages = []

    def __len__(self):
        return len(self.messages)


def build_test_agent():
    agent = Agent.__new__(Agent)
    agent.llm = FakeLLM()
    agent.max_iterations = 3
    agent.registry = ToolRegistry()
    agent.registry.register(CalculatorTool())
    agent.skill_registry = SkillRegistry(match_strategy="keyword")
    agent.conversation = []
    agent.tool_call_log = []
    agent.short_term = NoopShortTermMemory()
    agent.long_term = NoopLongTermMemory()
    agent.episodic = NoopEpisodicMemory()
    agent.working = NoopWorkingMemory()
    return agent


def test_tool_registry():
    reg = ToolRegistry()
    tools = [SQLTool(), CalculatorTool(), FileReadTool(), FileListTool(),
             PythonTool(), SearchTool(), ChartTool()]
    for t in tools:
        reg.register(t)
    assert len(reg.list_tools()) == 7
    assert reg.get("sql_query") is not None
    assert reg.get("nonexistent") is None
    print("  OK  tool registry (%d tools)" % len(reg.list_tools()))


def test_claude_tool_format():
    reg = ToolRegistry()
    reg.register(SQLTool())
    reg.register(CalculatorTool())
    claude_tools = reg.to_claude_tools()
    assert len(claude_tools) == 2
    for t in claude_tools:
        assert "name" in t
        assert "description" in t
        assert "input_schema" in t
    print("  OK  claude tool format valid")


def test_skill_registry():
    reg = SkillRegistry()
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    assert len(reg.list_skills()) == 4
    print("  OK  skill registry (%d skills)" % len(reg.list_skills()))


def test_skill_match():
    reg = SkillRegistry()
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    matched = reg.match("帮我分析一下销售数据")
    assert matched is not None
    assert matched.name in ["data_analysis", "sql_expert"]
    no_match = reg.match("今天天气怎么样")
    print("  OK  skill match (matched=%s, no_match=%s)" % (
        matched.name if matched else None,
        no_match.name if no_match else None,
    ))


def test_skill_build_prompt():
    skill = DocQASkill()
    prompt = skill.build_prompt("VIP客户怎么定义")
    assert "VIP" in prompt
    print("  OK  skill build_prompt")


def test_skill_embedding_match():
    reg = _use_fake_embedder(SkillRegistry(match_strategy="embedding"))
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    matched = reg.match("公司业绩怎么样")
    assert matched is not None
    print("  OK  skill embedding match (matched=%s)" % matched.name)


def test_skill_hybrid_match():
    reg = _use_fake_embedder(SkillRegistry(match_strategy="hybrid"))
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    kw_hit = reg.match("帮我分析一下销售数据")
    assert kw_hit is not None and kw_hit.name == "data_analysis"
    semantic_hit = reg.match("公司整体经营情况如何")
    assert semantic_hit is not None
    print("  OK  skill hybrid match (keyword=%s, semantic=%s)" % (kw_hit.name, semantic_hit.name))


def test_skill_match_with_scores():
    reg = _use_fake_embedder(SkillRegistry(match_strategy="hybrid"))
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    scores = reg.match_with_scores("生成一份月报")
    assert len(scores) == 4
    assert any(s["keyword_match"] for s in scores)
    assert all("embedding_score" in s for s in scores)
    print("  OK  skill match_with_scores (%d skills scored)" % len(scores))


def test_agent_react_tool_loop_with_fake_llm():
    agent = build_test_agent()
    result = agent.chat("帮我算 1 + 2")

    assert result["response"] == "计算结果是 3"
    assert result["tool_calls"][0]["tool"] == "calculator"
    assert "3" in result["tool_calls"][0]["output"]
    assert agent.working.steps
    assert agent.episodic.episodes
    assert result["trace"]["summary"]["llm_calls"] == 2
    assert result["trace"]["summary"]["tool_calls"] == 1
    assert result["trace"]["summary"]["tokens"]["total_tokens"] == 24
    assert result["trace"]["events"][0]["type"] == "llm"
    print("  OK  agent ReAct loop with fake LLM")


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll agent tests passed!")
