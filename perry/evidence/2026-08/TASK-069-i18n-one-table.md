# TASK-069 — one alias table, read; not four, hand-carried

> Rung: **V3**. Every claim is a run or a mutation.

## The finding, sharpened twice

Raised as *"~20 regexes hand-carry aliases while the schema already holds the
table"*. Both halves reproduced, and the shape was worse than that: not a
missing mechanism but a **split brain**. The schema declares 34 heading aliases
plus fields and columns, and **five** tools read it — `perry-lint`,
`perry-conform`, `perry-migrate`, `perry-goals`, `perry-diagnose`. The three
that did not were exactly the three on the state **read path**.

Then the count itself was wrong, and this file corrects it rather than carrying
it: `bin/perry-task` measured **zero** all along. The earlier "24 CJK lines" was
counting comments and docstrings. Two tools, not three.

**And the sharpest form was in `viewer/parsers.py`** — the read side of all
three frozen contracts. It already had `alias("headings", name)` reading the
schema, and **eight call sites hand-carried the Chinese spelling anyway, in the
same file**. The mechanism existed; the call sites went around it.

## What landed

- `viewer/parsers.py` — all 8 sites now `_section(text, *alias("headings", …))`.
  `Phase Scope Reduction Rule` gains a spelling for free: the schema declares
  two Chinese forms and the call site carried both, so a third added to the
  schema now reaches it.
- `bin/perry-state` — `TRACK_COLUMNS`, a hand-copy of `i18n.columns` **whose own
  comment named the schema as its source**, becomes `track_columns()` reading it.
- The one heading alias transcribed into a `perry-state` call site now resolves
  through `parsers.alias`.

## The duplicate the fix itself created

`bin/perry-state` briefly grew its own `heading_spellings()` — **a second
implementation of `alias()`, added by the fix for having two implementations.**
Removed; it calls `P.alias` now, and `test_the_alias_reader_is_one_function_not_one_per_tool`
asserts the function does not come back.

## Verified on shapes, not on fixtures Perry generated

A fully Chinese track register — `## 轨道`, `| 轨道 | 模式 | 主线 | 阶段序列 |
在制上限 | 时限 | 周期 | 默认验证级 |`, stages written with a Chinese comma —
parses to track name, mode, three split stages and an SLA. A fully Chinese
`OKR.md` — `## 使命`, `## 运行原则`, `## 反目标` — parses to mission, one
principle, one anti-goal, one objective. Both exercise TASK-078's separator work
and this row's together, which is what a real localized project actually looks
like.

## The guard is the category

`tests/test_i18n_one_table.py` asserts **no schema-declared alias appears as a
literal in any code line** of the three read-path tools, budget zero for each.
A ninth copy fails the build rather than being noticed in review — which is the
difference between fixing these instances and fixing what produced them.
