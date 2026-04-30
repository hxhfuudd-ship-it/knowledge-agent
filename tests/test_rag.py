"""RAG 模块测试"""
import sys
import tempfile
import os
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.loader import Document
from src.rag.chunker import TextChunker
from src.rag.vector_store import SimpleVectorStore
from src.rag.embedder import Embedder
from src.rag.retriever import Retriever


def _with_hash_fallback(fn):
    original_local = Embedder._try_init_local
    original_voyage = Embedder._try_init_voyage
    try:
        Embedder._try_init_local = lambda self: False
        Embedder._try_init_voyage = lambda self: False
        return fn()
    finally:
        Embedder._try_init_local = original_local
        Embedder._try_init_voyage = original_voyage


def test_chunker_fixed():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    doc = Document(content="这是一段测试文本。" * 20, metadata={"source": "test"})
    chunks = chunker.chunk([doc], strategy="fixed")
    assert len(chunks) > 1
    assert all(len(c.content) <= 60 for c in chunks)
    print("  OK  chunker fixed strategy (%d chunks)" % len(chunks))


def test_chunker_recursive():
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)
    doc = Document(
        content="第一段内容。\n\n第二段内容。\n\n第三段内容，这段比较长。" * 5,
        metadata={"source": "test"},
    )
    chunks = chunker.chunk([doc], strategy="recursive")
    assert len(chunks) >= 1
    print("  OK  chunker recursive strategy (%d chunks)" % len(chunks))


def test_vector_store():
    path = os.path.join(tempfile.mkdtemp(), "test_store.json")
    store = SimpleVectorStore(path)
    store.add(
        ids=["doc1"], documents=["hello"],
        embeddings=[[0.1, 0.2, 0.3]], metadatas=[{"text": "hello"}],
    )
    store.add(
        ids=["doc2"], documents=["world"],
        embeddings=[[0.3, 0.2, 0.1]], metadatas=[{"text": "world"}],
    )
    results = store.query(query_embedding=[0.1, 0.2, 0.3], n_results=2)
    docs = results["documents"][0]
    assert len(docs) == 2
    assert docs[0] == "hello"
    store.clear()
    assert store.count() == 0
    print("  OK  vector store add/query/clear")


def test_retriever_rebuilds_bm25_from_store():
    try:
        import rank_bm25  # noqa: F401
    except ImportError:
        print("  SKIP retriever bm25 rebuild (rank_bm25 not installed)")
        return

    path = os.path.join(tempfile.mkdtemp(), "test_store.json")
    retriever = Retriever()
    retriever._store = SimpleVectorStore(path)
    retriever.collection.add(
        ids=["doc1", "doc2", "doc3"],
        documents=["复购率 计算 方法", "销售额 统计 口径", "客户 等级 定义"],
        embeddings=[[0.1, 0.2, 0.3], [0.2, 0.1, 0.3], [0.3, 0.1, 0.2]],
        metadatas=[{"filename": "rules.md"}, {"filename": "sales.md"}, {"filename": "customer.md"}],
    )

    assert retriever.get_stats()["bm25_ready"] is False
    retriever.ensure_bm25_index()
    assert retriever.get_stats()["bm25_ready"] is True
    assert retriever.search_bm25("复购率", top_k=1)
    print("  OK  retriever rebuilds BM25 from persisted store")


def test_embedder_backend():
    def run():
        emb = Embedder("chinese")
        vecs = emb.embed_texts(["测试文本"])
        assert emb.backend == "hash"
        return emb, vecs

    emb, vecs = _with_hash_fallback(run)
    assert len(vecs) == 1
    assert len(vecs[0]) > 0
    print("  OK  embedder backend=%s dim=%d" % (emb.backend, len(vecs[0])))


def test_embedder_query():
    def run():
        emb = Embedder("chinese")
        return emb.embed_query("你好世界")

    vec = _with_hash_fallback(run)
    assert isinstance(vec, list)
    assert len(vec) > 0
    print("  OK  embedder query")


@pytest.mark.embedding
@pytest.mark.skipif(
    os.environ.get("RUN_EMBEDDING_TESTS") != "1",
    reason="set RUN_EMBEDDING_TESTS=1 to enable real embedding model test",
)
def test_real_embedder_optional():
    emb = Embedder("chinese")
    vec = emb.embed_query("真实模型可用性测试")
    assert isinstance(vec, list)
    assert len(vec) > 0
    print("  OK  real embedder backend=%s dim=%d" % (emb.backend, len(vec)))


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll RAG tests passed!")
