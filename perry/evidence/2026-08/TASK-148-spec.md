# TASK-148 — two byte-identical copies of the startable rule, 200 lines apart

> Source: `perry/evidence/2026-08/TASK-141-dispatch-2026-08-21-result.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — it removes a second statement of one rule
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Measured, twice, by two different rows

`bin/perry-task` states the `startable` rule in two places:

| where | function |
|---|---|
| ≈ line 4506 | `_cmd_list_from_board` |
| ≈ line 4728 | `cmd_list` |

**Both are reachable.** `_cmd_list_from_board` is called at
`bin/perry-task:1525` — verified. TASK-127's record originally called the
board-era path *dead*; that claim is wrong and has been corrected in place.

TASK-141 had to fix the rule and found it had to fix it **twice**. That is the
two-readers-of-one-rule failure mode `schema/task-list-contract.md` warns about
in its own prose, inside the tool the contract describes.

## Deliverable

The rule is stated **once** and both list paths call it. Changing it in the one
place changes both payloads.

The rule as it now stands, after TASK-141:

> open, and not itself waiting, and nothing unsatisfied under it — where a
> stored `blocked` no longer masks an empty `blocked_by`, and `blocked_stale`
> names the disagreement.

**Do not change the rule.** This row moves it; TASK-141 decided it, three days
of argument are recorded in its evidence, and a behaviour change smuggled into a
de-duplication is the hardest kind to review.

## Verification — V3

1. **Byte-for-byte identical payloads.** For this repository and for at least
   one fixture project, `perry-task list --json` before and after your change
   differs in **nothing** — diff the payloads, do not eyeball them. The same for
   the board-derived path, which needs a project with no store to reach.
2. **Both callers actually exercised.** A test reaches `_cmd_list_from_board`
   (a project with no store) and `cmd_list` (a project with one) and asserts
   both report the same `startable` / `blocked_stale` for the same graph. If you
   cannot reach one of them from a test, say so — an unreachable path is a
   different finding and a bigger one.
3. **A second copy cannot come back.** A guard fails if the rule's shape appears
   more than once in `bin/`. Prove it by re-introducing a copy and watching it
   redden, then removing it.
4. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `bin/perry-task`
- `bin/lib/__init__.py` if the shared home belongs there — its own docstring
  argues for exactly that, and TASK-120 put `kr_progress_provenance` there for
  the same reason
- focused tests

## Out of scope

- **Changing what `startable` or `blocked_stale` mean.** Move the rule; do not
  edit it.
- `conformance.blocked_without_dependency` and TASK-142's stranded-row checks.
- The contract version — moving an implementation changes no payload, so there
  is nothing to bump. **If you find yourself needing a bump, the payload moved
  and item 1 has failed.**
