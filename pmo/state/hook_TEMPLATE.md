# Perry hook — {{project_name}}

> **Tier 1** (user-read-and-edit). Written once at PMO bootstrap, then owned by you.
> Hooks are **pure additions** to Perry's generic behavior — they never override a core rule.
> Read at every standup by `/pmo`, `/okr`, `/design`.

## High-stakes operations

> **This section is a safety gate, not documentation.** `/pmo dispatch` scans
> every spec's `Files in scope` / `Deliverable` against this list and refuses on
> a match; `/pmo autopilot` skips matching rows outright and **refuses to run at
> all if this list is empty**. An empty list does not mean "nothing is
> dangerous" — it means the gate has nothing to match, so Perry treats it as
> unarmed.
>
> The defaults below are deliberately conservative. Delete what genuinely does
> not apply to this project; add anything an agent must never touch unattended.
> Each line is matched case-insensitively as a substring against spec fields, so
> prefer concrete path fragments and command names over prose.

- Production deploys — `deploy`, `release`, `promote`, `production`, `prod`
- Credentials and secrets — `.env`, `secrets`, `credentials`, `token`, `apikey`, `api_key`, `id_rsa`
- Infrastructure and cloud state — `terraform`, `helm`, `k8s`, `infra/`, `iam`
- Money — raising a cost ceiling, adding a paid API, changing billing config
- Destructive data operations — `DROP TABLE`, `migrate --down`, `rm -rf`, bulk delete, restore-over
- Anything that sends outbound messages on the user's behalf — email, Slack, PR comments on other people's repos
- Git history rewrites — `push --force`, `rebase` onto a shared branch, tag deletion

## Project specifics (optional — delete what you don't use)

If the project is **{{project_name}}**:
- Roadmap source-of-truth: {{file at the project root, or —}}
- Prefer MCP tools: {{list of mcp__*__tool names, or —}}
- Decision tag types: {{Process | Architecture | Tooling | … or leave default}}
- Cost ceiling source: {{file or section naming the spend cap, or —}}
- Special agents available: {{roles beyond Coding / Research / Review, or —}}
- Promotion / staging path: {{ordered stages before "shipped", or —}}

## Autopilot defaults (optional)

> Recognized by `pmo/reference/autopilot.md`. Omit the section to use the
> skill defaults (10 dispatches / 2h / 3 failures).

```
Autopilot defaults:
- max_dispatches: 10
- max_duration_min: 120
- max_failures: 3
- excluded_tasks:
```

<!--
Other optional profile blocks, documented in pmo/reference/:
  ## Architecture profile   → architecture.md (eager ARCHITECTURE.md creation)
  ## Operational profile    → runbooks.md     (eager runbook/ creation)
  ## ADR conventions        → decisions.md    (override the default ADR types)
-->
