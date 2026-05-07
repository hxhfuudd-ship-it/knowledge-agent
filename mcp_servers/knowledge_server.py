"""知识库 MCP Server：通过 MCP 协议暴露 RAG 检索能力"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.rag_tool import RAGSearchTool
from src.path_utils import resolve_under
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

DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"

_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_\u4e00-\u9fff][\w\u4e00-\u9fff\-. ]*$")
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
        "serverInfo": {"name": "knowledge-server", "version": "1.0.0"},
    }


def handle_initialized(params: dict) -> None:
    global _initialized
    _initialized = True


def handle_tools_list(params: dict) -> dict:
    return {
        "tools": [
            {
                "name": "search",
                "description": "语义搜索知识库文档",
                "annotations": {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "top_k": {"type": "integer", "description": "返回结果数量", "default": 3},
                    },
                    "required": ["query"],
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "score": {"type": "number"},
                                    "source": {"type": "string"},
                                    "chunk_id": {"type": "string"},
                                    "citation": {"type": "string"},
                                    "section": {"type": "string"},
                                },
                                "required": ["text", "score", "source", "chunk_id", "citation", "section"],
                            },
                        },
                    },
                    "required": ["query", "results"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "add_document",
                "description": "向知识库添加文本文档",
                "annotations": {
                    "readOnlyHint": False,
                    "destructiveHint": False,
                    "idempotentHint": False,
                    "openWorldHint": False,
                },
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "文档标题"},
                        "content": {"type": "string", "description": "文档内容"},
                    },
                    "required": ["title", "content"],
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "path": {"type": "string"}, "indexed": {"type": "boolean"}},
                    "required": ["title", "path", "indexed"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "list_sources",
                "description": "列出知识库中的所有文档来源",
                "annotations": {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
                "inputSchema": {"type": "object", "properties": {}},
                "outputSchema": {
                    "type": "object",
                    "properties": {"sources": {"type": "array", "items": {"type": "string"}}},
                    "required": ["sources"],
                    "additionalProperties": False,
                },
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
        query = arguments.get("query", "")
        if not query:
            return tool_result_text("缺少 query 参数", is_error=True)

        top_k = arguments.get("top_k", 3)
        rag.ensure_indexed()
        raw_results = rag.retriever.search_hybrid(query, top_k=top_k * 2)
        reranked = rag.reranker.rerank(query, raw_results, top_k=top_k)
        results = []
        for doc, score, meta in reranked:
            source = meta.get("filename", "unknown")
            chunk_id = meta.get("chunk_id", "unknown")
            citation = meta.get("citation", "%s#%s" % (source, chunk_id))
            results.append({
                "text": doc,
                "score": float(score),
                "source": source,
                "chunk_id": chunk_id,
                "citation": citation,
                "section": meta.get("section", ""),
            })
        return tool_result_structured({"query": query, "results": results})

    elif tool_name == "add_document":
        title = arguments.get("title", "")
        if not _SAFE_FILENAME_RE.match(title):
            return tool_result_text("文档标题包含非法字符", is_error=True)

        try:
            filepath = resolve_under(DOCS_DIR, "%s.md" % title)
        except ValueError:
            return tool_result_text("路径不合法", is_error=True)

        content = arguments.get("content", "")
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

        rag = get_rag_tool()
        rag._indexed = False
        rag.ensure_indexed()

        return tool_result_structured({
            "title": title,
            "path": str(filepath),
            "indexed": True,
        })

    elif tool_name == "list_sources":
        if not DOCS_DIR.exists():
            return tool_result_structured({"sources": []})
        files = [f.name for f in DOCS_DIR.iterdir() if f.is_file()]
        return tool_result_structured({"sources": sorted(files)})

    return tool_result_text("未知工具: %s" % tool_name, is_error=True)


def handle_resources_list(params: dict) -> dict:
    if not DOCS_DIR.exists():
        return {"resources": []}
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

    try:
        filepath = resolve_under(DOCS_DIR, filename)
    except ValueError:
        return {"contents": []}

    if filepath.exists() and filepath.is_file():
        content = filepath.read_text(encoding="utf-8")
        return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]}
    return {"contents": []}


def handle_prompts_list(params: dict) -> dict:
    return {
        "prompts": [
            {
                "name": "grounded_qa",
                "title": "有引用的知识库问答",
                "description": "先检索知识库，再基于片段回答并保留 citation。",
                "arguments": [
                    {"name": "question", "description": "用户问题", "required": True},
                    {"name": "top_k", "description": "检索片段数量", "required": False},
                ],
            }
        ]
    }


def handle_prompts_get(params: dict) -> dict:
    name = params.get("name")
    arguments = params.get("arguments", {})
    if name != "grounded_qa":
        raise MCPProtocolError(INVALID_PARAMS, "Unknown prompt: %s" % name)

    question = arguments.get("question", "")
    if not question:
        raise MCPProtocolError(INVALID_PARAMS, "Missing required argument: question")

    top_k = arguments.get("top_k", 3)
    return {
        "description": "有引用的知识库问答提示词",
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        "请先调用 search 工具检索知识库，top_k=%s。回答必须只基于检索片段，"
                        "如果证据不足要说明不知道，并在关键结论后标注 citation。\n\n问题：%s" % (top_k, question)
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
