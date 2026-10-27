from __future__ import annotations

import json
import os
import time
from pathlib import Path

import streamlit as st

from src.agent.extractor import analyze_case_live, load_cached_extractions
from src.graph.engine import apply_case_guardrail, render_ego_graph_html
from src.memory.outcome_store import OutcomeStore

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CASE_DIR = DATA_DIR / "hero_cases"

CASE_META = {
    "case_1_luca": {
        "button": "🚨 Case 1: Luca M. (Silent Churn & Overdue Invoice)",
        "folder": "case_1_luca",
    },
    "case_2_matei": {
        "button": "⚠️ Case 2: Matei D. (Hamstring Overload & Whiteboard Tactics)",
        "folder": "case_2_matei",
    },
    "case_3_andrei": {
        "button": "🚀 Case 3: Andrei P. (Top Scorer Development & Clinic Upsell)",
        "folder": "case_3_andrei",
    },
}

st.set_page_config(page_title="PitchPulse AI — Multimodal Graph Agent", layout="wide")

if "selected_case" not in st.session_state:
    st.session_state.selected_case = "case_1_luca"
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = {}

if not DATA_DIR.exists() or not (DATA_DIR / "cached_extractions.json").exists():
    st.error("Data folder not found. Please run `python seed_data.py` first.")
    st.stop()

st.title("PitchPulse AI — Multimodal Knowledge Graph & Intervention Agent")
st.caption("Predict → Decide → Act for academy retention and revenue protection across fragmented multimodal channels.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Active Players", "45")
m2.metric("Revenue at Risk", "4,050 RON")
m3.metric("Active Guardrail Blocks", "2")
m4.metric("Historical Save Rate", "91%")

with st.sidebar:
    st.header("Execution Mode")
    mode = st.radio(
        "Inference source",
        ["⚡ Instant Cached Demo Mode", "🔴 Live Gemini 2.5 Flash API"],
        index=0,
    )
    api_key_input = st.text_input("Gemini API Key (optional)", type="password")
    st.caption("If empty, app falls back to GEMINI_API_KEY env var.")

st.subheader("Scenario Selector")
selector_cols = st.columns(3)
for i, case_id in enumerate(CASE_META.keys()):
    if selector_cols[i].button(CASE_META[case_id]["button"], use_container_width=True):
        st.session_state.selected_case = case_id

selected_case = st.session_state.selected_case
case_folder = CASE_DIR / CASE_META[selected_case]["folder"]

cached = load_cached_extractions(DATA_DIR / "cached_extractions.json")
analysis = cached[selected_case]
fallback_used = False
status_message = "Loaded cached extraction."

start = time.perf_counter()
if mode == "🔴 Live Gemini 2.5 Flash API":
    api_key = api_key_input.strip() or os.getenv("GEMINI_API_KEY")
    analysis, fallback_used, status_message = analyze_case_live(case_folder, selected_case, api_key)
else:
    analysis = cached[selected_case]
elapsed_ms = (time.perf_counter() - start) * 1000

if mode == "⚡ Instant Cached Demo Mode":
    st.success(f"{status_message} ⚡ {elapsed_ms:.2f}ms")
else:
    if fallback_used:
        st.warning(f"{status_message}")
    else:
        st.success(status_message)

left_col, center_col, right_col = st.columns([1.2, 1.5, 1.2])

with left_col:
    st.markdown("### 📥 Multimodal Evidence Inbox")
    for evidence_file in sorted(case_folder.iterdir()):
        suffix = evidence_file.suffix.lower()
        st.markdown(f"**{evidence_file.name}**")
        if suffix == ".wav":
            st.audio(evidence_file.read_bytes(), format="audio/wav")
        elif suffix == ".png":
            st.image(str(evidence_file), use_container_width=True)
        elif suffix == ".pdf":
            st.info("PDF evidence loaded and available to Gemini extraction.")
            with st.expander("Preview metadata"):
                st.write({"file": evidence_file.name, "size_bytes": evidence_file.stat().st_size})
        elif suffix == ".json":
            payload = json.loads(evidence_file.read_text(encoding="utf-8"))
            msg = payload.get("message")
            if msg:
                st.markdown(
                    f"<div style='background:#1f2937;padding:10px;border-radius:10px;color:white;'>💬 {msg}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.json(payload)

with center_col:
    st.markdown("### 🕸️ Knowledge Graph & Multi-Hop Reasoning")
    graph, guardrail = apply_case_guardrail(analysis)
    html = render_ego_graph_html(graph, analysis.player_id)
    st.components.v1.html(html, height=500, scrolling=True)

    st.markdown("**Subgraph Reasoning Path**")
    for item in guardrail.reasoning_path:
        st.markdown(f"`{item}`")

    outcome = st.session_state.simulation_results.get(selected_case)
    risk_data = outcome["risk_after"] if outcome else analysis.risk_profile.model_dump()

    st.markdown("**Risk & Opportunity Scores**")
    st.progress(risk_data["dropout_risk"] / 100, text=f"Dropout Risk: {risk_data['dropout_risk']}%")
    st.progress(risk_data["collection_risk"] / 100, text=f"Collection Risk: {risk_data['collection_risk']}%")
    st.progress(risk_data["parent_engagement_risk"] / 100, text=f"Parent Engagement Risk: {risk_data['parent_engagement_risk']}%")
    st.progress(risk_data["injury_load_risk"] / 100, text=f"Injury Load: {risk_data['injury_load_risk']}%")
    st.progress(risk_data["development_opportunity"] / 100, text=f"Development Opportunity: {risk_data['development_opportunity']}%")

with right_col:
    st.markdown("### ⚡ Guardrailed Action Queue & Outcome Memory")
    level = "warning" if guardrail.triggered else "info"
    getattr(st, level)(f"**{guardrail.rule_name}** — {guardrail.suppressed_action}")

    for idx, intervention in enumerate(analysis.interventions):
        st.markdown(f"**{intervention.channel} • {intervention.priority}**")
        st.text_input(
            f"Recipient {idx+1}",
            value=intervention.recipient,
            key=f"recipient_{selected_case}_{idx}",
            disabled=False,
        )
        st.text_area(
            f"Draft {idx+1}",
            value=intervention.draft_message,
            key=f"draft_{selected_case}_{idx}",
            height=100,
        )

    approve = st.button("✅ Approve & Execute Intervention", use_container_width=True)
    simulate = st.button("⏩ Fast-Forward 7 Days: Simulate Outcome & Learn", use_container_width=True)

    store = OutcomeStore(DATA_DIR / "outcomes.db")
    if approve:
        st.success("Interventions approved and queued for execution.")

    if simulate:
        simulation = store.simulate_7_day_outcome(selected_case)
        st.session_state.simulation_results[selected_case] = simulation
        st.success("7-day simulation complete and outcome stored.")
        st.markdown(f"**Parent Reply:** {simulation['parent_reply']}")

st.markdown("---")
st.markdown("### 📚 Episodic Memory Playbook (SQLite)")
store = OutcomeStore(DATA_DIR / "outcomes.db")
episodes_df = store.list_episodes()
st.dataframe(episodes_df, use_container_width=True, hide_index=True)
