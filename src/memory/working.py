"""工作记忆：当前任务的中间状态"""
from typing import Any, Dict, Optional


class WorkingMemory:
    """保存当前任务执行过程中的中间状态"""

    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._task_context: Dict[str, Any] = {
            "current_task": None,
            "steps_completed": [],
            "intermediate_results": {},
        }

    def set(self, key: str, value: Any):
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_task(self, task_description: str):
        self._task_context["current_task"] = task_description
        self._task_context["steps_completed"] = []
        self._task_context["intermediate_results"] = {}

    def add_step(self, step: str, result: Any = None):
        self._task_context["steps_completed"].append(step)
        if result is not None:
            self._task_context["intermediate_results"][step] = result

    def get_task_context(self) -> str:
        """生成当前任务上下文描述"""
        ctx = self._task_context
        if not ctx["current_task"]:
            return ""

        lines = [f"当前任务: {ctx['current_task']}"]
        if ctx["steps_completed"]:
            lines.append("已完成步骤:")
            for s in ctx["steps_completed"]:
                lines.append(f"  - {s}")
        if ctx["intermediate_results"]:
            lines.append("中间结果:")
            for k, v in ctx["intermediate_results"].items():
                val_str = str(v)[:200]
                lines.append(f"  {k}: {val_str}")
        return "\n".join(lines)

    def clear(self):
        self._state.clear()
        self._task_context = {
            "current_task": None,
            "steps_completed": [],
            "intermediate_results": {},
        }
