import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io_utils import read_csv, read_json, write_json
from src.common.paths import CANDIDATES_DIR, PROCESSED_DIR, REVIEW_OUTPUT_DIR
from src.review.review_pack_builder import build_review_input
from src.review.review_formatter import build_review_result
from src.review.scoring_engine import score_b1_candidate
from src.indicators.building_wave import add_building_wave_features


def _load_candidates(pick_date: str) -> list[dict]:
    candidate_file = CANDIDATES_DIR / f"b1_candidates_{pick_date}.json"
    if not candidate_file.exists():
        raise FileNotFoundError(f"未找到候选文件: {candidate_file}")
    data = read_json(candidate_file)
    if isinstance(data, list):
        return data
    return data.get("candidates", data.get("items", []))


def _normalize_targets(text: str | None) -> set[str]:
    if not text:
        return set()
    return {x.strip().upper() for x in text.split(",") if x.strip()}


def _select_candidates(candidates: list[dict], top_n: int, targets: set[str]) -> list[dict]:
    selected = []
    seen = set()
    for item in candidates[:top_n]:
        code = str(item.get("code", "")).upper()
        if code and code not in seen:
            selected.append(item)
            seen.add(code)
    for item in candidates:
        code = str(item.get("code", "")).upper()
        if code in targets and code not in seen:
            selected.append(item)
            seen.add(code)
    return selected


def _enriched_row_for_date(code: str, pick_date: str) -> dict | None:
    processed_file = PROCESSED_DIR / f"{code}.csv"
    if not processed_file.exists():
        return None
    df = read_csv(processed_file)
    enriched = add_building_wave_features(df)
    row_df = enriched[enriched["trade_date"].astype(str) == pick_date]
    if row_df.empty:
        return None
    row = row_df.iloc[0].to_dict()
    row["pick_date"] = pick_date
    return row


def evaluate_candidate(item: dict, pick_date: str) -> dict | None:
    code = str(item.get("code", "")).upper()
    row = _enriched_row_for_date(code, pick_date)
    if row is None:
        return None
    review_input = build_review_input(
        row=row,
        chart_path="",
        processed_file=str(PROCESSED_DIR / f"{code}.csv"),
    )
    score_result = score_b1_candidate(review_input)
    review_result = build_review_result(review_input, score_result)
    review_result["quick_flags"] = {
        "recent_distribution_within_1m": review_input.get("building_wave", {}).get("recent_distribution_within_1m"),
        "recent_distribution_count_1m": review_input.get("building_wave", {}).get("recent_distribution_count_1m"),
        "overhead_supply_near_prev_high": review_input.get("building_wave", {}).get("overhead_supply_near_prev_high"),
        "failed_breakout_overhead_supply": review_input.get("building_wave", {}).get("failed_breakout_overhead_supply"),
        "overhead_heavy_volume_band": review_input.get("building_wave", {}).get("overhead_heavy_volume_band"),
        "peak_huge_volume_break_yellow_2d": review_input.get("building_wave", {}).get("peak_huge_volume_break_yellow_2d"),
        "top_3day_stair_volume_distribution": review_input.get("building_wave", {}).get("top_3day_stair_volume_distribution"),
    }
    return review_result


def main():
    parser = argparse.ArgumentParser(description="轻量批量验证：重算指定日期候选池前N只 + 指定重点票，快速查看新规则效果")
    parser.add_argument("--date", required=True, help="日期，例如 2026-03-20")
    parser.add_argument("--top", type=int, default=60, help="候选池前N只，默认 60")
    parser.add_argument("--targets", default="", help="额外重点股票代码，逗号分隔，例如 002001.SZ,002216.SZ")
    parser.add_argument("--out-name", default="quick_validate", help="输出文件名前缀")
    args = parser.parse_args()

    pick_date = args.date.strip()
    top_n = max(1, int(args.top))
    targets = _normalize_targets(args.targets)

    candidates = _load_candidates(pick_date)
    selected = _select_candidates(candidates, top_n=top_n, targets=targets)

    results = []
    missing = []
    for item in selected:
        code = str(item.get("code", "")).upper()
        try:
            result = evaluate_candidate(item, pick_date)
            if result is None:
                missing.append(code)
            else:
                results.append(result)
        except Exception as e:
            missing.append(f"{code}: {e}")

    results.sort(key=lambda x: x.get("total_score", 0), reverse=True)

    recommendations = [x for x in results if x.get("grade") in ["A", "B"]]
    watchlist = [x for x in results if x.get("grade") == "C"]
    excluded = [x for x in results if x.get("grade") in ["D", "E"]]
    dist_filtered = [x for x in results if x.get("quick_flags", {}).get("recent_distribution_within_1m")]
    overhead_hits = [
        x for x in results
        if any(bool(x.get("quick_flags", {}).get(k)) for k in [
            "overhead_supply_near_prev_high",
            "failed_breakout_overhead_supply",
            "overhead_heavy_volume_band",
        ])
    ]

    payload = {
        "pick_date": pick_date,
        "selected_total": len(selected),
        "reviewed_total": len(results),
        "missing_or_error": missing,
        "recommended_total": len(recommendations),
        "watchlist_total": len(watchlist),
        "excluded_total": len(excluded),
        "distribution_filtered_total": len(dist_filtered),
        "overhead_hit_total": len(overhead_hits),
        "top_results": results[:20],
        "target_results": [x for x in results if x.get("code") in targets],
    }

    out_dir = REVIEW_OUTPUT_DIR / pick_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.out_name}_{pick_date}.json"
    write_json(out_file, payload)

    print(json.dumps({
        "pick_date": pick_date,
        "selected_total": len(selected),
        "reviewed_total": len(results),
        "distribution_filtered_total": len(dist_filtered),
        "overhead_hit_total": len(overhead_hits),
        "top10": [
            {
                "code": x.get("code"),
                "name": x.get("name"),
                "score": x.get("total_score"),
                "grade": x.get("grade"),
                "dist": x.get("quick_flags", {}).get("recent_distribution_within_1m"),
                "overhead": any(bool(x.get("quick_flags", {}).get(k)) for k in [
                    "overhead_supply_near_prev_high",
                    "failed_breakout_overhead_supply",
                    "overhead_heavy_volume_band",
                ]),
            }
            for x in results[:10]
        ],
        "target_results": [
            {
                "code": x.get("code"),
                "name": x.get("name"),
                "score": x.get("total_score"),
                "grade": x.get("grade"),
                "decision": x.get("decision"),
                "quick_flags": x.get("quick_flags"),
                "risks": x.get("risks", [])[:5],
            }
            for x in results if x.get("code") in targets
        ],
        "missing_or_error_count": len(missing),
        "out_file": str(out_file),
    }, ensure_ascii=False, indent=2))
    print(f"\n已输出: {out_file}")


if __name__ == "__main__":
    main()
