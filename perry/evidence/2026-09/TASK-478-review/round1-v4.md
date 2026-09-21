# TASK-478 — V4 round 1, 2026-09-21

Fresh-context reviewer (Claude subagent, own worktree), criteria
`perry/evidence/2026-09/TASK-478-spec.md`, range
`8532871badf419aec8520248ff560f9ef5a34fe9..8775a4a7d9c5a22122a5a8bda32f87e7dbfa6e70`.
Copied by the PMO from the reviewer's returned text.

## Finding (behaviour)

`release/manage.py:274` finds the introducing commit with
`git log --reverse --topo-order --diff-filter=A base..head -- release/records.jsonl`.
Without `-m`, `--diff-filter=A` never lists merges, so an introduction made in a
merge commit is not found; `:276` then falls back to HEAD (the old behaviour).
Input: from `pre`, a file on `side` and one on `main`; `git merge --no-ff
--no-commit side`, add a baseline-only record with its projections, commit as
merge M; then a valid patch H. `check_base(pre, H)` refuses "first introduction
must contain only the 0.1.0 baseline", while `check_base(M, H)` is accepted. The
spec asks for "the ancestry-ordered first commit that adds it". Dropping
`--diff-filter=A` fixes this case and changed no other probe.

## Criteria

1 passes (exit 0, introduced `f89370e5`, 0.1.0–0.1.17; base code refuses);
2–4 confirmed on fresh fixtures; 5 confirmed; affected 6 modules / 181 tests
green; net +27; `git diff --check` clean.

## Green mutations (test gaps)

Dropping `--reverse`, `adds[-1]` for `adds[0]`, dropping `--diff-filter=A`,
dropping `--topo-order`, dropping `base=base_sha,`, dropping the `kind !=
"baseline"` check all leave the unit tests green. The test has one add and no
merge, so the choice of adding commit and the kept base are unpinned; dropping
`--reverse` really changes behaviour (add/delete/re-add probes flip). The kind
check is redundant with `validate()`. Red: reverting the fix, skipping the
recursion, dropping the baseline version, checking HEAD instead of the
introducing commit.

## Other probes (≈30 fixtures, each also against the base code)

Add/delete/re-add same baseline + patch accepted (first add); re-add of a
different baseline or a bad first add later fixed refused as rewritten (base
accepted both); introduced then deleted refused; base==head unchanged; base not
an ancestor refused; parallel identical adds merged accepted; parallel adds with
extra rows refused; PMO-only patch or new phase pointer without a record refused;
CLI `check --base <pre> --ref HEAD` exit 0. The author's flagged case (side-branch
introduction plus a product change on main) is refused, which matches the spec.

Observations, not FAIL grounds: the PMO-only rule is not applied between base and
the introducing commit; projections must be present in the introducing commit
(split records/projections now refused); `product_paths` covers introducing
commit → head while `base` reports the original; row removal inside the range is
invisible (as the existing branch always was). Callers: `main` `check --base`
(`:378`, `ci.yml:26`), the new recursion (`:281`), 15 test calls; `release.yml`
uses `prepare` only, `publish.py` none.

=== VERDICT ===
task: TASK-478
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-478-spec.md
checked: detached 8775a4a7 in my own worktree; criterion 1 read-only on this repository (exit 0; base code refuses); `bash tests/run --tier affected --base 8532871b…` green (6 modules, 181 tests); `git diff --check` clean; net +27; about 30 probe ranges in fresh `git init` fixtures under the scratch derivation (the four spec ranges, a merge as the introducing commit, add/delete/re-add, introduced-then-deleted, base==head, base not an ancestor, side-branch introductions with product, PMO or patch changes on either side, parallel adds, split records and projections, PMO-only and phase-pointer after the introduction, CLI `check --base X --ref HEAD`), each also run against the base code; 10 mutants on a `git archive` scratch copy, anchored by line number, `__pycache__` purged with over 1s waits, restore verified against `git show 8775a4a7`; 3 flag-drop mutants run through the probes; worktree files verified with `bin/perry-restore-check 8775a4a7`
not-checked: GitHub Actions itself (not re-run, out of scope); pushes where `github.event.before` is all zeros (new branch or force push), which predates this change; octopus merges; shallow clones; renames of records.jsonl; timestamp-ordering effects of dropping `--topo-order` with skewed commit dates (no probe distinguished it); how often merge-introduced adoptions happen in real use; full suite not re-run (no reason to)
proof: release/manage.py:274 (`--diff-filter=A` without `-m` excludes merge commits) and release/manage.py:276 (empty result falls back to head_sha). Input: a merge committed with `--no-commit` that adds a baseline-only record, followed by a valid patch; `check_base(pre, H)` refuses "first introduction must contain only the 0.1.0 baseline" while `check_base(M, H)` is accepted
=== END VERDICT ===
