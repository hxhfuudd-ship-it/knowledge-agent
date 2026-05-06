"""RAG 检索工具：让 Agent 能通过 RAG 检索知识库文档"""
import json
import logging
from typing import List
from pathlib import Path
from ..tools.base import Tool
from .loader import DocumentLoader
from .chunker import TextChunker
from .retriever import Retriever
from .reranker import SimpleReranker
from .. import config

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent.parent.parent / "data" / "documents"
MANIFEST_PATH = Path(__file__).parent.parent.parent / "data" / "vector_store_manifest.json"
INDEX_SCHEMA_VERSION = 2

_shared_retriever = None


def _get_retriever() -> Retriever:
    global _shared_retriever
    if _shared_retriever is None:
        _shared_retriever = Retriever()
    return _shared_retriever


class RAGSearchTool(Tool):
    name = "rag_search"
    description = (
        "从知识库中语义检索相关文档。适用于查找数据字典、业务规则、分析方法等知识。"
        "输入自然语言查询，返回带 source/chunk_id/citation 的相关文档片段。"
        "回答知识库问题时应基于这些片段，并在结论后标注引用。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询，如 '订单表的字段有哪些' 或 '如何计算复购率'",
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量，默认 3",
            },
        },
        "required": ["query"],
    }

    def __init__(self):
        self.retriever = _get_retriever()
        self.reranker = SimpleReranker()
        self._indexed = False
        self._index_signature = None

    @staticmethod
    def _docs_signature() -> List[dict]:
        if not DOCS_DIR.exists():
            return []
        loader = DocumentLoader()
        files = [
            f for f in DOCS_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in loader.SUPPORTED_SUFFIXES
        ]
        signature = []
        for f in sorted(files):
            stat = f.stat()
            signature.append({
                "path": f.name,
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
            })
        return signature

    @staticmethod
    def _build_index_signature() -> dict:
        return {
            "schema_version": INDEX_SCHEMA_VERSION,
            "chunk_strategy": "semantic",
            "chunk_size": config.get("rag.chunk_size", 512),
            "chunk_overlap": config.get("rag.chunk_overlap", 50),
            "embedding_model": config.get("rag.embedding_model", "chinese"),
            "documents": RAGSearchTool._docs_signature(),
        }

    @staticmethod
    def _load_manifest():
        if not MANIFEST_PATH.exists():
            return None
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "schema_version" in data:
                return data
            return {"schema_version": 1, "documents": data.get("documents")}
        except (json.JSONDecodeError, IOError):
            return None

    @staticmethod
    def _save_manifest(signature: dict):
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(signature, f, ensure_ascii=False, indent=2)

    def ensure_indexed(self):
        signature = self._build_index_signature()
        if self._indexed and self._index_signature == signature:
            self.retriever.ensure_bm25_index()
            return

        if self.retriever.collection.count() > 0 and self._load_manifest() == signature:
            self.retriever.ensure_bm25_index()
            self._index_signature = signature
            self._indexed = True
            return

        loader = DocumentLoader()
        chunk_size = config.get("rag.chunk_size", 512)
        chunk_overlap = config.get("rag.chunk_overlap", 50)
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        docs = loader.load(str(DOCS_DIR))
        if docs:
            chunks = chunker.chunk(docs, strategy="semantic")
            self.retriever.rebuild_documents(chunks)
            self._save_manifest(signature)
            logger.info("已索引 %d 个文档切片", len(chunks))
        else:
            self.retriever.collection.clear()
            self._save_manifest(signature)

        self._index_signature = signature
        self._indexed = True

    def execute(self, query: str, top_k: int = 3) -> str:
        self.ensure_indexed()

        results = self.retriever.search_hybrid(query, top_k=top_k * 2)
        if not results:
            return "未找到相关文档"

        reranked = self.reranker.rerank(query, results, top_k=top_k)

        output = ["RAG 检索结果（请基于片段回答，并保留 citation）："]
        for i, (doc, score, meta) in enumerate(reranked, 1):
            source = meta.get("filename", "unknown")
            chunk_id = meta.get("chunk_id", "unknown")
            section = meta.get("section", "")
            citation = meta.get("citation", "%s#%s" % (source, chunk_id))
            heading = "[%d] source=%s chunk_id=%s score=%.2f citation=%s" % (i, source, chunk_id, score, citation)
            if section:
                heading += " section=%s" % section
            output.append("%s\n%s\n" % (heading, doc))

        return "\n---\n".join(output)


class RAGIndexTool(Tool):
    name = "rag_index_stats"
    description = "查看知识库索引的统计信息，包括已索引文档数量等。"
    parameters = {
        "type": "object",
        "properties": {},
    }

    def __init__(self, retriever: Retriever = None):
        self.retriever = retriever or _get_retriever()

    def execute(self) -> str:
        stats = self.retriever.get_stats()
        return (
            "知识库索引统计:\n"
            "  集合名称: %s\n"
            "  文档切片数: %d\n"
            "  BM25 索引: %s" % (
                stats["collection"],
                stats["total_documents"],
                "已就绪" if stats["bm25_ready"] else "未构建",
            )
        )
