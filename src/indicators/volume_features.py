import pandas as pd


def add_volume_features(df: pd.DataFrame):
    df = df.copy()

    volume = pd.to_numeric(df["volume"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    prev_close = close.shift(1)

    df["volume_ratio_vs_prev_day"] = volume / volume.shift(1)
    df["volume_ratio_vs_prev_5d_avg"] = volume / volume.rolling(5).mean()
    df["is_10d_min_volume"] = volume <= volume.rolling(10).min()

    is_up_day = close >= prev_close
    is_down_day = close < prev_close
    df["is_up_day"] = is_up_day.fillna(False)
    df["is_down_day"] = is_down_day.fillna(False)

    up_volume = volume.where(is_up_day)
    down_volume = volume.where(is_down_day)

    df["up_day_volume_5d_avg"] = up_volume.rolling(5, min_periods=1).mean()
    df["down_day_volume_5d_avg"] = down_volume.rolling(5, min_periods=1).mean()
    df["down_vs_up_volume_ratio_5d"] = df["down_day_volume_5d_avg"] / df["up_day_volume_5d_avg"]
    df["down_day_volume_lighter_than_up_day_5d"] = df["down_vs_up_volume_ratio_5d"] <= 0.85

    rally_volume_5d_avg = volume.shift(3).rolling(5, min_periods=3).mean()
    pullback_volume_3d_avg = volume.rolling(3, min_periods=2).mean()
    df["pullback_vs_rally_volume_ratio"] = pullback_volume_3d_avg / rally_volume_5d_avg
    df["pullback_volume_lower_than_rally"] = df["pullback_vs_rally_volume_ratio"] <= 0.8

    df["volume_3d_trend_down"] = volume.rolling(3, min_periods=3).apply(
        lambda x: 1.0 if x.iloc[-1] <= x.iloc[0] else 0.0, raw=False
    ).fillna(0).astype(bool)

    return df
