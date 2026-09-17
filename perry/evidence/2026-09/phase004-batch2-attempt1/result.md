# Phase 004 batch 2 integration support result

Status: BLOCKED by required full gate; stopped without repairs or retry.

## Immutable identity

- Base / unchanged main: `73d551d8130d0e1c1814731c8ddc26d93e4d72ff`
- Integration branch: `codex/integrate-phase004-batch2-20260917`
- Frozen ref: `codex/phase004-batch2-gate-input-20260917` → `4256184ea6cef9edfc93bfca9d2debc8a1e934ed` (unchanged)
- Allocation commit / final head: `4256184ea6cef9edfc93bfca9d2debc8a1e934ed`
- Tested full merge tree: `e66495752f60f89ec4377315d604e35cd06ce871`
- No duration artifact commit exists: full failed before the import condition.
- integrated-to-main: false
- unpublished: true; no push, tag, release publication, task closure or V5 award.

## Allocations and release checks

| Version | Task | Delivery |
|---|---|---|
| 0.1.6 | TASK-447 | TASK-447-next-action-400-20260917 |
| 0.1.7 | TASK-455 | TASK-455-independent-architecture-review-20260917 |
| 0.1.8 | TASK-446 | TASK-446-one-screen-snapshot-20260917 |

All three allocations: patch, phase `004-guided`, date `2026-09-17`, integrator `pmo-agent`. Authored notes are in external `release-notes-yveycx2d/`; allocation used `release/manage.py`. Only release/records.jsonl, VERSION and CHANGELOG.md were committed by this session. Existing record bytes are an exact prefix of the final ledger. Expected start version was verified as 0.1.5; final version is 0.1.8.

- `release/manage.py check --base <base> --ref HEAD`: PASS; `release-base.log`.
- `release/manage.py check --tag v0.1.8 --ref HEAD`: PASS; `release-version.log`. This check created no tag.
- `git diff --check <base> <head>`: PASS; final worktree and index clean (`final-status.txt`).

## Required gates

The exact requested full command ran once, with four workers, all three environment variables unset and fresh canonical TMPDIR (`full-environment.txt`). Complete output: `full.log`; exit: `full-exit.txt` = 1.

Full: FAIL, 154 modules / 4,299 tests / 261.7 seconds; 2 failing tests in 2 modules. Syntax/help, template/fixture lint and tree-guard stages report exit 0. The command completed its built-in base attribution and found both failing modules pre-existing on the base; that does not permit acceptance. No extra full run or manual diagnostic retry was started.

Exact failures:

1. `test_board_from_declarations.TestThisProjectsStores.test_the_longest_next_action_is_whole`, tests/test_board_from_declarations.py:396:
   `AssertionError: 377 not greater than or equal to 1000 : the live store has no long next action to check`
2. `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`, tests/test_diagnose.py:708:
   `AssertionError: Lists differ: ['USER-005', 'USER-006', 'USER-101', 'USER-102', 'USER-103'] != []`

Receipt verification: NOT RUN / unavailable. The failed gate emitted neither merged-full/receipt.json nor merged-full/durations.json. tests/durations.json is byte-identical to base. No artifact was imported or committed.

Slow: NOT RUN, zero tests executed; intentionally stopped on full failure as instructed. No slow.log or slow-results.json is claimed.

## Exact-candidate architecture selection facts

This records integration facts, not an independent architecture verdict. Bound to the final head above (which remains the allocation commit because no successful durations artifact exists). Evidence includes `name-status.txt`, `modes.txt`, `summary.txt`, `full.diff`, both complete tree inventories, both top-level-directory lists and `contract-context-objects.json`. The root component index is byte-identical at base/head.

| Trigger class | Fact | Evidence |
|---|---|---|
| Listed boundary paths | false | No change to viewer/parsers.py, bin/lib/, schema/, root SKILL.md or goals/work/decide SKILL.md. Full name-status has only the eight delivered paths plus three release projections. |
| New top-level directory | false | Exact base/head top-level directory lists are equal. |
| New bin executable | false | bin/perry-lint is modified with mode 100755 at both ends; no added/renamed executable or mode gain. modes.txt and both inventories; summary.txt is empty. |
| Contract-version change | false | Root §5 remains task-list 2.4. Schema contract declarations remain tasks 2.4, decide 2.2, goals 3.5, asks/events 1.4, knowledge 1.3, next 1.0 and roles 1.1. Schema tree and executable declaration files have identical Git objects. VERSION 0.1.5 → 0.1.8 is the product release, not an API contract-version change. |
| Root architecture edit | false | ARCHITECTURE.md blob is identical at base/head. |
| Module architecture edit | unknown (incomplete module context) | Known bin/ARCHITECTURE.md and interim DESIGN-017 §5.4 module are unchanged. Root §2 supplies no tests module document and identifies release/README.md as a procedure, not a module document. A complete touched-module mapping is not confirmed; absence is not silently treated as false. |

Component mapping from unchanged ARCHITECTURE.md §2:

- bin/perry-lint → bin component, lines 59–73 → bin/ARCHITECTURE.md (unchanged).
- work/reference/*, reference/*, packs/software-ops/architecture.md → lanes and shipped skill prose, lines 100–127 → DESIGN-017 §5.4 interim module, explicitly designated at lines 356–358 of that design (unchanged). The software-ops architecture page is a shipped procedure, not the root or bin module architecture document.
- tests/test_spec_scannability.py and tests/test_summary_is_asked_for.py → tests, lines 129–132 → no module document named; unresolved.
- release/records.jsonl, VERSION, CHANGELOG.md → release, lines 75–81 → release/README.md procedure exists; no explicit module document designated; unresolved.

Architecture acceptance: unresolved; no independent PASS awarded. PMO owns resolution of missing module context and any needed fresh exact-candidate architecture review. Individual TASK-455/TASK-446 reviews are not a review of this combined integration candidate. Do not reuse this selection for a changed head; a future durations-only commit also requires rebinding.

## Accepted delivery evidence and scope

Read current-tree TASK-455-review/review.md, TASK-446-review/review.md, TASK-447-live-acceptance.md and all three delivery/result.md files under perry/evidence/2026-09/. Their acceptance is input evidence, not a waiver of the failed combined gate. Startup recovery was nonblocking; interrupted was empty. No conflict adjustment, PMO edit, product fix, architecture edit, delegation, main merge or publication was performed.
