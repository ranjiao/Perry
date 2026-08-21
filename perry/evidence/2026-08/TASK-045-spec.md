# TASK-045 spec — retire the runtime tolerance branches, behind the conformance marker

**Row**: `TASK-045` — *Retire the runtime tolerance branches, behind the
conformance marker*. Rung **V4**. Depends on `TASK-044` (done, V4) and
`TASK-047` (done, V5) — both closed.

## The precondition, verified 2026-08-21 before dispatch

The row sat blocked for three days on a chain the journal spells out: `044 →
047 → 045`, and the blocker was that **the gate still shipped `advisory`**.
Retiring tolerance while the gate is advisory means an unmigrated project
breaks **on read**, and ADR-004 says in the same paragraph that reading stays
deterministic and ungated — *"a front-end querying state is the reason
DESIGN-005 exists."*

That is now resolved. Checked, not assumed:

```
$ python3 bin/perry-conform status
🔖 Conformance · Perry · state root: perry · shape version 2 · gate: enforce
```

`TASK-044` done at V4, `TASK-047` done at V5. The chain is complete.

## The constraint, carried verbatim from the row's own 2026-08-18 note

> **NOTE FOR WHOEVER TAKES THIS: 'retire tolerance' does NOT mean delete every
> fallback.** The same table makes adopt and diagnose MORE tolerant — they must
> read any shape to propose a migration — and 'reading is tolerant, writing is
> strict' is a stated rule in three files. The branches to retire are the
> per-shape ones in the five named tools; the tolerant readers stay.

**If you delete a fallback that `adopt` or `diagnose` needs, you have failed
this row even if every test is green**, because their corpus is a foreign
project and this repository's tests mostly are not.

## The scope — five tools, named on the row

`bin/perry-state` · `bin/perry-task` · `bin/perry-goals` · `bin/perry-decide` ·
`bin/perry-lint`

ADR-004's *"Where tolerance lives now"* table is the authority for which
branches go and which stay. **Read that table first and quote it in your
report**; a list you derive by reading the code instead is a second opinion
about a decision that has already been made.

## What "a per-shape tolerance branch" means, and what it does not

**Retire**: a branch in one of the five tools that accepts a shape the declared
schema does not describe — an older column set, an alternative heading, a
pre-migration cell format — and silently reads it anyway. Behind an `enforce`
gate that branch is unreachable for a declared file and a lie for an undeclared
one.

**Keep**:

- anything `adopt` or `diagnose` reaches. They parse by definition.
- anything reading a **foreign** project — `parse_board` / `parse_okr` with no
  store, `parse_tracks`, `read_conformance`, `parse_phase`, `parse_decisions`.
- the *tolerant reader* half of "reading is tolerant, writing is strict". This
  row retires **per-shape** branches, not the posture.

If a branch is genuinely ambiguous between the two, **leave it and list it**.
An honest list of five undecided branches is worth more than a confident
deletion of one that adoption needed.

## Verification

1. **A count, and the enumeration behind it.** How many per-shape tolerance
   branches existed in each of the five tools, how many were retired, and — for
   every one left standing — one sentence naming who still needs it. A number
   with no enumeration is not this row's deliverable; two earlier rows on this
   project failed by fixing the named instance and leaving its siblings.
2. **Adoption still works on a project that never migrated.** Build a fixture
   with a pre-migration shape, run `perry-lint --root` and the adoption reader
   against it, and show they still read it. This is the check that catches the
   failure mode the note warns about, and it must be a **new** test, because
   the existing suite mostly runs on migrated fixtures.
3. **A declared file that violates its shape is refused, not tolerated** — the
   thing the gate flipping to `enforce` was supposed to buy.
4. **Mutation.** For each retired branch, restoring it must redden a specific
   test. If restoring a branch reddens nothing, the deletion was untested.
5. `perry-lint --root .` — 0 errors.

## Out of scope

- **Do not touch `schema/state-schema.json`.** If a declared shape genuinely
  has to move, **stop and report**.
- **Do not flip the gate, and do not run `perry-conform declare`.** That
  command is the user's alone.
- **Do not touch `perry/`.** `git diff -- perry/` must be empty.
- `bin/perry-tasks` and `bin/perry-okr` are **not** among the five. TASK-040 is
  editing `perry-tasks` in parallel.

## Ground rules

- Branch `coding/task-045-retire-tolerance`, commit there, **do not open a PR**
  and **do not push**. The PMO merges locally.
- Measure your own baseline before touching anything. Do not take a red count
  on trust — **the red set on this repository differs by interpreter**. Use
  `/usr/bin/python3` and say which you used.
- `python3 tests/parallel -j 4`. Never `bash tests/run` while another suite is
  running on this machine; two concurrent runs pollute each other and
  `test_host_support`'s dispatch-cap test reads machine-wide state.
- Known pre-existing reds on `/usr/bin/python3`: `test_diagnose` (two
  failures — TASK-153, and `['TASK-007','TASK-9999']`) and
  `test_contract_invariance` (`intake.oldest_undischarged was NoneType, now
  int` — a union-typed key, diagnosed in
  `evidence/2026-08/contract-invariance-union-types.md`, **not yours to fix**).
- **This row is V4.** Its deliverable is a count and an enumeration, so a
  reviewer will check the enumeration, not the diff. Write the report for that
  reader.
