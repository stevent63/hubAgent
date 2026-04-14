#!/usr/bin/env python3
"""
portfolio_track.py — Position ledger CRUD for RL portfolio tracking.

Usage:
    python3 scripts/portfolio_track.py enter --ticker FCX --date 2026-04-03 --signal Buy --conviction HIGH --theme "Mining"
    python3 scripts/portfolio_track.py exit --ticker FCX --date 2026-04-14 --signal pP
    python3 scripts/portfolio_track.py update
    python3 scripts/portfolio_track.py status
    python3 scripts/portfolio_track.py history
    python3 scripts/portfolio_track.py stats
    python3 scripts/portfolio_track.py verify
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / 'master' / 'portfolio_ledger.csv'

LEDGER_COLUMNS = [
    'entry_date', 'ticker', 'name', 'entry_signal', 'entry_mode', 'entry_mom',
    'entry_r', 'entry_close', 'entry_revl', 'entry_tr_weeks', 'conviction',
    'theme', 'thesis', 'exit_date', 'exit_signal', 'exit_close', 'exit_mom',
    'holding_days', 'pnl_pct', 'pnl_dollars_per_share', 'status', 'notes',
    'current_close', 'current_mom', 'current_mode', 'last_updated',
]


def log(msg: str) -> None:
    print(f"[portfolio_track.py] {msg}")


def load_ledger() -> list[dict]:
    """Load the portfolio ledger CSV."""
    if not LEDGER_PATH.exists() or LEDGER_PATH.stat().st_size == 0:
        return []
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_ledger(rows: list[dict]) -> None:
    """Write the full ledger back to CSV."""
    with open(LEDGER_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in LEDGER_COLUMNS})


def load_parsed_json(date: str, file_type: str = 'daily') -> dict | None:
    """Load a parsed JSON file for a given date."""
    path = REPO_ROOT / 'parsed_json' / f'{date}_{file_type}.json'
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def lookup_ticker(data: dict, ticker: str) -> dict | None:
    """Find a ticker's data in a parsed JSON session."""
    for s in data.get('signals', []):
        if s['ticker'] == ticker:
            return s
    return None


def compute_holding_days(entry_date: str, exit_date: str) -> int:
    """Compute business days between two dates."""
    try:
        import pandas as pd
        start = pd.Timestamp(entry_date)
        end = pd.Timestamp(exit_date)
        return len(pd.bdate_range(start, end)) - 1  # exclude entry day
    except ImportError:
        # Fallback: calendar days
        d1 = datetime.strptime(entry_date, '%Y-%m-%d')
        d2 = datetime.strptime(exit_date, '%Y-%m-%d')
        return (d2 - d1).days


def find_most_recent_json(file_type: str = 'daily') -> dict | None:
    """Find and load the most recent parsed JSON."""
    import re
    json_dir = REPO_ROOT / 'parsed_json'
    if not json_dir.exists():
        return None
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})_' + re.escape(file_type) + r'\.json$')
    dates = []
    for f in json_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            dates.append(m.group(1))
    if not dates:
        return None
    latest = sorted(dates)[-1]
    return load_parsed_json(latest, file_type)


# --- COMMANDS ---

def cmd_enter(args):
    """Enter a new position."""
    data = load_parsed_json(args.date)
    if not data:
        log(f"ERROR: No parsed JSON for {args.date}. Run extract.py first.")
        sys.exit(1)

    sig = lookup_ticker(data, args.ticker)
    if not sig:
        log(f"ERROR: Ticker {args.ticker} not found in {args.date} parsed data.")
        sys.exit(1)

    # Check for existing open position
    ledger = load_ledger()
    for row in ledger:
        if row['ticker'] == args.ticker and row['status'] == 'OPEN':
            log(f"WARNING: {args.ticker} already has an OPEN position (entered {row['entry_date']}). Adding new entry anyway.")
            break

    new_row = {
        'entry_date': args.date,
        'ticker': args.ticker,
        'name': sig.get('name', ''),
        'entry_signal': args.signal,
        'entry_mode': sig.get('mode', ''),
        'entry_mom': sig.get('mom', ''),
        'entry_r': sig.get('r', ''),
        'entry_close': sig.get('close', ''),
        'entry_revl': sig.get('revl', ''),
        'entry_tr_weeks': sig.get('tr_weeks', ''),
        'conviction': getattr(args, 'conviction', ''),
        'theme': getattr(args, 'theme', ''),
        'thesis': getattr(args, 'thesis', ''),
        'exit_date': '',
        'exit_signal': '',
        'exit_close': '',
        'exit_mom': '',
        'holding_days': '',
        'pnl_pct': '',
        'pnl_dollars_per_share': '',
        'status': 'OPEN',
        'notes': '',
        'current_close': sig.get('close', ''),
        'current_mom': sig.get('mom', ''),
        'current_mode': sig.get('mode', ''),
        'last_updated': args.date,
    }

    ledger.append(new_row)
    save_ledger(ledger)
    log(f"Entered {args.ticker} @ {sig.get('close', '?')} on {args.date} ({args.signal}, {getattr(args, 'conviction', '')})")


def cmd_exit(args):
    """Exit a position."""
    ledger = load_ledger()

    # Find the open position
    target_idx = None
    for i, row in enumerate(ledger):
        if row['ticker'] == args.ticker and row['status'] == 'OPEN':
            target_idx = i
            break

    if target_idx is None:
        log(f"ERROR: No OPEN position for {args.ticker}")
        sys.exit(1)

    row = ledger[target_idx]

    # Look up exit data
    data = load_parsed_json(args.date)
    exit_close = None
    exit_mom = None
    if data:
        sig = lookup_ticker(data, args.ticker)
        if sig:
            exit_close = sig.get('close')
            exit_mom = sig.get('mom')

    if exit_close is None:
        log(f"WARNING: Could not find {args.ticker} in {args.date} parsed data. Exit close not populated.")

    entry_close = float(row['entry_close']) if row['entry_close'] else None
    holding_days = compute_holding_days(row['entry_date'], args.date)

    pnl_pct = None
    pnl_dps = None
    if entry_close and exit_close:
        pnl_pct = (exit_close - entry_close) / entry_close * 100
        pnl_dps = exit_close - entry_close

    row['exit_date'] = args.date
    row['exit_signal'] = args.signal
    row['exit_close'] = exit_close if exit_close is not None else ''
    row['exit_mom'] = exit_mom if exit_mom is not None else ''
    row['holding_days'] = holding_days
    row['pnl_pct'] = f"{pnl_pct:.2f}" if pnl_pct is not None else ''
    row['pnl_dollars_per_share'] = f"{pnl_dps:.2f}" if pnl_dps is not None else ''
    row['status'] = 'CLOSED'
    row['current_close'] = exit_close if exit_close is not None else row.get('current_close', '')
    row['current_mom'] = exit_mom if exit_mom is not None else row.get('current_mom', '')
    row['last_updated'] = args.date

    ledger[target_idx] = row
    save_ledger(ledger)

    pnl_str = f"{pnl_pct:+.2f}%" if pnl_pct is not None else "unknown"
    log(f"Exited {args.ticker} on {args.date} ({args.signal}), held {holding_days} days, P&L: {pnl_str}")


def cmd_update(args):
    """Update all open positions with latest prices."""
    data = find_most_recent_json()
    if not data:
        log("ERROR: No parsed JSON files found.")
        sys.exit(1)

    by_ticker = {s['ticker']: s for s in data.get('signals', [])}
    ledger = load_ledger()
    updated = 0
    date = data.get('date', 'unknown')

    for row in ledger:
        if row['status'] != 'OPEN':
            continue
        sig = by_ticker.get(row['ticker'])
        if sig:
            row['current_close'] = sig.get('close', row.get('current_close', ''))
            row['current_mom'] = sig.get('mom', row.get('current_mom', ''))
            row['current_mode'] = sig.get('mode', row.get('current_mode', ''))
            row['last_updated'] = date
            updated += 1

    save_ledger(ledger)
    log(f"Updated {updated} open positions with {date} data")


def cmd_status(args):
    """Print current portfolio status."""
    ledger = load_ledger()
    open_positions = [r for r in ledger if r['status'] == 'OPEN']

    if not open_positions:
        log("No open positions.")
        return

    print(f"\n{'='*80}")
    print(f"PORTFOLIO STATUS — {len(open_positions)} open positions")
    print(f"{'='*80}")
    print(f"{'Ticker':<8} {'Entry Date':<12} {'Signal':<8} {'Entry':<10} {'Current':<10} {'Mode':<18} {'MoM':<6} {'Conv':<6} {'Theme'}")
    print(f"{'-'*8} {'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*18} {'-'*6} {'-'*6} {'-'*20}")

    for r in sorted(open_positions, key=lambda x: x.get('entry_date', '')):
        entry = r.get('entry_close', '-')
        current = r.get('current_close', '-')
        print(f"{r['ticker']:<8} {r.get('entry_date', '-'):<12} {r.get('entry_signal', '-'):<8} "
              f"{entry:<10} {current:<10} {r.get('current_mode', '-'):<18} "
              f"{r.get('current_mom', '-'):<6} {r.get('conviction', '-'):<6} {r.get('theme', '-')}")
    print()


def cmd_history(args):
    """Print all closed positions with P&L."""
    ledger = load_ledger()
    closed = [r for r in ledger if r['status'] == 'CLOSED']

    if not closed:
        log("No closed positions.")
        return

    print(f"\n{'='*90}")
    print(f"CLOSED POSITIONS — {len(closed)} trades")
    print(f"{'='*90}")
    print(f"{'Ticker':<8} {'Entry':<12} {'Exit':<12} {'Signal':<8} {'Exit Sig':<8} {'Days':<6} {'P&L%':<8} {'Theme'}")
    print(f"{'-'*8} {'-'*12} {'-'*12} {'-'*8} {'-'*8} {'-'*6} {'-'*8} {'-'*20}")

    for r in sorted(closed, key=lambda x: x.get('exit_date', '')):
        pnl = r.get('pnl_pct', '-')
        print(f"{r['ticker']:<8} {r.get('entry_date', '-'):<12} {r.get('exit_date', '-'):<12} "
              f"{r.get('entry_signal', '-'):<8} {r.get('exit_signal', '-'):<8} "
              f"{r.get('holding_days', '-'):<6} {pnl:<8} {r.get('theme', '-')}")
    print()


def cmd_stats(args):
    """Print summary statistics for closed positions."""
    ledger = load_ledger()
    closed = [r for r in ledger if r['status'] == 'CLOSED']
    open_count = sum(1 for r in ledger if r['status'] == 'OPEN')

    if not closed:
        log("No closed positions — stats require at least one closed trade.")
        print(f"\nOpen positions: {open_count}")
        return

    pnls = []
    holding_days_list = []
    for r in closed:
        if r.get('pnl_pct'):
            try:
                pnls.append(float(r['pnl_pct']))
            except ValueError:
                pass
        if r.get('holding_days'):
            try:
                holding_days_list.append(int(r['holding_days']))
            except ValueError:
                pass

    winners = [p for p in pnls if p > 0]
    losers = [p for p in pnls if p <= 0]

    total = len(pnls)
    win_rate = len(winners) / total * 100 if total else 0
    avg_win = sum(winners) / len(winners) if winners else 0
    avg_loss = sum(losers) / len(losers) if losers else 0
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)
    avg_hold = sum(holding_days_list) / len(holding_days_list) if holding_days_list else 0

    print(f"\n{'='*50}")
    print(f"PORTFOLIO STATISTICS")
    print(f"{'='*50}")
    print(f"Open positions:      {open_count}")
    print(f"Closed trades:       {total}")
    print(f"Win rate:            {win_rate:.1f}%")
    print(f"Avg winner:          {avg_win:+.2f}%")
    print(f"Avg loser:           {avg_loss:+.2f}%")
    print(f"Expectancy:          {expectancy:+.2f}%")
    print(f"Avg holding days:    {avg_hold:.1f}")

    # Segment by exit signal
    by_exit = {}
    for r in closed:
        sig = r.get('exit_signal', 'Unknown')
        if sig not in by_exit:
            by_exit[sig] = []
        if r.get('pnl_pct'):
            try:
                by_exit[sig].append(float(r['pnl_pct']))
            except ValueError:
                pass

    if by_exit:
        print(f"\n--- By Exit Signal ---")
        for sig, vals in sorted(by_exit.items()):
            avg = sum(vals) / len(vals) if vals else 0
            w = sum(1 for v in vals if v > 0)
            print(f"  {sig:<8}: {len(vals)} trades, {w}/{len(vals)} wins, avg {avg:+.2f}%")

    # Segment by conviction
    by_conv = {}
    for r in closed:
        conv = r.get('conviction', 'Unknown') or 'Unknown'
        if conv not in by_conv:
            by_conv[conv] = []
        if r.get('pnl_pct'):
            try:
                by_conv[conv].append(float(r['pnl_pct']))
            except ValueError:
                pass

    if by_conv:
        print(f"\n--- By Conviction ---")
        for conv, vals in sorted(by_conv.items()):
            avg = sum(vals) / len(vals) if vals else 0
            w = sum(1 for v in vals if v > 0)
            print(f"  {conv:<8}: {len(vals)} trades, {w}/{len(vals)} wins, avg {avg:+.2f}%")

    # Segment by theme
    by_theme = {}
    for r in closed:
        theme = r.get('theme', 'Unknown') or 'Unknown'
        if theme not in by_theme:
            by_theme[theme] = []
        if r.get('pnl_pct'):
            try:
                by_theme[theme].append(float(r['pnl_pct']))
            except ValueError:
                pass

    if by_theme:
        print(f"\n--- By Theme ---")
        for theme, vals in sorted(by_theme.items()):
            avg = sum(vals) / len(vals) if vals else 0
            w = sum(1 for v in vals if v > 0)
            print(f"  {theme:<20}: {len(vals)} trades, {w}/{len(vals)} wins, avg {avg:+.2f}%")

    print()


def cmd_verify(args):
    """Verify ledger integrity."""
    ledger = load_ledger()
    issues = []

    for i, row in enumerate(ledger):
        ticker = row.get('ticker', f'row_{i}')

        if not row.get('ticker'):
            issues.append(f"Row {i}: missing ticker")
        if not row.get('entry_date'):
            issues.append(f"Row {i} ({ticker}): missing entry_date")
        if not row.get('status') or row['status'] not in ('OPEN', 'CLOSED'):
            issues.append(f"Row {i} ({ticker}): invalid status '{row.get('status')}'")
        if row['status'] == 'CLOSED':
            if not row.get('exit_date'):
                issues.append(f"Row {i} ({ticker}): CLOSED but no exit_date")
            if not row.get('pnl_pct'):
                issues.append(f"Row {i} ({ticker}): CLOSED but no pnl_pct")
        if row['status'] == 'OPEN' and row.get('exit_date'):
            issues.append(f"Row {i} ({ticker}): OPEN but has exit_date")

    open_count = sum(1 for r in ledger if r['status'] == 'OPEN')
    closed_count = sum(1 for r in ledger if r['status'] == 'CLOSED')

    if issues:
        log(f"VERIFICATION FAILED — {len(issues)} issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        log(f"Ledger OK: {len(ledger)} rows ({open_count} open, {closed_count} closed)")


def main():
    parser = argparse.ArgumentParser(description='Portfolio position ledger CRUD')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # enter
    p_enter = subparsers.add_parser('enter', help='Enter a new position')
    p_enter.add_argument('--ticker', required=True)
    p_enter.add_argument('--date', required=True, help='Entry date YYYY-MM-DD')
    p_enter.add_argument('--signal', required=True, help='Entry signal (Buy, spBuy, etc.)')
    p_enter.add_argument('--conviction', default='', help='Conviction level')
    p_enter.add_argument('--theme', default='', help='Theme/sector')
    p_enter.add_argument('--thesis', default='', help='Entry thesis')

    # exit
    p_exit = subparsers.add_parser('exit', help='Exit a position')
    p_exit.add_argument('--ticker', required=True)
    p_exit.add_argument('--date', required=True, help='Exit date YYYY-MM-DD')
    p_exit.add_argument('--signal', required=True, help='Exit signal (Sell, pP, etc.)')

    # update
    subparsers.add_parser('update', help='Update open positions with latest prices')

    # status
    subparsers.add_parser('status', help='Print current portfolio status')

    # history
    subparsers.add_parser('history', help='Print closed positions with P&L')

    # stats
    subparsers.add_parser('stats', help='Print summary statistics')

    # verify
    subparsers.add_parser('verify', help='Verify ledger integrity')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        'enter': cmd_enter,
        'exit': cmd_exit,
        'update': cmd_update,
        'status': cmd_status,
        'history': cmd_history,
        'stats': cmd_stats,
        'verify': cmd_verify,
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
