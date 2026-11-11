"""Consolidate NHSBSA EPD monthly extracts. Requires duckdb==1.4.4."""
import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

import duckdb

CATALOG = "https://opendata.nhsbsa.net/api/3/action/package_show?id=english-prescribing-data-epd"
TARGET = 100_000_000
ARCHIVE_LIMIT = 3_000_000_000
CSV_LIMIT = 12_000_000_000

def download(url, path):
    parts = urlsplit(url)
    if parts.scheme != "https" or not (parts.hostname or "").endswith(".r2.cloudflarestorage.com"):
        raise ValueError("Unexpected NHSBSA storage URL")
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        partial = Path(tmp.name)
    try:
        with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as stream:
            while block := response.read(4 << 20):
                stream.write(block)
                if stream.tell() > ARCHIVE_LIMIT:
                    raise ValueError("Download exceeds expected archive size")
        os.replace(partial, path)
    finally:
        partial.unlink(missing_ok=True)

def import_month(db, cache, resource):
    name = resource["name"]
    month = int(name[-6:])
    archive = cache / (name + ".zip")
    if not archive.exists():
        download(resource["zip_url"], archive)
    with zipfile.ZipFile(archive) as zipped, tempfile.TemporaryDirectory(dir=cache) as scratch:
        entries = [e for e in zipped.infolist() if e.filename.lower() == name.lower() + ".csv"]
        if len(entries) != 1 or entries[0].file_size > CSV_LIMIT:
            raise ValueError("Unexpected archive contents")
        csv_path = Path(scratch) / "source.csv"
        digest = hashlib.sha256()
        with zipped.open(entries[0]) as src, csv_path.open("wb") as dst:
            while block := src.read(8 << 20):
                digest.update(block)
                dst.write(block)
        if digest.hexdigest() != resource["hash"].lower():
            raise ValueError("CSV checksum differs from the NHSBSA catalogue")
        db.execute("BEGIN")
        try:
            db.execute("""
                INSERT INTO dispensing
                SELECT YEAR_MONTH::INTEGER, PRACTICE_CODE, ICB_CODE, BNF_CODE,
                       BNF_DESCRIPTION, ITEMS::BIGINT, QUANTITY::DECIMAL(20,6),
                       TOTAL_QUANTITY::DECIMAL(20,6), NIC::DECIMAL(20,6),
                       ACTUAL_COST::DECIMAL(20,6)
                FROM read_csv(?, header=true, all_varchar=true, delim=',', quote='"',
                              escape='"', strict_mode=true)
                """, [str(csv_path)])
            count = db.execute("SELECT count(*) FROM dispensing WHERE year_month=?", [month]).fetchone()[0]
            total = db.execute("SELECT count(*) FROM dispensing").fetchone()[0]
            prior = db.execute("SELECT coalesce(sum(rows_loaded),0) FROM releases").fetchone()[0]
            if not count or prior + count != total:
                raise ValueError("Extract contains unexpected periods")
            db.execute("INSERT INTO releases VALUES (?,?,?,?,?)",
                       [month, resource["id"], resource["url"], digest.hexdigest(), count])
            db.execute("COMMIT")
            print(f"{month}: {count:,} records; total {total:,}", flush=True)
        except BaseException:
            db.execute("ROLLBACK")
            raise

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--cache", type=Path, default=Path("epd-cache"))
    parser.add_argument("--catalog-file", type=Path, help="Previously downloaded official package_show JSON")
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    if args.catalog_file:
        data = json.loads(args.catalog_file.read_bytes())
    else:
        with urllib.request.urlopen(CATALOG, timeout=60) as response:
            data = json.load(response)
    resources = sorted((r for r in data["result"]["resources"]
                        if re.fullmatch(r"EPD_2024(0[1-9]|1[0-2])", r["name"])), key=lambda r:r["name"])
    with duckdb.connect(str(args.database)) as db:
        db.execute("SET threads=4")
        db.execute("SET memory_limit='2GB'")
        db.execute("""CREATE TABLE IF NOT EXISTS dispensing (
            year_month INTEGER NOT NULL, practice_code VARCHAR, icb_code VARCHAR,
            bnf_code VARCHAR, bnf_description VARCHAR, items BIGINT,
            quantity DECIMAL(20,6), total_quantity DECIMAL(20,6),
            net_ingredient_cost_gbp DECIMAL(20,6), actual_cost_gbp DECIMAL(20,6))""")
        db.execute("""CREATE TABLE IF NOT EXISTS releases (
            year_month INTEGER PRIMARY KEY, resource_id VARCHAR, source_url VARCHAR,
            csv_sha256 VARCHAR, rows_loaded BIGINT NOT NULL)""")
        for resource in resources:
            if db.execute("SELECT count(*) FROM dispensing").fetchone()[0] >= TARGET:
                break
            month = int(resource["name"][-6:])
            if not db.execute("SELECT 1 FROM releases WHERE year_month=?", [month]).fetchone():
                import_month(db, args.cache, resource)
        rows = db.execute("SELECT count(*) FROM dispensing").fetchone()[0]
        logged = db.execute("SELECT sum(rows_loaded) FROM releases").fetchone()[0]
        if rows < TARGET or rows != logged:
            raise RuntimeError(f"Expected at least {TARGET:,} reconciled rows, found {rows:,}")
        db.execute("CHECKPOINT")
        print(f"Verified {rows:,} source records", flush=True)

if __name__ == "__main__":
    main()
