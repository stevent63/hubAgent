#!/usr/bin/env python3
"""
signal_search.py — Query master history for signal patterns.

Usage:
    python3 scripts/signal_search.py ticker --symbol CENX --signal Buy --lookback-days 90
    python3 scripts/signal_search.py events --signal spBuy --start 2026-02-28 --end 2026-03-21
    python3 scripts/signal_search.py hit-rate --signal Buy --forward-days 10 --threshold 5
    python3 scripts/signal_search.py persistence --mode "Dark Green" --min-days 30
    python3 scripts/signal_search.py trajectory --symbol GOOGL --start 2026-03-01
    python3 scripts/signal_search.py switch --lookback-days 60
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MASTER_HISTORY = REPO_ROOT / 'master' / 'master_history.csv'
MASTER_SIGNALS = REPO_ROOT / 'master' / 'master_signals.csv'


def log(msg: str) -> None:
    print(f"[signal_search.py] {msg}")


def load_master(path: Path | None = None) -> list[dict]:
    """Load master CSV into list of dicts."""
    if path is None:
        path = MASTER_HISTORY
    if not path.exists() or path.stat().st_size == 0:
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, '%Y-%m-%d')


def date_str(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d')


def get_available_dates(rows: list[dict], file_type: str = 'daily') -> list[str]:
    """Get sorted unique dates in the dataset."""
    dates = set()
    for r in rows:
        if r.get('file_type', 'daily') == file_type and r.get('date'):
            dates.add(r['date'])
    return sorted(dates)


def safe_float(val: str) -> float | None:
    if not val or val == 'None':
        return None
    try:
        return float(val)
    except ValueError:
        return None


def safe_int(val: str) -> int | None:
    if not val or val == 'None':
        return None
    try:
        return int(val)
    except ValueError:
        return None


def format_table(headers: list[str], rows: list[list], fmt: str = 'markdown') -> str:
    """Format data as markdown table, CSV, or JSON."""
    if fmt == 'json':
        data = [dict(zip(headers, row)) for row in rows]
        return json.dumps(data, indent=2)
    elif fmt == 'csv':
        lines = [','.join(headers)]
        for row in rows:
            lines.append(','.join(str(v) for v in row))
        return '\n'.join(lines)
    else:
        # Markdown
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        header_line = '| ' + ' | '.join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + ' |'
        sep_line = '|' + '|'.join('-' * (w + 2) for w in col_widths) + '|'
        data_lines = []
        for row in rows:
            data_lines.append('| ' + ' | '.join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)) + ' |')

        return '\n'.join([header_line, sep_line] + data_lines)


# ── COMMANDS ────────────────────────────────────────────────────────────────

def cmd_ticker(args):
    """Historical signals for a specific ticker."""
    rows = load_master(MASTER_SIGNALS if args.signal else MASTER_HISTORY)
    if not rows:
        log("No data in master history.")
        return

    cutoff = None
    if args.lookback_days:
        cutoff = date_str(datetime.now() - timedelta(days=args.lookback_days))

    filtered = []
    for r in rows:
        if r['ticker'] != args.symbol:
            continue
        if args.signal and r.get('signal_type') != args.signal:
            continue
        if cutoff and r.get('date', '') < cutoff:
            continue
        if r.get('file_type', 'daily') != args.file_type:
            continue
        filtered.append(r)

    if not filtered:
        log(f"No matching records for {args.symbol}")
        return

    # If forward-days requested, look up future data
    all_rows = load_master() if args.forward_days else []
    all_dates = get_available_dates(all_rows, args.file_type)

    headers = ['Date', 'Signal', 'Close', 'Mode', 'MoM', 'R', 'Days']
    if args.forward_days:
        headers.append(f'+{args.forward_days}d Close')
        headers.append(f'+{args.forward_days}d Δ%')

    table_rows = []
    for r in sorted(filtered, key=lambda x: x.get('date', '')):
        row = [
            r.get('date', ''),
            r.get('signal_type', ''),
            r.get('close', ''),
            r.get('mode', ''),
            r.get('mom', ''),
            r.get('r', ''),
            r.get('days', ''),
        ]

        if args.forward_days and all_dates:
            # Find the date N trading days forward
            try:
                idx = all_dates.index(r['date'])
                fwd_idx = idx + args.forward_days
                if fwd_idx < len(all_dates):
                    fwd_date = all_dates[fwd_idx]
                    fwd_row = next((x for x in all_rows if x['ticker'] == args.symbol
                                    and x['date'] == fwd_date
                                    and x.get('file_type', 'daily') == args.file_type), None)
                    if fwd_row:
                        fwd_close = safe_float(fwd_row.get('close', ''))
                        entry_close = safe_float(r.get('close', ''))
                        if fwd_close and entry_close:
                            delta_pct = (fwd_close - entry_close) / entry_close * 100
                            row.append(f"{fwd_close:.2f}")
                            row.append(f"{delta_pct:+.2f}%")
                        else:
                            row.extend([fwd_row.get('close', '-'), '-'])
                    else:
                        row.extend(['-', '-'])
                else:
                    row.extend(['-', '-'])
            except ValueError:
                row.extend(['-', '-'])

        table_rows.append(row)

    log(f"Found {len(table_rows)} records for {args.symbol}")
    print(format_table(headers, table_rows, args.format))


def cmd_events(args):
    """All signals of a type in a date range."""
    rows = load_master(MASTER_SIGNALS)
    if not rows:
        log("No data in master signals.")
        return

    filtered = []
    for r in rows:
        if r.get('signal_type') != args.signal:
            continue
        date = r.get('date', '')
        if args.start and date < args.start:
            continue
        if args.end and date > args.end:
            continue
        if r.get('file_type', 'daily') != args.file_type:
            continue
        filtered.append(r)

    if not filtered:
        log(f"No {args.signal} events found in range.")
        return

    # Group by date for count summary
    by_date = {}
    for r in filtered:
        d = r.get('date', '')
        by_date[d] = by_date.get(d, 0) + 1

    headers = ['Date', 'Ticker', 'Name', 'Close', 'Mode', 'MoM', 'R']
    table_rows = []
    for r in sorted(filtered, key=lambda x: (x.get('date', ''), x.get('ticker', ''))):
        table_rows.append([
            r.get('date', ''), r.get('ticker', ''), r.get('name', ''),
            r.get('close', ''), r.get('mode', ''),
            r.get('mom', ''), r.get('r', ''),
        ])

    log(f"Found {len(filtered)} {args.signal} events across {len(by_date)} dates")
    print(format_table(headers, table_rows, args.format))

    # Print daily counts
    print(f"\n--- Daily counts ---")
    for d in sorted(by_date):
        print(f"  {d}: {by_date[d]}")


def cmd_hit_rate(args):
    """Hit rate analysis: % of signals that hit a price threshold after N days."""
    all_rows = load_master()
    if not all_rows:
        log("No data in master history.")
        return

    # Find signal events
    signals = [r for r in all_rows
                if r.get('signal_type') == args.signal
                and r.get('file_type', 'daily') == args.file_type]

    if not signals:
        log(f"No {args.signal} signals found.")
        return

    all_dates = get_available_dates(all_rows, args.file_type)

    hits = 0
    misses = 0
    no_data = 0
    results = []

    for sig in signals:
        entry_close = safe_float(sig.get('close', ''))
        if not entry_close:
            no_data += 1
            continue

        try:
            idx = all_dates.index(sig['date'])
        except ValueError:
            no_data += 1
            continue

        fwd_idx = idx + args.forward_days
        if fwd_idx >= len(all_dates):
            no_data += 1
            continue

        fwd_date = all_dates[fwd_idx]
        fwd_row = next((r for r in all_rows if r['ticker'] == sig['ticker']
                         and r['date'] == fwd_date
                         and r.get('file_type', 'daily') == args.file_type), None)

        if not fwd_row:
            no_data += 1
            continue

        fwd_close = safe_float(fwd_row.get('close', ''))
        if not fwd_close:
            no_data += 1
            continue

        delta_pct = (fwd_close - entry_close) / entry_close * 100
        hit = delta_pct >= args.threshold
        if hit:
            hits += 1
        else:
            misses += 1

        results.append({
            'ticker': sig['ticker'],
            'date': sig['date'],
            'entry': entry_close,
            'fwd_close': fwd_close,
            'delta_pct': delta_pct,
            'hit': hit,
        })

    total = hits + misses
    hit_rate = hits / total * 100 if total else 0

    print(f"\n{'='*50}")
    print(f"HIT RATE: {args.signal} signals")
    print(f"{'='*50}")
    print(f"Threshold:    >= {args.threshold}% after {args.forward_days} trading days")
    print(f"Sample size:  {total} (excluded {no_data} with insufficient data)")
    print(f"Hits:         {hits}")
    print(f"Misses:       {misses}")
    print(f"Hit rate:     {hit_rate:.1f}%")

    if results:
        avg_delta = sum(r['delta_pct'] for r in results) / len(results)
        print(f"Avg return:   {avg_delta:+.2f}%")

    # Show individual results if small enough
    if len(results) <= 50:
        headers = ['Date', 'Ticker', 'Entry', f'+{args.forward_days}d', 'Δ%', 'Hit']
        table_rows = []
        for r in sorted(results, key=lambda x: x['delta_pct'], reverse=True):
            table_rows.append([
                r['date'], r['ticker'],
                f"{r['entry']:.2f}", f"{r['fwd_close']:.2f}",
                f"{r['delta_pct']:+.2f}%",
                'Y' if r['hit'] else 'N',
            ])
        print()
        print(format_table(headers, table_rows, args.format))


def cmd_persistence(args):
    """Names that held a mode for N+ consecutive days."""
    rows = load_master()
    if not rows:
        log("No data in master history.")
        return

    # Group by ticker, sorted by date
    by_ticker = {}
    for r in rows:
        if r.get('file_type', 'daily') != args.file_type:
            continue
        ticker = r.get('ticker', '')
        if ticker not in by_ticker:
            by_ticker[ticker] = []
        by_ticker[ticker].append(r)

    # Find persistence streaks
    results = []
    for ticker, ticker_rows in by_ticker.items():
        sorted_rows = sorted(ticker_rows, key=lambda x: x.get('date', ''))
        streak = 0
        streak_start = None

        for r in sorted_rows:
            if r.get('mode') == args.mode:
                if streak == 0:
                    streak_start = r.get('date', '')
                streak += 1
            else:
                if streak >= args.min_days:
                    results.append({
                        'ticker': ticker,
                        'name': sorted_rows[0].get('name', ''),
                        'streak': streak,
                        'start': streak_start,
                        'end': sorted_rows[max(0, sorted_rows.index(r) - 1)].get('date', ''),
                    })
                streak = 0
                streak_start = None

        # Check final streak
        if streak >= args.min_days:
            results.append({
                'ticker': ticker,
                'name': sorted_rows[0].get('name', ''),
                'streak': streak,
                'start': streak_start,
                'end': sorted_rows[-1].get('date', ''),
                'ongoing': True,
            })

    results.sort(key=lambda x: x['streak'], reverse=True)

    if not results:
        log(f"No tickers held {args.mode} for {args.min_days}+ consecutive sessions.")
        return

    log(f"Found {len(results)} tickers with {args.mode} streak >= {args.min_days} sessions")
    headers = ['Ticker', 'Name', 'Sessions', 'Start', 'End', 'Ongoing']
    table_rows = []
    for r in results:
        table_rows.append([
            r['ticker'], r.get('name', ''), r['streak'],
            r['start'], r['end'], 'Y' if r.get('ongoing') else 'N',
        ])
    print(format_table(headers, table_rows, args.format))


def cmd_trajectory(args):
    """MoM/mode/close time series for a single ticker."""
    rows = load_master()
    if not rows:
        log("No data in master history.")
        return

    filtered = [r for r in rows
                 if r['ticker'] == args.symbol
                 and r.get('file_type', 'daily') == args.file_type]

    if args.start:
        filtered = [r for r in filtered if r.get('date', '') >= args.start]
    if args.end:
        filtered = [r for r in filtered if r.get('date', '') <= args.end]

    filtered.sort(key=lambda x: x.get('date', ''))

    if not filtered:
        log(f"No data for {args.symbol}")
        return

    log(f"Trajectory for {args.symbol}: {len(filtered)} sessions")
    headers = ['Date', 'Close', 'Mode', 'MoM', 'R', 'Signal', 'Days']
    table_rows = []
    for r in filtered:
        table_rows.append([
            r.get('date', ''), r.get('close', ''), r.get('mode', ''),
            r.get('mom', ''), r.get('r', ''),
            r.get('signal_type', ''), r.get('days', ''),
        ])
    print(format_table(headers, table_rows, args.format))


def cmd_switch(args):
    """Switch candidates: daily DG + weekly transitioning to DG."""
    # This requires both daily and weekly data in master_history
    rows = load_master()
    if not rows:
        log("No data in master history.")
        return

    cutoff = None
    if args.lookback_days:
        cutoff = date_str(datetime.now() - timedelta(days=args.lookback_days))

    daily_rows = [r for r in rows if r.get('file_type') == 'daily']
    weekly_rows = [r for r in rows if r.get('file_type') == 'weekly']

    if not weekly_rows:
        log("No weekly data available. Switch analysis requires weekly file parsing.")
        log("Parse weekly HTML files with extract.py first.")
        return

    # Get most recent daily date
    daily_dates = get_available_dates(daily_rows, 'daily')
    weekly_dates = get_available_dates(weekly_rows, 'weekly')

    if not daily_dates or not weekly_dates:
        log("Insufficient data for Switch analysis.")
        return

    latest_daily = daily_dates[-1]
    latest_weekly = weekly_dates[-1]

    # Find tickers in DG on daily
    daily_dg = {r['ticker'] for r in daily_rows
                 if r['date'] == latest_daily and r.get('mode') == 'Dark Green'}

    # Find tickers transitioning on weekly (not yet DG, or recently flipped to DG)
    weekly_latest = {r['ticker']: r for r in weekly_rows if r['date'] == latest_weekly}

    candidates = []
    for ticker in daily_dg:
        w = weekly_latest.get(ticker)
        if not w:
            continue
        w_mode = w.get('mode', '')
        # Switch candidates: daily DG but weekly not yet DG, or weekly just flipped
        if w_mode in ('Light Green', 'Bear-Bull Flip', 'Bear-Bull (LR-LG)'):
            candidates.append({
                'ticker': ticker,
                'name': w.get('name', ''),
                'daily_mode': 'Dark Green',
                'weekly_mode': w_mode,
                'weekly_mom': w.get('mom', ''),
                'weekly_r': w.get('r', ''),
            })
        elif w_mode == 'Dark Green':
            # Already double green — active Switch, not candidate
            candidates.append({
                'ticker': ticker,
                'name': w.get('name', ''),
                'daily_mode': 'Dark Green',
                'weekly_mode': 'Dark Green',
                'weekly_mom': w.get('mom', ''),
                'weekly_r': w.get('r', ''),
            })

    candidates.sort(key=lambda x: x.get('weekly_mode', ''))

    if not candidates:
        log("No Switch candidates found.")
        return

    log(f"Found {len(candidates)} potential Switch names (daily={latest_daily}, weekly={latest_weekly})")
    headers = ['Ticker', 'Name', 'Daily Mode', 'Weekly Mode', 'Wkly MoM', 'Wkly R']
    table_rows = []
    for c in candidates:
        table_rows.append([
            c['ticker'], c['name'], c['daily_mode'], c['weekly_mode'],
            c['weekly_mom'], c['weekly_r'],
        ])
    print(format_table(headers, table_rows, args.format))


def main():
    parser = argparse.ArgumentParser(description='Query RL master history for signal patterns')
    subparsers = parser.add_subparsers(dest='command', help='Query type')

    # ticker
    p_ticker = subparsers.add_parser('ticker', help='Historical signals for a ticker')
    p_ticker.add_argument('--symbol', required=True, help='Ticker symbol')
    p_ticker.add_argument('--signal', default='', help='Filter to specific signal type')
    p_ticker.add_argument('--lookback-days', type=int, default=0, help='Limit to last N days')
    p_ticker.add_argument('--forward-days', type=int, default=0, help='Show price N trading days after')
    p_ticker.add_argument('--file-type', default='daily', choices=['daily', 'weekly'])
    p_ticker.add_argument('--format', default='markdown', choices=['markdown', 'csv', 'json'])

    # events
    p_events = subparsers.add_parser('events', help='All signals of a type in date range')
    p_events.add_argument('--signal', required=True, help='Signal type (Buy, spBuy, etc.)')
    p_events.add_argument('--start', default='', help='Start date YYYY-MM-DD')
    p_events.add_argument('--end', default='', help='End date YYYY-MM-DD')
    p_events.add_argument('--file-type', default='daily', choices=['daily', 'weekly'])
    p_events.add_argument('--format', default='markdown', choices=['markdown', 'csv', 'json'])

    # hit-rate
    p_hitrate = subparsers.add_parser('hit-rate', help='Hit rate analysis for a signal type')
    p_hitrate.add_argument('--signal', required=True, help='Signal type')
    p_hitrate.add_argument('--forward-days', type=int, required=True, help='Look-ahead period in trading days')
    p_hitrate.add_argument('--threshold', type=float, required=True, help='Min % gain to count as hit')
    p_hitrate.add_argument('--file-type', default='daily', choices=['daily', 'weekly'])
    p_hitrate.add_argument('--format', default='markdown', choices=['markdown', 'csv', 'json'])

    # persistence
    p_persist = subparsers.add_parser('persistence', help='Names holding a mode for N+ sessions')
    p_persist.add_argument('--mode', required=True, help='Mode name (e.g. "Dark Green")')
    p_persist.add_argument('--min-days', type=int, required=True, help='Minimum consecutive sessions')
    p_persist.add_argument('--file-type', default='daily', choices=['daily', 'weekly'])
    p_persist.add_argument('--format', default='markdown', choices=['markdown', 'csv', 'json'])

    # trajectory
    p_traj = subparsers.add_parser('trajectory', help='Time series for a ticker')
    p_traj.add_argument('--symbol', required=True, help='Ticker symbol')
    p_traj.add_argument('--start', default='', help='Start date YYYY-MM-DD')
    p_traj.add_argument('--end', default='', help='End date YYYY-MM-DD')
    p_traj.add_argument('--file-type', default='daily', choices=['daily', 'weekly'])
    p_traj.add_argument('--format', default='markdown', choices=['markdown', 'csv', 'json'])

    # switch
    p_switch = subparsers.add_parser('switch', help='Switch candidates (daily DG + weekly transitioning)')
    p_switch.add_argument('--lookback-days', type=int, default=60, help='Lookback window')
    p_switch.add_argument('--format', default='markdown', choices=['markdown', 'csv', 'json'])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        'ticker': cmd_ticker,
        'events': cmd_events,
        'hit-rate': cmd_hit_rate,
        'persistence': cmd_persistence,
        'trajectory': cmd_trajectory,
        'switch': cmd_switch,
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
