"""
Critic agent.
Scores how well sql_result answers user_query (0.0 – 1.0).
"""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from llm import get_chat_llm

_SYSTEM = """\
You are a SQL result quality critic.  Given a user question, the SQL generated,
and the result returned, score how well the result answers the question.

Score guide:
  1.0  : Perfect — complete, accurate, well-structured.
  0.7–0.9 : Good — minor cosmetic issues, correct data.
  0.4–0.6 : Partial — some data but incomplete or ambiguous.
  0.0–0.3 : Failed — empty result, wrong data, or execution error.

If there was an execution error, score it 0.0.

Respond with exactly this JSON and nothing else:
{"score": <float>, "explanation": "<one sentence>"}
"""

_llm = get_chat_llm()


def run_critic(state: AgentState) -> dict:
    error_trace = state.get("error_trace", "")
    if error_trace:
        return {
            "evaluation_score": 0.0,
            "evaluation_explanation": f"Execution failed: {error_trace}",
        }

    result = state.get("sql_result", {})
    result_preview = {
        "columns":   result.get("columns", []),
        "rows":      result.get("rows", [])[:5],
        "row_count": result.get("row_count", 0),
        "truncated": result.get("truncated", False),
    }

    prompt = (
        f"User question: {state['user_query']}\n\n"
        f"Generated SQL:\n{state.get('generated_sql', '')}\n\n"
        f"Result preview:\n{json.dumps(result_preview, default=str)}"
    )

    messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]
    response = _llm.invoke(messages)

    try:
        parsed = json.loads(response.content.strip())
        score       = float(parsed.get("score", 0.0))
        explanation = parsed.get("explanation", "")
    except Exception:
        score       = 0.0
        explanation = f"Failed to parse critic response: {response.content}"

    return {"evaluation_score": score, "evaluation_explanation": explanation}
