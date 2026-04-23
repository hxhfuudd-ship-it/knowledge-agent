"""知识库 MCP Server：通过 MCP 协议暴露 RAG 检索能力"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.rag_tool import RAGSearchTool

DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"

_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_\u4e00-\u9fff][\w\u4e00-\u9fff\-. ]*$")


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
        "serverInfo": {"name": "knowledge-server", "version": "1.0.0"},
    }


def handle_tools_list(params: dict) -> dict:
    return {
        "tools": [
            {
                "name": "search",
                "description": "语义搜索知识库文档",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "top_k": {"type": "integer", "description": "返回结果数量", "default": 3},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "add_document",
                "description": "向知识库添加文本文档",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "文档标题"},
                        "content": {"type": "string", "description": "文档内容"},
                    },
                    "required": ["title", "content"],
                },
            },
            {
                "name": "list_sources",
                "description": "列出知识库中的所有文档来源",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
    }


_rag_tool = None


def get_rag_tool():
    global _rag_tool
    if _rag_tool is None:
        _rag_tool = RAGSearchTool()
    return _rag_tool


def handle_tools_call(params: dict) -> dict:
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    if tool_name == "search":
        rag = get_rag_tool()
        result = rag.execute(query=arguments["query"], top_k=arguments.get("top_k", 3))
        return {"content": [{"type": "text", "text": result}]}

    elif tool_name == "add_document":
        title = arguments["title"]
        if not _SAFE_FILENAME_RE.match(title):
            return {"content": [{"type": "text", "text": "文档标题包含非法字符"}], "isError": True}

        filepath = (DOCS_DIR / ("%s.md" % title)).resolve()
        if not str(filepath).startswith(str(DOCS_DIR.resolve())):
            return {"content": [{"type": "text", "text": "路径不合法"}], "isError": True}

        content = arguments["content"]
        filepath.write_text(content, encoding="utf-8")

        rag = get_rag_tool()
        rag._indexed = False
        rag.ensure_indexed()

        return {"content": [{"type": "text", "text": "文档 '%s' 已添加到知识库" % title}]}

    elif tool_name == "list_sources":
        files = [f.name for f in DOCS_DIR.iterdir() if f.is_file()]
        return {"content": [{"type": "text", "text": json.dumps(sorted(files), ensure_ascii=False)}]}

    return {"content": [{"type": "text", "text": "未知工具: %s" % tool_name}], "isError": True}


def handle_resources_list(params: dict) -> dict:
    files = [f.name for f in DOCS_DIR.iterdir() if f.is_file()]
    resources = [
        {"uri": "knowledge:///%s" % f, "name": f, "mimeType": "text/plain"}
        for f in sorted(files)
    ]
    return {"resources": resources}


def handle_resources_read(params: dict) -> dict:
    uri = params.get("uri", "")
    filename = uri.replace("knowledge:///", "")
    if not _SAFE_FILENAME_RE.match(filename):
        return {"contents": []}

    filepath = (DOCS_DIR / filename).resolve()
    if not str(filepath).startswith(str(DOCS_DIR.resolve())):
        return {"contents": []}

    if filepath.exists():
        content = filepath.read_text(encoding="utf-8")
        return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]}
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
