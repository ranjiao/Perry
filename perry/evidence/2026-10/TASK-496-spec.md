# TASK-496 — Remove Perry session-context enforcement

Date: 2026-10-19. Owner: Coding Agent. Required verification: V3.

## Authority

User: “去掉这个限制，由agent环境和用户自己决定什么时候开新session”. This explicitly authorizes removing the session gate, including its threshold, config/architecture references and workflow instructions. It does not remove unrelated task-count, duration, failure, review, safety or static byte-bill checks.

## Acceptance criteria

1. Any valid live/explicit/historical transcript, including >200000 tokens, returns a read-only usage report and exit0. No OVER verdict, required handoff, required new-session prompt or unknown-telemetry question blocks work.
2. No built-in, schema, environment or project-config session ceiling can reinstate the gate. A legacy explicit --ceiling argument may be accepted only as an optional, clearly advisory comparison; no default ceiling.
3. Transcript identity/provenance, usage totals/categories, coverage and unknown reporting remain accurate. Invalid invocations remain nonzero; static --bill checks keep their existing scope.
4. Active skill/config/host/tool documentation is consistent: session decisions belong to the agent environment and user. Handoff/resume safety remains available when chosen. Historic evidence remains historical.
5. Meaningful high-volume/current/explicit/unknown and stale-config regressions pass; final appropriate complete checks and diff check pass. Changes are independently reviewed/integrated, with a release record under the current policy.

## Bound

Enumeration: rg for session_context_ceiling, PERRY_CONTEXT_CEILING, perry-context-budget and budget-boundary in bin/, schema/, work/, reference/, tests/ and governing architecture documents. Only active session-budget behavior and its readers/docs/tests are changed; no F/G/H architecture migration, unrelated WIP or historical evidence rewrite.
