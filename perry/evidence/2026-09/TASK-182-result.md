# TASK-182 — result

> Branch: `coding/task-182-render-gate`
> Baseline: `main` at `5e88be8`
> Spec: `perry/evidence/2026-09/TASK-182-spec.md`
> Design: `DESIGN-009 § 6` step 2, `§ 7` risk 2

## 0. The worktree was not cut at the baseline, and the brief said to check

The dispatch brief named `main` at `5e88be8` as the baseline. The worktree the
tool handed over was checked out at **`d49964e`**, an ancestor of `main` and
**32 commits behind it**. That commit predates `TASK-181`, so
`perry/okr.jsonl` in it held **41** records and no `objective` kind at all —
the exact state this row's before-measurement produces by deletion. Working
there would have "reproduced" the vacuity by accident and measured nothing.

```
git rev-parse HEAD                      d49964e   (worktree as handed over)
git merge-base --is-ancestor HEAD main  YES       (behind, not diverged)
git log --oneline HEAD..main | wc -l    32
git diff --stat HEAD main -- perry/okr.jsonl viewer/parsers.py
    perry/okr.jsonl   | 10 ++++++++
    viewer/parsers.py | 69 ++++++++++++++++++++++++++++-----------
```

The branch was therefore cut from `5e88be8` itself, and every number below is
measured there. Nothing on `main` was touched.

## 1. Before-state — both claims reproduced, and one of them understated

### 1a. The match already held (spec § "the row is not what its title implies")

```
python3 bin/perry-okr render --root . | md5   5f400212ba724adb6246b91ab60857e4
md5 -q perry/OKR.md                           5f400212ba724adb6246b91ab60857e4
python3 bin/perry-okr diff --root .           identical: true, exit 0
                                              51 records: objective 10, kr 38, version 3
                                              lines_verbatim: []  cells_verbatim: {}
```

Confirmed exactly.

### 1b. The gate could not fail

`git archive` copy of `5e88be8`, all 10 `objective` records deleted from
`perry/okr.jsonl`, **unfixed code**:

```
records left: 41  (kr 38, version 3)
identical:       true     ← UNCHANGED
lines_verbatim:  10       ← the only thing that moved
exit:            0
```

Confirmed exactly, including the exit code.

### 1c. **The spec's own detection signal never moved — a finding**

`DESIGN-009 § 7` risk 2 names the bar as "**`cells_verbatim` must be `{}`**",
and the spec quotes it. But in the measurement above `cells_verbatim` stays
`{}` through the deletion of all ten records. Deleting a whole record moves
`lines_verbatim`; it cannot move `cells_verbatim`, because a cell finding
requires a line that still *matched* a record.

So a fix written only against the spec's numbers would gate `lines_verbatim`
and still not implement the design's sentence. `cells_verbatim` is separately
reachable, and on `5e88be8` it was separately vacuous. Blanking one non-key
field (`metric`) of one `kr` record — the row still matches, its
`Metric / Target` cell is copied through:

```
identical:       true
cells_verbatim:  {"Metric / Target": 1}      ← risk 2's own signal, non-empty
exit:            0                            ← UNFIXED CODE
```

Both registers are gated by this row, and `test_a_cell_the_store_forgot_fails
_the_gate` pins the second one.

### 1d. Why the existing assertions did not catch any of this

`tests/test_md_store.py § RoundTrip.assert_round_trips` already asserts
`cells_verbatim == {}` and `lines_verbatim == []`, and
`TestThisRepositoryIsReproducedByteForByte.test_okr` already ran it against
`perry/OKR.md`. It cannot fail: it builds its records with
`M.derive(doc, text)` — **out of the very file it then compares them
against** — and never opens `perry/okr.jsonl`. Emptying the store leaves it
green. It asserts the scanner and the renderer are inverses, which nobody
doubted. Every case added by this row reads the store off disk.

## 2. The design decision, and why

**`identical` keeps meaning byte-identity. A new key carries the real
property. `diff` gains exit code 3.**

| | |
|---|---|
| `identical` | unchanged — `rendered == text`, the bytes |
| `every_line_and_cell_came_from_the_store` | new — no line or cell was copied through |
| exit 0 | bytes match **and** the store produced them |
| exit 1 | unchanged — the bytes differ |
| exit 2 | unchanged — nothing usable to compare |
| **exit 3** | new — the bytes match and the store did **not** produce them |

**Why not redefine `identical`.** It was the tempting option: every existing
reader gets the stronger property for free. It is wrong here because
`perry_md_store § main` prints that same boolean four lines further down under
the name **`byte_identical`**, in `verify`'s payload. Redefining `identical`
makes that label a lie inside the same function. Byte-identity is also a true
and separately useful fact, and collapsing two properties into one boolean is
what made this gate unreadable in the first place.

**Why a new exit code and not `1`.** `1` has meant "the file and the store's
projection differ in bytes" since `TASK-092`; `2` already means "the input is
unusable". "The bytes match and the store is not what produced them" is a third
finding, and a caller that cannot tell it from a drifted file cannot act on
either. Exit 3 is free. Every caller testing `!= 0` gains the gate; every
caller testing `== 1` keeps the meaning it was written against.

**What the predicate reads, and what it deliberately does not.** Three
registers, named once in `FELL_BACK_TO_COPYING` so the predicate and the
failure message cannot drift: `lines_verbatim`, `cells_verbatim`,
`cells_wearing_decoration` — every fallback, all invisible to `cmp`.
`records_not_in_the_file` is **excluded**: it reports the store holding a
record the file renders no line for, which is the store having *more* than the
file, not the file's bytes coming from somewhere else. Folding it in would make
this predicate mean "the projection is complete in both directions" — which is
`verify`'s sentence — and leave the two commands differing only in how they
print. Measured: `verify` exits 1 and `perry-lint` counts 10 drifted rows on
that case already, so it is covered and not covered twice.

## 3. Payload callers checked

`perry-okr diff`'s report is `plan()`'s dict plus `identical`. Every consumer:

| Consumer | Reads | Affected |
|---|---|---|
| `bin/perry-lint § check_md_store_drift` | calls `plan()` in-process; `cells_the_store_and_the_file_disagree_on`, `lines_verbatim`, `records_not_in_the_file`, `cells_wearing_decoration`, `records_out_of_stored_order` | **No.** Never reads `identical`, never shells out to `diff`. Already counts `lines_verbatim` as drift — **the census is not vacuous**; measured, it reports 10 drifted rows on the deleted-records copy. |
| `bin/perry-state § tracks_the_register_contradicts` | calls `plan()` in-process on `CONFIG` only; `cells_the_store_and_the_file_disagree_on` + `lines_verbatim` filtered to `kind == "track"` | **No.** Never reads `identical` or the exit code. |
| `perry_md_store § main` (`verify`) | prints `identical` as `byte_identical`; exits on `lines_verbatim`, `records_not_in_the_file`, drift, decoration | **No** — deliberately left alone. See finding in § 6. |
| `perry_md_store § main` (scaffold round-trip) | `records_not_in_the_file` | No. |
| `tests/test_md_store.py`, `tests/test_okr_store_is_the_source.py` | exit codes and report keys | Yes — pass; no existing expectation changed. |
| `bin/perry-tasks`, `tests/test_board_render.py` | their **own** `identical`, a separate implementation for `BOARD.md` | **No.** Different code path; out of the bound. |

The new key is set in `main()` beside `identical`, **not** inside `plan()`, so
`plan()`'s report keeps exactly the 7 keys the spec's `## Bound` enumerates and
the two in-process consumers see an unchanged shape.

## 4. `perry-config diff` — a deviation from the bound, stated

The bound's remainder says `perry-config diff` is not changed here.
`perry-config` and `perry-okr` are **the same `main()`**, reached with a
different `Doc`; the fix cannot be applied to one without the other unless
`diff` is special-cased per document. It was not special-cased: that would give
one command two meanings and two exit contracts, which is the defect ADR-004
and `reference/config.md § one fact, one place` exist to stop, and it is the
kind of exception that rots.

Measured instead — `.perry/config.md` is clean today, so the shared fix changes
no observable behaviour for it:

```
python3 bin/perry-config diff --root .   exit 0, before and after
    lines_verbatim [] · cells_verbatim {} · cells_wearing_decoration {}
    identical true · every_line_and_cell_came_from_the_store true
```

No config work was done and no config test was added. If the config store is
ever emptied the same way, it now fails the same way, for free.

## 5. Files changed

| File | What |
|---|---|
| `bin/perry_md_store.py` | `FELL_BACK_TO_COPYING`, `every_line_and_cell_came_from_the_store()`, the new key and exit 3 in `main()`, `USAGE`, `__all__` |
| `bin/perry-okr` | docstring: exit 3 |
| `bin/perry-config` | docstring: exit 3 |
| `tests/test_md_store.py` | `Project.copy_the_real_stores` / `okr_records` / `write_okr_records`; `TestTheByteGateCanFail` (5 cases) |
| `perry/evidence/2026-09/TASK-182-result.md` | this file |

`perry/OKR.md` is **not** in the list. Its md5 is
`5f400212ba724adb6246b91ab60857e4` before and after.

## 6. Findings to carry back

1. **`DESIGN-009 § 7` risk 2's stated detection signal does not detect the
   failure the spec measured.** `cells_verbatim` is unmoved by deleting
   records; `lines_verbatim` is what moves. Both are gated now, but the design
   row's wording is incomplete and § 7 should say so.
2. **`perry-okr verify` carries the same vacuity and is not fixed here.**
   Measured on the `cells_verbatim` case: `verify` exits **0** while
   `cells_verbatim` is `{"Metric / Target": 1}` — its exit condition checks
   `lines_verbatim`, `records_not_in_the_file`, drift and decoration, and omits
   `cells_verbatim`. It is a one-line fix and it is **out of this row's
   bound**, which scopes deliverable 1 to `diff`. Per `review.md § 1` this is a
   new row.
3. The worktree was 32 commits stale (§ 0).

## 7. After-state

Same `git archive` copy, same deletion of all 10 `objective` records, **fixed
code**:

```
identical:                              true    ← still true, and still correct
every_line_and_cell_came_from_the_store: false
lines_verbatim:                         10
exit:                                   3

stderr: perry-okr: the bytes match and the store did not produce them — 10
        line(s)/cell(s) of OKR.md were copied through because no record could
        rebuild them (lines_verbatim). `identical: true` here means the FILE
        reproduced itself.
```

And on risk 2's own signal (one KR's `metric` blanked in the store):

```
identical: true · cells_verbatim {"Metric / Target": 1} · exit 3
    (unfixed: exit 0)
```

## 8. The control

Store intact, nothing touched:

```
python3 bin/perry-okr diff --root .   exit 0
    identical                                true
    every_line_and_cell_came_from_the_store  true
    lines_verbatim                           []
    cells_verbatim                           {}
    cells_wearing_decoration                 {}
    kinds  objective 10 · kr 38 · version 3
```

`test_the_store_intact_is_a_pass` pins it, and mutation **M2** (predicate
always `False`) reddens exactly that case — so a fix that refuses everything
does not pass this row.

## 9. Mutations — 9 planted, 9 red, 0 green

Anchored by line number **with an assert on the old text** (a non-matching
anchor aborts rather than reporting a meaningless OK), `__pycache__` cleared
before every run, mtime pushed past the whole-second boundary, restored from
bytes snapshotted **before** the edit. `bin/perry_md_store.py` md5
`4468159da5a7f7eae70652e76460c9f4` before and after the whole battery.

| # | Mutation | Verdict | Named test that reddened |
|---|---|---|---|
| M1 | `every_line_and_cell_came_from_the_store` → `return True` (the original vacuity, restored) | RED | all three failing cases |
| M2 | → `return False` (**the control**) | RED | `test_the_store_intact_is_a_pass` |
| M3 | `lines_verbatim` dropped from `FELL_BACK_TO_COPYING` | RED | `test_removing_the_objective_records_fails_the_gate` |
| M4 | `cells_verbatim` dropped — risk 2's own signal | RED | `test_a_cell_the_store_forgot_fails_the_gate` |
| M5 | `cells_wearing_decoration` dropped | RED | `test_a_cell_wearing_unstored_words_fails_the_gate` |
| M6 | `return 3` → `return 0` | RED | all three |
| M7 | the payload key hardcoded `True` | RED | all three |
| M8 | the exit branch stops consulting the predicate | RED | all three |
| **M9** | **data, not source**: the 10 `objective` records deleted from this repository's own `perry/okr.jsonl` | **RED** | `test_no_line_or_cell_of_the_live_okr_is_copied_through` |

**M9 is the one that matters, and it was run against both tests at once:**

```
RED    NEW (this row)     test_no_line_or_cell_of_the_live_okr_is_copied_through
GREEN  OLD (pre-existing) TestThisRepositoryIsReproducedByteForByte.test_okr
```

The old test asserts `lines_verbatim == []` **and** `cells_verbatim == {}` and
stayed green with the store's ten Objectives gone, because it derives its
records from the file. That is the § 1d claim, measured. `RoundTrip`'s
docstring now says so, so the next reader does not take those two assertions
for the gate.

`perry/okr.jsonl` md5 `b6bc3b99ca79be09f84b443e4f094c40` before and after M9.

## 10. Runs

```
python3 tests/parallel -j 4
    110 modules · 3102 tests · 165.4s · 4 workers · exit 0 · all green

python3 bin/perry-lint --root .
    exit 0 · 0 error(s), 16 warning(s)
    OKR store: 51 record(s), 0 row(s) drifted
  baseline (5e88be8, git archive copy):
    exit 0 · 0 error(s), 16 warning(s)      ← identical

md5 -q perry/OKR.md
    5f400212ba724adb6246b91ab60857e4        before
    5f400212ba724adb6246b91ab60857e4        after
```

`perry/OKR.md` was never written. This row changed the checker.
