# TASK-037 — one refusal names the flag the user typed and its sibling does not

> Source: `perry/evidence/2026-08/TASK-037-round4-v4-review.md`, re-verified 2026-08-21
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P2
- **Attribution**: unlinked

## What is left of this row, and what is not

Created 2026-08-17 as *"perry-goals writer"*. It **failed V4 twice** — round 3,
then round 4 with *"the round 2 claim is FALSE IN ITS CENTRAL SENTENCE"* — and
was then **narrowed by ADR-007** on 2026-08-19: the writer moved to a store, so
its findings about cell escaping and the create/amend split stopped applying,
because *"a JSON string carries a line break without a guard."*

**Re-verified 2026-08-21 against today's code, and most of the residue is
already gone:**

| round 3 / 4 finding | today |
|---|---|
| `NameError: name 'args' is not defined` on a refusal path | **fixed** — the refusal returns properly |
| `viewer/tables.py` raises `Refused`, undefined in that module | **fixed** — line 230 is now a comment explaining the history |
| the flag-naming block sits in module scope | **fixed** — it is in function scope at `bin/perry-goals:2423` and works |

## The one thing that survives

`bin/perry-goals:1897` states the rule:

> *"…so and names the flag, so a user is never guessing where their words go."*

Its **whitespace** refusal obeys it:

```
perry-goals: refused — --promise was given only whitespace, which would erase
the Promise cell rather than change it. …
```

Its **line-break** sibling does not:

```
perry-goals: refused — was given 'a\n\nb', which contains a line break —
a markdown table row is one line. A register cell is one line of a markdown table.
```

**Same tool, same value, one refusal names the flag and the other does not.**
Reproduced on a declared fixture, not read off the code.

## Deliverable

Every `perry-goals` refusal that is *about a value the user passed* names the
flag it came from. **Find them all** — do not fix the one quoted above and stop;
the pattern this row has failed on twice is a fix applied to the named instance
while its siblings keep the defect.

## Verification — V3

1. **The reproduction becomes a test**, byte-exact on the refusal text.
2. **A sweep**: every refusal path in `bin/perry-goals` reachable from a
   user-supplied value is enumerated, and each either names its flag or is
   listed with the reason it cannot. **Report the count.**
3. **Reverting reddens** the specific refusal, not a shared assertion.
4. **The whitespace refusal is unchanged** — it already obeys the rule, and a
   change there would mean the fix was made in the wrong place.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `bin/perry-goals`
- focused tests

## Out of scope

- `viewer/tables.py` and the escaping rules — ADR-007 retired that half.
- `perry-task`'s refusals.
- The `link` and `commit` writers themselves (TASK-119, TASK-092 — both landed).
