# TASK-043 — the conformance marker

> Source: `perry/decisions/ADR-004-mandatory-migration.md` § "The mechanism this requires, which does not exist yet"
> Rung: **V4** per ADR-005 — this is the gate every writer calls, and it decides what happens on a project Perry did not create
> Dispatch mode: manual
> Estimated cycle: large
> Subjective verification: (none — but see § The trap)
> Touches architecture: every writer's entry path; `.perry/config.md`; `schema/state-schema.json`
> Deployed: no

**This file is the rubric a V4 reviewer scores against.** It states what the
work must satisfy. Where it names a decision rather than an answer, the
implementer decides and **states the reasoning in the commit** — the reviewer
scores the reasoning, not a guess at what I wanted.

## The problem, exactly

`bin/perry-lint`'s `is_adopted()` answers *"does this folder contain any Perry
file at all"* — satisfied by a `BOARD.md` existing, whatever is inside it. It
was written for a different job (stop linting a stranger's folder into a wall
of red) and it does that job correctly.

ADR-004 needs a different fact: **this file matches Perry's shape, at shape
version N, and the user said so.** Nothing answers that today, so every writer
either guesses or adapts, and adapting is what ADR-004 retires.

## What must be true

### 1 · The marker records a decision, and lint verifies a shape. They are two facts, not one.

- [ ] The marker is **declared**, not inferred. ADR-004 § 4: *"Adoption
      proposes; the user declares."* A tool may not stamp it on its own
      initiative.
- [ ] A declared marker that no longer matches the file is **reported**, not
      silently trusted and not silently revoked. A user can edit a file after
      declaring it; that is a finding, not a crash and not a correction.
- [ ] Conversely, a file that happens to conform but was never declared is
      **not** treated as conformant. If that feels wrong, say why in the commit
      — but the default has to be the one ADR-004 chose.

### 2 · Per file, not per project

ADR-004 § 5: a project may migrate its board and not its risks.

- [ ] Conformance is recorded and checked per state file.
- [ ] A writer gates on the file it is about to write, and on nothing else.
      `perry-goals` writing `OKR.md` must not care what `BOARD.md` says.

### 3 · Versioned from the start

- [ ] The marker carries a shape version.
- [ ] A project declared at version 1 is distinguishable from one at version 2
      **without re-deriving it by inspection** — that is the whole point of
      storing it.
- [ ] There is a stated answer to "what happens when the shape version moves
      and a project is still on the old one". It may be "refuse and name the
      re-migration"; it may not be "silently accept".

### 4 · A refusal names the way forward

Every refusal this task adds must say what to run. `perry-task`'s existing
refusals are the bar — the `risk-add` one names the count, the command, and the
dry-run. A gate that says "not conformant" and stops is a wall.

### 5 · Reading is not gated

- [ ] `perry-state`, `perry-task list`, `perry-goals list`, `perry-decide list`
      and the viewer keep working on an unmarked project.
- [ ] The three published contracts do not change shape. If a key is added it
      is additive, the minor moves, and `schema/task-list-contract.md §
      Changelog` records it.

This is not negotiable and it is the half of ADR-004 that is easy to break by
accident: a front-end querying state is why DESIGN-005 exists.

## The trap

**Every Perry project in existence has no marker, including this one.** A gate
that refuses an unmarked file turns `perry-task add` off for every user on
upgrade, and for Perry's own repo, and the 678-test suite will tell you
immediately.

So there must be a path from "already conformant, never declared" to
"declared", and it must not be an automatic stamp — see § 1. What that path is
(a subcommand, a first-write prompt, a lint suggestion, something else) is
**the main thing this task decides**. State the reasoning.

Related question worth answering in the same breath: does the gate ship
**enforcing** or **advisory** for one release? DESIGN-003 § 4 decision 4 made
exactly this call for the verification ladder — *"a hard gate on day one would
retroactively invalidate every `done` row written before rungs existed"* — and
the same argument may or may not apply here. Say which.

## What "conformant" means

`perry-lint` already validates state files against
`schema/state-schema.json`. Reuse that; do not write a second definition of
Perry's shape. Two implementations of one rule is the defect class this repo
has hit in every review round.

Open, decide and state: does conformance mean lint-clean on **errors** only, or
errors and warnings? Perry's own board is clean on both; a real project is not.

## Out of scope

- **Deleting any tolerance branch.** That is TASK-045 and it is blocked on this
  one by construction. Nothing may be removed here.
- **The migration itself** — dry run, losslessness, recoverability. TASK-044.
  This task defines the fact migration must produce; it does not build the
  producer.
- Changing what any reader parses.

## Verification

| Rung | Check |
|---|---|
| V2 | `perry-lint` clean; the 678-test suite green with no test edited except where behaviour deliberately changed |
| V3 | a run against copies of `~/proj/gimegime-pmo` (unmarked, non-conformant) and this repo (unmarked, conformant) showing what each gets — **never the originals** |
| V3 | a writer refuses on an unmarked file, and the refusal names the way forward |
| V3 | reading is unaffected on both, and the three contracts are byte-identical in shape |
| V4 | this file, scored by someone who did not build it |

Mutation discipline: every refusal and every gate verified by reverting it and
confirming a test goes red. **Revert exactly the thing you claim to revert** —
three of the last round's twelve claimed mutations did not reproduce because
the revert changed something adjacent, and a `git checkout` of a whole file is
not a mutation of one line.
