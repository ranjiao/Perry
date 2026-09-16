# TASK-463 — opt-in release skill result

Date: 2026-09-16. Author: Coding Agent. Branch:
`codex/task-463-release-skill`. Base:
`c1703abf4246d339e5e8b34158aa64b7b2e25026`. Immutable instruction head:
`ab1b6f3a61e518ecff79b00fd546efbe7bb7117b`.
The following result commit adds only this evidence.

## Delivered

A 159-line `packs/software-ops/releases.md` contains the opt-in procedure.
Conditional pointers in pack/work entrypoints and phase/integration/task-close
procedures make it discoverable without loading it during unconfigured work.
Pack activation alone enables no version writes or repeated activation questions.

The procedure requires a user-approved project policy or approved reference in
the existing hook, retaining the project's authoritative version/release records.
Policy records the baseline at adoption, not another mutable current-version copy.
It distinguishes phase, compatibility and manual strategies; component counters;
partial/multiple/retried deliveries; integrated versus published outcomes; and
split-repository authority versus Perry evidence roots. Existing files are inspected
before adopting outputs. Missing tooling calls for a bounded project adapter;
no generic runtime, CLI, machine enforcement or universal store is claimed.

Main integration coordinates allocation on the accepted history while coding
retains product-file edits/commits. Phase ownership stays with goals. Publication
uses the actual adapter, exact verified artifact and existing authorization;
new authority is requested only after preparing the concrete candidate. Recovery
records actual remote partial outcomes and does not overwrite published identity.
Task close retains its existing acceptance/verification rules.

## Validation

All tests used `env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME`.

Final command:

```bash
python3 tests/parallel test_pointers_resolve test_router_budget \
  test_shipped_vocabulary test_procedures_read_the_contract \
  test_procedures_call_the_tool test_ownership test_work_modes \
  test_spec_scannability
```

PASS: 8 modules, 283 tests, 4.2 seconds, 8 workers. No tests were added or weakened;
no wording-mirror tests or duration changes. `git diff --check` passes.

Initial six-module run passed 133 tests. The additional pack/scannability run
identified an inserted release link inside the existing byte-pinned Git role
boundary region (1 failing test). The new optional section was moved after that
region; the guarded text and guard remained unchanged. The final eight-module
run above passed. Subsequent edits only wrapped a policy line and removed a
trailing blank line before the instruction commit.

Independent realistic scenario forward-testing and merged full validation are
owned by the parent and are not claimed here. This author made no foreign project
writes, hook edits, runtime/schema changes, installs, push, tags or publications.
TASK-462 candidates and pending architecture authorization were untouched.

## ARCHITECTURE COMPLIANCE

- §2 packs and lanes: reusable software-domain guidance stays in software-ops;
  work/goals receive conditional references only. Root SKILL is unchanged.
- §3 ownership and §5 contracts: no new writer, namespace, config key, CLI or
  schema. Goals owns phase records, coding owns product changes and PMO retains
  ordinary receipts at the configured evidence root.
- NN-1/NN-2: project release authority is linked, not duplicated into a new ledger.
- NN-3/NN-4: no imaginary automation or semantic Python judgments; typed checks
  require actual project tooling and interpretation remains agent-owned.
- NN-5/NN-6: no runtime tests write product state; ARCHITECTURE is unchanged.
  New architecture questions: none for this procedure-only scope.

Skill-creator's progressive disclosure guidance was applied: one conditional
reference holds the procedure, with narrow entrypoints and no generic scaffolding.
Scope deviations: none.
