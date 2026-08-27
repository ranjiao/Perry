# A KR in the live phase cannot move — and the reason is a decision, not a gap

> Measured 2026-08-28 against `001bd2d`, while pricing TASK-094's scope
> decision.
>
> **This document was wrong when I first wrote it, an hour before this version.**
> It said `.perry/config.jsonl` was absent because work was missing and no row
> carried it. Both halves are false. What follows is the corrected finding, and
> the correction makes the item *cheaper* for you, not more expensive. The
> original text is in git at `47352c0`.

## What is true

```
002-linkage.md   P-O1.2   1.0 of 2.0   linked=1   its one task is `done`
```

`P-O1.2` is *"`OKR.md` and `.perry/config.md` likewise [become stores]"*. The
first half shipped — `perry/okr.jsonl` exists, because **you ran
`perry-okr write --from-file` at the start of this session.** The second half is
absent from disk.

## Why it is absent, which I did not check the first time

**`bin/perry-config` is complete.** Five commands, the same five `perry-okr` has:

```
perry-config build    derive the store; write nothing
perry-config verify   field-compare the store to the file
perry-config render   the store → .perry/config.md
perry-config write    --from-file → the store
perry-config diff     render and byte-compare
```

It runs today. `perry-config build` on this project returns **9 records — 7
settings and 2 tracks** — without writing anything.

**The store is absent on purpose, and TASK-092's own dispatch note says so in as
many words:**

> *`SKILL.md` promises `.perry/config.md` is "a tier-1 file the user owns and
> edits directly". Making it a projection turns a hand edit into reported drift.
> The agent implemented it and left the decision open: **no store exists until
> `perry-config write --from-file` is run, and every read path is unchanged
> until it is.** So the capability ships without the promise being broken until
> someone chooses to break it.*

And the phase consequence was recorded at the time, not discovered by me:

> *`P-O1.2` … On this reading the KR is **not yet met** by this row alone.
> Recorded rather than resolved; **it is the user's to read.***

## So the item is one decision, and it is yours

**Do you want `.perry/config.md` to become a rendered projection?** Saying yes
costs one command and moves `P-O1.2` from 1 of 2 to 2 of 2. Saying yes also
means a hand edit to your own config file becomes **reported drift** — at
`warn`, the severity you chose on 2026-08-21 — which is a change to what
`SKILL.md` promised you about that particular file.

It is the same shape as the OKR migration you chose to run this session. The
difference is that `OKR.md` was never promised to be hand-owned and
`.perry/config.md` was.

**Nothing is missing. Nobody dropped anything.** A row deliberately stopped one
step short and wrote down why.

## What I got wrong, and the general lesson in it

I read three artifacts that agreed — the KR's number, the absent file, and a
`claims[]` entry pointing at nothing — and concluded work was missing. **All
three are consistent with "the user has not run the command yet", and I did not
check for the command.** `bin/perry-config` is in `bin/README.md`, one grep away.

Three agreeing records are not corroboration when they are three views of the
same fact.

## The `risks.jsonl` case is the same shape and is also recorded

`perry/risks.jsonl` is likewise declared in `claims[]` and likewise absent.
`perry-lint` says so every run — *"no `risks.jsonl` — drift against the risks
store is unchecked, not clean"* — and `USER-016`'s answer records the gap
precisely: *"The declaration alone does not enable risks-write —
`cmd_risks_write` was never built; the refusal now reads the claim and names the
gap that is actually open."*

Confirmed: **0 matches for `cmd_risks_write` in `bin/perry-task`.** Unlike
config, this one really is unbuilt — but it is unbuilt *on the record*, in the
answer to an ask, which is where it belongs.

**Two declared-and-absent stores, two different reasons, both written down.**
The system worked. I was the one who did not read it.

## The signal is still worth building — and now it is better specified

A KR short of target whose every linked task is terminal is still invisible, and
the join is still never made. But this case teaches the guard its hardest
requirement:

**It must distinguish "stalled" from "waiting on a decision that is correctly
the user's."** Fired here, a naive guard would have reported `P-O1.2` as a
problem when the row is behaving exactly as designed — and would have been as
wrong as I was, for the same reason.

Perry has the register that answers this: `USER-` asks. A KR whose remaining
work is gated on an open ask is *waiting*, not *stalled*. That distinction is
the row.

## And the phase-scoping requirement, unchanged

```
001-linkage.md   P-O1.1   0.0 of 3.0   STALLED
001-linkage.md   P-O1.2   0.0 of 3.0   STALLED
001-linkage.md   P-O3.2   0.0 of 1.0   STALLED
002-linkage.md   P-O1.2   1.0 of 2.0   ← the only live one, and it is a decision
```

Phase 001 is closed and is *allowed* to end with unmet KRs. A guard that emits
all four is 75% noise and would be switched off in a day — the bug
`bin/perry-lint:1082` documents at length.

**Between phase-scoping and the waiting-vs-stalled distinction, a naive version
of this guard would be wrong on four of four rows on this project today.**
