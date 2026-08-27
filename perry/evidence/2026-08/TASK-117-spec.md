# TASK-117 spec — two tools disagree about whether the board has drifted

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Reproduced on a scratch fixture 2026-08-27.

## The measurement

A project with `BOARD.md` and `perry/tasks.jsonl` and **no
`.perry/events.jsonl`**:

```
$ perry-lint --root .
⚠ perry/BOARD.md:47 [store-drift] TASK-050 — `created`: file='' store='2026-08-17T19:24:52' …
⚠ perry/BOARD.md:73 [store-drift] TASK-066 — …
⚠ perry/BOARD.md:48 [store-drift] TASK-067 — …
   (many more)

$ perry-state --root . --json → board.drift
{"checked": false, "baseline": "", "drift": 0, "unrecorded": 0, …}
```

**One tool reports drift on the same tree the other reports `drift: 0` on.**

`checked: false` is honest as far as it goes. **`drift: 0` sitting beside it is
the trap** — a consumer that reads the number and not the flag concludes clean.
That is the same shape as `not_observable` reading zero, and this project has
already decided how it feels about it.

## The precedent is in-tree and was written this week

`perry-lint` says, on this very project:

```
· no `risks.jsonl` — drift against the risks store is unchecked, not clean
```

**"Unchecked, not clean"** is the answer. TASK-040 shipped that phrasing for the
risks store, and `bin/perry-lint § check_store_drift` states the rule in its own
docstring: *"'No store' and 'clean' are different answers."*

So this row is not a design question. It is one tool having learned the lesson
and the other not.

## The scope

Make `perry-state`'s `board.drift` say *unchecked* in a way a consumer cannot
read as *clean*, and make the two tools agree about when a comparison happened.

**Decide and argue which of the two is right about the drift itself.** They
differ on more than the flag: with no event log, `perry-lint` still compares the
board against the store field-by-field and finds differences, while
`perry-state` declines to compare at all. One of those is the correct behaviour
for a project with a store and no log, and the row is not done until you say
which and why.

Note before you assume `perry-lint` is right: several of its hits in the
reproduction are `created`: `file='' store='…'`, i.e. the board carries no such
column. Whether that is drift or an artifact of comparing a field the projection
does not render is **part of what you must determine**.

## Verification

1. On a project with a store and **no** event log, `perry-lint` and
   `perry-state` agree about whether a comparison happened and about the count.
2. A consumer reading only `board.drift`'s numeric fields **cannot conclude
   clean** when nothing was compared. Say how you achieved that — a null, a
   separate field, a refusal to emit the number. Argue the choice.
3. On a project **with** an event log, both tools' answers are unchanged.
   Byte-compare the payload against the base for this repository.
4. Mutation: reverting your change reddens a test that names the disagreement.
5. `perry-lint --root .` — 0 errors.

## Out of scope

- The risks store's own drift reporting — TASK-040 did that and it is the model
  you are copying, not the thing you are changing.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/` must
  end empty.
- `perry-state`'s payload is unversioned; you do not need a contract bump. If
  you find yourself wanting one, stop and report.

## Ground rules

- Branch `coding/task-117-drift-unchecked-not-clean`, commit there, **no PR, no
  push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly — Perry is stdlib-only as of
  tonight and that flag is what proves it.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`.
- Expected baseline: **80 modules · 2369 tests · 2 red** —
  `test_contract_invariance` (a union-typed key) and `test_diagnose` (two
  failures). **Neither is yours.**
- Other agents may be in `bin/perry-task`, `bin/perry-diagnose` and
  `tests/contract_key_parity.py`. You need `bin/perry-state` and
  `bin/perry-lint`.
