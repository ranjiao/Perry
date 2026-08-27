# TASK-154 — a title loses the subject's own id, not every id in the heading

**Merged locally 2026-08-28** from `coding/task-154-heading-title-hole` @
`46b1491`. Rung **V3**. `merge-check`: nothing new is red. `perry/` untouched.

## My spec named one call site; there were two

`ID_RE.sub("", …).strip(" —-–:·")` stood at line **345** (headings) **and at
line 246**, the branch that titles an id-named file from its H1.

Fixing only the one I cited would have satisfied my stated measurement and left
the identical hole one branch away. **Eight of the eleven titles that change on
this repository come from line 246** — the branch my spec never mentioned. Both
now call one helper, `heading_title(text, subject)`, sitting directly under
`heading_subject` and applying the same grammatical line to the other half.

*(The spec's line number was also off by one: 344 is `if not e["title"]:`.)*

## The decision, argued from what `user-load.md` actually says

**A mentioned id keeps its full form.** The rule is *"an ID never travels alone:
the first time an ID appears in any **user-facing output** it carries its human
name"*, and it was read exactly:

- It governs a **composed user-facing sentence**, not a stored datum. A title is
  the sentence an author wrote in their own heading; `perry-explain` **harvests**
  it, it does not author it. `label()` composes the user-facing form —
  `REL-002 ("Flake detector")` — and that is where the obligation already lives.
- **The file's own remedy for an unresolvable id is this script**: *"run
  `perry-explain <ID>`"*. That remedy only works **if the id is still there to be
  looked up.** Cutting `TASK-094` out of a title produces exactly what the same
  section calls the hardest case to resolve later — committed by the lookup
  itself.
- *"Prefer the name in prose, the ID in tables"* is advice to whoever **writes** a
  heading. It is not a licence for a reader tool to rewrite one, and it is a
  preference rather than a prohibition.

The alternative — expanding the mention into `why TASK-094 ("the store cutover")
had to land first` — was rejected for three reasons, and the third is decisive:
**titles flow onward into rows, standups and `--json`, where a fabricated
sentence is indistinguishable from a real one.**

## Eleven titles changed, every one gaining back a word

| id | before | after |
|---|---|---|
| TASK-013 | `finding` | `NS-01 finding` |
| TASK-034 | `one call answers both of  § 1.3's questions` | `one call answers both of DESIGN-004 § 1.3's questions` |
| TASK-051 | `/  — V4 review` | `/ TASK-052 — V4 review` |
| TASK-072–076 | `phase A…E: …` | `DESIGN-006 phase A…E: …` |
| TASK-103 | `locked at V5` | `DESIGN-007 locked at V5` |
| TASK-134 | `probe row for the  track experiment` | `probe row for the TASK-133 track experiment` |
| TASK-150 | `/  /  — result` | `/ TASK-151 / TASK-152 — result` |

The `phase A…E` rows are the sharpest case: **five titles that read as
unattached fragments now say which design they are a phase of.**

**Non-title fields: zero changes.** No `defined`, `kind`, `status`, `mentions`
or `in_tracking_doc` moved anywhere, so `--dangling` and `perry-diagnose`'s
`LOAD-*` inputs are untouched.

Repo-wide after, across 124 heading/document titles: **0 with a double space**
(4 before), **0 opening or closing on a separator**, **0 containing their own
id**.

## `heading_subject` is byte-identical, proved twice

Its body and docstring are unchanged, and `tests/test_heading_defines.py` passes
**unmodified** — and stays green **even with the old title line restored**,
which proves the two rules are separable and this change is confined to the
title half. TASK-149's monkeypatch mutation still bites.

Restoring the old line at both sites reddens **13 of 18** new tests, including a
repository-wide *"none of them has a hole in it"*. The mutation is pinned inside
the suite with a case for the line-246 branch, so removing **either** fix
reddens.

## One judgement documented rather than smoothed

For a co-subject heading `# TASK-150 / TASK-151 / TASK-152 — result`, TASK-150's
title keeps its leading slash. Adding `/` to the trim set would yield a title
**announcing someone else as its subject** — and `/` was not in the old strip set
either, so the separator vocabulary is unchanged by this row.

Three oddities remain (`OPS-001` = `—`, `USER-002` = `--claims vs --strict`,
`NS-01`, `TASK-044`), all `kind: row` — table cells an author typed, which this
row does not govern and which the old line never touched either.
