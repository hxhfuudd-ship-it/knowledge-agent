"""Offline RAG retrieval evaluation.

This evaluator focuses on retrieval quality, not final answer quality. It runs
against the local document corpus and reports source hit rate, keyword hit rate,
and MRR so RAG changes can be compared over time.
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

from src.rag.chunker import TextChunker
from src.rag.loader import DocumentLoader
from src.rag.retriever import Retriever


PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CASES_PATH = PROJECT_ROOT / "data" / "rag_eval_cases.yaml"
DEFAULT_DOCS_DIR = PROJECT_ROOT / "data" / "documents"


class HashEmbedder:
    """Deterministic offline embedder for stable retrieval evaluation."""

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        from src.rag.embedder import Embedder
        return Embedder._embed_hash(texts)

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]


def load_cases(path: str = None) -> List[Dict[str, Any]]:
    cases_path = Path(path) if path else DEFAULT_CASES_PATH
    with open(cases_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data.get("cases", [])


def build_offline_retriever(docs_dir: str = None) -> Retriever:
    loader = DocumentLoader()
    chunker = TextChunker(chunk_size=512, chunk_overlap=50)
    docs = loader.load(str(Path(docs_dir) if docs_dir else DEFAULT_DOCS_DIR))
    chunks = chunker.chunk(docs, strategy="semantic")

    retriever = Retriever(top_k=5)
    retriever.embedder = HashEmbedder()
    retriever.collection.persist_path = None
    retriever.rebuild_documents(chunks)
    return retriever


def _source_rank(results: List, expected_sources: List[str]) -> int:
    for index, (_doc, _score, meta) in enumerate(results, 1):
        source = meta.get("filename", "")
        if source in expected_sources:
            return index
    return 0


def _context_precision(results: List, expected_sources: List[str]) -> float:
    if not results or not expected_sources:
        return 0.0
    relevant = 0
    precision_sum = 0.0
    for index, (_doc, _score, meta) in enumerate(results, 1):
        if meta.get("filename", "") in expected_sources:
            relevant += 1
            precision_sum += relevant / index
    return precision_sum / relevant if relevant else 0.0


def _source_recall(results: List, expected_sources: List[str]) -> float:
    if not expected_sources:
        return 1.0
    retrieved_sources = {meta.get("filename", "") for _doc, _score, meta in results}
    return len(set(expected_sources) & retrieved_sources) / len(set(expected_sources))


def _keyword_hit(results: List, expected_keywords: List[str]) -> bool:
    if not expected_keywords:
        return True
    combined = "\n".join(doc for doc, _score, _meta in results)
    return all(keyword in combined for keyword in expected_keywords)


def _keyword_coverage(results: List, expected_keywords: List[str]) -> float:
    if not expected_keywords:
        return 1.0
    combined = "\n".join(doc for doc, _score, _meta in results)
    hits = sum(1 for keyword in expected_keywords if keyword in combined)
    return hits / len(expected_keywords)


def evaluate_cases(cases: List[Dict[str, Any]], retriever: Retriever, top_k: int = 3) -> Dict[str, Any]:
    details = []
    source_hits = 0
    keyword_hits = 0
    reciprocal_ranks = []
    source_recalls = []
    context_precisions = []
    keyword_coverages = []

    for case in cases:
        query = case.get("query", "")
        expected_sources = case.get("expected_sources", [])
        expected_keywords = case.get("expected_keywords", [])
        results = retriever.search_hybrid(query, top_k=top_k)
        rank = _source_rank(results, expected_sources)
        source_hit = bool(rank)
        keyword_hit = _keyword_hit(results, expected_keywords)
        source_recall = _source_recall(results, expected_sources)
        context_precision = _context_precision(results, expected_sources)
        keyword_coverage = _keyword_coverage(results, expected_keywords)
        source_hits += 1 if source_hit else 0
        keyword_hits += 1 if keyword_hit else 0
        reciprocal_ranks.append(1 / rank if rank else 0)
        source_recalls.append(source_recall)
        context_precisions.append(context_precision)
        keyword_coverages.append(keyword_coverage)
        details.append({
            "name": case.get("name", ""),
            "query": query,
            "expected_sources": expected_sources,
            "expected_keywords": expected_keywords,
            "retrieved_sources": [meta.get("filename", "") for _doc, _score, meta in results],
            "retrieved_chunk_ids": [meta.get("chunk_id", "") for _doc, _score, meta in results],
            "retrieved_citations": [meta.get("citation", "") for _doc, _score, meta in results],
            "scores": [round(score, 4) for _doc, score, _meta in results],
            "source_hit": source_hit,
            "source_rank": rank,
            "source_recall": source_recall,
            "context_precision": context_precision,
            "keyword_hit": keyword_hit,
            "keyword_coverage": keyword_coverage,
            "passed": source_hit and keyword_hit,
        })

    total = len(cases)
    passed = sum(1 for item in details if item["passed"])
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "source_hit_at_k": source_hits / total if total else 0,
        "source_recall_at_k": sum(source_recalls) / total if total else 0,
        "context_precision_at_k": sum(context_precisions) / total if total else 0,
        "keyword_hit_rate": keyword_hits / total if total else 0,
        "keyword_coverage": sum(keyword_coverages) / total if total else 0,
        "mrr": sum(reciprocal_ranks) / total if total else 0,
        "details": details,
    }


def to_markdown(results: Dict[str, Any]) -> str:
    lines = [
        "# RAG Retrieval Evaluation Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        "| Total | %d |" % results["total"],
        "| Passed | %d |" % results["passed"],
        "| Failed | %d |" % results["failed"],
        "| Source Hit@K | %.1f%% |" % (results["source_hit_at_k"] * 100),
        "| Source Recall@K | %.1f%% |" % (results["source_recall_at_k"] * 100),
        "| Context Precision@K | %.1f%% |" % (results["context_precision_at_k"] * 100),
        "| Keyword Hit Rate | %.1f%% |" % (results["keyword_hit_rate"] * 100),
        "| Keyword Coverage | %.1f%% |" % (results["keyword_coverage"] * 100),
        "| MRR | %.3f |" % results["mrr"],
        "",
        "## Details",
        "",
    ]
    for item in results.get("details", []):
        status = "PASS" if item["passed"] else "FAIL"
        lines.append("### [%s] %s" % (status, item["name"]))
        lines.append("- Query: %s" % item["query"])
        lines.append("- Expected Sources: %s" % ", ".join(item["expected_sources"]))
        lines.append("- Retrieved Sources: %s" % ", ".join(item["retrieved_sources"]))
        lines.append("- Retrieved Chunks: %s" % ", ".join(item["retrieved_chunk_ids"]))
        lines.append("- Citations: %s" % ", ".join(item["retrieved_citations"]))
        lines.append("- Source Rank: %s" % (item["source_rank"] or "not found"))
        lines.append("- Source Recall: %.1f%%" % (item["source_recall"] * 100))
        lines.append("- Context Precision: %.1f%%" % (item["context_precision"] * 100))
        lines.append("- Keyword Hit: %s" % item["keyword_hit"])
        lines.append("- Keyword Coverage: %.1f%%" % (item["keyword_coverage"] * 100))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local RAG retrieval quality")
    parser.add_argument("--cases", help="Path to rag_eval_cases.yaml")
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
        print("RAG eval report written to: %s" % output_path)
    else:
        print(content)

    if args.fail_on_regression and results["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
