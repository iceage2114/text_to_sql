from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExperienceRecord(BaseModel):
    query_id: str = Field(description="UUID for this interaction")
    user_query: str
    generated_sql: str | None = None
    sql_result_preview: str | None = None
    evaluation_score: float | None = None
    evaluation_explanation: str | None = None
    error_trace: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    retry_count: int = 0
    success: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class FailurePattern(BaseModel):
    pattern_id: str
    cluster_theme: str
    example_errors: list[str] = Field(default_factory=list)
    example_queries: list[str] = Field(default_factory=list)
    count: int = 1
    tool_created: str | None = None
    resolved: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
