"""
Retrospective runner.

Fetches unresolved FailurePatterns from ChromaDB, clusters them into
themes using the LLM, then invokes the ToolBuilder for each theme.
Can be triggered manually via POST /retrospective or run on a schedule.
"""
from __future__ import annotations

import json
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from agents.tool_builder import run_tool_builder
from config import settings
from llm import get_chat_llm
from memory.store import get_failure_patterns, mark_pattern_resolved
from tools.registry import registry

_SYSTEM_CLUSTER = """\
You are a failure analysis expert.  Given a list of error traces and user
queries from a Text-to-SQL system, group them into distinct failure themes.

Return a JSON array:
[
  {
    "theme": "descriptive theme name",
    "pattern_ids": ["id1", "id2"],
    "representative_error": "one representative error string",
    "representative_query": "one representative user query"
  }
]

Return ONLY valid JSON — no markdown, no explanation.
"""

_llm = get_chat_llm()


def run_retrospective(failure_limit: int | None = None) -> dict:
    """
    Main entry point.
    Returns a summary dict: patterns reviewed, clusters found, tools created.
    """
    n        = failure_limit or settings.retrospective_failure_limit
    patterns = get_failure_patterns(n=n)

    if not patterns:
        return {"message": "No unresolved failure patterns found.", "tools_created": []}

    failures_text = json.dumps(
        [
            {
                "id":    p.pattern_id,
                "error": p.example_errors[0] if p.example_errors else "",
                "query": p.example_queries[0] if p.example_queries else "",
            }
            for p in patterns
        ],
        indent=2,
    )

    response = _llm.invoke([
        SystemMessage(content=_SYSTEM_CLUSTER),
        HumanMessage(content=failures_text),
    ])

    try:
        clusters = json.loads(response.content.strip())
    except Exception as exc:
        return {"message": f"Failed to parse cluster response: {exc}", "tools_created": []}

    known_tool_names_before = {t["name"] for t in registry.list_tools()}
    tools_created = []

    for cluster in clusters:
        theme                = cluster.get("theme", "unknown")
        representative_error = cluster.get("representative_error", "")
        representative_query = cluster.get("representative_query", "")
        pattern_ids          = cluster.get("pattern_ids", [])

        print(f"[Retrospective] Theme: {theme}")

        mock_state = {
            "user_query":           representative_query,
            "error_trace":          representative_error,
            "schema_context":       "",
            "generated_sql":        "",
            "tools_used":           [],
            "retry_count":          0,
            "tool_builder_invoked": False,
        }
        run_tool_builder(mock_state)

        # Identify newly registered tools
        new_tools = [
            t["name"] for t in registry.list_tools()
            if t["name"] not in known_tool_names_before
        ]
        known_tool_names_before.update(new_tools)

        for tool_name in new_tools:
            for pid in pattern_ids:
                mark_pattern_resolved(pid, tool_name)
            tools_created.append({"theme": theme, "tool": tool_name})
            print(f"[Retrospective] Tool created for theme '{theme}': {tool_name}")

    return {
        "timestamp":          datetime.utcnow().isoformat(),
        "patterns_reviewed":  len(patterns),
        "clusters_found":     len(clusters),
        "tools_created":      tools_created,
    }
