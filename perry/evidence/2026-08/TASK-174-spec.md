# TASK-174 spec — autopilot re-derives a rule the contract already computes

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> The cheap half of the autopilot split the user approved 2026-08-27. The other
> half is `DESIGN-010` and needs its User Decisions first — **this row does not
> wait on that RFC and must not implement any of it.**

## The measurement

`work/reference/autopilot.md:131`:

> **Eligible**: status ∈ {`not_started`, `blocked` with all blockers resolved},
> has `evidence/<YYYY-MM>/<TASK-ID>-spec.md` with `Dispatch mode: auto` +
> non-`manual` Executor, hook safety scan passes, all listed dependencies
> resolved.

That first clause is a **second implementation** of a rule the payload now
computes exactly once. Three contract versions built it:

- **1.12** stopped `startable` reading the stored `status`, so a row whose every
  dependency has closed is `startable: true` with `blocked_stale: true` — the
  case autopilot's prose describes as *"`blocked` with all blockers resolved"*.
- **1.14** made a `USER-` ask a node, so a row waiting on a question is
  correctly unstartable. **Autopilot's prose does not know asks exist.**
- **1.15** added `depends_on_resolved`, so *why* is readable too.

`bin/lib § resolve_startability` is the one home for that rule and is already
under an AST guard that fails on a second statement of it — in *code*. This one
is in prose, so the guard cannot see it.

## The deliverable

1. **`work/reference/autopilot.md`'s eligibility step reads `startable`** — and
   `blocked_stale` where it needs to explain a row that reads `blocked` and is
   startable anyway. The spec/`Dispatch mode`/hook-scan clauses are unchanged;
   only the dependency reasoning moves.
2. **The skip reasons come from the payload too.** *"Skipped — blocked: open
   dependency"* should name what `blocked_by` says, and a row waiting on a
   `USER-` ask should say so rather than being lumped in with rows waiting on
   tasks. That distinction did not exist when the prose was written.
3. **A guard**, in the family of `tests/test_procedures_call_the_tool.py` —
   which already reads procedure prose and enforces *call the tool, then write
   prose*. Read it first. The rule here is its neighbour: **a procedure must not
   re-state a predicate the contract computes.**

Item 3 is the row. Items 1 and 2 without it fix today and not the class, and
this exact prose has already outlived three contract versions that changed what
it means.

## Scope discipline

- **Do not implement DESIGN-010.** No scout stage, no spec generation, no change
  to what the escalation gate does with a machine-authored spec. If you find
  yourself editing `bin/perry-state`'s escalation scan, stop.
- **Do not change what autopilot dispatches**, only how it decides. On this
  project the eligible list is 0 either way, for want of specs — that is
  DESIGN-010's problem and it is not evidence about your change.
- The guard must not be so broad it forbids a procedure from *explaining* a
  field. *"`startable` is false because a dependency is open"* is an
  explanation; *"eligible when status is `not_started` or every blocker has
  closed"* is a second implementation. Draw that line and defend it.

## Verification

1. `work/reference/autopilot.md` names `startable`, and its eligibility step no
   longer restates the status/dependency rule.
2. **The guard fires on the old prose.** Restore line 131 verbatim and the new
   test goes red. This is the one that proves the guard is real.
3. **The guard does not fire on an explanation.** Add a sentence that mentions
   `startable` descriptively and show it stays green.
4. Every other procedure page passes the new guard, or the ones that do not are
   **reported as findings** — do not fix them in this row.
5. `perry-lint --root .` — 0 errors, and `perry-lint --templates` exit 0.

## Out of scope

- `bin/` code. This row is prose plus a test.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/` must
  end empty.

## Ground rules

- Branch `coding/task-174-autopilot-reads-startable`, commit there, **no PR, no
  push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly — Perry is stdlib-only as of
  tonight and that flag is what proves it.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`.
- Expected baseline: **80 modules · 2369 tests · 2 red** —
  `test_contract_invariance` and `test_diagnose`. **Neither is yours.**
- `work/reference/autopilot.md` is also copied into the installed skill at
  `~/.claude/skills/perry/`. **Edit the repo copy only**; the install is not
  yours to touch.
