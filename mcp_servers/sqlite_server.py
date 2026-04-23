"""SQLite MCP Server：通过 MCP 协议暴露数据库查询能力"""
import json
import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "sample.db"

_TABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    handlers = {
        "initialize": handle_initialize,
        "tools/list": handle_tools_list,
        "tools/call": handle_tools_call,
        "resources/list": handle_resources_list,
        "resources/read": handle_resources_read,
    }

    handler = handlers.get(method)
    if handler:
        result = handler(params)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method: %s" % method}}


def handle_initialize(params: dict) -> dict:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}, "resources": {}},
        "serverInfo": {"name": "sqlite-server", "version": "1.0.0"},
    }


def handle_tools_list(params: dict) -> dict:
    return {
        "tools": [
            {
                "name": "list_tables",
                "description": "列出数据库中所有表",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "describe_table",
                "description": "查看表结构（字段名、类型）",
                "inputSchema": {
                    "type": "object",
                    "properties": {"table_name": {"type": "string", "description": "表名"}},
                    "required": ["table_name"],
                },
            },
            {
                "name": "query",
                "description": "执行 SQL SELECT 查询",
                "inputSchema": {
                    "type": "object",
                    "properties": {"sql": {"type": "string", "description": "SQL 查询语句"}},
                    "required": ["sql"],
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
                result = [row["name"] for row in rows]
                return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}

            elif tool_name == "describe_table":
                table = arguments.get("table_name", "")
                if not _TABLE_NAME_RE.match(table):
                    return {"content": [{"type": "text", "text": "非法表名"}], "isError": True}
                rows = conn.execute("PRAGMA table_info([%s])" % table).fetchall()
                columns = [{"name": r["name"], "type": r["type"], "notnull": bool(r["notnull"]), "pk": bool(r["pk"])} for r in rows]
                return {"content": [{"type": "text", "text": json.dumps(columns, ensure_ascii=False)}]}

            elif tool_name == "query":
                sql = arguments.get("sql", "").strip()
                if not sql.upper().startswith("SELECT"):
                    return {"content": [{"type": "text", "text": "只允许 SELECT 查询"}], "isError": True}
                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchmany(100)
                data = [dict(zip(columns, row)) for row in rows]
                return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}]}

            return {"content": [{"type": "text", "text": "未知工具: %s" % tool_name}], "isError": True}
    except sqlite3.Error as e:
        return {"content": [{"type": "text", "text": "数据库错误: %s" % e}], "isError": True}


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


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
            sys.stdout.write(json.dumps(error) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
