# TASK-019 / TASK-020 V4 re-review — custom groups

Date: 2026-08-19
Result: PASS for both tasks

The reviewer verified custom-group pipeline add and queue route visibility in
`perry-state`, including open counts, stage counts, WIP reporting, fixed-heading
compatibility, and non-task table exclusion. The focused matrix passed 444
tests. Reverting `all_tasks` to fixed/backbone-only behavior made the new
regressions fail; weakening the ID + Title task-table gate also failed tests.

=== VERDICT ===
task: TASK-019
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-019-spec.md
checked: pipeline stages; WIP; custom-group visibility; open counts; fixed
         headings; non-task exclusion; 444 focused tests; two mutations
not-checked: full suite; Windows; more foreign-project fixtures; domain-pack
             stage vocabularies
proof: viewer/parsers.py admits ID+Title task tables under arbitrary headings;
       reverting all_tasks or weakening the gate makes focused tests fail
=== END VERDICT ===

=== VERDICT ===
task: TASK-020
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-020-spec.md
checked: custom-group route; post-Intake visibility; arrival/stage preservation;
         repeated drain; overflow; discharged rows; non-task bounds; 444 tests
not-checked: full suite; Windows; malformed tables beyond tested cases
proof: routed custom-group rows reach tasks, open counts, stages and WIP;
       fixed-only and weakened-gate mutations make focused tests fail
=== END VERDICT ===
