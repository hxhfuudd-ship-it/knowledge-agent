"""长期记忆：重要信息持久化到向量数据库，跨会话保留"""
import logging
import time
import uuid
from typing import List, Dict, Optional
from pathlib import Path
from ..rag.vector_store import SimpleVectorStore
from ..rag.embedder import get_embedder
from .. import config

logger = logging.getLogger(__name__)

MEMORY_STORE_PATH = str(Path(__file__).parent.parent.parent / "data" / "long_term_memory.json")
MEMORY_SCHEMA_VERSION = 2


class LongTermMemory:
    """向量化长期记忆 - 跨会话持久化"""

    def __init__(self, namespace: Optional[str] = None, persist_path: Optional[str] = None, embedder=None):
        self.namespace = namespace or config.get("memory.namespace", "default")
        self.store = SimpleVectorStore(persist_path=persist_path or MEMORY_STORE_PATH)
        self._normalize_legacy_records()
        self.embedder = embedder or get_embedder()

    def save(self, content: str, category: str = "general", metadata: Optional[dict] = None,
             importance: float = 0.5, tags: Optional[List[str]] = None):
        mem_id = "%s:mem_%s" % (self.namespace, uuid.uuid4().hex[:12])
        meta = {
            "schema_version": MEMORY_SCHEMA_VERSION,
            "namespace": self.namespace,
            "category": category,
            "importance": round(float(importance), 3),
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tags": tags or [],
            **(metadata or {}),
        }

        embedding = self.embedder.embed_query(content)
        self.store.add(
            ids=[mem_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[meta],
        )

    def recall(self, query: str, top_k: int = 5, category: Optional[str] = None,
               tags: Optional[List[str]] = None) -> List[Dict]:
        if self.store.count() == 0:
            return []

        query_embedding = self.embedder.embed_query(query)
        filters = {"namespace": self.namespace}
        if category:
            filters["category"] = category
        if tags:
            filters["tags"] = {"contains": tags[0]} if len(tags) == 1 else {"in": tags}
        results = self.store.query(query_embedding=query_embedding, n_results=top_k, filters=filters)

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
                    "importance": meta.get("importance", 0.5),
                    "namespace": meta.get("namespace", self.namespace),
                    "tags": meta.get("tags", []),
                    "time": meta.get("time_str", ""),
                })
        memories.sort(key=lambda item: (item.get("relevance", 0), item.get("importance", 0)), reverse=True)
        return memories[:top_k]

    def get_all(self) -> List[Dict]:
        if self.store.count() == 0:
            return []
        return [
            {"content": doc, "metadata": meta}
            for doc, meta in zip(self.store.documents, self.store.metadatas)
            if meta.get("namespace", "default") == self.namespace
        ]

    def count(self) -> int:
        return len(self.get_all())

    def clear(self):
        if not self.store.documents:
            return
        keep = []
        keep_embeddings = []
        keep_metadatas = []
        keep_ids = []
        for doc_id, doc, emb, meta in zip(self.store.ids, self.store.documents, self.store.embeddings, self.store.metadatas):
            if meta.get("namespace", "default") != self.namespace:
                keep_ids.append(doc_id)
                keep_embeddings.append(emb)
                keep_metadatas.append(meta)
                keep.append(doc)
        self.store.ids = keep_ids
        self.store.documents = keep
        self.store.embeddings = keep_embeddings
        self.store.metadatas = keep_metadatas
        self.store._save()

    def _normalize_legacy_records(self):
        updated = False
        for meta in self.store.metadatas:
            if "namespace" not in meta:
                meta["namespace"] = "default"
                updated = True
            if "schema_version" not in meta:
                meta["schema_version"] = MEMORY_SCHEMA_VERSION
                updated = True
        if updated:
            self.store._save()
