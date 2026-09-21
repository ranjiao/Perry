# TASK-478 — the release check accepts a range that introduces the record

Date: 2026-09-21. Owner: Coding Agent. Priority: P1. Required verification: V4.
> Touches architecture: release/ component (release/manage.py check_base).
> Dispatch mode: auto
> Executor: claude-subagent
> Subjective verification: independent review against the written bounded criteria
> Deployed: no

Authorization: USER-991 (2026-09-21, in chat). CI run 35597517986 (push,
base `0b5bf99e`, head `174f35b2`) failed at `python3 release/manage.py check
--base "$BASE_SHA" --ref HEAD` with "release: first introduction must contain
only the 0.1.0 baseline", so the tests job never ran the suite.

## Deliverable

`release/manage.py check_base` (~line 252): when the base has no
`release/records.jsonl`, it currently requires HEAD's whole record to be the
single baseline row. Instead: find the commit in `base..head` that introduces
`release/records.jsonl` (the ancestry-ordered first commit that adds it),
require that commit's record to be exactly the 0.1.0 baseline (the existing
rule, applied to the introducing commit), then validate `introducing commit →
head` exactly as the existing-record branch does (append-only history, and every
later check that branch runs, including the phase-pointer and product-path
checks, against that commit as the base). The "base lost existing release
history" refusal is unchanged.

## Acceptance criteria

1. `python3 release/manage.py check --base 0b5bf99e --ref 174f35b2` passes on
   this repository (today it refuses).
2. A fixture range whose introducing commit carries more than the baseline is
   still refused with the first-introduction message.
3. A fixture where the base once had the record and it was deleted is still
   refused ("base lost existing release history").
4. A fixture range introducing the baseline and then a later version whose
   history is rewritten (a row changed or removed) is refused as rewritten.
5. Reverting the fix makes the new criterion-1-style fixture test fail; the
   unmodified candidate and the affected tier pass.

## Files in scope

`release/manage.py` (`check_base` and at most one small helper);
`tests/test_release_core.py`.

## Bound

Four ranges: introduction-plus-later-versions (accepted), introduction with
extra rows (refused), lost history (refused), rewritten after introduction
(refused). Net Python/test physical lines ≤ +40. No change to the record format,
to `prepare`/`publish`, or to the workflows.

## Verification

Temporary git fixture repositories only (never this repository's refs), candidate
PERRY_HOME, PERRY_PROJECT unset, fresh TMPDIR under the scratch derivation.
`bash tests/run --tier affected --base <pinned base>`; one reverting-fix proof
with `__pycache__` purged; `git diff --check`; criterion 1 run read-only against
this repository. Record the exact commit and line delta.

## Out of scope

`.github/workflows/`, `release/records.jsonl`, `VERSION`, `CHANGELOG.md`,
publishing, tags, `git push`, re-running CI, live PMO state, main integration.
