import pandas as pd
from src.selectors.b1_filter import filter_b1_candidates


def test_filter_b1_candidates_runs():
    df = pd.DataFrame([{
        "is_st": False,
        "market_cap": 3000000000,
        "j_value": 10,
        "white_above_yellow": True,
        "amplitude_pct": 2.5,
        "is_10d_min_volume": True,
    }])

    rules = {
        "basic_filter": {"min_market_cap": 2000000000},
        "b1_core": {"j_threshold": 20, "require_white_above_yellow": True},
        "price_filter": {"amplitude_pct_max": 4},
        "volume_filter": {"require_10d_min_volume": True},
    }

    out = filter_b1_candidates(df, rules)
    assert len(out) == 1
