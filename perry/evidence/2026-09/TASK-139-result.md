# TASK-139 — result

> Branch: `coding/task-139-design-backref-w2`
> Baseline: `main` at `b4799f9`
> Status: DONE. Full suite green, `perry-lint --root .` at 0 errors.

## Provenance and two corrections to the dispatch brief

1. **The brief says the prior attempt left "no branch and zero commits — the
   whole round lost". That is false.** The branch
   `coding/task-139-design-backref` exists, is checked out in worktree
   `agent-a3e772f0d0d66b963`, and carries one commit of its own,
   `5af2111` (*"TASK-139 evidence file, committed before the baseline run"*),
   on top of `061ee7b`. Its stub result file survived. What was lost was the
   analysis, not the round's disk state.
2. Because that branch is checked out in another worktree, git will not let
   this isolated worktree take the name. This round therefore runs on
   `coding/task-139-design-backref-w2`, following the project's existing
   second-attempt convention (`coding/task-155-per-kr-assertion-date-w2`,
   `coding/task-284-round2b`).

This worktree was cut at `d49964e`, **143 commits behind `main`**, where
`perry/evidence/2026-09/TASK-139-spec.md` does not exist. The branch was cut at
`b4799f9` instead, the baseline the dispatch names.

## What this round is about to do

- Reproduce the before-state: `DESIGN-001` at `impl_refs=11` and the provenance
  of all 11, per § Verification 1.
- Pick between shape (a) structural field and (b) typed `design-link` event,
  with the reasoning recorded.
- Guard it with the two controls the spec names, and mutate every line claimed.

Sections below are filled as the round proceeds.

## Before-state, reproduced on `b4799f9` (§ Verification 1)

**The spec's number has drifted. `DESIGN-001` reports `impl_refs=18`, not 11.**
The spec measured 11 on `5c76aa2`; on the dispatch's own baseline `b4799f9` the
count is 18 — 3 store blobs and 15 event-log lines.

| source | count | rows |
|---|---|---|
| store blobs | 3 | `TASK-212`, `TASK-297`, `TASK-282` |
| event log lines | 15 | `TASK-282`(x3), `TASK-212`, `TASK-292`(x4), `TASK-293`, `TASK-284`, `TASK-297`, `TASK-258`, `TASK-139`(x2), one bare `intake` |

Every one is an incidental prose mention. **`TASK-001`…`TASK-006`, the six rows
that actually implement `DESIGN-001`, contribute zero** — they are absent from
the board entirely (closed and removed) and no event line names both a
`TASK-00[1-6]` id and `DESIGN-001` as that row's own subject. The three log
lines that contain both strings are prose: two are `TASK-139`'s own dispatch
notes and one is `TASK-282`'s, each quoting the task range inside a sentence.

**The count is self-inflating.** Two of the 18 are `TASK-139`'s own dispatch
events — the row filed to fix the false negative is now feeding it. The signal
gets further from honest every time the PMO writes about the problem.

`DESIGN-001` is `locked` (2026-08-16) with `impl_refs=18 > 0`, so it does not
appear in `pending_handoff`. That is the false negative, reproduced.

## Design chosen: **(a) a structural field** — and two of the spec's premises are wrong

### The premise that made (a) look expensive is false

The spec says (a) *"Costs a schema change — which is the escalated claim
surface — and a migration for existing rows"*, and § Out of scope escalates the
schema edit. **Neither cost is real.**

`schema/state-schema.json` does not enumerate task-record fields *at all*.
`grep -o "next_action\|stage_since\|depends_on" schema/state-schema.json`
returns nothing. Its `claims[]` (24 entries) declares **paths and owners**, and
its `files[]` (16 entries) enumerates **markdown documents** — `board`, `okr`,
`phase`, `linkage`, `design`, … `tasks.jsonl` appears in `claims` only as a
path owned by `work`, with no field list.

The store's field list is `bin/perry_store.py § STORED`, a 20-name tuple. Adding
to it is additive by construction: `validate_records` skips unknown fields
outright (`if field not in STORED: continue`), and the file's own comment
records that `summary` was added exactly this way under TASK-106 — *"TASK-106 is
additive: legacy records remain valid"*. **No schema file is touched, and
nothing under `claims` is touched.** The escalation the spec attaches to (a)
does not apply, so the round did not need to stop and file the question.

Migration is not needed for correctness either: an absent field counts zero.

### The premise that made (b) look necessary is also false

The row's title — *"a design back-reference lives in a cell the close path
clears"* — is obsolete at `b4799f9`, and not only in the way the dispatch says.
**The close path does not clear the record.** `perry/tasks.jsonl` holds **321
records**, `TASK-001`…`TASK-006` among them, each at `"status": "done"` with its
`verification` and `evidence` intact. `perry-task done` removes the row from
`BOARD.md`, which is a *projection* (ADR-007).

`walk_design` builds `task_blobs` from `board.all_tasks` — the projection — so
it cannot see a closed row and never could. **The defect is in the reader, not
in the storage.** A structural field on the canonical store record is therefore
already lifecycle-durable, and needs nothing from the event log to survive
closure.

### Why (b) would have been the wrong choice

(b) puts the only record of a load-bearing fact in `.perry/events.jsonl`, which
`bin/perry-task:42` calls **"DERIVED AND DISPOSABLE"**, and whose own header
rules the choice out by name:

> *"Anything load-bearing that lives only in this file is a bug in the same
> class — the file is allowed to make Perry slower to explain itself, never
> wrong."*

Choosing (b) means authoring a fresh instance of a bug the tool documents.

**And that bug is already present, which is a finding of its own.** Since
`ae505b3`, `impl_refs` reads every raw line of `.perry/events.jsonl`, so the
closed-row property that `ae505b3` bought — the property Control 2 protects —
depends *today* on a file the tool says may be deleted. Deleting it right now
would drop every locked design back into `pending_handoff`: wrong, not merely
slower. Reading the canonical store instead **removes that dependency**, so (a)
strengthens `ae505b3`'s property rather than merely preserving it.

### The shape

- `bin/perry_store.py § STORED` gains `design_refs`, a list of design ids,
  mirroring the existing `depends_on` list field.
- `bin/perry-task design-link` sets it, and appends a `design-link` event for
  history — the log carrying history, which is its documented job, rather than
  truth.
- `walk_design`'s `impl_refs` counts store records whose `design_refs` names the
  design, over **all** records rather than the board projection. The substring
  match over blobs and over raw log lines is deleted.

### What DESIGN-001 will report

`pending`, honestly — which § Verification 2 names as a pass. Backfilling the
six historical rows is explicitly out of scope ("*a migration is its own row and
its own decision*"), so this round makes the count honest and does not invent
the edges.

## After-state

`DESIGN-001` reports **`impl_refs=0`** and appears in `pending_handoff` —
**pending, honestly**, which § Verification 2 names as a pass. All 18 prose
mentions stopped counting; no edge was invented to replace them, because
backfilling the six historical rows is explicitly out of scope
(*"a migration is its own row and its own decision"*).

The mechanism is proven live rather than asserted. In a disposable copy of this
repository, `perry-task design-link TASK-001 --design DESIGN-001` — against a
row that closed months ago and has no line on the board — wrote
`design_refs: ["DESIGN-001"]` into the record and moved `DESIGN-001` from
`impl_refs=0` to `1` and out of `pending_handoff`. That is the deliverable
working end to end on exactly the row the spec names.

## The two controls

**Control 1 — a prose mention must not count.**
`TestProseDoesNotCount` adds a row whose `title`, `next_action` AND `evidence`
all name `DESIGN-009` with an empty `design_refs`, and `impl_refs` stays `0`.
Three further cases: a mention beside a real edge does not add to it (1, not
4); prose in the event log does not count; and `DESIGN-0091` no longer bleeds
into `DESIGN-009`, which a substring match did.

**Control 2 — a closed row must still count.**
`TestAClosedRowStillCounts` counts a record at `"status": "done"`, and
`test_closing_the_linked_row_does_not_clear_the_edge` runs the real lifecycle:
link, then `perry-task done`, then assert the row is gone from `BOARD.md` and
the edge and the count both survive. `ae505b3`'s property is intact.

It is also now **stronger than `ae505b3` left it**.
`test_it_survives_the_event_log_being_deleted` empties and then deletes
`.perry/events.jsonl` and the count does not move. Before this round it would
have collapsed to zero for every design: the property depended on a file
`bin/perry-task:42` says may be deleted at any time.

## Mutations — 12 planted, 11 red, and the green ones changed the code

Every mutation asserts the old text at its anchor before replacing it, so a
stale anchor raises instead of silently no-op'ing. Restores come from
`git show HEAD:<path>` and are re-verified with `bin/perry-restore-check`.

| # | mutation | first verdict | final |
|---|---|---|---|
| M1 | `store = load_task_store(root)` → `None` | RED | RED |
| M2 | count a substring of the record again | RED | RED |
| M3 | edge count capped at 1 | RED | RED |
| M4 | `design_refs` dropped from `STORED` | **GREEN** | RED |
| M5 | the carry in `store_records` removed | **GREEN** | RED |
| M6 | `design-link` dropped from `changed` | RED | RED |
| M7 | unknown design id accepted | RED | RED |
| M8 | `design-link` dropped from `in_place` | **GREEN** | RED |
| M9 | repeated design ids not collapsed | **GREEN** | RED |
| M10 | `validate_records` skips the list type | RED | RED |
| M11 | `record()` drops the list branch | **GREEN** | RED |
| M12 | `off_board=` forced to `False` | **GREEN** | *code deleted* |

**Six mutations came back green, and each was a real finding.**

*Two of them were dead code I had written, and they were deleted rather than
tested.*

- **M12.** `cmd_design_link` computed `off_board = not _row_is_on_the_board(…)`
  and passed it to `commit`. It does nothing: inside `commit`, `off_board`
  reaches one clause gated on `retitle` and the `in_place` decision, which this
  event already satisfies by name. Forcing it to `False` changed no test.
- The off-board branch in `commit` — `if projected is None and event_name in
  ("summary", "design-link")` — was **unreachable**. Instrumented rather than
  reasoned about: `projected is None` was `False` for `design-link` on a closed
  row with the log present, emptied, and deleted. `store_records` derives the
  projection from `ctx["task_records"]`, which is the STORE, and the store
  keeps terminal records. I had added the branch on the assumption that a
  closed row has no projection; the assumption was wrong and the mutation is
  what said so.

*Four were tests that named a line they never reached.*

- **M4 / M5.** `test_an_unrelated_write_does_not_clear_the_edge` cannot reach
  the carry at all: `commit` copies every non-subject row out of the store
  byte-for-field, so an unrelated write never rebuilds the linked row. The path
  where the carry is load-bearing is a whole-store rebuild —
  `perry-tasks write --from-board` — which now has its own test. `STORED`
  membership is load-bearing for the TYPE CHECK, not the write, so it is
  guarded by `validate_records` tests instead.
- **M8.** Nothing asserted that a store-only field write does not reorder the
  store. It does not, and a test now says so.
- **M9 / M11.** Deduplication of repeated ids, and `record()`'s list branch,
  had no coverage. Note M11's first test still passed the key explicitly, so
  the mutation was invisible to it; the sibling case — a record with the key
  ABSENT, where `task.get(k, "")` returns `""` instead of `[]` — is the one
  that bites.

## Files changed

| file | what |
|---|---|
| `viewer/parsers.py` | `impl_refs` counts declared edges from the store; the substring match and the four-level event-log walk are gone |
| `bin/perry_store.py` | `design_refs` added to `STORED`, `record()` and `validate_records` |
| `bin/perry-task` | `design-link` subcommand, event kind, `changed` whitelist, `in_place`, and the carry in `store_records` |
| `tests/test_design_handoff.py` | rewritten: both controls, the writer, the round trips |
| `tests/test_parsers.py` | TASK-292's negative control **inverted** — see below |
| `tests/test_project_root_resolution.py` | probe re-pointed off the deleted walk |
| `tests/test_prioritize.py` | `design_refs` allowed; word map and regex widened for the first hyphenated task event |
| `schema/task-list-contract.md` | the pair rebuttal: eight of sixteen → nine of seventeen |
| `schema/events-list-contract.md` | the `design-link` row |

**`schema/state-schema.json` is untouched, and so is everything under
`claims`.** The escalation was not needed; see § Design chosen.

## A defect removed in passing, named not closed

`walk_design` no longer reads `.perry/events.jsonl` at all, which makes
**TASK-292**'s defect — a fixture test reading the host repository's event log,
so a PMO prose edit reddens the suite — unreachable from this reader.
`tests/test_parsers.py`'s negative control asserted that removing a fixture's
own log REPRODUCED the leak; it cannot any more, so it is inverted to assert
the answer does not move. TASK-292 is named here, not closed here — its own row
covers other readers.

`bin/perry-lint § check_verification` is the second reader the § Bound names.
Untouched, per § Bound and `review.md § 1`.

## Verification summary

| | |
|---|---|
| Baseline suite | 113 modules · **3162 tests** · all green at `b4799f9` |
| Final suite | 113 modules · **3184 tests** · all green |
| `perry-lint --root .` | **0 errors**, 26 warnings — none from this change |
| Mutations | 12 planted · 11 red · 6 green findings, all resolved |
| Restores | `bin/perry-restore-check HEAD …` — 9 paths, all match |

