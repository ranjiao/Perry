# TASK-143 — two PRs each green on their own base merged into a red tree

> Source: `.github/workflows/ci.yml`, and the merge that proved it
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — one CI job's checkout, plus whatever it takes to
>   report which pair disagreed
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Measured 2026-08-21, on the merge that had just happened

`PR #14` (TASK-100) put both store files into `claims[]` at `e3f8621`.
`PR #15` (TASK-110) shipped `tests/test_state_cost.py` asserting the
**pre-claim** world — `perry/tasks.jsonl (unclaimed)` present, and
`.perry/events.jsonl` rolling up under the `.perry/` row.

Each PR was **green on its own base.** The merged tree had **two red tests
neither PR could have seen**, and nobody found out until a human ran the suite
after the fact.

The workflow is:

```yaml
.github/workflows/ci.yml
on:
  push:      { branches: [main] }
  pull_request:
```

A `pull_request` event checks out the **merge result** by default in GitHub
Actions — so the shape of the fix is not necessarily "check out something
different". **Establish what this workflow actually tested for #14 and #15
before changing anything**; if the merge result was already what ran, the defect
is that each PR was tested against a base that then moved, and the fix is a
re-check at merge time rather than a different checkout.

**Do not assume the diagnosis. Reproduce it.**

## Deliverable

A merge into the integration branch is checked against the **merged result**,
not only against each PR's own base — and when a pair disagrees, the report says
**which pair**, not just that something is red.

Whether that is a workflow change, a job that re-runs on the branch tip, or a
required check that re-evaluates when the base moves, is yours to determine from
what you find. State the mechanism you rejected and why.

## Verification — V3

1. **Reconstruct the pair.** From this repository's history, build the two
   commits — the `claims[]` addition and the pre-claim test — and show your
   mechanism **reports red before the merge lands**, where the old one did not.
   This is the whole row; a change that cannot reproduce the original miss has
   not been shown to fix it.
2. **A pair that genuinely does not interact still passes.** Two independent
   changes must not be reported as conflicting. Without this the mechanism is
   "always re-run everything and hope", which is not a check.
3. **The report names the pair.** Not "the suite is red" — which PR's change,
   against which other, produced it. If the mechanism cannot attribute, say so
   plainly rather than shipping a signal nobody can act on.
4. `python3 tests/parallel -j 4`, `python3 bin/perry-lint`, `git diff --check`.

## Files in scope

- `.github/workflows/ci.yml`
- a helper script under `tests/` if the mechanism needs one
- documentation of the mechanism where a contributor will meet it

## Out of scope

- **`perry/` — no project state changes.** `git diff -- perry/` must end empty.
- Fixing the two `test_state_cost` assertions. They were repaired on
  `feat/work-modes` at `13cfe2f`; you are preventing the class, not that instance.
- Any change to what the suite runs, or to `tests/parallel` and `tests/run`.
- Branch protection settings and anything requiring repository admin — if the
  honest fix needs one, **say so and stop**; that is the user's to apply.
