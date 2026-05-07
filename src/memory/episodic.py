"""情景记忆：历史交互的摘要记录"""
import json
import logging
import time
from typing import List, Dict
from pathlib import Path
from .. import config

logger = logging.getLogger(__name__)

EPISODIC_PATH = Path(__file__).parent.parent.parent / "data" / "episodic_memory.json"


class EpisodicMemory:
    """记录历史交互的摘要，如"上次分析了销售数据，发现Q3下降" """

    def __init__(self, namespace: str = None):
        self.namespace = namespace or config.get("memory.namespace", "default")
        self.episodes: List[Dict] = []
        self._load()

    def add_episode(self, summary: str, details: dict = None):
        episode = {
            "summary": summary,
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "namespace": self.namespace,
            "details": details or {},
        }
        self.episodes.append(episode)
        self._save()

    def get_recent(self, n: int = 5) -> List[Dict]:
        return [ep for ep in self.episodes if ep.get("namespace", "default") == self.namespace][-n:]

    def get_context_string(self, n: int = 3) -> str:
        recent = self.get_recent(n)
        if not recent:
            return ""
        lines = ["以下是之前的交互记录："]
        for ep in recent:
            lines.append("- [%s] %s" % (ep["time_str"], ep["summary"]))
        return "\n".join(lines)

    def search(self, keyword: str) -> List[Dict]:
        return [ep for ep in self.episodes if ep.get("namespace", "default") == self.namespace and keyword in ep["summary"]]

    def count(self) -> int:
        return len(self.get_recent(len(self.episodes)))

    def clear(self):
        self.episodes = [ep for ep in self.episodes if ep.get("namespace", "default") != self.namespace]
        self._save()

    def _save(self):
        try:
            EPISODIC_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(EPISODIC_PATH, "w", encoding="utf-8") as f:
                json.dump(self.episodes, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error("情景记忆保存失败: %s", e)

    def _load(self):
        if not EPISODIC_PATH.exists():
            return
        try:
            with open(EPISODIC_PATH, "r", encoding="utf-8") as f:
                self.episodes = json.load(f)
            for episode in self.episodes:
                episode.setdefault("namespace", "default")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("情景记忆加载失败，将使用空记忆: %s", e)
            self.episodes = []
