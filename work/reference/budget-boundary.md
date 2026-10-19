# Session usage and optional handoff

## Session ownership

The agent environment and the user decide when to start a new session. Perry
sets no session token ceiling and does not stop, refuse dispatch/review, or
require a handoff because of token usage or unavailable telemetry.

`bin/perry-context-budget` is an optional, read-only usage report. A measured
figure is not a continuation verdict. Unknown identity or usage stays unknown;
it does not require a user decision. Old session-ceiling settings and environment
variables do not control work. An explicit legacy `--ceiling` is a comparison
reference only. Task counts, duration/failure budgets and safety gates retain
their separately agreed scope.

## Optional handoff

When the user or agent environment chooses a handoff, finish the atomic step in
hand first. Let a kernel mutation return, retain its evidence, and never leave a
mutation unrestored. Record in-flight task/branch/checkout/log paths as pending;
do not stop other agents merely because this session is handing off.

Fill the handoff template's `§ 0 Resume point` (≤ 8 KiB, evidence by path, no
pasted logs). A handoff is useful for continuity, not mandatory at a token count.

Before resuming from a handoff: run recovery/interrupted gates; compare recorded
checkout heads and the main tip; query the named native tasks; refresh stale
checks before relying on them. Never resume a pending transaction or interrupted
pipeline automatically. Perry does not reset the host or open a session itself.
