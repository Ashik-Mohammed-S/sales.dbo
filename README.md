# Pharmacy retail sales warehouse

A single-host SQLite warehouse for aggregate U.S. pharmacy and drug-store retail sales. Each observation represents one calendar month and one adjustment basis, in millions of U.S. dollars. Store revenue includes merchandise other than prescriptions. Select one series per analysis. Adding both series double-counts sales.

## Run

Use Python 3.11+ with SQLite 3.37+. No third-party Python dependencies are required. Run from this checkout with a database path in a private data directory.

```sh
python warehouse.py sales.sqlite --seed
python warehouse.py sales.sqlite
```

The optional seed contains February through June 2026 as published August 14, 2026. A normal refresh fetches both historical CSVs from FRED over verified HTTPS and commits both series together. Schedule the second command after each monthly release. A failed command exits nonzero. Missing published amounts remain NULL. Previously loaded months omitted from a later response retain their last observation. The observation table records each changed value, ingest timestamp and source payload digest. The timestamp records local ingestion time, not publisher release time.

```sql
SELECT month, usd_millions FROM monthly_sales
WHERE series = 'MRTSSM44611USN' ORDER BY month DESC LIMIT 12;
```

## Sources

U.S. Census Bureau, Monthly Retail Trade and Food Services, distributed through FRED, Federal Reserve Bank of St. Louis. The series pages identify these data as public domain and request citation. The series are alternative measures from one publisher. Coverage is national and contains no individual prescriptions, customers or stores.

- [Unadjusted monthly retail sales](https://fred.stlouisfed.org/series/MRTSSM44611USN)
- [Seasonally adjusted monthly retail sales](https://fred.stlouisfed.org/series/MRTSSM44611USS)

## Production operation

The database runs without a listening service. Place the database and its journal on a local encrypted volume. Give the ingestion identity write access to the private directory, and analysts read access through read-only snapshots. Restrict directory permissions before the first run. Keep databases, journals and backups outside the repository. Grant the worker outbound HTTPS access to fred.stlouisfed.org. The importer fixes the endpoint, rejects redirects, caps response size, validates the CSV schema and binds data as SQL parameters.

Serialize scheduled fetches so an older download cannot finish after a newer download. Monitor exit status and latest observation month. Alert on a missed release or unexpected changes to historical values. Take consistent backups using SQLite's backup API, encrypt and restrict backup storage, and restore a backup to a separate path regularly. Run PRAGMA integrity_check on the restored copy and compare the latest month and row counts. Patch the host and Python runtime. Review host access, backup retention and recovery objectives with the deployment owner. No deployment or compliance certification is supplied.
