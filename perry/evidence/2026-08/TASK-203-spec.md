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

---

## Amendment 2026-08-29 — USER-906, option B. This section binds.

Three rounds failed V4, all three ending in the same defect: an ordinary command
silently truncates a canonical register store. The user answered USER-906 with
**option B**. Where this amendment and the original disagree, this wins.

### The invariant

**An ordinary write may never SHRINK a canonical store.** Only an explicit
removal command — `purge`, `resolve-intake`, `intake-sweep` — may reduce a
record count. Any derivation that would produce fewer records than the store
already holds is a **refusal**, not a write.

One invariant, not a fourth predicate. It has to cover every door found across
three rounds without asking a new question at each: the command name (round 1),
the non-unique identity tuple (round 2), the four section shapes, and the
`ensure_section` ordering (round 3).

**Explicitly rejected: option A**, evaluating the gate against the board as it
was at command entry. That is the fourth "move the question" fix on this row and
the first three all looked principled too. A round 4 that snapshots the gate does
not satisfy this spec.

### Scope change

`asks.jsonl` is **IN scope**. The original's "out of scope" line is superseded:
DoD Must-Have 2 of phase 003 names `intake.jsonl` and `asks.jsonl` explicitly,
and the user declined options C and D, which were the two ways to drop it. All
three registers — risks, intake, asks — are this row's.

### The regression test comes first, and must be RED before the fix

Reproduced on this repository's own data (`evidence/2026-08/TASK-203-merge-hold.md`):
with the board's `## Intake` section absent, `perry-task add --track intake`
takes `perry/intake.jsonl` from 8240 bytes / 24 records to **0**, exit code 0,
and `perry-lint` then reports `0 error(s)` and `intake store: 0 record(s), 0
row(s) drifted`.

Write that test, watch it go red, then fix. A fix whose regression test was
written after it is not accepted here — three rounds of this row shipped tests
that were green for the wrong reason.

### Also required in this round, each found by the round 3 reviewer

1. The third shape test is **vacuous**: the legend table lands under `## Top
   risks` because `ensure_section` anchors `## Intake` before `## P0`, so the
   `foreign` shape has **no test on any register**. Give the foreign shape a
   real test on each of the three registers.
2. The uniqueness test **cannot distinguish uniqueness from adjacency** — it
   follows with an `intake`, which trips the ordinary positional check first, so
   it passed with the uniqueness guard deleted. Prove uniqueness alone.
3. `load_register_records` lets `JSONDecodeError` escape as a bare traceback
   where every other failure in that file is a `Refused`.
4. `readable_as_register`'s `section` parameter is dead — in the commit that
   answered a finding about a dead parameter.

### Where round 4 starts

**From `main`, not from `coding/task-203-register-stores`.** That branch is held
out of `main` because the truncation is reachable on this repository; the
measurement is `evidence/2026-08/TASK-203-merge-hold.md`. Read the branch for
what it learned — `REGISTER_EVENTS` is complete both ways over 21 subcommands,
the crash-recovery work at all three rename boundaries holds, the 60-cell
shape matrix is real — and rebuild on the invariant.

### Verification — V4, amended

Items 1 through 5 of the original still hold, plus:

6. The invariant holds on every one of the four doors, each with its own named
   test: command name, non-unique identity, the four section shapes on all
   three registers, and `ensure_section` ordering on a queue-mode track.
7. An explicit removal command is shown to still work — `resolve-intake` and
   `intake-sweep` reduce the count, and their tests prove the invariant does not
   block them.
8. Every mutation is exact: anchor by line, assert on the old text before
   replacing, clear `__pycache__`, wait past the whole-second boundary.
9. Baselines name **both** the runner and the tree. `bash tests/run` and
   `python3 -m unittest discover -s tests` disagree by 3 on this repository, and
   `test_diagnose`'s queue-register test reconciles against the live board.
   `main` at 70eae67 is 98 modules / 2882 tests / 3 failures under `tests/run`.
