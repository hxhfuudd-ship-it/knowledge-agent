"""Validation helpers for harness results."""
from typing import Dict, List, Optional


def contains_all_keywords(text: str, keywords: List[str]) -> bool:
    return all(keyword in text for keyword in keywords)


def contains_all_tools(actual_tools: List[str], expected_tools: List[str]) -> bool:
    return all(tool in actual_tools for tool in expected_tools)


def contains_sources(response: str, trace: Dict, expected_sources: List[str]) -> bool:
    if not expected_sources:
        return True

    text = response
    for event in trace.get("events", []):
        text += "\n" + str(event.get("output_preview", ""))

    return all(source in text for source in expected_sources)


def skill_matches(actual_skill: Optional[str], expected_skill: Optional[str]) -> bool:
    return not expected_skill or actual_skill == expected_skill


def validate_result(response: str, tools_used: List[str], trace: Dict, actual_skill: Optional[str], expectations) -> Dict[str, bool]:
    return {
        "tools": contains_all_tools(tools_used, expectations.tools),
        "keywords": contains_all_keywords(response, expectations.keywords),
        "sources": contains_sources(response, trace, expectations.sources),
        "skill": skill_matches(actual_skill, expectations.skill),
    }

