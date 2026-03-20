"""
Streamlit chat UI for the Text-to-SQL Self-Learning Agent.
Connects to the FastAPI backend running at http://127.0.0.1:8000.

Run with:
    streamlit run ui/app.py

To use a non-default API port (e.g. 8001):
    set API_PORT=8001
    streamlit run ui/app.py
"""
from __future__ import annotations

import json
import os

import pandas as pd
import requests
import streamlit as st

_port = os.environ.get("API_PORT", "8080")
API_BASE = f"http://127.0.0.1:{_port}"

st.set_page_config(page_title="Text-to-SQL Agent", page_icon="🤖", layout="wide")
st.title("🤖 Text-to-SQL Self-Learning Agent")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _render_response(data: dict) -> None:
    score   = data.get("evaluation_score", 0.0)
    success = data.get("success", False)

    status_icon = "✅" if success else "⚠️"
    st.markdown(
        f"{status_icon} **Score:** `{score:.2f}` — {data.get('evaluation_explanation', '')}"
    )

    if data.get("generated_sql"):
        with st.expander("Generated SQL", expanded=True):
            st.code(data["generated_sql"], language="sql")

    result = data.get("result", {})
    if result.get("columns") and result.get("rows"):
        df = pd.DataFrame(result["rows"], columns=result["columns"])
        st.dataframe(df, use_container_width=True)
        if result.get("truncated"):
            st.caption(f"⚠️ Results capped at {result.get('row_count', '?')} rows.")
    elif not success:
        st.error("No results returned.")

    tools = data.get("tools_used", [])
    if tools:
        st.caption(
            f"Tools: {' › '.join(tools)}  |  Retries: {data.get('retry_count', 0)}"
        )


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ System Controls")

    if st.button("📥 Ingest / Refresh Schema"):
        with st.spinner("Ingesting schema from SQL Server..."):
            try:
                resp = requests.post(f"{API_BASE}/ingest-schema", timeout=60)
                if resp.ok:
                    st.success(f"Ingested {resp.json()['tables_ingested']} tables.")
                else:
                    st.error(resp.text)
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Start the server first.")

    if st.button("🔁 Run Retrospective"):
        with st.spinner("Analysing failures and building tools..."):
            try:
                resp = requests.post(f"{API_BASE}/retrospective", timeout=300)
                if resp.ok:
                    st.json(resp.json())
                else:
                    st.error(resp.text)
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API.")

    st.divider()

    if st.button("🔧 Show Registered Tools"):
        try:
            resp = requests.get(f"{API_BASE}/tools", timeout=10)
            if resp.ok:
                for t in resp.json().get("tools", []):
                    st.markdown(f"**`{t['name']}`** — {t['description']}")
            else:
                st.error(resp.text)
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API.")

    if st.button("📜 Show Query History"):
        try:
            resp = requests.get(f"{API_BASE}/history", params={"n": 10}, timeout=10)
            if resp.ok:
                for item in resp.json().get("history", []):
                    icon = "✅" if item.get("success") else "❌"
                    st.write(
                        f"{icon} {item.get('user_query', '')} "
                        f"(score: {item.get('evaluation_score', 'N/A')})"
                    )
            else:
                st.error(resp.text)
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API.")

    st.divider()

    # ── Add few-shot example ──────────────────────────────────────────────
    with st.expander("➕ Add Few-Shot Example"):
        st.caption("Teach the agent a correct question → SQL pair directly.")
        ex_query = st.text_input("Natural language question", key="ex_query")
        ex_sql   = st.text_area("Correct T-SQL", key="ex_sql", height=120)
        if st.button("💾 Save Example"):
            if ex_query.strip() and ex_sql.strip():
                try:
                    resp = requests.post(
                        f"{API_BASE}/examples",
                        json={"query": ex_query.strip(), "sql": ex_sql.strip()},
                        timeout=15,
                    )
                    if resp.ok:
                        st.success("Example saved — will be used in future queries.")
                    else:
                        st.error(resp.text)
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API.")
            else:
                st.warning("Both fields are required.")

    # ── Failure diagnostics ───────────────────────────────────────────────
    with st.expander("🔍 Failure Diagnostics"):
        st.caption("Analyse unresolved failures and get recommendations.")
        if st.button("Load Diagnostics"):
            with st.spinner("Analysing failures..."):
                try:
                    resp = requests.get(f"{API_BASE}/failures", timeout=120)
                    if resp.ok:
                        data  = resp.json()
                        count = data.get("count", 0)
                        if count == 0:
                            st.success("No unresolved failures found.")
                        else:
                            st.warning(f"{count} unresolved failure(s) found")
                            for f in data.get("failures", []):
                                sev  = f.get("severity", "medium")
                                icon = "🔴" if sev == "high" else "🟡" if sev == "medium" else "🟢"
                                st.markdown(f"{icon} **{sev.upper()}** — {f.get('query', '')}")
                                st.markdown(f"**Diagnosis:** {f.get('diagnosis', '')}")
                                st.markdown(f"**Recommendation:** {f.get('recommendation', '')}")
                                with st.expander("Error detail"):
                                    st.code(f.get("error", ""), language="text")
                                st.divider()
                    else:
                        st.error(resp.text)
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API.")

    st.divider()
    st.caption("API: " + API_BASE)


# ── Chat ──────────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and isinstance(msg["content"], dict):
            _render_response(msg["content"])
        else:
            st.write(msg["content"])

user_input = st.chat_input("Ask a question about your data...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/query",
                    json={"query": user_input},
                    timeout=120,
                )
                if resp.ok:
                    data = resp.json()
                    _render_response(data)
                    st.session_state.messages.append({"role": "assistant", "content": data})
                else:
                    err = f"API error {resp.status_code}: {resp.text}"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})
            except requests.exceptions.ConnectionError:
                err = (
                    "Cannot connect to API server.  "
                    "Start it with: `uvicorn api.main:app --reload`"
                )
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
