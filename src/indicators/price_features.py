import pandas as pd


def _safe_pct_distance(price: pd.Series, line: pd.Series) -> pd.Series:
    base = line.abs().replace(0, pd.NA)
    return ((price - line).abs() / base) * 100


def add_price_features(df: pd.DataFrame):
    df = df.copy()
    close = pd.to_numeric(df["close"], errors="coerce")
    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")

    df["pct_change"] = (close / close.shift(1) - 1) * 100
    df["amplitude_pct"] = (high - low) / close.shift(1) * 100
    df["close_in_plus_minus_3pct"] = df["pct_change"].between(-3, 3)
    df["close_positive"] = df["pct_change"] > 0

    rolling_5d_max = close.rolling(5, min_periods=2).max()
    rolling_5d_min = close.rolling(5, min_periods=2).min()
    df["price_range_5d_pct"] = ((rolling_5d_max - rolling_5d_min) / close.shift(1).abs().replace(0, pd.NA)) * 100
    df["price_holding_sideways_5d"] = df["price_range_5d_pct"] <= 6.0

    if "j_value" in df.columns:
        j_change_3d = df["j_value"] - df["j_value"].shift(3)
        close_change_3d = ((close / close.shift(3)) - 1) * 100
        df["j_drop_3d"] = j_change_3d
        df["close_change_3d_pct"] = close_change_3d
        df["time_for_space_signal"] = (
            (j_change_3d <= -10) &
            (close_change_3d.abs() <= 3.0)
        )
    else:
        df["j_drop_3d"] = pd.NA
        df["close_change_3d_pct"] = pd.NA
        df["time_for_space_signal"] = False

    if "white_line" in df.columns:
        df["close_above_white"] = close >= df["white_line"]
        df["distance_to_white_pct"] = _safe_pct_distance(close, df["white_line"])
    else:
        df["close_above_white"] = False
        df["distance_to_white_pct"] = pd.NA

    if "yellow_line" in df.columns:
        df["close_above_yellow"] = close >= df["yellow_line"]
        df["distance_to_yellow_pct"] = _safe_pct_distance(close, df["yellow_line"])
    else:
        df["close_above_yellow"] = False
        df["distance_to_yellow_pct"] = pd.NA

    if "white_line" in df.columns and "yellow_line" in df.columns:
        upper = df[["white_line", "yellow_line"]].max(axis=1)
        lower = df[["white_line", "yellow_line"]].min(axis=1)
        df["close_between_white_yellow"] = (close >= lower) & (close <= upper)
    else:
        df["close_between_white_yellow"] = False

    return df
