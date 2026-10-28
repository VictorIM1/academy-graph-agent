from __future__ import annotations

from typing import Any

import networkx as nx
from pyvis.network import Network

from src.schemas import CaseAnalysis, GuardrailDecision


def build_case_graph(case: CaseAnalysis) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    player_node = case.player_id
    parent_node = f"parent::{case.player_name}"
    coach_node = f"coach::{case.squad}"
    team_node = f"team::{case.squad}"

    graph.add_node(player_node, label=case.player_name, node_type="Player", evidence=case.player_name)
    graph.add_node(parent_node, label=f"Parent of {case.player_name}", node_type="Parent", evidence="Parent communications")
    graph.add_node(coach_node, label=f"Coach {case.squad}", node_type="Coach", evidence="Coaching staff context")
    graph.add_node(team_node, label=case.squad, node_type="Team", evidence="Team context")

    graph.add_edge(parent_node, player_node, label="is_parent_of")
    graph.add_edge(player_node, coach_node, label="coached_by")
    graph.add_edge(player_node, team_node, label="belongs_to")

    for idx, signal in enumerate(case.signals):
        signal_node = f"signal::{idx}::{signal.target_node}"
        node_type = {
            "payment": "Invoice",
            "injury": "Injury",
            "attendance": "Session",
            "opportunity": "Concern",
            "concern": "Message",
        }[signal.entity_type]
        graph.add_node(
            signal_node,
            label=signal.target_node,
            node_type=node_type,
            severity=signal.severity_score,
            evidence=f"{signal.source_file}: {signal.summary}",
        )
        graph.add_edge(player_node, signal_node, label=signal.edge_label)

        summary = signal.summary.lower()
        if "invoice" in summary or "overdue" in summary:
            graph.add_node("invoice_status::unpaid", label="Unpaid Invoice", node_type="Invoice", evidence=signal.summary)
            graph.add_edge(player_node, "invoice_status::unpaid", label="unpaid_invoice")

        if "frustr" in summary or "demotivat" in summary:
            graph.add_node("emotion::frustration", label="Parent Frustration", node_type="Concern", evidence=signal.summary)
            graph.add_edge(parent_node, "emotion::frustration", label="expressed_frustration")

        if "confidence" in summary or "bench" in summary or "morale" in summary:
            graph.add_node("emotion::low_morale", label="Low Morale", node_type="Concern", evidence=signal.summary)
            graph.add_edge(player_node, "emotion::low_morale", label="low_morale")

        if "hamstring" in summary:
            graph.add_node("injury::hamstring", label="Recent Hamstring Injury", node_type="Injury", evidence=signal.summary)
            graph.add_edge(player_node, "injury::hamstring", label="recent_hamstring_injury")

        if "sprint" in summary or "high-intensity" in summary:
            graph.add_node(
                "load::high_sprint",
                label="High Sprint Tactical Load",
                node_type="Session",
                evidence=signal.summary,
            )
            graph.add_edge(team_node, "load::high_sprint", label="high_sprint_tactical_load")

        if "goals" in summary or "top rating" in summary:
            graph.add_node("perf::high_match", label="High Match Performance", node_type="Concern", evidence=signal.summary)
            graph.add_edge(player_node, "perf::high_match", label="high_match_performance")

        if "grupe" in summary or "individuale" in summary or "inquiry" in summary:
            graph.add_node("parent::inquiry", label="Parent Inquiry", node_type="Message", evidence=signal.summary)
            graph.add_edge(parent_node, "parent::inquiry", label="parent_inquiry")

    for intervention in case.interventions:
        intervention_node = f"intervention::{intervention.channel}::{intervention.recipient}"
        graph.add_node(
            intervention_node,
            label=intervention.subject_or_task,
            node_type="Intervention",
            evidence=intervention.draft_message,
        )
        graph.add_edge(player_node, intervention_node, label="recommended_for")

    return graph


def _has_node_with_prefix(subgraph: nx.Graph, prefix: str) -> bool:
    return any(str(node).startswith(prefix) for node in subgraph.nodes)


def _has_edge_label(subgraph: nx.MultiDiGraph, label: str) -> bool:
    for _, _, edge_data in subgraph.edges(data=True):
        if edge_data.get("label") == label:
            return True
    return False


def evaluate_cross_signal_guardrails(graph: nx.MultiDiGraph, player_id: str) -> GuardrailDecision:
    ego = nx.ego_graph(graph.to_undirected(), player_id, radius=2)
    ego_multi = graph.edge_subgraph([(u, v, k) for u, v, k in graph.edges(keys=True) if u in ego.nodes and v in ego.nodes]).copy()

    unpaid_invoice = _has_edge_label(ego_multi, "unpaid_invoice") or _has_node_with_prefix(ego, "invoice_status::")
    frustration_or_low_morale = _has_edge_label(ego_multi, "expressed_frustration") or _has_edge_label(ego_multi, "low_morale")

    recent_hamstring = _has_edge_label(ego_multi, "recent_hamstring_injury") or _has_node_with_prefix(ego, "injury::hamstring")
    high_sprint_load = _has_edge_label(ego_multi, "high_sprint_tactical_load") or _has_node_with_prefix(ego, "load::high_sprint")

    high_match_performance = _has_edge_label(ego_multi, "high_match_performance") or _has_node_with_prefix(ego, "perf::high_match")
    parent_inquiry = _has_edge_label(ego_multi, "parent_inquiry") or _has_node_with_prefix(ego, "parent::inquiry")

    if unpaid_invoice and frustration_or_low_morale:
        return GuardrailDecision(
            triggered=True,
            rule_name="Anti-Stupid Billing Guardrail",
            suppressed_action="Suppress automated invoice chasing for 5 days",
            reasoning_path=[
                "[Invoice: Overdue]",
                "[WhatsApp: Parent Frustrated]",
                "[Audio: Low Confidence / Low Morale]",
                "[Guardrail: Coach Check-in + Parent Outreach Before Billing]",
            ],
        )

    if recent_hamstring and high_sprint_load:
        return GuardrailDecision(
            triggered=True,
            rule_name="Load Protection Guardrail",
            suppressed_action="Cap sprint load by 35% and alert parent proactively",
            reasoning_path=[
                "[Medical PDF: Recent Hamstring Strain]",
                "[Tactics Image: High Sprint Repeats]",
                "[Coach Message: Stiffness Observed]",
                "[Guardrail: Load Cap + Parent Alert]",
            ],
        )

    if high_match_performance and parent_inquiry:
        return GuardrailDecision(
            triggered=True,
            rule_name="Retention & Upsell Trigger",
            suppressed_action="Trigger U16 Shadow Invite + Paid 1-on-1 Striker Clinic Offer",
            reasoning_path=[
                "[Match Sheet: High Performance]",
                "[WhatsApp: Parent Development Inquiry]",
                "[Guardrail: Premium Development Offer]",
            ],
        )

    return GuardrailDecision(
        triggered=False,
        rule_name="No cross-signal guardrail",
        suppressed_action="None",
        reasoning_path=["No conflicting high-priority cross-signal pattern found in 2-hop neighborhood."],
    )


def render_ego_graph_html(graph: nx.MultiDiGraph, player_id: str) -> str:
    ego_nodes = nx.ego_graph(graph.to_undirected(), player_id, radius=2).nodes
    subgraph = graph.subgraph(ego_nodes).copy()

    color_map = {
        "Player": "#4cafef",
        "Parent": "#f6c343",
        "Coach": "#66bb6a",
        "Team": "#8e99f3",
        "Session": "#ff8a65",
        "Invoice": "#ef5350",
        "Injury": "#ff7043",
        "Message": "#42a5f5",
        "Concern": "#ab47bc",
        "Intervention": "#26c6da",
    }

    net = Network(height="480px", width="100%", directed=True, bgcolor="#0e1117", font_color="#e6edf3")
    net.barnes_hut()

    for node, attrs in subgraph.nodes(data=True):
        node_type = attrs.get("node_type", "Concern")
        severity = float(attrs.get("severity", 0.5))
        base_size = 18 if node == player_id else 14
        size = base_size + int(severity * 10)
        net.add_node(
            str(node),
            label=attrs.get("label", str(node)),
            color=color_map.get(node_type, "#9e9e9e"),
            title=attrs.get("evidence", "No evidence"),
            size=size,
        )

    for source, target, attrs in subgraph.edges(data=True):
        net.add_edge(str(source), str(target), label=attrs.get("label", "related_to"), color="#7d8590")

    net.set_options(
        """
        {
            "nodes": {"font": {"size": 14}},
            "edges": {"arrows": {"to": {"enabled": true}}, "smooth": false},
            "interaction": {"hover": true, "navigationButtons": true},
            "physics": {"stabilization": true}
        }
        """
    )
    return net.generate_html(notebook=False)


def apply_case_guardrail(case: CaseAnalysis) -> tuple[nx.MultiDiGraph, GuardrailDecision]:
    graph = build_case_graph(case)
    guardrail = evaluate_cross_signal_guardrails(graph, case.player_id)
    return graph, guardrail
