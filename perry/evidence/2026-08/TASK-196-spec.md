# TASK-196 — `## Intake` becomes a store, following the risks precedent exactly

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `94aade4`

## The precedent, which was exercised end to end today

**Do not invent a mechanism.** `bin/perry-tasks` already carries two store
families, and the second is the template for yours:

```
perry-tasks risks-build    derive the store; write nothing
perry-tasks risks-render   the store → `## Top risks`   [--write]
perry-tasks risks-write    --from-board, the one-way import
perry-tasks risks-diff     render and byte-compare
```

I ran all four on this project an hour ago. **`risks-diff` returning
`identical: true` with `cells_verbatim {}`, `cells_wearing_decoration {}`,
`cells_the_store_and_board_disagree_on []` and `rows_out_of_stored_order {}` is
the gate the tool declares for itself** (`bin/perry-tasks:22`), and the import
only ran because it passed. Yours needs the same gate and the same four
difference sets.

**Read `perry/evidence/2026-08/TASK-195-result.md` first.** It is one page and
it is the worked example.

## The register

`viewer/parsers.py:1548 § _parse_intake` — `{arrived, request, outcome,
discharged}`, and its docstring states why `discharged` exists rather than being
derived at read time:

> a row whose `Outcome` is empty is still waiting, and the count of those is
> what makes an over-cap board mean *"the queue is not being drained"* rather
> than *"the board is long"*.

`BOARD.md § Intake` today: header `| Arrived | Request | Outcome |`, **54 rows**.
The count moves — I added several today — so **derive it, never hardcode it**.

Writers: `bin/perry-task § cmd_intake`, `cmd_resolve_intake`, `cmd_intake_sweep`.
They currently write the board section directly. After this row they write the
store and the section is rendered.

## The one thing that makes this harder than risks

`## Intake` rows have **no id**. Risks have `RX-001`. An intake row is addressed
by its **position** — `perry-task resolve-intake 36` takes an integer, and I
used exactly that today.

**So the store has to answer what `n` means across a write.** Decide and state
it: is `n` stored, or is it the row's ordinal in the store, and what happens to
`n` when an earlier row is discharged? A consumer that read `36` yesterday must
not silently get a different row today. **This is the judgement call of the
row** — say what you chose and what it costs.

## Files in scope

`bin/perry-tasks`, `bin/perry-task` (the three writers), `bin/perry_md_store.py`
or `bin/perry_store.py` as the shape requires, `schema/state-schema.json §
claims[]` (the store must be declared — `risks-write` refuses when the claim is
absent, and yours should too), `tests/`.

## Out of scope

- `## User Input Queue` (TASK-197) and `## Cadence` (TASK-198) — same shape,
  separate rows, and one at a time is how the risks one stayed provable.
- `perry/BOARD.md` except through `render --write`.
- The contract version, **unless** a payload key changes meaning. Say which.

## Verification

1. **`intake-render` reproduces the current 54-row section byte-for-byte before
   any write path is trusted**, with all four difference sets empty. Show it.
2. `intake-write --from-board` refuses when `claims[]` does not declare the
   store, the way `risks-write` does.
3. A hand edit to `## Intake` is **reported as drift** afterwards, and
   `perry-lint` gains a positive reading the way it did for risks:
   `· risks store: 4 record(s), 0 risk(s) drifted`.
4. **Mutation proof with counts**, including one that proves the `n` decision.
5. `perry-lint` otherwise unchanged: 0 errors, 3 warnings, 194 records, 0
   drifted. Suite: **88 modules, one red** (`test_diagnose`).

**Do not run the import on this project** — deriving and byte-comparing is this
row; running `--from-board` on the user's own board is theirs, as it was for
risks and for config.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
