import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.paths import ensure_dirs
from src.pipeline.preselect_pipeline import run_preselect_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--config", default="b1_rules.yaml")
    parser.add_argument("--max-candidates", type=int, default=None)
    args = parser.parse_args()

    ensure_dirs()
    run_preselect_pipeline(args.date, config_name=args.config, max_candidates=args.max_candidates)
