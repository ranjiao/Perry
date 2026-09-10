# TASK-356 — acceptance criteria

> **This states a bar. It does not negotiate one.** No V4 has ever run on this
> row, no round has ever scored against it, and it has never FAILed —
> `bin/perry-task list --json` shows `status: review`, `verification: ""`, and
> no evidence document anywhere carries a verdict block naming it. So the
> distinction `work/reference/review.md § 1` draws applies in the safe
> direction: *"Criteria written after a FAIL are a negotiation with the
> result."* There is no result here to negotiate with. Nothing below was
> chosen because a round objected to it, and nothing below was written to
> fail.
>
> Written 2026-09-10 by the PMO, measured on `56d072ff`.

- **Row**: `TASK-356` — *A board-render test breaks whenever a row's prose
  contains its sentinel word*
- **Under review**: the merged work described in
  `perry/evidence/2026-09/TASK-356-result.md`
- **Rung**: **V4** — argued in *The rung* below, not assumed

## Why this row had no criteria until today

The round the row's `V4 REVIEW` label names was killed by the 2026-09-04 rate
limit. Nothing re-dispatched it and nothing noticed, so the row has sat at
`review` while **the code it describes has been merged on `main` the whole
time**. `review.md § 1` refuses to dispatch a reviewer without written
criteria, so the row could not move in either direction. This file is what
unblocks it.

## Files in scope

- `tests/test_board_render.py` — `TestTheBytesComeFromTheStore.cell_of()`
  (line 225), the rewritten
  `test_every_rendered_field_moves_when_the_store_moves` (line 283), and the
  new `test_a_row_whose_prose_carries_every_sentinel_still_passes` (line 347).
- `perry/evidence/2026-09/TASK-356-result.md` — the exhibit, including the
  seven-field sentinel census.

The row's claim is that **exactly one file changed** and `bin/perry_store.py`
is untouched. Establish that first: this test is the only thing standing
between the renderer and a board that prints values the store does not hold.

## Deliverable

The store-ownership round trip grades **the cell the field renders into**, by
resolving the column **by name** through the schema glossary, and compares it
for **equality against the cell as it rendered before the mutation** rather
than for absence of a sentinel. A row's own English can no longer redden it.

## What must be true when this is done

Each criterion is a claim about behaviour. It is met only if the named
mutation turns the named test **red**, and a mutation that comes back green is
the finding either way (`review.md § 2` rule 2).

**1. Every stored field still has to reach its own column.** For each of the
seven graded fields, writing the sentinel into `tasks.jsonl` and re-rendering
must change **that field's cell** to the sentinel.

- Named test: `tests/test_board_render.py::TestTheBytesComeFromTheStore::test_every_rendered_field_moves_when_the_store_moves`
- Mutations that must redden it, each naming the field it perturbs:
  - `status` removed from `FIELD_BY_COLUMN` (`bin/perry_store.py:76`) → red on
    `field='status'`. **This is the mutation the row asks for by name.**
  - `next action` removed (`bin/perry_store.py:79`) → red on `field='next_action'`.
  - `depends on` removed (`bin/perry_store.py:80`) → red on `field='depends_on'`.
  - `owner` and `status` render each other's stored field
    (`bin/perry_store.py:76`) → red on both.
  - `depends_on` joined with `","` instead of `", "` (`bin/perry_store.py:292`)
    → red on `field='depends_on'`.
- **The subtest that goes red must name the field that moved.** A mutation
  that reddens the module without naming its field means the locator, not the
  renderer, is what failed.

**2. The row's own prose cannot redden it.** A row whose `title` and
`next_action` quote **every** sentinel at once — the worst board this project
could legitimately write — still passes all seven round trips.

- Named test: `…::test_a_row_whose_prose_carries_every_sentinel_still_passes`
- Mutation that must redden it: widen `cell_of()` back to `row_of()` — grade
  the whole rendered row instead of the cell. Under the old rule that board
  fails on **all seven** fields, which is the census result this criterion
  encodes.
- **This test must stay a construction, not a scan.** A test that read today's
  live prose would go red whenever the project's own text changed, which is
  the defect being fixed, re-introduced one level up. If it scans the board,
  criterion 2 is not met however green it is.

**3. The column is resolved by name, not by index.** `cell_of()` reads the
header through `T.split_row` and `T.header_index` — the repository's only row
splitter and only header fold — and looks the column up through
`P._column_keys`.

- Named tests: the two above, both of which locate through `cell_of()`.
- Mutation that must redden them: replace the name lookup with a fixed index
  (`cells[3]`). `viewer/parsers.py` spends its longest comment explaining that
  column *order* is not schema-constrained; a hardcoded index is that defect
  planted in the test.
- Additional required check, because a locator can fail *silently* rather than
  loudly: make `cell_of()` return `""` for an unresolvable column instead of
  asserting. `test_every_rendered_field_moves_when_the_store_moves` must still
  go red. **A locator that can return nothing and be graded is a round trip
  that passes without rendering anything.**

**4. The round trip cannot go vacuous.** `assertNotEqual(was, want)` fires
before either half, so a field whose stored value already equals its sentinel
fails loudly rather than passing silently.

- Named test: `…::test_every_rendered_field_moves_when_the_store_moves`
- Mutation that must redden it: set the fixture row's `status` to `dropped`
  before the round trip. The precondition must fire. This is not
  hypothetical — `dropped` is a status this board's rows genuinely take, which
  is why absence was the wrong comparison.

## Bound

    Enumeration: python3 -c "import sys;sys.path.insert(0,'tests');\
                 import test_board_render as t;\
                 print(sorted(t.TestTheBytesComeFromTheStore.MARKS))"
    Size:        7 (field, column, sentinel) triples on 56d072ff — depends_on,
                 evidence, next_action, owner, status, title, verification.
                 TestTheBytesComeFromTheStore.FIELD_COLUMN carries the same 7
                 keys, so a field cannot be graded against one column in one
                 test and another column in the next.
    Remainder:   bin/perry_store.py's FIELD_BY_COLUMN maps 15 columns on this
                 ref, so 8 rendered columns are NOT graded by this round trip:
                 id, track, stage, stage since, arrived, parent, commitment,
                 role. They are deliberately out of scope — this row narrowed
                 an assertion's SCOPE, it did not widen its COVERAGE, and
                 adding the other 8 would be a different row with a different
                 argument. Also out of scope: whether the three sentinels the
                 census flagged as ordinary words (`dropped`, `Nobody`, `V6`)
                 should be replaced with tokens prose cannot produce. Cell
                 scoping makes that unnecessary rather than urgent; if a
                 reviewer disagrees, that is a NEW ROW with its own bound
                 (`review.md § 1`), never a widening of this one.

**Why this bound ends.** "No sentinel ever collides with any row's prose" is a
universal negative over a board that changes every day — the shape `review.md
§ 1` says fails to *end* a round rather than fail it. So the criterion is not
that. It is: these 7 triples, each graded in its own column; the other 8
columns are named and excluded; and the worst-case board is a construction the
test carries, not a scan of live text.

## The rung, and why it is V4

`review.md § 0` asks three questions. Answered against **what this row can do
when it is wrong**:

1. *Does a defect here destroy or corrupt state that cannot be recreated?*
   No. The test writes only into its own fixture project.
2. *Does a defect here make a tool report a wrong answer nobody can detect?*
   **Yes — this test is the only thing that answers that question about the
   board.** `TestTheBytesComeFromTheStore`'s own docstring states its job: a
   renderer that emitted the board's existing row lines back would pass every
   byte-comparison test in the module. `BOARD.md` is a rendered surface a human
   reads and trusts. A renderer printing a stale `Status` with nothing red is
   exactly § 0's *"a count, a verdict, a rendered surface, a payload a consumer
   trusts."*
3. *Does it weaken a gate standing in front of either?* **Yes, and this is the
   answer that decides the rung.** `git diff --stat 5d247c1c^1 5d247c1c`
   deletes **9 lines** of `tests/test_board_render.py`: this row did not add an
   assertion beside the old one, it replaced it. It narrowed a live assertion
   twice over — from the whole row to one cell, and from *absence* to
   *equality* —
   and replaced a fixed reading with a name lookup that can fail. Each of those
   is a way for the gate to keep passing while grading less. That is not a
   hypothetical class: the row's own § 5 already records **one green** (the
   restore half has no independent power against any of the six mutants) and
   one refuted hypothesis. A change with a measured green in its own exhibit is
   not a V3.

§ 0's asymmetry decides it: *"the round you did not run leaves nothing behind
to notice."* An assertion that has quietly stopped grading leaves nothing
behind to notice.

**One thing the round should know and not re-derive.** The restore half of the
round trip has been measured as having no independent power, for a structural
reason: `BOARD.md` is a static template during these tests, so the only stale
value a renderer can hold *is* the board's original text, and the SET half
fails on it one assertion earlier. The author kept it deliberately and recorded
it as never having been shown to catch anything. **That is not a criterion and
must not be graded as one** — it is already disclosed, and § 2 is explicit that
a round's job is the product, not the exhibit.

## Baseline

`bash tests/run` in this worktree, on `56d072ff`, 2026-09-10:

    ✗ 3 of 123 MODULE(S) red
    ✗ 4 of 3507 TEST(S) failed

**All four reds are pre-existing at this base and not one of them belongs to
this row.** Named in full, with their subtest keys, so the next round does not
spend itself attributing them:

1. `tests/test_contract_key_parity.py::TestAWitnessProjectMakesAnEmptyCollectionObservable::test_without_the_witness_the_four_are_unobservable`
   — subtest `[conformance.in_progress_with_no_live_run[].means]`
2. `tests/test_contract_key_parity.py::TestTheWitnessedKeysRedden::test_the_same_mutation_is_silent_without_the_witness`
   — the same subtest key
3. `tests/test_diagnose.py::DecisionsAreCountedPerRecordNotPerMention::test_the_queue_register_reconciles_with_the_queue_on_this_repository`
   — `TASK-420`, being fixed in a sibling worktree
4. `tests/test_resume.py::TestStaleRuns::test_a_fresh_run_is_not_stale`
   — clock-dependent

None of the four is in `tests/test_board_render.py`. **Note the direction of
travel**: this row's own subject was a red in `test_board_render` on `main`,
and that red is gone at this base. Two further modules are known
**load-sensitive** on this machine and go red for reasons that are nobody's
row — `tests/test_host_support.py` (`TASK-357`) and `tests/test_diagnose.py`,
whose 4 subprocess-timeout errors this row's own § 6 measured at load 113–125
and which passed alone at load 42. Re-run a red module alone before
attributing it.

**The machine was not quiet, and the number is recorded rather than glossed.**
This run finished at load average **155 on 14 cores**, with other agents'
suites running throughout. `tests/test_host_support.py` came back green anyway,
and `test_diagnose`'s single red is the `TASK-420` assertion rather than the
subprocess-timeout shape load produces. So a round re-measuring on a quiet
machine should see these four and no others — but **re-run a red module alone
before attributing it**, which is `TASK-357`'s own subject.

## Out of scope

- The claim in the row's exhibit that `USER-916` renders `status: dropped` on
  the live board. The PMO could not reproduce it on `main`, and the row's own
  § 3 argument stands on the two measured collisions without it. **Settling it
  is a documentation matter, not a FAIL** (`review.md § 2`).
- Replacing any of the seven sentinels.
- The other 8 columns in `FIELD_BY_COLUMN` — see *Remainder*.
- `test_diagnose`'s load sensitivity, which this row's round measured and
  correctly declined to absorb.
