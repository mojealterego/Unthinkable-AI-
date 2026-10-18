from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentStep:
    agent: str
    purpose: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    blocking: bool = True


@dataclass
class ProductionRun:
    project_id: str
    brief: dict[str, Any]
    steps: list[AgentStep] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)

    def canonicalize(self) -> None:
        self.state.setdefault("scene_duration_seconds", 8)
        self.state.setdefault("continuity_revision", 0)
        self.state.setdefault("quality_gate", "not_started")


DEFAULT_PIPELINE: tuple[AgentStep, ...] = (
    AgentStep("Cinematic Commander", "accept brief, resolve trade-offs, maintain final authority"),
    AgentStep("Story Architect", "build premise, theme, dramaturgy and beat architecture"),
    AgentStep("Screenwriter", "compile screenplay, dialogue, action and scene intent"),
    AgentStep("Character Architect", "lock identity, psychology, objectives and continuity"),
    AgentStep("Production Designer", "define world, sets, props, materials and spatial rules"),
    AgentStep("Director of Photography", "define visual grammar, framing, exposure and camera intent"),
    AgentStep("Lens & Optics Specialist", "validate focal length, DOF, optical behavior and signature"),
    AgentStep("Lighting Director", "define physical lighting topology and exposure continuity"),
    AgentStep("Performance Director", "define blocking, gaze, gesture, facial and bodily performance"),
    AgentStep("Physics & Motion Supervisor", "validate kinematics, gravity, cloth, particles and temporal coherence"),
    AgentStep("Sound Director", "design production sound, ambience, Foley, SFX and perspective"),
    AgentStep("Music Director", "define score motifs, instrumentation, dynamics and synchronization"),
    AgentStep("Editor", "define editorial rhythm, coverage, transitions and causality"),
    AgentStep("VFX Supervisor", "define VFX, compositing, cleanup and simulation requirements"),
    AgentStep("Generative Video Architect", "compile provider-agnostic generation plan and failure recovery"),
    AgentStep("Continuity Intelligence", "lock temporal, identity, spatial, prop, lighting and motion state"),
    AgentStep("Visual QC Auditor", "independently inspect generated output against acceptance criteria"),
    AgentStep("Final Master Auditor", "release-gate the sequence and reject unresolved defects"),
)


def build_run(project_id: str, brief: dict[str, Any]) -> ProductionRun:
    run = ProductionRun(project_id=project_id, brief=brief, steps=list(DEFAULT_PIPELINE))
    run.canonicalize()
    return run
