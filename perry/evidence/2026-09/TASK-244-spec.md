# TASK-244 — spec

> Dispatch mode: manual — the gate refused on a false positive; the user is the escalation it demands.
> Executor: claude-subagent, run through `delegate`.
>
> `--escalation-scan` returns `verdict: refuse`, `refuse: ['setup']`, matching
> the word **setup** in "the harness re-does setup per test" — an ordinary
> English noun, not the `/perry setup` installer the hook means. That is the
> `TASK-290` class exactly: the gate matching a word rather than an intent.
>
> **The spec was not reworded.** Saying "fixture construction" instead would
> read as more precise and would still be rewording to pass, which
> `.perry/hook.md` names as the one thing a gate must never reward — the motive
> does not change what it is. The user instructed the dispatch on 2026-09-02
> after being shown the live 18m48s measurement, and that instruction is the
> escalation the refusal exists to force. It covers this row only.
> Estimated cycle: large
> Subjective verification: whether the coverage the slow module buys is worth what it costs — a human decides that, not the agent
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: — (`TASK-230` is done)
- **KR linkage**: declared unlinked — developer throughput, no phase-003 KR covers it
- **Verification rung**: V4

## Why this is P0, and why the row's own premise is stale

The user reports 2026-09-02 that test runtime is badly slowing development.

**This row was filed against the wrong module.** It says the floor is
`test_task_writer.py` at 105-149s. Measured live on 2026-09-02, on a quiet
machine, mid-run:

```
$ ps -p <pid> -o etime,time,command
ELAPSED   TIME       COMMAND
20:46     18:48.33   python3 -m unittest discover -s tests -p test_header_rule_harness.py -v
```

`tests/test_header_rule_harness.py` — **1,476 lines, 13 tests, 18m48s of CPU
and still running.** Roughly 90 seconds of CPU per test. Every other module in
the suite had finished; this one was the last worker alive.

`TASK-230` established the shape and it still holds: *"the run cannot finish
before its longest single module does"*, and its `--times` run measured the
suite finishing **0.02 seconds** after its longest module. So the floor is real
and the schedule is already optimal. What changed is **which module owns the
floor, and by how much** — 105-149s is a two-minute target's whole margin;
18m48s is a different problem.

## Files in scope

- `tests/test_header_rule_harness.py` — the binding module.
- `tests/parallel` — only if per-module timing needs a surface it lacks.
- Any module your own measurement shows is also over the line.

**Do not touch what the tests are testing.** The header rule and its guard are
`TASK-050`'s product, hard-won over eleven rounds; this row is about what the
harness costs, not about weakening it.

## Deliverable

**The suite's wall-clock stops being owned by one module.** Concretely, and in
this order:

1. **Measure first, per module.** `bash tests/run --times` or the equivalent —
   `TASK-230` left a timing surface; use it. Produce the ranked list. Confirm or
   correct the 18m48s figure and say which module is actually binding.
2. **Find where the time goes inside that module**, at test granularity. 13
   tests and ~90s each is a shape — is it one test, or all thirteen?
3. **Then cut it**, by whichever of these the measurement supports:
   - the harness re-does setup per test that could be done once;
   - it copies or archives a tree per test (`TASK-258` just made `copy_repo`
     4.6× faster by switching `copytree` to `git archive` — check whether this
     harness has the same shape);
   - the module can be split so workers can share it (`TASK-230` scoped
     sharding-below-the-file out and named it as this row's job);
   - a subset of the 13 is redundant.

**Cutting coverage is not the default.** If the answer is "these 13 tests are
worth 20 minutes", say so with the measurement and stop — that is a legitimate
result and it belongs to the user, not to you.

## Out of scope

- Making the two runners agree, and `tests/run`'s failure counts (`TASK-251`).
- `test_task_writer.py`, unless your ranking shows it still matters.
- Any project other than Perry's own.
- Weakening the header-rule guard `TASK-050` built.

## Verification

- **A quiet machine, and prove it was quiet.** Report load average and the
  worker count at start and end. Today's figures on this repository range from
  15s to 283s for the *same module* depending on load, and four agents running
  suites concurrently produced 250-950s full runs. A timing claim without a
  load figure is not evidence.
- Before and after, on the same quiet machine: total wall, and the ranked
  per-module list. Both numbers, both runs.
- **The suite still finds what it found.** Same tests pass, same tests fail.
  Name the baseline failure set explicitly — do not report "no new failures"
  without saying what the old ones were.
- **Mutation, and it is the acceptance**: break the header rule the harness
  guards and the harness must still go red. A faster harness that stopped
  catching the thing is the failure mode, and `TASK-050` spent eleven rounds
  on exactly that class.
- Clear `__pycache__` and wait past the second boundary before each re-run.

## Bound

**One module, one measurement, one cut.** Size 3:

1. the ranked per-module timing list, before and after;
2. `tests/test_header_rule_harness.py`'s internal profile at test granularity;
3. the change, plus the mutation proving the guard still goes red.

A second slow module your ranking exposes is a **new row**, recorded and left —
unless it is within a few percent of the binding one, in which case say so and
ask. The round ends when the binding module no longer owns the floor.

### Correction, 2026-09-02 — the dispatcher widened this in a message and the two disagreed

A message sent mid-run said *"a fix that leaves the other 107 at 286s has not
finished the job"* and called the other tree-walkers in scope. **That
contradicted this Bound, and this Bound wins.** `review.md § 1` says an
unbounded criterion does not fail a round, it fails to END one; a contradictory
one is worse, because the reviewer cannot tell which bar applies.

The split, stated once:

- **This row is the binding module's cost.** Fix
  `tests/test_header_rule_harness.py`. If `git archive` is the answer, note that
  it excludes `.claude/worktrees` **by construction** — it sees tracked files
  only — so the ten-repositories problem is solved for this module as a side
  effect rather than as a separate change.
- **`TASK-303` is the same root across the other 32 tree-walking modules**, and
  it also carries the correctness half: `test_header_index_is_the_only_fold` is
  red because it counted 270 reader sites inside agent worktrees.

So: **measure the other tree-walkers and report what they cost — that number is
wanted and belongs in your ranked list — but do not fix them here.** Handing
`TASK-303` a measured population is worth more than half-doing it.

The 286s figure is the target `TASK-303` is judged against, not this row.
