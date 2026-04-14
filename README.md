# hubAgent

Persistent Reversal Levels (RL) trading analysis system. Parses RL HTML signals into queryable, version-controlled data. Survives container resets, memory edits, and session boundaries.

## Quick Start

### Installation

```bash
git clone https://github.com/stevent63/hubAgent.git
cd hubAgent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Daily Workflow

1. Download RL HTML files from the Reversal Levels platform
2. Save to `raw_html/` as `YYYY-MM-DD_daily.html` (and optionally `_weekly.html`)
3. Run the morning orchestrator:

```bash
./scripts/morning_run.sh raw_html/2026-04-15_daily.html raw_html/2026-04-15_weekly.html
```

4. Review the overnight diff: `analyses/2026-04-15_diff.md`
5. Push to GitHub: `git push` (or set `PUSH=1` before running morning_run.sh)

### Starting a New Claude Session

Paste this template at the start of any conversation:

```
Read these files before we begin:
- https://raw.githubusercontent.com/stevent63/hubAgent/main/MARKET_AGENT_CONTEXT.md
- https://raw.githubusercontent.com/stevent63/hubAgent/main/user/chris.fiume@gmail.com.md
- https://raw.githubusercontent.com/stevent63/hubAgent/main/reference/briefing_format.md
- https://raw.githubusercontent.com/stevent63/hubAgent/main/reference/strategy_reference.md

Today's parsed CSV: https://raw.githubusercontent.com/stevent63/hubAgent/main/parsed_csv/YYYY-MM-DD_daily.csv

Run the morning briefing.
```

Any Claude session is operational in 30 seconds. This is the architectural goal.

## Architecture

```
hubAgent/
├── raw_html/                       # RL HTML files, dated filenames
├── parsed_json/                    # Per-file structured JSON output
├── parsed_csv/                     # Per-file CSV output (for Claude uploads)
├── master/                         # Cumulative append-only data
│   ├── master_history.csv          # Every row, every day, forever
│   ├── master_signals.csv          # Only non-Hold signal events
│   └── portfolio_ledger.csv        # Position tracking (entries/exits/P&L)
├── analyses/                       # Generated analyses, dated
├── scripts/
│   ├── extract.py                  # HTML → JSON + CSV + master append
│   ├── diff.py                     # Compare two sessions
│   ├── signal_search.py            # Query master history for patterns
│   ├── portfolio_track.py          # Position ledger CRUD
│   ├── backfill.py                 # One-time historical load
│   ├── get_user.py                 # Load user profile from .env
│   ├── morning_run.sh              # Daily orchestrator
│   └── eod_run.sh                  # EOD reconciliation (future)
├── reference/                      # Framework documentation
│   ├── strategy_reference.md       # RL system deep reference
│   ├── briefing_format.md          # Morning briefing format spec
│   ├── signal_definitions.md       # Signal types + thresholds
│   └── column_mapping.md           # HTML parsing schema
├── MARKET_AGENT_CONTEXT.md             # System orientation (read first)
├── user/                               # Per-user profiles
│   └── chris.fiume@gmail.com.md        # User preferences + trading style
├── context/
│   ├── portfolio_state.md          # Current holdings narrative
│   └── open_items.md               # In-progress items
├── skills/                         # Skill files for Claude sessions
├── tests/                          # Test suite
├── .env.example                        # Environment variable template
├── .gitignore
├── requirements.txt
└── CHANGELOG.md
```

## Scripts

### extract.py — HTML Parser
```bash
python3 scripts/extract.py raw_html/2026-04-15_daily.html
python3 scripts/extract.py raw_html/2026-04-15_weekly.html
python3 scripts/extract.py raw_html/2026-04-15_daily.html --no-master-append  # testing
```
Parses RL HTML into JSON + CSV. Appends to master_history.csv and master_signals.csv. Idempotent.

### diff.py — Overnight Comparison
```bash
python3 scripts/diff.py 2026-04-15                    # auto-finds prior session
python3 scripts/diff.py 2026-04-15 2026-04-14          # explicit dates
python3 scripts/diff.py --today-auto                   # most recent two dates
```
Computes new buys, exits, mode transitions, MoM accelerators. Writes markdown to `analyses/`.

### portfolio_track.py — Position Ledger
```bash
python3 scripts/portfolio_track.py enter --ticker FCX --date 2026-04-03 --signal Buy --conviction HIGH --theme "Mining"
python3 scripts/portfolio_track.py exit --ticker FCX --date 2026-04-14 --signal pP
python3 scripts/portfolio_track.py update              # refresh prices from latest parsed data
python3 scripts/portfolio_track.py status              # current portfolio
python3 scripts/portfolio_track.py history             # closed trades
python3 scripts/portfolio_track.py stats               # win rate, expectancy, segmentation
python3 scripts/portfolio_track.py verify              # integrity check
python3 scripts/portfolio_track.py update-exit --ticker X --pnl-pct Y   # backfill P&L
python3 scripts/portfolio_track.py remove --ticker X --reason "..."     # soft-delete
```

### signal_search.py — History Queries
```bash
python3 scripts/signal_search.py ticker --symbol CENX --signal Buy --lookback-days 90
python3 scripts/signal_search.py events --signal spBuy --start 2026-02-28 --end 2026-03-21
python3 scripts/signal_search.py hit-rate --signal Buy --forward-days 10 --threshold 5
python3 scripts/signal_search.py persistence --mode "Dark Green" --min-days 30
python3 scripts/signal_search.py trajectory --symbol GOOGL --start 2026-03-01
python3 scripts/signal_search.py switch --lookback-days 60
```
All queries support `--format markdown|csv|json`.

### morning_run.sh — Daily Orchestrator
```bash
./scripts/morning_run.sh raw_html/2026-04-15_daily.html [raw_html/2026-04-15_weekly.html]
PUSH=1 ./scripts/morning_run.sh raw_html/2026-04-15_daily.html  # auto-push
```
Runs extract → portfolio update → diff → git commit in sequence.

## Dependencies

- Python 3.9+
- beautifulsoup4, pandas, requests, lxml, python-dateutil, python-dotenv

## Contributing

Personal trading system. Not accepting external contributions. Fork freely.
