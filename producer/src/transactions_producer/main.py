import os
import csv
import json
import hashlib
from decimal import Decimal, InvalidOperation

from dateutil import parser as dtparser
from dateutil import tz
from confluent_kafka import Producer


# --- Configuration (via env vars) ---
TOPIC = os.getenv("TOPIC", "transactions.cleaned.v1")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "localhost:19092")
CSV_PATH = os.getenv("CSV_PATH", "data/transactions.csv")
SOURCE_FILE = os.getenv("SOURCE_FILE", os.path.basename(CSV_PATH))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


# --- Validation / Normalization Helpers ---

def normalize_side(raw: str) -> str:
    s = (raw or "").strip().upper()
    if s in ("B", "BUY"):
        return "BUY"
    if s in ("S", "SELL"):
        return "SELL"
    raise ValueError(f"Invalid side: {raw}")


def parse_positive_int(raw: str) -> int:
    n = int(str(raw).strip())
    if n <= 0:
        raise ValueError(f"Quantity must be > 0: {raw}")
    return n


def parse_positive_decimal(raw: str) -> Decimal:
    try:
        d = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid price: {raw}")
    if d <= 0:
        raise ValueError(f"Price must be > 0: {raw}")
    return d


def parse_ts_iso_utc(raw: str) -> str:
    dt = dtparser.isoparse(str(raw).strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.UTC)
    dt_utc = dt.astimezone(tz.UTC)
    return dt_utc.isoformat().replace("+00:00", "Z")


def deterministic_event_id(
        source_file: str,
        rownum: int,
        customer_id: str,
        symbol: str,
        event_ts: str,
        side: str,
        quantity: int,
        price: str,
) -> str:
    material = f"{source_file}|{rownum}|{customer_id}|{symbol}|{event_ts}|{side}|{quantity}|{price}"
    h = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"evt_{h}"


# --- Kafka delivery callback ---

def delivery_cb(err, msg):
    if err:
        print(f"DELIVERY FAILED: {err}")
    else:
        print(f"DELIVERED topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")


# --- Main Entrypoint ---

def main():
    print(f"Starting producer")
    print(f"Bootstrap: {BOOTSTRAP_SERVERS}")
    print(f"Topic: {TOPIC}")
    print(f"CSV: {CSV_PATH}")
    print(f"Dry run: {DRY_RUN}")

    conf = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "enable.idempotence": True,
        "acks": "all",
        "retries": 10,
        "linger.ms": 5,
    }

    producer = Producer(conf)

    total = 0
    published = 0
    rejected = 0

    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        required = {"event_ts", "customer_id", "symbol", "side", "quantity", "price"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(f"CSV missing required columns: {sorted(missing)}")

        for rownum, row in enumerate(reader, start=1):
            total += 1
            try:
                event_ts = parse_ts_iso_utc(row["event_ts"])
                customer_id = (row["customer_id"] or "").strip()
                symbol = (row["symbol"] or "").strip().upper()
                side = normalize_side(row["side"])
                quantity = parse_positive_int(row["quantity"])
                price = parse_positive_decimal(row["price"])
                source_file = (row.get("source_file") or SOURCE_FILE).strip() or SOURCE_FILE

                if not customer_id or not symbol:
                    raise ValueError("customer_id and symbol are required")

                event = {
                    "event_id": deterministic_event_id(
                        source_file,
                        rownum,
                        customer_id,
                        symbol,
                        event_ts,
                        side,
                        quantity,
                        str(price),
                    ),
                    "event_ts": event_ts,
                    "customer_id": customer_id,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": str(price),
                    "source_file": source_file,
                }

                key = event["event_id"].encode("utf-8")
                value = json.dumps(event).encode("utf-8")

                if DRY_RUN:
                    print(f"DRY_RUN publish: {event}")
                else:
                    producer.produce(TOPIC, key=key, value=value, on_delivery=delivery_cb)
                    producer.poll(0)

                published += 1

            except Exception as e:
                rejected += 1
                print(f"REJECT row={rownum} err={e} raw={row}")

    if not DRY_RUN:
        producer.flush(10)

    print(f"SUMMARY total={total} published={published} rejected={rejected}")


if __name__ == "__main__":
    main()