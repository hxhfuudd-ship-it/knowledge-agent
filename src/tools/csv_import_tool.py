"""CSV 导入工具：将 CSV 文件导入 SQLite 数据库"""
import re
import logging
from pathlib import Path
from .base import Tool
from .. import config

logger = logging.getLogger(__name__)

_project_root = Path(__file__).parent.parent.parent
ALLOWED_DIR = _project_root / "data"


class CsvImportTool(Tool):
    name = "csv_import"
    description = (
        "将 CSV 文件导入 SQLite 数据库。导入后可用 sql_query 工具查询。\n"
        "文件必须在 data/ 目录下。导入后会自动创建表。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "CSV 文件路径（相对于 data/ 目录），如 'sales.csv'",
            },
            "table_name": {
                "type": "string",
                "description": "导入后的表名，只允许字母数字下划线",
            },
            "if_exists": {
                "type": "string",
                "enum": ["replace", "append"],
                "description": "表已存在时的处理方式：replace（覆盖）或 append（追加），默认 replace",
            },
        },
        "required": ["file_path", "table_name"],
    }

    def execute(self, file_path: str, table_name: str, if_exists: str = "replace") -> str:
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return "错误：表名只允许字母、数字和下划线，且不能以数字开头"

        filepath = (ALLOWED_DIR / file_path).resolve()
        if not str(filepath).startswith(str(ALLOWED_DIR.resolve())):
            return "错误：文件路径不合法"
        if not filepath.exists():
            return "文件不存在: %s" % file_path
        if not filepath.suffix.lower() == ".csv":
            return "错误：只支持 CSV 文件"

        try:
            import pandas as pd
        except ImportError:
            return "错误：需要安装 pandas: pip install pandas"

        db_path = _project_root / config.get("database.path", "data/sample.db")

        try:
            df = pd.read_csv(str(filepath))
        except Exception as e:
            return "CSV 读取失败: %s" % e

        if df.empty:
            return "错误：CSV 文件为空"

        try:
            import sqlite3
            with sqlite3.connect(str(db_path)) as conn:
                df.to_sql(table_name, conn, if_exists=if_exists, index=False)

            dtypes = ", ".join("%s(%s)" % (col, df[col].dtype) for col in df.columns)
            return (
                "导入成功！\n"
                "- 表名: %s\n"
                "- 行数: %d\n"
                "- 列数: %d\n"
                "- 列信息: %s\n"
                "- 前 3 行预览:\n%s"
            ) % (table_name, len(df), len(df.columns), dtypes, df.head(3).to_string(index=False))
        except Exception as e:
            return "导入失败: %s" % e
