# TASK-203 — the merge onto `main` is clean, measured before the review

Measured 2026-08-30, ahead of the V4 verdict, so that a PASS can merge
immediately instead of discovering a conflict afterwards.

## The question

`TASK-095` round 6 landed in `main` at `7f934d5` and edits `bin/perry-task`.
`coding/task-203-round4` edits the same file. An earlier `git merge-tree` count
was read as "one conflicting region"; that reading was wrong — the count matched
"changed in both", not a conflict marker.

## Textual merge

```
$ git merge --no-commit --no-ff coding/task-203-round4     # onto main
Auto-merging bin/perry-task
Automatic merge went well; stopped before committing as requested
$ git diff --name-only --diff-filter=U
(nothing)
```

**Zero conflicts.**

## Semantic merge — the part a clean auto-merge does not prove

Both branches edit `bin/perry-task`, so a textual merge succeeding says nothing
about whether the result still means what either side intended. Both sides' own
modules were run on the merged tree:

| module | owner | result |
|---|---|---|
| `test_track_register_source` | TASK-095 round 6 | 57 tests, **OK** |
| `test_register_store_invariant` | TASK-203 round 4 | 39 tests, **OK** |
| `test_register_minters` | TASK-203 round 4 | 15 tests, **OK** |

The writer also still runs on this repository's own data:
`perry-task next … --dry-run` reports
`would write TASK-077 (next) → tasks.jsonl + journal + BOARD.md + event`.

## A note on the runner, because it cost a wrong reading here too

`python3 -m unittest tests.test_track_register_source` fails with
`ModuleNotFoundError: No module named 'gate'` — the module needs `tests/` on
`sys.path`, which `bash tests/run` and `python3 -m unittest discover -s tests`
both provide and a bare `-m unittest tests.X` does not. The first attempt above
reported 2 import errors for exactly that reason and they were the invocation's,
not the merge's. Recorded because "the runner disagrees with itself" has now
produced three wrong readings on this project.

## What this does NOT say

It does not say `TASK-203` round 4 is correct — that is the V4 review's to
decide, and the row has failed three rounds. It says only that **if** the review
passes, the merge is mechanical.

No full `tests/run` was taken on the merged tree; the three modules above were
targeted. The probe worktree was discarded after measurement.
