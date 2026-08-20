# TASK-141 — result

> Date: 2026-08-21 · Executor: claude-subagent · PR: https://github.com/ranjiao/Perry/pull/26
> Branch: `coding/task-141-stale-blocked` · Cycle time: ~30 min
> Code diff **8 files, +341/−17**. `perry-task/list` **1.11 → 1.12**, with a
> `semantics` entry — because a changed *meaning* is not covered by "1.x only
> adds keys", and the suite's own `test_a_minor_bump_carries_a_semantics_entry`
> enforces that.

## Option 2, and the argument for the one it did not take

`startable` stops letting a stored status mask an empty `blocked_by`, and the
payload names the disagreement as a new `tasks[].blocked_stale`. **The stored
status is left alone** — `list` reports, it does not rewrite a cell nobody asked
it to rewrite — so a stale row still *reads* `blocked` until somebody acts. That
cost is stated in the contract.

What option 1 would have cost, in its words: it writes state the user did not
ask for, on rows the user did not name, as a side effect of closing a different
row — and verification item 4 then binds it to an event per write, so it becomes
a write-path change with a log-format obligation attached (TASK-139's shape),
not one computation. **And it fixes nothing already on disk**: boards currently
stale stay stale until each row is closed again, and any store written by hand,
imported or migrated re-creates the condition.

> They are complementary, not alternatives — if option 1 ever lands,
> `blocked_stale` is what verifies it.

## Both directions, from one payload built by the store's own writer

```
TASK-002  blocked  depends_on=['TASK-001']  blocked_by=[]           startable=True   blocked_stale=True
TASK-004  blocked  depends_on=['TASK-003']  blocked_by=['TASK-003'] startable=False  blocked_stale=False
```

On the **pre-fix** tree the same fixture reproduces the original measurement
exactly — `TASK-002 blocked_by=[] startable=False`. Item 2 satisfied against
real pre-fix code rather than a recollection.

## The mutation that matters is not the obvious one

Reverting `startable` reddened exactly the two new tests, and **not** the
open-dependency test nor either boundary test.

Then it ran the *wrong fix* — deleting the status check outright — and found
something worth keeping:

> It reddened exactly the two boundary tests (a `blocked` row declaring no
> dependency; a `review` row). **It did NOT redden the open-dependency test**,
> because that direction is guarded by `blocked_by` itself, which the wrong fix
> leaves intact.

So the test the spec leaned on for "don't just delete the check" would **not**
have caught the deletion. The boundary tests are what actually catch it.

## The spec named one line; there were two

`bin/perry-task` carries **two byte-for-byte copies** of the `startable`
computation, ~200 lines apart — `_cmd_list_from_board` (≈4506) and `cmd_list`
(≈4728). It fixed both.

**This corrects a claim recorded in TASK-094's result**, which said only the
store-backed one was reachable. Verified here: `_cmd_list_from_board` is called
at `bin/perry-task:1525`. **Both are live**, and the earlier note in
`TASK-094-dispatch-2026-08-20-1958.md` is wrong on that point.

Opened as a question by the agent: the next change to this rule has the same
two-readers-of-one-rule failure mode the contract document itself warns about.

## Live board unchanged

TASK-050 and TASK-067 still report `startable=False`, `blocked_stale=False`.
TASK-037/045 were unblocked by hand in `4c7e841`, so the live board carries no
stale row and this change is a **read no-op** on it. `git diff -- perry/` empty.

## Its diagnosis of the leftover id is wrong, and this is recorded because it matters

<!-- The id is deliberately absent from this heading. A heading naming an id is
     how `perry-explain` decides that id is DEFINED there, so an earlier draft of
     this section silently made this file the definition of an id it only
     discusses — and `test_diagnose` went red because the id then appeared in
     neither the dangling list nor the exemption list. Opened as TASK-149. -->

The agent reported the baseline `test_diagnose` red as *"`REL-00` is a truncated
match against `REL-002` in README.md/SKILL.md prose"*. **It is not.** Tested
directly:

```
a file containing only  REL-002   → harvested: ['REL-002']      no truncation
a file containing only  REL-00    → harvested: ['REL-00']       a literal
```

The real source is a **literal bare `REL-00`**, written by the PMO into
`perry/journal/2026-08/2026-08-20.md:821` inside a V5 sign-off — *"the
dangling-id check reports [] — TASK-107 resolves and REL-00 is gone"* — and
since re-quoted in TASK-113's and TASK-126's records. Same self-reference class
as `DESIGN-900` and `ZZZ-404`, not a scanner defect.

Reporting the red rather than absorbing it was right; the diagnosis attached to
it was not, and taking it at face value would have sent someone to fix a
non-existent truncation bug in `perry-explain`.

## A flake, reported not absorbed

`test_host_support § test_concurrent_mixed_registers_do_not_exceed_global_cap`
failed once under load — asserted 3 concurrent dispatches, got 2 — then passed
3/3 in isolation and in every other run. **Three agents at 4 workers each on 14
cores.** Load-sensitive, not a regression; the same shared-cache race seen on
2026-08-20.

## Contract

1.11 → 1.12 with a `semantics` entry. Key parity unchanged at 0 / 17 — the new
key was documented in the same edit. `blocked_stale` is computed on every read
and **never lands in `tasks.jsonl`**: `perry_store.record()`'s fixed `STORED`
allowlist forbids it and a test pins that. A stored copy would go stale the same
way the status did, which is the bug being fixed.
