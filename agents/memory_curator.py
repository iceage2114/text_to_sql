"""
Memory Curator agent — terminal graph node.
Saves the full interaction as an ExperienceRecord.
On failure, also logs a FailurePattern for retrospective analysis.
"""
from __future__ import annotations

import json
import uuid

from config import settings
from graph.state import AgentState
from memory.models import ExperienceRecord
from memory.store import log_failure, save_experience


def run_memory_curator(state: AgentState) -> dict:
    query_id = state.get("query_id") or str(uuid.uuid4())
    score    = state.get("evaluation_score", 0.0)
    success  = score >= settings.critic_threshold and not state.get("error_trace")

    result       = state.get("sql_result", {})
    preview_rows = result.get("rows", [])[:3]
    preview      = json.dumps(
        {"columns": result.get("columns", []), "rows": preview_rows}, default=str
    )

    record = ExperienceRecord(
        query_id            = query_id,
        user_query          = state["user_query"],
        generated_sql       = state.get("generated_sql"),
        sql_result_preview  = preview,
        evaluation_score    = score,
        evaluation_explanation = state.get("evaluation_explanation"),
        error_trace         = state.get("error_trace"),
        tools_used          = state.get("tools_used", []),
        retry_count         = state.get("retry_count", 0),
        success             = success,
    )
    save_experience(record)

    if not success:
        log_failure(
            error_trace  = state.get("error_trace") or state.get("evaluation_explanation", "low score"),
            user_query   = state["user_query"],
            generated_sql= state.get("generated_sql"),
        )

    return {"memory_saved": True, "query_id": query_id}
