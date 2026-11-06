# /// script
# requires-python = ">=3.9"
# dependencies = ["PyYAML==6.0.3", "esdk-obs-python==3.26.6"]
# ///
"""Run with uv; supports both source checkout and standalone installed skill set."""
from pathlib import Path
import sys

here = Path(__file__).resolve().parent
source = here.parents[2] / "src"
sys.path.insert(0, str(source if source.is_dir() else here))
from hwsupabase.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
