# TASK-149 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-149-heading-defines` · Cycle time: ~13 min
> 2 files: `bin/perry-explain` (+68/−2), `tests/test_heading_defines.py` (312)

## The line is grammatical, not editorial

> **An id that OPENS a heading is being named. An id inside the sentence is
> being mentioned.**

`heading_subject(text)` strips markdown and leading decoration, then matches an
id **anchored at position 0**. A document that discusses an id is not thereby
the place that id lives.

## Two lines it deliberately did NOT draw, and said so in the docstring

- **"headings never define"** — takes `perry-explain ADR-001` with it, and every
  closed row whose only record is a journal heading.
- **A document-kind allowlist** (*"evidence records may not define"*) — it would
  have cleared the same red and been **wrong**, because the allowlist has to be
  kept in step with each project's layout and this script is meant to work on
  projects that never heard of Perry. **An evidence record may perfectly well
  define an id; what it must not do is define one by arguing about it.** A test
  pins exactly that: `test_the_rule_is_about_grammar_not_about_which_file_it_is_in`.

Nor is it tightened to a separator, because `# REL-002 spec` and
`# ADR-001 — PMO bootstrap` are the same act with different punctuation, and
pinning one would be a second invisible rule.

## Measured on this repository: five headings stop defining, all five were the defect

240 ids before and after — **none gained, none lost.**

| id | the heading that used to define it | the title it produced |
|---|---|---|
| TASK-068 | `### On TASK-068 specifically: correctly scoped…` | *"On  specifically: correctly scoped…"* |
| TASK-079 | `## The TASK-079 judgement: guarantee 4, not 3` | |
| TASK-089 | `## What does NOT hold, and belongs to TASK-089` | *"What does NOT hold, and belongs to"* |
| TASK-100 | `## 6 · The TASK-100 split was the right call…` | |
| TASK-101 | `### Live corpus and TASK-101 boundary` | |

**Every one had a real id-first definition that now wins**, and the hole in each
old title is where the id was cut out. `dangling` stays `[]`; `untitled` stays
`[]`.

## Item 2 — three definitions, each in its own test class so one cannot mask another

`## ADR-001 — PMO bootstrap` → `DECISIONS.md:3`, kind `section`, title *PMO
bootstrap*. A board row → kind `row`, title carried, status carried. A linkage
`- id: P-O1.1` → kind `linkage entry`, title from the following line. Item 3
drives the CLI for all three, human and `--json`.

## Item 4 — reverting moves one side only, and it is a test

`RevertingTheRuleSeparatesTheTwoCases` re-imports `perry-explain` and swaps in
the pre-TASK-149 rule:

- **reddens case 1** — `REL-00` goes from `defined=None` to
  `defined=notes/finding.md:3`. Asserted **in both directions**, so if the
  mutation ever stops biting, the test says so.
- **does not redden case 2** — ADR-001, TASK-042 and P-O1.1 are byte-identical
  under both rules. *A heading that names its subject satisfies the old rule and
  the new one alike.* The two cases are separable; no bigger finding.

## Item 5, and then the live document

On a copy, with the heading restored to the wording that caused this:

```
base ce89cde : dangling []   in_reports [DESIGN-900, ZZZ-404, ZZZ-405]   ← REL-00 LOST
this branch  : dangling []   in_reports [DESIGN-900, REL-00, ZZZ-404, ZZZ-405]
```

**After merging, the PMO restored the live heading** in
`TASK-141-dispatch-2026-08-21-result.md` to name the id again, deliberately, with
a comment saying it is the regression case. Verified in the main checkout:

```
dangling  : []
in_reports: ['DESIGN-900', 'REL-00', 'ZZZ-404', 'ZZZ-405']
```

The fix works on the document that caused it, and the document no longer has to
be written around the checker.

## Two boundaries noted rather than guessed at

`ID_RE.sub("")` still leaves a hole when a heading names a **second** id —
`### TASK-134 — probe row for the TASK-133 track experiment` titles as *"probe
row for the  track experiment"*. Pre-existing, separate. And a numbered
definition heading (`## 3. ADR-001 — foo`) would not define under this rule,
because stripping leading digits would also readmit `## 6 · The TASK-100 split…`.
**No instance exists here; the boundary is recorded rather than resolved.**

## Merged

`--no-ff`, after `merge-check` cleared the pair. Post-merge: **72 modules · 2078
tests · 1 red — TASK-153 only.**
