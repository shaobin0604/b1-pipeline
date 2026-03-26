import pandas as pd


def _max_consecutive_true(values) -> int:
    best = 0
    cur = 0
    for v in values:
        try:
            flag = bool(v) if pd.notna(v) else False
        except Exception:
            flag = False
        if flag:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def add_building_wave_features(
    df: pd.DataFrame,
    lookback_days: int = 30,
    attack_pct_min: float = 4.0,
    volume_ratio_min: float = 1.5,
    strong_body_pct_min: float = 3.8,
    upper_shadow_ratio_max: float = 0.28,
):
    df = df.copy()

    open_ = pd.to_numeric(df["open"], errors="coerce")
    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    volume = pd.to_numeric(df["volume"], errors="coerce")
    pct_change = pd.to_numeric(df.get("pct_change"), errors="coerce")
    if pct_change.isna().all():
        pct_change = (close / close.shift(1) - 1) * 100

    volume_ratio = volume / volume.shift(1)
    real_body = (close - open_).abs()
    candle_range = (high - low).replace(0, pd.NA)
    real_body_pct = (real_body / open_.replace(0, pd.NA)) * 100
    upper_shadow = (high - pd.concat([open_, close], axis=1).max(axis=1)).clip(lower=0)
    upper_shadow_ratio = upper_shadow / candle_range
    bullish = close > open_
    bearish = close < open_

    prev_high = high.shift(1)
    prev_20d_high = high.shift(1).rolling(20, min_periods=5).max()

    df["attack_bar_candidate"] = (
        bullish &
        (pct_change >= attack_pct_min) &
        (volume_ratio >= volume_ratio_min)
    ).fillna(False)
    df["strong_attack_bar"] = (
        df["attack_bar_candidate"] &
        (real_body_pct >= strong_body_pct_min) &
        (upper_shadow_ratio <= upper_shadow_ratio_max)
    ).fillna(False)
    df["weak_attack_upper_shadow_bar"] = (
        df["attack_bar_candidate"] &
        (upper_shadow_ratio > 0.42)
    ).fillna(False)

    df["gap_attack_bar"] = (
        df["attack_bar_candidate"] &
        (low > prev_high)
    ).fillna(False)
    df["gap_attack_low"] = low.where(df["gap_attack_bar"])

    df["bearish_reversal_after_new_high"] = (
        bearish &
        (high >= prev_20d_high) &
        (volume_ratio >= 1.3)
    ).fillna(False)

    df["pullback_heavy_volume_day"] = (
        bearish &
        (volume_ratio >= 1.2)
    ).fillna(False)

    df["double_volume_bull_bar"] = (
        bullish &
        (volume_ratio >= 2.0) &
        (pct_change >= max(attack_pct_min - 0.5, 3.0))
    ).fillna(False)

    df["attack_bar_volume_ratio"] = volume_ratio
    df["attack_bar_real_body_pct"] = real_body_pct
    df["attack_bar_upper_shadow_ratio"] = upper_shadow_ratio

    strong_attack_count = []
    weak_attack_count = []
    building_wave_quality_score = []
    recent_attack_exists = []
    recent_attack_age = []
    recent_attack_is_strong = []
    recent_attack_upper_shadow_ratio = []
    recent_attack_real_body_pct = []
    recent_attack_volume_ratio = []

    recent_gap_attack_exists = []
    recent_gap_attack_age = []
    recent_gap_attack_low = []
    broke_recent_gap_attack_low = []

    recent_bearish_reversal_exists = []
    recent_bearish_reversal_age = []

    pullback_heavy_volume_count_5d = []
    pullback_heavy_volume_max_consecutive_5d = []
    heavy_bear_count_10d = []
    max_consecutive_heavy_bear_10d = []
    double_volume_bull_count_30d = []
    max_bear_volume_last_10d_vs_recent_attack_ratio = []
    drawdown_from_post_cross_high_pct = []
    vertical_decline_with_heavy_volume = []
    rise_from_last_white_cross_pct = []
    high_volume_sideways_after_big_run = []

    climax_bear_after_acceleration = []
    secondary_top_huge_bear = []
    stair_down_after_new_high = []
    double_top_double_distribution = []
    top_green_long_red_short = []
    top_blowoff_reversal = []
    peak_huge_volume_break_yellow_2d = []
    top_3day_stair_volume_distribution = []
    overhead_supply_near_prev_high = []
    failed_breakout_overhead_supply = []
    overhead_heavy_volume_band = []
    failed_reclaim_yellow_on_day2 = []
    supply_absorption_breakthrough = []
    double_limit_then_high_volatility_sideways = []
    recent_distribution_within_1m = []
    recent_distribution_count_1m = []

    white_cross_signal = df.get("white_cross_signal")
    if white_cross_signal is None:
        white_cross_signal = pd.Series([False] * len(df), index=df.index)
    else:
        white_cross_signal = white_cross_signal.fillna(False)

    for i in range(len(df)):
        start = max(0, i - lookback_days)
        hist = df.iloc[start:i+1]
        strong_cnt = int(hist["strong_attack_bar"].fillna(False).sum())
        weak_cnt = int(hist["weak_attack_upper_shadow_bar"].fillna(False).sum())
        strong_attack_count.append(strong_cnt)
        weak_attack_count.append(weak_cnt)
        building_wave_quality_score.append(strong_cnt - weak_cnt)

        candidates = hist[hist["attack_bar_candidate"] == True]
        if candidates.empty:
            recent_attack_exists.append(False)
            recent_attack_age.append(pd.NA)
            recent_attack_is_strong.append(False)
            recent_attack_upper_shadow_ratio.append(pd.NA)
            recent_attack_real_body_pct.append(pd.NA)
            recent_attack_volume_ratio.append(pd.NA)
        else:
            last_idx = candidates.index[-1]
            last_row = df.loc[last_idx]
            recent_attack_exists.append(True)
            recent_attack_age.append(i - df.index.get_loc(last_idx))
            recent_attack_is_strong.append(bool(last_row.get("strong_attack_bar", False)))
            recent_attack_upper_shadow_ratio.append(last_row.get("attack_bar_upper_shadow_ratio"))
            recent_attack_real_body_pct.append(last_row.get("attack_bar_real_body_pct"))
            recent_attack_volume_ratio.append(last_row.get("attack_bar_volume_ratio"))

        gap_candidates = hist[hist["gap_attack_bar"] == True]
        if gap_candidates.empty:
            recent_gap_attack_exists.append(False)
            recent_gap_attack_age.append(pd.NA)
            recent_gap_attack_low.append(pd.NA)
            broke_recent_gap_attack_low.append(False)
        else:
            gap_idx = gap_candidates.index[-1]
            gap_row = df.loc[gap_idx]
            gap_low = gap_row.get("gap_attack_low")
            recent_gap_attack_exists.append(True)
            recent_gap_attack_age.append(i - df.index.get_loc(gap_idx))
            recent_gap_attack_low.append(gap_low)
            try:
                broke_recent_gap_attack_low.append(bool(pd.notna(gap_low) and pd.notna(close.iloc[i]) and close.iloc[i] < float(gap_low)))
            except Exception:
                broke_recent_gap_attack_low.append(False)

        bearish_reversals = hist[hist["bearish_reversal_after_new_high"] == True]
        if bearish_reversals.empty:
            recent_bearish_reversal_exists.append(False)
            recent_bearish_reversal_age.append(pd.NA)
        else:
            rev_idx = bearish_reversals.index[-1]
            recent_bearish_reversal_exists.append(True)
            recent_bearish_reversal_age.append(i - df.index.get_loc(rev_idx))

        pb_hist = df.iloc[max(0, i - 4):i+1]
        dirty_flags = pb_hist["pullback_heavy_volume_day"].fillna(False).tolist()
        dirty_count = int(sum(bool(x) for x in dirty_flags if pd.notna(x)))
        pullback_heavy_volume_count_5d.append(dirty_count)
        pullback_heavy_volume_max_consecutive_5d.append(_max_consecutive_true(dirty_flags))

        hist10_local = df.iloc[max(0, i - 9):i+1]
        heavy_bear_flags_10d = hist10_local["pullback_heavy_volume_day"].fillna(False).tolist()
        heavy_bear_count_10d.append(int(sum(bool(x) for x in heavy_bear_flags_10d if pd.notna(x))))
        max_consecutive_heavy_bear_10d.append(_max_consecutive_true(heavy_bear_flags_10d))

        hist30_local = df.iloc[max(0, i - 29):i+1]
        double_volume_bull_count_30d.append(int(hist30_local["double_volume_bull_bar"].fillna(False).sum()))

        recent_attack_vol = pd.NA
        if recent_attack_exists[-1]:
            try:
                recent_attack_vol = volume.iloc[i - int(recent_attack_age[-1])]
            except Exception:
                recent_attack_vol = pd.NA
        bear_vol_10d = pd.to_numeric(hist10_local.loc[hist10_local["pullback_heavy_volume_day"] == True, "volume"], errors="coerce")
        max_bear_vol_10d = bear_vol_10d.max() if not bear_vol_10d.empty else pd.NA
        if pd.notna(recent_attack_vol) and recent_attack_vol not in (0, 0.0) and pd.notna(max_bear_vol_10d):
            max_bear_volume_last_10d_vs_recent_attack_ratio.append(float(max_bear_vol_10d) / float(recent_attack_vol))
        else:
            max_bear_volume_last_10d_vs_recent_attack_ratio.append(pd.NA)

        cross_hist = white_cross_signal.iloc[:i+1]
        cross_points = cross_hist[cross_hist == True]
        if cross_points.empty:
            drawdown_from_post_cross_high_pct.append(pd.NA)
        else:
            cross_idx = cross_points.index[-1]
            cross_loc = df.index.get_loc(cross_idx)
            post_cross_high = pd.to_numeric(high.iloc[cross_loc:i+1], errors='coerce').max()
            if pd.notna(post_cross_high) and post_cross_high != 0 and pd.notna(close.iloc[i]):
                drawdown_from_post_cross_high_pct.append((float(post_cross_high) - float(close.iloc[i])) / float(post_cross_high) * 100)
            else:
                drawdown_from_post_cross_high_pct.append(pd.NA)

        pct3 = pct_change.iloc[max(0, i - 2):i+1]
        vol3 = volume.iloc[max(0, i - 2):i+1]
        down_count = int((pct3 < 0).fillna(False).sum())
        if len(vol3) >= 3 and pd.notna(vol3.iloc[-1]) and pd.notna(vol3.iloc[-2]) and pd.notna(vol3.iloc[-3]):
            vol_up_stair = bool(vol3.iloc[-1] >= vol3.iloc[-2] >= vol3.iloc[-3])
        else:
            vol_up_stair = False
        if i >= 2 and pd.notna(close.iloc[max(0, i - 2)]) and close.iloc[max(0, i - 2)] != 0 and pd.notna(close.iloc[i]):
            close_3d_pct = (close.iloc[i] / close.iloc[max(0, i - 2)] - 1) * 100
        else:
            close_3d_pct = pd.NA
        vertical_decline_with_heavy_volume.append(bool(down_count >= 2 and pd.notna(close_3d_pct) and close_3d_pct <= -6 and vol_up_stair))

        cross_hist = white_cross_signal.iloc[:i+1]
        cross_points = cross_hist[cross_hist == True]
        if cross_points.empty:
            rise_from_last_white_cross_pct.append(pd.NA)
        else:
            cross_idx = cross_points.index[-1]
            cross_loc = df.index.get_loc(cross_idx)
            base_close = close.iloc[cross_loc]
            if pd.notna(base_close) and base_close != 0 and pd.notna(close.iloc[i]):
                rise_from_last_white_cross_pct.append((close.iloc[i] / base_close - 1) * 100)
            else:
                rise_from_last_white_cross_pct.append(pd.NA)

        recent5 = df.iloc[max(0, i - 4):i+1]
        if len(recent5) >= 3:
            low_min = pd.to_numeric(recent5["low"], errors="coerce").min()
            high_max = pd.to_numeric(recent5["high"], errors="coerce").max()
            if pd.notna(low_min) and low_min != 0 and pd.notna(high_max):
                range_pct = ((high_max - low_min) / low_min) * 100
            else:
                range_pct = pd.NA
            vol_series = pd.to_numeric(recent5["volume"], errors="coerce")
            avg_vol_ratio = (vol_series / vol_series.shift(1)).mean()
            rise_pct = rise_from_last_white_cross_pct[-1]
            high_volume_sideways_after_big_run.append(bool(
                pd.notna(range_pct) and range_pct <= 8 and
                pd.notna(avg_vol_ratio) and avg_vol_ratio >= 1.08 and
                pd.notna(rise_pct) and rise_pct >= 80
            ))
        else:
            high_volume_sideways_after_big_run.append(False)

        hist20 = df.iloc[max(0, i - 19):i+1]
        hist10 = df.iloc[max(0, i - 9):i+1]
        hist15 = df.iloc[max(0, i - 14):i+1]
        hist8 = df.iloc[max(0, i - 7):i+1]

        close_now = close.iloc[i] if i < len(close) else pd.NA
        high_now = high.iloc[i] if i < len(high) else pd.NA
        low_now = low.iloc[i] if i < len(low) else pd.NA
        open_now = open_.iloc[i] if i < len(open_) else pd.NA
        pct_now = pct_change.iloc[i] if i < len(pct_change) else pd.NA
        vol_ratio_now = volume_ratio.iloc[i] if i < len(volume_ratio) else pd.NA
        upper_shadow_now = upper_shadow_ratio.iloc[i] if i < len(upper_shadow_ratio) else pd.NA
        body_pct_now = real_body_pct.iloc[i] if i < len(real_body_pct) else pd.NA

        # 1) 加速后单日放天量大阴线（S1）
        if len(hist20) >= 8:
            base_close_8 = close.iloc[max(0, i - 7)]
            accel_pct_8 = ((close_now / base_close_8 - 1) * 100) if pd.notna(base_close_8) and base_close_8 != 0 and pd.notna(close_now) else pd.NA
            prev10_vol_mean = pd.to_numeric(hist20["volume"].iloc[:-1], errors="coerce").tail(10).mean() if len(hist20) >= 6 else pd.NA
            recent20_max_vol = pd.to_numeric(hist20["volume"], errors="coerce").max()
            is_climax_bear = bool(
                bearish.iloc[i] if pd.notna(bearish.iloc[i]) else False
            ) and bool(
                pd.notna(pct_now) and pct_now <= -5.0
            ) and bool(
                pd.notna(accel_pct_8) and accel_pct_8 >= 15
            ) and bool(
                pd.notna(volume.iloc[i]) and pd.notna(prev10_vol_mean) and prev10_vol_mean > 0 and volume.iloc[i] >= prev10_vol_mean * 1.5
            ) and bool(
                pd.notna(volume.iloc[i]) and pd.notna(recent20_max_vol) and volume.iloc[i] >= recent20_max_vol * 0.95
            )
            climax_bear_after_acceleration.append(is_climax_bear)
        else:
            climax_bear_after_acceleration.append(False)

        # 2) 加速后次高点突然巨量长阴（S2）
        if len(hist10) >= 6:
            prev5 = hist10.iloc[:-1].tail(5)
            prev_high = pd.to_numeric(prev5["high"], errors="coerce").max()
            prev_high_day = prev5[pd.to_numeric(prev5["high"], errors="coerce") == prev_high].tail(1)
            prev_high_vol_ratio = pd.to_numeric(prev_high_day["attack_bar_volume_ratio"], errors="coerce").iloc[0] if not prev_high_day.empty and "attack_bar_volume_ratio" in prev_high_day else pd.NA
            prev_high_pct = pd.to_numeric(prev_high_day["pct_change"], errors="coerce").iloc[0] if not prev_high_day.empty else pd.NA
            high_rank = hist10["high"].rank(method="dense", ascending=False).iloc[-1] if len(hist10) >= 2 else pd.NA
            is_secondary_top = bool(
                bearish.iloc[i] if pd.notna(bearish.iloc[i]) else False
            ) and bool(
                pd.notna(pct_now) and pct_now <= -7.0
            ) and bool(
                pd.notna(vol_ratio_now) and vol_ratio_now >= 1.8
            ) and bool(
                pd.notna(high_now) and pd.notna(prev_high) and high_now >= prev_high * 0.975
            ) and bool(
                pd.notna(high_rank) and high_rank <= 2
            ) and bool(
                pd.notna(prev_high_vol_ratio) and prev_high_vol_ratio <= 1.1
            ) and bool(
                pd.notna(prev_high_pct) and prev_high_pct >= 0
            )
            secondary_top_huge_bear.append(is_secondary_top)
        else:
            secondary_top_huge_bear.append(False)

        # 3) 新高后连续阶梯放量下跌（S3）
        if len(hist15) >= 8:
            last8 = hist15.iloc[-8:]
            highs8 = pd.to_numeric(last8["high"], errors="coerce")
            closes8 = pd.to_numeric(last8["close"], errors="coerce")
            vols8 = pd.to_numeric(last8["volume"], errors="coerce")
            pcts6 = pd.to_numeric(last8["pct_change"].tail(6), errors="coerce")
            new_high_loc = highs8.idxmax() if not highs8.isna().all() else None
            after_new_high = last8.loc[new_high_loc:] if new_high_loc is not None else last8.iloc[0:0]
            down_days = int((pd.to_numeric(after_new_high["pct_change"], errors="coerce") < 0).fillna(False).sum()) if not after_new_high.empty else 0
            non_positive_days = int((pd.to_numeric(after_new_high["pct_change"], errors="coerce") <= 1.0).fillna(False).sum()) if not after_new_high.empty else 0
            vol_after = pd.to_numeric(after_new_high["volume"], errors="coerce") if not after_new_high.empty else pd.Series(dtype=float)
            vol_stair = _max_consecutive_true((vol_after.pct_change() >= 0.03).fillna(False).tolist()) >= 2 if len(vol_after) >= 3 else False
            weak_rebound = int((pd.to_numeric(after_new_high["pct_change"], errors="coerce") > 2.0).fillna(False).sum()) == 0 if not after_new_high.empty else False
            close_drop = ((closes8.iloc[-1] / closes8.iloc[0] - 1) * 100) if len(closes8) >= 2 and pd.notna(closes8.iloc[0]) and closes8.iloc[0] != 0 and pd.notna(closes8.iloc[-1]) else pd.NA
            stair_down_after_new_high.append(bool(
                new_high_loc is not None and len(after_new_high) >= 4 and
                down_days >= 3 and non_positive_days >= max(3, len(after_new_high) - 1) and
                pd.notna(close_drop) and close_drop <= -6 and
                vol_stair and weak_rebound
            ))
        else:
            stair_down_after_new_high.append(False)

        # 4) 双头双放量巨阴（S4）
        if len(hist20) >= 12:
            highs20 = pd.to_numeric(hist20["high"], errors="coerce")
            vols20 = pd.to_numeric(hist20["volume"], errors="coerce")
            pct20 = pd.to_numeric(hist20["pct_change"], errors="coerce")
            top_threshold = highs20.max() * 0.975 if pd.notna(highs20.max()) else pd.NA
            top_bear_mask = (
                (highs20 >= top_threshold) &
                (pct20 <= -4.5) &
                ((vols20 / vols20.shift(1)) >= 1.5).fillna(False)
            ) if pd.notna(top_threshold) else pd.Series([False] * len(hist20), index=hist20.index)
            top_bear_idxs = list(hist20.index[top_bear_mask])
            separated = False
            if len(top_bear_idxs) >= 2:
                for a, b in zip(top_bear_idxs[:-1], top_bear_idxs[1:]):
                    if df.index.get_loc(b) - df.index.get_loc(a) >= 4:
                        separated = True
                        break
            double_top_double_distribution.append(bool(len(top_bear_idxs) >= 2 and separated))
        else:
            double_top_double_distribution.append(False)

        # 5) 顶部绿长红短（绿肥红瘦，S5）
        if len(hist15) >= 8:
            zone = hist15.tail(10)
            pct_zone = pd.to_numeric(zone["pct_change"], errors="coerce")
            bear_zone = zone[pct_zone < 0]
            bull_zone = zone[pct_zone > 0]
            bear_body = (pd.to_numeric(bear_zone["open"], errors="coerce") - pd.to_numeric(bear_zone["close"], errors="coerce")).abs()
            bull_body = (pd.to_numeric(bull_zone["close"], errors="coerce") - pd.to_numeric(bull_zone["open"], errors="coerce")).abs()
            bear_vol_mean = pd.to_numeric(bear_zone["volume"], errors="coerce").mean() if len(bear_zone) > 0 else pd.NA
            bull_vol_mean = pd.to_numeric(bull_zone["volume"], errors="coerce").mean() if len(bull_zone) > 0 else pd.NA
            bear_body_mean = bear_body.mean() if len(bear_body) > 0 else pd.NA
            bull_body_mean = bull_body.mean() if len(bull_body) > 0 else pd.NA
            top_zone = bool(pd.notna(high_now) and pd.notna(pd.to_numeric(hist20["high"], errors="coerce").max()) and high_now >= pd.to_numeric(hist20["high"], errors="coerce").max() * 0.94) if len(hist20) >= 5 else False
            top_green_long_red_short.append(bool(
                top_zone and len(bear_zone) >= 4 and len(bull_zone) >= 2 and
                pd.notna(bear_body_mean) and pd.notna(bull_body_mean) and bear_body_mean >= bull_body_mean * 1.35 and
                pd.notna(bear_vol_mean) and pd.notna(bull_vol_mean) and bear_vol_mean >= bull_vol_mean * 1.15
            ))
        else:
            top_green_long_red_short.append(False)

        # 6) 顶部冲高爆量反转（按中材科技 2025-08-29 这类案例优化）
        if len(hist20) >= 8:
            recent20_high = pd.to_numeric(hist20["high"], errors="coerce").max()
            recent10_high = pd.to_numeric(hist10["high"], errors="coerce").max() if len(hist10) >= 3 else pd.NA
            day_range_pct = ((high_now - low_now) / low_now * 100) if pd.notna(high_now) and pd.notna(low_now) and low_now != 0 else pd.NA
            close_pos_in_range = ((close_now - low_now) / (high_now - low_now)) if pd.notna(close_now) and pd.notna(low_now) and pd.notna(high_now) and (high_now - low_now) != 0 else pd.NA
            upper_shadow_body_ratio = (upper_shadow.iloc[i] / real_body.iloc[i]) if pd.notna(upper_shadow.iloc[i]) and pd.notna(real_body.iloc[i]) and real_body.iloc[i] != 0 else pd.NA
            accel_base_close = close.iloc[max(0, i - 6)]
            accel_pct_7 = ((close_now / accel_base_close - 1) * 100) if pd.notna(accel_base_close) and accel_base_close != 0 and pd.notna(close_now) else pd.NA
            top_blowoff_reversal.append(bool(
                pd.notna(high_now) and pd.notna(recent20_high) and high_now >= recent20_high * 0.995 and
                pd.notna(vol_ratio_now) and vol_ratio_now >= 1.8 and
                pd.notna(day_range_pct) and day_range_pct >= 8.0 and
                pd.notna(close_pos_in_range) and close_pos_in_range <= 0.42 and
                pd.notna(accel_pct_7) and accel_pct_7 >= 12 and
                (
                    (pd.notna(upper_shadow_now) and upper_shadow_now >= 0.28) or
                    (pd.notna(upper_shadow_body_ratio) and upper_shadow_body_ratio >= 1.0) or
                    (pd.notna(pct_now) and pct_now <= -2.0)
                )
            ))
        else:
            top_blowoff_reversal.append(False)

        # 7) 最高点放巨量，随后连续两天跌破黄线并不断创新低（按三全食品反馈补）
        if i >= 2 and "yellow_line" in df.columns:
            peak_idx = hist20["high"].astype(float).idxmax() if len(hist20) >= 3 and not pd.to_numeric(hist20["high"], errors="coerce").isna().all() else None
            if peak_idx is not None and df.index.get_loc(peak_idx) <= i - 2:
                peak_loc = df.index.get_loc(peak_idx)
                peak_vol = volume.iloc[peak_loc] if peak_loc < len(volume) else pd.NA
                prev10_peak_vol_mean = pd.to_numeric(df.iloc[max(0, peak_loc - 10):peak_loc]["volume"], errors="coerce").mean() if peak_loc >= 1 else pd.NA
                yellow_1 = pd.to_numeric(df.get("yellow_line"), errors="coerce").iloc[i-1] if i-1 >= 0 else pd.NA
                yellow_2 = pd.to_numeric(df.get("yellow_line"), errors="coerce").iloc[i] if i >= 0 else pd.NA
                low_1 = low.iloc[i-1] if i-1 >= 0 else pd.NA
                low_2 = low.iloc[i] if i >= 0 else pd.NA
                close_1 = close.iloc[i-1] if i-1 >= 0 else pd.NA
                close_2 = close.iloc[i] if i >= 0 else pd.NA
                peak_huge_volume_break_yellow_2d.append(bool(
                    pd.notna(peak_vol) and pd.notna(prev10_peak_vol_mean) and prev10_peak_vol_mean > 0 and peak_vol >= prev10_peak_vol_mean * 1.5 and
                    pd.notna(close_1) and pd.notna(yellow_1) and close_1 < yellow_1 and
                    pd.notna(close_2) and pd.notna(yellow_2) and close_2 < yellow_2 and
                    pd.notna(low_1) and pd.notna(low_2) and low_2 < low_1
                ))
            else:
                peak_huge_volume_break_yellow_2d.append(False)
        else:
            peak_huge_volume_break_yellow_2d.append(False)

        # 8) 顶部开始连续3天放大量阶梯量（按日月股份反馈补）
        if i >= 2:
            recent3_high = pd.to_numeric(df.iloc[max(0, i-2):i+1]["high"], errors="coerce")
            recent3_vol = pd.to_numeric(df.iloc[max(0, i-2):i+1]["volume"], errors="coerce")
            recent3_close = pd.to_numeric(df.iloc[max(0, i-2):i+1]["close"], errors="coerce")
            top20_high = pd.to_numeric(hist20["high"], errors="coerce").max() if len(hist20) >= 5 else pd.NA
            prev10_vol_mean = pd.to_numeric(hist20["volume"].iloc[:-3], errors="coerce").tail(10).mean() if len(hist20) >= 8 else pd.NA
            top_3day_stair_volume_distribution.append(bool(
                len(recent3_vol) == 3 and
                pd.notna(top20_high) and pd.notna(recent3_high.max()) and recent3_high.max() >= top20_high * 0.97 and
                pd.notna(prev10_vol_mean) and prev10_vol_mean > 0 and (recent3_vol >= prev10_vol_mean * 1.2).fillna(False).sum() >= 2 and
                pd.notna(recent3_vol.iloc[0]) and pd.notna(recent3_vol.iloc[1]) and pd.notna(recent3_vol.iloc[2]) and recent3_vol.iloc[2] >= recent3_vol.iloc[1] >= recent3_vol.iloc[0] and
                pd.notna(recent3_close.iloc[0]) and pd.notna(recent3_close.iloc[2]) and recent3_close.iloc[2] <= recent3_close.iloc[0]
            ))
        else:
            top_3day_stair_volume_distribution.append(False)

        # 9) 上方供给：前高压制仍近，当前位置距离前高不远但尚未解放
        if len(hist20) >= 8:
            prev_high_20 = pd.to_numeric(hist20["high"].iloc[:-1], errors="coerce").max() if len(hist20) >= 2 else pd.NA
            dist_to_prev_high_pct = ((prev_high_20 - close_now) / close_now * 100) if pd.notna(prev_high_20) and pd.notna(close_now) and close_now != 0 else pd.NA
            overhead_supply_near_prev_high.append(bool(
                pd.notna(prev_high_20) and pd.notna(close_now) and close_now < prev_high_20 and
                pd.notna(dist_to_prev_high_pct) and 0 <= dist_to_prev_high_pct <= 6
            ))
        else:
            overhead_supply_near_prev_high.append(False)

        # 10) 上方供给：假突破后回落，突破高点未站稳
        if len(hist20) >= 10:
            recent10 = hist20.tail(10)
            top_idx = pd.to_numeric(recent10["high"], errors="coerce").idxmax() if not pd.to_numeric(recent10["high"], errors="coerce").isna().all() else None
            if top_idx is not None:
                top_loc = df.index.get_loc(top_idx)
                top_close = close.iloc[top_loc] if top_loc < len(close) else pd.NA
                top_vol = volume.iloc[top_loc] if top_loc < len(volume) else pd.NA
                prev_vol_mean = pd.to_numeric(df.iloc[max(0, top_loc - 10):top_loc]["volume"], errors="coerce").mean() if top_loc >= 1 else pd.NA
                failed_breakout_overhead_supply.append(bool(
                    top_loc <= i and i - top_loc <= 8 and
                    pd.notna(high.iloc[top_loc]) and pd.notna(close_now) and close_now <= high.iloc[top_loc] * 0.97 and
                    pd.notna(top_vol) and pd.notna(prev_vol_mean) and prev_vol_mean > 0 and top_vol >= prev_vol_mean * 1.3
                ))
            else:
                failed_breakout_overhead_supply.append(False)
        else:
            failed_breakout_overhead_supply.append(False)

        # 11) 上方供给：高位密集成交区仍压在头顶附近
        if len(hist20) >= 10:
            upper_band_start = pd.to_numeric(hist20["close"], errors="coerce").quantile(0.75)
            upper_band_end = pd.to_numeric(hist20["high"], errors="coerce").max()
            band_rows = hist20[(pd.to_numeric(hist20["close"], errors="coerce") >= upper_band_start)] if pd.notna(upper_band_start) else hist20.iloc[0:0]
            band_vol = pd.to_numeric(band_rows["volume"], errors="coerce").sum() if not band_rows.empty else 0
            total_vol = pd.to_numeric(hist20["volume"], errors="coerce").sum()
            dist_to_band_start_pct = ((upper_band_start - close_now) / close_now * 100) if pd.notna(upper_band_start) and pd.notna(close_now) and close_now != 0 else pd.NA
            overhead_heavy_volume_band.append(bool(
                pd.notna(total_vol) and total_vol > 0 and band_vol / total_vol >= 0.38 and
                pd.notna(dist_to_band_start_pct) and -1.5 <= dist_to_band_start_pct <= 5.5 and
                pd.notna(close_now) and pd.notna(upper_band_end) and close_now <= upper_band_end
            ))
        else:
            overhead_heavy_volume_band.append(False)

        # 12) 跌破黄线第二天仍未收回，强度明显不够
        if i >= 2 and "yellow_line" in df.columns:
            yellow_series = pd.to_numeric(df.get("yellow_line"), errors="coerce")
            close_d2 = close.iloc[i-2] if i-2 >= 0 else pd.NA
            close_d1 = close.iloc[i-1] if i-1 >= 0 else pd.NA
            close_d0 = close.iloc[i] if i >= 0 else pd.NA
            yellow_d2 = yellow_series.iloc[i-2] if i-2 >= 0 else pd.NA
            yellow_d1 = yellow_series.iloc[i-1] if i-1 >= 0 else pd.NA
            yellow_d0 = yellow_series.iloc[i] if i >= 0 else pd.NA
            failed_reclaim_yellow_on_day2.append(bool(
                pd.notna(close_d2) and pd.notna(yellow_d2) and close_d2 >= yellow_d2 and
                pd.notna(close_d1) and pd.notna(yellow_d1) and close_d1 < yellow_d1 and
                pd.notna(close_d0) and pd.notna(yellow_d0) and close_d0 < yellow_d0
            ))
        else:
            failed_reclaim_yellow_on_day2.append(False)

        # 13) 供给吸收突破：巨量涨停/强攻击K显著打入前期大阴线实体内部，视为主力主动承接头顶供给
        if len(hist30 := df.iloc[max(0, i - 79):i+1]) >= 15:
            top_bear_candidates = hist30[
                (pd.to_numeric(hist30["pct_change"], errors="coerce") <= -4.5) &
                ((pd.to_numeric(hist30["volume"], errors="coerce") / pd.to_numeric(hist30["volume"], errors="coerce").shift(1)) >= 1.1).fillna(False)
            ]
            if not top_bear_candidates.empty:
                last_bear_idx = top_bear_candidates.index[-1]
                bear_loc = df.index.get_loc(last_bear_idx)
                bear_open = open_.iloc[bear_loc] if bear_loc < len(open_) else pd.NA
                bear_close = close.iloc[bear_loc] if bear_loc < len(close) else pd.NA
                bear_body_top = max(bear_open, bear_close) if pd.notna(bear_open) and pd.notna(bear_close) else pd.NA
                bear_body_bottom = min(bear_open, bear_close) if pd.notna(bear_open) and pd.notna(bear_close) else pd.NA
                after_bear = df.iloc[bear_loc+1:i+1] if bear_loc + 1 <= i else df.iloc[0:0]
                if not after_bear.empty:
                    attack_candidates = after_bear[
                        (pd.to_numeric(after_bear.get("pct_change"), errors="coerce") >= 9.0) |
                        (
                            (after_bear.get("strong_attack_bar", False) == True) &
                            (pd.to_numeric(after_bear.get("attack_bar_volume_ratio"), errors="coerce") >= 1.8)
                        )
                    ]
                    absorbed = False
                    for attack_idx in attack_candidates.index:
                        attack_loc = df.index.get_loc(attack_idx)
                        attack_vol = volume.iloc[attack_loc] if attack_loc < len(volume) else pd.NA
                        attack_close = close.iloc[attack_loc] if attack_loc < len(close) else pd.NA
                        attack_high = high.iloc[attack_loc] if attack_loc < len(high) else pd.NA
                        prev_supply_vol_max = pd.to_numeric(df.iloc[max(0, bear_loc - 10):bear_loc+1]["volume"], errors="coerce").max()
                        entered_bear_body = bool(
                            pd.notna(attack_high) and pd.notna(bear_body_bottom) and attack_high >= bear_body_bottom * 1.01
                        )
                        strong_cover_volume = bool(
                            pd.notna(attack_vol) and pd.notna(prev_supply_vol_max) and attack_vol >= prev_supply_vol_max * 1.2
                        )
                        close_inside_body = bool(
                            pd.notna(attack_close) and pd.notna(bear_body_bottom) and pd.notna(bear_body_top) and
                            attack_close >= bear_body_bottom * 0.995 and attack_close <= bear_body_top * 1.03
                        )
                        if entered_bear_body and strong_cover_volume and (close_inside_body or pd.notna(attack_close) and pd.notna(bear_body_bottom) and attack_close >= bear_body_bottom):
                            absorbed = True
                            break
                    supply_absorption_breakthrough.append(absorbed)
                else:
                    supply_absorption_breakthrough.append(False)
            else:
                supply_absorption_breakthrough.append(False)
        else:
            supply_absorption_breakthrough.append(False)

        # 14) 连续两个涨停后高位大分歧震荡，且出现超大振幅，不够像干净B1（按600084反馈补）
        if len(hist15) >= 10:
            pct15 = pd.to_numeric(hist15["pct_change"], errors="coerce")
            limit_up_like = pct15 >= 9.7
            limit_positions = [idx for idx, flag in zip(hist15.index.tolist(), limit_up_like.fillna(False).tolist()) if flag]
            triggered = False
            if len(limit_positions) >= 2:
                for a, b in zip(limit_positions[:-1], limit_positions[1:]):
                    if df.index.get_loc(b) - df.index.get_loc(a) == 1:
                        b_loc = df.index.get_loc(b)
                        post = df.iloc[b_loc:min(len(df), b_loc + 8)].copy()
                        if len(post) >= 3:
                            post_amp = pd.to_numeric(post.get("amplitude_pct"), errors="coerce")
                            post_close = pd.to_numeric(post["close"], errors="coerce")
                            second_limit_close = close.iloc[b_loc] if b_loc < len(close) else pd.NA
                            high_zone_hold = bool(
                                pd.notna(second_limit_close) and len(post_close) >= 3 and post_close.min() >= second_limit_close * 0.90
                            )
                            huge_intraday_volatility = bool((post_amp >= 10.0).fillna(False).any())
                            if high_zone_hold and huge_intraday_volatility:
                                triggered = True
                                break
            double_limit_then_high_volatility_sideways.append(triggered)
        else:
            double_limit_then_high_volatility_sideways.append(False)

        recent_distribution_flags = [
            climax_bear_after_acceleration[-1],
            secondary_top_huge_bear[-1],
            stair_down_after_new_high[-1],
            double_top_double_distribution[-1],
            top_green_long_red_short[-1],
            top_blowoff_reversal[-1],
            peak_huge_volume_break_yellow_2d[-1],
            top_3day_stair_volume_distribution[-1],
        ]
        hist_dist_start = max(0, i - 19)
        dist_count = 0
        for j in range(hist_dist_start, i + 1):
            flags_j = [
                climax_bear_after_acceleration[j],
                secondary_top_huge_bear[j],
                stair_down_after_new_high[j],
                double_top_double_distribution[j],
                top_green_long_red_short[j],
                top_blowoff_reversal[j],
                peak_huge_volume_break_yellow_2d[j],
                top_3day_stair_volume_distribution[j],
            ]
            if any(flags_j):
                dist_count += 1
        recent_distribution_count_1m.append(dist_count)
        recent_distribution_within_1m.append(dist_count > 0)

    df["strong_attack_bar_count_30d"] = strong_attack_count
    df["weak_attack_upper_shadow_count_30d"] = weak_attack_count
    df["building_wave_quality_score"] = building_wave_quality_score
    df["recent_attack_bar_exists"] = recent_attack_exists
    df["recent_attack_bar_age"] = recent_attack_age
    df["recent_attack_bar_is_strong"] = recent_attack_is_strong
    df["recent_attack_bar_upper_shadow_ratio"] = recent_attack_upper_shadow_ratio
    df["recent_attack_bar_real_body_pct"] = recent_attack_real_body_pct
    df["recent_attack_bar_volume_ratio"] = recent_attack_volume_ratio

    df["recent_gap_attack_exists"] = recent_gap_attack_exists
    df["recent_gap_attack_age"] = recent_gap_attack_age
    df["recent_gap_attack_low"] = recent_gap_attack_low
    df["broke_recent_gap_attack_low"] = broke_recent_gap_attack_low

    df["recent_bearish_reversal_exists"] = recent_bearish_reversal_exists
    df["recent_bearish_reversal_age"] = recent_bearish_reversal_age

    df["pullback_heavy_volume_count_5d"] = pullback_heavy_volume_count_5d
    df["pullback_heavy_volume_max_consecutive_5d"] = pullback_heavy_volume_max_consecutive_5d
    df["heavy_bear_count_10d"] = heavy_bear_count_10d
    df["max_consecutive_heavy_bear_10d"] = max_consecutive_heavy_bear_10d
    df["double_volume_bull_count_30d"] = double_volume_bull_count_30d
    df["max_bear_volume_last_10d_vs_recent_attack_ratio"] = max_bear_volume_last_10d_vs_recent_attack_ratio
    df["drawdown_from_post_cross_high_pct"] = drawdown_from_post_cross_high_pct
    df["vertical_decline_with_heavy_volume"] = vertical_decline_with_heavy_volume
    df["rise_from_last_white_cross_pct"] = rise_from_last_white_cross_pct
    df["high_volume_sideways_after_big_run"] = high_volume_sideways_after_big_run

    df["climax_bear_after_acceleration"] = climax_bear_after_acceleration
    df["secondary_top_huge_bear"] = secondary_top_huge_bear
    df["stair_down_after_new_high"] = stair_down_after_new_high
    df["double_top_double_distribution"] = double_top_double_distribution
    df["top_green_long_red_short"] = top_green_long_red_short
    df["top_blowoff_reversal"] = top_blowoff_reversal
    df["peak_huge_volume_break_yellow_2d"] = peak_huge_volume_break_yellow_2d
    df["top_3day_stair_volume_distribution"] = top_3day_stair_volume_distribution
    df["overhead_supply_near_prev_high"] = overhead_supply_near_prev_high
    df["failed_breakout_overhead_supply"] = failed_breakout_overhead_supply
    df["overhead_heavy_volume_band"] = overhead_heavy_volume_band
    df["failed_reclaim_yellow_on_day2"] = failed_reclaim_yellow_on_day2
    df["supply_absorption_breakthrough"] = supply_absorption_breakthrough
    df["double_limit_then_high_volatility_sideways"] = double_limit_then_high_volatility_sideways
    df["recent_distribution_within_1m"] = recent_distribution_within_1m
    df["recent_distribution_count_1m"] = recent_distribution_count_1m

    df["building_wave_has_quality_attack"] = (
        (pd.to_numeric(df["strong_attack_bar_count_30d"], errors="coerce") >= 1) |
        (df["recent_attack_bar_is_strong"] == True)
    ).fillna(False)
    df["building_wave_upper_shadow_heavy"] = (
        pd.to_numeric(df["weak_attack_upper_shadow_count_30d"], errors="coerce") >= 2
    ).fillna(False)

    return df
