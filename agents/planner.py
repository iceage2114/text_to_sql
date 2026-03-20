"""
Planner agent.
Receives: user_query + schema_context
Produces: plan (numbered step list)
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from llm import get_chat_llm
from schema.store import get_full_schema_summary

_SYSTEM = """\
You are a SQL expert that plans how to answer a user data question.

Given the user query and a database schema summary, produce a concise numbered
step plan describing:
1. Which tables are needed
2. What JOINs or filters are required
3. What aggregations or calculations are needed
4. Any edge cases to watch for

Be specific about table and column names from the schema.
Return ONLY the numbered plan — nothing else.
"""

_llm = get_chat_llm()


def run_planner(state: AgentState) -> dict:
    schema_ctx = state.get("schema_context") or get_full_schema_summary()
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"User question: {state['user_query']}\n\nSchema:\n{schema_ctx}"),
    ]
    response = _llm.invoke(messages)
    return {"plan": response.content, "schema_context": schema_ctx}
