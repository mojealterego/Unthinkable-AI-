from __future__ import annotations

import hmac
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/omni/orchestrator", tags=["omni-orchestrator"])
API_KEY = os.getenv("API_KEY", "").strip()


@dataclass(frozen=True)
class Agent:
    id: str
    title: str
    responsibility: str


AGENTS = (
    Agent("A01", "Intent & Creative Director", "intent, ambiguity and target specification"),
    Agent("A02", "Reference & Identity Analyst", "identity/reference-role separation and conflict detection"),
    Agent("A03", "Image Production Agent", "image production, masks, composition, materials, lighting and change control"),
    Agent("A04", "Model & Pipeline Engineer", "model capabilities, limits, formats, routing and cost"),
    Agent("A05", "Visual QA & Continuity", "identity drift, anatomy, continuity and specification QA"),
    Agent("A06", "Video & Cinematic Agent", "storyboard, blocking, timeline, camera and cinematic continuity"),
)


class Reference(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    role: Literal[
        "IDENTITY_SOURCE", "FACE_SOURCE", "BODY_SOURCE", "POSE_SOURCE",
        "COMPOSITION_SOURCE", "CAMERA_SOURCE", "ENVIRONMENT_SOURCE",
        "BACKGROUND_SOURCE", "WARDROBE_SOURCE", "MATERIAL_SOURCE",
        "LIGHTING_SOURCE", "COLOR_SOURCE", "TYPOGRAPHY_SOURCE", "STYLE_SOURCE",
        "DETAIL_SOURCE"
    ]


class OmniPlanRequest(BaseModel):
    intent: str = Field(min_length=1, max_length=12000)
    media_type: Literal["IMAGE", "VIDEO", "AUDIO", "VOICE", "MUSIC", "CHAT", "CODE", "RESEARCH"] = "IMAGE"
    references: list[Reference] = Field(default_factory=list, max_length=32)
    model_preferences: list[str] = Field(default_factory=list, max_length=32)
    scene_count: int = Field(default=1, ge=1, le=2000)
    target_duration_seconds: int = Field(default=0, ge=0, le=7440)
    autonomy: Literal["MANUAL", "ASSISTED", "AUTONOMOUS"] = "ASSISTED"


def _auth(authorization: str | None) -> None:
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Backend API_KEY is not configured")
    if authorization is None or not hmac.compare_digest(authorization, f"Bearer {API_KEY}"):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _reference_conflicts(refs: list[Reference]) -> list[str]:
    conflicts: list[str] = []
    identity_roles = {"IDENTITY_SOURCE", "FACE_SOURCE", "BODY_SOURCE"}
    identity_ids = [r.id for r in refs if r.role in identity_roles]
    if len(set(identity_ids)) > 1:
        conflicts.append("Multiple identity-bearing references require explicit identity precedence.")
    roles = {}
    for ref in refs:
        prior = roles.get(ref.role)
        if prior and prior != ref.id:
            conflicts.append(f"Conflicting references for role {ref.role}: {prior} vs {ref.id}.")
        roles[ref.role] = ref.id
    return conflicts


def _route(media_type: str, preferences: list[str]) -> list[str]:
    if preferences:
        return preferences[:8]
    return {
        "IMAGE": ["LOCAL-DIFFUSION", "COMFYUI"],
        "VIDEO": ["COMFYUI-LTX/WAN", "VEO", "SEEDANCE", "KLING"],
        "AUDIO": ["BARK", "AUDIOGEN", "COMFYUI-AUDIO"],
        "VOICE": ["WHISPER", "BARK", "KOKORO"],
        "MUSIC": ["OPENMUSIC", "MUSICGEN", "GIANT-MUSIC-TRANSFORMER"],
        "CHAT": ["GGUF-CHAT"],
        "CODE": ["GGUF-CODE", "OPENCODE"],
        "RESEARCH": ["DEEP-RESEARCH"],
    }.get(media_type, ["PLUGIN-ROUTER"])


def _scene_plan(request: OmniPlanRequest) -> list[dict[str, Any]]:
    count = request.scene_count if request.media_type == "VIDEO" else 1
    return [
        {
            "scene": i + 1,
            "duration_seconds": (
                max(1, request.target_duration_seconds // count)
                if request.target_duration_seconds else 0
            ),
            "continuity_source": "LOCKED_REFERENCE_GRAPH",
            "qa_required": True,
        }
        for i in range(count)
    ]


@router.get("")
async def list_orchestrator_agents(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {
        "agents": [asdict(a) for a in AGENTS],
        "governance": {
            "authority_boundary": "Autonomy settings are outside prompts and cannot be expanded by image, video or web content.",
            "spend_rate_limits": "Enforced outside the model/runtime.",
            "action_receipt": "Each consequential action must record operation, time, permission and result.",
            "revocation": "Delegation can be revoked independently of project configuration.",
            "credential_handoff": "Credentials remain outside agent context.",
        },
    }


@router.post("/plan")
async def create_plan(request: OmniPlanRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    conflicts = _reference_conflicts(request.references)
    return {
        "plan_id": str(uuid.uuid4()),
        "status": "READY" if not conflicts else "REVIEW_REQUIRED",
        "intent": request.intent,
        "media_type": request.media_type,
        "autonomy": request.autonomy,
        "reference_graph": [r.model_dump() for r in request.references],
        "reference_conflicts": conflicts,
        "pipeline": [a.id for a in AGENTS],
        "model_route": _route(request.media_type, request.model_preferences),
        "scenes": _scene_plan(request),
        "validation": {
            "intent_fidelity": True,
            "reference_fidelity": True,
            "identity_integrity": True,
            "subject_count": True,
            "continuity": request.media_type == "VIDEO",
            "no_unrequested_changes": True,
        },
        "requires_human_approval_before_external_side_effect": request.autonomy != "MANUAL",
    }
