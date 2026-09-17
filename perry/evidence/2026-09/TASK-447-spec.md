# TASK-447 — Next action fits a 400-character pointer

Date: 2026-09-17. Owner: Coding Agent plus PMO for live task records. Priority: P2. Required verification: V3.
> Touches architecture: existing lexical length guide and tool-mediated PMO text.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: (none); PMO checks proposed summaries against preserved source before applying
> Deployed: no

Authorization: USER-957 and phase 004 O3; existing TASK-447 journal acceptance. No schema/claim edit, new hard write gate, or goal restatement.

## Deliverable

Change the existing next-action-oversized linter guide to 400 Unicode characters and describe its unit accurately. Move the long live accounts to evidence, leaving concise actionable pointers in task Next action cells through perry-task. Preserve all original text.

## Acceptance criteria

1. A 400-character Next action produces no oversized finding; 401 produces one. Exercise ASCII and Chinese strings so the unit is character count, not UTF-8 byte count. Existing warning severity and unrelated guides are unchanged.
2. Reverting the 400 threshold to 1000 makes the boundary regression fail. Candidate targeted tests, smoke and affected tier pass.
3. For the live task-list read contract, every migrated original is retained verbatim in a per-task evidence section. Replacement text keeps the actual unresolved next step, blockers and relevant verification/commit reference, and is at most 400 characters including its evidence pointer. No assertion of completion is invented.
4. After PMO applies approved proposals through perry-task, re-read the live contract and record p90 at or below 400 characters with the measurement method and command. Concurrently changed rows must be re-read and re-summarized, not overwritten using stale text.

## Files in scope

Coding: bin/perry-lint existing length constant, adjacent explanation/output unit; existing tests/test_summary_is_asked_for.py boundary coverage. External scratch only: proposed migration JSON and original-text evidence draft from the supplied live task-list snapshot.

PMO: perry/evidence/2026-09/TASK-447-next-action-accounts.md and acceptance receipt; live Next action fields only through bin/perry-task, plus normal tool-generated journal/events. Coding must not edit live or copied PMO stores or commit PMO evidence.

## Bound

One lexical warning threshold, four boundary fixtures (ASCII/Chinese, 400/401), and the 33 currently oversized rows in the 2026-09-17 supplied contract snapshot (100 open rows; nearest-rank p90 1,672; maximum 2,218). A row changed since that snapshot is explicitly reconciled. Preserve evidence links and pending user approvals. No new task, goal metric/check declaration, semantic classifier, schema field, or write-time length refusal.

## Verification

Pinned base and immutable coding commit; actual committed affected selection, smoke, named 400/401 tests and reverting-threshold proof. PMO compares source text exactly before each write and measures after from perry-task list --json. Report coding tests separately from the live migration. Use canonical PERRY_HOME, unset PERRY_PROJECT, fresh TMPDIR and four workers. No full suite duplication during coding; integrator owns merged full/slow gates.

## Out of scope

Erasing original prose, silently marking any task done, changing asks, guessing KR attribution, goal declarations, schema claim surface, foreign projects, release allocation, publication, and main integration. Coding commits only its two code/test paths; the PMO applies state changes after reviewing the proposal.

## Integration discovery and bounded repair — 2026-09-17

The first combined full gate ran 4,299 tests and found two failures already present in its PMO-updated base. They are owned by this continuation, not waived as unrelated baseline defects. One is tests/test_board_from_declarations.py::TestThisProjectsStores.test_the_longest_next_action_is_whole, whose anti-vacuity condition requires a real open action >=1,000 bytes; the now-accepted migration makes all 99 shorter than 400 characters. Extend coding scope by this one existing test module: preserve the >1,000-byte non-truncation proof in an isolated deterministic fixture, while retaining whole-cell checks on real store values. Do not weaken/delete that proof or recreate a long live action to satisfy it. Show a bounded truncation mutation turns the isolated proof red, exact restore green, targeted and committed affected selection pass. Aggregate Python/test net remains <=0. This is the same unintegrated delivery, not a second version allocation.

The second failure comes from newly archived synthetic USER identifiers written as unquoted prose. PMO owns its repair: quote the fixture/report excerpts using the existing documented quotation semantics, retain the exact original Markdown in a JSON exhibit, and verify the real dangling-ID assertion. Do not change the diagnostic, create fake USER records or waive unknown identifiers. The first failed candidate/ref and full output remain preserved; acceptance requires a new fixed-base full/slow receipt.
