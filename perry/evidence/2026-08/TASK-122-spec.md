# TASK-122 — the repair path the tools advertise leaves the file damaged

> Source: `bin/perry_store.py § describe_cell`, `bin/perry_md_store.py`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — one padding rule, in the branch that already
>   distinguishes a table cell from a bullet slot
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Reproduced 2026-08-21, exactly

`describe_cell`'s disagreement branch defaults the padding to one space on each
side:

```python
bin/perry_store.py:344
return {"f": field, "lead": lead or " ", "trail": trail or " ",
        "disagrees": body}
```

For a **table cell** that is right: `render_line` joins on `|`, so `| ` + value
+ ` |` needs it. For a **bullet slot** it is wrong, because
`slot_descriptor`'s literal span **already carries the separator's whitespace**:

```
input           '- Repo layout: single'
literal span    '- Repo layout: '        ← the space after the colon is already here
lead / trail    ' ' / ' '                ← invented on top of it
rendered        '- Repo layout:  split '
```

Two spaces after the colon, and a **trailing space `git diff --check` reports**.

## Why this is not cosmetic

`bin/perry_md_store.py:972` prints, in its own refusal message:

> `` `<tool> render --write` to bring the file back in line. ``

So the tool **instructs the user into the damage.** They follow the advice they
were given and get a file with trailing whitespace their next commit hook or
`git diff --check` complains about — for a repair the tool told them to run.

## Deliverable

`render --write` on a file whose bullet value disagrees with the store produces
a line that is byte-correct: the store's value in the slot, and **no whitespace
the input did not have.** The table-cell path keeps its padding — the two are
already distinguished by `escape` in the descriptor, and this is the same seam.

Whatever shape you choose, the rule must be stated where the padding is decided,
in the voice of the surrounding comments, saying **why a bullet and a cell
differ** — otherwise the next reader re-introduces it.

## Verification — V3

1. **The reproduction above becomes a test and is byte-exact**:
   `- Repo layout: single` with a store holding `split` renders
   `- Repo layout: split` — one space, no trailing space.
2. **The table cell is unchanged**, proved on the same run: a board row whose
   cell disagrees still renders with its `| ` … ` |` padding. **Reverting your
   fix must redden case 1 and NOT case 2** — if one change reddens both, the two
   paths are not actually separated and you have found something bigger; say so.
3. **The blank-marker path is untouched.** `- Code repo path: —` with an empty
   stored value still renders `—` and does not acquire padding.
   `tests/test_md_store.py § test_the_declared_blank_marker_survives_the_bullet_path`
   must stay green without being edited.
4. **The advertised repair is clean end to end**: on a real disagreeing
   `.perry/config.md` copy in a temp directory, `render --write` followed by
   `git diff --check` reports nothing. Run it; do not assert it.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry_store.py`
- `bin/perry_md_store.py` only if its refusal message needs to change
- focused tests

## Out of scope

- The table-cell padding rule itself.
- `perry/` — no project state changes; `git diff -- perry/` must end empty.
- Anything about *when* a disagreement is reported, as opposed to how the
  repaired line is rendered.
