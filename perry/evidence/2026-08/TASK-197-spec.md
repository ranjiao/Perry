# TASK-197 — `## User Input Queue` becomes a store, and which columns are stored is the row

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `afd3e56`

## Two precedents now, both exercised end to end today

```
perry-tasks risks-build / risks-render / risks-write --from-board / risks-diff
perry-tasks intake-build / intake-render / intake-write --from-board / intake-diff
```

**Read `perry/evidence/2026-08/TASK-196-result.md` first.** It is the closer of
the two and it is one page. Do not invent a third mechanism.

## The register, and why it is not intake with different words

`BOARD.md § User Input Queue` today:

```
| USER-id | Needed from user | Blocks | Idle | Status | Asked |
```

`viewer/parsers.py:1547 § _parse_user_input` — read its docstring in full before
anything else. Two things in it are the row:

> **Three real shapes are in circulation**: five columns with `Idle` (Perry's
> own board), four without it (**a live project dropped the column because a
> stored age is stale the moment it is written**), and five with `Asked`
> instead.

> **Third location of this defect.** The first two were `_parse_task_table` and
> the writer/reader split it caused.

## The judgement call: which columns are stored, and which are computed

`Idle` is an **age**. A live project deleted the column on the ground that
storing one is wrong. `intake` has the mirror of this and TASK-196 answered it:
`discharged` is stored *because* it rides inside prose the reader cannot re-derive,
while nothing derivable is stored.

**Decide what `Idle` is** — a stored cell the store carries, or a value computed
at read time from `Asked` — and say why. Then apply the same rule to every
column and state the result. **A store that carries a derived age is a store that
is wrong the moment it is written**, which is exactly the sentence that live
project acted on.

Note the count: Perry's board has **six** columns; the docstring says five. One
of them is stale. **Establish which and say so** — do not assume the code or the
comment.

## What `USER-` ids give you that intake did not

An intake row has no id, which made `n` TASK-196's whole judgement call. **A
`USER-` row has an id**, minted by `perry-task ask` through `mint_user_id` —
which TASK-118 rebuilt onto `mint_register_id` in August. So `order` is not
load-bearing here the way it was there.

But **check before relying on it**: is the id unique across answered and open
rows, and is it stable across a sweep? `perry-explain` resolves `USER-` ids
today; a store that renumbers them breaks that.

## Files in scope

`bin/perry-tasks`, `bin/perry_md_store.py` / `bin/perry_store.py` as the shape
requires, `schema/state-schema.json § claims[]` (the store must be declared —
both precedents refuse the import when the claim is absent), `bin/perry-lint`
(the drift check), `tests/`.

## Out of scope

- **The writers.** `perry-task ask` / `answer` keep writing the section, exactly
  as `risk-add` and `perry-task intake` still do. **TASK-203 covers all of them
  in one row** — TASK-196 declined this for a reason worth repeating: converting
  one register's writers alone makes an ordinary command mint a store as a side
  effect on a project that never ran the gated import, and leaves two registers
  with two answers to the same question. **Three would be worse than two.**
- `## Cadence` (TASK-198).
- Running `--from-board` on this project. Deriving and byte-comparing is the
  row; the import is the user's.

## Verification

1. **Render reproduces the current section byte-for-byte**, count derived and
   never hardcoded, with all four difference sets empty.
2. **But read TASK-196 § "the byte gate cannot fail for this register" first**
   and establish whether the gate is load-bearing *here*. For risks it catches a
   collapsed duplicate id; for intake it caught nothing and a row-count gate was
   built instead. **A `USER-` register has ids, so the risks argument may apply
   — check, and say which.** Reporting "the gate is a tautology here" is a
   result, not a failure.
3. A hand edit to the section is reported as drift; `perry-lint` gains its
   honest line the way risks and intake did.
4. **Mutation with counts**, including one that proves your `Idle` decision.
5. `perry-lint` otherwise unchanged. Suite: **89 modules, one red**.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
