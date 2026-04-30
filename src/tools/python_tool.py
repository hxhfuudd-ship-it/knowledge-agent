"""Python 代码执行工具：在受限子进程中执行 Python 代码片段"""
import json
import logging
import re
import subprocess
import sys
from .base import Tool

logger = logging.getLogger(__name__)

FORBIDDEN_MODULES = {"os", "sys", "subprocess", "shutil", "pathlib", "socket", "http", "importlib"}
FORBIDDEN_BUILTINS = {"exec", "eval", "compile", "__import__", "open", "input", "breakpoint"}

RUNNER = r'''
import contextlib
import importlib
import io
import json
import sys

ALLOWED_MODULES = {
    "math", "statistics", "json", "re", "datetime",
    "collections", "itertools", "functools", "decimal", "fractions",
}
MAX_OUTPUT_CHARS = 5000

payload = json.loads(sys.stdin.read())
code = payload["code"]

class LimitedWriter(io.StringIO):
    def write(self, text):
        remaining = MAX_OUTPUT_CHARS - len(self.getvalue())
        if remaining <= 0:
            return len(text)
        return super().write(text[:remaining])


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".", 1)[0]
    if root not in ALLOWED_MODULES:
        raise ImportError("禁止导入模块 %s" % root)
    return importlib.import_module(name)

safe_builtins = {
    "print": print, "len": len, "range": range, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter, "sorted": sorted,
    "sum": sum, "min": min, "max": max, "abs": abs, "round": round,
    "int": int, "float": float, "str": str, "bool": bool,
    "list": list, "dict": dict, "set": set, "tuple": tuple,
    "isinstance": isinstance, "type": type, "hasattr": hasattr,
    "True": True, "False": False, "None": None,
    "__import__": safe_import,
}

safe_globals = {"__builtins__": safe_builtins}
for module_name in ALLOWED_MODULES:
    try:
        safe_globals[module_name] = importlib.import_module(module_name)
    except ImportError:
        pass

stdout = LimitedWriter()
try:
    with contextlib.redirect_stdout(stdout):
        exec(compile(code, "<agent>", "exec"), safe_globals, {})
    output = stdout.getvalue()
    if len(output) >= MAX_OUTPUT_CHARS:
        output += "\n... (输出过长，已截断)"
    print(output if output else "(代码执行完毕，无输出)")
except Exception as e:
    print("执行错误: %s: %s" % (type(e).__name__, e))
'''


class PythonTool(Tool):
    name = "python_exec"
    description = (
        "在受限子进程中执行 Python 代码片段并返回输出。适合数据处理、格式转换、简单计算等。\n"
        "限制：不能访问文件系统、网络、系统命令；默认 3 秒超时。"
        "可用库：math、statistics、json、re、datetime、collections。"
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

    TIMEOUT_SECONDS = 3
    MAX_CODE_CHARS = 10000

    def execute(self, code: str) -> str:
        if len(code) > self.MAX_CODE_CHARS:
            return "错误：代码过长，最多允许 %d 个字符" % self.MAX_CODE_CHARS

        unsafe = self._validate_code(code)
        if unsafe:
            return unsafe

        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-c", RUNNER],
                input=json.dumps({"code": code}, ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "执行超时：代码运行超过 %d 秒" % self.TIMEOUT_SECONDS
        except OSError as e:
            logger.error("Python 子进程启动失败: %s", e)
            return "执行错误: 无法启动 Python 子进程"

        output = completed.stdout.strip()
        error = completed.stderr.strip()
        if completed.returncode != 0 and error:
            return "执行错误: %s" % error[:500]
        return output or "(代码执行完毕，无输出)"

    @staticmethod
    def _validate_code(code: str) -> str:
        for mod in FORBIDDEN_MODULES:
            if re.search(r'\b(?:import|from)\s+%s\b' % re.escape(mod), code):
                return "错误：禁止导入模块 %s" % mod

        for builtin in FORBIDDEN_BUILTINS:
            if re.search(r'\b%s\b' % re.escape(builtin), code):
                return "错误：禁止使用 %s" % builtin

        return ""
