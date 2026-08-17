# TASK-028 — `diagnose` sees modes, and the front door mentions them

> Source: `perry/design/DESIGN-003-work-modes.md` § 6 phase G
> Rung: **V4**, not V5. DESIGN-003 assigned phase G V5 as a whole, on the strength of the hand-off-contract rewrite in § 7 — *"a bad edit shows up as silent cross-lane writes, not as a lint error"*. That task was TASK-026; it landed and was signed on 2026-08-16. What is left runs on other people's projects and is therefore V4 under `ADR-005`, which is newer and general. Recorded rather than assumed: if the reviewer disagrees, the rung is the thing to argue about.
> Dispatch mode: manual
> Estimated cycle: medium
> Subjective verification: whether the README reads like Perry's front door rather than a feature list. A human judgement, and the only one here.
> Touches architecture: (none)
> Deployed: no

**This file is the rubric a V4 reviewer scores against.**

## Scope, and the half that moved

Phase G's third task was *"diagnose/adopt mode detection; README rewrite"*.
**The `adopt` half is deferred to TASK-044**, deliberately: `ADR-004` made
migration mandatory and TASK-044 rebuilds `/perry adopt` around five new
guarantees. Building mode detection into the adoption pipeline now, then
rebuilding the pipeline, is work done twice. Say so in the commit so the defer
is a decision on the record and not an omission.

So: **`diagnose` mode detection, and both READMEs.**

## What must be true

### 1 · `diagnose` reports what mode a project's work is actually in

`bin/perry-diagnose` mentions `mode` twice, neither about work modes. A
project's shape is the first thing an audit should name, and DESIGN-003 § 5.1
already defines the four and what distinguishes them.

- [ ] For each track or, on a project with no register, for the project as a
      whole, `diagnose` says which of `project` / `pipeline` / `queue` /
      `inquiry` the observable evidence fits.
- [ ] **It reports evidence, not a verdict it cannot support.** The four modes
      are distinguished by what closes the horizon and what the spine is — a
      project with none of those signals gets "cannot tell", not a default.
      `reference/diagnose.md` already names a check whose signal never clears
      as worse than no check.
- [ ] A declared mode that disagrees with the evidence is a finding. A project
      whose register says `pipeline` and whose board shows a steady-state queue
      has one of the two wrong, and which one is the user's to say.
- [ ] The finding has a catalog row in `reference/diagnose.md` with an id in
      the existing scheme, and a `WHY` entry, like every other finding.

### 2 · The READMEs name the four modes

`grep -c mode README.md README_cn.md` returns **0 and 0**. DESIGN-003 is the
largest thing built this phase and the front door does not mention it. A reader
deciding whether Perry fits their project cannot find out that it is not only
for software sprints.

- [ ] Both READMEs describe the four modes, in the terms `modes/*.md` uses, and
      say how a project declares one.
- [ ] `README_cn.md` is a translation of meaning, not of sentence structure —
      `$PERRY_HOME/reference/i18n.md § Writing chat prose in a language that is
      not English` governs, and the terms with no settled Chinese equivalent
      stay English.
- [ ] Neither README describes anything that does not exist. The last review
      round found `/perry pmo decide <topic>` advertised in both, for a
      subcommand deleted from that lane — see `TASK-027-round4-review.md § i-1`,
      which is explicitly this task's to fix.
- [ ] `ADR-004` is reflected: a project migrates once, and one that will not
      stays readable and is not drivable. A front door that promises drop-in
      compatibility is now false.

### 3 · No claim without a checker

Both READMEs and `reference/diagnose.md` are documents this project has
repeatedly caught making false claims — a command that does not exist, a
restatement in a file that does not contain it, a procedure nobody wrote.

- [ ] Every command either README shows is one the router or a lane index
      actually declares. There is already a guard for this shape in
      `tests/test_shipped_vocabulary.py`; extend it rather than writing a
      second one.

## Out of scope

- `/perry adopt` — TASK-044.
- Anything under `bin/perry-lint`, `bin/perry-task`, `bin/perry-goals`,
  `bin/perry-decide`, `.perry/config.md`'s shape, `schema/state-schema.json`,
  or `reference/adoption.md`. **TASK-043 is in flight and owns those.**
- Changing what any mode means. `modes/*.md` is the source; this task reads it.

## Verification

| Rung | Check |
|---|---|
| V2 | `perry-lint` clean; the suite green |
| V3 | `diagnose` run against copies of `~/proj/gimegime-pmo` and `~/proj/PolyForge` — **never the originals** — and the mode it reports for each argued from the evidence it cites |
| V3 | a project with no distinguishing signal gets "cannot tell", shown by a fixture |
| V4 | this file, scored by someone who did not build it |

Mutation discipline: every finding and every refusal verified by reverting it
and confirming a test goes red. Revert exactly what you claim to revert.
