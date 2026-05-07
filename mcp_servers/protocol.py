"""Small JSON-RPC helpers for the educational MCP servers."""
import json
from typing import Optional

JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2025-11-25"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPProtocolError(Exception):
    """Protocol-level error that should be returned as JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def result_response(req_id, result: dict) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": req_id, "result": result}


def error_response(req_id, code: int, message: str, data: Optional[dict] = None) -> dict:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": req_id, "error": error}


def parse_error_response(message: str = "Parse error") -> dict:
    return error_response(None, PARSE_ERROR, message)


def text_content(text: str) -> dict:
    return {"type": "text", "text": text}


def tool_result_text(text: str, is_error: bool = False) -> dict:
    result = {"content": [text_content(text)]}
    if is_error:
        result["isError"] = True
    return result


def tool_result_structured(data: dict, is_error: bool = False) -> dict:
    result = {
        "content": [text_content(json.dumps(data, ensure_ascii=False))],
        "structuredContent": data,
    }
    if is_error:
        result["isError"] = True
    return result


def empty_object_schema() -> dict:
    return {"type": "object", "additionalProperties": False}
