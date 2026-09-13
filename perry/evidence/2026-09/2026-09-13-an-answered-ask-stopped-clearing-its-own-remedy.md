# The escalation check reported the exact workflow its own remedy asks for

**Not a row.** A defect in `bin/perry-lint § check_reviews`, found by running
`--reviews` after following the protocol correctly, fixed in the same session.
Filed here rather than on the board per this project's standing rule that
findings go in the evidence.

---

## 1. What happened

`review-rounds-exhausted` exists because two FAILs is a decision, not a third
round. Its message says what to do:

> File the ask: name the two readings, say which one you recommend and why, and
> let the user choose. **An open ask blocking this row clears this finding.**

TASK-236 did exactly that. It FAILed V4 twice, `USER-927` was filed naming both
readings, the user chose (B), and round 3 was implemented on that authority.

`perry-lint --reviews` then reported:

```
⚠ BOARD.md [review-rounds-exhausted] TASK-236 has FAILed 2 V4 rounds on
  row-failing criteria and never PASSed … File the ask …
```

The remedy on offer was a second ask about a question already answered.

## 2. The cause, one line

```python
if ask.get("answered"):
    continue
```

The escalation counted **only while the question was still out**. The moment
the user answered — the whole point of filing it — the row went back to being
reported as one that had *"neither converged nor escalated"*.

This is the project's **measurement-artefact** shape: a check whose input is a
proxy for the thing it means. It meant *has a principle been picked*, and it
measured *is a question pending*. Those agree right up until the answer
arrives, which is the one moment the check is consulted.

## 3. Why the old behaviour was not simply a bug

`tests/test_review_verdicts § test_an_ANSWERED_ask_does_not_clear_it` asserted
it deliberately, with a reason:

> An answered ask is a decision already taken; it cannot license the next
> unexamined round the way a pending one licenses waiting.

That concern is real and the fix preserves it. It conflates two sets, and
separating them is the whole change:

| the FAILs that **prompted** the ask | settled by the answer |
| the FAILs that **arrive after** it | unexamined, and still count |

So an answered ask clears the rounds it was answering and nothing else. A row
that FAILs the limit again after the answer is failing on a principle the
answer did not settle, and fires again. The test is renamed
`test_an_answered_ask_with_nothing_to_order_it_does_not_clear_it`, because that
is what its fixture actually pins — it writes no `answer` event.

## 4. The ordering needs no new field

Both timestamps are already written by Perry's own writers, so this reads
timestamps rather than parsing prose (`ADR-007` decision 3):

| what | where |
|---|---|
| when an ask was answered | the `answer` event's `ts` |
| when a review document arrived | the first `evidence` event naming it |

**Unorderable means strict, in both directions**, which is the half that keeps
the teeth:

- an answered ask with **no `answer` event** clears nothing — the old behaviour,
  since nothing can say which rounds it settled;
- a FAIL with **no `evidence` event** counts — otherwise a missing event would
  silence the limit.

## 5. Measured on this project

```
before:  ⚠ review-rounds-exhausted  TASK-236 … 2 rounds, limit 2
after:   (absent)
         27 → 26 advisory findings
```

And the honest reading it now gives TASK-236: **one** FAIL since the principle
was picked, not three. Round 3 FAILed too, but that is the first round under
the answer, which is below the limit — so the check says "keep going" where
before it said "escalate again", and both of those are now the right answer to
the state they describe.

## 6. Mutations — five, none green

`__pycache__` cleared before every run.

| # | mutation | result |
|---|---|---|
| M1 | the rule removed — an answered ask clears nothing again | **RED** — 3 tests |
| M2 | an answered ask clears unconditionally, no ordering | **RED** — 2 tests incl. the teeth |
| M3 | an undated FAIL is dropped instead of counted | **RED** — `test_a_fail_no_event_dates_still_counts` |
| M4 | an answered ask with no `answer` event clears anyway | **RED** — the renamed test |
| M5 | the aside stops naming how many were not counted | **RED** — `test_the_finding_says_which_fails_the_answer_settled` |

Seven tests in `TestAnAnsweredAskClearsTheRoundsItAnswered`, module 104 green.

**One thing the tests are built to avoid.** The new class does not subclass the
class that owns `two_fails`; it copies the four-line helper. Subclassing a
`TestCase` re-runs all of the parent's tests under the child's name — measured
at 113 collected instead of 104 — and a suite that counts one assertion twice
reports work it did not do.

## 7. Suite

```
130 modules · 3784 tests · 82.4s · 8 workers
✗ 3 of 3784 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.

## 8. What this does not fix

`fail-verdict-left-at-review` has the **same shape and is still live** on
TASK-439. It decides "the FAIL was acted on" by looking for a status
round-trip off `review` and back, and a row whose fix was implemented without
ever moving the status is reported as one whose verdict was ignored. That is a
proxy for the same question this note is about, measured a different wrong way.
It is not fixed here, and it is not fixed because the honest repair is probably
the protocol rather than the check: `review.md § 5` does say to move the row.
