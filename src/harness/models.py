"""Structured models for the Agent harness."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HarnessExpectation:
    """Expected observable behavior for one Agent run."""

    tools: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    skill: Optional[str] = None


@dataclass
class HarnessCase:
    """One standardized Agent input for demo, regression, or evaluation."""

    name: str
    query: str
    category: str = "general"
    mode: str = "dry"
    description: str = ""
    expectations: HarnessExpectation = field(default_factory=HarnessExpectation)


@dataclass
class HarnessResult:
    """Observable result captured from one Agent run."""

    name: str
    category: str
    query: str
    mode: str
    passed: bool
    response: str = ""
    tools_used: List[str] = field(default_factory=list)
    skill: Optional[str] = None
    trace: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, bool] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "query": self.query,
            "mode": self.mode,
            "passed": self.passed,
            "response": self.response,
            "tools_used": self.tools_used,
            "skill": self.skill,
            "trace": self.trace,
            "checks": self.checks,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }

