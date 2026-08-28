# ADR-007 — Python owns typed fields; agents own prose; nothing parses documents

> Status: active
> Type: Architecture
> Date: 2026-08-19
> Deciders: Ran Jiao — **DECIDED 2026-08-19. Section 6 records the answers.**
>
> **`Status: active` was the closest available word and was wrong while this
> was a proposal; it is right now.** The gap it exposed stands:
> `bin/perry-decide` hardcodes `STATUSES = ("active", "superseded",
> "expired", "archived")` — not in the schema, not in any enum, and with no
> word for *drafted, awaiting a decision*. So a proposal cannot be filed as
> one, which is why every ADR in this repository reads `active`.
>
> That gap is this ADR's own thesis, found while filing this ADR: a field
> whose value space is spelled in a tool's `--help`, enforced from a hardcoded
> tuple, and bound in the schema nowhere.
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

**The diagnosis is the user's, on 2026-08-19:** Perry is hard to change because
it uses deterministic Python and regular expressions to answer questions about
*generalized natural-language prose*. The direction is backwards — state is
written as a document and then parsed back into fields, when it should be held
as an enumerable structured store and **rendered** into documents.

The measurement supports it, and it is not close.

**The schema names columns and describes them in English.** `BOARD.md`'s
required columns are a bare list — `['ID', 'Title', 'Owner', 'Status', 'Next
action', 'Evidence']` — with no types attached. The optional ones are prose:
*"Which declared track this row belongs to. Absent = the implicit `main`
track."* Eight enums exist at the top of the schema and are applied at six
sites. **Nothing binds a column to its value space**, so every check that needs
to know what a cell may contain re-derives it, in Python, from prose.

**3,320 lines exist to invert that direction** — `viewer/parsers.py` (3,015) and
`viewer/tables.py` (305) — plus 41 call sites in `perry-lint` and every guard
written to protect them.

And the recurrence record over one night says the same thing:

| Defect | Rounds | Why it recurs |
|---|---|---|
| `CLOCK_RE` — does this cell name a clock? | **5**, in 4 shapes | it is a natural-language question asked of a regex |
| "is this cell that column?" | **4**, 5 live copies | structure re-derived from prose, per reader |
| a `--next` value destroying its own row | 2 | a value lives in a markdown cell |
| `ROUND-2` read as an identifier | 3 | ids scanned out of prose |

`CLOCK_RE`'s fifth round is the proof. `\b` does not exist in Chinese, so the
English half matched on word boundaries and the Chinese half on bare substrings,
and `下周期` ("next cycle") wrote a live commitment row while `next cycle` was
refused. Four rounds had each moved that asymmetry rather than removing it.
**No fix to a regex ends this**, because the regex is answering a question
prose does not have a determinate answer to.

## Decision

**Three rules, and the third is the one that changes how agents work.**

1. **A field with a bounded value space is TYPED, and Python owns it.** Status,
   priority, rung, track, stage, mode, dates, ids, counts. The schema binds each
   to its enum or format; the tools validate against that binding and nothing
   else.
2. **A field with an unbounded value space is PROSE, and Python never parses
   it.** Title, next action, deliverable, promise, reason, evidence prose. It is
   stored and rendered verbatim. **No regex asks it a question.**
3. **The agent protocol inverts:** before doing anything, call the tool to read
   or write fields. Then, from what the tool returned, **generate** the spec and
   evidence documents. **The Python layer never parses a document at all.**

### The field that proves the rule

`By when` is *both*: 105 cells in this repository are a bare ISO date, 4 are an
SLA shorthand, and the rest are prose naming a clock. One column, two value
spaces, which is exactly why one regex has failed five times.

Under rule 1 and 2 it **splits**: `due` (ISO date or a declared SLA token —
typed, validated, sortable) and `by_when_note` (prose, never validated). Then
`CLOCK_RE` is deleted rather than given a sixth round.

### What this dissolves, and what it does not

Dissolved: the header rule, `split_row`/`render_row`/the `\|` escape,
`ragged-row`, rows destroyed by their own writer, ids scanned out of prose,
and `CLOCK_RE`.

**Not dissolved, and worth saying so:** vocabulary sprawl (`reference/glossary.md`
and its brake), the verification ladder and V4 discipline, and the evidence
documents themselves — which are prose, stay prose, and *should*.

## Relationship to ADR-006

ADR-006 decided this **for tasks**: `perry/tasks.jsonl` is truth, `BOARD.md` is
a projection, `.perry/events.jsonl` stays a log. This ADR **generalizes the same
move to every field of every state file**, and adds the agent protocol.

ADR-006 is not superseded; TASK-038 is its implementation and is still
`not_started`. If this is accepted, TASK-038 becomes the first slice of it
rather than a standalone change.

## Consequences

**The cost, stated plainly: `BOARD.md` stops being the thing you edit.** Today a
human can open it and change a cell, and Perry reads it. Under this it is
rendered output — a hand edit becomes drift, which `perry-state § reconcile_drift`
already reports rather than honours. That is a real loss of a real property, and
it is the main argument against.

Every existing project is markdown-canonical today. `perry-migrate` and ADR-004's
migrate-once posture are the path; the two real projects on this machine
(gimegime-pmo, PolyForge) are the test.

## 5b. The split runs per FILE, not per repository — measured

The parser serves **16 state files**, not just the board, so "stop parsing
documents" is not one decision. Counting each file's typed table columns
against its prose sections settles most of it:

| File | Table columns | Prose sections | What it is |
|---|---|---|---|
| `BOARD.md` | **35** | 0 | a store, rendered |
| `OKR.md` | **12** | 0 | a store, rendered |
| `.perry/config.md` | **8** | 0 | a store, rendered |
| `phase/NNN-*.md` | 4 | some | mixed — the KR table is a store, the rest is prose |
| `DECISIONS.md` | 4 | some | mixed — the index is a store, each ADR is prose |
| `.perry/roles/*.md` | 0 | **5** | a document. Stays one |
| `design/*.md` | 0 | **10** | a document. Stays one |

**So rule 1 and rule 2 partition the files, not just the fields**, and the
first slice picks itself: `BOARD.md` has 35 typed columns and no prose
sections, which is why every recurring defect this ADR cites lives there.

`design/*.md` and `.perry/roles/*.md` go the other way and go there **harder**:
under rule 2 Python should not be parsing them at all, not even leniently. It
should locate the file and hand it to an agent.

## 6. User decisions — NOT YET MADE

| # | Question | **Decided 2026-08-19** |
|---|---|---|
| 1 | Adopt the three rules as Perry's architecture? | **Accept.** |
| 2 | Does `BOARD.md` stop being hand-editable? | **Yes — it becomes rendered output, and a hand edit becomes drift.** Measured before deciding: `perry-state § drift` reports `drift: 0` on this project, so the property being given up is one almost nobody exercises. `unrecorded: 4` is a different thing — rows whose state moved with no event — and it does not change under this. |
| 3 | Split `By when` into `due` + `by_when_note`? | **Yes, and `CLOCK_RE` is deleted rather than given a sixth round.** |
| 4 | What happens to the 3,320 lines of parser? | Follows from 1 and § 5b: the readers for `BOARD.md`, `OKR.md` and `.perry/config.md` go when those become stores. The readers for `design/*.md` and `.perry/roles/*.md` go too, and **for a different reason** — under rule 2 Python should not be parsing prose at all; it locates the file and hands it to an agent. What survives is adoption of a foreign project, which is parsing by definition. |
| 5 | Scope of the first slice | **A new phase**, covering all three stores — `BOARD.md`, `OKR.md`, `.perry/config.md` — rather than `BOARD.md` alone. TASK-038 becomes its first task rather than a standalone change. |

### What decision 5 commits to

One phase, three stores, and the `By when` split inside it. The alternative —
`BOARD.md` first and the rest later — was rejected because the three share one
parser and one migration path, and migrating them separately means running
`perry-migrate` against the same projects three times. ADR-004's *a project
migrates once* is the posture; three slices would break it in spirit.

## References

- `perry/decisions/ADR-006-task-store-is-not-the-log.md`
- `perry/design/DESIGN-005-state-and-contracts.md § 4`, § 6 step 4
- `perry/evidence/2026-08/TASK-042-round5-v4-review.md` — the fifth round, and
  the `\b`-does-not-exist-in-Chinese finding
