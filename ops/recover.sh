#!/usr/bin/env bash
set -euo pipefail
repo=Ashik-Mohammed-S/sales.dbo
tag=${1:-$(curl -fsSL --retry 3 "https://api.github.com/repos/$repo/releases/latest" | jq -er .tag_name)}
[[ "$tag" =~ ^dispensing-[0-9]+-[0-9]+$ ]]
root=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
cd "$scratch"
base="https://github.com/$repo/releases/download/$tag"
for file in dispensing.part-00 dispensing.part-01 SHA256SUMS dispensing-manifest.json; do
  curl --fail --silent --show-error --location --retry 3 --max-time 900 "$base/$file" -o "$file"
done
cmp dispensing-manifest.json "$root/dispensing-manifest.json"
cat dispensing.part-00 dispensing.part-01 > dispensing.duckdb
sha256sum dispensing.part-00 dispensing.part-01 dispensing.duckdb > computed
diff -u SHA256SUMS computed
python "$root/verify_snapshot.py" dispensing.duckdb
echo "Recovered $tag in ${SECONDS}s"
