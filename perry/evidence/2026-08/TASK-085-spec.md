# TASK-085 — A decision's status has one binding, and a word for a proposal

> Source: opened 2026-08-19; re-measured 2026-08-20 against the post-PR-#8 tree
> Dispatch mode: auto
> Executor: claude-subagent (repository-local; the enum has three prose copies that must move in the same edit)
> Estimated cycle: small
> Subjective verification: the name of the new value — `proposed` is the obvious candidate, but `prescription_status` already uses it for a different thing, so a reader meeting both may expect them to mean the same
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked

## Deliverable

1. `schema/state-schema.json § enums` gains a `decision_status` entry. It is the
   one binding; `bin/perry-decide` reads it instead of its hardcoded
   `STATUSES = ("active", "superseded", "expired", "archived")` at line 79,
   which is also consulted at lines 182, 227, 419 and 420.
2. The enum carries a value meaning **drafted, awaiting the user** — a decision
   that has been written but not yet adopted. Today there is no such word, so a
   proposal is indistinguishable from a decision in force, which is the defect
   this row names.
3. The two prose copies move in the same edit, because a value list with three
   independent spellings is what made this a bug rather than a typo:
   `schema/decide-list-contract.md` (lines 18 and 49) and
   `decide/reference/decisions.md` (its status definitions, and the `archived`
   guidance around line 227).
4. Reading stays tolerant. `decide-list-contract.md` already promises "or
   whatever the file says — see `conformance.off_enum_status`", and an existing
   `DECISIONS.md` carrying a value outside the enum must still be read and
   reported, not refused. Writing is strict; reading is not.
5. The `perry-decide/list` contract's payload keys do not change. Adding a
   possible value to a documented field is not a break; renaming or removing one
   would be.

## Verification — V2

1. Assert `bin/perry-decide` has no hardcoded status tuple left — the values it
   accepts come from the schema, and a value added to the schema is accepted
   with no code edit.
2. Assert the new value round-trips: an ADR written with it is listed, counted
   and filtered by `--status <new>` like any other.
3. Assert an off-enum value in an existing `DECISIONS.md` is still read and
   reported through `conformance.off_enum_status`, not refused.
4. Assert the three spellings agree, mechanically — a test that reads the enum
   from the schema and asserts both prose files list exactly those values, so
   the next divergence fails instead of drifting.
5. `python3 bin/perry-lint`, `python3 tests/parallel`, `bash tests/run`,
   `git diff --check`.

## Files in scope

- `schema/state-schema.json` — the new `decision_status` enum only
- `bin/perry-decide` — read the enum instead of the tuple
- `schema/decide-list-contract.md`, `decide/reference/decisions.md` — the prose copies
- focused decide tests

## Out of scope

- **`schema/state-schema.json § claims[]`.** No path Perry claims in anyone's
  project changes. The edit adds one enum and touches nothing else in that file.
- The conformance gate and its default, which PR #8 just settled.
- `DECISIONS.md` itself, and any project's existing decision records. No file is
  rewritten to use the new value; it becomes available, not mandatory.
- `design_status`, `task_status` or any other enum.
- Deciding whether existing ADRs should be re-classified.
- Closing without the V2 evidence above.

## Changes

- 2026-08-20 — **The gate returned `pass`, and that pass does not constitute
  clearance.** `perry-state --escalation-scan` matched `state-schema.json` in
  both `Deliverable` and `Files in scope`, then green-lit both because the
  `Out of scope` section above names the same fragment. That disclaimer was
  written by the same author as the spec, so the mechanism is self-certifying:
  any spec can pass this rule by asserting it does not do the thing.

  The clearance that counts came from the user in chat, having been told the row
  edits `schema/state-schema.json`. Bound: **one new `decision_status` enum, no
  entry in `claims[]`, no change to which paths Perry claims.**

  Recorded rather than left implicit because the same self-certifying pass
  happened on `TASK-047-spec.md` and was refused as authority there too. Whether
  an `Out of scope` line written by the spec's own author should green-light a
  high-stakes rule is a real question about the gate, and neither override
  settles it.
