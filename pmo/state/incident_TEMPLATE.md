# Incident — {{YYYY-MM-DD}} — {{slug}}

> Status: open | investigating | resolved | archived
> Opened: {{YYYY-MM-DD HH:MM}} by {{user | pmo}}
> Affected component: {{runbook slug, or 'unknown'}}
> Severity: {{minor | major | critical}}
> Resolved: {{YYYY-MM-DD HH:MM, or '—'}}

## Symptom

What the user observed. Plain language. Include error messages verbatim, timestamps, what the user was doing when it happened. Write this first, while the moment is fresh.

## Timeline

- {{HH:MM}} — {{event 1}}
- {{HH:MM}} — {{event 2 — usually the first noticeable bad behaviour}}
- {{HH:MM}} — {{detection / first response}}
- {{HH:MM}} — {{fix applied}}
- {{HH:MM}} — {{verified resolved}}

## Root cause

One paragraph. Specific, not generic. Identify the actual mechanism, not just the surface error.

- Bad: "A bug in the reconnect logic."
- Good: "The trader-daemon's reconnect loop didn't reset its backoff counter on a successful connection. After one transient failure at 14:23, the counter stayed at 5-minute intervals indefinitely, so subsequent disconnects took 5+ minutes to recover instead of <1s."

## Fix

What was changed to resolve THIS incident. File paths, commands, config edits, commit SHAs. The immediate fix only — structural prevention belongs in `## Derived changes`.

## Evidence

- {{Log file path with relevant time range}}
- {{Commit SHA / PR URL of the fix}}
- {{Dashboard screenshot, canned op output, reproduction step}}
- {{Test or verification that confirms fix}}

## Derived changes

Filled at close-time by the 3-question gate (Knowledge / Invariant / Runbook). Each answer is either a concrete artifact path OR an explicit skip with reason.

- **Knowledge**: {{knowledge/<topic>/<slug>-digest.md, or 'skipped — <reason>'}}
- **Invariant**: {{INV-NNN added or strengthened, or 'skipped — <reason>'}}
- **Runbook**: {{runbook/<component>.md updated, or 'skipped — <reason>'}}

## Notes / open follow-ups

- {{anything else — future watch items, related risks, soft signals to monitor}}
