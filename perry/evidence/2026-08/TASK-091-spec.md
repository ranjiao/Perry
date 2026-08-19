# TASK-091 - `Due` is typed, track-aware, and implemented once

> Source: `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`,
> `perry/phase/002-fields-are-typed.md`,
> `perry/evidence/2026-08/TASK-042-spec.md`,
> `perry/evidence/2026-08/TASK-091-round-2.md`, and
> `perry/evidence/2026-08/TASK-091-v4-review-r2.md`
> Dispatch mode: auto
> Executor: coding agent (repository-local code, fixtures, and mutations)
> Estimated cycle: large
> Subjective verification: (none)
> Touches architecture: ADR-007 rules 1 and 2; phase 002 P-O2.1
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P0
- **Attribution**: P-O2.1

### Deliverable

1. `By when` remains split into `due` and `by_when_note`. `due` is a typed
   value whose accepted values are determined by the track context; prose is
   stored only in `by_when_note` and is never inspected by a clock regex.
   `CLOCK_RE` and equivalent prose-clock predicates do not return under another
   name.
2. The `due` writer and the file check apply the same track-aware rule. A
   `pipeline` commitment cannot carry an SLA token when the writer requires a
   calendar date. A `queue` track with no declared SLA cannot lint a value as
   valid when the writer refuses the commitment for missing configuration.
   `project`, `pipeline`, `queue` with SLA, and `queue` without SLA are all
   behavioral fixtures, not branches inferred from one `ops` example.
3. "Unfilled" is one semantic category, not three independent word lists.
   `perry-goals`, `perry-lint`, and `perry-diagnose` use one implementation or
   one declared binding for blank/unfilled cells. English and Chinese idioms
   with the same meaning receive the same classification, including casing and
   punctuation variants. A writer may refuse creating an unfilled commitment
   while lint reports an existing unfilled cell separately from an invalid
   typed value; that contextual action must not be implemented by duplicating
   the category.
4. Date and SLA normalization is implemented once. Formatting decoration is
   either accepted or refused identically by the writer, lint, diagnose, and
   migration paths. In particular, removing interior `*` characters in one
   path while stripping edge decoration in another is forbidden:
   `2026-**09**-30` has one answer everywhere.
5. `bad-typed-cell` is an **error**. A bounded typed field containing neither a
   value allowed by its track nor an unfilled marker is invalid state, like an
   off-enum value. This severity is independent of TASK-093's user decision
   about drift in a hand-edited rendered projection.
6. Migration handles that error rather than weakening it. A Chinese pre-split
   register whose `截止` column mixes the former `By when` meanings produces a
   migration plan or a named refusal; `perry-migrate` must not report "nothing
   to migrate", declare conformance, or silently leave the invalid typed value
   in place. Dry-run and apply make the same classification, and a successful
   split is lossless and idempotent in both configured languages.
7. Calendar validity has one callable predicate. Every in-scope caller uses
   `bin/lib`'s `is_iso_date` rather than a private regex, `datetime.strptime`,
   prefix search, or shape-only check. Invalid dates such as `2026-02-30` and
   `2026-13-45` are false before any caller invokes `date.fromisoformat`.
   Decoration handling is part of this predicate's tested contract.
8. The original commitment behavior remains intact: equivalent English and
   Chinese phrases receive the same verdict; bare unbounded units are refused;
   bounded or quantified schedules, `每周一次`, `逐月`, and valid configured SLA
   shorthands remain accepted where the track permits them; a refusal names the
   field and writes no `OKR.md`, phase, journal, event, or partial state.
9. The schema is the binding for the typed kind and its user-facing accepted
   vocabulary. `bin/perry-lint` does not carry a second prose description of
   accepted values. Unknown typed kinds, ragged rows, placeholders, and absent
   columns produce their declared finding/refusal rather than a traceback or a
   silently skipped check.
10. The fixes are mutation-sensitive by defect class. Tests must fail when any
    of the following is reintroduced:

    - an English-only or case-sensitive unfilled list;
    - a separate blank rule in goals, lint, or diagnose;
    - mode-blind acceptance of a pipeline SLA token or a queue/no-SLA value;
    - interior decoration removal in only one path;
    - a placeholder or ragged-row guard being deleted;
    - the unknown typed-kind branch being deleted;
    - the schema-provided accepted vocabulary being ignored;
    - `bad-typed-cell` changing from error to warn;
    - Chinese pre-split migration returning "nothing to migrate";
    - `perry-diagnose`, `perry-knowledge`, or `perry-state` bypassing
      `is_iso_date` with a private date implementation.

### Verification - V4

1. Re-run the six historical TASK-042 behaviors against real CLI subprocesses
   on disposable English and Chinese fixture projects. This file is now the
   canonical acceptance contract; TASK-042 is historical input, not a second
   bar for later reviewers to extend.
2. Run a differential sweep through the writer and lint paths for all four
   track contexts: `project`, `pipeline`, `queue` with SLA, and `queue` without
   SLA. Include generated dates, SLA units, decoration, placeholders, unfilled
   idioms, and random prose. Every disagreement is either removed or named in
   this specification before review; it cannot be dismissed as an unlisted
   edge case.
3. Exercise `perry-migrate` dry-run and apply on English and Chinese pre-split
   fixtures. Assert the same plan, byte-preservation on refusal, lossless split
   on success, idempotence on the second run, and no false conformance
   declaration. Restore-point and rollback mechanics are not re-reviewed here.
4. Run each mutation category in Deliverable item 10 on a fresh disposable
   copy with import caches cleared. Stock code is green and every mutation is
   red for a focused behavioral reason. Source grep, line-number assertions,
   and tests that duplicate the production predicate are not proof.
5. Preserve the published `perry-goals/list` payload and the relevant migration
   and conformance contracts. Any intentional contract change requires its own
   version/semantics entry; TASK-091 does not silently change a consumer shape.
6. Run the focused goals, diagnose, lint/conformance, knowledge, work-mode, and
   migration suites; then run `python3 tests/parallel`, `bash tests/run`,
   `python3 bin/perry-lint`, and `git diff --check`. Record exact results and
   separate unrelated repository failures rather than omitting them.
7. A fresh-context reviewer who did not implement the fixes evaluates this
   whole specification. PASS requires every defect class above to have a
   behavioral control, all in-scope mutations red, and no unresolved
   writer/lint/migration disagreement. The implementing session cannot award
   V4 or close the task.

### TASK-044 boundary

TASK-091 owns the semantic classification used by migration for `Due`: whether
a value is typed, unfilled, prose that belongs in `by_when_note`, invalid for
its track, or a pre-split value that needs transformation. It also owns proof
that dry-run and apply classify that value identically.

TASK-044 exclusively owns migration's project-wide safety guarantees: complete
diff presentation, dirty-tree policy, restore points, rollback after each write
site failure, preservation of every unrelated row/file, declaration authority,
and the definition of a valid partially migrated project. A TASK-091 reviewer
may report a concrete safety regression to TASK-044, but must not add those
guarantees to this task's PASS bar or redesign the migration transaction here.

### Dependencies

- None. The field split is phase 002's independent P0 slice.
- TASK-042 is superseded implementation work. It is retained only as the
  historical criteria source until TASK-091 passes V4, then may be dropped as
  its current next action states.

### Files in scope

- `bin/lib/__init__.py` - shared typed predicates and normalization.
- `bin/perry-goals` - writer behavior and zero-write refusals.
- `bin/perry-lint` - track-aware typed-cell findings and severity.
- `bin/perry-diagnose` - commitment classification using the shared semantics.
- `bin/perry-migrate` - pre-split detection and semantic transformation.
- `bin/perry-knowledge` and `bin/perry-state` - only their use of the shared
  calendar predicate introduced or changed by TASK-091.
- `schema/state-schema.json` and `schema/goals-list-contract.md` - typed binding
  and unchanged/read-contract declaration.
- Focused tests for goals, diagnose, lint/conformance, knowledge, work modes,
  migration, and contract invariance.
- TASK-091 implementation and review evidence.

### Out of scope

- `viewer/parsers.py` cadence `parse_due` / `parse_frequency`, decision sunset
  parsing, and date-like columns other than the TASK-091 `Due` / `Last
  verified` callers. Record a separate task if those are wrong; do not expand
  this V4 round into every date-shaped string in Perry.
- Store creation, renderer work, parser deletion, or the Goals/config migration
  owned by TASK-090, TASK-092, TASK-094, and TASK-095.
- The hand-edited-rendered-file severity decision owned by TASK-093.
- Namespace/claim findings owned by TASK-086 and TASK-100.
- TASK-044's restore, rollback, dirty-tree, declaration, and whole-project
  migration-safety guarantees.
- Migration or mutation of gimegime-pmo, PolyForge, or any external live
  project. Real-project cutover is TASK-097 at V5; fixtures and copies only.
- Closing TASK-091. Implementation returns it to `review`; fresh V4 closes it.

## Review convergence

This specification replaces review-by-accumulation. A later FAIL must map to a
numbered deliverable or verification item above and demonstrate the missing
behavioral control. A new instance of one of the five fixed classes - track
context, unfilled semantics, typed-value severity/migration, date-predicate
uniqueness, or mutation coverage - is in scope. A different parser, field, or
migration-safety concern is recorded against its owning task and does not move
TASK-091's boundary.
