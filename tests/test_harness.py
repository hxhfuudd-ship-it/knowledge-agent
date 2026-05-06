"""Harness tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

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
    assert detail["checks"]["tools"] is True
    assert detail["checks"]["keywords"] is True
    assert detail["trace"]["summary"]["tool_calls"] == 1
    print("  OK  harness dry-run scripted tool loop")

