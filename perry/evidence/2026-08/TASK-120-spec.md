# TASK-120 — the linkage edges are read but never folded into KR progress

> Source: `perry/phase/002-linkage.md`, `schema/goals-list-contract.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: medium
> Subjective verification: no
> Touches architecture: `perry-goals/list` is a versioned read contract — any
>   field added here is a `1.x`-style addition and must not remove or retype one
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked — it serves the ability to score KRs, not one KR

## The state, measured 2026-08-21

**The row's title understates it.** The numbers are not merely absent; they are
**wrong in both directions**, and today's own measurements prove it.

`perry-state --section linkage` carries `target` and `current` per KR. Both are
hand-written into `phase/<NNN>-linkage.md`'s YAML frontmatter and **nothing
derives, checks or ages them**:

| KR | target | current | reads as | actually |
|---|---|---|---|---|
| `P-O1.1` `BOARD.md` rendered from the store | 1.0 | **0.0** | 0% | **met** — TASK-038/088/089/090 all closed |
| `P-O2.2` readers resolving a header cell (baseline 5) | 0.0 | **0.0** | **met** | **not met** — TASK-094 measured 13 row splits and 87 header resolutions still reaching `BOARD.md` |

The second shape is the systemic one: **six of the eight phase KRs have
`target: 0.0`**, and an unset `current` defaults to `0.0`, so every
*drive-this-to-zero* KR reads as **met on the day it is written**, before any
work starts.

Meanwhile `perry-goals list --json` (`perry-goals/list/2.0`) returns each KR as
a **bare id string** — `"KR-O1.1"` — carrying neither target nor current. So the
one payload a front-end reads cannot express progress at all, and every OKR
roll-up this project has produced was measured by hand.

## The trap this row must not fall into

**Do not compute a completion ratio from the `tasks[]` edges and call it
progress.** `P-O2.1`'s metric is *"0 occurrences of `CLOCK_RE`"*. "TASK-091 is
closed" does not establish that the count is zero — only re-running the count
does. A ratio presented as `current` would be a fabricated measurement, which
`perry/OKR.md § Operating Principles` forbids in its first line: *never compute
a number by reading files and eyeballing it.*

`goals/SKILL.md` already carries the matching rule: **a KR's `target` /
`current` are numbers or absent**, never a prose target coerced into a number.

## Deliverable

The payload stops presenting an author-asserted number as a measured one, and
says when it has gone stale. Concretely, all three:

1. **Provenance.** Every `current` a payload emits is marked as **asserted by
   the author**, with the date it was asserted. A KR whose `current` was never
   written is `null` — never `0.0` by default, which is what makes a
   drive-to-zero KR read as met before it starts.
2. **Staleness.** A KR whose linked tasks have changed state since `current` was
   asserted is reported as stale, naming which tasks moved. This is the edge
   finally being read: not to compute the metric, but to know the number can no
   longer be trusted.
3. **Reachability.** `perry-goals/list` exposes `target`, `current`, its
   provenance and its staleness per KR, so a front-end can render a KR without
   parsing `phase/<NNN>-linkage.md` itself. Additive only.

**How the three combine is yours to argue.** If you conclude that a separate,
clearly-labelled *linked-task completion* count belongs beside `current` rather
than inside it, make that case in your result — it is a defensible answer, and
the one thing that is not defensible is a single number that hides which of the
two it is.

## Verification — V3

1. **Both of today's wrong readings flip.** With `phase/002-linkage.md`
   unchanged, `P-O1.1` no longer reports as 0-of-1 progress with four closed
   tasks, and `P-O2.2` no longer reports as met. Assert the reported shape, not
   a hand-typed number.
2. **A drive-to-zero KR with no asserted `current` is `null`, not `0.0`** —
   proved on a fixture whose KR has `target: 0` and no `current`. Reverting that
   default reddens it.
3. **Staleness discriminates.** On a fixture: a KR whose linked tasks have not
   moved since the assertion is **not** stale; closing one of its tasks makes it
   stale and names that task. Both directions, on the same fixture.
4. **The contract does not break.** `python3 tests/parallel test_contract_invariance`
   stays green, and `tests/test_contract_key_parity.py` reports **0
   documented-but-not-emitted** for `perry-goals/list` — every field you add is
   documented in `schema/goals-list-contract.md` in the same change. Note the
   parity check currently reports 5 emitted-but-undocumented keys on this
   contract already; that is TASK-131, not yours — **do not let your number hide
   inside it.** Record the before and after counts separately.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-goals`, `bin/perry-state` (its `linkage` / `attribution` sections)
- `schema/goals-list-contract.md`
- focused tests and their fixtures

## Out of scope

- **Writing `phase/<NNN>-linkage.md`.** No tool writes it today and that is
  TASK-119, a separate row. You read it.
- **Changing any KR's asserted `current` in this repository.** `phase/` is the
  `goals` lane's file and this row does not edit project state; `git diff --
  perry/` must end empty.
- The five already-undocumented `perry-goals/list` keys (TASK-131).
- Deriving a metric that only re-running a count can establish.
- **The shape declaration in `schema/state-schema.json`.** It sits behind this
  project's safety gate as part of the claim surface, and this row is scoped to
  need no change there: you are adding fields to a *payload*, not to the
  declared shape of a state file. **If you conclude the linkage record's
  declared fields genuinely must change, stop and say so in your result** — that
  is a per-task release the user gives, not a scope you widen.
