# TASK-142 — triage has no check for a row stranded by a process bug

> Source: `perry/evidence/2026-08/TASK-141-dispatch-2026-08-21-result.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — it adds predicates to a block that already exists
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Where this belongs, and it is not a new triage feature

`conformance` already carries this family — `blocked_without_dependency`,
`depends_on_unknown`, `dependency_cycles`, `next_action_cites_closed` — and
**triage already reads it at step 0.5** (`work/reference/subcommands.md:71`,
*"read `conformance` before judging any row"*). This is predicates to add, not a
feature to build.

## The three checks, each traced to a real incident rather than invented

| check | the incident |
|---|---|
| `blocked_by_closed_rows` | TASK-037 and TASK-045 sat `blocked` with every dependency closed. `blocked_without_dependency` tests `not depends_on` — the list being **empty** — and these had a non-empty list whose every entry had closed. **One predicate away.** |
| `in_progress_with_no_live_run` | two agents starved at the 600s watchdog on 2026-08-20; their rows stayed `in_progress` with no dispatch slot and no new event |
| `review_idle` | TASK-100/111/127/133 sat in `review` after their PRs merged, and nothing noticed |

## Read `blocked_stale`; do not restate its rule

TASK-141 landed `tasks[].blocked_stale` and TASK-148 moved the rule it depends on
into `bin/lib § resolve_startability`, **stated exactly once, with an AST guard
that fails if it appears twice.**

`blocked_by_closed_rows` is the aggregate of that field. **Read it.**
Recomputing the predicate would be a third statement of one rule, and the guard
that TASK-148 shipped exists precisely to stop that — you would either trip it or
work around it, and both are worse than calling the function.

## The requirement that is not a check

**`next_action_cites_closed` must report what it might MEAN**, not only the
pattern it matched. Its output is currently indistinguishable from a
prose-style complaint — and on 2026-08-20 the PMO saw it firing on exactly
TASK-037 and TASK-045, read it as prose hygiene, and **rewrote the cells to
silence it.** Those hits were two stranded rows raising their hands.

A check that reports a pattern without its meaning gets suppressed by whoever
reads it. Say what the disagreement might be — *the prose is stale, or the row is
unblocked* — and let triage decide which.

## Verification — V3

1. **The new predicate is not the old one.** With TASK-037 and TASK-045 restored
   to `blocked` on a fixture, `blocked_by_closed_rows` names **exactly those
   two** and `blocked_without_dependency` still names **none**.
2. **It discriminates.** A row blocked on a genuinely open dependency —
   TASK-050 on TASK-094 is the live shape — is **not** named.
3. **The starved-agent case is reproducible from a fixture**, not asserted: a
   row `in_progress`, no dispatch marker, no event newer than the threshold.
   And a row `in_progress` that *is* live must not be named.
4. **Each predicate reddens on its own case when reverted**, not on a shared
   one. If reverting any of the three reddens the same test, they are not
   separable and you have found something bigger — say so.
5. **`blocked_stale` is read, not recomputed** — proved by TASK-148's own guard
   staying green, and by a test that changes the rule in `bin/lib` and watches
   this check follow.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `bin/perry-task` — the `conformance` block
- `schema/task-list-contract.md` — every new key documented in the same change;
  the parity check will otherwise report it
- `work/reference/subcommands.md` — triage's step 0.5, only if what it must do
  with these changes
- focused tests and fixtures

## Out of scope

- **Changing `startable` or `blocked_stale`.** TASK-141 decided them, TASK-148
  moved them, and the argument is in their evidence.
- Fixing any stranded row on the live board.
- The staleness thresholds themselves if they already exist in
  `schema/state-schema.json § thresholds` — read them, do not invent a second set.
