# TASK-276 — spec

> Design: `design/DESIGN-015-linkage-is-a-store.md` (locked 2026-09-02), implementation plan row **A**
> Dispatch mode: manual
> Executor: manual — **a gate result, not a judgement.** `perry-state --escalation-scan` on this spec returns `verdict: refuse`, `refuse: ['claims', 'state-schema.json']`, both from `.perry/hook.md § High-stakes operations`. This row's whole deliverable is a `claims[]` edit, so the refusal is correct and not over-broad. Same disposition as `TASK-219`, and for the same reason: rewording the spec to pass is the one thing a safety gate must never reward. Dispatch by hand via `/perry work delegate`.
> Estimated cycle: small
> Subjective verification: (none) — every acceptance is a command or a count
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: P003-O3-KR2

## Files in scope

- `schema/state-schema.json` — the `claims[]` entry and the three record schemas.
- `bin/perry-lint` — only if the census needs the new store registered to report it.
- `tests/` — the new schema's guard.

## Deliverable

`linkage.jsonl` declared in `schema/state-schema.json` `claims[]` with
`owner: perry`, `anchor: state`, plus the `kr` / `edge` / `unlinked` record
schemas exactly as `DESIGN-015 § 5.1` spells them.

**No reader and no writer moves in this row.** `git diff --stat` should touch
`schema/` and `tests/` only.

## Out of scope

- Backfilling the 16 never-asked or 75 declared rows — phase 004.
- `tasks.jsonl`'s `Next action` prose — deferred 2026-09-02, `DESIGN-015 § 8`.
- Any project other than Perry's own.
- Importing any data — that is row B.
- Moving any reader — that is row C.

## Verification

- `python3 bin/perry-lint --claims --root . --json` resolves `linkage.jsonl`
  and exits 0 with no new collision on this project.
- With the store file absent, `perry-lint` reports it **`unchecked`, not
  `clean`** — the phase-003 operating rule, and the property `TASK-229`
  measured for the other six stores (`evidence/2026-08/TASK-229-result.md`).
- The three record schemas match `DESIGN-015 § 5.1` field for field.
- Mutation: revert the `claims[]` entry and a named test goes red.
