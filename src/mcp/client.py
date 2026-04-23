"""MCP Client：连接 MCP Server，动态发现和调用工具"""
import json
import logging
import subprocess
import sys
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP 客户端 - 通过 stdio 与 MCP Server 通信"""

    def __init__(self):
        self._servers: Dict[str, subprocess.Popen] = {}
        self._server_tools: Dict[str, List[dict]] = {}
        self._request_id = 0

    def connect(self, name: str, command: List[str]) -> Optional[dict]:
        """启动并连接一个 MCP Server"""
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self._servers[name] = proc

            response = self._send(name, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "knowledge-agent", "version": "1.0.0"},
            })

            tools_response = self._send(name, "tools/list", {})
            if tools_response and "tools" in tools_response:
                self._server_tools[name] = tools_response["tools"]

            return response
        except OSError as e:
            logger.error("MCP Server '%s' 启动失败: %s", name, e)
            return None

    def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[dict]]:
        if server_name:
            return {server_name: self._server_tools.get(server_name, [])}
        return dict(self._server_tools)

    def call_tool(self, server_name: str, tool_name: str, arguments: Optional[dict] = None) -> str:
        response = self._send(server_name, "tools/call", {
            "name": tool_name,
            "arguments": arguments or {},
        })

        if response and "content" in response:
            texts = [c["text"] for c in response["content"] if c.get("type") == "text"]
            return "\n".join(texts)
        return str(response)

    def list_resources(self, server_name: str) -> List[dict]:
        response = self._send(server_name, "resources/list", {})
        if response and "resources" in response:
            return response["resources"]
        return []

    def read_resource(self, server_name: str, uri: str) -> str:
        response = self._send(server_name, "resources/read", {"uri": uri})
        if response and "contents" in response:
            texts = [c.get("text", "") for c in response["contents"]]
            return "\n".join(texts)
        return ""

    def disconnect(self, name: Optional[str] = None):
        if name:
            proc = self._servers.pop(name, None)
            if proc:
                proc.terminate()
                proc.wait(timeout=5)
        else:
            for proc in self._servers.values():
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            self._servers.clear()

    def _send(self, server_name: str, method: str, params: dict) -> Optional[dict]:
        proc = self._servers.get(server_name)
        if not proc or proc.poll() is not None:
            logger.warning("MCP Server '%s' 未运行", server_name)
            return None

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        try:
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            if line:
                response = json.loads(line)
                return response.get("result")
        except (BrokenPipeError, IOError) as e:
            logger.error("MCP Server '%s' 通信失败: %s", server_name, e)
            return None
        except json.JSONDecodeError as e:
            logger.error("MCP Server '%s' 返回无效 JSON: %s", server_name, e)
            return None

        return None

    def __del__(self):
        self.disconnect()
