"""Assemble frame-counted silent shots with aligned stems and captions."""
import tempfile
from fractions import Fraction
from pathlib import Path

import numpy as np

from media import RATE, STEMS, probe, read_audio, read_project, run, wav


def assemble(folder, output):
    from audit import art
    from artwork import verify_lock, picture_proof
    root, p = read_project(folder)
    problems, evidence = art(root,p)
    problems += verify_lock(root,p,evidence)
    if problems:
        raise ValueError(" / ".join(problems))
    target = Path(output).resolve()
    if target.exists():
        raise ValueError(f"Choose a new output file: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    fps, size = p["fps"], p["size"]
    frames = sum(shot["frames"] for shot in p["shots"])
    samples = round(frames * RATE / fps)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        work = Path(temp)
        parts = []
        for i, shot in enumerate(p["shots"]):
            source = root / shot["clip"]
            track = next(s for s in probe(source)["streams"] if s["codec_type"] == "video")
            if ([track["width"], track["height"]] != size or Fraction(track["avg_frame_rate"]) != fps
                    or Fraction(track["r_frame_rate"]) != fps
                    or int(track.get("nb_frames", 0)) != shot["frames"]):
                raise ValueError(f"{source.name}: re-export a constant-frame-rate shot at the declared size, fps and frame count.")
            filename = f"shot{i:04}.mp4"
            run("ffmpeg", ["-v", "error", "-i", source, "-map", "0:v:0", "-an", "-c:v", "libx264",
                           "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                           "-video_track_timescale", str(fps * 1000), work / filename])
            parts.append(f"file '{filename}'")
        (work / "shots.txt").write_text("\n".join(parts) + "\n", encoding="ascii")
        mix = np.zeros((samples, 2), np.float32)
        for name in STEMS:
            data = read_audio(root / p["stems"][name])
            if abs(len(data) - samples) > 1:
                raise ValueError(f"{name} must be printed from frame zero to the end at {RATE} Hz.")
            n = min(len(data), samples)
            mix[:n] += data[:n]
        if np.max(np.abs(mix)) >= 0.999:
            raise ValueError("The printed stems clip when summed. Lower the stem gains together and try again.")
        wav(work / "mix.wav", mix)
        args = ["-v", "error", "-f", "concat", "-safe", "1", "-i", work / "shots.txt",
                "-i", work / "mix.wav"]
        caption = p.get("captions")
        if caption:
            args += ["-i", root / caption]
        args += ["-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
        if caption:
            args += ["-map", "2:s:0", "-c:s", "mov_text"]
        run("ffmpeg", [*args, "-movflags", "+faststart", work / "delivery.mp4"])
        issues,_ = picture_proof(root,p,work/"delivery.mp4")
        if issues:
            raise ValueError(" / ".join(issues))
        (work / "delivery.mp4").replace(target)
    return target
