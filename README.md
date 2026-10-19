# Perry — your virtual project office

Perry is one skill for Claude Code, OpenCode and Codex CLI. Use `/perry` for a
project snapshot, `/perry goals` to plan, `/perry work` to execute, and
`/perry decide` to develop and record decisions.

The skill supplies the method. A small native kernel stores structured items,
relations, events and attachments in one local SQLite store per project anchor,
shared across its worktrees. Markdown holds explanations and evidence. A
deterministic JSONL export provides a backup and review surface.

This tree is the **DESIGN-023 H retirement source candidate**. It is reviewable
implementation, not a record of live activation or user acceptance. The finite
[retirement ledger](release/retirement/README.md) includes proposed drops and
consumer blockers. Existing project documents and state are preserved.

[Install and update](INSTALL.md) · [Architecture](ARCHITECTURE.md) ·
[Native contract](work/reference/kernel.md) · [Tool helpers](tools/README.md) ·
[Maintainer release rules](release/README.md)

For developers, `bin/perry` is the only executable in `bin/`. Run `bin/perry --help`
or `bin/perry describe` for its native JSON contract. Skill helpers live under
`tools/`; old `perry-task`, `perry-state`, `perry-goals` and forwarding commands
are retired in this candidate. No compatibility CLI is retained.

The source is standard-library-only. `bash tests/run` runs the new native/helper
suite; `bash tests/run --tier slow` adds integration harness self-tests. An
independent integrator tests the actual combined tree before acceptance; the new
suite does not claim equivalence to the deleted typed-state test corpus.
