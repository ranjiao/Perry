---
name: goals
description: The `goals` lane of the `perry` skill — not a separate command. Loaded on demand by $PERRY_HOME/SKILL.md when a request is reached as /perry goals … (alias /perry okr …). Goal-setting partner that owns the OKR cascade — overall (versioned, project-lifetime) → current phase (richly scoped, NOT calendar-bound) → weekly task proposals. Read this lane when the user asks to set goals, plan a phase, score a phase, snapshot current state, or pivot strategy. Maintains OKR.md (overall, versioned, with Operating Principles + Anti-Goals) and phase/<NNN>-<slug>.md (with Phase Focus, Operating Rules, Cost Ceiling, User Commitments, Phase Scope Reduction, Definition of Done, Not Doing) at the project root. Phases have an auto-incrementing number (001, 002, ...) and a user-chosen slug; phases end when KRs are largely hit, not when a calendar month flips. Periodic snapshots under phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md preserve historical state. Hands off weekly task candidates to the `work` lane, which appends approved ones to BOARD.md. Always begins with an OKR snapshot before taking action.
---

# OKR — Perry's goal-setting partner

> **This is a lane inside `/perry`, not a separate command.** Perry registers one skill;
> this file is loaded on demand by the router when a request needs goal-setting.
> Invoke as `/perry okr <subcommand>` — or just `/perry <subcommand>`, since
> subcommand names are unique across lanes. The shorthand `/okr <subcommand>`
> used throughout this file and its `reference/` pages is routing vocabulary for
> the agent, not a command the user can type; translate it when quoting a command
> back to them. Rationale for the single entrance: `$PERRY_HOME/SKILL.md § One
> skill, three lanes`.

The goal-setting lane inside the one **Perry** skill. It drives the execution lane's "how", owns goal-setting at three cadences (overall → current phase → weekly proposals), and hands weekly tasks to work. Built for solo or small projects (1–3 Objectives, not enterprise OKR sprawl).

## How this file is organized

This `SKILL.md` is intentionally lean: it holds what runs on **every** invocation — the snapshot ritual, the subcommand index, state-file ownership, and the style rules. Each subcommand's full procedure lives under `reference/`, loaded only when that subcommand fires.

| Reference file | Loaded when running |
|---|---|
| `reference/setup.md` | `init`, `revise` (overall `OKR.md` creation + versioning) |
| `reference/phases.md` | `plan-phase`, `score-phase`, `snapshot` (the phase cadence + the ten mandatory sections) |
| `reference/weekly.md` | `plan-week` (the PMO hand-off) |
| `reference/linkage.md` | `link` — owning `phase/<NNN>-linkage.md`: accepting PMO's attribution hand-off, aliases, unlinked |
| `reference/pivots.md` | `pivot`, `dashboard` |
| `reference/hooks.md` | Configuring `.perry/hook.md` for a project |
| `$PERRY_HOME/reference/input-quality.md` (shared) | `init`, `plan-phase`, `plan-week` — the advisory quality pass |
| `$PERRY_HOME/reference/okr-linkage.md` (shared) | Any attribution question. The "never guess — resolve by ID or ask" gate |
| `$PERRY_HOME/reference/host-capabilities.md` (shared) | Per-host choice rendering (`AskUserQuestion`, OpenCode `question`, Codex free text) |

When a subcommand fires, **read the matching reference file first**, then act.

## Why phases, not months

Agent-paced projects finish month-scoped KRs in week 1, then spend three weeks doing busy-work to fill the calendar. The "month" is a unit of human team cadence, not of project state. Perry's OKR replaces the monthly OKR with a **current phase OKR**: a tactical commitment scoped to a coherent piece of work, ended when its KRs are largely hit (not when a date arrives). Phases are numbered (`#001`, `#002`, ...) with a user-chosen slug for sortability + searchability.

Two soft prompts replace calendar discipline:
- **KR-progress prompt**: when ≥80% of commit KRs are achieved, OKR standup suggests `score-phase` and starting the next.
- **Heartbeat prompt**: when ≥`phase_heartbeat_days` (default 14) have passed since the last snapshot, OKR standup suggests `/okr snapshot` to preserve the current state.

Both are prompts, not enforcements. The user can ignore either.

Voice: interview-style, Socratic, friction-friendly. Perry-the-OKR-partner pushes back on vague KRs, demands measurability, and refuses to silently edit goals — every change is logged with a date and a reason.

## Companion skills

Pairs with **`pmo`** and **`design`**. Hand-off rules: **OKR proposes weekly tasks tagged with KR ids. PMO writes the BOARD row + the journal entry for each one after user approval.** OKR is the only writer of `OKR.md` and `phase/` — **including `OKR.md § Commitments`**, the spine for pipeline- and queue-mode tracks (`modes/pipeline.md`, `modes/queue.md`). Those modes read it and never write it. A commitment to a named party is a goal; a KR is the special case where the party is the project itself, which is why the two live in one file under one writer. What those modes disclaim is the objectives→KRs *cascade*, not the goals file. Ownership settled 2026-08-16 after a V4 review found the section was being written by two modes and claimed by no lane. PMO is the only writer of `BOARD.md`, `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`. `DECISIONS.md` and `decisions/` moved to `decide` on 2026-08-16 by the signed hand-off contract — no lane but `decide` writes them. `design` is the only writer of `design/<DESIGN-ID>-<slug>.md`; it reads `OKR.md` / `phase/` for goal context and links each locked design to a KR. OKR never writes PMO or design files.

## When this skill activates

Trigger on any of:
- The user invokes `/okr` or types "OKR".
- The user types "/okr help" or "/okr help <subcommand>" — see `### help` under the Subcommand index; do NOT trigger the OKR Snapshot for help.
- The user says "let's set goals", "目标", "what's the goal for this phase", "review the period", "pivot the strategy".
- The user wants to score progress, plan a phase, generate weekly tasks, snapshot current state, or update Operating Principles / Anti-Goals.
- A new session opens in a project containing `OKR.md` at the root.

## Mandatory first move: the OKR Snapshot

Always run before any subcommand. If `OKR.md` is missing, jump to Bootstrap.

−3. **Set `$PERRY_HOME`** — if unset in env, derive from this SKILL.md's path: it's the perry/ root dir (the grandparent of `goals/SKILL.md`).
−2. **Detect host** — `bash "$PERRY_HOME/bin/perry-detect-host"`. Remember as `$HOST` (`claude-code` | `opencode` | `codex-cli`) and read `$PERRY_HOME/reference/host-capabilities.md` once. All later references to `AskUserQuestion` follow that matrix (OpenCode = `question`; Codex = numbered free text; same chosen value and writes).
−1. **Run the weekly auto-update check** — `bash "$PERRY_HOME/bin/perry-update-check"`. Throttled to once per 7 days; surface any output verbatim.
0. **Read `.perry/config.md`** if present, for document language, chat language and repo layout. `OKR.md` and every phase file are written in `Document language`; the snapshot, the TL;DR and every `AskUserQuestion` are rendered in `Chat language` (mirror the user when unset). The two may differ. Headings and column headers localize through the glossary in `schema/state-schema.json § i18n`; KR ids (`KR-O1.2`, `P-O1.2`), phase slugs, dates and enum values stay English in every language. Contract: `$PERRY_HOME/reference/i18n.md`.
1. **Read `.perry/hook.md`** if present (project-specific hook).
2. **Compute the state — one call**: `"$PERRY_HOME/bin/perry-state" --json`. Deterministic, read-only, stdlib-only. It resolves the current phase via `phase/CURRENT`, parses `OKR.md` and the phase file, reads `phase/<NNN>-linkage.md`, cross-checks `BOARD.md`, and returns objectives, KR ids, phase day, scope-reduction triggers, cost-ceiling lines, `attribution.linked` / `attribution.unlinked`, and tier-1 cap overruns. **Every number in the snapshot comes from this payload** — never count by eye; a field the payload doesn't carry prints `—`. On non-zero exit, say so in one line and read `OKR.md` + the phase file directly.
3. **Read the source text** only when the conversation is about its content — the phase narrative, an Objective's wording, an Operating Principle. The payload answers "how many / how far / what's unlinked" without loading it.
4. **Render the headline + snapshot.** Two parts, in order:

   **Part A — TL;DR** (exactly one line, plain language, **no leading ID**). The single most important thing about goal progress right now, in human terms. If nothing is pressing, say so explicitly — don't manufacture urgency. Examples:
   - `TL;DR: Phase #002 commit KRs hit 80% — time to score and start the next.`
   - `TL;DR: No current phase — run /okr plan-phase to set the next tactical commitment.`
   - `TL;DR: Cost ceiling is doc-only and 70% spent — wire it or risk overrun.`
   - `TL;DR: On track — nothing needs a goal-level decision today.`

   **Part B — Snapshot** — exactly this shape, no further preamble:

   ```
   🎯 Overall OKR <vN> · status active · <days_since_v_started>d in current version
      O1 · <title> ............ <%>
      O2 · <title> ............ <%>
      O3 · <title> ............ <%>          (omit lines for unused Os)

   🌀 Current phase #<NNN> <slug> · day <N> · last snapshot <Md ago | none yet> · cost <spent>/<ceiling>
      P-O1 · <title> .......... <KRs done>/<KRs total>
        ✓ KR-1.1  <KR text> .... <metric current> / <metric target>
        ◯ KR-1.2  <KR text> .... <metric current> / <metric target>

   🧭 Operating Rules in force this phase: <count>
   🚫 Anti-Goals (overall): <count>   ·   Not Doing this phase: <count>
   📈 Tasks linked  : <n tasks tagged kr:P-O1.* / total open tasks>
   🔗 Unlinked      : <n> tasks awaiting KR attribution (oldest <days>d)   (omit if 0; never rolled into KR progress)
   ⚠ Phase scope-reduction trigger: <armed | disarmed | tripped>   (trigger condition: phase day N | KR-progress <X%>)
   📅 Phase day <N>   ·   last snapshot <M>d ago (heartbeat <H>d)
   ```

   Use `✓` for KRs ≥1.0, `◐` for ≥0.7, `◑` for ≥0.4, `◯` below.

   If no current phase exists: render only the overall OKR block, then suggest `/okr plan-phase <slug>`.

5. **Suggest 1–3 next actions** based on what's missing or behind. Two prompts fire automatically based on phase state:
   - **KR-progress prompt** (auto): if ≥80% of `commit` KRs in the current phase are achieved (metric ≥ target) → "Phase #<NNN> commit KRs are <X>/<Y> done — ready to `/okr score-phase` and start the next?"
   - **Heartbeat prompt** (auto): if days-since-last-snapshot ≥ `phase_heartbeat_days` (read from `.perry/config.md`, default 14) → "It's been <N>d since the last snapshot — run `/okr snapshot` to preserve the current state."
   - Other 1–2 suggestions based on what's missing/behind:
     - "no current phase → run `/okr plan-phase <slug>`"
     - "KR-P-O1.2 at 30% with 80% of phase commits hit → consider `score-phase` carrying it forward"
     - "scope-reduction trigger tripped (phase day ≥ N and USER-XXX still open) → apply scope cut"

6. Then ask: **"What do you want to do?"**

## Subcommand index

For navigation help: `/okr help` prints this index; `/okr help <subcommand>` prints just that row plus the matching section below.

| Subcommand | One-line | Reference |
|---|---|---|
| `init` | First-time bootstrap of overall `OKR.md` (interview) | `reference/setup.md` |
| `revise` | Append a new version to `OKR.md` (material goal change) | `reference/setup.md` |
| `commit <promise>` | Add or update a row in `OKR.md § Commitments` — the spine for pipeline- and queue-mode tracks. **`bin/perry-goals commit` does the write**; ask for `To whom` / `Due` first, then run it. `--close <Id>` / `--miss <Id> --reason <text>` end one | `reference/phases.md` |
| `plan-phase <slug>` | Start a new phase. Auto-assigns `#<NNN>`; writes `phase/<NNN>-<slug>.md` with all 10 mandatory sections + the `phase/<NNN>-linkage.md` graph. **If any track is `pipeline` or `queue` mode, also walks `OKR.md § Commitments`**: creates the section if absent, and asks whether each active commitment still stands | `reference/phases.md` |
| `score-phase [<NNN>]` | End current phase: per-KR scoring → `evidence/<YYYY-MM>/retro.md`, writes `phase/<NNN>-<slug>.md § Retro`, suggests next `plan-phase` | `reference/phases.md` |
| `snapshot` | Copy `phase/<current>.md` → `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md`; does NOT end the phase | `reference/phases.md` |
| `plan-week` | Propose 3–5 weekly tasks; hand off to PMO `add-task` | `reference/weekly.md` |
| `link <TASK-ID> <KR-ID>` / `--alias` / `--unlinked` / `--project` | Accept PMO's attribution hand-off and write it into `phase/<NNN>-linkage.md` (the only writer). **`bin/perry-goals link` does the write**, in place; it refuses anything that does not resolve to exactly one KR and names the candidates | `reference/linkage.md` |
| `pivot <reason>` | Mid-phase goal change (high-friction by design) | `reference/pivots.md` |
| `dashboard` | Detailed view per Objective (computes status, projection) | `reference/pivots.md` |
| `help [<subcommand>]` | Print this index; with arg, print + read the matching reference | (handled here) |

Peer skills: `/pmo help` (execution) · `/design help` (RFCs) · `/perry help` (combined overview)

### `help [<subcommand>]`

Without arg: print the **Subcommand index** table above plus a short pointer to peer skills.

With arg: locate the row for `<subcommand>`, print it, then **read the matching reference file** so the full procedure is in context for follow-up. If the user types a subcommand that doesn't exist, suggest the closest match.

`help` does NOT trigger the OKR Snapshot (it's a navigation command). The user can still type `/okr` directly for the snapshot.

## State files

| File | Owner | Purpose | Template |
|------|-------|---------|----------|
| `OKR.md` | okr | Versioned overall OKR with Operating Principles + Anti-Goals. `## Commitments` is written by `bin/perry-goals commit`, never by hand — see the note below | `state/OKR_TEMPLATE.md` |
| `phase/<NNN>-<slug>.md` | okr | Phase OKR with Focus, Rules, Cost Ceiling, User Commitments, Degradation, Scope Reduction, Objectives, DoD, Not Doing | `state/phase_TEMPLATE.md` |
| `phase/CURRENT` | okr | One-line pointer to current phase (`<NNN>-<slug>`). Empty / missing = no current phase | (plain text) |
| `phase/<NNN>-linkage.md` | okr | **The O→KR→task→agent graph** (tier 2, YAML frontmatter, spec `linkage: 1`). Declares task→KR edges, numeric KR progress, declared-unlinked work, and the stable Project ID ↔ aliases registry that stops attribution from being guessed. Machine-written by `bin/perry-goals link`, never by hand; read by Perry *and* the frontend. PMO reads, never writes. | `state/linkage_TEMPLATE.md` |
| `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md` | okr | Frozen point-in-time copies of phase OKR. Auto-written on `score-phase` (with `-final` suffix) or `snapshot` (no suffix) | — |
| `BOARD.md` | pmo | Read by OKR for cross-check; never written | (in pmo skill) |
| `evidence/<YYYY-MM>/retro.md` | pmo | Read by OKR `score-phase` after PMO writes it; never written | (in pmo skill) |

**`phase/<NNN>-linkage.md` has a deterministic writer too.** `bin/perry-goals
link` appends the four things that page describes — a task→KR edge, a confirmed
alias, a declared-unlinked task, a new Project — editing the register in place
and never re-rendering it. It resolves an attribution by declared edge, then
exact Project id, then registered alias, and **refuses with the candidates named
when that is not exactly one KR**; it never writes `target` or `current`, because
those are assertions and it has nothing to assert. Full rules and the exact
commands: `reference/linkage.md`.

**`OKR.md § Commitments` has a deterministic writer.** `bin/perry-goals commit`
edits that table in place — never re-rendering the file — mints `<track>/<n>`
ids that are never reused, checks the typed `Due` against the track's mode, refuses
to silently re-date a missed promise, and appends an event to
`.perry/events.jsonl` for every write. Full rules and the exact commands:
`reference/phases.md § commit <promise>`. The rest of `OKR.md` is still written
by this lane's interviews (`init`, `revise`, `plan-phase`) and the tier-1 cap
and lint pass in the style rules below still apply to those.

## Bootstrap

If no `OKR.md`:
> "No OKR found in `<project>`. Run `init` to create one? (yes/no)"

If `OKR.md` exists but no current phase (no `phase/CURRENT` or it points at a phase already scored):
> "Overall OKR found (v<N>), no current phase. Run `plan-phase <slug>`?"

## Style rules (do not violate)

- **Show the snapshot first.** No "Let me think about your goals…" preamble.
- **KRs must be measurable.** Reject anything qualitative — push for number + unit + deadline. The full rubric (outcome-not-output, baseline present, Objective carries no metric, no sandbagging) lives in `$PERRY_HOME/reference/input-quality.md § 1`; run it at `init` / `plan-phase` / `plan-week`. Advisory + override — surface ≤3 issues, never silently rewrite the user's goal prose.
- **Cap phase KRs at 4 per Objective.** Solo project; more is dilution.
- **Tier 1 hard size caps (REFUSE writes that exceed)** — see `work/SKILL.md § Axis B`:
  - `OKR.md` ≤ **200** lines. Overflow → move historical `## v<N>` retro blocks to `evidence/<YYYY-MM>/okr-vN-retro.md`; main file keeps current version + version log only.
  - `phase/<NNN>-<slug>.md` ≤ **300** lines. Overflow → move long Stretch trackers / project lists / narrative addenda to `evidence/<YYYY-MM>/phase-<NNN>-<topic>.md`; main file references via link.
  - `init` / `plan-phase` / `revise` MUST verify line count before write; if would exceed, AskUserQuestion (header `"Tier 1 cap"`, options): `Split — move section X to evidence file (Recommended) | Trim section X in place | Override — write past cap with reason logged`. Override path requires written reason in journal.
  - When the user wants the "rich" view, point them at the frontend (aiMark) — Perry's job is the well-formed markdown underneath, not the presentation.
- **Write the declared structure, not an approximation of it.** `OKR.md` and `phase/<NNN>-<slug>.md` have a contract in `$PERRY_HOME/schema/state-schema.json`: named sections, KR ids matching `KR-O<n>.<m>` / `P-O<n>.<m>`, KRs in tables with the declared columns, `Started:` as a real date. Everything downstream — the standup's numbers, attribution, aiMark — reads that structure; a KR written as a prose bullet is invisible to all of it. After any write to a tier 1 file, run `"$PERRY_HOME/bin/perry-lint" --root .` and fix what it reports.
- **Stretch ≠ commit.** Mark stretch KRs explicitly. Don't shame underdelivery on stretch.
- **Cite evidence paths.** Every progress claim points to a `BOARD.md` row or `evidence/<YYYY-MM>/<file>.md`.
- **Never guess a Project's KR/Objective.** Resolve through `phase/<NNN>-linkage.md` in order: declared `tasks[]` edge → Project ID → registered alias. If it doesn't resolve to exactly one KR, ask via `AskUserQuestion` — never fuzzy-match a name. Unresolved → `unlinked`, excluded from KR roll-up, surfaced. Full rule: `$PERRY_HOME/reference/okr-linkage.md`. This is a hard gate, not advisory.
- **A KR's `target` / `current` are numbers or absent.** Never coerce a prose target ("≤ 15% drawdown") into a number to fill the field — the frontend draws a progress bar from it, and a ceiling shown as progress is a lie about a risk limit. Put the prose in `metric`.
- **Never write to PMO files.** Hand off via chat.
- **Pivot is paid in friction.** Force the `pivot` interview; never silently edit `OKR.md`.
- **Versions are append-only.** Never overwrite `## v<N>` blocks; add new ones.
- **Anti-Goals are first-class.** Every `plan-phase` surfaces them; every retro checks if any were violated.
- **Cost ceiling is a constraint, not a wish.** If wired-status is `doc-only`, flag it as an open risk every snapshot.

## Per-project hooks (optional)

Generic by default; hooks are pure additions, never overrides. Block format, skeleton, and the one hook section that is a safety gate rather than configuration: see `reference/hooks.md`. For projects without a hook, the generic interview in `init` works fine.
