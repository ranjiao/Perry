# Suite duration on `main`, before and after TASK-244

Both runs are `bash tests/run` in a throwaway `git worktree` under the
scratchpad, `__pycache__` cleared first, 8 workers, on the same machine within
twenty minutes of each other. The two loads are close enough to compare —
which is the only reason these two numbers may be put beside each other, and
the reason every other pair on this board may not.

| ref | what it carries | modules | tests | step 2 | exit | load at start |
|---|---|---|---|---|---|---|
| `d146c15` | TASK-247, 181, 293, 292, 258, 251 | 108 | 3031 | **313.8s** | 0 | 3.61 |
| `f3f4846` | the above **plus TASK-244 round 2** | 108 | 3034 | **106.6s** | 0 | 3.48 |

**2.94x, and the test count went up rather than down** — 3031 to 3034. Nothing
was removed to buy it.

## What the first row is not

`d49964e`, the `main` this day started on, measured **332.6s at load 9.38**
(TASK-284's round-1 reviewer, independently). The six rows merged before
TASK-244 are correctness work and bought no time: 332.6s at load 9.4 and
313.8s at load 3.6 are the same number once the load is read.

## Where the time was

99.0% of `tests/test_header_rule_harness.py` was 112 whole-tree scans, one per
corpus entry: `_hits` asked what the net reported about ONE planted file and
threw away everything the walk said about the other readers. The module was
265.996s and 260.74s in two independent measurements at `d49964e`.

`.claude/worktrees` is why the scans cost what they did. The census resolves to
a law, verified by prediction-then-measurement at 27 worktrees by TASK-244's
round-2 reviewer:

    readers      = 19 + 20 x worktrees      559 measured, 559 predicted
    header_sites = 75 x (worktrees + 1)    2100 measured, 2100 predicted

So every figure ever recorded for this census — 1350 at 17, 1800 at 23, 2025 at
26 — was a correct reading of a different day. **None of them is a constant and
none of them was wrong.**

## What this measurement does not establish

- **No full-suite ranking exists on pre-TASK-244 code.** Neither round nor
  either reviewer produced one; the "before" is established at module
  granularity three ways. TASK-244's round-2 reviewer flagged this rather than
  failing on it and wrote down why it judged the gap survivable.
- **`tests/durations.json` still describes a tree that does not exist** — 103
  keys against 108 modules, two of them deleted, the harness recorded 10x low.
  It was already stale at `d49964e`. TASK-304 is that row and its V4 review is
  running; nothing here rests on that file.
- **The floor moved rather than disappeared.** `tests/test_tree_guard.py` is
  now the longest module at 48-124s, and its cost is TASK-258's fix doing its
  job. TASK-312 is that row.
