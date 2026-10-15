# Work state and document ownership

Current task/ask/risk state lives only in the kernel store. Use `kernel.md` for
queries, mutations, relations, events, attachments and export. The store is resolved
by the kernel across worktrees; never duplicate it inside a checkout or edit SQLite.
The deterministic export is a recovery artifact, not another writer surface.

Work owns evidence, weekly reports, handoffs, knowledge documents, PROJECT_STATE
narrative and its declared role cards. Goals owns OKR and phase documents. Decide
owns designs and ADRs. Read across lanes; ask before writing across ownership.

Keep user-facing documents within their declared caps. Put detailed evidence in
linked documents rather than repeating live counts. A narrative snapshot states
its date; current status comes from query. The old JSONL registers and journals
are frozen historical inputs until final disposal. The work lane does not append
journal status changes, create intake/cadence records, or maintain stages/WIP/SLA.

## Two file models

Structured current state is held by kernel items/events. Authored narrative and
source evidence remain documents. Audience caps and ownership still apply as
specified in `work/SKILL.md § Axis B`; old journal files are retained history.
