#!/usr/bin/env python3
"""
seed_portfolio.py — One-time batch seeder for portfolio ledger.

Transcribed from ~/Downloads/portfolio_seed.md. Writes directly to
master/portfolio_ledger.csv using portfolio_track's save_ledger().

Run once:
    python3 scripts/seed_portfolio.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to path so we can import portfolio_track
sys.path.insert(0, str(Path(__file__).resolve().parent))

import portfolio_track as pt

SEED_NOTE = 'approximate entry — reconstructed from session history; awaiting historical backfill'

# ── OPEN POSITIONS ──────────────────────────────────────────────────────────

OPEN_POSITIONS = [
    # Semi / Storage / AI Infrastructure
    {'ticker': 'SNDK', 'entry_date': '2026-03-11', 'entry_signal': 'spBuy', 'conviction': 'HIGH', 'theme': 'Semi/Storage', 'thesis': 'Memory cycle capitulation — NAND flash deepest weekly compression'},
    {'ticker': 'WDC',  'entry_date': '2026-03-11', 'entry_signal': 'spBuy', 'conviction': 'HIGH', 'theme': 'Semi/Storage', 'thesis': 'Storage recovery alongside SNDK'},
    {'ticker': 'STX',  'entry_date': '2026-03-11', 'entry_signal': 'spBuy', 'conviction': 'HIGH', 'theme': 'Semi/Storage', 'thesis': 'Storage duopoly with WDC'},
    {'ticker': 'INTC', 'entry_date': '2026-03-11', 'entry_signal': 'spBuy', 'conviction': 'HIGH', 'theme': 'Semi', 'thesis': 'Semi capitulation entry — validated by +8.52 MoM acceleration'},
    {'ticker': 'TER',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Semi Test', 'thesis': 'Semi test duopoly (TER + Advantest) — 39-week compression'},
    {'ticker': 'FORM', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Semi Equipment', 'thesis': 'Probe card leader'},
    {'ticker': 'MKSI', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Semi Equipment', 'thesis': 'Vacuum/plasma control — elite R at flip'},
    {'ticker': 'AEIS', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Semi Power', 'thesis': 'Precision power conversion'},
    {'ticker': 'GLW',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Optical/Fiber', 'thesis': 'Corning fiber optic recovery'},
    {'ticker': 'ASX',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Semi Packaging', 'thesis': 'ASE Technology packaging'},
    {'ticker': 'AMD',  'entry_date': '2026-04-02', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Semi/GPU', 'thesis': 'CPU/GPU cycle participation'},
    {'ticker': 'PLAB', 'entry_date': '2026-04-07', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Semi Equipment', 'thesis': 'Photronics photomask leader'},
    {'ticker': 'POWL', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Power Infra', 'thesis': 'AI power grid infrastructure — fastest MoM accelerator'},
    {'ticker': 'ENS',  'entry_date': '2026-04-07', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Power/Battery', 'thesis': 'EnerSys — stored energy systems'},
    {'ticker': 'MOD',  'entry_date': '2026-04-07', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Power/Thermal', 'thesis': 'Modine thermal management'},

    # Mining / Metals
    {'ticker': 'CENX', 'entry_date': '2026-03-20', 'entry_signal': 'spBuy+', 'conviction': 'HIGH', 'theme': 'Mining/Aluminum', 'thesis': 'US aluminum supply deficit play'},
    {'ticker': 'AA',   'entry_date': '2026-03-20', 'entry_signal': 'spBuy', 'conviction': 'HIGH', 'theme': 'Mining/Aluminum', 'thesis': 'Alcoa — aluminum cycle turn'},
    {'ticker': 'NEM',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Mining/Gold', 'thesis': 'Gold mega-cap — institutional gold exposure'},
    {'ticker': 'RGLD', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Mining/Gold', 'thesis': 'Gold royalty — lower risk gold exposure'},
    {'ticker': 'SSRM', 'entry_date': '2026-03-31', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Mining/Silver', 'thesis': 'SSR Mining — silver leader'},
    {'ticker': 'PAAS', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/Silver', 'thesis': 'Pan American Silver broadening'},
    {'ticker': 'SVM',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/Silver', 'thesis': 'Silvercorp Metals'},
    {'ticker': 'TGB',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/Copper', 'thesis': 'Taseko Mines'},
    {'ticker': 'IAG',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/Gold', 'thesis': 'Iamgold — smaller gold producer'},
    {'ticker': 'NEXA', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/Zinc', 'thesis': 'Zinc / base metals diversification'},
    {'ticker': 'BVN',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/LatAm', 'thesis': 'Buenaventura — Peru exposure'},
    {'ticker': 'COPX', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/ETF', 'thesis': 'Copper miners ETF — broad exposure'},
    {'ticker': 'GDX',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/ETF', 'thesis': 'Gold miners ETF'},
    {'ticker': 'XBI',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Biotech/ETF', 'thesis': 'Biotech ETF — broad biotech exposure'},
    {'ticker': 'SPHR', 'entry_date': '2026-04-07', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Mining/Platinum', 'thesis': 'Sphere Entertainment — PGM exposure'},
    {'ticker': 'BURL', 'entry_date': '2026-03-31', 'entry_signal': 'Buy', 'conviction': 'LOW', 'theme': 'Consumer', 'thesis': 'Burlington — discount retail'},

    # Biotech
    {'ticker': 'PRAX', 'entry_date': '2026-04-08', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Biotech', 'thesis': 'Highest R biotech — elite signal with minimal extension'},
    {'ticker': 'ARWR', 'entry_date': '2026-04-04', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Biotech/RNA', 'thesis': 'Arrowhead — RNA therapeutics platform'},
    {'ticker': 'KYMR', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Biotech', 'thesis': 'Kymera — protein degradation'},
    {'ticker': 'BBIO', 'entry_date': '2026-03-24', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Biotech', 'thesis': 'BridgeBio — rare disease portfolio'},
    {'ticker': 'APGE', 'entry_date': '2026-03-31', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Biotech', 'thesis': 'Apogee Therapeutics'},
    {'ticker': 'COGT', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Biotech', 'thesis': 'Cogent Biosciences'},
    {'ticker': 'LQDA', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Biotech', 'thesis': 'Liquidia Corp'},
    {'ticker': 'DAN',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Industrial', 'thesis': 'Dana Inc — industrials/autos'},
    {'ticker': 'EWTX', 'entry_date': '2026-03-24', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Biotech', 'thesis': 'Edgewise Therapeutics'},

    # Utilities / Defensive
    {'ticker': 'EIX',  'entry_date': '2026-04-04', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Utilities', 'thesis': 'Edison International — defensive positioning'},
    {'ticker': 'AEP',  'entry_date': '2026-04-04', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Utilities', 'thesis': 'American Electric Power'},
    {'ticker': 'NEE',  'entry_date': '2026-04-04', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Utilities', 'thesis': 'NextEra Energy — largest US utility'},
    {'ticker': 'ATO',  'entry_date': '2026-04-04', 'entry_signal': 'Buy', 'conviction': 'LOW', 'theme': 'Utilities', 'thesis': 'Atmos Energy — gas utility'},

    # Satellite / Space / Telecom
    {'ticker': 'GSAT', 'entry_date': '2026-03-28', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Satellite', 'thesis': 'Globalstar — direct-to-phone satellite'},
    {'ticker': 'SATS', 'entry_date': '2026-04-01', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Satellite', 'thesis': 'EchoStar — satellite broadband'},

    # Financials / Industrial
    {'ticker': 'GS',   'entry_date': '2026-04-07', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Financials', 'thesis': 'Goldman — capital markets cycle'},
    {'ticker': 'MBIN', 'entry_date': '2026-04-01', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Financials', 'thesis': 'Merchants Bancorp — niche bank'},
    {'ticker': 'BSAC', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'LatAm/Banks', 'thesis': 'Banco Santander Chile'},
    {'ticker': 'CAT',  'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'HIGH', 'theme': 'Industrials', 'thesis': 'Caterpillar — industrial bellwether (leader confirmed)'},
    {'ticker': 'PSMT', 'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Consumer/LatAm', 'thesis': 'PriceSmart — LatAm membership retail'},

    # Energy-Adjacent
    {'ticker': 'FRO',  'entry_date': '2026-02-28', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Energy/Tankers', 'thesis': 'Frontline — tanker rates — last energy survivor'},
    {'ticker': 'NGL',  'entry_date': '2026-03-31', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Energy/Midstream', 'thesis': 'NGL Energy Partners'},

    # Specialty / Biotech
    {'ticker': 'ALB',  'entry_date': '2026-03-31', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Specialty Chem', 'thesis': 'Albemarle — lithium'},
    {'ticker': 'CX',   'entry_date': '2026-04-03', 'entry_signal': 'Buy', 'conviction': 'MED', 'theme': 'Building Materials', 'thesis': 'Cemex — LatAm cement'},
]

# ── CLOSED POSITIONS (enter first, then exit) ──────────────────────────────

CLOSED_POSITIONS = [
    # (entry fields, then exit fields)
    {
        'ticker': 'AXGN', 'entry_date': '2026-03-31', 'entry_signal': 'Buy',
        'conviction': 'MED', 'theme': 'Biotech/Medtech',
        'thesis': 'First portfolio exit of cycle',
        'exit_date': '2026-04-08', 'exit_signal': 'Sell',
        'exit_notes': 'Sell signal after mode flipped Unknown',
    },
    {
        'ticker': 'HCC', 'entry_date': '2026-03-20', 'entry_signal': 'Buy',
        'conviction': 'MED', 'theme': 'Energy/Coal',
        'thesis': 'Metallurgical coal',
        'exit_date': '2026-04-10', 'exit_signal': 'Sell',
        'exit_notes': 'Theme never fully participated',
    },
    {
        'ticker': 'GH', 'entry_date': '2026-04-03', 'entry_signal': 'Buy',
        'conviction': 'MED', 'theme': 'Biotech/Dx',
        'thesis': 'Triple Crown entry that failed',
        'exit_date': '2026-04-10', 'exit_signal': 'Sell',
        'exit_notes': '-9.48% loss',
        'pnl_pct': '-9.48',
    },
    {
        'ticker': 'ETR', 'entry_date': '2026-04-02', 'entry_signal': 'Buy',
        'conviction': 'MED', 'theme': 'Utilities',
        'thesis': 'Utility rotation play',
        'exit_date': '2026-04-13', 'exit_signal': 'pP',
        'exit_notes': 'First portfolio pP profit-take at +4.42%',
        'pnl_pct': '4.42',
    },
    {
        'ticker': 'KOD', 'entry_date': '2026-04-03', 'entry_signal': 'Buy',
        'conviction': 'MED', 'theme': 'Biotech',
        'thesis': 'Kodiak Sciences',
        'exit_date': '2026-04-13', 'exit_signal': 'pP',
        'exit_notes': 'Profit-take at +2.91% — flat price with high MoM = mature',
        'pnl_pct': '2.91',
    },
    {
        'ticker': 'FCX', 'entry_date': '2026-04-03', 'entry_signal': 'Buy',
        'conviction': 'HIGH', 'theme': 'Mining/Copper',
        'thesis': 'Copper supply deficit + metals broadening wave',
        'exit_date': '2026-04-14', 'exit_signal': 'pP',
        'exit_notes': 'Copper complex profit-take at +11.98%',
        'pnl_pct': '11.98',
    },
    {
        'ticker': 'HBM', 'entry_date': '2026-04-03', 'entry_signal': 'Buy',
        'conviction': 'MED', 'theme': 'Mining/Copper',
        'thesis': 'Hudbay Minerals — copper complex',
        'exit_date': '2026-04-14', 'exit_signal': 'pP',
        'exit_notes': 'Copper complex profit-take at +18.61%',
        'pnl_pct': '18.61',
    },
    {
        'ticker': 'SCCO', 'entry_date': '2026-04-03', 'entry_signal': 'Buy',
        'conviction': 'MED', 'theme': 'Mining/Copper',
        'thesis': 'Southern Copper — copper major',
        'exit_date': '2026-04-14', 'exit_signal': 'pP',
        'exit_notes': 'Copper complex profit-take at +15.56%',
        'pnl_pct': '15.56',
    },
]


def main():
    # Clear any existing ledger to avoid duplicates on re-run
    existing = pt.load_ledger()
    if existing:
        print(f"[seed] WARNING: Ledger already has {len(existing)} rows. Overwriting with fresh seed.")

    ledger = []
    entered_open = 0
    entered_closed = 0
    skipped = 0

    # Pass 1: Enter all open positions
    print(f"\n{'='*60}")
    print(f"[seed] Pass 1: Entering {len(OPEN_POSITIONS)} open positions...")
    print(f"{'='*60}")

    for pos in OPEN_POSITIONS:
        row = {
            'entry_date': pos['entry_date'],
            'ticker': pos['ticker'],
            'name': '',
            'entry_signal': pos['entry_signal'],
            'entry_mode': '',
            'entry_mom': '',
            'entry_r': '',
            'entry_close': '',
            'entry_revl': '',
            'entry_tr_weeks': '',
            'conviction': pos['conviction'],
            'theme': pos['theme'],
            'thesis': pos['thesis'],
            'exit_date': '',
            'exit_signal': '',
            'exit_close': '',
            'exit_mom': '',
            'holding_days': '',
            'pnl_pct': '',
            'pnl_dollars_per_share': '',
            'status': 'OPEN',
            'notes': SEED_NOTE,
            'current_close': '',
            'current_mom': '',
            'current_mode': '',
            'last_updated': pos['entry_date'],
        }
        ledger.append(row)
        entered_open += 1
        print(f"  OPEN  {pos['ticker']:<6} {pos['entry_date']} {pos['entry_signal']:<8} {pos['conviction']:<4} {pos['theme']}")

    # Pass 2: Enter closed positions as OPEN, then close them
    print(f"\n{'='*60}")
    print(f"[seed] Pass 2: Entering + closing {len(CLOSED_POSITIONS)} closed positions...")
    print(f"{'='*60}")

    for pos in CLOSED_POSITIONS:
        holding_days = pt.compute_holding_days(pos['entry_date'], pos['exit_date'])
        pnl = pos.get('pnl_pct', '')

        notes_parts = [SEED_NOTE]
        if pos.get('exit_notes'):
            notes_parts.append(pos['exit_notes'])

        row = {
            'entry_date': pos['entry_date'],
            'ticker': pos['ticker'],
            'name': '',
            'entry_signal': pos['entry_signal'],
            'entry_mode': '',
            'entry_mom': '',
            'entry_r': '',
            'entry_close': '',
            'entry_revl': '',
            'entry_tr_weeks': '',
            'conviction': pos['conviction'],
            'theme': pos['theme'],
            'thesis': pos['thesis'],
            'exit_date': pos['exit_date'],
            'exit_signal': pos['exit_signal'],
            'exit_close': '',
            'exit_mom': '',
            'holding_days': holding_days,
            'pnl_pct': pnl,
            'pnl_dollars_per_share': '',
            'status': 'CLOSED',
            'notes': '; '.join(notes_parts),
            'current_close': '',
            'current_mom': '',
            'current_mode': '',
            'last_updated': pos['exit_date'],
        }
        ledger.append(row)
        entered_closed += 1
        pnl_str = f"{float(pnl):+.2f}%" if pnl else 'unknown'
        print(f"  CLOSED {pos['ticker']:<6} {pos['entry_date']} → {pos['exit_date']} {pos['exit_signal']:<6} {holding_days:>3}d  P&L: {pnl_str}  {pos['theme']}")

    # Save
    pt.save_ledger(ledger)

    print(f"\n{'='*60}")
    print(f"[seed] COMPLETE")
    print(f"{'='*60}")
    print(f"  Open positions:   {entered_open}")
    print(f"  Closed positions: {entered_closed}")
    print(f"  Skipped:          {skipped}")
    print(f"  Total rows:       {len(ledger)}")
    print(f"  Ledger written:   {pt.LEDGER_PATH}")
    print(f"\nNote: entry_close/mom/r/mode/revl fields are blank — awaiting historical HTML backfill.")
    print(f"Run 'python3 scripts/portfolio_track.py verify' to check integrity.")


if __name__ == '__main__':
    main()
