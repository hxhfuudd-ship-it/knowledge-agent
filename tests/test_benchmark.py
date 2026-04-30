"""Benchmark CLI and dry-run validation tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.benchmark import Benchmark


def test_benchmark_validate_cases_passes_valid_cases():
    benchmark = Benchmark()
    results = benchmark.validate_cases([
        {
            "name": "case",
            "query": "hello",
            "category": "general",
            "expected_tools": [],
            "expected_keywords": [],
        }
    ])
    assert results["passed"] == 1
    assert results["failed"] == 0
    print("  OK  benchmark validates valid cases")


def test_benchmark_validate_cases_reports_invalid_cases():
    benchmark = Benchmark()
    results = benchmark.validate_cases([{"name": "bad"}])
    assert results["passed"] == 0
    assert results["failed"] == 1
    assert "缺少" in results["details"][0]["error"]
    print("  OK  benchmark reports invalid cases")
