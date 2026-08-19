# ADR-007 — Python owns typed fields; agents own prose; nothing parses documents

> Status: active
> Type: Architecture
> Date: 2026-08-19
> Deciders: Ran Jiao — **NOT YET DECIDED. Section 6 is the decision table.**
>
> **`Status: active` is the closest available word, and it is wrong.**
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

## 6. User decisions — NOT YET MADE

| # | Question | Options |
|---|---|---|
| 1 | Adopt the three rules as Perry's architecture? | accept / reject / accept for tasks only, i.e. leave ADR-006 as the whole of it |
| 2 | Does `BOARD.md` stop being hand-editable? | yes, it is rendered output · no, keep two-way and accept the parser · yes, but `perry-lint` gains a "you hand-edited a rendered file" finding |
| 3 | Split `By when` into `due` + `by_when_note`? | yes, and delete `CLOCK_RE` · no, keep one column and a sixth round |
| 4 | What happens to the 3,320 lines of parser? | delete with the last markdown-canonical reader · keep for adoption of foreign projects only · keep indefinitely |
| 5 | Scope of the first slice | TASK-038 as written · TASK-038 plus `By when` · a new phase |

## References

- `perry/decisions/ADR-006-task-store-is-not-the-log.md`
- `perry/design/DESIGN-005-state-and-contracts.md § 4`, § 6 step 4
- `perry/evidence/2026-08/TASK-042-round5-v4-review.md` — the fifth round, and
  the `\b`-does-not-exist-in-Chinese finding
