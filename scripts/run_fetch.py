import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.paths import ensure_dirs
from src.pipeline.fetch_pipeline import run_fetch_pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="fetch.yaml")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--limit", type=int, default=None, help="仅拉前 N 只股票，便于调试")
    parser.add_argument("--codes", nargs="*", default=None, help="指定股票代码列表，例如 000516.SZ 000019.SZ")
    parser.add_argument(
        "--mode",
        choices=["incremental", "full"],
        default="incremental",
        help="抓取模式：incremental=默认增量更新；full=全量重拉",
    )
    args = parser.parse_args()

    ensure_dirs()
    run_fetch_pipeline(
        config_name=args.config,
        start_date_override=args.start_date,
        end_date_override=args.end_date,
        code_limit=args.limit,
        codes=args.codes,
        mode=args.mode,
    )
