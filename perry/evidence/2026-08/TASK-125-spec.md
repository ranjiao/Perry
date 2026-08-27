# TASK-125 — the shape is in the repo; the insert against it is not

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `23ce1e0`

## The measurement, and the half that is already done

**The shape is committed.** `tests/fixtures/second-project/OKR.md` carries
`### Anti-Goals` at line 28, nested inside `## v2:` at line 13 — and `IN_REPO`
says so in a comment. So the **round trip** over that shape runs on every
machine, unconditionally. TASK-111 did that.

**What still does not run anywhere but here** is the **insert**:

```
tests/test_goals_writer.py:1334   for source in ELSEWHERE:
                        :1348       self.skipTest("none of […] present")
                        :1356   for source in ELSEWHERE:
                        :1376       self.skipTest("none of […] present")
```

```python
ELSEWHERE = [ Path.home()/"proj"/"gimegime-pmo"/"OKR.md",
              Path.home()/"proj"/"aimark"/"perry"/"OKR.md" ]
```

**Read 1334 and 1356 first and establish what they actually assert** before
assuming they are the same test twice. Reading a shape and writing into it are
different questions, and the row's title says *insert*.

## Why this is a real gap and not pedantry

An `### Anti-Goals` nested inside a version is the case where "insert at the end
of the version" and "insert before the next `##`" give different answers. The
round trip cannot see it: **a file that already has the section renders back
byte-identical whether or not the writer would have put a new one in the right
place.**

## The precedent, one merge old — use it, do not invent a second

**TASK-124** merged tonight and answered this exact question for
`tests/test_conformance.py`: commit the shape, read it through the real seam,
and **assert a property rather than a capture-day census**. Read
`perry/evidence/2026-08/TASK-124-result.md` before you design anything.

Its two rules that apply directly:

1. **Do not commit a snapshot of a real project.** That is the golden-file
   failure `test_contract_invariance` spent TASK-145 escaping.
2. **Add the anti-vacuity guard in the same change.** TASK-124's
   `test_the_corpus_can_still_tell_the_two_checkers_apart` exists so a fixture
   that drifts into uniformity fails instead of passing quietly. Yours needs the
   equivalent: something that fails if the fixture stops carrying the shape.

`tests/fixtures/second-project/` already holds the shape. **Extending it may be
better than adding a fixture** — say which you chose and why.

## What to decide and state

- **Does `ELSEWHERE` survive at all?** TASK-124 deleted its equivalent
  (`PERRY_TEST_CORPUS`) with the argument that it named one directory and that
  directory was no longer needed. `ELSEWHERE` is documented as *"never
  load-bearing: they widen the round-trip on the one machine that has them"*.
  **Widening on one machine is a real if small benefit** — decide whether it is
  worth a code path nothing else exercises, and argue it either way.
- **`test_the_corpus_actually_disagrees` deliberately excludes `ELSEWHERE`** and
  its docstring explains why. **Do not weaken that.** If your change would let
  `ELSEWHERE` back into that assertion, you have gone wrong.

## Files in scope

`tests/test_goals_writer.py`, `tests/fixtures/`.

## Out of scope

- `bin/perry-goals` — read-only. If the writer must change for the insert to be
  testable, **that is a finding to report, not a change to make**.
- `perry/` — read-only.
- `tests/test_conformance.py` — TASK-124 just landed there.

## Verification

1. The insert case runs with **`$HOME` pointed at an empty directory**. Show the
   run.
2. **Mutation proof**: break the insert position in `perry-goals` *temporarily*,
   confirm your new test reddens, revert byte-for-byte and show
   `git status --porcelain` empty. Report the count.
3. `test_the_corpus_is_entirely_inside_the_repository` and
   `test_the_corpus_actually_disagrees` both still pass, unmodified or with the
   modification argued.
4. Suite: **86 modules, one red** (`test_diagnose`, standing). Anything else is
   yours.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
