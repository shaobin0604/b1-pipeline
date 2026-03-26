import pandas as pd
from src.selectors.b1_filter import filter_b1_candidates


def test_filter_b1_candidates_runs():
    df = pd.DataFrame([{
        "code": "000001.SZ",
        "is_st": False,
        "recent_distribution_within_1m": False,
        "market_cap": 3000000000,
        "j_value": 10,
        "white_above_yellow": True,
        "close_above_yellow": True,
        "close_between_white_yellow": False,
        "distance_to_white_pct": 1.0,
        "distance_to_yellow_pct": 1.2,
        "pct_change": 1.5,
        "amplitude_pct": 2.5,
        "is_10d_min_volume": True,
        "volume_ratio_vs_prev_day": 0.9,
        "volume_ratio_vs_prev_5d_avg": 0.8,
    }])

    rules = {
        "basic_filter": {"min_market_cap": 2000000000},
        "b1_core": {
            "j_threshold": 20,
            "require_white_above_yellow": True,
            "require_close_above_yellow": False,
            "allow_close_between_white_yellow": True,
            "allow_near_white_or_yellow": True,
            "process_override_enabled": False,
        },
        "price_filter": {
            "board_profiles": {
                "limit_10": {
                    "close_change_pct_min": -3.0,
                    "close_change_pct_max": 3.0,
                    "amplitude_pct_max": 4.0,
                    "soft_close_change_pct_max": 3.5,
                    "soft_amplitude_pct_max": 5.0,
                }
            }
        },
        "volume_filter": {
            "require_10d_min_volume": True,
            "volume_ratio_vs_prev_day_max": 1.5,
            "volume_ratio_vs_prev_5d_avg_max": 1.5,
        },
        "trend_rules": {"near_line_distance_pct_max": 2.5},
        "pullback_rules": {"require_process_shrink_for_override": True},
    }

    out = filter_b1_candidates(df, rules)
    assert len(out) == 1
