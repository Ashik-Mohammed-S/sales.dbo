# Operating the public dispensing database

## Service and data scope

Public readers download a versioned DuckDB snapshot and query it locally. This edition covers January–June 2024. A newer publication date indicates a rebuild of this edition. Refreshing coverage requires a reviewed change to the source selection, manifest and expected monthly totals. Each row is a published NHS prescribing observation that may cover several prescription items. Costs are reported in GBP.

## Publish and verify

Run **Publish dispensing database** from the Actions tab on main. The build identity has read access. A separate job verifies the transferred files and publishes them with repository contents-write permission. Keep the last known-good release and at least one independent copy outside GitHub. For offsite backups, store the parts, manifest and SHA256SUMS together. On a fresh machine with DuckDB 1.4.4, run the reconstruction instructions in README.md and then `python verify_snapshot.py dispensing.duckdb`. Record the duration and retain the result with the backup.

The recovery workflow runs weekly on Monday at 06:17 UTC and on demand. It downloads assets anonymously, checks both parts and the reconstructed file, compares the release manifest with the repository manifest, and verifies the schema and monthly totals. Its log reports elapsed recovery time. A failure opens or updates an issue assigned to the owner. Enable GitHub notifications for assigned issues and failed Actions runs. Investigate missed scheduled runs from the Actions history.

## Rollback and incident response

1. Record the failing tag, reader impact, and failed run URL. Link users to the versioned known-good release immediately.
2. In **Public release recovery**, use **Run workflow** with the candidate tag to rehearse recovery. The drill preserves the public latest pointer.
3. To restore the latest pointer, the repository owner runs **Restore previous latest release** on main with that tag. This verifies the candidate against the historical edition, serializes the switch with publication and confirms the resulting pointer. If the candidate belongs to a different edition, review the correct historical manifest before changing the pointer.
4. Rerun **Public release recovery** with an empty tag to test the public latest URL. Record the affected versions, recovery time and corrective change before closing the issue.

## Owner access review

Keep Ashik-Mohammed-S as sole human publisher. Review Settings → Collaborators, deploy keys, GitHub Apps, Actions permissions and any tokens capable of writing repository contents. Remove unnecessary write access and record identities, scopes, reviewer and date privately. Use account two-factor authentication and store recovery codes offline.

In Settings → Rules → Rulesets, protect main against deletion and force pushes, and require a pull request for changes to the release pipeline. For a sole maintainer, requiring a second human approval needs a separately designated reviewer. Enable release immutability under repository settings for future releases, then confirm the Immutable badge on the next published release. Verify branch protection and release status after saving. Account authentication settings and access inventories belong in private records.

## Evidence

The [first successful public recovery drill](https://github.com/Ashik-Mohammed-S/sales.dbo/actions/runs/43107347008) verifies the January–June snapshot. Retain recovery logs, source licences, publisher-access reviews, change approvals and incident records for the period required by your chosen standard. Baseline checks use historical totals from the verified database. Each new edition should also reconcile those totals with the authoritative source extracts. Compliance assessment requires an identified standard, scope and evidence review.
