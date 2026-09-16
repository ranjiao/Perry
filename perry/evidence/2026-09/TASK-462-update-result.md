# TASK-462 — release consumer implementation receipt

Date: 2026-09-16. Author: Coding Agent (Codex). Scope: deliverable 6 and its
consumer tests only; the other coding agent owns release records, publishing,
documentation and duration registration. No task-state mutation or V4 claim.

Base: `bccc15f8` (`codex/task-462-release-update`). Initial review checkpoint:
`1095d535c60ecf36adc21feccaf4d6c6bb24b5ca`. This result's commit additionally
preserves raw VERSION line endings and tests CRLF/BOM/missing newline refusal.
The immutable final commit is reported in the coding handoff.

## Delivered behavior

The shell retains portable host lookup, seven-day throttle, force/quiet/strict
and help/unknown-argument behavior. Its stdlib-only `release/update.py` helper
uses the official GitHub latest-release endpoint, rejects draft/prerelease or
malformed/missing notes, and binds its strict `vX.Y.Z` tag to the fetched commit
and exact `X.Y.Z\n` target-tree VERSION. Numeric comparison prevents downgrades.
`target_commitish` is deliberately ignored. Release fetches accept only the
canonical ranjiao/Perry GitHub origin URLs; tests replace this boundary with a
mock, not a production environment bypass. Known local/cached tag movement
refuses. No release or failed verification never falls back to main.

Only clean safe descendants advance with `merge --ff-only`; no stash/reset,
branch replacement or forced checkout. Local/diverged work remains intact.
Developer symlinks, dirty trees and feature branches report origin/main.
`--channel release` explicitly opts a clean symlink into release consumption;
the other work protections still apply. Both main and release-detached HEAD
remain updateable across A → B → C even when origin/main still names A. Clean
pre-VERSION checkouts can migrate through a verified descendant release.

Requests have time/size limits (HTTP socket 5 seconds, overall checked deadline
10 seconds, response 1 MiB; every Git subprocess 30 seconds). Errors omit raw
remote URLs and network exception text. Concurrent updater calls are locked,
and dirty/head/branch/origin are checked again before fast-forward. This is not
a transaction against arbitrary external Git processes; Git's own fast-forward
and worktree checks remain the final guard.

## Validation

All commands run with PYTHONPATH, PERRY_PROJECT and PERRY_HOME unset.

- `python3 tests/parallel test_release_update test_host_support test_bin_argument_contract`:
  3 modules, 108 tests, 28.9 seconds, PASS at initial checkpoint.
- After raw-byte correction: `python3 -m unittest discover -s tests -p test_release_update.py`:
  18 tests, 12.255 seconds, PASS. Previous 17-test module took 10.824 seconds.
- `git diff --check`: PASS.
- New module `tests/test_release_update.py` needs parent-owned duration
  registration (rough initial duration 12.255 seconds).

Tests perform actual commits/fetches/fast-forwards solely in temporary local
repositories and mock GitHub responses. They exercise consecutive main and
detached updates, migration, no-release, malformed/draft/prerelease metadata,
tag/VERSION mismatch, exact VERSION bytes, moved/missing tags, unrelated
history, downgrade/numeric comparison, origin impersonation, local commits,
dirty/feature/symlink behavior, a concurrent edit, strict/quiet/offline policy,
bounded transport, host lookup/throttle/help. No live GitHub request, release,
installed-checkout update, push or main merge was performed. Parent owns final
combined full/slow gates and independent review; neither is claimed here.

## Architecture compliance

Product VERSION/release metadata is outside generic project-state schemas and
claims; no project state reader/writer or ownership change (NN-1/NN-2). Refusals
are explicit, strict returns failure and default background behavior reports
errors while retaining its existing zero-exit contract (NN-3). Version/tag
checks are deterministic; release prose is displayed opaquely (NN-4). Tests
write only temporary fixtures, not the tree running the suite (NN-5). No
architecture document or confirmed contract edit (NN-6); shell help remains
side-effect-free and undeclared arguments refuse (NN-B1/NN-B2).

## Independent-review correction

The initial `bd43fb92` candidate had a P2 behavior gap: a clean main local commit
that raised VERSION to 0.2.0 was refused as a downgrade when latest was 0.1.1;
the same detached local commit attempted to fetch nonexistent v0.2.0. Neither
lost work, but both missed the required developer main comparison/report.

Detached classification now uses an existing tag/cache association at HEAD to
identify a release candidate, independently of self-declared VERSION. A
candidate still requires remote tag/commit/VERSION verification; failures do
not fall back. Unassociated detached commits report developer work. On main,
a HEAD without a release association is compared against the verified target's
ancestry before downgrade refusal, so diverged local version work reports main.
Cached associations preserve the second detached release update. Stale
origin/main is not used to classify local commits.

Added both main/detached version-bump regressions and a known detached release
whose remote tag disappears: the latter must refuse without updating origin/main.
Final targeted command, with the same clean environment:
`python3 -m unittest discover -s tests -p test_release_update.py` — 20 tests,
13.604 seconds, PASS; `git diff --check` PASS. Updated suggested registration
for test_release_update.py: 13.604 seconds. Parent still owns full/slow and the
fresh independent delta verdict.
