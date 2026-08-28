# TASK-160 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-160-live-slot` · Cycle time: 22 min
> 7 files, +347/−18

## Shape (2), and shape (1) was rejected with a reason rather than a preference

> For `claude-subagent` and `opencode-subagent` **the dispatch has no OS process
> of its own** to point at, and the Task call is **synchronous** — the PMO is
> blocked inside it for the whole run, so it cannot touch a heartbeat. The one
> pid already in the marker is the **registering script's**, which exits
> immediately.

Shape (1) meant inventing a liveness channel for executors that have none, and
**getting it wrong fails toward instant slot loss — a cap that never holds**,
which is worse than the bug.

## The number is derived, and its window is closed at both ends

```
strictly above  8100s   TASK-148's 2h15m, the longest cycle measured
at or below    14400s   thresholds.in_progress_idle_hours = 4h, which the
                        schema says is calibrated against this very number
```

14400 is the top of that window. **Equality with the threshold is intended, not
a near miss**: the moment the sweep stops counting a marker is the moment
`in_progress_with_no_live_run` may name the row — **no gap either way.** All
three numbers are now read from source by `TestThresholdsAgree`, so they cannot
drift apart.

## Item 1 — the failure reproduced first, then held

Before, on a fixture: three agents live, TASK-142's marker aged to 72m →
`2 active dispatch(es)`, `total 2 / 3`, exit 0. **That is the PMO's observation
verbatim.** After, with TASK-148 also aged to its real 135m →
`3 active dispatch(es)`, `total 3 / 3`, exit 1, and a fourth register refused.

Both directions are pinned, including `test_the_old_one_hour_ttl_is_what_reaped_it`
— which reproduces the failure **against the old number**, so the file records
what was wrong rather than only that it is fixed.

## Item 2 — and the detail that makes it a real test

A marker past the TTL is still deleted and **the slot is genuinely reusable** — a
fresh `register` succeeds, not merely an uncounted file.

> The tests use the shipped default and never pass `PERRY_DISPATCH_STALE_TTL`
> in — a test that supplies its own TTL would have passed against the broken one
> too.

## What a reap now says

```
⚠️  Reaped dispatch slot: TASK-142-claude-subagent — its marker was 241m old,
past the 240m stale TTL (PERRY_DISPATCH_STALE_TTL=14400s). If that agent is
still running it no longer holds a slot, and the cap is now short by one.
```

**On every counting path, not just `list`** — because `register` is the call
where a silent reap does the damage: it is the one that decides whether one more
agent starts. stdout stays clean and parseable, asserted.

And the second half of raising a TTL: a crashed agent now holds a slot **4×
longer**, so `list` marks a marker that has outlived every measured cycle —
`• TASK-148-codex (started 200m ago — longer than any cycle measured on this
project; reaped at 240m)` — **making the hold visible before the reap line ever
prints.**

## The reader had to follow, and the reason is sharp

`bin/perry-task § live_dispatch_ids` carries its own copy of the default.

> Had only the writer moved, the reader would have the **shorter** TTL: it calls
> a marker dead while the writer still counts the slot live, so
> `in_progress_with_no_live_run` names a row an agent is actively holding — **and
> that entry's own `means` text then invites the PMO to re-dispatch onto it.**
> The exact failure the dispatch limit exists to prevent, arriving through the
> check built to catch it.

## Two files outside the stated scope, and why

Both because the change made an existing sentence **false**, not to add
behaviour: `schema/state-schema.json`'s `in_progress_idle_hours` **note** (not
its value) asserted *"PERRY_DISPATCH_STALE_TTL (default 1h)"* and condemned any
threshold *"at or below"* the TTL — which is exactly the pairing shipped. And
`schema/task-list-contract.md`'s 1.13 changelog bullet states the same
superseded invariant; it got a **forward-pointer rather than a rewrite of
shipped history.**

## It reported the baseline discrepancy too

Its own reading was **2 failures in `test_diagnose`, not 1** — and it traced the
second to `TASK-9999` in the PMO's own TASK-162 spec prose, a concrete example
id where `SKILL.md § Style rules` requires the placeholder form. Fixed by the
PMO; the remaining `TASK-007` is a **quote of real checker output** and is
TASK-165.

`test_host_support` did **not** flake — run alone, 35 tests green, and green in
both `-j 4` runs.
