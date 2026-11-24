"""Check the source board and decoded delivery; never treat a meter as a viewing."""
import math
from fractions import Fraction

import numpy as np
from PIL import Image

from artwork import picture_proof, verify_lock
from media import RATE, STEMS, db, fingerprint, movie_frame, probe, read_audio, read_project, region, rms


def art(root, p):
    problems, findings = [], []
    if not p.get("subjects"):
        return ["Declare recognisable subjects or a sourced graphic treatment."], []
    for subject in p["subjects"]:
        name = subject["id"]
        files = {key: root / subject[key] for key in ("reference",)}
        if subject.get("kind") == "graphic":
            files.update({k: root / subject[k] for k in ("source", "on")})
        elif subject.get("kind") == "model":
            files.update({k: root / subject[k] for k in ("model", "neutral", "on", "off")})
        else:
            problems.append(f"{name}: choose model or graphic.")
            continue
        for i, dependency in enumerate(subject.get("dependencies", [])):
            files[f"dependency_{i}"] = root / dependency
        missing = [k for k, f in files.items() if not f.is_file() or not f.stat().st_size]
        if missing or not subject.get("rights") or not subject.get("read"):
            problems.append(f"{name}: missing art/rights/visible features {missing}")
            continue
        row = {"subject": name, "registration": subject, "sha256": {k: fingerprint(f) for k, f in files.items()}}
        if subject["kind"] == "model":
            if row["sha256"]["neutral"] == row["sha256"]["on"]:
                problems.append(f"{name}: neutral and linework are the same image.")
            with Image.open(files["on"]) as on, Image.open(files["off"]) as off:
                if on.size != off.size:
                    problems.append(f"{name}: on/off camera output sizes differ.")
                    continue
                pixels = np.asarray(on.convert("RGB"), dtype=np.int16)
                diff = np.max(np.abs(pixels - np.asarray(off.convert("RGB"), dtype=np.int16)), axis=2) >= 10
            box = region(diff, subject["roi"])
            inside = int(diff[box].sum())
            row["changed_inside_fraction"] = round(float(np.mean(diff[box])), 5)
            row["fraction_of_all_change_inside"] = round(inside / max(1, int(diff.sum())), 5)
            if row["changed_inside_fraction"] < subject["min_changed"] or row["fraction_of_all_change_inside"] < 0.90:
                problems.append(f"{name}: model switch-off did not isolate visible geometry in its planned region.")
        findings.append(row)
    return problems, findings


def review(folder, movie):
    root, p = read_project(folder)
    fps = p["fps"]
    frames = sum(shot["frames"] for shot in p["shots"])
    count = round(frames * RATE / fps)
    problems, artwork = art(root, p)
    problems += verify_lock(root,p,artwork)
    info = probe(movie)["streams"]
    video = next(s for s in info if s["codec_type"] == "video")
    aud = next((s for s in info if s["codec_type"] == "audio"), {})
    if (int(video.get("nb_frames", 0)) != frames or Fraction(video["avg_frame_rate"]) != fps
            or [video["width"], video["height"]] != p["size"]):
        problems.append("Encoded picture length, size or rate differs from the plan.")
    if aud.get("channels") != 2 or int(aud.get("sample_rate", 0)) != RATE:
        problems.append("The delivered sound must be 48 kHz stereo.")
    if p.get("captions") and not any(s["codec_type"] == "subtitle" for s in info):
        problems.append("The planned selectable captions are missing.")
    if not aud:
        return {"passed": False, "issues": problems, "art": artwork, "sha256": fingerprint(movie)}
    mix = read_audio(movie)
    data = {k: read_audio(root / p["stems"][k]) for k in STEMS}
    if len(mix) < count - 1 or abs(len(mix) - count) > 2048:
        problems.append("Decoded audio duration differs from the picture (allowing AAC padding).")
    if any(abs(len(v) - count) > 1 for v in data.values()):
        problems.append("A stem has the wrong duration.")
    usable = min(count, len(mix), *(len(v) for v in data.values()))
    target = sum(v[:usable] for v in data.values())
    error = mix[:usable] - target
    windows = []
    for start in range(0, usable, RATE * 10):
        end = min(start + RATE * 10, usable)
        lo, hi = start * fps / RATE, end * fps / RATE
        ss = slice(start, end)
        # Reject broad mix changes, allowing the distortion of a lossy delivery codec.
        signal = rms(target[ss])
        residual = rms(error[ss])
        snr = round(20 * math.log10(max(signal, 1e-10) / max(residual, 1e-10)), 1) if signal else None
        if residual > max(0.0017, signal * 0.19):
            problems.append(f"At {start / RATE:g}s the decoded mix differs from the printed stems.")
        cues = p.get("cues", [])
        windows.append({"from_s": start / RATE, "to_s": end / RATE,
                        "effect_starts": sum(lo <= c["frame"] < hi for c in cues),
                        "continuing_effects": [c["name"] for c in cues if c["frame"] < lo < c["end"]],
                        "effects_rms_dbfs": db(data["effects"][ss]), "mix_rms_dbfs": db(mix[ss]),
                        "mono_rms_dbfs": db(mix[ss].mean(axis=1)), "mix_vs_stems_snr_db": snr})
    checked_frames = []
    if not problems:
        picture_issues, checked_frames = picture_proof(root,p,movie)
        problems.extend(picture_issues)
    accents = []
    for accent in p.get("accents", []):
        frame = accent["frame"]
        if not 1 <= frame < frames:
            problems.append(f"{accent['name']}: accent is outside the reviewable frames.")
            continue
        def samples(f):
            return slice(round(f * RATE / fps), round((f + 1) * RATE / fps))
        entry = {"name": accent["name"], "frame": frame}
        for stem in ("music", "effects"):
            value = rms(data[stem][samples(frame)])
            before = rms(data[stem][samples(frame - 1)])
            ratio = value / max(before, 1e-8)
            entry[stem + "_on_dbfs"] = db(data[stem][samples(frame)])
            if value < 10 ** (accent["floor_dbfs"][stem] / 20) or ratio < accent["rise_ratio"][stem]:
                problems.append(f"{accent['name']}: {stem} onset misses the chosen frame.")
        start, stop = accent["speech_free"]
        if not 0 <= start <= frame < stop <= frames:
            problems.append(f"{accent['name']}: invalid protected speech window.")
        else:
            guard = data["voice"][round(start * RATE / fps):round(stop * RATE / fps)]
            if np.max(np.abs(guard), initial=0.) > 10 ** (accent.get("voice_ceiling_dbfs", -45) / 20):
                problems.append(f"{accent['name']}: voice in the protected drop window.")
        if "roi" in accent:
            a, b = (np.asarray(movie_frame(movie, f, fps), dtype=np.int16) for f in (frame - 1, frame))
            diff = np.max(np.abs(a - b), axis=2)
            box = region(diff, accent["roi"])
            fraction = float(np.mean(diff[box] >= accent.get("pixel_step", 12)))
            entry["picture_change_fraction"] = round(fraction, 5)
            if fraction < accent["min_picture_change"]:
                problems.append(f"{accent['name']}: expected visual change is absent.")
        accents.append(entry)
    return {"passed": not problems, "issues": problems, "sha256": fingerprint(movie),
            "art": artwork, "delivered_art_frames":checked_frames, "accents": accents, "ten_second_windows": windows,
            "manual_reviews": ["physical likeness and contact", "first-watch story", "stereo and real phone audition"]}
