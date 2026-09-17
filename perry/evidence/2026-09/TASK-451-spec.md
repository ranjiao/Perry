# TASK-451 — Architecture schema anchored at the code root

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Required verification: V5 (fresh V4 review first; named human sign-off for the claim-surface delivery).
> Touches architecture: schema component and existing file-location contract, DESIGN-017 A1.

> Dispatch mode: auto
> Executor: codex
> Subjective verification: independent review against this written scope
> Deployed: no

Authorization: USER-957, continuing phase 004 under its approved autonomy. No push, publication, foreign project write, or architectural decision edit.

## Deliverable

Implement DESIGN-017 section 6 A1, as already described in the task's 2026-09-15 journal definition. Architecture's schema declaration anchors at the code root, drops blanket owner user, carries the locked per-section authority note, and declares component/module architecture documents with the approved 600-line cap. USER-933 explicitly authorizes this schema claim change.

## Acceptance criteria

1. schema/state-schema.json files[id=architecture] describes the code-root anchor and has no owner:user. Section authority agrees with DESIGN-017 5.1; no confirmed architecture rule is modified.
2. Module documents are declared as a kind tied to code components, with 600-line cap; do not blanket claim arbitrary foreign directories. Follow existing typed schema conventions.
3. Existing schema consumers safely understand the new anchor/kind; template lint and schema checks pass. The perry-state resolver change is TASK-452, not silently folded into A1.
4. Reverting the schema change makes a targeted structural test fail, and unmodified candidate passes. No semantic prose checker is introduced.

## Files in scope

schema/state-schema.json; bin/perry-lint existing anchor resolution, claim lookup and explicit file-kind selection; bin/perry-state-cost existing claim bucket anchor selection and bin/lib existing shared path/config helper surface if needed to avoid two anchor resolvers; existing schema/anchor validation or template tests requiring this declaration update. The reproduced scope dependency authorizes those existing consumer changes for the approved architecture declaration only. Module-kind declaration must not add a blanket glob claim or a second component registry. An agent supplies selected module paths from the confirmed component list; Python may validate typed paths and document structure but must not interpret prose to infer component membership. Existing shared code-root helpers may be reused, not duplicated. TASK-452 state architecture resolver remains separate. Do not change ARCHITECTURE.md, live perry stores, locked designs, or release versions.

## Bound

One root architecture declaration and one module-document kind, existing schema/template consumers only. At most 2 existing test modules changed, no new dependency or duplicate registry. Phase O4 net Python+test lines must be <=0: extend/replace existing coverage and remove superseded assertions instead of growing parallel machinery. Report the line delta explicitly.

## Verification

Pinned-base affected tier, perry-lint --templates, named schema tests, and one revert/mutation proving the declaration assertion. Use isolated fixtures; set PERRY_HOME to the candidate and unset PERRY_PROJECT. Run one suite at a time with -j 4 to avoid prior oversubscription. Record receipts externally.

## Out of scope

TASK-452 resolver; template/process redesign A3/B/C; decision hash D2; module generation; external migration; publication; main integration. Coding agent commits code/tests in its feature worktree and returns immutable SHA and architecture compliance.

## Scope clarification after dependency probe

The first dispatch produced no product changes. Its blocker report established the missing existing-consumer wiring. This clarification authorizes that wiring under USER-957 and, for the architecture declaration, USER-933; it does not revise a locked decision. Retain the original failing probes as evidence. Do not invoke `tests/run --help`: it starts the default suite. Read runner source for syntax. Run smoke plus `python3 tests/parallel --tier affected --base 7ffcc6337bc5c8b31d2e8992c251e23299bff1ea -j 4` sequentially and report the selection. Net Python/test lines must be <=0 without deleting meaningful coverage or compressing statements just to meet the count.

Consumer enumeration before review found one additional runtime anchor switch: `bin/perry-state-cost:buckets` still maps every non-project claim to state root. The same A1 code-anchor contract must apply there, using one shared resolver rather than a second implementation. Existing `tests/test_state_cost.py` may be the second test module. Other anchor mentions were inspected: board-store prose and state-only task archival do not select architecture files. TASK-452 perry-state architecture payload remains excluded.

Verification correction before closure: `work/reference/review.md` sets V5 for operations on the hook high-stakes list. USER-933 authorizes implementation of this claim-surface change; it is not a claim that the user has inspected the resulting delivery. Prepare the reviewed concrete diff and sign-off offer before asking. No implementing or reviewing agent self-awards V5.
