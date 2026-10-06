"""Very small SELECT-only gate.

Not a SQL parser. Strips comments and string literals, then looks at
keywords. Good enough to stop an agent from doing something dumb against
the demo db, not something I'd put in front of a prod warehouse alone.
"""
import re

BLOCKED = {
    "insert", "update", "delete", "drop", "alter", "create", "replace",
    "truncate", "attach", "detach", "pragma", "vacuum", "grant", "revoke",
    "merge", "copy", "call", "exec", "execute",
}

_comment_line = re.compile(r"--[^\n]*")
_comment_block = re.compile(r"/\*.*?\*/", re.S)
_string = re.compile(r"'(?:[^']|'')*'")


def _strip(sql: str) -> str:
    sql = _comment_block.sub(" ", sql)
    sql = _comment_line.sub(" ", sql)
    sql = _string.sub("''", sql)
    return sql


def check_select(sql: str, max_limit: int = 200) -> tuple[bool, str]:
    """Return (ok, reason). ok=False means don't run it."""
    if not sql or not sql.strip():
        return False, "empty query"
    clean = _strip(sql).strip().rstrip(";").strip()
    if ";" in clean:
        return False, "multiple statements not allowed"
    words = re.findall(r"[a-z_]+", clean.lower())
    if not words or words[0] not in ("select", "with"):
        return False, "only SELECT / WITH queries are allowed"
    bad = BLOCKED.intersection(words)
    if bad:
        return False, f"blocked keyword: {sorted(bad)[0]}"
    m = re.search(r"\blimit\s+(\d+)", clean, re.I)
    if m and int(m.group(1)) > max_limit:
        return False, f"limit {m.group(1)} is above max {max_limit}"
    return True, "ok"


def ensure_limit(sql: str, default: int = 50) -> str:
    clean = sql.strip().rstrip(";")
    if re.search(r"\blimit\s+\d+", _strip(clean), re.I):
        return clean
    return f"{clean} LIMIT {default}"
