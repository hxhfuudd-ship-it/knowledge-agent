"""Lightweight observability primitives for Agent runs."""
import time
from typing import Any, Dict, List, Optional


class TraceRecorder:
    """Collects per-run events and aggregate metrics."""

    def __init__(self):
        self.started_at = time.time()
        self._events: List[Dict[str, Any]] = []

    def add_event(self, event_type: str, name: str, duration_ms: float = 0,
                  metadata: Optional[dict] = None, error: Optional[str] = None):
        event = {
            "type": event_type,
            "name": name,
            "duration_ms": round(duration_ms, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": metadata or {},
        }
        if error:
            event["error"] = error
        self._events.append(event)

    def add_llm_call(self, model: str, stop_reason: str, duration_ms: float, usage: Optional[dict] = None):
        self.add_event(
            "llm",
            model or "unknown",
            duration_ms=duration_ms,
            metadata={"stop_reason": stop_reason, "usage": usage or {}},
        )

    def add_tool_call(self, name: str, duration_ms: float, success: bool,
                      input_data: Optional[dict] = None, output: str = "",
                      policy: Optional[dict] = None):
        self.add_event(
            "tool",
            name,
            duration_ms=duration_ms,
            metadata={
                "success": success,
                "input": input_data or {},
                "output_preview": str(output)[:300],
                "policy": policy or {},
            },
        )

    def add_error(self, name: str, error: str, duration_ms: float = 0):
        self.add_event("error", name, duration_ms=duration_ms, error=error)

    def summary(self) -> Dict[str, Any]:
        llm_events = [e for e in self._events if e["type"] == "llm"]
        tool_events = [e for e in self._events if e["type"] == "tool"]
        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        for event in llm_events:
            usage = event.get("metadata", {}).get("usage", {}) or {}
            total_usage["input_tokens"] += int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
            total_usage["output_tokens"] += int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
            total_usage["total_tokens"] += int(usage.get("total_tokens") or 0)

        if total_usage["total_tokens"] == 0:
            total_usage["total_tokens"] = total_usage["input_tokens"] + total_usage["output_tokens"]

        return {
            "total_duration_ms": round((time.time() - self.started_at) * 1000, 2),
            "llm_calls": len(llm_events),
            "tool_calls": len(tool_events),
            "tool_errors": sum(1 for e in tool_events if not e.get("metadata", {}).get("success", False)),
            "tokens": total_usage,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"summary": self.summary(), "events": list(self._events)}
