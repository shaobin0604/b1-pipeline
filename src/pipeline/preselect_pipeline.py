from src.common.config_loader import load_config
from src.common.io_utils import read_csv, write_json
from src.common.logger import get_logger
from src.common.paths import CANDIDATES_DIR, PROCESSED_DIR
from src.selectors.b1_filter import filter_b1_candidates
from src.selectors.candidate_builder import build_candidate_item

logger = get_logger(__name__)


def run_preselect_pipeline(pick_date: str, config_name: str = "b1_rules.yaml", max_candidates: int | None = None):
    logger.info("运行 B1 海选流程: %s", pick_date)
    rules = load_config(config_name)

    candidate_items = []
    files = list(PROCESSED_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"未找到 processed 文件: {PROCESSED_DIR}")

    for idx, file in enumerate(files, start=1):
        try:
            df = read_csv(file)
            if df.empty or "trade_date" not in df.columns:
                continue

            df_day = df[df["trade_date"].astype(str) == pick_date].copy()
            if df_day.empty:
                continue

            filtered = filter_b1_candidates(df_day, rules)
            if filtered.empty:
                continue

            row = filtered.iloc[0].to_dict()
            if not row.get("code"):
                row["code"] = file.stem
            item = build_candidate_item(row, pick_date)
            candidate_items.append(item)
        except Exception as e:
            logger.warning("[%s/%s] 海选 %s 失败: %s", idx, len(files), file.name, e)

    candidate_items.sort(key=lambda x: x.get("j_value", 999))
    if max_candidates:
        candidate_items = candidate_items[:max_candidates]

    result = {
        "pick_date": pick_date,
        "strategy": "B1",
        "total_candidates": len(candidate_items),
        "generated_at": pick_date,
        "candidates": candidate_items,
    }

    out_file = CANDIDATES_DIR / f"b1_candidates_{pick_date}.json"
    write_json(out_file, result)
    logger.info("海选完成，候选数: %s，输出: %s", len(candidate_items), out_file)
