# TASK-339 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: large
> Subjective verification: whether the written procedure answers the cases the code answered
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P0
- **Track / mode**: main / project
- **Dependencies**: `USER-916`
- **KR linkage**: unlinked

## Why this row exists

**User decision, `USER-916`, 2026-09-04**, in their words: *"不要用python代码来
检查文件语义。应该去掉这个检查逻辑，让agent自己来判断gate."*

`ADR-007` decision 3 says the Python layer never parses a document at all. The
dispatch gate does exactly that: it matches a spec's prose against the hook's
high-stakes list to decide whether a round is dangerous. Five rounds have tried
to make that match correct — bare substrings, blind to fields, cite-versus-write,
a full stop, a markdown italic — and the last measurement is the argument for
stopping: **formatting alone moves the verdict in both directions.** Bold or a
sentence-final full stop cleared a declared claim-surface write; bolding an
own-tree path `**perry/evidence/…**` made it refuse.

## The half that is easy and the half that is the row

Deleting the scanner is mechanical. **The gate arms every dispatch on this
project, so a deletion without a replacement procedure swaps a bad guard for no
guard.** The deliverable is a procedure in `work/reference/dispatch.md` that a
dispatching agent follows, written well enough that two agents reading it reach
the same verdict on the cases below.

## Files in scope

- `viewer/parsers.py` — `scan_spec_escalations` and the helpers that exist only for it.
- `bin/perry-state` — the `--escalation-scan` entry point.
- `bin/perry-lint` — its callers.
- `work/reference/dispatch.md` — **where the replacement procedure is written.**
- `work/reference/autopilot.md` — its one mention.
- `tests/test_escalation_boundaries.py`, `tests/test_escalation_union.py`, `tests/test_spec_scannability.py`, `tests/test_project_root_resolution.py`.

## The first question to answer

`escalation_union` / `hook_escalation_lines` / `escalation_fragments` extract the
high-stakes LIST from `.perry/hook.md`. A judging agent still needs that list —
but it can read that document itself. **Decide whether that half goes too, and
say why either way.** Do not delete it silently and do not keep it silently.

## What the procedure must not lose

Two things the code knew. Both came out of rounds that cost this project real
time, and a prose rewrite is where they are most likely to disappear.

**1. What makes a root foreign.** Relative is internal, full stop — a relative
path resolves against the scanned project's root and cannot name anyone else's
tree. Foreign is five shapes: absolute `/srv/…`, home `~/…`, variable
`$PERRY_HOME/…`, upward `../…`, and an **unresolved root** (`<target>/…`,
`{{project}}/…`). That last is a deliberate safe-direction judgement — a root
nobody has resolved is not a root known to be this project — and it is the only
one not obvious from an example.

**2. The collision.** The characters that IDENTIFY a foreign root are the same
characters you would strip as formatting noise. `_PATH_CHAR` admits `~ $ < > { }
*` *because* they mark a foreign root, which is why narrowing it re-roots
`~/other-project/evidence/2026-09/` into something that reads as this project's
own tree and stops refusing. "Ignore the markdown around the path" and "`~`
means someone else's home" are the same character. **So the procedure must state
ownership detection before any normalisation step.**

## Deliverable

1. The spec-scanning path is gone, with its tests, and no caller survives.
2. `work/reference/dispatch.md` carries the procedure, including both items above.
3. The `escalation_union` question is answered in writing.

## Verification

1. **Re-derive the corpus first.** Two figures are in circulation and neither is
   verified: the PMO measured 148 specs / 133 pass / 15 refuse / 0 unarmed on
   2026-09-03; TASK-290 round 2's result says 147 scanned / 16 refused. Measure
   it yourself before the deletion and put the number in the evidence.
2. **Walk six named specs through the written procedure by hand and show the
   answers.** Five must come out ALLOWED, because the scanner refused them on a
   citation: `TASK-099` (*"setup and hook code that reads repository documents —
   read."*), `TASK-108` (matches the tool names `bin/perry-diagnose`,
   `tests/test_diagnose.py`), `TASK-139` (*"changing it is escalated. If the
   design points that way, stop and file"*), `TASK-220` (cites `adopt` /
   `diagnose` as a router precedent), `TASK-244` (the English noun in *"the
   harness re-does setup per test"*). One must come out REFUSED: `TASK-107`, on
   `~/.claude/skills`, the `ln -s` variants, `publish`, `rm -rf`,
   `--force-with-lease`. **A procedure that cannot separate those six is not
   done**, and getting all six right by listing them is not a procedure either.
3. **The foreign-root case.** Show the procedure refusing
   `~/other-project/evidence/2026-09/` and allowing `perry/evidence/2026-09/`,
   and show that the reasoning does not depend on stripping formatting first.
4. **No caller survives.** `grep -rn "escalation.scan\|scan_spec_escalations"`
   over `bin/ viewer/ tests/ work/` returns only history and this row's evidence.
5. **Mutation.** Revert the deletion of the procedure section from
   `dispatch.md` and show a named test go red — or state plainly that no test
   can hold a written procedure, and say what holds it instead. Anchor by line
   number *with an assert on the old text*; clear `__pycache__`; wait past the
   whole-second boundary; verify restores with `git show <ref>:<path>`,
   single-path only. **Do NOT use `bin/perry-restore-check`** — it now refuses
   from a `git archive` copy and its `resolve()` follows symlinks (`TASK-256`).
   **A green mutation is the finding.**
6. Full suite via `tests/run` no redder than the baseline **you measure**, and
   `bin/perry-lint --root .` at 0 errors. Two known reds are not yours:
   `tests/test_contract_key_parity.py`'s two anti-vacuity controls decay with
   wall-clock time (`bin/perry-task:6303`, a 4-hour idle threshold against
   Perry's own live board) — that is `TASK-335`.

## Bound

```
Enumeration: grep -rn "escalation.scan\|escalation_scan\|scan_spec_escalations" bin/ viewer/ tests/ work/
Size:        on 7f890f9 — bin/perry-state 11, bin/perry-lint 4, viewer/parsers.py 3,
             work/reference/dispatch.md 1, work/reference/autopilot.md 1,
             tests/test_escalation_boundaries.py 16, tests/test_spec_scannability.py 7,
             tests/test_project_root_resolution.py 1 = 44 mentions.
             scan_spec_escalations itself is 152 lines (4642-4793).
Remainder:   `escalation_union` and the hook-extraction helpers are DECIDED by
             this row and removed by it only if the round argues they should be.
             The last element is the final mention in
             tests/test_project_root_resolution.py.
```

## Out of scope

- `.perry/hook.md`'s content. What counts as high-stakes is the user's list and
  this row does not edit it — it changes who reads it.
- Whether editing a NON-claims section of `schema/state-schema.json` should
  escalate at all. Nine of the fifteen refusals turn on that, it is a policy
  question for the hook, and this row **names it and leaves it** unless the
  written procedure cannot be finished without an answer — in which case say so
  rather than deciding it quietly.
- Any new mechanical check over a spec's prose. That is the thing being removed.
