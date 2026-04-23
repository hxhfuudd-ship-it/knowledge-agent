"""LLM 适配器抽象接口"""
from abc import ABC, abstractmethod
from typing import List, Optional, Generator
from .models import LLMResponse


class BaseAdapter(ABC):

    @abstractmethod
    def chat(self, messages: list, system: Optional[str] = None,
             tools: Optional[list] = None, max_tokens: int = 4096) -> LLMResponse:
        ...

    @abstractmethod
    def chat_stream(self, messages: list, system: Optional[str] = None,
                    tools: Optional[list] = None, max_tokens: int = 4096) -> Generator:
        ...

    @abstractmethod
    def format_tools(self, tools: list) -> list:
        ...

    @abstractmethod
    def format_tool_result(self, tool_call_id: str, content: str) -> dict:
        ...

    @abstractmethod
    def build_assistant_message(self, response: LLMResponse) -> dict:
        ...

    def format_tool_results(self, tool_results: list) -> list:
        """将多个工具结果打包为消息列表（不同 provider 格式不同）"""
        return tool_results
