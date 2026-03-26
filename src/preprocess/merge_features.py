from src.common.config_loader import load_config
from src.indicators.kdj import calc_kdj
from src.indicators.zhixing_lines import calc_zhixing_lines
from src.indicators.volume_features import add_volume_features
from src.indicators.price_features import add_price_features
from src.indicators.key_k import add_key_k_features
from src.indicators.building_wave import add_building_wave_features


def build_light_processed_df(df, rules_config: dict | None = None):
    df = df.copy()
    rules = rules_config or load_config("b1_rules.yaml")
    trend_rules = rules.get("trend_rules", {})

    white_ema_span_1 = int(trend_rules.get("white_ema_span_1", 10))
    white_ema_span_2 = int(trend_rules.get("white_ema_span_2", 10))
    yellow_ma_1 = int(trend_rules.get("yellow_ma_1", 14))
    yellow_ma_2 = int(trend_rules.get("yellow_ma_2", 28))
    yellow_ma_3 = int(trend_rules.get("yellow_ma_3", 57))
    yellow_ma_4 = int(trend_rules.get("yellow_ma_4", 114))
    cross_lookback_days = int(trend_rules.get("recent_cross_lookback_days", 5))

    df = calc_kdj(df)
    df = calc_zhixing_lines(
        df,
        white_ema_span_1=white_ema_span_1,
        white_ema_span_2=white_ema_span_2,
        yellow_ma_1=yellow_ma_1,
        yellow_ma_2=yellow_ma_2,
        yellow_ma_3=yellow_ma_3,
        yellow_ma_4=yellow_ma_4,
        cross_lookback_days=cross_lookback_days,
    )
    df = add_volume_features(df)
    df = add_price_features(df)
    return df


def build_processed_df(df, rules_config: dict | None = None):
    df = df.copy()
    rules = rules_config or load_config("b1_rules.yaml")
    key_k_rules = rules.get("key_k_rules", {})
    building_wave_rules = rules.get("building_wave_rules", {})

    df = build_light_processed_df(df, rules_config=rules)
    df = add_key_k_features(
        df,
        min_pct_change=float(key_k_rules.get("min_pct_change", 4.0)),
        volume_ratio_threshold=float(key_k_rules.get("volume_ratio_threshold", 1.5)),
        recent_lookback_days=int(key_k_rules.get("recent_lookback_days", 40)),
    )
    df = add_building_wave_features(
        df,
        lookback_days=int(building_wave_rules.get("lookback_days", 30)),
        attack_pct_min=float(building_wave_rules.get("attack_pct_min", 3.5)),
        volume_ratio_min=float(building_wave_rules.get("volume_ratio_min", 1.3)),
        strong_body_pct_min=float(building_wave_rules.get("strong_body_pct_min", 3.0)),
        upper_shadow_ratio_max=float(building_wave_rules.get("upper_shadow_ratio_max", 0.35)),
    )
    return df
