"""Build the stand-alone short, plus its editable and review materials."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from audit import art, review
from artwork import lock
from components import felt_note as tone
from cut import assemble
from media import RATE, exe, read_audio, wav
from tabletop import CONTACTS, FPS, FRAMES, SIZE, View, load_mesh, render, tile_points

SKILL = Path(__file__).resolve().parents[1]
EXAMPLE = SKILL / "examples" / "the-gap"
FONT = SKILL / "assets" / "CrimsonPro.ttf"
LINES = ((87, 144, "The last one is still standing."), (188, 239, "One gap broke the chain."))


def add_mono(track, part, frame, pan=0.):
    start = round(frame*RATE/FPS)
    end = min(start+len(part),len(track))
    track[start:end] += part[:end-start,None]*np.sqrt([(1-pan)/2,(1+pan)/2])


def audio(root):
    n=round(RATE*FRAMES/FPS)
    stems={key:np.zeros((n,2),np.float32) for key in ("voice","music","effects")}
    rng=np.random.default_rng(743)
    cues=[]
    def cue(name,frame,end):
        cues.append({"name":name,"frame":frame,"end":end})
    for take, (start,end,_) in enumerate(LINES,1):
        clip=read_audio(EXAMPLE / f"take{take}.wav")
        start_sample=round(start*RATE/FPS)
        stems["voice"][start_sample:start_sample+len(clip)] += .46*clip / np.abs(clip).max()
    for i,(frame,note) in enumerate(zip(CONTACTS,(146.83,174.61,220.,110.))):
        add_mono(stems["music"],tone(note,1.3,.175 if i<3 else .235,.27),frame)
        t=np.arange(round(.43*RATE))/RATE
        tick=.22*np.exp(-t/.009)*rng.normal(0,.55,len(t))+.19*np.exp(-t/.06)*np.sin(2*np.pi*(780-i*93)*t)
        wood=tone(163-i*12,.43,.20,.102) + tick
        add_mono(stems["effects"],wood,frame,-.4+i*.22)
        cue(("first contact","second contact","third contact","tile meets table")[i],frame,frame+13)
    # A quiet brushed surface introduces movement before the first click.
    t=np.arange(round(.5*RATE))/RATE
    rub=np.convolve(rng.normal(0,1,len(t)),np.ones(16)/16,mode="same")
    add_mono(stems["effects"],.060*rub*np.sin(np.pi*t/.5)**2,6,-.35)
    cue("tile edge rub",6,21)
    for frame,pitch,gain in ((2,73.42,.060),(120,110.,.043),(164,174.61,.058),(240,87.31,.055)):
        add_mono(stems["music"],tone(pitch,1.4,gain,.42),frame,.16)
    for key,sound in stems.items():
        wav(root/"audio"/f"{key}.wav",sound)
    return cues


def stamp(frame):
    ms=round(frame*1000/FPS)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def board(root, poses):
    img=Image.new("RGB",(960,400),(22,23,24))
    d=ImageDraw.Draw(img)
    for i,(caption,shot) in enumerate(poses):
        shot=shot.copy()
        shot.thumbnail((304,342))
        img.paste(shot,(i*320+(320-shot.width)//2,14+(342-shot.height)//2))
        d.text((i*320+160,376),caption,font=ImageFont.truetype(str(FONT),23),fill="ivory",anchor="mm")
    img.save(root/"review"/"source-board.jpg",quality=92)


def build(folder):
    folder=Path(folder).resolve()
    folder.mkdir(parents=True,exist_ok=False)
    for name in ("shots","audio","art","review"):
        (folder/name).mkdir()
    for name in ("domino.obj","domino.mtl","make_tile.py","reference.jpg","camera.svg"):
        shutil.copy2(EXAMPLE/name,folder/"art"/name)
    (folder/"production.md").write_text(
        "# The Gap\n\nThe fifth tile is too far away. Show its neighbour reaching the table, "
        "then let the viewer see the empty interval before hearing why it matters.\n\n"
        "[Camera decision](art/camera.svg) · [Photo](art/reference.jpg) · [Editable model](art/domino.obj) · "
        "[Model generator](art/make_tile.py) · [Photo, mesh and drawing](review/source-board.jpg)\n\n"
        "At 30 fps the contacts land at frames 23, 32, 41 and 58. The voice starts at 87 and 188. "
        "The camera reveals the final tile before the first line and closes toward the gap during the second.\n\n"
        "[Final film](the-gap.mp4) · [Captions](captions.srt) · [Editable film spec](project.json) · "
        "[Measured release](review/export.json) · [Reviewed artwork](art-lock.json)\n\n"
        "Original code, model, score and effects use MIT. The reference photograph is by Roland Scheicher "
        "and was dedicated to the public domain. The narration uses the Piper LJ Speech high voice. "
        "The lettering uses Crimson Pro under SIL OFL. "
        "[Source links and individual terms](https://github.com/PeterOla/MTake-DaVinci/blob/v0.1.0/skills/mtake-davinci/CREDITS.md)\n",
        encoding="utf8")
    shutil.copy2(Path(__file__).with_name("tabletop.py"),folder/"art"/"tabletop.py")
    mesh=load_mesh(folder/"art"/"domino.obj")
    proof_frame=102
    on=render(proof_frame,mesh,FONT,LINES)
    neutral=render(proof_frame,mesh,FONT,(),mode="neutral")
    off=render(proof_frame,mesh,FONT,LINES,omit=4)
    for name,img in (("on",on),("off",off),("neutral",neutral)):
        img.save(folder/"art"/f"{name}.png")
    board(folder,[("Photograph",Image.open(folder/"art"/"reference.jpg")),("Neutral mesh",neutral),("Shot camera",on)])
    view=View(proof_frame)
    xy=np.array(view.project(tile_points(mesh,4,proof_frame)))
    lo=(xy.min(axis=0)-[20,18])/SIZE
    hi=(xy.max(axis=0)+[32,18])/SIZE
    roi=np.clip([*lo,*hi],0,1).round(5).tolist()
    movie=folder/"shots"/"one-take.mp4"
    args=[exe("ffmpeg"),"-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{SIZE[0]}x{SIZE[1]}",
          "-r",str(FPS),"-i","pipe:0","-an","-c:v","libx264","-preset","veryfast","-crf","17",
          "-pix_fmt","yuv420p",str(movie)]
    with subprocess.Popen(args,stdin=subprocess.PIPE) as proc:
        for f in range(FRAMES):
            im=render(f,mesh,FONT,LINES)
            if f in (8,41,103,215):
                im.save(folder/"review"/f"frame-{f:03}.png")
            proc.stdin.write(im.tobytes())
        proc.stdin.close()
        if proc.wait():
            raise ValueError("FFmpeg could not finish the picture.")
    cues=audio(folder)
    captions="\n".join(f"{i}\n{stamp(s)} --> {stamp(e)}\n{text}\n" for i,(s,e,text) in enumerate(LINES,1))
    (folder/"captions.srt").write_text(captions,encoding="utf8")
    accents=[]
    for i,frame in enumerate(CONTACTS):
        a={"name":cues[i]["name"],"frame":frame,"speech_free":[21,66],
           "floor_dbfs":{"music":-28,"effects":-28},"rise_ratio":{"music":1.29,"effects":2.2}}
        if i==3:
            a.update(roi=[.43,.35,.92,.65],min_picture_change=.0012,pixel_step=10)
        accents.append(a)
    project={"title":"The Gap","fps":FPS,"size":SIZE,
             "scenes":[{"id":"bench","camera_sheet":"art/camera.svg","subjects":["standing tile"],
                        "approval":{"by":"MTake example authors","basis":"Authored teaching fixture, continuous pull to the gap."}}],
             "shots":[{"clip":"shots/one-take.mp4","frames":FRAMES,"scene":"bench",
                       "art_frames":[{"subject":"standing tile","frame":proof_frame}]}],
             "captions":"captions.srt","stems":{k:f"audio/{k}.wav" for k in ("music","effects","voice")},
             "subjects":[{"id":"standing tile","kind":"model","reference":"art/reference.jpg",
                          "rights":"Roland Scheicher, public-domain reference; original model under MIT.",
                          "read":"Paired face, inset division, rounded corners, thickness against the bench.",
                          "model":"art/domino.obj","on":"art/on.png","off":"art/off.png","neutral":"art/neutral.png",
                          "dependencies":["art/domino.mtl","art/tabletop.py"],
                          "roi":roi,"min_changed":.06}],
             "cues":cues,"accents":accents}
    (folder/"project.json").write_text(json.dumps(project,indent=2)+"\n",encoding="utf8")
    issues, evidence=art(folder,project)
    if issues:
        raise ValueError(" / ".join(issues))
    lock(folder,project,evidence,"MTake published demo fixture")
    master=assemble(folder,folder/"the-gap.mp4")
    result=review(folder,master)
    (folder/"review"/"export.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    if not result["passed"]:
        raise ValueError("Review failed: "+"; ".join(result["issues"]))
    print(f"{master}\nReview: {folder/'review'/'export.json'}")
