# The witness project — a board in the conditions Perry's own board is not in

`tests/contract_key_parity.py` reads a contract page and the payload the tool
emits, and diffs one against the other. A key that lives **inside a collection
the project leaves empty** cannot be diffed at all: there is no entry to look
at, so the check reports it under `not_observable` and moves on. On 2026-08-27
that was **15 keys across four collections** — honest, and never once verified.

This directory is a Perry project whose own state puts those four collections
in a non-empty state. The tools are run against it unmodified, with `--root`,
and every entry they report here is **derived** from the files below:

| collection | what in here produces it |
|---|---|
| `perry-decide` → `expired_sunsets` | `decisions/ADR-001-sunset-that-passed.md` is `active` with `Sunset: 2026-06-30` |
| `perry-goals` → `krs[].current_staleness.moved_tasks` | `phase/001-linkage.md` asserts `current` at 2026-08-05; both linked rows moved on 2026-08-06 |
| `perry-task` → `conformance.depends_on_unknown` | `WIT-002` depends on `WIT-404`, an id no register here carries |
| `perry-task` → `conformance.in_progress_with_no_live_run` | `WIT-001` is `in_progress`, holds no dispatch slot, and nothing has moved it since 2026-08-06 |

**Nothing here is written into a payload by hand.** The distinction this
project turns on: a fabricated `depends_on_unknown` *entry* would be a lie
about a board, and TASK-132 forbids it. A dependency edge that genuinely names
an id nothing carries is not a lie — it is a project with a broken dependency,
which is a thing projects are — and the finding the real tool computes from it
is a true statement about **this** project.

## Rules for anyone who edits this

- **Do not fix the findings.** They are the deliverable. `WIT-404` stays
  unresolved, `WIT-001` stays idle, ADR-001 stays `active` past its sunset, and
  `phase/001-linkage.md` keeps a date older than `.perry/events.jsonl`.
- **Do not work this board.** It is read, never worked. No agent is dispatched
  here and no id here is minted anywhere else.
- **Timestamps are fixed in the past on purpose.** `idle_hours` grows with the
  wall clock and that is fine — the parity check compares key *paths*, never
  values, and the four conditions above only get truer with time.
- Adding a fifth condition here is how a fifth collection stops being
  unobservable. Add the state, do not add the finding.
