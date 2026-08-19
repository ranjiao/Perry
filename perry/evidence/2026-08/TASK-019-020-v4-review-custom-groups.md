# TASK-019 / TASK-020 V4 review — custom groups

Date: 2026-08-19
Result: FAIL for both tasks

The writer supports task rows under arbitrary `--group` headings, but
`viewer/parsers.py` only recognizes the fixed P0, P1, P2, Cadence, Intake, and
Backbone headings. Rows successfully added or routed into a custom group are
therefore absent from `perry-state` task counts, stage counts, WIP reporting,
and queue triage.

On a clean HEAD archive, 44 targeted tests passed while both custom-group
reproductions failed at the read surface. Existing `--group` tests assert board
placement but not visibility to the state reader.

=== VERDICT ===
task: TASK-019
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-019-spec.md
checked: effective and default stages; missing-SLA payload; fixed-heading stage
         counts and WIP; custom-group pipeline add; 44 targeted tests
not-checked: full repository suite; Windows paths; additional foreign-project
             fixtures beyond the existing non-priority-heading shape
proof: viewer/parsers.py:654 ignores custom task headings, so a successful
       pipeline add at stage brief yields empty stage_counts and wip_breaches
=== END VERDICT ===

=== VERDICT ===
task: TASK-020
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-020-spec.md
checked: custom-group routing; repeated drain; arrival preservation; intake
         overflow; discharged rows; state-reader visibility; 44 targeted tests
not-checked: full repository suite; Windows paths; malformed custom-group tables
proof: viewer/parsers.py:654-676 excludes arbitrary headings from all_tasks; a
       successful route discharges Intake but perry-state reports open=0 and
       tasks=[]
=== END VERDICT ===
