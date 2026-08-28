# TASK-062 — the overflow signal names intake, and the standup can see it

> Rung: **V3**. Every claim is a run or a mutation.

## The contradiction

`modes/queue.md` puts `## Intake` inside `BOARD.md` deliberately — DESIGN-003
decision 3 chose zero new claimed paths — and states the consequence outright:

> The cost of that choice is real and named in the design's risk table:
> untriaged requests compete with the 200-line board cap. **That cost is the
> feature.** An intake that overflows the board is a project that is not
> triaging.

`perry-lint`'s `size-cap` finding said: *"Split the overflow into a sibling file
rather than writing past it."* That is **moving the signal somewhere it can grow
unnoticed** — the one response the mode rules out.

And `perry-state` carried **no intake block at all**: `## Intake` matched
nothing in `viewer/parsers.py`'s board-section dispatch, so the correlation
`work/reference/subcommands.md § triage` asks for — over cap *because* intake is
undrained — was not computable from the payload the standup reads.

## Both halves

**The prescription is mode-aware.** When undischarged intake rows account for
the overflow, the finding names the count and forbids the split:

> `232 lines, over the tier-2 cap of 200 — and 220 of them are undischarged
> ## Intake rows. **Do not split this into a sibling file.** … Run triage and
> route or discharge the rows; the cap comes back on its own.`

A board over the cap for ordinary reasons still gets the old advice, verified on
a 220-task fixture. Prescribing triage to a project whose intake is empty would
be as wrong as prescribing a split to one whose intake is full.

**The payload carries it.** `perry-state --json` → `intake: {rows,
undischarged, oldest_undischarged}`. `rows` is table length; `undischarged` is
what is still waiting, which is the number that makes an over-cap board *mean*
something. A board with no intake section reports zeroes, not a missing key.

## The mutation that mattered

`intake_rows` counts **undischarged** rows. Mutating that filter to count every
row came back **green** — and that was a gap in my fixtures, not a decorative
guard: every one had all 220 rows still waiting, so nothing distinguished "220
requests are queued" from "220 requests were handled and left on the record".

`test_a_discharged_intake_is_not_the_cause_of_the_overflow` now builds the
second case — 215 of 220 routed — and asserts the *ordinary* advice comes back.
7 mutations, 7 red.
