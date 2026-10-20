# Native process templates

[perry.json](perry.json) is Perry's shipped process data. The native kernel
validates and applies the JSON object with `template apply`; an agreed new
project first uses `init`. Exact inputs and compatibility rules come from
`bin/perry describe` and [the native contract](../../reference/kernel.md).

This directory is not copied into a project's document root. The applied
version lives in the store. Modes, packs and prose are interpreted by the Agent;
they do not automatically add native types, fields, state machines or guards.

The same template serves software, research, knowledge and operations projects.
Choose only the items needed now. A pipeline stage or commitment that is not a
declared field remains an explicit narrative convention, never an invented API.
Change process data only within the existing kernel contract and review its
compatibility. Do not create a template variant for every domain by default.

New projects: follow [first-run](../../reference/first-run.md). Existing document
projects need an agreed mapping and reconciliation; applying this JSON alone
does not migrate their records. Never initialize over an existing or missing
migration-era store, edit the database directly or replace it with a rehearsal.
