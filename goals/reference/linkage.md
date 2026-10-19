# Native attribution

Read `reference/okr-linkage.md`. Resolve in order: explicit native task→KR link
or migrated KR work_items; exact scoped Project ID; user-confirmed exact alias.
Never fuzzy-match a title. A legacy label requires its version/phase. Zero or
multiple candidates means ask with candidates and keep the work visibly unlinked.

`item get`/`query` supplies IDs, types and seqs. `rel add` with `contributes_to`
from task to KR records new approved attribution. Use current `expect` on both
ends; do not silently delete another session's new relation. Goals owns this
attribution; work proposes it. Adding a relation advances both item seqs, which
must be stated when reconciling preexisting snapshots.

The F importer instead puts typed task refs in the new KR's work_items so the
original task items, seqs and events remain byte-for-byte unchanged. Treat those
refs as explicit attribution with the source scope, never as extra work items
or a reason to double-count tasks that also have a new relation.

Phase project_registry, unlinked_tasks and agent_assignments are lists of exact
serialized legacy declarations retained as method data, not inferred task facts.
Read each declaration with its phase; IDs/aliases resolve only when exactly one
KR is declared. A confirmed alias update uses `item update` on the phase's
project_registry with fresh expect, preserving existing entries and the reason.
A new declaration uses the same representation; an alias already claimed by a
different Project refuses until the user resolves it. An unlinked declaration
records task, phase, actor/time and reason; it is not rolled into metrics.
Never assume a legacy unlinked declaration overrides a later explicit link.

A Project carried into a new phase retains its exact ID and confirmed aliases,
with its new approved KR. Do not infer a carry-over or copy old unlinked work.
Agent assignments are attribution context, not evidence of a running process.
Re-query after writes; report minted IDs, changed links and unresolved items.
No `linkage.jsonl` append, manual table update, journal write or legacy event.
