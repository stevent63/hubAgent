#!/usr/bin/env python3
"""Tests for scripts/diff.py"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import extract
import diff


FIXTURE_DIR = PROJECT_ROOT / 'tests' / 'fixtures'


class TestEquityFilter:
    def test_equity(self):
        assert diff.is_equity('AAPL') is True
        assert diff.is_equity('FCX') is True

    def test_fx(self):
        assert diff.is_equity('$DXY') is False

    def test_index(self):
        assert diff.is_equity('^SPX') is False

    def test_crypto(self):
        assert diff.is_equity('BTC_X') is False


class TestDiffComputation:
    """Test diff logic using parsed fixture data."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        # Parse both fixtures into temp dir
        self._orig_root_extract = extract.REPO_ROOT
        self._orig_root_diff = diff.REPO_ROOT
        extract.REPO_ROOT = Path(self.tmpdir)
        diff.REPO_ROOT = Path(self.tmpdir)
        for d in ['parsed_json', 'parsed_csv', 'analyses']:
            os.makedirs(os.path.join(self.tmpdir, d))
        # Parse fixtures
        data_13 = extract.parse_html(str(FIXTURE_DIR / '2026-04-13_daily.html'))
        extract.write_json(data_13)
        data_14 = extract.parse_html(str(FIXTURE_DIR / '2026-04-14_daily.html'))
        extract.write_json(data_14)

    def teardown_method(self):
        extract.REPO_ROOT = self._orig_root_extract
        diff.REPO_ROOT = self._orig_root_diff
        shutil.rmtree(self.tmpdir)

    def test_load_sessions(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        assert today['date'] == '2026-04-14'
        assert yesterday['date'] == '2026-04-13'

    def test_new_buys(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        buy_tickers = [s['ticker'] for s in result['new_buys']]
        # AMD went from Hold to Buy, CAT went from Hold to Buy
        assert 'AMD' in buy_tickers
        assert 'CAT' in buy_tickers

    def test_new_exits(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        exit_tickers = [s['ticker'] for s in result['new_exits']]
        # INTC went from Hold to pP, XOM went from Hold to Sell, NEE went from Hold to dSell
        assert 'INTC' in exit_tickers
        assert 'XOM' in exit_tickers
        assert 'NEE' in exit_tickers

    def test_bear_to_bull(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        b2b_tickers = [s['ticker'] for s in result['bear_to_bull']]
        # CAT: LR -> Bear-Bull Flip, AMD: LR -> LG, DG: LR -> Bear-Bull (LR-LG)
        assert 'CAT' in b2b_tickers
        assert 'AMD' in b2b_tickers
        assert 'DG' in b2b_tickers

    def test_bull_to_bear(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        btb_tickers = [s['ticker'] for s in result['bull_to_bear']]
        # NEE: LG -> LR
        assert 'NEE' in btb_tickers

    def test_equity_filtering(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        # $DXY should not be in equity lists
        equity_b2b_tickers = [s['ticker'] for s in result['bear_to_bull_equity']]
        assert '$DXY' not in equity_b2b_tickers

    def test_mom_deltas(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        # Should have mom deltas sorted descending
        assert len(result['mom_deltas']) > 0
        # AMD went from -0.50 to 8.05 = +8.55, should be biggest
        first = result['mom_deltas'][0]
        assert first['ticker'] == 'AMD'
        assert abs(first['mom_delta'] - 8.55) < 0.01

    def test_mode_distribution(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        assert 'today_modes' in result
        assert 'yesterday_modes' in result

    def test_markdown_output(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        md = diff.render_markdown('2026-04-14', '2026-04-13', result)
        assert '# Overnight Diff — 2026-04-14' in md
        assert '## Summary' in md
        assert '## Mode Distribution' in md
        assert 'Bear→Bull' in md

    def test_find_json_files(self):
        dates = diff.find_json_files('daily')
        assert '2026-04-13' in dates
        assert '2026-04-14' in dates
        assert dates == sorted(dates)

    def test_find_prior_date(self):
        prior = diff.find_prior_date('2026-04-14', 'daily')
        assert prior == '2026-04-13'

    def test_spbuy_counts(self):
        today = diff.load_session('2026-04-14', 'daily')
        yesterday = diff.load_session('2026-04-13', 'daily')
        result = diff.compute_diff(today, yesterday)
        # 04-14 has spBuy=1, 04-13 has spBuy=0
        assert result['today_spbuy'] == 1
        assert result['yesterday_spbuy'] == 0


if __name__ == '__main__':
    import traceback

    test_classes = [TestEquityFilter, TestDiffComputation]
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
