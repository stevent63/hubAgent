#!/usr/bin/env python3
"""
diff.py — Compare two RL sessions and produce overnight diff analysis.

Usage:
    python3 scripts/diff.py 2026-04-14
    python3 scripts/diff.py 2026-04-14 2026-04-13
    python3 scripts/diff.py --today-auto
    python3 scripts/diff.py 2026-04-14 --file-type weekly
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

BEARISH_MODES = {'Light Red', 'Dark Red'}
BULLISH_MODES = {'Dark Green', 'Light Green', 'Bear-Bull Flip', 'Bear-Bull (LR-LG)'}
EXIT_SIGNALS = {'Sell', 'pP', 'pP+', 'dSell'}
SPBUY_SIGNALS = {'spBuy', 'spBuy+', 'spBuy++'}
ALL_MODES = ['Dark Green', 'Light Green', 'Light Red', 'Dark Red', 'Bear-Bull Flip', 'Bear-Bull (LR-LG)', 'Unknown']


def log(msg: str) -> None:
    print(f"[diff.py] {msg}")


def is_equity(ticker: str) -> bool:
    """Return True if ticker is an equity (not FX, index, or crypto)."""
    if ticker.startswith('$'):
        return False
    if ticker.startswith('^'):
        return False
    if ticker.endswith('_X'):
        return False
    return True


def find_json_files(file_type: str) -> list[str]:
    """Find all parsed JSON files of given type, sorted by date."""
    json_dir = REPO_ROOT / 'parsed_json'
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})_' + re.escape(file_type) + r'\.json$')
    dates = []
    for f in json_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            dates.append(m.group(1))
    return sorted(dates)


def find_prior_date(today: str, file_type: str) -> str | None:
    """Find the most recent date before today that has a parsed JSON."""
    dates = find_json_files(file_type)
    prior = [d for d in dates if d < today]
    return prior[-1] if prior else None


def load_session(date: str, file_type: str) -> dict:
    """Load a parsed JSON session file."""
    path = REPO_ROOT / 'parsed_json' / f'{date}_{file_type}.json'
    if not path.exists():
        raise FileNotFoundError(f"No parsed JSON for {date} ({file_type}): {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_diff(today_data: dict, yesterday_data: dict) -> dict:
    """Compute all diff metrics between two sessions."""
    today_by_ticker = {s['ticker']: s for s in today_data['signals']}
    yesterday_by_ticker = {s['ticker']: s for s in yesterday_data['signals']}

    all_tickers = set(today_by_ticker.keys()) | set(yesterday_by_ticker.keys())

    new_buys = []
    new_exits = []
    bear_to_bull = []
    bull_to_bear = []
    mom_deltas = []

    for ticker in all_tickers:
        t = today_by_ticker.get(ticker)
        y = yesterday_by_ticker.get(ticker)

        if not t:
            continue

        # New Buy signals
        if t['signal_type'] == 'Buy':
            if not y or y['signal_type'] != 'Buy':
                new_buys.append(t)

        # New exit signals
        if t['signal_type'] in EXIT_SIGNALS:
            if not y or y['signal_type'] not in EXIT_SIGNALS:
                new_exits.append(t)

        # Mode transitions
        if y and t:
            y_mode = y.get('mode', '')
            t_mode = t.get('mode', '')

            if y_mode in BEARISH_MODES and t_mode in BULLISH_MODES:
                bear_to_bull.append(t)
            elif y_mode in BULLISH_MODES and t_mode in BEARISH_MODES:
                bull_to_bear.append(t)

        # MoM delta
        if y and t and t.get('mom') is not None and y.get('mom') is not None:
            delta = t['mom'] - y['mom']
            mom_deltas.append({**t, 'mom_delta': delta, 'mom_yesterday': y['mom']})

    # Sort results
    new_buys.sort(key=lambda s: s.get('r') or 0, reverse=True)
    new_exits.sort(key=lambda s: s.get('days') or 0, reverse=True)
    mom_deltas.sort(key=lambda s: s['mom_delta'], reverse=True)

    # Mode distribution
    today_modes = today_data.get('mode_counts', {})
    yesterday_modes = yesterday_data.get('mode_counts', {})

    today_total = today_data.get('total', 0)
    yesterday_total = yesterday_data.get('total', 0)

    # Bullish % = (DG + LG + Flips) / total
    today_bullish = sum(today_modes.get(m, 0) for m in BULLISH_MODES)
    yesterday_bullish = sum(yesterday_modes.get(m, 0) for m in BULLISH_MODES)
    today_bullish_pct = (today_bullish / today_total * 100) if today_total else 0
    yesterday_bullish_pct = (yesterday_bullish / yesterday_total * 100) if yesterday_total else 0

    # spBuy counts
    today_spbuy = sum(today_data.get('signal_counts', {}).get(s, 0) for s in SPBUY_SIGNALS)
    yesterday_spbuy = sum(yesterday_data.get('signal_counts', {}).get(s, 0) for s in SPBUY_SIGNALS)

    # Equity-only subsets
    bear_to_bull_equity = [s for s in bear_to_bull if is_equity(s['ticker'])]
    bull_to_bear_equity = [s for s in bull_to_bear if is_equity(s['ticker'])]

    return {
        'new_buys': new_buys,
        'new_exits': new_exits,
        'bear_to_bull': bear_to_bull,
        'bear_to_bull_equity': bear_to_bull_equity,
        'bull_to_bear': bull_to_bear,
        'bull_to_bear_equity': bull_to_bear_equity,
        'mom_deltas': mom_deltas[:20],
        'today_modes': today_modes,
        'yesterday_modes': yesterday_modes,
        'today_bullish_pct': today_bullish_pct,
        'yesterday_bullish_pct': yesterday_bullish_pct,
        'today_spbuy': today_spbuy,
        'yesterday_spbuy': yesterday_spbuy,
    }


def format_float(val, decimals=2) -> str:
    if val is None:
        return '-'
    return f"{val:.{decimals}f}"


def format_delta(val, decimals=0) -> str:
    if val is None:
        return '-'
    sign = '+' if val > 0 else ''
    if decimals == 0:
        return f"{sign}{int(val)}"
    return f"{sign}{val:.{decimals}f}"


def render_markdown(today_date: str, yesterday_date: str, diff: dict) -> str:
    """Render the diff as markdown."""
    lines = []
    lines.append(f"# Overnight Diff — {today_date}")
    lines.append(f"*Compared to {yesterday_date}*\n")

    # Summary
    lines.append("## Summary")
    lines.append(f"- **New Buy:** {len(diff['new_buys'])}")
    lines.append(f"- **New Sell/pP:** {len(diff['new_exits'])}")
    lines.append(f"- **Bear→Bull:** {len(diff['bear_to_bull'])} total ({len(diff['bear_to_bull_equity'])} equity)")
    lines.append(f"- **Bull→Bear:** {len(diff['bull_to_bear'])} total ({len(diff['bull_to_bear_equity'])} equity)")
    lines.append(f"- **spBuy count:** {diff['today_spbuy']} (was {diff['yesterday_spbuy']}, Δ {format_delta(diff['today_spbuy'] - diff['yesterday_spbuy'])})")
    lines.append("")

    # Mode Distribution
    lines.append("## Mode Distribution")
    lines.append("| Mode | Yesterday | Today | Δ |")
    lines.append("|------|-----------|-------|---|")
    for mode in ['Dark Green', 'Light Green', 'Light Red', 'Dark Red', 'Bear-Bull Flip', 'Bear-Bull (LR-LG)']:
        y_val = diff['yesterday_modes'].get(mode, 0)
        t_val = diff['today_modes'].get(mode, 0)
        delta = t_val - y_val
        lines.append(f"| {mode} | {y_val} | {t_val} | {format_delta(delta)} |")
    lines.append(f"| **Bullish %** | {diff['yesterday_bullish_pct']:.1f}% | {diff['today_bullish_pct']:.1f}% | {format_delta(diff['today_bullish_pct'] - diff['yesterday_bullish_pct'], 1)} |")
    lines.append("")

    # New Buy Signals
    if diff['new_buys']:
        lines.append("## Top New Buy Signals (by R)")
        lines.append("| Ticker | Name | Close | Mode | MoM | R | Days |")
        lines.append("|--------|------|-------|------|-----|---|------|")
        for s in diff['new_buys'][:25]:
            lines.append(f"| {s['ticker']} | {s['name']} | {format_float(s['close'])} | {s['mode']} | {format_float(s['mom'])} | {format_float(s['r'])} | {s.get('days', '-')} |")
        lines.append("")

    # New Exit Signals
    if diff['new_exits']:
        lines.append("## Top New Sell/pP Signals (by Days held)")
        lines.append("| Ticker | Name | Signal | Close | Mode | MoM | Days |")
        lines.append("|--------|------|--------|-------|------|-----|------|")
        for s in diff['new_exits'][:25]:
            lines.append(f"| {s['ticker']} | {s['name']} | {s['signal_type']} | {format_float(s['close'])} | {s['mode']} | {format_float(s['mom'])} | {s.get('days', '-')} |")
        lines.append("")

    # MoM Accelerators
    if diff['mom_deltas']:
        lines.append("## Biggest MoM Accelerators")
        lines.append("| Ticker | Name | MoM Yesterday | MoM Today | Δ MoM | Mode |")
        lines.append("|--------|------|---------------|-----------|-------|------|")
        for s in diff['mom_deltas']:
            lines.append(f"| {s['ticker']} | {s['name']} | {format_float(s['mom_yesterday'])} | {format_float(s['mom'])} | {format_delta(s['mom_delta'], 2)} | {s['mode']} |")
        lines.append("")

    # Bull→Bear Reversals
    if diff['bull_to_bear']:
        lines.append("## Equity Bull→Bear Reversals (WARNING SIGNAL)")
        lines.append("| Ticker | Name | Close | New Mode | MoM | R |")
        lines.append("|--------|------|-------|----------|-----|---|")
        equity_b2b = sorted(diff['bull_to_bear'], key=lambda s: s.get('r') or 0, reverse=True)
        for s in equity_b2b:
            lines.append(f"| {s['ticker']} | {s['name']} | {format_float(s['close'])} | {s['mode']} | {format_float(s['mom'])} | {format_float(s['r'])} |")
        lines.append("")

    # Bear→Bull Transitions
    if diff['bear_to_bull']:
        lines.append("## Bear→Bull Transitions")
        lines.append("| Ticker | Name | Close | New Mode | MoM | R |")
        lines.append("|--------|------|-------|----------|-----|---|")
        for s in sorted(diff['bear_to_bull'], key=lambda s: s.get('r') or 0, reverse=True):
            lines.append(f"| {s['ticker']} | {s['name']} | {format_float(s['close'])} | {s['mode']} | {format_float(s['mom'])} | {format_float(s['r'])} |")
        lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Compute overnight diff between two RL sessions')
    parser.add_argument('today', nargs='?', help='Today\'s date (YYYY-MM-DD)')
    parser.add_argument('yesterday', nargs='?', help='Prior session date (YYYY-MM-DD)')
    parser.add_argument('--today-auto', action='store_true',
                        help='Auto-detect today as most recent date, yesterday as second most recent')
    parser.add_argument('--file-type', choices=['daily', 'weekly'], default='daily')
    args = parser.parse_args()

    # Resolve dates
    if args.today_auto:
        dates = find_json_files(args.file_type)
        if len(dates) < 2:
            log(f"ERROR: Need at least 2 {args.file_type} JSON files for --today-auto. Found {len(dates)}.")
            sys.exit(1)
        today_date = dates[-1]
        yesterday_date = dates[-2]
    elif args.today:
        today_date = args.today
        if args.yesterday:
            yesterday_date = args.yesterday
        else:
            yesterday_date = find_prior_date(today_date, args.file_type)
            if not yesterday_date:
                log(f"ERROR: No prior {args.file_type} session found before {today_date}")
                sys.exit(1)
    else:
        log("ERROR: Provide a date or use --today-auto")
        sys.exit(1)

    log(f"Diffing {today_date} vs {yesterday_date} ({args.file_type})...")

    today_data = load_session(today_date, args.file_type)
    yesterday_data = load_session(yesterday_date, args.file_type)

    diff = compute_diff(today_data, yesterday_data)
    markdown = render_markdown(today_date, yesterday_date, diff)

    # Write output
    out_path = REPO_ROOT / 'analyses' / f'{today_date}_diff.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    log(f"Wrote {out_path.relative_to(REPO_ROOT)}")

    # Print summary
    log(f"New Buy: {len(diff['new_buys'])}")
    log(f"New Sell/pP: {len(diff['new_exits'])}")
    log(f"Bear→Bull: {len(diff['bear_to_bull'])} ({len(diff['bear_to_bull_equity'])} equity)")
    log(f"Bull→Bear: {len(diff['bull_to_bear'])} ({len(diff['bull_to_bear_equity'])} equity)")
    log(f"Bullish%: {diff['yesterday_bullish_pct']:.1f}% → {diff['today_bullish_pct']:.1f}%")
    log("Done.")


if __name__ == '__main__':
    main()
