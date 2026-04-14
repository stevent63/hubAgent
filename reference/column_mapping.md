# HTML Column Mapping — Parsing Schema

Reference for `scripts/extract.py` and any future parser maintenance.

---

## Daily File Table Structure

Column mapping by index in each row's `<td>` elements:

| Index | Field | Type | Notes |
|-------|-------|------|-------|
| 0 | Name | text | Company name |
| 1 | Ticker | text | Stock symbol |
| 2 | Close | float | Strip `$` and commas before parsing |
| 3 | Tr | integer | Weekly trend weeks count |
| 4 | Mode | CSS class | Extracted from class attribute, NOT text content |
| 5 | RevL | float | Reversal Level price |
| 6 | MoM | float | Momentum (can be negative) |
| 7 | Days | integer | Days in current mode |
| 8 | P/L% | text + float | Raw text includes `%`; store both raw and parsed |
| 9 | Envelope | float | Price channel metric (not stored in output) |
| 10 | R | float | Relative performance vs SPX; can be blank for FX/indices |

The **Action** column position varies — locate by header name `"Action"`, not by hardcoded index.

---

## CSS Class to Mode Mapping

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

If a cell has multiple CSS classes, check all against known mode classes. If no match → `mode = "Unknown"` + log warning (don't fail).

---

## Weekly File Differences

| Aspect | Daily | Weekly |
|--------|-------|--------|
| Duration column header | "Days" | "Weeks" |
| RevL header | "RevL" | "RevL (W)" |
| MoM header | "MoM" | "MoM (W)" |
| Tr interpretation | Same | Same |
| CSS classes | Same mapping | Same mapping (verify — may differ) |

**Auto-detection:** Inspect the 8th column header. "Days" → daily. "Weeks" → weekly. Also check for `(W)` suffixes in headers.

---

## Table Detection

Find the main signal table as: **largest `<table>` element that contains an "Action" column header.** This avoids picking up navigation tables or metadata tables in the HTML.

---

## Deduplication

RL HTML sometimes contains duplicate rows. Dedupe by compound key:

```
(name, ticker, signal_type)
```

Keep first occurrence. Log count of duplicates dropped.

---

## Date Extraction

Extract date from filename pattern only:

```
YYYY-MM-DD_{daily|weekly}.html
```

**Never** infer date from HTML file content — too fragile. If filename doesn't match pattern, raise `ValueError`.

---

## Filtering Policy

Do **NOT** filter at the extraction layer:
- FX names (`$`-prefix, e.g., `$DXY`)
- Index names (`^`-prefix, e.g., `^SPX`)
- Crypto names (`_X` suffix)

Store everything. Downstream consumers (diff.py, signal_search.py) filter as needed. The diff engine's equity-only counts exclude these prefixes/suffixes.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Malformed row (too few cells) | Log warning with row index, skip, continue |
| Missing required field | Log warning, set to `None`/`NaN`, continue |
| No table found with "Action" header | Raise `ValueError` with clear message |
| File not found | Raise `FileNotFoundError` |
| Unknown signal text | Log warning, store the text anyway |
| Unknown CSS class for mode | Set mode to "Unknown", log warning |

---

## Output Schemas

### JSON Output (`parsed_json/{date}_{type}.json`)

```json
{
  "date": "YYYY-MM-DD",
  "file_type": "daily|weekly",
  "source_file": "path/to/source.html",
  "extracted_at": "ISO timestamp",
  "total": 3427,
  "mode_counts": {"Dark Green": N, ...},
  "signal_counts": {"Hold": N, "Buy": N, ...},
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

### CSV Columns

```
date, file_type, ticker, name, close, mode, mode_css, revl, mom, r, days, tr_weeks, pl_raw, pl_num, signal_type
```

Same schema for per-file CSV, `master_history.csv`, and `master_signals.csv` (signals excludes Hold rows).

### Master CSV Idempotency

Before appending to master CSVs, check for existing rows matching `(date, file_type, ticker)`. Skip if already present. This makes re-running extract.py safe.
