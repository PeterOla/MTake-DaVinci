"""MTake DaVinci command line. Run from any working directory."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    cmd = parser.add_subparsers(dest="command", required=True)
    cmd.add_parser("doctor", help="Check the render and review toolchain.")
    for name in ("new", "demo", "art"):
        cmd.add_parser(name).add_argument("folder", type=Path)
    lock = cmd.add_parser("lock-art", help="Save the evidence you inspected at the camera-to-art handoff.")
    lock.add_argument("folder", type=Path)
    lock.add_argument("--reviewer", required=True)
    cut = cmd.add_parser("assemble")
    cut.add_argument("folder", type=Path)
    cut.add_argument("movie", type=Path)
    review = cmd.add_parser("review")
    review.add_argument("folder", type=Path)
    review.add_argument("movie", type=Path)
    review.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.command == "new":
        args.folder.mkdir(parents=True, exist_ok=False)
        for src in (SKILL / "templates").iterdir():
            shutil.copy2(src, args.folder / src.name)
        for child in ("art", "audio", "shots", "review"):
            (args.folder / child).mkdir()
        print(args.folder.resolve())
        return 0
    if args.command == "doctor":
        import importlib.metadata as md
        print(f"Python {sys.version.split()[0]} (3.11+ required)")
        ok = sys.version_info >= (3, 11)
        for pkg in ("numpy", "Pillow"):
            try:
                print(pkg, md.version(pkg))
            except md.PackageNotFoundError:
                print(f"Missing {pkg}; install requirements.txt."); ok = False
        for binary in ("ffmpeg", "ffprobe"):
            path = shutil.which(binary)
            print(binary, path or "MISSING")
            ok = ok and bool(path)
        if shutil.which("ffmpeg"):
            enc = subprocess.check_output(["ffmpeg", "-hide_banner", "-encoders"], text=True, errors="replace")
            for codec in ("libx264", "aac", "mov_text"):
                has = any(line.split()[1:2] == [codec] for line in enc.splitlines())
                print(codec, "available" if has else "MISSING")
                ok = ok and has
        return 0 if ok else 1
    from media import read_project
    if args.command == "demo":
        from demo import build
        build(args.folder)
    elif args.command == "assemble":
        from cut import assemble
        print(assemble(args.folder, args.movie))
    elif args.command in ("art", "lock-art"):
        from audit import art
        from artwork import inventory, lock
        root, p = read_project(args.folder, require_shots=False)
        issues, findings = art(root,p)
        issues += inventory(root,p,findings)[0]
        if args.command == "lock-art" and not issues:
            print(lock(root,p,findings,args.reviewer))
            return 0
        print(json.dumps({"issues": issues, "subjects": findings}, indent=2))
        return int(bool(issues))
    else:
        from audit import review
        report = review(args.folder, args.movie)
        if args.report:
            args.report.parent.mkdir(exist_ok=True, parents=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
        print(json.dumps(report, indent=2))
        return int(not report["passed"])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError, ImportError) as exc:
        sys.exit(f"MTake: {exc}")
