# TASK-270 — dispatch record, rounds 2 and 3

> Date: 2026-09-16 · Executor: claude-subagent (the round-1 agent, resumed) · Cycle time: 8 + 23 + 10 min
> Branch: `coding/task-270-state-root-unset` · Base: `81d5dda1` · Tip: `90310f52` · Merged: the commit following this record's parent (`--no-ff`)
> Decisions: `USER-948` (unset), `USER-949` (set, and unset at the project root)
> Results on the branch: `evidence/2026-09/TASK-270-round2-result.md`, `TASK-270-round3-result.md`

## The hazard, as round 1 found it

On a project whose state lives in `perry/`, `perry-config unset "State root"`
exited 0 with no warning, and the next plain `perry-task add` wrote `TASK-001`
into a new `./tasks.jsonl` and `./journal/` at the project root; `perry-task list`
then showed only that row, and the project's own rows vanished from every read.
Round 2 found `set "State root" <other>` does the same.

## What landed

- **`unset "State root"`** refuses when the current resolved state root holds a canonical store.
- **`set "State root" <other>`** refuses when the value changes where state resolves, the current root holds a store, and the target holds none.
- Both exit 1 through the tool's existing refusal path, write nothing (including under `--dry-run`), name the roots and the stores found, say that every later read and write would move to a root holding none of the project's state, and name `/perry relocate <path>`. No `--force` exists; `--force` exits 2.
- **Relocate needs no bypass**: its procedure `git mv`s the files (step 5) before calling `set` (step 6). A test moves every claimed path into a new root and then runs `set`, which proceeds.
- `unset` proceeds when the root already resolves to the project root — nothing moves (`USER-949` confirmed the agent's reading).
- **Two duplications removed**: `parsers.canonical_stores_under` is the one presence test (`set`, `unset` and `parsers.installed`, which held an inline copy); `resolve_state_root`'s rule moved verbatim into `parsers.state_root_for`.

## Merges with main

Round 3 merged main `3df4f61f` (TASK-416's `durations.json` entries); a final merge
of `7039d365` (TASK-271/275) resolved `tests/durations.json` again, keeping main's
`test_empty_config_store` timing because main's timed the file as TASK-275 edited it.
Each resolution was checked by parsing against both parents and by
`test_durations_provenance`.

## PMO verification

1. **Merge preview against main `d73c6ed8`**, merge exit status checked: `MERGE OK`; `bash tests/run` → `✓ all green`; `bash tests/run --tier slow` → `✓ all green`. Main moved one PMO-document commit (`532b62b1`) before the real merge.
2. **An earlier preview conflicted** in `tests/durations.json` and the PMO caught it by exit status, not by grepping text (the lesson from TASK-448's preview); the resolution was sent back to the agent rather than done in the primary checkout.
3. **Agent mutations**, each red on named tests: round 2 — refusal removed (10), check pointed at the project root (10), store names hardcoded without `tasks.jsonl` (2); round 3 — `set` refusal removed (16), target-holds-state exemption removed (8), presence check copied into `set` with one side changed (3).
4. **The PMO's own mutation was not diagnostic, and is recorded as such.** A first attempt used the wrong function name and changed nothing. A second short-circuited `refuse_set_that_strands_state` with `return None` and reddened tests — including cases that should proceed, because the function's return value is used elsewhere, so the mutation broke `set` wholesale rather than removing only the refusal. The specific evidence is the agent's round-3 mutation and the review below.

## Architecture review

**PASS.** It compared `parsers.state_root_for` with `resolve_state_root` at `81d5dda1` line by line — the sentinel set, `.resolve()`, the fallback when the path leaves the project, the return — and found it moved as it was. `installed` answers exactly as before (the same `canonical_store_names()` and `exists_or_unreadable`, no short-circuit side effects). Both refusals sit inside `project_lock` and before `write()`. Relocate's step 5 runs before step 6, and `--dry-run` stops at step 4. The `test_blank_cell_is_one_rule` change swaps a function name only. No writer gained a refusal, as decided.

## Still open, by decision

A config store emptied **outside** Perry (a hand truncation, a bad merge) that had
declared `State root` is accepted as empty (round 1), and the next write relocates
silently. No `unset` or `set` runs on that path, and the user chose not to guard the writers.
