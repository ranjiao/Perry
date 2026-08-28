# TASK-118 — three of the four minters never got ADR-007's treatment

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `b7ca674`

## The measurement

`bin/perry-task` has **four** id minters. Exactly one reads the canonical store:

| minter | line | reads |
|---|---|---|
| `mint_id` (TASK-) | 1636 | **the canonical store**, via `minting_records` |
| `mint_user_id` (USER-) | 4013 | `board.text()` ∪ journal ∪ events |
| `mint_cadence_id` (CAD-) | 4106 | board ∪ journal ∪ events |
| `mint_risk_id` (RX-) | 4346 | board ∪ journal ∪ events |

**All three of the others carry the docstring `"…from max(board ∪ journal ∪
events), like `mint_id`"`** — and `mint_id` has not worked that way since
ADR-007. Their docstrings cite a function whose behaviour changed underneath
them. TASK-167 corrected the module docstring that made the same claim; these
three were not in its scope.

So the row's title is right and slightly understated: it is not that the store
is missing from a list of sources, it is that **three minters mint from a
rendered projection** while the project's whole Objective 2 is that the store is
canonical and the markdown is derived.

## Why this is now sharper than when the row was opened

**TASK-167 (merged tonight) made a record able to leave the store.** `purge`
retires a task id by unioning the store with every id `purge` removed —
`minting_records`, *"what a new id may not be"*.

`mint_user_id`, `mint_cadence_id` and `mint_risk_id` have **no equivalent**.
Work out and state whether they are safe today and why. They read the event log,
which is append-only and still carries a purge event — so they may be safe *by
accident*, through a path nobody chose. **"Safe by accident" is a finding, not a
pass.** Say which it is, with the mechanism.

## The one that is worst, and it is `RX-`

`risks.jsonl` is **declared in `claims[]` and does not exist** — `perry-lint`
says so every run: *"no `risks.jsonl` — drift against the risks store is
unchecked, not clean"*. And `USER-016`'s answer records why: *"`cmd_risks_write`
was never built."*

So `mint_risk_id` reads the markdown board for a register whose store is
declared and absent. **Do not build the risks store** — that is `USER-016`'s
open item and not yours. But your change must not make it harder, and you should
say what `mint_risk_id` should read on the day it exists.

## What to build

Bring the three onto one mechanism with `mint_id`, or state precisely why one of
them cannot come. The bar is that **the source of truth for an id is the same
kind of thing for all four**.

Two constraints:

1. **A register with no store still needs a minter.** `CAD-` and `RX-` have no
   `.jsonl`. Whatever you do must work for a register whose canonical form is
   still the markdown, without pretending otherwise in a docstring.
2. **Do not renumber anything.** Existing `USER-`, `CAD-` and `RX-` ids are on
   the board and in the event log. `USER-903` was minted tonight.

## Files in scope

`bin/perry-task`, `bin/lib/`, `tests/`.

## Out of scope

- Building `risks.jsonl` or `cmd_risks_write` — `USER-016`.
- `bin/perry-decide § mint_id` (line 242, `ADR-`) and any minting in
  `bin/perry-goals` / `bin/perry-migrate`. **Measure them and say what you
  find** — they may be the same defect one file over — but do not change them.
- `mint_id` itself. TASK-167 just landed there; leave it.

## Verification

1. A test per minter proving what it reads, failing if it reads something else.
2. **Mutation proof per minter**, with counts.
3. `USER-903`, and the highest live `CAD-` and `RX-`, still resolve; the next
   minted id of each family is unchanged by your change. Prove it, do not assert
   it.
4. `perry-lint` on this repository: **0 errors, 3 warnings, 173 records, 0 rows
   drifted** — unchanged. If it moves you have found something; report it rather
   than adjusting to fit.
5. State your answer to the purge question above.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
