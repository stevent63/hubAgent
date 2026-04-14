# Changelog

## Phase 3b — User Profile Separation + Massive API Naming (2026-04-14)
- Renamed `context/CONTEXT.md` → `MARKET_AGENT_CONTEXT.md` at repo root
- Extracted user-specific content into `user/chris.fiume@gmail.com.md`
- Added User Profile Loading section to MARKET_AGENT_CONTEXT.md
- Created `scripts/get_user.py` — reads USER_EMAIL from .env, returns profile path
- Created `.env.example` with MASSIVE_API_KEY and USER_EMAIL template
- Updated Polygon references → Massive (Polygon rebranded)
- Added python-dotenv to requirements.txt
- Updated README.md bootstrap template and architecture tree

## Phase 3 — Queryable History + Documentation (2026-04-14)
- Built `scripts/signal_search.py` — 6 query patterns:
  - `ticker`: historical signals for a name with optional forward-days lookups
  - `events`: all signals of a type in a date range
  - `hit-rate`: % of signals hitting a price threshold after N trading days
  - `persistence`: names holding a mode for N+ consecutive sessions
  - `trajectory`: time series of (date, close, mode, MoM, R) for a ticker
  - `switch`: Switch candidates (daily DG + weekly transitioning)
  - All queries support `--format markdown|csv|json`
- Created `reference/strategy_reference.md` — canonical RL system deep reference
- Created `reference/briefing_format.md` — non-negotiable morning briefing format
- Created `reference/signal_definitions.md` — all signal types with thresholds
- Created `reference/column_mapping.md` — HTML parsing schema for maintainers
- Rewrote `README.md` as operational entry point with full usage docs
- 21 signal_search tests (90 total across all suites, all passing)

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
