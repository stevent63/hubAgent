#!/usr/bin/env python3
"""Tests for scripts/signal_search.py"""

import csv
import os
import sys
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import extract
import signal_search as ss


FIXTURE_DIR = PROJECT_ROOT / 'tests' / 'fixtures'


class Args:
    """Simple namespace for CLI args."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name):
        return None


class TestHelpers:
    def test_safe_float(self):
        assert ss.safe_float('1.23') == 1.23
        assert ss.safe_float('-5.3') == -5.3
        assert ss.safe_float('') is None
        assert ss.safe_float('None') is None

    def test_safe_int(self):
        assert ss.safe_int('5') == 5
        assert ss.safe_int('') is None

    def test_format_table_markdown(self):
        result = ss.format_table(['A', 'B'], [['1', '2'], ['3', '4']], 'markdown')
        assert '| A' in result
        assert '|---|' in result or '|--' in result

    def test_format_table_csv(self):
        result = ss.format_table(['A', 'B'], [['1', '2']], 'csv')
        assert 'A,B' in result
        assert '1,2' in result

    def test_format_table_json(self):
        result = ss.format_table(['A', 'B'], [['1', '2']], 'json')
        assert '"A": "1"' in result


class TestWithFixtureData:
    """Tests that use parsed fixture data in master CSVs."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_root = extract.REPO_ROOT
        self._orig_ss_root = ss.REPO_ROOT
        self._orig_master = ss.MASTER_HISTORY
        self._orig_signals = ss.MASTER_SIGNALS

        extract.REPO_ROOT = Path(self.tmpdir)
        ss.REPO_ROOT = Path(self.tmpdir)
        ss.MASTER_HISTORY = Path(self.tmpdir) / 'master' / 'master_history.csv'
        ss.MASTER_SIGNALS = Path(self.tmpdir) / 'master' / 'master_signals.csv'

        for d in ['parsed_json', 'parsed_csv', 'master']:
            os.makedirs(os.path.join(self.tmpdir, d))

        # Parse both fixtures and populate master CSVs
        data_13 = extract.parse_html(str(FIXTURE_DIR / '2026-04-13_daily.html'))
        extract.write_json(data_13)
        extract.write_csv(data_13)
        extract.append_master(data_13, 'master_history.csv')
        extract.append_master(data_13, 'master_signals.csv',
                              filter_fn=lambda s: s['signal_type'] != 'Hold')

        data_14 = extract.parse_html(str(FIXTURE_DIR / '2026-04-14_daily.html'))
        extract.write_json(data_14)
        extract.write_csv(data_14)
        extract.append_master(data_14, 'master_history.csv')
        extract.append_master(data_14, 'master_signals.csv',
                              filter_fn=lambda s: s['signal_type'] != 'Hold')

    def teardown_method(self):
        extract.REPO_ROOT = self._orig_root
        ss.REPO_ROOT = self._orig_ss_root
        ss.MASTER_HISTORY = self._orig_master
        ss.MASTER_SIGNALS = self._orig_signals
        shutil.rmtree(self.tmpdir)

    def test_load_master(self):
        rows = ss.load_master()
        # 14 rows from 04-13 + 13 rows from 04-14 = 27
        assert len(rows) == 27

    def test_get_available_dates(self):
        rows = ss.load_master()
        dates = ss.get_available_dates(rows)
        assert dates == ['2026-04-13', '2026-04-14']

    def test_ticker_query(self):
        ss.cmd_ticker(Args(symbol='AAPL', signal='', lookback_days=0,
                           forward_days=0, file_type='daily', format='markdown'))

    def test_ticker_with_signal_filter(self):
        ss.cmd_ticker(Args(symbol='INTC', signal='pP', lookback_days=0,
                           forward_days=0, file_type='daily', format='markdown'))

    def test_ticker_with_forward_days(self):
        ss.cmd_ticker(Args(symbol='AAPL', signal='', lookback_days=0,
                           forward_days=1, file_type='daily', format='markdown'))

    def test_events_query(self):
        ss.cmd_events(Args(signal='pP', start='', end='', file_type='daily', format='markdown'))

    def test_events_date_range(self):
        ss.cmd_events(Args(signal='Buy', start='2026-04-14', end='2026-04-14',
                           file_type='daily', format='markdown'))

    def test_trajectory(self):
        ss.cmd_trajectory(Args(symbol='AAPL', start='', end='',
                               file_type='daily', format='markdown'))

    def test_trajectory_with_dates(self):
        ss.cmd_trajectory(Args(symbol='NEM', start='2026-04-14', end='',
                               file_type='daily', format='markdown'))

    def test_persistence(self):
        # AAPL is DG on both days = 2 session streak
        ss.cmd_persistence(Args(mode='Dark Green', min_days=2,
                                file_type='daily', format='markdown'))

    def test_persistence_no_results(self):
        ss.cmd_persistence(Args(mode='Dark Green', min_days=100,
                                file_type='daily', format='markdown'))

    def test_hit_rate(self):
        # Buy signals on 04-14, forward 0 would need 04-15 data (doesn't exist)
        # But pP on 04-13 (ETR) with forward_days=1 can check 04-14
        ss.cmd_hit_rate(Args(signal='pP', forward_days=1, threshold=0,
                             file_type='daily', format='markdown'))

    def test_switch_no_weekly(self):
        # No weekly data → should log message and return
        ss.cmd_switch(Args(lookback_days=60, format='markdown'))

    def test_csv_format(self):
        ss.cmd_trajectory(Args(symbol='AAPL', start='', end='',
                               file_type='daily', format='csv'))

    def test_json_format(self):
        ss.cmd_trajectory(Args(symbol='AAPL', start='', end='',
                               file_type='daily', format='json'))

    def test_ticker_not_found(self):
        ss.cmd_ticker(Args(symbol='FAKESYMBOL', signal='', lookback_days=0,
                           forward_days=0, file_type='daily', format='markdown'))


if __name__ == '__main__':
    import traceback

    test_classes = [TestHelpers, TestWithFixtureData]
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
