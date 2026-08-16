# Extending PMO + per-project hooks

Loaded only when the agent is adding a new subcommand / feature, or configuring per-project behavior via `.perry/hook.md`. Not loaded on routine standup / triage / dispatch flow.

## Extending PMO (where new content goes)

When adding a new feature or refining an existing one, default to **`reference/<topic>.md`** rather than expanding `pmo/SKILL.md`. Update the **Subcommand index** in SKILL.md with a one-line pointer to the new reference, and add a row to `## How this file is organized`.

Rationale: every new line in `SKILL.md` is loaded on every PMO invocation; reference files are loaded only when the matching subcommand fires. Keeping `SKILL.md` small protects context budget for the actual project state.

If a new feature is broadly applicable (touches every standup, every reply), it does belong in `SKILL.md` — but rarely. When in doubt, write the detail to a reference file and link.

## Per-project hooks

`.perry/hook.md` is written at PMO bootstrap from `state/hook_TEMPLATE.md` and read at every standup. Its contents are pure additions to PMO's generic behavior, never overrides of the core rules — with one exception that is not optional:

> **`## High-stakes operations` is a safety gate, not configuration.** `/pmo dispatch` refuses any spec whose `Files in scope` / `Deliverable` matches a line in it; `/pmo autopilot` skips matching rows and **refuses to run when the list is empty** (`autopilot.md` pre-flight step 0). A project without the list has an unarmed gate, so bootstrap always writes the conservative default and asks the user to confirm it. Everything below this line is genuinely optional.

Check whether it's armed with `"$PERRY_HOME/bin/perry-state" --section project` (`hook.high_stakes_armed`); `bin/perry-lint` warns when it isn't.

### Block format

```
If the project is **<name>**:
- Roadmap source-of-truth: <file>
- Prefer MCP tools: <list>
- Decision tag types: <list>
- Cost ceiling source: <file or none>
- Special agents available: <list>
- Anything else specific.
```

### Skeleton example

```
If the project is **<your project name>**:
- Roadmap source-of-truth: <file at the project root, e.g., ROADMAP.md>.
- Prefer MCP tools <list of mcp__*__tool names> over guessing or asking
  when the user wants up-to-date numbers / state.
- Decision tag types: <Process | Architecture | Tooling | ... — pick the
  set that matches your project's vocabulary>.
- Cost ceiling source: <file or section that names the spend cap>.
- Special agents available: <list of agent roles you delegate to via
  `pmo delegate`, beyond the generic Coding/Research/Review trio>.
- Promotion / staging path (if any): <ordered list of stages a deliverable
  must pass through before being considered shipped>.
- High-stakes operations that REQUIRE user authorization: <list>.
```

For projects without a hook, the generic standup + subcommands work fine. Most solo / small projects don't need one until they have project-specific MCP tools or domain-specific decision categories.

## Other hook profiles

Beyond the generic block above, two more-specific profile blocks are recognized by other reference files:

- `## Architecture profile` block — see `$PERRY_HOME/packs/software-ops/architecture.md`. Drives eager creation of `ARCHITECTURE.md` at bootstrap.
- `## Operational profile` block — see `$PERRY_HOME/packs/software-ops/runbooks.md`. Drives eager creation of `runbook/` at bootstrap.
- `## ADR conventions` block — see `reference/decisions.md`. Overrides the default ADR type list.

All hook blocks are optional and additive.
