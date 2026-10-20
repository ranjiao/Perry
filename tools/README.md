# Skill-side tools

`bin/perry` is the single native kernel entrance. Everything here belongs to the
skill: host facilities, read-only document safety facts, source analysis and
measurements. None imports the legacy library/viewer or writes native state by
opening SQLite/exports. The kernel source is unchanged by H.

| Former path | Final path | Behavior |
|---|---|---|
| `bin/perry-architecture` + `bin/perry_architecture/` | `tools/architecture_cli.py` + `tools/architecture/` | facts, host analysis, target checks, append-only checkpoints |
| `bin/perry-detect-host` | `tools/detect-host.sh` | host token |
| `bin/perry-update-check` | `tools/update-check.sh` | bounded update check; source migration only tested offline |
| `bin/perry-codex-preflight` | `tools/codex-preflight.sh` | executor preflight; source retained, no network smoke run in H |
| `bin/perry-context-budget` | `tools/context_budget.py` | report-only context telemetry |
| `bin/perry-dispatch-limit` | `tools/dispatch_limit.sh` | host dispatch slot/cache coordination |
| `bin/perry-churn` | `tools/churn.py` | Git churn measurement |
| `bin/perry-knowledge` | `tools/knowledge.py` | read-only knowledge cards and source facts |
| roles section in `bin/perry-state` | `tools/roles.py` | read-only role files |
| `bin/perry-restore-check` | `tools/restore_check.py` | verify target and verifier bytes against Git |
| `bin/perry-state-cost` | `tools/state_cost.py` | tracked Git document-size measurement; explicit paths |
| recovery/interrupted and safety lint checks | `tools/document_checks.py` | conservative STOP facts; procedures retain judgment |

[Exact helper output shapes and limits](helper-contracts.md). All Python tools
run via `python3 tools/<name>.py`; shell tools via `bash tools/<name>.sh`.
Unknown options refuse. Help is read-only. No legacy CLI alias is available.

## Safety facts and red evidence

Run `python3 tools/document_checks.py startup --root ABS --state-root REL` before
current state reads. Exit 1 means recovery or interrupted run: stop and follow the
[operating rules](../reference/operating-rules.md). The helper never repairs,
resumes or reads the native database. It preserves the small legacy dossier
vocabulary only to prevent unknown restore points from vanishing during cutover.
It does not import the old state parser. Planning drafts are also checked.

`dispatch --input FILE` accepts a JSON scope/hook/spec packet and reports lexical
screening facts. Read the actual spec, classify naming versus doing, and verify
the actual instruction behind `authorization`. A string is not consent. Cross-lane
or foreign document writes refuse. The helper executes no operation.

`review --input FILE` checks evidence-path presence, criteria, independent reviewer
identity difference, verdict and the explicit human boundary. It does not authenticate
a user, read for meaning, accept a task, or award a verification rung. Actual review
and human sign-off remain required. Invalid packets exit 2; blocked facts exit 1.

`tests/test_document_checks.py` deliberately plants corrupt recovery markers,
unknown/duplicate stages, bad steps, interrupted runs, unarmed/unextractable hooks,
unauthorized high-stakes commands, foreign/other-lane paths, missing evidence,
self-review, failed verdicts and agent V5 actors. They are real red inputs; the
suite expects the refusal. Native guard red cases live in `kernel/tests/`.

Ordinary document meaning checks are explicit skill procedures. The
[finite H ledger](../release/retirement/README.md) preserves each old check's
original disposition proposal. Actual approvals and final cutover evidence are
separate records; a procedure's existence never proves that its manual check
ran. One-time F preparation notes now live under
`release/retirement/pre-cutover-notes/`, outside the maintained helper surface.
