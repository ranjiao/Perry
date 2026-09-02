# TASK-244 — round 2 result

> Branch: `coding/task-244-round2b`, from `coding/task-244-suite-floor` at `8829174`.
> Worktree: `.claude/worktrees/agent-adff2adaaf0acc200`. Machine: 14 CPUs, Python 3.9.6.
> **Four other agents were running suites concurrently for the whole of this round.**
> Every wall-clock figure below carries the load average it was taken at.

Round 1 was reviewed at V4 and FAILED on one line. This round repairs that line
and nothing else that round 1 got right. Status of each item is filled in as it
is earned; a line that says **NOT EARNED** is a number I could not measure, not a
number I am asserting.

## Why round 1 failed, restated so this file stands alone

`tests/test_header_rule_harness.py:1165` changed `_hits` from
`offenders_by_symbol(root)` — the whole-tree walk — to `offenders_at(root, where)`,
a single-file scan. `_hits` is the route to the net for 105 of the 111 plants, and
`offenders_at` never calls `readers_under`. So after round 1 nothing reaching the
net through `_hits` could observe a defect in the **enumeration**: not an
inference, a call graph.

Round 4's actual historical hole was an enumeration defect — *"a Python reader
outside `bin/` and `viewer/` was invisible"* — and it shipped through rounds 5,
6, 7 and 8. The corpus encodes it in `D19 planted in a SUBDIRECTORY` and
`D22 OUTSIDE 'bin/' and 'viewer/'`, and in
`test_the_control_is_caught_at_every_path_the_corpus_uses`, whose docstring says
it outright: *"otherwise 'escaped' and 'the scan never looked here' are the same
result."* Under `offenders_at` the second case is impossible by construction, so
the docstring's claim had become false of the code beneath it.

## (a) The fix — route chosen and why

*(filled in below as the work lands)*

## (b) The reviewer's mutation, re-run on this branch

*(filled in below)*

## (c) The docstring that contradicted the code

*(filled in below)*

## (d) Worktree-dependent figures, corrected

*(filled in below)*

## (e) The second beneficiary, `tests/test_one_header_rule.py`

*(filled in below)*

## Unattributed red module from round 1's run

`tests/test_host_support.py` was reported red by a previous run and believed
unrelated. Establishing whether that is a pre-existing flake is part of this
round. *(filled in below)*

## What this round refused

*(filled in below)*
