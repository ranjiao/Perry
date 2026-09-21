# TASK-478 — V4 round 2, 2026-09-21

Fresh-context reviewer (not the round-1 reviewer), criteria
`perry/evidence/2026-09/TASK-478-spec.md`, range
`8532871badf419aec8520248ff560f9ef5a34fe9..7696952e99d4d05782e287fab2f2a0b4e9061811`.
Copied by the PMO from the reviewer's returned text.

## F1 (blocking) — a merge that drops the record hides the first add

`release/manage.py:273-275` lists commits touching the record with a plain
`git log`, which simplifies history: at a merge TREESAME to one parent for the
path it follows only that parent. If a merge drops the record, the line that
added it and allocated versions (M1, M2) is skipped and a later re-add becomes
the "introduction". Repro: `pre`; `side` from `pre` (unrelated commit); on main
M1 adds the baseline, M2 allocates 0.1.1; `git merge side` + `git rm` of the
record, `VERSION`, `CHANGELOG.md`; head re-adds a changed baseline plus a product
change. `check_base(pre, head)` accepts with `new=['0.1.0']`; the same history
without the merge is refused as "rewritten" (criterion 4 in merge form).

| Shape | Candidate | Same history without the merge |
|---|---|---|
| 5: `git merge -s ours main` from side, re-add changed baseline | accepted | refused |
| 5b: merge + `git rm`, re-add changed baseline | accepted | refused |
| 5c: merge drops 0.1.1, re-add identical baseline | accepted `['0.1.0']` | refused (product changes need a record) |
| 3: side adds baseline + 0.1.1, deletes, merged; main adds later | accepted | refused (first introduction) |

`--full-history` on the same `git log` fixes all four in a scratch copy; the
test module stays green; criterion 1 still passes (`introduced f89370e5`). Not a
regression: base `8532871b` also accepts shapes 4, 5, 5b.

## F2 (same cause, outside the changed lines)

The unchanged "base lost existing release history" check at `:270` has the same
blind spot: a side commit S1 adds the baseline, a merge drops it and is the base;
plain `git log base -- release/records.jsonl` is empty, `--full-history` lists
the merge and S1; a head re-adding a changed baseline is accepted. The spec keeps
that refusal unchanged, so not counted against this change.

## F3 (test gaps)

Green mutants: dropping `--topo-order` (it matters with clock-skewed dates — a
child listed before the add makes a valid range refused), and adding
`--full-history` (no test covers a dropping merge).

## Held

Criterion 1 (exit 0, `introduced f89370e5`, 0.1.0–0.1.17); merge introduces;
side adds/keeps; side add with extra rows refused; two different adds merged into
new content refused; criss-cross with skewed dates; base==head; base not an
ancestor refused; introduction == head; CLI form exit 0. Mutants: 9 of 11 killed.
Affected tier green; `git diff --check` clean; Bound net +40.

=== VERDICT ===
task: TASK-478
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-478-spec.md
checked: criterion 1 read-only on this repository (exit 0, introduced f89370e5); `bash tests/run --tier affected --base 8532871b…` green (EXIT=0); git diff --check clean; Bound net +40 (+41/−1, two in-scope files); 11 line-anchored mutants of release/manage.py:273-282 in a git-archive scratch copy, __pycache__ cleared with 1.2 s waits and restores checked against git show 7696952e (9 killed, 2 green: dropping --topo-order, adding --full-history); 23 fixture range shapes (fresh git init under the perry-scratch derivation) run against the candidate, a --full-history variant, a no-topo-order variant and the base-commit code: merge introduces, side adds/keeps, side adds with extra rows, side add+remove then later add, linear add/allocate/delete/re-add, merge -s ours drop, merge+git rm drop (changed and identical re-add), two different adds merged (picking one / new content), criss-cross with skewed dates (both tips), clock-skewed children with and without --topo-order, base==head with and without the record, base not an ancestor, introduction == head, CLI `check --base <sha> --ref HEAD`, base that lost history through a merge that dropped the record; bin/perry-restore-check 7696952e on both files OK, worktree clean
not-checked: full suite (not re-run, no reason to); the ci.yml workflow itself, only its command run locally; phase-pointer interaction when the introduction lies inside the range; renames or copies of release/records.jsonl, grafts, shallow clones (CI checkout depth), replace refs; octopus merges; merges with more than one drop/re-add cycle; whether the pre-existing F2 blind spot at release/manage.py:270 should be fixed under this task (the spec says that refusal is unchanged); round 1's conclusions and the author's proof were not relied on
proof: release/manage.py:273-275 — `git log --reverse --topo-order` without `--full-history` skips, at a merge that drops the record, the commits that first added it and allocated versions (M1, M2), so the later re-add is taken as the introduction. Input: on main, M1 adds the baseline and M2 allocates 0.1.1; `git merge side` (side branched from pre) with `git rm` of release/records.jsonl, VERSION and CHANGELOG.md; then a head re-adding a changed baseline. `check_base(pre, head)` accepts it with new_versions ['0.1.0']; the same history without the merge is refused as "release history was rewritten or deleted" (criterion 4). The same happens with `git merge -s ours main` from side.
=== END VERDICT ===
