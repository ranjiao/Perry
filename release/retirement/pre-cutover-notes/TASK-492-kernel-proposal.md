# Bounded proposal: reserve a prefix floor on an activated store

Status: proposal only; no kernel or target change in TASK-492.

Existing contracts: `item create` mints ceiling + 1; `import` refuses a
nonempty store; §5.7 explicitly says no command emits `ceiling:<prefix>`.
Consequently a sparse set of issued legacy filenames cannot always be appended
without either reusing an issued ID or fabricating placeholder items.

Smallest proposed extension: optional `ceilings` map on existing `template apply`
input, outside the template object. Keys must name declared prefixes; values
must be nonnegative SQLite-range integers. In one transaction validate template
compatibility and monotonically raise each floor. Existing/equal/lower floors
are no-ops (never lower them); changed floors append ordinary `ceiling:` changes.
Same-version identical-template + raised floor must write rather than returning
early. The event must retain import/replay's rule against mixing template and
item changes. Support actor, note, dry-run and refusal rollback. No new concept,
command group, guard, field kind, legacy reader, or special ADR vocabulary.

Approval requires updating kernel §5.6/§5.7, declaration, implementation, replay
checks and focused tests for same-version raise, unknown prefixes, range/type
errors, concurrency, dry-run, export/import, and non-regression of work events.
This requires root/user authority under locked DESIGN-023 §7.

For the measured Perry source all ADR-001..ADR-027 files exist; importing every
real record in numeric order mints the exact IDs and reaches floor 27 naturally.
SkyTonight has no ADR filename and rehearses with existing primitives. Perry
has DESIGN-001..017 and DESIGN-019..023, so its actual DESIGN-018 hole requires
the generic floor extension to preserve all filename identities. A floor of 18
just before creating the real DESIGN-019 suffices; final ceiling is 23. This is
an actual Perry rehearsal blocker, not a hypothetical requirement. The adapter
plans all records but refuses apply before changing the store while this gap
remains. No placeholder item or direct SQLite/event write is permitted.
