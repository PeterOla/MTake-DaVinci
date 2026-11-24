"""Behaviour tests on a second, two-shot project; no reference-film assets required."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SKILL=Path(__file__).resolve().parents[1]/"skills"/"mtake-davinci"
sys.path.insert(0,str(SKILL/"scripts"))
from artwork import lock
from audit import art, review
from cut import assemble
from media import RATE, run, wav
from tabletop import angle, POSITIONS, CONTACTS, HEIGHT, THICKNESS


class ReleaseReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch=tempfile.TemporaryDirectory()
        cls.root=Path(cls.scratch.name)
        r=cls.root
        size=(96,160)
        off=Image.new("RGB",size,(17,18,19))
        on=off.copy()
        ImageDraw.Draw(on).rectangle((24,50,60,104),fill=(138,118,94))
        neutral=off.copy()
        ImageDraw.Draw(neutral).rectangle((24,50,60,104),fill=(100,100,100))
        for name,image in (("off",off),("on",on),("neutral",neutral)):
            image.save(r/(name+".png"))
            run("ffmpeg",["-v","error","-loop","1","-framerate","20","-i",r/(name+".png"),
                          "-frames:v","10","-c:v","libx264","-pix_fmt","yuv420p",r/(name+".mp4")])
        (r/"shape.obj").write_text("o test\nv 0 0 0\nv 0 1 0\nv 1 0 0\nf 1 2 3\n")
        (r/"camera.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        (r/"titles.srt").write_text("1\n00:00:00,600 --> 00:00:00,950\nThe signal.\n")
        cls.buffers={}
        for key,hz,gain,frame in (("voice",750,.12,15),("effects",160,.22,10),("music",330,.18,10)):
            data=np.zeros((RATE,2),np.float32)
            length=int(.16*RATE)
            wave=np.sin(np.arange(length)*2*np.pi*hz/RATE)*np.linspace(gain,0,length)
            start=round(frame*RATE/20)
            data[start:start+length]=wave[:,None]
            cls.buffers[key]=data
            wav(r/(key+".wav"),data)
        cls.spec={"title":"The signal","fps":20,"size":size,
                  "scenes":[{"id":"signal","camera_sheet":"camera.svg","subjects":["lamp"],
                             "approval":{"by":"test fixture","basis":"Two test poses."}}],
                  "shots":[{"clip":"off.mp4","frames":10,"scene":"signal"},
                           {"clip":"on.mp4","frames":10,"scene":"signal",
                            "art_frames":[{"subject":"lamp","frame":0}]}],
                  "subjects":[{"id":"lamp","kind":"model","reference":"neutral.png","rights":"Original test fixture.",
                               "read":"Lit panel","model":"shape.obj","neutral":"neutral.png","on":"on.png",
                               "off":"off.png","roi":[.2,.26,.72,.73],"min_changed":.12}],
                  "stems":{k:k+".wav" for k in cls.buffers},"captions":"titles.srt",
                  "cues":[{"name":"click","frame":10,"end":13}],
                  "accents":[{"name":"lamp on","frame":10,"speech_free":[8,14],
                              "floor_dbfs":{"effects":-28,"music":-28},"rise_ratio":{"effects":2,"music":2},
                              "roi":[.22,.28,.70,.69],"min_picture_change":.25}]}
        cls.write(cls.spec)
        errors,evidence=art(r,cls.spec)
        if errors: raise ValueError(errors)
        lock(r,cls.spec,evidence,"fixture")
        cls.movie=assemble(r,r/"candidate.mp4")

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    @classmethod
    def write(cls,p):
        (cls.root/"project.json").write_text(json.dumps(p),encoding="utf8")

    def setUp(self):
        self.write(self.spec)

    def tearDown(self):
        for k,data in self.buffers.items():
            wav(self.root/(k+".wav"),data)
        self.write(self.spec)

    def issues(self):
        return " ".join(review(self.root,self.movie)["issues"])

    def test_finished_second_film(self):
        report=review(self.root,self.movie)
        self.assertTrue(report["passed"],report)
        self.assertEqual(report["delivered_art_frames"][0]["frame"],10)
        self.assertEqual(report["ten_second_windows"][0]["effect_starts"],1)

    def test_mute_score(self):
        wav(self.root/"music.wav",self.buffers["music"]*0)
        self.assertIn("music onset",self.issues())

    def test_effect_one_frame_late(self):
        wav(self.root/"effects.wav",np.roll(self.buffers["effects"],RATE//20,axis=0))
        self.assertIn("effects onset",self.issues())

    def test_speech_on_beat(self):
        wav(self.root/"voice.wav",np.roll(self.buffers["voice"],-5*RATE//20,axis=0))
        self.assertIn("voice in the protected",self.issues())

    def test_wrong_region_and_empty_switch_off(self):
        adjusted=copy.deepcopy(self.spec)
        adjusted["subjects"][0]["roi"]=[0,0,.15,.20]
        self.assertTrue(art(self.root,adjusted)[0])
        adjusted["subjects"][0].update(roi=[.2,.26,.72,.73],off="on.png")
        self.assertTrue(art(self.root,adjusted)[0])

    def test_stale_model_prevents_assembly(self):
        path=self.root/"shape.obj"
        before=path.read_bytes()
        try:
            path.write_bytes(before+b"# revision\n")
            with self.assertRaisesRegex(ValueError,"changed after review"):
                assemble(self.root,self.root/"stale.mp4")
        finally:
            path.write_bytes(before)
        self.assertFalse((self.root/"stale.mp4").exists())

    def test_visible_substitution_prevents_delivery(self):
        p=copy.deepcopy(self.spec)
        p["shots"][1]["clip"]="off.mp4"
        self.write(p)
        with self.assertRaisesRegex(ValueError,"does not match"):
            assemble(self.root,self.root/"absent.mp4")
        self.assertFalse((self.root/"absent.mp4").exists())

    def test_unregistered_subject_prevents_delivery(self):
        p=copy.deepcopy(self.spec)
        p["shots"][1]["art_frames"]=[]
        self.write(p)
        with self.assertRaisesRegex(ValueError,"no delivery-frame"):
            assemble(self.root,self.root/"no-landmark.mp4")

    def test_art_handoff_before_shots(self):
        p=copy.deepcopy(self.spec)
        p["shots"]=[]
        self.write(p)
        subprocess.run([sys.executable,str(SKILL/"scripts"/"mtake.py"),"art",self.root],
                       check=True,capture_output=True)


class WorldMotion(unittest.TestCase):
    def test_contacts_and_gap(self):
        import math
        for idx,frame in enumerate(CONTACTS[:3]):
            front=POSITIONS[idx]+HEIGHT*math.sin(angle(idx,frame))
            self.assertAlmostEqual(front,POSITIONS[idx+1]-THICKNESS)
            self.assertEqual(angle(idx+1,frame),0.)
            self.assertGreater(angle(idx+1,frame+1),0.)
        self.assertLess(POSITIONS[3]+HEIGHT,POSITIONS[4]-THICKNESS)
        self.assertEqual(angle(4,269),0.)


if __name__=="__main__":
    unittest.main()
