# PROJECT_STATE — {{project_name}}

> Living dashboard. Edited by the `pmo` skill on every standup. Keep < 300 lines.
> The live work board lives in `BOARD.md`; this file is for cross-phase state.

## Snapshot

- **Current phase**: #{{NNN}} {{slug}}                    <!-- e.g., #002 cash-deployment -->
- **Phase started**: {{phase_start_date}}    ·    **Phase day**: {{N}}
- **Current ISO week**: {{YYYY-WW}}
- **Project started**: {{start_date}}
- **Last standup**: {{last_standup_date}}
- **Latest handoff**: {{handoff/<YYYY-MM-DD>.md if any, else —}}

## Active OKR pointer

- Overall: `OKR.md` v{{N}}.
- Current phase: `phase/{{NNN}}-{{slug}}.md` (resolve via `phase/CURRENT`).
- Last snapshot: `phase/snapshots/{{YYYY-MM-DD}}-{{NNN}}-{{slug}}.md`, {{Md ago}}.

## Risks

> Format: severity (H/M/L) · description · owner · mitigation · status. Triaged via `pmo risk`.

- [ ] H · {{risk}} · {{owner}} · {{mitigation}} · open
- [ ] M · {{risk}} · {{owner}} · {{mitigation}} · open

## Recent cross-session work

> Most recent first. Each entry: date · session id/name · 1-line summary · output evidence path.

- {{date}} · {{session}} · {{summary}} · {{evidence path}}

## Carry-over watch

> Tasks that have rolled over from previous phases. Each carry-over should also exist in `BOARD.md`.

- {{TASK-ID-from-previous-phase}} → {{new TASK-ID}} · {{1-line reason for carry-over}}

## Notes

<!-- Free-form context that doesn't fit elsewhere. Prune ruthlessly. -->
