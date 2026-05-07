from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .episodic import EpisodicMemory
from .working import WorkingMemory


def build_memory_bundle(namespace: str = None, short_term_max_messages: int = 20):
    """构建同一 namespace 下的四层记忆，供 Agent / UI / 测试统一使用。"""
    return {
        "short_term": ShortTermMemory(max_messages=short_term_max_messages, namespace=namespace),
        "long_term": LongTermMemory(namespace=namespace),
        "episodic": EpisodicMemory(namespace=namespace),
        "working": WorkingMemory(namespace=namespace),
    }

__all__ = [
    "ShortTermMemory",
    "LongTermMemory",
    "EpisodicMemory",
    "WorkingMemory",
    "build_memory_bundle",
]
