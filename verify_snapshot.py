"""Validate fixed January–June 2024 NHS dispensing edition, using exact decimals."""
import json
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
EXPECTED = [[202401,18080573,104528254,"853901355.279420","901972979.300000",0],
    [202402,17651709,98030390,"802969696.280900","848489417.070000",0],
    [202403,17779549,99722305,"814884932.078550","862275277.280000",0],
    [202404,18042595,103115284,"838292073.451970","887962580.900000",0],
    [202405,18143434,105348285,"860250319.053270","910717577.580000",0],
    [202406,17776026,98676692,"818287806.254150","864768183.910000",0]]
COLUMNS = [
    ("year_month", "INTEGER"), ("practice_code", "VARCHAR"), ("icb_code", "VARCHAR"),
    ("bnf_code", "VARCHAR"), ("bnf_description", "VARCHAR"), ("items", "BIGINT"),
    ("quantity", "DECIMAL(20,6)"), ("total_quantity", "DECIMAL(20,6)"),
    ("net_ingredient_cost_gbp", "DECIMAL(20,6)"), ("actual_cost_gbp", "DECIMAL(20,6)"),
]

def verify(path):
    manifest = json.loads((ROOT / "dispensing-manifest.json").read_text())
    with duckdb.connect(path, read_only=True) as db:
        columns = [(r[0], r[1]) for r in db.execute("DESCRIBE dispensing").fetchall()]
        if columns != COLUMNS:
            raise ValueError("Unexpected dispensing schema")
        rows = db.execute("""
            SELECT year_month, count(*), sum(items), sum(actual_cost_gbp)::VARCHAR,
                   sum(net_ingredient_cost_gbp)::VARCHAR,
                   count(*) FILTER (WHERE nullif(trim(bnf_code), '') IS NULL)
            FROM dispensing GROUP BY year_month ORDER BY year_month
        """).fetchall()
        if [list(r) for r in rows] != EXPECTED:
            raise ValueError(f"Monthly data differs from historical baseline: {rows}")
        releases = db.execute("""
            SELECT year_month, rows_loaded, csv_sha256, source_url
            FROM releases ORDER BY year_month
        """).fetchall()
        expected = [(r["year_month"], r["rows"], r["csv_sha256"], r["source_url"])
                    for r in manifest["releases"]]
        if releases != expected or sum(r[1] for r in rows) != manifest["rows"]:
            raise ValueError("Provenance or record count mismatch")
        print(f"Verified {manifest['rows']:,} rows, six months, cost and item totals.")

if __name__ == "__main__":
    verify(sys.argv[1])
