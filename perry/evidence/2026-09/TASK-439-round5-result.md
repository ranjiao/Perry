# TASK-439 — round 5: an unreadable register is its own answer

**Rung:** V4. **Round 4 verdict:** FAIL, two findings against round 3's answer
A, plus ROW findings (`evidence/2026-09/TASK-439-round4-v4-review.md`). This is
the first FAIL since `USER-928` was answered, so `review.md § 6`'s guard allows
a round. All three fixes were specified by the verdict and needed no principle
decision.

---

## 1. F-1 — a malformed register stood the gate down, behind a false warning

Round 3 swapped the gate's `.exists()` test for `_current_store_phase`, which
reaches `parsers.load_linkage_store`. That reader returns `None` for a
**malformed** store exactly as for an **absent** one — deliberately, and
documented there: it is read-only, and `perry-lint § check_linkage_store` is
the tool that says *why* a store will not parse.

That contract is right and is **not changed**. What was wrong was reading its
three-way answer as a two-way one. Reproduced by the PMO before fixing:

| `linkage.jsonl` | `add`, neither flag |
|---|---|
| intact, KRs declared for the open phase | rc=1, refused |
| same file plus one `<<<<<<< HEAD` line | **rc=0, row filed** |

The warning it printed — "declares no key result for the current phase … the
window `score-phase` step 7 opens" — was **false in every clause** of that
project. That is the defect class this row FAILed on twice, introduced while
splitting that very sentence to avoid it.

### What landed

`_register_state(state_root)` returns one of four answers, asked once, read by
both the gate and the warning so they cannot disagree:

| state | meaning | `add`, neither flag |
|---|---|---|
| `absent` | no `linkage.jsonl` | files, warns "no register" |
| `unparseable` | file present, did not load | **refused, says so, names `perry-lint`** |
| `no-phase` | loaded, nothing for the open phase | files, warns "between phases" |
| `declared` | loaded, a KR for the open phase | refused, "pass exactly one" |

Once `exists()` is true, `None` can only be the load failing — that is the
whole of the distinction, and the shared reader keeps its contract.

**Why refuse rather than warn:** a register nobody can parse is one we cannot
ask, not one with nothing to say. A caller who passes `--kr` is not blocked —
this command only consulted the file to decide whether to ask.

## 2. F-2 — the phase match was never exercised

Deleting the phase match at `bin/perry-task:2809`, the property
`TestTheGateKeysOffThePhaseNotTheFile` is **named** for, left the module green.
The `gap()` fixture cleared `phase/CURRENT`, so the function returned at
`if not number` before the store was read. Every test returned early.

Round 4 found exactly this shape in its own guard and disclosed it; nobody —
including me — went back to look for it in round 3's.

`gap()` now points `phase/CURRENT` at `004-next`, a real phase the store has no
`kr` records for, so the store **is** read and the match **is** evaluated.
`test_the_phase_match_is_load_bearing` asserts the fixture keeps that shape:
the pointer names a phase, the store carries `kr` records, and none of them is
for 004.

## 3. ROW-3 — the third surface

`bin/README.md:438` still carried round 1's **original** wording — "is reported
by `perry-lint` for as long as it stands" — and was stale on A as well ("once
the project has a linkage register"). Round 1 enumerated two surfaces, round 4
fixed two, and there were three. Rewritten to what is now true, including the
unparseable refusal.

ROW-4 ("there is no third reader" is false — `bin/lib/__init__.py:1377`
publishes task ids store-wide) is recorded, not acted on: it does not overturn
C, which the verdict charged only at ROW.

## 4. Tests

`TestAnUnreadableRegisterIsItsOwnAnswer`, six, plus
`test_the_phase_match_is_load_bearing`. Module: **39 tests, all green.**

## 5. Mutations — four, none green

`__pycache__` cleared before every run.

| # | mutation | result |
|---|---|---|
| M1 | `unparseable` folds back into `no-phase` — round 4's F-1 | **RED** — 5 tests |
| M2 | delete the phase match — **round 4's green F-2** | **RED** — 5 tests, incl. `test_the_phase_match_is_load_bearing` |
| M3 | the unparseable refusal removed | **RED** — 5 tests |
| M4 | the refusal claims the between-phases window again | **RED** — 2 tests |

M2 is the one that matters: the same mutation the verdict ran against round 3,
now red on the test named for it.

## 6. Suite

```
130 modules · 3814 tests · 77.2s · 8 workers
✗ 3 of 3814 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.

**One note carried from the first run of this suite, which covered this row and
TASK-236's round 5 together.** It reddened
`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_registers_do_not_exceed_opencode_cap`,
which is neither row's code. Re-run alone it passed three times out of three: a
concurrency flake under the parallel runner, recorded rather than attributed.
The same run caught an unrooted hand-back in TASK-236's change, not this one's;
that is in TASK-236's round-5 result.
