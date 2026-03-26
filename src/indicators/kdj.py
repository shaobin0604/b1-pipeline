import pandas as pd


def calc_kdj(df: pd.DataFrame, n: int = 9):
    df = df.copy()
    low_n = df["low"].rolling(n).min()
    high_n = df["high"].rolling(n).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    df["k_value"] = rsv.ewm(com=2).mean()
    df["d_value"] = df["k_value"].ewm(com=2).mean()
    df["j_value"] = 3 * df["k_value"] - 2 * df["d_value"]
    return df
