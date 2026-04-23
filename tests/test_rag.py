"""RAG 模块测试"""
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.loader import Document
from src.rag.chunker import TextChunker
from src.rag.vector_store import SimpleVectorStore
from src.rag.embedder import Embedder


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


def test_embedder_backend():
    emb = Embedder("chinese")
    vecs = emb.embed_texts(["测试文本"])
    assert len(vecs) == 1
    assert len(vecs[0]) > 0
    print("  OK  embedder backend=%s dim=%d" % (emb.backend, len(vecs[0])))


def test_embedder_query():
    emb = Embedder("chinese")
    vec = emb.embed_query("你好世界")
    assert isinstance(vec, list)
    assert len(vec) > 0
    print("  OK  embedder query")


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll RAG tests passed!")
