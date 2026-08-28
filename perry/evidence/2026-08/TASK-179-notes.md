# TASK-179 — notes moved off the board, 2026-08-28

> Moved here by `/perry work triage` on 2026-08-28, for the reason given in
> `TASK-077-notes.md`: the `Next action` cell held a record rather than a next
> step, and the 2026-08-20 precedent is that rewriting such a cell in place
> destroys the only copy.

## The cell, verbatim

> FOURTH INSTANCE, added tonight by me: `perry/evidence/2026-08/TASK-132-result.md:28`
> names WIT-404 while describing the witness fixture, and WIT-404 is
> DELIBERATELY dangling inside that fixture — an id no register carries is the
> whole point of it. `tests/fixtures/` is illustrative so the fixture's own
> README does not charge the project; my record does. The dangling list is now
> TASK-007, TASK-9999, USER-900, USER-902, WIT-404 — five ids, every one of
> them added by a record describing a checker or a fixture.

## The running list this row exists to settle

| id | added by | why it dangles |
|---|---|---|
| TASK-007 | a record describing a checker | — |
| TASK-9999 | a record describing a checker | — |
| USER-900 | a record describing a checker | — |
| USER-902 | a record describing a checker | — |
| WIT-404 | `evidence/2026-08/TASK-132-result.md:28` | deliberately dangling **inside the fixture**; an id no register carries is the fixture's entire point |

**Five ids, and every one was added by a record that documents a checker or a
fixture.** That is the shape of the problem: writing *about* a dangling-id
check costs a dangling id, and the reconcile test asserts zero.

`tests/fixtures/` is illustrative, so the fixture's own README does not charge
the project — but an evidence record describing that fixture does.

## Board state at the time of the move

`not_started` · P1 · `startable: true` · `blocked_by: []`. Its one declared
dependency, TASK-210, is `done`. Not blocked; unstarted.
