# DESIGN-020: Perry has a sequence and never tells the user where they are in it

> Status: locked
> Date: 2026-09-14 · Locked: 2026-09-14
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: O3-KR1, O3-KR2 (`perry/OKR.md` v3, Objective 3 — the skill is the product, and it is written well enough to be one)
> Supersedes: DESIGN-011   · Superseded by: —
> Revisits: `SKILL.md § Mandatory first move` step 5, `reference/snapshot.md § Step 5`, `goals/SKILL.md` standup step 5, `work/SKILL.md` standup step 7, `decide/SKILL.md` snapshot step 5, `reference/first-run.md § The recommended order for a new project`, `goals/reference/setup.md`, `goals/reference/phases.md § plan-phase`, `goals/reference/weekly.md`
> Sign-off: User Decisions 1–8 answered by Ran Jiao in session on 2026-09-14; 9–12 are inherited from `DESIGN-011` as chosen there. Moved `draft` → `locked` without an `in_review` hold, as `DESIGN-013` and `DESIGN-014` did, because that state exists to await exactly these answers. The lock-time `reference/input-quality.md § 3` pass raised 3.3 (no alternative to the whole approach), 3.4 (goal 1 had no bound) and 3.6 (affected surfaces unlisted); all three were fixed before lock at the user's choice — § 5.9, goal 1, § 5.8.

## 1. Problem

Two halves of one defect. **Perry has an intended sequence — set goals, plan a
phase, plan the week, work, review, close the phase, plan the next — and the
user can neither see where they are in it nor get from one step to the next
without already knowing the command.** And when they do reach a planning step,
the plan is collected as fields rather than drafted with them.

### 1.1 The sequence lives only in prose, and only fires when asked

- **The command surface is large and partly ambiguous.** The three lane
  `SKILL.md` files carry 77 backticked command rows between them
  (`grep -cE '^\| `[a-z-]+'`: goals 23, work 40, decide 14, measured
  2026-09-14). The router lists five bare names that must be disambiguated
  (`plan-week`, `handoff`, `status`, `revise`, `init`), and `plan-week` means two
  different things: `goals` proposes 3–5 weekly tasks, `work` picks this ISO
  week's 3–5 P0 rows.
- **The intended order is written down once, for first run only.**
  `reference/first-run.md § The recommended order for a new project` lists
  `goals init → plan-phase → work → decide init → plan-week` and then never
  speaks again. The phase-close order is not written down at all (`DESIGN-012`).
- **"Suggest next actions" exists at five sites, and none is a rule.**
  `reference/snapshot.md` step 5 (4 examples), `goals/SKILL.md` standup step 5
  (two "auto" prompts plus 3 examples), `work/SKILL.md` standup step 7 (11
  examples), `decide/SKILL.md` step 5 (3 examples), and one subcommand row
  (`score-phase` — "Suggests next `plan-phase`"). Each is a list of example
  sentences an agent pattern-matches. No condition is stated in terms of a
  field, no state payload carries the facts, and two agents reading the same
  project can recommend different things.
- **Nothing fires after a command finishes.** Every one of those sites is a
  standup or snapshot. A user who has just finished `plan-phase` is told
  nothing about `plan-week`; a user who finished `score-phase` is told about
  `plan-phase` only by that one table cell.
- **Measured on this repository**: `perry-state --json § history` on
  2026-09-14 (ISO week 38) reports `latest_weekly: 2026-W35` and
  `latest_handoff_days: 15`. The work standup prints both numbers; no rule turns
  either into a recommendation. The goals lane's KR-progress prompt ("≥80% of
  commit KRs achieved → suggest `score-phase`") cannot fire at all: none of the
  19 overall KRs carries a current value.

This is the shape `TASK-266` already named: **an instruction with no surface
behind it does not run.**

### 1.2 Plans are collected, not drafted

Inherited from `DESIGN-011 § 1`, and still true:
`goals/reference/setup.md § init` is a ten-field checklist with zero
`AskUserQuestion` calls (measured 2026-08-27; the file is 50 lines and was last
touched 2026-09-03 for a link fix). `DESIGN-011` locked the fix on 2026-08-28 —
a question bank asked one question at a time — and none of `TASK-190`…`TASK-194`
has started.

`DESIGN-011` also stopped short in three places this design needs:

1. **No draft the user edits.** Its output goes from the premise challenge
   straight to `OKR.md`. There is no stage where the user sees the whole plan,
   changes a line in their own editor, and approves it — the cheapest edit a
   person can make is to a draft, and the design never produces one.
2. **Nothing persists mid-interview.** An interview interrupted at question 4
   is lost; `DESIGN-001`'s LOSSLESS property was written for adoption and
   diagnosis and never applied to planning.
3. **Its own non-goal forbids half of this design.** `DESIGN-011 § 3` lists
   "Touching the tier-0 router" as out of scope. A passive recommendation at
   `/perry` is exactly that. Revising a locked doc to reverse a non-goal is a
   structural change, so this doc supersedes it.

And one constraint that did not exist when `DESIGN-011` was written: **KRs are
store records** (`ADR-019`, `DESIGN-013 § 5.1`), and `goals` has no KR writer
(`TASK-264`). A finalize step has nothing to call today; hand-appending
`okr.jsonl` is what `O2-KR1` exists to end.

### 1.3 What the rest of the field does

Recorded because two of these are patterns to take and two are costs to avoid
(full notes: 2026-09-14 product research, sources in § 10).

- **Take**: Spec Kit `/clarify` asks at most five questions, one per message,
  each with a recommended option, and writes each answer into the artifact
  immediately. gstack `/office-hours` writes a `Status: DRAFT` document and asks
  *Approve / Revise* before anything is final. superpowers' brainstorming stops
  for approval before writing a plan.
- **Avoid**: Scott Logic measured Spec Kit producing 2,577 lines of markdown for
  689 lines of code with 3.5 hours of review. gstack's draft step runs an
  adversarial reviewer subagent in a loop, and review loops are the most-cited
  cost complaint across these tools (superpowers #1152, #1120).

## 2. Goals

1. **Proactive.** After a Perry command that changes project state completes,
   the reply ends with one *next* block of at most three lines — at most one
   primary recommendation and two alternates — each with a plain-language reason and the exact command, and
   an offer to run the primary now.
2. **Passive.** `/perry` with no arguments shows a one-line *you are here*
   position on the sequence and the same *next* block, computed from the same
   rules as goal 1.
3. **Deterministic.** Every recommendation is produced by evaluating typed
   facts against a declared rule table: the same state yields the same
   recommendation, and each recommendation names the facts that fired it. The
   five example lists in § 1.1 are replaced by pointers to that table.
4. **Honest about what it cannot know.** A rule whose fact is unknown does not
   fire; the block says what could not be determined instead.
5. **One planning flow, three horizons.** `goals init` / `revise`,
   `plan-phase` and `plan-week` run *interview → draft → edit → approve →
   finalize*, with at most 8, 5 and 2 questions respectively before a draft
   exists.
6. **The user edits, not composes.** Every question carries a drafted answer:
   a choice question offers 2–3 options with the drafted one first; an open
   question shows a proposed sentence to accept or change.
7. **The draft is a file.** It can be edited in any editor or in aiMark, and an
   interrupted flow resumes at its next unanswered question without re-asking
   (`DESIGN-001`: DISCOVERABLE, POSITIONED, LOSSLESS).
8. **Nothing becomes state before approval, and state is written by tools.**
   Finalize calls the owning lane's writer. No store is hand-appended, and
   `OKR.md`, `phase/`, `okr.jsonl`, `linkage.jsonl` and the board are untouched
   until the user approves.
9. **The output is good.** A plan produced by the flow passes
   `reference/input-quality.md § 1` with zero issues on a real transcript
   (`DESIGN-011` goal 3, inherited; the rubric is unchanged).
10. **Silenceable.** A user can turn proactive blocks off for a project and
    still get the passive one.

## 3. Non-Goals

- **Running a recommended command without the user's say-so.** A
  recommendation is an offer. Tools that decide for the user are the ones users
  leave (2026-09-14 research: Motion).
- **A model choosing what to recommend.** The agent phrases the block; it never
  picks which rule fired or reorders them.
- **An adversarial reviewer loop on drafts.** The rubric runs once, inline,
  advisory with override. § 1.3 is why.
- **gstack's decision-brief format** (per-option completeness scores, ✅/❌
  bullets of ≥40 characters). Questions follow `reference/user-load.md`.
- **Any background process, schedule or notification.** "Proactive" means at
  the end of a command the user ran — Perry's anti-goal of no daemon stands.
- **Removing or renaming a subcommand or alias.** Existing entrances stay; this
  adds guidance over them.
- **Changing what `OKR.md` or a phase file looks like**, or
  `reference/input-quality.md` (inherited from `DESIGN-011`).
- **Porting office-hours' content**, and **a per-question preference store**
  (inherited from `DESIGN-011`).
- **Interviews for `decide new` and `work add-task`.** Left to § 8.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Where recommendations surface | After commands + at /perry / At /perry only / Goals lane only | **After commands + at /perry** | 2026-09-14 |
| 2 | Relationship to DESIGN-011 | New design superseding it / Revise DESIGN-011 | **New design superseding it** | 2026-09-14 |
| 3 | Which commands end with a next block | State-changing only (Recommended) / Every command / Planning and close only | **State-changing only** | 2026-09-14 |
| 4 | Who evaluates the rules | perry-state over a rule file (Recommended) / Agent reads facts and prose / Rules inside state-schema.json | **perry-state over a rule file** | 2026-09-14 |
| 5 | Where a planning draft lives | Draft file under state root (Recommended) / Chat only / Adoption-style dossier | **Draft file under state root** — includes consent to the one `state-schema.json § claims[]` entry for `plans/` | 2026-09-14 |
| 6 | A single planning entrance | Add /perry plan (Recommended) / No new command | **Add /perry plan** | 2026-09-14 |
| 7 | Default shape of a first OKR | 1 objective, ≤3 KRs (Recommended) / 1–3 objectives as today / Appetite + signals allowed | **1 objective, ≤3 KRs** | 2026-09-14 |
| 8 | Silencing proactive blocks | Per-project setting (Recommended) / Per-rule snooze / Not silenceable | **Per-project setting** | 2026-09-14 |
| 9 | What routes the question set | track spine (DESIGN-008) | **track spine** — inherited, DESIGN-011 UD 1 | 2026-08-28 |
| 10 | How hard the push is | name the gap, offer a rewrite, once | **once** — inherited, DESIGN-011 UD 2 | 2026-08-28 |
| 11 | Does plan-phase share the bank | yes | **yes** — inherited, DESIGN-011 UD 3 | 2026-08-28 |
| 12 | Where the premise challenge sits | after questions, before the draft is approved | **before approval** — inherited, DESIGN-011 UD 4, restated for the draft stage | 2026-08-28 |

**On 1 and 2.** Answered by Ran Jiao in session, 2026-09-14: recommendations
are both proactive ("the current work is done; next, run `/perry …`") and
passive at the top-level command, and this is a new design that replaces
`DESIGN-011`.

**On 3.** A read (`/perry help`, `status`, `dashboard`) already ends in the
user's own next question; a block there is noise. *Every command* is the most
guidance and the most tokens. *Planning and close only* misses `close-task`,
`friday-review` and `handoff`, which are exactly where cadence lapses (§ 1.1).

**On 4.** The rule conditions are typed predicates, so code may evaluate them
(`ADR-007` decisions 2–3). A rule file read by `perry-state` makes the same
state produce the same answer and makes a rule testable. *Agent reads facts and
prose* is today's behaviour, and § 1.1 is its result. *Inside
`state-schema.json`* puts the rules beside the other declarations, and any edit
to that file is a project-wide change that needs the user's consent each time.

**On 5.** A draft file is the only option that satisfies goals 7 and 8 at once.
It adds a claimed path, which means one edit to `schema/state-schema.json §
claims[]` — named here so the consent is given with the decision, not
discovered at implementation. *Chat only* loses the edit surface and every
interrupted interview. *Adoption-style dossier* puts a plan inside `.perry/`,
where users do not look for their own documents.

**On 6.** `/perry plan` resolves to `init`, `plan-phase` or `plan-week` from the
facts, so the user needs one word instead of knowing three commands and which
lane's `plan-week` they mean. The existing subcommands remain direct entrances.

**On 7.** Wodtke's *Radical Focus* sets one objective and three key results; the
2026-09-14 research found no evidence that solo builders use multi-objective
OKRs. *Appetite + signals* (Shape Up) lets a small project skip KR vocabulary
entirely.

**On 8.** A per-rule snooze needs a store of snoozes. A project setting is one
config record, and the passive block stays available either way.

## 5. Architecture

### 5.1 Overview

```
typed state (stores, config, history, drafts, clock)
        │
        ▼
perry-state --section next [--after <subcommand>] [--lane <lane>]
        │  facts{}  →  rule table (in order)  →  fired[]
        ▼
payload: position[] · primary · alternates[≤2] · unknown[]
        │
        ├── passive:   /perry snapshot, lane standups
        └── proactive: closing step of a state-changing subcommand
                         │
                         └─ user picks → router runs that subcommand
                                           (planning commands enter § 5.5)
```

### 5.2 The facts

Only typed values and filesystem facts. Most already exist in `perry-state`;
the new ones are marked.

| Fact | Source | Today |
|---|---|---|
| `installed`, `recovery.blocking`, `interrupted[]` | `perry-state` | exists |
| `okr.present`, `okr.version` | `okr.jsonl` | exists |
| `phase.status`, `phase.number`, `phase.day` | `phase/CURRENT`, linkage | exists |
| `phase.kr_progress` — commit KRs measured / met / unmeasured | `linkage.jsonl` current vs target | **new**; `unmeasured` when no current value |
| `week.iso`, `week.planned` | clock; the latest finalized week draft (§ 5.5) | **new** |
| `history.latest_weekly`, `history.latest_handoff_days` | `weekly/`, `handoff/` | exists |
| `drafts[]` — horizon, status, step, age | draft files' typed frontmatter (§ 5.5) | **new** |
| `user_input_queue.count`, `.oldest` | `asks.jsonl` | exists |
| `design.pending_handoff` | `perry-state § design` | exists (known false positives: `TASK-212`, `TASK-282`) |
| `board.lines`, `board.cap` | board | exists |
| `project.tracks[].spine` | `.perry/config.jsonl` | exists |
| `today.weekday` | clock, injectable for tests | **new** |

A draft's body is never read by Python. Only its frontmatter enums and dates
are facts.

### 5.3 The rule table

One rule file, read by `perry-state`, explained rule-for-rule in
`reference/next.md` (UD 4). Each rule:

```
id        stable handle, e.g. R-week-unplanned
when      predicate over facts (typed comparisons only)
spine     project | pipeline | queue | inquiry | any
lane      goals | work | decide | router
command   the exact command to recommend
reason    template filled from the facts that fired it
after     subcommands after which it may fire proactively ([] = passive only)
```

Evaluation: rules in declared order; **overlays first**, which always win; then
the sequence. The first rule that fires is the primary; the next two that
recommend *different* commands are the alternates. A rule whose `when` touches
an unknown fact does not fire and adds that fact to `unknown[]`.

The initial table for a `project`-spine track. This is the sequence Perry's
prose already prescribes, stated as conditions for the first time:

| Order | Rule | When | Recommend |
|---|---|---|---|
| overlay | R-recovery | `recovery.blocking` | the recovery the payload names |
| overlay | R-interrupted | `interrupted[]` non-empty | resume or abandon it |
| overlay | R-draft-waiting | a draft is `drafted` (awaiting approval) | review that draft |
| 1 | R-setup | `installed = false` | first-time setup |
| 2 | R-no-okr | `okr.present = false` | `/perry plan` → OKR route |
| 3 | R-no-phase | OKR present, no active phase | `/perry plan` → phase route |
| 4 | R-phase-closable | `phase.kr_progress.met / measured ≥ 0.8` and nothing unmeasured | `/perry work end-phase-retro`, then the close sequence |
| 5 | R-week-unplanned | active phase, `week.planned = false` | `/perry plan` → week route |
| 6 | R-asks-waiting | an ask older than 5 days | `/perry work nudge` |
| 7 | R-review-due | `today.weekday = Friday` or last weekly older than last ISO week | `/perry work friday-review` |
| 8 | R-handoff-stale | `latest_handoff_days ≥ 7` and a state-changing command ran today | `/perry work handoff` |
| 9 | R-design-unhanded | `design.pending_handoff` non-empty | `/perry decide handoff <id>` |
| 10 | R-board-over-cap | `board.lines > board.cap` | `/perry work triage` |

`queue` and `pipeline` spines replace rules 3–5 with their own (SLA breach, WIP
over limit, commitment due) and never recommend a phase or a week plan.
Thresholds come from `schema/state-schema.json § thresholds`, never literals.

### 5.4 The payload and the two surfaces

```json
"next": {
  "contract": "perry-next/1.0",
  "position": [
    {"step": "goals", "state": "done", "label": "OKR v3"},
    {"step": "phase", "state": "done", "label": "Phase 003, day 18"},
    {"step": "week",  "state": "missing", "label": "2026-W38 not planned"},
    {"step": "review", "state": "late", "label": "last weekly 2026-W35"}
  ],
  "primary":    {"rule": "R-week-unplanned", "command": "/perry plan",
                 "reason": "2026-W38 has no plan", "facts": ["week.planned=false"]},
  "alternates": [{"rule": "R-review-due", "command": "/perry work friday-review",
                  "reason": "the last weekly report is 2026-W35", "facts": ["history.latest_weekly=2026-W35"]}],
  "unknown":    ["phase.kr_progress: no key result has a current value"],
  "conformance": {"...": "per perry-state convention"}
}
```

**Passive.** `/perry` renders the `position` line directly under the TL;DR and
replaces today's step 5 with the `next` block. Lane standups call the same
section with `--lane`, so a lane shows its own rules and the overlays. Rendered
as:

```
You are here: Goals ✓ · Phase 003 day 18 ✓ · Week 38 plan ✗ · Weekly review late
Next: /perry plan — 2026-W38 has no plan
  also: /perry work friday-review — the last weekly report is 2026-W35
  cannot tell: whether the phase can close (no key result has a current value)
```

**Proactive.** Every subcommand selected by UD 3 ends with one shared closing
step, defined once in `reference/next.md § Closing step` and cited by pointer
from each procedure:

1. Run `perry-state --section next --after <subcommand> --compact`.
2. Render at most three lines: `✓ <what finished>. Next: <command> — <reason>`,
   plus alternates.
3. Ask with the host choice UI: `Run <primary> now (Recommended) | <alternate> |
   Not now`. Selecting runs it through the router; `Not now` ends the turn.
4. Nothing fired → say `Nothing is due.` and ask nothing. Never manufacture a
   next step.

The closing step is skipped when proactive blocks are silenced (UD 8), inside a
dispatched agent session (no human is reading), and in the middle of a planning
flow — the flow's own next question is the next step.

### 5.5 The planning flow

One engine, one question bank, routed by horizon and track spine.

```
route → interview → draft → edit ⇄ revise → premise check → rubric → approve → finalize → next
         (≤8/5/2 Q)  (file)  (editor or chat)                (once)   (user)    (tools)
```

**Routes.**

| Route | Entered when | Questions before draft | Produces | Finalize writes through |
|---|---|---|---|---|
| OKR, first | no OKR | ≤8, shortest path 4–5 | mission, objectives, KRs, anti-goals | `perry-okr` / the goals KR writer (`TASK-264`) |
| OKR, revision | OKR exists, user asks or pivots | ≤5 | a new version block: what changed, which KRs it invalidates | same |
| Phase | OKR exists, no active phase | ≤5 | focus, not-doing, definition of done, phase KRs, appetite | goals phase writer (`TASK-157` names the gap) and `perry-goals link` |
| Week | active phase, week unplanned | ≤2 | 3–5 proposed tasks, each linked to a KR or declared unlinked | proposed by `goals`, written by `work` through `perry-task add` (hand-off contract) |
| Commitments | `pipeline` / `queue` spine | ≤3 | arrival rate or SLA, what "resolved" means | `perry-goals commit` |

**The question bank** is `DESIGN-011 § 5.1`'s format, kept, with two fields
added:

```
### Q<n> · <what it is for>

Kind:                choice | sentence
Draft answer:        how to propose one — from the repo, the state, or earlier answers
Ask:                 the question, in the user's language
Push until you hear: what a real answer contains
Red flags:           answers that look like answers and are not
Produces:            the draft section(s) this answer becomes
Skip when:           the condition under which it is already answered
```

A `choice` question renders the drafted option first with `(Recommended)`. A
`sentence` question shows the proposed sentence with `Use this | Edit it | Say
it differently`. On Codex both fall back to numbered free text
(`reference/host-capabilities.md § Prompt rendering`). Smart-skip, the single
push, the escape hatch and the anti-sycophancy table are `DESIGN-011 § 5.2–5.4`,
unchanged.

**The draft file** (UD 5): `<state root>/plans/<horizon>/<YYYY-MM-DD>-<slug>.md`.
Typed frontmatter, prose body:

```yaml
horizon: okr | phase | week | commitments
route: first | revision
status: interviewing | drafted | approved | finalized | abandoned
step: q3                 # next unanswered question; POSITIONED
answered: [q1, q2]
target: "phase/004"      # what finalize will write
created: 2026-09-14
updated: 2026-09-14
finalized_refs: []       # ids and paths written at finalize
```

The body has the target document's shape — the OKR or phase template's sections
— filled from the answers as they arrive, so the file is useful from the first
answer on (LOSSLESS). `perry-state`'s interrupted scan gains a `plan` pipeline
over these files (DISCOVERABLE).

**Edit and approve.** Once the route's questions are answered, `status` becomes
`drafted`. The agent shows the path and a summary of 12 lines or fewer
(objective and KR titles, or the task list), and asks:
`Approve (Recommended) | Change a section | I'll edit the file | Abandon`.
*Change a section* takes one instruction ("KR2 should be a retention number")
and edits only that section. *I'll edit the file* ends the turn; the next
`/perry` shows `R-draft-waiting`. Before approval the premise challenge runs
(`DESIGN-011 § 5.5`), and then the rubric (`reference/input-quality.md § 1`)
runs **once**, surfacing at most three advisory issues the user may override.

**Finalize.** On approval the agent reads the draft — its meaning is the
agent's to interpret, never Python's — and calls the owning lane's writer with
typed fields. A writer that refuses stops finalize with its message. **A writer
that does not exist stops finalize and says which one**; nothing is
hand-appended. On success `status: finalized`, `finalized_refs` records what was
written, and the closing step (§ 5.4) runs with `--after plan`.

A finalized draft is history. Nothing reads it as authority afterwards: the
stores are the state, and an edit to `OKR.md` after finalize is an edit to the
projection, handled as it is today.

### 5.6 `/perry plan` (UD 6)

Resolved by the router from `next` facts, in order: an interrupted or `drafted`
plan → resume it; no OKR → OKR route; no active phase → phase route; week
unplanned → week route; otherwise ask which: *revise the OKR · start a new
phase · re-plan this week*. `goals init`, `goals revise`, `goals plan-phase`
and `plan-week` stay as direct entrances into the same routes.

### 5.7 What does not change

`reference/input-quality.md`, byte for byte. The shape of `OKR.md` and of a
phase file. The hand-off contract: `goals` proposes weekly tasks and `work`
writes them. Every existing subcommand and alias.

### 5.8 Affected surfaces

What this design changes, so implementation and review know where to look.

| Surface | Change | Cost or constraint |
|---|---|---|
| `SKILL.md` — the tier-0 router, 222 lines, read on every invocation | snapshot step 5 becomes a pointer to the `next` block; `/perry plan` joins the command surface | every added line is paid on every `/perry` call, which is why `DESIGN-011 § 3` excluded the router; the closing step's body lives in `reference/next.md`, not here |
| `goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md` | the example lists become pointers; each subcommand UD 3 selects gains the closing-step pointer | lane files load on demand, so the cost is per lane |
| `goals/reference/setup.md`, `phases.md § plan-phase`, `weekly.md` | rewritten around the question bank and the draft flow | inherits `DESIGN-011`'s scope for `setup.md` |
| `bin/perry-state` | a `next` section; a `plan` pipeline in the interrupted scan | a published payload: its `schema` field and `O2-KR4`'s documented-versus-emitted parity apply |
| `schema/README.md` contracts table | a `next` row with its own contract document, as `perry-roles/list` has | aiMark does not shell out to `perry-state` (`schema/README.md`, line 206), so it sees `next` only through that row |
| `schema/state-schema.json § claims[]` | one entry for `plans/` | consented in UD 5 |
| the rule file and `reference/next.md` (both new) | the declared rules and their prose | a test keeps every rule id present in both |
| `.perry/config` | one `- Key: value` setting for UD 8 | documented in `reference/config.md` |
| `reference/first-run.md`, `reference/snapshot.md` | the recommended order and step 5 point at the rule table instead of restating it | — |
| `tests/test_shipped_vocabulary.py` | `reference/next.md` joins the shorthand carve-out if it quotes lane commands | the router names this test as that carve-out's mechanical list |

### 5.9 Alternatives considered

- **Merge the five example lists into one prose table and write no code.**
  Cheapest, and closest to today. Rejected: the agent would still read facts
  off the payload and match prose, which is how the five sites in § 1.1 came to
  differ; goal 3 — same state, same recommendation — cannot be tested against
  prose; and the goals lane's KR-progress prompt shows a prose rule can go
  unfired for as long as its fact is missing, with nothing to say so.
- **Proactive prompts through host hooks** — for example a Claude Code `Stop`
  hook that appends the next step. Rejected: `reference/host-capabilities.md`
  records no equivalent for OpenCode or Codex, and Perry is one skill across
  three hosts. A turn-end hook also fires after every turn rather than after a
  state-changing command, which is UD 3's rejected *every command* by another
  route.
- **Keep `DESIGN-011` and add a separate recommendation design.** Rejected in
  UD 2: the interview's output is the draft, and a waiting draft is what the
  recommendation resumes. Two locked documents would each own half of that seam.
- **One wizard that walks the whole sequence in a session** (OKR, then phase,
  then week). Rejected: it front-loads up to fifteen questions on a user who
  asked for one plan — the ceremony § 1.3's abandoned tools are criticised for.
  The recommendation offers the next step; it does not take it.

## 6. Implementation plan

Phases A and B ship value on their own. Phase C's transcript is the gate for D
and E, as `DESIGN-011` step 2 was: if a bank-produced plan still trips three
rubric checks, the questions are wrong and the rest is decoration.

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | `next` section: facts, rule file, payload; passive block at `/perry` and lane standups; the five example lists become pointers. Verified on fixture projects at each stage (empty, OKR only, phase without week plan, closable phase, queue track); deleting a rule turns its fixture red | TASK-NNN (new) | Coding Agent |
| B | Proactive closing step for the subcommands UD 3 selects, plus the silence setting. A guard enumerates those subcommands and fails when one lacks the closing-step pointer | TASK-NNN (new) | Coding Agent |
| C | Question bank and interview → draft for the first-OKR route only; one real transcript scored by the unchanged rubric | re-point `TASK-190`, `TASK-191` | Coding Agent + User |
| D | Draft file, edit/approve, resume through the interrupted scan, finalize through writers. Depends on `TASK-264` | TASK-NNN (new), `TASK-264` | Coding Agent |
| E | Phase, week and commitments routes; routing by spine; escape hatch and premise challenge on the draft | re-point `TASK-192`, `TASK-193`, `TASK-194` | Coding Agent |
| F | `/perry plan` entrance (UD 6) | TASK-NNN (new) | Coding Agent |

`TASK-177` and `TASK-190`…`TASK-194` implement the superseded `DESIGN-011`.
At lock they are re-pointed to this design by the `work` lane, not dropped —
their scope survives here and ids are never reissued.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| A recommendation is wrong because a fact is stale or unknown — e.g. `R-phase-closable` on a phase with no KR values | `unknown[]` non-empty; fixture tests per rule | a rule never fires on an unknown fact; the block prints what it could not tell |
| Blocks become nagging and get ignored | the user silences them, or picks `Not now` repeatedly | one primary at most; `Nothing is due` is a normal answer; UD 8 |
| Every command gets more expensive | length of the closing step's output in transcripts | `--compact`, three lines at most, one section call |
| The flow is longer than the form it replaces (`DESIGN-011` risk 1) | Phase C transcript: questions asked, minutes, rubric issues | per-route question caps; a question with no `Produces:` is cut |
| The rule table drifts from the command set | a test resolves every rule's `command` to a subcommand row, and every UD 3 subcommand to the closing step | rules name commands, never paraphrase them |
| Python starts judging a draft's meaning | review of the `next` and draft readers | facts are frontmatter enums and dates only; the body is never parsed (`ADR-007`) |
| The new claimed path needs a schema edit | Phase D cannot start without it | consent is part of UD 5 |
| A dispatched agent session is handed a "run it now?" prompt with no human to answer | dispatch transcripts | the closing step is skipped inside dispatched sessions |
| The bank and the rubric disagree about what a good KR is (`DESIGN-011` risk 5) | a test that every rubric check in § 1 has a question whose `Produces:` covers it | the bank cites the rubric row it serves |

## 8. Open questions

- **Do `decide new` and `work add-task` use the same engine?** Both run the
  rubric on their own inputs; sharing the bank would make it a `reference/` file
  and its size a cost three lanes pay (`DESIGN-011 § 8`, carried).
- **Do lane standups keep a lane-only view**, or does every surface show the
  global primary?
- **`R-handoff-stale` cannot see a session ending.** Firing after a
  state-changing command on a day with no handoff is a proxy; whether it is a
  good one is measured in Phase B.
- **Week boundaries.** ISO weeks today; a track with a declared `Cycle` may want
  its own.

## 9. Changes (append-only after lock)

## 10. References

- `perry/design/DESIGN-011-the-okr-is-elicited-not-collected.md` — superseded
  by this doc. § 5.1–5.5 (question format, routing, push, escape hatch, premise
  challenge) are inherited as written; what changed at the framing level is
  that elicitation is now one stage of a draft-and-approve flow, and that the
  flow is reached through a state-derived recommendation which `DESIGN-011`'s
  non-goals excluded.
- `DESIGN-001` (resumable pipelines), `DESIGN-008` (track axes), `DESIGN-012`
  (close-phase order), `DESIGN-013 § 5.1`, `ADR-007`, `ADR-012`, `ADR-019`.
- `TASK-157`, `TASK-212`, `TASK-264`, `TASK-266`, `TASK-282`.
- `reference/user-load.md`, `reference/host-capabilities.md § Prompt rendering`,
  `reference/input-quality.md § 1`, `reference/first-run.md`,
  `reference/snapshot.md`.
- Spec Kit `/clarify`: https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/clarify.md
- superpowers brainstorming: https://raw.githubusercontent.com/obra/superpowers/main/skills/brainstorming/SKILL.md ·
  issues https://github.com/obra/superpowers/issues/1152 and /1120
- gstack `/office-hours`, draft and approval: `~/.claude/skills/gstack/office-hours/sections/design-and-handoff.md` (local install)
- Scott Logic, Spec Kit measured: https://blog.scottlogic.com/2025/11/26/putting-spec-kit-through-its-paces-radical-idea-or-reinvented-waterfall.html
- GATE, elicitation vs user-written prompts: https://arxiv.org/abs/2310.11589
- Wodtke, *Radical Focus* weekly cadence: https://cwodtke.com/monday-commitments-and-friday-wins/
