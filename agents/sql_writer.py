"""
SQL Writer agent.
Receives: plan + schema_context + few-shot examples from memory
Produces: generated_sql + optional requested_tool_calls
"""
from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config import settings
from graph.state import AgentState
from llm import get_chat_llm
from memory.store import search_similar_queries
from schema.store import search_schema
from tools.registry import registry

_llm = get_chat_llm()


def _build_few_shot(user_query: str) -> str:
    similar = search_similar_queries(user_query, k=5)
    if not similar:
        return ""
    # Sort by score descending — highest quality examples first
    similar.sort(key=lambda r: r.evaluation_score or 0.0, reverse=True)
    similar = similar[:3]
    lines = ["Relevant past successful queries (for reference):\n"]
    for r in similar:
        if r.generated_sql:
            note = f"  # Why it worked: {r.evaluation_explanation}\n" if r.evaluation_explanation else ""
            lines.append(f"# Question: {r.user_query}\n{note}{r.generated_sql}\n")
    return "\n".join(lines)


def _build_tool_section() -> str:
    """Inject available helper tools (everything except run_sql) into the prompt."""
    tools = [t for t in registry.list_tools() if t["name"] != "run_sql"]
    if not tools:
        return ""
    lines = ["\nAvailable helper tools (call before writing SQL if useful):"]
    for t in tools:
        props = t.get("input_schema", {}).get("properties", {})
        args_str = ", ".join(
            f"{k}: {v.get('type', 'any')}" for k, v in props.items()
        )
        lines.append(f'  - {t["name"]}({args_str}) — {t["description"]}')
    lines.append("")
    lines.append("To call tools, output ONLY a TOOLS line (valid JSON array) then the SQL on the next line:")
    lines.append('  TOOLS: [{"name": "tool_name", "args": {"param": "value"}}]')
    lines.append("  SELECT ...")
    lines.append("")
    lines.append("STRICT OUTPUT RULES:")
    lines.append("  - No prose, no explanations, no markdown — ONLY the TOOLS line (if needed) and the SQL.")
    lines.append("  - If no tools are needed, output ONLY the SQL statement.")
    lines.append("  - Never write 'No results returned' or any other text outside the TOOLS line and SQL.")
    return "\n".join(lines)


def run_sql_writer(state: AgentState) -> dict:
    user_query  = state["user_query"]
    plan        = state.get("plan", "")
    error_trace = state.get("error_trace", "")
    tool_results = state.get("tool_results", {})

    few_shot = _build_few_shot(user_query)

    relevant_tables = search_schema(user_query + " " + plan, k=5)
    schema_detail   = "\n\n".join(t["doc"] for t in relevant_tables)

    retry_hint = ""
    if error_trace:
        retry_hint = (
            f"\n\nPrevious attempt failed with this error:\n{error_trace}\n"
            "Fix the SQL to avoid this error."
        )

    tool_context = ""
    if tool_results:
        tool_context = "\n\nTool results available:\n"
        for name, result in tool_results.items():
            tool_context += f"  {name}: {json.dumps(result, default=str)}\n"

    prompt = (
        f"User question: {user_query}\n\n"
        f"Plan:\n{plan}\n\n"
        f"Relevant schema:\n{schema_detail}\n\n"
        f"{few_shot}"
        f"{retry_hint}"
        f"{tool_context}"
    )

    # Only offer tool calling on the first attempt and only when no tool results
    # have been collected yet — prevents the LLM from looping on tool calls
    # instead of writing SQL.
    already_have_tools = bool(tool_results)
    tool_section = "" if already_have_tools else _build_tool_section()
    system = (
        "You are a SQL Server (T-SQL) expert.  Generate a single valid T-SQL SELECT\n"
        "statement that answers the user question.\n\n"
        "Rules:\n"
        "- Only use SELECT statements.  Never use INSERT, UPDATE, DELETE, DROP, EXEC,\n"
        "  or any DDL/DCL.\n"
        "- Use square-bracket quoting: [TableName].[ColumnName].\n"
        f"- Default to SELECT TOP {settings.row_limit} unless the user asks for counts/aggregates.\n"
        "- Prefer explicit JOIN syntax over implicit comma joins.\n"
        "- Output ONLY the SQL (or a TOOLS line followed immediately by SQL).\n"
        "  No explanations. No prose. No markdown fences."
        + tool_section
    )
    messages = [SystemMessage(content=system), HumanMessage(content=prompt)]
    response = _llm.invoke(messages)

    raw = response.content.strip()
    requested_tool_calls: list[dict] = []

    # Scan all lines for a TOOLS: prefix — LLM may emit prose before it
    raw_lines = raw.splitlines()
    tools_line_idx = None
    for i, line in enumerate(raw_lines):
        if line.strip().upper().startswith("TOOLS:"):
            tools_line_idx = i
            break

    if tools_line_idx is not None:
        try:
            tools_text = raw_lines[tools_line_idx].strip()
            requested_tool_calls = json.loads(tools_text[6:].strip())
        except Exception:
            pass
        # SQL is everything after the TOOLS line
        raw = "\n".join(raw_lines[tools_line_idx + 1:]).strip()

    sql = raw
    # Strip accidental markdown fences
    if sql.startswith("```"):
        sql = sql.split("```")[1].lstrip("sql").strip()

    # Strip any remaining prose — fast-forward to first SQL keyword
    sql_start = re.search(r"(?m)^(SELECT|WITH)\b", sql, re.IGNORECASE)
    if sql_start:
        sql = sql[sql_start.start():]

    tools_used = list(state.get("tools_used", []))
    if "sql_writer" not in tools_used:
        tools_used.append("sql_writer")

    return {
        "generated_sql": sql,
        "error_trace": "",
        "tools_used": tools_used,
        "requested_tool_calls": requested_tool_calls,
        "needs_sql_rewrite": False,
    }
