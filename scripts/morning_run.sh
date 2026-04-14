#!/bin/bash
# morning_run.sh — daily orchestrator
# Usage: ./scripts/morning_run.sh path/to/daily.html [path/to/weekly.html]

set -e

DAILY_FILE="$1"
WEEKLY_FILE="${2:-}"

if [ -z "$DAILY_FILE" ]; then
    echo "Usage: ./scripts/morning_run.sh <daily_html> [weekly_html]"
    exit 1
fi

# Ensure venv active
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

echo "=== Morning Run: $(date) ==="

# Phase 1: Extract
echo "[1/4] Extracting $DAILY_FILE..."
python3 scripts/extract.py "$DAILY_FILE"

if [ -n "$WEEKLY_FILE" ]; then
    echo "[1b/4] Extracting $WEEKLY_FILE..."
    python3 scripts/extract.py "$WEEKLY_FILE"
fi

# Phase 2: Update portfolio with today's prices
echo "[2/4] Updating portfolio with latest prices..."
python3 scripts/portfolio_track.py update

# Phase 3: Diff vs prior session
echo "[3/4] Computing overnight diff..."
python3 scripts/diff.py --today-auto

# Phase 4: Commit
echo "[4/4] Committing to git..."
git add raw_html/ parsed_json/ parsed_csv/ master/ analyses/
git commit -m "Morning run $(date +%Y-%m-%d)"

if [ "${PUSH:-0}" = "1" ]; then
    git push origin main
    echo "Pushed to origin."
else
    echo "Committed locally. Run 'git push' to sync to GitHub."
fi

# Summary
DATE=$(basename "$DAILY_FILE" | cut -d'_' -f1)
echo ""
echo "=== Morning Run Complete ==="
echo "Parsed JSON:     parsed_json/${DATE}_daily.json"
echo "Parsed CSV:      parsed_csv/${DATE}_daily.csv"
echo "Diff analysis:   analyses/${DATE}_diff.md"
echo "Portfolio ledger: master/portfolio_ledger.csv"
echo ""
echo "For Claude session, share:"
echo "  https://raw.githubusercontent.com/stevent63/hubAgent/main/parsed_csv/${DATE}_daily.csv"
echo "  https://raw.githubusercontent.com/stevent63/hubAgent/main/analyses/${DATE}_diff.md"
