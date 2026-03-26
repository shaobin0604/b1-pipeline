import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io_utils import read_csv, write_json
from src.common.paths import CHARTS_DIR, PROCESSED_DIR
from src.review.review_pack_builder import build_review_input
from src.review.scoring_engine import score_b1_candidate
from src.review.review_formatter import build_review_result


def main():
    parser = argparse.ArgumentParser(description="对单个案例做回归验证：看某只股票在某天的评分结果")
    parser.add_argument("--code", required=True, help="股票代码，例如 000516.SZ")
    parser.add_argument("--date", required=True, help="日期，例如 2025-05-12")
    parser.add_argument("--with-chart", action="store_true", help="如果对应日期已有图，则把图路径带进结果")
    args = parser.parse_args()

    code = args.code.strip().upper()
    pick_date = args.date.strip()
    processed_file = PROCESSED_DIR / f"{code}.csv"
    if not processed_file.exists():
        raise FileNotFoundError(f"未找到 processed 文件: {processed_file}")

    df = read_csv(processed_file)
    row_df = df[df["trade_date"].astype(str) == pick_date]
    if row_df.empty:
        raise ValueError(f"{code} 在 {pick_date} 没有找到对应交易日数据")
    row = row_df.iloc[0].to_dict()
    row["pick_date"] = pick_date

    chart_path = None
    if args.with_chart:
        chart_file = CHARTS_DIR / pick_date / f"{code}_day.png"
        if chart_file.exists():
            chart_path = str(chart_file)

    review_input = build_review_input(
        row=row,
        chart_path=chart_path or "",
        processed_file=str(processed_file),
    )
    score_result = score_b1_candidate(review_input)
    result = build_review_result(review_input, score_result)

    out_file = ROOT / "data" / "review_output" / pick_date / f"case_review_{code}.json"
    write_json(out_file, result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n已输出: {out_file}")


if __name__ == "__main__":
    main()
