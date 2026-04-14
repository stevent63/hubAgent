# Changelog

## Phase 2 — Diff + Portfolio Tracking (2026-04-14)
- Built `scripts/diff.py` — overnight session comparison engine
  - Computes: new Buys, new Sell/pP exits, bear→bull & bull→bear transitions, MoM accelerators
  - Equity-only filtering (excludes FX $-prefix, indices ^-prefix, crypto _X suffix)
  - Mode distribution deltas, bullish % change, spBuy count tracking
  - Outputs morning-ready markdown to `analyses/{date}_diff.md`
- Built `scripts/portfolio_track.py` — position ledger CRUD
  - Commands: enter, exit, update, status, history, stats, verify
  - Auto-populates entry/exit fields from parsed JSON
  - P&L calculation, business-day holding periods, win rate, expectancy
  - Segmented stats by exit signal, conviction, theme
- Built `scripts/morning_run.sh` — daily orchestrator (extract → update → diff → commit)
- 16 diff tests, 13 portfolio tests (all passing)
- Added second test fixture (`2026-04-13_daily.html`) for diff testing

## Phase 1 — Foundation (2026-04-14)
- Created repository directory structure per build spec
- Built `scripts/extract.py` — HTML parser for RL daily/weekly files
  - Parses all signal types, modes (via CSS class), numeric fields
  - Auto-detects daily vs weekly from column headers
  - Deduplicates by (name, ticker, signal_type) compound key
  - Outputs: JSON, CSV, master_history.csv append, master_signals.csv append
  - Idempotent: re-running on same file produces no duplicates
- Created test suite with 32 passing tests covering parsing, output, idempotency, error handling
- Added test fixture HTML in `tests/fixtures/`
- Created `.gitignore`, `requirements.txt`
