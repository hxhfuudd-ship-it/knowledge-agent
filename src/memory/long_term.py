"""长期记忆：重要信息持久化到向量数据库，跨会话保留"""
import logging
import time
from typing import List, Dict, Optional
from pathlib import Path
from ..rag.vector_store import SimpleVectorStore
from ..rag.embedder import get_embedder

logger = logging.getLogger(__name__)

MEMORY_STORE_PATH = str(Path(__file__).parent.parent.parent / "data" / "long_term_memory.json")


class LongTermMemory:
    """向量化长期记忆 - 跨会话持久化"""

    def __init__(self):
        self.store = SimpleVectorStore(persist_path=MEMORY_STORE_PATH)
        self.embedder = get_embedder()
        self._counter = self.store.count()

    def save(self, content: str, category: str = "general", metadata: Optional[dict] = None):
        self._counter += 1
        mem_id = "mem_%d" % self._counter
        meta = {
            "category": category,
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            **(metadata or {}),
        }

        embedding = self.embedder.embed_query(content)
        self.store.add(
            ids=[mem_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[meta],
        )

    def recall(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.store.count() == 0:
            return []

        query_embedding = self.embedder.embed_query(query)
        results = self.store.query(query_embedding=query_embedding, n_results=top_k)

        memories = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            for doc, meta, dist in zip(docs, metadatas, distances):
                memories.append({
                    "content": doc,
                    "relevance": round(1 - dist, 3),
                    "category": meta.get("category", ""),
                    "time": meta.get("time_str", ""),
                })
        return memories

    def get_all(self) -> List[Dict]:
        if self.store.count() == 0:
            return []
        return [
            {"content": doc, "metadata": meta}
            for doc, meta in zip(self.store.documents, self.store.metadatas)
        ]

    def count(self) -> int:
        return self.store.count()

    def clear(self):
        self.store.clear()
        self._counter = 0
