from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExtractedSignal(BaseModel):
    source_modality: Literal["audio", "pdf", "image", "text"]
    source_file: str
    entity_type: Literal["concern", "injury", "payment", "opportunity", "attendance"]
    summary: str
    severity_score: float = Field(ge=0.0, le=1.0)
    target_node: str
    edge_label: str


class RiskProfile(BaseModel):
    dropout_risk: int = Field(ge=0, le=100)
    injury_load_risk: int = Field(ge=0, le=100)
    development_opportunity: int = Field(ge=0, le=100)
    parent_engagement_risk: int = Field(ge=0, le=100)
    collection_risk: int = Field(ge=0, le=100)


class GuardrailDecision(BaseModel):
    triggered: bool
    rule_name: str
    suppressed_action: str
    reasoning_path: list[str]


class ProposedIntervention(BaseModel):
    channel: Literal["WhatsApp_Parent", "Coach_Task", "Training_Modification", "Billing_Hold"]
    recipient: str
    subject_or_task: str
    draft_message: str
    priority: Literal["CRITICAL", "HIGH", "MEDIUM"]


class CaseAnalysis(BaseModel):
    player_id: str
    player_name: str
    squad: str
    signals: list[ExtractedSignal]
    risk_profile: RiskProfile
    guardrail: GuardrailDecision
    interventions: list[ProposedIntervention]
    similar_past_case: dict[str, Any] = Field(default_factory=dict)
