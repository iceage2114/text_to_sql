"""
FastAPI REST API for the Text-to-SQL Self-Learning Agent.

Endpoints:
  POST /query            Run user query through the LangGraph agent
  GET  /tools            List all registered tools (core + generated)
  GET  /schema           Full schema summary from ChromaDB
  GET  /history          Last N query interactions
  POST /retrospective    Trigger a retrospective self-improvement run
  POST /ingest-schema    (Re)ingest schema from the connected MSSQL database
  GET  /health           Health check
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Text-to-SQL Self-Learning Agent",
    description=(
        "LangGraph multi-agent system: natural language → T-SQL, "
        "with self-correction, memory, and autonomous tool creation."
    ),
    version="1.0.0",
)


# ── Request / Response models ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    max_retries: int | None = None


class QueryResponse(BaseModel):
    query_id: str
    user_query: str
    generated_sql: str | None
    result: dict[str, Any]
    evaluation_score: float
    evaluation_explanation: str
    retry_count: int
    tools_used: list[str]
    success: bool


class RetrospectiveRequest(BaseModel):
    failure_limit: int | None = None


class ExampleRequest(BaseModel):
    query: str
    sql: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    from graph.graph import run_query as _run
    from config import settings
    try:
        state = _run(req.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    score = state.get("evaluation_score", 0.0)
    return QueryResponse(
        query_id              = state.get("query_id", ""),
        user_query            = req.query,
        generated_sql         = state.get("generated_sql"),
        result                = state.get("sql_result", {}),
        evaluation_score      = score,
        evaluation_explanation= state.get("evaluation_explanation", ""),
        retry_count           = state.get("retry_count", 0),
        tools_used            = state.get("tools_used", []),
        success               = score >= settings.critic_threshold and not state.get("error_trace"),
    )


@app.get("/tools")
def list_tools():
    from tools.registry import registry
    return {"tools": registry.list_tools()}


@app.get("/schema")
def get_schema():
    from schema.store import get_full_schema_summary
    return {"schema_summary": get_full_schema_summary()}


@app.get("/history")
def get_history(n: int = 20):
    from memory.store import get_recent_history
    return {"history": get_recent_history(n=n)}


@app.post("/retrospective")
def run_retrospective(req: RetrospectiveRequest = RetrospectiveRequest()):
    from retrospective.runner import run_retrospective as _retro
    return _retro(failure_limit=req.failure_limit)


@app.post("/examples")
def save_example(req: ExampleRequest):
    """Save a user-provided question/SQL pair as a high-confidence few-shot example."""
    from memory.store import save_example as _save
    try:
        query_id = _save(req.query, req.sql)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"saved": True, "query_id": query_id}


@app.get("/failures")
def get_failures():
    """Return unresolved failure patterns with an LLM-generated diagnosis."""
    from memory.store import get_failure_diagnostics
    try:
        diagnostics = get_failure_diagnostics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"failures": diagnostics, "count": len(diagnostics)}


@app.post("/ingest-schema")
def ingest_schema():
    from schema.store import ingest_schema as _ingest
    try:
        count = _ingest()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"source": "live_database", "tables_ingested": count}


@app.post("/ingest-schema/ddl")
def ingest_schema_from_ddl(ddl_path: str = "ddl_output.sql"):
    """
    Ingest schema from a local DDL SQL file instead of querying the live database.
    Defaults to ddl_output.sql in the project root.
    """
    from schema.store import ingest_schema_from_ddl as _ingest_ddl
    try:
        count = _ingest_ddl(ddl_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"source": ddl_path, "tables_ingested": count}


@app.post("/ingest-schema/semantic")
def ingest_schema_semantic(ddl_path: str = "ddl_output.sql"):
    """
    Ingest the fully-enriched semantic schema: DDL + annotations.yaml merged.
    Produces the richest ChromaDB embeddings with business meanings, column
    descriptions, synonyms, and metric definitions.
    Recommended for best SQL generation quality.
    """
    from schema.store import ingest_schema_from_semantic as _ingest_sem
    try:
        count = _ingest_sem(ddl_path=ddl_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"source": "semantic_layer", "ddl": ddl_path, "tables_ingested": count}


@app.get("/health")
def health():
    return {"status": "ok"}
