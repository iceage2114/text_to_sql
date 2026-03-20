"""
LangGraph StateGraph — wires all agents into the full execution loop.

Flow:
  planner --> sql_writer --> executor --> critic
    critic: score >= threshold          --> memory_curator --> END
    critic: score < threshold, retries left  --> increment_retry --> sql_writer
    critic: score < threshold, retries exhausted, tool_builder not yet tried
                                        --> tool_builder --> sql_writer
    critic: score < threshold, all options exhausted
                                        --> memory_curator --> END
"""
from __future__ import annotations

import uuid
from typing import Literal

from langgraph.graph import END, StateGraph

from agents.critic import run_critic
from agents.executor import run_executor
from agents.memory_curator import run_memory_curator
from agents.planner import run_planner
from agents.sql_writer import run_sql_writer
from agents.tool_builder import run_tool_builder
from config import settings
from graph.state import AgentState


# ── Routing logic ──────────────────────────────────────────────────────────────

def route_after_critic(
    state: AgentState,
) -> Literal["increment_retry", "tool_builder", "memory_curator"]:
    score                 = state.get("evaluation_score", 0.0)
    retry_count           = state.get("retry_count", 0)
    max_retries           = state.get("max_retries", settings.max_retries)
    tool_builder_invoked  = state.get("tool_builder_invoked", False)

    if score >= settings.critic_threshold:
        return "memory_curator"

    if retry_count < max_retries:
        return "increment_retry"

    # Retries exhausted — attempt tool builder once
    if not tool_builder_invoked:
        return "tool_builder"

    # All options exhausted — save failure and end
    return "memory_curator"


def increment_retry(state: AgentState) -> dict:
    """Bump the retry counter before handing back to sql_writer."""
    return {"retry_count": state.get("retry_count", 0) + 1}


# ── Build graph ────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("planner",         run_planner)
    g.add_node("sql_writer",      run_sql_writer)
    g.add_node("executor",        run_executor)
    g.add_node("critic",          run_critic)
    g.add_node("increment_retry", increment_retry)
    g.add_node("tool_builder",    run_tool_builder)
    g.add_node("memory_curator",  run_memory_curator)

    g.set_entry_point("planner")
    g.add_edge("planner",         "sql_writer")
    g.add_edge("sql_writer",      "executor")
    g.add_conditional_edges(
        "executor",
        lambda s: "sql_writer" if s.get("needs_sql_rewrite") else "critic",
        {"sql_writer": "sql_writer", "critic": "critic"},
    )

    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "increment_retry": "increment_retry",
            "tool_builder":    "tool_builder",
            "memory_curator":  "memory_curator",
        },
    )

    g.add_edge("increment_retry", "sql_writer")
    g.add_edge("tool_builder",    "sql_writer")   # After new tool, retry writing
    g.add_edge("memory_curator",  END)

    return g.compile()


# Compiled graph singleton
graph = build_graph()


def run_query(user_query: str) -> AgentState:
    """Entry point: run a user query through the full agent graph."""
    initial: AgentState = {
        "user_query":            user_query,
        "schema_context":        "",
        "plan":                  "",
        "generated_sql":         "",
        "sql_result":            {},
        "error_trace":           "",
        "evaluation_score":      0.0,
        "evaluation_explanation":"",
        "retry_count":           0,
        "max_retries":           settings.max_retries,
        "tool_builder_invoked":  False,
        "requested_tool_calls":  [],
        "tool_results":          {},
        "needs_sql_rewrite":     False,
        "tools_used":            [],
        "memory_saved":          False,
        "query_id":              str(uuid.uuid4()),
    }
    return graph.invoke(initial)
