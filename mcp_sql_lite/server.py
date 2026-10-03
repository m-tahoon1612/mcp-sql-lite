"""json-rpc over stdio, mcp-ish. wip"""
import json
import sys

from .tools import TOOL_SPECS


def handle(msg):
    method = msg.get("method")
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                  "serverInfo": {"name": "mcp-sql-lite", "version": "0.0.1"}}
    elif method == "tools/list":
        result = {"tools": TOOL_SPECS}
    else:
        return {"jsonrpc": "2.0", "id": msg.get("id"),
                "error": {"code": -32601, "message": "method not found"}}
    return {"jsonrpc": "2.0", "id": msg.get("id"), "result": result}


def serve():
    for line in sys.stdin:
        if not line.strip():
            continue
        resp = handle(json.loads(line))
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
