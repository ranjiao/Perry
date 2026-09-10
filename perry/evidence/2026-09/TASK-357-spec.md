# TASK-357 — acceptance criteria

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

- **Row**: `TASK-357` — *The dispatch-limiter test is load-sensitive, so any
  row that adds work to the suite trips it*
- **Under review**: the merged work described in
  `perry/evidence/2026-09/TASK-357-result.md`
- **Rung**: **V4** — argued in *The rung* below, not assumed
- **Board note, and it is not a criterion**: the row records
  `blocked_by: TASK-313`, and `TASK-313` is `not_started` with `evidence: —`.
  That blocker governs *dispatching new work*, not verifying work already
  merged, and the row's own § 9 argues at length that neither row absorbs the
  other. A round must not read the open blocker as a defect in this row.

## Why this row had no criteria until today

The round the row's `V4 REVIEW` label names was killed by the 2026-09-04 rate
limit. Nothing re-dispatched it and nothing noticed, so the row has sat at
`review` while **the code it describes has been merged on `main` the whole
time**. `review.md § 1` refuses to dispatch a reviewer without written
criteria, so the row could not move in either direction. This file is what
unblocks it.

## Files in scope

- `tests/test_host_support.py` — the new
  `TestOpenCodeDispatchLimit.assert_cap_held()` (line 146), the two contended
  tests that call it (lines 248 and 264), and `run_contended()` (line 116)
  with its `CONTENDED_ROUND_TIMEOUT = 180` (line 114).
- `perry/evidence/2026-09/TASK-357-result.md` — the exhibit, including the
  timing-assumption census and the anomaly hunt.

The row's central claim is that **`bin/perry-dispatch-limit` is byte-identical
to its base** — verified by the author with
`git diff --exit-code <BASE> HEAD -- bin/perry-dispatch-limit`, and stated as
deliberate so that the mutations measure the cap and nothing else. Establish
that first; criterion 3 reads differently if the tool moved.

## Deliverable

The two contended dispatch-limiter tests assert a property that is **exact at
any load** instead of one that was asserting the machine's schedule. The tool
is not changed and no retry is added — that decision is settled with measured
arithmetic in the exhibit, not with preference.

## What must be true when this is done

Each criterion is a claim about behaviour. It is met only if the named
mutation turns the named test **red**, and a mutation that comes back green is
the finding either way (`review.md § 2` rule 2).

**1. The cap's arithmetic is still pinned, and pinned where load cannot reach
it.** A limiter that admits one more than its cap must go red.

- Named tests: `tests/test_host_support.py::TestOpenCodeDispatchLimit::test_global_cap_still_wins`
  (serial, `TOTAL=1`) and `…::test_opencode_has_an_independent_configurable_cap`
  (serial, `OPENCODE=1`).
- Mutations that must redden them: `-ge` → `-gt` at
  `bin/perry-dispatch-limit:330` (global cap) reddens the first;
  `-ge` → `-gt` at `bin/perry-dispatch-limit:325` (per-executor cap) reddens
  the second.
- **These two must stay red under 16 CPU burners.** The row's own division of
  labour is that *the serial tests own the cap's arithmetic and the contended
  tests own the race*; if the serial half is not load-independent, the new
  contended assertion has given up detection power rather than relocating it,
  and that is a FAIL.

**2. The race is still pinned.** A limiter with no mutual exclusion must go red
in both contended tests, idle and under load.

- Named tests: `…::test_concurrent_mixed_registers_do_not_exceed_global_cap`
  and `…::test_concurrent_registers_do_not_exceed_opencode_cap`.
- Mutation that must redden them: `acquire_lock` → `:` at
  `bin/perry-dispatch-limit:313`.

**3. The new assertion cannot pass by everyone losing.** `winners ==
min(cap, decided)` is asserted over contenders that **reached a cap decision**,
together with `markers == winners` and `winners >= 1`.

- Named test: `…::test_concurrent_mixed_registers_do_not_exceed_global_cap`,
  through `assert_cap_held()`.
- Mutations that must redden it, and **all three are required** — this is the
  criterion that carries the row, because `assert_cap_held` is a *weaker*
  assertion than the one it replaced and each of these is a way for it to be
  weaker than intended:
  - **the classifier over-admits**: count every exit-1 contender as a cap
    refusal, rather than only those whose stderr carries the limiter's own cap
    message. This is the mistake the row's own § 6 records making and catching;
    it must still be caught.
  - **the classifier under-admits**: count a genuine cap refusal as undecided.
    `decided` then collapses toward `winners` and the assertion becomes
    vacuous.
  - **liveness is dropped**: delete `winners >= 1`. A round in which every
    contender times out on the lock must not pass.

**4. A cap refusal in the mixed test names the GLOBAL cap.** Both per-executor
caps are set to 20 there, so a per-executor refusal would mean the round
measured the wrong limit.

- Named test: `…::test_concurrent_mixed_registers_do_not_exceed_global_cap`
- Mutation that must redden it: lower the per-executor cap so the
  per-executor refusal fires first.
- **This assertion must constrain only the capped bucket.** If it tests every
  exit-1 contender, it re-imports the load sensitivity the row exists to
  remove — see criterion 3's first mutation.

**5. The helper's own budget is not a second timing assumption.**
`run_contended`'s per-process `communicate(timeout=CONTENDED_ROUND_TIMEOUT)`
is 180s (`tests/test_host_support.py:114`), against
contended rounds measured at up to 42.7s under 16 burners. A timeout here
fails as an `ERROR`, which reads even less like a timing problem than a `FAIL`
does.

- Named tests: both contended tests, which fail as errors if it is too small.
- Mutation that must redden them: return the timeout to 20s and run under 16
  burners.

## Bound

    Enumeration: grep -c '^    def test_' tests/test_host_support.py
    Size:        35 test methods on 56d072ff, in 6 classes — the same 35 the
                 row's timing-assumption census covered. Of those, the census
                 found 3 carrying a timing assumption plus one shared helper:
                 test_concurrent_mixed_registers_do_not_exceed_global_cap and
                 test_concurrent_registers_do_not_exceed_opencode_cap (both
                 fixed), test_a_reap_is_announced_and_names_the_slot_it_took
                 (reported, NOT fixed), and run_contended's communicate timeout
                 (fixed).
    Remainder:   the 32 tests the census cleared, and it is cleared with a
                 reason per class rather than by silence: TestHostDetection (7),
                 TestMtimeIsPortable (4), TestOpenCodeSetup (6) and
                 TestOpenCodeDocumentationContract (4) contain no concurrency
                 and no wall-clock arithmetic; the rest backdate mtimes with
                 wide margins in the safe direction. Deliberately out of scope:
                 test_a_reap_is_announced_and_names_the_slot_it_took, which is
                 named, measured (30.3s of a ~60s budget consumed under load)
                 and left unfixed on purpose — it is elapsed time, not a race.
                 If it ever prints `242m old`, that is this, and a NEW ROW.
                 Also out of scope: every other module in the suite. This bound
                 is one file.

**Why this bound ends.** "No test anywhere is load-sensitive" is a universal
negative over a growing suite — `review.md § 1`'s eleven-round shape exactly.
So the criterion is not that. It is 35 tests in one file, enumerated by a
command that prints the number, with the 3 that carry a timing assumption
named and the one deliberately unfixed named too. A load-sensitive test found
in another module is a new row with its own bound, never a widening of this
one. Two are already known and named in the *Baseline* section below.

## The rung, and why it is V4

`review.md § 0` asks three questions. Answered against **what this row can do
when it is wrong**:

1. *Does a defect here destroy or corrupt state that cannot be recreated?*
   Indirectly, and the mechanism is short. The dispatch limiter is what stops
   more agents running than the cap allows. Agents beyond the cap write
   concurrently to one board; `TASK-341` is a live row about what two of them
   sharing a tree already cost.
2. *Does a defect here make a tool report a wrong answer nobody can detect?*
   Not by itself — the row changes no tool.
3. *Does it weaken a gate standing in front of either?* **Yes, and this is the
   answer that decides the rung.** `git diff --stat aea60ba3^1 aea60ba3`
   deletes **5 lines** of `tests/test_host_support.py` — the row replaced an
   assertion rather than adding one beside it. It replaced `winners == cap`
   with
   `winners == min(cap, decided)` — deliberately and with good arithmetic, but
   it is still a **strictly weaker** assertion whose strength now depends on a
   **new classifier** reading exit codes and stderr text. The row's own § 6
   records that its first version of that classifier counted the lock-protocol
   anomaly's exit-1 as a cap refusal. A gate whose grading power moved into a
   new judgement, in a row whose author already got that judgement wrong once
   and caught it, is not a V3.

And the honest limit the row states itself — *under heavy load the contended
test cannot detect an off-by-one cap* — is exactly the kind of trade a fresh
reader has to check rather than take on the author's word, which is what V4
buys. § 0's asymmetry decides the rest: *"the round you did not run leaves
nothing behind to notice."*

**A constraint the round inherits, and it is expensive.** This row's
verification method requires deliberate CPU load, and § 10 records that it is
**mutually exclusive with parallel dispatch** in both directions: 16 burners
make every other agent's timings meaningless, and other agents make these
measurements untrustworthy. The author's own "idle" baseline was taken at load
109–121 caused by four other agents. **A round that re-measures under load
must have the machine to itself, must announce its window, and must record
it.** A round that cannot get the machine may verify criteria 1–4 idle and say
under `not-checked` that the load half was not re-measured — that is a smaller
round honestly reported, not a FAIL.

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

None of the four is in `tests/test_host_support.py`. Two further modules are
known **load-sensitive** on this machine and go red for reasons that are
nobody's row — `tests/test_host_support.py` itself (this row) and
`tests/test_diagnose.py` (`TASK-356-result.md § 6`: 4 subprocess-timeout errors
at load 113–125, green alone at load 42). **Re-run a red module alone before
attributing it** — that instruction is this row's own subject, and a round
that skips it will misattribute something.

**The machine was not quiet, and the number is recorded rather than glossed.**
This run finished at load average **155 on 14 cores**, with other agents'
suites running throughout. `tests/test_host_support.py` came back green anyway,
and `test_diagnose`'s single red is the `TASK-420` assertion rather than the
subprocess-timeout shape load produces. So a round re-measuring on a quiet
machine should see these four and no others — but **re-run a red module alone
before attributing it**, which is `TASK-357`'s own subject.

## Out of scope

- **The lock-protocol race** in `bin/perry-dispatch-limit` — a holder's lock
  directory removed underneath it between `mkdir` (line 162) and the `owner`
  write, surfacing as an exit 1 indistinguishable from a cap refusal. The row
  found it, reproduced it (6 anomalies in 8 rounds), and deliberately did not
  fix it. It is `TASK-313`'s subject and a change to a file this row keeps
  byte-identical on purpose. **Fixing it here would destroy criterion 3's
  measurement.**
- Adding a retry to the register path. Settled against with arithmetic in § 3:
  serialising 20 contenders needs ≥ 114s of lock budget against the 10s
  shipped, the required budget scales with ambient load, and one uncontended
  critical section already exceeds the timeout at 11.8s.
- `test_a_reap_is_announced_and_names_the_slot_it_took` — see *Remainder*.
- Amending `TASK-341`'s correction note, which currently tells the next reader
  that `TASK-313` *is* the `2 != 3` red. § 9 shows that is wrong. It is a
  documentation defect with its own ID, and `review.md § 2` is explicit: **file
  a row, never a FAIL on this one.**
