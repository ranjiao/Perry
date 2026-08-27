# TASK-154 spec — a heading naming a second id leaves a hole in the title

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Reproduced 2026-08-28.

## The measurement

`bin/perry-explain:344`:

```python
t = ID_RE.sub("", strip_md(h.group(1))).strip(" —-–:·")
```

`ID_RE.sub("", …)` strips **every** id in the heading, not just the subject the
heading defines. Run against three real shapes:

```
heading: TASK-050 — why TASK-094 had to land first
title  : 'why  had to land first'          ← a hole, and a double space

heading: TASK-050 supersedes TASK-049
title  : 'supersedes'                      ← the title is one dangling verb

heading: ADR-001 — PMO bootstrap
title  : 'PMO bootstrap'                   ← correct
```

**The second case is worse than the row's title suggests.** A heading whose
whole content is a relation between two ids reduces to a verb, and that verb
becomes the id's name everywhere `perry-explain` is consulted.

`reference/user-load.md` requires every id to travel with its human name. A
title of `'supersedes'` satisfies the letter of that and defeats it entirely.

## Why the current line is the way it is

`heading_subject` (line 150) got this exactly right one level up, and its
docstring is worth reading before you touch anything: **an id that *opens* a
heading is being named; an id inside the sentence is being mentioned.** That
distinction was fought for — TASK-149 — and it must survive.

The title line never learned it. It strips all ids because *the subject's own id
must not appear in its title*, and stripping everything was the cheap way to
guarantee that.

## The fix has to keep three things true

1. **The subject's own id is not in its title.** `ADR-001 — PMO bootstrap`
   still yields `PMO bootstrap`, not `ADR-001 — PMO bootstrap`.
2. **A mentioned id survives in the title**, because it is part of the sentence
   that names the subject.
3. **No double spaces, no dangling separators.** `strip_md` and the `.strip()`
   set exist for that; whatever you do must not reintroduce the hole in a new
   place.

Decide and argue: does a mentioned id keep its **full form** (`TASK-094`), or
does the title get rebuilt some other way? A title reading *"why TASK-094 had to
land first"* is honest and is also an id inside a title, which is a shape
`reference/user-load.md` has opinions about. **Read that file and say whether it
permits this.**

## Verification

1. The three cases above produce sensible titles. Paste them.
2. **`heading_subject`'s rule is untouched** — an id that opens a heading is
   still the subject, an id inside the sentence is still a mention. TASK-149's
   tests still pass, unmodified.
3. **On this repository, no title regresses.** Compare `perry-explain`'s title
   for every id before and after; any that change must change for the better and
   you must list them.
4. Mutation: restoring the old line reddens a test that names the hole.
5. `perry-lint --root .` — 0 errors.

## Out of scope

- **The `dangling` / `dangling_in_reports` machinery.** TASK-179 owns the
  standing tension about ids quoted in records; this row is only about the
  *title* a heading produces.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/` must
  end empty.

## Ground rules

- Branch `coding/task-154-heading-title-hole`, commit there, **no PR, no push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly — Perry is stdlib-only as of
  tonight and that flag is what proves it.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`.
- Expected baseline: roughly **80 modules · ~2393 tests · 2 red** —
  `test_contract_invariance` and `test_diagnose`. **Neither is yours**, and
  `test_diagnose`'s queue-reconcile failure is **order/parallel sensitive**: it
  fails under `-j 4` and passes in a smaller run. Do not chase it.
