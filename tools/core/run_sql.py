"""Core tool: execute a read-only SQL query against SQL Server."""
from __future__ import annotations

from typing import Any

import sqlglot
import sqlglot.expressions as exp
from sqlalchemy import text

from config import settings
from db import engine

NAME = "run_sql"
DESCRIPTION = (
    "Execute a read-only T-SQL SELECT query against the connected SQL Server database. "
    "Returns a dict with 'columns' (list of names) and 'rows' (list of value lists). "
    "Results are automatically capped at the configured ROW_LIMIT."
)
INPUT_SCHEMA = {
    "type": "object",
    "properties": {"query": {"type": "string", "description": "T-SQL SELECT query"}},
    "required": ["query"],
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "columns": {"type": "array"},
        "rows": {"type": "array"},
        "row_count": {"type": "integer"},
        "truncated": {"type": "boolean"},
    },
}

_FORBIDDEN_NODES = (
    exp.Drop, exp.Delete, exp.Update, exp.Insert,
    exp.Command, exp.Alter, exp.TruncateTable,
    exp.Transaction, exp.Rollback, exp.Commit,
)


def _validate_sql(query: str) -> None:
    """Raise ValueError if the query is not a pure SELECT."""
    try:
        tree = sqlglot.parse(query, dialect="tsql")
    except Exception as exc:
        raise ValueError(f"SQL parse error: {exc}") from exc

    for statement in tree:
        if not isinstance(statement, exp.Select):
            raise ValueError(
                f"Only SELECT statements are allowed. Got: {type(statement).__name__}"
            )
        for node in statement.walk():
            if isinstance(node, _FORBIDDEN_NODES):
                raise ValueError(f"Forbidden SQL operation: {type(node).__name__}")


def execute(query: str) -> dict[str, Any]:
    _validate_sql(query)
    with engine.connect() as conn:
        result = conn.execute(text(query))
        columns = list(result.keys())
        rows = result.fetchmany(settings.row_limit + 1)
    truncated = len(rows) > settings.row_limit
    rows = rows[: settings.row_limit]
    return {
        "columns": columns,
        "rows": [list(r) for r in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }
