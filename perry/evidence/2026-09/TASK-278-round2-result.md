# TASK-278 — round 2 result (after the V4 FAIL)

> Branch: `worktree-agent-a819191f7ac35bb5b`, four commits, not pushed.
> Base for every restore: **`4c5e4bd`**. Not `main`, which moves.
> Fixes: `0103c64` · guards: `baae207`, `da32d63`, `9485b95`.

## 0. The base, verified before any work — and it was wrong

The worktree I was handed was at **`d49964e`, 508 commits behind `main`** —
`TASK-381` exactly, three of four agents in one day. `perry/linkage.jsonl` did
not exist there at all.

```
$ git log --oneline -1
d49964e chore: consolidate test suite and project state
$ git merge-base --is-ancestor 4c5e4bd HEAD   ->  ANCESTOR-FAIL
$ git rev-list --count main..HEAD             ->  0      (no commits of my own)
$ git rev-list --count HEAD..main             ->  508
```

The branch carried no commits of its own, so per the dispatch I reset onto
`4c5e4bd` (which is `main`'s tip: `Merge TASK-279`). After the reset:

```
$ git log --oneline -1
4c5e4bd Merge TASK-279: add --kr writes the edge inside the row's own transaction
$ git merge-base --is-ancestor 4c5e4bd HEAD   ->  ANCESTOR-OK
$ wc -l < perry/linkage.jsonl                 ->  121
$ bin/perry-lint --root .
  0 error(s), 38 warning(s)
  · linkage store: 121 record(s), 0 row(s) drifted
```

**This matters beyond the reset.** The V4 review measured at `6af6fd2`; my base
is later and includes row D (`TASK-279`), which the review could not have seen.
Every line number below is re-derived at `4c5e4bd`, and row D added a
`linkage.jsonl` writer that did not exist when § 5.6 was written (§ 3).

## 1. Baseline, measured in my own worktree

`bash tests/run` at `4c5e4bd`:

```
118 modules · 3371 tests · 93.6s · 8 workers
✗ 1 of 118 MODULE(S) red
    FAIL test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
```

Re-run alone (`bash tests/run --only test_diagnose`): **same one red**, 1 of 145
— so it is not order-dependent. This is `TASK-380`, a true finding about the
user's decision backlog that no code change here clears.

Final, after everything below: **118 modules · 3378 tests · 1 red — the same
one.** +7 tests, no new failures.

## 2. A confound that would have faked the whole acceptance

The dispatch's three differentials could not be reproduced as written, and the
reason is worth recording because it would have produced a false PASS.

`TASK-278`'s own `next_action` — written when the FAIL was filed — contains the
sentence *"TASK-028, TASK-046 and TASK-087 are ALL REFUSED"*. `next_action` is
itself a live reference (`names_id`), so on the tree today **all three refuse
already**, naming `TASK-278.next_action`, whether or not the defect is fixed:

```
$ perry-task purge TASK-028 … --dry-run     # BEFORE any fix, unmodified base
{"refused": "TASK-028 is named by TASK-278.next_action — `V4 FAILED
 2026-09-07, evidence/2026-09/TASK-278-v4-review.md`. …"}
```

The message truncates `next_action` at 60 characters, so the citation that
does the work is not visible in the refusal. Running the three commands after
the fix and seeing "refused" would have proved nothing at all.

Every differential below is therefore measured in a scratch copy with
`TASK-278`'s `next_action` and `evidence` cleared, so the register is the only
thing that can refuse. Stated plainly: **the three ids are protected today by
the FAIL note about them, not by the register.**

## 3. The seams, re-derived by call site

Never by grepping a name. Row C reported the spec's line numbers were stale and
unpredictably so; they still are — § 5.6's site 6 is written `4503` and is now
`4751`, having moved **forward 248 lines**.

### The six § 5.6 readers

| # | § 5.6 says | actually, at `4c5e4bd` | which seam decides store-vs-document | scoped before | after |
|---|---|---|---|---|---|
| 1 | `perry-goals:1657` | `perry-goals:1335` `Register.graph` → `linkage_graph:1676` | `linkage_graph` | yes | yes |
| 2 | `perry-goals:3033` | `perry-goals:3238` `cmd_krs` → `load_linkage` | `parsers.load_linkage` | **NO** | **fixed** |
| 3 | `perry-task:4491` | `perry-task:4853` `live_references` (store `:4934`, documents `:4980`) | its own inline loop | **NO** | **fixed** |
| 4 | `perry-lint:1200` | `perry-lint:1401` sweep → `_linkage_records_for_phase:1253` | `perry-lint` helper | yes | yes |
| 5 | `perry-lint:1231` | `perry-lint:1234` `_is_linkage_register` | n/a — a glob filter | n/a | n/a |
| 6 | `parsers.py:4503` | `parsers.py:4751` `load_snapshot` → `load_linkage` | `parsers.load_linkage` | **NO** | **fixed** |

**All six spec line numbers are stale.** Sites 2 and 6 share one seam, which is
why one edit fixes both.

### How many seams, and which I changed

The review found **four** distinct store-versus-document decisions where the row
claimed one. I confirm four at my base, and **left three**:

| seam | before | after |
|---|---|---|
| `parsers.load_linkage` (sites 2, 6) | store-wide — **defect** | per-phase, via the new `parsers.linkage_records_for_phase` |
| `perry-goals.linkage_graph` (site 1) | correct, but its own second copy of the rule | **collapsed** — now calls the shared helper |
| `perry-task.live_references` (site 3) | exclusive `else:` — **defect** | a union of both authorities |
| `perry-lint._linkage_records_for_phase` (site 4) | correct | **unchanged, deliberately** |

`perry-lint`'s helper keeps its own spelling on purpose and it is not
duplication: its `unlinked` records attach to the **current** phase, while the
readers' attach to the phase being read. Collapsing them would have to pick
one, and its version is the guarded one. Filed as a finding, not merged.

**A seventh reader the review could not have seen.** Row D (`TASK-279`) landed
after `6af6fd2` and added `perry-task:2739 linkage_edge_change`, which reads
`linkage.jsonl` to append an `add --kr` edge. It is a **writer**, so it makes no
store-vs-document read decision and is not a § 5.6 seam — but it can append an
edge whose `kr` names a phase the store holds no `kr` record for, and my filter
then correctly declines to be the authority for that phase, so the edge renders
nowhere. Finding 4 below; not this row's fix.

## 4. Defect 2 — `purge` deleting rows a register still names (fixed first)

`bin/perry-task:4953` was an `else:` making the document scan an exclusive
alternative to the store scan. It is now a **union**: the register documents are
scanned whether or not the store exists.

A reference guard is the one place where reading both authorities is the
requirement rather than redundancy. Over-reporting costs a refusal a user can
clear by editing; under-reporting costs a record `mint_id` never re-issues.

The document is still read **by line**, because the refusal has to name the line
to edit, and `agents[].tasks` is now attributed as itself rather than as a KR
edge.

Deconfounded, `--dry-run`, in a `git archive` scratch copy:

| id | base `4c5e4bd` | this branch |
|---|---|---|
| `TASK-028` | **not refused** | `refused: … 001-linkage.md:16 krs[].tasks (and 1 more: 001-linkage.md:105 agents[].tasks)` |
| `TASK-046` | **not refused** | `refused: … 001-linkage.md:24 krs[].tasks (and 1 more: 001-linkage.md:103 agents[].tasks)` |
| `TASK-087` | **not refused** | `refused: … 002-linkage.md:69 krs[].tasks` |

The three register lines are exactly the ones the FAIL named.

## 5. Defect 1 — another phase's key results

`viewer/parsers.py` handed the whole store to `linkage_from_store` with no
filter for the phase `document_path` names.

`perry-goals krs --root perry --phase 001`:

| | base `4c5e4bd` | this branch |
|---|---|---|
| under `## O1 — The three non-`project` modes run on a live track` | `P003-O1-KR1`, `P003-O1-KR2`, `P003-O1-KR3` | `P001-O1-KR1` … `P001-O1-KR4` |
| phase 001's own 8 KRs | **all dropped** | all present |

`--phase 002` prints only `P002-*`; `--phase 003`, the store-covered phase,
still prints its six `P003-*` KRs from the store.

**Site 6**, `perry-state --section linkage` with `phase/CURRENT` set to
`001-work-modes-live` — a normal state, and what `CURRENT` holds the moment
phase 004 opens:

| | base | this branch | 001's document declares |
|---|---|---|---|
| first KR under O1 | `P003-O1-KR1` | `P001-O1-KR1` | `P001-O1-KR1` |
| `unlinked` count | **100** | **23** | **23** |

That is DESIGN-015 § 7 row 1 — *"The move silently drops existing edges"* —
closed at the reader it was arriving through.

**Invariance held.** With `CURRENT` back at `003-storage-code`, both
`perry-state --section linkage` and `--section attribution` are **byte-identical**
between base and this branch.

## 6. The mutation round — 10 planted, 10 red, control green

Line-anchored with an assert on the old text (never `str.replace`), bytecode
cleared and the clock pushed past the whole-second boundary before every run,
restores taken from `git show <ref>:<path>` and verified byte-equal. Harness and
specs: `.claude/rc2/mutate.py`, `.claude/rc2/mutations.json`. Graded against 8
modules: `test_linkage_store_readers`, `test_linkage_import`,
`test_okr_store_is_the_source`, `test_linkage_task_exists`,
`test_linkage_writer`, `test_purge`, `test_unlinked_declaration`,
`test_register_store_invariant`.

| # | mutation | verdict | named test that went red |
|---|---|---|---|
| M0 | control, no edit | **GREEN** (required) | — |
| M1 | `perry-task`: restore the exclusive `else:` — FAIL 2 put back | **RED** | `test_site_3_a_register_the_store_does_not_cover_still_protects_a_row`, `test_site_3_perry_task_names_the_store_and_its_line` |
| M2 | `load_linkage`: hand the whole store over unfiltered — FAIL 1 put back verbatim | **RED** | `test_site_2_a_phase_the_store_does_not_cover_reads_its_own_document`, `test_site_6_…` |
| M3 | helper returns `[]` not `None` (review's V2 shape at the new seam) | **RED** | `test_site_2_…`, `test_site_6_…` |
| M4 | helper matches every phase (review's **V11**, which was green) | **RED** | `test_site_1_…`, `test_site_2_…`, `test_site_6_…` |
| M5 | `linkage_document_phase`: filename branch nulled | **RED** | `test_the_filename_names_the_phase_when_the_document_does_not` |
| M5b | both phase-derivation branches nulled | **RED** | `test_site_2_perry_goals_krs_reads_the_store`, `test_site_6_perry_state_attribution_reads_the_store` |
| M6 | `linkage_graph` takes the store for every phase (review's **V10**, which was green) | **RED** | `test_site_1_the_writer_reads_only_its_own_phases_records` |
| M7 | document reference loses its line number | **RED** | `test_site_3_a_register_…`, `test_site_3_perry_task_names_…` |
| M8 | `agents[].tasks` reported as `krs[].tasks` | **RED** | `test_site_3_an_agents_tasks_entry_is_a_live_reference_and_says_so` |
| M9 | `JSONDecodeError` branch drops the line (review's **V1**, which was green) | **RED** | `test_an_unreadable_line_survives_a_retraction_too` |

### The greens, every one named and closed

Three mutations came back green on the first pass. None is a footnote.

- **M6 GREEN.** My first `test_site_1` called `linkage_records_for_phase`
  **directly**. The helper was right and its one caller was never asked, so
  taking the whole store inside `linkage_graph` changed no assertion. This is
  the review's V10/V11 hole surviving into my own guard. Closed by driving
  `perry-goals link` with `CURRENT` pointed at a phase the store does not
  cover, which is the only path that reaches `linkage_graph` there.
- **M8 GREEN.** No fixture document had an `agents:` block, so the attribution
  I had just written was unasserted. Closed by adding one — and it matters:
  the store has **no record kind for an agent assignment**, so that half of the
  register is only ever a document reference, and reading the store *instead of*
  the document retired all 16 of `001-linkage.md`'s entries for every phase.
- **M5 GREEN.** `linkage_document_phase` asks the filename first and the
  document's `phase:` field second; every register on this project declares
  both, so nulling the filename branch changed no answer. Not an equivalent
  mutant — the filename is what survives a register that declares no `phase:`
  at all. Closed with a document that has none. M5b then proves the derivation
  as a whole is guarded.

### Two existing tests re-aimed, with the reasoning recorded

Both asserted the exclusive rule — the defect written down — and the reasoning
is in their docstrings, not only here.

- `test_site_3_perry_task_names_the_store_and_its_line` asserted
  `assertNotIn("003-linkage.md", refused)`, i.e. that the refusal must name the
  store *instead of* the document. That requirement **is** FAIL 2. What it was
  really protecting — that site 3 has moved to the store — is still measured,
  and by a stronger refutation: the fixture's two halves disagree about which
  KR holds the row, so a reader still on the document names neither
  `linkage.jsonl:` nor `KR1`.
- `test_site_3_uses_no_regex_over_the_store` scanned a window running to the end
  of the function. DESIGN-015's claim is about `linkage.jsonl` — one JSON object
  per line is `json.loads`. The register **document** did not become JSONL and
  is still *"markdown with a YAML-shaped block in it"*. The window now ends at
  the store scan; ending it at the whole function forbids reading the document
  at all, which is the defect.

## 7. What row C got right, not regressed

- **The drift verdict is real.** `bin/perry-lint --root .` still prints
  `linkage store: 121 record(s), 0 row(s) drifted`, and planting the row's own
  mutation (`P003-O1-KR1` `target` 6→99) in a scratch copy gives
  `⚠ [linkage-store-drift] P003-O1-KR1 differs between the store and
  phase/003-linkage.md` and `121 record(s), 1 row(s) drifted`. Restored: clean.
- **Site 4 and site 5 untouched**; `perry-lint`'s per-phase authority — the
  catch this row is credited with — is exactly as it was.
- **One review finding closed incidentally.** A `kr` record for a phase with no
  register document used to leak into another phase's render
  (`krs --phase 003` printed `P004-O1-KR1`); it no longer does. The drift
  verdict still cannot see such a record — that is `TASK-375`, untouched.

## 8. The two exhibit corrections, counted myself

Counted from the documents with `parse_linkage`, inheriting neither figure:

| | phase 001 | phase 002 | total |
|---|---|---|---|
| KRs | 8 | 8 | **16** |
| `unlinked` declarations | 23 | 4 | **27** |
| KRs carrying a non-empty `tasks[]` | 6 | 8 | **14** |
| individual edges | 18 | 13 | **31** |
| `agents[].tasks` entries | 16 | 0 | **16** |

The review is right and the row's **"12 edge lists" matches neither 14 nor 31**.

The second correction — that the `JSONDecodeError` branch is **reachable** — I
confirm and have acted on. `linkage_graph` returns the `document` argument
itself on the `None` fallback and `Register` passes `self.model`, so
`reg.graph` **is** `reg.model` and a task the document declares unlinked does
request a retraction. The branch's code was correct, so nothing hid behind it;
what was wrong was the claim that it needed no guard. The test is re-aimed at
the live path, the source comment no longer asserts something false, and M9
(the review's green V1) is now red.

## 9. Findings filed, not fixed

1. **`perry-lint:1611`** — the store's `unlinked` sweep goes to zero for a
   store-covered phase that is not current. Armed for phase 004. Same category,
   untouched: no current input reaches it and it is not one of the two defects.
2. **`perry-lint._linkage_records_for_phase`** stays a third spelling, on
   purpose (§ 3).
3. **`parsers.py` `linkage_from_store` docstring** still says the store/document
   split is read off `schema/state-schema.json`; the field list is hardcoded.
   Unchanged by me.
4. **`perry-task:2739 linkage_edge_change`** (row D) can append an `edge` whose
   `kr` names a phase the store holds no `kr` record for. The store is then not
   the authority for that phase, so the edge renders nowhere and the drift
   verdict does not see it. Reachable via `add --kr` today.
5. The review's other uncaught drift classes (duplicate `kr` id, order-sensitive
   `tasks` comparison) are `TASK-375`'s and untouched.

## 10. What I did not check

- **`perry-goals plan-phase` / `score-phase` writing `kr` records for a future
  phase.** This is where finding 1 becomes live, and I did not exercise it.
- **Whether `add --kr` for a phase-001 KR produces a wrong render end to end.**
  I reasoned it from the code (finding 4) and did not run it.
- **Rows E and F.** The document strip and the computed `P003-O3-KR2` are not in
  this base; I did not reason about whether these fixes survive them.
- **Projects other than Perry.** `tests/fixtures/sample-project*` carry no
  `linkage.jsonl`, so the store-absent path is exercised only by unit fixtures.
- **The full 118-module suite under each mutation.** M0–M9 were graded against
  the 8 modules listed in § 6 with a 0-red control. A mutation I called red
  might also be red elsewhere; more importantly, none was called **green** at
  the end, so no green rests on that narrowing.
- **`perry-lint`'s own per-phase helper under mutation.** I did not re-plant the
  review's V3 against site 4, because I did not change it — its guard is the
  review's V2, which it already passes.
- **Concurrency.** I ran alone in my own worktree; I did not test interleaved
  `purge` and `link` against one store.
- **The union's cost.** `live_references` now reads every `phase/*-linkage.md`
  on every removal check. Three files here; I did not measure it on a project
  with many phases.
- **Whether `TASK-027` and the other 21 rows are now protected by the register
  rather than by luck.** I fixed the mechanism and verified the three the FAIL
  named; I did not re-sweep all 30.
