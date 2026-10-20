# Perry — your virtual project office

[中文](README_cn.md) · [Install and update](INSTALL.md)

Perry is one Agent skill for planning goals, managing work and recording decisions.
It supports Claude Code, OpenCode and Codex CLI. The Agent supplies the method and
judgment; a small local kernel records structured project state.

## What Perry does

| Lane | Use it for |
|---|---|
| `goals` | Objectives, key results, measurements and phases |
| `work` | Tasks, dependencies, questions, risks and verification evidence |
| `decide` | Design discussions, approved designs and architecture decision records |

These are three lanes inside the one `perry` skill. You do not install three
separate skills. Modes describe how work progresses; optional packs add domain
procedures. They do not add background workers or authorize external actions.

## Get started

The installation guide covers macOS and Linux. Native Windows installation has
not been verified.

1. Install Python 3.11 or newer, Git and a supported Agent host. Perry's Python
   code uses only the standard library; no `pip install` is required.
2. Follow [installation](INSTALL.md). Choose a published release when available,
   or explicitly choose the development source on `main`. Installing the skill
   links its source folder into the host; it does not initialize a project.
3. Open **your own project directory** in the host and load `perry`. Ask it to
   set up a new project or inspect an existing one. In Claude Code, `/perry` is
   the entry point; other hosts use their own skill invocation.

For example: “This is a new research project. Help me choose a minimal structure
and set up Perry. Keep the project documents in Chinese.” The Agent first checks
existing files, agrees the layout and boundaries, then initializes only what is
needed. See the [new-project guide](reference/new-projects.md).

The Perry source checkout is the installed tool, not the template for your
project. Its `perry/` directory contains Perry's own development records.

## Existing projects and storage

Existing Markdown/JSONL projects need a reviewed migration plan. Updating the
installed skill, applying a process template or opening a project in a viewer
**does not migrate its data**. See [existing projects](INSTALL.md#existing-projects).

Native items, relations and events live in SQLite. Git worktrees share the store
in their common Git directory; projects without Git use `.perry/perry.db`.
Markdown holds explanations and evidence under the agreed document root.
Kernel-generated JSONL exports support backup and review. A normal Git commit
of the project does not include the SQLite store under `.git`; export the state
and back up the referenced documents when preserving a project.

## For developers

`bin/perry` is the native JSON CLI, distinct from commands typed to an Agent.
Run `bin/perry --help` or `bin/perry describe`; helpers live under `tools/`.
The old `perry-task`, `perry-state` and `perry-goals` commands are retired.

`bash tests/run` runs the native kernel and helper suite;
`bash tests/run --tier slow` adds isolated Git integration self-tests. These
check source behavior, not a user's project migration or human acceptance.

[Architecture](ARCHITECTURE.md) · [Native contract](reference/kernel.md) · [Project-neutral design](reference/design-principles.md) ·
[Tool helpers](tools/README.md) · [Maintainer release rules](release/README.md)

## Repository layout

| Paths | Purpose |
|---|---|
| `bin/`, `kernel/` | CLI entry point and generic state engine |
| `SKILL.md`, `goals/`, `work/`, `decide/` | Agent router and the three lanes; lane procedures and narrative templates |
| `reference/`, `modes/`, `packs/` | Shared rules, work modes and domain procedures |
| `templates/` | `scaffolds/` for standalone artifacts, `process/` for native process data, `internal/` for Perry workflow and policy templates |
| `tools/`, `tests/` | Skill helpers and their tests; kernel tests stay in `kernel/` |
| `release/` | Version records, publication tools and historical retirement records |
| `perry/`, `.perry/` | Perry's own development documents, evidence, exports and project preferences; not files to copy into a new project |
