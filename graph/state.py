from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict):
    # Input
    user_query: str

    # Schema context retrieved from ChromaDB
    schema_context: str

    # Planner output
    plan: str

    # SQL Writer output
    generated_sql: str

    # Executor output
    sql_result: dict[str, Any]
    error_trace: str

    # Critic output
    evaluation_score: float
    evaluation_explanation: str

    # Control flow
    retry_count: int
    max_retries: int
    tool_builder_invoked: bool

    # Tool orchestration
    requested_tool_calls: list[dict]
    tool_results: dict[str, Any]
    needs_sql_rewrite: bool

    # Audit
    tools_used: list[str]
    memory_saved: bool
    query_id: str
