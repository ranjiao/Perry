# Perry hook — {{project_name}}

> User-owned project preferences and explanations. The root Perry procedure
> authors agreed edits; lanes read freely and request changes through the root.
> This hook adds project requirements and never weakens shared safety rules.

## High-stakes operations

The canonical machine-readable policy is `.perry/safety.json`. Review its proposal
from `templates/internal/safety_POLICY_TEMPLATE.json` against actual operations
and existing project boundaries. Record the actual user decision in approval_ref;
an empty reference remains unarmed. Hook prose/backticks are not the machine list.
Role rules add to the project policy; they cannot remove a project restriction.

### Domain boundaries to review with the owner

The following conservative proposals are not an armed policy. Review every
applicable boundary and carry it into the structured policy; preserve all
existing restrictions. Never delete a restriction merely because this task does
not use it. A matching string does not authenticate consent.

- Production deploys — `deploy`, `deploys`, `deploying`, `release`, `releases`, `promote`, `production`, `prod`
- Credentials and secrets — `.env`, `secret`, `secrets`, `credentials`, `token`, `tokens`, `apikey`, `api_key`, `id_rsa`
- Infrastructure and cloud state — `terraform`, `helm`, `k8s`, `infra/`, `iam`
- Money — `cost ceiling`, `paid API`, `billing`, `invoice`, `payment`, `refund`, `pricing`
- Destructive data operations — `DROP TABLE`, `migrate --down`, `rm -rf`, `rm -fr`, bulk delete, restore-over
- Anything sent on the user's behalf — `publish`, `publishes`, `publishing`, `published`, `send`, `sends`, `sending`, `sent`, `email`, `slack`, `post`, `posts`, `posting`, `client`, `filing`, `submit`, `submits`, `submitting`
- Git history rewrites — `push --force`, `rebase` onto a shared branch, tag deletion

## Project specifics (optional — delete what you don't use)

If the project is **{{project_name}}**:
- Roadmap source-of-truth: {{file at the project root, or —}}
- Prefer MCP tools: {{list of mcp__*__tool names, or —}}
- Decision tag types: {{Process | Architecture | Tooling | … or leave default}}
- Cost ceiling source: {{file or section naming the spend cap, or —}}
- Special agents available: {{— · roles are declared as cards in `.perry/roles/`}}
- Promotion / staging path: {{ordered stages before "shipped", or —}}

## Autopilot defaults (optional)

> Recognized by `work/reference/autopilot.md`. Omit the section to use the
> skill defaults (10 dispatches / 2h / 3 failures).

```
Autopilot defaults:
- max_dispatches: 10
- max_duration_min: 120
- max_failures: 3
- excluded_tasks:
```


## Native project preferences

- Document root: {{agreed narrative root; not a new database location}}
- Document/chat languages: {{actual preferences}}
- Packs: {{explicit list; [] means none, absence selects software-ops}}
- Workflow conventions: {{selected modes by workstream; no undeclared native fields}}

Current state is queried through the native CLI. This hook holds preferences,
not live task/goal counts, a second risk register or a session token ceiling.
For procedures and constraints read `$PERRY_HOME/reference/config.md` and
`$PERRY_HOME/reference/safety-policy.md`. Optional profiles are interpreted by
the Agent and do not schedule work or authorize external actions.
