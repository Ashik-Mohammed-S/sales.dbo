"""Build and refresh a local pharmacy retail sales warehouse. Python 3.11+."""
import argparse
import csv
import hashlib
import io
import re
import sqlite3
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

SERIES = {"MRTSSM44611USN": "unadjusted", "MRTSSM44611USS": "seasonally adjusted"}
LIMIT = 2_000_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS observation (
    series TEXT NOT NULL CHECK(series IN ('MRTSSM44611USN','MRTSSM44611USS')),
    month TEXT NOT NULL,
    retrieved TEXT NOT NULL,
    usd_millions INTEGER CHECK(usd_millions >= 0),
    payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256)=64),
    PRIMARY KEY(series, month, retrieved)
) STRICT;
CREATE VIEW IF NOT EXISTS monthly_sales AS
SELECT series, month, usd_millions, retrieved, payload_sha256 FROM (
    SELECT *, row_number() OVER (PARTITION BY series, month ORDER BY retrieved DESC) AS ranking
    FROM observation
) WHERE ranking=1;
"""

def parse(series, body):
    reader = csv.reader(io.StringIO(body.decode("utf-8-sig")))
    if next(reader, None) != ["observation_date", series]:
        raise ValueError("Unexpected CSV header")
    rows = {}
    for day, value in reader:
        month = date.fromisoformat(day)
        if day != month.isoformat() or month.day != 1 or day in rows:
            raise ValueError("Invalid or repeated observation month")
        if value in ("", "."):
            rows[day] = None
        elif re.fullmatch(r"[0-9]{1,10}(?:\.0+)?", value):
            rows[day] = int(value.split(".")[0])
        else:
            raise ValueError("Unexpected sales amount")
    if not rows or all(value is None for value in rows.values()):
        raise ValueError("No sales amounts received")
    return rows

def apply_changes(db, payloads, retrieved):
    for series, body in payloads.items():
        rows = parse(series, body)
        digest = hashlib.sha256(body).hexdigest()
        previous = dict(db.execute(
            "SELECT month, usd_millions FROM monthly_sales WHERE series=?", (series,)))
        db.executemany("INSERT INTO observation VALUES (?,?,?,?,?)", (
            (series, month, retrieved, amount, digest)
            for month, amount in rows.items()
            if month not in previous or previous[month] != amount))

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise ValueError("Unexpected source redirect")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--seed", action="store_true", help="Load the bundled historical extract")
    args = parser.parse_args()
    opener = urllib.request.build_opener(NoRedirect())
    payloads = {}
    for series in SERIES:
        if args.seed:
            body = (Path(__file__).parent / "seed" / (series + ".csv")).read_bytes()
        else:
            with opener.open("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + series,
                             timeout=30) as response:
                body = response.read(LIMIT + 1)
        if len(body) > LIMIT:
            raise ValueError("Source exceeds size limit")
        payloads[series] = body
    db = sqlite3.connect(args.database, timeout=30)
    try:
        db.execute("PRAGMA trusted_schema=OFF")
        db.executescript(SCHEMA)
        db.execute("BEGIN IMMEDIATE")
        if args.seed and db.execute("SELECT 1 FROM observation LIMIT 1").fetchone():
            raise ValueError("Seed requires an empty database")
        # Serialize the timestamp with other writers.
        refresh_locked(db, payloads)
    finally:
        db.close()

def refresh_locked(db, payloads):
    retrieved = datetime.now(timezone.utc).isoformat()
    apply_changes(db, payloads, retrieved)
    db.commit()

if __name__ == "__main__":
    main()
