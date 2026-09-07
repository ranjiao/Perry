# TASK-276 — V4 review

Reviewer: review agent, worktree `agent-a09eebcc4be909030`.
Criteria: `perry/evidence/2026-09/TASK-276-spec.md` — the only authority.
Range: `45923e7^1..d1ceb58` (merges `45923e7`, `61cead6`, `555ced0`, `d1ceb58`).
Design: `perry/design/DESIGN-015-linkage-is-a-store.md` § 5.1, plan row A.

**Result: PASS.**

---

## 0 · Environment, and two things that had to be corrected first

**The worktree was at the wrong commit.** On entry `HEAD` was `d49964e`
(2026-09-02), which predates the whole range: `perry/evidence/2026-09/` did not
exist and neither did `perry/linkage.jsonl`. The prompt's premise — "the file
now EXISTS on your branch (TASK-277 imported 121 records)" — holds only at
`main`. I verified the branch carried **no commits of its own**
(`git log main..HEAD` empty, `merge-base` == `HEAD`, `git status --porcelain
-uall` empty, no stashes), so a fast-forward could not discard anyone's work,
and fast-forwarded to the **pinned SHA `1032e76`**. Every ref in this document
is that pinned SHA, never the moving `main`.

**A second agent shares this session's scratchpad.** Mid-round, my mutation
harness `mutate.py` was overwritten by a harness belonging to a *different*
review (TASK-277, worktree `agent-a0226103415fff483`, ref `b493493`), which
also created `mut/`, `w277/`, `base/` and `run_m1.py` in the same directory.
I re-verified both scratch copies against the ref (pristine), renamed my
harness `mutate276_a09ee.py`, and re-ran from there. The M1 result predates the
overwrite and used my own harness. Recorded as finding **F8** — it is an
isolation defect in the harness, not in this row.

**Load.** Load average ran 6.93 → 11.41 during the round. **No timing figure in
this document is offered as evidence**, and I measured none.

### Baseline, measured in this worktree at `1032e76` before any change

| Measurement | Result |
|---|---|
| `bash tests/run` | **exit 1** — 116 modules · 3320 tests · **1 module red, 1 test failed** |
| the red | `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` — `'LOAD-03' unexpectedly found` |
| re-run alone | **reproduces** (`tests/test_diagnose.py:561`) — a genuine pre-existing red, not a flake, not load-sensitive |
| `python3 bin/perry-lint --root .` | **0 error(s), 38 warning(s)** |
| linkage census line | `linkage store: 121 valid record(s), comparison incomplete — drift is unchecked, not clean` |

The red is about Perry's own state tripping `LOAD-03`; it is unrelated to
`claims[]` and to this row. Per the standing rule I re-ran it alone before
attributing it.

**I did not write to the project under review.** Every destructive check ran in
a `git archive` copy under the scratchpad (`copyA`–`copyD`, `copyBase`). Final
integrity check: `git status --porcelain -uall` empty, and
`bin/perry-restore-check 1032e76` reports ✓ for `schema/state-schema.json`,
`bin/perry-lint`, `tests/test_linkage_store_declared.py`,
`tests/test_store_drift.py` and `perry/linkage.jsonl`.

---

## 1 · Criterion 1 — the census resolves it, exits 0, adds no collision

`python3 bin/perry-lint --claims --root . --json` → **exit 0**, and:

```
linkage.jsonl -> {"state": "perry", "owner": "perry", "detail": "1 existing Perry file(s)"}
claimed 25 · collisions 5
collision paths: ['evidence/', 'handoff/', 'intake.jsonl', 'knowledge/', 'phase/']
```

The criterion says *adds no new collision*, which is a delta, not a count. I
measured the delta by deleting the `claims[]` entry (lines 1034–1040) in a copy
and re-running:

| | claimed | collisions | collision set |
|---|---|---|---|
| with the claim (shipped) | 25 | **5** | evidence/, handoff/, intake.jsonl, knowledge/, phase/ |
| claim removed | 24 | **5** | *identical* |

The claim adds one claimed path and **zero** collisions. **PASS.**

## 2 · Criterion 2 — absent must be `unchecked`, not `clean`

The row's most important property. Tested in `copyA` by moving
`perry/linkage.jsonl` aside — **in the copy**, never in the live tree, per
`review-constraints.md § You are a reader`.

Human-readable, store absent:

```
· no `linkage.jsonl` — drift against the linkage store is unchecked, not clean
```

Machine-readable (`--json`): `store_present: false`,
`comparison_performed: false`, `records: 0`. The word `clean` appears on no
linkage census line in any state. Restore verified by byte comparison against
`git show 1032e76:perry/linkage.jsonl` — an independent source, not a digest of
what I wrote back; `copyA` and the live tree both hash `025ab97c1581f7cb`.

I also drove the two other reachable states with hand-built input (`copyC`),
which is what a user editing the store can actually produce:

| Input | Reported |
|---|---|
| `kind: "bogus"` | `` `kind` is 'bogus', expected one of edge/kr/unlinked `` |
| `task: "not-a-task-id"` | does not match `^TASK-\d+$` |
| `via: "teleport"` | does not match `^(add\|link)$` |
| `declared_at` omitted | `is missing and is required` |
| `target: "SIX"` | `is str, expected number` |
| one unparseable line | `linkage-store-unreadable … nothing here to check` |

In every case the census line still ends `unchecked, not clean`. **PASS.**

## 3 · Criterion 3 — the three record schemas, field for field

Read from `DESIGN-015 § 5.1` itself, not from the result's paraphrase:

| kind | DESIGN-015 § 5.1 | `stores.declared` | |
|---|---|---|---|
| `kr` | kind, phase, objective, id, title, target, current, stretch, linked, current_provenance | identical | ✓ |
| `edge` | kind, task, kr, declared_at, actor, via | identical | ✓ |
| `unlinked` | kind, task, declared_at, actor, via | identical | ✓ |

`metric` is absent from `kr` (Decision 2) ✓. There is no fourth kind (§ 5.2) ✓.
The `claims[]` entry carries `owner: perry`, `anchor: state`, `kind: file` ✓.

The guard's target list (`DESIGN_015_5_1`, `test_linkage_store_declared.py:54`)
is transcribed from the design rather than read back out of the schema, so it
is a real comparand and not a JSON round-trip assertion. **PASS.**

## 4 · Criterion 4 — mutation, and the enumerated battery

Nine mutations, each line-anchored by number, `__pycache__` cleared and the
whole-second boundary crossed on both sides, each restored from
`git show 1032e76:<path>` and re-verified against a **freshly re-read** ref.

| # | Mutation | File:line | Result | Named test |
|---|---|---|---|---|
| M1 | drop the `claims[]` entry (valid JSON, claim absent) | schema:1034–1040 | **RED** | `TestTheClaim.test_linkage_jsonl_is_claimed` + `…test_the_claim_is_owned_by_perry_and_anchored_at_the_state_root` |
| M2 | `owner` `perry`→`work` | schema:1037 | **RED** | `…test_the_claim_is_owned_by_perry_and_anchored_at_the_state_root` |
| M3 | `anchor` `state`→`project` | schema:1038 | **RED** | same |
| M4 | `discriminator` `kind`→`type` | schema:832 | **RED** | `TestTheCensusCountsIt.test_the_records_it_counts_are_the_ones_the_schema_declares` |
| M5 | `kr` loses `current_provenance` | schema:888 | **RED** | `test_each_kind_carries_exactly_the_fields_design_015_spells` |
| M6 | `edge` loses `via` | schema:924 | **RED** | `test_via_distinguishes_add_from_link_and_is_required` (+2) |
| M7a | absent line drops `drift against the` | perry-lint:5286 | **RED** | `test_with_the_file_absent_the_line_says_unchecked_not_clean` |
| M8 | census line removed entirely | perry-lint:5283 | **RED** | 6 tests incl. `test_the_census_prints_a_line_for_the_seventh_store` |
| M9 | census removed, vs the drift census | perry-lint:5283 | **RED** | `test_every_declared_store_has_a_line [linkage.jsonl]` |

**9 of 9 red. No green mutation.** Restore verified 9 of 9.

M4 and M7a are the two the author reports as having been **GREEN** during their
own round (result § 7, M9/M10) and fixed in `75a016f`. Both are genuinely red
now — the fix is real, not asserted. M4 in particular confirms the declared
`discriminator` is now *read* by `_linkage_record_findings` rather than being a
key nothing consults.

## 5 · The author's central argument, tested rather than restated

The claim: **zero deletions proves no existing claim's path or owner was
modified.**

*Is the arithmetic true of the range?* Yes, and I counted deletion **lines**,
not the summary: `git diff 45923e7^1..d1ceb58` restricted to each file yields
`0` lines matching `^-[^-]` for **both** `schema/state-schema.json` (148/0) and
`bin/perry-lint` (190/0).

*Does it hold across all four merges, or only the first?* It holds cumulatively,
but the per-commit history is **not** deletion-free, and the author's phrasing
does not say so. `75a016f` ("fix both GREEN mutations") deletes 2 lines from
`bin/perry-lint`; the arithmetic is 182 + 10 − 2 = 190. I inspected those two
lines: they are `kind = rec.get("kind")` and one f-string, **both introduced
earlier in the same range** by `8272d95`. So no line that existed at the range
base was removed or altered, and the cumulative claim survives contact with the
per-commit history. Worth stating precisely, because "insertions only" read as
a property of every commit would be false.

*Is the argument sound?* For its actual scope, yes. A modified line appears as
deletion + insertion, so a deletion-free range diff does prove no pre-existing
line changed — which covers `claims[]`, the six existing store checks, and, the
part that matters most here, the **six DESIGN-015 § 5.6 reader sites**. Two of
those six live in `bin/perry-lint`, so "no reader moves" is a real risk on this
row, and zero deletions is what discharges it: the 190 added lines are a new
`check_linkage_store_drift` function plus a new census branch, not an edit to
the existing linkage checks. `TestNothingElseInClaimsMoved` pins the same fact
from the other side against a hardcoded pre-TASK-276 list, which is the right
construction (an independent comparand, not a re-read of the file under test).

Where the argument does **not** reach: zero deletions says nothing about what an
*addition* can do to an existing claim's behaviour — shadowing, or a new NS-01
collision. That is why criterion 1 is a separate measurement, and I measured it
as a delta (§ 1) rather than accepting the count.

## 6 · Findings — none of them a FAIL on this row

**F1 · The claim becomes an NS-01 collision the moment the store exists.**
Reproduced against the **reviewed** code at `d1ceb58` by planting the real
121-record store (TASK-277's own import) into a copy:

| `d1ceb58` | collisions | linkage.jsonl |
|---|---|---|
| store absent (state at the row) | 5 | `state: free` |
| store present | **6** | `state: collision` — *"1 file(s) Perry did not write, e.g. perry/linkage.jsonl"* |

Perry tells the user to `/perry relocate` away from Perry's own store. TASK-277's
own commit message confirms this fired in reality.

**This is not a FAIL on TASK-276**, for a reason I established by enumeration
rather than by argument. I enumerated *all eight* declared `.jsonl` claims
against `looks_like_perry_record` at the range base `45923e7^1` — before this
row existed:

```
.perry/events.jsonl  True     tasks.jsonl  True     okr.jsonl  True
risks.jsonl          True     asks.jsonl   True     .perry/config.jsonl True
intake.jsonl         False   <-- NS-01, already broken at the range base
```

The defect class **pre-exists TASK-276**: `intake.jsonl` fails identically today
and is one of the 5 baseline collisions. TASK-276 joined an existing pattern
("declared before it exists, like `intake.jsonl` and `asks.jsonl`") rather than
inventing one; importing is explicitly row B and out of scope; and on this
project at this commit the file is absent, so the row's own criterion — *adds no
new collision on this project* — is met on the measurement, not on a technicality.

**F2 · The class survives at `1032e76`.** TASK-277's `_matches_a_declared_store`
fixes `linkage.jsonl` by reading `stores.declared`, but `intake.jsonl` is still
`False` and still collides. Worth its own row: the remaining store is the one
whose shape is not declared in `stores.declared`.

**F3 · The spec contradicts itself about `bin/perry-lint`.** *Deliverable* says
"`git diff --stat` should touch `schema/` and `tests/` only", but *Files in
scope* lists `bin/perry-lint` conditionally and *Verification* demands the
absent-file census line, which cannot exist without perry-lint code. Two of
three sections require the file the third forbids. The code satisfies the two
operative sections; the sentence in *Deliverable* is the one that is wrong.
A spec-drafting matter to raise as a separate row, not a defect in the change.

**F4 · Undeclared fields pass silently.** A record carrying
`"extra_field": "surprise"` validates and counts as good. The declared field
sets are used as a *lower* bound, never an upper one. Permissive, not wrong —
DESIGN-015 does not require closed records — but row B's import would be
better protected if it were strict.

**F5 · One bad line disables validation of the whole file.** The parse is a
single comprehension inside one `try`, so a stray line yields
`linkage-store-unreadable` and **0 records validated** rather than 120 validated
and one reported. It still reports `unchecked, not clean`, so the direction is
safe.

**F6 · `if not declared: return []` mis-states an existing file.** With the
`stores.declared` block absent but the file present, the census prints "no
`linkage.jsonl`" though it exists (`store_present` is set only after that
return). Conservative direction — it never claims `clean` — and not reachable
without hand-editing the schema.

**F7 · Exhibit arithmetic is stale.** The result quotes `bin/perry-lint | 187`;
the range is 190, because the exhibit was written before `75a016f`. A
pre-check/documentation matter, explicitly not a FAIL at V4.

**F8 · Scratchpad isolation.** Another review agent overwrote a file in this
session's "session-specific, isolated" scratchpad (§ 0). Harness hygiene, not
this row.

**F9 · `perry-restore-check --root` cannot verify a scratch copy.** `--root`
repoints its *git* queries too, so against a `git archive` copy it answers
`<ref> is not a commit in <copy>` — the exact use `review-constraints.md`
recommends. I fell back to byte comparison against `git show`.

---

## 7 · Verdict reasoning

All four criteria in `TASK-276-spec.md § Verification` are met on measurement:
the census resolves the store and exits 0 with an unchanged collision set; the
absent-file line says `unchecked, not clean` in both human and machine output;
the three record schemas match `DESIGN-015 § 5.1` field for field with `metric`
absent and no fourth kind; and reverting the `claims[]` entry turns named tests
red. Nine of nine mutations are red. No reader and no writer moved — proven by a
deletion-free range diff over the two files that contain four of the six § 5.6
reader sites, and independently pinned by `TestNothingElseInClaimsMoved`.

The one behaviour that is genuinely wrong on a producible input (F1) is a
pre-existing defect class demonstrated by `intake.jsonl` at the range base, is
scoped out of this row by the spec, and was fixed in the row that produced the
input. It is not this row's FAIL.

```
=== VERDICT ===
task: TASK-276
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-276-spec.md
checked: Baseline measured in THIS worktree at pinned 1032e76 before any change - `bash tests/run` exit 1, 116 modules/3320 tests, 1 red (test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks, LOAD-03), re-run ALONE and reproduced, pre-existing and unrelated; `perry-lint --root .` 0 errors/38 warnings. Criterion 1: `perry-lint --claims --root . --json` exit 0, linkage.jsonl resolves state=perry/owner=perry; collision DELTA measured by deleting the claims[] entry in a copy - 25 claimed/5 collisions vs 24/5, identical collision set, so zero new NS-01. Criterion 2: store moved aside IN A COPY (copyA) - line reads "no `linkage.jsonl` - drift against the linkage store is unchecked, not clean", --json store_present=false/comparison_performed=false, word "clean" on no linkage line in any state; restore byte-verified against `git show 1032e76:perry/linkage.jsonl`. Criterion 3: three record schemas read against DESIGN-015 section 5.1 in the design itself, not the result's paraphrase - kr/edge/unlinked field sets identical, `metric` absent, no fourth kind, claims[] owner=perry anchor=state kind=file. Criterion 4 + battery: 9 line-anchored mutations, pycache cleared and whole-second boundary crossed both sides, each restored from `git show 1032e76:<path>` re-read fresh - M1 claims[] entry dropped, M2 owner, M3 anchor, M4 discriminator, M5 kr field, M6 edge via, M7a census wording, M8 census emission, M9 census vs test_store_drift - 9 of 9 RED, 0 green, 9 of 9 restores verified. Author's central argument tested not restated: 0 lines matching ^-[^-] in BOTH files across the whole range; per-commit history is NOT deletion-free (75a016f deletes 2 lines of bin/perry-lint) but both deleted lines were added earlier in the same range by 8272d95, so no pre-range line changed and the cumulative claim holds across all four merges; this is what discharges "no reader moves", since 2 of the 6 DESIGN-015 section 5.6 reader sites live in bin/perry-lint. Enumerated the NS-01 category rather than the instance: all 8 declared .jsonl claims run through looks_like_perry_record at the range base 45923e7^1, at d1ceb58 and at 1032e76 - intake.jsonl already False at the base, so the class pre-exists this row. Validator driven with hand-built user-producible input (bad kind, bad pattern, missing required, wrong type, unparseable line). All destructive work in git-archive copies (copyA-D, copyBase); live tree finished `git status --porcelain -uall` empty with perry-restore-check 1032e76 green on all five reviewed files.
not-checked: I did not re-run the full `bash tests/run` AFTER the mutation battery - the battery ran in scratch copies and the live tree is byte-verified unchanged against 1032e76, so the baseline still describes it, but I have no post-round full-suite number of my own. I did not attribute or fix the pre-existing test_diagnose LOAD-03 red beyond reproducing it alone. I did not review tests/test_board_render.py or tests/test_host_support.py on their merits: `git log --name-only` attributes their changes in this range to TASK-356 and TASK-357, not TASK-276, and they are in the range only because it spans four merges. I did not verify tests/durations.json's recorded cost is accurate - the machine was loaded (load average 6.93-11.41) so no timing figure in this round is evidence, and I measured none. I did not test row B/C/D behaviour (import, reader moves, `add --kr` writing edges) - all out of scope. I did not exercise the Chinese-locale fixture path for the linkage census beyond what `bash tests/run` covers. I did not check whether `stores.declared` is consumed anywhere outside bin/perry-lint. F4 (extra undeclared fields pass) and F5 (one bad line voids validation of the whole file) are reported but I did not enumerate every malformed shape.
proof: n/a - PASS. The nearest thing to a defect, F1, is reproducible (at d1ceb58, planting the real 121-record store makes `perry-lint --claims` report collisions 5->6 with linkage.jsonl "1 file(s) Perry did not write", via bin/perry-lint `looks_like_perry_record` returning False for a linkage record), but it is a PRE-EXISTING class - intake.jsonl returns False identically at the range base 45923e7^1, before this row - it is scoped out of TASK-276 by the spec's "Out of scope: Importing any data - that is row B", and the spec's criterion is "no new collision ON THIS PROJECT", where the file is absent and the measured delta is 5->5. Raise F1/F2 (intake.jsonl still unrecognised at 1032e76) and F3 (the spec's Deliverable forbids the bin/perry-lint edit its own Verification section requires) as separate rows.
=== END VERDICT ===
```
