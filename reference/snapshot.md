# The combined snapshot — the steps the router points at

Tier 1. Loaded on demand from `SKILL.md § Mandatory first move: combined
snapshot`, which keeps the ordering-critical steps (set `$PERRY_HOME`, detect
host, the interrupted-run gate, the state read) and points here for the rest.

Extracted from `SKILL.md` on 2026-08-18 (TASK-064) to keep the tier-0
router inside its byte budget. The prose is carried over unchanged.

## Why the interrupted-run gate exists

This gate exists because such a run is otherwise **invisible**. `/perry adopt`
stages 0–3 deliberately write no state file (`reference/adoption.md § The one
rule`), so `installed: false` in step 3 is true for an abandoned adoption and
for a folder that has never heard of Perry alike — and the next session
re-runs First-time setup, re-asks language and repo layout, and starts a
*second* dossier beside the first. Dossier paths are dated, so nothing
collides and nothing warns.

## The interrupted-run card

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

## A flag mismatch is refused, not merged

**A flag mismatch is refused, not merged.** If the invocation carries a
`--depth` or `--only` that disagrees with the dossier's `depth:` / `lanes:`,
say so and ask which wins rather than resuming into a mixed scope.

## Step 3b — load the mode file for each declared track

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

## Step 3c — apply the active packs' display glossary

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

## Step 4 — render the combined dashboard

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

## Step 5 — suggest 1-3 next actions, and step 6 — ask

5. **Suggest 1–3 next actions** combining `goals`, `work`, and `decide` concerns:
   - "phase #002 commit KRs ≥80% → run `/perry work end-phase-retro`, `/perry goals score-phase`, `/perry work rollover`, `/perry goals plan-phase <new-slug>`"
   - "USER-014 (\"Confirm staging env default\") idle 6d, weekly is 8d old → run `/perry work nudge` then `/perry work friday-review`"
   - "no current phase → run `/perry goals plan-phase <slug>`, then `/perry goals plan-week`, then `/perry work` to add the tasks"
   - "DESIGN-002 (\"Flake scoring\") in_review for 8d → run `/perry decide lock` or `/perry decide revise`"

6. Then ask: **"What do you want to do?"**

If the user picks an OKR-flavored action (plan, score, pivot, revise), read `$PERRY_HOME/goals/SKILL.md` and follow it. A work-flavored action (triage, status, delegate, handoff, rollover, risk) → `$PERRY_HOME/work/SKILL.md`. Recording a decision (`adr`) is the `decide` lane, not this one. A design-flavored action (RFC, architecture, lock, supersede) → `$PERRY_HOME/decide/SKILL.md`. If unclear, ask which, then route. **Read the lane file in full before acting on it** — it is loaded on demand precisely so it can be complete.
