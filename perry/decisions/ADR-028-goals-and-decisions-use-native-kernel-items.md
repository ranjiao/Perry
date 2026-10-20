# ADR-028 — Goals and decisions use native kernel items

Native metadata and lifecycle: `ADR-028` through `bin/perry item get`.
This document is the owned rationale attachment, not a second status register.

## Context

DESIGN-023 F/G/H and ADR-025 scheduled final goals/decide/root cutover. The user
approved the bounded monotonic prefix-floor revision and the concrete423 exact
retirements plus R0096 grammar narrowing on2026-10-20. Independent integration
landed Perry0.1.29 at7f784906 and aiMark at27586cdb, preserving existing WIP.
Actual Perry and SkyTonight additive migrations preserved every preexisting work
item and event, repeated without events, and exported/replayed byte-identically.

## Options

Retain legacy structured writers/current-state parsers, or use the approved
native process template and lane-owned narratives. The latter implements the
locked decisions; it introduces no new kernel concepts, command groups or guards.

## Chosen

Goals, checks, phases and decision metadata are canonical native items/events.
Versioned source identities and raw historical assertions are preserved. An old
scalar is not promoted to a measured metric. Skill procedures own interpretation,
measurement execution, the next step and actual approval checks. The kernel only
checks the generic contract and derives declared metrics.

As ADR-025 scheduled, this ADR supersedes ADR-017/022. ADR-012/014 are folded into
the active store ADR-026 through typed links and a new narrative amendment.
ADR-011 is archived because its transition is complete. ADR-015/019 retain their
one-home principles with native-medium/owned-narrative amendments. Structured
project/role safety remains additive and fail-closed. Legacy sources and journals
remain frozen historical attachments; no old header is rewritten as current state.

## Consequences

Current dashboards and consumers query the kernel. Each real project retains its
own store/IDs; missing DESIGN-018 stays absent. The existing template apply may
reserve monotonic issued-number floors under the actual approved design revision.
Fresh DB/source backups and exact plans are retained. Recovery never imports over
a populated store or automatically replaces live DB history. Task completion and
human V5 remain separate from source integration, data migration and this ADR.

## Evidence

- evidence/2026-10/TASK-492-prefix-floor/approval.json
- evidence/2026-10/TASK-494-review-candidate/approval.json
- evidence/2026-10/TASK-494-formal-cutover-20261020/Perry/live/verification.json
- evidence/2026-10/TASK-494-formal-cutover-20261020/SkyTonight/live/verification.json
