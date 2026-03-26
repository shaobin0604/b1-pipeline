import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.paths import ensure_dirs
from src.pipeline.full_pipeline import run_full_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    run_full_pipeline(args.date, skip_fetch=args.skip_fetch)
