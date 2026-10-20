# Native-store amendments — ADR-026 / ADR-015 / ADR-019

Current metadata and typed relationships live in the native items. The original
ADR files stay frozen and keep their historical attachment hashes. This is a new
owned rationale attachment, authorized by DESIGN-023, ADR-025 and actual user
cutover approval2026-10-20; it does not establish another current-state table.

ADR-026 now carries the final structured-state medium for goals/decisions as
well as work. ADR-012 freshness responsibility is retained in native query/event
capture and explicit seq/hash evidence; stale snapshots do not invent facts.
ADR-014's non-reissued issued-number principle lives in native event-sourced
prefix ceilings and export/replay, including the explicitly approved sparse floor.

ADR-015 still gives each owned narrative one home; structured current metadata
is native and the narrative is attached, rather than a body generated from a
second structured header. ADR-019 still makes the canonical store the copy of
structured state. Its medium is SQLite plus replayable canonical events/exports;
legacy JSONL/headers are frozen historical inputs, not a second writer.

References: native ADR-028 and its activation evidence. These amendments change
the medium and boundaries already selected in DESIGN-023, not project goals,
phase criteria, unmeasured values, namespace ownership or human acceptance.
