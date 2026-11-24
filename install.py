"""Install the complete portable skill into one agent discovery directory."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "mtake-davinci"


def install(parent):
    dest = parent.expanduser().resolve() / NAME
    if dest.exists() or dest.is_symlink():
        raise SystemExit(f"Already exists: {dest}. Choose another destination or back up the existing installation.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(dir=dest.parent) as tmp:
        stage = Path(tmp) / NAME
        shutil.copytree(ROOT / "skills" / NAME, stage,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "LICENSE", stage / "LICENSE")
        stage.rename(dest)
    print(dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--project", type=Path, help="Project where the agent should discover the skill")
    choice.add_argument("--dest", type=Path, help="Existing or new skills parent directory")
    args = parser.parse_args()
    parent = args.dest or ((args.project or Path.home()) / ".agents" / "skills")
    install(parent)
