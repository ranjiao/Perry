# TASK-452 — V4 round 2, 2026-09-21

Fresh-context reviewer (Claude subagent, own worktree; not the round-1 reviewer),
criteria `perry/evidence/2026-09/TASK-452-spec.md`, range
`895ecbad9a4c95834cfa881892a0e9179ba4a0d4..7791e2a9b9347ac76e788b0954ee2f9076658bc0`.
Copied by the PMO from the reviewer's returned text.

## Result

PASS. Round 1's defect is fixed: `tier1_caps` cap-checks the same
ARCHITECTURE.md the architecture section reads. No user-producible input found
on which the change does the wrong thing.

## Probe — perry-state against perry-lint, 14 scratch layouts

State root at project root; state root `perry/` with code root unset, `code`,
`code/`, `.`, absolute outside the project, missing directory, a file, the state
root itself; stale state-root copy with nothing at the code root; legacy draft,
bold-label legacy, no `Status:` and empty headers. The architecture section, the
tier-1 cap entry, cap and review-age warnings and the dashboard `🏛 Architecture`
line always named the same file; `perry-lint`'s findings named the same path and
ignored the stale copy. On a split project `OKR.md` is still measured at the
state root. Live Perry, read-only: `--section architecture` exists true, v1,
reviewed 2026-09-15, status "" (criterion 1).

## Readers enumerated

`perry-lint`, `perry-state-cost`: `lib.anchor_root`, agree by construction.
perry-state compact entry and dashboard: read the fixed payload. `perry-task`,
`perry-goals`, viewer `__main__`: call `load_snapshot` without `code_root` but
read no `arch_meta` — only `bin/perry-state` does (:1987, :2192).
`perry-lint --architecture-module`: code anchor, untouched. `test_claims`' ban on
passing `project_root` to `load_snapshot` still holds.

**Pre-existing, out of scope (note):** `bin/perry-diagnose:2641-2645` prefixes the
state root onto every schema path and ignores `"anchor": "code"`; with state
root `perry/` it lists the real root ARCHITECTURE.md as an orphan and counts a
stale `perry/ARCHITECTURE.md` as Perry's. Identical at the base; a wrong output
of a shipped tool, worth its own row.

## Mutations (line-anchored; pycache cleared, 1.2 s waits; restores checked by `bin/perry-restore-check` against 7791e2a9)

| Mutation | Result |
|---|---|
| state:1483 → `root / rel` (round 1's bug) | red, 4 |
| state:1753 → `code_root=None` | red, 4 |
| parsers:5235 → read at the state root | red, 4 |
| state:1752 → code root = project root | red, 2 |
| state:1752 → code root = state root | red, 4 |
| parsers:4038 → read `Status:` again | red, 1 |
| draft warning and `Status:` read both restored | red, 1 |
| state:1988 → threshold 100000 | red, 1 |
| state:1987 → draft warning back, alone | green (dead: status is always "") |
| state:1988 → threshold 1800 | green (180-day boundary unpinned; unchanged from base) |
| state:1483 → every tier-1 file at the code root | green (no test pins other tier-1 files at the state root; code correct per the OKR.md probe) |
| state:1988 → staleness only when the document exists | green (no behaviour change) |

Notes, none a FAIL: bold-label `**Last reviewed**:` headers parse empty (as at
base); an empty ARCHITECTURE.md reports exists false but gets a cap entry (as at
base); the test helper cannot express `..` or `~` as a code repo path.

=== VERDICT ===
task: TASK-452
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-452-spec.md
checked: Read review-constraints.md, the spec and the full diff 895ecbad..7791e2a9 (bin/perry-state, viewer/parsers.py, tests/test_parsers.py, schema/README.md). Ran `bash tests/run --tier affected --base 895ecbad…` with PERRY_HOME=worktree and PERRY_PROJECT unset: 158 modules, 4461 tests, 1 red, `test_v5_signoff.test_every_v5_close_in_the_log_still_reads` (TASK-451-integration/acceptance.md). Ran that module alone on a `git archive` copy of 895ecbad: the same single failure, so it comes from the base. Ran 12 line-anchored mutations against test_parsers with pycache cleared, a 1.2 s wait, and each restore verified by bin/perry-restore-check against 7791e2a9. Probed 14 scratch fixture layouts through perry-state --json and --dashboard and perry-lint --json. Checked OKR.md is still capped at the state root on a split project. Ran perry-state read-only on the live Perry project (--section architecture and --json). Probed perry-diagnose on a split project at the candidate and at the base. Bound: net Python/test lines = 0 (perry-state −1, parsers 0, test_parsers +1); `git diff --check` clean.
not-checked: perry-state-cost on a split fixture (it needs a git repository in scratch; covered only by the same resolver and the green test_state_cost). The viewer serve/UI readers (none in this tree; out of scope). The ≥180-day stale boundary and tier-1 placement of files other than ARCHITECTURE.md, which the tests don't pin (the mutants survived). Code repo paths through `~` expansion or symlinks. The full or slow suite (not re-run, no reason). Main after TASK-476.
proof: —
=== END VERDICT ===
