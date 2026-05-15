# Incidents — postmortems as a feedback loop

When production breaks, the user's instinct is to fix it and move on. That instinct burns a free lesson. **Every incident is a paid signal about which invariant is missing, which runbook is wrong, and which knowledge digest is overdue.** The `incident` subcommand exists to turn that signal into structural changes — not paperwork.

The smallest possible incident record is fine. A 5-line file is better than no file.

## When to open an incident

Open one whenever any of these happen:
- A deployed component (anything with a runbook) misbehaves in production.
- A canned op fails or produces an unexpected result.
- A scheduled job silently doesn't run, or runs with bad output.
- A real-account / external-system action diverges from what was intended.
- The user has to dig into agent-written code to figure out what happened.

Do NOT open an incident for:
- A dispatched task that failed during dispatch (that's a `review` row, handled by the normal task lifecycle).
- A bug found before deployment.
- A planning miss / scope cut (that's a `triage` or retro item).

## File layout

```
<project_root>/
└── incidents/
    ├── INDEX.md                                # auto-maintained catalog
    ├── <YYYY-MM-DD>-<slug>.md                  # one file per incident
    └── ...
```

Naming: ISO date + 1–3 word slug. Examples: `2026-05-12-trader-stuck.md`, `2026-05-13-alert-bot-silent.md`. Slug should match the affected runbook's slug when possible.

`incidents/INDEX.md` lists every incident with: date · slug · status · affected component · 1-line summary · ID of derived invariant/runbook/digest change (if any).

## Subcommands

### `/pmo incident <slug>` — open a new incident

1. Compute filename: `incidents/<today>-<slug>.md`.
2. If file exists already today with that slug, prompt: `Append to existing | Make new with -2 suffix | Cancel`.
3. Create file from `state/incident_TEMPLATE.md`. Pre-fill: date, slug, status `open`, opened-by `user` or `pmo`.
4. Ask the user to fill the **Symptom** field via free-text prompt (the only mandatory at-open field). Everything else can be filled later.
5. Append a one-line entry to today's journal under `## Notes`: `Incident opened: <slug> (<symptom one-liner>)`.
6. Update `incidents/INDEX.md`.
7. If a runbook exists for the affected component, **print its "Common failures + canned ops" section verbatim** as the next step. This is the first place the user should look.

The point at open-time is to write down the symptom while it's fresh. Root cause / fix can come later.

### `/pmo incident close <slug>` — close an incident (3-question gate)

This is where the feedback loop lives. Refuse the close until all three questions have a concrete answer (yes-with-action OR explicit no-with-reason).

1. Open `incidents/<YYYY-MM-DD>-<slug>.md`. Verify these fields are filled: Symptom · Timeline · Root cause · Fix.
   - If any are empty: refuse close, list missing fields.
2. Use `AskUserQuestion` with **three** questions (in one call):

   **Q1** — `header: "Knowledge"`, options:
   - `Yes — write digest (Recommended if novel)` — calls `/pmo digest --paste` after close to capture the lesson as a knowledge entry.
   - `No — duplicate of existing digest` — prompt for the digest path; record it as the reference.
   - `No — too narrow to generalise` — must include a one-line reason.

   **Q2** — `header: "Architecture"`, options:
   - `Yes — update ARCHITECTURE.md` — prompt for which §-section. Common edits: add a new §6 non-negotiable; tighten a §5 contract; surface a §7 open question. The doc edit is the user's; PMO opens the file and pre-drafts the proposed change inline based on the incident root cause.
   - `Yes — file a follow-up ADR` — calls `/pmo decide` so the decision history captures the new structural rule before it lands in `ARCHITECTURE.md`. The ADR's resolution writes the section edit when ready.
   - `No — incident is on the runbook side, not the architecture` — must include a one-line reason.

   **Q3** — `header: "Runbook"`, options:
   - `Yes — update runbook/<component>.md` — appends a new "Common failures" entry pre-drafted from this incident; bumps `Last verified:` date.
   - `Yes — write runbook for <component>` (only offered if the component has none) — schedules a P1 task.
   - `No — runbook already covers this case` — must include a one-line reason.

3. Each question's outcome is written into the incident file under `## Derived changes`:
   ```
   ## Derived changes
   - Knowledge: knowledge/<topic>/<this-incident>-digest.md       (or "skipped — <reason>")
   - Architecture: ARCHITECTURE.md §6.NN-7 (added) / §5.<contract> (tightened)   (or "skipped — <reason>")
   - Runbook: runbook/trader-daemon.md (failure mode added)       (or "skipped — <reason>")
   ```

4. Flip incident status to `resolved`. Update `incidents/INDEX.md` with the derived-change ID(s).
5. Append a `## Status changes` line to today's journal: `Incident <slug> resolved · root cause: <one-line> · derived: <list of changes>`.

The 3-question gate is intentionally noisy. Skipping all three with reasons is allowed — but each skip is a recorded choice, which means a pattern of "skipped — too narrow" across many incidents becomes visible in `mid-phase-review`.

### `/pmo incident list [--open | --all]`

Default: list open incidents (status ≠ `resolved` and ≠ `archived`). With `--all`, include resolved ones (latest 20). Output columns: date · slug · status · component · symptom one-liner · derived-changes count.

### `/pmo incident archive <slug>`

Manually mark an incident `archived` (no longer relevant, e.g., the component itself was deprecated). Preserves the file; only flips status. Surfaced separately in `INDEX.md`.

## Incident template (`state/incident_TEMPLATE.md`)

```markdown
# Incident — {{YYYY-MM-DD}} — {{slug}}

> Status: open | investigating | resolved | archived
> Opened: {{YYYY-MM-DD HH:MM}} by {{user | pmo}}
> Affected component: {{runbook slug, or 'unknown'}}
> Severity: {{minor | major | critical}}              # filled at close
> Resolved: {{YYYY-MM-DD HH:MM, or '—'}}

## Symptom

What the user observed. Plain language. Include error messages verbatim, timestamps, what the user was doing when it happened.

## Timeline

- {{HH:MM}} — {{event 1}}
- {{HH:MM}} — {{event 2}}
- {{HH:MM}} — {{detection / first response}}
- {{HH:MM}} — {{fix applied}}
- {{HH:MM}} — {{verified resolved}}

## Root cause

One paragraph. Why did this happen? Be specific — not "a bug in the code" but "the trader-daemon's reconnect loop didn't reset its backoff counter on success, so after one transient failure it stayed at 5-minute reconnect intervals indefinitely."

## Fix

What was changed to resolve THIS incident. File paths, commands, config edits. Distinguishes the immediate fix from the structural prevention (see Derived changes).

## Evidence

- {{Log file path / commit SHA / dashboard screenshot path / canned op output}}
- {{Test or reproduction step that confirms fix}}

## Derived changes

Filled at close-time by the 3-question gate:

- Knowledge: {{knowledge/<topic>/<slug>-digest.md, or 'skipped — <reason>'}}
- Architecture: {{ARCHITECTURE.md §-section added or tightened, or 'skipped — <reason>'}}
- Runbook: {{runbook/<component>.md updated, or 'skipped — <reason>'}}

## Notes / open follow-ups

- {{anything else — future watch items, related risks, etc.}}
```

## Integration with other PMO surfaces

- **Standup dashboard**: when `incidents/` exists, the dashboard adds a line: `🔥 Incidents · <open> open · <this-week> this week · <phase> this phase`. Omit if directory missing.
- **`triage`**: open incidents older than 3 days are surfaced as P0 attention items.
- **`mid-phase-review`**: pulls all incidents from the current phase, summarises by component, lists "derived-change skipped" rationales as a pattern check.
- **`end-phase-retro`**: same plus "of <N> incidents this phase, <K> drove ARCHITECTURE.md edits / <K> drove runbook updates / <K> drove digests" — this number is the feedback-loop health metric.
- **Hook integration**: project hooks can declare an `## Incident routing` block that maps known failure-mode keywords to specific runbooks or canned ops (the open-time flow surfaces them automatically when symptom text matches).

## Bootstrap

PMO does NOT create `incidents/` at project bootstrap. It's created lazily on first `/pmo incident <slug>`. On that event:

1. `mkdir -p incidents/`
2. Create `incidents/INDEX.md` from `state/incidents_INDEX_TEMPLATE.md`.
3. Proceed with incident creation.

## Why the 3-question gate is non-negotiable

An incident without derived changes is a fix-and-forget. Fix-and-forget is how the same incident recurs in 6 weeks under a different surface. The 3 questions force the user to make the trade-off explicitly:

> "I'm closing this incident WITHOUT updating ARCHITECTURE.md because <reason>."

That recorded "without" is what makes the next mid-phase review honest. If the same root cause shows up 4 incidents in a row and the user keeps skipping ARCHITECTURE edits with "too narrow", the pattern is visible — and PMO will say so in the review.
