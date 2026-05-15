# Runbook — {{component-slug}}

> Component: {{Display name}}
> Owner: {{user | named agent | team}}
> Status: active | deprecated | archived
> Tier 1 hard cap: ≤ 150 lines. Overflow → split troubleshooting matrix to `runbook/{{component-slug}}-troubleshooting.md`. Keep this main file's four mandatory sections (What / Healthy / Failures / Escalation) in canonical short form.
> Created: {{YYYY-MM-DD}}
> Last verified: {{YYYY-MM-DD}}
> Linked spec: evidence/{{YYYY-MM}}/{{TASK-ID}}-spec.md
> Linked architecture sections: {{§N references in ARCHITECTURE.md, or '(none)'}}

## What it does

One paragraph. What this component is, what triggers it, what state it touches. Written for someone who didn't read the code — concrete and factual, no marketing.

Example shape: "Runs as a cron job every 5 minutes during US market hours (13:30–20:00 UTC, Mon–Fri). Reads pending orders from `state/queue.db`, submits to broker via `live_trading/submit.py`, writes acknowledgements back to `state/queue.db`. Logs to `logs/trader.log`."

## How to tell it's healthy

Concrete checks. Each line should be runnable in <30 seconds, no source-reading required.

- `<command>` → expected output pattern
- Log file `<path>` should show entries every <interval>; grep `<pattern>`
- Metric/dashboard `<URL>` healthy range: <range>
- Endpoint `<URL>` returns shape <description>

## Common failures + canned ops

For each known failure mode: symptom + diagnose command + fix command. Both runnable by the user.

### {{Failure mode 1}}
- **Symptom**: {{what the user sees in chat, in logs, on the dashboard}}
- **Diagnose**: `{{single command}}`
- **Canned fix**: `{{single command, or named op like Telegram /restart_trader}}`
- **If fix doesn't work**: see Escalation.

### {{Failure mode 2}}
- **Symptom**: ...
- **Diagnose**: ...
- **Canned fix**: ...

<!-- Add new failure modes as incidents reveal them (see /pmo incident close 3-question gate). -->

## Escalation

When canned ops fail, in order:

1. {{First diagnostic step the user takes}}
2. {{Who/what to invoke — usually `/pmo incident <slug>` to open a postmortem record}}
3. {{Worst case: shutdown command — exact syntax}}

## Change log

- {{YYYY-MM-DD}} — created from {{TASK-ID}}
- {{YYYY-MM-DD}} — verified by user; still accurate (bumps Last verified)
- {{YYYY-MM-DD}} — {{what changed and why; link to source incident if relevant}}
