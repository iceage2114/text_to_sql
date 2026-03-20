"""
Stores and retrieves schema information using ChromaDB + GitHub Models embeddings.
Each document is a natural-language description of one table.

Ingestion sources:
  1. Live database  — ingest_schema()           reads INFORMATION_SCHEMA directly
  2. DDL SQL file   — ingest_schema_from_ddl()  parses a .sql file (e.g. ddl_output.sql)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import chromadb

from config import settings
from llm import GitHubEmbeddingFunction
from schema.ingestion import build_semantic_schema

_COLLECTION = "schema_embeddings"


def _get_collection():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection(
        name=_COLLECTION,
        embedding_function=GitHubEmbeddingFunction(),
    )


def _table_to_doc(table_name: str, table_def: dict) -> str:
    cols = table_def["columns"]
    pk_cols = [c for c, v in cols.items() if v.get("primary_key")]
    fk_lines = [
        f"  - {fk['parent_column']} references {fk['ref_table']}.{fk['ref_column']}"
        for fk in table_def.get("foreign_keys", [])
    ]
    doc = f"Table: {table_name}\n"
    doc += f"Business meaning: {table_def.get('business_meaning') or 'N/A'}\n"
    doc += f"Primary keys: {', '.join(pk_cols) or 'none'}\n"
    doc += "Columns:\n"
    for name, meta in cols.items():
        fk_note = f" (FK -> {meta['fk']})" if meta.get("fk") else ""
        doc += f"  - {name}: {meta['type']}{fk_note}\n"
    if fk_lines:
        doc += "Foreign keys:\n" + "\n".join(fk_lines) + "\n"
    return doc


def ingest_schema(schema: dict[str, Any] | None = None) -> int:
    """Ingest (or re-ingest) all tables from the live database into ChromaDB."""
    if schema is None:
        schema = build_semantic_schema()
    col = _get_collection()
    documents, ids, metadatas = [], [], []
    for table_name, table_def in schema["tables"].items():
        doc = _table_to_doc(table_name, table_def)
        documents.append(doc)
        ids.append(f"table::{table_name}")
        metadatas.append({"table_name": table_name, "schema_json": json.dumps(table_def)})
    col.upsert(documents=documents, ids=ids, metadatas=metadatas)
    return len(documents)


def _parse_ddl_file(ddl_path: Path) -> dict[str, Any]:
    """
    Parse a DDL SQL file produced by test_ddl.py into the same semantic schema
    dict format that build_semantic_schema() returns.

    Handles:
      - CREATE TABLE [schema].[table] blocks
      - Column definitions with type, nullability, defaults
      - CONSTRAINT [pk] PRIMARY KEY (...)
      - CONSTRAINT [fk] FOREIGN KEY (...) REFERENCES ...
    """
    text = ddl_path.read_text(encoding="utf-8")

    # Split on table header comments: -- [schema].[table]
    table_header = re.compile(
        r"--\s*=+\s*\n--\s*\[(?P<schema>[^\]]+)\]\.\[(?P<table>[^\]]+)\]\s*\n--\s*=+",
        re.MULTILINE,
    )

    col_line = re.compile(
        r"^\s*\[(?P<col>[^\]]+)\]\s+(?P<type>[A-Z]+)"
        r"(?:\((?P<len>[^)]+)\))?"
        r"(?:\s+DEFAULT\s+(?P<default>\S+))?"
        r"\s+(?P<null>NOT NULL|NULL)",
        re.IGNORECASE,
    )
    pk_line  = re.compile(r"CONSTRAINT\s+\[[^\]]+\]\s+PRIMARY KEY\s*\((?P<cols>[^)]+)\)", re.IGNORECASE)
    fk_line  = re.compile(
        r"CONSTRAINT\s+\[(?P<fkname>[^\]]+)\]\s+FOREIGN KEY\s*\((?P<pcols>[^)]+)\)"
        r"\s+REFERENCES\s+\[(?P<rschema>[^\]]+)\]\.\[(?P<rtable>[^\]]+)\]\s*\((?P<rcols>[^)]+)\)",
        re.IGNORECASE | re.DOTALL,
    )

    schema_dict: dict[str, Any] = {"tables": {}}
    matches = list(table_header.finditer(text))

    for i, m in enumerate(matches):
        tbl_schema = m.group("schema")
        tbl_name   = m.group("table")
        start      = m.end()
        end        = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block      = text[start:end]

        # Extract just the CREATE TABLE body
        ct_match = re.search(r"CREATE TABLE[^(]+\((.+?)\);", block, re.DOTALL | re.IGNORECASE)
        body = ct_match.group(1) if ct_match else block

        columns:     dict[str, Any] = {}
        pk_cols:     list[str]      = []
        foreign_keys: list[dict]   = []

        for line in body.splitlines():
            cm = col_line.match(line)
            if cm:
                type_str = cm.group("type").upper()
                if cm.group("len"):
                    type_str += f"({cm.group('len')})"
                columns[cm.group("col")] = {
                    "type":        type_str,
                    "nullable":    cm.group("null").upper() == "NULL",
                    "primary_key": False,
                    "default":     cm.group("default"),
                }
                continue

            pm = pk_line.search(line)
            if pm:
                pk_cols = [c.strip().strip("[]") for c in pm.group("cols").split(",")]
                for c in pk_cols:
                    if c in columns:
                        columns[c]["primary_key"] = True
                continue

            fm = fk_line.search(line)
            if fm:
                parent_cols = [c.strip().strip("[]") for c in fm.group("pcols").split(",")]
                ref_cols    = [c.strip().strip("[]") for c in fm.group("rcols").split(",")]
                for pc, rc in zip(parent_cols, ref_cols):
                    if pc in columns:
                        columns[pc]["fk"] = f"{fm.group('rtable')}.{rc}"
                foreign_keys.append({
                    "fk_name":      fm.group("fkname"),
                    "parent_table": tbl_name,
                    "parent_column": parent_cols[0] if parent_cols else "",
                    "ref_table":    fm.group("rtable"),
                    "ref_column":   ref_cols[0] if ref_cols else "",
                    "ref_schema":   fm.group("rschema"),
                })

        schema_dict["tables"][tbl_name] = {
            "columns":          columns,
            "business_meaning": "",
            "foreign_keys":     foreign_keys,
            "schema":           tbl_schema,
        }

    return schema_dict


def ingest_schema_from_ddl(ddl_path: str | Path = "ddl_output.sql") -> int:
    """
    Parse ddl_path (default: ddl_output.sql) and ingest all tables into ChromaDB.

    Use this instead of ingest_schema() when:
      - You want to work offline (no live DB connection needed)
      - You have pre-annotated the DDL with business meanings as SQL comments
      - You want to lock the schema to a specific snapshot

    Returns the number of tables upserted.
    """
    path = Path(ddl_path)
    if not path.exists():
        raise FileNotFoundError(f"DDL file not found: {path.resolve()}")
    schema = _parse_ddl_file(path)
    return ingest_schema(schema)


def ingest_schema_from_semantic(
    ddl_path: str | Path = "ddl_output.sql",
    annotations_path: Path | None = None,
) -> int:
    """
    Build the fully-enriched semantic schema (DDL + annotations.yaml) and
    ingest it into ChromaDB using enriched natural-language documents.

    This produces the richest possible ChromaDB embeddings because each
    table document contains:
      - Business name and purpose
      - Column descriptions
      - Synonym terms users might say
      - Relevant metric definitions

    Returns the number of tables upserted.
    """
    from semantic.layer import build_enriched_document, build_semantic_schema as _build

    enriched = _build(ddl_path=ddl_path, annotations_path=annotations_path)
    metrics  = enriched.get("metrics", [])

    col = _get_collection()
    documents, ids, metadatas = [], [], []

    for table_name, table_def in enriched["tables"].items():
        doc = build_enriched_document(table_name, table_def, metrics=metrics)
        documents.append(doc)
        ids.append(f"table::{table_name}")
        metadatas.append({"table_name": table_name, "schema_json": json.dumps(table_def)})

    col.upsert(documents=documents, ids=ids, metadatas=metadatas)
    return len(documents)


def search_schema(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Semantic search over schema embeddings. Returns relevant table dicts."""
    col = _get_collection()
    count = col.count()
    if count == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(k, count))
    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append({
            "table_name": meta["table_name"],
            "doc": doc,
            "schema_def": json.loads(meta["schema_json"]),
        })
    return output


def get_full_schema_summary(max_tables: int = 30) -> str:
    """Return a text summary of all tables for planner context."""
    col = _get_collection()
    count = col.count()
    if count == 0:
        return "No schema ingested yet. Run POST /ingest-schema first."
    results = col.get(limit=min(max_tables, count), include=["documents"])
    return "\n\n".join(results["documents"])
