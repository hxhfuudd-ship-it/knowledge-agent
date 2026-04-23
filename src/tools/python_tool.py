"""Python 代码执行工具：在受限沙箱中执行 Python 代码片段"""
import io
import re
import contextlib
import logging
from .base import Tool

logger = logging.getLogger(__name__)

FORBIDDEN_MODULES = {"os", "sys", "subprocess", "shutil", "pathlib", "socket", "http", "importlib"}
FORBIDDEN_BUILTINS = {"exec", "eval", "compile", "__import__", "open", "input", "breakpoint"}


class PythonTool(Tool):
    name = "python_exec"
    description = (
        "执行 Python 代码片段并返回输出。适合数据处理、格式转换、简单计算等。\n"
        "限制：不能访问文件系统、网络、系统命令。可用库：math、statistics、json、re、datetime、collections。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "要执行的 Python 代码",
            }
        },
        "required": ["code"],
    }

    ALLOWED_MODULES = {
        "math", "statistics", "json", "re", "datetime",
        "collections", "itertools", "functools", "decimal", "fractions",
    }

    def execute(self, code: str) -> str:
        for mod in FORBIDDEN_MODULES:
            if re.search(r'\b(?:import|from)\s+%s\b' % re.escape(mod), code):
                return "错误：禁止导入模块 %s" % mod

        for builtin in FORBIDDEN_BUILTINS:
            if re.search(r'\b%s\b' % re.escape(builtin), code):
                return "错误：禁止使用 %s" % builtin

        safe_globals = {"__builtins__": {
            "print": print, "len": len, "range": range, "enumerate": enumerate,
            "zip": zip, "map": map, "filter": filter, "sorted": sorted,
            "sum": sum, "min": min, "max": max, "abs": abs, "round": round,
            "int": int, "float": float, "str": str, "bool": bool,
            "list": list, "dict": dict, "set": set, "tuple": tuple,
            "isinstance": isinstance, "type": type, "hasattr": hasattr,
            "True": True, "False": False, "None": None,
        }}

        for mod_name in self.ALLOWED_MODULES:
            try:
                safe_globals[mod_name] = __import__(mod_name)
            except ImportError:
                pass

        stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout):
                exec(compile(code, "<agent>", "exec"), safe_globals)  # noqa: S102
            output = stdout.getvalue()
            return output if output else "(代码执行完毕，无输出)"
        except Exception as e:
            return "执行错误: %s: %s" % (type(e).__name__, e)
