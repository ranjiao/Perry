# TASK-283 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — the acceptance is a count and a mutation
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: `P003-O2-KR1`

## Why this row matters more than its title, and a KR is affected

`bin/perry-lint § _track_context` resolves a board row's `Track` cell against
the register. Measured on `main` at `5e88be8`:

- `:680-683` walks up until `P.configured(root)` — **that half is correct**, and
  is `TASK-247`'s fix.
- `:684` then reads `root / ".perry" / "config.md"` and parses it inline
  (`:690-708`), **while `.perry/config.jsonl` sits beside it holding the same
  nine records**. It never consults the store.

So on a store-only project it returns `{}` — the permissive "undeclared" case
its own docstring specifies. That is strictly better than reading a *foreign*
register, and it is still not reading the register.

**The phase consequence, which is the reason this is P1.** `P003-O2-KR1` reads:

> Call sites in `bin/` that read the track register from `.perry/config.md` as
> truth while `.perry/config.jsonl` exists, excluding the drift-comparison
> reader — **target 0**

Its baseline enumerated **four `parse_tracks` call sites**, and those are fixed.
`_track_context` is a **fifth site that the enumeration never named**, because
it does not call `parse_tracks` — it carries its own inline parser. It is not
the drift-comparison reader, so the exclusion does not cover it.

**Therefore `P003-O2-KR1` is not at 0, and its metric currently says otherwise.**
Correcting a KR is the `goals` lane's write, not this row's and not `work`'s
(`SKILL.md § The hand-off contract`). This spec states the finding; the hand-off
is printed at close and the edit is `goals`'.

## The shape to copy — it already exists, twice

`bin/perry-state § declared_tracks_detail` (`:1160`) is the answer this project
already settled on: it returns `(tracks, source)`, where `source` is `store`,
`absent`, or one of `TRACKS_STORE_UNUSABLE` — *"in which case the tracks
returned are the PROJECTION's and the caller must not treat them as truth."*

`bin/perry-goals:2161` consumes it and warns when the register and the
projection disagree. `bin/perry-state:218` consumes it too.
`declared_tracks`'s own docstring says it outright:

> **Anything that can [act on the difference], uses `declared_tracks_detail`** —
> a caller that silently takes the projection here is the defect the V4 round 1
> review found.

`_track_context` is exactly such a caller. **This is a data-authority
conversion, not a new mechanism, and not an existence check.**

## Files in scope

- `bin/perry-lint` — `_track_context` (`:654-709`), its cache `_TRACK_CONTEXTS`, and its one call site at `:975`.
- `tests/test_track_register_source.py` — the guard that already exists for this defect class; extend it rather than starting a new file.
- `tests/` — a fixture for the store-only project shape.

## Deliverable

`_track_context` resolves a track through the store when there is one, and can
say when it did not.

1. It goes through `declared_tracks_detail` (or states in one line why that
   function cannot serve it and what it uses instead). **No second inline
   parser of the track register survives this row.**
2. On a store-only project — `.perry/config.jsonl` present, `.perry/config.md`
   absent — a declared track resolves to its row rather than to `{}`.
3. When the store is present but unusable, the caller can tell: the projection's
   answer is not silently returned as truth. Follow whatever
   `TRACKS_STORE_UNUSABLE` already means; do not invent a second vocabulary.
4. The `_TRACK_CONTEXTS` cache is keyed on something that stays correct when the
   source changes. It is keyed on `str(cfg)` today — a path that may not exist.

## Verification

1. **Reproduce the defect first**, on a `git archive` copy: build a store-only
   project (`.perry/config.jsonl`, no `.perry/config.md`), lint a board whose
   rows carry a declared track, and show `_track_context` returning `{}`. That
   before-state must be in the evidence.
2. **After the change**, the same fixture resolves the track to its row.
3. **A control**: a genuinely undeclared track still returns `{}` on both. A fix
   that resolves everything passes item 2 and is wrong.
4. **A second control**: on a project with *both* files present and agreeing —
   this repository — every current `perry-lint` finding is unchanged. Diff the
   full `perry-lint --root .` output before and after; it must be identical.
5. **Mutation**: revert the store read and show a named test go red. Anchor by
   line number *with an assert on the old text*, clear `__pycache__`, wait past
   the whole-second boundary, restore against **pre-mutation** bytes. A green
   mutation is the finding.
6. Full suite no redder than baseline; `perry-lint --root .` at 0 errors.

## Bound

```
Enumeration: grep -n "config\.md" bin/perry-lint bin/perry-state bin/perry-goals
             bin/perry-task bin/perry-diagnose bin/perry_md_store.py
             — then keep the hits that READ the register as truth
Size:        1 on 5e88be8 — bin/perry-lint:684 (_track_context)
Excluded:    bin/perry-state:1171 (declared_tracks_detail's own fallback, which
             fires only when the store is absent — the legitimate case);
             bin/perry_md_store.py:197 (TRACK_COLUMNS, a column-shape
             declaration, not a register read); perry-goals:2177/2185/2192 and
             perry-diagnose:2230 (message text naming the file to a human)
Remainder:   the drift-comparison reader, excluded by the KR itself
```

A sixth site found by the round is **a new row, not a widening of this one**.

## Out of scope

- Editing `perry/phase/003-linkage.md` or `perry/phase/003-storage-code.md` to
  correct `P003-O2-KR1`. Those are `goals`-owned; the finding is handed off, not
  written. `perry-goals krs` is read-only and there is no KR write path — that
  gap is `TASK-264`.
- `.perry/config.md`'s status as a projection. `USER-903` already decided it;
  this row does not reopen it.
- The four original `parse_tracks` sites. They are fixed and are not re-derived
  here.
