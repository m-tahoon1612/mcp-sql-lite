"""The tools the server exposes. Each returns plain python data."""
import sqlite3

from .safety import check_select, ensure_limit
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
    {
        "name": "run_select",
        "description": "Run a read-only SELECT. A LIMIT is added if missing (max 200 rows).",
        "inputSchema": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
            "required": ["sql"],
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


def run_select(conn: sqlite3.Connection, args: dict) -> dict:
    sql = args.get("sql") or ""
    ok, reason = check_select(sql)
    if not ok:
        raise ToolError(f"query rejected: {reason}")
    sql = ensure_limit(sql)
    try:
        cur = conn.execute(sql)
    except sqlite3.Error as e:
        raise ToolError(f"sqlite error: {e}") from None
    names = [d[0] for d in cur.description or []]
    rows = cur.fetchall()
    return {"columns": names, "rows": [list(r) for r in rows], "row_count": len(rows)}


HANDLERS = {
    "list_tables": list_tables,
    "describe_table": describe_table,
    "run_select": run_select,
}
