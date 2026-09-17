# F1 commitment-intake correction

New scoped follow-up commit: `ded43b71ac085039f9bb0124551297f6780e999e`
(`TASK-192: reuse explicit commitment terms at writer handoff`). Parent remains
`1867c7d54651d51f07b82b58933a019b1581270f`; no earlier delivery was amended.
Branch: `codex/okr-discussion-192-194-20260917`.

Only `goals/reference/phases.md`, `commit` → `Creating one` step 3 changed
(13 added / 4 removed lines). It now points to shared intake, reuses explicit
unchanged terms, asks only consequential missing terms one at a time with a wait,
and preserves the same three-question cap through handoff. At exhaustion it
drafts without another intake question. Unknown required fields block writes.
An exact complete explicit commit instruction still authorizes the existing
supported writer operation; prior policy, interview answers and draft edits do
not create new consent. Existing writer refusals remain in force.

F1 source: `/private/tmp/perry-scratch/planning-acceptance/20260917/assessment.md`,
F1 finding at lines 26–28. No scenario corpus was needed for this fix. The F2
phase-output contract correction from 1867 is byte-identical after this edit.

## Enumeration within the same commit subsection

| Existing related directive | Disposition |
|---|---|
| Opening: gather fields, then run the command; no hand-edited table | Unchanged; step 3 now explicitly governs intake, including when the opening instruction already supplies terms |
| Creating one step 1: refuse unsupported track/section shape | Unchanged writer prerequisite; not a request to repeat supplied terms |
| Creating one step 3: ask both party and Due unconditionally | Corrected as above; only conflicting intake directive changed |
| Creating one step 4: typed Due, pipeline ISO date, queue declared SLA first | Unchanged validation/precondition; no invented SLA or new policy consent |
| Creating one step 4: old register requires migration | Unchanged explicit writer path; no migration executed |
| Creating one step 6: print board-side handoff | Unchanged; no PMO write |
| Ending one: close requires discharge account; miss requires reason; passed Due requires miss/new promise rather than silent re-date | Unchanged lifecycle/refusal rules; no repeated-input instruction added |
| Hand-edit reconciliation: explicit accept-hand-edit behavior; diff/render/import paths | Unchanged drift/import contracts; not automatic consent or an intake-budget reset |

No other subsection/workflow, tests, schema or runtime changed. No main, PMO,
goal-state, release, host or live-project writes; no delegation, push, publication
or merge. No V4/V5, architecture PASS or task closure is awarded. TASK-191 and
other out-of-scope acceptance/decisions remain unresolved.

## Scenarios and checks

[Corrected scenarios](scenarios.md) cover complete explicit terms (zero repeat
questions), missing party/Due asked separately, and three exhausted questions
with both unknown-Due and complete-authorized alternatives. These are hypothetical
inputs and actual proposed responses, **NOT real human transcripts or automated
proof of model behavior**. No scenario executes a goal writer.

Canonical PERRY_HOME/cwd:
`/private/tmp/perry-scratch/Perry/okr-isolated-20260917/planning-discussion`.
PERRY_PROJECT/PYTHONPATH unset; TMPDIR:
`/private/tmp/perry-scratch/planning-discussion/20260917/tmp`.
[Runner wrapper](run-check.sh) records command/HEAD/date, exit and tree guard.
One suite at a time; 4 workers for modules; no full/slow.

| Check | Result | Receipt |
|---|---|---|
| Targeted: goals writer, procedure tool boundary, router budget | 3 modules / 145 tests pass, 9.1s; tree unchanged | [log](logs/targeted.log), [JSON](logs/targeted.json) |
| New committed HEAD smoke | Pass; tree unchanged | [log](logs/smoke.log) |
| New committed HEAD affected against `9051a43f78bb4e2f892c678c9b4ab54df8bfa376` | 18 modules / 595 tests pass, 22.3s; 4 workers; tree unchanged | [log](logs/affected.log), [JSON](logs/affected.json) |
| Exact single-hunk scope, parent, F2 preservation, clean tree, diff check | Pass | [integrity](logs/integrity.json) |

Targeted ran on the scoped working diff over 1867. Smoke ran once after committing:
`bash tests/run --tier smoke`. The committed affected run uses the runner's own
selector via `python3 tests/parallel --tier affected --base 9051a43f78bb4e2f892c678c9b4ab54df8bfa376 -j 4 --results <fix/logs/affected.json>`;
this preserves 4 workers, which tests/run's affected entry cannot accept directly.
Smoke plus the external tree guard supply the surrounding checks. This is not a
full-suite or merged-state verification claim.

Rubric unchanged from the actual base, SHA-256:
`399cdb615d6ae7b87c5a82f5a2e26e82d9951607b0e39ac9d5bce50465a74e88`.
Net Python/test change: 0. Implementation is ready for independent reassessment.
