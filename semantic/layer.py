"""
semantic/layer.py

Builds an enriched schema dict by merging:
  1. Raw DDL (from ddl_output.sql via _parse_ddl_file)
  2. Business annotations (from semantic/annotations.yaml)

The result is the same format as build_semantic_schema() but every annotated
table/column gets a rich natural-language description that the LLM can use
to generate far more accurate SQL.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_ANNOTATIONS_PATH = Path(__file__).parent / "annotations.yaml"


# ── public API ────────────────────────────────────────────────────────────────

def load_annotations(path: Path | None = None) -> dict:
    p = path or _ANNOTATIONS_PATH
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_semantic_schema(
    ddl_path: str | Path = "ddl_output.sql",
    annotations_path: Path | None = None,
) -> dict[str, Any]:
    """
    Parse the DDL file and merge with annotations.
    Returns the same dict structure as schema.ingestion.build_semantic_schema().
    """
    from schema.store import _parse_ddl_file

    ddl   = _parse_ddl_file(Path(ddl_path))
    annot = load_annotations(annotations_path)

    table_annots  = annot.get("tables",   {})
    global_metrics= annot.get("metrics",  [])
    global_synonyms= annot.get("synonyms", [])

    for table_name, table_def in ddl["tables"].items():
        ta = table_annots.get(table_name, {})

        # Business name and description
        if ta.get("business_name"):
            table_def["business_name"] = ta["business_name"]
        if ta.get("description"):
            table_def["business_meaning"] = ta["description"].strip()

        # Column-level enrichment
        col_annots = ta.get("columns", {})
        for col_name, col_def in table_def["columns"].items():
            ca = col_annots.get(col_name, {})
            if ca.get("description"):
                col_def["description"] = ca["description"]
            if ca.get("unit"):
                col_def["unit"] = ca["unit"]

        # Attach global synonyms that reference this table
        table_synonyms = [
            s["terms"] for s in global_synonyms
            if s.get("maps_to") == table_name
        ]
        if table_synonyms:
            table_def["synonyms"] = table_synonyms[0]

    # Attach global metrics to the schema root
    ddl["metrics"]  = global_metrics
    ddl["synonyms"] = global_synonyms
    return ddl


def build_enriched_document(
    table_name: str,
    table_def: dict,
    metrics: list[dict] | None = None,
) -> str:
    """
    Convert a single enriched table_def into a descriptive text document
    for ChromaDB embedding.  This is much richer than the raw DDL version.
    """
    lines: list[str] = []

    # Header
    schema_prefix = table_def.get("schema", "dbo")
    biz_name = table_def.get("business_name", table_name)
    lines.append(f"Table: {table_name}  (Business name: {biz_name})")
    lines.append(f"Schema: {schema_prefix}")

    meaning = table_def.get("business_meaning", "").strip()
    if meaning:
        lines.append(f"Business purpose: {meaning}")

    synonyms = table_def.get("synonyms", [])
    if synonyms:
        lines.append(f"Also known as: {', '.join(synonyms)}")

    # Primary keys
    pks = [c for c, v in table_def["columns"].items() if v.get("primary_key")]
    if pks:
        lines.append(f"Primary keys: {', '.join(pks)}")

    # Columns
    lines.append("Columns:")
    for col_name, col_def in table_def["columns"].items():
        type_str = col_def.get("type", "")
        nullable = " (nullable)" if col_def.get("nullable") else ""
        fk_note  = f" -> FK to {col_def['fk']}" if col_def.get("fk") else ""
        pk_note  = " [PK]" if col_def.get("primary_key") else ""
        desc     = col_def.get("description", "")
        desc_str = f"  // {desc}" if desc else ""
        lines.append(f"  - [{col_name}]: {type_str}{pk_note}{fk_note}{nullable}{desc_str}")

    # Foreign keys
    fks = table_def.get("foreign_keys", [])
    if fks:
        lines.append("Relationships:")
        for fk in fks:
            lines.append(
                f"  - {fk.get('parent_column','?')} references "
                f"{fk.get('ref_schema','dbo')}.{fk.get('ref_table','?')}"
                f".{fk.get('ref_column','?')}"
            )

    # Relevant global metrics
    if metrics:
        relevant = [
            m for m in metrics
            if table_name.lower() in m.get("sql", "").lower()
        ]
        if relevant:
            lines.append("Common metrics for this table:")
            for m in relevant:
                lines.append(f"  - {m['name']}: {m['description']}")
                lines.append(f"    SQL: {m['sql']}")

    return "\n".join(lines)
