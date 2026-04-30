"""文件读写工具：读取知识库目录下的文件"""
from pathlib import Path
from .base import Tool
from ..path_utils import resolve_under

ALLOWED_DIR = Path(__file__).parent.parent.parent / "data" / "documents"


class FileReadTool(Tool):
    name = "read_file"
    description = (
        "读取知识库目录下的文件内容。可用于查看数据字典、业务文档等。"
        "先用 list_files 查看有哪些文件，再用此工具读取。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "文件名（不含路径），如 'data_dictionary.py'",
            }
        },
        "required": ["filename"],
    }

    def execute(self, filename: str) -> str:
        try:
            filepath = resolve_under(ALLOWED_DIR, filename)
        except ValueError:
            return "错误：文件路径不合法"
        if not filepath.exists() or not filepath.is_file():
            return "文件不存在: %s" % filename

        try:
            content = filepath.read_text(encoding="utf-8")
            if len(content) > 5000:
                content = content[:5000] + "\n... (内容过长，已截断)"
            return content
        except Exception as e:
            return "读取失败: %s" % e


class FileListTool(Tool):
    name = "list_files"
    description = "列出知识库目录下的所有文件。"
    parameters = {
        "type": "object",
        "properties": {},
    }

    def execute(self) -> str:
        if not ALLOWED_DIR.exists():
            return "知识库目录不存在"

        files = [f.name for f in ALLOWED_DIR.iterdir() if f.is_file()]
        if not files:
            return "知识库目录为空"
        return "\n".join("- %s" % f for f in sorted(files))
