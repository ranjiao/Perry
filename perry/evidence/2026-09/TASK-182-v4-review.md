# TASK-182 — v4 fresh-context review

> Reviewer: fresh-context V4, repository-local stdlib only, no MCP
> Branch: `review/task-182-v4-fresh`
> Base (the branch's own): `13650c4d476d1292ed657ed83a4ee332215c3c43`
> Reviewed: `DESIGN-009 § 6` step 2 / `§ 7` risk 2, as landed on `main`
> Spec: `perry/evidence/2026-09/TASK-182-spec.md`
> Round's result document: `perry/evidence/2026-09/TASK-182-result.md`

**The work is merged.** `HEAD` was handed over at `d49964e`, an ancestor of
`main`; `coding/task-182-render-gate` (`cdf68d4`) is an ancestor of `main`
(`git merge-base --is-ancestor coding/task-182-render-gate main` → yes), and
the row landed at `2822241`. `main` is checked out in the shared worktree and
cannot be checked out again here, so this branch was cut **from `main`** and
every measurement below is against `13650c4` unless a commit is named.

**Restore instrument, stated once.** Every mutation restore in § 4 is verified
by a **single path**: `git diff --stat 13650c4d476d1292ed657ed83a4ee332215c3c43
-- bin/perry_md_store.py` must print nothing, against **this branch's own
base**, never against `main`. `git status --porcelain` is printed beside it.
Both are empty after all nine restores.

**The landed code is still the code the round shipped.** `bin/perry_md_store.py`
has moved once since `2822241` and not in this row's surface:

```
git diff --stat 2822241 13650c4 -- bin/perry_md_store.py
    bin/perry_md_store.py | 5 +++--    (render_separator in scaffold_config)
```

---

## Criterion 1 — the round trip on the live file — **MET**

```
$ python3 bin/perry-okr diff --root .                          exit 0
    lines_from_store 51 · lines_verbatim [] · records_not_in_the_file []
    cells_verbatim {} · cells_wearing_decoration {}
    cells_the_store_and_the_file_disagree_on [] · records_out_of_stored_order []
    kinds {objective 10, kr 38, version 3}
    identical true
    every_line_and_cell_came_from_the_store true

$ python3 bin/perry-okr render --root . | md5   af0cf40f8d0a11ecc685cfdd0da47b78
$ md5 -q perry/OKR.md                          af0cf40f8d0a11ecc685cfdd0da47b78

$ python3 bin/perry-okr verify --root .                        exit 0
    records 51 · lines_from_store 51 · lines_the_store_does_not_hold []
    records_not_in_the_file [] · drift_count 0
    cells_wearing_decoration {} · byte_identical true
```

`render --write` was run on a `git archive HEAD` copy (never on `perry/OKR.md`
in this tree): md5 `af0cf40f…` before, `af0cf40f…` after, exit 0. Byte-identical.

## The live fact — the 2026-09-03 hand edit still round-trips — **MET**

Both hand edits are on `main`: `d47f6ca1` added the tenth Operating Principle,
`30758986` repointed the overflow instruction from `evidence/<YYYY-MM>/
okr-vN-retro.md` to `phase/snapshots/okr-vN.md`.

```
md5 perry/OKR.md @5e88be8 / @cdf68d4 / @2822241   5f400212ba724adb6246b91ab60857e4
                 @d47f6ca1                       82d8f94a0138e13e5c10c4407230f127
                 @30758986 / @13650c4 / live     af0cf40f8d0a11ecc685cfdd0da47b78
md5 perry/okr.jsonl @5e88be8 … @13650c4 … live   b6bc3b99ca79be09f84b443e4f094c40
```

The file moved twice and **the store did not move at all** — which is the
point: both edits are LAYOUT. Measured on the file as it stands today
(criterion 1 above): `diff` exit 0, `identical true`,
`every_line_and_cell_came_from_the_store true`, `verify byte_identical true`
with `drift_count 0`, `perry-lint --root .` → `OKR store: 51 record(s), 0
row(s) drifted`. **Yes — it still round-trips**, and it is now a stronger
statement than it was on 2026-09-03, because on `5e88be8` the same green was
reachable with the store emptied.

## Criterion 2 — the property on documents other than Perry's own OKR — **MET**

Fixtures built in a temp tree (`perry/OKR.md` + Perry's own `.perry/config.md`,
store minted with `perry-okr write --from-file`, then `diff` / `render` /
`verify`). "Round-trips" below means all three: `diff` exit 0 with
`every_line_and_cell_came_from_the_store true`, `render` output byte-equal to
the file, `verify` exit 0.

| # | Document | Round-trips? | On failure |
|---|---|---|---|
| 0 | control fixture (mission, principles, anti-goals, one Objective + KR table, versioning log) | **yes** | LOUD |
| A | KR table with an escaped `\|` in two cells | **yes** — stored unescaped (`text: "Text with an escaped \| pipe"`, `metric: "3 \| 4"`), re-escaped on render | **LOUD** — exit 3 |
| B | CJK Objective heading `### 目标 1: 维持整个资金池的长期稳定收益` + CJK cells (`中文关键结果，带标点。`, `3 个 / 3 个`, `下周期`) | **yes** — `title` correctly split on the schema ordinal `^(Objective\|目标) \d+`, colon separator stripped | **LOUD** — exit 3 |
| C | trailing whitespace on the Objective heading and on a KR row, **and no final newline** | **yes** | **LOUD** — exit 3 |
| D | `## Appendix — a section with no template`, prose + a two-column table under it | **yes — the section is reproduced byte for byte, not dropped** | **LOUD** — exit 3 |

The failure column is measured, not asserted: for each of A–D the store was
then perturbed two ways and `diff` re-run.

```
A escaped pipe    drop every objective record  exit=3 lv=1  cv={}
                  blank one kr metric          exit=3 lv=0  cv={"Metric / Target": 1}
B CJK             drop every objective record  exit=3 lv=1  cv={}
                  blank one kr metric          exit=3 lv=0  cv={"Metric / Target": 1}
C trailing ws     drop every objective record  exit=3 lv=1  cv={}
                  blank one kr metric          exit=3 lv=0  cv={"Metric / Target": 1}
D untemplated     drop every objective record  exit=3 lv=1  cv={}
                  blank one kr metric          exit=3 lv=0  cv={"Metric / Target": 1}
```

`identical` stays `true` in all eight; the exit code and
`every_line_and_cell_came_from_the_store` are what move. **Loud in every case.**

**Case D is the one the review brief names, and it passes for the right
reason.** `bin/perry-okr`'s own help says the mission, the operating principles
and every rationale paragraph are LAYOUT — "never parsed, never re-rendered,
and reproduced byte for byte". The Appendix heading, its prose and its
`Colour / Meaning` table produce no site, no record, and no report entry, and
`render` returns them unchanged. Nothing is dropped.

### Eleven further documents, and two the gate catches that the round never named

The four above were not enough to find a break, so eleven more were built.
Two of them make the new gate fire where `5e88be8` was silent — neither
appears in the spec or the result document:

| Document | `write` | `diff` | Report |
|---|---|---|---|
| **undeclared 6th column `Owner` on the KR table** | 0 | **3** | `cells_verbatim {"Owner": 2}` — the column is not in `KR_COLUMNS`/`KR_EXTRA`, so the cell is copied, not rebuilt |
| **a pipe inside inline code — `` `a\|b` ``** | 0 | **3** | `cells_verbatim {"#5": 1}` — the row splits into six cells and the sixth is unstored |
| double spaces inside a cell | 0 | 0 | round-trips |
| CRLF line endings throughout | 0 | 0 | round-trips |
| a row four cells wide under a five-column header | 0 | 0 | round-trips |
| `*italic*` / `**bold**` decorating whole cells | 0 | 0 | round-trips |
| an empty cell | 0 | 0 | round-trips |
| no trailing pipe on the row | 0 | 0 | round-trips |
| legacy `- KR2: …` bullet form outside any table | 0 | 0 | round-trips |
| NBSP / full-width space inside a cell | 0 | 0 | round-trips |
| the same `Id` under the same Objective in two version blocks | 0 | 0 | round-trips (3 kr, 2 objective) |

On `5e88be8` both of the first two exited **0**. That is real value the row
delivers beyond the case its own spec measured.

## Criterion 3 — a control that fails loudly rather than round-tripping lossily — **MET**

Two, both loud, both naming the thing:

1. **Two KR rows carrying the same `Id` under one Objective.**
   `perry-okr write --from-file` **exit 1**, refuses, writes nothing:
   `"OKR.md produces a store this tool could not read back; nothing was
   written"`, `store_findings[0].key = "kr/v1: 2026-01-01/Objective 1 — The
   first objective/KR-O1.1"`, line 3. No lossy store is minted.

2. **`OKR.md` absent.** `perry-okr render` **exit 2**:
   `"no OKR.md at …, and this document has no scaffold — there is no declared
   shape to rebuild it into from okr.jsonl alone."`

Item 2 is also a structural fact worth stating plainly: **`perry-okr render`
does not build `OKR.md` from records; it rebuilds, in place, every line of an
existing `OKR.md` that a record claims, and copies the rest.** The row's title
("`render` rebuilds `OKR.md` byte-for-byte from objective records") is true of
the stored lines and not of the file. The spec says as much — "the row is not
what its title implies" — and this review is not marking it against the row.

## Criterion 4 — nine mutations planted by this reviewer — **MET · 5 red, 4 GREEN**

Every mutation is anchored **by line number with an assert on the old text at
that line** (`assert lines[n-1] == expect`, aborting on a miss rather than
no-opping into a false green), `__pycache__` cleared before every run, mtime
pushed past the whole-second boundary, restored from the bytes snapshotted
**before** the edit. Single instrument, this branch's own base:
`git diff --stat 13650c4 -- bin/perry_md_store.py` empty, and
`git status --porcelain` empty, after every one.
`bin/perry_md_store.py` md5 `c4b55b5f7bf568ec71660f4ce621086b` before and
after the whole battery.

Red/green below is `python3 tests/test_md_store.py` (54 tests); **every GREEN
was then escalated to the full `bash tests/run` and survived that too.**

| # | Mutation | Line | Verdict | Caught by |
|---|---|---|---|---|
| R1 | the predicate's quantifier: `return not any(...)` → `return not all(...)` | 985 | RED | all three failing cases |
| R2 | `main()` short-circuits the predicate: `= True if report["identical"] else …` — the exact vacuity, rewritten as an optimisation, with the function and the tuple untouched | 1218 | RED | all three failing cases |
| R3 | `plan()` stops incrementing the decoration counter (`elif False and "decorated" in f:`) — the PRODUCER, not the tuple | 897 | RED | `test_a_cell_wearing_unstored_words_fails_the_gate`, `test_an_appended_hand_edit_is_counted_rather_than_hidden` |
| R4 | `FELL_BACK_TO_COPYING` **widened** with `records_not_in_the_file` | 946 | RED | `test_the_three_registers_the_predicate_reads_are_the_named_three` |
| R5 | `return 3` → `return 1` (a caller testing `== 1` is now lied to) | 1244 | RED | all three failing cases |
| **R6** | the **count** in `diff`'s exit-3 sentence replaced by a constant `0` | 1238 | **GREEN** | nothing — module and full suite both green |
| **R7** | the **register names** in that sentence replaced by `()` | 1241 | **GREEN** | nothing |
| **R8** | `every_line_and_cell_came_from_the_store` dropped from `__all__` | 1347 | **GREEN** | nothing |
| **R9** | `USAGE` stops documenting exit 3 | 1049 | **GREEN** | nothing |

The gate itself is well pinned: R1, R2, R3 and R5 are four independent ways to
reintroduce the defect and all four go red, R2 being the one a future
maintainer would most plausibly write. **The four greens are all in the
operator-facing half of the deliverable, and one of them exposes a live
defect.**

### The finding R6 uncovers: the shipped failure sentence under-reports

`bin/perry_md_store.py:1238`:

```python
f"them — {sum(len(report[k]) for k in FELL_BACK_TO_COPYING)} "
f"line(s)/cell(s) of {doc.rel_file} were copied through "
```

`lines_verbatim` is a **list** (so `len` is the number of lines — correct), but
`cells_verbatim` and `cells_wearing_decoration` are **dicts of column → count**,
so `len` is the number of distinct *columns*, not of cells. Measured live on
the undeclared-`Owner`-column document above:

```
report:  cells_verbatim {"Owner": 2}          ← two cells were copied
stderr:  … — 1 line(s)/cell(s) of OKR.md were copied through …
```

The exit code and the JSON are right; the sentence a human reads is wrong, and
nothing in 3253 tests notices. It happens not to show in the result document's
own § 7 evidence because that case moves `lines_verbatim` only.

### Two smaller ones from R7 and R9

- `FELL_BACK_TO_COPYING`'s own docstring says it exists "because
  `every_line_and_cell_came_from_the_store` and the sentence `diff` prints when
  it fails **both** have to agree about what a fallback is". Only the predicate
  half is enforced; the sentence half can be emptied silently (R7).
- `USAGE` already contradicts itself, before any mutation. Lines 1048–1052
  introduce exit 3; line 1061, nine lines later, still reads
  `Exit codes: 0 read or written · 1 refused, or drifted · 2 bad invocation.`
  R9 shows nothing would catch the other half going too.

## Criterion 5 — every number in the result document re-derived — **MET, with one exception**

Re-derived on `git archive` copies of `5e88be8` (before) and `13650c4` (after).

| Result doc | Claim | Re-derives? |
|---|---|---|
| § 1a | 51 records — objective 10, kr 38, version 3 | **yes** |
| § 1a | `diff` identical true, exit 0, `lines_verbatim []`, `cells_verbatim {}` | **yes** |
| § 1b | delete 10 objective records on unfixed code: 41 left, identical **true**, `lines_verbatim` **10**, exit **0** | **yes, exactly** |
| § 1c | blank one kr `metric` on unfixed code: identical true, `cells_verbatim {"Metric / Target": 1}`, exit **0** | **yes, exactly** |
| § 3 | `perry-lint` counts **10** drifted rows on the deleted-records copy, and the census is not vacuous | **yes** — `OKR store: 41 record(s), 10 row(s) drifted` |
| § 4 | `perry-config diff` exit 0 before and after, all three registers empty | **yes**, both trees |
| § 6 fnd 2 | `verify` exits **0** while `cells_verbatim` is non-empty — still open | **yes**, on `5e88be8` **and on `13650c4` today** |
| § 7 | fixed code, same deletion: identical true, predicate false, `lines_verbatim` 10, exit **3** | **yes** |
| § 7 | fixed code, blanked metric: `cells_verbatim {"Metric / Target": 1}`, exit **3** | **yes** |
| § 8 | control: exit 0, both halves true, kinds 10/38/3 | **yes** |
| § 5, § 10 | `perry/OKR.md` md5 `5f400212ba724adb6246b91ab60857e4` before and after | **yes at the stated baseline** — identical at `5e88be8`, `cdf68d4` and `2822241`. Today `af0cf40f…`, from the two 2026-09-03 hand edits, which are later than this row |
| § 9 | `bin/perry_md_store.py` md5 `4468159da5a7f7eae70652e76460c9f4` | **yes at `cdf68d4` and `2822241`**; today `c4b55b5f…` after one unrelated line |
| § 9 | `perry/okr.jsonl` md5 `b6bc3b99ca79be09f84b443e4f094c40` | **yes**, everywhere, including today |
| § 0 | `git diff --stat HEAD main -- perry/okr.jsonl viewer/parsers.py` → `10 ++++++++` / `69 +++---` | **yes, exactly** |
| § 10 | `perry-lint` 0 error(s), 16 warning(s), baseline identical | **yes at `5e88be8`** (0/16, both trees). Today 0 errors / 37 warnings — later rows, not this one |
| § 10 | `110 modules · 3102 tests` | superseded, not contradicted — today `114 modules · 3253 tests` |
| **§ 0** | **the worktree was `d49964e` and "32 commits behind" `main`, `git log --oneline HEAD..main \| wc -l` → 32** | **NO** |

**The one that does not re-derive.** The result document names its baseline as
`main` at `5e88be8` and, two lines later, reports `HEAD..main` as 32 commits.
Measured:

```
git log --oneline d49964e..5e88be8 | wc -l                 115
git log --oneline --no-merges d49964e..5e88be8 | wc -l     102
git log --oneline --first-parent d49964e..5e88be8 | wc -l   67
```

No reading of the stated baseline yields 32. It re-derives against exactly one
commit — `ffd48127` ("TASK-293 FAILed its V4 on a false claim…"), where
`d49964e..ffd48127` is **32** — so the command was run truthfully at a moment
when the local `main` ref was at `ffd48127`, and `main` had advanced to
`5e88be8` by the time the baseline line was written. The measurement is honest;
the document is **internally inconsistent** and a reader cannot reproduce it
from the two facts it states. It is a provenance number and it decides nothing
about the row's PASS.

## Criterion 6 — suite and lint — **MET**

```
$ bash tests/run
    0. tree guard  ✓ nothing under <worktree> moved
    ✓ all green                                                   exit 0

$ python3 bin/perry-lint --root .
    0 error(s), 37 warning(s)                                     exit 0
    · OKR store: 51 record(s), 0 row(s) drifted
    · config store: 9 record(s), 0 row(s) drifted
```

`tests/parallel -j 4` (the instrument the result document used) reports
`114 modules · 3253 tests` with **1 module red: `test_one_primitive.py`**.
Re-run alone as the brief requires: `python3 tests/test_one_primitive.py` →
`Ran 6 tests … OK`. It is the known TASK-341 order-dependent red and is not
this row's. `test_contract_key_parity`, `test_one_choke_point` and
`test_host_support` were green in both instruments.

`perry/OKR.md` and `perry/okr.jsonl` were never written in this worktree; their
md5s are unchanged and `git status --porcelain` is empty but for this file.

---

## Findings carried back (none of them a failure of this row's bar)

1. **`diff`'s exit-3 sentence under-reports copied cells** (§ 4, R6).
   `sum(len(report[k]))` counts dict *keys* for the two cell registers.
   `cells_verbatim {"Owner": 2}` prints as "1 line(s)/cell(s)". One line;
   nothing tests the sentence at all (R6, R7 both green through the full suite).
2. **`USAGE` contradicts itself about its own exit codes.** Line 1061 still
   enumerates `0 · 1 · 2` nine lines after the paragraph that introduces 3.
3. **The 2026-09-01 intake dropped on 2026-09-02 as "covered by TASK-182" is
   not covered by TASK-182's gate.** Reproduced on `13650c4`: append two
   records (an `objective` and its `kr`) to `perry/okr.jsonl`, then

   ```
   perry-okr render --write   exit 0
       "rendered … from 53 stored record(s)"   ← and OKR.md is byte-UNCHANGED
   perry-okr diff             exit 0   identical true
                                       every_line_and_cell_came_from_the_store TRUE
                                       records_not_in_the_file [the two new keys]
   perry-okr verify           exit 1   ← the only tool that fails
   perry-lint --root .        exit 0   "53 record(s), 2 row(s) drifted"  (⚠, not an error)
   ```

   The row's result document § 2 **names this exclusion, argues it, and measures
   the coverage**, and the measurement re-derives: `verify` does exit 1 and
   `perry-lint` does count the rows. But `render --write` prints a record count
   the file does not carry, `diff` — the command this row made into the gate —
   exits 0, and `perry-lint` reports it as a warning at exit 0. So the intake's
   substance survives in `verify` alone. This is a **new row**, per
   `review.md § 1`; it is outside this spec's `## Bound` and outside its
   deliverables, all three of which are about the opposite direction.
4. **The result document's § 0 commit count is internally inconsistent** (§ 5).
5. Restated from the round, both re-derived here and both still open:
   `perry-okr verify` omits `cells_verbatim` from its exit condition (exits 0
   with `cells_verbatim {"Metric / Target": 1}`), and `DESIGN-009 § 7` risk 2's
   stated detection signal is not the register that moves on the failure the
   spec measured.

## Verdict

**PASS.**

All three deliverables hold, and hold for the right reason. Deliverable 1:
`diff` gains exit 3 and a second key, `identical` keeps meaning bytes,
and four independent mutations that would restore the vacuity all go red —
including R2, the short-circuit a maintainer would actually write. Deliverable
2: `test_no_line_or_cell_of_the_live_okr_is_copied_through` asserts risk 2's
bar on the live file **reading the store off disk**, which is precisely what
the pre-existing `TestThisRepositoryIsReproducedByteForByte` could not do.
Deliverable 3: `test_removing_the_objective_records_fails_the_gate` is the
control, and `test_the_store_intact_is_a_pass` is the counter-control that a
gate refusing everything would fail.

The property holds on fifteen documents built here that are not Perry's own
`OKR.md`, including CJK headings and cells, escaped pipes, CRLF, trailing
whitespace with no final newline, and a section the renderer has no template
for — which is reproduced byte for byte rather than dropped. Two of those
documents make the new gate fire where `5e88be8` was silent. Two more fail
loudly and name the reason. The 2026-09-03 hand edit still round-trips, and
that green is now worth something it was not worth on 2026-09-03.

Against that: four green mutations, all in the operator-facing surface, one of
which exposes a wrong number in the sentence the new exit code prints. That is
a defect in the deliverable and it is recorded as finding 1 — but it does not
touch the gate, the exit code, the report, or any of the spec's three
deliverables, and a FAIL on it would be a FAIL for a message string while the
mechanism the row exists to build is sound and mutation-proven.

    === RESULT ===
    Branch: review/task-182-v4-fresh
    Verdict: PASS
    Criteria met: 6 of 6
    Criteria NOT met: none
    Documents you constructed: escaped `|` in two KR cells → round-trips (stored unescaped, re-escaped on render) → LOUD, exit 3; CJK Objective heading + CJK cells → round-trips (title split on the schema ordinal, colon separator stripped) → LOUD, exit 3; trailing whitespace on heading and row with no final newline → round-trips → LOUD, exit 3; `## Appendix` section with no template, prose + unknown table → round-trips, reproduced byte for byte and NOT dropped → LOUD, exit 3; plus 11 more — undeclared 6th column `Owner` → round-trips byte-wise but the gate FIRES, exit 3, `cells_verbatim {"Owner": 2}` (exit 0 on 5e88be8) → LOUD; pipe inside inline code `a|b` → gate FIRES, exit 3, `cells_verbatim {"#5": 1}` (exit 0 on 5e88be8) → LOUD; duplicate KR `Id` → does NOT round-trip, `write` refuses at exit 1 naming the key → LOUD; `OKR.md` absent → `render` exit 2, "no scaffold" → LOUD; double spaces, CRLF, short row, `*italic*` cells, empty cell, no trailing pipe, legacy `- KR2:` bullet, NBSP/full-width space, same Id in two version blocks → all round-trip
    Does the hand edit of 2026-09-03 still round-trip: Yes. Both edits (d47f6ca1's tenth Operating Principle, 30758986's phase/snapshots/okr-vN.md repoint) moved perry/OKR.md from 5f400212ba724adb6246b91ab60857e4 to af0cf40f8d0a11ecc685cfdd0da47b78 while perry/okr.jsonl stayed at b6bc3b99ca79be09f84b443e4f094c40 — LAYOUT, exactly as bin/perry-okr's help claims. Today: diff exit 0, identical true, every_line_and_cell_came_from_the_store true, verify byte_identical true drift_count 0, perry-lint "OKR store: 51 record(s), 0 row(s) drifted". Stronger than on 2026-09-03, when the same green was reachable with the store emptied.
    Mutations planted: 9, 5 red, 4 GREEN
      RED   R1 predicate `not any` → `not all` (l.985)
      RED   R2 main() short-circuits the predicate when identical is true (l.1218) — the vacuity as an optimisation
      RED   R3 plan() stops counting decorated cells (l.897) — the producer, not the tuple
      RED   R4 FELL_BACK_TO_COPYING widened with records_not_in_the_file (l.946)
      RED   R5 return 3 → return 1 (l.1244)
      GREEN R6 the count in diff's exit-3 sentence → constant 0 (l.1238) — and the shipped count is ALREADY wrong: len() of a dict counts columns, so cells_verbatim {"Owner": 2} prints "1 line(s)/cell(s)"
      GREEN R7 the register names in that sentence → "()" (l.1241) — FELL_BACK_TO_COPYING's stated no-drift contract is enforced for the predicate half only
      GREEN R8 every_line_and_cell_came_from_the_store dropped from __all__ (l.1347)
      GREEN R9 USAGE stops documenting exit 3 (l.1049) — and USAGE line 1061 already contradicts it
      All four greens were escalated to the full `bash tests/run` and survived it.
    Numbers in the result document that did NOT re-derive: one — § 0's "git log --oneline HEAD..main | wc -l → 32". Against the baseline the same document names (main at 5e88be8) the true values are 115 (all), 102 (--no-merges), 67 (--first-parent). It re-derives against exactly one commit, ffd48127, where d49964e..ffd48127 is 32 — so it was measured truthfully before main advanced, and the document is internally inconsistent rather than false. Decides nothing about the row. Everything else re-derived exactly at its stated baseline, including all four md5s, the 41/10/exit-0 before-state, the {"Metric / Target": 1} cells_verbatim case, the 10 drifted lint rows, verify still exiting 0 on the cells_verbatim case, and the 10/69 diffstat. Three figures are superseded by later commits rather than wrong: OKR.md md5 (hand edits of 2026-09-03), perry_md_store.py md5 (one unrelated line), and 0 errors/16 warnings → 0 errors/37 warnings.
    Tree clean: (git status --porcelain printed nothing but this review file)
    === END RESULT ===
