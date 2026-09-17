# TASK-456 — shipped prose tier budgets and section-preserving splits

Date: 2026-09-17. Owner: Coding Agent. Priority: P2. Required verification: V4.
> Touches architecture: existing shipped prose budget guard and reference-page routing.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: fresh reviewer checks section ownership, routing and bounded context-preservation evidence
> Deployed: no

Authorization: USER-957 and locked DESIGN-017 §5.4 E1, decisions 6/8/9/10. L2 cap 32,768 bytes; L3 cap is explicitly selected at implementation from a measured distribution. No architecture decision or schema edit is authorized. Implement on the supplied candidate containing accepted TASK-455, not an older dispatch procedure; preserve pending TASK-445 separately.

## Deliverable

Extend the existing budget test to L2 and L3 shipped pages and split the three named oversized L2 reference pages along their own sections. One procedure has one full body; routing stubs and precise pointers replace copied prose.

## Acceptance criteria

1. Enumerate L2 and L3 from the locations DESIGN-017 §5.4 defines, excluding live perry project/evidence and scratch content. Record the actual byte distribution before edits. Existing L0/L1 caps remain unchanged. L2 cap is 32,768 bytes; choose and justify the L3 cap from the recorded distribution rather than changing a goal.
2. The existing deterministic budget guard reports every over-budget shipped page with path/tier/actual/cap. Exact cap passes; one byte over fails for both L2 and L3. Keep this structural; Python must not interpret prose quality or choose split boundaries.
3. work/reference/subcommands.md, work/reference/dispatch.md and reference/diagnose.md are <=32,768 bytes after section splits. All newly introduced L2 pages obey the same cap. L3 pages obey the declared implementation cap. No missing normative section or copied procedure body; record moved section headings with old/new locations and content-preservation evidence. Adjust pointers on demand and keep citation resolution green.
4. Preserve host eligibility, isolation, scratch derivation, high-stakes step 4, no-self-merge, task verification and the newly accepted independent integration architecture gate. Any guarded-region test update names only the moved/redirected contract and proves substantive guard behavior still rejects its bounded mutation. Do not loosen guard hashes or discard tests to fit budget.
5. Targeted existing budget/pointer/spec-routing checks, smoke and committed affected tier pass. Mutation evidence demonstrates one-byte-over rejection for each new tier. Net Python/test lines <=0; the prose split is excluded from that line accounting by the phase rule.

## Files in scope

Existing tests/test_router_budget.py and existing pointer/spec-routing guards only when a moved path requires exact adjustment; the three named reference pages; new section pages under their existing reference directories; existing index/citation pointers that must resolve to the moved sections. No new command, backend, parser, dependency, schema or release change. Root/lanes remain routers; do not move prose into SKILL.md to evade budgets. Report any needed scope expansion before implementing it.

## Bound

Three required page splits and two new tier budgets. L3 selection is location-based from the locked design; preserve L0/L1 semantics. No unrelated wording cleanup, architecture text changes, live task store edits or pending decision-card integration. A later TASK-445 integration must reconcile its still-unmerged small prose additions explicitly if they overlap these moved sections.

## Verification

Pinned base/head, byte census, relocation map and relevant before/after section evidence; deterministic cap/cap+1 fixtures and reverted-cap proof; targeted/smoke/committed affected at four workers. Independent V4 and exact-candidate architecture selection before main integration. Canonical PERRY_HOME, unset PERRY_PROJECT, isolated TMPDIR. Integrator owns merged full/slow gates and release allocation.

## Out of scope

TASK-457 context bill, changing decided architecture, guessed module confirmation, lowering acceptance coverage, semantic Python classification, foreign writes, user sign-off, publication and main integration.
