# ADR-014 — The ADR id high-water mark lives in a store, not in the event log

> Status: active
> Type: Architecture
> Date: 2026-09-02
> Deciders: Ran Jiao
> Supersedes: ADR-013   · Superseded by: —
> Sunset: —

## Context

`ADR-013` (2026-09-02, this morning) answered `USER-909`: an ADR id is an
address and is never reissued, with the high-water mark kept in
`.perry/events.jsonl`. Its measurements stand and are not revisited here — only
the highest id reissues, a middle gap is never filled, and `perry-decide` has
no delete command for option (b) to refuse in.

**What it got wrong was the elimination step.** ADR-013 rejected the obvious
home — a counter beside the other stores — on this ground:

> the cheap counter-file fix is foreclosed by `TASK-235`'s own guard,
> `tests/test_decide_writer.py:461` `ADR_ONLY = ^decisions/ADR-\d+-[^/]+\.md$`,
> which permits nothing but ADR bodies in `decisions/`.

That guard governs **`decisions/` only**. A store at the state root, beside the
six that already live there, is not an object it refuses. A local constraint was
read as a global one, and the correct answer was excluded by it.

**And the home that was chosen is declared disposable.** `DESIGN-004 § 5.3` and
`bin/perry-task --help` both say so in the same words: *"The event log is DERIVED
AND DISPOSABLE. Delete `.perry/events.jsonl` and Perry still works."* ADR-013
recorded the consequence honestly — deleting the log re-exposes reissue — and
then titled itself *"never reissued"*, so its title says `never` where its body
says `usually`.

**This project has run that experiment before.** `ADR-006` exists because
something load-bearing was put in the log: `DESIGN-004 § 5.3`'s disposability
sentence *"was false for a release, and is true again."* ADR-013 knowingly made
it half-false a second time, for a smaller fact.

Raised by the 2026-09-02 design-register audit, finding `G-04`, whose
reconciling argument is the one adopted here: **a high-water mark is current
state, not history.**

## Options

1. **A store at the state root — chosen.** The minted-id ceiling is a record in
   a JSONL store beside `tasks`, `risks`, `intake`, `asks`, `okr` and `config`.
   - Pros: it is what the fact IS. Current state, one place, the same shape and
     the same lint census as every other store. Survives deleting the event log,
     so the title's `never` becomes true.
   - Cons: a new claimed path, which is the undecided goal-5 question the same
     audit raises as `C-05`. That question is not settled here and this ADR
     should not be read as settling it.

2. **The event log — ADR-013's answer, superseded.**
   - Pros: no new claimed path; the log is already `owner: perry`.
   - Cons: the fact is not history, and the file is declared disposable. The
     guarantee is only as durable as a file the project tells everyone they may
     delete.

3. **A counter file inside `decisions/`.**
   - Rejected then and still rejected, correctly: `ADR_ONLY` permits only ADR
     bodies there. ADR-013's error was generalising this refusal to every
     location rather than to `decisions/`.

4. **Do nothing; keep ADR-013 and note the gap.**
   - Honest, and cheap. Rejected because `TASK-240` has not started, so the
     correction costs nothing now and costs a rewrite later.

## Chosen

**Option 1.** `mint_id` takes the maximum of the ADR files on disk and the
ceiling recorded in a store. An id, once issued, is never issued again, and the
guarantee does not rest on a file the project declares disposable.

`perry-decide` may still append an event for the audit trail — that is a trace,
not the source of truth, and nothing reads it to decide the next id.

## Consequences

- **`ADR-013` is superseded, not wrong.** Its measurements, its rejection of
  option (b), and its statement of the stake all stand. What changes is where
  the mark lives.
- `TASK-240` implements this ADR rather than ADR-013, and its acceptance moves:
  deleting `.perry/events.jsonl` must NOT re-expose reissue. That is the test
  ADR-013 could not have passed.
- The pin `test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge`
  is still inverted rather than deleted, unchanged from ADR-013.
- A seventh store is proposed here and an eighth in `DESIGN-015`. **Both are
  claims-surface changes and neither settles `C-05`** — whether
  `DESIGN-003`/`DESIGN-004` goal 5, *"zero new claimed paths"*, is retired in
  writing or still binding. That decision is open and this ADR is one more
  instance of it being taken without being taken.
- Middle gaps stay permanent; ids are not compacted. Unchanged.

## Evidence

- `perry/decisions/ADR-013-adr-ids-are-never-reissued.md` — the superseded
  decision, whose measurements this one keeps.
- `tests/test_decide_writer.py:461` — the `ADR_ONLY` guard, and the scope
  ADR-013 read too widely.
- `DESIGN-004 § 5.3` and `bin/perry-task --help` — the disposability
  declaration.
- `perry/decisions/ADR-006-*.md` — the precedent for putting a load-bearing
  fact in the log, and what it cost.
- The 2026-09-02 design-register audit, finding `G-04`.

## What would reopen this

- Goal 5 is settled the other way — every new claimed path refused — in which
  case the mark needs a home inside an existing claim.
- The store layer itself is replaced, at which point "beside the other six" is
  no longer a location.
- A second minter for ADR ids appears, so `max(files ∪ store)` stops being
  computed in one place.
