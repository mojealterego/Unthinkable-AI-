"""Optional FastAPI gateway. All AI planning endpoints default to deny absent API_KEY."""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from services.ai_studio.omni_orchestrator import router as creative_router, _auth
from services.cinema.orchestrator import run_studiosync
from services.cinema.crew.orchestrator import build_run
from dataclasses import asdict

app = FastAPI(title="Unthinkable AI Service Gateway", version="0.1.0")
app.include_router(creative_router)

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
