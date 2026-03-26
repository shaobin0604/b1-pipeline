import pandas as pd


def add_key_k_features(
    df: pd.DataFrame,
    min_pct_change: float = 4.0,
    volume_ratio_threshold: float = 1.5,
    recent_lookback_days: int = 40,
):
    df = df.copy()

    close = pd.to_numeric(df["close"], errors="coerce")
    open_ = pd.to_numeric(df["open"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    volume = pd.to_numeric(df["volume"], errors="coerce")
    pct_change = pd.to_numeric(df.get("pct_change"), errors="coerce")
    if pct_change.isna().all():
        pct_change = (close / close.shift(1) - 1) * 100

    volume_ratio = volume / volume.shift(1)
    real_body_pct = ((close - open_).abs() / open_.replace(0, pd.NA)) * 100
    bullish = close > open_

    df["key_k_candidate"] = (
        bullish &
        (pct_change >= min_pct_change) &
        (volume_ratio >= volume_ratio_threshold)
    ).fillna(False)

    df["key_k_volume_ratio"] = volume_ratio
    df["key_k_real_body_pct"] = real_body_pct
    df["key_k_low"] = low.where(df["key_k_candidate"])
    df["key_k_close"] = close.where(df["key_k_candidate"])

    recent_key_k_low = []
    recent_key_k_age = []
    recent_key_k_exists = []
    recent_key_k_body = []
    recent_key_k_volume_ratio = []

    for i in range(len(df)):
        start = max(0, i - recent_lookback_days)
        hist = df.iloc[start:i+1]
        candidates = hist[hist["key_k_candidate"] == True]
        if candidates.empty:
            recent_key_k_exists.append(False)
            recent_key_k_low.append(pd.NA)
            recent_key_k_age.append(pd.NA)
            recent_key_k_body.append(pd.NA)
            recent_key_k_volume_ratio.append(pd.NA)
            continue

        last_idx = candidates.index[-1]
        last_row = df.loc[last_idx]
        recent_key_k_exists.append(True)
        recent_key_k_low.append(last_row.get("key_k_low"))
        recent_key_k_age.append(i - df.index.get_loc(last_idx))
        recent_key_k_body.append(last_row.get("key_k_real_body_pct"))
        recent_key_k_volume_ratio.append(last_row.get("key_k_volume_ratio"))

    df["recent_key_k_exists"] = recent_key_k_exists
    df["recent_key_k_low"] = recent_key_k_low
    df["recent_key_k_age"] = recent_key_k_age
    df["recent_key_k_real_body_pct"] = recent_key_k_body
    df["recent_key_k_volume_ratio"] = recent_key_k_volume_ratio

    base = pd.to_numeric(df["recent_key_k_low"], errors="coerce").abs().replace(0, pd.NA)
    df["distance_to_recent_key_k_low_pct"] = ((close - pd.to_numeric(df["recent_key_k_low"], errors="coerce")).abs() / base) * 100
    df["near_recent_key_k_low"] = df["distance_to_recent_key_k_low_pct"] <= 3.0
    df["key_k_support_confluence_with_yellow"] = (
        (df["near_recent_key_k_low"] == True) &
        (pd.to_numeric(df.get("distance_to_yellow_pct"), errors="coerce") <= 2.0)
    ).fillna(False)

    return df
