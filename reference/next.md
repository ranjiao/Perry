# The next block — where the project is, and what to do next

`perry-state --section next` decides what Perry recommends. The agent puts that
answer into words and never chooses it. The rules are declared in
`reference/next-rules.json`. This page says why each rule exists and how the
block is rendered. The payload's keys and types are `schema/next-contract.md`.

DESIGN-020 § 5.2–5.4 is the design. Its § 9 entry of 2026-09-15 is the rule this
page enforces: **the command decides, the agent renders.**

## Where it is shown

- **`/perry`**, at `reference/snapshot.md` step 5: `perry-state --section next`.
- **A lane standup**, at its next-actions step:
  `perry-state --section next --lane goals` (or `work`, `decide`). A lane shows
  its own rules and the overlays.

Neither call writes anything, so both are safe on every standup.

`--after <subcommand>` keeps only the rules that may fire after that subcommand.
It belongs to the closing step of a state-changing command, and `TASK-443`
builds that step. It is not built here.

## Rendering

Render the block in the chat language, in this shape:

```
You are here: Goals ✓ · Phase 004 day 1 ✓ · Week 2026-W38 plan ? · Weekly review late
Next: /perry work triage — 5 queue item(s) are past their SLA, the longest-waiting being TASK-270
  also: /perry work friday-review — today is Tuesday and the last weekly report is 2026-W35
  cannot tell: whether this week is planned (week plans have no source until TASK-444 records a finalized week)
```

1. **You are here** — one line from `position[]`, in its order. Mark each step
   by its `state`: `done` ✓, `missing` ✗, `late` or `due` in words, `unknown` ?.
   Leave out `not_applicable` steps. Show `not_reached` steps dimmed or leave
   them out.
2. **Next** — `primary.command`, then `primary.reason`. If `primary` is `null`,
   print `Nothing is due.` and stop there. Never make up a next step.
3. **also** — one line per `alternates[]` entry, in order. There are at most
   two.
4. **cannot tell** — one line per `unknown[]` entry: what could not be decided,
   and its `reason`.

The reasons are written as plain sentences, and IDs appear inside them. Keep
them as they are. Translate them only when the chat language is not English.

### What the agent may and may not do

- **Never reorder, add or drop a recommendation.** The user sees exactly the
  `position`, `primary` and `alternates` the command returned.
- **One note of your own, at most, marked as yours**, on its own line below the
  block. It is for context the command cannot read, such as the user having
  just said to skip this week's review:

  ```
  (my note: you said to skip this week's review — the recommendation above still shows it)
  ```

  The note never replaces the primary and never names a different command as
  the one to run.
- **Do not count, compare or judge state to build the block.** If a
  recommendation looks wrong, the fix is a fact or a rule, not a different
  sentence.
- **`rule_errors` non-empty** means the rule file could not be used as
  declared. Say so in one line after the block. It is a defect to fix, not a
  reason to guess.

## How the rules are evaluated

- **Overlays first.** They always win and are kept under every `--lane` and
  `--after`.
- **Then the rules, in declared order.** A rule is eligible when its `spine`
  is `any` or is the mode of a declared track (`project.tracks[].mode`). Rules
  3–5 are `project` rules. A `queue` or `pipeline` project gets its own rules
  in their place and is never told to plan a phase or a week.
- **The first rule that fires is `primary`.** The next two that recommend a
  *different* command are `alternates`.
- **Three answers, not two.** A predicate over a fact the payload cannot tell
  is *unknown*. It does not fire, and the fact is listed in `unknown[]`.
  `all` is false as soon as one part is false. `any` is true as soon as one
  part is true. The same state always gives the same block.
- **Predicates compare typed values only**: a fact path, an operator
  (`eq ne lt le gt ge in exists nonempty`) and a literal or
  `{"threshold": name}`. No rule reads prose (ARCHITECTURE.md § NN-4).
- **Thresholds** come from `schema/state-schema.json § thresholds` when a name
  is declared there, which is read and never written. Otherwise they come from
  the rule file, with a note. `conformance.thresholds[]` says which source each
  one came from.

## The facts

Each fact is a value `perry-state` already computes, or the clock
(ARCHITECTURE.md § NN-1). Computing one needs no new read of a state file.

| Fact | From |
|---|---|
| `installed`, `recovery.blocking`, `recovery.first_path`, `interrupted.*` | the payload's `installed`, `recovery`, `interrupted` |
| `okr.present`, `okr.version` | `okr` |
| `phase.status`, `phase.number`, `phase.day` | `phase` |
| `phase.kr_progress.*` | `linkage.objectives[].krs[]`: `current`, `target` and `stretch` of the current phase's key results |
| `week.iso`, `today.date`, `today.weekday` | the clock |
| `history.*` | `history`: `latest_weekly`, `latest_handoff`, `latest_handoff_days`, `latest_journal_days` |
| `user_input_queue.*` | `user_input_queue.count` and `.oldest` |
| `design.pending_handoff_count`, `design.first_pending_id` | `design.pending_handoff` |
| `board.lines`, `board.cap`, `board.over_cap_by` | `board` |
| `project.spines` | `project.config.tracks[].mode` |
| `queue.sla_breaches`, `queue.oldest_breach_id` | `project.config.tracks[]`: `sla_check`, `sla_breaches` |
| `pipeline.wip_breaches` | `project.config.tracks[]`: `wip`, `wip_breaches` |

**A commit key result** is one whose `stretch` is not `true`. It is
**measured** when it has both a `current` and a `target`. It is **met** when
`current >= target`, but a target of `0` is met only at `0`, because such a key
result is counting something down. `met_ratio` is unknown when the phase has no
commit key result, or when any of them is unmeasured.

**Always unknown in this release**, because nothing computes them yet:

- `week.planned` and `drafts.drafted` — no source until `TASK-444`.
- `commitments.due` — `perry-state` does not compute which commitments are due.
- `phase.days_since_snapshot` — `perry-state` computes no date for the last
  phase snapshot.

## The rules

### R-recovery

A pending task transaction or a malformed dossier means the stores cannot be
trusted until it is repaired. Nothing else is worth doing first. It sends the
user to `/perry`, whose step 2 names every path and the repair.

### R-interrupted

An adoption or diagnosis run was left part-way, and the user's answers are in
its dossier. `/perry` step 2 shows the card that resumes or abandons it. Without
this overlay the run is invisible (`reference/snapshot.md § Why the
interrupted-run gate exists`).

### R-draft-waiting

A plan draft is written and waiting for approval. That approval comes before any
new work is planned. Drafts have no source until `TASK-444`, so this overlay
never fires yet. It adds `drafts.drafted` to `unknown[]` instead.

### R-setup

The directory is not an installed Perry project, so no other rule can say
anything. `/perry` runs first-time setup.

### R-no-okr

With no goals written down there is nothing to plan a phase against, and no key
result for work to serve. The sequence starts here.

### R-no-phase

The goals exist but no phase is active, so no work is aimed at a phase key
result. This is a `project` rule. Queue and pipeline tracks run on commitments,
not phases.

### R-phase-closable

At least 80% of the phase's measured commit key results are met, and none is
unmeasured. The phase can close: `end-phase-retro`, then the close sequence
(DESIGN-012). If any key result has no current value, the command cannot tell,
and says so.

### R-week-unplanned

A phase is active and this ISO week has no plan. It cannot fire until
`TASK-444` gives `week.planned` a source. Until then it adds `week.planned` to
`unknown[]` on every project with an active phase.

### R-sla-breach

A `queue` track's rows have waited longer than its declared SLA. In a queue
project this takes the place of rules 3–5. Triage is where the oldest breach is
picked up.

### R-queue-commitment-due

A queue project's commitment is due. It takes the place of rules 3–5 alongside
R-sla-breach. `perry-state` does not compute due commitments, so this rule is
declared and reports `commitments.due` as unknown.

### R-wip-over-limit

A `pipeline` track has a stage at or over its work-in-progress limit. In a
pipeline project this takes the place of rules 3–5. The limit is the pipeline's
central control (`modes/pipeline.md`).

### R-pipeline-commitment-due

The pipeline counterpart of R-queue-commitment-due. It is declared, and it
reports `commitments.due` as unknown for the same reason.

### R-asks-waiting

The oldest open question to the user has waited at least 5 days. That is the age
at which `/perry work nudge` surfaces it. Work blocked on a person is usually the
cheapest to unblock.

### R-review-due

It is Friday, no weekly report exists, or the newest report is older than last
week. The weekly report is where a week's work is summed up, and a lapsed one is
the first sign the cadence has stopped.

### R-phase-heartbeat

A phase that runs for `phase_heartbeat_days` (default 14) with no snapshot has
no frozen record to compare its end against. `goals/SKILL.md` used to prompt
`/perry goals snapshot` at that age, and this rule keeps the prompt. Nothing in
the payload dates the last snapshot, so the rule never fires. It reports
`phase.days_since_snapshot` as unknown on every project with an active phase.
DESIGN-020 § 5.3 has no place for it, so it sits after R-review-due, the other
cadence rule. ARCHITECTURE.md §7 asks whether it should survive.

### R-handoff-stale

Project state changed today, and the last handoff is at least 7 days old or
does not exist. "Changed today" means a journal line dated today, and every
mutating command writes one. This is a proxy for a session ending
(DESIGN-020 § 8), and its quality is measured in phase B.

### R-design-unhanded

A locked design has no implementation tasks, so a decision is made and no work
follows from it. Hand-off prints the tasks for `work` to add.

### R-board-over-cap

The board is longer than its cap. Past the cap it stops being read, and triage
pushes detail into evidence. No board file is measured any more, so
`board.lines` is `0` and this rule is quiet on every store-backed project.
