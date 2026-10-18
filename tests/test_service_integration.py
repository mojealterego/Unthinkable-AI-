"""Backend contract tests for imported production-domain modules."""
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from services.ai_studio.consent_core import Access, ConsentError, Duration, Grant, authorize
from services.ai_studio.omni_orchestrator import OmniPlanRequest, Reference, _reference_conflicts, _scene_plan
from services.cinema.orchestrator import run_studiosync
from services.cinema.crew.orchestrator import build_run

class ReuseIntegrationTests(unittest.TestCase):
    def test_cinema_demo_provenance_never_claims_real_mcp_results(self):
        data = run_studiosync("Unexpected weather cancels exterior filming", mode="demo")
        self.assertEqual(data["integration"]["mode"], "demo")
        self.assertEqual(data["approvals"]["status"], "required")
        self.assertTrue(any(e["type"] == "synthetic" for e in data["provenance"]))
        self.assertFalse(any(e["type"] == "mcp" for e in data["provenance"]))

    def test_cinema_live_without_configuration_fails_closed(self):
        with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "", "CLICKHOUSE_MCP_URL": ""}):
            with self.assertRaises(RuntimeError):
                run_studiosync("Unexpected weather cancels exterior filming", mode="live")

    def test_scene_plan_and_reference_conflicts(self):
        refs = [Reference(id="actor-one", role="IDENTITY_SOURCE"),
                Reference(id="actor-two", role="FACE_SOURCE")]
        self.assertTrue(_reference_conflicts(refs))
        req = OmniPlanRequest(intent="Film", media_type="VIDEO",
            scene_count=3, target_duration_seconds=7440)
        scenes = _scene_plan(req)
        self.assertEqual(len(scenes), 3)
        self.assertEqual(sum(s["duration_seconds"] for s in scenes), 7440)
        self.assertTrue(all(s["qa_required"] for s in scenes))

    def test_film_crew_contains_18_reproducible_specialist_roles(self):
        plan = build_run("film-001", {"goal": "long film"})
        self.assertEqual(len(plan.steps), 18)
        self.assertEqual(plan.state["scene_duration_seconds"], 8)
        self.assertEqual(plan.state["quality_gate"], "not_started")
        self.assertEqual(plan.steps[0].agent, "Cinematic Commander")
        self.assertEqual(plan.steps[-1].agent, "Final Master Auditor")

    def test_scoped_consent_and_revocation(self):
        now = datetime(2026, 10, 18, tzinfo=timezone.utc)
        grant = Grant(subject_id="owner", resource="cinema:scene:1",
                      access=frozenset({Access.WRITE}), duration=Duration.TASK,
                      created_at=now, expires_at=now + timedelta(hours=1), task_id="t1")
        authorize(grant, subject_id="owner", resource="cinema:scene:1",
                  access=Access.WRITE, now=now, task_id="t1")
        for change in ({"subject_id":"other"}, {"access":Access.DELETE}, {"task_id":"t2"}):
            args = dict(subject_id="owner",resource="cinema:scene:1",access=Access.WRITE,now=now,task_id="t1")
            args.update(change)
            with self.assertRaises(ConsentError):
                authorize(grant,**args)
        with self.assertRaises(ConsentError):
            authorize(grant,subject_id="owner",resource="cinema:scene:1",
                      access=Access.WRITE,now=now+timedelta(hours=1),task_id="t1")

if __name__ == "__main__":
    unittest.main()
