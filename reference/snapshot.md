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

**A `pipeline: plan` row** is a planning draft (`goals/reference/planning.md`).
Its card reads `⏸  Interrupted plan · <horizon>/<route> · <path>`, then
`Stopped <N>d ago · pending question: <step> · asked <questions_asked>/8 ·
answered <interview_answers>`, and — instead of the adoption card's last line —
`Saved as a draft; no canonical goal has been written.` Resume re-reads it
with `draft show` and shows the recorded pending question without asking a new
one; Abandon is `draft abandon`. There is no Start over: the file stays.

**Never resume without asking.** A run continued on Perry's initiative

## A flag mismatch is refused, not merged

**A flag mismatch is refused, not merged.** If the invocation carries a
`--depth` or `--only` that disagrees with the dossier's `depth:` / `lanes:`,
say so and ask which wins rather than resuming into a mixed scope.

## Step 3 — which read, and when the big one

`SKILL.md` step 3 calls `perry-state --compact`. It is a strict projection of
`--json`, computed in the same process — `bin/perry-state § COMPACT` declares
every field of it and `tests/test_compact_payload.py` walks that same
declaration — so the two can never answer differently about a value they both
carry.

Measured on Perry's own project, 2026-09-09:

| Call | Bytes, measured 2026-09-09 on Perry's own project |
|---|---|
| `--compact` | ~11,300 |
| `--dashboard` (text, no vocabulary) | 1,053 |
| `--json` | ~259,000 |

**The two large figures are approximate on purpose.** They were written exact
three times in this branch and were wrong all three times within a day, because
they move with the project's own content: `--compact` grew 22% while phase B
was landing, from KR titles and track declarations, not from task rows. What
does not move is the ratio — `--compact` is about 4% of `--json` — and the
property behind it: task ROWS are counted, not carried, so a project with two
thousand of them costs the same integer. `tests/test_compact_payload.py`
asserts the ratio and the growth property; nothing asserts a byte count, which
is why none of them should be stated as one. It carries what
step 4 renders and what a WRITE needs first — the declared tracks, their modes
and the stages legal on each, which used to mean reading `--section project`,
11,681 bytes, three levels down.

Reach for more only when something needs it. `--section <name>` gives one
top-level key in full (`board`, `okr`, `phase`, `project`, …), `perry-explain
<ID>` answers about one id, and `--json` is the whole payload — unchanged, and
still the contract `schema/` documents.

## Step 3b — load the mode file for each declared track

3b. **Load the mode file for each declared track** — `project.tracks[]` in
   the payload above (`project.config.tracks[]` under `--json`). For each distinct `mode` in that list, read
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

   **Which register the list came from — `tracks_source`.** It travels with
   the list: `project.config.tracks_source` under `--json`,
   `project.tracks_source` under `--compact`. The implicit `main` above is the
   project's real answer for three of its values and a stand-in for two, and
   the list alone cannot tell you which:

   | `tracks_source` | `.perry/config.jsonl` | the track list is | what to do |
   |---|---|---|---|
   | `store` | present, usable, holds at least one track record | the project's register, in stored order | use it |
   | `store-default` | present and usable (an empty store included), holds no track record | DESIGN-003's implicit `main`, and that is the project's answer | use it |
   | `absent` | not there | the implicit `main`: nobody has configured this project | use it; this is not an error |
   | `unreadable` | present, and could not be read: bytes that do not parse as JSONL, or a path Perry may not look at | the implicit `main` as a **stand-in**, not the project's register. Every track the store declares is missing | do not trust the list or anything keyed on a track. `warnings[]` says so, `perry-task` and `perry-goals` refuse writes, and `perry-lint` reports the store |
   | `invalid` | present and parses, and holds a record that does not validate | the same stand-in as `unreadable` | the same as `unreadable` |

   `bin/perry-state` still defines the name `no-track-record` and never emits
   it: a usable store with no track record is `store-default`.
   `tests/test_tracks_source_documented.py` holds this table to what the tool
   emits, in both directions.

   Cost discipline: **one mode file per distinct mode, not per track.** Five
   pipeline tracks read `modes/pipeline.md` once. Modes are tier 1 and loaded
   on demand, exactly like `*/reference/*.md` — the router's own tier-0 cost is
   this paragraph and one payload field.

   The register is the track records in `.perry/config.jsonl`, which the user
   owns and writes with `perry-config track`, because a track is configuration
   rather than state and `.perry/` is a path Perry already claims. Its shape is
   in `schema/state-schema.json`; `perry-lint` validates each record's `mode`
   and `default_rung` whenever the store exists and reports the absence when it
   doesn't.

## Step 3c — apply the active packs' display glossary

3c. **Apply the active packs' display glossary** — `project.packs[]` in the
   payload (`project.config.packs[]` under `--json`). Each entry carries a `glossary` map of *term → shown as*. When
   rendering anything a human reads — the dashboard, the TL;DR, suggested
   actions, `AskUserQuestion` labels — substitute the mapped nouns.

   Only `present: true` entries are active. Report unavailable selections as
   unavailable; invalid/unreadable settings are unknown. Explicit `packs: []`
   enables no pack. See `reference/config.md § Pack capabilities and controls`
   for selection provenance and optional route/gate eligibility. Never infer
   capability readiness from pack presence or ask to enable it at every snapshot.

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

4. **Render the combined dashboard** — no preamble. Steps 4–6 together are
   one initial screen: **at most 12 visible lines and 1,200 Unicode characters**.
   Count all text, whitespace, links, blank lines, the next block and any
   question or agent note. This bounds authored text, not wrapping at an
   unknown UI width. The agent authors the words; a deterministic counter may
   measure lines/characters/bytes, never interpret prose or select facts.

   Use this compact shape, applying the active-pack glossary from step 3c:

   ```
   🅿 Perry · <project name> · <date>
   You are here: <position[] in returned order and states>
   Progress: <declared measurements, or unknown/absent/stale explicitly>
   Open tasks: <open> · P0=<n> · P1=<n> · P2=<n> · blocked=<n>
   Pending user decisions: <count> · <brief oldest topic and age, if known>
   Next: <primary.command> — <primary.reason>
   Details: <explicit link or “ask for snapshot details”> — objectives, pending decisions, alternates, unknown causes and sources.
   ```

   Project/current phase position, honest progress, open/blocked counts,
   pending decisions and the selector's primary stay on the initial screen.
   Use payload figures only: task closures and KR links are not measured KR
   progress. Missing current values or checks mean unknown, never zero or done;
   absent goals/phase/measurements and stale values must be named as such.
   Use `—` for empty fields. Never fabricate values. A missing pending count
   means unknown, not no decisions. Do not count rows to fill a missing field.

   **One detail level, no loss of facts.** Prepare a single detail view from
   the same capture, reachable by the explicit pointer above (a linked artifact,
   supported collapsed view, or “ask for snapshot details”; not another new
   command). Do not append expanded details to the initial screen. Preserve
   overall/phase objective titles and supplied measures, period/day/cost facts,
   all pending user decisions with their full requests and blocking references,
   top risk, last decision, weekly/handoff facts, and every returned alternate
   and unknown cause. Preserve absent/unknown values there too. Keep all
   recommendations in returned order across initial and detail views; moving
   an alternate is not deleting it. Details must not require another drill-down
   to see the retained facts. Cite the capture's project root, generated time
   and calls (`--compact`, `--section next`, plus any targeted reads); never
   present an old capture as current. Resolve missing detail through the
   existing section/explain reads, not a parallel reader of state files.

   **Every ID printed here carries its title**, in either view, per
   `## Style rules`. If the payload has an ID but no title, run
   `bash "$PERRY_HOME/bin/perry-explain" <ID>` rather than inventing a name.
   Long objective/pending titles belong in details; the initial summary may
   name a short topic without an ID. Keep selector reasons unchanged (apart
   from chat-language translation); attach titles for IDs they contain.

   Measure the authored initial text before sending. Move secondary facts to
   details, remove optional prose and shorten topic summaries until it fits;
   never remove pending decisions, unknowns or recommendations from both views.
   If mandatory selector text alone cannot fit, disclose the budget exception
   and preserve it; do not silently truncate or claim a passing measurement.

   **Safety takes precedence.** A blocking recovery or interrupted-run gate
   replaces the normal dashboard with its existing stop/card and required
   paths/errors/choice. Do not read further state, auto-resume, or imply normal
   startup. Fit the safety card when possible; never hide a required error or
   choice to claim the budget. Steps before 4 and their gates are unchanged.

## Step 5 — render the next block, and step 6 — ask

5. **Render the next block.** Run `"$PERRY_HOME/bin/perry-state" --section next`
   and follow `reference/next.md § Rendering`: the *you are here* line and
   primary stay on the initial screen; the at most two returned alternates
   and every `unknown[]` fact/reason appear in the single detail view, in
   returned order. Signal unknowns on the initial screen with the detail
   pointer even when `primary` is null (`Nothing is due.` is not “all known”).
   The command decides. Never reorder, add or drop a recommendation, and never
   build one from dashboard numbers. One line marked as your own note is
   allowed; it counts toward the budget and cannot replace the recommendation.

6. For an unscoped `/perry` invocation, ask **"What do you want to do?"** within
   the same budget. During already authorized work, retain that choice/autonomy
   and continue the requested scope; do not demand a new question or execute
   the selector's recommendation merely because it appeared. Startup safety
   questions still apply. This does not change the shared closing procedure.

If the user picks an OKR-flavored action (plan, score, pivot, revise), read `$PERRY_HOME/goals/SKILL.md` and follow it. A work-flavored action (triage, status, delegate, handoff, rollover, risk) → `$PERRY_HOME/work/SKILL.md`. Recording a decision (`adr`) is the `decide` lane, not this one. A design-flavored action (RFC, architecture, lock, supersede) → `$PERRY_HOME/decide/SKILL.md`. If unclear, ask which, then route. **Read the lane file in full before acting on it** — it is loaded on demand precisely so it can be complete.
