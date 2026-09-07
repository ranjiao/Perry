# TASK-394 — spec

> Design: `design/DESIGN-015-linkage-is-a-store.md` § 5.3 and § 5.5
> Dispatch mode: auto
> Executor: claude-subagent — touches `perry-task`'s `commit()` and recovery marker, the riskiest write path Perry has
> Estimated cycle: medium
> Subjective verification: the flag's spelling and whether a declaration may be withdrawn
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track**: main
- **Dependencies**: `TASK-279` (row D, the transaction this joins) — landed
- **KR linkage**: `P003-O3-KR2` — this row is what makes that KR reachable

## Why this row exists

`USER-921` chose **(A)** on 2026-09-08: give `add` a writer for the declaration,
rather than restate the KR so that omission counts as an answer. The alternative
was rejected because after it **a KR at 100% would say nothing about whether
anyone was ever asked** — never-asked and declared-no-KR would collapse into one
reading, the exact distinction `DESIGN-015 § 5.2` built the derivation to tell
apart.

## The design already specifies the record; only the writer is missing

`§ 5.3` defines the KR as a count over *"rows whose `add` event carried a
non-null `kr`, **or for which an `unlinked` record exists with `via: "add"`**"*.
`§ 5.5`'s table assigns that record to the **`work`** lane, produced by *"`add`
with an explicit unlinked declaration"*. `bin/lib/__init__.py:741` **already
reads exactly that shape.**

**Verified before filing**: `via: "add"` is hardcoded at exactly one site,
`bin/perry-task:2798`, which writes **edge** records; `bin/perry-goals:2022`
appends an `unlinked` record carrying **no `via` field at all**. Nothing anywhere
produces `kind: unlinked` with `via: "add"`.

So this row builds **the one half of § 5.5 that was never implemented**, and it
changes no reader.

## Deliverable

`perry-task add` can declare, at creation, that a row serves no KR — writing
`{"kind":"unlinked", …, "via":"add"}` into `linkage.jsonl` **inside the same
recovery marker and `commit()` as the row itself**, exactly as row D's edge does.

## Four things it must not do

1. **It must not make `--kr` mandatory.** Omitting it stays legal and stays a
   warning — `§ 5.2`'s *record and warn*. The new declaration is a third state,
   not a replacement for silence.
2. **It must not retroactively re-declare rows already filed without `--kr`.**
   Those stay never-asked, which is **true of them**. So **the KR will not jump
   when this lands, and should not.**
3. **The declaration must not half-land.** Same recovery marker, same `commit()`,
   same canonical set as the row — an `unlinked` record written as a second
   transaction is a row that claims an answer nothing backs, which is the defect
   row D was built to avoid.
4. **It must not accept a blank or ambiguous value** the way `--kr "   "` was
   accepted before `TASK-281` round 2 refused it. Whatever spelling you choose,
   a malformed one is a refusal.

## The judgement, and it is yours to make and state

**The flag's spelling.** `perry-goals link --unlinked <TASK-ID>` is the existing
precedent on the other lane. Decide and say why, and say what happens if both it
and `--kr` are passed — that is a caller contradiction and must be refused, not
resolved by precedence.

**Whether a declaration can be withdrawn.** The linkage writer is append-only
with no retraction (`TASK-391` is a live row about exactly that shape). If a
declaration cannot be withdrawn, say so in the refusal text at the point it is
made, so a caller learns it before rather than after.

## Verification

1. **The one sequence**, nothing run in between: file a row with the declaration,
   then `perry-state --section linkage`. It must count as **answered** and the KR
   must rise. Show the before and after.
2. **Silence still means never-asked**: a row filed without `--kr` and without
   the declaration still lands in the denominator, still warns, and does **not**
   count. Show it.
3. **Atomicity, and the bar is higher than row D's was.** Row D claimed five
   crash points; `TASK-279`'s V4 found **seven**, because row D's harness kills
   only before *canonical renames* while the event append is an `open(...,"a")`.
   **You inherit the seven-point matrix, not the five.** At every one, the
   declaration must not survive alone.
4. **A control**: the record you write is byte-identical in shape to what
   `bin/lib:741` reads — assert against that predicate, not against a literal.
5. **Mutation**: revert the writer and show a **named** test go red; and revert
   the `via` value alone and show a different one go red. A green mutation is a
   finding — `TASK-281` round 1 closed one against a fixture that could never be
   produced, and round 2 had to re-open it.

## Bound

```
Enumeration: the three record kinds in schema § stores.declared.linkage.jsonl
Size:        3 — kr, edge, unlinked
This row:    `unlinked` written by the work lane at add time. One cell of the
             § 5.5 table: {work} × {unlinked}.
Remainder:   {work}×{kr} is "never" by that table; {goals}×{all three} is
             `perry-goals link`, already built. The last element is the
             work-lane `unlinked` writer this row builds.
```

## Out of scope

- Any change to how the KR is computed — `bin/lib:741` already reads this shape.
- Backfilling the rows already filed without `--kr` — phase 004's, and item 2 above.
- `perry-goals link --unlinked` — the other lane's writer, already built.
- The four publishers of `current` — that is `TASK-382`.
