"""Optional FastAPI gateway. All AI planning endpoints default to deny absent API_KEY."""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
import os
from services.film_studio.router import router as own_film_router
from services.visionstory.router import router as visionstory_router
from services.visionstory.speech import router as visionstory_speech_router
from services.visionstory.production import router as visionstory_production_router
from services.visionstory.media_tools import router as visionstory_media_router
from services.virtual_number.router import router as virtual_number_router
from services.web_studio.router import router as web_studio_router
from services.web.router import router as web_router
from services.web.nocode_router import router as nocode_router
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from services.ai_studio.omni_orchestrator import router as creative_router, _auth
from services.cinema.orchestrator import run_studiosync
from services.cinema.owned_studio import router as owned_cinema_router
from services.cinema.crew.orchestrator import build_run
from dataclasses import asdict

app = FastAPI(title="Unthinkable AI Service Gateway", version="0.1.0")
app.include_router(creative_router)
app.include_router(virtual_number_router)
app.include_router(web_studio_router)
app.include_router(web_router)
app.include_router(nocode_router)
app.include_router(own_film_router)
# Historical provider adapters are opt-in only. Unthinkable never needs them.
if os.getenv("UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY", "0") == "1":
    app.include_router(visionstory_router)
    app.include_router(visionstory_speech_router)
    app.include_router(visionstory_production_router)
    app.include_router(visionstory_media_router)
app.include_router(owned_cinema_router)

class IncidentRequest(BaseModel):
    description: str = Field(min_length=10, max_length=4000)
    mode: str = Field(default="demo", pattern="^(demo|live)$")

@app.get("/health")
def health():
    return {"status": "ok", "modules": ["cinema", "creative_orchestrator"],
            "real_media_generation": False}

@app.post("/api/cinema/incident")
def analyze_incident(data: IncidentRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        return run_studiosync(data.description, mode=data.mode)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

class CrewRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=128)
    brief: dict = Field(default_factory=dict)

@app.post("/api/cinema/crew")
def build_crew(req: CrewRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    plan = build_run(req.project_id, req.brief)
    return {
        "project_id": plan.project_id,
        "mode": "planning_only",
        "scene_duration_seconds": plan.state["scene_duration_seconds"],
        "steps": [asdict(s) for s in plan.steps],
        "requires_human_approval": True,
        "generated_video": False,
    }

class ShotInput(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    durationSeconds: int = Field(ge=1, le=86400)
    prompt: str = Field(default="", max_length=10000)
    actorReference: str = Field(default="", max_length=2048)
    mediaReference: str = Field(default="", max_length=2048)
    approved: bool = False

class FilmProjectInput(BaseModel):
    format: Literal["unthinkable-film-shotlist-v1"] = "unthinkable-film-shotlist-v1"
    title: str = Field(min_length=1, max_length=200)
    masterPrompt: str = Field(default="", max_length=12000)
    shots: list[ShotInput] = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def check_project(self):
        if len({shot.id for shot in self.shots}) != len(self.shots):
            raise ValueError("Duplicate shot identifiers")
        if sum(shot.durationSeconds for shot in self.shots) > 43200:
            raise ValueError("Total project duration exceeds the 12-hour planning limit")
        return self

@app.post("/api/cinema/projects/plan")
def plan_project(project: FilmProjectInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    production = build_run("unthinkable-film-shotlist-v1", {
        "title": project.title, "master_prompt": project.masterPrompt,
    })
    cursor = 0
    timeline = []
    for shot in project.shots:
        timeline.append({
            "id": shot.id,
            "name": shot.name,
            "start_seconds": cursor,
            "duration_seconds": shot.durationSeconds,
            "end_seconds": cursor + shot.durationSeconds,
            "prompt": shot.prompt,
            "actor_reference": shot.actorReference,
            "media_reference": shot.mediaReference,
            "approved": shot.approved,
        })
        cursor += shot.durationSeconds
    return {
        "format": "unthinkable-production-plan-v1",
        "mode": "planning_only",
        "project_title": project.title,
        "master_prompt": project.masterPrompt,
        "duration_seconds": cursor,
        "scenes": timeline,
        "crew": [asdict(step) for step in production.steps],
        "quality_gate": production.state["quality_gate"],
        "unapproved_shot_ids": [s.id for s in project.shots if not s.approved],
        "requires_human_approval": True,
        "generated_video": False,
        "live_model_jobs": 0,
    }
