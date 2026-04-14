#!/usr/bin/env python3
"""Tests for scripts/extract.py"""

import csv
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import extract


FIXTURE_DIR = PROJECT_ROOT / 'tests' / 'fixtures'
DAILY_FIXTURE = FIXTURE_DIR / '2026-04-14_daily.html'


class TestDateParsing:
    def test_valid_daily(self):
        date, ftype = extract.parse_date_and_type('raw_html/2026-04-14_daily.html')
        assert date == '2026-04-14'
        assert ftype == 'daily'

    def test_valid_weekly(self):
        date, ftype = extract.parse_date_and_type('raw_html/2026-04-14_weekly.html')
        assert date == '2026-04-14'
        assert ftype == 'weekly'

    def test_invalid_filename(self):
        try:
            extract.parse_date_and_type('bad_filename.html')
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_nested_path(self):
        date, ftype = extract.parse_date_and_type('/some/deep/path/2025-12-01_daily.html')
        assert date == '2025-12-01'
        assert ftype == 'daily'


class TestParseHelpers:
    def test_parse_float_dollar(self):
        assert extract.parse_float('$260.49') == 260.49

    def test_parse_float_comma(self):
        assert extract.parse_float('$1,260.49') == 1260.49

    def test_parse_float_negative(self):
        assert extract.parse_float('-5.30') == -5.30

    def test_parse_float_percent(self):
        assert extract.parse_float('+1.69%') == 1.69

    def test_parse_float_blank(self):
        assert extract.parse_float('') is None

    def test_parse_float_none(self):
        assert extract.parse_float(None) is None

    def test_parse_int_normal(self):
        assert extract.parse_int('34') == 34

    def test_parse_int_blank(self):
        assert extract.parse_int('') is None


class TestHTMLParsing:
    def test_parse_fixture(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        assert data['date'] == '2026-04-14'
        assert data['file_type'] == 'daily'

    def test_total_after_dedup(self):
        """Fixture has 14 rows, 1 duplicate → 13 unique."""
        data = extract.parse_html(str(DAILY_FIXTURE))
        assert data['total'] == 13

    def test_mode_extraction(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        by_ticker = {s['ticker']: s for s in data['signals']}
        assert by_ticker['AAPL']['mode'] == 'Dark Green'
        assert by_ticker['AAPL']['mode_css'] == 'c4'
        assert by_ticker['AMD']['mode'] == 'Light Green'
        assert by_ticker['CAT']['mode'] == 'Bear-Bull Flip'
        assert by_ticker['XOM']['mode'] == 'Dark Red'
        assert by_ticker['NEE']['mode'] == 'Light Red'
        assert by_ticker['DG']['mode'] == 'Bear-Bull (LR-LG)'

    def test_signal_types(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        by_ticker = {s['ticker']: s for s in data['signals']}
        assert by_ticker['AAPL']['signal_type'] == 'Hold'
        assert by_ticker['INTC']['signal_type'] == 'pP'
        assert by_ticker['AMD']['signal_type'] == 'Buy'
        assert by_ticker['XOM']['signal_type'] == 'Sell'
        assert by_ticker['NEE']['signal_type'] == 'dSell'
        assert by_ticker['SSRM']['signal_type'] == 'AddSh'
        assert by_ticker['PRLB']['signal_type'] == 'spBuy'
        assert by_ticker['DG']['signal_type'] == 'dBuy'

    def test_numeric_parsing(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        by_ticker = {s['ticker']: s for s in data['signals']}
        assert by_ticker['AAPL']['close'] == 260.49
        assert by_ticker['AAPL']['revl'] == 251.42
        assert by_ticker['AAPL']['mom'] == 2.81
        assert by_ticker['AAPL']['r'] == 0.14
        assert by_ticker['AAPL']['days'] == 5
        assert by_ticker['AAPL']['tr_weeks'] == 34
        assert by_ticker['XOM']['mom'] == -5.30
        assert by_ticker['XOM']['r'] == -1.20

    def test_pl_fields(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        by_ticker = {s['ticker']: s for s in data['signals']}
        assert by_ticker['AAPL']['pl_raw'] == '+1.69%'
        assert by_ticker['AAPL']['pl_num'] == 1.69

    def test_blank_r_value(self):
        """$DXY has blank R value — should be None."""
        data = extract.parse_html(str(DAILY_FIXTURE))
        by_ticker = {s['ticker']: s for s in data['signals']}
        assert by_ticker['$DXY']['r'] is None

    def test_fx_not_filtered(self):
        """FX names ($-prefix) should be preserved."""
        data = extract.parse_html(str(DAILY_FIXTURE))
        tickers = [s['ticker'] for s in data['signals']]
        assert '$DXY' in tickers

    def test_mode_counts(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        # After dedup: AAPL,INTC,NEM,SSRM,GS,PRAX=6 DG; XOM,PRLB=2 DR; AMD=1 LG; NEE,$DXY=2 LR; CAT=1 Flip; DG=1 LR-LG
        assert data['mode_counts']['Dark Green'] == 6
        assert data['mode_counts']['Dark Red'] == 2
        assert data['mode_counts']['Light Green'] == 1
        assert data['mode_counts']['Light Red'] == 2
        assert data['mode_counts']['Bear-Bull Flip'] == 1

    def test_signal_counts(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        assert data['signal_counts']['Hold'] == 5
        assert data['signal_counts']['Buy'] == 2
        assert data['signal_counts']['pP'] == 1
        assert data['signal_counts']['Sell'] == 1
        assert data['signal_counts']['spBuy'] == 1

    def test_deduplication(self):
        """AAPL appears twice in fixture — only first kept."""
        data = extract.parse_html(str(DAILY_FIXTURE))
        aapl_rows = [s for s in data['signals'] if s['ticker'] == 'AAPL']
        assert len(aapl_rows) == 1


class TestOutputFiles:
    """Test JSON and CSV output writing."""

    def setup_method(self):
        """Create temp directory structure."""
        self.tmpdir = tempfile.mkdtemp()
        for d in ['parsed_json', 'parsed_csv', 'master']:
            os.makedirs(os.path.join(self.tmpdir, d))
        # Monkey-patch REPO_ROOT
        self._orig_root = extract.REPO_ROOT
        extract.REPO_ROOT = Path(self.tmpdir)

    def teardown_method(self):
        extract.REPO_ROOT = self._orig_root
        shutil.rmtree(self.tmpdir)

    def test_json_output(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        json_path = extract.write_json(data)
        assert json_path.exists()
        with open(json_path) as f:
            loaded = json.load(f)
        assert loaded['date'] == '2026-04-14'
        assert loaded['total'] == 13
        assert len(loaded['signals']) == 13

    def test_csv_output(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        csv_path = extract.write_csv(data)
        assert csv_path.exists()
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 13
        assert rows[0]['date'] == '2026-04-14'
        assert set(reader.fieldnames) == set(extract.CSV_COLUMNS)

    def test_master_history_append(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        count = extract.append_master(data, 'master_history.csv')
        assert count == 13

        master_path = Path(self.tmpdir) / 'master' / 'master_history.csv'
        with open(master_path) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 13

    def test_master_signals_filter(self):
        data = extract.parse_html(str(DAILY_FIXTURE))
        count = extract.append_master(
            data, 'master_signals.csv',
            filter_fn=lambda s: s['signal_type'] != 'Hold'
        )
        # Non-Hold signals: Buy(AMD,CAT), pP(INTC), Sell(XOM), dSell(NEE), AddSh(SSRM), spBuy(PRLB), dBuy(DG) = 8
        assert count == 8

    def test_idempotency(self):
        """Running append twice should not duplicate rows."""
        data = extract.parse_html(str(DAILY_FIXTURE))
        count1 = extract.append_master(data, 'master_history.csv')
        assert count1 == 13
        count2 = extract.append_master(data, 'master_history.csv')
        assert count2 == 0  # No new rows

        master_path = Path(self.tmpdir) / 'master' / 'master_history.csv'
        with open(master_path) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 13  # Still 13, not 26


class TestFileTypeDetection:
    def test_daily_headers(self):
        assert extract.detect_file_type(['Name', 'Ticker', 'Close', 'Tr', 'Mode', 'RevL', 'MoM', 'Days']) == 'daily'

    def test_weekly_headers(self):
        assert extract.detect_file_type(['Name', 'Ticker', 'Close', 'Tr', 'Mode', 'RevL (W)', 'MoM (W)', 'Weeks']) == 'weekly'


class TestErrorHandling:
    def test_file_not_found(self):
        try:
            extract.parse_html('/nonexistent/file.html')
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_bad_filename_pattern(self):
        # Create a temp file with bad name
        tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
        tmp.close()
        try:
            extract.parse_html(tmp.name)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        finally:
            os.unlink(tmp.name)


if __name__ == '__main__':
    # Simple test runner
    import traceback

    test_classes = [
        TestDateParsing, TestParseHelpers, TestHTMLParsing,
        TestOutputFiles, TestFileTypeDetection, TestErrorHandling,
    ]

    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        for method_name in dir(instance):
            if not method_name.startswith('test_'):
                continue
            # Run setup if it exists
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
