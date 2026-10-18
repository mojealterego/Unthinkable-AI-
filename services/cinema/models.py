from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


EvidenceType = Literal["synthetic", "mcp", "model_inference", "user_input"]


class Evidence(BaseModel):
    source: str
    type: EvidenceType
    statement: str


class ScenarioChange(BaseModel):
    scene_id: str
    change: str
    operational_effects: list[str] = Field(default_factory=list)


class StudioOption(BaseModel):
    name: str
    available_window: str
    fit_score: float
    estimated_cost: float
    notes: str
    evidence: list[str] = Field(default_factory=list)


class BudgetDelta(BaseModel):
    baseline: float
    revised: float
    delta: float
    currency: str = "USD"
    confidence: Literal["low", "medium", "high"] = "medium"


class Approval(BaseModel):
    status: Literal["required", "not_required", "approved"]
    actions: list[str] = Field(default_factory=list)


class IntegrationStatus(BaseModel):
    mode: Literal["demo", "configured"]
    gemini_configured: bool
    clickhouse_mcp_configured: bool


class StudioSyncResult(BaseModel):
    incident_summary: str
    scenario_changes: list[ScenarioChange]
    studio_options: list[StudioOption]
    budget: BudgetDelta
    approvals: Approval
    provenance: list[Evidence]
    integration: IntegrationStatus
    next_step: str
