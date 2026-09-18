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
It belongs to the shared closing step below. Read-only commands keep their
existing output and do not run that step.

## Rendering

For the combined `/perry` snapshot, use `reference/snapshot.md § Step 4`'s
initial-screen budget and single detail view: position and primary initially,
all returned alternates and unknown causes behind its explicit detail pointer.
This changes placement only. A null primary never suppresses unknowns. Lane
standups and the closing step retain their existing rendering and procedure.

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
- **`conformance.rule_errors` non-empty** means the rule file could not be used as
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
| `drafts.drafted` | `drafts.drafted`: drafted plans, plus approved ones whose content changed; unknown while a plan is unreadable |
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

- `week.planned` — no source until `TASK-444` records a finalized week.
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

A plan draft is written and waiting for review: `drafted`, or approved and
changed since. That approval comes before any new work is planned. `/perry
plan` here means only: resume that draft through
`goals/reference/planning.md` — re-read it, show the path and summary, ask.
There is no planning router for a new horizon yet; with no draft, the direct
entrances (`/perry goals init`) apply. An approved, unchanged draft fires
nothing: its finalize writer does not exist, and nothing finalizes on startup.

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

## Closing step

This is the one proactive closing procedure (DESIGN-020 UD 3/8). It is an
agent instruction, not a new recommendation engine or automatic command runner.

1. **Complete first.** Run once after the outer user-invoked state-changing
   procedure has completed its writes and reported its result. Skip read-only,
   dry-run, refused and cancelled paths. Nested helpers return to their caller;
   they do not ask a second next-step question. Skip **dispatched agent sessions**
   and **planning in progress**, including a first-init interview or chat draft
   still awaiting approval: their existing flow owns the next question. Session
   context supplies these facts; do not parse prose or create a hidden flag.
2. Read `"$PERRY_HOME/bin/perry-config" show --root . --json`. The existing
   `settings.proactive_next_steps` is the exact enum `on | off`; absent means
   `on`. `off` skips this closing block and question, not passive standups or
   safety gates. An unexpected value or failed read is a configuration error:
   report it and ask no next-step question; never infer the user's preference.
3. Run `"$PERRY_HOME/bin/perry-state" --root . --section next --after <subcommand>`
   using the actual outer subcommand token from the inventory below. Do not
   alias `status` to `friday-review` to obtain a different recommendation. The
   existing CLI forbids `--compact` with `--section`; this legal invocation
   intentionally omits the combination printed in DESIGN-020 §5.4. No CLI or
   payload contract is changed. If it fails, report the failure, do not guess.
4. Read the returned `next`. Nonempty `conformance.rule_errors` means report the defect and
   ask nothing. Otherwise render at most three recommendation lines in chat
   language: `✓ <what actually finished>. Next: <primary.command> — <primary.reason>`;
   then each `alternates[]` entry in returned order, with its command and reason.
   Do not add, substitute, reorder or drop recommendations. Unknown facts are
   not permission to invent advice. `primary: null` means `✓ <finished>. Nothing
   is due.` and **no question**; the successful result still stands.
5. If there is a primary, use the host choice UI: `Run <primary.command> now
   (Recommended)`, each returned alternate, and `Not now`. If the host has too
   few choice slots, present the same complete numbered set in chat and wait
   for the user's explicit selection; no silent truncation or automatic choice.
   A selection routes the exact returned command through the normal router,
   preserving its own gates. `Not now`, no response, or dismissal ends here.
   Do not execute a recommendation merely because it was returned.

### Procedure inventory

Bound: the currently shipped user-facing router/lane procedures and their
pack extensions, inspected for actual writes (including reports and config).
Each row is a completion-capable procedure, not a claim that every invocation
writes. The pointer in that procedure applies only after its write path.
`setup`/`bootstrap` name successful first-time procedures, not new CLI verbs.
Nested knowledge promotion, ADR bootstrap/migration and tool writer calls close
through their outer procedure; they do not mint new skill commands. Multiword
operations keep their literal first subcommand token for `--after`; options and
IDs are not recommendation-rule names. Rules may yield no result for a listed
command: changing the rule table is outside this task.

| Lane | Procedure | Source | After token |
|---|---|---|---|
| `router` | `setup` | `SKILL.md` | `setup` |
| `router` | `relocate` | `SKILL.md` | `relocate` |
| `router` | `adopt` | `reference/adoption.md` | `adopt` |
| `router` | `diagnose` | `reference/diagnose.md` | `diagnose` |
| `goals` | `init` | `goals/reference/setup.md` | `init` |
| `goals` | `revise` | `goals/reference/setup.md` | `revise` |
| `goals` | `commit` | `goals/reference/phases.md` | `commit` |
| `goals` | `plan-phase` | `goals/reference/phases.md` | `plan-phase` |
| `goals` | `score-phase` | `goals/reference/phases.md` | `score-phase` |
| `goals` | `snapshot` | `goals/reference/phases.md` | `snapshot` |
| `goals` | `plan-week` | `goals/reference/weekly.md` | `plan-week` |
| `goals` | `link` | `goals/reference/linkage.md` | `link` |
| `goals` | `pivot` | `goals/reference/pivots.md` | `pivot` |
| `decide` | `init` | `decide/SKILL.md` | `init` |
| `decide` | `new` | `decide/SKILL.md` | `new` |
| `decide` | `resolve` | `decide/SKILL.md` | `resolve` |
| `decide` | `lock` | `decide/SKILL.md` | `lock` |
| `decide` | `revise` | `decide/SKILL.md` | `revise` |
| `decide` | `supersede` | `decide/SKILL.md` | `supersede` |
| `decide` | `drop` | `decide/SKILL.md` | `drop` |
| `decide` | `adr` | `decide/reference/decisions.md` | `adr` |
| `work` | `bootstrap` | `work/reference/bootstrap.md` | `bootstrap` |
| `work` | `plan-week` | `work/reference/subcommands.md` | `plan-week` |
| `work` | `triage` | `work/reference/subcommands.md` | `triage` |
| `work` | `status` | `work/reference/subcommands.md` | `status` |
| `work` | `friday-review` | `work/reference/subcommands.md` | `friday-review` |
| `work` | `monday-plan` | `work/reference/subcommands.md` | `monday-plan` |
| `work` | `midweek-check` | `work/reference/subcommands.md` | `midweek-check` |
| `work` | `mid-phase-review` | `work/reference/subcommands.md` | `mid-phase-review` |
| `work` | `end-phase-retro` | `work/reference/subcommands.md` | `end-phase-retro` |
| `work` | `risk` | `work/reference/subcommands.md` | `risk` |
| `work` | `add-task` | `work/reference/subcommands.md` | `add-task` |
| `work` | `close-task` | `work/reference/subcommands.md` | `close-task` |
| `work` | `drop-task` | `work/reference/subcommands.md` | `drop-task` |
| `work` | `coordinate` | `work/reference/subcommands.md` | `coordinate` |
| `work` | `handoff` | `work/reference/subcommands.md` | `handoff` |
| `work` | `rollover` | `work/reference/subcommands.md` | `rollover` |
| `work` | `delegate` | `work/reference/delegate.md` | `delegate` |
| `work` | `dispatch` | `work/reference/dispatch.md` | `dispatch` |
| `work` | `autopilot` | `work/reference/autopilot.md` | `autopilot` |
| `work` | `digest` | `work/reference/digests.md` | `digest` |
| `work` | `review` | `work/reference/review.md` | `review` |
| `work` | `health-check` | `work/reference/health-check.md` | `health-check` |
| `work` | `architecture init` | `packs/software-ops/architecture.md` | `architecture` |
| `work` | `architecture review` | `packs/software-ops/architecture.md` | `architecture` |
| `work` | `architecture-audit` | `packs/software-ops/architecture.md` | `architecture-audit` |
| `work` | `incident` | `packs/software-ops/incidents.md` | `incident` |
| `work` | `incident close` | `packs/software-ops/incidents.md` | `incident` |
| `work` | `incident archive` | `packs/software-ops/incidents.md` | `incident` |
| `work` | `runbook-check` | `packs/software-ops/runbooks.md` | `runbook-check` |

Read-only exclusions: router/lane standups and help; goals `krs`, `dashboard`;
decide `status`, `handoff` (reprints only); work `nudge`, `architecture diff`,
`incident list`. Conditional writes include triage, risk, diagnose/adopt dossier
work, audit/report writers and config preferences; pure inspection paths skip.
Alias routes inherit the canonical procedure, but keep the user's actual
subcommand token. Setting/unsetting silence via the existing config tool is a
preference change, not an invitation to immediately ask a next-step question.
When adding a procedure, explicitly classify it here and add its completion
pointer; the inventory guard checks declared routing, not prose meaning.
