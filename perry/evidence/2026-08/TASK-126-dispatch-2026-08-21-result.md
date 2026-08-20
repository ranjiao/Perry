# TASK-126 — result

> Date: 2026-08-21 · Executor: claude-subagent · PR: https://github.com/ranjiao/Perry/pull/22
> Branch: `coding/task-126-dangling-self-reference` · Cycle time: ~35 min
> 2 code files: `bin/perry-diagnose` (+109/−…), `tests/test_diagnose.py` (+72/−…)
> **The suite is fully green for the first time: 65 modules · 1933 tests · 0 red.**

## The fourth mark, and why it is not in `report_lines`

The first three marks ask whether **this line** is a report. The fourth asks
whether **this id** has one — which cannot be decided from a single file, so it
lives in `split_dangling` as a second pass rather than in `report_lines`. Two
independent conditions, both required:

- the **document** names one of this checker's findings or tests anywhere in it
  (`document_reports_on_a_check`, reusing `names_a_check` over the whole file —
  no second vocabulary is introduced);
- the **id** is one the project has already reported on.

Option 2 from the spec — a distinct fourth *outcome* — was rejected with an
argument: it needs the identical classification work, buys nothing structurally,
and would have forced rewriting an existing assertion.
**Option 1 landed with zero existing assertions changed.**

## The path exemption was considered and rejected, and the rejection is testable

Re-run independently by the PMO, not accepted from the agent's report. A temp
project with an `evidence/`-shaped dispatch record that **does** name `LOAD-02`
and a `test_` function, and is genuinely blocked on two ids:

```
dangling            : ['QQQ-77', 'ZZZ-404']
dangling_in_reports : ['LOAD-02']
```

**A wholesale `perry/evidence/**` exemption would have printed `dangling: []`.**
The shipped rule contains no path and no English reading.

The simple direction also holds: a project whose only content is
`Blocked on ZZZ-404 until Friday.` still reports `dangling: ['ZZZ-404']`.

## On this repository

```
before   dangling: ['DESIGN-900','REL-00']   dangling_in_reports: ['ZZZ-404']
after    dangling: []                        dangling_in_reports: ['DESIGN-900','REL-00','ZZZ-404']
```

Exactly two ids moved between the lists. **Both stay visible; neither was
added to an exemption list** — there is no id list in the change. `git diff --
perry/` is 0 bytes: no record was edited to make a checker pass, which was the
row's hard bound.

## Both halves proved load-bearing

Reverting the mark reddened **four** tests, three of them naming the two halves
separately:

| test | failure |
|---|---|
| `test_perry_itself_passes_its_own_id_checks` | `['DESIGN-900','REL-00'] != []` |
| `test_perrys_own_repository_reports_the_exemption_it_used` | `'REL-00' unexpectedly found` |
| `test_a_record_narrating_a_check_it_reported_is_not_a_reference` | `['ZZZ-404'] != []` |
| `test_a_record_about_a_check_still_reports_an_id_it_never_reported_on` | `['ZZZ-404','ZZZ-405'] != ['ZZZ-405']` |

A fifth new test — `test_a_document_that_reports_on_nothing_is_still_a_reference` —
correctly stayed **green** under the revert. It is an anti-vacuity test, and its
staying green is the evidence that the other four are not measuring the same thing.

Tests 1930 → 1933, none weakened.

## One note for the PMO, raised by the agent

`split_dangling` no longer early-exits on the first live mention — it must read
every mention to decide the id half. `perry-explain` caps mentions at 40 per id
and the two predicates share one per-file cache, so the cost is bounded; the
suite ran 155s against a 220s baseline, though that comparison is dominated by
the removed red-test retries rather than by this change.

## PR hygiene

PR #22 reports 28 files and +1911/−73. **The code change is 2 files, +162/−19**;
the rest is the unpushed-ancestor sweep — `feat/work-modes` is 14 commits ahead
of origin, so every PR cut from it carries those commits in its diff until the
branch is pushed. Third occurrence.
