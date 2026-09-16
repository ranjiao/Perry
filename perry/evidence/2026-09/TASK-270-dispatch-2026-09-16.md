# TASK-270 — dispatch record, round 1

> Date: 2026-09-16 · Executor: claude-subagent (async, isolated worktree) · Cycle time: 16 min
> Branch: `coding/task-270-empty-config-store` · Base: `538d94a7` · Tip: `fdc634a6` · Merged: `81d5dda1` (`--no-ff`)
> Re-measurement: `evidence/2026-09/TASK-270-reproduction-2026-09-16.md` · Spec: `evidence/2026-09/TASK-270-spec.md` · Result: `evidence/2026-09/TASK-270-result.md` (on the branch)

## What landed

**The rule, from the writers' own reason for refusing.** A writer refuses `.perry/config.jsonl` only when the store may hide a declaration it could not read — bytes that did not parse, or a record that failed validation. Record count is not part of it: an empty store declares nothing, so DESIGN-003's implicit `main` stamps over nothing, which is the same terms a settings-only store was already accepted on. The old justification for refusing an empty store ("`write --from-file` never produces one"; "an interrupted write does") was false: the importer is gone and `perry-config` writes atomically.

- **One predicate**, `viewer/parsers.py § config_store_unusable`, called by `perry-task`, `perry-goals` and `perry-lint`'s census; `perry-state`'s unusable set is now the parser's own object rather than a copy.
- `unset` / `untrack` print on stderr when they leave the store empty, and name `perry-config set` and `track` as the recovery; `--json` stdout stays one object.
- `perry-lint` prints `config store: empty`; `NS-01` no longer calls an empty file at a `.perry/`-anchored claim foreign.
- A non-empty store with a record that fails validation is refused exactly as before, same wording.

## PMO verification

1. **Merge preview against main `09a70040`**: merge exit status `MERGE OK`, then the full suite — `✓ all green`, tree guard `✓`. One runner warning, not a red: `tests/test_empty_config_store.py` has no `durations.json` entry (added in round 2).
2. **Agent's five mutations**, each red on named tests: the empty store classed invalid again (7), the rule forked into `perry-task` (3) and into `perry-lint` (2), `NS-01` flagging the empty store (2), a writer accepting a genuinely invalid store (3).

## Architecture review

**PASS.** It verified the rule lives in one place and every consumer calls it; that the old "do not validate" wording now appears only for a store that really fails; that no `schema/` file changed and `resolve_state_root` is untouched; and — the load-bearing safety question — that `lib.write_atomic` writes a fsynced temp file and swaps it in with `os.replace`, so no Perry write can leave a torn empty store. It confirmed the `NS-01` exemption is narrow: the only project-root-anchored `.jsonl` claims are `.perry/config.jsonl` and `.perry/events.jsonl`.

**One § 7 candidate:** a config store emptied from OUTSIDE Perry (a hand truncation, a bad merge) was refused by accident before and is accepted now; if that project had declared `State root`, the next write relocates to the project root at exit 0.

## The finding the row was told to report, not fix

On a project whose state lives in `perry/`, `perry-config unset "State root"` exits 0 with no warning, and the next plain `perry-task add` writes `TASK-001` into a new `./tasks.jsonl` and `./journal/` at the project root. `perry-task list` then shows only that row; the project's own rows vanish from every read. **`USER-948`** decided it: `unset "State root"` refuses when the state root holds Perry state and points at `/perry relocate`; the writers are not guarded. That is this row's round 2. The outside-Perry truncation path above stays open by that decision.
