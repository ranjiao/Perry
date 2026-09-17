# TASK-457 — five declared context bills

Date: 2026-09-17. Owner: Coding Agent. Priority: P2. Required verification: V4.
> Touches architecture: existing read-only context tool and declared skill reference indexes.
> Dispatch mode: auto
> Executor: codex
> Subjective verification: fresh reviewer compares each bill's declared load set with index rows
> Deployed: no

Authorization: USER-957, locked DESIGN-017 §5.4 E2 and decision 9. Extend the existing read-only `bin/perry-context-budget` with `--bill <snapshot|add-task|close-task|dispatch|plan-phase|all>` rather than adding a second tool. This is an agent implementation choice preserving the same approved measurement. The supplied committed base contains TASK-456's section splits; their own verification/integration remain separate.

## Deliverable

Print a reproducible byte bill for the five named subcommands: L0 router, its L1 lane when applicable, and L2 reference paths declared by its index rows. Show paths, byte contributions, total, per-command budget and over/within status. Clearly distinguish this static declared load from runtime transcript usage and conditional/project-specific context.

## Acceptance criteria

1. Each of the five commands yields its explicit path list and exact UTF-8 file-byte sum, no duplicate path counting. Snapshot has no lane. Primary load declarations remain the existing reference-column indexes, not a parallel registry. Add an explicit snapshot reference row to the existing router as needed; do not infer its load set from free prose. Other command/index matches use explicitly backticked command tokens/known CLI syntax only, never prose meaning. Report excluded non-L2/conditional scope honestly.
2. Missing/ambiguous index declaration, missing file or a path escaping the chosen skill root is an explicit error/unknown, never a zero-cost success. Shared `$PERRY_HOME` reference paths and lane-relative references resolve correctly. Default root is the installation; an optional bill-specific skill-root fixture argument may override it. Do not repurpose legacy --root project semantics. Reject incompatible bill/session/composition/ceiling arguments clearly. Billing must not enumerate/read transcript/session files or write any state/cache.
3. Set five finite budgets from the actual post-split byte distribution and document the measurement/rationale in the result. At cap passes; cap+1 reports overflow. Report exact bytes, not characters or inferred tokens. Preserve default, --session, --composition, --ceiling, --root, --json and --help legacy behavior when no bill is requested; --json may expose a distinct bill payload without changing the old payload.
4. Real source invocations show five bills. Bounded fixtures prove shared/lane paths, deduplication, missing/ambiguous inputs, root containment, Unicode byte counting, read-only behavior and cap/cap+1; a budget-inflation mutation reddens the new boundary proof. Smoke, existing context tests, pointers/budgets and committed affected tier pass. Fresh V4 compares actual declared index rows against all five results. No Python natural-language classification or new dependency.

## Files in scope

bin/perry-context-budget; existing tests/test_context_budget.py; root SKILL.md and work/goals SKILL.md reference-index declarations only if needed; bin/README.md usage entry if appropriate. Keep new measurement inside the existing tool, not a new backend or module. No schema, decided architecture, goal-check or live PMO change. No unrelated dispatch/procedure rewrite.

## Bound

Five subcommands and one read-only mode. Net Python/test lines <=0 across this delivery; preserve meaningful assertions and concise rationale. Do not meet that constraint by dropping tests, weakening validation or compressing code into unreadable one-liners. Reuse/simplify relevant existing code and commentary. If the bound cannot be met faithfully, report the concrete constraint rather than silently exceeding it.

## Verification

Exact base/head; retained five live bills, per-file source/hash/byte receipt and authored index mapping; fixtures and negative/revert proof; legacy context regression, targeted/smoke/committed affected with at most four workers. Canonical PERRY_HOME, unset PERRY_PROJECT, isolated TMPDIR. No full/slow duplicate: integrator owns final combined gates and fresh exact-candidate architecture review. Author returns ordinary RESULT, never its own architecture verdict or V4/V5.

## Out of scope

Runtime token accounting changes, new metadata registry, guessing dynamic reads, new normative architecture rules, existing contract-version edits, user approvals, foreign writes, publication and main integration.
