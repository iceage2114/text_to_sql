"""
Executor agent.
Runs any requested_tool_calls first, then generated_sql through run_sql.
Sets sql_result on success, error_trace on failure.
"""
from __future__ import annotations

from graph.state import AgentState
from tools.registry import registry


def run_executor(state: AgentState) -> dict:
    tools_used   = list(state.get("tools_used", []))
    tool_results: dict = {}

    # ── Execute requested tool calls before running SQL ───────────────────────
    for call in state.get("requested_tool_calls", []):
        tool_name = call.get("name", "")
        args      = call.get("args", {})
        tool      = registry.get_tool(tool_name)
        if tool is None:
            tool_results[tool_name] = {"error": f"Tool '{tool_name}' not found"}
            continue
        try:
            tool_results[tool_name] = tool.execute(**args)
            if tool_name not in tools_used:
                tools_used.append(tool_name)
        except Exception as exc:
            tool_results[tool_name] = {"error": str(exc)}

    # ── Run the generated SQL ─────────────────────────────────────────────────
    sql = state.get("generated_sql", "")
    if not sql:
        # Tools were dispatched but no SQL yet — signal the graph to loop back
        # to sql_writer (with tool_results populated) rather than failing.
        needs_rewrite = bool(tool_results)
        return {
            "error_trace": "" if needs_rewrite else "No SQL was generated.",
            "sql_result": {},
            "tool_results": tool_results,
            "tools_used": tools_used,
            "needs_sql_rewrite": needs_rewrite,
        }

    run_sql = registry.get_tool("run_sql")
    if run_sql is None:
        return {
            "error_trace": "run_sql tool not found in registry.",
            "sql_result": {},
            "tool_results": tool_results,
            "tools_used": tools_used,
        }

    tools_used.append("run_sql")

    try:
        result = run_sql.execute(query=sql)
        return {
            "sql_result": result,
            "error_trace": "",
            "tools_used": tools_used,
            "tool_results": tool_results,
        }
    except Exception as exc:
        return {
            "sql_result": {},
            "error_trace": str(exc),
            "tools_used": tools_used,
            "tool_results": tool_results,
        }
