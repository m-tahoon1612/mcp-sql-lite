"""Spawn the server, do the handshake, list tools, run a query.

    python examples/client.py
    python examples/client.py "SELECT country, count(*) FROM customers GROUP BY 1"
"""
import json
import subprocess
import sys

query = sys.argv[1] if len(sys.argv) > 1 else (
    "SELECT p.category, sum(o.qty * p.price_eur) AS revenue "
    "FROM orders o JOIN products p USING (product_id) "
    "WHERE o.status = 'paid' GROUP BY 1 ORDER BY 2 DESC"
)

proc = subprocess.Popen(
    [sys.executable, "-m", "mcp_sql_lite"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)

_next_id = 0


def call(method, params=None):
    global _next_id
    _next_id += 1
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": _next_id,
                                 "method": method, "params": params or {}}) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())


init = call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                           "clientInfo": {"name": "example-client", "version": "0"}})
print("server:", init["result"]["serverInfo"])
proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")

tools = call("tools/list")["result"]["tools"]
print("tools:", ", ".join(t["name"] for t in tools))

res = call("tools/call", {"name": "run_select", "arguments": {"sql": query}})["result"]
if res["isError"]:
    print("error:", res["content"][0]["text"])
else:
    data = json.loads(res["content"][0]["text"])
    print(" | ".join(data["columns"]))
    for row in data["rows"]:
        print(" | ".join(str(v) for v in row))

proc.stdin.close()
proc.wait()
