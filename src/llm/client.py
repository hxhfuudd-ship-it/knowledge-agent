"""LLM 客户端门面 + 工厂函数"""
import logging
import os
from typing import Optional
from .base_adapter import BaseAdapter
from .models import LLMResponse
from .. import config

logger = logging.getLogger(__name__)


class LLMClient:

    def __init__(self, adapter: BaseAdapter, model: str):
        self.adapter = adapter
        self.model = model

    def chat(self, messages, system=None, tools=None, max_tokens=None) -> LLMResponse:
        max_tokens = max_tokens or config.get("llm.max_tokens", 4096)
        formatted_tools = self.adapter.format_tools(tools) if tools else None
        return self.adapter.chat(messages, system=system, tools=formatted_tools, max_tokens=max_tokens)

    def chat_stream(self, messages, system=None, tools=None, max_tokens=None):
        max_tokens = max_tokens or config.get("llm.max_tokens", 4096)
        formatted_tools = self.adapter.format_tools(tools) if tools else None
        yield from self.adapter.chat_stream(messages, system=system, tools=formatted_tools, max_tokens=max_tokens)

    def format_tool_result(self, tool_call_id: str, content: str) -> dict:
        return self.adapter.format_tool_result(tool_call_id, content)

    def format_tool_results(self, tool_results: list) -> list:
        return self.adapter.format_tool_results(tool_results)

    def build_assistant_message(self, response: LLMResponse) -> dict:
        return self.adapter.build_assistant_message(response)


def create_llm_client(provider=None, model=None, **kwargs) -> LLMClient:
    provider = provider or config.get("llm.provider", "anthropic")
    model = model or config.get("llm.model", "claude-sonnet-4-20250514")

    if provider == "anthropic":
        from .anthropic_adapter import AnthropicAdapter
        adapter = AnthropicAdapter(model=model)
    elif provider == "openai":
        from .openai_adapter import OpenAIAdapter
        base_url = kwargs.get("base_url") or config.get("llm.base_url", "")
        api_key_env = config.get("llm.api_key_env", "")
        api_key = kwargs.get("api_key") or (os.environ.get(api_key_env) if api_key_env else None)
        adapter = OpenAIAdapter(model=model, base_url=base_url or None, api_key=api_key)
    else:
        raise ValueError("未知 LLM provider: %s（支持 anthropic / openai）" % provider)

    logger.info("LLM 客户端初始化: provider=%s, model=%s", provider, model)
    return LLMClient(adapter=adapter, model=model)
