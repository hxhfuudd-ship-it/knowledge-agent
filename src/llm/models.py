"""标准化 LLM 响应模型"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    text: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    raw: object = None

    @property
    def has_tool_calls(self) -> bool:
        return self.stop_reason == "tool_use"
