# TASK-044 — migration is dry-runnable, lossless, recoverable, and declared

> Source: `perry/decisions/ADR-004-mandatory-migration.md` § "What the migration must guarantee, or this decision is not safe to hold"
> Rung: **V4** per ADR-005 — this is the only thing in Perry that rewrites a stranger's files
> Dispatch mode: manual
> Estimated cycle: large
> Subjective verification: does a migrated board still read like the project's own? A human judgement, and the reason the dry run exists
> Touches architecture: `/perry adopt`; the conformance marker TASK-043 defines
> Deployed: no
> **Blocked by TASK-043** — this task produces the fact that task defines. Do not start before it lands.

**This file is the rubric a V4 reviewer scores against.**

## Why this one is different

Every other task in this project edits Perry. This one edits **someone else's
project**, on Perry's initiative, and ADR-004 makes it the price of using the
tool at all. Its own reopening criterion is *"migration proves unbuildable to
the five guarantees below"* — so a migration that cannot hold them does not
mean "ship it anyway", it means ADR-004 was wrong and the tolerance branches
come back.

The concrete thing to keep in view: `~/proj/gimegime-pmo` is a year old, has
41 tasks under headings its author chose, and is somebody's real record of
their work. The failure mode is not a crash. It is a board that still parses
and no longer reads like theirs.

## The five guarantees

### 1 · Dry run first, always

- [ ] `--dry-run` prints the **complete** diff, not a summary and not a count.
- [ ] It writes nothing — asserted by comparing the file's bytes before and
      after, not by reading the code.
- [ ] The dry run and the real run produce the same result. A preview that can
      diverge from what happens is worse than no preview, because it is
      trusted.

### 2 · Nothing is lost

- [ ] Every id present before is present after. Asserted by the tool itself
      and refused if it fails, not left for the user to notice.
- [ ] Row counts per section are preserved, or the difference is stated and
      accounted for row by row.
- [ ] Free prose the schema has nowhere to put is **carried, not dropped**.
      A cell Perry does not model is still the project's writing.
- [ ] The guarantee holds on the hardest real case available: gimegime-pmo's
      board, on a copy.

### 3 · Recoverable

- [ ] Refuses on a dirty working tree, **or** writes a restore point it names
      in the output. Decide which and say why — a git-only answer excludes
      projects not under git, and a restore point is state Perry now owns.
- [ ] The recovery path is shown working, not described.

### 4 · The user declares

ADR-004 § 4: *"Mandatory migration means the tool may refuse without it; it
never means the tool may perform it unasked."*

- [ ] Migration never runs as a side effect of another command.
- [ ] The declaration is what TASK-043's marker records. This task writes it;
      it does not invent a second one.
- [ ] `risk-add`'s existing refusal is the shape to match: it names the count,
      names the command, and points at the dry run.

### 5 · Partial migration is a state, not a failure

- [ ] A project may migrate `BOARD.md` and not `OKR.md`, and both halves work:
      the migrated file is writable, the other refuses and says why.
- [ ] A migration that cannot complete leaves the project in a state that is
      **valid**, not half-written. Whatever "valid" means here has to be
      stated, because it is the one guarantee with no obvious definition.

## What migration is not

- **Not a rewrite of the project's vocabulary.** `## Open — 工程线` is a
  heading its author chose. If Perry's shape can accommodate it — and
  `perry-task add --group` exists precisely because it can — migration should
  not rename it. Decide and state where the line is: what must change for a
  file to be Perry-shaped, and what is merely different.
- **Not a quality pass.** Migration does not fix stale rows, reword next
  actions, or close things that look done. It changes shape and nothing else.
- **Not silent.** Every file it touched, listed, with what changed in each.

## The measurement that decides whether this worked

`~/proj/gimegime-pmo` reports **59 lint errors** today (`KR-O3.2`'s baseline was
61). `~/proj/PolyForge` reports **13**, and carries almost no Perry state.

- [ ] After migration, on a copy: gimegime-pmo's lint errors go to 0, or every
      remaining one is a fact about the project rather than about its shape,
      named individually.
- [ ] PolyForge is the other case — nearly nothing to migrate. It must not
      produce a wall of output or a half-built structure.

## Out of scope

- Deleting tolerance branches — TASK-045, and blocked on both this and 043.
- Defining the conformance marker — TASK-043. If its shape turns out wrong for
  migration, that is a finding to report, not a thing to redesign here.

## Verification

| Rung | Check |
|---|---|
| V2 | `perry-lint` clean; the suite green |
| V3 | a full run on copies of both real projects, with the before/after id sets printed |
| V3 | the dry run's output compared byte-for-byte against what the real run does |
| V3 | the recovery path exercised, not described |
| V4 | this file, scored by someone who did not build it |
| V5 | the user reads a migrated board and says it still reads like the project's |

Mutation discipline: every guarantee verified by reverting its implementation
and confirming a test goes red. **The losslessness assertion is the one to be
most suspicious of** — a test that migrates a board Perry generated proves
nothing, because Perry's own boards are already Perry-shaped.
