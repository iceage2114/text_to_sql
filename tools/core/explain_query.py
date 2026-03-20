"""Core tool: return the SQL Server estimated execution plan."""
from __future__ import annotations

from typing import Any

from db import engine

NAME = "explain_query"
DESCRIPTION = (
    "Return the SQL Server estimated execution plan for a T-SQL query using "
    "SET SHOWPLAN_TEXT ON.  Useful for diagnosing slow or incorrect queries."
)
INPUT_SCHEMA = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"plan": {"type": "string"}},
}


def execute(query: str) -> dict[str, Any]:
    with engine.raw_connection() as raw_conn:
        cursor = raw_conn.cursor()
        cursor.execute("SET SHOWPLAN_TEXT ON")
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            plan = "\n".join(str(r[0]) for r in rows)
        finally:
            cursor.execute("SET SHOWPLAN_TEXT OFF")
    return {"plan": plan}
