import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io_utils import read_json
from src.common.paths import ensure_dirs
from src.pipeline.preprocess_pipeline import run_preprocess_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="b1_rules.yaml")
    parser.add_argument("--code", default=None, help="仅处理单只股票，例如 000001.SZ")
    parser.add_argument("--stage", choices=["light", "full"], default="full")
    parser.add_argument("--date", default=None, help="light 阶段用于生成当日初筛名单")
    parser.add_argument("--codes-from", default=None, help="从 json 文件读取 codes，供 full 阶段使用")
    args = parser.parse_args()

    ensure_dirs()

    codes = None
    if args.codes_from:
        data = read_json(args.codes_from)
        items = data.get("codes", [])
        codes = [item["code"] if isinstance(item, dict) else item for item in items]

    run_preprocess_pipeline(
        config_name=args.config,
        code=args.code,
        codes=codes,
        stage=args.stage,
        pick_date=args.date,
    )
