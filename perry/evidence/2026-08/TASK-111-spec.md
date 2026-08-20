# TASK-111 — A test reads two files outside the repository

> Source: found 2026-08-20 while diagnosing why PR #12's CI was red
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## The defect, and the reason it is worse than one red test

`tests/test_goals_writer.py` builds its byte-identity corpus from five files:

```python
IN_REPO   = [ROOT/"perry"/"OKR.md", ROOT/"tests"/"fixtures"/"sample-project"/"OKR.md",
             ROOT/"goals"/"state"/"OKR_TEMPLATE.md"]
ELSEWHERE = [Path.home()/"proj"/"gimegime-pmo"/"OKR.md",
             Path.home()/"proj"/"aimark"/"perry"/"OKR.md"]
texts = [p.read_text() for p in IN_REPO + ELSEWHERE if p.exists()]
```

The last two live **outside the repository**. On CI they are absent, `if
p.exists()` skips them silently, the corpus shrinks, and
`test_the_corpus_actually_disagrees` fails its assertion that the corpus holds at
least two distinct version counts.

The test's own docstring says it exists so the corpus *"cannot quietly become
uniform"*. `if p.exists()` is precisely how it quietly becomes uniform on every
machine but one. It is **green here and red on CI forever**, which is the state
in which a real regression stops being visible — and this repository has been
reading past a red CI all day because of it.

## Deliverable

1. The corpus no longer changes strength with the machine. Either the shapes it
   needs are committed as fixtures, or the test **skips loudly with the reason
   named** — never silently narrows its own assertion.
2. `test_the_corpus_actually_disagrees` passes on a checkout with no home
   directory projects present.
3. The corpus still exercises what it was written to cover: the multi-version
   shape and the objective-heading shape. Whatever replaces the missing files
   must carry those, or the fix is a relaxation wearing a fixture's clothes.
4. No other test in the suite silently narrows an assertion when an optional
   path is absent.

## Verification — V3

1. Run the affected test with `HOME` pointed at an empty directory. It passes,
   or it skips with a message naming what is missing and why.
2. Remove the multi-version shape from the corpus and assert the test **fails** —
   the guard must still discriminate.
3. Same for the objective-heading shape.
4. A mechanical check over `tests/` naming any test that reads a path outside the
   repository root without either committing the file or skipping with a stated
   reason. Report what it finds; fix what is in this row's scope.
5. `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `tests/test_goals_writer.py`
- a committed fixture, if that is the route chosen

## Out of scope

- `bin/perry-goals` and the writer itself. This row is about the corpus the test
  reads, not the code it tests.
- Anything under `perry/`.
- The other tests the sweep names, unless one is trivially the same edit.
- `viewer/`, `bin/perry_store.py`, `bin/perry-lint`, `bin/perry-diagnose`,
  `tests/test_migrate.py`, `schema/state-schema.json` — each is carried by a
  live dispatch or an open unmerged branch.
- Closing without the V3 evidence above.
