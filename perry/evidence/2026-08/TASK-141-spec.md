# TASK-141 — a row stays blocked after its blockers close

> Source: `bin/perry-task § startable`, and the two rows it stranded
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — one computation, plus whatever the close path needs
>   to keep it honest
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Measured 2026-08-20, on this project's own board

TASK-037 and TASK-045 both sat at `status: blocked` with **every** dependency
closed — TASK-037 on TASK-092, TASK-045 on the TASK-044 → TASK-047 chain, all
three `done`. TASK-045's own `Next action` still read *"blocked on chain
044 → 047 → 045"*, a chain that had fully closed.

Both reported, at the same time:

```
TASK-037  status=blocked  blocked_by=[]  startable=False
TASK-045  status=blocked  blocked_by=[]  startable=False
```

`blocked_by` is **empty**. The computation already knows nothing is blocking
them. Here is why nothing can say so:

```python
bin/perry-task:4728
task["startable"] = bool(task["open"]
                         and task["status"] not in {"blocked", "review"}   # read first
                         and not task["blocked_by"])                        # never reached
```

**The stored status is read before the computed `blocked_by` and masks it.**
`startable` can never contradict a stale `blocked`, so the disagreement is
invisible to every consumer.

The other half: `perry-task done` **never looks at dependents.** Closing a task
unblocks nothing, so the stale state is created by the ordinary close path and
then hidden by the line above.

Two of the four blocked rows were stale. The other two — TASK-050 on TASK-094,
TASK-067 on TASK-094 + TASK-095 — were genuinely blocked, and any fix has to
keep saying so.

## Deliverable

A row whose `depends_on` are all closed stops reporting as blocked **without
anyone noticing by hand.** Either:

1. the close path clears the status of every dependent it just unblocked, or
2. `startable` stops letting a stored status mask an empty `blocked_by`, and the
   payload surfaces the disagreement **by name** rather than silently
   recomputing it.

**These are not equivalent and the choice is yours to argue.** (1) mutates rows
as a side effect of closing another — powerful, and it writes state the user did
not ask for. (2) leaves the stored value alone and makes the contradiction
visible — honest, and the board still *reads* `blocked` until someone acts.
A third shape that does both is legitimate if you say why. Whichever you take,
**say in your result what the other one would have cost.**

## Verification — V3

1. **Both directions on one fixture.** A row whose every dependency is closed no
   longer reports as blocked; a row with at least one open dependency still
   does. The second is what stops this from being "delete the check".
2. **Reconstruct the real case.** A fixture reproducing TASK-037's shape —
   `status: blocked`, one `depends_on`, that dependency `done` — reproduces
   `startable=False` with `blocked_by=[]` on the current code, and does not
   after your change. Build it from the store's own writer, not by hand-editing
   a board.
3. **Reverting your change reddens exactly the new case** and not the
   genuinely-blocked one.
4. If you take option 1, a close that unblocks a dependent must be **visible in
   the event log** — a state change nothing recorded is the defect one level
   over, and this project has TASK-139 open for exactly that shape.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-task`
- focused tests and fixtures

## Out of scope

- **`conformance`'s stranded-row checks — that is TASK-142**, a separate row
  that reports this class rather than fixing it. Do not add
  `blocked_by_closed_rows` here; it will collide.
- `perry/` — no project state changes. **In particular, do not "fix" TASK-050 or
  TASK-067 on the live board.** `git diff -- perry/` must end empty.
- The `review` half of that same exclusion set. A row in `review` is waiting on a
  human, which is a different question from being blocked by a row.
