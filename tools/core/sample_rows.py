"""Core tool: fetch sample rows from a table."""
from __future__ import annotations

from typing import Any

from sqlalchemy import text

from db import engine

NAME = "sample_rows"
DESCRIPTION = (
    "Fetch a small sample of rows from a table to understand its data shape. "
    "Uses SELECT TOP so it is safe on large tables."
)
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "table_name": {"type": "string"},
        "limit": {"type": "integer", "default": 5, "description": "Rows to return (max 20)"},
    },
    "required": ["table_name"],
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"columns": {"type": "array"}, "rows": {"type": "array"}},
}


def execute(table_name: str, limit: int = 5) -> dict[str, Any]:
    limit = min(max(1, limit), 20)
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT TOP {limit} * FROM [{table_name}]"))
        columns = list(result.keys())
        rows = [list(r) for r in result.fetchall()]
    return {"columns": columns, "rows": rows}
