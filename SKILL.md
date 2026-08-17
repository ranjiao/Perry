---
name: perry
description: Perry — a virtual project office for solo or small projects, with one entrance. Use for a where-are-we project snapshot or standup; setting, revising or scoring goals (OKR, objectives, key results, phases); planning a week; running a task board and triaging blockers; logging decisions and ADRs; drafting or locking a design doc / RFC; weekly status, session handoff, and delegating work to agents; converting an existing project into tracked state (/perry adopt); and auditing how a project is structured for agent work (/perry diagnose). Three lanes live inside it — goals (objectives, phases, commitments), work (board, journal, evidence), decide (RFCs and decisions) — reached as "/perry goals plan-phase", "/perry work triage", "/perry decide lock". The former names okr / pmo / design keep working as permanent aliases. They are NOT separate skills. State lives at the project root in OKR.md, phase/, BOARD.md, journal/, DECISIONS.md and design/.
---

# Perry — virtual project office

> *Perry runs the office. You run the project.*

Perry is a single skill with three internal lanes that share a project's state files at the project root. This file is the entry point and the router: a combined snapshot, a brief intro for new users, and dispatch to whichever lane the request belongs to.

## One skill, three lanes

**Perry registers exactly one skill: `perry`.** The three lanes below live under `$PERRY_HOME/<lane>/SKILL.md` and are **loaded on demand by this router** — they are not separately invocable commands. When a request belongs to a lane, read that lane's SKILL.md in full and follow it.

Earlier versions symlinked them as sibling skills so `/okr`, `/pmo` and `/design` worked directly. That was withdrawn: the host's skill namespace is shared, and `design` collides with `design-review`, `design-consultation`, `design-html`, `design-shotgun` and an entire `design:` plugin family, while `okr` collides with `lark-okr`. Claiming a common English word in a namespace Perry doesn't own is the same error as claiming a project's `design/` directory — see `## State root`. In practice users reached Perry through `/perry` and let it route anyway, so the siblings cost a namespace and bought nothing. `setup` removes the stale links on upgrade.

### Command surface

```
/perry                          combined snapshot (the default)
/perry <lane> <subcommand>      /perry goals plan-phase · /perry work triage · /perry decide lock
                                aliases: okr → goals · pmo → work · design → decide
/perry <subcommand>             allowed when the subcommand name is unambiguous
/perry adopt | diagnose        handled here, not in a lane
/perry relocate <path> | help   handled here, not in a lane
```

**Most** subcommand names are unique across the three lanes, so `/perry plan-phase` resolves without one. **Five are not**, and a bare invocation of these must ask rather than guess:

| Ambiguous | Lanes |
|---|---|
| `plan-week` | goals (proposes) · work (writes) |
| `handoff` | work (session handoff) · decide (design → implementation) |
| `status` | work (weekly report) · decide (design doc status) |
| `revise` | goals (OKR version) · decide (design doc) |
| `init` | goals (OKR) · decide (design lane bootstrap) |

Name the lane when a request is ambiguous or the user is new.

> **Reading the lane docs**: `goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md` and everything under `*/reference/` are written in shorthand — they say `/pmo triage` where the user would now type `/perry work triage`. Inside a Perry session that shorthand is unambiguous routing vocabulary for the agent, not a command the user can type, so it is left as-is — including where it still uses the pre-rename lane names. Only translate it when quoting a command back to the user.

> **Host portability**: Perry runs on **Claude Code** (default install at `~/.claude/skills/perry/`) and **Codex CLI** (default install at `~/.agents/skills/perry/`). Both hosts read SKILL.md frontmatter natively for skill discovery — no AGENTS.md or other routing file is needed. The standup ritual below sets `$PERRY_HOME` from the install location, detects which host is live, and reads `$PERRY_HOME/reference/host-capabilities.md` for the fallback rules (free-text prompts instead of `AskUserQuestion` on Codex, refusal of `Executor: claude-subagent` on Codex, etc.). Where this file or a child SKILL.md names a Claude-Code-specific tool (`AskUserQuestion`, `Agent()`, `Bash run_in_background`), that capability page owns the per-host translation; SKILL.md prose stays single-sourced.

| Lane | Reached as | Loaded from | Owns | What it does |
|------|-----------|-------------|------|--------------|
| **`goals`** | `/perry goals …` (alias `okr`) | `$PERRY_HOME/goals/SKILL.md` | `OKR.md`, `phase/<NNN>-<slug>.md` | Goal-setting: overall versioned OKR, current phase OKR with 10 mandatory sections (NOT calendar-bound; phases end when KRs hit), weekly task proposals (handed off to PMO) |
| **`work`** | `/perry work …` (alias `pmo`) | `$PERRY_HOME/work/SKILL.md` | `BOARD.md` (live), `journal/<YYYY-MM>/<DD>.md` (daily), `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/` | Execution stewardship: standup ritual, task triage, agent delegation, status reports, cadence rituals, phase rollover |
| **`decide`** | `/perry decide …` (alias `design`) | `$PERRY_HOME/decide/SKILL.md` | `design/<DESIGN-ID>-<slug>.md`, `DECISIONS.md`, `decisions/` | Design-doc and decision stewardship: RFC drafting, user-decision tables, lock workflow, hand-off of implementation tasks to PMO |

## The hand-off contract (the most important rule)

> **Signed off: Ran Jiao, 2026-08-16.** Checked: the drafted contract section,
> `perry/design/DESIGN-003-work-modes.md § 5.9` (blast radius), and
> `perry/evidence/2026-08/TASK-026-spec.md`; approved as written, without
> per-line reconciliation against `schema/state-schema.json § files[].owner`
> — `tests/test_ownership.py` covers that agreement mechanically.
>
> Recorded at this precision on purpose. V5's whole value is saying **what was
> actually checked**; writing "reviewed" or inflating it into a line-by-line
> audit would make the rung a label instead of a record. `perry-lint` cannot
> check this section at all — a wrong contract shows up later as silent
> cross-lane writes, not as a lint error, which is why it is the one thing in
> Perry that requires a human gate.

**The invariant, unchanged since Perry had three registered skills:**

> **Each lane reads the others' files freely. No lane writes outside its own.**

Everything below is that sentence applied to a file list. It is a
**file-ownership** contract, not a skill-registration one — it held when the
lanes were separate skills and it holds now that they are loaded on demand,
which is why collapsing to one entrance changed nothing about how state is
written.

| Lane | Only writer of | Proposes, never writes |
|---|---|---|
| **`goals`** (`goals/`) | `OKR.md` — **including `## Commitments`** — and `phase/<NNN>-<slug>.md` | weekly tasks, handed to `work` |
| **`work`** (`work/`) | `BOARD.md` (incl. `## Intake`, `## Cadence`), `journal/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/` | KR attribution edges, handed to `goals` |
| **`decide`** (`decide/`) | `design/<DESIGN-ID>-<slug>.md`, **`DECISIONS.md` and `decisions/`** | implementation tasks on lock, handed to `work` |

**Two changes from the previous contract, and why.**

1. **`DECISIONS.md` + `decisions/` move from `work` to `decide`.** A settled
   decision and the document that settles it now have one owner. `work` was
   the largest lane and the record of *what was decided* sat one lane away from
   the RFCs that decided it, which is where "where do I record this?" became
   ambiguous.
2. **`OKR.md § Commitments` is explicitly `goals`.** Pipeline- and queue-mode
   tracks put their spine there (`modes/pipeline.md`, `modes/queue.md`) and
   both disclaim the objectives→KRs cascade — which read as though they owned
   the section. They do not. A commitment to a named party *is* a goal; a KR is
   the special case where the party is the project itself, so the two live in
   one file under one writer. Settled 2026-08-16 after an independent review
   found the section written by two modes and claimed by no lane.

**The lane names and the directories now agree.** They did not when this
section was signed: the contract stated target names beside their then-current
directories (`goals` (today `okr/`), …) precisely so it would never name a
directory that did not exist — the defect `reference/user-load.md` forbids.
TASK-027 landed the rename, and the parentheticals were collapsed as that
section itself instructed.

**Why this edit did not need a second signature.** What was signed is the
ownership set — which lane may write which files — and that is byte-identical
before and after. The edit removed a scaffold the contract carried for one
release and put in writing that the scaffold's job is done. An edit that
*changed* an ownership row would need a fresh V5, and this one is recorded here
rather than silently applied so the distinction stays visible.

**What "only writer" forbids, concretely.** A lane that needs a change in
another lane's file **asks in chat and stops** — it does not write and
apologise, and it does not write "just this once" because the other lane is not
loaded. Three cases that have to refuse: `goals` writing `BOARD.md`; `work`
writing `DECISIONS.md` (the newly moved file, i.e. the case this change
creates); `decide` writing `journal/`.

This single rule is what keeps the set composable and lets you drop in a fifth
lane later (e.g. `research-journal`, `risk-review`) without breakage — a new
lane is a directory with a `SKILL.md`, a row in the table above, and an entry in
the routing reference.

## When this skill activates

Trigger on any of:
- The user invokes `/perry` or types "Perry".
- The user types "/perry help" or "/perry help <lane>" — see `## /perry help` below; do NOT trigger the combined snapshot for help.
- The user opens a session and wants a "where are we" overview without specifying OKR vs PMO.
- The user is new to Perry and asks how it works or what to do first.
- A new session opens in a project that contains both `OKR.md` and `BOARD.md` and the user wants the combined view.

If the user clearly wants only goal-setting → the `goals` lane. If clearly only execution → `work`. The snapshot is for the cases in between.

## Mandatory first move: combined snapshot

When `/perry` is invoked, always run this before doing anything else.

−2. **Set `$PERRY_HOME`** — if the env var is not already set, derive it from the path of the SKILL.md you just read. `$PERRY_HOME` is the directory containing this top-level SKILL.md (it also contains `bin/`, `reference/`, `modes/`, `packs/`, `goals/`, `work/`, `decide/`). For a lane SKILL.md (`<PERRY_HOME>/<lane>/SKILL.md`), use the grandparent directory. All later bin/ invocations in this file and the reference files are written as `$PERRY_HOME/bin/<script>` — they only work if this step ran.

−1. **Detect host once** — silently:
   ```
   bash "$PERRY_HOME/bin/perry-detect-host"
   ```
   Output: `claude-code` | `codex-cli` | `unknown`. Remember as `$HOST` for the rest of the conversation. Then read `$PERRY_HOME/reference/host-capabilities.md` for fallback rules. If output is `unknown`, default `$HOST=claude-code` but tell the user once and recommend setting `PERRY_HOST` in their shell profile.

0. **Run the weekly auto-update check** — silently in the background:
   ```
   bash "$PERRY_HOME/bin/perry-update-check"
   ```
   The script throttles itself to once per 7 days; most invocations exit immediately with no output. When it does run, output is one line (or zero). Surface its output to the user verbatim if non-empty (the user wants to know about updates), then continue with the snapshot.

1. **Read `.perry/config.md`** if present, to pick up document language, chat language and repo layout. If absent and any state file exists, prompt the user to run first-time setup so the config is recorded. **Everything rendered from here on — the dashboard, the TL;DR, the suggested next actions, every `AskUserQuestion` label — is written in the chat language** (`Chat language`, or the user's own language when unset). Everything written to a file uses `Document language`, which may be a different one. The full contract, including what never gets translated, is `reference/i18n.md` — read it before the first localized write in a session.

2. **Check for an interrupted run — before anything else reads project state.**

   ```
   "$PERRY_HOME/bin/perry-state" --section interrupted
   ```

   Deterministic, read-only, stdlib-only. Returns one row per pipeline someone
   walked away from mid-run — terminal stages (`done`, `abandoned`) are dropped
   by the scanner, so no reader has to know which values are terminal. Each row
   carries `pipeline`, `stage`, `step`, `idle_days`, `stale`, and how much the
   user has already banked (`declarations`, `interview_answers`,
   `candidates_pending`).

   **Every number on the card below comes from this payload.** Do not open the
   dossier to eyeball its frontmatter — that is the same estimating
   `schema/README.md` forbids for every other number Perry prints, and here it
   would be estimating how much of the user's own work survived.

   This gate exists because such a run is otherwise **invisible**. `/perry adopt`
   stages 0–3 deliberately write no state file (`reference/adoption.md § The one
   rule`), so `installed: false` in step 3 is true for an abandoned adoption and
   for a folder that has never heard of Perry alike — and the next session
   re-runs First-time setup, re-asks language and repo layout, and starts a
   *second* dossier beside the first. Dossier paths are dated, so nothing
   collides and nothing warns.

   - **None found** → continue to step 3 unchanged.
   - **One found** → render the card below, then ask. Do **not** run First-time
     setup, and do not render the dashboard first; the user cannot evaluate a
     dashboard for a project whose adoption never finished.
   - **More than one** → list them with their stage and age, ask which to act on,
     then treat that one as the single case.

   The card names position, what is already banked, and what is not — the user
   is being asked to spend an hour or throw one away, and needs both numbers:

   ```
   ⏸  Interrupted run · /perry adopt · <project>
      Stopped <N>d ago at stage <n> (<stage>) · step: <step>
      Already decided : <e.g. state root `perry/`, document language English>
      Already authored: <e.g. 2 Objectives, 9 KRs>
      Not yet done    : <e.g. phase, 6 clusters, attribution, 2 transcriptions>
      Nothing has been written to the project yet.
   ```

   Fill every line from the dossier — `stage`, `step`, `updated`, the count of
   `declarations[]`, and `candidates[]` by `status`. A line the dossier cannot
   answer prints `—`; never estimate what the user already did.

   Then one `AskUserQuestion`, header `"Interrupted run"`, options:
   `Resume where you left off (Recommended) | Start over (archives this one) | Abandon it`.

   **When `stale: true`** (the run has not advanced in `stale_after_days`, a
   calibrated default of 30 declared in `schema/state-schema.json § thresholds`),
   say so in one clause and move `Abandon it` to first with the `(Recommended)`
   tag. A run untouched for a month is more likely finished-with than paused,
   and the user should not have to re-read a card they have already skipped
   several times. It stays a recommendation, never an automatic retirement —
   `abandoned` is set by the user, never by Perry deciding a run has gone
   stale.

   - **Resume** → re-enter at `stage`/`step`. Every declaration in
     `declarations[]` is already banked and is **not** re-asked.
   - **Start over** → move the file to `.perry/<pipeline>/archive/<date>-<name>.md`
     and begin a fresh run. Archive rather than delete: `candidates[]` with
     `status: rejected` are the don't-ask-me-again record, and `--recheck` reads
     the archive.
   - **Abandon** → set `stage: abandoned` in place. Terminal; this gate skips it
     from now on, and the rejection record survives.

   **Never resume without asking.** A run continued on Perry's initiative
   re-commits the user to decisions they may no longer stand behind.
   `--resume` is the shorthand for a user who already knows: it skips the card
   and continues. `--recheck` is unaffected — it operates on finished runs.

   **A flag mismatch is refused, not merged.** If the invocation carries a
   `--depth` or `--only` that disagrees with the dossier's `depth:` / `lanes:`,
   say so and ask which wins rather than resuming into a mixed scope.

3. **Compute the state — one call**:
   ```
   "$PERRY_HOME/bin/perry-state" --json
   ```
   Deterministic, read-only, stdlib-only. `installed: false` → jump to **First-time setup** below — **but only if step 2 found no interrupted run.** An abandoned adoption reports `installed: false` too, because stages 0–3 write no state file; treating that as a fresh project is the failure step 2 exists to prevent. Otherwise the payload carries everything the combined dashboard needs across all three children — OKR version + objectives, phase number / day / KR totals, board counts, User Input Queue, top risk, last ADR, locked designs and their hand-off status, plus a `warnings` array. **Every number below comes from this payload**; a field it doesn't carry prints `—`. Flag any child whose files are missing (no `OKR.md`, no `BOARD.md`, empty `design/`).

3b. **Load the mode file for each declared track** — `project.config.tracks[]`
   in the payload above. For each distinct `mode` in that list, read
   `$PERRY_HOME/modes/<mode>.md` in full, once. **A mode that is not one of the
   four** (a typo in the register — `perry-state` passes the cell through
   verbatim) has no file: say so in one line, fall back to `project` for that
   track, and point at `perry-lint`, which reports it as a `bad-enum`. Do not
   silently skip the track — a track with no mode loaded is a track with no
   rules. That file declares what the
   track's spine is, what closes its horizon, whether its calendar is binding,
   what its item states are, what `triage` asks of it, and its default
   verification rung.

   **The payload is never empty.** A project that has declared no tracks
   reports exactly one — `main`, mode `project`, `declared: false` — so there
   is no "no tracks" branch to write and nothing to special-case. That single
   implicit track loads `modes/project.md`, which adds nothing to Perry's
   behavior on purpose: `project` is the shape Perry was built for and its
   rules already live in `goals/SKILL.md` and `work/SKILL.md`. A project written
   before tracks existed therefore behaves identically, which is the property
   `tests/test_work_modes.py` protects.

   Cost discipline: **one mode file per distinct mode, not per track.** Five
   pipeline tracks read `modes/pipeline.md` once. Modes are tier 1 and loaded
   on demand, exactly like `*/reference/*.md` — the router's own tier-0 cost is
   this paragraph and one payload field.

   The register is a `## Tracks` table in `.perry/config.md` — a tier-1 file
   the user owns and edits directly, because a track is configuration rather
   than state and `.perry/` is a path Perry already claims. Its shape is in
   `schema/state-schema.json`; `perry-lint` validates the `Mode` and
   `Default rung` cells whenever the section exists and skips it entirely when
   it doesn't.

3c. **Apply the active packs' display glossary** — `project.config.packs[]` in
   the payload. Each entry carries a `glossary` map of *term → shown as*. When
   rendering anything a human reads — the dashboard, the TL;DR, suggested
   actions, `AskUserQuestion` labels — substitute the mapped nouns.

   **It renames prose and nothing else.** File names, IDs, enum values, schema
   column keys, headings the schema matches on, and command names are invariant
   — a glossary that could move them would break every parser, and the loader
   does not read them. This is a third axis on the mechanism
   `reference/i18n.md` already defines: document language governs files, chat
   language governs replies, the pack glossary governs which *noun* is used in
   both. A project with no `Packs:` field gets `software-ops`, whose glossary is
   deliberately near-empty because Perry's default vocabulary was built from
   that domain.

4. **Render the combined dashboard** — exactly this shape, no preamble:

   ```
   🅿  Perry · <project name> · <today's date>

   🎯 OKR (vN, <period>) · <days_elapsed>/<days_total>d
      O1 · <title> ............ <%>
      O2 · <title> ............ <%>
      O3 · <title> ............ <%>          (omit unused Os)

   🌀 Current phase #<NNN> <slug> · day <N> · cost <spent>/<ceiling>
      P-O1 · <title> .......... <KRs done>/<KRs total>
      P-O2 · <title> .......... <KRs done>/<KRs total>

   📋 Open tasks  : P0=<n>(<done>/<total>) · P1=<n> · P2=<n> · blocked=<n>
   ⏳ User Input Q: <pending count> · oldest: <USER-id> "<title>" @ <days idle>d
   🚧 Top risk    : <risk title, ≤80 chars>
   📝 Last decision: <ADR-id> "<title>" (<date>)
   📅 Last weekly : <YYYY-WW>, <days>d ago · last handoff: <date>, <days>d ago
   ```

   Use `—` for empty fields. Never fabricate values.

   **Every ID printed here carries its title**, per `## Style rules` — a
   dashboard line naming `USER-014` and nothing else tells the user they are
   blocked and not what on. If the payload has an ID but no title for it, run
   `bash "$PERRY_HOME/bin/perry-explain" <ID>` rather than printing the bare ID
   or inventing a name.

5. **Suggest 1–3 next actions** combining `goals`, `work`, and `decide` concerns:
   - "phase #002 commit KRs ≥80% → run `/perry work end-phase-retro`, `/perry goals score-phase`, `/perry work rollover`, `/perry goals plan-phase <new-slug>`"
   - "USER-014 (\"Confirm staging env default\") idle 6d, weekly is 8d old → run `/perry work nudge` then `/perry work friday-review`"
   - "no current phase → run `/perry goals plan-phase <slug>`, then `/perry goals plan-week`, then `/perry work` to add the tasks"
   - "DESIGN-002 (\"Flake scoring\") in_review for 8d → run `/perry decide lock` or `/perry decide revise`"

6. Then ask: **"What do you want to do?"**

If the user picks an OKR-flavored action (plan, score, pivot, revise), read `$PERRY_HOME/goals/SKILL.md` and follow it. A work-flavored action (triage, status, delegate, handoff, rollover, risk) → `$PERRY_HOME/work/SKILL.md`. Recording a decision (`adr`) is the `decide` lane, not this one. A design-flavored action (RFC, architecture, lock, supersede) → `$PERRY_HOME/decide/SKILL.md`. If unclear, ask which, then route. **Read the lane file in full before acting on it** — it is loaded on demand precisely so it can be complete.

## First-time setup

When `/perry` is run in a project with no Perry state files at all **and step 2
found no interrupted run**. If a dossier or diagnosis exists with a non-terminal
`stage`, this section does not run — the user already answered these questions
once, and asking again is how a resumable pipeline loses the work it was
supposed to protect.

1. Briefly explain Perry (≤3 sentences).

2. **Run the namespace check before asking anything** — silently:

   ```
   python3 "$PERRY_HOME/bin/perry-lint" --claims --root . --json
   ```

   Read-only, exit 0 always. It resolves every path in
   `schema/state-schema.json § claims[]` against this folder and returns
   `collisions` plus a `suggested_state_root`.

   - **`collisions: 0`** → write `State root: perry` and **ask nothing.** The
     clean case must cost the user zero questions; that is the whole reason
     this is a check rather than a standing question.

     **`perry` is the default, not `.`.** Two shapes in circulation is two code
     paths a reader can disagree about, and one already did: `bin/perry-goals`
     passed the project root where the state root was wanted, and the bug was
     invisible on every `.`-rooted project — including the test fixture. A
     subdirectory also removes the whole namespace-collision class rather than
     detecting it, which is what the check above exists for.
   - **`collisions > 0`** → add State root as a **third question in the same
     `AskUserQuestion` call** below. No extra round trip.

   Without this step Perry claims a namespace it was not given. The escape
   hatch used to be offered only on the adopt path, so a greenfield `/perry` in
   a folder that already owned `design/` wrote straight over it with no question
   asked — and every later lint run reported the user's own file as a malformed
   Perry design doc. Never enumerate the claimed paths here; run the check.

3. **Confirm the project-wide preferences before any file is written** — record them in `.perry/config.md` (create the file if missing) so every subsequent session and every child skill reads from one source. Ask via a single `AskUserQuestion` tool call (two questions, or three when step 2 found a collision):
   - **Document language** (header `"Language"`): options = `English (Recommended if user typed English) | 中文 (Recommended if user typed 中文) | other`. The "Recommended" tag goes on whichever matches the language the user has been typing. Each option's `description` says what it changes in consequences: *"OKR, board titles, decisions and design docs get written in this language. IDs, file names and status words stay English so tools can still read them."*
   - **Repo layout** (header `"Repo layout"`): options = `Single repo (Recommended for non-code projects) | Split repo (PMO ↔ code; only if both exist and you've seen branch contention)`. See **Repo layout options** below for the trade-off explanation that goes into each option's `description`.

   - **State root** (header `"State root"`) — **only when step 2 reported a
     collision.** Options = `Put Perry's files under <suggested>/ (Recommended) |
     Use the project root anyway | Another directory`. Name the colliding path
     and its owner in the question itself — "this project already has `design/`
     with 1 file Perry did not write" — because the user cannot evaluate the
     options without knowing what is at stake. `Use the project root anyway` is
     a real answer: it means lint will report those files, and the option's
     `description` must say so.

   **Don't ask about chat language here.** Write `Chat language: follow user` and mirror whatever the user types — that is right for nearly everyone and costs them no decision. Only pin it (and only when the user asks, e.g. "reply in Chinese even when I type English") by writing a named language into that field.

   Document language governs **files**; chat language governs **replies**; they are allowed to differ, and often should. `reference/i18n.md` is the contract — the three layers of text, the glossary that localizes headings and column headers, what stays English in every language, and how to switch later.
4. **Ask whether this is a new project or an existing one** — one `AskUserQuestion` (header `"Starting point"`, options: `New project — start from goals (Recommended if the folder is nearly empty) | Existing project — analyze what's here first`). The second option routes to **`/perry adopt`**: Perry reads the project's own evidence (README, roadmap, git history, existing design/ADR docs, TODOs, issues) and proposes candidates the user confirms, instead of interviewing from a blank slate. Read `reference/adoption.md` before running it. Adoption writes no state file directly — it produces a dossier, the user confirms it, and the normal subcommands materialize the result.

   **Then offer tracks, once, and only when it would change something.** If the
   folder shows a shape other than software — a `clients/` or `deliverables/`
   tree, a mail or ticket export, a `sources/`-shaped folder — ask one
   `AskUserQuestion` (header `"Work shape"`, options drawn from
   `$PERRY_HOME/modes/`: `One kind of work (Recommended if unsure) | Several
   kinds — set up tracks | Tell me the difference`). On the second, write a
   `## Tracks` table. On a plain software project, **skip the question
   entirely** — the implicit `main` track is right and asking costs a decision
   for nothing.

   For a new project, recommend the order below.
5. Recommend the order:
   - First, run `/perry goals init` — interview to create `OKR.md` (mission, Operating Principles, 1–3 Objectives + KRs, Anti-Goals, version v1).
   - Then, run `/perry goals plan-phase <slug>` — creates the first phase OKR (`phase/001-<slug>.md`) with all 10 mandatory sections.
   - Then, run `/perry work` — bootstraps the execution files (`BOARD.md`, `journal/<current-YYYY-MM>/`, `PROJECT_STATE.md`, `evidence/`, `weekly/`, `handoff/`; `DECISIONS.md` and `decisions/` are the `decide` lane's) and runs the first standup.
   - Then, run `/perry decide init` — creates `design/` **and** `DECISIONS.md` + `decisions/` (via `perry-decide bootstrap`). **Do not skip this step.** It was absent from this chain for a release: `work`'s bootstrap correctly refuses to create the decision files and names a `decide` bootstrap, `decide`'s `init` only made `design/`, and nothing here invoked `decide` at all — so every project that followed this list ended up with no decision record, and `adr` wrote its index row into a file that did not exist.
   - Finally, run `/perry goals plan-week` — proposes the first batch of weekly tasks, which `/perry work` then writes as BOARD rows + a journal entry under `## New tasks added`.
6. Ask: "Run `/perry goals init` now?" — if yes, read `$PERRY_HOME/goals/SKILL.md` and follow its `init` subcommand. If no, stop and let the user proceed at their own pace.

## `/perry adopt` — converting an existing project

For a project that already exists — code, docs, git history, an issue tracker — the blank-slate `init` chain above throws away the answers the project already contains. `/perry adopt` reads them instead.

```
/perry adopt [--depth=quick|standard|deep] [--only=okr,board,design,knowledge,arch] [--resume] [--recheck]
```

**Read `reference/adoption.md` before running it.** The one rule that governs the whole pipeline: **evidence proposes, the user declares.** Adoption writes exactly one file of its own — `.perry/adoption/<YYYY-MM-DD>-dossier.md` — and everything that reaches `OKR.md` / `BOARD.md` / `design/` gets there through the normal subcommands after the user accepted it. File ownership is unchanged: adoption is an orchestrator, not a fourth writer.

Five stages, each resumable: **scan** (read-only report) → **harvest** (cited evidence) → **infer** (candidates, clustered) → **confirm** (goals authored by the user from a strawman; tasks triaged by cluster; designs/ADRs transcribed only where a source doc exists) → **commit** (materialize, then `perry-lint` must pass). `--recheck` re-runs the harvest against an adopted project and reports drift — work that landed in the repo but never on the board.

Sources, trust tiers, and the depth matrix (including non-code projects) are in `reference/adoption-sources.md`.

## `/perry relocate <path>` — moving Perry's state root

```
/perry relocate <path>          # e.g. /perry relocate perry
/perry relocate . --dry-run     # show the moves, touch nothing
```

Moves every path Perry claims under a new state root and rewrites
`State root:` in `.perry/config.md`. `.perry/` itself never moves — it holds
the pointer, so it cannot sit behind it.

This exists because the state root is chosen **once**, at setup, and projects
grow. A project adopted at `.` that later adds its own `design/proposal.md`
gets `NS-01` (`reference/diagnose.md § Finding catalog`), and relocation is one
of its only two remedies — the other being moving your own file. There is no
per-path opt-out by design, so doing this by hand across fifteen paths is where
someone loses a journal directory.

**Procedure:**

1. **Refuse on a dirty tree.** Same discipline as `diagnose` requiring a restore
   point: `git status --porcelain` must be empty, or stop and say so. Not a git
   repo → copy the tree to `.perry/relocate-<YYYY-MM-DD>-backup/` first.
2. **Compute the moves** from `schema/state-schema.json § claims[]`, never from
   a hand-written list — that is what drifted before. Skip `anchor: project`.
3. **Check the destination is free**:
   ```
   python3 "$PERRY_HOME/bin/perry-lint" --claims --root . --state-root <path>
   ```
   A destination with collisions of its own is refused, not merged into.
4. **Show every move `from → to` and confirm** (`AskUserQuestion`, header
   `"Relocate"`, options: `Move <n> paths | Show the full list first | Cancel`).
   Never move a user's files without the list in front of them.
5. **`git mv` each existing path** (plain `mv` outside git). Paths that do not
   exist are skipped silently — a project without `runbook/` is not an error.
6. **Rewrite `State root:`** in `.perry/config.md`, adding a short `## Why the
   state root is not \`.\`` block naming what collided.
7. **Verify**: `perry-lint --root .` must pass, and `perry-lint --claims` must
   report zero collisions. If either fails, print the `from → to` list so the
   move is reversible by hand, and stop.

`--dry-run` stops after step 4 and writes nothing.

**What it never does.** It never moves a file it did not put there — only paths
Perry claims, and within them only files Perry wrote. It never deletes. It never
relocates *into* a directory that already collides. And it never runs on a dirty
tree, because the `git mv` set is the only thing making it reversible.

## `/perry diagnose` — auditing how a project works with agents

`adopt` converts a project **into** Perry. `diagnose` asks the prior question: **is this project's working structure sound at all?** It runs on any folder, including one that has never heard of Perry, and the right answer is often "leave it alone" or "you need three files" rather than "adopt Perry".

```
/perry diagnose [--depth=quick|standard|deep] [--only=<lanes>] [--dry-run] [--resume] [--recheck]
```

**Read `reference/diagnose.md` before running it.** The governing rule: **every prescription traces to a finding, and every finding traces to a measurement or an answer the user gave.** Nothing may be prescribed because Perry prefers it — diagnosis is inherently judgmental, and without that gate this subcommand becomes a machine that converts every project into a heavier project. It writes exactly one file of its own — `.perry/diagnose/<YYYY-MM-DD>-diagnosis.md` — and changes to Perry state still go through the owning child skill.

Six stages: **scan** (`bin/perry-diagnose`, deterministic and read-only) → **read** (what a script can't measure — the gap between what the docs say and what `git log` shows) → **interview** (≤6 outcome-framed questions; the user's answers override the scan) → **prescribe** (the smallest change set, hard-capped by the user's stated maintenance tolerance) → **execute** (gated per item, restore point first, moves and never deletes) → **recheck** (drift, with declined items remembered rather than re-proposed).

It targets the three ways agent projects actually fail — concurrent sessions interfering, documents growing past the budget where they stop being obeyed, and goals drifting with no runnable check to say what is done. The research behind each, the isolation ladder, and the three archetypes are in `reference/project-archetypes.md`; runnable scaffolds are in `templates/`.

Two outcomes are first-class and must stay available: **zero findings**, and a prescription of pure **subtraction**. A diagnostic that has to find something to justify the run is one the user stops reading by the third invocation.

## Repo layout options

Perry supports two layouts. Pick one at first-time setup; record the choice in `.perry/config.md`.

### Option A — single repo (default for non-code projects)

Everything (OKR, TASKS, evidence, design, handoff, weekly) lives in one repo at the project root. Use this when:
- The project does not produce code (research notes, ops runbooks, business planning, personal projects without a codebase).
- The project ships code but the volume of code commits is low and PMO commits will not pollute the history.

This is the simplest layout. No cross-repo references; everything is one `git log` away.

### Option B — two-repo split (PMO docs ↔ code)

PMO docs live in `<project>-pmo/` (this repo, where Perry's state files sit); code lives in `<project>/`. Use this when:
- The project ships code AND has been observed to suffer from branch contention between PMO doc commits and code commits, OR PMO commits visibly pollute code commit history.
- The user explicitly prefers the separation.

Cross-reference convention:
- PMO docs reference code via `<commit-SHA> path/to/file.py` (commit SHA pinned, not branch — survives rebases).
- Code commits reference PMO task IDs in commit messages (e.g., `Closes TASK-007`).
- Each repo has its own `.git/`; neither repo is a submodule of the other.

Trigger to migrate from A → B: ≥ 2 incidents of branch contention or commit-history pollution within a month. Capture the trigger as a `DECISIONS.md` ADR (`Type: Process`) before splitting.

When B is in effect, `.perry/config.md` records both paths so every child skill knows where to look. Delegation prompts to Coding Agents must explicitly state which repo their work targets.

### `.perry/config.md` shape

```
# Perry configuration

- Document language: <English | 中文 | ...>
- Chat language: <follow user | English | 中文 | ...>
- Repo layout: <single | split>
- State root: <. | relative path>
- Packs: <comma-separated pack names, or absent for software-ops>
- Conformance gate: <advisory | enforce>   (optional; default advisory)
- PMO repo path: <absolute path>
- Code repo path: <absolute path or — if single>
- Last updated: <YYYY-MM-DD>

## Tracks            (optional; absent = one implicit `main` track, mode `project`)

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| main | project | phase/ | — | — | — | — | V3 |
```

`## Tracks` is what turns on `pipeline` / `queue` / `inquiry` mode. A project
that never writes it behaves exactly as Perry did before DESIGN-003 — that is
the point — but a user who never hears the section exists cannot reach three of
the four modes at all, so **first-time setup offers it** (below) and `adopt`
proposes one before it proposes goals.

Children read this file before any output. If the file is missing, prompt the user to run first-time setup.

The field **names** above stay English in every language — this is the file that declares the language, so it has to be readable before the language is known. `Chat language` is optional; absent means `follow user`. See `reference/i18n.md`.

### `State root` — where Perry's files live

**`perry` is the default that setup writes**, as of 2026-08-17. It puts Perry's whole tree under `perry/`, leaving the project's own `design/`, `evidence/` and `knowledge/` untouched — removing the namespace-collision class rather than detecting it case by case.

**The code fallback is still the project root, and must stay that way.** A project whose config has no `State root` line keeps its files exactly where they are. Changing the fallback would send every reader into a subdirectory that does not exist and make an adopted project's entire history vanish from every tool at once. **The default governs what setup writes; it never governs where an existing project is looked for.** Earlier projects wrote `.` and are not migrated — `perry relocate` is there for anyone who wants to move, and "no automatic rewrite of a project's existing structure" is an Anti-Goal.

Two shapes in circulation is two code paths a reader can disagree about, and one already did: `bin/perry-goals` passed the project root where the state root was wanted, and the bug was invisible on every `.`-rooted project — including the test fixture. That is why the default moved, and why `tests/test_claims.py` now asserts every tool resolves through `resolve_state_root` rather than reaching for the project root itself.

**Do not enumerate the claimed paths here.** `schema/state-schema.json § claims[]` is the one authoritative list, and `perry-lint --claims --root .` computes the collision against it. This paragraph used to name five paths while the skills wrote eighteen, so a project owning `evidence/` or `knowledge/` collided silently — a second, hand-maintained copy is what drifted. Run the check; don't recite a list.

`.perry/` itself **never moves**: it is the anchor that marks the folder as a Perry project and it holds this pointer, so it cannot sit behind the pointer. Every reader resolves the root the same way — `viewer/parsers.py § resolve_state_root` is the one implementation, and `schema/state-schema.json` declares which files are anchored at the project root (`anchor: project`) rather than the state root.

Adoption asks this question during `confirm`, before anything is materialized (`reference/adoption.md`).

### `Conformance gate` — and the one thing the agent must not do

Under [ADR-004](perry/decisions/ADR-004-mandatory-migration.md) a project
migrates to Perry's shape once, and every writer then gates on a **declared**
marker: *this file matches Perry's shape, at shape version N, and the user said
so*. The declarations live in `.perry/conformance.md`; `bin/perry-conform`
computes the verdict and is the only thing that writes them.

Today the gate is **advisory** — `perry-task` and `perry-decide` write anyway
and print what they found. Set `Conformance gate: enforce` (or export
`PERRY_CONFORMANCE=enforce`) to make them refuse instead. **Reading is never
gated in either mode.**

When a write prints a conformance line, **relay it and let the user decide.** Do
not run `perry-conform declare` on the user's behalf: `perry/OKR.md` — *"adoption
proposes; the user declares"* — is the rule the marker exists to encode, and a
tool or an agent stamping it unasked is the violation, not the shortcut. Say
which file, which verdict, and which command; then wait.

## Routing reference

When the user types something inside a `/perry` session, route to the right child rather than answering ad-hoc.

**Route to the `goals` lane (alias `okr`) for:**
- Setting or revising goals · `init`, `revise`, `pivot`
- Phase planning · `plan-phase`, `score-phase`, `snapshot`, `dashboard`
- Weekly task proposals · `plan-week` (the hand-off step)
- Anything about Operating Principles, Anti-Goals, OKR versions, Cost Ceiling, KR scoring

**Route to the `work` lane (alias `pmo`) for:**
- The standup itself, status, triage, blocker check
- Task lifecycle · `add-task`, `close-task`, `drop-task`
- Cadence rituals · `monday-plan`, `midweek-check`, `friday-review`, `mid-phase-review`, `end-phase-retro`
- Cross-session work · `coordinate`, `delegate` (manual prompt), `dispatch` (auto end-to-end via claude-subagent or codex), `handoff`
- Opening the project in a browser / live web console · `viewer` (= `browse`) — agent starts it and opens the browser for you
- Risks and chasing the user · `risk`, `nudge`
  (ADR recording moved to the `decide` lane — see below)
- Phase transition · `rollover`

**Route to the `decide` lane (alias `design`) for:**
- Anything called RFC / architecture / design doc · `new`, `resolve`, `lock`, `revise`, `supersede`, `drop`, `handoff`, `status`
- Recording a decision · `adr <topic>`, `adr --supersede` / `--expire` / `--archive`. Moved here from `work` by the signed hand-off contract: `DECISIONS.md` and `decisions/` belong to this lane
- "Should we design this before building it?" → yes if multi-system, irreversible, or has multiple open user decisions

**Handle here in the router (without loading a lane):**
- The combined snapshot itself.
- `adopt` — converting an existing project into Perry state. It spans all three lanes, so it is orchestrated here and materialized through the children's own subcommands (`reference/adoption.md`).
- `diagnose` — auditing and refactoring how a project works with agents. Also an orchestrator, and the one subcommand that must be able to conclude the project needs *less* structure, or none of Perry's (`reference/diagnose.md`).
- "Explain Perry" / "what is this skill" — short pointer to README.
- Recommending the next action when the choice spans more than one child.
- Confirming or updating `.perry/config.md` (document language, repo layout).
- `help` — see below.

## `/perry help [<lane>]`

Without arg: print a compact overview of the three lanes + when to use each + a pointer to each lane's own `help`. This is the navigation entry point for users who don't know what's available yet.

Suggested format:

```
Perry — virtual project office. One command: /perry

  /perry    Combined snapshot across all three lanes.
            Use when: starting a fresh session, one-stop "where are we",
            or you don't know which lane you want. This is the default —
            you can always just type /perry.
            Common: /perry, /perry help

  /perry goals <sub>     Goal-setting (alias: /perry okr) (overall + current phase OKR + weekly proposals)
            Use when: setting goals, planning a phase, scoring KRs,
            pivoting strategy.
            Common: init, plan-phase, plan-week, score-phase, snapshot, dashboard
            Full list: /perry help goals

  /perry work <sub>      Execution stewardship (alias: /perry pmo) (BOARD, journal, dispatch, cadence)
            Use when: standup, planning the week, delegating to agents,
            tracking blockers, writing weekly status, phase rollover.
            Common: triage, plan-week, dispatch, friday-review, handoff
            Full list: /perry help work

  /perry decide <sub>    Design-doc / RFC / decision stewardship (alias: /perry design) (locked decisions before building)
            Use when: drafting an RFC, locking user decisions, handing off
            implementation tasks to PMO.
            Common: new, resolve, lock, adr, handoff
            Full list: /perry help decide

  The lane name is optional when the subcommand is unambiguous —
  /perry plan-phase and /perry goals plan-phase are the same thing.

  /perry adopt   Convert an EXISTING project into Perry state.
            Use when: the project already has code, docs, git history, or a
            tracker, and starting from a blank OKR would throw that away.
            Evidence proposes; you declare. Nothing is written until you accept.
            Common: /perry adopt, --depth=quick, --recheck

  /perry diagnose  Audit how a project works with agents, then refactor it.
            Use when: sessions keep interfering, the md files have become a
            jungle nobody can navigate, or there's no way to say what's done.
            Works on ANY folder — Perry not required, and "your structure is
            fine" is a valid result. Measures, interviews, prescribes the
            smallest fix, then executes it with your approval per item.
            Common: /perry diagnose, --dry-run, --recheck

First-time setup: /perry in a new project → confirms language + repo layout,
then asks new-vs-existing and routes to /perry adopt for existing projects.
Read more: $PERRY_HOME/README.md
```

With arg `goals`, `work` or `decide` (or their aliases `okr`, `pmo`, `design`): read that lane's SKILL.md and render its `help` subcommand (the lane owns the detail). Don't re-render their tables here.

`help` does NOT trigger the combined snapshot ritual.

## Style rules

- **Lead with the dashboard, not narration.**
- **Numbers, IDs, file paths.** Not paragraphs.
- **An ID never travels alone.** The first time an ID appears in any user-facing output, it carries its human name: `REL-002 ("Flake detector") is blocked on USER-014 ("Confirm staging env default")`, never `REL-002 blocked on USER-014`. Later mentions in the same response may use the bare ID, and a table with a Title column already satisfies this. Perry mints `REL-`, `ADR-`, `DESIGN-`, `P-O1.2`, `USER-`, `CAD-`, `SRC-`, `CL-`, `RX-` and phase numbers — that is a private vocabulary issued to someone who never agreed to learn it, and an unresolvable ID is a dead end in the middle of a sentence the user is trying to act on. Use `bin/perry-explain <ID>` to resolve one, `--all` for the glossary. Full rule in `reference/user-load.md`.
- **Never ask a question the user cannot evaluate.** Before offering options, check whether the user can predict what will be different for them under each. If not, reframe in consequences, or decide it yourself and say so, or narrow to two — see `reference/user-load.md § The three exits`. Depth of analysis and usefulness of a question come apart completely once the subject leaves the user's expertise, and this gets *worse* as the agent gets better.
- **Never mint an example ID that resolves to nothing.** Writing a concrete
  `SRC-<number>` or `TASK-<number>` in prose to illustrate a shape creates a
  reference Perry's own `LOAD-02` check reports as dangling — correctly, because a reader cannot tell
  an illustration from a real cross-reference. Use the placeholder form
  (`SRC-n`, `TASK-NNN`, `<DESIGN-ID>`) in every example. This rule exists
  because Perry violated it three times in one session while writing the
  documentation that forbids it — and a fourth time in the sentence recording
  the third. That fourth one is the tension worth naming: **writing down that
  you cited a nonexistent ID requires not citing it again.** Describe it
  ("a source id in an example"), never quote it. The check cannot tell an
  incident report from a live cross-reference, and it should not try — a
  checker that special-cased prose about itself would be one exemption away
  from useless.
- **Cite the file** for every claim.
- **Never invent state.** Print `—` and ask.
- **Write in the configured languages.** Chat replies follow `Chat language` (or the user's own language when unset); files follow `Document language`. IDs, enum values, file paths, slugs and command names stay English in every language, so a Chinese dashboard line reads `REL-002（"抖动检测器"）blocked，等 USER-014`. Never translate a quoted artifact — a path, a command, an error message, or the user's own words. **A file stays in one language end to end. A chat reply mixes**: a technical term with no settled equivalent in the chat language stays English — `交付了 contract 2.0`, not `交付了契约 2.0` — and an English idiom is never translated word for word, it is replaced by a plain description of what happened. The test is "would someone doing this job say it out loud?" Perry failed this for a whole session while following every other rule here; `reference/i18n.md § Writing chat prose in a language that is not English` has the specifics.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.

## User-prompt convention (AskUserQuestion)

Whenever a Perry skill (top-level or any child) needs the user to make a choice with **2–4 distinct options**, prefer the `AskUserQuestion` tool over free-text "what do you want?" prompts. The Claude Code / Desktop UI renders `AskUserQuestion` as clickable button choices with an automatic "Other" free-text fallback — much faster for the user than typing.

> **Codex host**: `AskUserQuestion` is not available. Render the same option set as a numbered free-text prompt per `$PERRY_HOME/reference/host-capabilities.md § AskUserQuestion → numbered free-text prompt`. The chosen value, downstream writes, and conventions below are unchanged — only the rendering differs.

### When to use it

- Any subcommand that branches based on a user choice with a small bounded option set (e.g., `/perry goals score-phase` per-KR `achieved | partial | missed | dropped`, `/perry work triage` per-row `apply | edit | skip`, `/perry decide resolve` per-User-Decision row).
- First-time setup choices (document language, repo layout).
- Per-spec dispatch choice when the spec doesn't pin an executor (`/perry work dispatch` → falls back to asking `claude-subagent | codex | manual`).
- Multi-select when you offer up to 4 candidate items the user may approve all/some/none of (use `multiSelect: true`).

### When NOT to use it

- Open-ended questions that need a sentence or paragraph (e.g., "What is this project's mission?"). Free-text only.
- Choice sets larger than 4 options. Either narrow first (recommend 1–4 + leave "Other" as the auto-filled fallback), or split into two `AskUserQuestion` calls.
- Confirmations that should always block on explicit user words (e.g., authorizing a high-stakes operation per the project hook). The auto-update check, `/perry work dispatch` pre-flight refusals, and similar safety gates STILL ask in chat — `AskUserQuestion` is not a permission grant.

### Conventions

- **2–4 options per question.** No more, no fewer.
- **Label ≤ 5 words.** The tool enforces this; long descriptions go in the `description` field, not `label`. Labels and descriptions are written in the **chat** language; an option whose value lands in a file (a status, an executor, an enum) shows the invariant token alongside the localized wording — `跳过 (skip)` — so the user can connect the button they pressed to the word that appears in the file.
- **Recommended option first.** Append `(Recommended)` to the label so the user sees which one Perry suggests.
- **Header chip ≤ 12 chars** (e.g., "Executor", "Status", "KR-1.2").
- **Each option's `description` carries the trade-off** — what happens, what it implies, what's lost. Don't make the user guess.
- **The trade-off is stated in consequences, not mechanism.** "Runs on your laptop with no setup, but breaks if two people use it at once" is decidable. "SQLite vs Postgres" is not, unless the user already knows. If an option cannot be expressed in something the user will experience, that is the signal it should not be a question — see `reference/user-load.md`.
- **Offer the escape hatch on anything the user may not be equipped for.** "Or I pick and tell you what I picked" as an explicit option. If they take it, don't re-ask a variant later. Two deferrals in a session means stop offering choices and switch to recommendations they can veto — and say that's what you're doing.
- **Cap open decisions at three at a time.** Past that, queue and say so. A decision backlog stalls everything downstream or lets it proceed on a guess, and afterwards nobody can tell which happened.
- **Anything decided on the user's behalf gets logged** as agent-decided, with what would trigger a revisit. Asking less is only acceptable if those calls stay visible and reversible.
- **Optional `preview`** for showing a code/template snippet (e.g., showing what the rendered task block will look like before they approve).
- Mutually exclusive options unless `multiSelect: true`.

### Concrete pattern: child skills with structured option lists

For child skills whose state files already enumerate options (notably `design/<DESIGN-ID>-*.md`'s `User Decisions` table), write the Options column in **pipe-separated short labels** so `decide` can map each cell directly to `AskUserQuestion` options without rephrasing:

```
| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Cache backend | Redis | Memcached | DynamoDB | TBD | — |
```

Each piped token becomes one `AskUserQuestion` option label.

## Per-project hooks (optional)

If your project has specific roadmap files, MCP tools, agent roles, cost ceilings, or promotion stages, add a hook block to **the children's** `SKILL.md` files (`goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md` each have a `## Per-project hooks` section). The top-level Perry skill stays project-agnostic.

Project hook files live at the project root (not in the skill folder), so a single Perry installation can serve many projects without entanglement. The recommended location is `<project_root>/.perry/hook.md`; children read it on every invocation.

## Auto-update

Every Perry skill invocation runs `bin/perry-update-check` as the first action. The script:
- Throttles itself to **once per 7 days** via `$PERRY_HOME/.update-check` mtime; most invocations exit immediately with no output.
- Detects "dev mode" — symlink install, dirty working tree, or non-`main` branch — and in that case **only fetches and reports**; it never auto-pulls (so it can't trample your WIP if you're editing Perry source).
- For "consumer mode" (real directory, clean tree, on `main`), does an ff-only `git pull` from `origin/main`.
- Always exits 0 (network failure, unresolved merge, etc. → notify and continue; never block the standup).

Manual trigger: `bash "$PERRY_HOME/bin/perry-update-check" --force` (bypasses throttle).

The script is invoked from the standup ritual of every lane, so any `/perry …` invocation covers it. If the skill source is not a git checkout (e.g., extracted from a tarball), the check exits silently.

## See also

- [README.md](README.md) — full overview, file layout, design rationale.
- [INSTALL.md](INSTALL.md) — install instructions.
- [schema/README.md](schema/README.md) — the state-file contract every skill, template, and parser must agree with; validated by `bin/perry-lint`.
- [reference/adoption.md](reference/adoption.md) — `/perry adopt`: the five-stage pipeline that converts an existing project into Perry state. The governing rule (**evidence proposes, the user declares**), the asymmetry between what may be inferred and what may not, cluster triage, the cluster→KR attribution pass, and the list of things adoption never does.
- [reference/i18n.md](reference/i18n.md) — the localization contract: `Document language` (files) vs `Chat language` (replies), the three layers of text and which one never gets translated, the heading/column glossary in `schema/state-schema.json § i18n` that lets a Chinese project lint and parse exactly like an English one, why templates stay English source, why `bin/` scripts speak English and the agent translates on relay, and how to switch language or add a new one.
- [reference/user-load.md](reference/user-load.md) — the shared contract for all four skills on **how much a human can carry**: never ask a question the user cannot evaluate (and the three exits when the honest answer is that they can't), cap open decisions, log what was decided on their behalf, and the rule that **an ID never travels alone**. Perry mints nine ID families; this is what stops them becoming a private vocabulary.
- [reference/diagnose.md](reference/diagnose.md) — `/perry diagnose`: the six-stage pipeline that audits and refactors how a project works with agents. The governing rule (**every prescription traces to a finding**), the six-question interview, the prescription patterns, and the execution safety rules.
- [reference/project-archetypes.md](reference/project-archetypes.md) — the research diagnose applies: the three failure modes of agent projects, the isolation ladder, the tier discipline for documents, the minimum viable spine, three archetypes, and an explicit account of where the evidence is thin.
- [templates/](templates/) — runnable scaffolds for the three archetypes, including a verification loop for the two that have none natively (`kb-lint`, `deliverable-lint`).
- [reference/adoption-sources.md](reference/adoption-sources.md) — the harvest catalog: source detectors, A/B/C trust tiers (which cap derived confidence), the depth matrix, scale limits, non-code projects, and the citation forms every piece of evidence must produce.
- [reference/input-quality.md](reference/input-quality.md) — shared input-quality rubric run by `goals` / `decide` / `work` before writing user-authored content to tier 1 files (advisory + override).
- [reference/okr-linkage.md](reference/okr-linkage.md) — shared O→KR→Project attribution gate: resolve a Project/Task's KR by stable ID via `phase/<NNN>-linkage.md`, and when it's unclear **ask the user, never guess** (hard gate; unresolved → `unlinked`, excluded from roll-up).
- [goals/SKILL.md](goals/SKILL.md) — full goal-setting subcommands and templates.
- [work/SKILL.md](work/SKILL.md) — full execution stewardship subcommands and templates.
- [decide/SKILL.md](decide/SKILL.md) — full design-doc stewardship subcommands and templates.
