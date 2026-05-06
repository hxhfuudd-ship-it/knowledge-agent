"""Structured models for the Agent harness."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HarnessLimits:
    """Execution boundaries for one Agent task."""

    max_iterations: int = 3
    min_tool_calls: int = 0
    max_tool_calls: Optional[int] = None
    timeout_ms: Optional[float] = None


@dataclass
class HarnessExpectation:
    """Expected observable behavior for one Agent run."""

    tools: List[str] = field(default_factory=list)
    ordered_tools: List[str] = field(default_factory=list)
    forbidden_tools: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    skill: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)


@dataclass
class HarnessCase:
    """One standardized Agent input for demo, regression, or evaluation."""

    name: str
    query: str
    category: str = "general"
    mode: str = "dry"
    description: str = ""
    goal: str = ""
    success_criteria: List[str] = field(default_factory=list)
    limits: HarnessLimits = field(default_factory=HarnessLimits)
    expectations: HarnessExpectation = field(default_factory=HarnessExpectation)


@dataclass
class HarnessResult:
    """Observable result captured from one Agent run."""

    run_id: str
    name: str
    category: str
    query: str
    mode: str
    status: str
    passed: bool
    goal: str = ""
    success_criteria: List[str] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    response: str = ""
    tools_used: List[str] = field(default_factory=list)
    trajectory: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    skill: Optional[str] = None
    trace: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, bool] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "name": self.name,
            "category": self.category,
            "query": self.query,
            "mode": self.mode,
            "status": self.status,
            "passed": self.passed,
            "goal": self.goal,
            "success_criteria": self.success_criteria,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "response": self.response,
            "tools_used": self.tools_used,
            "trajectory": self.trajectory,
            "artifacts": self.artifacts,
            "skill": self.skill,
            "trace": self.trace,
            "checks": self.checks,
            "violations": self.violations,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }
