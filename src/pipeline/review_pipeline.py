from pathlib import Path

from src.common.io_utils import read_csv, read_json, write_json
from src.common.logger import get_logger
from src.common.paths import CANDIDATES_DIR, CHARTS_DIR, PROCESSED_DIR, REVIEW_INPUT_DIR, REVIEW_OUTPUT_DIR
from src.review.review_formatter import build_review_result
from src.review.review_pack_builder import build_review_input
from src.review.scoring_engine import score_b1_candidate

logger = get_logger(__name__)


def _build_review_inputs(pick_date: str):
    candidate_file = CANDIDATES_DIR / f"b1_candidates_{pick_date}.json"
    if not candidate_file.exists():
        raise FileNotFoundError(f"未找到候选文件: {candidate_file}")

    data = read_json(candidate_file)
    candidates = data.get("candidates", [])
    review_dir = REVIEW_INPUT_DIR / pick_date
    review_dir.mkdir(parents=True, exist_ok=True)

    items = []
    packed = 0
    for item in candidates:
        code = item["code"]
        processed_file = PROCESSED_DIR / f"{code}.csv"
        chart_file = CHARTS_DIR / pick_date / f"{code}_day.png"
        if not processed_file.exists():
            logger.warning("缺少 processed 文件: %s", processed_file)
            continue
        if not chart_file.exists():
            logger.warning("缺少图表文件: %s", chart_file)
            continue

        df = read_csv(processed_file)
        row_df = df[df["trade_date"].astype(str) == pick_date]
        if row_df.empty:
            continue
        row = row_df.iloc[0].to_dict()

        review_input = build_review_input(
            row=row,
            chart_path=str(chart_file.relative_to(Path.cwd().parent)) if False else str(chart_file),
            processed_file=str(processed_file),
        )
        out_file = review_dir / f"{code}.json"
        write_json(out_file, review_input)
        review_input["files"] = review_input.get("files", {})
        review_input["files"]["input_json"] = str(out_file)
        items.append(review_input)
        packed += 1

    manifest = {
        "pick_date": pick_date,
        "strategy": "B1",
        "total_candidates": packed,
        "items": items,
    }
    manifest_file = review_dir / f"b1_candidates_{pick_date}.json"
    write_json(manifest_file, manifest)
    logger.info("review_input 打包完成: %s 只", packed)
    return manifest


def run_review_pipeline(pick_date: str):
    logger.info("运行评分流程: %s", pick_date)
    manifest = _build_review_inputs(pick_date)
    items = manifest.get("items", [])

    recommendations = []
    watchlist = []
    excluded = []

    for item in items:
        score_result = score_b1_candidate(item)
        review_item = build_review_result(item, score_result)
        grade = review_item["grade"]
        if grade in ["A", "B"]:
            recommendations.append(review_item)
        elif grade == "C":
            watchlist.append(review_item)
        else:
            excluded.append(review_item)

    recommendations.sort(key=lambda x: x["total_score"], reverse=True)
    watchlist.sort(key=lambda x: x["total_score"], reverse=True)
    excluded.sort(key=lambda x: x["total_score"], reverse=True)

    out_dir = REVIEW_OUTPUT_DIR / pick_date
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "pick_date": pick_date,
        "strategy": "B1",
        "review_version": "B1 精选打分标准 v1",
        "reviewed_total": len(items),
        "recommended_total": len(recommendations),
        "watchlist_total": len(watchlist),
        "excluded_total": len(excluded),
        "score_thresholds": {
            "A": "90-100",
            "B": "80-89",
            "C": "70-79",
            "D": "60-69",
            "E": "<60",
        },
        "summary": {
            "top_pick_count": len(recommendations[:3]),
            "high_quality_count": len(recommendations),
            "main_risks": ["首版评分仍需用案例继续校准白黄线和关键K逻辑"],
        },
        "recommendations": recommendations,
        "watchlist": watchlist,
        "excluded": excluded,
    }

    out_file = out_dir / f"b1_review_{pick_date}.json"
    write_json(out_file, result)

    summary_file = out_dir / "summary.md"
    lines = [
        f"# B1 Review Summary - {pick_date}",
        "",
        f"- reviewed_total: {len(items)}",
        f"- recommended_total: {len(recommendations)}",
        f"- watchlist_total: {len(watchlist)}",
        f"- excluded_total: {len(excluded)}",
        "",
        "## Top Recommendations",
    ]
    if recommendations:
        for idx, item in enumerate(recommendations[:10], start=1):
            lines.append(f"{idx}. {item['code']} {item.get('name', '')} | score={item['total_score']} | grade={item['grade']} | {item['comment']}")
    else:
        lines.append("- 无推荐")

    summary_file.write_text("\n".join(lines), encoding="utf-8")
    logger.info("评分完成，输出: %s", out_file)
