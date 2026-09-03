# TASK-155 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — the property is measured, not judged
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: intake / queue · `Arrived` 2026-08-21
- **Dependencies**: —
- **KR linkage**: unlinked

## Why this row exists, and the one word in its title that is now false

The row was filed as *"the register `updated` field carries two facts, so
appending an edge **silently** re-dates every asserted number in the file"*.

**The two-facts half is true and unfixed. "Silently" is false**, and has been
since before the row was filed. `bin/perry-goals:2055-2062` prints, on every
write that would re-date an asserted KR:

> ⚠ this write bumps `updated`, which is also where `current`'s assertion date
> is read from (`asserted_scope: register` — there is no per-KR date). N KR(s)
> with an asserted `current` will read as freshly asserted and lose any
> staleness signal: … Nothing about those numbers changed.

The ambiguity is in fact disclosed at **three** layers, and fixed at none:

| layer | what it does | where |
|---|---|---|
| the contract | emits `asserted_scope: "register"` beside the date "so it cannot be read as *when this number was arrived at*" | `schema/goals-list-contract.md:144`, `bin/lib/__init__.py:705` |
| the writer | warns on stderr, naming every KR it is about to re-date | `bin/perry-goals:2055-2062` |
| the reader | reports `asserted` / `stale` / `stale_ids` counts | `perry-state § attribution.kr_currents` |

So this row is not "nobody noticed". It is **a defect that has been carefully
described three times and fixed zero times**, and the description is now doing
the work the fix should do. That is worth stating plainly in the round: the
cheapest wrong outcome here is a fourth disclosure.

## What is actually true, measured 2026-09-03 on `5c76aa2`

- `perry/phase/003-linkage.md` carries one `updated:` in its frontmatter —
  `2026-09-02T11:51:23Z`.
- It is written at exactly one site: `reg.set_updated(stamp)`,
  `bin/perry-goals:2063`, reached by every `link-*` write.
- It is read as a **freshness** signal at `bin/perry-state:1971`
  (`idle_days`) and carried into the payload at `:1968`, `:2160`, `:2381`.
- `attribution.kr_currents` today: `total 6 · asserted 3 · unasserted 3 ·
  measured 0 · stale 0`.

The consequence: **`stale` can only ever be computed against a register-wide
date**, so any link write resets the staleness of all asserted KRs at once, and
`stale: 0` is not evidence that the three asserted numbers are fresh.

## Files in scope

- `bin/perry-goals` — `set_updated` (`:1581`), its one call site (`:2063`), and the warning at `:2055-2062` that becomes redundant if the fix lands.
- `bin/lib/__init__.py:705` — where `asserted_scope` is set.
- `bin/perry-state` — `:1968`, `:1971`, `:2160`, `:2381`, the readers.
- `schema/goals-list-contract.md` — the emitted contract. **A contract shape change is versioned**, so state the version consequence rather than editing quietly.
- `perry/phase/003-linkage.md` — the live register. **`phase/` is the `goals` lane's file and `work` is not its writer.** If the fix needs a per-KR field written into it, that write is a hand-off: state it and stop.
- `tests/` — the guard.

## Deliverable

A KR's asserted `current` carries **its own** assertion date, so that appending
an edge to the register cannot re-date a number nobody re-measured.

Concretely, the property to reach: after a `link-*` write, a KR whose `current`
was asserted before that write still reports the date it was asserted, and
`asserted_scope` for it is no longer `register`.

**The hand-off is the hard part and must not be improvised.** `perry-goals krs`
is read-only and calls itself the only surface for phase KRs;
`goals/reference/phases.md:212` says nothing in the linkage file is edited by
hand once it exists; and there is **no KR write path** — that gap is `TASK-264`,
and it was crossed by hand once already, recorded in `USER-912`'s answer. So:

- If the fix can be made entirely in the readers and the contract, do that.
- If it requires a new field in `phase/<NNN>-linkage.md`, **stop and hand off**
  rather than writing it. Say so in the RESULT block. Do not hand-edit the
  register; that is the thing `TASK-264` exists to stop being normal.

## Verification

1. **Reproduce the re-dating first.** On a `git archive` copy: assert a
   `current` on a KR, record its `asserted_at`, append an unrelated edge, and
   show the date moved and `stale` reset. That is the before-state and it must
   be in the evidence.
2. **After the fix**, the same sequence leaves the untouched KR's date alone.
3. **The warning becomes provably unnecessary**, or it stays and the round says
   why. A warning kept beside a fix that made it false is a fourth disclosure.
4. **Mutation**: revert the per-KR date and show a named test go red. Anchor by
   line number with an assert on the old text, clear `__pycache__`, wait past
   the whole-second boundary, restore against pre-mutation bytes.
5. **A control**: a KR whose `current` is genuinely re-measured *must* re-date.
   A fix that freezes every date passes item 2 and is wrong.
6. Full suite no redder than baseline; `perry-lint --root .` at 0 errors.

## Bound

```
Enumeration: grep -rn "asserted_scope\|set_updated\|asserted_at" bin/ viewer/ schema/
Size:        7 sites on 5c76aa2 — perry-goals:1581, :2038, :2058, :2063;
             lib/__init__.py:705; goals-list-contract.md:53, :144
Readers:     bin/perry-state:1968, :1971, :2160, :2381 — 4 more, counted
             separately because they consume rather than define
Remainder:   OKR.md's own `## Commitments` dates are a different field with a
             different owner (the goals lane) and are out. A KR-level date
             appearing anywhere else is a new row, per review.md § 1.
```

## Out of scope

- Building the KR write path. That is `TASK-264` and it is what makes the
  goals-lane half of this possible; if this row blocks on it, say so and stop.
- Editing `perry/phase/003-linkage.md` by hand for any reason.
- The `updated` field's other consumers outside the linkage register.
