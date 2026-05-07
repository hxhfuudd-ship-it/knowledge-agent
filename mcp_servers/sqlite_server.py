"""SQLite MCP Server：通过 MCP 协议暴露数据库查询能力"""
import json
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import config
from mcp_servers.protocol import (
    INVALID_PARAMS,
    MCP_PROTOCOL_VERSION,
    MCPProtocolError,
    error_response,
    parse_error_response,
    result_response,
    tool_result_structured,
    tool_result_text,
)

DB_PATH = PROJECT_ROOT / config.get("database.path", "data/databases/default.db")

_TABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_initialized = False


def handle_request(request: dict):
    if not isinstance(request, dict):
        return error_response(None, -32600, "Invalid request")

    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")
    is_notification = "id" not in request

    if method == "notifications/initialized":
        handle_initialized(params)
        return None

    if is_notification:
        return None

    handlers = {
        "initialize": handle_initialize,
        "tools/list": handle_tools_list,
        "tools/call": handle_tools_call,
        "resources/list": handle_resources_list,
        "resources/read": handle_resources_read,
        "prompts/list": handle_prompts_list,
        "prompts/get": handle_prompts_get,
    }

    handler = handlers.get(method)
    if not handler:
        return error_response(req_id, -32601, "Unknown method: %s" % method)

    try:
        result = handler(params)
        return result_response(req_id, result)
    except MCPProtocolError as e:
        return error_response(req_id, e.code, e.message, e.data)
    except Exception as e:
        return error_response(req_id, -32603, "Internal error", {"detail": str(e)})


def handle_initialize(params: dict) -> dict:
    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
        "serverInfo": {"name": "sqlite-server", "version": "1.0.0"},
    }


def handle_initialized(params: dict) -> None:
    global _initialized
    _initialized = True


def handle_tools_list(params: dict) -> dict:
    return {
        "tools": [
            {
                "name": "list_tables",
                "description": "列出数据库中所有表",
                "inputSchema": {"type": "object", "properties": {}},
                "annotations": {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {"tables": {"type": "array", "items": {"type": "string"}}},
                    "required": ["tables"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "describe_table",
                "description": "查看表结构（字段名、类型）",
                "annotations": {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
                "inputSchema": {
                    "type": "object",
                    "properties": {"table_name": {"type": "string", "description": "表名"}},
                    "required": ["table_name"],
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string"},
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "notnull": {"type": "boolean"},
                                    "pk": {"type": "boolean"},
                                },
                                "required": ["name", "type", "notnull", "pk"],
                            },
                        },
                    },
                    "required": ["table_name", "columns"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "query",
                "description": "执行 SQL SELECT 查询",
                "annotations": {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
                "inputSchema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 查询语句"}},
                    "required": ["sql"],
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "columns": {"type": "array", "items": {"type": "string"}},
                        "rows": {"type": "array", "items": {"type": "object"}},
                        "row_count": {"type": "integer"},
                        "truncated": {"type": "boolean"},
                    },
                    "required": ["columns", "rows", "row_count", "truncated"],
                    "additionalProperties": False,
                },
            },
        ]
    }


def handle_tools_call(params: dict) -> dict:
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row

            if tool_name == "list_tables":
                rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
                result = {"tables": [row["name"] for row in rows]}
                return tool_result_structured(result)

            elif tool_name == "describe_table":
                table = arguments.get("table_name", "")
                if not _TABLE_NAME_RE.match(table):
                    return tool_result_text("非法表名", is_error=True)
                rows = conn.execute("PRAGMA table_info([%s])" % table).fetchall()
                columns = [{"name": r["name"], "type": r["type"], "notnull": bool(r["notnull"]), "pk": bool(r["pk"])} for r in rows]
                return tool_result_structured({"table_name": table, "columns": columns})

            elif tool_name == "query":
                sql = arguments.get("sql", "").strip()
                if not sql.upper().startswith("SELECT"):
                    return tool_result_text("只允许 SELECT 查询", is_error=True)
                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchmany(101)
                data = [dict(zip(columns, row)) for row in rows]
                result = {
                    "columns": columns,
                    "rows": data[:100],
                    "row_count": min(len(data), 100),
                    "truncated": len(data) > 100,
                }
                return tool_result_structured(result)

            return tool_result_text("未知工具: %s" % tool_name, is_error=True)
    except sqlite3.Error as e:
        return tool_result_text("数据库错误: %s" % e, is_error=True)


def handle_resources_list(params: dict) -> dict:
    return {
        "resources": [{
            "uri": "sqlite:///tables",
            "name": "数据库表列表",
            "description": "当前数据库中所有表的列表",
            "mimeType": "application/json",
        }]
    }


def handle_resources_read(params: dict) -> dict:
    uri = params.get("uri", "")
    if uri == "sqlite:///tables":
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            return {"contents": [{"uri": uri, "mimeType": "application/json",
                                  "text": json.dumps([t[0] for t in tables], ensure_ascii=False)}]}
        except sqlite3.Error as e:
            return {"contents": [{"uri": uri, "text": "错误: %s" % e}]}
    return {"contents": []}


def handle_prompts_list(params: dict) -> dict:
    return {
        "prompts": [
            {
                "name": "sql_analysis",
                "title": "SQL 数据分析",
                "description": "把业务问题转成只读 SQL 分析流程，并要求解释查询依据。",
                "arguments": [
                    {"name": "question", "description": "需要分析的业务问题", "required": True},
                ],
            }
        ]
    }


def handle_prompts_get(params: dict) -> dict:
    name = params.get("name")
    arguments = params.get("arguments", {})
    if name != "sql_analysis":
        raise MCPProtocolError(INVALID_PARAMS, "Unknown prompt: %s" % name)

    question = arguments.get("question", "")
    if not question:
        raise MCPProtocolError(INVALID_PARAMS, "Missing required argument: question")

    return {
        "description": "SQL 数据分析提示词",
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        "请基于 SQLite 数据库回答下面的问题。先使用 list_tables/describe_table 理解表结构，"
                        "再只执行 SELECT 查询，最后给出结论、关键指标和必要的 SQL 依据。\n\n问题：%s" % question
                    ),
                },
            }
        ],
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            error = parse_error_response()
            sys.stdout.write(json.dumps(error) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
