# Escalation override — TASK-290 and TASK-308, 2026-09-03

> Written because `.perry/hook.md § High-stakes operations` is a safety gate and
> an override that leaves no record is indistinguishable from a gate that never
> fired. Both halves are here: what the gate refused, and who released it.

## What the gate said

`bin/perry-state --escalation-scan`, **exit 3, verdict `refuse`**, on both specs.

| row | refused on | where the fragment sits | what the row actually writes |
|---|---|---|---|
| `TASK-290` | `evidence/` | one sentence in `## Deliverable` that **explains the false positive** — *"the hook means someone else's `evidence/`"* | `viewer/parsers.py`, `bin/perry-state`, two test files |
| `TASK-308` | `diagnose`, `evidence/` | `## Deliverable` — a citation of `reference/diagnose.md`, and *reading* `evidence/**/*-spec.md` | `bin/perry-lint`, `tests/` |

Neither row writes into `evidence/`, `design/`, `knowledge/` or `inputs/`, which
is what `.perry/hook.md:34` escalates (*"overwriting a project's own …"*).
`diagnose` matched the **filename** `reference/diagnose.md`, not the
`/perry diagnose` pipeline the hook's bullet names.

**This is the documented false-positive class**, filed as `TASK-290` itself and
re-measured on `47fa45a`: 25 of 145 specs refused, 13 legitimately
(`state-schema.json` 8, `claims` 5) and 12 on citations (`evidence/` 8,
`diagnose` 8, `design/` 4).

## Who released it, and what was not done

**The user authorised the dispatch of both rows on 2026-09-03**, having been
shown the refusal, the fragments, the sections they sit in, and the four
available routes (authorise · move the sentence · `delegate` · fix the hook).

**Nothing was reworded to pass.** `.perry/hook.md` says rewording to get past a
gate is the one thing a safety gate must never reward, and both specs go out
byte-identical to the versions the gate refused. The PMO declined to move
`TASK-290`'s explanatory sentence out of `## Deliverable` on its own initiative,
because it wrote that document and is not the right party to decide where that
line falls.

## The precedent this sets, stated rather than left implicit

This is the **first** override of an `exit 3` refusal on this project. It is
scoped to these two specs at these bytes. It is not a standing permission, and
a future refusal — including a later round of either row — gets its own
decision.

`TASK-290` is the row that removes the need for overrides of this class: it is
currently blocking `TASK-308`, `TASK-219`, `TASK-263` and `TASK-099` on
citations.


---

## Correction, 2026-09-03, after TASK-290 landed

**This record was wrong about `TASK-219`.** It listed four rows as blocked "on
citations". `TASK-219` was not one of them: its refusal is `state-schema.json`
in `## Deliverable` — the claim surface, legitimate — and it **still refuses**
after TASK-290's fix. Verified. Only `TASK-308`, `TASK-263` and `TASK-099` were
citation-blocked, and all three pass now.

**The override is spent and is not needed again for this class.** `TASK-290`'s
own spec now scans `exit 0`; `TASK-308`'s did too, before it was dispatched
under this override and has since landed. Any future refusal gets its own
decision, as this record already said.

## What the override bought that nobody expected

TASK-290's round found **seven** specs passing on a green light, not the one its
spec described — and **three of them named `schema/state-schema.json` in their
own `Files in scope`**, the write-intent section, cancelled by a mention in
`Out of scope`. `TASK-047`'s body says outright that it "really does edit" it.

**`TASK-139` is one of the three, and the PMO dispatched it twice on 2026-09-03
while the gate reported clean.** Nothing was harmed: both briefs told the agent
not to touch the schema. But that was the brief doing the gate's job.

So the override, taken to unblock a citation false-positive, surfaced a
false-**pass** over the claim surface that had been live the whole time. Both
directions of the same defect, and only one of them was visible.
