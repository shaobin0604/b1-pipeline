from pathlib import Path
import os
import time

import pandas as pd

from src.common.config_loader import load_config
from src.common.io_utils import write_csv
from src.common.logger import get_logger
from src.common.paths import RAW_DAILY_DIR, RAW_DIR
from src.data_fetch.fetch_daily import fetch_daily_for_code
from src.data_fetch.fetch_market_cap import fetch_market_cap
from src.data_fetch.fetch_stock_basic import fetch_stock_basic
from src.data_fetch.tushare_client import build_client

logger = get_logger(__name__)


def _to_tushare_date(date_str: str | None) -> str | None:
    if not date_str:
        return None
    return str(date_str).replace("-", "")


def _normalize_codes(codes: list[str] | None) -> list[str] | None:
    if not codes:
        return None
    cleaned = []
    for code in codes:
        code = str(code).strip()
        if code:
            cleaned.append(code.upper())
    return cleaned or None


def _read_existing_last_trade_date(path: Path) -> str | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path, usecols=["trade_date"])
        if df.empty or "trade_date" not in df.columns:
            return None
        last_value = str(df.iloc[0]["trade_date"]).strip().replace("-", "")
        return last_value or None
    except Exception:
        return None


def _merge_incremental_daily(out_file: Path, new_daily: pd.DataFrame):
    if new_daily is None or new_daily.empty:
        return False

    new_daily = new_daily.copy()
    if "trade_date" in new_daily.columns:
        new_daily["trade_date"] = new_daily["trade_date"].astype(str).str.replace("-", "", regex=False)

    if not out_file.exists() or out_file.stat().st_size == 0:
        write_csv(out_file, new_daily)
        return True

    try:
        existing = pd.read_csv(out_file)
    except Exception:
        write_csv(out_file, new_daily)
        return True

    if existing.empty:
        write_csv(out_file, new_daily)
        return True

    if "trade_date" in existing.columns:
        existing["trade_date"] = existing["trade_date"].astype(str).str.replace("-", "", regex=False)

    merged = pd.concat([new_daily, existing], ignore_index=True)
    if "trade_date" in merged.columns:
        merged = merged.drop_duplicates(subset=["trade_date"], keep="first")
        merged = merged.sort_values("trade_date", ascending=False).reset_index(drop=True)
    else:
        merged = merged.drop_duplicates().reset_index(drop=True)

    write_csv(out_file, merged)
    return True


def _resolve_tushare_token(cfg: dict) -> str:
    env_token = os.getenv("TUSHARE_TOKEN", "").strip()
    cfg_token = str(cfg.get("tushare", {}).get("token") or "").strip()

    if env_token:
        return env_token
    if cfg_token and cfg_token not in {"YOUR_TUSHARE_TOKEN", "${TUSHARE_TOKEN}"}:
        return cfg_token

    raise ValueError(
        "未找到有效的 Tushare token。请优先设置环境变量 TUSHARE_TOKEN，"
        "或在 config/fetch.yaml 中填写 token。"
    )


def run_fetch_pipeline(
    config_name: str = "fetch.yaml",
    start_date_override: str | None = None,
    end_date_override: str | None = None,
    code_limit: int | None = None,
    codes: list[str] | None = None,
    mode: str = "incremental",
):
    cfg = load_config(config_name)
    token = _resolve_tushare_token(cfg)

    market_cfg = cfg.get("market", {})
    output_cfg = cfg.get("output", {})
    opt_cfg = cfg.get("fetch_options", {})

    start_date = _to_tushare_date(start_date_override or market_cfg.get("start_date"))
    end_date = _to_tushare_date(end_date_override or market_cfg.get("end_date"))
    target_end_date = end_date or time.strftime("%Y%m%d")
    sleep_seconds = float(opt_cfg.get("sleep_seconds", 0.3))
    codes = _normalize_codes(codes)
    mode = str(mode or "incremental").strip().lower()
    if mode not in {"incremental", "full"}:
        raise ValueError("mode 仅支持 incremental 或 full")

    pro = build_client(token)

    logger.info("开始拉取股票基础信息")
    stock_basic = fetch_stock_basic(pro)
    if codes:
        stock_basic = stock_basic[stock_basic["ts_code"].astype(str).isin(codes)].copy()
    if code_limit:
        stock_basic = stock_basic.head(code_limit)
    stock_basic_file = Path(output_cfg.get("stock_basic_file", RAW_DIR / "stock_basic.csv"))
    write_csv(stock_basic_file, stock_basic)
    logger.info("已写入股票基础信息: %s (count=%s)", stock_basic_file, len(stock_basic))

    market_cap_file = Path(output_cfg.get("market_cap_file", RAW_DIR / "market_cap.csv"))
    should_refresh_market_cap = (not codes) and (code_limit is None or code_limit >= len(stock_basic))
    if should_refresh_market_cap:
        logger.info("开始拉取市值快照")
        market_cap = fetch_market_cap(pro, target_end_date)
        write_csv(market_cap_file, market_cap)
        logger.info("已写入市值快照: %s (count=%s)", market_cap_file, len(market_cap))
    else:
        logger.info("本次为子集抓取，跳过重写市值快照以避免覆盖全市场 market_cap.csv")

    daily_dir = Path(output_cfg.get("daily_dir", RAW_DAILY_DIR))
    daily_dir.mkdir(parents=True, exist_ok=True)

    total = len(stock_basic)
    success = 0
    skipped = 0
    missing = 0
    failed = 0

    logger.info("开始拉取日线数据，mode=%s, target_end_date=%s", mode, target_end_date)

    for idx, row in stock_basic.iterrows():
        code = row["ts_code"]
        out_file = daily_dir / f"{code}.csv"
        try:
            fetch_start_date = start_date
            if mode == "incremental":
                last_trade_date = _read_existing_last_trade_date(out_file)
                if last_trade_date and last_trade_date >= target_end_date:
                    skipped += 1
                    if (idx + 1) % 200 == 0:
                        logger.info(
                            "进度 %s/%s | success=%s skipped=%s missing=%s failed=%s",
                            idx + 1, total, success, skipped, missing, failed,
                        )
                    continue
                fetch_start_date = last_trade_date or start_date

            daily = fetch_daily_for_code(pro, code, start_date=fetch_start_date, end_date=target_end_date)
            if daily is None or daily.empty:
                missing += 1
                logger.warning("[%s/%s] %s 无日线数据", idx + 1, total, code)
                continue

            if mode == "incremental":
                _merge_incremental_daily(out_file, daily)
            else:
                write_csv(out_file, daily)

            success += 1
            if success % 50 == 0 or (idx + 1) % 200 == 0:
                logger.info(
                    "进度 %s/%s | success=%s skipped=%s missing=%s failed=%s",
                    idx + 1, total, success, skipped, missing, failed,
                )
            time.sleep(sleep_seconds)
        except Exception as e:
            failed += 1
            logger.warning("[%s/%s] 拉取 %s 失败: %s", idx + 1, total, code, e)

    logger.info(
        "数据拉取完成 | success=%s skipped=%s missing=%s failed=%s total=%s",
        success, skipped, missing, failed, total,
    )
