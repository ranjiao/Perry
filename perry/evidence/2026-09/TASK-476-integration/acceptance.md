# TASK-476 — acceptance, 2026-09-21 (V3)

`test_v5_signoff` joined every V5 close's evidence path to the state root, and
TASK-451's V5 close (committed at `3bf4550a`) recorded the repo-relative form
`perry/evidence/…`, so main was red from `3bf4550a` to `af328b36`. The cause was
the PMO's own `--evidence` argument; the event log is append-only and was not
touched.

| Step | Result |
|---|---|
| Candidate | `d001c26c` on `coding/task-476-v5-evidence-join`, base `1e1cdd4c`; one file, `tests/test_v5_signoff.py`, +7/−3 (one `evidence()` helper used by both tests in `TestHistoryIsNotRewritten`) |
| Author proofs | module 36/36 (35/36 at base); reverting the helper's join reddens the TASK-451 subtest, restore verified with `git diff --exit-code`; a scratch copy pointing one V5 close of each path form at a missing file fails both ways |
| Architecture trigger | none — the diff touches only `tests/`, no listed boundary path, no new directory or executable, no contract or architecture document |
| First full gate | suite green (158 modules / 4,460 tests) but refused STALE: the PMO committed `37db3614` to main during the run |
| Full gate re-run | `tests/merge-check --base main delivery=coding/task-476-v5-evidence-join --tier full`: green on merged tree `e7d4530c`, base `37db3614`; `receipt.json`, `full.log` |
| Integration | `integ/task-476` `af328b36` (`--no-ff` onto `37db3614`, tree `e7d4530c`) + durations `67fa5e3c`; `--verify-receipt` VERIFIED on `67fa5e3c` |
| Slow gate | `bash tests/run --tier slow` at `67fa5e3c`: 162 modules · 4,563 tests · all green; tree guard: nothing moved (`slow.log`) |
| Merge | refs rechecked; `git merge --ff-only integ/task-476` → main `67fa5e3c`; `python3 -m unittest -q test_v5_signoff` OK on main |

Lesson recorded for the PMO: no commit to main while a merge gate that names
`--base main` is running.
