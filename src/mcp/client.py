"""MCP Client：连接 MCP Server，动态发现和调用工具"""
import json
import logging
import io
import subprocess
import time
from select import select
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPError(RuntimeError):
    """MCP JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Optional[dict] = None):
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.data = data


class MCPClient:
    """MCP 客户端 - 通过 stdio 与 MCP Server 通信"""

    def __init__(self, timeout_seconds: float = 5.0):
        self._servers: Dict[str, subprocess.Popen] = {}
        self._server_tools: Dict[str, List[dict]] = {}
        self._server_prompts: Dict[str, List[dict]] = {}
        self._request_id = 0
        self.timeout_seconds = timeout_seconds

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
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "knowledge-agent", "version": "1.0.0"},
            })
            if response is None:
                raise MCPError(-32603, "MCP initialize failed")
            self._notify(name, "notifications/initialized", {})

            tools_response = self._send(name, "tools/list", {})
            if tools_response and "tools" in tools_response:
                self._server_tools[name] = tools_response["tools"]

            try:
                prompts_response = self._send(name, "prompts/list", {})
                if prompts_response and "prompts" in prompts_response:
                    self._server_prompts[name] = prompts_response["prompts"]
            except MCPError as e:
                logger.info("MCP Server '%s' 不支持 prompts: %s", name, e)

            return response
        except OSError as e:
            logger.error("MCP Server '%s' 启动失败: %s", name, e)
            return None
        except MCPError as e:
            logger.error("MCP Server '%s' 初始化失败: %s", name, e)
            self.disconnect(name)
            return None

    def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[dict]]:
        if server_name:
            return {server_name: self._server_tools.get(server_name, [])}
        return dict(self._server_tools)

    def call_tool(self, server_name: str, tool_name: str, arguments: Optional[dict] = None) -> str:
        try:
            response = self._send(server_name, "tools/call", {
                "name": tool_name,
                "arguments": arguments or {},
            })
        except MCPError as e:
            return str(e)

        if response and "content" in response:
            texts = [c["text"] for c in response["content"] if c.get("type") == "text"]
            return "\n".join(texts)
        return str(response)

    def call_tool_result(self, server_name: str, tool_name: str, arguments: Optional[dict] = None) -> Optional[dict]:
        """调用 MCP 工具并保留 structuredContent / isError 等完整结果。"""
        return self._send(server_name, "tools/call", {
            "name": tool_name,
            "arguments": arguments or {},
        })

    def list_resources(self, server_name: str) -> List[dict]:
        try:
            response = self._send(server_name, "resources/list", {})
        except MCPError:
            return []
        if response and "resources" in response:
            return response["resources"]
        return []

    def read_resource(self, server_name: str, uri: str) -> str:
        try:
            response = self._send(server_name, "resources/read", {"uri": uri})
        except MCPError:
            return ""
        if response and "contents" in response:
            texts = [c.get("text", "") for c in response["contents"]]
            return "\n".join(texts)
        return ""

    def list_prompts(self, server_name: Optional[str] = None) -> Dict[str, List[dict]]:
        if server_name:
            return {server_name: self._server_prompts.get(server_name, [])}
        return dict(self._server_prompts)

    def get_prompt(self, server_name: str, prompt_name: str, arguments: Optional[dict] = None) -> Optional[dict]:
        try:
            return self._send(server_name, "prompts/get", {
                "name": prompt_name,
                "arguments": arguments or {},
            })
        except MCPError:
            return None

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
            self._server_tools.clear()
            self._server_prompts.clear()

    def _notify(self, server_name: str, method: str, params: dict) -> bool:
        proc = self._servers.get(server_name)
        if not proc or proc.poll() is not None:
            logger.warning("MCP Server '%s' 未运行", server_name)
            return False

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        try:
            proc.stdin.write(json.dumps(notification) + "\n")
            proc.stdin.flush()
            return True
        except (BrokenPipeError, IOError) as e:
            logger.error("MCP Server '%s' 通知失败: %s", server_name, e)
            return False

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
            line = self._readline_with_timeout(proc)
            if line:
                response = json.loads(line)
                if "error" in response:
                    error = response["error"]
                    raise MCPError(error.get("code", -32603), error.get("message", "MCP error"), error.get("data"))
                return response.get("result")
        except (BrokenPipeError, IOError) as e:
            logger.error("MCP Server '%s' 通信失败: %s", server_name, e)
            return None
        except TimeoutError as e:
            logger.error("MCP Server '%s' 超时: %s", server_name, e)
            return None
        except json.JSONDecodeError as e:
            logger.error("MCP Server '%s' 返回无效 JSON: %s", server_name, e)
            return None

        return None

    def _readline_with_timeout(self, proc: subprocess.Popen) -> str:
        stream = proc.stdout
        if stream is None:
            raise TimeoutError("MCP Server stdout not available")

        try:
            fileno = stream.fileno()
        except (AttributeError, io.UnsupportedOperation, ValueError):
            return stream.readline()

        ready, _, _ = select([fileno], [], [], self.timeout_seconds)
        if not ready:
            raise TimeoutError("MCP Server response timed out after %.1fs" % self.timeout_seconds)

        line = stream.readline()
        deadline = time.time() + self.timeout_seconds
        while line and not line.strip() and time.time() < deadline:
            line = proc.stdout.readline()
        return line

    def __del__(self):
        self.disconnect()
