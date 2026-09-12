# TASK-379 — result

> Status: implemented and measured; **not reviewed**.
> Executor: the PMO session, inline on `main`, per `ADR-018 § B` — the change
> is small, already specified, and verifiable by a command you would have
> asked an agent for anyway.
> Rung: **V2**. `bin/perry-lint` is a reader, it puts no bytes on a user's
> disk, and `schema/state-schema.json` was not touched. `ADR-020`'s gate
> answers no.

## 0. The gap was narrower than the row said, and that is the first finding

`perry-lint --reviews` **already carries the V4 half**. `review-with-no-verdict`
reports a row at `review` at V4 with no verdict block naming it, and its guard
is literally `if (rungs.get(tid) or "").upper() != "V4": continue`.

So the row's framing — *"five rows sit at review with merged code and no
verdict document, and nothing reports it"* — was true of those five rows for a
reason it did not name: **they were V4 and the check was silent for a different
cause**, or they were below V4 and the check returns early. The gap is
everything the early return skips: V3, V2, and **no rung at all**.

## 1. The brief's predicate was wrong, and the control proves it

Measured 2026-09-12, before any edit. Eight rows at `review`; three carried no
verdict block:

| row | rung | verdict blocks | evidence file on disk |
|---|---|---|---|
| TASK-183 | V3 | 0 | `TASK-183-result.md` |
| TASK-253 | V3 | 0 | **none** |
| TASK-415 | V3 | 0 | `TASK-415-result.md` |

Two of the three have exactly what their rung asks for. A verdict block is a
**V4** artifact (`review.md § 3`); V3's artifact is a reproducible run.
Implemented as filed, this check would have reported `TASK-183` and `TASK-415`
on the day it shipped — which is how a guard becomes noise and then gets
deleted. `test_a_v3_row_with_a_result_document_is_silent` is that control, kept
as a test rather than as a sentence.

Both rows have since closed at V3 on those same documents.

## 2. The hole this session opened and then found

`TASK-285` was moved to `review` earlier today with its rung **deliberately
left empty**, because the rung was the open question. Both halves of the check
walked straight past it: the V4 guard because the rung is not V4, and the new
V3 guard because it is not V3.

**An empty rung is not a small omission.** `review.md § 0` makes the rung the
thing that decides what the round owes, and `§ 1` refuses a dispatch without
written criteria. A row at `review` with no rung has no shape to its round at
all, and nothing said so. It gets its own finding.

## 3. What a V2 row at `review` owes — the spec's open question, decided

`ADR-020` made V2 the floor on 2026-09-11 and `review.md § 0` calls its
artifact *"a structural check — a linter over required sections, schema and
format, attested by a script"*.

**A linter pass is not a document someone else produces. It is runnable now, by
whoever is reading the finding.** So for a V2 row there is no round in flight
and nothing to wait for, which makes `review` the wrong column rather than a
missing artifact. It is reported as its own shape —
`review-at-v2-has-nothing-to-wait-for` — and the message says to run the pass
and close, or to raise the rung if that is not enough.

No row has yet sat at `review` carrying V2, so this is a decision taken on the
rule rather than on an observed shape, and it is recorded here as such.

## 4. What was added

Three findings in `check_reviews`, below the existing V4 guard:

- `review-with-no-run` — V3, and no evidence file filed under the row's id.
- `review-with-no-rung` — at `review` carrying no rung.
- `review-at-v2-has-nothing-to-wait-for` — V2, per § 3.

All three carry the age the V4 finding carries, and none judges it. The
evidence directory is read **independently of the row's own `Evidence` cell**:
`TASK-253` sat here with an em-dash in the cell *and* no file, and a check that
trusted the cell would have had one honest side and one side copied from the
thing it is checking.

Live output on this repository after the change:

```
⚠ BOARD.md [review-with-no-run]  TASK-253 is at `review` at V3 and no evidence
                                 document is filed under its id …
⚠ BOARD.md [review-with-no-rung] TASK-285 is at `review` carrying NO
                                 verification rung …
```

Two rows reported, five V4 rows silent, `0 error(s)` on the default pass.

## 5. Mutations

`tests/test_review_verdicts.TestTheWaitingRoomBelowV4`, 9 tests. Each mutation
planted in `bin/perry-lint`, module re-run, `perry-lint` restored and
re-verified green afterwards.

| | mutation | result | tests reddened |
|---|---|---|---|
| M1 | V3 guard inverted | RED | 5 |
| M2 | `_has_doc` always False | RED | 1 |
| M3 | id prefix match without the `-` separator | RED | 1 |
| M4 | the no-rung branch removed | RED | 2 |
| M5 | the V2 branch removed | RED | 2 |
| M6 | `if rung == "V4": continue` removed | **GREEN** | 0 |
| M7 | the `status != "review"` filter removed | RED | 1 |
| M8 | the age dropped from the V3 message | RED | 1 |

**M6 is a genuine equivalent mutant and is recorded rather than explained
away.** The three branches below the `continue` each test the rung explicitly,
so a V4 row falls past all of them and fires nothing either way. The `continue`
is documentation and a guard against a future `else:`, not the thing producing
the behaviour. `test_v4_is_left_to_the_check_that_owns_it` now says so in its
own docstring: a test that cannot fail on the line it appears to guard is this
project's most-found defect, and one that admits it beats one that is quietly
wrong.

**M4 came back GREEN on its first run and that was a defect in the HARNESS, not
in the code.** The anchor `        if not rung:` occurs **twice** in
`bin/perry-lint` — line 1730 in an unrelated check and line 2961 in this one —
and a single-occurrence replace mutated the first. Re-anchored on the branch's
own comment, M4 is RED. Recorded because it is the same class as `TASK-235`'s
wrong-`PERRY_HOME` note: **a silent way to measure the wrong thing**, where the
green reads as evidence about the code and is evidence about the patch.

## 6. Suite, and the two reds this change caused before it was clean

Final: **3 of 3,674 failed** — 2 in `test_contract_key_parity` and 1 in
`test_resume`, the pre-existing set, both modules reproducing when run alone,
the failing key observable because `TASK-285` and `TASK-436` are `in_progress`.
`test_review_verdicts` is 97 tests, green. The suite grew by exactly the 9
tests this row adds.

**It was not clean on the first run, and both new reds are worth recording
because neither was in the code under test.**

1. `test_claims.TestNoTestFileEndsEarly`, two tests. The new class was appended
   to the END of `test_review_verdicts.py`, below its
   `if __name__ == "__main__": unittest.main()` — so under a direct
   `python file.py` run it would have been defined after the entry point and
   never collected. The guard caught it, which is the guard working. The class
   was moved above the entry point.

2. `test_handed_back_root.TestTheFlagReachesTheTemplateThatNamesIt`, one test.
   Its exemption set is `NO_ROOT_TO_GIVE = {("bin/perry-lint", "check_file",
   5642)}` — **keyed by LINE NUMBER**. Adding ~70 lines to `check_reviews`
   moved that call site from 5642 to 5714, and the module went red for a change
   that touched neither the call nor the template it is about. Verified the
   same call, byte for byte, at `HEAD:5642` and at `5714` here. Re-pinned to
   5714 with a comment saying what the cost is.

   **This is `TASK-404`'s class exactly** — a test that reddens when the file
   moves rather than when the code breaks — and `TASK-431`'s note about a guard
   *"keyed by function not line"* is the shape of the fix. Re-keying it on the
   enclosing function is a row of its own and is not taken here; it is
   recorded, not filed, per this board's standing rule about opening rows.

## 7. Left alone, deliberately

- `v4-close-without-verdict` and `review-with-no-verdict` are untouched. The
  spec put them out of scope and they work.
- Closing any of the rows the new check reports. This row builds the detector;
  what to do about what it finds is the board's business.
