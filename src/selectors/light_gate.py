import pandas as pd


def _is_near_line(row, max_distance_pct: float) -> bool:
    d_white = row.get("distance_to_white_pct")
    d_yellow = row.get("distance_to_yellow_pct")
    near_white = pd.notna(d_white) and float(d_white) <= max_distance_pct
    near_yellow = pd.notna(d_yellow) and float(d_yellow) <= max_distance_pct
    return near_white or near_yellow


def is_light_candidate(row, rules: dict) -> bool:
    if row.get("is_st", False):
        return False

    min_market_cap = rules.get("basic_filter", {}).get("min_market_cap", 2000000000)
    market_cap = row.get("market_cap")
    if pd.isna(market_cap) or market_cap < min_market_cap:
        return False

    j_threshold = min(float(rules.get("b1_core", {}).get("j_threshold", 25)), 20.0)
    j_value = row.get("j_value")
    j_ok = pd.notna(j_value) and float(j_value) < j_threshold

    allow_between = rules.get("b1_core", {}).get("allow_close_between_white_yellow", True)
    allow_near_line = rules.get("b1_core", {}).get("allow_near_white_or_yellow", True)
    near_line_distance_pct_max = rules.get("trend_rules", {}).get("near_line_distance_pct_max", 2.5)

    white_above_yellow = bool(row.get("white_above_yellow", False))
    if not white_above_yellow:
        return False

    close_val = row.get("close")
    yellow_val = row.get("yellow_line")
    close_not_far_below_yellow = (
        pd.notna(close_val) and pd.notna(yellow_val) and float(yellow_val) != 0 and float(close_val) >= float(yellow_val) * 0.9
    )
    if not close_not_far_below_yellow:
        return False

    position_ok = False
    if allow_between and bool(row.get("close_between_white_yellow", False)):
        position_ok = True
    if allow_near_line and _is_near_line(row, near_line_distance_pct_max + 0.5):
        position_ok = True
    if bool(row.get("close_above_yellow", False)):
        position_ok = True

    process_ok = any([
        bool(row.get("time_for_space_signal", False)),
        bool(row.get("price_holding_sideways_5d", False)),
        bool(row.get("pullback_volume_lower_than_rally", False)),
        bool(row.get("down_day_volume_lighter_than_up_day_5d", False)),
        bool(row.get("volume_3d_trend_down", False)),
    ])

    return bool(j_ok and position_ok and process_ok)


def filter_light_candidates(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    mask = df.apply(lambda row: is_light_candidate(row, rules), axis=1)
    return df[mask].copy()
