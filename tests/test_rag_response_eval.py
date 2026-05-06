"""RAG response evaluation tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.rag_response_eval import evaluate_cases, load_cases
from src.eval.rag_eval import build_offline_retriever


def test_rag_response_eval_load_cases():
    cases = load_cases("data/rag_response_eval_cases.yaml")
    assert len(cases) >= 3
    assert all(case.get("response") for case in cases)
    print("  OK  rag response eval loads cases")


def test_rag_response_eval_runs():
    cases = load_cases("data/rag_response_eval_cases.yaml")
    retriever = build_offline_retriever()
    results = evaluate_cases(cases, retriever, top_k=3)
    assert results["total"] == 3
    assert "citation_hit_rate" in results
    assert "avg_groundedness" in results
    assert "avg_coverage" in results
    assert results["passed"] >= 2
    print("  OK  rag response eval runs")


def test_rag_response_eval_is_grounded():
    cases = load_cases("data/rag_response_eval_cases.yaml")
    retriever = build_offline_retriever()
    results = evaluate_cases(cases, retriever, top_k=3)
    assert results["grounded_pass_rate"] >= 0.66
    assert results["citation_hit_rate"] >= 0.66
    print("  OK  rag response eval groundedness")
