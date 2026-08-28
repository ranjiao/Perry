# TASK-196 — the Intake store, and the gate I mandated turned out to be empty here

**From `coding/task-196` @ `981aa8c`.** Rung **V3**. The import was **not** run
on this project: `perry/BOARD.md` untouched, `perry/intake.jsonl` still absent —
that write is the user's, as it was for risks and for config.

## The shape

`perry/intake.jsonl`, keys in `INTAKE_STORED` order:

```
order        int, 0-based — THE KEY
arrived · request · outcome     the three cells
discharged   bool — the one stored field with no column
```

`discharged` is this register's `cleared`: whether a request has left the queue
rides inside the `Outcome` cell's prose, so the store carries it typed. Carried
across `--from-board` **only when the store says `True`**, because
`check_intake_undischarged` makes discharge one-way — `True` is a fact the board
cannot un-say, `False` is *"still waiting"*, which the cell answers for itself.

Four verbs, the risks four with one word changed. Plus `intake.jsonl` in
`claims[]`, `check_intake_store_drift` in `perry-lint`, and 50 tests.

## It refused the gate I made non-negotiable, and it was right

I wrote that the byte-for-byte render *"is not negotiable"*. It complied, then
reported:

> **The byte gate cannot fail for this register; its green is a tautology.**

**Measured, not asserted** — escaped pipe, ragged short row, ragged long row,
missing trailing pipe, blank first cell, indented line: **all six byte-identical
either way.** For risks the same gate catches a real class (a repeated `RX-001`
is one record rendering two lines). Nothing here collapses anything.

So it kept the gate, labelled it, and **built the one that is load-bearing**:
the store's row count against `Board.section_rows`' row count, compared row by
row before a byte is written — *"a different function, in a different file"*
(`bin/perry-tasks:907`). Its reason:

> **one integer with two meanings is the single failure a register with no id
> cannot survive.**

My gate was copied from the precedent. Its gate is derived from how *this*
register dies.

## It also refused an instruction, on evidence

My spec said the three writers *"write the store and the section is rendered"*
afterwards. It did not convert them, because **the risks precedent did not
convert `risk-add`/`risk-clear` either — and this board's own `## Intake`
carries the open row saying so.**

Converting intake's three alone would make an ordinary `perry-task intake`
**mint the store as a side effect** on a project where the user has not run the
gated import — the very write my spec's last paragraph reserves for the user —
and would leave two registers with two answers to *"does an ordinary write
update its store"*. That belongs to one row covering both.

## The correctness bug underneath: four implementations, wrong in both directions

```
viewer/parsers.py:1320  _NO_DATE      ⊃ 待定 无 ? ??      ⊅ pending
bin/perry-task:4740     INTAKE_UNSET  ⊃ pending ""        ⊅ 待定 无 ? ??
```

`待定` read as **discharged** for the writer's refusal and **waiting** for the
reader's queue-depth count. `pending` read the other way. Same cell, two
readings, opposite signs.

**TASK-042's round-3 V4 review found this and named it**: *"`INTAKE_UNSET` has
no Chinese member at all"*, at `TASK-042-round3-v4-review.md:234`, carried into
round 4 as item 9 — **and it was left unchanged.** A finding with no row does
not get fixed; that is the third instance of the shape recorded today.

One rule now — `parsers.intake_is_discharged` — over **the union of both sets**,
so nothing any of the four called waiting became discharged.

## The `n` decision, and the published key that settles it

**`n` stays the ordinal**; the store keys on `order`, `n = order + 1`.

Minting `IN-NNN` was rejected because `schema/task-list-contract.md:421` already
publishes the ordinal as a contract key:

> `| n | int | the row's position — **the number `route` and `resolve-intake`
> take** |`

Redefining it is exactly the silent move the row forbids.

**Cost, stated:** `n` is a cursor, not a name — a sweep renumbers every row
below the ones it removes, as it always did. **What changes is that this can no
longer happen unnoticed.**

## Numbers

Byte comparison on this project's own section, count derived and never
hardcoded: **54 records**, all four difference sets empty, `identical: true`.

Mutations on a 4-row fixture:

| | records | drifted |
|---|---|---|
| after import | 4 | 0 |
| hand-edit one `Request` | 4 | **1** |
| after `intake-render --write` | 4 | 0, board sha back to `a8168303` |
| `resolve-intake 2` + `intake-sweep` | 4 | **3** |
| after re-import | 2 | 0 |

**The fourth row is the `n` proof.** Before it, `n=2` was *"the suite's red set
changes with the interpreter"*; after it, `n=2` is *"tasks[].role is typed as
one string"*. **Before this store existed, that shift was reported by nothing at
all.**

Suite **89 modules · 2664 tests · one red** (`test_diagnose`). `perry-lint`
identical before and after, plus the new honest line `· no intake.jsonl — drift
against the intake store is unchecked, not clean` — the same shape risks carried
until this morning.

## One more it had to fix to avoid breaking others

`looks_like_perry_record` needed a third branch: **this is the first store with
no `id`**, and without it every project that imports one gets an `NS-01` against
Perry's own claim.
