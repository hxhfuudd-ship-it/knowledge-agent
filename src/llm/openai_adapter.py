"""OpenAI 兼容适配器（DeepSeek / Kimi / OpenAI 等）"""
import json
import logging
from typing import Optional, Generator
from .base_adapter import BaseAdapter
from .models import LLMResponse, ToolCall

logger = logging.getLogger(__name__)

STOP_REASON_MAP = {"stop": "end_turn", "tool_calls": "tool_use", "length": "max_tokens"}


class OpenAIAdapter(BaseAdapter):

    def __init__(self, model: str, base_url: str = None, api_key: str = None):
        try:
            import openai
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
        kwargs = {}
        if base_url:
            kwargs["base_url"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        self.client = openai.OpenAI(**kwargs)
        self.model = model

    def chat(self, messages, system=None, tools=None, max_tokens=4096) -> LLMResponse:
        msgs = self._prepend_system(messages, system)
        kwargs = dict(model=self.model, max_tokens=max_tokens, messages=msgs)
        if tools:
            kwargs["tools"] = tools
        response = self.client.chat.completions.create(**kwargs)
        return self._normalize(response)

    def chat_stream(self, messages, system=None, tools=None, max_tokens=4096) -> Generator:
        msgs = self._prepend_system(messages, system)
        kwargs = dict(model=self.model, max_tokens=max_tokens, messages=msgs, stream=True)
        if tools:
            kwargs["tools"] = tools

        collected_text = ""
        tool_calls_acc = {}
        finish_reason = "stop"

        for chunk in self.client.chat.completions.create(**kwargs):
            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                continue

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            delta = choice.delta
            if delta and delta.content:
                collected_text += delta.content
                yield {"type": "token", "content": delta.content}

            if delta and delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id:
                        tool_calls_acc[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_acc[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments

        tool_calls = []
        for idx in sorted(tool_calls_acc):
            tc = tool_calls_acc[idx]
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(id=tc["id"], name=tc["name"], input=args))

        stop = STOP_REASON_MAP.get(finish_reason, finish_reason)
        resp = LLMResponse(text=collected_text, tool_calls=tool_calls, stop_reason=stop, usage={})
        yield {"type": "final", "response": resp}

    def format_tools(self, tools):
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

    def format_tool_result(self, tool_call_id, content):
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}

    def format_tool_results(self, tool_results):
        return tool_results

    def build_assistant_message(self, response: LLMResponse):
        msg = {"role": "assistant", "content": response.text or None}
        if response.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.input, ensure_ascii=False)},
                }
                for tc in response.tool_calls
            ]
        return msg

    @staticmethod
    def _prepend_system(messages, system):
        if not system:
            return messages
        return [{"role": "system", "content": system}] + messages

    def _normalize(self, response) -> LLMResponse:
        choice = response.choices[0]
        msg = choice.message
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, input=args))
        stop = STOP_REASON_MAP.get(choice.finish_reason, choice.finish_reason or "end_turn")
        usage = getattr(response, "usage", None)
        usage_dict = {}
        if usage:
            usage_dict = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                "total_tokens": getattr(usage, "total_tokens", 0) or 0,
            }

        return LLMResponse(
            text=msg.content or "",
            tool_calls=tool_calls,
            stop_reason=stop,
            raw=response,
            usage=usage_dict,
        )
