# TASK-439 — round 3, answer A: the gate keys off the phase

**Rung:** V4. **Authority:** `USER-928`, answer **A**, given 2026-09-13.
Round 2 FAILed on two findings; this round closes the second and leaves the
first open, because the user has answered half the ask.

---

## 0. What A is, and what it is not

`review.md § 6` sent TASK-439's second FAIL to the user as `USER-928` with
three readings. The user chose **A** for FAIL-2 and has not yet chosen between
**B** and **C** for FAIL-1. So this round implements A alone, and FAIL-1's
false sentence is **still in the product** — deliberately, pending that answer,
and recorded here so nobody reads this file as closing the row.

## 1. The defect A closes

The gate fired on `linkage.jsonl` merely EXISTING. `--unlinked` needs more than
that: `linkage_add_change` refuses a declaration when the store declares no key
result for the current phase, because such a record has no phase to be made
against and would be counted under every phase at once.

So the gate demanded an answer the register could not supply and the writer
would refuse. Measured on `fc6df1d6` with `phase/CURRENT` cleared — the state
`goals/reference/phases.md § score-phase` step 7 **prescribes**, "until the
next `plan-phase`":

| command | before A |
|---|---|
| `add` (neither flag) | refused — "pass exactly one" |
| `add --unlinked` | **refused** — "no key result for the current phase" |
| `add --kr P004-O9-KR9` | **written, exit 0, empty stderr** |

The accepted one wrote `{"kind": "edge", "kr": "P004-O9-KR9", "via": "add"}` to
a key result no record declares, and `perry-lint` printed zero lines about it.

**The only way past a gate whose own message says *"resolve the id through
`linkage.jsonl` rather than guessing it"* was the guess
`reference/okr-linkage.md` forbids.** Before this row, all five such states
filed with a warning — so the gate was strictly worse than what it replaced.

## 2. What landed

One condition. The gate now asks `_current_store_phase(state_root)` — the
**same predicate the writer asks**, read from the store's own `kr` records — so
the gate and the writer cannot disagree about whether the register can answer.

Measured after, same fixture:

| command | in the gap | register intact |
|---|---|---|
| neither flag | **files, with a warning** | refused, rc=1 |
| `--unlinked` | refused (writer's rule, untouched) | rc=0 |
| `--kr <real>` | — | rc=0 |

**The warning's sentence was split, and that was not optional.** Before A there
was one way to reach that line — no store at all — and the text said so. A adds
a second: a store that exists and declares nothing for this phase. Telling that
caller *"this project has no `linkage.jsonl`"* is a false statement about a
file they can see, which is the defect class this row has already FAILed on
twice. The two cases now each say what is true of them.

## 3. THE BOUND — what A does not fix, as a test rather than a sentence

**A fabricated `--kr` is still accepted in the gap.** A removes the *forcing*,
not the *acceptance*: the caller is no longer pushed into the guess, but
nothing here validates the id. That is id validation and it is not this gate.

`test_a_fabricated_kr_is_still_accepted_in_the_gap` pins it. Written as a test
rather than as prose because a limit in a result document is a limit nobody
re-runs; if id validation lands later, that test goes red, and red is the
correct signal to come back and re-read this section.

## 4. Tests — `TestTheGateKeysOffThePhaseNotTheFile`, seven

| test | what it pins |
|---|---|
| `test_the_gap_files_the_row_instead_of_refusing` | the FAIL, directly |
| `test_the_gap_still_warns` | it files, it does not go quiet |
| `test_the_warning_does_not_claim_the_store_is_missing` | the new branch tells the truth |
| `test_a_store_less_project_still_says_the_store_is_missing` | **the control for it** — the other branch untouched |
| `test_the_honest_answer_is_not_refused_while_the_row_is_filed` | the asymmetry that made this a FAIL, asserted as such |
| `test_a_fabricated_kr_is_still_accepted_in_the_gap` | § 3's bound |
| `test_the_gate_still_refuses_where_the_register_answers` | **anti-vacuity** — same command, register present, refused |

Module: **34 tests, all green.**

## 5. Mutations — three, none green

`__pycache__` cleared before every run.

| # | mutation | result |
|---|---|---|
| M1 | revert the gate to keying off the file | **RED** — 3 tests, incl. the gap and the asymmetry |
| M2 | the gate stands down everywhere | **RED** — 10 tests |
| M3 | the warning tells both cases the same false thing | **RED** — `test_the_warning_does_not_claim_the_store_is_missing` |

M2's breadth is the point: the gate is load-bearing for ten assertions across
five classes, so A narrowing it is a narrowing and not a removal.

## 6. Suite

```
130 modules · 3791 tests · 80.9s · 8 workers
✗ 3 of 3791 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.

## 7. STILL OPEN — this row is not done

`USER-928` is answered for FAIL-2 and **not** for FAIL-1. The refusal still
tells callers that a standing declaration is reported by
`perry-state --section attribution` *"for as long as it stands"*, and that
reader passes through `linkage_records_for_phase`, which keeps a record only
while its phase matches `phase/CURRENT`. On this project: **143 standing
declarations, 116 reported**, and those 116 go the day 004 opens.

B makes the sentence true by widening the reader, at the cost of a published
`perry-state` payload moving 116 → 143 without its own review. C deletes the
claim. The user has that choice; the row stays blocked on it.
