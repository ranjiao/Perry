# TASK-341 — acceptance criteria

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

- **Row**: `TASK-341` — *One test writes a probe file into the live tree while
  another asserts what is in it*
- **Under review**: the merged work described in
  `perry/evidence/2026-09/TASK-341-result.md`
- **Rung**: **V4** — argued in *The rung* below, not assumed
- **A caveat about the exhibit**: the row's agent was killed by the 2026-09-04
  rate limit with its work committed and **no RESULT block**, and the
  full-suite baseline its own brief asked for was never taken. The round takes
  the baseline below instead. An incomplete exhibit is normally the author's
  problem before dispatch (`review.md § 2`); here the author is gone, the code
  is merged, and the gap is named rather than hidden.

## Why this row had no criteria until today

The round the row's `V4 REVIEW` label names never ran. Nothing re-dispatched
it and nothing noticed, so the row has sat at `review` while **the code it
describes has been merged on `main` the whole time**. `review.md § 1` refuses
to dispatch a reviewer without written criteria, so the row could not move in
either direction. This file is what unblocks it.

## Files in scope

- `tests/test_one_choke_point.py` — the `scratch_tree()` helper (line 450) and
  the five probe sites that now use it.
- `tests/test_row_integrity.py` — the `_scratch_bin()` helper (line 79) and
  the three probe sites that now use it, plus the `root`/`home` parameters
  added to `_domain()` / `_tools()`.
- `perry/evidence/2026-09/TASK-341-result.md` — the exhibit, including the
  audit-hook census.

The row's claim is that **no file under `bin/`, `viewer/` or the repository
root changed.** Establish that first: these two modules are guards over the
shipped tree, and a round that does not know whether the guarded code moved
cannot grade criterion 2.

## Deliverable

Two things, and the row was explicit that the second is not optional:

1. **The census.** Which tests in the suite write inside `PERRY_HOME`, and
   which tests' assertions depend on the state of the tree they run in —
   measured, not grepped. The row demanded a census rather than a fix to the
   named pair, and the census is what found the second, unnamed collision in
   `tests/test_row_integrity.py`, whose path is built across two lines and
   which a static grep does not find.
2. **The probes move off the live tree**, into a real scratch tree walked by
   the real walker — not into a mock, and not by teaching the observing guard
   to ignore a file.

## What must be true when this is done

Each criterion is a claim about behaviour. It is met only if the named
mutation turns the named test **red**, and a mutation that comes back green is
the finding either way (`review.md § 2` rule 2).

**1. Nothing in these two modules writes into the live checkout.** For the
whole time either module runs, this repository contains no file it does not
own. The row measured 75.1% of `test_one_choke_point`'s wall time carrying a
foreign file before, and 0.0% after.

- Named test: none, and that is stated rather than glossed. This criterion is
  a property of a *window*, not of an end state, so no assertion in the suite
  holds it — `tests/tree_guard.py` compares the tree before and after a run
  and a probe written and removed inside a `finally` is invisible to it. The
  round verifies it by **re-running the row's own poller**: loop the module
  against a `git archive` copy of this ref while a second process polls
  `bin/`, `bin/lib/` and the repository root for files the repository does not
  own. Required result: **0**.
- Mutation that must make it non-zero: point one `scratch_tree(...)` /
  `_scratch_bin(...)` site back at `PERRY_HOME`. The poller must see the probe.
- If the round would rather have an assertion than a poller, **that is a new
  row** — a guard that fails a test writing into `PERRY_HOME` — not a widening
  of this bound.

**2. The guards still bite, and they still bite on THIS tree.** Moving a probe
into a scratch tree is the way this row could quietly destroy the thing it was
protecting: a walker that only ever walks a scratch root stops guarding the
repository, and every test stays green while it happens.

- Named tests, and both halves are required:
  - the plant half — `tests/test_one_choke_point.py::TestNothingOutsideTheChokePointBuildsARow::test_the_guard_sees_a_file_in_a_subdirectory`
    and `tests/test_row_integrity.py::TestEveryoneReadsTheRowTheSameWay::test_the_guard_sees_a_file_in_a_subdirectory`;
  - the live-read half — `tests/test_one_choke_point.py::…::test_the_live_bin_lib_is_inside_the_real_domain`
    and `tests/test_row_integrity.py::…::test_the_live_bin_lib_is_reached_by_this_walk`.
    These carry the one property a scratch tree cannot: that the **live**
    `bin/lib` exists and is reached by the walk.
- Mutations that must redden them, anchored **by symbol and by the line it
  sits on at `56d072ff`** — re-anchor by symbol if the file has moved, never
  by `str.replace` on a string that occurs more than once (`review.md § 2`
  rule 2): `rglob("*")` → `glob("*")` in `_tools()`,
  `tests/test_row_integrity.py:357`; `SKIP_DIRS` gains `"lib"`,
  `tests/test_one_choke_point.py:337`; `offenders()` ignores its `root` and
  reports against `PERRY_HOME`, `def offenders` at
  `tests/test_one_choke_point.py:409`; `_tools()` ignores its `home`,
  `def _tools` at `tests/test_row_integrity.py:318`.
- **Note for the round**: the mutation table in the row's own exhibit cites
  line numbers measured on its branch, and four of them have since drifted
  (`386`→`389`, `416`→`409`, `444`→`435`, `354`→`318`). That drift is
  expected and is not a finding; `review.md § 2` names citation drift a
  pre-check matter, not a FAIL.
- **A green on either of the last two is the finding**, not a curiosity: it
  means the scratch parameter is decorative and the round should say so.

**3. The domain is still discovered, not hardcoded.** `shipped_dirs()` asks
the live tree which directories exist, so a directory created tomorrow is
covered the day it appears. The probes move; the discovery does not.

- Named tests: `tests/test_one_choke_point.py::…::test_the_guard_sees_a_row_builder_in_any_shipped_directory`
  and `…::test_the_guard_domain_is_the_censuss_domain`
- Mutations that must redden them: narrow the domain walk back to
  `("bin","viewer")` — `_domain()` at `tests/test_one_choke_point.py:345`, the
  `SKIP_DIRS` filter it applies at line 389; hardcode `shipped_dirs()`,
  `def shipped_dirs` at `tests/test_one_choke_point.py:435`.

**4. The observing guard was not weakened to make the collision go away.**
`tests/test_one_primitive.py::TestOneImplementationPerPrimitive::test_bin_lib_is_the_only_exemption`
still asserts the exact list `["bin/lib/__init__.py"]` — no `*probe*` exclusion,
no untracked-file exclusion, no lock. Its own docstring says why: *"a guard
people can add themselves to is a guard that stops meaning anything."*

- Named test: the one above.
- Mutation that must redden it: plant a real second file in `bin/lib/` of a
  `git archive` copy. It must go red — that red is correct and is the point.

## Bound

    Enumeration: grep -rn 'with scratch_tree(\|with _scratch_bin(' tests/*.py
    Size:        8 probe sites on 56d072ff — 5 in tests/test_one_choke_point.py
                 (lines 524, 548, 566, 605, 733) and 3 in
                 tests/test_row_integrity.py (lines 414, 444, 470), one per test
                 method. This is exactly the 8 live-tree writers the row's own
                 audit-hook census found across 3,257 tests, now planting into a
                 scratch tree instead.
    Remainder:   the other 124 of the 126 tests/test_*.py modules on this ref.
                 The census measured them at ZERO writes into PERRY_HOME and the
                 round does not re-measure them. Two things make that remainder
                 honest rather than convenient: (a) the census ran over 114
                 modules and there are 126 today, so up to 12 modules have been
                 added since and were never censused; (b) the census's own
                 instrument had two bugs the row found and fixed, and its
                 definitive column is `open()` in a write mode. A ninth writer
                 found in any of those 124 is a NEW ROW with its own bound
                 (`review.md § 1`), never a widening of this one. Also
                 deliberately out of scope: the 137 observer tests in 51 modules
                 — they are readers, this row does not touch them, and after this
                 change there is nothing in the tree for them to observe.

**Why this bound ends.** `review.md § 1`'s eleven-round failure was a
criterion asking for a universal negative over a live tree — *prove nothing
anywhere does X*. "No test writes into the live tree" is that criterion
exactly, and written that way this round would not converge either. So it is
not written that way: the set is the 8 sites the grep prints, the remainder is
measured and named with its own limits, and the round ends when the 8 are
checked.

## The rung, and why it is V4

`review.md § 0` asks three questions. Answered against **what this row can do
when it is wrong**:

1. *Does a defect here destroy or corrupt state that cannot be recreated?*
   Not directly — but the row's own § 1 records the near miss: an interrupted
   repro left `bin/lib/rowprobe.py` on disk and the next `git add -A`
   **committed it**. A probe in the live tree is one killed process away from
   becoming tracked content.
2. *Does a defect here make a tool report a wrong answer nobody can detect?*
   Yes, in the direction that matters. The tests in scope are the guards over
   the row builder and the row splitter — the rules that stop a title
   containing a pipe from producing a six-cell row against a five-cell header.
   A rendered row that is silently wrong is the archetype of a wrong answer a
   reader cannot detect.
3. *Does it weaken a gate standing in front of either?* **Yes, and this is the
   answer that decides the rung.** Unlike a row that only adds coverage, this
   one **changed what an existing guard walks**, and the size of that change
   is measurable: `git diff --stat 0724fa6c^1 0724fa6c` deletes **129 lines**
   across the two guard modules against 613 insertions. This is a rewrite of
   two live guards, not an addition beside them. Before, the guards walked
   `PERRY_HOME`; now they walk a parameterised root. If the parameter is
   ignored, or the walk stops descending, the guards keep passing while
   guarding nothing — which is precisely the shape this repository has already
   been bitten by three times in this very module (rounds 2, 3 and 5, recorded
   in its own comments).

§ 0's asymmetry decides the close call: *"Raising a rung is cheap and
reversible; lowering one is neither, because the round you did not run leaves
nothing behind to notice."* A guard that has stopped guarding leaves nothing
behind to notice.

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

None of the four is in `tests/test_one_choke_point.py`,
`tests/test_row_integrity.py` or `tests/test_one_primitive.py`. Two further
modules are known **load-sensitive** on this machine and go red for reasons
that are nobody's row — `tests/test_host_support.py` (`TASK-357`) and
`tests/test_diagnose.py` (recorded in `TASK-356-result.md § 6`) — so re-run a
red module alone before attributing it. **This matters more here than
elsewhere**: this row's whole subject is a red landing on the module that had
nothing wrong with it.

**The machine was not quiet, and the number is recorded rather than glossed.**
This run finished at load average **155 on 14 cores**, with other agents'
suites running throughout. `tests/test_host_support.py` came back green anyway,
and `test_diagnose`'s single red is the `TASK-420` assertion rather than the
subprocess-timeout shape load produces. So a round re-measuring on a quiet
machine should see these four and no others — but **re-run a red module alone
before attributing it**, which is `TASK-357`'s own subject.

## Out of scope

- The lock-protocol race in `bin/perry-dispatch-limit` — `TASK-313`, and
  `TASK-357-result.md § 5` is its first concrete reproduction.
- Any change to the 137 observer tests. The row's chosen direction is
  explicitly that the observers stay exactly as they are.
- Re-running the audit-hook census over all 126 modules — see *Remainder*.
- The correction note in this row's own record that identifies `TASK-313` with
  the `2 != 3` red. `TASK-357-result.md § 9` shows that identification is
  wrong. It is a documentation defect with its own fix, and `review.md § 2` is
  explicit: **file a row, never a FAIL on this one.**
