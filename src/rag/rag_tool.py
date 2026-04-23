"""RAG 检索工具：让 Agent 能通过 RAG 检索知识库文档"""
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
        "输入自然语言查询，返回最相关的文档片段。"
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

    def ensure_indexed(self):
        if self._indexed:
            return
        if self.retriever.collection.count() > 0:
            self._indexed = True
            return

        loader = DocumentLoader()
        chunk_size = config.get("rag.chunk_size", 512)
        chunk_overlap = config.get("rag.chunk_overlap", 50)
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        docs = loader.load(str(DOCS_DIR))
        if docs:
            chunks = chunker.chunk(docs, strategy="recursive")
            self.retriever.add_documents(chunks)
            logger.info("已索引 %d 个文档切片", len(chunks))
        self._indexed = True

    def execute(self, query: str, top_k: int = 3) -> str:
        self.ensure_indexed()

        results = self.retriever.search_hybrid(query, top_k=top_k * 2)
        if not results:
            return "未找到相关文档"

        reranked = self.reranker.rerank(query, results, top_k=top_k)

        output = []
        for i, (doc, score, meta) in enumerate(reranked, 1):
            source = meta.get("filename", "unknown")
            output.append("[%d] (来源: %s, 相关度: %.2f)\n%s\n" % (i, source, score, doc))

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
