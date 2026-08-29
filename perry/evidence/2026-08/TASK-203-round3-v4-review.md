# TASK-203 — V4 review round 3: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-203-spec.md`.
> Under review: `d075698`. All destructive work on scratch copies; the worktree
> stayed clean.
>
> *Interruption note, the reviewer's own:* the PMO killed their first
> `bash tests/run` on the base copy mid-run and said so. **It was re-run from
> scratch and every number below comes from the complete re-run.**

## What round 3 fixed, verified

**All four claimed mutations reproduce to the exact count** (2 / 1 / 2 / 7).

**Finding 3 is genuinely closed** — the new merge test is red under the *honest*
`current = []`, and red for the named reason. **Both self-reported
"green for the wrong reason" corrections are real.**

**Finding 2's behaviour is fixed for all four shapes and all three registers** —
a 60-cell matrix (3 registers × 5 shape variants × store present/absent ×
own/unrelated write). *"No cell truncates a present store to zero through a
shape the gate can see."*

`readable_as_register` is correct for all three and a `KeyError` is impossible.
`REGISTER_EVENTS` complete both ways over all 21 mutating subcommands. Crash
recovery holds at all three rename boundaries. Five refusal paths hashed
whole-tree: nothing written. Localized `zh` board correct for all three
registers. Baseline verified on both runners, failure sets byte-identical.

## Finding 1 — BLOCKING. The gate is read at a moment the command controls

`cmd_add`'s queue-mode branch calls `ensure_section("Intake", …)` at
`bin/perry-task:2973`. `commit()` asks the gate at `:2549` — **after** that
mutation. So the gate is asked about a board state the command it guards has
already destroyed: it sees a freshly created, perfectly readable, **empty**
intake table, answers yes, derives `[]`, and writes `store_text([])` into the
canonical transaction.

```
intake.jsonl before:  291 bytes, 3 records
  ← `## Intake` removed from BOARD.md by hand
  ← perry-task add --title "a queue task" --track ops        (rc 0)
intake.jsonl after :  0 bytes, 0 records
perry-lint: intake store: 0 record(s), 0 row(s) drifted
```

On `45a355d` the same file is **byte-identical** after the same command.

> *"This is round 1's blocking finding restated without a word altered … Same
> command name, same board state, same zero bytes. Round 2 closed it for the
> project-mode track; the queue-mode track — the mode `## Intake` exists for —
> was never asked."*

**The shipped regression test is one word from red.** Give
`test_a_present_store_is_never_emptied_by_a_write_that_lost_its_section` a
`--track ops` fixture and nothing else, and it fails `0 != 1`.

Enumerated, section deleted by hand then one command — every loss silent, rc 0,
permanent, canonical, and reported by `perry-lint` as `0 row(s) drifted`:

| register | command | before → after |
|---|---|---|
| intake | `add --track ops` | 3 → **0** |
| intake | `intake` | 3 → **1** |
| asks | `ask` | 3 → **1** |
| risks | `risk-add` | 3 → **1** |

All four are byte-identical on base.

> *"The outcome for a given board now depends on which command you happen to run
> next. Round 1 keyed the exemption on the command name and was told the question
> was wrong; round 2 keyed it on a non-unique tuple; round 3 keyed it on the
> shape — and the shape is read at a moment the command controls."*

## Finding 2 — non-blocking. My third shape test is vacuous, same blind spot moved

`test_a_second_table_under_the_heading` appends the legend table to the **end of
the file** — but `ensure_section` anchors `## Intake` *before* `## P0`, so the
last section is `## Top risks` and **the legend lands there.** `## Intake` stays
a clean single-table section, the gate is never asked about `foreign`, and the
assertion passes trivially. Green with the gate reverted and green with
`readable_as_register` weakened.

**The `foreign` shape has no test at all, for any register** — two of the four
shapes Finding 2 named, and the one where round 2 showed the truncating command
was the register's own.

> *"The author caught two green-for-the-wrong-reason tests by mutation and
> shipped a third of the same class in the same commit, uncaught, because the
> mutation that would have exposed it was read as '2 failures, as expected'
> rather than 'why only 2 of 3?'."*

## Finding 3 — non-blocking. The uniqueness test cannot tell uniqueness from adjacency

The duplicate pair sits at orders 2 and 3 — **adjacent**. A weaker guard tripping
only on *consecutive* equal identities is **green across all 2815 tests**. So is
round 2's `(request, arrived)` → `(request,)`: `arrived` is a decoration on the
tuple that nothing asserts.

## (a) The uniqueness refusal is over-broad, and correctly so

Measured three ways: with `Outcome` cells intact, ten ordinary writes leave
`intake.jsonl` **byte-identical**. The only thing the join carries is
`discharged`, which `intake_is_discharged` re-derives from any non-blank
`Outcome`. The realistic loss is one boolean on rows a human has hand-blanked,
and the error direction is safe — a discharged row is re-reported as waiting,
never the reverse. *"Materially better than round 2, which fabricated a
discharge."*

## (b) `prose` does not lock `intake` out

`ensure_section` returns early when the heading exists, so it does **not** turn a
prose section into a table — `intake_section_shape`'s docstring saying it does is
wrong. `append_section_row` refuses first. *"There is no path where `intake` on a
prose section silently skips the store forever."*

## (c) Two asymmetries survive, both pre-existing

On a `foreign` section `risk-add` refuses with an explanation while `intake` and
`ask` return rc 0, append a row and skip the store — and on a renamed key column
the request text is dropped from the board row too. And on the id-keyed
registers a duplicate id **on the board** now silently deletes a stored record,
while a duplicate **in the store** leaks one record's `cleared` onto the other.
*"Both live in `perry_store` and predate the row, but they were unreachable until
this change made ordinary commands write those files."*

## (e) The flake did not reproduce — ~70 executions

6 isolated, 8-way concurrent × 7 tests, 4 full suites, both trees, both runners —
**never red.** *"I could not reproduce it and I am not accepting the author's
account of it either; I am recording that it did not appear."* A plausible
mechanism is named (a `recover_stale_lock` TOCTOU) and marked a reading, not a
measurement.

## Smaller

- **A corrupt line in a register store is now an uncaught traceback.**
  `load_register_records` lets `JSONDecodeError` escape; nothing is written, but
  every other failure in the file is a `Refused` with a way forward. Before this
  row, a corrupt `risks.jsonl` did not affect `risk-add` at all.
- **`readable_as_register`'s `section` parameter is dead** — declared, passed,
  never read. *"In the same commit that answers a review finding about
  `SECTION_OF` being assigned and never read."*

## Verdict

```
=== VERDICT ===
task: TASK-203
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-203-spec.md
proof: bin/perry-task:2297 (the gate) is asked by commit() at :2549, which runs
       AFTER cmd_add has already called `ensure_section("Intake", …)` at :2973
       on a queue-mode track. The gate sees a freshly created, readable, EMPTY
       intake table, derives [], and writes store_text([]) inside the canonical
       transaction. Measured on a 3-record 291-byte intake.jsonl, `## Intake`
       removed by hand, then `perry-task add --title "a queue task" --track ops`
       (rc 0): 0 bytes, 0 records, perry-lint `0 row(s) drifted`. On 45a355d the
       same file is byte-identical. Round 1's Finding 2 unchanged. The shipped
       regression test goes red when its fixture is given `--track ops` and
       nothing else. Same door three more times, all rc 0 and all preserved on
       base: intake 3→1, ask 3→1, risk-add 3→1. Second, non-blocking:
       test_a_second_table_under_the_heading appends its legend to the end of
       the file, which is under `## Top risks` — ensure_section anchors
       `## Intake` before `## P0` — so the section is never `foreign` and the
       test is green with the gate reverted. The `foreign` shape has no test on
       any register.
=== END VERDICT ===
```
