# TASK-439 — round 4, answer C: the visibility claim comes out

**Rung:** V4. **Authority:** `USER-928`, answer **C** for FAIL-1, given
2026-09-13. Round 3 implemented **A** for FAIL-2 (`d8dc6ae8`). With this, both
halves of the ask are discharged.

---

## 1. The sentence, and why deleting it is the fix

The refusal told a caller that reaching for `--unlinked` buys a record that
stays **visible**. That was the only non-neutral item in `§ What it must not
do` item 1's argument that the refusal does not make `--unlinked` the easy
default — and **the same sentence FAILed two V4 rounds**:

| round | the reader it named | why it was false |
|---|---|---|
| 1 | `perry-lint` | `linkage-unlinked-exists` warns ONLY on a declared id that is not a record in `tasks.jsonl`. A healthy declaration hits its `continue` |
| 2 | `perry-state --section attribution` | reads through `parsers.linkage_records_for_phase`; **143 standing declarations on this project, 116 reported** |

There was no third reader. Neither of the two reports a healthy standing
declaration from a past phase, so the property the sentence described does not
exist anywhere.

The user was offered **B** — widen the reader so the claim becomes true — and
declined it. `declared_unlinked` stays phase-scoped, and that is now a recorded
property rather than a defect awaiting a fix.

## 2. What landed

| file | change |
|---|---|
| `bin/perry-task` | the refusal keeps `CANNOT BE WITHDRAWN` and drops the visibility clause |
| `bin/perry-task` | the comment carrying must-not item 1's argument: four items, and an account of the deleted fifth |
| `work/reference/subcommands.md` | the `add-task` bullet, the second product surface round 1 enumerated |

## 3. WHAT C COSTS, said plainly

Round 1's reviewer called standing visibility the only non-neutral item in this
argument. After C the friction is **irreversibility alone** — one item instead
of two.

That is a real reduction and it is worth stating rather than papering over.
What makes it the right trade is that the remaining item is **true**: a false
friction is not friction, it is a sentence that reads as one until somebody
measures it, which two reviewers now have.

## 4. A GREEN MUTATION IN MY OWN GUARD, AND IT IS THE BEST THING HERE

The class's load-bearing test is `test_the_named_reader_is_phase_scoped`. Its
job is not to describe today's behaviour — it is to **stop the claim being
re-added in good faith** by someone who checks it on a fresh board and sees it
work, and to go red the day option B lands so C can be revisited.

So I mutated the phase check it names — `viewer/parsers.py:4137`, the
`unlinked` branch of `linkage_records_for_phase`, made to return `True`
unconditionally, which is option B simulated.

```
=== M4: option B simulated — the reader stops being phase-scoped ===
Ran 32 tests   OK          ← GREEN
```

**The guard did not guard.** The first draft moved `phase/CURRENT` to a phase
with no records at all, and `linkage_records_for_phase` returns `None` outright
when its slice holds no `kr` record (`:4143`). The declaration vanished through
a different door, so the test was green whatever the phase check did.

### Two doors, which the round-2 review and my own comment both blurred

| declarations | dropped by |
|---|---|
| the 27 from phases 001 and 002 | the `unlinked` phase check |
| the 116 from 003, once another phase opens | the empty-slice `None` while the new phase has no register; the phase check once it has one |

Same outcome, two mechanisms. The test now builds phase 004 a register so the
slice is real and the phase check is the only thing that can drop the record.
Re-run, **M4 is RED**. The comment in `bin/perry-task` is corrected to match.

## 5. Tests — `TestTheRefusalMakesNoVisibilityClaim`, four

| test | what it pins |
|---|---|
| `test_the_message_claims_no_standing_visibility` | neither tool name, nor the phrase, can come back |
| `test_the_friction_it_keeps_is_the_true_one` | C deleted one item, not both |
| `test_the_named_reader_is_phase_scoped` | **the measurement behind the deletion** — red when B lands |
| `test_the_lane_page_makes_no_visibility_claim_either` | the second product surface |

Module: **32 tests, all green.**

## 6. Mutations — five, one green and corrected

| # | mutation | result |
|---|---|---|
| M1 | the claim comes back in the refusal | **RED** |
| M2 | the true friction is dropped too | **RED** — 2 tests |
| M3 | the claim comes back in the lane page | **RED** |
| M4 | option B simulated: the phase check always passes | **GREEN, then RED after § 4's fix** |
| M5 | the empty-slice `None` guard removed | **GREEN — correctly** |

M5's green is the control for § 4 rather than a defect: once the test builds a
register for phase 004, that guard is no longer the door it goes through, so
removing it must change nothing. If M5 had reddened, the test would still be
measuring the wrong mechanism.

Restore verified: `viewer/parsers.py` is sha256-identical to `git show HEAD:`.

## 7. Suite

```
130 modules · 3789 tests · 89.3s · 8 workers
✗ 3 of 3789 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.

## 8. Both halves of USER-928 are discharged

| finding | answer | where |
|---|---|---|
| FAIL-2 — the gate forced a guess where the register could not answer | **A** | `d8dc6ae8`, round 3 |
| FAIL-1 — the refusal's visibility claim | **C** | this round |

B was offered and declined, so it is **not** a deferred row. The bound round 3
recorded still stands: a fabricated `--kr` is accepted in the between-phases
window, pinned by `test_a_fabricated_kr_is_still_accepted_in_the_gap`, because
A removed the forcing and not the acceptance.

The row is ready for a fresh V4.
