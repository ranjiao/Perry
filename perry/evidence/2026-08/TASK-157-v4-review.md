# TASK-157 — V4 review: **PASS**

Reviewed `coding/task-157-kr-declared-once` at `1e0935b`, detached in
`scratchpad/review-157`. No write of any kind was made in that worktree or in
`/Users/bytedance/proj/Perry`. Every destructive check ran on `git archive`
exports into `scratchpad/rv157-jr/` (uniquely prefixed, per the standing
constraint about fixed-name tooling in the shared scratchpad).

## Both audit claims: CONFIRMED, by my own measurement

### Claim 1 — the phase half of `linkage-kr-exists` shipped with nothing holding it. **CONFIRMED.**

I exported `f15d234` twice, deleted the guard from one copy, and ran the whole
suite on both.

```
$ python3 - <<'EOF'   # deletes exactly the 7-line block, asserts the anchor is unique
  if not kr.id.startswith(f"P{own}-"):
      findings.append(Finding("warn", rel, "linkage-kr-exists", …))
EOF
bin/perry-lint  68ac6f33042c20df25cff530a76d07d3 -> 975ce09e29ff2b620eb6fa6eef86a155

$ cd tree-f15d234 && bash tests/run     # 99 modules · 2910 tests · 453.4s · 8 workers  → 5 failures
$ cd mut-f15d234  && bash tests/run     # 99 modules · 2910 tests · 451.6s · 8 workers  → 5 failures
$ diff f15-clean.fails f15-mut.fails
IDENTICAL failure sets
```

The whole suite is byte-for-byte unchanged by deleting the guard. The claim is
exactly right, including its wording.

The fix holds. At branch head, the same deletion (green-first asserted OK
first) reddens the two new tests and nothing else:

```
### M4 phase-half guard dropped
  green-first: ['Ran 56 tests in 30.952s'] OK  fails=[]
  mutated   : ['Ran 56 tests in 27.460s'] FAILED (failures=2)
     FAIL: test_cadence.TestLinkageBelongsToItsOwnPhase.test_a_kr_belonging_to_another_phase_is_reported
     FAIL: test_cadence.TestLinkageBelongsToItsOwnPhase.test_the_phase_half_names_the_phase_and_the_id
  restored md5 68ac6f33… == 68ac6f33… : True
```

`test_a_genuinely_wrong_kr_is_still_reported` stayed **green** under that
mutation — which is the direct proof that it cannot reach the phase half. And
under M3 (objective half deleted) it is the only test that goes red, while the
two new ones stay green. The two halves are held separately, by disjoint tests.
The new tests can only fire on the phase half: the fixture's `001-linkage.md`
declares `P001-O1-KR1` under `- id: O1`, the mutation rewrites only the phase
segment to `P002`, so `kr_objective_id` still returns `O1 == obj.id` and the
objective branch is silent.

### Claim 2 — eight KR→overall-OKR edges were deleted and replaced with prose. **CONFIRMED, numbers exact.**

```
$ grep -n "linked:" tree-f15d234/perry/phase/001-linkage.md
15: linked: "`parse_tracks` on `.perry/config.md` returns `[('main','project')]` — 0 of 3 …"
23: linked: "The code ships — `perry-state` carries `stage_counts`, `wip_breaches` …"
… all eight are verbatim the retro score table's `Measured` column
   (001-work-modes-live.md:232, `| KR | Score | Measured |`)

$ grep -n "linked:" tree-1e0935b/perry/phase/001-linkage.md
KR-O1.1, KR-O1.2, KR-O1.3, KR-O1.1, KR-O2.1, KR-O2.1, KR-O3.4, KR-O3.4
```

That sequence is byte-identical to the `Linked overall KR` column of
`001-work-modes-live.md` at `8abd30d`. Phase 002's column is `—` on all 8 rows;
phase 003's 8 were transcribed correctly. So **16 of 24 at `f15d234`, 24 of 24
at `3784059`** — the audit's arithmetic is right. This was the most important
thing on the branch: it is a silent deletion of eight graph edges, strictly
worse than the duplication the row exists to remove, and the inherited RESULT
asserted the opposite in writing.

**Both halves of the new guard verified, by mutation:**

```
### M12  linked put back to the retro prose        → FAIL test_every_linked_value_names_an_overall_kr_this_project_declares
### M12b linked: "KR-O9.9" (right shape, dangling) → FAIL (same test)   ← it RESOLVES, it does not shape-match
### M5   parse_linkage stops reading `linked`      → FAIL (same test, via the `checked >= 8` refusal) + 2 more
```

M5 is the zero-value refusal firing: with the field unread, `checked` drops to
0 and the test refuses to pass vacuously. Both halves are real.

## Claims measured independently

**Option (b) as described — confirmed.** No `phase/<NNN>-<slug>.md` carries a
KR declaration table; the only survivors of a full-tree grep are
`tests/fixtures/sample-project-zh` (deliberately the unmigrated fixture, and
`TestAProjectWithNoRegisterStillReadsItsDocument` asserts it still has one, or
that class asserts nothing) and `phase/snapshots/` (excluded by construction).
The render and all three refusals, run on an exported head:

```
$ python3 bin/perry-goals krs --root .            → the four-column table, exit 0
$ python3 bin/perry-goals krs --write --root .    → refused …  exit 1
$ python3 bin/perry-goals krs foo   --root .      → refused …  exit 1
$ python3 bin/perry-goals krs --phase 099 --root . → refused — no linkage register at phase/099-linkage.md, exit 1
$ python3 bin/perry-goals krs --phase 001 --root . → the scored phase's table, exit 0
```

`plan-phase` no longer authors the block: `goals/state/phase_TEMPLATE.md` (both
tables replaced by a pointer), `goals/reference/phases.md` step 7 and *After
write* step 2, and the `krs` row in `goals/SKILL.md`. All three checked, and
M7 (a table re-appended to the template) reddens
`test_the_template_carries_no_kr_table`.

**The regression case — confirmed.** `git diff 8abd30d..HEAD --
perry/phase/003-linkage.md` is eight additive `linked:` lines and nothing else.
`P003-O2-KR1` keeps `target: 0` and its `metric:` string unchanged. On `main`
the metric is in two files; on the branch, one — asserted as a cardinality plus
a property rather than a filename literal, which is the right shape for a
live-state assertion.

**The duplication at the fork point — re-measured independently.** My own
scanner over the `8abd30d` export, pairing each declaration row with its
register entry and normalising backticks/bold/whitespace:

```
declaration rows: 24
title cell differs : 24
metric cell differs: 24
both differ: 24
```

24 of 24, not the spec's 22. The branch's number is the correct one. Note the
sense of "disagree": textual non-identity, and in most rows it is the register
that says *more* (the baseline moved from the title cell into `metric`). The
companion `TASK-157-removed-kr-tables.md` measures the other direction — 7 of
24 cells carried a word the register does not — and both statements are true of
the same data. The evidence file names its method; a reader who reads only the
"24 of 24" line will over-read it.

**Twelve mutations — I re-ran all twelve, not five.** Harness: green-first
asserted before every mutation, `__pycache__` cleared each run,
`discover -s tests -p <module>.py` as the runner, file restored and md5-compared
after. Every one was green first and every restore matched. `diff -r` of the
mutation box against the pristine head export: no differences.

| # | revert | reddened |
|---|---|---|
| M1 | `kr_rows` phase level reads the document | 4 tests incl. `test_the_goals_payload_follows_the_register` |
| M2 | `perry-state` phase payload reads the document | `test_the_standup_payload_follows_the_register` |
| M3 | objective-agreement finding dropped | `test_a_genuinely_wrong_kr_is_still_reported` |
| M4 | phase-agreement finding dropped | the two new `test_cadence` tests |
| M5 | `parse_linkage` stops reading `linked` | 3 tests |
| M6 | `krs` accepts extra args | `test_there_is_no_write_flag` |
| M7 | template regains a KR table | `test_the_template_carries_no_kr_table` |
| M8 | KR table back in `003-storage-code.md` | `test_perry_owns_no_phase_document_with_a_kr_table` + 1 |
| M9 | `phase_key_results` always falls back | 5 tests |
| M10 | never falls back | `test_its_krs_still_reach_the_payload` |
| M11 | `perry-lint` never falls back | `test_a_project_that_serves_an_undocumented_kr_is_reported` |
| M12 | `001-linkage.md` `linked` back to prose | `test_every_linked_value_names_an_overall_kr_…` |

**Every guard on this branch survives its own deletion.** That is the defect
this branch's own audit found in its predecessor, and it is not repeated here.

**The green-first check is real and it matters.** Reproduced:

```
$ python3 -m unittest tests.test_cadence
ModuleNotFoundError: No module named 'gate'      (tests/test_cadence.py:30)
Ran 1 test … FAILED (errors=1)
```

One `_FailedTest`, indistinguishable from a mutation working if you only read
the exit code. Asserting the target GREEN before mutating is what makes the
table above mean anything; this is a better harness than the previous rounds.

**Baselines — reproduced exactly.** Runner `bash tests/run` (which is
`tests/parallel`, 8 workers). Trees are `git archive` exports of the named
commits into scratch, so each carries that commit's committed board state.

| Runner | Tree | Modules · tests | Failures |
|---|---|---|---|
| `bash tests/run` | export of `8abd30d` | 98 · 2882 | 5 |
| `bash tests/run` | export of `f15d234` | 99 · 2910 | 5 |
| `bash tests/run` | export of `1e0935b` (head) | 99 · 2913 | 5 |

The same five tests on every row, `FAIL:` line for `FAIL:` line: the two
`test_contract_key_parity` witness tests, `test_diagnose`'s queue-register
reconcile (`2 != 0`) and `test_perry_itself_passes_its_own_id_checks`, and
`test_kr_progress_provenance`'s. The branch adds no failure and removes none.
`python3 bin/perry-lint --root perry` on the head export: **0 errors**, 5
pre-existing warnings.

`python3 -m unittest discover -s tests` on the head export: **Ran 2913 tests …
FAILED (failures=8, skipped=4)** — the same five, plus exactly the three
`test_risks_store.TestTheReadersAreOneFunction` tests. That module alone under
`discover -s tests -p test_risks_store.py` is green (53 tests, OK), which is the
double-import artefact the branch names, not a regression. Both runners
reproduce their claimed numbers.

`test_board_render.test_every_rendered_field_moves_when_the_store_moves` did not
fire on any of my runs.

**The inherited RESULT's errors — confirmed corrected.** `f15d234`'s RESULT
carries live `BASELINE_8ABD30D` / `AFTER_RUN` placeholders at lines 163–164; the
head RESULT carries none outside the audit paragraph that names them as the
defect. Five measured baseline rows, each naming runner and tree. "3
pre-existing failures" is corrected to 5 with the data-dependence explained,
"22 rows" to 24. The document separates inherited from measured throughout, and
its `What I did NOT do` section is unusually honest — it names the schema
consequence, the untested consumer, and the missing TASK-236 report without
being asked.

## Findings — none blocking, one worth a row

1. **`goals/state/linkage_TEMPLATE.md` was not updated with the rest of
   `plan-phase`.** It has no `linked:` slot, and its metric placeholder still
   reads `metric: "{{metric as written in the phase file}}"` — pointing the
   next phase author at a file that no longer holds the metric. Consequence:
   the next register can be authored with every `linked` empty, and nothing
   catches it — `test_every_linked_value_names_an_overall_kr_this_project_declares`
   requires only `checked >= 8`, which phases 001 and 003 already satisfy on
   their own, and `test_a_register_without_it_is_not_an_error` makes an absent
   `linked` legal by design. That is the same shape as Claim 2 — an edge that
   is silently absent and unreported — displaced from the past into the future.
   Small fix; it belongs on the board rather than in another round.
2. `perry-goals link` was tested against a **declared copy** and preserves all
   nine `linked:` values across a rewrite (only `updated`, `tasks[]` and
   `unlinked[]` move). The rescued edges are not at risk from the register's
   own writer. Recorded because it was the one way Claim 2's fix could have
   been undone by the next command anyone runs.
3. The corrected RESULT says "four unsubstituted placeholders" and then lists
   six. Cosmetic.
4. `tests/test_parsers.py § test_the_phase_template_declares_no_krs_and_the_register_does`
   ends `assertTrue(link.error or link.objectives)`. Measured:
   `link.error == 'unfilled template placeholders'`, `link.objectives == []`, so
   that assertion passes on the error branch alone and does not verify the
   linkage template declares KRs. Weak rather than wrong — the docstring names
   both branches — and the other three assertions in the test are real.
5. `phase_key_results_by_objective` appends a register KR whose objective the
   document has no heading for to the **last** objective. Documented as a
   deliberate choice (keeping `kr_total` equal to the sum of the groups), but it
   mis-groups silently. Not exercised by this branch's data.
6. Consumer-visible content change, disclosed by the author and confirmed by
   me: `perry-state --json` `phase.objectives[].krs[]` keeps its exact key set
   and `kr_total` (8 before, 8 after, same ids, `qualifier` was already `""` on
   both), but `metric` now carries the register's wording with the baseline
   inline — up to ~300 bytes where the document's cell was `"0"`. A consumer
   rendering that cell in a narrow column sees a different string. Not a
   contract break; not a break I can rule out for a specific UI.
7. `schema/state-schema.json` marks the phase KR table `"optional": true`, so
   `perry-lint` will not report a project that hand-writes one back. Only this
   repository's own test sweep does. The author states this and gives the
   reason (a linter rule would false-positive on every unmigrated phase). I
   agree with the trade.

## Checked / not checked

**Checked:** both audit claims, by full-suite measurement and by reading the
documents at `8abd30d`; option (b)'s three surfaces and three refusals; the
`003-linkage.md` additive diff; the fork-point duplication, re-measured with my
own scanner; all twelve mutations with green-first and md5 restore, plus one of
my own (`KR-O9.9`); the green-first check's motivating loader failure; three
full-suite baselines; `perry-lint --root perry`; the register writer's
preservation of `linked`; the payload key shape fork vs head; every new test
read for the four vacuity modes named in the dispatch.

**Not checked:**
- **aiMark or any external consumer.** No access to it from here. The key shape
  and `kr_total` are unchanged, but finding 6 is a real content change and
  nobody has run a consumer against it. **I do not think it blocks**: the read
  contract is intact, and the row that owns consumer breakage
  (`P002-O3-KR2`) is a different row.
- **Whether a CLI render is a good enough read surface.** DESIGN-013 § 6 defers
  that to TASK-236 and no report exists. **I do not think it blocks this row
  either**, and I want to be explicit about why rather than wave it through:
  this is the *phase* KR table, 16% of one document with a 307-byte longest
  cell, and the render reproduces it as the same markdown through the same row
  renderer. The judgement DESIGN-013 is protecting is about `OKR.md` and
  `BOARD.md`, which are what a human opens; a phase file's KR table is not.
  Reversing this row later costs one command. If the PMO reads § 7 as making
  *every* such move conditional on TASK-236's report, that is a decision call
  above this review, and it should be made on the design rather than on this
  branch's quality.
- **`main` was not merged**, per the dispatch. I make no statement about the 7
  files it also touches.

## Verdict

**PASS.** The audit was right on both counts and I confirmed both with my own
measurements rather than by re-reading its arithmetic. The work it produced is
the most carefully verified branch I have reviewed in this repository: twelve
mutations that all reproduce, a harness that asserts green before it mutates,
three named baselines that reproduce to the test, and a RESULT that says which
agent measured what. Finding 1 should be filed as a row before the next phase is
planned.
