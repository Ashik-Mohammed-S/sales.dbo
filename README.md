# Pharmacy sales and dispensing data

## Download the public database

Get both `dispensing.part-00` and `dispensing.part-01`, plus `SHA256SUMS`, from the [latest published snapshot](https://github.com/Ashik-Mohammed-S/sales.dbo/releases/latest). From their download directory, reconstruct the database and verify the digest before opening it.

**Linux**

```sh
cat dispensing.part-00 dispensing.part-01 > dispensing.duckdb
sha256sum -c SHA256SUMS
```

**Windows PowerShell**

```powershell
cmd /c "copy /b dispensing.part-00+dispensing.part-01 dispensing.duckdb"
$expected = ((Select-String -Path SHA256SUMS -Pattern '  dispensing\.duckdb

The verified January–June 2024 build contains **107,473,886** records. See the [source manifest](dispensing-manifest.json) for counts and SHA-256 checksums.

Build a single DuckDB table, `dispensing`, from complete monthly English Prescribing Dataset extracts. The importer starts in January 2024 and stops after the first complete month that brings the total to at least 100 million source observations. Each row preserves a publisher observation of dispensing activity. Multiple items can contribute to one row. Actual costs and net ingredient costs are reported in GBP. U.S. retail revenue is maintained separately below.

Install into a private virtual environment with Python 3.12 and allow several gigabytes for the database, compressed downloads and one expanded CSV. Use a private local data directory on an encrypted volume. Only the build identity needs write access. Distribute a read-only snapshot to analysts after the writer closes.

```sh
python -m pip install duckdb==1.4.4
python build_dispensing.py dispensing.duckdb --cache epd-cache
```

The build checks each expanded CSV against the NHSBSA catalogue SHA-256, projects ten fields and appends the month in one transaction. A completed month is skipped on rerun. Use a new database and cache to ingest a revised release. Connect to the result with DuckDB. For example:

```sql
SELECT year_month, count(*) AS source_records,
       sum(items) AS prescription_items, sum(actual_cost_gbp) AS reported_cost_gbp
FROM dispensing
GROUP BY year_month ORDER BY year_month;
```

Join `dispensing` to `releases` using `year_month` to retrieve each row's source and checksum. The release table enforces one row per month. The import excludes practice street addresses. Control host access, test restores, and keep the database, its write-ahead log and source cache outside Git.

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Source: [NHS Business Services Authority, English Prescribing Dataset](https://opendata.nhsbsa.net/dataset/english-prescribing-data-epd). Consult the publisher's caveats for coverage and changes to cost calculations.

## U.S. pharmacy retail sales warehouse

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
).Line -split ' ')[0]
if ((Get-FileHash dispensing.duckdb -Algorithm SHA256).Hash -ne $expected) { throw 'Database checksum mismatch' }
```

Open the verified file using `duckdb -readonly dispensing.duckdb`. Readers can continue querying their copy offline. Each rebuild uploads to a new draft release and publishes it after validation. Older versioned releases stay available. The latest-release link switches to the new snapshot upon publication. Repository write access controls who can publish.

## English NHS dispensing warehouse

The verified January–June 2024 build contains **107,473,886** records. See the [source manifest](dispensing-manifest.json) for counts and SHA-256 checksums.

Build a single DuckDB table, `dispensing`, from complete monthly English Prescribing Dataset extracts. The importer starts in January 2024 and stops after the first complete month that brings the total to at least 100 million source observations. Each row preserves a publisher observation of dispensing activity. Multiple items can contribute to one row. Actual costs and net ingredient costs are reported in GBP. U.S. retail revenue is maintained separately below.

Install into a private virtual environment with Python 3.12 and allow several gigabytes for the database, compressed downloads and one expanded CSV. Use a private local data directory on an encrypted volume. Only the build identity needs write access. Distribute a read-only snapshot to analysts after the writer closes.

```sh
python -m pip install duckdb==1.4.4
python build_dispensing.py dispensing.duckdb --cache epd-cache
```

The build checks each expanded CSV against the NHSBSA catalogue SHA-256, projects ten fields and appends the month in one transaction. A completed month is skipped on rerun. Use a new database and cache to ingest a revised release. Connect to the result with DuckDB. For example:

```sql
SELECT year_month, count(*) AS source_records,
       sum(items) AS prescription_items, sum(actual_cost_gbp) AS reported_cost_gbp
FROM dispensing
GROUP BY year_month ORDER BY year_month;
```

Join `dispensing` to `releases` using `year_month` to retrieve each row's source and checksum. The release table enforces one row per month. The import excludes practice street addresses. Control host access, test restores, and keep the database, its write-ahead log and source cache outside Git.

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Source: [NHS Business Services Authority, English Prescribing Dataset](https://opendata.nhsbsa.net/dataset/english-prescribing-data-epd). Consult the publisher's caveats for coverage and changes to cost calculations.

## U.S. pharmacy retail sales warehouse

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
