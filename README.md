# mcp-sql-lite

A small stdio server that gives an agent three read-only data tools:
`list_tables`, `describe_table` and `run_select`. It speaks a subset of the
Model Context Protocol (JSON-RPC 2.0, one message per line on stdin/stdout),
which is what most agent hosts and IDE assistants expect from a local tool
server these days.

I wrote it to understand what an MCP server actually has to do before
wiring one up to a real warehouse. Turns out: not much. A handshake, a tool
list with JSON schemas, and a `tools/call` that returns text. The
interesting part is deciding what the model is allowed to run.

There's no real database. On startup it loads a fake shop schema
(customers, products, orders, ~20 rows) into an in-memory sqlite db.

## Run it

```
python -m mcp_sql_lite              # waits for json-rpc on stdin
python examples/client.py           # spawns the server, lists tools, runs a query
python examples/client.py "SELECT country, count(*) FROM customers GROUP BY 1"
```

By hand:

```
$ python -m mcp_sql_lite
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
{"jsonrpc": "2.0", "id": 1, "result": {"tools": [...]}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_select","arguments":{"sql":"select count(*) from orders"}}}
{"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "{\"columns\": ...
```

To use it from an MCP host, point the host's server config at
`python -m mcp_sql_lite` with this repo as the working directory (or
`pip install -e .` and use the `mcp-sql-lite` command).

## Tools

| tool | args | returns |
|---|---|---|
| list_tables | - | table names + row counts |
| describe_table | `table` | columns, types, short notes, 3 sample rows |
| run_select | `sql` | columns, rows, row_count |

Tool failures (unknown table, rejected query, sqlite error) come back as a
normal result with `isError: true` so the model sees the message and can
retry. Protocol problems (unknown method, bad JSON) are JSON-RPC errors.

## The SELECT gate

`safety.py` strips comments and string literals, then:

- first keyword must be `SELECT` or `WITH`
- no second statement after a `;`
- no write/DDL/admin keywords anywhere (`DELETE`, `ATTACH`, `PRAGMA`, ...)
- `LIMIT` over 200 is rejected, missing `LIMIT` gets `LIMIT 50` appended

## Tests

```
python -m unittest
```
