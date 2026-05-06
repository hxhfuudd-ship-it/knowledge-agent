"""Offline RAG response evaluation.

This evaluator focuses on whether the final answer is grounded in retrieved
context, not just whether the retriever found relevant chunks.
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .rag_eval import build_offline_retriever


PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CASES_PATH = PROJECT_ROOT / "data" / "rag_response_eval_cases.yaml"

_STOPWORDS = {
    "citation",
    "source",
    "sources",
    "chunk",
    "chunk_id",
    "section",
    "http",
    "https",
    "html",
    "md",
    "the",
    "and",
    "or",
    "to",
    "of",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "sum",
}


def load_cases(path: str = None) -> List[Dict[str, Any]]:
    cases_path = Path(path) if path else DEFAULT_CASES_PATH
    with open(cases_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data.get("cases", [])


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _response_mentions_citation(response: str, contexts: List[Dict[str, Any]]) -> bool:
    response_text = _normalize(response)
    for ctx in contexts:
        candidates = [
            ctx.get("citation", ""),
            ctx.get("chunk_id", ""),
            ctx.get("source", ""),
            ctx.get("section", ""),
        ]
        if any(candidate and _normalize(candidate) in response_text for candidate in candidates):
            return True
    return False


def _strip_citation(response: str) -> str:
    return re.split(r"citation\s*[:：]", response, maxsplit=1, flags=re.IGNORECASE)[0]


def _content_terms(text: str) -> List[str]:
    terms = []
    for token in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}", _normalize(text)):
        token = token.lower()
        if token in _STOPWORDS:
            continue
        terms.append(token)
    return terms


def _context_text(contexts: List[Dict[str, Any]]) -> str:
    parts = []
    for ctx in contexts:
        parts.extend([
            str(ctx.get("content", "")),
            str(ctx.get("section", "")),
            str(ctx.get("source", "")),
        ])
    return " ".join(parts)


def _response_faithfulness(response: str, contexts: List[Dict[str, Any]]) -> float:
    context_text = _normalize(_context_text(contexts))
    response_terms = _content_terms(_strip_citation(response))
    if not response_terms:
        return 0.0
    hits = sum(1 for term in response_terms if term in context_text)
    return hits / len(response_terms)


def _question_coverage(response: str, expected_keywords: List[str]) -> float:
    if not expected_keywords:
        return 1.0
    hits = sum(1 for keyword in expected_keywords if keyword in response)
    return hits / len(expected_keywords)


def evaluate_cases(cases: List[Dict[str, Any]], retriever, top_k: int = 3) -> Dict[str, Any]:
    details = []
    grounded_hits = 0
    citation_hits = 0
    coverage_scores = []
    groundedness_scores = []

    for case in cases:
        query = case.get("query", "")
        expected_keywords = case.get("expected_keywords", [])
        response = case.get("response", "")
        results = retriever.search_hybrid(query, top_k=top_k)
        contexts = [
            {
                "content": doc,
                "citation": meta.get("citation", ""),
                "chunk_id": meta.get("chunk_id", ""),
                "section": meta.get("section", ""),
                "source": meta.get("filename", ""),
            }
            for doc, _score, meta in results
        ]
        citation_hit = _response_mentions_citation(response, contexts)
        groundedness = _response_faithfulness(response, contexts)
        coverage = _question_coverage(response, expected_keywords)
        grounded_hit = citation_hit and groundedness >= 0.6 and coverage >= 0.8

        grounded_hits += 1 if grounded_hit else 0
        citation_hits += 1 if citation_hit else 0
        groundedness_scores.append(groundedness)
        coverage_scores.append(coverage)

        details.append({
            "name": case.get("name", ""),
            "query": query,
            "response": response,
            "expected_keywords": expected_keywords,
            "retrieved_citations": [ctx["citation"] for ctx in contexts],
            "groundedness": groundedness,
            "citation_hit": citation_hit,
            "coverage": coverage,
            "passed": grounded_hit,
        })

    total = len(cases)
    passed = sum(1 for item in details if item["passed"])
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "citation_hit_rate": citation_hits / total if total else 0,
        "avg_faithfulness": sum(groundedness_scores) / total if total else 0,
        "avg_groundedness": sum(groundedness_scores) / total if total else 0,
        "avg_coverage": sum(coverage_scores) / total if total else 0,
        "grounded_pass_rate": grounded_hits / total if total else 0,
        "details": details,
    }


def to_markdown(results: Dict[str, Any]) -> str:
    lines = [
        "# RAG Response Evaluation Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        "| Total | %d |" % results["total"],
        "| Passed | %d |" % results["passed"],
        "| Failed | %d |" % results["failed"],
        "| Citation Hit Rate | %.1f%% |" % (results["citation_hit_rate"] * 100),
        "| Avg Faithfulness | %.1f%% |" % (results["avg_faithfulness"] * 100),
        "| Avg Coverage | %.1f%% |" % (results["avg_coverage"] * 100),
        "| Grounded Pass Rate | %.1f%% |" % (results["grounded_pass_rate"] * 100),
        "",
        "## Details",
        "",
    ]
    for item in results.get("details", []):
        status = "PASS" if item["passed"] else "FAIL"
        lines.append("### [%s] %s" % (status, item["name"]))
        lines.append("- Query: %s" % item["query"])
        lines.append("- Response: %s" % item["response"])
        lines.append("- Retrieved Citations: %s" % ", ".join(item["retrieved_citations"]))
        lines.append("- Citation Hit: %s" % item["citation_hit"])
        lines.append("- Faithfulness: %.1f%%" % (item["groundedness"] * 100))
        lines.append("- Coverage: %.1f%%" % (item["coverage"] * 100))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAG response grounding quality")
    parser.add_argument("--cases", help="Path to rag_response_eval_cases.yaml")
    parser.add_argument("--docs-dir", help="Document directory to evaluate")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", help="Write report to this path")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit non-zero when any eval case fails")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    retriever = build_offline_retriever(args.docs_dir)
    results = evaluate_cases(cases, retriever, top_k=args.top_k)
    content = json.dumps(results, ensure_ascii=False, indent=2) if args.format == "json" else to_markdown(results)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print("RAG response eval report written to: %s" % output_path)
    else:
        print(content)

    if args.fail_on_regression and results["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
