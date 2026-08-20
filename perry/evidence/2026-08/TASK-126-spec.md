# TASK-126 — closing the dangling-id row requires writing the record that re-dangles it

> Source: `perry/evidence/2026-08/TASK-113-dispatch-2026-08-20-1813.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: no — one rule inside one checker
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked — this serves no phase-002 KR

## The state, measured 2026-08-20

`tests/test_diagnose.py` has two red tests and they are **the last red in the
suite**, on CI and locally:

```
test_perry_itself_passes_its_own_id_checks
  AssertionError: Lists differ: ['DESIGN-900', 'REL-00'] != []
test_perrys_own_repository_reports_the_exemption_it_used
  AssertionError: 'REL-00' unexpectedly found in ['DESIGN-900', 'REL-00']
```

TASK-113 fixed exactly this and measured `dangling: []` in its own worktree.
It went red again **because of the record written to close it.** Every live
mention of both ids is in one file:

```
REL-00      LIVE   TASK-113-dispatch-2026-08-20-1813.md:11, 18, 35
            report TASK-113-dispatch…:57, 89 · TASK-113-spec.md:37, 40
            report journal/2026-08/2026-08-20.md:514   (inside `## V5 sign-off`)
DESIGN-900  LIVE   TASK-113-dispatch-2026-08-20-1813.md:16
            report TASK-108-dispatch-2026-08-20-1547.md:112
```

Every other mention in the repository **already classifies correctly**. The
three marks in `bin/perry-diagnose § report_lines` work; what they do not cover
is a paragraph describing the check in plain English — *"prose about a check
counted as the thing the check measures"* — with no finding code and no
`test_` name in the same paragraph.

**So the row cannot be closed without writing a record, and writing the record
reopens it.** That is the defect, not the two ids.

## Deliverable

`LOAD-02` can reach zero on a project that has documented its own fix. Either:

1. the structural marks are extended so that a document whose **subject is the
   check** stops counting as a live reference — without its prose being
   edited — or
2. the check reports a distinct reason when an id's only live mentions are in
   documents about itself, and the two tests assert that reason.

**Whichever you choose, argue it in the code where the existing three marks are
argued.** That block already explains why the mark is scoped to the paragraph
and not the line; a fourth mark, or a fourth outcome, belongs in the same voice
with the same kind of reason.

## What you must not do

- **Do not edit `perry/evidence/2026-08/TASK-113-dispatch-2026-08-20-1813.md`,
  or any other record, to make the check pass.** Rewording a true account to
  satisfy a checker is the failure this row exists to end, and the next close
  would reproduce it. `git diff -- perry/` must be empty at the end, exactly as
  it was TASK-113's hard bound.
- **Do not add either id to an exemption list.** TASK-113's record states that
  the two ids stay *"visible, not deleted"*.
- **Do not widen the rule until it stops discriminating.** `modes/`,
  `reference/` and `README` prose that names an id which resolves to nothing is
  still a finding. The guard below is how you show you did not.

## Verification — V3

1. `python3 bin/perry-diagnose --only=user_load --json --root .` reports
   `dangling: []` for this repository, with `DESIGN-900` and `REL-00` visible
   in whatever list your chosen option puts them in.
2. **Anti-vacuity, both directions**, re-run rather than asserted:
   - a temp project whose only content is `Blocked on ZZZ-404 until Friday.`
     still reports `dangling: ['ZZZ-404']`;
   - a temp project containing a genuinely live reference inside an
     `evidence/`-shaped file still reports it. A fix that exempts
     `perry/evidence/**` wholesale fails this.
3. **The new mark is proved to be load-bearing**: revert it and watch both
   `test_diagnose` tests go red again.
4. The two named tests pass, and `tests/test_diagnose.py` is not weakened —
   if you change an assertion, say which and why in your result.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, and `git diff -- perry/` empty.

## Baseline

Measure it in your own worktree. `test_diagnose` should be the **only** red
module; if you see more, say so — three others were fixed today and one of them
(`test_host_support`) was a GNU/BSD `stat` defect that had been red on CI since
long before.

## Files in scope

- `bin/perry-diagnose`
- `tests/test_diagnose.py`

## Out of scope

- `TASK-112` — the sign-off drafting guard that cannot describe itself. Same
  family, different tool, its own row.
- Any change under `perry/`.
