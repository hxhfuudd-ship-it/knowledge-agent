"""RAG retrieval evaluation tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.rag_eval import build_offline_retriever, evaluate_cases, load_cases


def test_rag_eval_load_cases():
    cases = load_cases("data/rag_eval_cases.yaml")
    assert len(cases) >= 3
    assert all(case.get("query") for case in cases)
    print("  OK  rag eval loads cases")


def test_rag_eval_offline_retriever_runs():
    cases = load_cases("data/rag_eval_cases.yaml")[:2]
    retriever = build_offline_retriever()
    results = evaluate_cases(cases, retriever, top_k=3)
    assert results["total"] == 2
    assert "source_hit_at_k" in results
    assert "mrr" in results
    assert results["details"][0]["retrieved_sources"]
    print("  OK  rag eval offline retriever runs")

