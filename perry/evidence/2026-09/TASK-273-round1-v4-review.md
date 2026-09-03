# TASK-273 — round 1, V4 review

- **Criteria**: `perry/evidence/2026-09/TASK-273-spec.md` (the only authority),
  including its `## Bound`.
- **Under review**: `main` at `c506ca5`. The row's account is
  `perry/evidence/2026-09/TASK-273-result.md`.
- **Verdict**: PASS, with one green mutation recorded below.

## The checkout, and how it was verified

This worktree was cut at **`d49964e`** ("chore: consolidate test suite and
project state"), on branch `worktree-agent-a19acb3e1b6ee05ac`, **211 commits
behind `main`** (`git rev-list --left-right --count main...HEAD` → `211 0`), with
`main` at `c506ca5` when the round opened. The subject of this review does not
exist in the checked-out tree, so **nothing was read from the working copy**.
Every path was resolved through `git show <ref>:<path>`, and all of these
resolve:

```
perry/evidence/2026-09/TASK-273-spec.md      perry/evidence/2026-09/TASK-273-result.md
bin/perry-task   bin/perry-tasks   bin/perry_store.py   bin/perry-lint   bin/perry-restore-check
```

**Nothing was written to the repository under review, and no Perry write tool
was run against it.** Four throwaway trees were built with `git archive` in a
uniquely-named scratch directory and every duplicate was planted there:

| tree | what it is |
|---|---|
| `t273base` | `9c9670e` — the row's own named baseline, before any code change |
| `t273rev` | `c506ca5` — `main`, the thing under review |
| `c1a` / `c1b` | two fresh `c506ca5` extractions, `c1b` with TASK-273's four `bin/` commits reverse-patched (`patch -R` of `7efb9aa`, `dcacf4c`, `942c79a`, `265f423`), so Control 1 isolates this row's hunks from 211 commits of unrelated movement |

### `main` moved during the round, and here is why it does not matter

`main` advanced from `c506ca5` to `47887dd` mid-review (`7b8951e`, `3275338`,
`5fddcc9`, `47887dd` — TASK-256's V4 review landing). `git diff --stat c506ca5
47887dd` touches only `perry/BOARD.md`, `perry/tasks.jsonl`,
`perry/journal/…`, `.perry/events.jsonl` and one evidence file: **no code, no
tests**. The three files under review hash the same at both refs —
`bin/perry_store.py 742f4f554f35…`, `bin/perry-task 8666185c6b03…`,
`bin/perry-tasks 3f0c58f2485c…` — which are exactly the digests the mutation
harness printed when it verified its restores, so `git show main:<path>` and
`git show c506ca5:<path>` were the same bytes throughout. One casualty: my first
`t273nofix` tree was extracted after the move and so carried a later `perry/`
state, which made the first Control 1 run an unclean comparison. **Control 1 was
re-run from scratch on `c1a`/`c1b`, both pinned to `c506ca5`**, and § 6 reports
that run.

## 1. The spec was wrong about direction 1, and the round was right to say so

**The spec's mechanism does not destroy anything, exactly as the round reports.**
On `t273base`, a board of `RX-001, RX-002, RX-001` against a store of
`RX-001, RX-002, RX-003`, `perry-tasks risks-build` derives **2** records from 3
rows — and both surviving ids are intact. The `seen` skip alone loses the second
row's *prose*, not a record.

**The round's mechanism reproduces exactly**, on `t273base`:

```
board  RX-001, RX-002, RX-001   (third row's id mistyped)
store  RX-001, RX-002, RX-003
one `perry-task risk-add --title "a brand new risk"`:
  rc 0, stderr EMPTY
  stdout: perry-task: wrote RX-003 (risk-add) → … + risks.jsonl + …
  before  RX-003 "the record that is about to be overwritten"
  after   RX-003 "a brand new risk"    (opened 2026-01-01 → 2026-09-03)
```

`mint_register_id` (`bin/perry-task:1807`) reads `minting_text`, which is
`board.text()` plus the ids in `.perry/events.jsonl` — the board TEXT, exactly
as the round says. The duplicate suppresses `RX-003` from that text, the id is
reissued, and the live record is overwritten. `refuse_to_shrink` sees 3 → 3;
`substituted_away` joins on the id and finds `RX-003` on both sides.

### One thing the round did not establish, and it makes the case stronger

The reissue only happens when the id is absent from the **event log** as well as
from the board. I measured both halves:

- Build the same three risks with three `perry-task risk-add` calls, then
  hand-mistype the third row's id. `.perry/events.jsonl` carries `RX-003`, so
  `mint` returns **`RX-004`** — the record is still destroyed, but
  `substituted_away` warns on stderr. Loud, not silent.
- Now the reachable route, with **no hand-planted store at all**: create
  `risks.jsonl` with the documented one-way import,
  `perry-tasks risks-write --from-board`, whose own docstring says it appends
  **no events** on purpose. `.perry/events.jsonl` does not exist. Hand-mistype
  one row's id. One `perry-task risk-add`:

```
 import rc: 0   events file exists: False
 hand edit: third row's id mistyped RX-003 -> RX-001
 rc: 0   stderr: ''
 store after:  RX-001 "first risk" · RX-002 "second risk" · RX-003 "a brand new risk"
```

So the silent variant is not an artefact of planting a store by hand: **the
documented migration path produces exactly the state it needs**, and one typo
plus one ordinary command then destroys a record at rc 0 with an empty stderr.

**At `main` the same input refuses**, rc 1, `risks.jsonl` byte-identical:

> `## Top risks` carries the same id on more than one row — `RX-001` on lines
> 28, 30. … Nothing was written.

The fix closes the path the round found, not the one the spec described — which
is the right path to close.

**Direction 2 reproduces** on `t273base` as specified: a store holding
`RX-001 (open, cleared "")` and a stale `RX-001 (cleared 2026-02-02)` comes out
of one `risk-add` as a single `RX-001`, `status: open`, `cleared: "2026-02-02"`,
rc 0. (The `substituted_away` report does fire here about the vanished duplicate
record; the `cleared` leak itself is unreported.) At `main` it refuses, rc 1,
store byte-identical.

## 2. The doors — enumerated independently, and there is no fifth

Every writer of an id-keyed register store, found by grepping `store_text(` and
`write_atomic(` across `bin/`, `viewer/` and `setup/` at `main`:

| # | write site | register | guarded by |
|---|---|---|---|
| 1 | `bin/perry-task:2735` — `register_change`, committed by `replace_canonical_pair` | risks | board: `register_change`; store: `load_register_records` |
| 2 | same site, same call | asks | same |
| 3 | `bin/perry-tasks:680` — `cmd_risks_write --from-board` | risks | board: new `refuse_duplicate_ids`; store: pre-existing `validate_risk_records` |
| 4 | `bin/perry-tasks:1324` — `cmd_asks_write --from-board` | asks | same |

`bin/perry-tasks:1023` is intake (not id-keyed) and `:1512` is `tasks.jsonl`.
Nothing in `perry-lint`, `perry-goals`, `perry-decide`, `perry-knowledge`,
`viewer/` or `setup/` writes either store. **Four doors; confirmed.**

The one candidate for a fifth is `perry-tasks risks-render --write` /
`asks-render --write` (`bin/perry-tasks:427`, `:1134`), which writes `BOARD.md`
FROM the store. It already refuses a duplicated store at rc 2 through
`validate_*_records` findings — pre-existing, not something TASK-273 had to add.

**And the choke point really is one.** `register_change` has exactly one call
site (`bin/perry-task:3020`) and `load_register_records` exactly one
(`:2664`). All five id-keyed events were exercised against a duplicated board
and a duplicated store on `t273rev`:

```
risk-add   (board dup): rc=1  stores unchanged=True
risk-clear (board dup): rc=1  stores unchanged=True
ask        (board dup): rc=1  stores unchanged=True
answer     (board dup): rc=1  stores unchanged=True
risk-add   (store dup): rc=1  store  unchanged=True
risk-clear (store dup): rc=1  store  unchanged=True
```

(`risk-migrate` is not exercisable here: it refuses outright on a section that
is already a table, so a duplicate row cannot exist on the shape it converts.)

## 3. The `--from-board` importers, and the scope call

**The byte gate's hole is real and I re-measured it.** On `t273base`:

| input | rc | records written |
|---|---|---|
| 3 risk rows, two sharing `RX-002` with **identical cells** | **0** | **2** (stderr empty) |
| 3 risk rows, two sharing `RX-002` with **different prose** | 1 | 0 (byte gate) |
| 3 ask rows, two sharing `USER-002` with **identical cells** | **0** | **2** (stderr empty) |

On `t273rev` all three refuse at rc 1 with nothing written, and the clean-board
control still imports at rc 0 with 2 records.

**The scope call is right.** The Bound says "This row: the risks/asks builders
(`:750-761`) and the `by_id` collapse (`:748`)", and "a fourth site is a new
row" — a fourth `seen` **site**. `cmd_risks_write` / `cmd_asks_write` introduce
no `seen` set; they are two more *callers* of `risk_records` / `ask_records`,
i.e. of the very lines the Bound puts in scope. Leaving them out would have left
a documented command silently importing three rows as two records at rc 0 — the
defect this row exists to close, one command over. Guarding them is inside the
Bound, not a widening of it.

## 4. `tasks.jsonl` is SAFE — the three grounds attacked, and a fourth found

**Ground 1 — validator, not builder: TRUE.** `bin/perry_store.py:204` is
`validate_records`, and the duplicate branch is
`elif tid in seen: bad.append({"field": "id", … "expected": "unique task id"})`
followed by `continue` **into `findings`** — a report where the register
builders write a bare `continue` past the row. Confirmed at `main` and at
`548f206`.

**Ground 2 — no ordinary write rebuilds the store from the board: TRUE, but
narrower than the sentence sounds.** `commit` builds `records` by mutating
`current`, and `current = load_task_records(state_root)` — the store. There IS a
board-to-record derivation, `store_records` (`bin/perry-task:1940`), and it does
walk the board; it is reached only by `perry-tasks build/verify/write
--from-board` and by the store-ahead check, not by the mutation path. The claim
holds for "ordinary write"; a reader should not take it as "no such derivation
exists".

**Ground 3 — every caller gates: essentially TRUE, with one caller worth
naming.** `load_task_records` (`:1884`) raises `Refused` on findings;
`bin/perry-task:2032` raises; `perry-explain:554` returns `state: invalid`;
`perry-lint:3216` and `perry-tasks:204/1481/1547` report or refuse. The one
caller that does **not** gate is `store_records` at `:1978`, which uses
`if not current_findings:` to *skip* carrying `summary`/`design_refs` forward
rather than refuse — unreachable with a duplicated store on the write path,
because `commit` calls `load_task_records` first.

**Ground 4, which the result does not name and which is the strongest of them:**
`Board.refuse_duplicate_task_ids()` (`bin/perry-task:904`) is a board-side
duplicate-id **refusal that predates TASK-273** and is the exact analogue of the
one this row adds for the registers. Measured on `t273rev`:

```
duplicated tasks.jsonl + `perry-task add`        rc 1 — "malformed at line 2 (`id` is TASK-001, expected unique task id)"
duplicated task id on the BOARD + `add`          rc 1 — "BOARD.md has duplicate task ids: TASK-001 on lines 7, 9"
perry-tasks write --from-board, duplicate board  rc 1 — same refusal, 0 records written
```

The verdict "SAFE, no new row" is correct and better supported than the result
argues.

**One observation for the next reader**, not a defect: `duplicate_row_ids` is now
a second implementation of "duplicate ids on a board section", beside
`refuse_duplicate_task_ids`. They use different id predicates —
`HANDLE_RE.fullmatch` there, any non-empty `strip_handle` result here — and here
that is *correct*, because `duplicate_row_ids` deliberately mirrors
`risk_records`' own `if not rid or rid in seen` so that it reports precisely the
rows the derivation would collapse. But it is two places holding one rule, which
this repository's own habit usually forbids, and nothing states the relationship.

## 5. Out-of-scope registers, and the Bound's count

`intake` is out on both sides and it is not merely harmless: `intake_records`
has no `seen` set, no `by_id` and no id column, `INTAKE_STORED` carries no `id`,
and `REGISTER_SPEC["intake"][5]` is `None`. Verified behaviourally: two `##
Intake` rows for the same request on the same day still write (3 records, rc 0).
`grep -c cadence bin/perry_store.py` → `0`, so the two lines do not serve it.

**The Bound's count is wrong and the round's correction is exactly right.**
`grep -n "seen" bin/perry_store.py` at `548f206` gives **10** declarations —
`:202, :541, :750, :779, :856, :1066, :1143, :1377, :1404, :1476` — not 3. The
classification the result gives for the other seven checks out line by line:
validators at `:779`/`:1404`, plan walkers at `:856`/`:1476`, the intake pair at
`:1066`/`:1143`, and `:1377` is the ask builder the spec folded into its `:750`
entry. The scope the Bound draws is unaffected.

## 6. The two controls, re-run

**Control 1 — a clean board writes exactly as before.** Two extractions of
`c506ca5`, `c1b` reverse-patched. `diff -r --brief c1a c1b` reports **exactly
three differing files** — `bin/perry-task`, `bin/perry-tasks`,
`bin/perry_store.py` — and nothing else, so the comparison isolates this row's
hunks from everything else on `main`.

```
$ diff <(sed 's#/c1a#/cX#' c1a.txt) <(sed 's#/c1b#/cX#' c1b.txt)
$ echo $?
0
```

**Byte-identical** once the scratch path in the banner is normalised: 50 lines
each, `0 error(s), 37 warning(s)`, rc 0 both. (The result reports "26 warnings";
at `c506ca5` it is 37. The count moved with `main`; the invariant — unchanged,
and 0 errors — holds.)

Deliverable 2's linter half is also unchanged where it matters: on a store
holding two `RX-001` records, `perry-lint`'s output is line-for-line identical
with and without the hunks, rc 1 both, including
`⚠ risks.jsonl [risk-store-badly-typed] 'RX-001' — 'id' is RX-001, expected
unique risk id.`

**Control 2 — a repeated value that is not an id is not caught.** Five boards on
`t273rev`, all rc 0 with the expected record count:

```
two risks OPENED on the same day                              rc 0  3 records
two risks with the same STATUS and the same SENTENCE          rc 0  3 records
two asks ASKED on the same date, same question text           rc 0  3 records
two INTAKE rows for the same request on the same day          rc 0  3 records
a struck-out row beside a live row with DIFFERENT ids         rc 0  3 records
```

## 7. Mutation — 21 planted, 20 red, **1 green**

Every mutation was applied to the `git archive main` copy, never to the
repository. Each anchor was asserted **unique on the old text** before the edit
(a non-match aborts the run rather than no-opping), the file was asserted
byte-equal to `git show main:<path>` *before* mutating, `__pycache__` was cleared
and the run slept past the whole-second boundary on both sides of each run, and
**every restore was written from `git show main:<path>` and re-verified against
`git show`** — never against a snapshot this harness took. Final SHA-256 of each
restored file: `bin/perry_store.py 742f4f554f35…`, `bin/perry-task
8666185c6b03…`, `bin/perry-tasks 3f0c58f2485c…` — the same digests at `c506ca5`
and at `main`'s later tip, so the ref the harness compared against is the ref
under review.

**Batch 1 — the guard itself. 12 planted, 12 RED.**

| # | mutation | result |
|---|---|---|
| M1 | `duplicate_row_ids`: `len(rows[rid]) > 1` → `> 2` | RED (9) |
| M2 | `duplicate_row_ids` returns `[]` | RED (9) |
| M3 | `duplicate_record_ids`: `> 1` → `> 2` | RED (4) |
| M4 | `register_change`: board refusal disabled | RED (5) |
| M5 | `load_register_records`: store refusal disabled | RED (3) |
| M6 | `REGISTER_ID_KEYED` loses `"asks"` | RED (1) |
| M7 | `REGISTER_SPEC["asks"][5]` → `None` | RED (2) |
| M8 | risks importer guard disabled | RED (2) |
| M9 | asks importer guard disabled | RED (1) |
| M10 | `if not rid:` → `if rid is None:` | RED (1) |
| M11 | `strip_handle` dropped from the board report | RED (1) |
| M12 | `DUPLICATE_IDS_SHOWN` 5 → 1 | RED (1) |

**Batch 2 — the round's own claims. 8 planted, 7 RED, 1 GREEN.**
(N5 is discounted: my replacement was syntactically invalid Python, so its red
is an import error rather than a signal.)

| # | mutation | result |
|---|---|---|
| N1 | **the round's green #1 replayed** — `"intake"` INTO `REGISTER_ID_KEYED` | **RED** — `test_intake_is_declared_out_on_both_sides_not_merely_harmless` |
| N2 | **the round's green #2 replayed** — `if not rid:` → `if rid is None:` | **RED** — `test_rows_with_an_empty_id_cell_are_not_two_rows_sharing_a_blank_id` |
| N3 | intake given an id column in `REGISTER_SPEC` | RED (2) |
| N4 | the board refusal stops naming the lines | RED (1) |
| N5 | *(discarded — malformed patch)* | — |
| N6 | the importer's `refuse_duplicate_ids` renamed out from under its two call sites | RED (5, across all three modules) — but a crude one: it raises `NameError`, so its red says the call sites are exercised, not that the message content is pinned |
| N7 | `duplicate_record_ids` line numbers off by one | RED — `test_the_report_itself_finds_both_records` |
| N8 | `duplicate_row_ids` line numbers off by one | **GREEN** |

**Rule 3 confirmed.** The result claims 12 mutations, 12 red, with two greens
found and closed. I planted 12 of my own against the same halves and got 12 red;
and replaying *both* of the greens the round reported now makes a test fail. The
account is accurate.

### The green mutation — the finding

`bin/perry_store.py § duplicate_row_ids`:

```python
rows[rid].append({"line": row["line"] + 1,      # ← delete the `+ 1`
```

Nothing goes red across `test_duplicate_ids_are_refused`, `test_risks_store` and
`test_asks_store`. The refusal would then name **lines 27 and 29** for rows that
sit on lines 28 and 30 — sending a human one line above each row they have to
fix. (Verified the shipped numbers are right today: a board whose duplicate rows
are on 28 and 30 reports `{'line': 28, …}, {'line': 30, …}`.)

The reason it is undefended is **the shape the round itself named as its second
green, one test over**:

- `test_two_risk_rows_with_one_id_refuse_and_name_both_lines` asserts
  `assertRegex(r"`RX-001` on lines \d+, \d+")` — a pattern that cannot fail on a
  wrong number.
- `test_the_report_itself_finds_both_rows` asserts only
  `len(dupes[0]["rows"]) == 2`, never the `line` values.
- The **store-side sibling is pinned** —
  `test_the_report_itself_finds_both_records` asserts the actual line values,
  which is exactly why N7 goes red and N8 does not.

**Why this does not fail the row.** It is a diagnostic-precision gap, not a
behavioural one. With the mutation in place the refusal still fires, still names
the id, still prints each duplicate row's text (`line 28: 'RX-001 · a ·
2026-01-01 · open'`), and the store is still byte-identical — no record is lost
on any input a user can produce. The spec's deliverables and both controls are
met with the mutation applied. It is a real hole in the test set on one half of a
symmetric pair, and it should be closed the way the round closed its own two:
assert the line numbers on the board side as they already are on the store side.

## 8. The suite

`bash tests/run` on the pristine `c506ca5` copy (tree guard: *"nothing under …
moved"*):

```
114 modules · 3258 tests · 328.5s · 8 workers
✗ 2 of 114 MODULE(S) red
✗ 9 of 3258 TEST(S) failed
```

**Neither red module is attributable to TASK-273.**

- `tests/test_tree_guard.py` — 8 errors, every one the same:
  `git rev-parse HEAD failed there: 致命错误：不是 Git 仓库`. The module builds
  its fixture from the last commit of the tree it runs in, and a `git archive`
  copy has no `.git`. An artefact of the *reviewer's* isolation, not of the row;
  `review-constraints.md` prescribes exactly this copy.
- `tests/test_one_choke_point.py::test_the_guard_agrees_with_the_census_rule` —
  1 failure, and **it fails identically at `9c9670e`**, this row's own baseline,
  where it names `viewer/parsers.py:2360` / `bin/perry-lint:976` instead of
  `viewer/parsers.py:2366` / `bin/perry-lint:987`. Not a TASK-273 regression; it
  is TASK-323's own subject, in flight on the branch this worktree sits on.

`tests/test_duplicate_ids_are_refused.py` runs **31 tests, OK, 2.4s** — the
count the result claims for it.

The `114 modules` figure matches the result. The test total is 3258 here against
the result's 3193, because `main` gained TASK-139 / TASK-290 / TASK-308 /
TASK-323 tests after this row merged.

One footnote from the durations line, also an artefact: *"2 entries at refs git
could not resolve: 47ffa26, 942c79a"* — `942c79a` is a TASK-273 commit, and it is
unresolvable only because the copy has no object store.

## What I did not check

- **The full suite at `9c9670e`.** The result's "3162 → 3193" figures are not
  verified as numbers; what I verified instead is that the one genuinely failing
  module at `c506ca5` fails identically at `9c9670e`, so this row is no redder
  than its baseline on that module.
- **`tests/test_tree_guard.py`** could not run in this reviewer's isolation
  (a `git archive` copy has no `.git`), so its 27 tests are unmeasured here.
- `tests/durations.json` — I did not re-measure the new module's registered
  duration, nor verify the `load1 25.4` claim.
- `risk-migrate` end to end (it refuses on a table, so the duplicate state cannot
  exist on the shape it converts).
- Non-English boards / the `zh` fixture; the register headings are matched by
  the i18n glossary and I exercised only English sections.
- Concurrency and crash recovery: `replace_canonical_pair` /
  `recover_transaction` against a duplicated store, and two writers racing under
  the project lock.
- `perry-goals`, `perry-decide` and `perry_md_store` for the same `by_id`
  collapse — a fourth site is a new row under the Bound, so I did not audit them.
- The refusal *messages*' content beyond the substrings the tests assert — N6 was
  too crude to measure that, and I did not replace it with a finer one.
- `bin/perry-restore-check` itself: I hand-rolled the comparison against
  `git show main:<path>`, which `review-constraints.md § Verify a restore against
  an independent source` permits, rather than invoking the tool.

## Verdict

**PASS.**

Every deliverable in `perry/evidence/2026-09/TASK-273-spec.md` is met, and each
was checked by reproduction rather than by reading the account:

1. A repeated id on a board section is a refusal naming both rows — verified on
   all four id-keyed events plus both `--from-board` importers, stores byte-
   identical in every case.
2. A repeated id in the store is reported by `perry-lint` (output unchanged,
   line for line) and now refused by the writer, with the one-line reason the
   spec asked for carried in the refusal itself.
3. `tasks.jsonl` is decided and named safe, correctly, and with a fourth ground
   the result did not claim.

Both controls hold; the Bound is honoured; the spec's own two wrong claims were
corrected on measurement and I re-measured both corrections independently — the
`seen` skip alone destroys nothing, and the real chain is board text → reissued
id → overwritten record, reachable through the documented import with no
hand-planted state and no message on stderr.

The one green mutation (§ 7) is a diagnostic-precision gap in the test set, not
a behavioural defect: with it applied, no record is lost on any input a user can
produce. It should be closed, and it does not fail the row.
