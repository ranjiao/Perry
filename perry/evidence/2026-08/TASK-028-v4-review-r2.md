# TASK-028 V4 review round 2

Date: 2026-08-19
Result: FAIL

The implicit-main fix handles an untracked board row but not an untracked
commitment. With one declared pipeline track, one correctly tracked pipeline
row, and one blank-Track commitment, the commitment is assigned to no track
and repository evidence is assigned to the pipeline track. The result is a
false MODE-01 warning against a correct declaration.

=== VERDICT ===
task: TASK-028
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-028-spec.md
checked: isolated HEAD copy; prior single-track row fix; untracked commitment
         without an untracked row; MODE-01 behavior; 153 targeted tests
not-checked: full repository suite; real-project copies; subjective README
             front-door quality; non-English aliases; Windows
proof: bin/perry-diagnose:1496 creates implicit main only for a blank-Track row;
       a blank-Track commitment is then assigned to no track and MODE-01 fires
=== END VERDICT ===
