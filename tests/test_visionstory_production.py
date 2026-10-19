"""VisionStory production regression, all provider operations mocked."""
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.gateway.app import app
from services.visionstory.client import VisionStoryRest

P="/api/cinema/visionstory"
H={"Authorization":"Bearer test-gateway"}
AUDIO={"audio":{"asset_id":"owned_audio"},"confirmed_audio_rights":True,
       "approved_for_paid_processing":True}
CLIP={"model_id":"seedance-2.0","prompt":"A quiet cinematic street portrait",
      "duration_sec":8,"resolution":"720p","aspect_ratio":"9:16",
      "client_request_id":"request00001","approved_for_paid_generation":True,
      "confirmed_media_rights":True,"max_approved_credits":20,
      "refs":[{"asset_id":"owned_reference"}]}

class Provider:
    def __init__(self):
        self.calls=[]
        self.price=16
        self.credits_left=50
    def __call__(self,method,path,payload):
        self.calls.append((method,path,payload))
        if path=="/api/v1/billing/credits":
            return {"data":{"remaining":self.credits_left}}
        if path=="/api/v1/ai_video/models":
            return {"data":{"models":[{"model_id":"seedance-2.0","params":{
                "duration_sec":{"values":[8]},
                "resolution":{"values":["720p"]},
                "aspect_ratio":{"values":["9:16"]},
                "prompt":{"max_length":5000},"refs":{"max":2},
            }}]}}
        if path.startswith("/api/v1/ai_video/cost?"):
            return {"data":{"credit":self.price}}
        if path=="/api/v1/ai_video" and method=="POST":
            return {"data":{"video_id":"video_001","status":"queued","cost_credit":self.price}}
        if path.startswith("/api/v1/ai_video?video_id="):
            return {"data":{"video_id":"video_001","status":"created","video_url":"https://cdn.example/v.mp4","cost_credit":16}}
        if path=="/api/v1/audio/transcribe":
            return {"data":{"text":"Witaj","words":[{"text":"Witaj","start_sec":0.0,"end_sec":0.8}],
                "srt":"1\n00:00:00,000 --> 00:00:00,800\nWitaj\n","duration_sec":0.8,
                "cost_credit":1,"language":"pl"}}
        if path=="/api/v1/audio/align":
            return {"data":{"words":[{"text":"Witaj","start_sec":0.0,"end_sec":0.8}],
                "duration_sec":0.8,"cost_credit":1}}
        raise AssertionError(path)

class Tests(unittest.TestCase):
    def setUp(self):
        self.remote=Provider()
        self.http=TestClient(app)
        a=patch("services.ai_studio.omni_orchestrator.API_KEY","test-gateway")
        b=patch("services.visionstory.production.configured_client",
                return_value=VisionStoryRest("fake-provider",transport=self.remote))
        a.start();b.start();self.addCleanup(a.stop);self.addCleanup(b.stop)
    def test_srt_without_diarization_and_alignment(self):
        transcript=self.http.post(P+"/audio/transcribe",headers=H,
            json=AUDIO|{"srt":True,"diarize":False})
        self.assertEqual(transcript.status_code,200,transcript.text)
        self.assertIn("Witaj",transcript.json()["srt"])
        self.assertFalse(self.remote.calls[-1][2]["diarize"])
        alignment=self.http.post(P+"/audio/align",headers=H,
            json=AUDIO|{"text":"Witaj"})
        self.assertEqual(alignment.status_code,200,alignment.text)
        self.assertEqual(alignment.json()["words"][0]["text"],"Witaj")
    def test_quote_does_not_submit_and_submit_respects_budget(self):
        quote=self.http.post(P+"/ai-video/estimate",headers=H,json=CLIP)
        self.assertEqual(quote.status_code,200,quote.text)
        self.assertEqual(quote.json()["credits_estimated"],16)
        self.assertFalse(any(p=="/api/v1/ai_video" for _,p,_ in self.remote.calls))
        insufficient=self.http.post(P+"/ai-video",headers=H,
            json=CLIP|{"max_approved_credits":10})
        self.assertEqual(insufficient.status_code,409,insufficient.text)
        self.assertFalse(any(p=="/api/v1/ai_video" for _,p,_ in self.remote.calls))
        accepted=self.http.post(P+"/ai-video",headers=H,json=CLIP)
        self.assertEqual(accepted.status_code,200,accepted.text)
        self.assertEqual(accepted.json()["client_request_id"],"request00001")
        self.assertEqual(self.remote.calls[-1][2]["refs"],[{"asset_id":"owned_reference"}])
        status=self.http.get(P+"/ai-video/video_001",headers=H)
        self.assertEqual(status.status_code,200,status.text)
        self.assertEqual(status.json()["status"],"created")
    def test_payments_require_auth_and_explicit_user_rights(self):
        self.assertEqual(self.http.post(P+"/ai-video",json=CLIP).status_code,401)
        self.assertEqual(self.http.post(P+"/ai-video",headers=H,
            json=CLIP|{"approved_for_paid_generation":False}).status_code,403)
        self.assertEqual(self.http.post(P+"/audio/transcribe",headers=H,
            json=AUDIO|{"confirmed_audio_rights":False}).status_code,403)
        self.assertEqual(self.remote.calls,[])
    def test_invalid_clip_model_options_and_refs_not_submitted(self):
        for changes in [
            {"duration_sec":9},{"resolution":"4k"},
            {"refs":[{"asset_id":"a"}],"first_frame":{"asset_id":"b"}},
            {"refs":[{"url":"https://unknown.example/file.jpg"}]},
        ]:
            with self.subTest(changes=changes):
                resp=self.http.post(P+"/ai-video",headers=H,json=CLIP|changes)
                self.assertEqual(resp.status_code,422,resp.text)
        self.assertFalse(any(p=="/api/v1/ai_video" for _,p,_ in self.remote.calls))
    def test_credit_not_available_never_issues_expensive_call(self):
        self.remote.credits_left=0
        answer=self.http.post(P+"/ai-video",headers=H,json=CLIP)
        self.assertEqual(answer.status_code,402,answer.text)
        self.assertFalse(any(p=="/api/v1/ai_video" for _,p,_ in self.remote.calls))

if __name__=="__main__":
    unittest.main()
