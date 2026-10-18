from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl


class ProjectBrief(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    premise: str = Field(min_length=1)
    genre: str | None = None
    tone: str | None = None
    visual_references: list[HttpUrl] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    target_duration_seconds: int | None = Field(default=None, ge=8)
    language: str = "en"


class SceneRequest(BaseModel):
    project_id: str
    scene_id: str
    brief: str
    prior_scene_ids: list[str] = Field(default_factory=list)
    references: list[HttpUrl] = Field(default_factory=list)


class AgentArtifact(BaseModel):
    agent: str
    artifact_type: str
    content: Any
    status: Literal["draft", "approved", "rejected", "needs_revision"] = "draft"
    revision: int = 1


class OrchestrationRun(BaseModel):
    run_id: str
    project_id: str
    status: Literal["queued", "running", "blocked", "completed", "failed"]
    artifacts: list[AgentArtifact] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
