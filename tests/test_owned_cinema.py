"""First-party Cinema smoke and safety tests, no external paid API."""
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.gateway.app import app
from services.cinema.owned_studio import EditProject, ffmpeg_arguments

ROOT="/api/cinema/owned"
AUTH={"Authorization":"Bearer local-test-key"}
MP4=b"\x00\x00\x00\x18ftypisom"+bytes(128)
MP3=b"ID3"+bytes(128)

class OwnedCinemaTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        env=patch.dict(os.environ,{"UNTHINKABLE_CINEMA_MEDIA_DIR":self.temp.name})
        auth=patch("services.ai_studio.omni_orchestrator.API_KEY","local-test-key")
        env.start();auth.start();self.addCleanup(env.stop);self.addCleanup(auth.stop)
        self.http=TestClient(app)
    def upload(self,id,ext,body):
        mime={"mp4":"video/mp4","mp3":"audio/mpeg"}[ext]
        return self.http.put(ROOT+"/assets/"+id+"?extension="+ext,
            headers=AUTH|{"Content-Type":mime},content=body)
    def project(self):
        return {"title":"Własny film","clips":[
            {"asset_id":"shot_A","trim_start_ms":0,"duration_ms":1000},
            {"asset_id":"shot_B","trim_start_ms":0,"duration_ms":1250}],
            "soundtrack_asset_id":"music_A","width":1280,"height":720,"fps":25}
    def render(self):
        return {"project":self.project(),"request_id":"ownrender_12345",
            "approved_for_local_render":True,"confirmed_media_rights":True}
    def test_no_visionstory_or_external_keys_required(self):
        self.assertEqual(self.http.get(ROOT+"/capabilities").status_code,401)
        r=self.http.get(ROOT+"/capabilities",headers=AUTH)
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json()["primary"])
        self.assertFalse(r.json()["external_api_keys_required"])
        self.assertFalse(r.json()["video_model_inference"])
    def test_ingest_local_assets_and_no_overwrite(self):
        self.assertEqual(self.upload("shot_A","mp4",MP4).status_code,200)
        self.assertEqual(self.upload("shot_A","mp4",MP4).status_code,409)
        self.assertEqual(self.upload("shot_B","mp4",b"invalid"+bytes(100)).status_code,422)
        self.assertEqual(self.upload("music_A","mp3",MP3).status_code,200)
        self.assertFalse((Path(self.temp.name)/"assets"/"shot_B.mp4").exists())
    def test_ffmpeg_compiler_has_local_inputs_and_music(self):
        p=EditProject.model_validate(self.project())
        args=ffmpeg_arguments(p,[Path("/tmp/shot_A.mp4"),Path("/tmp/shot_B.mp4")],
                              Path("/tmp/music_A.mp3"),Path("/tmp/render.mp4"))
        self.assertIn("concat=n=2:v=1:a=0[vout]"," ".join(args))
        self.assertIn("apad=pad_dur=2.250[aout]"," ".join(args))
        self.assertIn("file,pipe",args)
        self.assertEqual(args[-2],"2.250")
        self.assertNotIn("https://"," ".join(args))
    def test_render_is_actual_local_worker_and_idempotent(self):
        for id,ext,blob in (("shot_A","mp4",MP4),("shot_B","mp4",MP4),("music_A","mp3",MP3)):
            self.assertEqual(self.upload(id,ext,blob).status_code,200)
        commands=[]
        def runner(argv,**kwargs):
            commands.append(argv)
            Path(argv[-1]).write_bytes(MP4)
            return subprocess.CompletedProcess(argv,0)
        with patch("services.cinema.owned_studio.shutil.which",return_value="/usr/bin/ffmpeg"), \
             patch("services.cinema.owned_studio.subprocess.run",side_effect=runner):
            result=self.http.post(ROOT+"/renders",headers=AUTH,json=self.render())
        self.assertEqual(result.status_code,200,result.text)
        status=self.http.get(ROOT+"/renders/ownrender_12345",headers=AUTH)
        self.assertEqual(status.json()["status"],"completed",status.text)
        self.assertEqual(len(commands),1)
        self.assertEqual(self.http.get(ROOT+"/renders/ownrender_12345/file").status_code,401)
        mp4=self.http.get(ROOT+"/renders/ownrender_12345/file",headers=AUTH)
        self.assertEqual(mp4.status_code,200)
        self.assertEqual(mp4.content,MP4)
        with patch("services.cinema.owned_studio.subprocess.run") as mocked:
            repeat=self.http.post(ROOT+"/renders",headers=AUTH,json=self.render())
            self.assertTrue(repeat.json()["reused"])
            mocked.assert_not_called()
        changed=self.render()
        changed["project"]["title"]="Changed"
        self.assertEqual(self.http.post(ROOT+"/renders",headers=AUTH,json=changed).status_code,409)
    def test_missing_assets_or_rights_cannot_trigger_worker(self):
        self.assertEqual(self.http.post(ROOT+"/renders",headers=AUTH,json=self.render()).status_code,422)
        self.assertEqual(self.http.post(ROOT+"/renders",headers=AUTH,
            json=self.render()|{"approved_for_local_render":False}).status_code,403)
        self.assertEqual(self.http.post(ROOT+"/renders",headers=AUTH,
            json=self.render()|{"confirmed_media_rights":False}).status_code,403)
    def test_malformed_timeline_does_not_render(self):
        project=self.project()
        project["clips"][0]["asset_id"]="../../etc/passwd"
        self.assertEqual(self.http.post(ROOT+"/renders",headers=AUTH,
            json=self.render()|{"project":project}).status_code,422)

if __name__=="__main__":
    unittest.main()
