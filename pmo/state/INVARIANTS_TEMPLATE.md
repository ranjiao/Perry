# Architecture invariants

> Last reviewed: {{YYYY-MM-DD}}
> Active count: 0
> Project: {{project name}}

Mechanical, checkable rules about this codebase or its operation. Differs from `OKR.md` Operating Principles (aspirational) by being **enforceable** — every active invariant should have a `Check:` field that can be run.

See `pmo/reference/architecture.md` for the full procedure: how to add, supersede, retire, audit, and how dispatch consumes the `Touches invariants:` field.

## Status legend

- `active` — currently enforced; checked by `/pmo audit`.
- `superseded` — replaced by a newer INV-NNN; kept for history. Links to replacement.
- `retired` — deliberately dropped (reason recorded inline). Not checked.

## Severity legend

- `hard` — dispatch refuses any task touching this invariant unless user explicitly waives with a written reason.
- `soft` — dispatch warns and asks for acknowledgement once.

---

<!-- Add invariants below this line. Use `/pmo invariant add` for the interactive flow. -->

<!--
## INV-001 — Short one-line title

- **Status**: active
- **Severity**: hard
- **Rule**: One paragraph explaining the rule. Should be precise enough that a stranger reading this file can tell whether the code complies.
- **Check**: `<runnable command — grep / lint / find — non-zero exit on violation>`
- **Added**: YYYY-MM-DD (source: ADR-NNN | incident YYYY-MM-DD-slug | manual)
- **Rationale**: Why this is a hard rule, not just a preference. Often references a past incident or a structural risk.
- **Known exceptions**: (none) | <list with date and reason for each>
-->
