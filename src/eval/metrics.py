"""评估指标：衡量 Agent 各方面表现"""
import time
from typing import List, Dict, Any, Callable


class Metrics:
    """Agent 评估指标计算"""

    @staticmethod
    def tool_accuracy(test_cases: List[Dict]) -> Dict[str, float]:
        """工具调用准确率：是否选对了工具、参数是否正确"""
        total = len(test_cases)
        correct_tool = 0
        correct_params = 0

        for case in test_cases:
            expected = case.get("expected_tool")
            actual = case.get("actual_tool")
            if expected == actual:
                correct_tool += 1
                if case.get("expected_params") == case.get("actual_params"):
                    correct_params += 1

        return {
            "tool_selection_accuracy": correct_tool / total if total else 0,
            "param_accuracy": correct_params / total if total else 0,
            "total_cases": total,
        }

    @staticmethod
    def retrieval_quality(results: List[Dict]) -> Dict[str, float]:
        """RAG 检索质量：Recall@K, MRR, NDCG"""
        recalls = []
        mrrs = []

        for r in results:
            relevant = set(r.get("relevant_ids", []))
            retrieved = r.get("retrieved_ids", [])
            k = len(retrieved)

            # Recall@K
            if relevant:
                hits = len(relevant & set(retrieved))
                recalls.append(hits / len(relevant))
            else:
                recalls.append(0)

            # MRR (Mean Reciprocal Rank)
            rr = 0
            for i, doc_id in enumerate(retrieved):
                if doc_id in relevant:
                    rr = 1 / (i + 1)
                    break
            mrrs.append(rr)

        return {
            "recall_at_k": sum(recalls) / len(recalls) if recalls else 0,
            "mrr": sum(mrrs) / len(mrrs) if mrrs else 0,
            "total_queries": len(results),
        }

    @staticmethod
    def response_quality(evaluations: List[Dict]) -> Dict[str, float]:
        """回答质量：准确性、完整性、相关性（基于评分）"""
        accuracy_scores = [e.get("accuracy", 0) for e in evaluations]
        completeness_scores = [e.get("completeness", 0) for e in evaluations]
        relevance_scores = [e.get("relevance", 0) for e in evaluations]

        n = len(evaluations) or 1
        return {
            "avg_accuracy": sum(accuracy_scores) / n,
            "avg_completeness": sum(completeness_scores) / n,
            "avg_relevance": sum(relevance_scores) / n,
        }

    @staticmethod
    def latency_cost(records: List[Dict]) -> Dict[str, float]:
        """延迟和成本统计"""
        latencies = [r.get("latency_ms", 0) for r in records]
        tokens = [r.get("total_tokens", 0) for r in records]

        return {
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            "total_tokens": sum(tokens),
            "avg_tokens_per_query": sum(tokens) / len(tokens) if tokens else 0,
        }
