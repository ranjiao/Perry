# TASK-230 — the full suite takes eleven minutes, and that cost has started changing behaviour

> Dispatch mode: manual
> Executor: manual — the first half is measurement, and the second half changes how every other row is verified. A runner that reports a wrong verdict is worse than a slow one.
> Estimated cycle: medium
> Subjective verification: whether a parallel-only failure is a real contention bug or a runner defect — the runner cannot tell you
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V3
- **Dependencies**: —
- **KR linkage**: unlinked — serves no phase #003 KR (they are all store-and-code)

## Why now

**The suite's cost stopped being a nuisance and started producing wrong
outcomes.** On 2026-08-28 two dispatches were sent to `claude-subagent`. Both
did substantial, correct work. Both were killed by a 600-second no-progress
watchdog **at the moment they kicked off the full suite** — TASK-209's last
words were *"Now the full suite. Let me kick it off in the background"*;
TASK-095's were *"Now the V3 mutation step"*. Neither reached a commit or a PR,
and the PMO had to verify and commit their work by hand.

A second signal predates that. The journal records `test_host_support` flaking
**three times under suite contention**, passing 3/3 every time it is run alone,
with merge-check refusing to attribute it once and TASK-147's sweep excluding
it. That is a test already sensitive to how the suite is run.

## Measured baseline, 2026-08-28

| | |
|---|---|
| Wall time, full serial run | **~11 minutes** (18:11 → 18:22, this session) |
| Test files | 91 |
| Test functions | 2793 |
| Files spawning subprocesses | **76 of 91** |
| `subprocess.run` / `check_output` call sites | **276** |
| Cores available | 14 |

≈ 0.24s per test, which is what a suite dominated by process spawns costs. The
time is in `fork` + real filesystem work, not in computation.

## Can it be parallelised? Measured, not assumed

**The hazards were checked, and the tree is in better shape than expected:**

- **No test writes into the live repository.** Searched for writes through
  `PERRY_HOME` / `REPO_ROOT`; zero hits. Tests read the real repo and write into
  temporary directories.
- **68 of 91 files use `TemporaryDirectory` / `mkdtemp`** — isolated by
  construction.
- **The other 23 are static contract checks** — `test_ownership.py`,
  `test_claims.py`, `test_i18n.py`, `test_entrance.py`,
  `test_contract_invariance.py` and similar. They read repository files and
  assert properties. Read-only sharing across processes is safe.
- The work is **process-bound, not GIL-bound**, so multiple processes give a
  near-linear win where serial spawning gives none.

**The blocker is tooling, and it is a declared decision.** `pytest` and
`pytest-xdist` are both **not installed** (Python 3.9.6, Xcode's). Phase #003's
Cost Ceiling reads *"Perry is stdlib Python and stays that way. A dependency is
a decision, not an implementation detail."* So the default path is a
**stdlib-only runner** — `unittest` + `concurrent.futures` — sharding by test
**file**, not by test, because file is the isolation boundary the existing
fixtures already assume.

**Shard by file, never by test method.** Several files build a fixture once per
class; splitting a class across workers would rebuild or race it.

## Deliverable

1. **A ranked per-file wall-time breakdown.** Eleven minutes is an aggregate;
   nobody has looked at where it goes. It is entirely possible that a handful of
   files hold most of it, in which case fixing those beats parallelising
   everything.
2. **A stdlib parallel runner** that shards files across processes and merges
   results into one verdict. Target: a routine full run **under two minutes** on
   14 cores.

## Verification — V3, and the pass/fail SET is the gate, not the clock

1. **Record the serial baseline**: total wall time **and the exact set of
   passing test ids**.
2. **The sharded run must produce the identical set.** A test that passes
   serially and fails in parallel is a **contention bug the sharding exposed** —
   it is reported and fixed, never retried away. `test_host_support` is the
   known candidate and the reason this clause exists.
3. **Run the sharded suite five times; the set must be stable across all five.**
   A parallel runner that is right four times in five is a worse gate than a
   slow one that is right every time.
4. **Report the measured speedup, not the theoretical one.**

## Out of scope

- Deleting or skipping tests to make the number smaller. The suite is slow
  because it spawns real processes and asserts against real files, and that is
  the discipline that catches what this project keeps catching — six times
  today alone, in the *"a gate covers a different surface than it claims"*
  pattern.
- Adding `pytest` / `pytest-xdist`. If the stdlib runner proves genuinely
  inadequate, that is a **user decision** under the Cost Ceiling, raised as one,
  not slipped in as an implementation detail.
