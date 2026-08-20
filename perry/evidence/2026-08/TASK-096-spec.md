# TASK-096 — Lane procedures call the deterministic tool before prose

> Source: `work/reference/review.md`,
> `work/reference/review-constraints.md`,
> `perry/evidence/2026-08/TASK-096-v4-review.md`, and
> `perry/evidence/2026-08/TASK-096-v4-review-r2.md`
> Dispatch mode: auto
> Executor: coding agent (repository-local guard and behavioral tests)
> Estimated cycle: large
> Subjective verification: (none)
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: P-O3.1

### Deliverable

1. The guard enforces one invariant over the lane procedure corpus: a
   procedure that changes tool-owned state must call the deterministic writer
   before generating prose about that change. Direct hand edits are findings
   unless a narrowly defined exemption applies and the guard records that
   exemption as an observable suppression.
2. The corpus is the lane-shaped trees discovered by a top-level `SKILL.md`
   beside `reference/`, currently `goals/`, `work/`, and `decide/`. For every
   discovered lane, the guard scans its `SKILL.md` and
   `reference/**/*.md`. A future fourth directory with the same shape is
   discovered without adding its name to a list. Lane `state/` files are not
   in this corpus, and module prose must not claim that every Markdown file
   under a lane is scanned.
3. Suppressions performed by `scan()` are observable to tests. Each record
   identifies the page, source line or section, exemption identity, suppressed
   target, and suppressed step. Tests inspect those records rather than
   reimplementing `ADOPTION_HEADING` or another exemption predicate over raw
   page text. Letting an adoption/document exemption leak past its section
   must make a focused test fail.
4. Every exemption is bounded by behavioral fixtures for both its allowed and
   refused branches: adoption/document transcription, template-origin
   transcription, an R2 deterministic-tool call, owner-call proximity in both
   directions, numbered and bulleted step segmentation, prose before the first
   list item, and prohibition or descriptive prose. Deleting or widening an
   exemption boundary, using an unrelated template token, or letting one
   clause discharge another target must make a focused test fail.
5. Every rule declared in `TARGETS` has positive and negative behavioral
   fixtures. Removing the `BOARD.md row` rule or the
   `OKR.md § Commitments` rule must fail. The distinction between a target's
   broad `pattern` and its narrower `cell` is exercised. When one step names
   multiple targets, every target is scanned; changing the R2-hit path from
   `continue` to `break` must fail.
6. The tests hold the complete semantic defect categories found in the first
   two V4 rounds, not only the original planted sentences:
   - suppression leakage or unrelated discharge, including section scope,
     template scope, owner-pattern boundaries, and both proximity windows
     (round-2 mutations G1-G4);
   - disabled targets or skipped scanning units, including paragraph and step
     segmentation, prose before a list, `cell` handling, and multiple targets
     in one step (G5-G11);
   - false-positive control vocabulary, including the justified adoption,
     prohibition, descriptive, write, and read forms (G12-G20);
   - mechanical lane discovery of both `SKILL.md` and recursive `reference/`
     pages (G21).
   Each category has a stated rationale and a mutation-sensitive test. The
   numbered mutations remain the review inventory, but line numbers are not
   the contract.
7. The live in-scope corpus reports zero unlicensed hand edits. If satisfying
   these criteria exposes a genuine violation in a `goals/`, `work/`, or
   `decide/` procedure page, that page is corrected to call the deterministic
   tool; the guard is not weakened to preserve a zero count.
8. `TASK-101` is the downstream whole-tree expansion. Stabilize these guard
   semantics and tests first, then widen the corpus. In particular,
   `packs/software-ops/incidents.md:84` is an explicitly known deferred
   violation owned by `TASK-101`; `TASK-096` must neither silently claim a
   project-wide zero nor expand into `packs/` to absorb it.

### Verification — V4

1. Run mutation controls for every category in Deliverable item 6. A test is
   accepted only when the stock implementation is green and the relevant
   weakening or widening mutation is red; an assertion over a copied regex or
   a live-tree count alone is not sufficient.
2. The lane-discovery fixtures prove all of the following: `SKILL.md` is not
   dropped, recursive `reference/**/*.md` pages are not dropped, either half
   of the lane-shape predicate cannot be removed, and a synthetic fourth lane
   is included while its `state/` pages remain excluded.
3. Suppression-observability fixtures prove the reported page, line or
   section, exemption identity, target, and step. They include a non-adoption
   section after an adoption section and a fenced heading so raw-line heading
   enumeration cannot substitute for `scan()` behavior.
4. Run the focused guard suite, the broader relevant test suite,
   `python3 bin/perry-lint`, and `git diff --check`. Record exact commands and
   results; unrelated failures are separated from TASK-096 failures rather
   than omitted.
5. A fresh-context V4 reviewer works only on disposable copies under `/tmp`
   for destructive trials, clears Python bytecode caches between mutations,
   and waits past filesystem timestamp boundaries before rerunning imported
   code. The verdict maps every failure to an acceptance item and states what
   was not checked.
6. PASS requires all in-scope categories above to have behavioral proof and no
   unresolved in-scope violation. A finding outside this corpus is recorded
   against `TASK-101` and does not reopen TASK-096's agreed scope.

### Dependencies

- None. `TASK-101` depends on this task because corpus expansion must reuse
  stabilized guard semantics rather than changing semantics and coverage at
  the same time.

### In scope

- `tests/test_procedures_call_the_tool.py`.
- `goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md`, and their
  `reference/**/*.md` pages only when a genuine violation is exposed.
- TASK-096 implementation and review evidence.

### Out of scope

- Root `SKILL.md`, root `reference/`, `packs/`, `modes/`, `templates/`, and
  lane `state/` trees.
- `packs/software-ops/incidents.md:84` and whole-tree corpus expansion, both
  owned by `TASK-101`.
- Adding new tool-owned target families outside the currently declared
  `TARGETS`; that is a separate closed-list expansion decision.
- Changing deterministic writer behavior, task state, or the V4/V5 process.
- Closing TASK-096. Implementation returns it to fresh-context V4 review.

## Review convergence

This specification is the canonical acceptance contract. Later review rounds
must evaluate the full contract, not only the previous round's last mutation.
A FAIL identifies the violated item, demonstrates the behavioral control, and
states whether it is a new in-scope defect category or an instance of one
already listed. Repeating a green mutation without adding the missing focused
regression is not progress; widening the corpus belongs to TASK-101.
