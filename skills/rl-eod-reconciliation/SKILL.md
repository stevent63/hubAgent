---
name: rl-eod-reconciliation
description: Post-market reconciliation agent that scores the morning's conviction calls against actual intraday price action using Polygon API data. Runs at or after 4 PM ET each trading day. Produces a short, direct reconciliation note and updates the signal log for the hit-rate tracker. Trigger when the user says "run EOD", "end of day", "reconciliation", "how did today go", "score today's calls", "market close update", or any reference to checking how morning signals performed. This is the missing half of the morning agent — it closes the feedback loop on the same day.
---

# RL EOD Reconciliation Agent

You close the loop. The morning agent makes calls. You score them against what actually happened. Same day.

Your output is short — 5 to 15 sentences covering every open signal. A trader reads this in under a minute and knows exactly what confirmed, what failed, and what's still in play. You are not a report. You are a scorecard with just enough context to be actionable.

---

## Architecture

```
Morning Agent (pre-market)
    ↓ writes
signal_log.json (OPEN signals with QT/Opportunist levels)
    ↓ reads
EOD Agent (post-market, 4:01 PM ET)
    ↓ pulls
Polygon API (intraday bars for each OPEN ticker)
    ↓ writes
EOD Reconciliation Note + updated signal_log.json
    ↓ feeds
Hit-Rate Tracker (Saturday weekly run)
```

One input file. One API. One output note. One updated log.

---

## Trigger & Timing

**When to run:** Any time after 4:00 PM ET on a trading day. Can also run during market hours for a mid-day check (will note that market is still open and results are partial).

**What triggers it:** User says "run EOD" or equivalent. Eventually, cron job at 4:05 PM ET.

**What it needs:**
1. `signal_log.json` with OPEN entries (produced/updated by morning agent)
2. Polygon API key (environment variable `POLYGON_API_KEY`)
3. Today's date (auto-detected, or user-specified for backfill)

---

## Pipeline

### Step 1: Load Signal Log

Read `signal_log.json`. Filter to:
- All entries with `status: "OPEN"`
- Group into two buckets:
  - **Today's calls**: `date_flagged` = today (from this morning's briefing)
  - **Prior open signals**: `date_flagged` < today (still being tracked from prior days)

Report counts: "12 open signals: 4 from this morning, 8 prior."

If no signal_log.json exists or no OPEN signals found, say so and stop. Don't fabricate.

### Step 2: Pull Polygon Data

For each unique ticker with an OPEN signal, pull intraday data:

**Primary endpoint — Intraday bars (1-minute or 5-minute):**
```
GET /v2/aggs/ticker/{ticker}/range/5/minute/{date}/{date}
?adjusted=true&sort=asc&apiKey={key}
```

For today's calls, pull today's full session. For prior open signals, pull today's bars (we already have prior days from previous EOD runs stored in price_path).

**Fallback — Daily OHLCV (if intraday fails or for prior-day backfill):**
```
GET /v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}
?adjusted=true&sort=asc&apiKey={key}
```

**Rate limiting:** Polygon free tier = 5 requests/minute. Paid tiers are higher. Batch requests where possible. If tracking 20+ tickers, implement a simple delay between calls. The script handles this automatically.

**What to extract per ticker per day:**
```json
{
  "ticker": "GOOGL",
  "date": "2026-03-23",
  "open": 171.20,
  "high": 173.45,
  "low": 169.80,
  "close": 172.90,
  "volume": 28400000,
  "vwap": 172.15,
  "qt_touched": true,
  "qt_touch_time": "11:23",
  "qt_held_at_close": true,
  "opp_touched": false,
  "opp_touch_time": null,
  "intraday_high_time": "14:35",
  "intraday_low_time": "10:12",
  "session_mfe_pct": 2.9,
  "session_mae_pct": -0.4
}
```

**Level touch detection logic:**
- QT touched = intraday high ≥ QT price (for long signals)
- Opportunist touched = intraday low ≤ Opportunist price (for limit buy entries)
- Touch time = timestamp of the first bar where the level was breached
- "Held at close" = close ≥ QT price (for longs)

### Step 3: Score Each Signal

For each OPEN signal, compute:

**Intraday metrics (from today's Polygon data):**
- `today_pnl_pct`: (today_close - close_at_flag) / close_at_flag × 100
- `session_mfe`: highest point reached today relative to entry
- `session_mae`: lowest point reached today relative to entry
- `qt_touched_today`: boolean
- `qt_touch_time`: when (if applicable)
- `qt_held_at_close`: boolean
- `opp_touched_today`: boolean
- `opp_touch_time`: when
- `distance_to_qt_pct`: how far close is from QT, as % of entry

**Cumulative metrics (updated from all days since flag):**
- Update `max_favorable_excursion` if today's high set new MFE
- Update `max_adverse_excursion` if today's low set new MAE
- Append today to `price_path` array
- Update `mode_trajectory` (from RL file if available, otherwise note "RL mode unknown — Polygon price only")

**Resolution check (same rules as hit-rate tracker):**

```
TARGET_HIT:
  - QT price touched intraday AND held at close
  - OR: close > QT price (may have gapped above)

SOFT_HIT (new status — QT touched but didn't hold):
  - QT touched intraday but close < QT
  - Don't resolve yet — mark as SOFT_HIT for tracking
  - These are the most analytically interesting outcomes

STOPPED_OUT:
  - Cumulative MAE from entry exceeded -8%
  - OR: close below RevL on a signal that required bullish stance

EXPIRED:
  - Exceeded evaluation window without resolution
  - Mean reversion: 10 trading days
  - Trend following: 15 trading days
  - Regime change: 20 trading days

STILL_OPEN:
  - Within evaluation window, no resolution trigger
```

### Step 4: Write Reconciliation Note

The output. Short. Direct. Every open signal gets one sentence.

**Format:**

```
# EOD Reconciliation — Monday March 23, 2026

12 open signals tracked. 4 from this morning, 8 prior.

## Today's Calls
GOOGL spBuy: QT $172.50 hit at 11:23 AM, closed $172.90 above → TARGET_HIT (+2.6%)
NVDA dBuy: Touched Opportunist $118.20 at 2:15 PM, bounced to $119.80 by close → working (+1.4% from Opp)
AMD Buy: Drifted lower all day, never approached QT $158.30. Close $154.10 → not confirming (-0.8%)
TSLA spBuy: Gapped down at open, hit -8% hard stop by 2:47 PM. Close $161.20 → STOPPED_OUT (-8.3%)

## Prior Open Signals (day 2+)
MSFT Buy (day 3): Flat. Close $412.50, QT $415.80 → still 0.8% away. MoM rising per this AM's RL. Patient.
AAPL Switch (day 7): Grinding higher. Close $198.20, QT $195.50 → already above QT → TARGET_HIT (+3.1%)
META dBuy (day 5): Fading. Close $485.20, down -2.1% from entry. MAE now -3.4%. Approaching concern zone.
AVGO spBuy (day 9): Last day before expiry window. Close $178.30, QT $180.10 → needs +1.0% tomorrow or expires.
[... one line per signal ...]

## Summary
- Resolved today: 2 TARGET_HIT, 1 STOPPED_OUT
- Soft hits (touched QT, didn't hold): 0
- Still open: 9 (3 from today, 6 prior)
- Signals approaching expiry (within 2 days): 2

## Signal Log Updated
signal_log.json written with 3 status changes and 12 price path updates.
```

**Tone rules:**
- One sentence per signal. No padding.
- Lead with the ticker and signal type, then the key fact.
- Include the QT level and actual close so the trader can see distance.
- Use "→" to show the verdict.
- "Working" = moving in the right direction but not yet resolved.
- "Not confirming" = flat or slightly adverse, still within normal range.
- "Concerning" = adverse but not yet stopped.
- "Patient" = nothing happening, no concern.
- Round percentages to one decimal.

### Step 5: Update Signal Log

Write the updated `signal_log.json` with:
- Status changes (OPEN → TARGET_HIT, STOPPED_OUT, EXPIRED)
- New price_path entries for every OPEN signal
- Updated MFE/MAE values
- SOFT_HIT flags where applicable
- Resolution dates and final P/L for resolved signals

Save to `/mnt/user-data/outputs/signal_log.json`.

---

## Polygon API Reference

### Authentication
All requests use query parameter: `?apiKey={POLYGON_API_KEY}`

### Endpoints Used

**Intraday Aggregates (primary):**
```
GET https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
```
- `multiplier`: 5 (5-minute bars — good balance of resolution vs data volume)
- `timespan`: "minute"
- `from`, `to`: YYYY-MM-DD format
- Returns: array of `{o, h, l, c, v, vw, t, n}` where `t` is unix ms timestamp

**Daily Aggregates (fallback / multi-day):**
```
GET https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}
```
- Same response structure, one bar per day

**Previous Close (quick check):**
```
GET https://api.polygon.io/v2/aggs/ticker/{ticker}/prev
```
- Returns yesterday's OHLCV. Useful for quick gap detection.

### Response Parsing
```python
def parse_polygon_aggs(response_json):
    """Parse Polygon aggregates response into usable format."""
    results = response_json.get('results', [])
    bars = []
    for bar in results:
        bars.append({
            'timestamp': datetime.fromtimestamp(bar['t'] / 1000, tz=timezone.utc),
            'open': bar['o'],
            'high': bar['h'],
            'low': bar['l'],
            'close': bar['c'],
            'volume': bar['v'],
            'vwap': bar.get('vw', None),
        })
    return bars
```

### Rate Limiting Strategy
```python
import time

def polygon_get(url, api_key, rate_limit_delay=0.25):
    """Fetch with simple rate limiting."""
    resp = requests.get(f"{url}&apiKey={api_key}")
    time.sleep(rate_limit_delay)  # 4 req/sec stays well under limits
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 429:
        time.sleep(12)  # back off on rate limit
        return polygon_get(url, api_key, rate_limit_delay)
    else:
        return None
```

---

## Level Touch Detection

The core analytical function. Given intraday bars and a set of levels, determine if/when each level was touched.

```python
def detect_level_touches(bars, levels, entry_price):
    """
    bars: list of {timestamp, open, high, low, close, volume, vwap}
    levels: {qt_price, opportunist_price, revl, hard_stop}
    entry_price: close_at_flag from signal log

    Returns touch report for each level.
    """
    report = {}

    for level_name, level_price in levels.items():
        if level_price is None:
            continue

        touched = False
        touch_time = None
        held_at_close = False

        for bar in bars:
            # QT and RevL: touched if high >= level (long bias)
            if level_name in ('qt_price', 'revl'):
                if bar['high'] >= level_price and not touched:
                    touched = True
                    touch_time = bar['timestamp']

            # Opportunist: touched if low <= level (limit buy)
            elif level_name == 'opportunist_price':
                if bar['low'] <= level_price and not touched:
                    touched = True
                    touch_time = bar['timestamp']

            # Hard stop: touched if low <= level
            elif level_name == 'hard_stop':
                if bar['low'] <= level_price and not touched:
                    touched = True
                    touch_time = bar['timestamp']

        # Check if held at close (last bar)
        if touched and bars:
            last_close = bars[-1]['close']
            if level_name == 'qt_price':
                held_at_close = last_close >= level_price
            elif level_name == 'opportunist_price':
                held_at_close = last_close >= entry_price  # bounced above entry

        report[level_name] = {
            'touched': touched,
            'touch_time': touch_time.strftime('%H:%M') if touch_time else None,
            'held_at_close': held_at_close
        }

    return report


def compute_session_excursions(bars, entry_price):
    """Compute MFE and MAE for the session relative to entry."""
    if not bars:
        return {'mfe_pct': 0, 'mae_pct': 0, 'mfe_time': None, 'mae_time': None}

    max_high = entry_price
    min_low = entry_price
    mfe_time = None
    mae_time = None

    for bar in bars:
        if bar['high'] > max_high:
            max_high = bar['high']
            mfe_time = bar['timestamp']
        if bar['low'] < min_low:
            min_low = bar['low']
            mae_time = bar['timestamp']

    return {
        'mfe_pct': round((max_high - entry_price) / entry_price * 100, 2),
        'mae_pct': round((min_low - entry_price) / entry_price * 100, 2),
        'mfe_time': mfe_time.strftime('%H:%M') if mfe_time else None,
        'mae_time': mae_time.strftime('%H:%M') if mae_time else None,
    }
```

---

## Integration with Morning Agent

The morning agent's only new responsibility: **append conviction calls to signal_log.json.**

This is not a new script. It's 20 lines added to the end of the morning briefing flow:

```python
import json
from pathlib import Path

def append_signals_to_log(conviction_calls, briefing_context, log_path='signal_log.json'):
    """
    conviction_calls: list of dicts from morning agent's conviction section
        Each has: ticker, signal_type, mode, mom, r, close, revl, qt_price, opp_price, sector
    briefing_context: dict with date, regime, bullish_pct, spbuy_count
    """
    # Load existing log or start fresh
    log = []
    if Path(log_path).exists():
        with open(log_path) as f:
            log = json.load(f)

    existing_ids = {entry['id'] for entry in log}

    for call in conviction_calls:
        signal_id = f"{briefing_context['date']}-{call['ticker']}-{call['signal_type']}"
        if signal_id in existing_ids:
            continue  # don't double-log

        log.append({
            'id': signal_id,
            'ticker': call['ticker'],
            'date_flagged': briefing_context['date'],
            'source': 'morning_briefing',
            'signal_type': call['signal_type'],
            'signal_nature': classify_nature(call['signal_type']),
            'mode_at_flag': call['mode'],
            'mode_weekly_at_flag': call.get('mode_weekly'),
            'mom_at_flag': call['mom'],
            'r_at_flag': call['r'],
            'close_at_flag': call['close'],
            'revl_at_flag': call['revl'],
            'qt_price': call['qt_price'],
            'opportunist_price': call['opp_price'],
            'sector': call.get('sector', 'Unknown'),
            'regime_context': briefing_context['regime'],
            'breadth_at_flag': {
                'bullish_pct': briefing_context['bullish_pct'],
                'spbuy_count': briefing_context['spbuy_count']
            },
            'conviction_tier': call.get('conviction', 'MEDIUM'),
            'convergence_score': call.get('convergence'),
            'thesis_snippet': call.get('thesis', ''),
            'status': 'OPEN',
            'resolution_date': None,
            'days_to_resolution': None,
            'final_pnl_pct': None,
            'max_favorable_excursion': 0.0,
            'max_adverse_excursion': 0.0,
            'soft_hit_count': 0,
            'mode_trajectory': [call['mode']],
            'price_path': [{
                'date': briefing_context['date'],
                'close': call['close'],
                'high': call['close'],  # no intraday data at flag time
                'low': call['close'],
                'source': 'rl_file'
            }]
        })

    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)

    return len(conviction_calls)
```

That's the entire integration surface. The morning agent calls this once at the end. The EOD agent reads the same file.

---

## Integration with Hit-Rate Tracker

The hit-rate tracker reads `signal_log.json` on its Saturday run. Because the EOD agent has already been updating it all week with Polygon-enriched price paths, the tracker has:

- Intraday MFE/MAE data (not just close-to-close)
- Exact QT touch times
- SOFT_HIT flags for signals that touched target but reversed
- Complete price paths from flag through resolution

The tracker doesn't need to call Polygon itself. The EOD agent has already done all the data enrichment. The tracker's job is purely analytical — compute rates, segment, and write the assessment.

---

## Run Protocol

### Manual (current state)
```bash
# User triggers after 4 PM ET
# Claude reads signal_log.json from uploads, runs the pipeline, outputs updated file

"Run EOD"
→ Claude loads signal_log.json
→ Pulls Polygon data for each OPEN ticker
→ Scores signals, writes reconciliation note
→ Outputs updated signal_log.json
```

### Automated (target state)
```bash
#!/bin/bash
# run_eod.sh — runs at 4:05 PM ET via cron

export POLYGON_API_KEY="your_key_here"
export SIGNAL_LOG="data/signal_log.json"
export OUTPUT_DIR="data/eod/"

python3 eod_reconciliation.py \
    --signal-log "$SIGNAL_LOG" \
    --date "$(date +%Y-%m-%d)" \
    --output-dir "$OUTPUT_DIR" \
    --polygon-key "$POLYGON_API_KEY"

# Outputs:
# data/eod/eod_2026-03-23.md  (reconciliation note)
# data/signal_log.json         (updated in place)
```

### Backfill Mode
```bash
# Score signals for a date in the past (e.g., missed a day)
python3 eod_reconciliation.py \
    --signal-log data/signal_log.json \
    --date 2026-03-20 \
    --polygon-key "$POLYGON_API_KEY"
```

---

## Edge Cases

**No OPEN signals:** "No open signals to reconcile. Morning agent hasn't logged any conviction calls yet." Stop.

**Polygon API down or ticker not found:** Log the failure, skip the ticker, note it in the reconciliation. "GOOGL: Polygon data unavailable — skipped. Will retry tomorrow."

**Market holiday:** Detect via Polygon returning empty results. "Market was closed today. No reconciliation needed."

**Pre-market run (before 4 PM):** Run anyway but note: "Market still open — results are partial. Re-run after close for final reconciliation."

**Signal flagged on a ticker that was halted or delisted:** Polygon will return gaps or errors. Mark signal as INVALIDATED with note.

**Weekend/backfill:** Can pull historical intraday data from Polygon for any date. Useful for catching up after missed days.

---

## Rules

1. **One sentence per signal.** The reconciliation note is not a report. It's a scorecard.
2. **Always show the level and the actual price.** "QT $172.50, closed $172.90" — the trader needs to see the numbers, not just "hit target."
3. **SOFT_HIT is the most interesting outcome.** Track it carefully. Over time, the ratio of soft hits that eventually convert to real hits vs those that reverse permanently is deeply informative.
4. **Never skip the update.** Even if no signals resolved today, the price_path and MFE/MAE updates are valuable. Every day of data makes the hit-rate tracker more precise.
5. **The signal log is append-only for entries, update-only for status.** Never delete an entry. Never modify historical price_path data. Only append new checkpoints and update status fields.
6. **Polygon data is truth for price. RL data is truth for signals.** Don't second-guess RL signals with Polygon data. Don't second-guess Polygon prices with RL close prices (they can differ slightly due to timing).
