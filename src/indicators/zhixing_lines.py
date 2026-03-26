import pandas as pd


def _safe_pct_distance(a: pd.Series, b: pd.Series) -> pd.Series:
    base = b.abs().replace(0, pd.NA)
    return ((a - b).abs() / base) * 100


def calc_zhixing_lines(
    df: pd.DataFrame,
    white_ema_span_1: int = 10,
    white_ema_span_2: int = 10,
    yellow_ma_1: int = 14,
    yellow_ma_2: int = 28,
    yellow_ma_3: int = 57,
    yellow_ma_4: int = 114,
    cross_lookback_days: int = 5,
):
    """Approximate Tongdaxin-compatible implementation of user's zhixing lines.

    User-provided formulas:
    - 知行短期趋势线(white): EMA(EMA(C,10),10)
    - 知行多空线(yellow): (MA(C,M1)+MA(C,M2)+MA(C,M3)+MA(C,M4))/4
      with default params: M1=14, M2=28, M3=57, M4=114
    """
    df = df.copy()
    close = pd.to_numeric(df["close"], errors="coerce")

    white_inner = close.ewm(span=white_ema_span_1, adjust=False, min_periods=1).mean()
    df["white_line"] = white_inner.ewm(span=white_ema_span_2, adjust=False, min_periods=1).mean()

    ma1 = close.rolling(yellow_ma_1, min_periods=1).mean()
    ma2 = close.rolling(yellow_ma_2, min_periods=1).mean()
    ma3 = close.rolling(yellow_ma_3, min_periods=1).mean()
    ma4 = close.rolling(yellow_ma_4, min_periods=1).mean()
    df["yellow_line"] = (ma1 + ma2 + ma3 + ma4) / 4.0

    df["white_above_yellow"] = df["white_line"] > df["yellow_line"]

    prev_rel = df["white_line"].shift(1) <= df["yellow_line"].shift(1)
    curr_rel = df["white_line"] > df["yellow_line"]
    df["white_cross_signal"] = (prev_rel & curr_rel).fillna(False)
    df["white_crossed_above_yellow_recently"] = (
        df["white_cross_signal"].rolling(cross_lookback_days, min_periods=1).max().fillna(0).astype(bool)
    )

    df["white_yellow_distance_pct"] = _safe_pct_distance(df["white_line"], df["yellow_line"])

    return df
