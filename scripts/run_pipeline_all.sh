#!/bin/bash

set -ex

usage() {
    echo "Usage: $0 --date YYYY-MM-DD"
    exit 1
}

DATE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --date)
            DATE="$2"
            shift 2
            ;;
        *)
            usage
            ;;
    esac
done

if [ -z "$DATE" ]; then
    usage
fi

if [ -z "$TUSHARE_TOKEN" ]; then
    echo "Error: TUSHARE_TOKEN environment variable is not set."
    echo "Please set it before running this script:"
    echo "  export TUSHARE_TOKEN=your_token_here"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=== Step 1: Fetch data ==="
uv run scripts/run_fetch.py --end-date "$DATE"

echo "=== Step 2: Preprocess (light stage) ==="
uv run scripts/run_preprocess.py --stage light --date "$DATE"

echo "=== Step 3: Preprocess (full stage) ==="
uv run scripts/run_preprocess.py --stage full --codes-from "./data/light_candidates/light_candidates_${DATE}.json"

echo "=== Step 4: Preselect ==="
uv run scripts/run_preselect.py --date "$DATE"

echo "=== Step 5: Export charts ==="
uv run scripts/run_export_charts.py --date "$DATE"

echo "=== Step 6: Review ==="
uv run scripts/run_review.py --date "$DATE"

echo "=== Pipeline completed for $DATE ==="
