# TASK-092 — `OKR.md` and `.perry/config.md` become stores with renderers

> Source: `perry/design/DESIGN-005-state-and-contracts.md` § 5.5 steps 1–2; the same shape TASK-088/089/090 landed for `BOARD.md`
> Dispatch mode: auto
> Executor: claude-subagent (the pattern exists and is exercised; this applies it to two more files)
> Estimated cycle: large
> Subjective verification: `.perry/config.md` is documented as a file **the user owns and edits directly** — `SKILL.md` calls the track register "a tier-1 file the user owns and edits directly, because a track is configuration rather than state". Making it a rendered projection means a hand edit becomes reported drift. That may be right, and it is a change to what the user was promised about that file.
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Why this row is dispatchable, when a neighbouring one is not

`TASK-037-spec` carries `Executor: manual — not dispatchable`, citing
DESIGN-005 § 5.5: *"riskiest of the markdown three — `OKR.md` is prose the user
argues with"*, and **"the risk is not one a test catches: the failure mode is a
file that still parses and no longer reads the way its author wrote it."**

That verdict is about the `perry-goals` **writer**, and its reasoning turns on
the absence of a mechanical check. This row supplies exactly that check: a
renderer is correct only if it reproduces the file **byte for byte**, and
`bin/perry-tasks diff` already implements that comparison for `BOARD.md`. A file
that no longer reads the way its author wrote it fails a byte comparison by
definition. The precedent's reasoning does not transfer; its caution does, which
is why the verification below is two real projects rather than a fixture.

## Deliverable

1. A store for `OKR.md` and a store for `.perry/config.md`, in the shape
   `perry/tasks.jsonl` already has: the store holds what is written, everything
   else in the read contract is computed.
2. A renderer for each that reproduces the existing file **byte-identically**
   from its store, reusing `bin/perry_store.py`'s cell model rather than growing
   a second one. Note in particular the declared-blank-marker rule landed in
   `c9018ae`: an authored `—` is layout while the field is empty and is replaced
   when the store gains a value.
3. Writers write the store. `bin/perry-goals`' existing write path targets the
   store, and the file becomes the projection.
4. A hand edit to either file is **reported as drift**, not silently honoured
   and not overwritten — the same contract `perry-tasks diff` reports for the
   board.
5. The read contracts do not move. A consumer pinned to the current
   `perry-goals` payload needs no edit; this row changes where the bytes come
   from, not what any reader is told.

## Verification — V4

1. `render` reproduces this repository's `OKR.md` **byte-identically**. Not
   "parses the same" — byte-identically.
2. The same for `.perry/config.md`, including its `## Tracks` table and the
   `## Why the state root is not .` prose section this project carries.
3. The same two on a **second real project** — a copy of `~/proj/gimegime-pmo`,
   never the original. Two projects is the point: one project's file is a
   fixture wearing a disguise.
4. Mutate one field in each store and assert the rendered file moves with it,
   and that the drift report names the cell — the guard that the byte-identity
   above is not achieved by echoing the file back.
5. A hand edit to the rendered file is reported, with the cell named, and is
   neither honoured nor overwritten.
6. `python3 bin/perry-lint`, `python3 tests/parallel`, `bash tests/run`,
   `git diff --check`.

## Files in scope

- `bin/perry_store.py` — extend the shared cell model; do not fork it
- `bin/perry-goals` — write the store
- the new store/renderer entry points, following `bin/perry-tasks`' shape
- focused store and renderer tests, and their two-project fixtures

## Out of scope

- **`schema/state-schema.json`.** No entry is added, and in particular no
  `claims[]` entry: `tasks.jsonl` is itself in none, which is TASK-100's row and
  stays there. If this row appears to need a schema change, stop and say so
  rather than making one.
- `BOARD.md` and `perry/tasks.jsonl` — already done, and byte-identical output
  from them must be preserved.
- `bin/perry-task`, `work/reference/subcommands.md` — carried by a live dispatch.
- `bin/perry-decide`, `bin/perry-lint`, `bin/perry-migrate`, `bin/perry-diagnose`
  — each carried by an open unmerged branch.
- Deciding whether `.perry/config.md` **should** become a projection. Implement
  it, surface the tension named in `Subjective verification`, and let the user
  answer at close.
- Closing without the V4 evidence above.
