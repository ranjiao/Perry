## Context

DESIGN-023 decisions 2 and 13 replace the work lane's JSONL current-state
registers with the kernel store. ADR-025 schedules this record at phase E,
when the new store begins to govern work. Goals and decide remain on their
existing writers until their separately scoped cutover.

## Options

1. Keep rewritten legacy registers and disposable history (ADR-006).
2. Use one kernel SQLite store per project anchor, with replayable events and
   deterministic JSONL exports (DESIGN-023, chosen).

## Chosen

For work items, SQLite items are current state and SQLite events are history.
Events are required for a verified replay/import; they are no longer disposable.
The store is resolved under the Git common directory at perry/<anchor>.db,
with root.db for a top-level anchor, shared across repository checkouts.
Outside Git, it is <anchor>/.perry/perry.db. There is no project registry.
The kernel owns resolution and transactions; callers use its CLI.

## Consequences

- The work lane writes tasks, asks, risks, relations, fields and attachments
  through the kernel. Its old registers and journal are frozen history.
- Export writes items.jsonl and events.jsonl under <state root>/export.
  Import verifies replay and refuses nonempty stores. Export is a recovery
  artifact, never a second writer or current-state authority.
- Recovery protects the database and events together. Restore from the
  validated export; do not recover by dropping history or copying a database
  bound to a rehearsal anchor.
- ADR-006 is superseded at the actual work cutover. ADR-019's one-copy principle
  holds, with the kernel-defined database location for work. Final folding of
  ADR-012/ADR-014 and amendment of ADR-019 remain phase F/H work under ADR-025.
- This does not assert that goals, decide or the root legacy dashboard have
  already migrated. Their separately scoped migration remains pending.

## Evidence

- perry/design/DESIGN-023-a-kernel-and-a-skill.md, decisions 2 and 13; sections 5.3 and 5.4.
- perry/decisions/ADR-025-earlier-designs-reconciled-with-design-023.md.
- TASK-490; its final cutover receipt supplies the live import hashes and sequence.

## What would reopen this

A verified export cannot reproduce the live item/event state, different
checkouts resolve different stores for the same anchor, or a consumer needs
to bypass the CLI to obtain current work state.
