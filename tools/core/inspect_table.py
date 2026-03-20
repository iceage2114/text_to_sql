"""Core tool: inspect a table's schema and constraints."""
from __future__ import annotations

from typing import Any

from sqlalchemy import text

from db import engine

NAME = "inspect_table"
DESCRIPTION = (
    "Return detailed metadata for a specific SQL Server table: columns, types, "
    "nullable flags, primary keys, foreign keys, and indexes."
)
INPUT_SCHEMA = {
    "type": "object",
    "properties": {"table_name": {"type": "string"}},
    "required": ["table_name"],
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "table_name": {"type": "string"},
        "columns": {"type": "array"},
        "indexes": {"type": "array"},
    },
}


def execute(table_name: str) -> dict[str, Any]:
    with engine.connect() as conn:
        col_sql = text("""
            SELECT
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.IS_NULLABLE,
                c.CHARACTER_MAXIMUM_LENGTH,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS IS_PK,
                fk_ref.REF_TABLE,
                fk_ref.REF_COLUMN
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN (
                SELECT kcu.TABLE_NAME, kcu.COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                    ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
            LEFT JOIN (
                SELECT
                    fkc.parent_object_id,
                    cp.name AS PARENT_COL,
                    tr.name AS REF_TABLE,
                    cr.name AS REF_COLUMN
                FROM sys.foreign_key_columns fkc
                JOIN sys.tables tr  ON fkc.referenced_object_id = tr.object_id
                JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id
                                   AND fkc.parent_column_id  = cp.column_id
                JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id
                                   AND fkc.referenced_column_id  = cr.column_id
            ) fk_ref ON OBJECT_ID(c.TABLE_NAME) = fk_ref.parent_object_id
                    AND c.COLUMN_NAME = fk_ref.PARENT_COL
            WHERE c.TABLE_NAME = :tname AND c.TABLE_SCHEMA = 'dbo'
            ORDER BY c.ORDINAL_POSITION
        """)
        rows = conn.execute(col_sql, {"tname": table_name}).fetchall()

        idx_sql = text("""
            SELECT i.name, i.is_unique, i.is_primary_key, c.name AS col
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id
                                     AND i.index_id  = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id
                              AND ic.column_id = c.column_id
            JOIN sys.tables t  ON i.object_id  = t.object_id
            WHERE t.name = :tname
            ORDER BY i.name, ic.key_ordinal
        """)
        idx_rows = conn.execute(idx_sql, {"tname": table_name}).fetchall()

    columns = [
        {
            "name": r[0], "type": r[1], "nullable": r[2] == "YES",
            "max_length": r[3], "primary_key": bool(r[4]),
            "fk_table": r[5], "fk_column": r[6],
        }
        for r in rows
    ]

    indexes: dict[str, dict] = {}
    for r in idx_rows:
        n = r[0]
        if n not in indexes:
            indexes[n] = {"name": n, "unique": bool(r[1]), "primary": bool(r[2]), "columns": []}
        indexes[n]["columns"].append(r[3])

    return {"table_name": table_name, "columns": columns, "indexes": list(indexes.values())}
