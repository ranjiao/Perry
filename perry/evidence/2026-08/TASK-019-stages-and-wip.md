# TASK-019 — the other two findings: two readers, two answers, and a step with no data

> Rung: **V3**. Every claim is a run or a mutation. TASK-056 closed the first of
> this row's three findings; these are the other two.

## Finding 2 — the reader denied a stage the writer was using

On a queue track with a blank `Stages` cell, reproduced before fixing:

```
perry-state  → stage_list: []          "this track has no stage vocabulary"
perry-task   → row born at 'triaged'   the mode's default entry stage
```

`stages_of` had a mode-default fallback; `parse_tracks` had none. **`[]` was the
wrong answer**: a track that declares no stages still has them — its mode's — and
every row the writer creates lands in one.

`stage_list` is now the **effective** vocabulary, read from the same
`work_modes.modes.<mode>.default_stages` the writer reads, and
`stages_declared` keeps "did the project declare them" answerable rather than
one field trying to mean both.

## Finding 3 — not a contradiction; a step with nothing to read

`grep -i wip bin/perry-task` returned nothing, and `modes/pipeline.md` **says so
itself**: *"The checks a future release would build are: WIP overflow, an item
in no stage, and a `done` row that never reached the terminal stage. Until then
they are rules an agent follows, not rules a script catches."* An honest
concession, materially unlike TASK-056's case where three documents claimed a
check that lived somewhere else.

What the concession left behind was worse than the missing check. **`viewer/
parsers.py § Task` carried neither `track` nor `stage`** — the two columns the
non-`project` modes are *defined* by — and `perry-state` reads the board through
that class. So the mode's own triage step 2, "stages at their WIP limit", was
doable only by eyeballing a board the triage procedure forbids eyeballing.
Meanwhile `perry-task/list` parsed both columns with its own reader: two readers
of one board, and the one the standup and triage use had dropped exactly the
columns the mode measures.

Both columns now resolve **by header name** in that parser, and
`perry-state --json` reports per track:

- `stage_counts` — the whole distribution, because triage step 2 also asks for
  the oldest item per stage and a count that only appeared on breach would make
  the ordinary case unreadable;
- `wip_breaches` — every stage **at or over** its declared limit, with the count
  and the limit. *At*, not over: the stage is full and the next arrival is the
  problem.

A track that declares no `WIP` reports counts and no breaches. Silence where the
project made no promise — inventing a limit is the mistake `no_default` exists
to prevent.

`modes/pipeline.md`'s concession paragraph now records **which of its three
checks landed**, and a test asserts it, because a concession that stops being
true and stays written is the defect this project keeps finding.

## Mutations

11 written. **Three came back green on the first pass and all three were my
mutations, not blind guards** — recorded because the difference matters:

- `tr["wip_breaches"] = [] or [...]` is the identity; `[]` is falsy.
- `parse_wip(cell or "review:1")` never fired, because the fixture's blank cell
  is `—`, not the empty string — the very tolerance `UNDECLARED_CELL` exists for.
- The mode-file mutation changed a heading sentence while leaving both strings
  the test asserts on.

Redone against the real anchors: red, red, red. 11/11.
