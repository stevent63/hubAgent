#!/usr/bin/env python3
"""
extract.py — Parse RL HTML files into JSON, CSV, and master append files.

Usage:
    python3 scripts/extract.py raw_html/2026-04-14_daily.html
    python3 scripts/extract.py raw_html/2026-04-14_daily.html --file-type daily
    python3 scripts/extract.py raw_html/2026-04-14_daily.html --no-master-append
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from bs4 import BeautifulSoup

# CSS class → mode name
MODE_MAP = {
    'c4': 'Dark Green',
    'c5': 'Light Green',
    'c6': 'Dark Red',
    'c7': 'Light Red',
    'c20': 'Bear-Bull Flip',
    'c21': 'Bear-Bull (LR-LG)',
}

# All known signal types for validation
KNOWN_SIGNALS = {
    'Buy', 'dBuy', 'spBuy', 'spBuy+', 'spBuy++', 'wBuy',
    'Sell', 'dSell',
    'pP', 'pP+',
    'AddSh', 'Add',
    'Hold',
}

CSV_COLUMNS = [
    'date', 'file_type', 'ticker', 'name', 'close', 'mode', 'mode_css',
    'revl', 'mom', 'r', 'days', 'tr_weeks', 'pl_raw', 'pl_num', 'signal_type',
]

# Repo root — scripts/ is one level down from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent


def log(msg: str) -> None:
    print(f"[extract.py] {msg}")


def parse_date_and_type(filepath: str) -> tuple[str, str | None]:
    """Extract date and file type from filename pattern YYYY-MM-DD_{daily|weekly}.html."""
    basename = Path(filepath).name
    match = re.match(r'^(\d{4}-\d{2}-\d{2})_(daily|weekly)\.html$', basename)
    if not match:
        raise ValueError(
            f"Filename '{basename}' does not match expected pattern "
            f"YYYY-MM-DD_{{daily|weekly}}.html"
        )
    return match.group(1), match.group(2)


def detect_file_type(headers: list[str]) -> str:
    """Auto-detect daily vs weekly from column headers."""
    headers_lower = [h.lower().strip() for h in headers]
    if 'weeks' in headers_lower:
        return 'weekly'
    if 'days' in headers_lower:
        return 'daily'
    # Fallback: check for weekly-specific headers
    if any('(w)' in h for h in headers_lower):
        return 'weekly'
    return 'daily'


def extract_mode(td_element) -> tuple[str, str]:
    """Extract mode from CSS classes on the <td> element. Returns (mode_name, css_class)."""
    classes = td_element.get('class', [])
    for cls in classes:
        if cls in MODE_MAP:
            return MODE_MAP[cls], cls
    return 'Unknown', ''


def parse_float(value: str, field_name: str = '', row_context: str = '') -> float | None:
    """Parse a string to float, handling $, commas, %, and blanks."""
    if value is None:
        return None
    cleaned = value.strip().replace('$', '').replace(',', '').replace('%', '')
    if cleaned == '' or cleaned == '-' or cleaned == 'N/A':
        return None
    try:
        return float(cleaned)
    except ValueError:
        if field_name:
            log(f"WARNING: Could not parse {field_name}='{value}' {row_context}")
        return None


def parse_int(value: str, field_name: str = '', row_context: str = '') -> int | None:
    """Parse a string to int, handling blanks."""
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == '' or cleaned == '-' or cleaned == 'N/A':
        return None
    try:
        return int(cleaned)
    except ValueError:
        if field_name:
            log(f"WARNING: Could not parse {field_name}='{value}' {row_context}")
        return None


def find_signal_table(soup: BeautifulSoup) -> tuple:
    """Find the main signal table — largest table with an 'Action' column header."""
    tables = soup.find_all('table')
    if not tables:
        raise ValueError("No <table> elements found in HTML file")

    best_table = None
    best_headers = None
    best_row_count = 0

    for table in tables:
        header_row = table.find('tr')
        if not header_row:
            continue
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        if 'Action' not in headers:
            continue
        rows = table.find_all('tr')[1:]  # skip header
        if len(rows) > best_row_count:
            best_table = table
            best_headers = headers
            best_row_count = len(rows)

    if best_table is None:
        raise ValueError(
            "No table found with 'Action' column header. "
            "Check that the HTML file contains the RL signal table."
        )

    return best_table, best_headers


def parse_html(filepath: str, file_type_override: str | None = None) -> dict:
    """Parse an RL HTML file and return structured data."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    date_str, filename_type = parse_date_and_type(str(filepath))
    log(f"Parsing {filepath.name}...")

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'lxml')
    table, headers = find_signal_table(soup)

    # Detect file type from headers, override if specified
    detected_type = detect_file_type(headers)
    file_type = file_type_override or filename_type or detected_type
    log(f"Detected file type: {file_type}")

    # Find column indices by header name
    action_idx = headers.index('Action')

    # Parse rows
    data_rows = table.find_all('tr')[1:]  # skip header row
    signals = []
    warnings = []

    for row_idx, tr in enumerate(data_rows):
        tds = tr.find_all('td')
        if len(tds) < 8:
            log(f"WARNING: Row {row_idx} has only {len(tds)} cells, skipping")
            continue

        row_context = f"(row {row_idx})"
        try:
            name = tds[0].get_text(strip=True)
            ticker = tds[1].get_text(strip=True)
            row_context = f"(row {row_idx}, {ticker})"

            close = parse_float(tds[2].get_text(strip=True), 'close', row_context)
            tr_weeks = parse_int(tds[3].get_text(strip=True), 'tr_weeks', row_context)
            mode, mode_css = extract_mode(tds[4])
            revl = parse_float(tds[5].get_text(strip=True), 'revl', row_context)
            mom = parse_float(tds[6].get_text(strip=True), 'mom', row_context)
            days = parse_int(tds[7].get_text(strip=True), 'days', row_context)
            pl_raw = tds[8].get_text(strip=True) if len(tds) > 8 else None
            pl_num = parse_float(pl_raw, 'pl_num', row_context) if pl_raw else None

            # R value at index 10 (skip index 9 which is Envelope)
            r_value = None
            if len(tds) > 10:
                r_value = parse_float(tds[10].get_text(strip=True), 'r', row_context)

            # Action column — find by header index
            signal_type = 'Hold'
            if len(tds) > action_idx:
                signal_text = tds[action_idx].get_text(strip=True)
                if signal_text and signal_text in KNOWN_SIGNALS:
                    signal_type = signal_text
                elif signal_text and signal_text != '':
                    log(f"WARNING: Unknown signal '{signal_text}' {row_context}")
                    signal_type = signal_text  # Store it anyway

            if mode == 'Unknown':
                log(f"WARNING: Unknown mode CSS for {ticker} {row_context}")

            signals.append({
                'ticker': ticker,
                'name': name,
                'close': close,
                'mode': mode,
                'mode_css': mode_css,
                'revl': revl,
                'mom': mom,
                'r': r_value,
                'days': days,
                'tr_weeks': tr_weeks,
                'pl_raw': pl_raw,
                'pl_num': pl_num,
                'signal_type': signal_type,
            })
        except Exception as e:
            log(f"WARNING: Error parsing row {row_idx}: {e}")
            warnings.append(f"Row {row_idx}: {e}")
            continue

    log(f"Extracted {len(signals)} rows")

    # Deduplication by (name, ticker, signal_type)
    seen = set()
    deduped = []
    dup_count = 0
    for sig in signals:
        key = (sig['name'], sig['ticker'], sig['signal_type'])
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        deduped.append(sig)

    if dup_count > 0:
        log(f"Deduplicated {dup_count} rows (compound key collisions)")

    signals = deduped

    # Compute mode counts
    mode_counts = {}
    for sig in signals:
        m = sig['mode']
        mode_counts[m] = mode_counts.get(m, 0) + 1

    # Compute signal counts
    signal_counts = {}
    for sig in signals:
        s = sig['signal_type']
        signal_counts[s] = signal_counts.get(s, 0) + 1

    # Log summary
    mode_summary = ' '.join(
        f"{k.replace('Dark Green', 'DG').replace('Light Green', 'LG').replace('Dark Red', 'DR').replace('Light Red', 'LR').replace('Bear-Bull Flip', 'Flips').replace('Bear-Bull (LR-LG)', 'LR-LG')}={v}"
        for k, v in sorted(mode_counts.items())
    )
    log(f"Mode distribution: {mode_summary}")

    signal_summary = ' '.join(f"{k}={v}" for k, v in sorted(signal_counts.items(), key=lambda x: -x[1]))
    log(f"Signal counts: {signal_summary}")

    return {
        'date': date_str,
        'file_type': file_type,
        'source_file': str(filepath),
        'extracted_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'total': len(signals),
        'mode_counts': mode_counts,
        'signal_counts': signal_counts,
        'signals': signals,
    }


def write_json(data: dict) -> Path:
    """Write parsed data to JSON file."""
    out_path = REPO_ROOT / 'parsed_json' / f"{data['date']}_{data['file_type']}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log(f"Wrote {out_path.relative_to(REPO_ROOT)}")
    return out_path


def write_csv(data: dict) -> Path:
    """Write parsed data to per-file CSV."""
    out_path = REPO_ROOT / 'parsed_csv' / f"{data['date']}_{data['file_type']}.csv"
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for sig in data['signals']:
            row = {
                'date': data['date'],
                'file_type': data['file_type'],
                **sig,
            }
            writer.writerow({k: row.get(k) for k in CSV_COLUMNS})
    log(f"Wrote {out_path.relative_to(REPO_ROOT)}")
    return out_path


def append_master(data: dict, master_filename: str, filter_fn=None) -> int:
    """Append rows to a master CSV. Returns count of rows appended."""
    master_path = REPO_ROOT / 'master' / master_filename
    signals = data['signals']
    if filter_fn:
        signals = [s for s in signals if filter_fn(s)]

    # Load existing keys for idempotency check
    existing_keys = set()
    if master_path.exists():
        with open(master_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get('date', ''), row.get('file_type', ''), row.get('ticker', ''))
                existing_keys.add(key)

    # Determine rows to append
    new_rows = []
    for sig in signals:
        key = (data['date'], data['file_type'], sig['ticker'])
        if key not in existing_keys:
            new_rows.append(sig)

    if not new_rows:
        log(f"No new rows to append to {master_filename} (idempotency: all rows already present)")
        return 0

    # Write header if file doesn't exist or is empty
    write_header = not master_path.exists() or master_path.stat().st_size == 0

    with open(master_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        for sig in new_rows:
            row = {
                'date': data['date'],
                'file_type': data['file_type'],
                **sig,
            }
            writer.writerow({k: row.get(k) for k in CSV_COLUMNS})

    return len(new_rows)


def main():
    parser = argparse.ArgumentParser(description='Parse RL HTML files into JSON/CSV/master')
    parser.add_argument('filepath', help='Path to RL HTML file')
    parser.add_argument('--file-type', choices=['daily', 'weekly'], default=None,
                        help='Override file type detection')
    parser.add_argument('--no-master-append', action='store_true',
                        help='Skip appending to master CSV files')
    args = parser.parse_args()

    # Parse the HTML
    data = parse_html(args.filepath, file_type_override=args.file_type)

    # Write outputs
    write_json(data)
    write_csv(data)

    if not args.no_master_append:
        history_count = append_master(data, 'master_history.csv')
        log(f"Appended {history_count} rows to master_history.csv")

        signal_count = append_master(
            data, 'master_signals.csv',
            filter_fn=lambda s: s['signal_type'] != 'Hold'
        )
        log(f"Appended {signal_count} signal events to master_signals.csv")

    log("Done.")


if __name__ == '__main__':
    main()
