"""记忆系统测试"""
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.short_term import ShortTermMemory
from src.memory.episodic import EpisodicMemory
from src.memory.working import WorkingMemory


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


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll memory tests passed!")
