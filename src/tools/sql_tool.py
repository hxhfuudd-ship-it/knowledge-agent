"""SQL 查询工具：执行自然语言转 SQL 查询"""
import sqlite3
from pathlib import Path
from .base import Tool
from .. import config

_project_root = Path(__file__).parent.parent.parent


class SQLTool(Tool):
    name = "sql_query"
    _description_base = "对 SQLite 数据库执行 SQL 查询。只允许 SELECT 查询，禁止修改数据。"
    description = _description_base
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

    @staticmethod
    def _get_table_info() -> str:
        db_path = _project_root / config.get("database.path", "data/databases/default.db")
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
                if not tables:
                    return "数据库中没有表"
                lines = []
                for t in tables:
                    cols = conn.execute("PRAGMA table_info([%s])" % t).fetchall()
                    col_names = ", ".join(c[1] for c in cols)
                    lines.append("- %s: %s" % (t, col_names))
                return "\n".join(lines)
        except sqlite3.Error:
            return "（无法读取表结构）"

    def to_claude_tool(self) -> dict:
        table_info = self._get_table_info()
        dynamic_desc = "%s\n数据库包含以下表：\n%s" % (self._description_base, table_info)
        return {
            "name": self.name,
            "description": dynamic_desc,
            "input_schema": self.parameters,
        }

    def execute(self, sql: str) -> str:
        sql_stripped = sql.strip()
        sql_upper = sql_stripped.upper()

        if not sql_upper.startswith("SELECT"):
            return "错误：只允许 SELECT 查询"

        tokens = sql_upper.replace("(", " ").replace(")", " ").split()
        for kw in self.FORBIDDEN_KEYWORDS:
            if kw in tokens:
                return "错误：禁止使用 %s 操作" % kw

        db_path = _project_root / config.get("database.path", "data/databases/default.db")
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
