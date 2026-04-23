"""工具模块测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.calculator_tool import CalculatorTool
from src.tools.sql_tool import SQLTool
from src.tools.file_tool import FileReadTool, FileListTool
from src.tools.python_tool import PythonTool
from src.tools.search_tool import SearchTool
from src.tools.chart_tool import ChartTool


def test_calculator_basic():
    calc = CalculatorTool()
    assert calc.execute(expression="2 + 3") == "5"
    assert calc.execute(expression="10 / 3") == str(10 / 3)
    assert calc.execute(expression="2 ** 10") == "1024"
    print("  OK  calculator basic")


def test_calculator_functions():
    calc = CalculatorTool()
    assert calc.execute(expression="sqrt(144)") == "12.0"
    assert calc.execute(expression="abs(-5)") == "5"
    assert "计算错误" in calc.execute(expression="__import__('os')")
    print("  OK  calculator functions + safety")


def test_sql_tool_reject():
    sql = SQLTool()
    assert "错误" in sql.execute(sql="DROP TABLE users")
    assert "错误" in sql.execute(sql="DELETE FROM users")
    assert "错误" in sql.execute(sql="INSERT INTO users VALUES (1)")
    print("  OK  sql reject dangerous queries")


def test_sql_tool_query():
    sql = SQLTool()
    result = sql.execute(sql="SELECT 1 AS test_col")
    assert "test_col" in result
    print("  OK  sql basic query")


def test_file_list():
    fl = FileListTool()
    result = fl.execute()
    assert "business_rules" in result or "data_dictionary" in result or "知识库目录" in result
    print("  OK  file list")


def test_file_read_traversal():
    fr = FileReadTool()
    result = fr.execute(filename="../../config/settings.yaml")
    assert "不合法" in result or "不存在" in result
    print("  OK  file read path traversal blocked")


def test_python_tool_basic():
    py = PythonTool()
    result = py.execute(code="print(1 + 2)")
    assert "3" in result
    print("  OK  python basic exec")


def test_python_tool_sandbox():
    py = PythonTool()
    result = py.execute(code="import os\nos.listdir('.')")
    assert "错误" in result or "禁止" in result
    result2 = py.execute(code="open('/etc/passwd')")
    assert "错误" in result2 or "禁止" in result2
    print("  OK  python sandbox blocks dangerous ops")


def test_search_tool():
    s = SearchTool()
    result = s.execute(query="test")
    assert "演示模式" in result
    print("  OK  search tool demo mode")


def test_chart_tool_bad_data():
    c = ChartTool()
    result = c.execute(chart_type="bar", title="test", data={"labels": ["a"], "values": []})
    assert "错误" in result
    print("  OK  chart tool rejects bad data")


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll tool tests passed!")
