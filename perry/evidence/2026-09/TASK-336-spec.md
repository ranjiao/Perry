# TASK-336 — acceptance criteria

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

- **Row**: `TASK-336` — *summary_tokens' CJK behaviour lost its pin when the
  fragment floor was removed*
- **Under review**: the merged work described in
  `perry/evidence/2026-09/TASK-336-result.md`
- **Rung**: **V3** — argued in *The rung* below, not assumed
- **Depends on**: `TASK-330` (done) — the row whose correct removal is the
  collateral this row repairs

## Why this row had no criteria until today

The round the row's `V4 REVIEW` label names was killed by the 2026-09-04 rate
limit. Nothing re-dispatched it and nothing noticed, so the row has sat at
`review` while **the code it describes has been merged on `main` the whole
time**. `review.md § 1` refuses to dispatch a reviewer without written
criteria — *"a fresh reviewer with no written criteria invents its own bar"* —
so the row could not move in either direction. This file is what unblocks it.

## Files in scope

Three files, and the split between them is the whole argument for the rung:

- `bin/lib/__init__.py` — **comment only, and the PMO measured it rather than
  taking the row's word.** On the merge commit `f5ee0e94`:

        git diff f5ee0e94^1 f5ee0e94 -- bin/lib/__init__.py
        → one hunk, +9/-2, every changed line a `#:` comment
        → 0 non-comment lines changed

  The round should re-derive this, because everything below depends on it.
- `tests/test_summary_is_asked_for.py` — the three tests added under
  `TestTheCheckDoesNotJudgeLanguage`. **Purely additive, measured**:
  `git diff --numstat f5ee0e94^1 f5ee0e94 -- tests/test_summary_is_asked_for.py`
  → `100  0`. Not one existing line was deleted, so no assertion that was
  grading something before this row is grading less after it.
- `perry/evidence/2026-09/TASK-336-result.md` — the exhibit.

## Deliverable

The property *`summary_tokens` counts CJK without assuming spaces* is held by
a named test again, reached **through the one rule that survived TASK-330** —
`summary-repeats-title`'s prefix arm — rather than through the word floor
TASK-330 correctly deleted.

## What must be true when this is done

Each criterion is a claim about behaviour. It is met only if the named
mutation turns the named test **red**, and a mutation that comes back green is
the finding either way (`review.md § 2` rule 2).

**1. A good Chinese summary is not refused.** A summary that opens with its
Chinese title and adds at least `SUMMARY_MIN_WORDS` tokens of new text
produces no finding from `lib.summary_shape`, and `perry-task add` accepts the
row.

- Named test: `tests/test_summary_is_asked_for.py::TestTheCheckDoesNotJudgeLanguage::test_a_chinese_summary_that_extends_its_chinese_title_is_not_a_repeat`
- Mutation that must redden it: revert `summary_tokens`
  (`bin/lib/__init__.py:1972-1974`) to `str.split()` — `cjk = 0`,
  `rest = len(s.split())`.
- **Why this test and not the older one**: the pre-existing
  `test_a_chinese_summary_is_not_refused_for_being_chinese` pairs a Chinese
  summary with an *English* title, so `summary-repeats-title` returns before it
  counts anything. It names the right language and never reaches the code that
  handles it. If the named test above is deleted or weakened so that
  `fs.startswith(ft)` no longer holds, criterion 1 is not met even if the test
  is green.

**2. The rule still fires in Chinese.** A Chinese summary that genuinely
restates its title is still refused — on **both** arms: equality after
folding, and the prefix arm with a margin under the threshold.

- Named test: `…::test_a_chinese_summary_that_does_restate_its_title_is_still_caught`
- Mutation that must redden it: make `summary-repeats-title` skip CJK input
  entirely. This is the wrong fix that satisfies criterion 1, and criterion 2
  exists to refuse it.

**3. The prefix arm's margin is counted in tokens, not characters.**

- Named test: `…::test_the_prefix_arms_margin_is_counted_in_tokens_not_characters`
- Mutation that must redden it: replace
  `abs(summary_tokens(fs) - summary_tokens(ft))` at `bin/lib/__init__.py:2093`
  with `abs(len(fs) - len(ft))`.
- **This mutation came back GREEN in the row's own round 1**, against a suite
  that included both tests the row had just added, because a 24-character
  gloss of a 6-character title clears five of anything. The round found it and
  closed it. The criterion is that it is *closed*, not that it exists.

**4. English behaviour did not move.** For an ASCII string `summary_tokens`
*is* `str.split()`, and the rows on this board that fired before still fire and
no others.

- Named tests: `…::test_a_one_character_title_does_not_swallow_every_summary`
  and `…::TestOnePlaceDefinesWhatASummaryIs::test_the_writer_and_the_linter_agree_over_a_corpus`
- Mutation that must redden them: `SUMMARY_MIN_WORDS = 5` → `0` at
  `bin/lib/__init__.py:1930`, and `return cjk + rest` → `return rest`.

**5. The removed rules stay removed.** TASK-330 deleted
`summary-has-no-sentence` and `summary-is-a-fragment` by the user's decision.
Nothing here re-introduces either under any spelling, and both stay named in
the NOT CHECKED register.

- Named tests: `…::test_neither_a_fragment_nor_a_sentenceless_value_is_a_finding`
  and `…::TestOnePlaceDefinesWhatASummaryIs::test_the_contract_enumerates_exactly_the_rules_the_predicate_emits`

## Bound

    Enumeration: grep -rn 'summary_tokens(' bin/ viewer/ | grep -v __pycache__
    Size:        2 lines on 56d072ff — the definition at bin/lib/__init__.py:1960
                 and exactly ONE production call site, bin/lib/__init__.py:2093,
                 inside summary_shape's prefix arm. viewer/ has none.
    Remainder:   the three test-side uses (tests/test_summary_is_asked_for.py:510,
                 513 and one in a docstring at 558) are the pins themselves, not
                 sites where the property could be unheld. summary_shape emits
                 2 rules today — `summary-missing` (line 2075) and
                 `summary-repeats-title` (line 2096) — and only the second
                 counts tokens, in 1 of its 2 arms. Deliberately out of scope:
                 whether SUMMARY_MIN_WORDS = 5 is the right threshold, the
                 CJK ranges in _SUMMARY_CJK beyond the four already covered,
                 and any rule TASK-330 removed. A sixth CJK range that turns
                 out to matter is a new row with its own bound, never a widening
                 of this one (`review.md § 1`).

**Why this bound ends.** The failure `review.md § 1` records is a criterion
with no last element — *"no reader resolves a header cell by its own rule"*
cost eleven rounds. This one has a last element and the grep prints it: there
is exactly one place in the shipped tree where the CJK count is load-bearing.
A reviewer does not have to prove a universal negative about where else the
property might be unheld, because the enumeration answers it.

## The rung, and why it is V3

`review.md § 0` asks three questions. Answered against **what this row can do
when it is wrong**, which is the axis § 0 says is the only one:

1. *Does a defect here destroy or corrupt state that cannot be recreated?*
   **No.** The row writes no state and touches no writer.
2. *Does a defect here make a tool report a wrong answer nobody can detect?*
   **No, and this is the load-bearing answer.** The production diff is
   comment-only: zero non-comment lines. `summary_shape` answers byte-identically
   before and after this row, so no defect in it can change what `perry-task
   add` or `perry-lint` says to anybody.
3. *Does it weaken a gate standing in front of either?* **No, and this is
   measured, not assumed.** The test-file diff is `100 0` — a hundred lines
   added, **zero deleted**. No existing assertion was narrowed, rescoped or
   deleted, so no gate that was grading something yesterday is grading less
   today. **This is exactly what separates this row from `TASK-341`,
   `TASK-356` and `TASK-357`**, whose test diffs delete 129, 9 and 5 lines
   respectively — each of those changed what an existing gate grades, and each
   is a V4 for that reason. This one only adds.

Worst outcome, stated plainly: the new pin does not bite, and the CJK property
is unpinned again — a coverage gap, which § 0's *send* list does not contain.
And a coverage gap here is exactly what V3 measures: *a reproducible run —
command, inputs, output, re-runnable, attested by a script.* The five
mutations above are one line each, deterministic, and anchored by line number.

`review.md § 0`: **"159 of this board's 209 closures are already V3"**, and V3
is the default rather than a concession. This is one of them.

**What would raise it.** If the round establishes that
`git diff <BASE> -- bin/lib/__init__.py` contains any non-comment line, answer
2 changes and the rung is V4. Check that before anything else.

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

None of the four is in `tests/test_summary_is_asked_for.py`. A fifth red is
this row's business; these four are not. Two further modules are known
**load-sensitive** on this machine and go red for reasons that are nobody's
row — `tests/test_host_support.py` (`TASK-357`) and `tests/test_diagnose.py`
(recorded in `TASK-356-result.md § 6`) — so re-run a red module alone before
attributing it.

**The machine was not quiet, and the number is recorded rather than glossed.**
This run finished at load average **155 on 14 cores**, with other agents'
suites running throughout. `tests/test_host_support.py` came back green anyway,
and `test_diagnose`'s single red is the `TASK-420` assertion rather than the
subprocess-timeout shape load produces. So a round re-measuring on a quiet
machine should see these four and no others — but **re-run a red module alone
before attributing it**, which is `TASK-357`'s own subject.

## Out of scope

- Whether `summary-repeats-title` is the right rule at all. TASK-330 settled
  what this predicate is entitled to judge, and re-opening it here would be
  re-litigating a user decision through a review round.
- The 37 `summary-missing` warnings on rows that predate the gate.
- `test_host_support`'s load sensitivity, which this row's round measured and
  correctly refused to absorb — it is `TASK-357`, with its own criteria file.
