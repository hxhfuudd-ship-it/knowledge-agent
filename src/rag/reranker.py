"""重排序器：对检索结果二次排序，提升相关性"""
import logging
from typing import List, Tuple
from .. import config

logger = logging.getLogger(__name__)


class Reranker:
    """使用 LLM 对检索结果重排序"""

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            from ..llm import create_llm_client
            self._llm = create_llm_client()
        return self._llm

    def rerank(self, query: str, documents: List[Tuple[str, float, dict]],
               top_k: int = 3) -> List[Tuple[str, float, dict]]:
        if len(documents) <= top_k:
            return documents

        try:
            llm = self._get_llm()

            doc_list = ""
            for i, (doc, _, _) in enumerate(documents):
                truncated = doc[:300] + "..." if len(doc) > 300 else doc
                doc_list += "\n[文档%d] %s\n" % (i, truncated)

            prompt = (
                "请评估以下文档与查询的相关性。\n\n"
                "查询：%s\n\n文档列表：\n%s\n\n"
                "请返回最相关的 %d 个文档编号（从最相关到最不相关），"
                "格式为逗号分隔的数字。只返回数字，如：2,0,4"
            ) % (query, doc_list, top_k)

            response = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
            )
            text = response.text.strip()
            indices = [int(x.strip()) for x in text.split(",") if x.strip().isdigit()]

            reranked = []
            score = 1.0
            for idx in indices[:top_k]:
                if 0 <= idx < len(documents):
                    doc, _, meta = documents[idx]
                    reranked.append((doc, score, meta))
                    score -= 0.1
            return reranked if reranked else documents[:top_k]
        except Exception as e:
            logger.warning("LLM 重排序失败，使用原始排序: %s", e)
            return documents[:top_k]


class SimpleReranker:
    """简易重排序：基于关键词匹配度（不调用 API，用于测试）"""

    def rerank(self, query: str, documents: List[Tuple[str, float, dict]],
               top_k: int = 3) -> List[Tuple[str, float, dict]]:
        query_chars = set(query)

        scored = []
        for doc, orig_score, meta in documents:
            overlap = len(query_chars & set(doc)) / max(len(query_chars), 1)
            combined = orig_score * 0.6 + overlap * 0.4
            scored.append((doc, combined, meta))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
