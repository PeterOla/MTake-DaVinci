"""Media I/O used by the portable editor and review commands."""
import hashlib
import json
import math
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image

RATE = 48000
STEMS = ("voice", "music", "effects")


def exe(name):
    path = shutil.which(name)
    if not path:
        raise ValueError(f"Install {name} and add it to PATH; see references/setup.md.")
    return path


def run(name, args, **kwargs):
    return subprocess.run([exe(name), *map(str, args)], check=True, **kwargs)


def probe(path):
    result = run("ffprobe", ["-v", "error", "-show_format", "-show_streams", "-of", "json", path],
                 capture_output=True)
    return json.loads(result.stdout)


def fingerprint(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_audio(path):
    result = run("ffmpeg", ["-v", "error", "-i", path, "-map", "0:a:0", "-ar", RATE,
                            "-ac", 2, "-f", "f32le", "pipe:1"], capture_output=True)
    return np.frombuffer(result.stdout, dtype="<f4").reshape(-1, 2)


def wav(path, sound):
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes((np.clip(sound, -1, 1) * 32767).astype("<i2").tobytes())


def rms(a):
    return math.sqrt(float(np.mean(np.square(a, dtype=np.float64)))) if len(a) else 0.


def db(a):
    v = rms(a)
    return round(20 * math.log10(v), 2) if v else None


def movie_frame(path, index, fps):
    # Decode by frame index. Seeking in seconds can select a neighbouring frame.
    import io
    result = run("ffmpeg", ["-v", "error", "-i", path, "-vf", f"select=eq(n\\,{index})",
                            "-frames:v", 1, "-c:v", "png", "-f", "image2pipe", "pipe:1"],
                 capture_output=True)
    return Image.open(io.BytesIO(result.stdout)).convert("RGB")


def read_project(folder, *, require_shots=True):
    root = Path(folder).resolve()
    p = json.loads((root / "project.json").read_text(encoding="utf-8-sig"))
    if type(p.get("fps")) is not int or not 1 <= p["fps"] <= 120:
        raise ValueError("Use a constant integer fps in the portable editor.")
    size = p.get("size", [])
    if len(size) != 2 or any(type(n) is not int or n <= 0 or n % 2 for n in size):
        raise ValueError("Size must contain two positive even pixel dimensions.")
    if require_shots and (not p.get("shots") or any(type(s.get("frames")) is not int or s["frames"] < 1 for s in p["shots"])):
        raise ValueError("Give each shot its source clip and positive frame count.")
    return root, p


def region(image, roi):
    if len(roi) != 4 or not (0 <= roi[0] < roi[2] <= 1 and 0 <= roi[1] < roi[3] <= 1):
        raise ValueError(f"Invalid normalised region {roi}")
    h, w = image.shape[:2]
    x1, y1, x2, y2 = (round(n * side) for n, side in zip(roi, (w, h, w, h)))
    if x1 == x2 or y1 == y2:
        raise ValueError("Region contains no pixels.")
    return np.s_[y1:y2, x1:x2]
