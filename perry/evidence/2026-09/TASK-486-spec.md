# TASK-486 — DESIGN-023 A: kernel spec — concepts, template schema, CLI surface

Date: 2026-09-24. Owner: Coding Agent. Priority: P1. Required verification: V1.
KR: O3-KR4. Design: `perry/design/DESIGN-023-a-kernel-and-a-skill.md § 5`, `§ 6` row A.
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: the user confirms the `ARCHITECTURE.md § 2` addition and the NN-1/NN-2 marking
> Touches architecture: §2 (a new `kernel/` component), §6 NN-1, NN-2
> Deployed: no

## Files in scope
- `kernel/ARCHITECTURE.md` — new. It is a module document under DESIGN-017
  User Decision 3.
- `ARCHITECTURE.md § 2` and `§ 6` — proposed edits only. They are written after
  the user confirms them (NN-6).

## Deliverable
`kernel/ARCHITECTURE.md` fixes the following before any kernel code is written:
1. **The eight concepts** of DESIGN-023 § 5.1, each with its fields.
2. **The process template's JSON schema.** It covers:
   - types, fields and field kinds, including ordered `enum` and `metric`;
   - states, transitions, relation kinds and id prefixes;
   - guards: the four kinds, `when`, grouped `limit` and its `mode`.
3. **Every command,** with its JSON input, JSON output and error codes:
   - `init`, `template` (apply, show, validate);
   - `item` (create, get, update, move);
   - `rel`, `attach`, `query`, `events`, `export`, `import`, `describe`.
4. **The metric formula and roll-up.** `met` and `fraction` come from
   `current`, `target`, `baseline` and `direction`. It also fixes how several
   checks on one KR roll up (DESIGN-022 User Decision 2) — one fixed rule, not a
   configurable one.
5. **The store path rule** for a project anchor, `--store` and `PERRY_STORE`, and
   the live-store check (DESIGN-023 § 5.3).
6. **The argument for each new claimed path** (ADR-016): the store path and
   `<state root>/export/`.
7. **DESIGN-016's argument-contract lessons,** as rules of the CLI:
   - `--root` and `--store` beat the environment;
   - unknown keys are refused;
   - queries are bounded by default;
   - `--help` never executes;
   - no tracebacks;
   - a no-op reads differently from a write.
8. **The concept and command budget:** 8 concepts and 12 command groups (Goal 6).

## Out of scope
- Kernel code (TASK-487).
- The content of the process template (TASK-488).

## Acceptance criteria
1. `kernel/ARCHITECTURE.md` exists and covers items 1–8 above. Every command
   names its error codes.
2. It names no type, state or field that the Perry template defines. DESIGN-023
   Goal 1 applies to the spec as well as to the code.
3. The user has confirmed, in session, the `ARCHITECTURE.md § 2` addition and
   the marking of NN-1 and NN-2 for phase H.

## Bound

The eight Deliverable items and the three acceptance criteria. One new file, plus the two `ARCHITECTURE.md` edits once the user confirms them. No code.

## Changes

- 2026-09-24 — `Dispatch mode: manual` → `auto`. The user directed the PMO in session to drive the DESIGN-023 rows, and confirmed this change.
