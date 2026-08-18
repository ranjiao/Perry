# TASK-080 — the eight V4 closes with no readable verdict

`perry-lint --reviews` reported eight rows closed at `V4` where no evidence
document carried a verdict block naming them. This is that worklist, worked.

**The rule this obeys, from `work/reference/review.md § 3`: a block is
transcribed from what its review document actually says.** A verdict written
now to satisfy the check is the thing the convention exists to prevent, so the
three rows that had no review are **not** given one — they are downgraded to
the rung they actually reached, which is the honest repair.

## Five had a review. Transcribed.

| Row | Source | What it says |
|---|---|---|
| TASK-021 | `TASK-021-close.md` | **PASS** at round 2. Round 1 (`TASK-021-v4-review.md`) was a FAIL; the close records the findings fixed and the guards that now fail on what they name |
| TASK-043 | `TASK-019-020-040-044-round2-v4-review.md` | Verified **inside another task's review** — "the declaration is TASK-043's marker … no second mechanism was invented". No standalone verdict was ever issued |
| TASK-051 | `TASK-051-052-v4-review.md § 2` | **PASS**, with two required corrections to what the code says about itself |
| TASK-057 | `TASK-050-053-057-060-v4-review.md` | **PASS** |
| TASK-060 | `TASK-050-053-057-060-v4-review.md` | **PASS** |

## Three had none. Downgraded, not invented.

`TASK-033`, `TASK-054` and `TASK-055` closed at `V4` with evidence that is **a
list of source files and test names** — `bin/perry-diagnose + reference/…​ +
tests/test_diagnose.py`. That is real evidence and it is **V3**: a reproducible
run attested by a script. V4 additionally requires a reviewer who did not see
the reasoning that produced the artifact, and none exists for any of the three.

Their close events now read `V3`. Nothing about the work changed; the claim
about it did.

## One dangling reference, found on the way

`TASK-021-close.md` cites `TASK-021-v4-review-round2.md`, **which does not
exist**. The round-2 verdict survives only as a quotation inside the close
document. That is why the PASS above is sourced to the close and not to the
review it names.

=== VERDICT ===
task: TASK-021
rung: V4
result: PASS
criteria: evidence/2026-08/TASK-021-spec.md
checked: transcribed from TASK-021-close.md, which records round 2's PASS and
         names each round-1 finding with the guard that now fails on it
not-checked: the round-2 review document itself — it is cited and missing
proof: (none — this is a PASS)
=== END VERDICT ===

=== VERDICT ===
task: TASK-051
rung: V4
result: PASS
criteria: evidence/2026-08/TASK-051-spec.md
checked: transcribed from TASK-051-052-v4-review.md section 2 — recognizing a
         table by shape rather than by vocabulary
not-checked: whether the two required corrections to what the code says about
             itself were made; the review required them and this backfill did
             not verify them
proof: (none — this is a PASS)
=== END VERDICT ===

=== VERDICT ===
task: TASK-057
rung: V4
result: PASS
criteria: evidence/2026-08/TASK-057-spec.md
checked: transcribed from TASK-050-053-057-060-v4-review.md — evidence_paths on
         closed rows, contract 1.5
not-checked: nothing beyond the transcription
proof: (none — this is a PASS)
=== END VERDICT ===

=== VERDICT ===
task: TASK-060
rung: V4
result: PASS
criteria: evidence/2026-08/TASK-060-spec.md
checked: transcribed from TASK-050-053-057-060-v4-review.md — --prefix, and
         adopting the board's own id family
not-checked: nothing beyond the transcription
proof: (none — this is a PASS)
=== END VERDICT ===

=== VERDICT ===
task: TASK-043
rung: V3
result: PASS
criteria: evidence/2026-08/TASK-044-spec.md § guarantee 5
checked: verified inside TASK-044's round-2 review rather than on its own —
         `apply` reports the declaration count and `perry-conform status` shows
         it, with no second mechanism invented
not-checked: TASK-043 never had a review of its own, so this records V3 rather
             than the V4 its close claimed
proof: (none — this is a PASS)
=== END VERDICT ===
