"""Self-hosted FFmpeg film studio: no vendor credentials or chargeable provider."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.gateway.app import app
from services.film_studio.engine import Shot, Timeline

AUTH={"Authorization":"Bearer studio-test-key"}
URL="/api/film-studio"

class OwnStudioTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        env=patch.dict(os.environ,{"UNTHINKABLE_FILM_ROOT":self.temp.name})
        auth=patch("services.ai_studio.omni_orchestrator.API_KEY","studio-test-key")
        env.start();auth.start();self.addCleanup(env.stop);self.addCleanup(auth.stop)
        self.api=TestClient(app)

    def test_provider_free_and_capabilities_truthful(self):
        r=self.api.get(URL+"/capabilities",headers=AUTH)
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()["provider"],"unthinkable_self_hosted")
        self.assertFalse(r.json()["third_party_credits"])
        self.assertFalse(r.json()["external_accounts_required"])
        self.assertFalse(r.json()["native_wan_ai_inference"])

    def test_authenticated_upload_and_invalid_input(self):
        self.assertEqual(self.api.get(URL+"/capabilities").status_code,401)
        self.assertEqual(self.api.get(URL+"/assets").status_code,401)
        data=AUTH|{"Content-Type":"video/mp4"}
        self.assertEqual(self.api.post(URL+"/assets",headers=data,
            content=b"not media").status_code,422)
        self.assertEqual(self.api.get(URL+"/assets",headers=AUTH).json()["assets"],[])
        self.assertEqual(self.api.post(URL+"/assets",headers=AUTH|{"Content-Type":"application/zip"},
            content=b"PK12341234").status_code,415)

    def test_private_storage_and_approval(self):
        payload={"title":"Projekt 1","shots":[{"asset_id":"a"*32,
            "duration_seconds":3,"name":"Scena 1"}]}
        self.assertEqual(self.api.post(URL+"/timeline/render",headers=AUTH,
            json=payload).status_code,403)
        self.assertEqual(self.api.post(URL+"/timeline/validate",headers=AUTH,
            json=payload|{"confirm_media_rights":True}).status_code,422)
        with patch.dict(os.environ,{"UNTHINKABLE_FILM_ROOT":""}):
            self.assertEqual(self.api.get(URL+"/assets",headers=AUTH).status_code,503)

    def test_rejects_long_timeline(self):
        with self.assertRaises(ValueError):
            Timeline(title="Długi film",shots=[
                Shot(asset_id="b"*32,name="Ujęcie",duration_seconds=3600)
                for _ in range(13)
            ])

    @unittest.skipUnless(shutil.which("ffmpeg"),"ffmpeg unavailable on test host")
    def test_real_mp4_song_edit_and_private_download(self):
        ffmpeg=shutil.which("ffmpeg")
        assert ffmpeg
        source=Path(self.temp.name)/"source.mp4"
        song=Path(self.temp.name)/"track.mp3"
        a=subprocess.run([ffmpeg,"-hide_banner","-loglevel","error","-y",
            "-f","lavfi","-i","color=c=blue:s=320x180:r=24:d=1",
            "-c:v","libx264","-pix_fmt","yuv420p",str(source)],
            capture_output=True,timeout=30)
        self.assertEqual(a.returncode,0,a.stderr.decode(errors="replace"))
        b=subprocess.run([ffmpeg,"-hide_banner","-loglevel","error","-y",
            "-f","lavfi","-i","sine=frequency=330:duration=1",
            "-c:a","libmp3lame",str(song)],capture_output=True,timeout=30)
        self.assertEqual(b.returncode,0,b.stderr.decode(errors="replace"))
        assets=[]
        for f,mime in [(source,"video/mp4"),(song,"audio/mpeg")]:
            r=self.api.post(URL+"/assets",headers=AUTH|{"Content-Type":mime},
                            content=f.read_bytes())
            self.assertEqual(r.status_code,201,r.text)
            assets.append(r.json()["asset_id"])
        payload={"title":"Mój teledysk","shots":[{"asset_id":assets[0],
            "duration_seconds":1,"name":"Intro"}],"soundtrack_asset_id":assets[1],
            "output_width":640,"fps":24,"confirm_media_rights":True}
        r=self.api.post(URL+"/timeline/render",headers=AUTH,json=payload)
        self.assertEqual(r.status_code,202,r.text)
        self.assertIsNone(r.json()["provider"])
        job_id=r.json()["job_id"]
        for _ in range(180):
            status=self.api.get(URL+"/jobs/"+job_id,headers=AUTH)
            if status.json()["status"] in ("completed","failed"):
                break
            time.sleep(.1)
        self.assertEqual(status.json()["status"],"completed",status.text)
        self.assertEqual(self.api.get(URL+"/jobs/"+job_id+"/file").status_code,401)
        movie=self.api.get(URL+"/jobs/"+job_id+"/file",headers=AUTH)
        self.assertEqual(movie.status_code,200)
        self.assertEqual(movie.content[4:8],b"ftyp")
        self.assertEqual(movie.headers["cache-control"],"private, no-store")

if __name__=="__main__":
    unittest.main()
