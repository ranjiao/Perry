# TASK-462 — product release core result

Date: 2026-09-16. Author: Coding Agent. Branch:
`codex/task-462-version-core`. Base:
`bccc15f83d4f52c0c0c6ab737ac795597a0e0ae6`. Immutable joint code head:
`fe48c3f4f8595d2123e1d38373ea7e30a807597e`.
Core checkpoint: `f89370e5`. Updater author head integrated:
`4c7311be65508e820d287f531e69700cbdc8bbe4` (see separate update result).
The subsequent result commit changes only this evidence file.

## Delivered

- Canonical typed JSONL baseline 0.1.0 at phase 004, honestly summarizing current
  capabilities and this delivery without inventing pre-version releases.
- Stdlib allocation/check/render/notes commands, distinct delivery identities,
  explicit major decision references, optimistic current-version check,
  serialized writes and deterministic projections with explicit crash repair.
- Explicit-base Git checks preserve integrated history and reject product changes
  without entries; documented PMO-only paths do not require or justify patch
  allocations. New CURRENT slug requires its matching phase entry; clearing it
  does not. Initial baseline exception cannot reset deleted history.
- CI compares actual event base using full history. Manual publication tests the
  immutable integrated commit then creates its exact tag and notes, without
  overwrite endpoints. Credential-bearing redirects refuse. Legacy latest
  selection avoids forcing a historical release to latest. Partial remote tag /
  Release failure is documented as non-atomic and requires maintainer recovery.
- AGENTS remains 60 lines with a Perry-only mandatory maintenance link. README
  and INSTALL explain published-release installs, explicit symlink release
  updates, developer report-only behavior, and pre-first-release refusal.
- Integrated updater in this same baseline rather than landing a second
  unversioned product change. No generic project's state/version policy changed.

## Verification receipts

All Python/test commands used `env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME`.

1. `python3 -m unittest discover -s tests -p test_release_core.py -q`:
   15 tests PASS, 8.491s (final core code; temporary Git fixtures and mocked API).
2. `python3 -m unittest discover -s tests -p 'test_release_*.py' -q`:
   33 tests PASS, 20.758s before updater's final safe-checkout delta.
3. Final updater author receipt: 20 tests PASS, 13.604s on `4c7311be`;
   independently rerunning its unchanged tests is left to the parent joint gate.
4. `python3 -m unittest discover -s tests -p test_durations_provenance.py -q`:
   24 tests PASS, 1.114s. Both new modules registered with actual measured times.
5. `python3 release/manage.py check --base bccc15f8 --ref HEAD` at joint code
   head: PASS, one new version `0.1.0`, expected product-path list.
6. `python3 release/manage.py prepare --ref fe48c3f4f8595d2123e1d38373ea7e30a807597e --tag v0.1.0`:
   PASS in clean checkout, prints baseline notes; creates no tag or release.
7. `git diff --check`: PASS. Worktree clean at joint code handoff.

Tests exercise duplicate/stale allocations, same task repeated delivery, phase
and major resets, missing authorization reference, malformed metadata/prose
absence, projection drift, interrupted canonical/projection writes and repair,
product no-bump/PMO-only/phase pointer boundaries, rewritten/deleted/reintroduced
history, tag mismatch/reuse, dirty checkout, unmerged commit, redirect refusal,
existing remote release/tag and partial-publication failure without overwrites.
No mutation-testing pass is claimed; these are direct contract/refusal tests.

Full and slow suites on the final merged preview and fresh-context architecture
review belong to the parent integration gate and are not self-awarded here.
GitHub Actions execution/publication, branch protection, remote permissions,
installation, and live update were not performed. No push or tag was created.

## ARCHITECTURE COMPLIANCE

- Root §1/§2/§3: product-local release metadata lives under release/, outside the
  generic project-state schema and reader. No schema or ARCHITECTURE file edit.
- NN-1/NN-2: one release record loader and validator; VERSION/CHANGELOG are
  projections, never competing authorities. Release records are not Perry
  project-state files and do not introduce a second state-store reader.
- NN-3: invalid allocations, mismatched projections, stale versions, unsafe
  update/publication inputs and prior tag/release identities refuse. Multi-file
  writes deliberately expose interrupted state as check failure with explicit
  repair rather than pretending a cross-file/remote atomic transaction.
- NN-4: all Python decisions use typed fields, paths, Git identity and numerical
  versions. Notes and authorization meaning remain agent/human-owned opaque text.
- NN-5: tests write only temporary Git repositories; publisher API is mocked.
- NN-6: no architecture decisions edited. New questions: none required to ship
  this bounded contract. Actual authorization quality and release-note quality
  remain review responsibilities, not a proposed semantic parser.

Scope deviation: INSTALL.md was included with parent approval as a necessary
correction to the old `git pull` consumer guidance. No other expansion.

## Review follow-up — exact checked-out commit guard

Reviewer found that removing the `HEAD == requested SHA` check survived the
previous core suite. Added a clean checkout at a later commit while requesting
the older release commit: both prepare and publish now explicitly assert refusal,
and publisher asserts that no API request is made. Production behavior unchanged.

- Clean-env core module: 16 tests PASS, 14.955s; duration registration updated.
- Mutation removed only `commit(root, "HEAD") != sha or ` from prepare's guard.
  The new targeted test failed with `AssertionError: Refused not raised`, exit 1
  (one test, 0.805s). The mutation is killed, not merely detected by tree checks.
- Restored `release/manage.py` byte-for-byte against `git show HEAD:release/manage.py`;
  SHA-256 `7703018f84e639ba582d4fb7d8a6467d370dfa969b85676c249ae99d961e5e79`.
- Re-ran the new targeted test after restoration: PASS. No production changes.
  Parent must validate the new immutable head for the final merged gate.
