from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


class OutcomeStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    player_name TEXT NOT NULL,
                    subgraph_signature TEXT NOT NULL,
                    guardrail_applied TEXT NOT NULL,
                    intervention_taken TEXT NOT NULL,
                    parent_reply TEXT NOT NULL,
                    attendance_delta REAL NOT NULL,
                    invoice_status TEXT NOT NULL,
                    risk_before TEXT NOT NULL,
                    risk_after TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_episode(self, episode: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO episodes (
                    episode_id, player_name, subgraph_signature, guardrail_applied,
                    intervention_taken, parent_reply, attendance_delta, invoice_status,
                    risk_before, risk_after, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode["episode_id"],
                    episode["player_name"],
                    episode["subgraph_signature"],
                    episode["guardrail_applied"],
                    episode["intervention_taken"],
                    episode["parent_reply"],
                    episode["attendance_delta"],
                    episode["invoice_status"],
                    episode["risk_before"],
                    episode["risk_after"],
                    episode["timestamp"],
                ),
            )
            conn.commit()

    def list_episodes(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql_query(
                "SELECT episode_id, player_name, guardrail_applied, intervention_taken, attendance_delta, invoice_status, timestamp FROM episodes ORDER BY timestamp DESC",
                conn,
            )
        return df

    def seed_default_episodes(self) -> None:
        with self._connect() as conn:
            existing = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        if existing:
            return

        now = datetime.now(timezone.utc).isoformat()
        seed_rows = [
            {
                "episode_id": "EP-001",
                "player_name": "Luca M.",
                "subgraph_signature": "invoice+frustration+bench_morale",
                "guardrail_applied": "Anti-Stupid Billing Guardrail",
                "intervention_taken": "Coach 1-on-1 check-in before billing reminder",
                "parent_reply": "Mulțumim, Luca revine la antrenament.",
                "attendance_delta": 0.75,
                "invoice_status": "PAID",
                "risk_before": "dropout=0.89;collection=0.78",
                "risk_after": "dropout=0.18;collection=0.00",
                "timestamp": now,
            },
            {
                "episode_id": "EP-002",
                "player_name": "Radu T.",
                "subgraph_signature": "invoice+active_parent_frustration",
                "guardrail_applied": "NONE",
                "intervention_taken": "Automated invoice reminder fired first",
                "parent_reply": "Ne retragem din academie.",
                "attendance_delta": -1.0,
                "invoice_status": "UNPAID",
                "risk_before": "dropout=0.64;collection=0.70",
                "risk_after": "dropout=0.96;collection=0.91",
                "timestamp": now,
            },
            {
                "episode_id": "EP-003",
                "player_name": "Matei D.",
                "subgraph_signature": "hamstring+high_sprint_load",
                "guardrail_applied": "Load Protection Guardrail",
                "intervention_taken": "Reduced sprint load by 35% + proactive parent update",
                "parent_reply": "Mulțumim pentru grijă, continuăm programul.",
                "attendance_delta": 0.40,
                "invoice_status": "N/A",
                "risk_before": "injury=0.84",
                "risk_after": "injury=0.31",
                "timestamp": now,
            },
            {
                "episode_id": "EP-004",
                "player_name": "Andrei P.",
                "subgraph_signature": "high_performance+parent_inquiry",
                "guardrail_applied": "Retention & Upsell Trigger",
                "intervention_taken": "U16 shadow invite + paid striker clinic offer",
                "parent_reply": "Andrei e încântat, acceptăm clinica.",
                "attendance_delta": 0.60,
                "invoice_status": "PAID",
                "risk_before": "opportunity=0.55",
                "risk_after": "opportunity=0.91",
                "timestamp": now,
            },
        ]
        for row in seed_rows:
            self.add_episode(row)

    def simulate_7_day_outcome(self, case_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        simulations = {
            "case_1_luca": {
                "episode_id": f"SIM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "player_name": "Luca M.",
                "subgraph_signature": "invoice+frustration+low_morale+missed_sessions",
                "guardrail_applied": "Anti-Stupid Billing Guardrail",
                "intervention_taken": "Coach empathy call + parent outreach + delayed billing",
                "parent_reply": "Mulțumim mult că a vorbit antrenorul cu el, vine mâine la antrenament și am achitat factura #1042",
                "attendance_delta": 0.75,
                "invoice_status": "PAID",
                "risk_before": {
                    "dropout_risk": 89,
                    "collection_risk": 78,
                    "parent_engagement_risk": 72,
                    "injury_load_risk": 28,
                    "development_opportunity": 46,
                },
                "risk_after": {
                    "dropout_risk": 18,
                    "collection_risk": 0,
                    "parent_engagement_risk": 22,
                    "injury_load_risk": 20,
                    "development_opportunity": 62,
                },
                "timestamp": now,
            },
            "case_2_matei": {
                "episode_id": f"SIM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "player_name": "Matei D.",
                "subgraph_signature": "hamstring+high_sprint_tactical_load",
                "guardrail_applied": "Load Protection Guardrail",
                "intervention_taken": "Sprint volume cap -35% and modified microcycle",
                "parent_reply": "Apreciem mesajul, Matei spune că se simte mai bine.",
                "attendance_delta": 0.4,
                "invoice_status": "N/A",
                "risk_before": {
                    "dropout_risk": 22,
                    "collection_risk": 12,
                    "parent_engagement_risk": 30,
                    "injury_load_risk": 86,
                    "development_opportunity": 58,
                },
                "risk_after": {
                    "dropout_risk": 18,
                    "collection_risk": 10,
                    "parent_engagement_risk": 18,
                    "injury_load_risk": 34,
                    "development_opportunity": 63,
                },
                "timestamp": now,
            },
            "case_3_andrei": {
                "episode_id": f"SIM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "player_name": "Andrei P.",
                "subgraph_signature": "high_match_performance+parent_inquiry",
                "guardrail_applied": "Retention & Upsell Trigger",
                "intervention_taken": "U16 shadow invite + paid 1-on-1 striker clinic",
                "parent_reply": "Confirmăm, Andrei participă și la clinica de finalizare.",
                "attendance_delta": 0.6,
                "invoice_status": "PAID",
                "risk_before": {
                    "dropout_risk": 16,
                    "collection_risk": 8,
                    "parent_engagement_risk": 24,
                    "injury_load_risk": 20,
                    "development_opportunity": 80,
                },
                "risk_after": {
                    "dropout_risk": 10,
                    "collection_risk": 0,
                    "parent_engagement_risk": 10,
                    "injury_load_risk": 18,
                    "development_opportunity": 96,
                },
                "timestamp": now,
            },
        }

        if case_id not in simulations:
            raise ValueError(f"Unsupported case_id: {case_id}")

        selected = simulations[case_id]
        self.add_episode(
            {
                "episode_id": selected["episode_id"],
                "player_name": selected["player_name"],
                "subgraph_signature": selected["subgraph_signature"],
                "guardrail_applied": selected["guardrail_applied"],
                "intervention_taken": selected["intervention_taken"],
                "parent_reply": selected["parent_reply"],
                "attendance_delta": selected["attendance_delta"],
                "invoice_status": selected["invoice_status"],
                "risk_before": str(selected["risk_before"]),
                "risk_after": str(selected["risk_after"]),
                "timestamp": selected["timestamp"],
            }
        )
        return selected
