#!/usr/bin/env python3
"""Tests for scripts/portfolio_track.py"""

import csv
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import extract
import portfolio_track as pt


class Args:
    """Simple namespace for CLI args — unlike MagicMock, returns None for unset attrs."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name):
        return None


FIXTURE_DIR = PROJECT_ROOT / 'tests' / 'fixtures'


class TestPortfolioCRUD:
    """Test portfolio ledger CRUD operations."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_root_extract = extract.REPO_ROOT
        self._orig_root_pt = pt.REPO_ROOT
        self._orig_ledger = pt.LEDGER_PATH

        extract.REPO_ROOT = Path(self.tmpdir)
        pt.REPO_ROOT = Path(self.tmpdir)
        pt.LEDGER_PATH = Path(self.tmpdir) / 'master' / 'portfolio_ledger.csv'

        for d in ['parsed_json', 'parsed_csv', 'master']:
            os.makedirs(os.path.join(self.tmpdir, d))

        # Parse fixtures into temp dir
        data_13 = extract.parse_html(str(FIXTURE_DIR / '2026-04-13_daily.html'))
        extract.write_json(data_13)
        data_14 = extract.parse_html(str(FIXTURE_DIR / '2026-04-14_daily.html'))
        extract.write_json(data_14)

    def teardown_method(self):
        extract.REPO_ROOT = self._orig_root_extract
        pt.REPO_ROOT = self._orig_root_pt
        pt.LEDGER_PATH = self._orig_ledger
        shutil.rmtree(self.tmpdir)

    def test_empty_ledger(self):
        ledger = pt.load_ledger()
        assert ledger == []

    def test_enter_position(self):
        args = Args()
        args.ticker = 'AAPL'
        args.date = '2026-04-14'
        args.signal = 'Buy'
        args.conviction = 'HIGH'
        args.theme = 'Tech'
        args.thesis = 'Testing'

        pt.cmd_enter(args)

        ledger = pt.load_ledger()
        assert len(ledger) == 1
        assert ledger[0]['ticker'] == 'AAPL'
        assert ledger[0]['status'] == 'OPEN'
        assert ledger[0]['entry_close'] == '260.49'
        assert ledger[0]['entry_mode'] == 'Dark Green'
        assert ledger[0]['conviction'] == 'HIGH'
        assert ledger[0]['theme'] == 'Tech'

    def test_exit_position(self):
        # Enter first
        enter_args = Args()
        enter_args.ticker = 'AAPL'
        enter_args.date = '2026-04-13'
        enter_args.signal = 'Buy'
        enter_args.conviction = 'HIGH'
        enter_args.theme = 'Tech'
        enter_args.thesis = ''
        pt.cmd_enter(enter_args)

        # Exit
        exit_args = Args()
        exit_args.ticker = 'AAPL'
        exit_args.date = '2026-04-14'
        exit_args.signal = 'pP'
        pt.cmd_exit(exit_args)

        ledger = pt.load_ledger()
        assert len(ledger) == 1
        assert ledger[0]['status'] == 'CLOSED'
        assert ledger[0]['exit_signal'] == 'pP'
        assert ledger[0]['exit_close'] == '260.49'
        assert float(ledger[0]['pnl_pct']) > 0  # 258.10 → 260.49

    def test_pnl_calculation(self):
        enter_args = Args()
        enter_args.ticker = 'AAPL'
        enter_args.date = '2026-04-13'
        enter_args.signal = 'Buy'
        enter_args.conviction = ''
        enter_args.theme = ''
        enter_args.thesis = ''
        pt.cmd_enter(enter_args)

        exit_args = Args()
        exit_args.ticker = 'AAPL'
        exit_args.date = '2026-04-14'
        exit_args.signal = 'Sell'
        pt.cmd_exit(exit_args)

        ledger = pt.load_ledger()
        # (260.49 - 258.10) / 258.10 * 100 = 0.926%
        pnl = float(ledger[0]['pnl_pct'])
        assert abs(pnl - 0.93) < 0.02

    def test_holding_days(self):
        days = pt.compute_holding_days('2026-04-07', '2026-04-14')
        # Mon Apr 7 to Mon Apr 14 = 5 business days
        assert days == 5

    def test_update_positions(self):
        enter_args = Args()
        enter_args.ticker = 'AAPL'
        enter_args.date = '2026-04-13'
        enter_args.signal = 'Buy'
        enter_args.conviction = ''
        enter_args.theme = ''
        enter_args.thesis = ''
        pt.cmd_enter(enter_args)

        update_args = Args()
        pt.cmd_update(update_args)

        ledger = pt.load_ledger()
        # Should be updated with 04-14 data (most recent)
        assert ledger[0]['current_close'] == '260.49'
        assert ledger[0]['last_updated'] == '2026-04-14'

    def test_exit_nonexistent_errors(self):
        exit_args = Args()
        exit_args.ticker = 'FAKE'
        exit_args.date = '2026-04-14'
        exit_args.signal = 'Sell'
        try:
            pt.cmd_exit(exit_args)
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass

    def test_enter_missing_json_errors(self):
        args = Args()
        args.ticker = 'AAPL'
        args.date = '2025-01-01'  # No JSON for this date
        args.signal = 'Buy'
        args.conviction = ''
        args.theme = ''
        args.thesis = ''
        try:
            pt.cmd_enter(args)
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass

    def test_verify_clean(self):
        enter_args = Args()
        enter_args.ticker = 'AAPL'
        enter_args.date = '2026-04-14'
        enter_args.signal = 'Buy'
        enter_args.conviction = ''
        enter_args.theme = ''
        enter_args.thesis = ''
        pt.cmd_enter(enter_args)

        verify_args = Args()
        pt.cmd_verify(verify_args)
        # Should not raise

    def test_multiple_entries(self):
        for ticker in ['AAPL', 'INTC', 'NEM']:
            args = Args()
            args.ticker = ticker
            args.date = '2026-04-14'
            args.signal = 'Buy'
            args.conviction = 'MED'
            args.theme = 'Test'
            args.thesis = ''
            pt.cmd_enter(args)

        ledger = pt.load_ledger()
        assert len(ledger) == 3
        assert all(r['status'] == 'OPEN' for r in ledger)

    def test_save_load_roundtrip(self):
        args = Args()
        args.ticker = 'GS'
        args.date = '2026-04-14'
        args.signal = 'Buy'
        args.conviction = 'HIGH'
        args.theme = 'Financials'
        args.thesis = 'Strong mode'
        pt.cmd_enter(args)

        # Load and verify all fields survive roundtrip
        ledger = pt.load_ledger()
        assert ledger[0]['conviction'] == 'HIGH'
        assert ledger[0]['theme'] == 'Financials'
        assert ledger[0]['thesis'] == 'Strong mode'


class TestLookup:
    def test_lookup_ticker_found(self):
        data = {'signals': [{'ticker': 'AAPL', 'close': 260.49}, {'ticker': 'INTC', 'close': 25.73}]}
        result = pt.lookup_ticker(data, 'AAPL')
        assert result['close'] == 260.49

    def test_lookup_ticker_missing(self):
        data = {'signals': [{'ticker': 'AAPL', 'close': 260.49}]}
        result = pt.lookup_ticker(data, 'FAKE')
        assert result is None


if __name__ == '__main__':
    import traceback

    test_classes = [TestPortfolioCRUD, TestLookup]
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        for method_name in dir(instance):
            if not method_name.startswith('test_'):
                continue
            if hasattr(instance, 'setup_method'):
                instance.setup_method()
            try:
                getattr(instance, method_name)()
                passed += 1
                print(f"  PASS: {cls.__name__}.{method_name}")
            except Exception as e:
                failed += 1
                errors.append((cls.__name__, method_name, e))
                print(f"  FAIL: {cls.__name__}.{method_name}: {e}")
                traceback.print_exc()
            finally:
                if hasattr(instance, 'teardown_method'):
                    instance.teardown_method()

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    if errors:
        print(f"\nFailures:")
        for cls_name, method, err in errors:
            print(f"  {cls_name}.{method}: {err}")
    sys.exit(0 if failed == 0 else 1)
