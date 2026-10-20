# ADR-008 — OpenCode is a first-class Perry host

> Status: active
> Type: Design
> Date: 2026-08-19
> Deciders: Ran Jiao — requested OpenCode support on 2026-08-19
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

DESIGN-003 decision 8 deliberately limited Perry to Claude Code and Codex CLI.
Its revisit trigger was explicit: add a third host when a user reports Perry
failing on one and the capability matrix is cheap to extend.

On 2026-08-19 the user ran Perry inside OpenCode. Perry loaded the skill but
misidentified the host as Codex, refused the native subagent executor, did not
know OpenCode's skill installation paths, and translated structured questions
using the wrong tool contract. The revisit trigger was met by an observed
failure, not by speculative portability work.

## Options

1. Keep Claude Code + Codex only and require OpenCode users to use `codex exec`.
   Rejected: Perry already loads natively in OpenCode, so refusing its Task and
   question tools turns a detectable adapter gap into a permanent limitation.
2. Treat OpenCode as Claude Code. Rejected: tool names and contracts differ;
   OpenCode uses `question`, `Task(subagent_type: general)`, and synchronous
   Task completion.
3. Add an explicit OpenCode host adapter and native executor. Chosen.

## Chosen

- Host token: `opencode`.
- Native executor: `opencode-subagent`.
- Native subagents run through synchronous `Task(subagent_type: general)`.
- Structured choices use OpenCode `question`; Claude's `multiSelect` maps to
  OpenCode's `multiple`.
- Global and project skill locations are
  `~/.config/opencode/skills/perry` and `.opencode/skills/perry`.
- Codex remains an optional executor on every host.
- Runtime detection precedence is explicit override, Codex runtime sentinels,
  OpenCode sentinels, Claude sentinels, then parent process. `CODEX_HOME` is not
  a runtime sentinel.

## Consequences

- Host capability documentation and dispatch procedures carry a third branch.
- `perry-dispatch-limit` enforces a separate OpenCode executor cap and one
  active dispatch per task across all executors.
- OpenCode Task writes `in_progress` before the synchronous call, so an
  interrupted parent leaves observable state.
- Setup supports both global and project-local OpenCode installation without
  writing `opencode.json`.
- Every new host must add detection, installation, executor lifecycle and
  contract tests; “reads SKILL.md” alone is not support.

## What would reopen this

- OpenCode changes or removes the `question` or `Task` contracts.
- Native Task gains a stable asynchronous completion contract worth adopting.
- A fourth host exposes a common adapter interface that makes the three
  host-specific branches unnecessary.
