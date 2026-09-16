# TASK-462 — proposed architecture component entry

The full merged-preview suite identified release/ as a new component absent
from ARCHITECTURE.md section 2. The architecture document reserves its edits
to the user; the implementation spec did not authorize changing it.

Proposed addition to section 2, with all existing boundaries unchanged:

```markdown
### `release/` — Perry product versions and releases
- **Purpose**: maintain Perry's own product versions and verified release updates.
- **Owns**: typed release records, deterministic VERSION/CHANGELOG projections,
  integration checks and explicit publication of an exact tested commit.
- **Doesn't own**: the versions or state of projects managed by Perry, the
  meaning of authored change notes, or the user's decision to raise a major version.
- **Procedure**: [`release/README.md`](release/README.md).
```

No schema, claim, ownership transfer, compatibility contract or existing
non-negotiable changes. The addition describes the approved implementation.
