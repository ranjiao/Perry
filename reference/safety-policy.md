# Structured high-stakes policy

The project policy lives in `.perry/safety.json`, owned by the root procedure.
It is skill data, never a kernel command or a semantic classifier. Hook prose
explains intent; backticked prose no longer supplies the machine list. Role
escalation rules can only add to the project policy.

Use `state/safety_POLICY_TEMPLATE.json` as a proposal, review the actual project
operations and preserve every existing boundary when migrating. Restore database
operations for a SQLite-backed project. Do not silently prune a rule because the
current task does not use it. Record the actual reviewed decision in
`approval_ref`; an empty reference keeps the policy unarmed. A field value alone
cannot prove that consent occurred. Never fill it with an invented human action.

The JSON has exactly `version: 1`, `approval_ref` and nonempty `rules`. Each rule
has a unique `id`, a human `label` and nonempty single-line literal `patterns`.
Patterns are case-insensitive, matched at word boundaries; they are not regular
expressions. The helper screens scope/spec text but cannot distinguish quoting
an operation from executing it. The agent reads the actual spec, project policy,
hook and role rules and records the scope-specific judgment. Existing explicit
user authority persists; do not request it again for the same action.

`tools/safety_policy.py` validates the actual project-owned regular file.
`tools/document_checks.py dispatch --input <packet>` requires an absolute project
`root` and loads that root's policy; the packet cannot replace it with hook text.
It reports the policy path and SHA256. Missing/unreviewed/empty/malformed policy,
foreign paths, unresolved ownership or missing criteria stop automated dispatch.
For a high-stakes match the recorded authorization must name the actual session
instruction; shape success is not permission. Autopilot skips matched operations
and refuses to start under an unarmed policy.

First setup shows the proposed list before installing it. Existing projects
review a concrete old→new policy table during cutover, including restored database
rules; no policy or user hook is changed by running the read-only helper. Changes
to the gate itself follow the same user-owned policy boundary. A source candidate
or a passing test is not acceptance of a live policy edit.
