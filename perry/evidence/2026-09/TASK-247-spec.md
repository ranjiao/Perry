# TASK-247 — spec

> Design: — (phase KR row, not design-derived)
> Dispatch mode: auto
> Executor: codex (self-contained: three call sites in two files, no MCP needed, and the predicate to reuse already exists)
> Estimated cycle: small
> Subjective verification: (none) — the acceptance is a count of call sites plus a mutation
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: — (TASK-233 is done)
- **KR linkage**: P003-O2-KR1
- **Verification rung**: V4

## Why

`P003-O2-KR1` drives to zero the call sites reading `.perry/config.md` as the
authority while `.perry/config.jsonl` exists. These three ask *"is there a
`config.md`"* as their test for *"is this project configured"*, so a project
configured by the store alone reads as unconfigured.

**The population was re-measured 2026-09-02 on `d49964e` and the row's own
description had decayed.** It said the third site was `bin/perry-migrate:228`;
that file was deleted 2026-08-31 by `TASK-261`. The live third site is
`bin/perry-lint:657`. The count is still three — the members are not.

## Files in scope

- `bin/perry-diagnose` — line 1376, `(root / ".perry" / "config.md").is_file()`.
- `bin/perry-diagnose` — line 2515, the `config.md` half of the `is_perry`
  disjunction; the `OKR.md and BOARD.md` half stays as it is.
- `bin/perry-lint` — line 657, the upward walk that breaks only on `config.md`.
- `tests/` — the mutation guard.

Line numbers are as of 2026-09-02: **re-derive them before editing.** Count
call sites, never names.

## Deliverable

The three sites use the wide test — store **or** markdown. Two call sites in
this repository already ask it correctly and are the shape to reuse rather than
re-invent: `viewer/parsers.py:402` (the predicate itself) and
`bin/perry-goals:2158`.

## Out of scope

- `schema/state-schema.json` and anything under `claims` — not touched by this row.
- The `OKR.md`/`BOARD.md` half of `perry-diagnose:2515`'s disjunction.
- `bin/perry-lint`'s other 22 rootless handed-back commands — that is `TASK-254`.
- Any project other than Perry's own.
- Backfilling or migrating anyone else's configuration.

## Verification

- A grep for existence checks over `bin/` and `viewer/` returns **zero** sites
  testing `config.md` alone as the configured predicate. Report the command and
  its output, not a claim.
- On a project with `.perry/config.jsonl` and **no** `.perry/config.md`, all
  three code paths report it as configured. Build that fixture; do not assert
  it from reading.
- **Mutation, and the acceptance turns on it**: revert one of the three sites
  to the narrow test and a named test goes red. A gate that was never shown
  able to go red is not evidence (phase 003 operating rule).
- `bash tests/run` shows no new failures against the pre-existing baseline;
  name the baseline and which runner produced it.
