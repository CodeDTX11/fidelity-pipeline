import contextlib
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from transactions_producer import main as producer_main


class FakeProducer:
    def __init__(self, conf):
        self.conf = conf

    def produce(self, *args, **kwargs):
        raise AssertionError("produce() should not be called in dry-run mode")

    def poll(self, timeout):
        return None

    def flush(self, timeout):
        return None


def test_main_drops_invalid_rows_but_continues_batch(tmp_path, monkeypatch):
    rows = [
        {
            "event_ts": "2026-03-01T10:15:30Z",
            "customer_id": "cust-1",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": "10",
            "price": "182.45",
            "source_file": "transactions.csv",
        },
        {
            "event_ts": "2026-03-01T10:15:30Z",
            "customer_id": "cust-2",
            "symbol": "MSFT",
            "side": "HOLD",
            "quantity": "8",
            "price": "412.11",
            "source_file": "transactions.csv",
        },
        {
            "event_ts": "not-a-timestamp",
            "customer_id": "cust-3",
            "symbol": "NVDA",
            "side": "SELL",
            "quantity": "5",
            "price": "901.00",
            "source_file": "transactions.csv",
        },
        {
            "event_ts": "2026-03-01T12:15:30Z",
            "customer_id": "   ",
            "symbol": "   ",
            "side": "BUY",
            "quantity": "2",
            "price": "50.00",
            "source_file": "transactions.csv",
        },
    ]

    csv_path = tmp_path / "transactions.csv"
    with csv_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    monkeypatch.setattr(producer_main, "CSV_PATH", str(csv_path))
    monkeypatch.setattr(producer_main, "SOURCE_FILE", "transactions.csv")
    monkeypatch.setattr(producer_main, "DRY_RUN", True)
    monkeypatch.setattr(producer_main, "Producer", FakeProducer)

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        producer_main.main()

    stdout = output.getvalue()
    assert "SUMMARY total=4 published=1 rejected=3" in stdout
    assert "'customer_id': 'cust-1'" in stdout
    assert "'customer_id': 'cust-2'" not in stdout
    assert "'customer_id': 'cust-3'" not in stdout
