"""记忆系统测试"""
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.short_term import ShortTermMemory
from src.memory.episodic import EpisodicMemory
from src.memory.working import WorkingMemory
from src.memory.long_term import LongTermMemory


class FakeEmbedder:
    def embed_query(self, text):
        return self.embed_texts([text])[0]

    def embed_texts(self, texts):
        vectors = []
        for text in texts:
            vectors.append([
                1.0 if "中文" in text or "回复" in text else 0.0,
                1.0 if "英文" in text else 0.0,
                1.0 if "偏好" in text else 0.0,
            ])
        return vectors


def test_short_term():
    mem = ShortTermMemory(max_messages=3)
    mem.add("user", "hello")
    mem.add("assistant", "hi")
    mem.add("user", "how are you")
    mem.add("assistant", "fine")
    assert len(mem) <= 3
    msgs = mem.get_messages()
    assert msgs[-1]["content"] == "fine"
    mem.clear()
    assert len(mem) == 0
    print("  OK  short term memory (sliding window)")


def test_episodic():
    mem = EpisodicMemory()
    initial = len(mem.episodes)
    mem.add_episode("测试交互1", {"tools_used": ["sql_query"]})
    mem.add_episode("测试交互2", {"tools_used": ["rag_search"]})
    assert len(mem.episodes) >= initial + 2
    recent = mem.get_recent(5)
    assert len(recent) >= 2
    ctx = mem.get_context_string(n=2)
    assert "测试交互" in ctx
    print("  OK  episodic memory (add/get_recent/context)")


def test_working():
    mem = WorkingMemory()
    mem.set_task("分析销售趋势")
    mem.add_step("查询订单表", "返回 100 条记录")
    mem.add_step("计算月度汇总", "生成 12 个月数据")
    ctx = mem.get_task_context()
    assert "分析销售趋势" in ctx
    assert "查询订单表" in ctx
    mem.clear()
    assert mem.get_task_context() == ""
    print("  OK  working memory (task/steps/clear)")


def test_long_term_namespace_and_filters():
    store_path = os.path.join(tempfile.mkdtemp(), "memory.json")
    embedder = FakeEmbedder()

    mem_a = LongTermMemory(namespace="project_a", persist_path=store_path, embedder=embedder)
    mem_b = LongTermMemory(namespace="project_b", persist_path=store_path, embedder=embedder)
    mem_a.save("用户偏好：默认使用中文回复", category="preference", importance=0.9, tags=["preference"])
    mem_b.save("用户偏好：默认使用英文回复", category="preference", importance=0.9, tags=["preference"])

    recall_a = mem_a.recall("回复偏好", top_k=5, category="preference", tags=["preference"])
    recall_b = mem_b.recall("回复偏好", top_k=5, category="preference", tags=["preference"])

    assert recall_a and "中文" in recall_a[0]["content"]
    assert recall_b and "英文" in recall_b[0]["content"]
    assert all(item["namespace"] == "project_a" for item in recall_a)
    assert all(item["namespace"] == "project_b" for item in recall_b)
    print("  OK  long term memory namespace/filtering")


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll memory tests passed!")
