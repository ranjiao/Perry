# TASK-019 / TASK-020 — the round-4 review's five open items, closed

> Rung: V3 (reproducible run) for each fix; the rows still need a fresh V4.
> Prior document: the round-4 review that raised M-7, M-8, m-9, m-10 and m-11.
>
> **That review was never committed when this file was written, and this line
> cited `TASK-019-020-v4-review.md`, which raises a different set (B1–B4,
> S5–S12, M13–M15).** The round-5 V4 review found it — see
> `TASK-019-020-round5-review.md` § M-5 — and named it as this document's own
> stated pattern, "a claim about something that is not there", applied to
> itself. The four round-5 reviews are now in this directory; the findings this
> file closes are the ones listed in the table below, and the corrections to
> what that table claims are in `TASK-019-020-round5-review.md`.

## What was closed

| Id | Finding | Commit |
|---|---|---|
| M-8 | `perry-task add` refused on a board with no `## P0`/`## P1`/`## P2` | `78cdd62` |
| m-9 | `unittest.main()` mid-file: a green report over a truncated suite | `70a6292` |
| M-7 | `goals/SKILL.md` declared `commit <promise>`; no procedure existed | `f2e2cc3` |
| m-10 | `subcommands.md` cited restatements that were not in either file | `80cde0a` |
| m-11 | Two guards could not fail on the defect they named | `02235b1` |

## What each turned up that the finding did not predict

**M-8** — the fix needed three changes, not one. `heading_re()` used `\b`,
which needs a word character on one side, so the real project's
`## P2 (低优先 carry)` never matched and `--group` refused a section the same
tool had just listed. And a project's own section can be narrower than six
columns, so the required columns are added and existing rows widened with
empty cells rather than dropping what does not fit — the way `--commitment`
was lost once already.

**m-9** — the review named one file. It was **six**, and this session's own
commit made a seventh before the guard I was writing caught it. Recovered
three tests in `TestEveryToolResolvesTheStateRoot` that had sat below
`test_claims.py`'s own entry point and never run outside discovery.

**M-7** — `commit` could not simply be deleted. `OKR.md § Commitments` is the
declared spine of pipeline and queue tracks, read by two mode files and
specified in the schema, and with no procedure it had **no writer at all**.

**m-10** — `dispatch.md` did mention stage moves in passing; what neither file
had was `Stage since`, the cell the invariant is about.

**m-11** — writing the behavioural test found a live crash. `cmd_route` read
`intake.get("arrived")`, set `values["arrived"]` on only some branches, then
used `values['arrived']` unconditionally. Routing a hand-typed `## Intake`
row — request cell, no date — into a pipeline track raised
`KeyError: 'arrived'`.

## The pattern across all five

Four of the five are the same defect wearing different clothes: **a claim
about something that is not there.** A subcommand index promising a procedure
nobody wrote. A sentence citing a restatement that does not exist. A guard
asserting a schema key and calling it a behaviour. A suite reporting OK over
tests it never loaded.

The fifth, M-8, is the other recurring one: **Perry's own board is the one
board Perry never has to adapt to.** `add` had been unable to write to a real
project's board for as long as the read side had been able to read it, and no
test noticed because every fixture was a board `add` itself had created.

## Verification performed

```
571 → 583 tests, direct execution and discovery agreeing file by file
perry-lint                       → clean
```

Mutations run, each reverting one fix and confirming the test goes red:

| Reverted | Test that went red |
|---|---|
| `heading_re` back to `\b` | `test_a_heading_ending_in_punctuation_resolves` |
| required-column widening | `test_a_narrower_section_gains_the_columns_…` |
| an entry point back into mid-file | both m-9 guards |
| the `commit` procedure | `test_every_row_has_a_procedure_in_the_reference_it_names` |
| the `adr` rename | same |
| autopilot's stage restatement | both m-10 guards |
| `arrived` on the pipeline branch | `test_routing_into_a_pipeline_track_carries_…` |
| the queue refusal | `test_routing_one_into_a_queue_track_is_refused_not_crashed` |
| `jline` back to `values['arrived']` | `test_routing_a_hand_typed_intake_row_does_not_traceback` |
| route's `Stage since` | `test_routing_into_a_pipeline_track_carries_…` |
| `stage`'s restamp | `test_a_stage_move_restamps_the_clock_on_such_a_board` |
| `add`'s stage stamp | `test_the_columns_are_created_on_a_board_that_never_had_them` |

## What these rows still wait on

A fresh V4 on TASK-019 and TASK-020. Five rounds of review have each found
real defects in what the previous round approved, and nothing here changes
that — this document records fixes, not an independent judgement of them.


## Correction, 2026-08-17

The round-5 V4 review re-ran the twelve mutations in the table above. **Nine
reproduce. Three do not**, and all three are the same defect: the guard they
name cannot fail.

| Row | Status |
|---|---|
| "an entry point back into mid-file → both m-9 guards" | only guard 1 goes red; `test_every_class_is_defined_before_the_entry_point_runs` is inert on every input — its driver prints `0 0` for all 14 files |
| "the `commit` procedure → `test_every_row_has_a_procedure…`" | the guard is satisfied by `phases.md`'s H1, which names `commit`. Deleting the whole procedure leaves 600 tests green. The original mutation reverted via `git checkout`, restoring an H1 that did **not** name `commit` — so it measured the title, not the procedure |
| "the `adr` rename → same" | same mechanism; the mutation renamed the H1 along with the sections |

The table should not be trusted as filed. This correction is recorded here
rather than by editing the table, so the difference between what was claimed
and what holds stays visible.
