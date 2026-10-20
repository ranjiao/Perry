# ADR-{{N}} — {{Title in configured document language}}


Native item: {{kernel_item_id}}. Current type, lifecycle, date, supersession
and sunset metadata are read from that item. This attachment preserves the
reviewed decision, rationale, consequences and sources; attach its exact bytes.

## Context

<!-- Why this decision needs to be made. Observable facts driving it. Write in the configured document language. -->

## Options

1. **Option A — {{name}}**
   - Pros: ...
   - Cons: ...
2. **Option B — {{name}}**
   - Pros: ...
   - Cons: ...
<!-- Include anti-pattern / rejected options when useful for the audit trail. -->

## Chosen

**{{Option label}}** — {{one-sentence rationale}}

## Consequences

- {{what changes operationally}}
- {{what's now true that wasn't}}
- {{what's now off-limits / on-limits}}
- {{revisit triggers, if any}}

## Evidence

- {{PR URL / commit SHA / evidence file path / journal entry / chat decision quote}}
- ...

## Revisit rationale (when applicable)

{{Explain observable expiry/revisit conditions and their evidence. Record current
sunset metadata on the native ADR item; interpretation and a user-authorized
expire action follow the decide procedure. No automatic file/status writer.}}

Native events preserve supersede/expire/archive history. Keep prior approved
reasoning intact; update narrative only for an explicit reviewed rationale change.
