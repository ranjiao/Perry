# The witness project — a board in the conditions Perry's own board is not in

`tests/contract_key_parity.py` reads a contract page and the payload the tool
emits, and diffs one against the other. A key that lives **inside a collection
the project leaves empty** cannot be diffed at all: there is no entry to look
at, so the check reports it under `not_observable` and moves on. On 2026-08-27
that was **15 keys across four collections** — honest, and never once verified.

This directory is a Perry project whose own state puts those collections in a
non-empty state. The tools are run against it unmodified, with `--root`,
and every entry they report here is **derived** from the files below:

| collection | what in here produces it |
|---|---|
| `perry-decide` → `expired_sunsets` | `decisions/ADR-001-sunset-that-passed.md` is `active` with `Sunset: 2026-06-30` |
| `perry-goals` → `krs[].current_staleness.moved_tasks` | `linkage.jsonl` asserts each KR's `current` at 2026-08-05 (`asserted_at`); both linked rows moved on 2026-08-06 |
| `perry-goals` → `krs[].checks`, `krs[].checks[].measurement` (3.5) | `linkage.jsonl` declares one `increase` check on the overall `O1-KR1` (keyed by `okr_version: "v1: 2026-06-01"`) and on `P001-O1-KR1`, each measured once at 2026-08-05 |
| `perry-task` → `conformance.depends_on_unknown` | `WIT-002` depends on `WIT-404`, an id no register here carries |
| `perry-task` → `conformance.in_progress_with_no_live_run` | `WIT-001` is `in_progress`, holds no dispatch slot, and nothing has moved it since 2026-08-06 |
| `perry-task` → `conformance.review_idle` | `WIT-003` has been in `review` since 2026-08-06 and nobody has ruled on it |
| `perry-task` → `tasks[].evidence_relations` | `WIT-001` carries a real evidence cell naming a file, a file with a `§` section, a `(2 rows)` note and a directory — the four `kind`s, on the FIRST row, which is where a payload lists an entry shape from |

The first four are the ones that were unobservable when this project was
written. **`review_idle` is here for the general case**: it is
`in_progress_with_no_live_run`'s twin by design — TASK-176's pair — it happened
to be non-empty on Perry's board that night, and the day it empties is the day
its six keys would have gone dark. Holding it open here means the reading no
longer depends on which rows are idle that minute, which is what the fix has to
mean if it means anything.

**Nothing here is written into a payload by hand.** The distinction this
project turns on: a fabricated `depends_on_unknown` *entry* would be a lie
about a board, and TASK-132 forbids it. A dependency edge that genuinely names
an id nothing carries is not a lie — it is a project with a broken dependency,
which is a thing projects are — and the finding the real tool computes from it
is a true statement about **this** project.

## Rules for anyone who edits this

- **Do not fix the findings.** They are the deliverable. `WIT-404` stays
  unresolved, `WIT-001` stays idle, `WIT-003` stays unreviewed, ADR-001 stays
  `active` past its sunset, and `linkage.jsonl` keeps an `asserted_at` older than
  `.perry/events.jsonl`.
- **There is no `BOARD.md`** (TASK-262 round 4b). The project held one until
  its readers were retired; it was upgraded by
  `reference/version-compatibility.md § Upgrading a project to G3`. The task
  store was already canonical and was not re-imported (that would have
  overwritten `WIT-002`'s `depends_on`); the one bullet under `## Top risks`
  became `risks.jsonl` through `perry-task risk-migrate`, which is the one
  `risk-migrate` event and the journal day dated 2026-09-15. That event names
  no task, so no row's idle clock moved.
- **`WIT-001`'s evidence cell was written into the store by hand, on purpose,
  and no event was logged for it.** `perry-task evidence`
  would have appended an event dated today, and `WIT-001`'s whole job here is
  that **nothing has moved it since 2026-08-06** — writing that cell through
  the tool empties `in_progress_with_no_live_run`, the condition this row was
  added beside. Every path in the cell exists in this directory, so the cell
  is a true statement about this project and `evidence_not_found` stays empty.
- **`.perry/events.jsonl` uses real event kinds.** `add`, `start`, `status` —
  `bin/perry-task § TASK_EVENTS`. An event whose kind is not in that set is
  skipped when a row's timeline is built, so a plausible-looking `"created"`
  or `"review"` leaves `updated` null and silently empties two of the
  collections above.
- **Do not work this board.** It is read, never worked. No agent is dispatched
  here and no id here is minted anywhere else.
- **Timestamps are fixed in the past on purpose.** `idle_hours` grows with the
  wall clock and that is fine — the parity check compares key *paths*, never
  values, and the conditions above only get truer with time.
- Adding another condition here is how another collection stops being
  unobservable. **Add the state, never the finding.**
- A payload lists a collection's entry shape from its FIRST element, so a
  condition that only holds on `krs[3]` is not observable. That is why
  `linkage.jsonl` registers the overall KR as well as the phase one.
