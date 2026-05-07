"""MCP 协议层测试"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.knowledge_server import handle_request as handle_knowledge_request
from mcp_servers.sqlite_server import handle_request as handle_sqlite_request
from src.mcp.client import MCPClient, MCPError


def test_sqlite_mcp_prompts_and_structured_tools():
    tools = handle_sqlite_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert tools["result"]["tools"][0]["outputSchema"]["properties"]["tables"]["type"] == "array"
    for tool in tools["result"]["tools"]:
        annotations = tool["annotations"]
        assert annotations["readOnlyHint"] is True
        assert annotations["destructiveHint"] is False
        assert annotations["openWorldHint"] is False

    prompts = handle_sqlite_request({"jsonrpc": "2.0", "id": 2, "method": "prompts/list", "params": {}})
    assert prompts["result"]["prompts"][0]["name"] == "sql_analysis"

    prompt = handle_sqlite_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "prompts/get",
        "params": {"name": "sql_analysis", "arguments": {"question": "GMV 怎么算？"}},
    })
    assert "SQLite 数据库" in prompt["result"]["messages"][0]["content"]["text"]

    call_result = handle_sqlite_request({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "list_tables", "arguments": {}},
    })
    assert "structuredContent" in call_result["result"]
    assert "tables" in call_result["result"]["structuredContent"]


def test_knowledge_mcp_prompts_and_search_shape():
    tools = handle_knowledge_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert tools["result"]["tools"][0]["outputSchema"]["properties"]["results"]["type"] == "array"
    annotations_by_name = {tool["name"]: tool["annotations"] for tool in tools["result"]["tools"]}
    assert annotations_by_name["search"]["readOnlyHint"] is True
    assert annotations_by_name["add_document"]["readOnlyHint"] is False
    assert annotations_by_name["add_document"]["idempotentHint"] is False

    prompts = handle_knowledge_request({"jsonrpc": "2.0", "id": 2, "method": "prompts/list", "params": {}})
    assert prompts["result"]["prompts"][0]["name"] == "grounded_qa"

    prompt = handle_knowledge_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "prompts/get",
        "params": {"name": "grounded_qa", "arguments": {"question": "复购率是什么？", "top_k": 2}},
    })
    assert "citation" in prompt["result"]["messages"][0]["content"]["text"]


def test_mcp_client_handles_error_and_prompts():
    client = MCPClient()

    class FakeProc:
        def __init__(self):
            self.stdin = self
            self.stdout = self
            self._responses = []
            self._writes = []
            self._alive = True

        def poll(self):
            return None if self._alive else 1

        def write(self, payload):
            self._writes.append(json.loads(payload))
            request = self._writes[-1]
            method = request["method"]
            if method == "initialize":
                self._responses.append({"jsonrpc": "2.0", "id": request["id"], "result": {"protocolVersion": "2025-11-25", "capabilities": {}}})
            elif method == "tools/list":
                self._responses.append({"jsonrpc": "2.0", "id": request["id"], "result": {"tools": []}})
            elif method == "prompts/list":
                self._responses.append({"jsonrpc": "2.0", "id": request["id"], "result": {"prompts": [{"name": "demo"}]}})
            elif method == "prompts/get":
                self._responses.append({"jsonrpc": "2.0", "id": request["id"], "result": {"messages": []}})
            elif method == "tools/call":
                self._responses.append({"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32602, "message": "bad args"}})

        def flush(self):
            return None

        def readline(self):
            if self._responses:
                return json.dumps(self._responses.pop(0)) + "\n"
            return ""

        def terminate(self):
            self._alive = False

        def wait(self, timeout=None):
            self._alive = False

    fake = FakeProc()
    client._servers["demo"] = fake

    assert client._send("demo", "initialize", {}) == {"protocolVersion": "2025-11-25", "capabilities": {}}
    assert client._send("demo", "tools/list", {}) == {"tools": []}
    client._server_prompts["demo"] = [{"name": "demo"}]
    assert client.list_prompts("demo")["demo"][0]["name"] == "demo"

    try:
        client.call_tool_result("demo", "bad_tool")
    except MCPError as exc:
        assert exc.code == -32602
    else:
        assert False, "expected MCPError"


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
    print("\nAll MCP tests passed!")
