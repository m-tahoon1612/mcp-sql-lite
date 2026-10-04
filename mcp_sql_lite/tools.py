"""The tools the server exposes. Each returns plain python data."""
import sqlite3

from .sample_data import SCHEMA

TOOL_SPECS = [
    {
        "name": "list_tables",
        "description": "List tables in the database with row counts.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "describe_table",
        "description": "Columns, types and notes for one table, plus 3 sample rows.",
        "inputSchema": {
            "type": "object",
            "properties": {"table": {"type": "string"}},
            "required": ["table"],
        },
    },
]


class ToolError(Exception):
    pass


def list_tables(conn: sqlite3.Connection, args: dict) -> list[dict]:
    out = []
    for t in SCHEMA:
        (n,) = conn.execute(f"SELECT count(*) FROM {t}").fetchone()
        out.append({"table": t, "rows": n})
    return out


def describe_table(conn: sqlite3.Connection, args: dict) -> dict:
    table = (args.get("table") or "").strip().lower()
    if table not in SCHEMA:
        raise ToolError(f"unknown table {table!r}, try list_tables")
    cols = [{"name": c, "type": t, "note": n} for c, t, n in SCHEMA[table]]
    cur = conn.execute(f"SELECT * FROM {table} LIMIT 3")
    names = [d[0] for d in cur.description]
    sample = [dict(zip(names, r)) for r in cur.fetchall()]
    return {"table": table, "columns": cols, "sample": sample}


HANDLERS = {
    "list_tables": list_tables,
    "describe_table": describe_table,
}
