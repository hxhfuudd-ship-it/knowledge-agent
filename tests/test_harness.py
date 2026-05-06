"""Harness tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.harness.models import HarnessCase, HarnessExpectation, HarnessLimits
from src.harness.runner import HarnessRunner, load_cases


def test_harness_validate_cases():
    runner = HarnessRunner()
    results = runner.validate_cases([
        {
            "name": "case",
            "query": "hello",
            "expect": {"tools": [], "keywords": [], "sources": []},
        }
    ])
    assert results["passed"] == 1
    assert results["failed"] == 0
    print("  OK  harness validates case structure")


def test_harness_dry_run_scripted_tool_loop():
    cases = load_cases("data/harness_cases.yaml")
    runner = HarnessRunner()
    results = runner.run_cases([cases[0]], live=False)
    detail = results["details"][0]
    assert results["passed"] == 1
    assert detail["tools_used"] == ["calculator"]
    assert detail["status"] == "passed"
    assert detail["run_id"].startswith("calculator_tool_trace-")
    assert detail["trajectory"][0]["tool"] == "calculator"
    assert detail["violations"] == []
    assert detail["checks"]["tools"] is True
    assert detail["checks"]["ordered_tools"] is True
    assert detail["checks"]["forbidden_tools"] is True
    assert detail["checks"]["tool_call_limits"] is True
    assert detail["checks"]["keywords"] is True
    assert detail["trace"]["summary"]["tool_calls"] == 1
    print("  OK  harness dry-run scripted tool loop")


def test_harness_detects_forbidden_tool_violation():
    case = HarnessCase(
        name="forbidden_tool_case",
        query="请计算 1 + 1",
        expectations=HarnessExpectation(
            tools=["calculator"],
            forbidden_tools=["web_search"],
            keywords=["2"],
        ),
        limits=HarnessLimits(min_tool_calls=1, max_tool_calls=2),
    )
    script = {
        "tool_calls": [
            {"name": "calculator", "input": {"expression": "1 + 1"}},
            {"name": "web_search", "input": {"query": "1 + 1"}},
        ],
        "final_response": "结果是 2。",
    }

    detail = HarnessRunner().run_case(case, script=script).to_dict()

    assert detail["passed"] is False
    assert detail["status"] == "failed"
    assert detail["checks"]["forbidden_tools"] is False
    assert "调用了禁止工具" in detail["violations"]
    print("  OK  harness detects forbidden tool violation")


def test_harness_detects_order_and_tool_limit_violation():
    case = HarnessCase(
        name="wrong_order_case",
        query="先查数据再画图",
        expectations=HarnessExpectation(
            tools=["sql_query", "create_chart"],
            ordered_tools=["sql_query", "create_chart"],
            keywords=["图"],
        ),
        limits=HarnessLimits(min_tool_calls=2, max_tool_calls=2),
    )
    script = {
        "tool_calls": [
            {"name": "create_chart", "input": {"chart_type": "bar"}},
            {"name": "sql_query", "input": {"query": "SELECT 1"}},
            {"name": "calculator", "input": {"expression": "1 + 1"}},
        ],
        "final_response": "图已生成。",
    }

    detail = HarnessRunner().run_case(case, script=script).to_dict()

    assert detail["passed"] is False
    assert detail["checks"]["ordered_tools"] is False
    assert detail["checks"]["tool_call_limits"] is False
    assert "工具调用顺序不符合任务轨迹" in detail["violations"]
    assert "工具调用次数超出边界" in detail["violations"]
    print("  OK  harness detects trajectory and limit violations")
