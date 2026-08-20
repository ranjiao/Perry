# TASK-122 — result

> Date: 2026-08-21 · Executor: claude-subagent · PR: https://github.com/ranjiao/Perry/pull/25
> Branch: `coding/task-122-bullet-padding` · Cycle time: ~50 min
> Code diff **2 files, +129/−5** — `bin/perry_store.py` +24/−5,
> `tests/test_md_store.py` +105/−0. (PR reports 32 files: the unpushed-ancestor
> sweep, fourth occurrence.)

## The rule, and where the why is written

> **"A table cell has boundaries; a bullet slot has neighbours"** — so only a
> cell may be handed padding it did not come with.

`render_line` joins cells on `|`, which carries no whitespace of its own, so a
cell arriving as `single` must leave as `| split |`. A bullet slot is joined on
`""` between literal spans that **already hold every character around it** — the
span before the slot in `- Repo layout: single` is `'- Repo layout: '`,
separator space included.

Mechanically it is **one variable**: `pad = " " if escape else ""`, used at both
places that invented padding — the disagreement branch (the reproduction) and the
whitespace-only branch. No new function, no branch keyed on a field name; the
same `escape` seam that already decided pipe-escaping now decides one more thing.

It also **corrected a docstring that had gone false**: `cell_text` claimed
escaping was *"the ONE thing that differs between a table cell and a bullet
slot"*. Leaving that would be the stale prose that lets the next reader
re-introduce the padding.

## Item 2, both ways, on one run

Reverting **only** the rule, tests untouched:

| reddened (3, all bullet) | did **not** redden (5, incl. the whole cell side) |
|---|---|
| `..._renders_byte_exact` | `test_a_table_cell_that_lost_its_padding_is_still_given_it_back` |
| `..._ends_without_a_trailing_space` | `test_a_track_row` (a board cell that disagrees) |
| `test_the_advertised_repair_survives_git_diff_check` | `test_a_config_setting`, both blank-marker tests |

The sharpest case-2 test is the first in the right column: it is the
**padding-invention path itself**, `single` → `| split |`. It stayed green.
**The two paths are separated by `escape`; there is no bigger finding here.**

The revert's own output is the bug verbatim:

```
AssertionError: Tuples differ:
  (2, '.perry/config.md:6: trailing whitespace.\n+- State root: perry \n', '')
  != (0, '', '')
```

## Item 4, run end to end rather than asserted

A real `.perry/config.md` copied to a temp git repo, **declared through
`perry-conform declare`** — an earlier attempt with a bogus gate line was
correctly refused by the ADR-004 gate and redone — store written, drift planted,
then the advertised repair:

```
perry-config: rendered .../.perry/config.md from 9 stored record(s)
git diff --check exit=0 (silent)
6:- State root: perry$        ← cat -et; the $ is end-of-line, no trailing space
```

It is now a test, **and it asserts the value was actually restored** — otherwise
a clean `--check` would just be the cleanliness of a file nothing happened to.

## One deliberate change beyond the reproduction

A bullet whose slot is whitespace-only and whose store gains a value:
`- Code repo path: ` → before `- Code repo path: value ` (trailing space), after
`- Code repo path: value`. It kept the input's own space (`pad or raw`) rather
than dropping it, so the line neither gains whitespace nor loses what the author
wrote. **No file in the repo exercises this** — Perry's config uses `—` for
empties — but leaving that branch on the old rule would have made the fix a patch
instead of a rule.

## It corrected the PMO, and the PMO was wrong

The dispatch prompt said `test_diagnose`'s red *"has since been fixed on a
sibling branch"*. **It has not.** TASK-126's fix is on PR #22, **unmerged**, so
`feat/work-modes` still carries the red and every worktree cut from it inherits
it. The agent measured its own baseline, found the red, and **reported it rather
than absorbing it** — which is the behaviour every dispatch prompt asks for,
applied to the prompt itself.

Worse, confirmed afterwards: the list is now
`['DESIGN-900', 'REL-00', 'ZZZ-404']`. **`ZZZ-404` came from
`TASK-126-spec.md` and `TASK-126-dispatch-2026-08-21-result.md`, both written by
the PMO** — the anti-vacuity example quoted in them. Writing the record about the
self-reference defect added a third instance of it. Third occurrence today;
first one caused while documenting the fix.

## Two questions handed back

1. A bullet slot genuinely empty in the source — `- Code repo path:` with no
   space — renders `- Code repo path:value`. Faithful to *no whitespace the input
   did not have*, and ugly. Unreachable from any current file; if a
   `- Label: value` shape is wanted, that is a **normalization** rule and belongs
   with whoever owns the config's shape, not in a renderer whose contract is
   byte-comparison.
2. Nothing outside `describe_cell` proves the two paths stay separated. If a
   third caller ever passes `escape=False` for a reason other than *"not in a
   table"*, the flag's two meanings come apart — worth a conformance-style check
   that the only producers of `escape=False` are slot descriptors.
