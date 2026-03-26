# Development Notes

## Recommended Python version

- Python 3.11+

## Install

### Basic runtime install

```bash
pip install -r requirements.txt
```

### Editable local development install

```bash
pip install -e .
pip install pytest
```

## Local token setup

Windows PowerShell:

```powershell
$env:TUSHARE_TOKEN="your_token_here"
```

macOS / Linux:

```bash
export TUSHARE_TOKEN="your_token_here"
```

## Test commands

Run all tests:

```bash
pytest tests
```

Run a single test file:

```bash
pytest tests/test_kdj.py
```

## Typical daily workflow

```bash
py scripts/run_fetch.py --end-date YYYY-MM-DD
py scripts/run_preprocess.py --stage light --date YYYY-MM-DD
py scripts/run_preprocess.py --stage full --codes-from .\data\light_candidates\light_candidates_YYYY-MM-DD.json
py scripts/run_preselect.py --date YYYY-MM-DD
py scripts/run_export_charts.py --date YYYY-MM-DD
py scripts/run_review.py --date YYYY-MM-DD
```

## Engineering reminders

- Run scripts from the project root.
- Keep secrets out of tracked config.
- Keep `data/` and `logs/` local only.
- Prefer incremental fetch for daily work.
- Validate ranking changes with sample cases before broad claims.
