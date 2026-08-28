# TASK-119 — the linkage graph is documented as machine-written and no tool writes it

> Source: `goals/SKILL.md § State files`, `goals/reference/linkage.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — it adds the writer a documented file already claims
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: KR-O2.1 (`perry/OKR.md` v2) — the `goals` lane's write tool

## Measured

`goals/SKILL.md § State files` describes `phase/<NNN>-linkage.md` as
**"Machine-written; read by Perry *and* the frontend"**, and
`goals/reference/linkage.md` documents `link <TASK-ID> <KR-ID>`, `--alias`,
`--unlinked`, `--project` as the way it is maintained.

```
$ python3 bin/perry-goals
perry-goals: expected one of list / commit
```

**There is no `link` subcommand.** This project's own
`perry/phase/002-linkage.md` was written **by hand** on 2026-08-20, because the
tool the documentation names does not exist. Every edge in it, and every number,
was typed.

## Why this row is worth more than the missing verb

TASK-120 landed on 2026-08-21 and made the register's numbers **honest** —
`current` is now reported as an author's assertion, with a staleness signal and
a linked-task tally beside it. It did that *without* touching the register,
because nothing writes it.

Two consequences that are now this row's:

1. **`asserted_scope` is a constant.** Every asserted KR reports `"register"`
   because there is no per-KR assertion date to report. A writer is what could
   add one — and adding that field **would** need `schema/state-schema.json`,
   which is behind this project's safety gate. **If your design needs it, stop
   and say so**; do not widen scope.
2. **`goals/state/linkage_TEMPLATE.md:13` writes `current: 0` into every new
   register.** That is the default TASK-120 identified as making every
   drive-to-zero KR read as met on the day it is written. It is **authoring**,
   which is this row.

## Deliverable

`bin/perry-goals` gains the writer its own documentation already describes:
declare a task→KR edge, record an alias, declare a task unlinked, and write the
result into `phase/<NNN>-linkage.md` **without re-rendering the parts it did not
change** — the same in-place discipline `perry-goals commit` already uses on
`OKR.md § Commitments`, and for the same reason.

Two rules from the surrounding documents that the writer must carry:

- **Never guess an attribution.** `reference/okr-linkage.md`'s one rule (the
  shared one at the skill root): resolve by declared edge, then project id, then
  registered alias; if it
  does not resolve to exactly one KR, **refuse and say the candidates** — never
  fuzzy-match a name. A writer that guesses is worse than no writer.
- **A KR's `target` / `current` are numbers or absent.** Never coerce prose into
  a number, and **do not write `current: 0` by default** — that is the defect
  named above. An unasserted `current` is absent.

## Verification — V3

1. **Round-trip byte-identity.** Writing an edge into a register and re-reading
   it leaves every byte the write did not touch unchanged — including this
   repository's own `002-linkage.md`, on a copy. Prove it with a byte compare,
   not a parse.
2. **The refusal fires.** An ambiguous attribution names its candidates and
   writes nothing; a task already listed under a different KR is refused rather
   than moved silently (`perry-lint` already refuses a task under two KRs —
   the writer must not be able to create that state).
3. **A new register carries no invented `current`.** Creating one from the
   template and adding a KR leaves `current` absent, not `0`. Reverting that
   reddens.
4. **`perry-state --section linkage` reads what the writer wrote**, with
   TASK-120's provenance keys resolving — `asserted_scope` still `"register"`
   unless you added a per-KR date, in which case item 5 applies.
5. **If you conclude a per-KR assertion date is required**, stop and say so in
   your result: it needs `schema/state-schema.json`, which is a per-task release
   the user gives.
6. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-goals`
- `goals/reference/linkage.md` and `goals/SKILL.md`'s subcommand row, **only**
  where they now describe something that exists differently
- `goals/state/linkage_TEMPLATE.md` — the `current: 0` default
- focused tests and fixtures

## Out of scope

- **Writing this project's own `perry/phase/002-linkage.md`.** Ship the tool;
  using it here is a separate act. `git diff -- perry/` must end empty.
- `schema/state-schema.json` — see item 5.
- Folding edges into KR progress (TASK-120, landed) and the KR-id migration to
  `P002-O3-KR1` (DESIGN-007 step 10).
