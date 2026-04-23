"""Tool 基类：所有工具继承此类，定义统一的工具接口"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Tool(ABC):
    """工具基类 - Agent 通过 tool use 调用的原子操作

    子类通过类属性定义 name/description/parameters，无需用 @property。
    """

    name: str = ""
    description: str = ""
    parameters: dict = {}

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
