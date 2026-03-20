"""
Tool Builder agent — the self-learning core.

Invoked when the executor exhausts retries with an unrecoverable error.

Steps:
  1. LLM analyses error + schema  → missing capability description
  2. LLM writes a conformant Python tool module
  3. Code is dry-run tested inside a threading.Timer timeout guard
  4. On success  → registry.register_tool() writes + hot-loads the tool
  5. On failure  → log_failure() for the retrospective runner
"""
from __future__ import annotations

import threading
import traceback
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from config import settings
from graph.state import AgentState
from llm import get_chat_llm
from memory.store import log_failure
from tools.registry import registry

_SYSTEM_ANALYZE = """\
You are an expert database tool engineer.  The Text-to-SQL agent failed to
answer a user question.  Analyse the error and schema context and identify
the specific missing capability (e.g. "no helper to detect timestamp column
formats", "no date-truncation function for fiscal quarters").

Respond with a single sentence naming the missing capability only.
"""

_SYSTEM_WRITE = """\
You are an expert Python engineer.  Write a Python module for a SQL Server
database helper tool that follows this EXACT contract:

    NAME: str          # unique snake_case name
    DESCRIPTION: str   # one-sentence description
    INPUT_SCHEMA: dict # JSON Schema for execute() keyword arguments
    OUTPUT_SCHEMA: dict

    def execute(**kwargs) -> dict:
        ...

Rules:
- Use EXACTLY this boilerplate to connect — do not deviate:

    from sqlalchemy import create_engine, text
    import urllib.parse
    from config import settings

    def _get_engine():
        conn_str = settings.mssql_conn_str.strip()
        if "DRIVER=" in conn_str.upper():
            url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}"
        else:
            url = conn_str
        return create_engine(url, pool_pre_ping=True)

- Only issue SELECT queries inside execute().
- When iterating query results, access columns by index (row[0], row[1])
  or use result.mappings() to get dict-like rows. Do NOT use row["col"].
- Make execute() work when called with NO arguments (use safe defaults or
  return an empty result) so it can be validated without live input.
- NEVER use subprocess, os.system, eval(), exec(), or arbitrary file I/O.
- Return ONLY the raw Python source code — no markdown fences.
"""

_llm = get_chat_llm(temperature=0.2)


def _run_with_timeout(fn, timeout: int) -> tuple[bool, Any, str]:
    """Execute fn() in a thread.  Returns (success, result, error_message)."""
    result_holder:  list = [None]
    error_holder:   list = [""]
    success_holder: list = [False]

    def target():
        try:
            result_holder[0]  = fn()
            success_holder[0] = True
        except Exception:
            error_holder[0] = traceback.format_exc()

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        return False, None, f"Timed out after {timeout}s"
    if not success_holder[0]:
        return False, None, error_holder[0]
    return True, result_holder[0], ""


def run_tool_builder(state: AgentState) -> dict:
    user_query  = state["user_query"]
    error_trace = state.get("error_trace", "")
    schema_ctx  = state.get("schema_context", "")

    # ── Step 1: identify missing capability ───────────────────────────────────
    analyze_prompt = (
        f"User question: {user_query}\n"
        f"Error encountered:\n{error_trace}\n"
        f"Schema context (truncated):\n{schema_ctx[:2000]}"
    )
    resp = _llm.invoke([
        SystemMessage(content=_SYSTEM_ANALYZE),
        HumanMessage(content=analyze_prompt),
    ])
    capability_gap = resp.content.strip()
    print(f"[ToolBuilder] Capability gap: {capability_gap}")

    # ── Step 2: write the tool ─────────────────────────────────────────────────
    write_prompt = (
        f"Capability needed: {capability_gap}\n"
        f"Error context:\n{error_trace}\n"
        f"Schema context (truncated):\n{schema_ctx[:2000]}"
    )
    resp2 = _llm.invoke([
        SystemMessage(content=_SYSTEM_WRITE),
        HumanMessage(content=write_prompt),
    ])
    code = resp2.content.strip()
    if code.startswith("```"):
        code = code.split("```")[1].lstrip("python").strip()

    # Extract NAME from generated code
    tool_name = f"auto_tool_{len(registry.list_tools())}"
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("NAME"):
            try:
                tool_name = stripped.split("=", 1)[1].strip().strip("\"'")
                break
            except Exception:
                pass

    # ── Step 3: dry-run compile + call execute() with no args ────────────────
    test_ns: dict = {}

    def dry_run():
        exec(compile(code, "<tool_builder>", "exec"), test_ns)
        if "execute" not in test_ns:
            raise ValueError("Generated tool has no execute() function")
        # Actually call execute() with no arguments to catch runtime errors
        # (wrong attribute names, bad SQL, import failures, etc.)
        # A TypeError from missing required args is acceptable — it means
        # the function exists and runs; it just needs arguments.
        try:
            result = test_ns["execute"]()
            if not isinstance(result, dict):
                raise ValueError(
                    f"execute() must return a dict, got {type(result).__name__}"
                )
        except TypeError:
            pass  # Missing required args — function itself is valid

    ok, _, err = _run_with_timeout(dry_run, timeout=settings.tool_timeout_seconds)

    tools_used = list(state.get("tools_used", []))
    tools_used.append("tool_builder")

    if not ok:
        log_failure(
            error_trace=f"Tool builder dry-run failed for '{tool_name}': {err}",
            user_query=user_query,
            generated_sql=state.get("generated_sql"),
        )
        return {
            "tools_used": tools_used,
            "error_trace": f"Tool creation failed (dry-run): {err}",
            "tool_builder_invoked": True,
        }

    # ── Step 4: register ───────────────────────────────────────────────────────
    registered = registry.register_tool(tool_name, code, capability_gap)
    if registered:
        print(f"[ToolBuilder] Registered new tool: {tool_name}")
        return {
            "tools_used": tools_used,
            "error_trace": f"New tool '{tool_name}' created. Retrying query.",
            "tool_builder_invoked": True,
            "retry_count": 0,  # Reset retries so the new tool gets a full attempt
        }

    log_failure(
        error_trace=f"Tool '{tool_name}' failed denylist scan",
        user_query=user_query,
        generated_sql=state.get("generated_sql"),
    )
    return {
        "tools_used": tools_used,
        "error_trace": f"Tool '{tool_name}' rejected by safety scan.",
        "tool_builder_invoked": True,
    }
