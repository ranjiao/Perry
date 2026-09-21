# ADR-023 — The next-step rule table covers every lifecycle stage and event, and every lane subcommand is classified

> Status: active
> Type: Design
> Date: 2026-09-21
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

- A new phase with no tasks got no recommendation. `R-week-unplanned` was meant
  to cover it, but its fact `week.planned` has no source until `TASK-444`
  (`reference/next.md:130`). A rule over an unknown fact never fires, and no
  other rule keys on "a phase with nothing to do", so `primary` was null.
- Enumerating every `goals`, `work` and `decide` subcommand against the
  lifecycle (2026-09-21) found twelve more stages or events that no rule covered.
  Among them: KRs with no declared check; `score-phase` before the retro;
  midweek; rows owed a V4 review; rows closable on a PASS verdict; dispatchable
  rows; stale blocks; month rollover; waiting inputs; overdue cadence; a raised
  risk; a stale architecture review.
- Most of the facts are already in the `perry-state --json` payload but not
  declared as `NEXT_FACTS`. Two need a reader first, verdict blocks and spec
  headers, and NN-1 allows only one reader.
- Nothing recorded which subcommands are deliberately never recommended, so an
  unclassified new subcommand could not be told from an intended one.

## Options

1. **Extend the rule table in DESIGN-020 § 5.10.** Thirteen new rules plus one
   renamed, in three batches, a single rule order, a never-recommended list, and
   a guard over every lane's Subcommand index.
   - Pros: one table and one order, the same state always gives the same
     answer, and each rule is testable by a fixture.
   - Cons: more rules to keep ordered. A near-universal rule such as
     `R-dispatchable` must sit low.
2. **Add only `R-kr-unstaffed`.**
   - Pros: the smallest change that fixes the reported case.
   - Cons: leaves the other twelve gaps, and the next one is found the same way.
3. **Let the agent pick a next step when `primary` is null.**
   - Rejected: DESIGN-020 § 9 (2026-09-15) requires the command to decide. An
     agent's pick is the prose-driven behaviour § 1.1 of that design measured.

## Chosen

Option 1 (`USER-990`, `USER-992`, `USER-994`), specified in `DESIGN-020 § 5.10`,
with UD 13–15:

- **UD 13.** Phase length is deferred to the next phase, so `mid-phase-review`
  and a due-date close stay user-initiated.
- **UD 14.** A KR that is measured and met does not count as unstaffed. No
  schema change.
- **UD 15.** All three batches are written now and implemented batch by batch
  (§ 6 G, H, I).
- **`goals check`.** The goals index gains a `check` row, so `R-checks-undeclared`
  has a command to name.
- **Rule order.** Lifecycle rules come before execution rules. Finishing work
  (review, close) comes before starting work (dispatch). Cadence and hygiene
  come last. `R-rollover` sits before the execution loop.

## Consequences

- **Rules:** `reference/next-rules.json` grows from 18 rules to 31, and
  `R-phase-closable` becomes `R-phase-scorable` plus `R-retro-due`. The block
  still shows one primary and at most two alternates.
- **Facts:** `perry-state` declares 13 fact rows more. Verdict blocks and spec
  headers are read through `viewer/parsers.py` (NN-1).
- **Contract:** `next-contract.md` takes a minor version bump for each batch.
- **Guard:** every lane Subcommand index command is either some rule's
  `command` or on the never-recommended list. The list extends the read-only
  inventory in `tests/test_next_closing.py`.
- **Procedure:** `goals/reference/weekly.md` step 1 takes unstaffed KRs first
  when there are any.
- **Not touched:** `schema/state-schema.json`.

## What would reopen this

- A phase declares a duration (UD 13 revisited). `mid-phase-review` and a
  due-date close then get rules.
- `R-kr-unstaffed` fires on KRs that no task should serve often enough that the
  user silences it. That calls for UD 14's declaration option.
- A rule placed below `R-dispatchable` is never seen on busy boards. That calls
  for re-ordering, or for narrowing `R-dispatchable`.
