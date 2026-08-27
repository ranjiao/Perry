# TASK-123 — two tools write the same file in opposite directions

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `017132d`

## The measurement

`bin/perry-okr` is store-first, with the five commands ADR-007 asks for:

```
perry-okr build    derive the store; write nothing
perry-okr verify   field-compare the store to the file
perry-okr render   the store → OKR.md
perry-okr write    --from-file  OKR.md → the store
perry-okr diff     render and byte-compare
```

`bin/perry-goals` writes **the same file** the other way. `ctx["okr"]` is
`Okr(state_root / "OKR.md")` (line 2805), and `cmd_commit` (2337) *"Add, update,
close or miss one row of `OKR.md § Commitments`"* — **editing the markdown
directly**, with the store derived afterwards if at all. `perry-goals` mentions
`okr.jsonl` twice in the whole file.

So `OKR.md` has **two writers with opposite notions of which artifact is true**,
and the user ran `perry-okr write --from-file` on this project this session — so
the store exists and is live.

## What makes this a P1 rather than tidiness

ADR-007's claim is that **a hand edit to a rendered file is reported rather than
honoured**. A second writer that edits the rendered file *as its normal
operation* is not a hand edit and is not reported — it is a supported path that
does the thing the ADR exists to prevent. `perry-lint` reports **0 rows drifted**
today, which means either the two are in accidental agreement or the drift check
does not cover this register. **Establish which. That answer is the row.**

## What to do

Bring `perry-goals`' writes of `OKR.md` onto the store, or state precisely why a
register cannot come. Three constraints:

1. **`## Commitments` is `goals`-owned** per the hand-off contract, and stays so.
   This is about *which artifact it writes*, not about who writes it.
2. **`OKR.md` must not be re-rendered as a side effect.** `perry-okr render`'s
   byte-comparison is the bar — if your change makes `render --write` produce
   different bytes than the file has now, you have changed the user's file.
   Prove it does not.
3. **Do not touch `perry-okr`.** It is correct.

## What to establish and state before changing anything

- **Does `perry-lint`'s drift check cover `OKR.md § Commitments`?** If it does,
  why is drift 0 with two writers? If it does not, that gap is a finding in its
  own right and may be bigger than the row.
- **How many `perry-goals` subcommands write `OKR.md`?** `cmd_commit` is the one
  I found. **Grep for the write, not for the name** — six of my specs in two days
  named a call site once where there were more, and the seventh over-counted the
  same way.

## Files in scope

`bin/perry-goals`, `bin/lib/`, `tests/`, `schema/goals-list-contract.md` (only if
the payload's meaning changes — say so and version it if it does).

## Out of scope

- `bin/perry-okr`, `bin/perry-config`, `perry/okr.jsonl`.
- `perry/OKR.md` — read-only. If the file needs migrating, that is a command the
  **user** runs, exactly as they ran `perry-okr write --from-file`. Say what the
  command is; do not run it.
- `USER-903` (whether `.perry/config.md` becomes a projection) is a separate open
  decision. Do not pre-empt it.

## Verification

1. A test that the store is the source for every `perry-goals` write of
   `OKR.md`, failing if a write path reads the file as truth.
2. **Mutation proof with counts**, per write path you touched.
3. `perry-okr diff` byte-clean before and after.
4. `perry-lint`: **0 errors, 3 warnings, 173 records, 0 rows drifted** —
   unchanged. If drift moves, report it rather than adjusting to fit.
5. Suite: **86 modules, one red** (`test_diagnose`, standing).

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
