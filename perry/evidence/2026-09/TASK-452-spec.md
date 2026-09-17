# TASK-452 — State reports architecture at the code root

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Required verification: V4.
> Touches architecture: bin state consumer and existing parser, DESIGN-017 A2.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: independent review against the written bounded criteria
> Deployed: no

Authorization: USER-957 and locked DESIGN-017 A2. Dependency TASK-451 must satisfy the task store's startable gate before dispatch. This spec is prepared, not a start or completion claim.

## Deliverable

Make perry-state read the root architecture document from configured code_repo_path, or the project root when unset, through the existing shared location contract from A1. Stop using Status: draft as a warning/gate while preserving last-reviewed ageing. No schema, decided architecture text or foreign-project write.

## Acceptance criteria

1. On Perry, --section architecture reports exists true for the root document. In an isolated copy with that root file absent it reports false, even if a stale same-named file remains under the state directory.
2. A split fixture reads the configured code root. An unset code root uses the project root. Root absence is reported without silently substituting the state-root document.
3. Existing old Status: draft headers remain readable; exposed legacy status is empty as DESIGN-017 specifies. No draft warning is emitted. Existing last_reviewed value/age and stale-review warning remain correct.
4. Reverting the location fix makes the root-versus-state fixture fail; reverting warning removal makes the draft fixture fail. Unmodified candidate and affected tier pass.

## Files in scope

bin/perry-state architecture payload/location wiring and draft warning; the existing viewer/parsers.py parse_arch_meta/load_snapshot path only if necessary to expose the chosen file or retain backwards-compatible parsing without a duplicate parser; existing architecture/state fixture tests in at most 2 modules. Reuse A1's shared code-root resolver. Do not migrate viewer storage readers, import bin into viewer, or create another location resolver.

## Bound

Four locations: single root, split code root, missing code root document, stale state-root decoy. Two headers: legacy draft and no Status. Two review ages: fresh and stale. No new architecture rule, module generation, template overhaul, decision hash, or review workflow. Net Python/test physical lines <=0; retain meaningful existing coverage.

## Verification

Pin current main after A1 is integrated. Use isolated fixtures, candidate PERRY_HOME, unset PERRY_PROJECT and a fresh TMPDIR. One suite at a time, 4 workers. Run smoke and the committed affected selection, two bounded reverting-fix proofs, git diff --check. Read runner source; tests/run --help currently launches full tests and is not a discovery command. Record the exact commit and line delta externally.

## Out of scope

Schema claim changes, stored decisions, V5 sign-off, foreign writes, live PMO state, release allocation, publication, and main integration. Coding commits code/tests on its own branch. A separate reviewer awards V4; the integrator owns merged full/slow acceptance.
