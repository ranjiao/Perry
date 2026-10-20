---
adoption: 1
stage: scan
updated: "{{actual UTC timestamp}}"
---

# Adoption dossier — {{project name}}

Root-owned workflow record at `.perry/adoption/<date>-dossier.md`. Follow
`$PERRY_HOME/reference/adoption.md` and `adoption-sources.md`. Native items and
attachments are materialized by their owning lanes; this dossier is not a store.
Replace placeholders and omit unused example rows before saving.

## Agreed scope

- Absolute project/code roots and document root: {{actual paths}}
- Depth and selected subjects: {{quick/standard/deep; goals/tasks/designs/decisions/knowledge/architecture}}
- Existing native state and prior dossier: {{observed identity or unresolved setup condition}}
- Actual user instruction and boundaries: {{reference and exact scope}}

## Sources and observations

| Source reference | Kind / trust tier | Read scope and date | Observed fact, quote or unavailable input |
|---|---|---|---|
| {{reopenable path/lines, commit or external source}} | {{kind; A/B/C}} | {{what was actually read}} | {{separate observation from inference}} |

## Candidates

| Local candidate label | Proposed kind and outcome | Source references and uncertainty | Proposed owning lane | User resolution |
|---|---|---|---|---|
| {{local label, not a minted native ID}} | {{proposal only}} | {{support and limits}} | {{goals/work/decide or sourced document work}} | {{pending/accepted/edited/rejected/deferred and actual reason}} |

Cluster related outcomes when useful; preserve the evidence and actual scope.
An objective, KR or attribution remains a proposal until the user declares it.
A source's rationale can be transcribed; inferred intent is never a past ADR.

## Actual declarations and decisions

{{Record the user's exact words, source/time, scope and any approved edits.
Keep multi-line declarations intact. An Agent recommendation is not a decision.
On resume re-read these records; do not repeat answered questions.}}

## Materialization and reconciliation

| Confirmed candidate | Actual native ID / owned document | Operation and evidence | Reconciliation or partial failure |
|---|---|---|---|
| {{accepted local label}} | {{kernel-returned ID or actual attachment path}} | {{real command/result reference}} | {{created/linked/left unlinked/unresolved}} |

Native IDs come from the CLI. Goals owns goal/phase state and attribution; work
owns tasks/asks/risks; decide owns designs/ADRs. No BOARD.md, frozen register or
journal is written. Keep declined/deferred rows and reasons for later rechecks.
Do not repeat a completed write after a partial run; inspect its actual result.

## Resume and completion evidence

Stages: scan → harvest → infer → confirm → commit → done; abandoned is terminal.
Here commit means materialize confirmed work, not a Git commit instruction.
Add an optional `step` scalar only when entering one of these existing labels:

- confirm: state_root, goals, phase, clusters, attribution, transcriptions.
- commit: config, okr, phase, design, board, linkage, decisions, knowledge,
  architecture, risks.

The legacy labels okr/board/linkage are recovery identifiers: use native goals,
work items and approved attribution operations, never legacy files/commands.
An abandoned dossier retains its rejected choices. A changed scope needs an
actual decision. A later recheck preserves prior evidence and accepted mappings.

{{Record current stage/step, next safe action, unresolved rows, actual item/query
and attachment checks. Mark done only after the confirmed set reconciles.}}

After saving, run startup safety with the actual absolute root and document root:
`python3 "$PERRY_HOME/tools/document_checks.py" startup --root <absolute-project> --state-root <relative-documents>`.
A nonterminal record is correctly reported as interrupted on later startup;
that report requires a user choice, never automatic replay or a new empty run.
