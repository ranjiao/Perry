# TASK-091 - fresh-context V4 review, round 3

> Reviewer: fresh Review Agent; did not implement the change.
> Canonical criteria: `perry/evidence/2026-08/TASK-091-spec.md`.
> Prior review read as required context:
> `perry/evidence/2026-08/TASK-091-v4-review-r2.md`.
> Review surface: the canonical artifacts above and the current git diff.
> Workspace writes by this review: this evidence file only. No code, task
> state, BOARD, journal, event, commit, or push mutation.

## Verdict

**PASS.**

Round 3 initially found one in-scope writer/lint disagreement that made the
working tree a FAIL: `_track_context` understood English `Track` / `Mode` /
`SLA` headers but not their schema-declared Chinese `轨道` / `模式` / `时限`
forms. The implementing session fixed that during the review. The final
implementation maps every localized header back to its canonical schema key
through `canonical_column`, and the same real-CLI fixtures now agree across
writer, lint, and migration.

No unresolved TASK-091 finding remains. The full repository gate still has
unrelated failures, recorded below rather than omitted or charged to this
task.

## Review safety and snapshot

- `bin/perry-state --section recovery`: `blocking: false`, no pending
  transactions and no malformed dossiers.
- `bin/perry-state --section interrupted`: empty.
- All destructive behavioral work ran on disposable projects or disposable
  copies. No Perry write command was aimed at this repository.
- The first full-gate attempt crossed an implementation update and was
  interrupted rather than used as evidence.
- The final full gates compared the diff hash before and after. Both saw the
  same snapshot:
  `6b7ab310e71cede9e68d8b3e3b373329f700d79ad099c47637cf1d2eb0244c85`.

## Initial localized Tracks FAIL

I built equivalent disposable projects whose `.perry/config.md` declared:

```markdown
## Tracks

| Track | Mode | SLA |
|---|---|---|
| rel | pipeline | 10d |
| bare | queue | - |
```

and:

```markdown
## 轨道

| 轨道 | 模式 | 时限 |
|---|---|---|
| rel | pipeline | 10d |
| bare | queue | - |
```

The `OKR.md` fixture then carried either `rel` / `3d` or `bare` /
`2026-09-30` in its typed `Due` cell.

Before the fix:

| Config header | Track / Due | `perry-goals commit` | `perry-lint` |
|---|---|---|---|
| English | `rel` / `3d` | rc 1, pipeline refusal, zero writes | error `bad-typed-cell` |
| English | `bare` / `2026-09-30` | rc 1, missing-SLA refusal, zero writes | error `bad-typed-cell` |
| Chinese | `rel` / `3d` | rc 1, pipeline refusal, zero writes | **no `bad-typed-cell`** |
| Chinese | `bare` / `2026-09-30` | rc 1, missing-SLA refusal, zero writes | **no `bad-typed-cell`** |

The writer already resolved the localized track table. Lint's new
`_track_context` built its row only when the normalized header literally
contained `track` and `mode`, so the Chinese table returned `{}` and fell into
the permissive project context. This directly violated Deliverable 2 and the
track-context mutation class in Deliverable 10; it also affected the migration
scratch linter used by Verification 3.

## Fix and independent reproduction

The first repair used schema-backed `column_index` lookups for `Track`, `Mode`,
and `SLA`. The repository's existing work-mode vocabulary guard correctly
rejected that fixed tuple because lint must not carry a second list of
mode-default columns.

The final repair generalized the binding:

1. `canonical_column(header)` normalizes a header and maps it through the
   schema-loaded `COLUMN_ALIASES` and `accepted()` vocabulary.
2. `_track_context` uses `column_index(..., "Track")` and
   `column_index(..., "Mode")` only to recognize a track table.
3. It canonicalizes the complete header row and zips that row to the cells.
   Chinese `时限` therefore becomes the canonical `sla` key without lint
   naming `SLA` as a private mode-default inventory.
4. Empty and undeclared tracks return `{}`, preventing the typed finding path
   from turning into an rc 2 type error.

After the final repair, the same independent CLI fixture produced:

| Track / Due | Writer | Lint |
|---|---|---|
| `rel` / `3d` under Chinese headers | rc 1, zero writes | rc 1, one error `bad-typed-cell`, pipeline context named |
| `bare` / `2026-09-30` under Chinese headers | rc 1, zero writes | rc 1, one error `bad-typed-cell`, missing clock named |

The migration scratch path also produced a single error-level
`bad-typed-cell` for both localized configurations instead of declaring
conformance or saying that there was nothing to migrate.

Deleting the schema reverse binding by making `canonical_column` return only
`norm(header)` made the two localized goals/migration controls fail with four
behavioral failures. One observed migration failure changed the expected rc 1
to rc 0 for the queue/no-SLA case. The repaired branch is therefore
mutation-sensitive rather than covered only by a source assertion.

## Deliverable map

### D1 - typed `Due`, prose-only note

PASS. `Due` remains split from `by_when_note`. The writer classifies only the
typed cell; diagnose reads the typed date and prose note as separate values;
no `CLOCK_RE`-style predicate was reintroduced in scope.

### D2 - writer/lint track parity

PASS after the localized-header fix. Generated values cover `project`,
`pipeline`, queue with SLA, and queue without SLA. Real CLI controls cover the
two restrictive contexts under Chinese track headers. Pipeline SLA tokens and
all populated queue/no-SLA values are rejected by both writer and lint.

### D3 - one blank/unfilled category

PASS. Goals, lint, diagnose, and migration use `lib.is_blank_cell`; the schema
declares the multilingual vocabulary. Case, terminal punctuation, Markdown
edge decoration, and paired English/Chinese idioms are tested. The writer may
refuse creating an unfilled commitment while lint classifies the existing cell
as unfilled rather than malformed.

### D4 - one normalization contract

PASS. `normalize_typed_cell` owns edge decoration. Date and SLA predicates,
the writer, lint, diagnose, and migration share it. `**2026-09-30**` is
accepted where its track permits it; `2026-**09**-30` is not silently repaired
by one path.

### D5 - bad typed state is an error

PASS. `bad-typed-cell` is error severity, including prose, non-template
placeholders, pipeline duration tokens, and queue/no-clock populated values.
Migration remains callable because its repair path is exempt from the
conformance write gate.

### D6 - migration handles the error

PASS. English and Chinese pre-split fixtures receive a plan or a named refusal.
Dry-run and apply agree. Successful splits preserve typed cells, move prose
losslessly to the note column, preserve declared unfilled markers, and are
idempotent. Track-invalid typed values are named refusals and remain
byte-identical.

### D7 - one calendar predicate

PASS. Goals, diagnose, knowledge, and state call `lib.is_iso_date`; impossible
dates are false before calendar arithmetic. Direct sentinel tests pin the
diagnose, knowledge, and state bindings. Edge decoration is part of the shared
predicate's contract.

### D8 - historical commitment behavior

PASS. The real CLI writer tests preserve English/Chinese equivalence, refuse
bare unbounded units, accept bounded and quantified schedules where applicable,
and retain configured SLA shorthand behavior. Refusals name the field and
leave `OKR.md`, events, and partial state unchanged.

### D9 - schema binding and defensive rows

PASS. The schema owns the typed kind and user-facing accepted vocabulary.
Unknown kinds report `schema-unknown-type`; ragged rows report rather than
indexing past the row; non-template placeholders are not silently skipped;
template placeholders remain exempt; missing/unknown columns keep their
declared findings. The localized track fix also reads schema vocabulary rather
than adding a Chinese header list to lint.

### D10 - mutation sensitivity

PASS. Thirteen defect classes were exercised on fresh disposable copies with
`PERRY_HOME` unset and bytecode caches excluded:

1. Case-sensitive unfilled normalization: red, two focused failures.
2. English-only unfilled schema loading: red, four focused failures.
3. Separate blank implementation in lint or diagnose: red; the shared-binding
   sentinels observed the missing calls.
4. Mode-blind lint acceptance: red, fourteen parity failures including
   queue/no-SLA durations.
5. Interior `*` removal in lint only: red, five writer/lint disagreements.
6. Template placeholder guard removed: red, template placeholder reported.
7. Ragged-row typed guard removed: red with the expected indexing error.
8. Unknown typed-kind branch removed: red with an attempted call of the absent
   predicate.
9. Schema accepted vocabulary ignored: red; sentinel text disappeared.
10. `bad-typed-cell` error changed to warn: red.
11. Chinese pre-split `bad-typed-cell` filtered from migration: red; the
    `nothing to migrate` regression returned.
12. Diagnose, knowledge, or state changed to private date implementations:
    red independently for all three sentinel controls.
13. Localized track header canonicalization removed: red, four goals/migration
    failures across pipeline and queue/no-SLA.

The mode, decoration, placeholder, ragged-row, unknown-kind, vocabulary,
severity, Chinese-migration, and shared-date mutations failed for their focused
behavioral reason. No source grep or line-number assertion was counted as the
sole proof for these classes.

## Verification map

### V1 - six historical CLI behaviors

PASS. `tests.test_goals_writer` runs the actual writer subprocess on disposable
English and Chinese projects and retains the historical TASK-042 behavior under
this specification's canonical boundary.

### V2 - four-track differential sweep

PASS. A deterministic generated corpus covers dates, impossible dates, SLA
units, edge and interior decoration, placeholders, multilingual unfilled
idioms, prose, and random mixed strings across `main` project, `rel` pipeline,
`ops` queue with SLA, and `bare` queue without SLA. The final localized CLI
controls close the schema-language gap that the initial in-process sweep did
not expose.

### V3 - migration dry-run/apply

PASS. English and Chinese pre-split fixtures cover dry-run byte preservation,
apply classification, lossless success, second-run idempotence, false
conformance prevention, track-specific refusals, and localized migration
scratch context.

### V4 - fresh mutation copies

PASS. The thirteen classes above were run on fresh copies, with import routing
pointed at the copy rather than the live repository. Stock focused tests were
green; every listed mutation was red.

### V5 - payload and conformance contracts

PASS. The focused goals and conformance modules remained green. No intentional
consumer-shape change or new semantics/version declaration was introduced.

### V6 - focused and repository gates

Focused in-scope command:

```text
python3 -m unittest \
  tests.test_goals_writer \
  tests.test_diagnose \
  tests.test_conformance \
  tests.test_knowledge_cards \
  tests.test_knowledge_promotion \
  tests.test_work_modes \
  tests.test_migrate
```

Result: **497 tests, 82.075 s, OK**.

Final localized/work-mode command covered the two goals controls, localized
migration control, and the complete work-mode module. Result: **92 tests,
4.720 s, OK**.

Other exact results:

- `python3 bin/perry-lint`: rc 0, `0 error(s), 3 warning(s)`. All three warnings
  are the pre-existing BOARD/store drift for TASK-090, TASK-096, and TASK-104.
- `git diff --check`: rc 0, no output.
- Isolated rerun of
  `tests.test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`:
  **1 test, 3.235 s, OK**.

Repository-wide commands were run and not hidden:

```text
python3 tests/parallel
bash tests/run
```

Both reached **56 modules, 1642 tests**. They reported four red modules:

1. `test_board_render.py`: the live BOARD rendered two verbatim `Depends on`
   cells.
2. `test_store_is_canonical.py`: the fixture inherited the same three live
   BOARD/store drift rows instead of observing zero drift.
3. `test_router_budget.py`: `SKILL.md` is 21,036 bytes against a 20,480-byte
   cap, 556 bytes over.
4. `test_host_support.py`: one global dispatch-cap test observed two successes
   instead of three while two complete repository gates were deliberately run
   concurrently. Its isolated rerun passed.

The first two are the known BOARD/store drift explicitly excluded from this
review. The third is the known SKILL budget explicitly excluded from TASK-091.
The fourth was test-runner interference, is unrelated to every TASK-091 file,
and passed alone. None maps to D1-D10 or V1-V5, and none changes this verdict.

### V7 - independent reviewer

PASS. This review started from the written specification and prior review,
reproduced a new failure independently, required its repair, reran the original
fixture and a mutation of the repair, and did not self-award an implementing
session's result.

## TASK-044 boundary and not checked

The review checked only TASK-091's migration semantics: classification of
typed, unfilled, prose, track-invalid, and pre-split `Due` values, plus dry-run
and apply agreement for that classification.

It did **not** re-review TASK-044's project-wide safety guarantees: complete
diff presentation, dirty-tree policy, restore-point construction, rollback at
each write failure site, preservation of every unrelated row/file,
declaration authority, or the definition of a valid partially migrated
project. No TASK-044 regression was observed in the in-scope fixtures, but
those guarantees are not part of this PASS claim.

Also not checked, per the specification's boundary:

- Any real-project migration or cutover of gimegime-pmo, PolyForge, or another
  external live project.
- `viewer/parsers.py` cadence `parse_due` / `parse_frequency`, decision sunset
  parsing, or other date-shaped fields.
- TASK-090/092/093/094/095 behavior, renderer ownership, or the
  hand-edited-projection severity decision.
- Windows filesystem behavior or concurrent `perry-goals commit` writers.

## Final machine-readable verdict

```text
=== VERDICT ===
task: TASK-091
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-091-spec.md
focused: 497 tests green; localized/work-mode gate 92 tests green
mutations: 13 defect classes red on disposable copies
lint: 0 errors; 3 known store-drift warnings
diff_check: clean
snapshot: 6b7ab310e71cede9e68d8b3e3b373329f700d79ad099c47637cf1d2eb0244c85
repository_gate: 1642 tests; 4 unrelated red modules recorded above
boundary: TASK-044 safety guarantees not re-reviewed
=== END VERDICT ===
```
