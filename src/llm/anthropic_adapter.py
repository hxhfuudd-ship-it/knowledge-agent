"""Anthropic Claude 适配器"""
import logging
from typing import Optional, Generator
from .base_adapter import BaseAdapter
from .models import LLMResponse, ToolCall

logger = logging.getLogger(__name__)


class AnthropicAdapter(BaseAdapter):

    def __init__(self, model: str):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = model
        self._api_error = anthropic.APIError

    def chat(self, messages, system=None, tools=None, max_tokens=4096) -> LLMResponse:
        kwargs = dict(model=self.model, max_tokens=max_tokens, messages=messages)
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        response = self.client.messages.create(**kwargs)
        return self._normalize(response)

    def chat_stream(self, messages, system=None, tools=None, max_tokens=4096) -> Generator:
        kwargs = dict(model=self.model, max_tokens=max_tokens, messages=messages)
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        with self.client.messages.stream(**kwargs) as stream:
            for event in stream:
                if hasattr(event, "type") and event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        yield {"type": "token", "content": event.delta.text}
            response = stream.get_final_message()

        yield {"type": "final", "response": self._normalize(response)}

    def format_tools(self, tools):
        return tools

    def format_tool_result(self, tool_call_id, content):
        return {"type": "tool_result", "tool_use_id": tool_call_id, "content": content}

    def format_tool_results(self, tool_results):
        return [{"role": "user", "content": tool_results}]

    def build_assistant_message(self, response: LLMResponse):
        return {"role": "assistant", "content": response.raw.content}

    def _normalize(self, response) -> LLMResponse:
        text_parts = [b.text for b in response.content if hasattr(b, "text")]
        tool_calls = [
            ToolCall(id=b.id, name=b.name, input=b.input)
            for b in response.content if b.type == "tool_use"
        ]
        usage = getattr(response, "usage", None)
        usage_dict = {}
        if usage:
            input_tokens = getattr(usage, "input_tokens", 0) or 0
            output_tokens = getattr(usage, "output_tokens", 0) or 0
            usage_dict = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }

        return LLMResponse(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            raw=response,
            usage=usage_dict,
        )
