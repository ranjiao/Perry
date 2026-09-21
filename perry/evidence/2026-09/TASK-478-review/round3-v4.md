# TASK-478 — V4 round 3, 2026-09-21

Fresh-context reviewer (not the round-1 or round-2 reviewer), criteria
`perry/evidence/2026-09/TASK-478-spec.md` including Amendment 1, range
`8532871badf419aec8520248ff560f9ef5a34fe9..9134f6185453ee713eba459ff33882623f773c5e`.
Copied by the PMO from the reviewer's returned text.

**PASS.** The proof was re-derived independently: a range holds every ancestor
of a range commit that is not an ancestor of base, so with the full-history
walk of base empty every first add lies in the range; a commit holding the
record while no parent does is always listed under `--full-history`; with
`--reverse --topo-order` ancestors precede descendants, so `adds[0]` is a
genuine add, merges included.

Shapes (fresh `git init` fixtures, each matching the linear-history verdict):
criterion 1 read-only on this repository (exit 0, introduced f89370e5,
0.1.0–0.1.17); criterion 6 — merge+`git rm`, `-s ours` both ways, octopus drop,
octopus `-s ours`, two merge-drop cycles, merge drop + plain drop + identical
re-add, round-2 shapes 3/5/5c, all refused; criterion 7 — base lost the record
via merge, octopus, octopus `-s ours`, refused; criterion 8 — skewed dates
accepted, 16 date/length/direction variants of two parallel adds always pick the
head's first-parent line; parents holding different records; criss-cross; a
merge adding the record with neither parent holding it (baseline accepted,
extra rows refused); unrelated root with extra rows refused; TREESAME-to-lacking
merge; base==head; base not an ancestor; `log.follow`, `diff.renames=copies`,
`log.showRoot=false` configs; CLI `check --base <sha> --ref HEAD` (exit 1 on 6
and 7, 0 on a valid range). The base code wrongly accepts 12 of these shapes.

Speed: the full-history walk takes 0.035 s over 2,596 commits; criterion 1 1.0 s.
Affected tier green; `git diff --check` clean; Bound net +59 (+62/−3).
Mutants: 12 of 13 killed. Green: `--topo-order` → `--date-order` (still ancestry
safe; with two independent adds the pick then depends on dates, unpinned).

Non-blocking: with two independent adds the head's first-parent add is used and
the other is never checked (spec does not decide); commits between base and the
add are not checked (spec scopes checks to intro..head).

=== VERDICT ===
task: TASK-478
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-478-spec.md (including Amendment 1, criteria 6-8, Bound +60; read from primary checkout)
checked: worktree detached at 9134f618 (clean, perry-restore-check OK on both files); criterion 1 read-only `release/manage.py check --base 0b5bf99e --ref 174f35b2` exit 0 introduced f89370e5 (1.0 s), plus 542cc01e..9134f618 (0.45 s), full-history walk 0.035 s over 2596 commits; `bash tests/run --tier affected --base 8532871b…` EXIT=0; git diff --check clean; Bound net +59 (+62/-3); criterion-5 revert of manage.py to 8532871b turns the 3 new tests red; 13 line-anchored mutants of release/manage.py:270-282 in a git-archive scratch copy, __pycache__ purged with 1.2 s waits, restores cmp'd against `git show 9134f618:release/manage.py` (12 killed; --date-order green, shown equivalent for the ancestry guarantee); fixture shapes in fresh git-init repos under the perry-scratch derivation, run against the candidate and the 8532871b code: merge+rm drop, -s ours both directions, octopus drop and octopus -s ours (range and as base), two merge-drop cycles, merge-drop+plain-drop+identical re-add, round-2 shapes 3/5/5c, parallel adds X/Y with each side kept and both merge directions, 16 date/length/direction variants, criss-cross (+rewrite), parents holding different records, evil merge adding baseline / baseline+extra, unrelated root holding extra rows, TREESAME-to-lacking merge, skewed decreasing dates, base==head with/without the record, base not an ancestor, log.follow/diff.renames/log.showRoot configs, CLI `check --base <sha> --ref HEAD` (exit 1/1/0) and short-sha/branch forms
not-checked: full suite (not re-run; affected tier green and change confined to two files); the ci.yml workflow on GitHub (only its command, locally); shallow clones, grafts, replace refs, log.showSignature/GPG output on stdout; renames or copies into release/records.jsonl beyond the diff.renames config; which of two independent adds should be authoritative (spec leaves it undefined, candidate uses head's first-parent line); product/phase-pointer changes between base and the introducing commit (spec scopes checks to intro..head); random DAG fuzzing beyond the enumerated shapes; earlier rounds' verdicts and the author's proof were not relied on
proof: —
=== END VERDICT ===
