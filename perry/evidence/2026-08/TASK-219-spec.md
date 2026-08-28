# TASK-219 — `retro-cites-phase-scores`, the check that the retro cites rather than re-derives

> Design: **DESIGN-012** § 5.4 and User Decision 4 (`design/DESIGN-012-close-phase.md`), locked 2026-08-28.
>
> Dispatch mode: manual
> Executor: manual — **not a judgement call, a gate result.** `.perry/hook.md § High-stakes operations` lists `state-schema.json` under *the claim surface*, and this row's deliverable edits it, so `/perry work dispatch` refuses. The refusal is arguably over-broad — a `cross_file` row changes no path Perry writes into anyone's project — but the hook says in its own words that the cheapest way to pass this gate is to reword the spec, and that is the one thing a safety gate must never reward. The wording stands and the row is dispatched by hand.
> Estimated cycle: small
> Subjective verification: whether the described surface is the surface actually compared
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V3
- **Dependencies**: —
- **KR linkage**: unlinked — see § Attribution

## Why

Decision 1 put the retro after scoring, which makes "the retro cites the
verdicts rather than re-deriving them" a comparison between two files that both
exist. Under *retro before score* it would not have been checkable at all —
there would be nothing to compare against yet.

Without it, the `goals` / `work` split holds only because someone did it by
hand, which is exactly what happened on 2026-08-28.

## Deliverable

One row in `schema/state-schema.json § cross_file`:

```
{ "id": "retro-cites-phase-scores", "severity": "warn",
  "description": "Each per-KR status in evidence/<YYYY-MM>/retro.md must equal
                  the status for that KR id in phase/<NNN>-<slug>.md § Retro." }
```

plus its implementation in `bin/perry-lint`.

**`warn`, not `error`.** The boundary settled 2026-08-21
(`phase/002-fields-are-typed.md § User Commitments`): errors are shape
violations, warnings are quality signals. A retro disagreeing with the scores
is a content disagreement inside a well-shaped file.

## Verification — V3

1. **Mutation**: change one per-KR status in a retro; the check must go red. A
   gate whose green is a tautology is worse than no gate (phase #002 lesson 4).
2. **The surface is the one described.** `linkage-objective-agrees` is declared
   at `error`, **is** implemented, and still let the 002-linkage misnesting pass
   at 0 errors — because it reads a linkage row's `Objective` column rather than
   the frontmatter's `objectives[].id` nesting. Assert which two spans this
   check compares, in a test, so the description cannot drift from the code.
3. Full suite green.

## Out of scope

- A `files[]` spec for `evidence/`. Decisions 3 and 4 both refused to add a
  claim or a shape surface; `evidence/` stays outside the conformance gate, so
  no project's retro becomes unwritable for failing to match a heading set.

## Attribution

Serves `DESIGN-012` / `KR-O2.3`. Declared `unlinked` against phase #003 by
`goals`; see TASK-218 § Attribution for the same reasoning.
