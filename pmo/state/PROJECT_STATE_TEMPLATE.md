# PROJECT_STATE — {{project_name}}

> Living dashboard. Edited by the `pmo` skill on every standup. Keep < 300 lines.
> The Month-Level board lives in `TASKS.md`; this file is for cross-monthly state.

## Snapshot

- **Phase**: {{phase}}                    <!-- e.g., Phase 1 system-build -->
- **Current month**: {{YYYY-MM}}
- **Current ISO week**: {{YYYY-WW}}
- **Started**: {{start_date}}
- **Last standup**: {{last_standup_date}}
- **Latest handoff**: {{handoff/<YYYY-MM-DD>.md if any, else —}}

## Active OKR pointer

- Overall: `OKR.md` v{{N}}, period {{period}}, {{days_elapsed}}/{{days_total}}d.
- Monthly: `monthly/{{YYYY-MM}}.md`, week {{n}}/{{weeks_in_month}}.

## Risks

> Format: severity (H/M/L) · description · owner · mitigation · status. Triaged via `pmo risk`.

- [ ] H · {{risk}} · {{owner}} · {{mitigation}} · open
- [ ] M · {{risk}} · {{owner}} · {{mitigation}} · open

## Recent cross-session work

> Most recent first. Each entry: date · session id/name · 1-line summary · output evidence path.

- {{date}} · {{session}} · {{summary}} · {{evidence path}}

## Carry-over watch

> Tasks that have rolled over from previous months. Each carry-over should also exist in `TASKS.md`.

- {{TASK-ID-from-previous-month}} → {{new TASK-ID}} · {{1-line reason for carry-over}}

## Notes

<!-- Free-form context that doesn't fit elsewhere. Prune ruthlessly. -->
