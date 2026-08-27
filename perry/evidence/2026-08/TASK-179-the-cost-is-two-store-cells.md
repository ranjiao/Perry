# TASK-179 — the cost is two store cells, and one of them is TASK-179's own

> Measured 2026-08-28 against `9653156`, to make the morning's decision a
> choice between things rather than between descriptions of things.
> **It kills two of the three options I put in the handoff.**

## What I told you, and why it was the wrong frame

The handoff said: *four ids, added by evidence records; the options are widen
the mark, exempt evidence records, or accept the cost.* That framing came from
counting **documents**. Counting documents is what made it look like an
evidence-record problem.

```
TASK-007    {evidence: 13, journal: 1, handoff: 1, BOARD.md: 1}   16 documents
TASK-9999   {evidence: 12, journal: 1, handoff: 1, BOARD.md: 1}   15
USER-900    {evidence:  3, journal: 2, handoff: 1, BOARD.md: 1}    7
USER-902    {evidence:  1, journal: 1, handoff: 1, BOARD.md: 1}    4
WIT-404     {evidence:  1, journal: 1, handoff: 1, BOARD.md: 1}    4
```

46 document-touches. On that reading, *"reword the records"* was already
unaffordable and *"exempt evidence records"* looked like the cheap fix.

## The measurement that changes the answer

**Exempt `evidence/`, `journal/` and `handoff/` — all three, entirely — and the
dangling list does not shrink by one id.**

```
TASK-007    survives in: ['perry/BOARD.md']
TASK-9999   survives in: ['perry/BOARD.md']
USER-900    survives in: ['perry/BOARD.md']
USER-902    survives in: ['perry/BOARD.md']
WIT-404     survives in: ['perry/BOARD.md']
```

Every one of the five. `BOARD.md` is a **rendered projection of
`perry/tasks.jsonl`**, so the mention is not in a document anybody wrote — it is
in a store cell, and the renderer puts it on the board every time it runs.

## It is two cells

```
TASK-165  .next_action   names  USER-900
TASK-179  .next_action   names  TASK-007, TASK-9999, USER-900, USER-902, WIT-404
```

That is the entire population. **TASK-179's own `next_action` supplies five of
the five** — the row that exists to describe the defect is the row committing
it, and it does so because I wrote the evidence into the cell where the tool
asks what happens next.

**So the exit is not a document policy.** Rewording the fourteen evidence
records would have left the list exactly as it is.

## What each option is actually worth now

| option | what it costs | what it leaves |
|---|---|---|
| **Widen the check-name mark** | the mark is scoped to a **paragraph** (`bin/perry-diagnose:700-776`), deliberately and with an argument in its docstring. A `next_action` is a **table cell**, not a paragraph. Widening the paragraph rule reaches none of the five. | the red |
| **Exempt evidence records** | measured above | **the red, unchanged** |
| **Exempt `BOARD.md`** | `BOARD.md` is where a *genuine* dangling reference surfaces. Exempting it removes the check's main surface to save two cells. | a check that cannot see its own subject |
| **Move the prose out of the cell** | the two `next_action` cells become short, and the detail moves to the evidence record it belongs in — which is exempt or not, but no longer decides anything. `next_action` is *"what happens next"*, not a findings register. | nothing red, nothing exempted, nothing widened |
| **Accept and stop asserting zero** | honest; costs the assertion | a check nobody is required to keep at zero |

## The recommendation, and it is not one of the three I offered

**Move the prose out of `next_action`.** It is the only option that removes the
red without weakening the check, and it is arguably right independent of this
row: a `next_action` cell currently carrying a five-id findings paragraph is
being used as a place to write, and there is a `perry/evidence/` for that.

Concretely: TASK-179's `next_action` becomes a pointer to this document, and
TASK-165's stops naming `USER-900` inline. Two `perry-task` calls.

**What that does not settle**, and you should decide it knowingly: the check
still charges the project the day a `next_action` legitimately needs to name an
id that has no record — a row about a *missing* thing. That case has not
happened yet. When it does, this decision comes back, and the answer will
probably be the exemption. **Deferring it is a choice, not an oversight.**

## The second failure in the same module

`test_diagnose` is red twice. The other one is not this:

```
test_the_queue_register_reconciles_with_the_queue_on_this_repository
  diagnose and perry-task disagree about how many queue rows
  are waiting on the user:  2 != 0
```

`perry-task list --json` reports `asks.open: 0` with an empty `items[]`.
Diagnose's register says 2. **Whatever this is, it is not the dangling-id
question**, and closing TASK-179 will not make `test_diagnose` green on its own.
Filed as intake so it stops riding along on TASK-179's back.
