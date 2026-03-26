from pathlib import Path

import pandas as pd

from src.common.config_loader import load_config
from src.common.io_utils import read_csv, write_csv, write_json
from src.common.logger import get_logger
from src.common.paths import PROCESSED_DIR, PROCESSED_LIGHT_DIR, RAW_DAILY_DIR, RAW_DIR, LIGHT_CANDIDATES_DIR
from src.preprocess.merge_features import build_processed_df, build_light_processed_df
from src.selectors.light_gate import filter_light_candidates

logger = get_logger(__name__)


def _load_stock_basic() -> pd.DataFrame:
    path = RAW_DIR / "stock_basic.csv"
    if not path.exists():
        raise FileNotFoundError(f"未找到股票基础信息文件: {path}")
    df = read_csv(path)
    df = df.rename(columns={"ts_code": "code"})
    df["is_st"] = df["name"].fillna("").astype(str).str.upper().str.contains("ST")
    return df[["code", "name", "industry", "is_st"]]


def _load_market_cap() -> pd.DataFrame:
    path = RAW_DIR / "market_cap.csv"
    if not path.exists():
        return pd.DataFrame(columns=["code", "market_cap"])
    df = read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=["code", "market_cap"])
    df = df.rename(columns={"ts_code": "code", "total_mv": "market_cap"})
    if "market_cap" in df.columns:
        df["market_cap"] = pd.to_numeric(df["market_cap"], errors="coerce") * 10000
    return df[["code", "market_cap"]]


def _build_meta_maps(stock_basic: pd.DataFrame, market_cap: pd.DataFrame):
    meta_map = {}
    for _, row in stock_basic.iterrows():
        meta_map[str(row["code"])] = {
            "name": row.get("name"),
            "industry": row.get("industry"),
            "is_st": bool(row.get("is_st", False)),
        }
    cap_map = {}
    for _, row in market_cap.iterrows():
        cap_map[str(row["code"])] = row.get("market_cap")
    return meta_map, cap_map


def _resolve_files(code: str | None = None, codes: list[str] | None = None):
    if code:
        return [Path(RAW_DAILY_DIR) / f"{code}.csv"]
    if codes:
        return [Path(RAW_DAILY_DIR) / f"{c}.csv" for c in codes]
    return list(Path(RAW_DAILY_DIR).glob("*.csv"))


def _prepare_df(file: Path, meta_map: dict, cap_map: dict) -> pd.DataFrame | None:
    if not file.exists():
        logger.warning("文件不存在: %s", file)
        return None
    df = read_csv(file)
    if df.empty:
        return None

    df.columns = [str(c).lower() for c in df.columns]
    df = df.rename(columns={"ts_code": "code", "vol": "volume", "trade_date": "trade_date"})
    if "trade_date" not in df.columns:
        logger.warning("%s 缺少 trade_date 列", file.name)
        return None

    df["trade_date"] = pd.to_datetime(df["trade_date"].astype(str))
    df = df.sort_values("trade_date").reset_index(drop=True)

    code_val = str(df.loc[0, "code"])
    meta = meta_map.get(code_val, {})
    df["name"] = meta.get("name")
    df["industry"] = meta.get("industry")
    df["is_st"] = bool(meta.get("is_st", False))
    df["market_cap"] = cap_map.get(code_val)
    return df


def run_preprocess_pipeline(
    config_name: str = "b1_rules.yaml",
    code: str | None = None,
    codes: list[str] | None = None,
    stage: str = "full",
    pick_date: str | None = None,
):
    rules = load_config(config_name)
    stock_basic = _load_stock_basic()
    market_cap = _load_market_cap()
    meta_map, cap_map = _build_meta_maps(stock_basic, market_cap)

    files = _resolve_files(code=code, codes=codes)
    if not files:
        raise FileNotFoundError(f"未找到原始日线文件: {RAW_DAILY_DIR}")

    total = len(files)
    success = 0
    light_pass_items = []

    out_dir = PROCESSED_LIGHT_DIR if stage == "light" else PROCESSED_DIR

    for idx, file in enumerate(files, start=1):
        try:
            df = _prepare_df(file, meta_map, cap_map)
            if df is None:
                continue

            if stage == "light":
                processed = build_light_processed_df(df, rules_config=rules)
            else:
                processed = build_processed_df(df, rules_config=rules)

            processed["trade_date"] = processed["trade_date"].dt.strftime("%Y-%m-%d")
            out_file = out_dir / file.name
            write_csv(out_file, processed)
            success += 1

            if stage == "light" and pick_date:
                df_day = processed[processed["trade_date"].astype(str) == pick_date].copy()
                if not df_day.empty:
                    filtered = filter_light_candidates(df_day, rules)
                    if not filtered.empty:
                        row = filtered.iloc[0].to_dict()
                        light_pass_items.append({
                            "code": row.get("code", file.stem),
                            "name": row.get("name"),
                            "j_value": row.get("j_value"),
                            "white_above_yellow": bool(row.get("white_above_yellow", False)),
                            "close_between_white_yellow": bool(row.get("close_between_white_yellow", False)),
                            "distance_to_white_pct": row.get("distance_to_white_pct"),
                            "distance_to_yellow_pct": row.get("distance_to_yellow_pct"),
                        })

            if success % 50 == 0:
                logger.info("已处理 %s 只股票", success)
        except Exception as e:
            logger.warning("[%s/%s] 处理 %s 失败: %s", idx, total, file.name, e)

    logger.info("%s 阶段预处理完成，成功生成文件: %s 只", stage, success)

    if stage == "light" and pick_date:
        light_pass_items.sort(key=lambda x: x.get("j_value", 999) if x.get("j_value") is not None else 999)
        out_file = LIGHT_CANDIDATES_DIR / f"light_candidates_{pick_date}.json"
        write_json(out_file, {
            "pick_date": pick_date,
            "stage": "light_j_gate",
            "total_scanned": success,
            "total_passed": len(light_pass_items),
            "codes": light_pass_items,
        })
        logger.info("light 初筛完成，入围数: %s，输出: %s", len(light_pass_items), out_file)
