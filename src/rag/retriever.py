"""检索器：向量检索 + BM25 关键词混合检索"""
import logging
import re
from typing import List, Tuple, Optional
from pathlib import Path
from .loader import Document
from .embedder import get_embedder
from .vector_store import SimpleVectorStore
from .. import config

logger = logging.getLogger(__name__)

_project_root = Path(__file__).parent.parent.parent


def _get_store_path() -> str:
    return str(_project_root / "data" / "vector_store.json")


class Retriever:
    """混合检索 = 向量相似度 + BM25 关键词匹配"""

    def __init__(self, collection_name: Optional[str] = None, top_k: Optional[int] = None):
        self.collection_name = collection_name or config.get("rag.collection_name", "knowledge_base")
        self.top_k = top_k or config.get("rag.top_k", 5)
        self.embedder = get_embedder()
        self._store = None
        self._documents: List[str] = []
        self._bm25 = None

    @property
    def collection(self) -> SimpleVectorStore:
        if self._store is None:
            self._store = SimpleVectorStore(persist_path=_get_store_path())
        return self._store

    def add_documents(self, chunks: List[Document]):
        if not chunks:
            return

        texts = [c.content for c in chunks]
        embeddings = self.embedder.embed_texts(texts)
        base = self.collection.count()
        ids = ["doc_%d" % (base + i) for i in range(len(chunks))]
        metadatas = []
        for c in chunks:
            clean = {}
            for k, v in c.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean[k] = v
            metadatas.append(clean)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        self._documents = list(self.collection.documents)
        self._build_bm25(self._documents)

    def rebuild_documents(self, chunks: List[Document]):
        self.collection.clear()
        self._documents = []
        self._bm25 = None
        self.add_documents(chunks)

    def ensure_bm25_index(self):
        documents = list(self.collection.documents)
        if documents and (self._bm25 is None or self._documents != documents):
            self._documents = documents
            self._build_bm25(documents)

    def _build_bm25(self, texts: List[str]):
        try:
            from rank_bm25 import BM25Okapi
            tokenized = [self._tokenize(t) for t in texts]
            self._bm25 = BM25Okapi(tokenized)
        except ImportError:
            logger.info("rank_bm25 未安装，BM25 检索不可用")
            self._bm25 = None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """中文按字+英文按词的简易分词"""
        tokens = []
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                tokens.append(char)
            elif char.isalnum():
                tokens.append(char.lower())
            # 跳过标点和空白
        # 合并连续英文字符为单词
        merged = []
        buf = ""
        for t in tokens:
            if t.isascii() and t.isalnum():
                buf += t
            else:
                if buf:
                    merged.append(buf)
                    buf = ""
                merged.append(t)
        if buf:
            merged.append(buf)
        return merged

    def search_vector(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float, dict]]:
        k = top_k or self.top_k
        query_embedding = self.embedder.embed_query(query)

        results = self.collection.query(query_embedding=query_embedding, n_results=k)

        items = []
        if results and results["documents"]:
            docs = results["documents"][0]
            distances = results["distances"][0] if results.get("distances") else [0] * len(docs)
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            for doc, dist, meta in zip(docs, distances, metadatas):
                score = 1 - dist
                items.append((doc, score, meta))
        return items

    def search_bm25(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float, dict]]:
        self.ensure_bm25_index()
        if not self._bm25 or not self._documents:
            return []

        k = top_k or self.top_k
        try:
            tokenized_query = self._tokenize(query)
            scores = self._bm25.get_scores(tokenized_query)

            indexed_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

            results = []
            for idx, score in indexed_scores[:k]:
                if score > 0:
                    meta = self.collection.metadatas[idx] if idx < len(self.collection.metadatas) else {}
                    results.append((self._documents[idx], score, meta))
            return results
        except Exception as e:
            logger.warning("BM25 检索失败: %s", e)
            return []

    @staticmethod
    def _lexical_score(query: str, document: str) -> float:
        query_terms = set(Retriever._tokenize(query))
        if not query_terms:
            return 0.0
        doc_terms = set(Retriever._tokenize(document))
        hits = query_terms & doc_terms
        return len(hits) / len(query_terms)

    def search_hybrid(self, query: str, top_k: Optional[int] = None,
                      vector_weight: float = 0.7) -> List[Tuple[str, float, dict]]:
        k = top_k or self.top_k

        vector_results = self.search_vector(query, top_k=k * 2)
        bm25_results = self.search_bm25(query, top_k=k * 2)

        doc_scores = {}
        doc_meta = {}

        lexical_weight = 0.15
        effective_vector_weight = max(vector_weight - lexical_weight, 0)

        for doc, score, meta in vector_results:
            doc_scores[doc] = effective_vector_weight * score
            doc_meta[doc] = meta

        bm25_weight = 1 - vector_weight
        if bm25_results:
            max_bm25 = max((s for _, s, _meta in bm25_results), default=1) or 1
            for doc, score, meta in bm25_results:
                normalized = score / max_bm25
                doc_scores[doc] = doc_scores.get(doc, 0) + bm25_weight * normalized
                if doc not in doc_meta:
                    doc_meta[doc] = meta

        for doc in list(doc_scores):
            doc_scores[doc] += lexical_weight * self._lexical_score(query, doc)

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return [(doc, score, doc_meta.get(doc, {})) for doc, score in sorted_docs[:k]]

    def get_stats(self) -> dict:
        return {
            "collection": self.collection_name,
            "total_documents": self.collection.count(),
            "bm25_ready": self._bm25 is not None,
        }
