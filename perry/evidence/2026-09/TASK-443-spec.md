# TASK-443 — Shared proactive next step after state-changing commands

Date: 2026-09-17. Owner: Coding Agent. Verification: V3 with independent review.
> Dispatch mode: auto
> Executor: codex
> Estimated cycle: medium
> Subjective verification: independent scenario review
> Touches architecture: sections 2, 3, 5, NN-4; preserve existing ownership
> Deployed: no

User authorized progressing the recommended task batch on 2026-09-17.

## Deliverable

Implement DESIGN-020 section 5.4 and decisions 3/8. Enumerate state-changing commands from actual skill procedures, define one shared closing step and link each. Query perry-state --section next --after with actual subcommand; render returned primary/alternates without inventing advice. Respect explicit project silence, dispatched sessions and in-progress planning; no primary means no question. Preserve read-only commands and current deterministic rule engine. Use existing config infrastructure, not hidden state or natural-language parsing.

## Files in scope

reference/next.md; state-changing procedures and their indexes; existing config/state surface for project silence if needed; focused tests.

## Verification

A bounded command inventory shows complete routing; actual next payload scenarios cover recommendations, no result, silenced project, dispatched execution and planning-in-progress. Test setting roundtrip and default; independent scenario review.

## Out of scope

No recommendation-rule redesign, planning drafts, pack-control implementation, new namespace or unsolicited next-step execution. No architecture edits, publication or host installation.

## Bound

The named DESIGN-020 phase only; preserve other tasks and their acceptance.
