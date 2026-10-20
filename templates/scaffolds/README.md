# Standalone project scaffolds

These starting points work without Perry or its native store. Copy only the
selected files, replace every placeholder and verify the project's actual
commands. No command automatically creates a project from this directory.

| Scaffold | Smallest useful content | Verification |
|---|---|---|
| [software/](software/) | Rules, short state and durable decisions | Use the project's real tests/build; no language or engine is assumed |
| [knowledge-base/](knowledge-base/) | Catalog, immutable sources and authored pages | `bin/kb-lint` checks links, reachability, citation presence and duplicate titles |
| [ops/](ops/) | Requests and deliverables; procedures/incidents when needed | `bin/deliverable-lint` checks document structure and recorded sign-off shape |

A linter checks observable shape. It does not prove a cited source supports a
claim, a deliverable works, or a human actually approved release. Verify those
against actual evidence and authorization. Neither linter publishes anything.

## Reuse in a native Perry project

| Standalone file | Native Perry handling |
|---|---|
| `AGENTS.md` | Read and adapt useful commands/domain rules into the project's existing instructions; preserve its native startup and ownership rules |
| `STATE.md`, `INTAKE.md` | Do not copy as current registers; use native tasks/asks/risks and an optional dated narrative |
| `DECISIONS.md` | Do not create a parallel decision registry; decide owns native ADR/design items and reasoning attachments |
| `journal/` or activity logs | Do not use for task/status events; native events own that history. A knowledge ingestion log may describe source/content changes |
| `wiki/`, `raw/`, `index.md`, deliverables, runbooks, incidents | Reuse selected artifact patterns with agreed ownership, exact paths and collision checks |
| `bin/kb-lint`, `bin/deliverable-lint` | Optional artifact checks; review their directory assumptions and limitations before installing |

Start with one writer per shared file or explicit edit coordination. Append-only
text does not make simultaneous file writes or branch merges conflict-free.
Retain approved prior entries; record corrections and supersession explicitly.

For type-specific combinations and adoption steps, use the
[new-project guide](../../reference/new-projects.md).
