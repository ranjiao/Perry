# TASK-110 — Measure what Perry's own state costs, and propose a retention policy

> Source: split out of TASK-070 on 2026-08-20. TASK-070 matched `.perry/hook.md`'s "Destructive filesystem operations" rule, correctly: it proposes deleting from `evidence/` and `journal/`. This row is the half that deletes nothing, so it can proceed while the deleting half waits for the user's approval of what this produces.
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: the retention policy itself. This row produces a proposal; adopting it is TASK-070 and is the user's decision.
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## The measurement that prompted it

Taken 2026-08-20 on this repository, and note the trend rather than the number:

| | audit | 2026-08-18 | 2026-08-20 |
|---|---|---|---|
| Perry state as a share of tracked bytes | 19.5% | 20.6% | **31.3%** |
| `perry/evidence/` | — | 174KB / 36 files | **981KB / 135 files** |

`evidence/` grew 5.6× in two days, and most of that is one day of dispatch
records and specs. The row this came from was opened against `journal/`; the
measurement says `evidence/` is now four times larger. A policy written from the
old number would govern the wrong directory.

## Deliverable

1. **A reproducible measurement**, committed as a command this repository can
   re-run — not a number pasted into a document. For every directory Perry
   writes: bytes, file count, and growth across the tracked history, so the
   trend is visible and not just the snapshot.
2. **A retention proposal, per directory.** For each: what is kept forever, what
   is moved, what is deleted, and **the bytes each rule recovers.** A rule whose
   saving is not stated cannot be traded against what it costs.
3. **What becomes unrecoverable, stated per rule.** `evidence/` holds the
   verification record that `done` rows cite; `journal/` is the append-only
   history; `.perry/events.jsonl` is described as derived and disposable, and
   `design/` and `decisions/` are the architecture record and stay. Each rule
   says which of those it touches and what a future reader loses.
4. **The proposal is a document, not an action.** Nothing is deleted, moved or
   rewritten by this row.
5. Deliver the proposal text **in the RESULT block**, not by writing under
   `perry/` — that directory is the PMO's state and is out of bounds for you.
   The PMO files it as evidence.

## Verification — V3

1. Re-running the recorded measurement command reproduces the same figures.
2. The proposal covers every directory the measurement names — no directory is
   silently omitted, and one that needs no rule says so explicitly.
3. Every rule states the bytes it recovers and what becomes unrecoverable.
4. A reviewer can reach a **different** retention decision from the same
   document. If the proposal only supports its own conclusion, it is an argument
   wearing a measurement's clothes.
5. `python3 tests/parallel`, `python3 bin/perry-lint`, `git diff --check` — the
   measurement command must not perturb the suite.

## Files in scope

- a measurement command, wherever this repository puts such tools
- its focused tests

## Out of scope

- **Deleting, moving or rewriting anything.** That is TASK-070, and it waits for
  the user to approve what this row produces.
- Anything under `perry/` — the PMO's state. Read it to measure it; do not write it.
- `schema/state-schema.json`, `claims`, and which paths Perry claims.
- `bin/perry_store.py`, `bin/perry-goals` — carried by a live dispatch.
- Closing without the V3 evidence above.

## Changes

- 2026-08-20 — **The gate refuses this spec, and the refusal is the split
  working rather than failing.** `perry-state --escalation-scan` matches
  `design/` and `evidence/` against `.perry/hook.md`'s "Destructive filesystem
  operations — bulk delete, overwriting a project's own `design/`, `evidence/`,
  `knowledge/`, `inputs/`". Both appear because this row's `Deliverable`
  **names** those directories while stating it deletes nothing from them; the
  matcher cannot distinguish measuring a directory from emptying it.

  This is precisely why TASK-070 was split. The user was shown the split — one
  row that measures and proposes, one that executes and waits for approval of
  what the first produces — and chose it, which is the clearance this row runs
  under. Bound: **nothing under `perry/` is written, moved or deleted; the
  proposal is delivered as text, and the PMO files it.** The dispatch prompt
  carries that bound.

  Worth keeping: the same fragment will refuse every future row that so much as
  reasons about these directories in writing. A row that is careful enough to
  say "I delete nothing from `evidence/`" is refused for saying it, while one
  that never mentions the directory passes. That is a real property of a scanner
  that reads prose, and TASK-107 fixed word boundaries, not this.
