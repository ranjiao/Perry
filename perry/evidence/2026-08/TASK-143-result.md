# TASK-143 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally (new workflow)
> Branch: `coding/task-143-merge-result-ci` · Cycle time: ~39 min
> 4 files, +628: `tests/merge-check` (523), `.github/workflows/merge-check.yml`
> (99), `ci.yml` (+5 comment), `AGENTS.md` (+1)

## The row's premise was wrong, and the agent established that rather than assuming it

**CI never ran for #14 or #15 at all.**

```
actions/runs?head_sha=e3f8621  →  total_count 0
actions/runs?head_sha=765b2c1  →  total_count 0
```

Verified independently by the PMO. *"Green on its own base"* was **each agent's
own local suite run, never a CI verdict.** Both PRs were non-draft and merged
cleanly, and PR #16 — created 33 seconds after #15 — **did** get a run, so
Actions was working.

**The fact is established; the cause is not, and the agent refused to guess.**

And the suspected diagnosis was wrong: `ci.yml` **already tests the merge
result** — PR #16's own log shows `+9e18354:refs/remotes/pull/16/merge`, *"Merge
96822a4e into e9d8c4dc"*. "Check out something different" would have prevented
nothing. That instruction — *do not assume the diagnosis* — is the only reason
this row did not ship a plausible no-op.

## The two real defects, neither of which is the checkout

1. The merge is computed against **the base as it stood when the event fired**,
   and GitHub never re-fires when the base moves. #14 landed on `02e61fd`, #15
   on top of #14; during this session alone `feat/work-modes` moved three times.
2. **Nothing ever tests two OPEN changes together.**

## The mechanism, and what it rejected

`tests/merge-check` merges the base tip with every candidate, runs the suite on
that tree, and **on red** re-runs the failing check three ways: the base alone
(pre-existing → nobody), each candidate alone (its own regression), and each
surviving pair. **Green apart + red together = the pair.** Happy path is one
suite run. The workflow also fires on **push to an integration branch** — the
moment a base moves under still-open PRs.

Rejected, with reasons: **file-overlap filtering** — #14 and #15 had *zero*
overlapping files, so any same-files shortcut misses precisely this case; a
`pull_request`-only job, which cannot fire when the base moves; re-running
everything on merge, which names no pair.

## Item 1, and the old mechanism run against the same commits

Reconstructed `e9d8c4dc + e3f8621 + 765b2c1`, full suite, no module named:

```
CONFLICTING PAIR — pr14 × pr15 · test_state_cost.py
```

The **old** mechanism on the same commits: `merge(base, 765b2c1)` runs
`test_state_cost` at 21 tests all green; `merge(base, e3f8621)` does not contain
the module. **Green both ways, red merged.**

Item 2: two changes to the *same tool* → `"✓ nothing new is red"`, exit 0. And
on the live base, `--pr 23 --pr 24` → *"the merged result of 2 change(s) is
green — no pair disagrees."*

## Two CI bugs found by running it, not by reading it

The workflow first checked out the base — which cannot run a checker the base
does not have yet — and `refs/pull/*/head:refs/remotes/pull/*` D/F-collides with
the `.../merge` ref `actions/checkout` already wrote. Both found live, twice
green afterwards.

## The contrast that is the argument for the whole row

On one identical tree: `tests` (ci.yml) reported **failure**; `merge-check`
reported **success — attributed to nobody**, because it baselines the base
first. `test_host_support` was red on the merged tree and, without that
baselining step, the mechanism would have blamed the only open PR.

**`ci.yml` has come back failure on essentially every PR since 2026-08-20
05:41. A check that cannot be green is not a gate.**

## Needs repository admin — stopped at saying so, as instructed

`merge-check` must be marked a **required status check** in branch protection
before it can refuse a merge. Until an admin applies it, **it reports; it cannot
block.** Stated in the script's `--help`, the workflow header and the PR body
rather than assumed.

## The most likely source of a false accusation, flagged by the agent

`test_host_support § test_concurrent_mixed_registers_do_not_exceed_global_cap`
is **load-flaky** — green 3/3 alone, red under a loaded parallel sweep. A test
that flips under load can satisfy *"green alone, red together"* by luck and name
two innocent changes.

## Merged locally

Merged with `--no-ff` into `feat/work-modes` under the workflow the user set on
2026-08-21. Post-merge suite: **68 modules · 1991 tests · all green** — the first
fully green tree in the main checkout. `perry-lint` 0 errors.
