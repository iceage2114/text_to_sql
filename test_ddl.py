"""
test_ddl.py

Connects to AdventureWorks2019 on JONATHANS-PC\\SQLEXPRESS and prints
the reconstructed DDL for every user table in the database:
  - CREATE TABLE statement (columns + types + nullability + defaults)
  - PRIMARY KEY constraints
  - FOREIGN KEY constraints
  - Indexes (non-PK)

Output is also saved to ddl_output.sql in the same directory.

Usage:
    python test_ddl.py
    python test_ddl.py --schema Sales        # filter to one schema
    python test_ddl.py --out my_ddl.sql      # custom output file
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pyodbc

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=JONATHANS-PC\\SQLEXPRESS;"
    "DATABASE=AdventureWorks2019;"
    "Trusted_Connection=yes"
)


# ── helpers ───────────────────────────────────────────────────────────────────

def get_tables(cursor, schema_filter: str | None) -> list[tuple[str, str]]:
    query = """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
    """
    params: list = []
    if schema_filter:
        query += " AND TABLE_SCHEMA = ?"
        params.append(schema_filter)
    query += " ORDER BY TABLE_SCHEMA, TABLE_NAME"
    cursor.execute(query, params)
    return cursor.fetchall()


def get_columns(cursor, schema: str, table: str) -> list[dict]:
    cursor.execute("""
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            c.ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
    """, (schema, table))
    cols = []
    for r in cursor.fetchall():
        cols.append({
            "name":      r[0],
            "type":      r[1],
            "max_len":   r[2],
            "precision": r[3],
            "scale":     r[4],
            "nullable":  r[5] == "YES",
            "default":   r[6],
        })
    return cols


def format_type(col: dict) -> str:
    t = col["type"].upper()
    if t in ("CHAR", "VARCHAR", "NCHAR", "NVARCHAR", "BINARY", "VARBINARY"):
        length = col["max_len"]
        if length is None or length == -1:
            return f"{t}(MAX)"
        return f"{t}({length})"
    if t in ("DECIMAL", "NUMERIC"):
        return f"{t}({col['precision']},{col['scale']})"
    return t


def get_primary_keys(cursor, schema: str, table: str) -> list[str]:
    cursor.execute("""
        SELECT kcu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
           AND tc.TABLE_SCHEMA    = kcu.TABLE_SCHEMA
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
          AND tc.TABLE_SCHEMA = ?
          AND tc.TABLE_NAME   = ?
        ORDER BY kcu.ORDINAL_POSITION
    """, (schema, table))
    return [r[0] for r in cursor.fetchall()]


def get_foreign_keys(cursor, schema: str, table: str) -> list[dict]:
    cursor.execute("""
        SELECT
            fk.name                   AS fk_name,
            cp.name                   AS parent_col,
            tr.name                   AS ref_table,
            SCHEMA_NAME(tr.schema_id) AS ref_schema,
            cr.name                   AS ref_col
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc
            ON fk.object_id = fkc.constraint_object_id
        JOIN sys.tables tp
            ON fkc.parent_object_id = tp.object_id
        JOIN sys.schemas sp
            ON tp.schema_id = sp.schema_id
        JOIN sys.columns cp
            ON fkc.parent_object_id = cp.object_id
           AND fkc.parent_column_id = cp.column_id
        JOIN sys.tables tr
            ON fkc.referenced_object_id = tr.object_id
        JOIN sys.columns cr
            ON fkc.referenced_object_id = cr.object_id
           AND fkc.referenced_column_id = cr.column_id
        WHERE sp.name = ? AND tp.name = ?
        ORDER BY fk.name, fkc.constraint_column_id
    """, (schema, table))
    fks: dict[str, dict] = {}
    for r in cursor.fetchall():
        name = r[0]
        if name not in fks:
            fks[name] = {
                "name":       name,
                "parent_cols": [],
                "ref_schema": r[3],
                "ref_table":  r[2],
                "ref_cols":   [],
            }
        fks[name]["parent_cols"].append(r[1])
        fks[name]["ref_cols"].append(r[4])
    return list(fks.values())


def get_indexes(cursor, schema: str, table: str) -> list[dict]:
    cursor.execute("""
        SELECT
            i.name       AS idx_name,
            i.is_unique,
            c.name       AS col_name,
            ic.is_descending_key
        FROM sys.indexes i
        JOIN sys.index_columns ic
            ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c
            ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        JOIN sys.tables t
            ON i.object_id = t.object_id
        JOIN sys.schemas s
            ON t.schema_id = s.schema_id
        WHERE s.name = ? AND t.name = ?
          AND i.is_primary_key = 0
          AND i.type > 0
        ORDER BY i.name, ic.key_ordinal
    """, (schema, table))
    idxs: dict[str, dict] = {}
    for r in cursor.fetchall():
        name = r[0]
        if name not in idxs:
            idxs[name] = {"name": name, "unique": bool(r[1]), "cols": []}
        direction = " DESC" if r[3] else ""
        idxs[name]["cols"].append(f"[{r[2]}]{direction}")
    return list(idxs.values())


# ── DDL builder ───────────────────────────────────────────────────────────────

def build_table_ddl(cursor, schema: str, table: str) -> str:
    lines: list[str] = []
    lines.append(f"-- {'='*70}")
    lines.append(f"-- [{schema}].[{table}]")
    lines.append(f"-- {'='*70}")
    lines.append(f"CREATE TABLE [{schema}].[{table}] (")

    columns  = get_columns(cursor, schema, table)
    pks      = get_primary_keys(cursor, schema, table)
    fks      = get_foreign_keys(cursor, schema, table)

    col_defs: list[str] = []
    for col in columns:
        type_str     = format_type(col)
        nullable_str = "NULL" if col["nullable"] else "NOT NULL"
        default_str  = f" DEFAULT {col['default']}" if col["default"] else ""
        col_defs.append(
            f"    [{col['name']}] {type_str}{default_str} {nullable_str}"
        )

    if pks:
        pk_cols = ", ".join(f"[{c}]" for c in pks)
        col_defs.append(f"    CONSTRAINT [PK_{table}] PRIMARY KEY ({pk_cols})")

    for fk in fks:
        parent = ", ".join(f"[{c}]" for c in fk["parent_cols"])
        ref    = ", ".join(f"[{c}]" for c in fk["ref_cols"])
        col_defs.append(
            f"    CONSTRAINT [{fk['name']}] FOREIGN KEY ({parent})\n"
            f"        REFERENCES [{fk['ref_schema']}].[{fk['ref_table']}] ({ref})"
        )

    lines.append(",\n".join(col_defs))
    lines.append(");")

    for idx in get_indexes(cursor, schema, table):
        unique = "UNIQUE " if idx["unique"] else ""
        cols   = ", ".join(idx["cols"])
        lines.append(
            f"CREATE {unique}INDEX [{idx['name']}]\n"
            f"    ON [{schema}].[{table}] ({cols});"
        )

    lines.append("")
    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Export DDL from AdventureWorks2019")
    parser.add_argument("--schema", default=None, help="Filter to one schema (e.g. Sales)")
    parser.add_argument("--out",    default="ddl_output.sql", help="Output file path")
    args = parser.parse_args()

    print(f"Connecting to JONATHANS-PC\\SQLEXPRESS / AdventureWorks2019 ...")
    try:
        conn = pyodbc.connect(CONN_STR, timeout=10)
    except pyodbc.Error as exc:
        print(f"Connection failed: {exc}", file=sys.stderr)
        sys.exit(1)

    cursor = conn.cursor()
    tables = get_tables(cursor, args.schema)

    if not tables:
        filter_msg = f" in schema '{args.schema}'" if args.schema else ""
        print(f"No tables found{filter_msg}.")
        conn.close()
        return

    print(f"Found {len(tables)} table(s). Generating DDL ...")

    ddl_parts: list[str] = [
        "-- DDL export: AdventureWorks2019",
        f"-- Server : JONATHANS-PC\\SQLEXPRESS",
        f"-- Tables : {len(tables)}",
        f"-- Schema filter: {args.schema or '(all)'}",
        "",
    ]

    for schema, table in tables:
        try:
            ddl_parts.append(build_table_ddl(cursor, schema, table))
        except Exception as exc:
            ddl_parts.append(f"-- ERROR generating DDL for [{schema}].[{table}]: {exc}\n")
            print(f"  WARNING: skipped [{schema}].[{table}] — {exc}")

    conn.close()

    full_ddl = "\n".join(ddl_parts)

    out_path = Path(args.out)
    out_path.write_text(full_ddl, encoding="utf-8")
    print(f"\nDDL written to: {out_path.resolve()}")
    print(f"Tables exported: {len(tables)}")

    # Print a short preview
    preview_lines = full_ddl.splitlines()[:40]
    print("\n--- Preview (first 40 lines) ---")
    print("\n".join(preview_lines))


if __name__ == "__main__":
    main()
