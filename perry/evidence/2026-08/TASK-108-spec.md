# TASK-108 — The open-decision count measures prose, not decisions

> Source: found 2026-08-20 while triaging and dispatching; the count rose three times for one question
> Dispatch mode: auto
> Executor: claude-subagent (repository-local counting logic and fixtures)
> Estimated cycle: small
> Subjective verification: whether prose that raises a question **not** yet in the User Input Queue should still count — it is a real unrecorded decision, but counting it means the number is no longer reconcilable against the queue
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Deliverable

1. The open-decision count counts **distinct decisions**, not occurrences of
   decision-words in prose. A pending row in the User Input Queue counts once,
   however many files discuss it.
2. Prose that describes a decision already recorded in the queue does not add
   to the count. Today it does, and the effect is backwards: on this repository
   the check reports **7** while the queue holds **2**, and three of the
   reported items are three different files discussing the same `USER-004`.
   Writing an open question down is what makes the number go up.
3. On this repository the reported number equals the number of pending rows in
   the User Input Queue.
4. The two existing exemptions keep working: a `TBD` a template declares as a
   legal field value, and a `TBD` inside an `## Implementation plan`. Both were
   added for the same reason this row exists — the check was counting
   placeholders as people waiting.

## Verification — V4

1. Fixture: one pending `USER-` row, discussed in three separate files. Assert
   the count is **1**, not 3.
2. Fixture: two pending rows, no prose about either. Assert **2**.
3. Fixture: an answered row plus prose about it. Assert **0** — answered rows
   already do not count, and prose about them must not resurrect them.
4. Assert the declared-`TBD` and `## Implementation plan` exemptions still hold,
   using the fixtures that already cover them.
5. On this repository, assert the reported number equals the pending count that
   `perry-task list --all --json` reports under `asks.open`.
6. `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`. `tests/test_diagnose.py TestUserLoadFindings` must pass —
   it is red today for exactly this reason.

## Files in scope

- `bin/perry-diagnose` — the open-decision counting and its evidence list
- focused diagnose tests and fixtures

## Out of scope

- The other user-load findings. Only the open-decision one changes.
- The User Input Queue's schema, columns, or how rows are written.
- `bin/perry-lint`, `bin/perry-task`, `bin/perry-conform`, `bin/perry-migrate`
  and `schema/state-schema.json` — each is carried by an open unmerged branch,
  and this row must not touch their surface.
- Rewording the prose in `perry/` that currently trips the check. The count is
  wrong; the prose is right, and editing documentation to satisfy a miscount is
  the move this project already refused once.
- Closing without the V4 evidence above.

## Changes

- 2026-08-20 — **High-stakes gate overridden by the user, explicitly.** The
  computational scan (`perry-state --escalation-scan`) refused this spec with
  `verdict: refuse`, on the fragment `diagnose` matching in `Files in scope`
  from `.perry/hook.md`'s "Writing into a project Perry does not own — `adopt`
  commit stage, `diagnose` execute stage, `relocate`, `git mv`".

  This is a true whole-word match, not the substring artifact TASK-107 fixed —
  the first genuine refusal the repaired matcher has produced. What it cannot
  distinguish is granularity: the rule guards the **execute stage**, which
  writes into a project Perry does not own, while this row touches only the
  read-and-count path. The user was shown that distinction and cleared it,
  bounded as follows: **no change to the diagnose execute stage, no write to any
  project outside this repository, and no change to which paths Perry claims.**
  The dispatch prompt carries that bound as a constraint.

  Recorded because a gate that is overridden without a written trace is a gate
  that was never really armed — and because the granularity question is a real
  one this override does not settle. Whether `.perry/hook.md`'s fragment should
  distinguish the execute stage from the rest of the tool is the user's call and
  remains open.
