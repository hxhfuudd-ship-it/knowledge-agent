"""计算器工具：安全的数学表达式求值"""
import ast
import math
import operator
from .base import Tool


class CalculatorTool(Tool):
    name = "calculator"
    description = "执行数学计算。支持基本运算和常用数学函数（sin, cos, sqrt, log, pow 等）。"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '2 + 3 * 4' 或 'sqrt(144)'",
            }
        },
        "required": ["expression"],
    }

    SAFE_FUNCTIONS = {
        "abs": abs, "round": round, "min": min, "max": max, "pow": pow,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "ceil": math.ceil, "floor": math.floor,
        "pi": math.pi, "e": math.e,
    }

    SAFE_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
        ast.USub: operator.neg, ast.UAdd: operator.pos,
    }

    def execute(self, expression: str) -> str:
        try:
            result = self._safe_eval(expression)
            return str(result)
        except Exception as e:
            return "计算错误: %s" % e

    def _safe_eval(self, expr: str):
        """基于 AST 的安全表达式求值，不使用 eval"""
        tree = ast.parse(expr, mode="eval")
        return self._eval_node(tree.body)

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("不支持的常量类型")

        if isinstance(node, ast.Name):
            if node.id in self.SAFE_FUNCTIONS:
                return self.SAFE_FUNCTIONS[node.id]
            raise ValueError("未知变量: %s" % node.id)

        if isinstance(node, ast.BinOp):
            op = self.SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError("不支持的运算符")
            return op(self._eval_node(node.left), self._eval_node(node.right))

        if isinstance(node, ast.UnaryOp):
            op = self.SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError("不支持的运算符")
            return op(self._eval_node(node.operand))

        if isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            args = [self._eval_node(a) for a in node.args]
            if callable(func):
                return func(*args)
            raise ValueError("不可调用的对象")

        raise ValueError("不支持的表达式类型: %s" % type(node).__name__)
