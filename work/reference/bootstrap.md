# Bootstrap work state

Read the root first-run procedure and `kernel.md`. For a genuinely new project,
obtain its root/layout/language and high-stakes decisions before creating state.
The root router owns configuration. This lane owns task/ask/risk items and work
documents, never the goals/decide files.

## Procedure

0. Follow the root first-run collision, preference and high-stakes procedure.
   Record new preferences as ordinary prose through the root owner; existing
   configuration JSONL remains frozen metadata. Do not invent a config writer.

1. Inspect the project hook and obtain its high-stakes boundary agreement.

2. **Create state files under the agreed state root**:
   - Work documents: `evidence/`, `weekly/`, `handoff/`, `inputs/`, `knowledge/`.
   - **not** `decisions/` or `design/`; only decide creates those.

3. Run kernel `init` with the agreed state_root and actual actor, then apply the parsed
shipped process template. Read `template show` and query the types this lane owns to verify
the result. A missing store on an existing project is a migration condition, not
permission to initialize over history. Never restore work state by hand-editing
exports or copying a database that is bound to a rehearsal anchor.

Do not create legacy task, ask, risk, intake or cadence registers, a board or daily
journals. Existing projects use the reviewed reconciliation/switch plan. Retain
old documents as history and export the kernel state using its own command.

<!-- next-close: work bootstrap -->
