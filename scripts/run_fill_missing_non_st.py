import sys
from pathlib import Path
import glob
import os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.fetch_pipeline import run_fetch_pipeline
from src.pipeline.preprocess_pipeline import run_preprocess_pipeline
from src.common.io_utils import write_json
from src.common.paths import RAW_DIR, PROCESSED_DIR

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
    missing = load_missing_non_st()
    report = {
        'initial_missing': len(missing),
        'batch_size': BATCH_SIZE,
        'batches': []
    }
    print(f'initial_missing={len(missing)}')
    for idx, batch in enumerate(batched(missing, BATCH_SIZE), start=1):
        print(f'=== batch {idx} size={len(batch)} ===')
        run_fetch_pipeline(config_name='fetch.yaml', codes=batch)
        ok = 0
        fail = []
        for code in batch:
            daily_file = RAW_DIR / 'daily' / f'{code}.csv'
            if daily_file.exists():
                run_preprocess_pipeline(config_name='b1_rules.yaml', code=code)
                out_file = PROCESSED_DIR / f'{code}.csv'
                if out_file.exists():
                    ok += 1
                else:
                    fail.append(code)
            else:
                fail.append(code)
        report['batches'].append({'batch': idx, 'requested': len(batch), 'ok': ok, 'fail': fail})
        write_json(ROOT / 'data' / 'fill_missing_non_st_progress.json', report)
        print(f'batch_done idx={idx} ok={ok} fail={len(fail)}')
    final_missing = load_missing_non_st()
    report['final_missing'] = len(final_missing)
    report['final_missing_sample'] = final_missing[:100]
    write_json(ROOT / 'data' / 'fill_missing_non_st_progress.json', report)
    print(f'final_missing={len(final_missing)}')


if __name__ == '__main__':
    main()
