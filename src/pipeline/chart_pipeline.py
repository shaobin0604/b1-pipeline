from pathlib import Path

from src.common.config_loader import load_config
from src.common.io_utils import read_csv, read_json
from src.common.logger import get_logger
from src.common.paths import CHARTS_DIR, CANDIDATES_DIR, PROCESSED_DIR
from src.charts.plot_daily_chart import plot_daily_chart

logger = get_logger(__name__)


def run_chart_pipeline(pick_date: str, config_name: str = "chart.yaml"):
    logger.info("运行图表导出流程: %s", pick_date)
    cfg = load_config(config_name)
    lookback_days = int(cfg.get("chart", {}).get("lookback_days", 60))

    candidate_file = CANDIDATES_DIR / f"b1_candidates_{pick_date}.json"
    if not candidate_file.exists():
        raise FileNotFoundError(f"未找到候选文件: {candidate_file}")

    data = read_json(candidate_file)
    candidates = data.get("candidates", [])
    out_dir = CHARTS_DIR / pick_date
    out_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for item in candidates:
        code = item["code"]
        processed_file = PROCESSED_DIR / f"{code}.csv"
        if not processed_file.exists():
            logger.warning("缺少 processed 文件: %s", processed_file)
            continue

        df = read_csv(processed_file)
        if df.empty or "trade_date" not in df.columns:
            continue

        df["trade_date"] = df["trade_date"].astype(str)
        df = df[df["trade_date"] <= pick_date].copy()
        if df.empty:
            continue
        df = df.tail(lookback_days)

        out_file = out_dir / f"{code}_day.png"
        plot_daily_chart(df, code=code, name=item.get("name", code), out_path=str(out_file))
        success += 1

    logger.info("图表导出完成，成功生成: %s 张", success)
