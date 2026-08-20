# TASK-121 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-121-live-state-guard` · Cycle time: ~1h15m
> 6 new files, +2637: the guard (701), its tests (419), the recorded floor,
> and three history fixtures.

## What the class IS

> A check is in it when **a value it read out of the project it lives in is
> asserted equal to a literal that enumerates or counts what that project
> happens to hold today.**

Two halves, both required:

1. **It reaches live state** — a path `schema/state-schema.json` declares Perry
   writes, resolved through `.perry/config.md`'s `State root:`, or the parsed
   payload of a `bin/` tool run inside this repo. **The path list is read out of
   the schema and never named in the guard** — instance 8's literals were about
   *which paths Perry owns*, so anything keyed on `BOARD.md` would have missed
   it. A test proves the same one-claim schema lands at `BOARD.md` in one
   project and `docs/BOARD.md` in another.
2. **Its expectation is closed** — a non-trivial constant, or a non-empty
   list/set/dict *display*. **`[]`, `{}`, `0`, `1`, `""` are not closed**:
   *"nothing is wrong"* is a property quantified over whatever the project
   holds, and it is the shape **all** of TASK-113's repairs converged on.

Half one keeps `test_prioritize`'s exact-table assertions against self-built
boards off the report; half two keeps `sum(...) == len(records)` off it.

## What it deliberately does not catch — seven items, two of them known instances

**Containment** (instance 8's `assertIn("perry/tasks.jsonl (unclaimed)", …)`) —
catching it needs a path-literal signal indistinguishable from the fixtures' own
path strings. **A live value used as INPUT** (instance 2's `TASK-038` borrowed
off the board) — the defect is in the fixture, not in an expected value. Plus
`assertTrue`/`assertFalse` on a live value, a tool's exit code and human text,
`schema/` and `SKILL.md` and `bin/` themselves, and — tried and reverted — the
repository root handed to a helper, which put 21 fixture-only assertions on the
report.

## Item 1: whole modules, checked in verbatim from history

`d90612a:tests/test_md_store.py`, `d90612a:tests/test_track_attribution.py`,
`e116f8a:tests/test_v5_signoff.py`. **Whole modules, because trimming to the
interesting class is an approximation by another name.** Byte-compared against
`git show` where reachable, SHA-256-pinned where not — CI checks out at depth 1
and would otherwise silently skip. One hit each, and all three repaired forms
are silent.

## The floor is 7, not zero — and it is judged, not silenced

**Three real instances, each owing its own row, none fixed here:**

| where | the literal |
|---|---|
| `test_md_store § test_okr` | `assertGreater(len(krs), 20)` over `perry/OKR.md` |
| `test_task_writer § …round_trips` | `assertGreater(len(rows), 5)` over the live board |
| `test_prioritize § test_an_id_shaped_word_in_prose_is_warned_about` | `ctx` built from the live task records |

The third comes with a sharper note from the agent: **its unflagged neighbour is
the more fragile half** — `fn("see ADR-006 and USER-014", ctx) == []` needs both
ids to still resolve on this board, and `[]` is not closed, so the guard says
nothing about it.

**Four named false positives**, the fourth added at merge (below).

## merge-check earned its keep on its first real use

Run on the pair `t121 × t135` before merging either:

```
BROKEN ON ITS OWN — t121 · test_live_state_expectations.py
    FAIL: test_the_floor_is_not_claimed_to_be_zero
```

Not a pair conflict — **the base had moved under the branch**, which is exactly
the defect TASK-143 named the day it landed. TASK-122's new test arrived between
this branch's baseline and the merge, taking the floor from 6 to 7.

The new hit was **classified, not silenced**: false positive, same class as the
two `test_md_store` hits already recorded — the literal `'- State root: docs'`
is the value the test wrote four lines earlier, and its only live dependency is
that the real config *has* a `- State root:` bullet, which is the shape under
test rather than a census.

## The guard found its own test

`test_the_floor_is_not_claimed_to_be_zero` read `count("instance") == 3` and
`count("false positive") == 3` — **a census of what the repository held the day
it was written**, and therefore an instance of the class the module reports. It
went red for a reason that had nothing to do with whether the guard works.

Rewritten to assert the **property**: the recorded floor matches the live sweep,
it is not empty, and **at least one entry is a real instance** — a floor of
nothing but false positives would mean the guard stopped discriminating. Proved
by blanking every verdict to `false positive` and watching it redden.

## Merged

`--no-ff` into `feat/work-modes`. Post-merge: **70 modules · 2042 tests · all
green**, `perry-lint` 0 errors, 0 rows drifted.
