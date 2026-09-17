# TASK-190 — first-OKR elicitation bank result

Date: 2026-09-17. Author: Coding Agent. Branch:
`codex/task-190-question-bank`. Base:
`0ed39d11` (scope/dispatch batch). Immutable instruction head:
`508135f32e5b42a4c4ac4dfe5869d9ca7b685506`.
The result commit adds only this evidence. No version was allocated: the parent
coordinates accepted delivery ordering and release allocation separately.

## Delivered

`goals/reference/elicitation.md` is a 149-line first-OKR-only question bank with
eight entries, each carrying Kind, Draft answer, Ask, Push until you hear,
Red flags, Produces and Skip when. Produces maps rubric 1.1–1.8; coverage is not
asserted to mean a draft passed. Q1–Q4 are the normal path; Q5 closes the common
baseline gap; Q6–Q8 are gap-specific. One question at a time, normally four to
five, capped at eight including clarification/push questions. Defaults are one
qualitative objective and no more than three distinct outcome KRs.

Answers distinguish sourced facts, user decisions, proposed thresholds and
unknowns. An absent metric is not a zero baseline. Proposed sentences/choices
help the user edit a draft rather than fill a field list. Unknowns survive into
the visible scorecard and rubric feedback. The bank does not manufacture an
objective count to override rubric 1.5's existing solo-project qualification.

The first-init interview in setup now loads the bank and stops at a visible chat
draft plus the unchanged advisory rubric. It does not create plans/, claim resume
or finalize support, hand-append canonical goal stores or automatically start a
phase. Existing config-first startup stays intact. The lane's init row and
adjacent ownership text reflect the draft-only boundary; no expanded router,
phase reuse, escape/premise mechanism or new command is introduced.

## Validation

All tests used `env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME`:

```bash
python3 tests/parallel test_pointers_resolve test_router_budget \
  test_shipped_vocabulary test_ownership test_procedures_call_the_tool \
  test_starts_write_the_config_store_first
```

PASS: 6 modules, 119 tests, 8.9 seconds. `git diff --check` passes.
No new wording-mirror tests or runtime code were added. Mechanical tests do not
judge the semantic quality of an interview; independent behavior review belongs
to the parent, and the real first-project interview gate remains TASK-191.
No synthetic walkthrough or current SkyTonight project was used to claim that
gate: SkyTonight already has an active OKR and is not a no-OKR fixture.

`reference/input-quality.md` is byte-identical to the base (checked against Git),
SHA-256: `399cdb615d6ae7b87c5a82f5a2e26e82d9951607b0e39ac9d5bce50465a74e88`.
Schema, writers, ARCHITECTURE and all live project files are unchanged. No host
installation, publication, push or main merge was performed. Full merged checks
are parent-owned and are not claimed by this result.

## ARCHITECTURE COMPLIANCE

- §2 lanes/references: goal elicitation stays in an on-demand goals reference;
  only its setup caller and narrow lane description change. Root router unchanged.
- §3 ownership and §5 contracts: no state writer, namespace, schema or CLI changes.
  Config bootstrap uses the existing command; the new first-OKR path does not
  cross the unsupported finalization boundary or write PMO files.
- NN-3: the draft says not finalized; no persistence/resume/writer success is
  claimed for an unimplemented operation.
- NN-4: semantic judgments and rubric feedback stay with the agent/user. No
  Python prose parser, automatic quality verdict or fabricated project fact.
- NN-5/NN-6: existing tests use their fixtures; no project state or architecture
  changes. New architecture questions: none for the question-bank scope.

Scope/risk notes: setup's pre-existing structural/write guidance and revise path
remain outside this task; their historical KR-ID/handwriting guidance is not a
newly implemented finalizer. The new first-init path explicitly stops before any
of those writes. TASK-191 owns the real interview gate; TASK-192/193/194 own wider
routing, escape/premise and phase reuse. TASK-443's closing hook was coordinated:
a first-init chat draft is pending planning, not a completed state-changing action.
