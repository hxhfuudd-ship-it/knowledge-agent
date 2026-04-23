"""Agent 集成测试（不调用真实 API，测试工具注册和结构）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.base import ToolRegistry
from src.tools import SQLTool, CalculatorTool, FileReadTool, FileListTool, PythonTool, SearchTool, ChartTool
from src.skills.base import SkillRegistry
from src.skills.data_analysis import DataAnalysisSkill
from src.skills.sql_expert import SQLExpertSkill
from src.skills.report_gen import ReportGenSkill
from src.skills.doc_qa import DocQASkill


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
    reg = SkillRegistry(match_strategy="embedding")
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    matched = reg.match("公司业绩怎么样")
    assert matched is not None
    print("  OK  skill embedding match (matched=%s)" % matched.name)


def test_skill_hybrid_match():
    reg = SkillRegistry(match_strategy="hybrid")
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    kw_hit = reg.match("帮我分析一下销售数据")
    assert kw_hit is not None and kw_hit.name == "data_analysis"
    semantic_hit = reg.match("公司整体经营情况如何")
    assert semantic_hit is not None
    print("  OK  skill hybrid match (keyword=%s, semantic=%s)" % (kw_hit.name, semantic_hit.name))


def test_skill_match_with_scores():
    reg = SkillRegistry(match_strategy="hybrid")
    for cls in [DataAnalysisSkill, SQLExpertSkill, ReportGenSkill, DocQASkill]:
        reg.register(cls())
    scores = reg.match_with_scores("生成一份月报")
    assert len(scores) == 4
    assert any(s["keyword_match"] for s in scores)
    assert all("embedding_score" in s for s in scores)
    print("  OK  skill match_with_scores (%d skills scored)" % len(scores))


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll agent tests passed!")
