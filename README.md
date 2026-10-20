# Perry — your virtual project office

Perry is one skill for Claude Code, OpenCode and Codex CLI. Use `/perry` for a
project snapshot, `/perry goals` to plan, `/perry work` to execute, and
`/perry decide` to develop and record decisions.

The skill supplies the method. A small native kernel stores structured items,
relations, events and attachments in one local SQLite store per project anchor,
shared across its worktrees. Markdown holds explanations and evidence. A
deterministic JSONL export provides a backup and review surface.

The native architecture is integrated. Perry's own project and SkyTonight completed
local cutover and named human acceptance on 2026-10-20; see the
[cutover record](perry/evidence/2026-10/TASK-494-formal-cutover-20261020/FINAL.md).
The finite [retirement ledger](release/retirement/README.md) remains an immutable
source proposal inventory, separate from actual approval records. It is not a
current blocker list. Public release availability follows the installation rules.

[Install and update](INSTALL.md) · [Architecture](ARCHITECTURE.md) ·
[Native contract](reference/kernel.md) · [Tool helpers](tools/README.md) ·
[Maintainer release rules](release/README.md)

For developers, `bin/perry` is the only executable in `bin/`. Run `bin/perry --help`
or `bin/perry describe` for its native JSON contract. Skill helpers live under
`tools/`; old `perry-task`, `perry-state`, `perry-goals` and forwarding commands
are retired. No compatibility CLI is retained.

The source is standard-library-only. `bash tests/run` runs the new native/helper
suite; `bash tests/run --tier slow` adds integration harness self-tests. An
independent integrator tests the actual combined tree before acceptance; the new
suite does not claim equivalence to the deleted typed-state test corpus.

## Repository layout

| Paths | Purpose |
|---|---|
| `bin/`, `kernel/` | Thin CLI entry point and generic state engine |
| `SKILL.md`, `goals/`, `work/`, `decide/` | Agent router and three method lanes; each lane owns `reference/` procedures and `templates/` narrative starting points |
| `reference/`, `modes/`, `packs/` | Shared procedures/native contract, work modes and domain guidance (including pack-specific templates) |
| `templates/` | `scaffolds/` for standalone artifacts, `process/` for native process data, `internal/` for Perry workflow/policy templates |
| `tools/`, `tests/` | Skill helpers and their verification; kernel tests stay with the kernel |
| `release/` | Version history, publication tools and historical source retirement records |
| `perry/`, `.perry/` | This repository's dogfood documents, evidence, export and local configuration; current structured state lives in the kernel store |

Historical project records and cutover backups are retained for traceability.
Generated Python caches and retired placeholder directories are not part of the
source layout. Host-specific settings stay separate from Perry runtime state.

For a new project, use the [project organization guide](reference/new-projects.md)
to select state ownership, a work mode, domain packs and useful scaffold files.
