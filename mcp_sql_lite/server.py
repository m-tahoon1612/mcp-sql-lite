"""Line-delimited JSON-RPC 2.0 over stdin/stdout, MCP-ish.

Implements just enough of the MCP handshake (initialize, tools/list,
tools/call, ping) for agent hosts and my own scripts to talk to it.
One JSON object per line in, one per line out. Logs go to stderr.
"""
import json
import sys

from . import __version__
from .sample_data import build_db
from .tools import HANDLERS, TOOL_SPECS, ToolError

PROTOCOL_VERSION = "2025-06-18"


def log(msg: str) -> None:
    print(f"[mcp-sql-lite] {msg}", file=sys.stderr, flush=True)


class Server:
    def __init__(self, conn=None):
        self.conn = conn or build_db()

    def handle(self, msg: dict) -> dict | None:
        method = msg.get("method")
        mid = msg.get("id")
        params = msg.get("params") or {}

        # notifications have no id and get no response
        if mid is None:
            if method not in ("notifications/initialized", "notifications/cancelled"):
                log(f"ignoring notification {method}")
            return None

        try:
            result = self.dispatch(method, params)
        except _RpcError as e:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": e.code, "message": str(e)}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def dispatch(self, method: str, params: dict):
        if method == "initialize":
            return {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-sql-lite", "version": __version__},
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": TOOL_SPECS}
        if method == "tools/call":
            name = params.get("name")
            if name not in HANDLERS:
                raise _RpcError(-32602, f"unknown tool {name!r}")
            try:
                data = HANDLERS[name](self.conn, params.get("arguments") or {})
            except ToolError as e:
                # tool errors are results, not protocol errors - the model should see them
                return {"content": [{"type": "text", "text": str(e)}], "isError": True}
            return {"content": [{"type": "text", "text": json.dumps(data, default=str)}],
                    "isError": False}
        raise _RpcError(-32601, f"method not found: {method}")


class _RpcError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def serve(stdin=sys.stdin, stdout=sys.stdout) -> None:
    server = Server()
    log("ready, reading json-rpc from stdin")
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            resp = {"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": f"parse error: {e}"}}
        else:
            resp = server.handle(msg) if isinstance(msg, dict) else {
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32600, "message": "batch requests not supported"}}
        if resp is not None:
            stdout.write(json.dumps(resp) + "\n")
            stdout.flush()
