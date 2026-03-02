import os
import json
import hashlib
import pandas as pd
from decimal import Decimal
from dateutil import parser as dtparser
from dateutil import tz
from confluent_kafka import Producer


# --- Configuration (via env vars with fallback defaults) ---
TOPIC = os.getenv("TOPIC", "transactions.cleaned.v1")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "localhost:19092")
CSV_PATH = os.getenv("CSV_PATH", "data/transactions.csv")
SOURCE_FILE = os.getenv("SOURCE_FILE", os.path.basename(CSV_PATH))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


# --- Helpers ---

def normalize_side(val: str) -> str:
    """Normalize side values to BUY or SELL, raise if unrecognized."""
    s = str(val).strip().upper()
    mapping = {"B": "BUY", "BUY": "BUY", "S": "SELL", "SELL": "SELL"}
    if s not in mapping:
        raise ValueError(f"Invalid side: {val}")
    return mapping[s]


def parse_ts_iso_utc(val: str) -> str:
    """Parse a timestamp string and normalize to UTC ISO format."""
    dt = dtparser.isoparse(str(val).strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.UTC)
    return dt.astimezone(tz.UTC).isoformat().replace("+00:00", "Z")


def safe_normalize_side(val: str) -> str | None:
    """Normalize side values, returning None when the value is invalid."""
    try:
        return normalize_side(val)
    except Exception:
        return None


def safe_parse_ts_iso_utc(val: str) -> str | None:
    """Normalize timestamps, returning None when parsing fails."""
    try:
        return parse_ts_iso_utc(val)
    except Exception:
        return None


def deterministic_event_id(source_file, rownum, customer_id, symbol, event_ts, side, quantity, price) -> str:
    """Generate a deterministic SHA-256 based event ID from the row's fields.
    This ensures the same row always produces the same event_id (idempotency)."""
    material = f"{source_file}|{rownum}|{customer_id}|{symbol}|{event_ts}|{side}|{quantity}|{price}"
    h = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"evt_{h}"


# --- Kafka delivery callback ---

def delivery_cb(err, msg):
    """Called by the producer after each message is acknowledged by Kafka.
    Logs success or failure."""
    if err:
        print(f"DELIVERY FAILED: {err}")
    else:
        print(f"DELIVERED topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")


# --- Main Entrypoint ---

def main():
    print(f"Starting producer | bootstrap={BOOTSTRAP_SERVERS} topic={TOPIC} csv={CSV_PATH} dry_run={DRY_RUN}")

    # --- Load CSV into a pandas DataFrame ---
    # A DataFrame is an in-memory table — rows are records, columns are fields
    df = pd.read_csv(CSV_PATH)
    total = len(df)

    # --- Drop rows missing any required field ---
    # dropna checks for null/empty values across the specified columns
    # rows with any missing value in these columns are removed entirely
    required_cols = ["event_ts", "customer_id", "symbol", "side", "quantity", "price"]
    df = df.dropna(subset=required_cols)

    # --- Normalize string columns ---
    # .str gives access to string methods that apply to every row in the column at once
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df = df[(df["customer_id"] != "") & (df["symbol"] != "")]

    # --- Normalize side: map B/S/BUY/SELL to BUY/SELL, drop invalid rows ---
    # Invalid side values are converted to None so only those rows are rejected.
    df["side"] = df["side"].apply(lambda v: safe_normalize_side(v) if pd.notna(v) else None)
    df = df.dropna(subset=["side"])  # drop any rows where side normalization failed

    # --- Filter out non-positive quantity and price ---
    # df[condition] returns only rows where the condition is True
    # reassigning df overwrites it with the filtered version
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["quantity"] > 0]
    df = df[df["price"] > 0]

    # --- Normalize timestamps to UTC ISO format ---
    # Invalid timestamps are converted to None so only those rows are rejected.
    df["event_ts"] = df["event_ts"].apply(lambda v: safe_parse_ts_iso_utc(v) if pd.notna(v) else None)
    df = df.dropna(subset=["event_ts"])

    # --- Fill in source_file if not present in the CSV ---
    if "source_file" not in df.columns:
        df["source_file"] = SOURCE_FILE
    else:
        df["source_file"] = df["source_file"].fillna(SOURCE_FILE).str.strip().replace("", SOURCE_FILE)

    rejected = total - len(df)
    published = 0

    # --- Set up Kafka producer ---
    conf = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "enable.idempotence": True,   # exactly-once producer semantics (no duplicate writes on retry)
        "acks": "all",                # wait for all in-sync replicas to acknowledge the write
        "retries": 10,                # retry up to 10 times on transient failures
        "linger.ms": 5,               # wait up to 5ms to batch messages before sending
    }
    producer = Producer(conf)

    # --- Iterate cleaned rows and produce to Kafka ---
    # iterrows() yields (index, row) pairs; _ means we don't need the index
    for rownum, (_, row) in enumerate(df.iterrows(), start=1):
        event = {
            "event_id": deterministic_event_id(
                row["source_file"],
                rownum,
                row["customer_id"],
                row["symbol"],
                row["event_ts"],
                row["side"],
                int(row["quantity"]),
                str(Decimal(str(row["price"]))),
            ),
            "event_ts": row["event_ts"],
            "customer_id": row["customer_id"],
            "symbol": row["symbol"],
            "side": row["side"],
            "quantity": int(row["quantity"]),
            "price": str(Decimal(str(row["price"]))),
            "source_file": row["source_file"],
        }

        # Encode key and value as bytes — Kafka messages are raw bytes
        key = event["event_id"].encode("utf-8")
        value = json.dumps(event).encode("utf-8")

        if DRY_RUN:
            print(f"DRY_RUN publish: {event}")
        else:
            # produce() is async — delivery_cb is called when Kafka acknowledges
            producer.produce(TOPIC, key=key, value=value, on_delivery=delivery_cb)
            # poll(0) triggers delivery callbacks without blocking
            producer.poll(0)

        published += 1

    # --- Flush ensures all buffered messages are sent before exiting ---
    if not DRY_RUN:
        producer.flush(10)

    print(f"SUMMARY total={total} published={published} rejected={rejected}")


if __name__ == "__main__":
    main()

# import os
# import csv
# import json
# import hashlib
# from decimal import Decimal, InvalidOperation
#
# from dateutil import parser as dtparser
# from dateutil import tz
# from confluent_kafka import Producer
#
#
# # --- Configuration (via env vars) ---
# TOPIC = os.getenv("TOPIC", "transactions.cleaned.v1")
# BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "localhost:19092")
# CSV_PATH = os.getenv("CSV_PATH", "data/transactions.csv")
# SOURCE_FILE = os.getenv("SOURCE_FILE", os.path.basename(CSV_PATH))
# DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
#
#
# # --- Validation / Normalization Helpers ---
#
# def normalize_side(raw: str) -> str:
#     s = (raw or "").strip().upper()
#     if s in ("B", "BUY"):
#         return "BUY"
#     if s in ("S", "SELL"):
#         return "SELL"
#     raise ValueError(f"Invalid side: {raw}")
#
#
# def parse_positive_int(raw: str) -> int:
#     n = int(str(raw).strip())
#     if n <= 0:
#         raise ValueError(f"Quantity must be > 0: {raw}")
#     return n
#
#
# def parse_positive_decimal(raw: str) -> Decimal:
#     try:
#         d = Decimal(str(raw).strip())
#     except (InvalidOperation, ValueError):
#         raise ValueError(f"Invalid price: {raw}")
#     if d <= 0:
#         raise ValueError(f"Price must be > 0: {raw}")
#     return d
#
#
# def parse_ts_iso_utc(raw: str) -> str:
#     dt = dtparser.isoparse(str(raw).strip())
#     if dt.tzinfo is None:
#         dt = dt.replace(tzinfo=tz.UTC)
#     dt_utc = dt.astimezone(tz.UTC)
#     return dt_utc.isoformat().replace("+00:00", "Z")
#
#
# def deterministic_event_id(
#         source_file: str,
#         rownum: int,
#         customer_id: str,
#         symbol: str,
#         event_ts: str,
#         side: str,
#         quantity: int,
#         price: str,
# ) -> str:
#     material = f"{source_file}|{rownum}|{customer_id}|{symbol}|{event_ts}|{side}|{quantity}|{price}"
#     h = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
#     return f"evt_{h}"
#
#
# # --- Kafka delivery callback ---
#
# def delivery_cb(err, msg):
#     if err:
#         print(f"DELIVERY FAILED: {err}")
#     else:
#         print(f"DELIVERED topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")
#
#
# # --- Main Entrypoint ---
#
# def main():
#     print(f"Starting producer")
#     print(f"Bootstrap: {BOOTSTRAP_SERVERS}")
#     print(f"Topic: {TOPIC}")
#     print(f"CSV: {CSV_PATH}")
#     print(f"Dry run: {DRY_RUN}")
#
#     conf = {
#         "bootstrap.servers": BOOTSTRAP_SERVERS,
#         "enable.idempotence": True,
#         "acks": "all",
#         "retries": 10,
#         "linger.ms": 5,
#     }
#
#     producer = Producer(conf)
#
#     total = 0
#     published = 0
#     rejected = 0
#
#     with open(CSV_PATH, newline="") as f:
#         reader = csv.DictReader(f)
#         required = {"event_ts", "customer_id", "symbol", "side", "quantity", "price"}
#         missing = required - set(reader.fieldnames or [])
#         if missing:
#             raise RuntimeError(f"CSV missing required columns: {sorted(missing)}")
#
#         for rownum, row in enumerate(reader, start=1):
#             total += 1
#             try:
#                 event_ts = parse_ts_iso_utc(row["event_ts"])
#                 customer_id = (row["customer_id"] or "").strip()
#                 symbol = (row["symbol"] or "").strip().upper()
#                 side = normalize_side(row["side"])
#                 quantity = parse_positive_int(row["quantity"])
#                 price = parse_positive_decimal(row["price"])
#                 source_file = (row.get("source_file") or SOURCE_FILE).strip() or SOURCE_FILE
#
#                 if not customer_id or not symbol:
#                     raise ValueError("customer_id and symbol are required")
#
#                 event = {
#                     "event_id": deterministic_event_id(
#                         source_file,
#                         rownum,
#                         customer_id,
#                         symbol,
#                         event_ts,
#                         side,
#                         quantity,
#                         str(price),
#                     ),
#                     "event_ts": event_ts,
#                     "customer_id": customer_id,
#                     "symbol": symbol,
#                     "side": side,
#                     "quantity": quantity,
#                     "price": str(price),
#                     "source_file": source_file,
#                 }
#
#                 key = event["event_id"].encode("utf-8")
#                 value = json.dumps(event).encode("utf-8")
#
#                 if DRY_RUN:
#                     print(f"DRY_RUN publish: {event}")
#                 else:
#                     producer.produce(TOPIC, key=key, value=value, on_delivery=delivery_cb)
#                     producer.poll(0)
#
#                 published += 1
#
#             except Exception as e:
#                 rejected += 1
#                 print(f"REJECT row={rownum} err={e} raw={row}")
#
#     if not DRY_RUN:
#         producer.flush(10)
#
#     print(f"SUMMARY total={total} published={published} rejected={rejected}")
#
#
# if __name__ == "__main__":
#     main()
