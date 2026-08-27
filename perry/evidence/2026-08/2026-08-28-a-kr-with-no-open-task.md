# One KR in the live phase cannot move, and nothing says so

> Measured 2026-08-28 against `001bd2d`, while pricing TASK-094's scope
> decision. Not what I was looking for.

## The finding

```
002-linkage.md   P-O1.2   1.0 of 2.0   linked=1   STALLED — no open task
```

`P-O1.2` — *"`OKR.md` and `.perry/config.md` likewise [become stores]"* —
reports **1 of 2**. Its linkage register names exactly one task, `TASK-092`,
and `TASK-092` is **`done`**.

So the KR is short of target, honest about being short, and **there is no open
row anywhere on the board that would move it.** It cannot advance. Nothing
reports that.

## The missing half is real, and it is already declared

| | |
|---|---|
| `perry/okr.jsonl` | **exists** — the first half |
| `.perry/config.jsonl` | **does not exist** (`ls: No such file or directory`) |
| `schema/state-schema.json § claims[]` | **declares `.perry/config.jsonl`** — added 2026-08-21 answering `USER-016` |

Three independent records agree the second half is outstanding: the KR's own
number, the absent file, and a `claims[]` entry pointing at nothing. **The
project knows. The board does not.**

`TASK-092`'s title carries both halves — *"`OKR.md` **and** `.perry/config.md`
become stores with renderers"* — and it closed. Whether it closed early or the
scope shrank deliberately, I cannot tell from here and did not guess.

## The class, which is what makes this worth a row rather than a fix

**A KR whose `current < target` and whose every linked task is terminal is
stalled, and Perry has no signal for it.**

`perry-lint` has four linkage codes. None asks this. `perry-diagnose` reports
dangling ids and register reconciliation. Neither asks this. The information is
sitting in two files that are already parsed together — the linkage register
names the tasks and the store knows their status — and the join is never made.

It is adjacent to **TASK-156** (in flight tonight), which checks that a linked
task *exists*. This checks something different and strictly harder: that a
linked task can still *do* anything.

## The sweep, with the one result that is not a finding

```
001-linkage.md   P-O1.1   0.0 of 3.0   linked=3   STALLED
001-linkage.md   P-O1.2   0.0 of 3.0   linked=2   STALLED
001-linkage.md   P-O3.2   0.0 of 1.0   linked=4   STALLED
002-linkage.md   P-O1.2   1.0 of 2.0   linked=1   STALLED
```

**Only the last one counts.** `001-linkage.md` belongs to a phase that has been
scored and closed; a closed phase is *allowed* to end with unmet KRs, and
reporting those as stalled would be the exact bug `bin/perry-lint:1082`
documents at length — judging an old phase's register against today.

**Any guard built for this must be phase-scoped, and that is not a detail.**
Three of the four rows above are noise, and a guard that emitted all four would
be switched off within a day.

## What I did

Opened two rows and did not fix anything:

1. The config store — the half of `P-O1.2` that has no owner.
2. The signal — a stalled KR with no open task, phase-scoped.

I did not touch `perry/phase/002-linkage.md`. It belongs to the `goals` lane and
it is not wrong: **1 of 2 is the correct number.** The register is the only
artifact in this whole finding that is behaving properly.
