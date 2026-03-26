# B1 Pipeline

A-share B1 semi-automatic stock-selection pipeline.

This project focuses on turning the daily B1 workflow into a reproducible pipeline:

1. fetch daily market data
2. preprocess indicators and structure features
3. run a first-pass candidate filter
4. export review charts and review inputs
5. score and rank candidates
6. produce a final shortlist for manual decision-making

## Current scope

Current pipeline stages are already connected end-to-end:

- fetch
- preprocess
- preselect
- export_charts
- review

Important note:

- `white_line / yellow_line` is currently an MVP approximation, not the final Tongdaxin formula implementation.
- The current rules and scoring logic have been calibrated using user-confirmed B1 reference samples.
- The current engineering objective is **not fully automatic trading**. It is a **semi-automatic ranking and review system** that helps produce a strong daily shortlist.

## Repository structure

```text
b1_pipeline/
├─ config/          # strategy and pipeline config
├─ scripts/         # runnable entry scripts
├─ src/             # core pipeline code
├─ tests/           # unit tests
├─ data/            # local-only data directory (ignored by git)
├─ logs/            # local logs (ignored by git)
└─ README.md
```

## Quick start

### 1. Create environment

Recommended: Python 3.11+

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Tushare token

This project expects your Tushare token from an environment variable.

**Windows PowerShell**

```powershell
$env:TUSHARE_TOKEN="your_token_here"
```

**macOS / Linux**

```bash
export TUSHARE_TOKEN="your_token_here"
```

You can also keep a local private config, but do **not** commit real tokens into Git.

### 3. Daily workflow

Recommended daily path after the 2026-03-25 refactor:

```bash
py scripts/run_fetch.py --end-date YYYY-MM-DD
py scripts/run_preprocess.py --stage light --date YYYY-MM-DD
py scripts/run_preprocess.py --stage full --codes-from .\data\light_candidates\light_candidates_YYYY-MM-DD.json
py scripts/run_preselect.py --date YYYY-MM-DD
py scripts/run_export_charts.py --date YYYY-MM-DD
py scripts/run_review.py --date YYYY-MM-DD
```

## Fetch modes

```bash
py scripts/run_fetch.py --mode incremental --end-date YYYY-MM-DD
py scripts/run_fetch.py --mode full --start-date 2025-01-01 --end-date YYYY-MM-DD
```

Notes:

- `incremental` is the default mode and should be the normal daily path.
- `full` is for repair / backfill / debugging, not daily use.
- Incremental mode checks the latest local `trade_date` first and only fetches missing ranges.

## Current light gate

Current first-pass light filter:

- `J < 20`
- `white_line > yellow_line`
- `close >= yellow_line * 0.9`

This keeps the full-market first pass lighter, then runs heavy full preprocessing only on filtered candidates.

## Current strategy direction

### Preselect layer

The preselect layer is designed to avoid missing strong B1 names too early.

So the pipeline intentionally avoids overly strict hard filters such as:

- forcing `white_above_yellow = true` in every case
- forcing `close_above_yellow = true`
- forcing `is_10d_min_volume = true`

This is based on real reference samples showing that good B1 setups can appear:

- above the white/yellow lines
- between the white and yellow lines
- near white-line support or yellow-line support
- after a shallow break and fast stabilization
- in time-for-space consolidations with low volatility and fast J reset

### Review layer

The review/scoring layer currently pays more attention to:

- low J values, especially deeply negative J
- mild daily fluctuation and moderate close change
- white/yellow position and distance
- whether close is between the white/yellow lines or near support
- shrinking volume behavior
- time-for-space / sideways digestion / small-candle pullback style

## Practical notes

### 1. Working directory matters

Some scripts use project-relative paths. Run them from the project root to avoid writing files into the wrong `data/` directory.

### 2. `market_cap.csv` should remain a full-market snapshot

Historically, subset fetches could overwrite `data/raw/market_cap.csv` and break later filtering with missing market cap values.

Current behavior:

- subset fetches (`--codes` / `--limit`) skip rewriting `market_cap.csv`
- full-market daily runs can refresh the market-cap snapshot normally

## Security note

- Do **not** commit real API tokens.
- `data/` and `logs/` are intentionally ignored by git.
- If you previously committed a real token, rotate it before making the repository public or sharing access broadly.

## Tests

Example:

```bash
pytest tests
```

## Project status

This repository is still an evolving research/engineering project.

The current objective is to improve shortlist quality and front-of-list realism, so the final top 10 candidates better match real manual trading preference order.
