from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DAILY_DIR = RAW_DIR / "daily"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_LIGHT_DIR = DATA_DIR / "processed_light"
CANDIDATES_DIR = DATA_DIR / "candidates"
LIGHT_CANDIDATES_DIR = DATA_DIR / "light_candidates"
REVIEW_INPUT_DIR = DATA_DIR / "review_input"
CHARTS_DIR = DATA_DIR / "charts"
REVIEW_OUTPUT_DIR = DATA_DIR / "review_output"
LOGS_DIR = ROOT / "logs"


def ensure_dirs():
    for p in [
        RAW_DIR, RAW_DAILY_DIR, PROCESSED_DIR, PROCESSED_LIGHT_DIR,
        CANDIDATES_DIR, LIGHT_CANDIDATES_DIR,
        REVIEW_INPUT_DIR, CHARTS_DIR, REVIEW_OUTPUT_DIR, LOGS_DIR
    ]:
        p.mkdir(parents=True, exist_ok=True)
