# TASK-136 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-136-queue-sla` · Cycle time: ~55 min
> 6 files, +710/−3 · `tests/test_queue_sla.py` new, 26 tests

## The three sets provably partition the track

On a fixture with `sla: 5d`:

```
inside    arrived today−2  → in neither list; sla_check.measured counts it
breached  arrived today−9  → {"id":"T-LATE","arrived":"2026-08-12","age_days":9,
                              "sla":"5d","over_by_days":4,"commitment":"ops/1"}
no clock  Arrived blank    → sla_no_clock ["T-NOCLOCK"], absent from sla_breaches
```

And the clockless row **stays in `rows_with_no_computable_age`** rather than
being folded into *"not breached"* — asserted across both payloads. That is the
decision `cmd_route` had to make in the other direction, preserved.

## A track with no SLA says so, verbatim

```
sla_check.runnable: false   reason: "no-sla"
"track 'bare' declares no SLA — the breach step cannot run, and this is not
 zero breaches. Declare `SLA` in `.perry/config.md § Tracks`, or write
 `no SLA — best effort` there if that is the truth"
```

A **400-day-old** row on that track is not reported late. Two further
non-runnable reasons, both quoting the cell: `sla-not-a-duration` and
`not-a-queue-track`.

## Exactly-SLA-old falls inside, and the side is not the agent's opinion

`modes/queue.md`'s own triage step says *"rows whose `today − Arrived`
**exceeds** the track's `SLA`"* — **exceeds, not reaches.**

> A row that has used exactly its five calendar days is on its last day; calling
> that a breach reports the project late one day before it is.

Pinned from both sides at `5d` (5 clean, 6 breached, `over_by_days` 1) and again
at `2w` (14 clean, 15 breached).

## Item 4 — four mutations, four disjoint reds

| mutation | red |
|---|---|
| revert the breach append | 6, **all** breach/boundary; no no-clock test fired |
| fold no-clock into "not breached" | 8, **all** no-clock; no breach test fired |
| boundary moved to at-or-over | exactly the two boundary tests |
| invent a default SLA on a blank cell | exactly the four no-SLA tests |

## It corrected the spec it was given

The spec said `intake` is *"declared and empty"*. **By the time it ran, it held
12 rows** — every one added to that track during the night — all
`Arrived: 2026-08-20`. So the step runs **for real** here rather than on a
fixture, and item 5's empty case was asserted on a fixture instead.

Live, after merge:

```
main     sla=—     runnable=False  rows=26
intake   sla=5d    runnable=True   rows=14  breaches=0  no_clock=0
```

**That is KR-O1.2's first of three** — a live track's mode-specific triage
question producing real output. The first breach on this board falls due
**2026-08-26**.

## A finding it refused to absorb

**The two clockless readers disagree about `—`.** `perry-state`'s
`sla_no_clock` uses `lib § is_blank_cell`, so `—` / `n/a` / `无` are clockless.
`perry-task`'s `rows_with_no_computable_age` tests `not t["arrived"]` — raw
truthiness — so **a hand-written `—` reads as a clock there** and the row is not
flagged. Harmless on tool-written boards; live on a hand-edited one.

*One column, two readers, two answers — the shape this repo keeps paying for.*
Left alone because the spec inherited that report rather than editing it.

## Two boundaries recorded rather than guessed

`no SLA — best effort` is **blessed prose** in `modes/queue.md` and is reported
here as `sla-not-a-duration` — true and non-alarming, but it does not
distinguish a deliberate declaration from a typo'd `5 working days`. Recognising
it would be a new token, which the spec warned against, **so it is a question and
not a decision.**

And `h` units round **up** to whole days, because `Arrived` is a date with no
time of day. Stated in `sla_deadline` and tested; a project wanting sub-day SLAs
needs an `Arrived` that carries a time, which is a schema question.
