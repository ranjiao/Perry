# TASK-226 — a row entered `.perry/conformance.md` with neither of its two documented writers running

> Dispatch mode: manual
> Executor: manual — an integrity question about the file that gates every write under `Conformance gate: enforce`. Dispatching an agent to investigate a write whose cause is unknown risks adding a second unexplained write.
> Estimated cycle: small
> Subjective verification: whether the explanation found actually accounts for the observation, or merely fits it
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V4
- **Dependencies**: —
- **Source**: `/perry work end-phase-retro` and the session that followed, 2026-08-28. Intake row 6, discharged the same day.

## The observation

Two `perry-conform status` runs, roughly twenty minutes apart on 2026-08-28:

| | verdict | the card |
|---|---|---|
| first | `23/24 declared and matching` | `· knowledge/goals/linkage-graph-before-first-add.md  undeclared` |
| second | `24/25 declared and matching` | `✓ knowledge/goals/linkage-graph-before-first-add.md  conformant @v2` |

Both totals moved by one, consistently with `DESIGN-012-close-phase.md` being
created (undeclared) **and** the card becoming declared. `git diff` on
`.perry/conformance.md` shows the row added with date `2026-08-28`.

**No `perry-conform declare` and no `perry-migrate` was run between those two
readings.** `bin/perry-conform:11` and `:41` both state that this file is
written only by those two.

## What was ruled out during the session

- **`bin/perry-knowledge`** — `grep -n conform bin/perry-knowledge` returns
  nothing. It reports the missing index and does not touch conformance.
- **`bin/perry-task`** — the only conformance-related behaviour is a refusal
  (`:1129`, `:1152`) that points the caller at `perry-conform declare`.
- **The full test suite** — it ran in the background and **had already
  completed** before the first of the two readings, so a test writing into the
  real root does not explain a change that happened afterwards. (`declare --all`
  does exist in `tests/test_conformance.py:555`, which is why it was checked.)
- Between the two readings the only writes performed were: `git diff`
  (read-only), a heredoc creating `perry/design/DESIGN-012-close-phase.md`,
  `perry-state`, and `perry-lint`.

## Deliverable

Determine what wrote the row. One of:

- **A third writer exists** → remove it, or document it in `bin/perry-conform`
  alongside the two already named. The file's own docstring is the contract
  being violated; a third writer that stays must be declared.
- **The observation has another explanation** → record it, and retire this row
  with that explanation written down rather than by concluding it was noise.

## Verification — V4

1. **Reproduce, or prove it cannot be reproduced.** Re-run the same sequence
   against a copy of the project and watch `.perry/conformance.md`.
2. If a writer is found, a **mutation**: with it removed or fenced, the same
   sequence must leave the file untouched.
3. If it cannot be reproduced, the row closes on the written explanation, not
   on "did not recur" — the file gates every write under the `enforce` gate,
   and a gate whose record can change by an unknown route is not a gate.

## Out of scope

- Whether authored files *should* be auto-declared. That is **TASK-223**, a
  feature request; this is an integrity question, and the two must not be
  merged — an auto-declare feature landing first would make this observation
  permanently unexplainable.
