# TASK-095 — PMO close verification

> Written 2026-09-02 by the PMO before closing the row, at the user's
> instruction to "confirm it, and if it is really done, close it".
> Measured at commit `c518b9d`, read with `git show HEAD:<path>` rather than
> from the working tree — `TASK-247`'s agent was concurrently editing
> `bin/perry-diagnose` and `bin/perry-lint` in the same tree, so the tree was
> a moving target and the commit was not.

## Why this file exists

The round-6 V4 review PASSED on 2026-08-29 and the row was never closed.
`perry-lint --reviews` cannot read that PASS: it reports
`evidence/2026-08/TASK-095-round6-v4-review.md:538` as **verdict-malformed**
(the block is missing `checked` and `not-checked`) and the criteria as
**criteria-unbounded** (`TASK-095-spec.md` carries no `## Bound`).

Closing at V4 over a verdict no checker can read is how `TASK-079` and
`TASK-108` became `v4-close-without-verdict` — the rung claimed, not run. So
this closure does not rest on the review alone. It rests on the measurement
below, and the malformation is recorded rather than papered over.

## The deliverable, and what was measured against it

`phase/003-storage-code.md` states it: **"four `parse_tracks` call sites read
`.perry/config.jsonl`"**, verified by **"the four named lines no longer call a
markdown parser"**. The baseline named `bin/perry-task:6680`,
`bin/perry-diagnose:1888`, `bin/perry-goals:2102`, `bin/perry-state:139`.

### 1 · Call sites, counted rather than grepped for a name

| File | `parse_tracks` occurrences | live call sites |
|---|---|---|
| `bin/perry-task` | 3 | **0** — `:3099`, `:6484`, `:6923` are all comment or docstring |
| `bin/perry-diagnose` | 1 | **0** — `:2053` is a comment |
| `bin/perry-goals` | 1 | **0** — `:578` is a docstring |
| `bin/perry-state` | 10 | **1** — the definition at `:643`, eight comments, and one call at `:1174` |

The distinction matters and is the phase's own operating rule: counting the
name returns 15, counting call sites returns 1.

### 2 · The one remaining call is guarded, read from the control flow

```python
def declared_tracks_detail(project_root: Path) -> tuple[list[dict], str]:
    stored, source = stored_tracks(project_root)
    if stored is not None:
        return stored, source                      # store wins, returns early
    cfg = project_root / ".perry" / "config.md"
    if not cfg.exists():
        return [dict(DEFAULT_TRACK)], source
    return parse_tracks(cfg.read_text(...)), source  # only when stored is None
```

`parse_tracks` is unreachable while the store is present. That is exactly what
`P003-O2-KR1` asks for — the markdown is a fallback, not an authority.

### 3 · Behavioural test, with a working control

Reading control flow is not proof that the built code does it. A fixture was
built with a store and a markdown table that **contradict each other** — the
store declares track `alpha`, the markdown declares track `beta`:

```
both present, contradicting   → tracks: ['alpha']   source: store
store removed                 → tracks: ['beta']    source: absent
```

**The second line is the control.** The test could have returned `beta` in the
first case and did not, and it does return `beta` once the store is gone — so
the assertion is falsifiable rather than true by construction.

### 4 · No second reader bypasses the funnel

`parse_tracks(` is defined and called only in `bin/perry-state`. `bin/perry-config`
reads `## Tracks` because it is the tool that renders and byte-compares that
file — the drift-comparison reader `P003-O2-KR1` excludes by name.

## Verdict

**The deliverable is met.** Four baseline call sites, zero remaining; the one
survivor is a guarded fallback whose guard was tested with a control.

## What this file does NOT claim

- It does not supply the round-6 review's missing `checked` / `not-checked`
  fields. Those state what the **reviewer** examined; writing them from outside
  the review would make the rung a label instead of a record.
- It does not re-run the round-6 review. This is a PMO verification of the
  deliverable, not a fresh V4.
- `perry-lint --reviews` will still report the round-6 file as malformed after
  this closure. That is correct and should stay visible.
