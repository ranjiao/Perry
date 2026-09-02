# TASK-251 — spec

> Filed 2026-08-30 from the `TASK-249` rounds
> Dispatch mode: auto
> Executor: claude-subagent (one runner script, stdlib only, no MCP)
> Estimated cycle: small
> Subjective verification: (none) — the acceptance is a reproduction and a mutation
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked — evidence integrity, not a phase-003 KR
- **Verification rung**: V4

## Why

`tests/parallel` prints a failed module's stderr **truncated to its last 25
lines**, and nothing marks that anything was elided:

```python
for r in failed:
    print(f"\n\033[31m✗ {r['mod']}\033[0m")
    print("\n".join(r["err"].strip().splitlines()[-25:]))
```

The mechanism was found 2026-08-30 by the `TASK-249` agent *while retracting a
number this trap had produced*. When a module fails twice, the second failure's
`FAIL:` header survives the 25-line window and the first one's does not — so a
reader counting headers counts one failure where there were two.

**This corrupts the evidence every other row rests on.** Every spec in this
project asks the agent to report a baseline failure count and which runner
produced it, precisely because two runners disagree. A truncation that silently
drops failures makes that instruction unreliable at its source.

## Files in scope

- `tests/parallel` — the failure-reporting block, around :283-290.
- `tests/run` — only if the same number is reported there.
- `tests/` — a guard for the new behaviour.

Re-derive line numbers before editing.

## Deliverable

A reader can tell how many modules failed and how many tests failed, and cannot
mistake one number for the other. Truncation, if it remains, **says that it
truncated** and says how much it dropped.

Three numbers currently look like a failure count; the row's title says two of
the three are wrong. Name all three in your result, say which is authoritative,
and make the output distinguish them.

## Out of scope

- The tests themselves. This row is the runner's reporting.
- Making the two runners agree — that is a bigger question and not this row.
- `bin/`, `viewer/`, `schema/state-schema.json`, and any declaration file.
- Any project other than Perry's own.

## Verification

- **Reproduce first**: construct a module that fails twice, run it through the
  runner, and show the reported count disagreeing with the real one. A fix
  whose failure was never reproduced is a guess.
- After the change, the same construction reports both failures, or reports
  explicitly that output was elided and by how much.
- **Mutation**: restore the bare `[-25:]` slice and show the reproduction goes
  wrong again, with a NAMED test going red. A green mutation is a finding
  either way.
- Clear `__pycache__` and wait past the second boundary before re-running.
- `bash tests/run`: baseline failure count before and after, with the runner
  named. This row is about that number, so getting it right here is the point.
