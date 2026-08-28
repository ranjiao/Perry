# TASK-040 — the risks write path (second half)

**Merged locally 2026-08-21** from `coding/task-040-risks-write` @ `6a9da46`.
`merge-check` alone and alongside TASK-045: nothing new is red.
Post-merge suite, `/usr/bin/python3 tests/parallel -j 4`:
**80 modules · 2331 tests · 2 red**, both pre-existing.

The first half is `TASK-040-result.md`. The substance of this half — including
the five things the spec got wrong about today's code — is in the merge commit.

## Verified independently

- `perry/`, `schema/` and TASK-045's five tools all untouched.
- `RISK_STORE_NO_WRITE_PATH` and `risk_store_refusal` gone (grep count 0).
- `RISK_STORE_UNDECLARED` survives as a **live** guard at `bin/perry-tasks:509`
  — `if not risk_store_is_declared()` — so withdrawing the `claims[]` entry
  switches the command off rather than leaving a stale message behind.
- The import run on a throwaway copy of this project's board:
  `wrote risks.jsonl (4 risk record(s))`, then `risks-diff` →
  `identical: true`, `source: "store"`, `cells_verbatim: {}`.

## Not reproduced here, and it is the operational one

The agent measured that after an import, `perry-task risk-add` produces a drift
warning, because `risk-add` writes the board and the event log and **not**
`risks.jsonl`. My own attempt hit the conformance gate first — the throwaway
fixture was not declared, so `risk-add` refused and nothing was added. The
finding is taken on the agent's measurement, and it holds a fortiori on a
**declared** project, which is what `perry/` is.

**Do not migrate this project's own risks until `risk-add` / `risk-clear` write
the store.** Filed as a follow-up row.
