# TASK-357 — the concurrent dispatch-limiter test is load-sensitive, and the assertion is the bug

Branch cut from `main` at `dda8d5f`. `BASE=$(git merge-base HEAD main)` = `dda8d5f`.

Machine: darwin 25.5.0, 14 logical CPUs, Python 3.9.6. Load applied as 16 busy-loop
shells (`while :; do :; done`), the same shape named in the row.

---

## 1. Reproduction — both halves

Test under the row:
`tests/test_host_support.py § TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
(`def` at line 184). It starts 20 concurrent `perry-dispatch-limit register`
processes behind a gate file against `PERRY_MAX_DISPATCH_TOTAL=3` and asserts
`sum(code == 0 for code, _, _ in results) == 3`.

Run at the branch base, with none of this row's code present, that one test plus its
sibling alone:

### Idle — 0 of 6 red

```
run 1: OK
run 2: OK
run 3: OK
run 4: OK
run 5: OK
run 6: OK
```

### Under 16 CPU burners — 6 of 6 red

```
run 1: RED   FAIL: test_concurrent_mixed_registers_do_not_exceed_global_cap
             AssertionError: 2 != 3
run 2: RED   AssertionError: 2 != 3
run 3: RED   AssertionError: 2 != 3
run 4: RED   AssertionError: 2 != 3
run 5: RED   AssertionError: 2 != 3
run 6: RED   AssertionError: 2 != 3
=== 6 of 6 red (under 16 burners) ===
```

The load sensitivity reproduces, and it reproduces in the direction the row
predicted: **every failure is an UNDER-count.** Across every run recorded on this
branch the winner count was 1, 2 or 3 and never 4. **The cap the test is named for
never broke.**

---

## 2. Why it under-counts — measured, not guessed

An instrumented replica of the same 20-process race, bucketing each loser by the
reason its own stderr gives:

| | winners | losers, and why | markers | wall |
|---|---|---|---|---|
| idle | 3 | 17 × `exit 1 global-cap` | 3 | 3.8s |
| idle | 3 | 17 × `exit 1 global-cap` | 3 | 4.1s |
| idle | 3 | 17 × `exit 1 global-cap` | 3 | 4.3s |
| 16 burners | 2 | 18 × `exit 2 lock-timeout` | 2 | 13.3s |
| 16 burners | 3 | 17 × `exit 2 lock-timeout` | 3 | 14.8s |
| 16 burners | 3 | 17 × `exit 2 lock-timeout` | 3 | 12.7s |
| 16 burners | 3 | 17 × `exit 2 lock-timeout` | 3 | 15.0s |
| 16 burners | 1 | 19 × `exit 2 lock-timeout` | 1 | 18.6s |
| 16 burners | 1 | 19 × `exit 2 lock-timeout` | 1 | 15.5s |

The two columns are different failures wearing the same red.

* **Idle**, every loser is refused *by the cap*: exit 1, stderr
  `❌ Global dispatch limit hit: 3 / 3 in flight`. All 20 contenders got a turn at
  the lock, so exactly 3 could win.
* **Under load**, essentially every loser is refused *by the lock*: exit 2, stderr
  `Failed to acquire dispatch marker lock after 10s`. They never reached the cap
  check at all. They are not evidence about the cap in either direction.

So the assertion `== 3` is not asserting the cap. It is asserting that all 20
contenders won the lock race within `LOCK_WAIT_TIMEOUT`, which is a statement about
the machine's schedule, not about `bin/perry-dispatch-limit`.

---

## 3. The decision: assertion, not retry — and here is the arithmetic

The row asked whether the right fix is to assert the cap is never *exceeded*, or to
make the register path genuinely retry so that the exact count becomes a promise the
tool keeps. Measured cost of **one uncontended** `register` critical section — no
competitor at all, just the lock, the stale sweep and the marker write:

```
critical section IDLE            n=10  median=0.251s  max=0.308s   mean=0.248s
critical section UNDER 16 BURNERS n=10  median=5.699s  max=11.833s  mean=6.569s
```

A 23× blow-up, because the critical section shells out roughly ten times
(`date`, `ls`, `wc`, `stat`, `basename`) and every one of those is a process spawn on
a saturated machine.

That settles it against the retry:

1. **Serializing 20 contenders needs ≥ 114s of lock budget** at the measured median,
   against the 10s `LOCK_WAIT_TIMEOUT` the tool ships. Making `== 3` a promise means
   raising the timeout by more than 11×.
2. **The required budget is a function of ambient load, not a constant.** 114s is what
   *this* machine needed at *this* load. There is no finite timeout that makes "all N
   contenders get a turn" true for arbitrary contention, so no retry budget can turn
   the exact count into a promise. It can only move the load at which the test flips.
3. **A single critical section already exceeds the timeout**: max 11.8s > 10s. One
   competitor is enough to time a waiter out under load, with no relation to the cap.
4. Raising the timeout trades directly against the reason it exists — a genuinely
   wedged lock would hang a real dispatch for that long, and this tool's whole
   history (TASK-160, TASK-211) is about dispatch bookkeeping failing quietly.

Exit 2 is also the *right* answer for a contender that could not get a turn: it is
loud, distinct from exit 1, and fails closed. Nothing over-admits. The tool is
behaving as designed; the test is asserting something the tool never promised.

**Decision: fix the assertion. Do not add a retry.**

---

## 4. But not by loosening it to `<=` and walking away

A bare `wins <= 3` is a test that barely fails: under load a genuinely broken
limiter admitting 4 could still show 2 winners and pass.

The invariant that is both exact and load-independent comes from what the lock
actually guarantees. Processes that acquire the lock are serialized, and each one
either wins (count below cap) or is refused by the cap (count at cap). So, writing
`D` for the number of contenders that **reached a cap decision** — exit 0, or exit 1
whose stderr carries the limiter's own cap message:

```
wins == min(cap, D)
```

exactly, at any load. Contenders that timed out on the lock are excluded, because
they carry no information about the cap. This is strictly stronger than `== 3`
in one direction (it also pins the `D < cap` case) and honest in the other (it never
demands that a contender which never ran must have run).

Asserted alongside it:

* `markers == wins` — every winner left exactly one marker and no marker exists
  without a winner.
* `wins >= 1` — liveness; the race cannot deadlock everyone out.
* every marker carries the executor it was registered under.

---

## 5. A real defect in `bin/perry-dispatch-limit`, found under load

Not the cap — the lock. Hunting the losers that exit for *neither* reason, over
8 rounds × 20 processes under 16 burners: **6 anomalies, concentrated in 2 rounds.**

```
--- anomalous exit 1 ---
mv: rename .../in-flight/.lock/.owner.80401.85 to .../in-flight/.lock/owner:
    No such file or directory
--- anomalous exit 1 ---
bin/perry-dispatch-limit: line 180: .../in-flight/.lock/.owner.80408.18697:
    No such file or directory
rounds=8 anomalies=6 over_counts=0
```

A process that legitimately won `mkdir "$LOCK_DIR"` (line 162) has its lock
directory removed underneath it before it can write `owner` (line 182). Under load
that window is seconds wide. Two consequences, both bad:

1. **`set -e` turns it into exit 1** — the same exit code as "cap hit". A caller
   cannot tell "the cap refused me" from "the lock protocol broke".
2. **`release_lock`'s guard has a hole in the other direction.** Its
   `[ -z "$owner" ] || [ "$owner" = "$LOCK_TOKEN" ]` test protects a *later* owner
   that has already written `owner`, but a later owner that has only done its
   `mkdir` has an empty `owner` file, so the aborting process `rmdir`s a lock
   somebody else is holding. That is the mechanism by which two processes could be
   in the critical section at once.

No over-count was observed in any run on this branch (`over_counts=0`, and every
recorded round had winners ≤ cap). So this is a latent hole, not an observed
breach — but it is the hole through which the cap would break, and it is a
different defect from the one this row fixes. **Recommend a separate row.** It
should not be fixed here: it is a change to the lock protocol in
`bin/perry-dispatch-limit`, and this row is not touching that file, deliberately,
so that the mutation in §7 measures the cap and nothing else.

---

## 6. The fix

`tests/test_host_support.py` only. `bin/perry-dispatch-limit` is **not** touched —
deliberately, so that the mutations in §7 measure the cap and nothing else.

* New `TestOpenCodeDispatchLimit.assert_cap_held(home, results, cap)` carries the
  property and the reasoning. Both contended tests call it.
* `test_concurrent_registers_do_not_exceed_opencode_cap` (cap 2) and
  `test_concurrent_mixed_registers_do_not_exceed_global_cap` (cap 3) drop
  `winners == cap` for `winners == min(cap, decided)`, `markers == winners`, and
  `winners >= 1`.
* The mixed test additionally asserts that every *cap* refusal names the **global**
  cap, since both per-executor caps are set to 20 and a per-executor refusal would
  mean the round measured the wrong limit.
* `run_contended`'s per-process `communicate(timeout=20)` becomes 180s. A contended
  round was measured at up to 42.7s under 16 burners, so 20s was itself a
  load-sensitive failure — and it fails as an `ERROR`, not a `FAIL`, which reads
  even less like a timing problem.

### One mistake worth recording

The first version of the "must name the global cap" assertion tested *every* exit-1
contender, not just the ones refused by the cap. That went red immediately, because
the lock-protocol defect in §5 also exits 1 — so the assertion re-imported exactly
the load sensitivity this row exists to remove. It now constrains only the `capped`
bucket. The classifier's third bucket is what keeps that honest: a contender that
failed for neither reason is counted as undecided rather than being quietly read as
a cap refusal.

---

## 7. The property still bites

Mutations planted in `bin/perry-dispatch-limit`, each anchored by line number **and**
an assert on the old text, with `__pycache__` cleared and a wait past the whole-second
boundary before and after, and the file restored and re-compared in a `finally`.

| mutation | contended global | contended opencode | serial global | serial per-executor |
|---|---|---|---|---|
| **M1** L330 `-ge`→`-gt` (global cap admits one extra) | **RED** `4 != 3` | green (n/a) | **RED** `0 != 1` | green (n/a) |
| **M2** L325 `-ge`→`-gt` (per-executor cap admits one extra) | green (n/a) | **RED** `3 != 2` | green (n/a) | **RED** `0 != 1` |
| **M3** L313 `acquire_lock`→`:` (no mutual exclusion) | **RED** `17 != 3` | **RED** `20 != 2` | green (n/a) | green (n/a) |

3 planted, 3 caught, **0 green**. The "green (n/a)" cells are by construction: each
mutation moves one cap, and the tests that do not exercise that cap's boundary
correctly stay green. `test_global_cap_still_wins` uses `TOTAL=1` and
`test_opencode_has_an_independent_configurable_cap` uses `OPENCODE=1`, so each pins
its own cap's arithmetic serially, with no concurrency at all.

### And the same two mutations under 16 burners

| mutation | contended global | contended opencode | serial global |
|---|---|---|---|
| **M1** global off-by-one | green — **escapes** | green (n/a) | **RED** `0 != 1` |
| **M3** no mutual exclusion | **RED** `15 != 3` | **RED** `20 != 2` | green (n/a) |

Stated plainly, because it is the honest limit of the new form: **under heavy load
the contended test cannot detect an off-by-one cap.** With only two or three
contenders reaching a decision, `min(cap, decided)` equals `decided`, and one extra
admission is invisible. Two things make that acceptable rather than a hole:

1. **No detection power was lost.** The old `== 3` was red 6-of-6 *at base* under
   this load. A test that is red whether or not the defect is present carries no
   information about the defect; it could not detect M1 under load either.
2. **The arithmetic is pinned where load cannot reach it.** `test_global_cap_still_wins`
   is serial and stayed **RED on M1 under 16 burners**. That is the right division of
   labour: the serial tests own the cap's arithmetic, the contended tests own the
   claim that the cap survives a race — and M3, the actual race defect, is caught by
   both contended tests under load, at `15 != 3` and `20 != 2`.

