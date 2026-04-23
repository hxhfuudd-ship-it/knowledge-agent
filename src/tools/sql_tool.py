"""SQL 查询工具：执行自然语言转 SQL 查询"""
import sqlite3
from pathlib import Path
from .base import Tool
from .. import config

_project_root = Path(__file__).parent.parent.parent


class SQLTool(Tool):
    name = "sql_query"
    description = (
        "对 SQLite 数据库执行 SQL 查询。数据库包含以下表：\n"
        "- departments（部门）: id, name, manager, budget\n"
        "- employees（员工）: id, name, department_id, position, salary, hire_date\n"
        "- products（产品）: id, name, category, price, stock\n"
        "- customers（客户）: id, name, email, city, level\n"
        "- orders（订单）: id, customer_id, order_date, total_amount, status\n"
        "- order_items（订单明细）: id, order_id, product_id, quantity, unit_price\n"
        "只允许 SELECT 查询，禁止修改数据。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "要执行的 SQL SELECT 查询语句",
            }
        },
        "required": ["sql"],
    }

    FORBIDDEN_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "ATTACH", "DETACH"}

    def execute(self, sql: str) -> str:
        sql_stripped = sql.strip()
        sql_upper = sql_stripped.upper()

        if not sql_upper.startswith("SELECT"):
            return "错误：只允许 SELECT 查询"

        tokens = sql_upper.replace("(", " ").replace(")", " ").split()
        for kw in self.FORBIDDEN_KEYWORDS:
            if kw in tokens:
                return "错误：禁止使用 %s 操作" % kw

        db_path = _project_root / config.get("database.path", "data/sample.db")
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql_stripped)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()

            if not rows:
                return "查询结果为空"

            result = " | ".join(columns) + "\n"
            result += " | ".join(["---"] * len(columns)) + "\n"
            for row in rows[:50]:
                result += " | ".join(str(row[c]) for c in columns) + "\n"

            if len(rows) > 50:
                result += "\n... 共 %d 行，仅显示前 50 行" % len(rows)

            return result
        except sqlite3.Error as e:
            return "SQL 执行错误: %s" % e
