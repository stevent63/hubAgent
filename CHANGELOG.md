# Changelog

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
