import pandas as pd


def fetch_market_cap(pro, trade_date: str):
    """Fetch daily market cap snapshot for a trade date.

    trade_date should be in YYYYMMDD format.
    Returns columns: ts_code, total_mv, trade_date
    """
    try:
        df = pro.daily_basic(trade_date=trade_date, fields="ts_code,trade_date,total_mv")
        if df is None:
            return pd.DataFrame(columns=["ts_code", "total_mv", "trade_date"])
        return df
    except Exception:
        return pd.DataFrame(columns=["ts_code", "total_mv", "trade_date"])
