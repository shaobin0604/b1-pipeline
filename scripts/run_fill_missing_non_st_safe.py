import sys
import glob
import os
import time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.config_loader import load_config
from src.common.io_utils import write_json, write_csv
from src.common.paths import RAW_DIR, RAW_DAILY_DIR, PROCESSED_DIR
from src.data_fetch.fetch_daily import fetch_daily_for_code
from src.data_fetch.tushare_client import build_client
from src.pipeline.preprocess_pipeline import run_preprocess_pipeline

BATCH_SIZE = 100


def load_missing_non_st():
    stock_basic = pd.read_csv(RAW_DIR / 'stock_basic.csv')
    stock_basic['name'] = stock_basic['name'].fillna('').astype(str)
    non_st = set(stock_basic.loc[~stock_basic['name'].str.upper().str.contains('ST'), 'ts_code'].astype(str).str.upper())
    processed = set(Path(p).stem.upper() for p in glob.glob(str(PROCESSED_DIR / '*.csv')))
    return sorted(non_st - processed)


def batched(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]


def main():
    cfg = load_config('fetch.yaml')
    token = cfg.get('tushare', {}).get('token')
    if not token or token == 'YOUR_TUSHARE_TOKEN':
        raise ValueError('fetch.yaml 中未配置有效 tushare token')

    market_cfg = cfg.get('market', {})
    start_date = str(market_cfg.get('start_date', '')).replace('-', '')
    end_date = str(market_cfg.get('end_date', '')).replace('-', '')
    sleep_seconds = float(cfg.get('fetch_options', {}).get('sleep_seconds', 0.3))

    pro = build_client(token)
    missing = load_missing_non_st()
    report = {
        'initial_missing': len(missing),
        'batch_size': BATCH_SIZE,
        'batches': [],
    }
    print(f'initial_missing={len(missing)}')

    for idx, batch in enumerate(batched(missing, BATCH_SIZE), start=1):
        ok_fetch = 0
        ok_preprocess = 0
        fetch_fail = []
        preprocess_fail = []
        print(f'=== batch {idx} size={len(batch)} ===')
        for code in batch:
            try:
                daily = fetch_daily_for_code(pro, code, start_date=start_date, end_date=end_date)
                if daily is None or daily.empty:
                    fetch_fail.append(code)
                    continue
                write_csv(RAW_DAILY_DIR / f'{code}.csv', daily)
                ok_fetch += 1
                time.sleep(sleep_seconds)
            except Exception as e:
                fetch_fail.append(f'{code}: {e}')
                continue

            try:
                run_preprocess_pipeline(config_name='b1_rules.yaml', code=code)
                if (PROCESSED_DIR / f'{code}.csv').exists():
                    ok_preprocess += 1
                else:
                    preprocess_fail.append(code)
            except Exception as e:
                preprocess_fail.append(f'{code}: {e}')

        report['batches'].append({
            'batch': idx,
            'requested': len(batch),
            'ok_fetch': ok_fetch,
            'ok_preprocess': ok_preprocess,
            'fetch_fail': fetch_fail,
            'preprocess_fail': preprocess_fail,
        })
        write_json(ROOT / 'data' / 'fill_missing_non_st_safe_progress.json', report)
        print(f'batch_done idx={idx} ok_fetch={ok_fetch} ok_preprocess={ok_preprocess} fetch_fail={len(fetch_fail)} preprocess_fail={len(preprocess_fail)}')

    final_missing = load_missing_non_st()
    report['final_missing'] = len(final_missing)
    report['final_missing_sample'] = final_missing[:100]
    write_json(ROOT / 'data' / 'fill_missing_non_st_safe_progress.json', report)
    print(f'final_missing={len(final_missing)}')


if __name__ == '__main__':
    main()
