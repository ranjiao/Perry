# TASK-197 — the ask store, and a docstring that went stale two days after it was written

**From `coding/task-197` @ `26ce7cb`.** Rung **V3**. The import was **not** run:
`perry/asks.jsonl` still absent, that write is the user's.

## Stored vs derived, per column

| column | verdict | why |
|---|---|---|
| `USER-id` → `id` | **stored** | minted by `mint_user_id`; **this register has ids, unlike intake** |
| `Needed from user` → `needed` | stored | the human's sentence |
| `Blocks` → `blocks` | **stored — tried as derived and failed** | see below |
| **`Idle`** | **DERIVED — not stored** | **the row** |
| `Status` → `status` | stored | free prose, never an enum |
| `Asked` → `asked` | stored | a date — **the input the age is computed from** |
| `answered` | stored, no column | this register's `discharged` |
| `order` | stored | authored row order |

Field names are the ones `schema/task-list-contract.md § asks` already
publishes, **so the store and the payload are not two vocabularies for one row.**

## The `Idle` argument, and how it was proved

`Idle` is `today − Asked` and nothing else. `bin/perry-state § idle_days`
already derives it; `perry-task ask` has stamped `Asked` and left `Idle` alone
since TASK-039 — **whose own docstring records what the other choice cost: both
rows on Perry's board carried `Idle: —`, the one field the queue exists for,
unfilled.**

The proof runs in both directions on one fixture:

```
edit Idle  3d → 47d   →  0 drifted     ← if it were stored, this reddens
edit Asked            →  1 drifted     ← the input is what is stored
asks-render --write   →  restores every stored cell and LEAVES the edited Idle
```

**The last line is the one that matters**: the renderer does not repair `Idle`,
because it never held it. `cells_verbatim: {"Idle": 7}` is the receipt — the
column is *counted*, not a hole in the proof.

## `Blocks` was tried as derived and failed on measurement

A task's `blocks` is derived (the inverse of `depends_on`), so it applied the
same reading here. **Only 2 of the 7 rows on Perry's board have an inverse edge**
(`TASK-114←USER-015`, `TASK-040←USER-016`); the other five name `TASK-005`,
`TASK-038`, `TASK-079` and two `—` that no task declares. **Deriving it would
blank five of seven cells on the first render.**

## Six vs five: the docstring is stale, and the way it went stale is the finding

I asked which of the two counts was wrong and told it to trust neither.

`_parse_user_input`'s docstring calls *"five columns with `Idle`"* **Perry's own
board**. It was written **2026-08-17** by TASK-039. **The same TASK-039 shipped
the `ask` writer**, whose `ensure_section_columns` appended `Asked` the first
time it ran here — **2026-08-19, `9b80ae8`**.

**The comment went stale two days after it was written, by the writer its own
task added.** And Perry's board is a **fourth shape** the docstring's list of
three does not name. Docstring corrected to name all four.

## The byte gate: load-bearing here, and that is a measured difference from intake

Eleven inputs measured: **ten byte-identical either way, and the duplicate
`USER-` id is not** — two lines collapse into one record and the second comes
back wearing the first's question, blocker, status and date. **So the risks
argument applies here and the intake finding does not.**

It kept the gate as the real gate, asserted the eight tautological inputs *as*
tautological so its green cannot be read as a general correctness check, and
**deliberately did not copy intake's row-count gate** — nothing addresses an ask
by position, so a row-count gate would be *this* register's tautology.

Two rows, two opposite answers, each measured rather than inherited.

## Numbers

`7 records`, `identical: true`, all four difference sets empty,
`cells_verbatim: {"Idle": 7}`. Count derived, never hardcoded.

Mutations on a 4-row fixture — the third and sixth rows are the ones that carry
an argument:

| | records | drifted |
|---|---|---|
| after import | 4 | 0 |
| hand-edit `Needed from user` | 4 | **1** |
| **hand-edit `Idle` 3d → 47d** | 4 | **0** ← the `Idle` proof |
| hand-edit `Asked` | 4 | **1** |
| after `asks-render --write` | 4 | 0, wrong `Idle` left standing |
| **`perry-task answer` (writer unconverted)** | 4 | **1** ← the honest current state |
| after re-import | 4 | 0, `answered` flips `True` |
| board reverted to `pending`, re-import | 4 | 0, **`answered` stays `True`** |

The last row is discharge being one-way, the same rule intake carries.

## Found, not fixed, and the reason is good

`bin/perry-diagnose:298` asks *"is this ask answered?"* with

```python
ANSWERED = re.compile(r"\b(answered|resolved|closed|done|decided|已回答|已解决|已决定)\b", re.I)
```

— a word search over free prose. So **`pending — will be resolved by TASK-9`
matches `resolved` and reads as answered**, while the store reads it as open.
Four of eight real `Status` spellings disagree, **in both directions**. That is
`intake_is_discharged`'s defect one register over.

**Not fixed, and the reason is why I agree**: it moves `LOAD-03` counts, and
`test_diagnose` is the suite's one red module — **a semantic change to a checker
under a red test is unreviewable.** It moved the rule into
`parsers.ask_is_answered` with byte-identical behaviour, so the store is the
fourth *caller* rather than a fourth *copy*.

## Verification

`perry-lint` before and after identical, plus the honest new line `· no
asks.jsonl — drift against the ask store is unchecked, not clean`.
Suite **90 modules · 2723 tests · one red** (`test_diagnose`, same two failures
before and after, verified by stashing).
