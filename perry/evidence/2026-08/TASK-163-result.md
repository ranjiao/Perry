# TASK-163 — a dash is not a clock, to either reader

**Merged locally 2026-08-28** from `coding/task-163-a-dash-is-not-a-clock` @
`d9bb5b8`. Rung **V3**.

## My spec named one call site; there were two, again

`bin/perry-task:5519` (board-derived) and `:5716` (record-derived) carried the
raw-truthiness expression **verbatim**. Fixing only the one I named would have
left the two `list` paths disagreeing about a dash **for the same reason the two
tools did**. They are now one function called from both.

**That is the third time tonight a spec of mine located a duplicated expression
once**: TASK-178's `serve.py` had a fifth reference, TASK-154's title line had
two call sites, and this.

And the predicate reads **two** hand-edited date cells, not one — `stage_since`
had the same raw truthiness as `arrived`.

## `ABSENT` vs `is_blank_cell`, measured rather than assumed

`is_blank_cell` is a **strict superset**, and on every input they disagree it is
the one that is right:

```
agree      '' '—' '-' '–' 'n/a' 'na' 'tbd' '无' 'none' '  ' 'None' 'TBD'
           '2026-09-30' 'soon' '0'
disagree   '?' '？' 'N.A.' 'TBA' 'N/A.' '待定' '不适用' '暂无' '无。' '**—**' '`-`'
```

`is_blank_cell` reads `schema § i18n.blank_cell` through `_blank_key`, which
strips markdown decoration and terminal punctuation. `ABSENT` is a hardcoded
literal set matched with a bare `.lower()` — **the fourth copy of the list the
schema was created to unify**, monolingual-plus-one-token and blind to
decoration.

**Unifying them is a follow-up, and it said why**: `ABSENT` is read by
`evidence_paths`, the relations parser and `parse_depends` — different columns —
so swapping it in would silently change what counts as "no dependency" and what
counts as an evidence span. The cost of leaving it is named:
**`Depends on: 待定` currently parses as a real dependency id.**

## Why one test could not have caught this

The fixture writes `| … | triaged | — | — |` **directly into `BOARD.md`**,
because a tool-written board cannot show the defect — the writer emits an empty
string.

Each case asserts **both tools on the same row in one tuple**, because two
single-tool tests in two classes would both have stayed green while the tools
disagreed — **which is precisely the state this row found.**

```
before   dash: (no_computable_age False, sla_no_clock True)   DISAGREE
after    dash: (True, True)                                   AGREE
```

Mutation reddens 8 assertions, all naming the dash, including six subTests over
every declared spelling of nothing. `rows_with_no_computable_age` on this
repository is `[]` before and after — the writer emits `""`, so a correct fix
moves nothing here.

## A stale comment it moved rather than left

`tests/test_queue_sla.py` carried *"the em-dash spelling is covered separately
below, because the two readers do not agree about it and that is a finding
rather than something this change gets to alter."* That sentence stopped being
true with this commit; it now points at the new class.
