# TASK-379 — spec

> Design: none. A gap measured on 2026-09-07 and **re-measured on 2026-09-12**,
> because every row the original measurement named has since closed
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: what a V2 row at `review` owes, now that `ADR-020`
> makes V2 the floor and a linter pass its artifact
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V2 — `bin/perry-lint` is a reader, it puts no bytes on
  a user's disk, and this change does not touch
  `schema/state-schema.json`. `ADR-020`'s gate answers no. Raise it if the
  implementation turns out to need a schema field for the artifact rule.

## Why

`perry-lint --reviews` guards the **exit** from review and not the **waiting
room**. `v4-close-without-verdict` fires on a row *closed* at V4 with no
verdict document. Nothing at all fires on a row that is *sitting at* `review`
with its code merged on `main` and no artifact of the rung it claims.

The original measurement, 2026-09-07, found all five rows then at `review` —
`TASK-278`, `TASK-336`, `TASK-341`, `TASK-356`, `TASK-357` — carried **zero**
verdict documents while all five had their code merged. **All five are now
closed**, so that exhibit is gone and this spec does not rest on it.

**Re-measured 2026-09-12, and the shape has changed in a way that matters.**

| row | rung | verdict blocks | commits on `main` | artifact on disk |
|---|---|---|---|---|
| TASK-183 | V3 | 0 | 5 | `TASK-183-result.md` |
| TASK-253 | V3 | 0 | 7 | **none** |
| TASK-281 | V4 | 1 | 21 | yes |
| TASK-411 | V4 | 1 | 10 | yes |
| TASK-412 | V4 | 1 | 11 | yes |
| TASK-415 | V3 | 0 | 5 | `TASK-415-result.md` |
| TASK-419 | V4 | 1 | 13 | yes |
| TASK-431 | V4 | 1 | 15 | yes |

**"No verdict document" is the wrong predicate now.** Three of the eight carry
none, and two of those three are V3 rows whose rung never asked for one: a
verdict block is a V4 artifact (`review.md § 3`), a V3 row's artifact is a
reproducible run, and since `ADR-020` a V2 row's artifact is a linter
attestation. Applied as written, the original check would report `TASK-183` and
`TASK-415` — which have exactly what their rung asks for — and would be right
about only `TASK-253`, which has `evidence: —` and no file of any kind.

So the finding this row is really about is **a row at `review` whose rung's own
artifact is absent**, and the rung chooses which artifact.

## Files in scope

- `bin/perry-lint § check_reviews` — where `v4-close-without-verdict` lives and
  where the waiting-room half belongs beside it.
- `schema/state-schema.json` — **read only.** If the artifact-per-rung mapping
  needs to be declared there rather than hard-coded, that is a finding to
  report, not an edit to make: the file is on `.perry/hook.md § High-stakes
  operations` and needs the user's authorization.
- `tests/` — where the check and its negative control land.
- `perry/evidence/2026-09/TASK-379-result.md` — written.

## Bound

```
Enumeration: every row whose stored `status` is `review`, from
             `perry/tasks.jsonl`
Size:        8 on 2026-09-12 — re-derive it in your own tree, it will differ
Remainder:   rows at `not_started`, `in_progress`, `done` and `dropped`. A row
             that never reached `review` cannot be sitting in the waiting room,
             and a closed one is the EXIT half `v4-close-without-verdict`
             already covers. Out of scope, deliberately: this row adds the
             complement of an existing check, it does not widen it.
Last element: the lowest-ranked id in your own enumeration's order
```

```
Artifact per rung — the mapping the check needs, and the one open question
V4  a verdict block naming the row  (review.md § 3; the existing detector)
V3  a result document naming the row
V2  UNSETTLED. ADR-020 made V2 the floor on 2026-09-11 and calls its artifact
    "a structural check ... attested by a script". No row has yet sat at
    `review` carrying V2, so there is no observed shape to copy. Decide it in
    the report and say why; do not invent a file convention in code and leave
    the argument out.
```

## Deliverable

1. A finding in `perry-lint --reviews` for a row at `review` whose rung's
   artifact is absent, keyed on the rung and not on "verdict document".
2. **A negative control that proves the detector works**, in the shape the
   original measurement used: run it against a row that *does* carry its
   artifact and show it returns exactly that artifact and reports nothing.
3. `perry/evidence/2026-09/TASK-379-result.md`: the re-derived table above in
   your own tree, the V2 decision with its argument, the mutations.

## What it must not do

1. **It must not report a row for lacking an artifact its rung never asked
   for.** That is the defect in the row's own original framing, and reproducing
   it would make the check noise on the day it ships. `TASK-183` and
   `TASK-415` are the live controls: both must stay silent.
2. **It must not edit `schema/state-schema.json`.** See Files in scope.
3. **It must not promote the finding to an error.** `--reviews` is an advisory
   pass; a row legitimately sits at `review` for days.
4. **It must not compute its expectation the way the code does.** The store on
   disk is one honest side; the evidence directory is the other.

## Verification

1. The eight rows above, re-derived in your own tree, each with the verdict the
   new check gives and why.
2. `TASK-253` reports. `TASK-183` and `TASK-415` do not. `TASK-281`, `411`,
   `412`, `419`, `431` do not.
3. **Mutation.** Delete the artifact a silent row depends on, in a scratch
   copy, and show the check reddens on that row by name. Then restore and show
   it goes silent again. A mutation that comes back green is the finding.
4. The default `perry-lint` pass still reports `0 error(s)`, and the advisory
   count moves by exactly the number of rows this check adds.

## Out of scope

- The exit half, `v4-close-without-verdict`. It works and is not being changed.
- `review-rounds-exhausted`, the other `--reviews` finding.
- Closing any of the eight rows. This row builds the detector; what to do about
  what it finds is the board's business, not this round's.
