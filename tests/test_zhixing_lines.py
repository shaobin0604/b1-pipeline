import pandas as pd
from src.indicators.zhixing_lines import calc_zhixing_lines


def test_calc_zhixing_lines_runs():
    df = pd.DataFrame({"close": list(range(1, 50))})
    out = calc_zhixing_lines(df)
    assert "white_line" in out.columns
    assert "yellow_line" in out.columns
