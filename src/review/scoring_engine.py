def _price_profile(data: dict) -> dict:
    limit_pct = data.get("basic", {}).get("limit_pct", 10)
    if limit_pct >= 30:
        return {
            "comfort_pct": 6.0,
            "hard_pct": 7.0,
            "comfort_amp": 9.0,
            "soft_amp": 10.0,
        }
    if limit_pct >= 20:
        return {
            "comfort_pct": 4.0,
            "hard_pct": 5.0,
            "comfort_amp": 7.0,
            "soft_amp": 8.0,
        }
    return {
        "comfort_pct": 3.0,
        "hard_pct": 3.8,
        "comfort_amp": 4.2,
        "soft_amp": 5.0,
    }


def _cap(value: int | float, max_value: int | float) -> int | float:
    return min(value, max_value)


def score_b1_candidate(data: dict) -> dict:
    strengths = []
    risks = []
    raw_subscores = {
        "base_quality": 0,
        "cost_zone_path": 0,
        "white_control_path": 0,
        "key_k": 0,
        "building_wave": 0,
        "risk_adjustment": 0,
    }

    daily = data.get("daily", {})
    indicators = data.get("indicators", {})
    volume = data.get("volume_features", {})
    position = data.get("price_position", {})
    key_k = data.get("key_k", {})
    building_wave = data.get("building_wave", {})
    basic = data.get("basic", {})
    price_profile = _price_profile(data)
    limit_pct = basic.get("limit_pct", 10)

    j_value = indicators.get("j_value")
    j_drop_3d = indicators.get("j_drop_3d")
    amp = daily.get("amplitude_pct")
    pct_change = daily.get("pct_change")
    close_change_3d_pct = daily.get("close_change_3d_pct")
    white_above_yellow = indicators.get("white_above_yellow")
    distance_pct = indicators.get("white_yellow_distance_pct")
    d_white = position.get("distance_to_white_pct")
    d_yellow = position.get("distance_to_yellow_pct")
    near_white = d_white is not None and d_white <= 1.8
    near_yellow = d_yellow is not None and d_yellow <= 1.8
    very_near_yellow = d_yellow is not None and d_yellow <= 0.6
    tight_cost_zone = distance_pct is not None and distance_pct <= 2.5
    close_between = position.get("close_between_white_yellow")
    close_above_yellow = position.get("close_above_yellow")
    close_above_white = position.get("close_above_white")

    is_10d_min = volume.get("is_10d_min_volume")
    vr_prev_day = volume.get("volume_ratio_vs_prev_day")
    vr_prev_5 = volume.get("volume_ratio_vs_prev_5d_avg")
    down_vs_up_ratio = volume.get("down_vs_up_volume_ratio_5d")
    down_lighter = volume.get("down_day_volume_lighter_than_up_day_5d")
    pullback_vs_rally_ratio = volume.get("pullback_vs_rally_volume_ratio")
    pullback_lower_than_rally = volume.get("pullback_volume_lower_than_rally")
    volume_3d_trend_down = volume.get("volume_3d_trend_down")
    time_for_space = bool(position.get("time_for_space_signal"))
    sideways_5d = bool(daily.get("price_holding_sideways_5d"))

    # ---------- Base quality ----------
    if j_value is not None:
        if j_value <= 0:
            raw_subscores["base_quality"] += 16
            strengths.append("J值进入深低位/负值区，洗盘较充分")
        elif j_value <= 12:
            raw_subscores["base_quality"] += 14
            strengths.append("J值处于理想低位")
        elif j_value <= 20:
            raw_subscores["base_quality"] += 11
            strengths.append("J值处于有效低位")
        elif j_value <= 25:
            raw_subscores["base_quality"] += 7
            strengths.append("J值已回落到可观察区")
        else:
            risks.append("J值偏高")

    if white_above_yellow:
        raw_subscores["base_quality"] += 10
        strengths.append("白线在黄线上方，只做上升趋势票")
    else:
        raw_subscores["risk_adjustment"] -= 18
        risks.append("黄线在白线上方，属于下跌/弱趋势，不做")

    if indicators.get("white_crossed_above_yellow_recently"):
        raw_subscores["base_quality"] += 6
        strengths.append("白线近期上穿黄线，属于早期优势结构")

    if amp is not None:
        comfort_amp = price_profile["comfort_amp"]
        soft_amp = price_profile["soft_amp"]
        if amp <= 1.5:
            raw_subscores["base_quality"] += 8
            strengths.append("日内振幅极小，走势很稳")
        elif amp <= min(3.0, comfort_amp):
            raw_subscores["base_quality"] += 6
            strengths.append("日内振幅较小")
        elif amp <= comfort_amp:
            raw_subscores["base_quality"] += 5
            strengths.append(f"日内振幅对{limit_pct}CM票仍可接受")
        elif time_for_space and amp <= soft_amp:
            raw_subscores["base_quality"] += 3
            strengths.append(f"虽然单日振幅偏大，但对{limit_pct}CM票仍在可容忍范围")
        else:
            risks.append("日内振幅偏大")

    if pct_change is not None:
        comfort_pct = price_profile["comfort_pct"]
        hard_pct = price_profile["hard_pct"]
        if -1.5 <= pct_change <= 1.5:
            raw_subscores["base_quality"] += 8
            strengths.append("收盘平稳，符合温和回调特征")
        elif -comfort_pct <= pct_change <= comfort_pct:
            raw_subscores["base_quality"] += 5
            strengths.append(f"涨跌幅对{limit_pct}CM票仍在舒适区")
        elif time_for_space and pct_change <= hard_pct:
            raw_subscores["base_quality"] += 3
            strengths.append(f"涨跌幅略偏大，但对{limit_pct}CM票仍在可容忍范围")
        else:
            risks.append("收盘涨跌幅偏离B1舒适区")

    if down_lighter:
        raw_subscores["base_quality"] += 8
        strengths.append("近5日阴线缩量、阳线相对放量")
    elif down_vs_up_ratio is not None and down_vs_up_ratio <= 1.0:
        raw_subscores["base_quality"] += 4
        strengths.append("近5日阴线量能不强于阳线")

    if pullback_lower_than_rally:
        raw_subscores["base_quality"] += 10
        strengths.append("回调阶段整体量能明显低于前期放量上涨阶段")
    elif pullback_vs_rally_ratio is not None and pullback_vs_rally_ratio <= 1.0:
        raw_subscores["base_quality"] += 5
        strengths.append("回调阶段整体量能低于前期上涨阶段")

    if volume_3d_trend_down:
        raw_subscores["base_quality"] += 4
        strengths.append("近3日量能呈收缩趋势")

    if is_10d_min:
        raw_subscores["base_quality"] += 6
        strengths.append("成交量达到10日极缩")

    if vr_prev_day is not None:
        if vr_prev_day <= 0.75:
            raw_subscores["base_quality"] += 5
            strengths.append("相对前一日极缩量")
        elif vr_prev_day <= 1.0:
            raw_subscores["base_quality"] += 3
            strengths.append("相对前一日缩量")
        elif vr_prev_day <= 1.2:
            raw_subscores["base_quality"] += 1

    if vr_prev_5 is not None:
        if vr_prev_5 <= 0.8:
            raw_subscores["base_quality"] += 5
            strengths.append("相对近5日均量明显收缩")
        elif vr_prev_5 <= 1.0:
            raw_subscores["base_quality"] += 3
            strengths.append("相对近5日均量温和收缩")
        elif vr_prev_5 <= 1.2:
            raw_subscores["base_quality"] += 1

    # ---------- Cost-zone path ----------
    if distance_pct is not None:
        if distance_pct <= 1.5:
            raw_subscores["cost_zone_path"] += 12
            strengths.append("黄白线极近，主力成本区集中")
        elif distance_pct <= 2.5:
            raw_subscores["cost_zone_path"] += 8
            strengths.append("黄白线较近，靠近主力成本区")
        elif distance_pct <= 5.0:
            raw_subscores["cost_zone_path"] += 4

    if close_between:
        raw_subscores["cost_zone_path"] += 8
        strengths.append("收盘位于白黄线之间，属于成本区支撑")
    elif close_above_yellow:
        raw_subscores["cost_zone_path"] += 5
        strengths.append("收盘站在黄线上方")

    if near_yellow:
        raw_subscores["cost_zone_path"] += 11
        strengths.append("价格贴近黄线，接近主力成本/强支撑区")
    if very_near_yellow and tight_cost_zone:
        raw_subscores["cost_zone_path"] += 12
        strengths.append("几乎贴着黄线且黄白线距离小，属于建仓后第一B1高性价比区")
    if indicators.get("white_crossed_above_yellow_recently") and tight_cost_zone:
        raw_subscores["cost_zone_path"] += 7
        strengths.append("黄白线刚形成多头结构，第一B1优势明显")

    # ---------- White-control path ----------
    if near_white:
        raw_subscores["white_control_path"] += 12
        strengths.append("价格贴近白线，符合控盘线附近企稳特征")
    elif d_white is not None and d_white <= 3.0 and white_above_yellow:
        raw_subscores["white_control_path"] += 7
        strengths.append("价格相对白线不远，仍属于白线控盘回踩区")

    if not close_above_white and near_white:
        raw_subscores["white_control_path"] += 3
        strengths.append("略破白线但距离很近，可视为轻微试探支撑")
    if distance_pct is not None and distance_pct > 5.0 and white_above_yellow and (near_white or (d_white is not None and d_white <= 3.0)):
        raw_subscores["white_control_path"] += 8
        strengths.append("虽离黄线较远，但仍受白线控盘，属于白线控盘回踩型")
    if sideways_5d:
        raw_subscores["white_control_path"] += 10
        strengths.append("近5日价格横住，符合时间换空间特征")
    if time_for_space:
        raw_subscores["white_control_path"] += 12
        strengths.append("价格没怎么跌，但J快速下行，属于时间换空间")
    elif j_drop_3d is not None and close_change_3d_pct is not None and j_drop_3d <= -6 and abs(close_change_3d_pct) <= 4:
        raw_subscores["white_control_path"] += 8
        strengths.append("J值下降快于股价调整速度")
    if down_lighter:
        raw_subscores["white_control_path"] += 5
    if pullback_lower_than_rally:
        raw_subscores["white_control_path"] += 6
    elif pullback_vs_rally_ratio is not None and pullback_vs_rally_ratio <= 1.0:
        raw_subscores["white_control_path"] += 3

    # ---------- Key K ----------
    recent_key_k_exists = bool(key_k.get("recent_key_k_exists"))
    recent_key_k_age = key_k.get("recent_key_k_age")
    distance_to_key_k_low = key_k.get("distance_to_recent_key_k_low_pct")
    near_key_k_low = bool(key_k.get("near_recent_key_k_low"))
    key_k_confluence = bool(key_k.get("key_k_support_confluence_with_yellow"))
    key_k_body = key_k.get("recent_key_k_real_body_pct")
    key_k_vol_ratio = key_k.get("recent_key_k_volume_ratio")

    if recent_key_k_exists:
        raw_subscores["key_k"] += 4
        strengths.append("近期存在关键K候选，说明前面有主力放量进攻痕迹")
    if recent_key_k_age is not None:
        try:
            if float(recent_key_k_age) <= 20:
                raw_subscores["key_k"] += 3
                strengths.append("关键K距离当前不远，参考价值较高")
        except Exception:
            pass
    if near_key_k_low:
        raw_subscores["key_k"] += 8
        strengths.append("当前价格贴近关键K低点，支撑明确")
    elif distance_to_key_k_low is not None:
        try:
            if float(distance_to_key_k_low) <= 5.0:
                raw_subscores["key_k"] += 4
                strengths.append("当前价格靠近关键K低点")
        except Exception:
            pass
    if key_k_confluence:
        raw_subscores["key_k"] += 10
        strengths.append("黄线与关键K低点形成支撑共振，盈亏比更高")
    if key_k_body is not None:
        try:
            if float(key_k_body) >= 4.0:
                raw_subscores["key_k"] += 3
                strengths.append("关键K实体较大，更像有效建仓阳线")
        except Exception:
            pass
    if key_k_vol_ratio is not None:
        try:
            if float(key_k_vol_ratio) >= 2.0:
                raw_subscores["key_k"] += 3
                strengths.append("关键K量能明显放大，确认度更高")
        except Exception:
            pass

    # ---------- Building wave ----------
    quality_attack = bool(building_wave.get("building_wave_has_quality_attack"))
    upper_shadow_heavy = bool(building_wave.get("building_wave_upper_shadow_heavy"))
    wave_quality_score = building_wave.get("building_wave_quality_score")
    strong_attack_count = building_wave.get("strong_attack_bar_count_30d")
    weak_attack_count = building_wave.get("weak_attack_upper_shadow_count_30d")
    recent_attack_exists = bool(building_wave.get("recent_attack_bar_exists"))
    recent_attack_age = building_wave.get("recent_attack_bar_age")
    recent_attack_is_strong = bool(building_wave.get("recent_attack_bar_is_strong"))
    recent_attack_upper_shadow_ratio = building_wave.get("recent_attack_bar_upper_shadow_ratio")
    recent_attack_real_body_pct = building_wave.get("recent_attack_bar_real_body_pct")
    recent_attack_volume_ratio = building_wave.get("recent_attack_bar_volume_ratio")

    if quality_attack:
        raw_subscores["building_wave"] += 3
        strengths.append("前期建仓波中存在像样的大实体放量进攻K")
    if recent_attack_exists:
        raw_subscores["building_wave"] += 1
        strengths.append("前期存在可识别的进攻阳线")
    if recent_attack_is_strong:
        raw_subscores["building_wave"] += 2
        strengths.append("最近关键进攻K实体较好、上影较轻，更像有效建仓推进")
    if recent_attack_age is not None:
        try:
            if float(recent_attack_age) <= 12 and recent_attack_is_strong:
                raw_subscores["building_wave"] += 1
                strengths.append("像样的建仓进攻K离当前不远")
        except Exception:
            pass
    if recent_attack_real_body_pct is not None:
        try:
            if float(recent_attack_real_body_pct) >= 5.5 and recent_attack_is_strong:
                raw_subscores["building_wave"] += 1
                strengths.append("进攻K实体较大")
        except Exception:
            pass
    if recent_attack_volume_ratio is not None:
        try:
            if float(recent_attack_volume_ratio) >= 2.0 and recent_attack_is_strong:
                raw_subscores["building_wave"] += 1
                strengths.append("进攻K放量较明显")
        except Exception:
            pass
    if wave_quality_score is not None:
        try:
            if float(wave_quality_score) >= 2 and quality_attack:
                raw_subscores["building_wave"] += 2
                strengths.append("建仓波整体质量较好，强攻击K多于弱攻击K")
            elif float(wave_quality_score) <= -1:
                raw_subscores["risk_adjustment"] -= 4
                risks.append("建仓波质量偏弱，弱攻击/虚冲K偏多")
        except Exception:
            pass
    if upper_shadow_heavy:
        raw_subscores["risk_adjustment"] -= 4
        risks.append("前期建仓波上影偏多，像冲高试盘而非强建仓")
    if weak_attack_count is not None and strong_attack_count is not None:
        try:
            if float(weak_attack_count) >= 2 and float(strong_attack_count) == 0:
                raw_subscores["risk_adjustment"] -= 3
                risks.append("前期进攻K更多是上影偏重的弱攻击")
        except Exception:
            pass
    if recent_attack_upper_shadow_ratio is not None:
        try:
            if float(recent_attack_upper_shadow_ratio) >= 0.5:
                raw_subscores["risk_adjustment"] -= 2
                risks.append("最近进攻K上影偏重，建仓质量打折")
        except Exception:
            pass

    # ---------- New dirty-structure penalties ----------
    pullback_heavy_count = building_wave.get("pullback_heavy_volume_count_5d")
    pullback_heavy_consecutive = building_wave.get("pullback_heavy_volume_max_consecutive_5d")
    heavy_bear_count_10d = building_wave.get("heavy_bear_count_10d")
    max_consecutive_heavy_bear_10d = building_wave.get("max_consecutive_heavy_bear_10d")
    double_volume_bull_count_30d = building_wave.get("double_volume_bull_count_30d")
    max_bear_volume_last_10d_vs_recent_attack_ratio = building_wave.get("max_bear_volume_last_10d_vs_recent_attack_ratio")
    drawdown_from_post_cross_high_pct = building_wave.get("drawdown_from_post_cross_high_pct")
    recent_bearish_reversal_exists = bool(building_wave.get("recent_bearish_reversal_exists"))
    recent_bearish_reversal_age = building_wave.get("recent_bearish_reversal_age")
    recent_gap_attack_exists = bool(building_wave.get("recent_gap_attack_exists"))
    broke_recent_gap_attack_low = bool(building_wave.get("broke_recent_gap_attack_low"))
    vertical_decline_with_heavy_volume = bool(building_wave.get("vertical_decline_with_heavy_volume"))
    rise_from_last_white_cross_pct = building_wave.get("rise_from_last_white_cross_pct")
    high_volume_sideways_after_big_run = bool(building_wave.get("high_volume_sideways_after_big_run"))

    if rise_from_last_white_cross_pct is not None:
        try:
            rise_pct = float(rise_from_last_white_cross_pct)
            if rise_pct >= 80:
                raw_subscores["risk_adjustment"] -= 8
                risks.append("???????????????????")
            elif rise_pct >= 60:
                raw_subscores["risk_adjustment"] -= 5
                risks.append("?????????????????????")
            elif rise_pct >= 40:
                raw_subscores["risk_adjustment"] -= 2
                risks.append("????????????????????")
            elif rise_pct <= 20:
                raw_subscores["building_wave"] += 1
                strengths.append("???????????????????")
        except Exception:
            pass

    if double_volume_bull_count_30d is not None:
        try:
            if float(double_volume_bull_count_30d) >= 2:
                raw_subscores["building_wave"] += 3
                strengths.append("?30????????????????????")
            elif float(double_volume_bull_count_30d) == 1:
                raw_subscores["building_wave"] += 1
                strengths.append("?30????????????????")
            else:
                raw_subscores["risk_adjustment"] -= 2
                risks.append("?30???????????????")
        except Exception:
            pass

    if drawdown_from_post_cross_high_pct is not None:
        try:
            dd = float(drawdown_from_post_cross_high_pct)
            if dd > 22:
                raw_subscores["risk_adjustment"] -= 10
                risks.append("??????????????????????")
            elif dd > 18:
                raw_subscores["risk_adjustment"] -= 6
                risks.append("????????????????")
            elif dd <= 12:
                raw_subscores["building_wave"] += 1
                strengths.append("????????????????")
        except Exception:
            pass

    if max_bear_volume_last_10d_vs_recent_attack_ratio is not None:
        try:
            ratio = float(max_bear_volume_last_10d_vs_recent_attack_ratio)
            if ratio > 1.2:
                raw_subscores["risk_adjustment"] -= 7
                risks.append("?10???????????????????")
            elif ratio > 1.0:
                raw_subscores["risk_adjustment"] -= 4
                risks.append("?10???????????????????")
            elif ratio <= 0.7:
                raw_subscores["building_wave"] += 2
                strengths.append("?10??????????????????")
        except Exception:
            pass

    if max_consecutive_heavy_bear_10d is not None:
        try:
            if float(max_consecutive_heavy_bear_10d) >= 2:
                raw_subscores["risk_adjustment"] -= 6
                risks.append("?10?????????????????")
        except Exception:
            pass

    if heavy_bear_count_10d is not None:
        try:
            if float(heavy_bear_count_10d) >= 3:
                raw_subscores["risk_adjustment"] -= 5
                risks.append("?10??????????????")
            elif float(heavy_bear_count_10d) == 0:
                raw_subscores["building_wave"] += 1
                strengths.append("?10????????????????")
        except Exception:
            pass

    climax_bear_after_acceleration = bool(building_wave.get("climax_bear_after_acceleration"))
    secondary_top_huge_bear = bool(building_wave.get("secondary_top_huge_bear"))
    stair_down_after_new_high = bool(building_wave.get("stair_down_after_new_high"))
    double_top_double_distribution = bool(building_wave.get("double_top_double_distribution"))
    top_green_long_red_short = bool(building_wave.get("top_green_long_red_short"))
    top_blowoff_reversal = bool(building_wave.get("top_blowoff_reversal"))
    peak_huge_volume_break_yellow_2d = bool(building_wave.get("peak_huge_volume_break_yellow_2d"))
    top_3day_stair_volume_distribution = bool(building_wave.get("top_3day_stair_volume_distribution"))
    overhead_supply_near_prev_high = bool(building_wave.get("overhead_supply_near_prev_high"))
    failed_breakout_overhead_supply = bool(building_wave.get("failed_breakout_overhead_supply"))
    overhead_heavy_volume_band = bool(building_wave.get("overhead_heavy_volume_band"))
    failed_reclaim_yellow_on_day2 = bool(building_wave.get("failed_reclaim_yellow_on_day2"))
    supply_absorption_breakthrough = bool(building_wave.get("supply_absorption_breakthrough"))
    double_limit_then_high_volatility_sideways = bool(building_wave.get("double_limit_then_high_volatility_sideways"))
    recent_distribution_within_1m = bool(building_wave.get("recent_distribution_within_1m"))
    recent_distribution_count_1m = building_wave.get("recent_distribution_count_1m")

    if recent_distribution_within_1m:
        count_text = ""
        try:
            if recent_distribution_count_1m is not None:
                count_text = f"（近1个月命中{int(recent_distribution_count_1m)}次）"
        except Exception:
            pass
        risks.append(f"近1个月内出现主力出货形态{count_text}，该B1按规则直接不考虑")

    if pullback_heavy_consecutive is not None:
        try:
            if float(pullback_heavy_consecutive) >= 2:
                raw_subscores["risk_adjustment"] -= 6
                risks.append("回调高点附近连续放量，洗盘不干净")
            elif float(pullback_heavy_count or 0) >= 2:
                raw_subscores["risk_adjustment"] -= 3
                risks.append("回调过程中出现多次放量反压")
        except Exception:
            pass

    if recent_bearish_reversal_exists:
        try:
            if recent_bearish_reversal_age is not None and float(recent_bearish_reversal_age) <= 20:
                raw_subscores["risk_adjustment"] -= 7
                risks.append("前期出现创新高后放量转阴的高位风险K")
        except Exception:
            raw_subscores["risk_adjustment"] -= 4
            risks.append("前期存在高位放量阴线风险")

    if recent_gap_attack_exists:
        raw_subscores["building_wave"] -= 1
        risks.append("前期关键进攻更像跳空推进，不如完整实体阳线扎实")
    if broke_recent_gap_attack_low:
        raw_subscores["risk_adjustment"] -= 6
        risks.append("回调已跌破跳空攻击K最低点，建仓波质量明显打折")

    if vertical_decline_with_heavy_volume:
        raw_subscores["risk_adjustment"] -= 7
        risks.append("回调呈直上直下并伴随阶梯放量下跌，不符合优质B1")

    if high_volume_sideways_after_big_run:
        raw_subscores["risk_adjustment"] -= 6
        risks.append("大涨后放量横盘，分歧偏大，不像干净回调")

    # ---------- Main-force distribution-style penalties ----------
    if climax_bear_after_acceleration:
        raw_subscores["risk_adjustment"] -= 8
        risks.append("加速后出现单日天量大阴，疑似主力集中出货")

    if secondary_top_huge_bear:
        raw_subscores["risk_adjustment"] -= 7
        risks.append("加速后次高点突发巨量长阴，像高位派发而非健康分歧")

    if stair_down_after_new_high:
        raw_subscores["risk_adjustment"] -= 8
        risks.append("新高后连续阶梯放量下跌，出货味道重")

    if double_top_double_distribution:
        raw_subscores["risk_adjustment"] -= 7
        risks.append("顶部区域出现双头双放量阴线，顶部派发嫌疑大")

    if top_green_long_red_short:
        raw_subscores["risk_adjustment"] -= 5
        risks.append("顶部绿长红短，反弹弱、抛压重")

    if top_blowoff_reversal:
        raw_subscores["risk_adjustment"] -= 8
        risks.append("顶部冲高创新高后爆量反转，疑似借冲高集中派发")

    if peak_huge_volume_break_yellow_2d:
        raw_subscores["risk_adjustment"] -= 8
        risks.append("最高点放巨量后，连续两天跌破黄线并创新低，出货后走坏明显")

    if top_3day_stair_volume_distribution:
        raw_subscores["risk_adjustment"] -= 7
        risks.append("顶部连续3天放大量且量能阶梯抬升，派发味道重")

    # ---------- Overhead supply / trapped-supply penalties ----------
    if overhead_supply_near_prev_high:
        raw_subscores["risk_adjustment"] -= 4
        risks.append("前高压力很近，上方仍有明显套牢/抛压")

    if failed_breakout_overhead_supply:
        raw_subscores["risk_adjustment"] -= 6
        risks.append("前面有放量冲高但未站稳，头顶套牢供给较重")

    if overhead_heavy_volume_band:
        raw_subscores["risk_adjustment"] -= 5
        risks.append("高位密集成交区仍压在头顶附近，向上容易遇压")

    if supply_absorption_breakthrough:
        raw_subscores["building_wave"] += 3
        strengths.append("后续巨量强攻击K已明显吸收前期头顶供给")
        if failed_breakout_overhead_supply:
            raw_subscores["risk_adjustment"] += 4
            risks.append("供给吸收突破已部分对冲前期假突破套牢压力")
        if overhead_heavy_volume_band:
            raw_subscores["risk_adjustment"] += 3
            risks.append("供给吸收突破已部分对冲高位密集成交压制")

    if failed_reclaim_yellow_on_day2:
        raw_subscores["risk_adjustment"] -= 6
        risks.append("跌破黄线第二天仍未收回，说明强度不够")

    if double_limit_then_high_volatility_sideways:
        raw_subscores["risk_adjustment"] -= 9
        risks.append("短期连续两个涨停后高位剧烈横盘，且出现超大振幅，不够像干净B1")

    if rise_from_last_white_cross_pct is not None:
        try:
            if float(rise_from_last_white_cross_pct) >= 100:
                raw_subscores["risk_adjustment"] -= 5
                risks.append("自白线上穿黄线以来累计涨幅过大，位置偏高")
            elif float(rise_from_last_white_cross_pct) >= 80:
                raw_subscores["risk_adjustment"] -= 3
                risks.append("自白线上穿黄线以来累计涨幅已较大")
        except Exception:
            pass

    # ---------- Risk adjustments ----------
    chosen_path = "cost_zone_path" if raw_subscores["cost_zone_path"] >= raw_subscores["white_control_path"] else "white_control_path"

    if pct_change is not None and pct_change > price_profile["hard_pct"] and not time_for_space:
        raw_subscores["risk_adjustment"] -= 4
        risks.append("当日涨幅偏大，不够像低吸型B1")
    if pct_change is not None and pct_change < -price_profile["hard_pct"]:
        raw_subscores["risk_adjustment"] -= 4
        risks.append("当日跌幅偏大，可能不是温和洗盘")
    if amp is not None and amp > price_profile["soft_amp"] and not time_for_space:
        raw_subscores["risk_adjustment"] -= 4
        risks.append("日内振幅偏大")
    if distance_pct is not None and distance_pct > 8 and chosen_path != "white_control_path":
        raw_subscores["risk_adjustment"] -= 2
        risks.append("白黄线分离过大，性价比下降")
    if vr_prev_day is not None and vr_prev_day > 1.2 and not (pullback_lower_than_rally or down_lighter):
        raw_subscores["risk_adjustment"] -= 2
        risks.append("相对前一日缩量不明显")
    if vr_prev_5 is not None and vr_prev_5 > 1.2 and not pullback_lower_than_rally:
        raw_subscores["risk_adjustment"] -= 2
        risks.append("相对近5日均量缩量不明显")

    subscores = {
        "base_quality": int(_cap(raw_subscores["base_quality"], 58)),
        "cost_zone_path": int(_cap(raw_subscores["cost_zone_path"], 24)),
        "white_control_path": int(_cap(raw_subscores["white_control_path"], 26)),
        "key_k": int(_cap(max(raw_subscores["key_k"], 0), 12)),
        "building_wave": int(_cap(max(raw_subscores["building_wave"], 0), 8)),
        "risk_adjustment": int(raw_subscores["risk_adjustment"]),
    }

    chosen_path = "cost_zone_path" if subscores["cost_zone_path"] >= subscores["white_control_path"] else "white_control_path"
    score = (
        subscores["base_quality"]
        + max(subscores["cost_zone_path"], subscores["white_control_path"])
        + subscores["key_k"]
        + subscores["building_wave"]
        + subscores["risk_adjustment"]
    )

    if recent_distribution_within_1m:
        score = min(score, 35)
        grade = "E"
        decision = "淘汰（近1个月内出现主力出货形态）"
    elif score >= 86:
        grade = "A"
        decision = "重点优先审核"
    elif score >= 72:
        grade = "B"
        decision = "进入最终人工审核池"
    elif score >= 58:
        grade = "C"
        decision = "进入观察名单"
    elif score >= 44:
        grade = "D"
        decision = "低优先级观察/大多淘汰"
    else:
        grade = "E"
        decision = "淘汰"

    path_comment = "黄线成本区/第一B1路径" if chosen_path == "cost_zone_path" else "白线控盘/时间换空间路径"

    return {
        "total_score": score,
        "grade": grade,
        "decision": decision,
        "subscores": subscores,
        "strengths": strengths,
        "risks": risks,
        "comment": f"已接入脏结构惩罚版：基础质量分 + 双路径择优（{path_comment}）+ 关键K支撑 + 建仓波质量，并新增回调放量脏量、高位放量阴线、跳空攻击失守、直上直下放量下跌，以及主力出货案例化惩罚（加速后天量大阴、次高点巨量长阴、新高后阶梯放量下跌、双头双放量阴、顶部绿长红短、冲高创新高后爆量反转）。"
    }
