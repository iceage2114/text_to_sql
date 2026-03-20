"""
Connects to SQL Server and builds a semantic schema dict by introspecting
INFORMATION_SCHEMA views.  Used by schema/store.py and all agents.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from config import settings
from db import engine


def _get_columns(conn) -> dict[str, list[dict]]:
    sql = text("""
        SELECT
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.COLUMN_DEFAULT,
            CASE WHEN kcu.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END AS IS_PRIMARY_KEY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON c.TABLE_NAME = kcu.TABLE_NAME
           AND c.COLUMN_NAME = kcu.COLUMN_NAME
           AND EXISTS (
               SELECT 1 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
               WHERE tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                 AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
           )
        WHERE c.TABLE_SCHEMA = 'dbo'
        ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
    """)
    rows = conn.execute(sql).fetchall()
    tables: dict[str, list[dict]] = {}
    for row in rows:
        tbl = row[0]
        tables.setdefault(tbl, []).append({
            "column": row[1],
            "type": row[2],
            "nullable": row[3],
            "max_length": row[4],
            "precision": row[5],
            "default": row[6],
            "primary_key": row[7] == "YES",
        })
    return tables


def _get_foreign_keys(conn) -> list[dict]:
    sql = text("""
        SELECT
            fk.name         AS fk_name,
            tp.name         AS parent_table,
            cp.name         AS parent_column,
            tr.name         AS ref_table,
            cr.name         AS ref_column
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        JOIN sys.tables tp  ON fkc.parent_object_id    = tp.object_id
        JOIN sys.columns cp ON fkc.parent_object_id    = cp.object_id
                           AND fkc.parent_column_id    = cp.column_id
        JOIN sys.tables tr  ON fkc.referenced_object_id = tr.object_id
        JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id
                           AND fkc.referenced_column_id  = cr.column_id
        ORDER BY parent_table, parent_column
    """)
    rows = conn.execute(sql).fetchall()
    return [
        {
            "fk_name": r[0],
            "parent_table": r[1],
            "parent_column": r[2],
            "ref_table": r[3],
            "ref_column": r[4],
        }
        for r in rows
    ]


def build_semantic_schema() -> dict[str, Any]:
    """
    Return a semantic schema dict:
    {
        "tables": {
            "orders": {
                "columns": {
                    "order_id":    {"type": "int", "primary_key": True, ...},
                    "customer_id": {"type": "int", "fk": "customers.id", ...},
                },
                "business_meaning": "",
                "foreign_keys": [...]
            }
        }
    }
    """
    with engine.connect() as conn:
        raw_columns = _get_columns(conn)
        fks = _get_foreign_keys(conn)

    fk_by_table: dict[str, list[dict]] = {}
    for fk in fks:
        fk_by_table.setdefault(fk["parent_table"], []).append(fk)

    schema: dict[str, Any] = {"tables": {}}
    for table, columns in raw_columns.items():
        col_dict = {}
        for col in columns:
            entry: dict[str, Any] = {
                "type": col["type"],
                "nullable": col["nullable"] == "YES",
                "primary_key": col["primary_key"],
            }
            if col["max_length"]:
                entry["max_length"] = col["max_length"]
            for fk in fk_by_table.get(table, []):
                if fk["parent_column"] == col["column"]:
                    entry["fk"] = f"{fk['ref_table']}.{fk['ref_column']}"
            col_dict[col["column"]] = entry

        schema["tables"][table] = {
            "columns": col_dict,
            "business_meaning": "",
            "foreign_keys": fk_by_table.get(table, []),
        }

    return schema


if __name__ == "__main__":
    s = build_semantic_schema()
    print(json.dumps(s, indent=2))
