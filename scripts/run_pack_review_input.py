import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.paths import ensure_dirs
from src.pipeline.review_pipeline import _build_review_inputs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    ensure_dirs()
    _build_review_inputs(args.date)
