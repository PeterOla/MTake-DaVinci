"""Bind a scene's approved camera and source evidence to visible delivery frames."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

from media import fingerprint, movie_frame, region


def inventory(root, p, findings):
    issues, scenes = [], []
    ids=[s["id"] for s in p.get("subjects",[])]
    if len(set(ids))!=len(ids):
        issues.append("Use a unique id for each registered subject appearance.")
    expected=set()
    seen=set()
    for scene in p.get("scenes",[]):
        sid=scene["id"]
        approval=scene.get("approval",{})
        sheet=root/scene.get("camera_sheet","")
        if sid in seen or not sheet.is_file() or not approval.get("by") or not approval.get("basis"):
            issues.append(f"{sid}: record the approved camera sheet, decision maker and basis.")
            continue
        seen.add(sid)
        expected.update(scene["subjects"])
        scenes.append({"scene":sid,"camera_sha256":fingerprint(sheet),"approval":approval,
                       "planned_subjects":sorted(scene["subjects"])})
    if not scenes or set(ids)!=expected:
        issues.append("The subjects declared at camera planning and the art evidence must agree.")
    return issues, {"scenes":scenes,"subjects":findings}


def lock(root,p,findings,reviewer):
    issues, snapshot=inventory(root,p,findings)
    if issues or not reviewer.strip():
        raise ValueError(" / ".join(issues or ["Name the person or agent who inspected the artwork."]))
    record={"reviewed_by":reviewer.strip(),"snapshot":snapshot}
    output=root/"art-lock.json"
    output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf8")
    return output


def verify_lock(root,p,findings):
    issues,snap=inventory(root,p,findings)
    file=root/"art-lock.json"
    if not file.is_file():
        return issues+["Missing art-lock.json. Inspect the board, then run lock-art."]
    record=json.loads(file.read_text(encoding="utf8"))
    if record.get("snapshot")!=snap or not record.get("reviewed_by"):
        issues.append("Artwork or camera changed after review; inspect the board and renew the art lock.")
    scenes={s["id"]:set(s["subjects"]) for s in p.get("scenes",[])}
    checked={s:set() for s in scenes}
    for shot in p["shots"]:
        sid=shot.get("scene")
        if sid not in scenes:
            issues.append("Every shot must refer to its approved scene.")
            continue
        for landmark in shot.get("art_frames",[]):
            subject=landmark["subject"]
            if subject not in scenes[sid] or not 0<=landmark["frame"]<shot["frames"]:
                issues.append(f"{sid}: invalid artwork checkpoint for {subject}.")
            else:
                checked[sid].add(subject)
    for sid,items in scenes.items():
        if items!=checked[sid]:
            issues.append(f"{sid}: a planned subject has no delivery-frame checkpoint.")
    return issues


def picture_proof(root,p,movie):
    subjects={s["id"]:s for s in p["subjects"]}
    problems, rows=[], []
    offset=0
    for shot in p["shots"]:
        for mark in shot.get("art_frames",[]):
            f=offset+mark["frame"]
            s=subjects[mark["subject"]]
            frame=np.asarray(movie_frame(movie,f,p["fps"]),dtype=float)
            with Image.open(root/s["on"]) as im:
                on=np.asarray(im.convert("RGB"),dtype=float)
            if frame.shape!=on.shape:
                problems.append(f"{s['id']}: delivery camera size differs from the artwork proof.")
                continue
            box=region(on,s.get("roi",[0,0,1,1]))
            delta_on=np.abs(frame[box]-on[box])
            if s["kind"]=="model":
                with Image.open(root/s["off"]) as im:
                    off=np.asarray(im.convert("RGB"),dtype=float)[box]
                mask=np.max(np.abs(on[box]-off),axis=2)>=10
                if not mask.any():
                    problems.append(f"{s['id']}: no subject pixels available to compare.")
                    continue
                error=float(delta_on[mask].mean())
                absent=float(np.abs(frame[box]-off)[mask].mean())
                good=error<.65*absent and error<=s.get("max_delivery_error",12)
            else:
                error=float(delta_on.mean())
                good=error<=s.get("max_delivery_error",8)
            rows.append({"subject":s["id"],"frame":f,"mean_pixel_error":round(error,3)})
            if not good:
                problems.append(f"{s['id']}: final frame {f} does not match the inspected shot artwork.")
        offset+=shot["frames"]
    return problems,rows
