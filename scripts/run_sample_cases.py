import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io_utils import read_csv, write_json
from src.common.paths import PROCESSED_DIR
from src.review.review_pack_builder import build_review_input
from src.review.scoring_engine import score_b1_candidate
from src.review.review_formatter import build_review_result
from src.selectors.b1_filter import is_b1_candidate
from src.common.config_loader import load_config

DEFAULT_CASES = [
    {"code": "688799.SH", "date": "2025-05-12", "label": "华纳药厂 perfect_b1_1"},
    {"code": "600366.SH", "date": "2025-08-04", "label": "宁波韵升 perfect_b1_2"},
    {"code": "688321.SH", "date": "2025-06-20", "label": "微芯生物 perfect_b1_3"},
    {"code": "301338.SZ", "date": "2026-01-14", "label": "凯格精机 perfect_b1_4a"},
    {"code": "301338.SZ", "date": "2026-02-13", "label": "凯格精机 perfect_b1_4b"},
    {"code": "600601.SH", "date": "2025-07-23", "label": "方正科技 perfect_b1_5"},
    {"code": "300689.SZ", "date": "2025-07-18", "label": "澄天伟业 perfect_b1_6"},
    {"code": "002074.SZ", "date": "2025-08-04", "label": "国轩高科 perfect_b1_7"},
]


def evaluate_case(case: dict, rules: dict) -> dict:
    code = case["code"].strip().upper()
    pick_date = case["date"].strip()
    processed_file = PROCESSED_DIR / f"{code}.csv"

    result = {
        "label": case.get("label"),
        "code": code,
        "date": pick_date,
        "processed_exists": processed_file.exists(),
    }
    if not processed_file.exists():
        result["status"] = "missing_processed"
        return result

    df = read_csv(processed_file)
    row_df = df[df["trade_date"].astype(str) == pick_date]
    if row_df.empty:
        result["status"] = "missing_trade_date"
        return result

    row = row_df.iloc[0].to_dict()
    row["pick_date"] = pick_date
    result["status"] = "ok"
    result["preselect_pass"] = bool(is_b1_candidate(row, rules))
    result["core_snapshot"] = {
        "j_value": row.get("j_value"),
        "white_above_yellow": row.get("white_above_yellow"),
        "close_above_yellow": row.get("close_above_yellow"),
        "close_between_white_yellow": row.get("close_between_white_yellow"),
        "distance_to_white_pct": row.get("distance_to_white_pct"),
        "distance_to_yellow_pct": row.get("distance_to_yellow_pct"),
        "is_10d_min_volume": row.get("is_10d_min_volume"),
        "volume_ratio_vs_prev_day": row.get("volume_ratio_vs_prev_day"),
        "volume_ratio_vs_prev_5d_avg": row.get("volume_ratio_vs_prev_5d_avg"),
        "pct_change": row.get("pct_change"),
        "amplitude_pct": row.get("amplitude_pct"),
    }

    review_input = build_review_input(row=row, chart_path="", processed_file=str(processed_file))
    score_result = score_b1_candidate(review_input)
    review_result = build_review_result(review_input, score_result)
    result["review_result"] = review_result
    return result


def main():
    parser = argparse.ArgumentParser(description="批量验证用户给出的完美案例在当前系统里的海选和评分结果")
    parser.add_argument("--cases-file", default=None, help="可选，自定义案例 JSON 文件路径")
    args = parser.parse_args()

    rules = load_config("b1_rules.yaml")
    cases = DEFAULT_CASES
    if args.cases_file:
        with open(args.cases_file, "r", encoding="utf-8") as f:
            cases = json.load(f)

    results = []
    for case in cases:
        try:
            results.append(evaluate_case(case, rules))
        except Exception as e:
            results.append({
                "label": case.get("label"),
                "code": case.get("code"),
                "date": case.get("date"),
                "status": "error",
                "error": str(e),
            })

    out_file = ROOT / "data" / "review_output" / "sample_case_regression.json"
    payload = {"results": results}
    write_json(out_file, payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    print(f"\n已输出: {out_file}")


if __name__ == "__main__":
    main()
