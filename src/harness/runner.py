"""Standardized Agent runner for demos, regression checks, and live evaluation."""
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.llm.models import LLMResponse, ToolCall
from src.tools.base import Tool

from .models import HarnessCase, HarnessExpectation, HarnessResult
from .validators import validate_result


DEFAULT_CASES_PATH = Path(__file__).parent.parent.parent / "data" / "harness_cases.yaml"


class ScriptedLLM:
    """Small deterministic LLM for dry-run harness cases.

    It gives the harness a stable execution environment: no network, no real model,
    but still exercises the Agent's tool-call loop and trace collection.
    """

    model = "scripted-harness-llm"

    def __init__(self, tool_calls: List[Dict[str, Any]], final_response: str):
        self.tool_calls = tool_calls
        self.final_response = final_response
        self.calls = 0

    def chat(self, messages, system=None, tools=None, max_tokens=None):
        self.calls += 1
        if self.calls == 1 and self.tool_calls:
            calls = [
                ToolCall(
                    id=item.get("id", "call_%d" % index),
                    name=item["name"],
                    input=item.get("input", {}),
                )
                for index, item in enumerate(self.tool_calls, 1)
            ]
            return LLMResponse(
                text="",
                tool_calls=calls,
                stop_reason="tool_use",
                usage={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            )

        return LLMResponse(
            text=self.final_response,
            stop_reason="end_turn",
            usage={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
        )

    @staticmethod
    def build_assistant_message(response):
        return {"role": "assistant", "content": response.text}

    @staticmethod
    def format_tool_result(tool_call_id, content):
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}

    @staticmethod
    def format_tool_results(tool_results):
        return tool_results


class NoopShortTermMemory:
    summary = ""

    def __init__(self):
        self.messages = []

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})

    def clear(self):
        self.messages = []

    def __len__(self):
        return len(self.messages)


class NoopLongTermMemory:
    def recall(self, query, top_k=3):
        return []


class NoopEpisodicMemory:
    def __init__(self):
        self.episodes = []

    def get_context_string(self, n=3):
        return ""

    def add_episode(self, summary, details=None):
        self.episodes.append({"summary": summary, "details": details or {}})


class NoopWorkingMemory:
    def __init__(self):
        self.steps = []

    def get_task_context(self):
        return ""

    def add_step(self, step, result=None):
        self.steps.append({"step": step, "result": result})

    def clear(self):
        self.steps = []


class ScriptedTool(Tool):
    """Dry-run tool that records the intended tool trajectory without side effects."""

    parameters = {"type": "object", "properties": {}}

    def __init__(self, name: str, output: str = ""):
        self.name = name
        self.description = "Scripted harness tool for dry-run trajectory validation."
        self.output = output or "Harness scripted output from %s." % name

    def execute(self, **kwargs) -> str:
        return self.output


def _parse_expectations(raw: Dict[str, Any]) -> HarnessExpectation:
    raw = raw or {}
    return HarnessExpectation(
        tools=list(raw.get("tools", [])),
        keywords=list(raw.get("keywords", [])),
        sources=list(raw.get("sources", [])),
        skill=raw.get("skill"),
    )


def _parse_case(raw: Dict[str, Any]) -> HarnessCase:
    return HarnessCase(
        name=raw.get("name", ""),
        query=raw.get("query", ""),
        category=raw.get("category", "general"),
        mode=raw.get("mode", "dry"),
        description=raw.get("description", ""),
        expectations=_parse_expectations(raw.get("expect")),
    )


def load_cases(path: Optional[str] = None) -> List[Dict[str, Any]]:
    cases_path = Path(path) if path else DEFAULT_CASES_PATH
    with open(cases_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data.get("cases", [])


class HarnessRunner:
    """Run Agent cases and capture standardized observable outputs."""

    def __init__(self, agent_factory=None):
        self.agent_factory = agent_factory

    def validate_cases(self, raw_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        details = []
        passed = 0
        for raw in raw_cases:
            missing = [key for key in ("name", "query") if not raw.get(key)]
            expect = raw.get("expect", {})
            ok = (
                not missing
                and isinstance(expect.get("tools", []), list)
                and isinstance(expect.get("keywords", []), list)
                and isinstance(expect.get("sources", []), list)
            )
            if ok:
                passed += 1
            details.append({
                "name": raw.get("name", ""),
                "category": raw.get("category", "general"),
                "query": raw.get("query", ""),
                "mode": raw.get("mode", "dry"),
                "passed": ok,
                "error": "缺少或无效字段: %s" % ", ".join(missing) if missing else "",
            })
        return self._summary(details)

    def run_cases(self, raw_cases: List[Dict[str, Any]], live: bool = False) -> Dict[str, Any]:
        results = []
        for raw in raw_cases:
            case = _parse_case(raw)
            result = self.run_case(case, raw.get("script"), live=live)
            results.append(result.to_dict())
        return self._summary(results)

    def run_case(self, case: HarnessCase, script: Optional[Dict[str, Any]] = None, live: bool = False) -> HarnessResult:
        start = time.perf_counter()
        try:
            agent = self._build_agent(case, script, live=live)
            output = agent.chat(case.query)
            response = output.get("response", "")
            tools_used = [tool_call.get("tool", "") for tool_call in output.get("tool_calls", [])]
            trace = output.get("trace", {})
            skill = output.get("skill")
            checks = validate_result(response, tools_used, trace, skill, case.expectations)
            passed = all(checks.values())
            agent.reset()
            return HarnessResult(
                name=case.name,
                category=case.category,
                query=case.query,
                mode="live" if live else "dry",
                passed=passed,
                response=response,
                tools_used=tools_used,
                skill=skill,
                trace=trace,
                checks=checks,
                latency_ms=round((time.perf_counter() - start) * 1000, 1),
            )
        except Exception as exc:
            return HarnessResult(
                name=case.name,
                category=case.category,
                query=case.query,
                mode="live" if live else "dry",
                passed=False,
                latency_ms=round((time.perf_counter() - start) * 1000, 1),
                error=str(exc),
            )

    def _build_agent(self, case: HarnessCase, script: Optional[Dict[str, Any]], live: bool):
        if live:
            if self.agent_factory:
                return self.agent_factory()
            from src.agent.core import Agent
            return Agent()

        from src.agent.core import Agent
        from src.observability import TraceRecorder
        from src.skills.base import SkillRegistry
        from src.tools.base import ToolRegistry

        script = script or {}
        final_response = script.get("final_response") or "Harness dry-run response: %s" % case.name
        tool_calls = script.get("tool_calls", [])
        tool_outputs = script.get("tool_outputs", {})

        agent = Agent.__new__(Agent)
        agent.llm = ScriptedLLM(tool_calls=tool_calls, final_response=final_response)
        agent.max_iterations = 3
        agent.registry = ToolRegistry()
        for tool_call in tool_calls:
            name = tool_call.get("name", "")
            if name:
                agent.registry.register(ScriptedTool(name=name, output=tool_outputs.get(name, "")))
        agent.skill_registry = SkillRegistry(match_strategy="keyword")
        agent.conversation = []
        agent.tool_call_log = []
        agent.trace = TraceRecorder()
        agent.short_term = NoopShortTermMemory()
        agent.long_term = NoopLongTermMemory()
        agent.episodic = NoopEpisodicMemory()
        agent.working = NoopWorkingMemory()
        return agent

    @staticmethod
    def _summary(details: List[Dict[str, Any]]) -> Dict[str, Any]:
        passed = sum(1 for item in details if item.get("passed"))
        total = len(details)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total else 0,
            "details": details,
        }
