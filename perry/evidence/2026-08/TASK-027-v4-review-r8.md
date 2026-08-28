# TASK-027 V4 review round 8

Date: 2026-08-19
Result: PASS

The reviewer checked live lane directories, permanent aliases, router and
shipped vocabulary guards, lane frontmatter names/descriptions, startup root
inventories, and ownership/claims. The focused matrix passed 108 tests.

On disposable copies, changing `name: goals` to `name: okr` failed the new
frontmatter guard. Replacing the live startup inventory with the retired lane
directories produced six failures: three retired names and three missing live
names.

=== VERDICT ===
task: TASK-027
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-027-spec.md
checked: live lane directories; permanent aliases; router/vocabulary guards;
         frontmatter name/description; startup inventories; ownership/claims;
         108 focused tests; name and directory mutations
not-checked: full suite; setup on all three hosts; exhaustive re-audit of
             intentionally exempt lane-doc shorthand
proof: all focused tests pass; both prior defect mutations make the guards red
=== END VERDICT ===
