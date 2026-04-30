"""Environment doctor tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import doctor


def test_format_report_counts_failures():
    report = doctor.format_report([
        ("a", True, "ok"),
        ("b", False, "bad"),
    ])
    assert "[OK] a - ok" in report
    assert "[FAIL] b - bad" in report
    assert "1 passed, 1 failed" in report
    print("  OK  doctor report formatting")


def test_run_checks_without_packages():
    results = doctor.run_checks(include_packages=False)
    names = [name for name, _, _ in results]
    assert "env_file" in names
    assert "llm_credentials" in names
    assert "database" in names
    assert "documents" in names
    assert all(isinstance(ok, bool) for _, ok, _ in results)
    print("  OK  doctor checks shape")
