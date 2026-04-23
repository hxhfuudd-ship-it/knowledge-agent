"""短期记忆：对话上下文窗口管理，支持 LLM 压缩"""
import logging
from typing import List, Dict, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """滑动窗口管理对话历史，超长时用 LLM 压缩早期对话保留关键信息"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: List[Dict] = []
        self._summary: str = ""
        self._compressor = None

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self._compress_and_trim()

    def _compress_and_trim(self):
        keep = self.max_messages // 2
        old_messages = self.messages[:-keep]
        self.messages = self.messages[-keep:]

        compressor = self._get_compressor()
        if compressor:
            old_text = self._messages_to_text(old_messages)
            prefix = "之前的对话摘要：%s\n\n" % self._summary if self._summary else ""
            self._summary = compressor(prefix + old_text)
            logger.info("对话已压缩，摘要长度: %d", len(self._summary))
        else:
            old_text = self._messages_to_text(old_messages[-4:])
            self._summary = (self._summary + "\n" + old_text).strip()[-500:]

    def _get_compressor(self):
        if self._compressor is not None:
            return self._compressor
        try:
            from ..llm import create_llm_client
            llm = create_llm_client()

            def compress(text: str) -> str:
                resp = llm.chat(
                    messages=[{"role": "user", "content":
                        "请用 2-3 句话压缩以下对话的关键信息（保留数据发现、用户偏好、重要结论）：\n\n%s" % text
                    }],
                    max_tokens=300,
                )
                return resp.text

            self._compressor = compress
            return compress
        except Exception as e:
            logger.warning("LLM 压缩不可用，使用简单截断: %s", e)
            return None

    @property
    def summary(self) -> str:
        return self._summary

    def get_messages(self) -> List[Dict]:
        return deepcopy(self.messages)

    def get_context(self) -> Dict:
        return {
            "summary": self._summary,
            "messages": self.get_messages(),
        }

    def get_summary_context(self) -> str:
        parts = []
        if self._summary:
            parts.append("对话摘要：%s" % self._summary)
        for m in self.messages[-10:]:
            role = "用户" if m["role"] == "user" else "助手"
            content = m["content"] if isinstance(m["content"], str) else str(m["content"])
            parts.append("%s: %s" % (role, content[:200]))
        return "\n".join(parts)

    @staticmethod
    def _messages_to_text(messages: List[Dict]) -> str:
        lines = []
        for m in messages:
            role = "用户" if m["role"] == "user" else "助手"
            content = m["content"] if isinstance(m["content"], str) else str(m["content"])
            lines.append("%s: %s" % (role, content[:300]))
        return "\n".join(lines)

    def clear(self):
        self.messages = []
        self._summary = ""

    def __len__(self):
        return len(self.messages)
