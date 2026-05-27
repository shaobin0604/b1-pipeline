import pandas as pd


def _is_near_line(row, max_distance_pct: float) -> bool:
    d_white = row.get("distance_to_white_pct")
    d_yellow = row.get("distance_to_yellow_pct")
    near_white = pd.notna(d_white) and float(d_white) <= max_distance_pct
    near_yellow = pd.notna(d_yellow) and float(d_yellow) <= max_distance_pct
    return near_white or near_yellow


def _board_limit_type(code: str) -> str:
    code = str(code).upper()
    if code.startswith(("300", "301", "688")):
        return "limit_20"
    if code.startswith(("8", "4")):
        return "limit_30"
    return "limit_10"


def _board_profile(row, rules: dict) -> dict:
    profiles = rules.get("price_filter", {}).get("board_profiles", {})
    key = _board_limit_type(row.get("code", ""))
    return profiles.get(key, profiles.get("limit_10", {}))


def _process_override_pass(row, rules: dict) -> bool:
    if not rules.get("b1_core", {}).get("process_override_enabled", False):
        return False
    if not row.get("white_above_yellow", False):
        return False

    strong_support_distance = rules.get("trend_rules", {}).get("strong_support_distance_pct_max", 1.2)
    near_white_strong = pd.notna(row.get("distance_to_white_pct")) and float(row.get("distance_to_white_pct")) <= strong_support_distance
    near_yellow_strong = pd.notna(row.get("distance_to_yellow_pct")) and float(row.get("distance_to_yellow_pct")) <= strong_support_distance
    strong_support = near_white_strong or near_yellow_strong or bool(row.get("close_between_white_yellow", False))
    if not strong_support:
        return False

    process_shrink_ok = bool(row.get("pullback_volume_lower_than_rally", False)) or bool(row.get("down_day_volume_lighter_than_up_day_5d", False))
    if rules.get("pullback_rules", {}).get("require_process_shrink_for_override", True) and not process_shrink_ok:
        return False

    time_for_space_ok = bool(row.get("time_for_space_signal", False)) or bool(row.get("price_holding_sideways_5d", False))
    j_value = row.get("j_value")
    j_ok = pd.notna(j_value) and float(j_value) < rules.get("b1_core", {}).get("j_threshold", 25)
    return bool(j_ok and (process_shrink_ok or time_for_space_ok))


def is_b1_candidate(row, rules: dict) -> bool:
    if row.get("is_st", False):
        return False

    # ← 新增：板块白名单过滤
    allowed_boards = rules.get("basic_filter", {}).get("allowed_board_types")
    if allowed_boards:
        if _board_limit_type(row.get("code", "")) not in allowed_boards:
            return False
        
    if bool(row.get("recent_distribution_within_1m", False)):
        return False

    min_market_cap = rules["basic_filter"]["min_market_cap"]
    market_cap = row.get("market_cap")
    if pd.isna(market_cap) or market_cap < min_market_cap:
        return False

    j_threshold = rules["b1_core"].get("j_threshold", 25)
    j_value = row.get("j_value", 999)
    if pd.isna(j_value) or j_value >= j_threshold:
        return False

    if rules["b1_core"].get("require_white_above_yellow", False) and not row.get("white_above_yellow", False):
        return False

    if rules["b1_core"].get("require_close_above_yellow", False) and not row.get("close_above_yellow", False):
        return False

    allow_between = rules["b1_core"].get("allow_close_between_white_yellow", True)
    allow_near_line = rules["b1_core"].get("allow_near_white_or_yellow", True)
    near_line_distance_pct_max = rules.get("trend_rules", {}).get("near_line_distance_pct_max", 2.5)

    position_ok = False
    if row.get("close_above_yellow", False):
        position_ok = True
    if allow_between and row.get("close_between_white_yellow", False):
        position_ok = True
    if allow_near_line and _is_near_line(row, near_line_distance_pct_max):
        position_ok = True

    process_override = _process_override_pass(row, rules)
    if not position_ok and not process_override:
        return False

    if rules["volume_filter"].get("require_10d_min_volume", False) and not row.get("is_10d_min_volume", False):
        return False

    vr_prev_day = row.get("volume_ratio_vs_prev_day")
    max_vr_prev_day = rules["volume_filter"].get("volume_ratio_vs_prev_day_max")
    if pd.notna(vr_prev_day) and max_vr_prev_day is not None and vr_prev_day > max_vr_prev_day:
        if not process_override:
            return False

    vr_prev_5 = row.get("volume_ratio_vs_prev_5d_avg")
    max_vr_prev_5 = rules["volume_filter"].get("volume_ratio_vs_prev_5d_avg_max")
    if pd.notna(vr_prev_5) and max_vr_prev_5 is not None and vr_prev_5 > max_vr_prev_5:
        if not process_override:
            return False

    price_profile = _board_profile(row, rules)
    pct_change = row.get("pct_change", 999)
    amplitude_pct = row.get("amplitude_pct", 999)
    if pd.isna(pct_change) or pd.isna(amplitude_pct):
        return False

    soft_price_ok = bool(
        row.get("white_above_yellow", False)
        and (position_ok or process_override)
        and (
            bool(row.get("time_for_space_signal", False))
            or bool(row.get("price_holding_sideways_5d", False))
            or bool(row.get("close_between_white_yellow", False))
            or (pd.notna(row.get("distance_to_white_pct")) and float(row.get("distance_to_white_pct")) <= near_line_distance_pct_max + 1.5)
            or (pd.notna(row.get("distance_to_yellow_pct")) and float(row.get("distance_to_yellow_pct")) <= near_line_distance_pct_max + 1.5)
        )
        and (
            bool(row.get("pullback_volume_lower_than_rally", False))
            or bool(row.get("down_day_volume_lighter_than_up_day_5d", False))
            or bool(row.get("volume_3d_trend_down", False))
            or (
                pd.notna(vr_prev_day) and pd.notna(vr_prev_5)
                and float(vr_prev_day) <= max_vr_prev_day
                and float(vr_prev_5) <= max_vr_prev_5
            )
        )
    )

    close_change_pct_min = price_profile.get("close_change_pct_min", -3.0)
    close_change_pct_max = price_profile.get("close_change_pct_max", 3.0)
    amplitude_pct_max = price_profile.get("amplitude_pct_max", 4.2)
    if soft_price_ok:
        close_change_pct_min = price_profile.get("soft_close_change_pct_max", abs(close_change_pct_min)) * -1
        close_change_pct_max = price_profile.get("soft_close_change_pct_max", close_change_pct_max)
        amplitude_pct_max = price_profile.get("soft_amplitude_pct_max", amplitude_pct_max)

    if pct_change < close_change_pct_min:
        return False
    if pct_change > close_change_pct_max:
        return False
    if amplitude_pct > amplitude_pct_max:
        return False

    return True


def filter_b1_candidates(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    mask = df.apply(lambda row: is_b1_candidate(row, rules), axis=1)
    return df[mask].copy()
