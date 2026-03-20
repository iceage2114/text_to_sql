"""
ChromaDB-backed memory store:
  - query_history    : every interaction ExperienceRecord
  - failure_patterns : unrecoverable errors for retrospective analysis
"""
from __future__ import annotations

import json
import uuid
from typing import Any

import chromadb

from config import settings
from llm import GitHubEmbeddingFunction
from memory.models import ExperienceRecord, FailurePattern

_QUERY_HISTORY = "query_history"
_FAILURE_PATTERNS = "failure_patterns"


def _get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=settings.chroma_path)


def _get_ef() -> GitHubEmbeddingFunction:
    return GitHubEmbeddingFunction()


def _history_col():
    return _get_client().get_or_create_collection(name=_QUERY_HISTORY, embedding_function=_get_ef())


def _failure_col():
    return _get_client().get_or_create_collection(name=_FAILURE_PATTERNS, embedding_function=_get_ef())


# ── Query History ──────────────────────────────────────────────────────────────

def _record_to_meta(record: ExperienceRecord) -> dict:
    """Convert ExperienceRecord to a ChromaDB-safe metadata dict.
    
    ChromaDB only accepts str/int/float/bool scalars — lists must be
    serialised as JSON strings.
    """
    data = record.model_dump(mode="json")
    # Serialise every list value to a JSON string
    return {k: json.dumps(v) if isinstance(v, list) else (v if v is not None else "") for k, v in data.items()}


def _meta_to_record(meta: dict) -> ExperienceRecord:
    """Reverse _record_to_meta: deserialise JSON-string lists back to lists."""
    restored = {}
    for k, v in meta.items():
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                restored[k] = parsed if isinstance(parsed, list) else v
            except (json.JSONDecodeError, ValueError):
                restored[k] = v
        else:
            restored[k] = v
    return ExperienceRecord(**restored)


def save_experience(record: ExperienceRecord) -> None:
    col = _history_col()
    doc = f"Query: {record.user_query}\nSQL: {record.generated_sql or ''}\nSuccess: {record.success}"
    col.upsert(
        documents=[doc],
        ids=[record.query_id],
        metadatas=[_record_to_meta(record)],
    )


def search_similar_queries(query: str, k: int = 5) -> list[ExperienceRecord]:
    """Return top-k successful past experiences similar to the given query."""
    col = _history_col()
    count = col.count()
    if count == 0:
        return []
    results = col.query(
        query_texts=[query],
        n_results=min(k, count),
        where={"success": True},
    )
    records = []
    for meta in results["metadatas"][0]:
        try:
            records.append(_meta_to_record(meta))
        except Exception:
            pass
    return records


def get_recent_history(n: int = 20) -> list[dict[str, Any]]:
    col = _history_col()
    count = col.count()
    if count == 0:
        return []
    results = col.get(limit=min(n, count), include=["metadatas"])
    return results["metadatas"]


def save_example(user_query: str, sql: str) -> str:
    """Save a user-provided question/SQL pair as a high-confidence few-shot example."""
    record = ExperienceRecord(
        query_id=str(uuid.uuid4()),
        user_query=user_query,
        generated_sql=sql,
        evaluation_score=1.0,
        success=True,
        tools_used=[],
        retry_count=0,
    )
    save_experience(record)
    return record.query_id


# ── Failure Patterns ───────────────────────────────────────────────────────────

def _pattern_to_meta(pattern: FailurePattern) -> dict:
    data = pattern.model_dump(mode="json")
    return {k: json.dumps(v) if isinstance(v, list) else (v if v is not None else "") for k, v in data.items()}


def log_failure(error_trace: str, user_query: str, generated_sql: str | None = None) -> str:
    """Log a failure. Returns pattern_id."""
    col = _failure_col()
    pattern_id = str(uuid.uuid4())
    pattern = FailurePattern(
        pattern_id=pattern_id,
        cluster_theme="",
        example_errors=[error_trace],
        example_queries=[user_query],
    )
    doc = f"Error: {error_trace}\nQuery: {user_query}\nSQL: {generated_sql or ''}"
    col.upsert(
        documents=[doc],
        ids=[pattern_id],
        metadatas=[_pattern_to_meta(pattern)],
    )
    return pattern_id


def get_failure_patterns(n: int = 100) -> list[FailurePattern]:
    col = _failure_col()
    count = col.count()
    if count == 0:
        return []
    results = col.get(
        limit=min(n, count),
        where={"resolved": False},
        include=["metadatas"],
    )
    patterns = []
    for meta in results["metadatas"]:
        try:
            # Deserialise list fields stored as JSON strings
            restored = {}
            for k, v in meta.items():
                if isinstance(v, str):
                    try:
                        parsed = json.loads(v)
                        restored[k] = parsed if isinstance(parsed, list) else v
                    except (json.JSONDecodeError, ValueError):
                        restored[k] = v
                else:
                    restored[k] = v
            patterns.append(FailurePattern(**restored))
        except Exception:
            pass
    return patterns


def get_failure_diagnostics(n: int = 50) -> list[dict[str, Any]]:
    """Return unresolved failure patterns with an LLM-generated diagnosis per pattern."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from llm import get_chat_llm

    patterns = get_failure_patterns(n=n)
    if not patterns:
        return []

    _SYSTEM = """\
You are a Text-to-SQL diagnostic expert. Given a failure — an error trace and
the user query that caused it — produce a short diagnosis and a concrete
recommendation for the developer.

Respond with exactly this JSON and nothing else:
{"diagnosis": "<one sentence>", "recommendation": "<one sentence>", "severity": "high|medium|low"}

Severity guide:
  high   — agent cannot answer this class of question at all
  medium — agent sometimes gets it right but is unreliable
  low    — minor cosmetic or formatting issue"""

    llm = get_chat_llm()
    results = []
    for p in patterns:
        error  = p.example_errors[0]  if p.example_errors  else "unknown error"
        query  = p.example_queries[0] if p.example_queries else "unknown query"
        prompt = f"User query: {query}\nError: {error}"
        try:
            resp   = llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
            parsed = json.loads(resp.content.strip())
        except Exception:
            parsed = {"diagnosis": error, "recommendation": "Run retrospective to attempt auto-fix.", "severity": "medium"}
        results.append({
            "pattern_id":     p.pattern_id,
            "query":          query,
            "error":          error,
            "diagnosis":      parsed.get("diagnosis", ""),
            "recommendation": parsed.get("recommendation", ""),
            "severity":       parsed.get("severity", "medium"),
        })
    return results


def mark_pattern_resolved(pattern_id: str, tool_created: str) -> None:
    col = _failure_col()
    existing = col.get(ids=[pattern_id], include=["metadatas", "documents"])
    if not existing["ids"]:
        return
    meta = existing["metadatas"][0]
    # meta values may be JSON-stringified lists — keep them as-is
    meta["resolved"] = True
    meta["tool_created"] = tool_created
    col.upsert(
        documents=existing["documents"],
        ids=[pattern_id],
        metadatas=[meta],
    )
