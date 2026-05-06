"""Validation helpers for harness results."""
from typing import Dict, List, Optional, Tuple


def contains_all_keywords(text: str, keywords: List[str]) -> bool:
    return all(keyword in text for keyword in keywords)


def contains_all_tools(actual_tools: List[str], expected_tools: List[str]) -> bool:
    return all(tool in actual_tools for tool in expected_tools)


def excludes_forbidden_tools(actual_tools: List[str], forbidden_tools: List[str]) -> bool:
    return not any(tool in actual_tools for tool in forbidden_tools)


def follows_ordered_tools(actual_tools: List[str], expected_order: List[str]) -> bool:
    if not expected_order:
        return True

    cursor = 0
    for tool in actual_tools:
        if tool == expected_order[cursor]:
            cursor += 1
            if cursor == len(expected_order):
                return True
    return False


def stays_within_tool_limits(actual_tools: List[str], min_calls: int = 0, max_calls: Optional[int] = None) -> bool:
    count = len(actual_tools)
    if count < min_calls:
        return False
    if max_calls is not None and count > max_calls:
        return False
    return True


def stays_within_latency_limit(latency_ms: float, timeout_ms: Optional[float]) -> bool:
    return timeout_ms is None or latency_ms <= timeout_ms


def contains_sources(response: str, trace: Dict, expected_sources: List[str]) -> bool:
    if not expected_sources:
        return True

    text = response
    for event in trace.get("events", []):
        text += "\n" + str(event.get("output_preview", ""))

    return all(source in text for source in expected_sources)


def skill_matches(actual_skill: Optional[str], expected_skill: Optional[str]) -> bool:
    return not expected_skill or actual_skill == expected_skill


def artifact_expectations_met(actual_artifacts: List[Dict], expected_artifacts: List[str]) -> bool:
    if not expected_artifacts:
        return True

    artifact_text = "\n".join(
        str(artifact.get("name") or artifact.get("path") or artifact)
        for artifact in actual_artifacts
    )
    return all(expected in artifact_text for expected in expected_artifacts)


def _violation_messages(checks: Dict[str, bool]) -> List[str]:
    labels = {
        "tools": "缺少期望工具调用",
        "ordered_tools": "工具调用顺序不符合任务轨迹",
        "forbidden_tools": "调用了禁止工具",
        "tool_call_limits": "工具调用次数超出边界",
        "keywords": "最终回答缺少关键内容",
        "sources": "结果或 trace 缺少期望来源",
        "skill": "未匹配到期望 skill",
        "artifacts": "缺少期望交付物",
        "latency": "执行耗时超过限制",
    }
    return [labels.get(name, name) for name, passed in checks.items() if not passed]


def validate_result(
    response: str,
    tools_used: List[str],
    trace: Dict,
    actual_skill: Optional[str],
    expectations,
    limits=None,
    artifacts: Optional[List[Dict]] = None,
    latency_ms: float = 0.0,
) -> Tuple[Dict[str, bool], List[str]]:
    checks = {
        "tools": contains_all_tools(tools_used, expectations.tools),
        "ordered_tools": follows_ordered_tools(tools_used, expectations.ordered_tools),
        "forbidden_tools": excludes_forbidden_tools(tools_used, expectations.forbidden_tools),
        "tool_call_limits": stays_within_tool_limits(
            tools_used,
            min_calls=getattr(limits, "min_tool_calls", 0),
            max_calls=getattr(limits, "max_tool_calls", None),
        ),
        "keywords": contains_all_keywords(response, expectations.keywords),
        "sources": contains_sources(response, trace, expectations.sources),
        "skill": skill_matches(actual_skill, expectations.skill),
        "artifacts": artifact_expectations_met(artifacts or [], expectations.artifacts),
        "latency": stays_within_latency_limit(latency_ms, getattr(limits, "timeout_ms", None)),
    }
    return checks, _violation_messages(checks)
