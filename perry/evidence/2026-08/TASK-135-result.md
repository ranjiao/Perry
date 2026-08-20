# TASK-135 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-135-move-row-to-track` · Cycle time: ~35 min
> 6 files, +713/−18: `bin/perry-task` (+189, `cmd_track`),
> `tests/test_track_move.py` (new, 30 tests), `tests/test_prioritize.py`,
> `schema/task-list-contract.md`, `schema/events-list-contract.md`,
> `work/reference/subcommands.md`

## The clock decision, and the argument is better than the question

`Arrived` is **carried** on a queue→queue move — never restamped, because
resetting it to today would **erase an in-flight breach**, the same exemption
arriving through the other door. It is **cleared** on a move off a queue, with
what it held written to **both the journal and the event**.

The reasoning, from the code rather than from taste:

> `Arrived` is not provenance, it is **a queue's clock** — `cmd_route`'s own
> docstring says *"today − Arrived is the number every SLA check measures"* — and
> a clock left on a row no queue governs is a live-looking number the next SLA
> reader picks up.

And it is already load-bearing in the negative direction, **measured**:
`cmd_route` had to *stop* writing `Arrived` onto pipeline rows precisely because
a non-empty `arrived` hides the row from `rows_with_no_computable_age` — the
finding that says *"this row has no clock at all"*. Keeping it would suppress the
one report that could notice the move.

**Dropping the cell is not dropping the fact.** That is `drop`'s precedent one
field down: the journal is append-only, so the fact moves to the surface that
records *what happened* rather than *what is true now*. `--arrived` on a
destination that cannot read it is **refused**, not silently ignored.

## The refusal, in one place so three entrances cannot disagree

```
perry-task: refused — track 'ops' is not declared in `.perry/config.md § Tracks`.
Declared: main, intake, press. Add a row to that table naming its mode, or name
one of those. Nothing was written
```

With no declared tracks it reads *"(none — this project has only the implicit
`main`)"*. Exit 1, no traceback, no track created, no event written. The wording
lives in `track_of`, which `add`, `route` and `track` all call.

## The event's `field` is `track`, not `stage`

```json
{"event":"track","field":"track","from":"<old>","to":"<new>",
 "stage","stage_from","arrived","arrived_from","reason"}
```

Deliberate, and the reason is worth keeping: **a consumer told the pair was a
stage would resolve `main → intake` against a stage vocabulary that does not
contain them.**

## Item 5, in its stronger form

Not just *"lint reports no `store-drift`"* after a move in both directions — the
clearing direction being the one a renderer can silently skip — but also that
**`perry-tasks render --write` after a move leaves `BOARD.md` byte-identical**,
which is what proves the store learned all four cells and not only `track`.

## Four questions handed back

1. **TASK-136 gets sharper, not softer.** Rows now reach a queue track carrying
   a real `Arrived`, and `today − Arrived` is still computed nowhere. **The clock
   this row makes correct still has no consumer.**
2. A move does not re-derive `Verification` from the destination's
   `default_rung` — deliberate, because ADR-005 makes the rung a claim about who
   is hurt when the work is wrong, and `default_rung` is a birth default. Worth
   an explicit decision rather than silence: this repo's `intake` overrides
   queue's V2 to V3 for exactly such a reason.
3. A move does not check the destination's WIP limit. Consistent with
   `cmd_stage`, which also does not — **but it is now reachable in bulk.**
4. `bin/perry-goals § track_named` is a **second copy** of the undeclared-track
   refusal with a different tail. Left alone as out of scope, but it now words
   the same failure differently from `perry-task`'s.

## Merged

`--no-ff` into `feat/work-modes`, alongside TASK-121. Post-merge: **70 modules ·
2042 tests · all green**, `perry-lint` 0 errors, 0 rows drifted. **No live row
was moved** — `git diff -- perry/` was empty; using the tool on this board is a
separate act.
