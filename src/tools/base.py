"""Tool 基类：所有工具继承此类，定义统一的工具接口"""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ToolPolicy:
    """工具权限策略 - Agent runtime 用它做风险判断和执行审计。

    Tool schema 是给模型看的“如何调用”；ToolPolicy 是给 Agent runtime
    看的“是否应该调用、是否需要确认、调用后如何审计”。
    """

    risk_level: str = "medium"  # low | medium | high
    requires_confirmation: bool = False
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    external_access: bool = False
    allowed_scopes: Tuple[str, ...] = ()
    description: str = ""

    def __post_init__(self):
        if self.risk_level not in {"low", "medium", "high"}:
            raise ValueError("risk_level must be one of: low, medium, high")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["allowed_scopes"] = list(self.allowed_scopes)
        return data

    def to_mcp_annotations(self) -> dict:
        """转换为 MCP ToolAnnotations 风格的行为提示。

        MCP annotations 是 hint，不应替代本地权限校验；本项目仍以
        ToolPolicy 作为可信 runtime 策略。
        """
        return {
            "readOnlyHint": self.read_only,
            "destructiveHint": self.destructive,
            "idempotentHint": self.idempotent,
            "openWorldHint": self.external_access,
        }


class Tool(ABC):
    """工具基类 - Agent 通过 tool use 调用的原子操作

    子类通过类属性定义 name/description/parameters，无需用 @property。
    """

    name: str = ""
    description: str = ""
    parameters: dict = {}
    policy: ToolPolicy = ToolPolicy()

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行工具逻辑，返回字符串结果"""
        ...

    def to_claude_tool(self) -> dict:
        """转换为 Claude API tool use 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def policy_dict(self) -> dict:
        return self.policy.to_dict()


class ToolRegistry:
    """工具注册中心：管理所有可用工具"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def to_claude_tools(self) -> List[dict]:
        return [t.to_claude_tool() for t in self._tools.values()]

    def list_tool_policies(self) -> List[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "policy": tool.policy_dict(),
            }
            for tool in self._tools.values()
        ]
