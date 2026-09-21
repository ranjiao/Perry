# TASK-452 — V4 round 1, 2026-09-21

Fresh-context reviewer (Claude subagent, own worktree), criteria
`perry/evidence/2026-09/TASK-452-spec.md`, range
`895ecbad9a4c95834cfa881892a0e9179ba4a0d4..1f90d40ca9aff9f2132c1f1e6d3c0f6992d572f7`.
Copied by the PMO from the reviewer's returned text (subagents cannot write files).

## Finding (behaviour)

`bin/perry-state:1483` — `tier1_caps` builds `root / rel` for `ARCHITECTURE.md`
with `root` = the state root (called at `:1933`). The change moved the
architecture section to the code root and left this reader behind, so one
payload describes two files:

- state-root copy present, code-root document absent: `architecture.exists`
  false, while `operations.tier1_caps` reports the state-root file (449 lines on
  a Perry copy) and warns over-cap past 500 lines about a document it says does
  not exist;
- a 600-line code-root document: `exists: true`, no cap entry, no warning — on
  Perry itself the real document's 500-line cap is never checked.

At 895ecbad both readers used the state root and agreed; the change split them,
against criterion 2 ("without silently substituting the state-root document").

## Readers of the document, enumerated

| Reader | Location | Status |
|---|---|---|
| `perry-state` architecture section (`load_snapshot(code_root=…)`) | code root | correct |
| `perry-state` `tier1_caps` | state root | **defect** |
| `perry-lint` (`lib.anchor_root`, :4993, :5706) | code root | correct |
| `perry-state-cost` (`lib.anchor_root`, :251) | code root | correct |
| `perry-task` (:6722, :8345), `perry-goals` (:1215), `viewer/parsers.py __main__` | state root, no `code_root` | output no architecture data today |
| `perry-diagnose` | path globs only | no content read |

No code or `schema/*-contract.md` branches on the architecture `status`, so
`status: ""` breaks no consumer.

## Passed

Criterion 1 on Perry and on a copy with the root removed; `code_repo_path`
relative, absolute, `./code/`, empty, missing directory, `~/nonexistent`, a
file, `../sibling` behave as A1's resolver defines; draft header parses with
`status: ""` and no warning; 2020 review warns, today does not, garbage does
not; Bound net −3 (+50/−53); `git diff --check` clean. Affected tier at
1f90d40c: 162/162 selected, 158 modules / 4,461 tests, the only red
`test_v5_signoff` (base red, TASK-476).

## Mutations (scratch copy; restores `cmp` against `git show 1f90d40c:<path>`)

Red: M1 parsers back to state root; M2 no `code_root` passed; M3b parsers reads
`Status:` again; M4 stale threshold disabled; M6 `anchor_root` ignores
`code_repo_path`; M7 fall back to the state-root copy. Green: M3a restoring only
perry-state's draft warning (dead code — status is always ""; criterion 4 holds
through M3b); M5 restoring the `exists` guard around ageing (no behaviour change).

## Notes, not failures

`IsADirectoryError` when `ARCHITECTURE.md` is a directory (predates the change);
the decoy subtest reuses the stale case's text; docs still describing a draft
window: `packs/software-ops/architecture.md:190`,
`work/state/ARCHITECTURE_TEMPLATE.md:6`, `decide/state/design_TEMPLATE.md:3`
(outside this row). The reviewer checked out the head in its own worktree as
briefed, although `review-constraints.md` forbids `git checkout`.

=== VERDICT ===
task: TASK-452
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-452-spec.md
checked: read the diff 895ecbad..1f90d40c, lib.anchor_root and every load_snapshot/ARCHITECTURE.md reader in bin/ and viewer/ (enumerated by git grep); ran perry-state --json (PERRY_HOME set, PERRY_PROJECT unset) on Perry and on scratch fixtures covering single root, split code root, missing code-root doc with state-root decoy, unset code root, absolute/relative/./code//missing/~/file/../sibling code_repo_path, empty doc, draft header, no-Status header, fresh/stale/garbage review dates, 600-line decoy, 600-line root doc; on a scratch copy of Perry with root ARCHITECTURE.md moved to perry/; ran `bash tests/run --tier affected --base 895ecbad…` (only red test_v5_signoff, confirmed red alone on a base archive copy); ran 8 line-anchored mutations (M1-M7 incl. M3a/M3b) on an archive copy, clearing __pycache__ and waiting 1.2s each, with restores checked by cmp against git show 1f90d40c:<path>; git diff --numstat (Python/test net -3) and --check
not-checked: perry-restore-check itself (refuses a non-git copy; restores checked by hand with cmp instead); test_v5_signoff at base was run in a git-archive copy, not a git checkout; no full or slow suite; the viewer HTML/serve path (none exists under viewer/); perry-task/perry-goals architecture reads beyond confirming they output no arch_meta; skill/pack docs that still describe a draft window were only grepped; behaviour on Windows or case-insensitive path variants
proof: bin/perry-state:1483 (tier1_caps builds `path = root / rel` for "ARCHITECTURE.md" with root = state root, called at bin/perry-state:1933); input: a project whose state-root perry/ARCHITECTURE.md is present and whose code-root ARCHITECTURE.md is absent gives architecture.exists false while operations.tier1_caps reports the state-root file (449 lines on a Perry copy) and warns over-cap when it exceeds 500 lines; a 600-line code-root document gives no cap entry and no warning
=== END VERDICT ===
