# hubAgent Build Specification
## For Claude Code CLI Execution

**Target Repository:** https://github.com/stevent63/hubAgent
**Build Goal:** Persistent, queryable Reversal Levels (RL) trading analysis system that survives container resets, memory edits, and session boundaries.
**Execution Model:** Claude Code CLI runs this spec in phases, commits after each phase, confirms with user before proceeding to next phase.

---

## CORE PRINCIPLES FOR BUILD

Before beginning, internalize these:

1. **Durability over speed.** Every file written must be reproducible, version-controlled, and accessible via raw.githubusercontent.com URLs from any future Claude session.

2. **Idempotent operations.** Scripts should be safely re-runnable. Running extract.py twice on the same file should produce the same output, not duplicates in master_history.csv.

3. **Fail loud, fail early.** If a parse fails or a file is malformed, raise clear errors with line numbers and ticker context. Never silently drop data.

4. **Minimal external dependencies.** Python 3.11+, beautifulsoup4, pandas, requests. That's it. No frameworks, no ORMs, no Docker.

5. **Human-readable outputs.** CSVs over databases. Markdown over HTML. Git-diffable formats throughout.

6. **Comments explain WHY, not WHAT.** Code is self-documenting for mechanics; comments document decisions.

---

## REPOSITORY STRUCTURE

Final target state:

```
hubAgent/
├── raw_html/                       # RL HTML files, dated filenames
│   ├── 2026-04-14_daily.html
│   ├── 2026-04-14_weekly.html
│   └── .gitkeep
├── parsed_json/                    # Per-file structured output
│   ├── 2026-04-14_daily.json
│   ├── 2026-04-14_weekly.json
│   └── .gitkeep
├── parsed_csv/                     # Per-file CSV output (for Claude uploads)
│   ├── 2026-04-14_daily.csv
│   ├── 2026-04-14_weekly.csv
│   └── .gitkeep
├── master/                         # Cumulative append-only data
│   ├── master_history.csv          # Every row, every day, forever
│   ├── master_signals.csv          # Only non-Hold signal events
│   ├── portfolio_ledger.csv        # Position tracking (entries/exits/P&L)
│   └── .gitkeep
├── analyses/                       # Generated analyses, dated
│   ├── 2026-04-14_diff.md
│   ├── 2026-04-14_morning.md
│   └── .gitkeep
├── scripts/
│   ├── extract.py                  # HTML → JSON + CSV + master append
│   ├── diff.py                     # Compare two sessions
│   ├── signal_search.py            # Query master history for patterns
│   ├── portfolio_track.py          # Position ledger CRUD
│   ├── backfill.py                 # One-time historical load
│   ├── morning_run.sh              # Daily orchestrator
│   └── eod_run.sh                  # EOD reconciliation (Phase 4)
├── skills/                         # Skill files for Claude (versioned copies)
│   ├── rl-eod-reconciliation/
│   │   └── SKILL.md
│   ├── rl-hit-rate-tracker/
│   │   └── SKILL.md
│   ├── rl-weekend-analyst/
│   │   └── SKILL.md
│   ├── rl-buy-signals-viz/
│   │   └── SKILL.md
│   ├── switch-viz-analysis/
│   │   └── SKILL.md
│   └── stock-universe-visualization/
│       └── SKILL.md
├── reference/                      # Framework documentation
│   ├── strategy_reference.md       # RL system overview
│   ├── briefing_format.md          # Morning agent format spec
│   ├── signal_definitions.md       # Each signal type + thresholds
│   ├── column_mapping.md           # HTML parsing schema
│   └── pdfs/                       # The 13 RL strategy PDFs
│       └── .gitkeep
├── context/
│   ├── CONTEXT.md                  # Session orientation (ALREADY WRITTEN)
│   ├── portfolio_state.md          # Current holdings narrative
│   └── open_items.md               # In-progress items
├── tests/
│   ├── test_extract.py
│   ├── test_diff.py
│   ├── test_portfolio.py
│   └── fixtures/                   # Sample HTML files for testing
├── .gitignore
├── requirements.txt
├── README.md
└── CHANGELOG.md                    # Versioned build milestones
```

---

## PHASE 1: FOUNDATION

**Estimated time:** 60-90 minutes
**Deliverable:** Directory structure created, extract.py operational on sample file, first parsed output in repo.

### Tasks

**1.1 Clone repository and create directory structure**

```bash
cd ~
git clone https://github.com/stevent63/hubAgent.git
cd hubAgent
mkdir -p raw_html parsed_json parsed_csv master analyses scripts skills reference/pdfs context tests/fixtures
touch raw_html/.gitkeep parsed_json/.gitkeep parsed_csv/.gitkeep master/.gitkeep analyses/.gitkeep reference/pdfs/.gitkeep
```

**1.2 Create `.gitignore`**

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
venv/
ENV/
env/
.env
.env.local
*.log
.DS_Store
.vscode/
.idea/
*.swp
*.swo
```

**1.3 Create `requirements.txt`**

```
beautifulsoup4==4.12.3
pandas==2.2.0
requests==2.32.0
lxml==5.1.0
python-dateutil==2.9.0
```

Install: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

**1.4 Build `scripts/extract.py`**

Full requirements spec:

**INPUTS:**
- Argument 1: path to RL HTML file
- Optional flag: `--file-type daily|weekly` (auto-detected if omitted)
- Optional flag: `--no-master-append` (for testing without polluting master files)

**PARSING LOGIC:**

Use BeautifulSoup with lxml parser. Find the main signal table (largest table with the "Action" column header).

Column mapping (by INDEX in each row's `<td>` elements):
- Index 0: Name (text)
- Index 1: Ticker (text)
- Index 2: Close (float, strip $ and commas)
- Index 3: Tr (weekly trend weeks count — integer)
- Index 4: Mode — extracted from CSS class on the `<td>` element, NOT text content
- Index 5: RevL (float)
- Index 6: MoM (float, can be negative)
- Index 7: Days (integer — daily file) OR Weeks (integer — weekly file)
- Index 8: P/L% (text with "%" — store both raw text and parsed float)
- Index 10: R value (float, can be negative, can be blank for FX/indices)

The Action column text is in a specific position — locate by header name ("Action") rather than hardcoded index because it can vary. Extract text like "Buy", "Sell", "Hold", "spBuy", "spBuy+", "spBuy++", "dBuy", "dSell", "pP", "pP+", "wBuy", "AddSh", "Add".

CSS class to mode mapping:
```python
MODE_MAP = {
    'c4': 'Dark Green',
    'c5': 'Light Green',
    'c6': 'Dark Red',
    'c7': 'Light Red',
    'c20': 'Bear-Bull Flip',
    'c21': 'Bear-Bull (LR-LG)',
}
```

If a cell has multiple classes, check against all known mode classes. If no match, mode = "Unknown" and log a warning (don't fail).

**FILE TYPE DETECTION:**

Inspect the 8th column header. If it says "Days" → daily file. If "Weeks" → weekly file. Weekly file also has headers like "RevL (W)" or "MoM (W)". Store file_type in the output.

**DEDUPLICATION:**

RL HTML sometimes contains duplicate rows. Dedupe by compound key `(name, ticker, signal_type)`. Keep first occurrence. Log count of duplicates dropped.

**FILTERING:**

Do NOT filter out FX ($-prefix), indices (^-prefix), or crypto (_X suffix) at this layer. Store everything. Downstream consumers can filter as needed.

**DATE EXTRACTION:**

Extract date from filename pattern `YYYY-MM-DD_{daily|weekly}.html`. If filename doesn't match pattern, raise error. Never infer date from file content (too fragile).

**OUTPUTS:**

1. **JSON file** at `parsed_json/{date}_{type}.json`:

```json
{
  "date": "2026-04-14",
  "file_type": "daily",
  "source_file": "raw_html/2026-04-14_daily.html",
  "extracted_at": "2026-04-14T09:15:23",
  "total": 3427,
  "mode_counts": {
    "Dark Green": 1745,
    "Light Green": 414,
    "Light Red": 630,
    "Dark Red": 471,
    "Bear-Bull Flip": 133
  },
  "signal_counts": {
    "Hold": 3075,
    "Buy": 124,
    "pP": 87,
    "dSell": 39,
    "Sell": 34,
    "AddSh": 19,
    "spBuy": 15,
    "pP+": 12,
    "wBuy": 9,
    "dBuy": 5,
    "spBuy++": 4,
    "Add": 2,
    "spBuy+": 2
  },
  "signals": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc",
      "close": 260.49,
      "mode": "Dark Green",
      "mode_css": "c4",
      "revl": 251.42,
      "mom": 2.81,
      "r": 0.14,
      "days": 5,
      "tr_weeks": 34,
      "pl_raw": "+1.69%",
      "pl_num": 1.69,
      "signal_type": "Hold"
    }
  ]
}
```

2. **CSV file** at `parsed_csv/{date}_{type}.csv`:

Flat columns: `date, file_type, ticker, name, close, mode, mode_css, revl, mom, r, days, tr_weeks, pl_raw, pl_num, signal_type`

3. **Master history append** to `master/master_history.csv`:

Same columns as per-file CSV. Check for existing rows matching `(date, file_type, ticker)` before appending; skip if already present (idempotency).

4. **Master signals append** to `master/master_signals.csv`:

Same columns, but ONLY rows where `signal_type != 'Hold'`. This is the event log.

**ERROR HANDLING:**

- Malformed row: log warning with row index and ticker, skip row, continue
- Missing required field: log warning, set to None/NaN, continue
- Complete parse failure (no table found): raise ValueError with clear message
- File not found: raise FileNotFoundError

**LOGGING:**

Print to stdout:
```
[extract.py] Parsing 2026-04-14_daily.html...
[extract.py] Detected file type: daily
[extract.py] Extracted 3427 rows
[extract.py] Deduplicated 12 rows (compound key collisions)
[extract.py] Mode distribution: DG=1745 LG=414 LR=630 DR=471 Flips=133 Unknown=0
[extract.py] Signal counts: Hold=3075 Buy=124 Sell=34 pP=87 ...
[extract.py] Wrote parsed_json/2026-04-14_daily.json
[extract.py] Wrote parsed_csv/2026-04-14_daily.csv
[extract.py] Appended 3427 rows to master_history.csv
[extract.py] Appended 352 signal events to master_signals.csv
[extract.py] Done.
```

**1.5 Test extract.py**

Chris will provide one sample `2026-04-14_daily.html` in `raw_html/`. Run:

```bash
python3 scripts/extract.py raw_html/2026-04-14_daily.html
```

Verify:
- JSON file created at correct path
- CSV file created at correct path
- Master CSV grew by expected row count
- Signal counts match user's independent count (spot-check against visible HTML)
- Re-running the same command produces no duplicates in master (idempotency check)

**1.6 Commit Phase 1**

```bash
git add .
git commit -m "Phase 1: repository foundation + extract.py operational"
git push origin main
```

**PHASE 1 EXIT CRITERIA:**
- extract.py parses a daily file correctly
- Output JSON schema validates against spec
- master_history.csv is append-only and idempotent
- All files committed to GitHub
- Claude (via web_fetch on raw.githubusercontent.com) can retrieve the parsed CSV

---

## PHASE 2: DIFF + PORTFOLIO TRACKING

**Estimated time:** 90-120 minutes
**Deliverable:** diff.py operational, portfolio_track.py with CRUD ops, morning_run.sh orchestrator.

### Tasks

**2.1 Build `scripts/diff.py`**

**INPUTS:**
- Argument 1: today's date (YYYY-MM-DD)
- Argument 2: prior session's date (YYYY-MM-DD) — optional
- Flag: `--today-auto` — auto-detects most recent prior session
- Flag: `--file-type daily|weekly` — default daily

**LOGIC:**

Load both JSON files from `parsed_json/`. Compute:

1. **New Buy signals** — today has signal_type='Buy' AND (yesterday didn't exist OR yesterday's signal_type != 'Buy')
2. **New Sell/pP signals** — today has signal_type in ('Sell', 'pP', 'pP+', 'dSell') AND yesterday didn't
3. **Bear→Bull transitions** — yesterday mode in (Light Red, Dark Red) AND today mode in (Dark Green, Light Green, Bear-Bull Flip, Bear-Bull (LR-LG))
4. **Bull→Bear transitions** — the warning signal (opposite of above)
5. **MoM acceleration leaders** — top 20 by (today.mom - yesterday.mom)
6. **Mode distribution change** — count deltas for each mode
7. **Bullish percentage change** — (DG+LG+Flips) / total
8. **spBuy count change** — sum of spBuy+spBuy++spBuy++

Also compute equity-only subsets (filter FX $-prefix, indices ^-prefix, crypto _X suffix) for bear/bull transition counts — the equity-only numbers are the ones Chris tracks most closely.

**OUTPUT:**

Markdown file at `analyses/{today}_diff.md`:

```markdown
# Overnight Diff — 2026-04-14

## Summary
- **New Buy:** 124
- **New Sell/pP:** 120
- **Bear→Bull:** 117 total (81 equity)
- **Bull→Bear:** 20 total (0 equity)

## Mode Distribution
| Mode | Yesterday | Today | Δ |
|------|-----------|-------|---|
| Dark Green | 1817 | 1745 | -72 |
| Light Green | 358 | 414 | +56 |
| Light Red | 718 | 630 | -88 |
| Dark Red | 415 | 471 | +56 |
| Bullish % | 64.7% | 66.9% | +2.2 |

## Top New Buy Signals (by R)
[Sorted table of top 25 new Buys]

## Top New Sell/pP Signals (by Days held)
[Sorted table of top 25 exits]

## Biggest MoM Accelerators
[Sorted table of top 20 by Δ MoM]

## Equity Bull→Bear Reversals (WARNING SIGNAL)
[Full list, sorted by R descending]
```

**2.2 Build `scripts/portfolio_track.py`**

**COMMANDS:**

```bash
# Enter new position
python3 scripts/portfolio_track.py enter \
    --ticker FCX --date 2026-04-03 --signal Buy \
    --conviction HIGH --theme "Mining Wave" \
    --thesis "Copper supply deficit + metals broadening"

# Exit position
python3 scripts/portfolio_track.py exit \
    --ticker FCX --date 2026-04-14 --signal pP

# Update all open positions with latest prices from most recent parsed_json
python3 scripts/portfolio_track.py update

# Print current portfolio status
python3 scripts/portfolio_track.py status

# Print all closed positions with P&L summary
python3 scripts/portfolio_track.py history

# Print summary stats (hit rate, avg holding period, avg P&L, etc.)
python3 scripts/portfolio_track.py stats

# Reload from CSV and validate integrity
python3 scripts/portfolio_track.py verify
```

**LEDGER SCHEMA** (`master/portfolio_ledger.csv`):

```
entry_date, ticker, name, entry_signal, entry_mode, entry_mom, entry_r,
entry_close, entry_revl, entry_tr_weeks, conviction, theme, thesis,
exit_date, exit_signal, exit_close, exit_mom, holding_days,
pnl_pct, pnl_dollars_per_share, status, notes, current_close, current_mom,
current_mode, last_updated
```

- `status` = OPEN or CLOSED
- `current_*` fields updated by `update` command from latest parsed_json
- `notes` is free-text, manually editable

**ENTER LOGIC:**

When entering a position, look up the entry_date's parsed_json to populate all entry_* fields from the actual signal data. User provides ticker, date, signal, conviction, theme, thesis. System fills in the rest. If that date's parsed_json doesn't exist, error out clearly.

**EXIT LOGIC:**

When exiting, look up the exit_date's parsed_json for exit_close and exit_mom. Calculate:
- holding_days = exit_date - entry_date (business days, not calendar days — use pandas bdate_range)
- pnl_pct = (exit_close - entry_close) / entry_close * 100

**STATS LOGIC:**

Aggregate across closed positions:
- Total trades
- Win rate (% with pnl_pct > 0)
- Average holding days
- Average winner P&L, average loser P&L
- Expectancy = (win_rate * avg_win) + ((1-win_rate) * avg_loss)
- Segmentation: by signal_type, by conviction, by theme, by exit_signal (Sell vs pP vs pP+)

**2.3 Build `scripts/morning_run.sh`**

```bash
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
```

Make executable: `chmod +x scripts/morning_run.sh`

**2.4 Seed portfolio ledger with current ~52 positions**

This is the ONE-TIME manual step. User (or Chris) provides entry dates and themes for current positions. Example seeds:

```bash
python3 scripts/portfolio_track.py enter --ticker FCX --date 2026-04-03 --signal Buy --conviction HIGH --theme "Mining"
python3 scripts/portfolio_track.py enter --ticker CENX --date 2026-03-20 --signal spBuy+ --conviction HIGH --theme "Aluminum"
# etc.
```

Then record recent exits:
```bash
python3 scripts/portfolio_track.py exit --ticker FCX --date 2026-04-14 --signal pP
```

**2.5 Commit Phase 2**

```bash
git add .
git commit -m "Phase 2: diff engine + portfolio ledger operational"
git push origin main
```

**PHASE 2 EXIT CRITERIA:**
- diff.py produces morning-ready markdown for any two dates
- portfolio_track.py CRUD operations all work
- morning_run.sh runs end-to-end with real data
- Current portfolio seeded in ledger
- All committed

---

## PHASE 3: QUERYABLE HISTORY + DOCUMENTATION

**Estimated time:** 90-120 minutes
**Deliverable:** signal_search.py operational, reference docs complete, README.md finalized.

### Tasks

**3.1 Build `scripts/signal_search.py`**

**CORE QUERIES:**

```bash
# Historical signals for a specific ticker
python3 scripts/signal_search.py ticker \
    --symbol CENX --signal Buy --lookback-days 90 --forward-days 10

# Output: every Buy signal on CENX in last 90 days, with price/mode 10 days after each

# Switch candidates (requires weekly file parsing)
python3 scripts/signal_search.py switch \
    --lookback-days 60

# Output: names that went from daily DG+weekly LR to daily DG+weekly DG

# All signals of a type in a date range
python3 scripts/signal_search.py events \
    --signal spBuy --start 2026-02-28 --end 2026-03-21

# Hit rate analysis
python3 scripts/signal_search.py hit-rate \
    --signal Buy --forward-days 10 --threshold 5

# Output: % of Buy signals that were up >= 5% after 10 trading days

# Pattern: consecutive days in mode
python3 scripts/signal_search.py persistence \
    --mode "Dark Green" --min-days 30

# Output: names that held Dark Green for 30+ consecutive days

# MoM trajectory for a ticker
python3 scripts/signal_search.py trajectory \
    --symbol GOOGL --start 2026-03-01

# Output: time series of (date, mom, mode, close) for GOOGL since March 1
```

**IMPLEMENTATION NOTES:**

- Load `master_history.csv` once with pandas (should be fast even at 100K+ rows)
- For "forward-days" lookups, use pandas bdate_range to handle weekends/holidays
- Output formats: markdown table (default), CSV (--format csv), JSON (--format json)

**3.2 Write `reference/strategy_reference.md`**

Comprehensive RL system documentation. Include:

- Core principle (bullish above RevL, bearish below)
- All signal types with entry/exit implications
- Mode colors and transition semantics
- MoM scale and thresholds
- R value interpretation
- The five strategies Chris uses (Switch, Opportunist, spBuy, MoM Swing, QuickTarget)
- Key indicators (PuLL, Envelope, Iceberg, Rela, Key Prices)
- Daily vs weekly file differences
- The "12 Key Learnings" from CONTEXT.md reformatted as reference

This should be the canonical source. CONTEXT.md is a briefer orientation; this is the deep reference.

**3.3 Write `reference/briefing_format.md`**

The non-negotiable morning briefing format:

```markdown
# Morning Briefing Format — Non-Negotiable

## Section 1: What Changed Overnight
- X new Buy | Y new Sell/pP | Z bear→bull | W bull→bear (equity subset)
- Mode distribution table (yesterday vs today)
- Bullish % change
- spBuy count change (capitulation / recovery indicator)

## Section 2: Portfolio Signals (if applicable)
- New exits (Sell, pP, pP+)
- New warnings (dSell)
- Names entering consideration zone (MoM ≥ 8)
- Biggest MoM accelerators
- Active count change

## Section 3: Conviction Ideas
- 2-3 highest conviction calls
- Direct language, no hedging
- Signal priority order: Buy → dBuy → spBuy → trend changes → Switch → MoM >7 → R flips
- Cluster by sector/theme, not ticker-alphabetic

## Section 4: Macro/Sector Context
- Index ETF status (SPY, QQQ, IWM, DIA)
- Sector ETF changes (XLE, XLK, XLF, etc.)
- Bond/commodity context if relevant

## Section 5: Playbook
- Numbered actions for the day
- Specific price levels, not vague guidance
- Exit instructions for triggered signals
- Watch list for next 1-3 sessions

## Tone Rules
- High signal per word
- No padding, no caveats unless material
- Conviction is value-add
- External context seasons signals, doesn't override them
```

**3.4 Write `reference/signal_definitions.md`**

Every signal type with full spec:

```markdown
# Signal Definitions

## Entry Signals

### Buy
- Condition: price crossed RevL with confirming momentum
- Mode typically: Bear-Bull Flip or Dark Green
- Action: enter at open or QT level
- Hold until: Sell, pP, or mode deterioration

### dBuy
- Condition: developing Buy, earlier stage
- Lower conviction than Buy
- Watch for upgrade to Buy

### spBuy / spBuy+ / spBuy++
- Condition: bottom-fishing in Dark Red; price has capitulated
- Higher risk/reward
- ++ = strongest bottom signal
- Size smaller (3-5% max per name)

### wBuy
- Condition: weak Buy; marginal signal
- Lowest entry conviction

## Exit Signals

### Sell
- Condition: price broke below RevL
- HARD EXIT — no hesitation, no averaging down
- Clean execution at open

### pP / pP+
- Condition: extended momentum, profit-consideration
- Typically fires when MoM is in 8-10 range but NOT always at 10
- Take profits on winners
- Not a hard exit — discretion allowed for tax/holding period — but system is saying "mature"

### dSell
- Condition: developing Sell; warning
- Not a hard exit yet
- Tighten stop, cut on Sell confirmation

## Add Signals

### AddSh / Add
- Condition: existing position getting strong add signal
- Confirmed uptrend with re-accelerating momentum

## MoM Thresholds

- MoM +8 to +10: consideration zone (watch for pP)
- MoM > +10 held 2+ sessions with flat price: pre-pP pattern
- MoM < -7 with spBuy: capitulation opportunity

## R Thresholds

- R > +1.5: elite outperformer
- R +1.0 to +1.5: strong
- R +0.5 to +1.0: good
- R 0 to +0.5: market-like
- R < 0: laggard (NOT inherently bad — regime change bets, catch-up trades, mega-caps with index-flow protection)
```

**3.5 Write `reference/column_mapping.md`**

Full HTML parsing documentation. Column indices, CSS classes, known edge cases, weekly file differences. Essential for any future maintainer or parser fix.

**3.6 Write `README.md`**

The entry point for anyone (human or Claude) landing on the repo:

```markdown
# hubAgent

Persistent Reversal Levels (RL) trading analysis system.

## Quick Start

### Daily Workflow

1. Download RL HTML files from Reversal Levels platform
2. Save to `raw_html/` with naming: `YYYY-MM-DD_daily.html`, `YYYY-MM-DD_weekly.html`
3. Run: `./scripts/morning_run.sh raw_html/2026-04-14_daily.html raw_html/2026-04-14_weekly.html`
4. Review: `analyses/2026-04-14_diff.md`
5. Push to GitHub: `git push` (or set `PUSH=1` in morning_run.sh env)

### Starting a New Claude Session

Paste this template:

\`\`\`
Read these files before we begin:
- https://raw.githubusercontent.com/stevent63/hubAgent/main/context/CONTEXT.md
- https://raw.githubusercontent.com/stevent63/hubAgent/main/reference/briefing_format.md
- https://raw.githubusercontent.com/stevent63/hubAgent/main/reference/strategy_reference.md

Today's parsed CSV: https://raw.githubusercontent.com/stevent63/hubAgent/main/parsed_csv/YYYY-MM-DD_daily.csv

Run the morning briefing.
\`\`\`

## Architecture

[Tree diagram from spec]

## Scripts

- `extract.py` — HTML → JSON + CSV + master append
- `diff.py` — Compare two sessions, produce overnight diff
- `portfolio_track.py` — Position ledger CRUD
- `signal_search.py` — Query master history
- `backfill.py` — One-time historical load
- `morning_run.sh` — Daily orchestrator
- `eod_run.sh` — End-of-day reconciliation (future)

## Installation

[Standard venv install]

## Contributing

This is a personal trading system. Not accepting external contributions. But feel free to fork.
```

**3.7 Commit Phase 3**

```bash
git add .
git commit -m "Phase 3: queryable history + full documentation"
git push origin main
```

**PHASE 3 EXIT CRITERIA:**
- signal_search.py handles all 6 query patterns
- reference/ directory complete with 4 docs
- README.md operational as entry point
- Any Claude session can bootstrap from raw.githubusercontent.com URLs
- Committed

---

## PHASE 4: SKILLS + HISTORICAL BACKFILL

**Estimated time:** 60-90 minutes
**Deliverable:** All skill files versioned in repo, any historical RL HTML backfilled.

### Tasks

**4.1 Copy skill files from `/mnt/skills/user/`**

For each skill Chris uses:
- rl-eod-reconciliation
- rl-hit-rate-tracker
- rl-weekend-analyst
- rl-buy-signals-viz
- switch-viz-analysis
- stock-universe-visualization

Copy entire skill directory (SKILL.md + any supplementary files) to `hubAgent/skills/{skill-name}/`.

If Claude Code doesn't have direct access to `/mnt/skills/user/`, prompt user to provide the content of each SKILL.md file and commit those directly.

**4.2 Build `scripts/backfill.py`**

**PURPOSE:**

One-time script to populate master_history.csv from any historical RL HTML files.

**LOGIC:**

```python
# Usage: python3 scripts/backfill.py
# Iterates over all *.html files in raw_html/
# Sorts by date ascending
# Runs extract.py logic on each, appending to master_history.csv
# Skips files already parsed (check parsed_json/ for existing output)
# Reports: files processed, rows added, errors encountered
```

**4.3 Copy the 13 RL strategy PDFs**

User provides the 13 PDFs. Place in `reference/pdfs/` with clear naming:
- `00-Welcome.pdf`
- `01-RL-Fundamentals.pdf`
- `02-Signal-Types.pdf`
- etc.

(Names depend on what Chris has — preserve his original naming.)

**4.4 Write `context/portfolio_state.md`**

Current portfolio narrative (as of last run). Snapshot of:
- Active positions count and list
- Recent exits and P&L
- Consideration zone names
- dSell warnings
- Theme allocation
- Current path assessment (chop/pullback/lockout)

This file gets UPDATED after each significant portfolio event, not every session.

**4.5 Write `context/open_items.md`**

In-progress / pending items. Current list from CONTEXT.md:
- Weekly file extractor fix
- EOD reconciliation deployment
- Switch universe ongoing tracking
- Hit-rate tracker activation
- Sector classification map

**4.6 Commit Phase 4**

```bash
git add .
git commit -m "Phase 4: skills + reference PDFs + historical backfill"
git push origin main
```

**PHASE 4 EXIT CRITERIA:**
- All skill files committed under skills/
- All reference PDFs in reference/pdfs/
- Any available historical HTML backfilled into master
- Context files (portfolio_state, open_items) present

---

## PHASE 5: EOD RECONCILIATION + POLYGON INTEGRATION

**Estimated time:** 120-180 minutes
**Deliverable:** EOD agent operational, hit-rate tracking possible.

This is the phase that activates the Polygon API key (`AEAnWuVQl33zGCnt1FtIUeaml3obF0dx`). Chris should store this in `.env` file (gitignored).

### Tasks

**5.1 Build `scripts/eod_reconcile.py`**

Reference `/mnt/skills/user/rl-eod-reconciliation/SKILL.md` for full spec. Key elements:

- Read portfolio_ledger.csv for OPEN positions
- For each open position, pull Polygon intraday bars for today
- Check if QT levels touched, held at close
- Compute session MFE/MAE
- Update ledger with current_* fields and write reconciliation note
- Output to `analyses/{date}_eod.md`

**5.2 Build `scripts/eod_run.sh`**

Orchestrator for EOD:

```bash
#!/bin/bash
# eod_run.sh — post-market reconciliation
# Run after 4:15 PM ET

source .venv/bin/activate
source .env  # loads POLYGON_API_KEY

python3 scripts/eod_reconcile.py --date $(date +%Y-%m-%d)

git add analyses/ master/portfolio_ledger.csv
git commit -m "EOD reconciliation $(date +%Y-%m-%d)"

if [ "${PUSH:-0}" = "1" ]; then
    git push origin main
fi
```

**5.3 Build `scripts/hit_rate_tracker.py`**

Saturday run. Aggregates closed positions and OPEN positions with enough history. Segments by:
- Signal type (Buy, dBuy, spBuy, etc.)
- Conviction tier (HIGH, MEDIUM, LOW)
- Theme
- Regime at entry (correction, recovery, etc.)

Outputs written analytical assessment to `analyses/{saturday_date}_hit_rate.md`.

**5.4 Update `reference/signal_definitions.md`** with actual hit rates once enough data accumulates.

**5.5 Commit Phase 5**

```bash
git add .
git commit -m "Phase 5: EOD reconciliation + Polygon integration + hit-rate tracker"
git push origin main
```

**PHASE 5 EXIT CRITERIA:**
- EOD script runs end-to-end with Polygon data
- Saturday hit-rate tracker produces meaningful assessment (once 4+ weeks of data exist)
- Feedback loop closed: morning agent makes calls, EOD scores them, weekly tracker assesses patterns

---

## TESTING STRATEGY

Throughout each phase, write tests as you go.

**tests/test_extract.py:**
- Test CSS class mapping
- Test date extraction from filename
- Test deduplication logic
- Test daily vs weekly detection
- Test malformed row handling
- Test idempotency (run twice, same output)

**tests/test_diff.py:**
- Test with fixtures for two consecutive days
- Test bear→bull detection
- Test MoM acceleration ranking
- Test with missing prior day (should error clearly)

**tests/test_portfolio.py:**
- Test enter/exit/update cycle
- Test P&L calculation
- Test status reporting
- Test integrity verification

Use pytest. Run before each commit.

---

## ROLLBACK STRATEGY

If any phase produces broken output:

1. Git commits are atomic — revert the phase commit
2. Master files (master_history.csv, portfolio_ledger.csv) are append-only, so partial reverts are safe
3. If master_history gets corrupted, regenerate from raw_html via backfill.py

---

## CHANGELOG FORMAT

Maintain `CHANGELOG.md` at repo root:

```markdown
# Changelog

## 2026-04-14 — Phase 1 Complete
- Repository structure created
- extract.py operational on daily files
- First parsed output: 2026-04-14_daily.json

## 2026-04-15 — Phase 2 Complete
- diff.py operational
- portfolio_track.py CRUD ops functional
- morning_run.sh orchestrator end-to-end

[etc.]
```

Update after each phase.

---

## HANDOFF TO CLAUDE CODE

When executing this spec:

1. **Execute phases sequentially.** Do not skip ahead.
2. **Commit after each phase.** Never bundle multiple phases in one commit.
3. **Test each script against real data before proceeding.** Chris will provide sample HTML files.
4. **Ask Chris for clarification if any requirement is ambiguous.** Do not guess on:
   - Skill file contents (must come from Chris or `/mnt/skills/user/`)
   - Historical HTML files (availability unknown)
   - Portfolio seed data (entry dates for existing positions)
5. **Report completion of each phase with:**
   - Files created
   - Test results
   - Commit hash
   - Any deviations from spec with justification

---

## SUCCESS CRITERIA (BUILD COMPLETE)

- [ ] All 5 phases committed and pushed to GitHub
- [ ] A fresh Claude session can bootstrap by fetching 3-4 URLs from raw.githubusercontent.com
- [ ] Morning workflow: `./scripts/morning_run.sh` runs in < 30 seconds and commits cleanly
- [ ] EOD workflow: `./scripts/eod_run.sh` updates ledger with real Polygon data
- [ ] Container resets, memory edits, session boundaries no longer destroy analytical state
- [ ] Chris can delete every Claude conversation and still run the system

**The test:** Can Chris delete this entire conversation, open a fresh Claude session next Monday, paste the bootstrap prompt from README, upload nothing, and get a complete morning briefing? If yes, the build succeeded.