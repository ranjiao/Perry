---
diagnosis: 1
stage: scan
updated: "{{actual UTC timestamp}}"
---

# Diagnosis — {{project name}}

Root-owned workflow record at `.perry/diagnose/<date>-diagnosis.md`. Follow
`$PERRY_HOME/reference/diagnose.md`. This is an Agent-authored evidence record,
not output from a retired classifier. Replace placeholders and omit unused rows.

## Scope and owner declarations

- Absolute source/project roots: {{actual agreed roots}}
- Depth and subjects: {{quick/standard/deep; context/docs/concurrency/tracking}}
- Project purpose/type: {{observed evidence, uncertainty and actual user declaration}}
- State owner: {{standalone documents or native Perry; actual evidence}}
- Maintenance tolerance: {{what the owner will maintain, or unknown}}
- User authority and excluded operations: {{actual instruction/reference}}

## Measurements and observations

| Subject | Actual method / command | Observed value and units | Source/date, exclusions and limits |
|---|---|---|---|
| {{instruction load, links, ownership, actual workflow or another scoped subject}} | {{reproducible method}} | {{measured value or unknown}} | {{evidence, not a presumed default score}} |

No default zero counts, universal budget or directory-based project classifier.
A missing measurement stays unknown. Separate observations, reported incidents
and inference. The owner's declared purpose overrides a structural guess.

## Findings and interview

| Local finding label | Observed problem or owner report | Supporting source / actual answer | Consequence and status |
|---|---|---|---|
| {{local label}} | {{specific evidence-led finding}} | {{measurement or exact user words}} | {{open/closed/accepted-risk/disputed}} |

{{Record questions actually asked and their verbatim answers. At most six core
questions; preserve settled answers on resume. Zero findings is valid.}}

## Prescriptions

| Local prescription label | Exact proposed operation and paths | Findings addressed | Effort, owner and rollback | Actual decision and status |
|---|---|---|---|---|
| {{rx-<number>}} | {{smallest useful change, including no change or subtraction}} | {{finding references}} | {{within agreed maintenance tolerance}} | {{proposed/accepted/done/declined/deferred with real source}} |

Use `reference/new-projects.md` when choosing standalone scaffolds versus native
state. Do not create parallel STATE/INTAKE/DECISIONS registers in native projects.
A diagnosis does not authorize foreign writes, live migration, installation,
publication, architecture target changes or removal of safety boundaries.

## Execution checkpoint and actual changes

Restore point: {{actual backup/branch and source hashes; unresolved until created}}.
An execution step cannot start without its actual scoped authority and a usable
restore point. Show exact operations and conflicts before acting. Owning lanes
write their own native state and narratives; preserve unrelated work.

| Prescription | Actual create/edit/move operation | Before/after paths and evidence | Rollback reference / unresolved result |
|---|---|---|---|
| {{accepted rx label}} | {{what really happened, or not run}} | {{actual paths/hashes/results}} | {{restorable bytes or explicit limit}} |

Retain declined prescriptions; do not propose them again without changed evidence.
Preserve exact user wording and read a document in full before rewriting it.

## Resume and recheck

Stages: scan → read → interview → prescribe → execute → done; abandoned is
terminal. Recheck is a later explicit operation, not a separate stage.
Omit `step` until its stage is entered. Recognized interview steps are q1–q6,
audience and attachment; execute steps use rx-<number> for the real prescription.
Do not start another run or auto-resume an interrupted one without the choice.

{{Repeat the same bounded measurements; inspect actual resulting artifacts.
Record failed/unrun checks, source changes, retained uncertainty and the owner's
acceptance of the concrete results. A clean safety gate is not semantic proof.}}

After saving, run:
`python3 "$PERRY_HOME/tools/document_checks.py" startup --root <absolute-project> --state-root <relative-documents>`.
A valid nonterminal record is reported as interrupted; duplicate safety fields or unsupported workflow versions/stages/steps require
repair through the documented recovery procedure.
