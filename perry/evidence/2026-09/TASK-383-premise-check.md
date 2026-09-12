# TASK-383 — the premise, checked before writing a spec

> Written by the PMO on 2026-09-12, in place of the spec the row was asked
> for. **The defect this row describes no longer exists, and it was not fixed
> — it was removed by `ADR-019` on 2026-09-08, four days ago.**
> This file is the measurement, not the decision. Dropping the row is the
> user's call: `ADR-013` makes an id terminal and never reissued.

## What the row claims

> Filing a row with `--kr` writes the edge into the store, which leaves the
> register document stale and `perry-lint` reporting drift. The tool named as
> the way to clear it answers nothing to write, because it checks the store,
> where the edge already is. The drift is therefore permanent and grows by one
> row per `add --kr`, in the one store this phase just finished making a real
> drift verdict for.

Three things have to be true for that: a register **document**, a **drift
check** comparing it to the store, and a writer that **judges from one and
writes to the other**. All three are gone.

## 1. The document

```
$ ls perry/phase/*linkage*
zsh: no matches found
$ git log --oneline --diff-filter=D -- 'perry/phase/003-linkage.md'
054aac6c ADR-019: phase/<NNN>-linkage.md deleted; linkage.jsonl holds 241 records
```

`054aac6c`, **2026-09-08**. The row's `Next action` records it as *"UNBLOCKED
2026-09-08 by the phase 003 mid-phase triage"* — the same day. The triage
unblocked a row whose premise that day's ADR was deleting.

## 2. The drift check

`bin/perry-lint` has already retired it, and says so in its own past tense:
*"This used to iterate `phase/*-linkage.md` and choose, per phase, between…"*
(:1371), *"this function used to hold `linkage.jsonl` up against
`phase/<NNN>-linkage.md`"* (:4949), and the payload key is now `linkage_store`
rather than `linkage_store_drift` (:5861).

The before and after, both from the project's own output:

| | |
|---|---|
| `ADR-019` § Context, before | `linkage store: 124 record(s), 1 row(s) drifted` |
| today | `linkage store: 256 record(s), 0 malformed` |

There is no drift line for linkage any more, because there is no second copy to
drift from. A count of malformed records is a different verdict about a
different thing.

## 3. The writer

`bin/perry-goals § link_edge` — the exact function the row names — describes the
defect in the past tense as its own docstring:

> **Judged against the graph, written to the store, and after ADR-019 those are
> one file.** The question "is this task already linked, and to what" is a
> question about the project; it is answered from `linkage.jsonl`, which is
> also where the answer is written. **The old writer asked the store and
> spliced the document, and the two could disagree between the two writes.**

The `already linked` short-circuit the row calls a defect is now correct by
construction: the graph it judges against and the store it writes to are the
same file.

## What this means, and what it does not

**It does not mean the row was wrong.** It was true when filed. `ADR-019` was
decided on a different argument — *one place per fact* — and removing this
defect was a consequence nobody listed. That is worth saying because it is the
second time today a row's premise was found gone rather than met: `TASK-379`'s
exhibit had closed itself, and this one was deleted by an ADR.

**What it changes for `O3`.** The recommendation for `P003-O3-KR2` was to make
`perry-task add` REFUSE without `--kr` or `--unlinked` and re-baseline the
denominator. That recommendation was hedged on this row — making the gate
mandatory would multiply whatever drift this row described. It would multiply
nothing. **`TASK-383` is not a precondition for that option**, and the
sequencing note that said it was is withdrawn here.

## The remaining question, if any

Whether `add --kr` has any *other* unclearable consequence now. Measured: no.
`linkage.jsonl` is the single home, `link_edge` reads and writes it, and
`perry-lint` reports `0 malformed` over 256 records. If a second copy of an
edge is ever reintroduced, this row's mechanism returns with it — and that is
a new row, not this id.
