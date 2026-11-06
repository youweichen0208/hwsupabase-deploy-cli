#!/usr/bin/env python3
"""Install the whole skill set, including its shared Python helper, to an explicit directory."""
import argparse
from pathlib import Path
import shutil
import tempfile

NAMES = ("hw-supabase-deliver", "hw-supabase-setup", "hw-supabase-deploy-web", "hw-supabase-deploy-python")


def install(destination):
    root = Path(__file__).resolve().parents[1]
    destination = Path(destination).expanduser().resolve()
    for name in NAMES:
        if (destination / name).exists():
            raise ValueError("Existing skill would be overwritten: " + name + "; remove or back it up explicitly first")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination, prefix=".hw-skills-") as temp:
        staged = Path(temp)
        for name in NAMES:
            shutil.copytree(root / "skills" / name, staged / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(root / "src" / "hwsupabase", staged / NAMES[0] / "scripts" / "hwsupabase",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(root / "examples", staged / NAMES[0] / "assets" / "examples",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".env", ".venv"))
        for name in NAMES:
            (staged / name).rename(destination / name)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    try:
        print("Installed four skills in", install(args.destination))
    except ValueError as error:
        parser.exit(2, str(error) + "\n")
