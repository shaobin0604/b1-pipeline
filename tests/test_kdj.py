import pandas as pd
from src.indicators.kdj import calc_kdj


def test_calc_kdj_runs():
    df = pd.DataFrame({
        "low": [1,2,3,4,5,6,7,8,9,10],
        "high": [2,3,4,5,6,7,8,9,10,11],
        "close": [1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5],
    })
    out = calc_kdj(df)
    assert "j_value" in out.columns
