# TASK-203 — an ordinary write does not update its store, for either the risks or the intake register

> Serves **P003-O1-KR1** (`phase/003-storage-code.md`): *stores declared in `claims[]` that exist on disk.* Target **6 of 6**, baseline **4 of 6** — `intake.jsonl` and `asks.jsonl` were built by TASK-196 / TASK-197 and never imported.
>
> Dispatch mode: auto
> Executor: claude-subagent (codex ruled out by the user on 2026-08-28 — quota)
> Estimated cycle: medium
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V4
- **Dependencies**: —
- **KR linkage**: `P003-O1-KR1`

## Baseline, measured 2026-08-28 — and half of it measured live

Of the six declared stores, four exist: `tasks.jsonl`, `okr.jsonl`,
`risks.jsonl`, `.perry/config.jsonl`. Two do not: **`intake.jsonl`** and
**`asks.jsonl`**. (`.perry/events.jsonl` is a seventh claimed path and is
deliberately outside this KR's count of six — the event log is derived and
disposable.)

**The intake half was demonstrated on 2026-08-28, not inferred.** Nine
`perry-task intake` writes and seven `resolve-intake` writes ran against this
project during that day's triage. Every one of them re-rendered
`BOARD.md § Intake` and appended an event. **`intake.jsonl` still does not
exist.** `perry-lint` says so in the words that matter: *"no `intake.jsonl` —
drift against the intake store is unchecked, not clean."*

**The risks half is stated by the row and has not been re-measured. Measure it
first** — `risks.jsonl` does exist and reports 4 records at 0 drift, so the
claim to check is whether an ordinary `perry-task risk-add` / `risk-clear`
updates it, or whether the store is only current because it was imported once.
If the risks half does not reproduce, say so and narrow the row rather than
fixing what is not broken.

## Files in scope

`bin/perry-task`, `bin/perry_store.py`, `bin/perry-tasks`, and their tests.

## Deliverable

An ordinary write to either register updates its store in the same transaction
that writes the board and the journal — the arrangement `tasks.jsonl` already
has. Concretely: after `perry-task intake` on a project with no `intake.jsonl`,
the store exists and holds that row; after `resolve-intake`, it carries the
outcome.

The one-way importers (`perry-tasks intake-write --from-board`,
`risks-write --from-board`) stay what they are — a first mint for a project
that has none — and are **not** the path an ordinary write takes.

## Verification — V4

1. On a fixture project with no `intake.jsonl`: run `perry-task intake`, then
   `perry-lint`. The store exists and the census prints a **drift verdict**
   rather than *"no `intake.jsonl` — unchecked, not clean"*.
2. `perry-tasks intake-diff` renders the derived records back and byte-compares
   clean immediately after an ordinary write.
3. **Mutation**: revert the store write on one path and show a test goes red.
4. Re-run the risks half of the claim and record the answer either way.
5. `python3 -m unittest discover -s tests` green.

## Out of scope

- `asks.jsonl`. Same shape, different register, and folding both into one row is
  how a two-store change gets one store's worth of testing. If the fix is
  genuinely shared, say so in the RESULT and propose the follow-up row.
- `perry-lint`'s census coverage — **TASK-209**.
