"""轻量向量存储：纯 Python 实现，基于 JSON 持久化 + 余弦相似度检索"""
import json
import logging
import math
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SimpleVectorStore:
    """不依赖外部库的向量数据库，用于学习和小规模场景"""

    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = persist_path
        self.documents: List[str] = []
        self.embeddings: List[List[float]] = []
        self.metadatas: List[dict] = []
        self.ids: List[str] = []

        if persist_path:
            self._load()

    def add(self, ids: List[str], documents: List[str],
            embeddings: List[List[float]], metadatas: Optional[List[dict]] = None):
        for i, doc_id in enumerate(ids):
            meta = metadatas[i] if metadatas else {}
            if doc_id in self.ids:
                idx = self.ids.index(doc_id)
                self.documents[idx] = documents[i]
                self.embeddings[idx] = embeddings[i]
                self.metadatas[idx] = meta
            else:
                self.ids.append(doc_id)
                self.documents.append(documents[i])
                self.embeddings.append(embeddings[i])
                self.metadatas.append(meta)

        self._save()

    def query(self, query_embedding: List[float], n_results: int = 5) -> dict:
        if not self.embeddings:
            return {"documents": [[]], "distances": [[]], "metadatas": [[]]}

        scores = []
        for i, emb in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_embedding, emb)
            scores.append((i, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:n_results]

        docs = [self.documents[i] for i, _ in top]
        distances = [1 - sim for _, sim in top]
        metas = [self.metadatas[i] for i, _ in top]

        return {"documents": [docs], "distances": [distances], "metadatas": [metas]}

    def count(self) -> int:
        return len(self.documents)

    def clear(self):
        self.ids.clear()
        self.documents.clear()
        self.embeddings.clear()
        self.metadatas.clear()
        self._save()

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _save(self):
        if not self.persist_path:
            return
        try:
            Path(self.persist_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump({
                    "ids": self.ids,
                    "documents": self.documents,
                    "embeddings": self.embeddings,
                    "metadatas": self.metadatas,
                }, f, ensure_ascii=False)
        except IOError as e:
            logger.error("向量存储保存失败: %s", e)

    def _load(self):
        path = Path(self.persist_path)
        if not path.exists():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.ids = data.get("ids", [])
            self.documents = data.get("documents", [])
            self.embeddings = data.get("embeddings", [])
            self.metadatas = data.get("metadatas", [])
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("向量存储加载失败，将使用空存储: %s", e)
