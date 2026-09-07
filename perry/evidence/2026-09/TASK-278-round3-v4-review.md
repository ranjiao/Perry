# TASK-278 — round 3 V4 review

> Criteria: `perry/evidence/2026-09/TASK-278-spec.md`, the only authority.
> Base pinned at **`e928ed4`**. Every destructive probe was `--dry-run` inside a
> `git archive` copy at `/tmp/v4-278-r3rev/` — **outside the repository**
> (`TASK-373`, `TASK-385`). The primary checkout at `/Users/bytedance/proj/Perry`
> was not touched, and nothing was written into a board cell.

**Result: PASS.**

## 0. Base — it was wrong again, and I reset

The worktree I was handed was at **`d49964e`**, an ancestor of `main`, with a
clean tree and **no commits of its own**. `TASK-381` for the tenth time.

```
git merge-base --is-ancestor e928ed4 HEAD   ->  NO     (bad base)
git log --oneline main..HEAD                ->  (empty)
git status --porcelain                      ->  (empty)
```

Reset onto **`e928ed4`**, which is `main`'s tip at the time of this round;
`git merge-base --is-ancestor e928ed4 HEAD` now passes. All four round-3
commits (`0d23b5b`, `42b355c`, `0909998`, `d46fb18`) are ancestors of my HEAD,
so the code I review is the code that was merged.

**Round 3's four commits touch exactly two paths** — `bin/perry-task` and
`tests/test_linkage_store_readers.py`. Nothing else. That matters twice below.

## 1. Baseline — the dispatch's number is right, and two extra reds were mine

`bash tests/run` in the scratch copy, twice:

| run | modules · tests | red |
|---|---|---|
| 1 | 120 · 3448 | the 3 predicted **+ `test_one_header_rule` + `test_tree_guard` (8 errors)** |
| 2 | 120 · 3448 | **the 3 predicted, and only those** |

The two extra reds were **artifacts of my own scratch copy**, not of the tree:
a `git archive` extract is not a git repository, and both modules ask git about
it — `test_tree_guard` died on `git rev-parse HEAD` *failed*, and
`test_one_header_rule.test_git_tracks_answers_both_ways` on
`_git_tracks(PERRY_HOME/bin/perry-lint)` returning False. I did not assume
that: I made the copy a repository and both went green (`test_one_header_rule`
18 tests OK). **Recording it because the next round will hit it too** — a
`git archive` scratch copy reddens two modules for reasons that have nothing to
do with the code.

Confirmed baseline, matching the dispatch exactly — **3 red modules / 4 red
tests**:

| module | failing test(s) |
|---|---|
| `test_contract_key_parity` | `test_without_the_witness_the_four_are_unobservable`, `test_the_same_mutation_is_silent_without_the_witness` |
| `test_diagnose` | `test_perry_itself_passes_its_own_id_checks` |
| `test_linkage_import` | `test_the_store_accounts_for_the_register_in_both_directions` |

Per `knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` I did
not settle `test_contract_key_parity` on one run: it is red in **both** full
parallel runs, which is the direction round 3 warned about. **No new failures.**

## 2. The Bound — the axes are not the right axes, and 16 is not the size

This is the round's strongest claim and it is **wrong about its own size**. It
is wrong in the safe direction, and the code covers the cells the Bound misses,
which is why this is a finding and not the FAIL.

**Axis 1 (7 value branches, 4 id-carrying) is correct.** I re-derived it from
`viewer/parsers.py § parse_map` independently rather than reading the table:
`rest` non-empty → `scalar()` (flow list / block-scalar sentinel / bare scalar
= 3), `rest` empty with the next line deeper → `parse_block` (list / map = 2),
`rest` empty with a `- ` at the key's own indent → `parse_list` (1), else
`None` (1). Seven. The four that survive `_as_list` as an exactly-matching id
are the flow list, the bare scalar, and both block lists. Confirmed empirically
in § 3.

**Axis 2, "the KEY spelling — exactly 2", is not 2.** `parse_map` does
`key.strip().strip("\"'")`, and `str.strip` removes *any run of either quote
character from both ends*. `tasks`, `"tasks"`, `'tasks'`, `""tasks""` and even
`"tasks'` all normalise to the same key. The spelling set is unbounded, not
binary. It is a correct *behavioural* partition — locator-matched versus not —
but a Bound is a claim about a set's size, and this one counts a partition and
calls it an enumeration.

**A placement sits outside the three-axis model entirely.** A KR is a *list
item*, and `parse_list` has its own `- key: value` branch
(`viewer/parsers.py:3735-3743`) that `parse_map` never sees:

```yaml
    krs:
      - tasks: ["TASK-087"]
        id: P002-O3-KR2
```

This is a real, lint-clean edge that every reader honours, and the locator's
`(\s*)tasks:` cannot match a line whose first non-space character is `-`. It
cannot be a cell of "`parse_map` value × key × location" because it is not
parsed by `parse_map` at all. Measured as shape **H** below: the guard
**refuses** it (`line not located`) — the code is right, the Bound does not
contain it.

Note in passing that `parse_list`'s branch does **not** strip quotes from the
key, unlike `parse_map` — so the two halves of the parser disagree about key
spelling. That asymmetry is a `viewer/parsers.py` finding, not this row's.

**The "last element" claim holds.** A flow list split across physical lines
raises `unexpected indent` in `parse_yaml_subset`, so the register declares
nothing — I reproduced this. The set is closed; it is just larger and shaped
differently than the document says.

## 3. The shape space, measured — 15 cells, one invariant, zero violations

I did not re-run round 3's differential, which the PMO had already verified.
I built the enumeration instead: every cell rewrites
`perry/phase/002-linkage.md:69` (line-anchored, asserted against the old text),
then measures three things — does `perry-lint` accept the register, does a
**reader** honour the edge (`parse_linkage(...).kr_for_task('TASK-087')`), and
what does `purge --dry-run` do. `TASK-087` was confound-swept first (§ 5).

| cell | lint | reader honours | `purge TASK-087 --dry-run` |
|---|---|---|---|
| A flow list (shipped shape) | 0 err | yes | REFUSED `002-linkage.md:69 krs[].tasks` |
| B block scalar `tasks: \|` | **1 err** | no | not refused |
| C bare scalar | **1 err** | yes | REFUSED `:69` |
| D block list, deeper indent | 0 err | yes | REFUSED **`:70`** — the item line |
| E block list, key's own indent | 0 err | yes | REFUSED **`:70`** |
| F nested map | **1 err** | no | not refused |
| G empty value | 0 err | no | not refused |
| A2 flow list, `"tasks":` | 0 err | yes | REFUSED `(line not located)` |
| A3 flow list, `'tasks':` | 0 err | yes | REFUSED `(line not located)` |
| D2 block list, quoted key | 0 err | yes | REFUSED `(line not located)` |
| D3 block list, comment **before** item | 0 err | yes | REFUSED **`:71`** |
| D4 block list, comment **between** items | 0 err | yes | REFUSED **`:72`** |
| D5 block list, blank line between items | 0 err | yes | REFUSED **`:72`** |
| H `- tasks:` inline list-item key | 0 err | yes | REFUSED `(line not located)` |
| H2 `- "tasks":` inline | **1 err** | register does not parse | not refused |

**The invariant: `purge` refuses exactly the cells a reader honours, and only
those. 11 of 11 honoured cells refused; 4 of 4 unhonoured cells proceeded.**
Every cell that proceeds is one where no reader resolves the edge, and three of
those four are registers `perry-lint` grades as **errors**.

**That invariant is a proof, not a sample.** `Linkage.kr_for_task`
(`viewer/parsers.py:1197`) iterates `objectives → krs`, returning on
`task_id in kr.tasks`. The structural half of `live_references`
(`bin/perry-task:5091-5100`) iterates the same two levels with the same
membership test and *does not short-circuit*, so it is a strict superset of
what any `parse_linkage` reader can resolve; `agents[].tasks` is checked
separately with the same test. A reader cannot honour an edge the guard fails
to declare. Round 1's data-loss category is closed by construction and not by
fixture count.

## 4. Where I pressed hardest

**M9 — is the structural half load-bearing on an input a user can produce?
Yes, and on better inputs than the round claims.** Round 3 says the quoted key
is the only such input and concedes it is exotic. It is not the only one: shape
**H** (`- tasks:` as a list item's first key) is lint-clean, reader-honoured,
and invisible to the locator, and it is *not* reachable by widening the locator
regex to accept quotes — the line begins with a dash. So the structural half is
required by a second, independent shape, and round 3's own justification for
keeping it is stronger than the one it wrote down.

At the test level the closure is real, not narrative: my mutation **V3**,
which empties the `declared - located` fallback, turns two named tests red —
`test_site_3_a_quoted_tasks_key_is_caught_by_the_structural_read_alone` and
`test_site_3_a_quoted_agents_tasks_key_is_caught_structurally_too`. The
deliverable is no longer dead weight.

**The M5 comment gap is CLOSED, not carried.** The dispatch asked whether a
comment inside a block list still defeats the region scanner. It does not:
`bin/perry-task:4916` skips blank and `#` lines instead of breaking, and cells
D3/D4 locate the item line correctly (`:71`, `:72`). Mutation **V1**, removing
the `#` clause from that line, goes red on
`test_site_3_a_comment_between_block_items_does_not_end_the_scan`. It matters
for `purge` and it is asserted.

**The unlocatable refusal is the right trade.** A quoted-key or inline-key
register refuses with `TASK-087 is named by 002-linkage.md krs[].tasks (line
not located)` — the user gets the file and the field path, loses only the line
number, and can `grep`. The alternative is not "refuse with a line": it is
widening a regex that still cannot reach shape H, in exchange for removing the
only inputs that hold the structural half honest. It **fails closed**, which is
the only property that is irreversible if lost. I judge the choice correct.

## 5. Confound sweep — done independently, and one path round 3 missed

`TASK-087` appears **once** in `perry/tasks.jsonl` (its own record: `next_action`
empty, `evidence` a `.py` file, `status: done`, `order: null`), and **zero**
times in `perry/BOARD.md`, `perry/okr.jsonl` and `perry/linkage.jsonl`.
`TASK-278`'s own `next_action` no longer names any probe id — the round-1 trap
is genuinely out of the cell.

**Round 3's sweep checked four files and stopped there; the evidence-citation
path is a fifth and it is live.** `live_references` walks markdown cited by a
*surviving* record's `Evidence` cell, and `TASK-087` is named in
`TASK-278-v4-review.md`, `TASK-278-round2-v4-review.md` and
`TASK-278-round3-result.md`. It happens to be harmless — `TASK-278`'s evidence
cell cites only `TASK-278-result.md`, which does not name `TASK-087`, and no
record cites the `evidence/2026-09/` directory — but that is luck, not sweeping.
If a future round points `TASK-278`'s evidence cell at a review file, the probe
ids become live references and every differential silently self-confounds.

**This file names `TASK-087`, `TASK-028` and `TASK-046`.** Any later round
probing those rows must sweep the evidence-citation path, not just the four
state files, and strip this file in its scratch copy.

## 6. Rounds 1 and 2's wins — not regressed

| win | measured at `e928ed4` |
|---|---|
| `krs --phase 001` | its own eight, `P001-O1-KR1 … P001-O3-KR2` |
| `krs --phase 002` | its own eight, `P002-O1-KR1 … P002-O3-KR2` |
| `krs --phase 003` | its six `P003-*` |
| three flow probes | `TASK-028` → `001-linkage.md:16 krs[].tasks (and 1 more: 001-linkage.md:105 agents[].tasks)`; `TASK-046` → `:24` + `:103 agents[].tasks`; `TASK-087` → `002-linkage.md:69 krs[].tasks` — byte-identical to round 2's record |
| `perry-lint --root .` | `0 error(s), 29 warning(s)` |
| drift is real | planting `kr` `target` **6 → 99** on `P003-O1-KR1` moves `1 row(s) drifted` → **`2 row(s) drifted`** and names `P003-O1-KR1`; restored byte-identical against the ref |

**The drift number moved and it is not this row's doing.** The store reads
`123 record(s), 1 row(s) drifted`, not round 2's `121 record(s), 0 row(s)
drifted`. The drifted row is `P003-O3-KR2`. Round 3's commits touch only
`bin/perry-task` and one test file — neither is read by `perry-lint`'s drift
comparison — so the change is live state (`TASK-382`/`TASK-383` filed with
`--kr`), exactly as round 3 reported. The *capability* is intact, which is what
must not regress.

Likewise `perry-state --section attribution` now reports `linked: 6` where the
spec's verification clause names 5. Same cause, same reasoning: the spec's
clause is an invariance requirement across the change, and `perry-state` does
not read `bin/perry-task`, the only production file this round touched.

## 7. Mutation — 3 planted, control green, one survived

Line-anchored with an assert on the old text; `__pycache__` cleared and a sleep
**past the whole-second boundary** before every run; `bin/perry-task` restored
from `git show HEAD:bin/perry-task` — **my own branch's ref, never `main`** —
and byte-compared. Harness `/tmp/v4-278-r3rev/mutate.py`.

Graded against `test_linkage_store_readers`, `test_linkage_writer`,
`test_linkage_task_exists`. **`test_purge` was dropped from the graded set**:
it cannot be loaded standalone (`ModuleNotFoundError: task_writer_support`), so
its red is a loader artifact and would have made every verdict meaningless.
Control on the remaining three: **GREEN**.

| # | mutation | result | killed by |
|---|---|---|---|
| V1 | `#`-comment skip removed from `bin/perry-task:4916` | red | `test_site_3_a_comment_between_block_items_does_not_end_the_scan` |
| V2 | blank-line skip removed from the same line | **GREEN** | — |
| V3 | `declared - located` fallback emptied | red | both quoted-key tests |

**V2 is a real coverage gap and not a defect.** Nothing asserts that a blank
line inside a block list fails to end the item run. The behaviour is correct —
cell D5 locates `:72` across a blank line — but it is unasserted, so the next
edit to that line can silently take it away. Worth a test, not a row.

## 8. Findings that are not the verdict

1. **The Bound undercounts its own set** (§ 2): axis 2 is a partition, not a
   count of 2, and shape H is outside the model. The prose is wrong; the code
   is right. Per V4's own rule a wrong document is a separate row.
2. **`parse_list` does not strip quotes from keys and `parse_map` does**
   (`viewer/parsers.py:3743` vs `:3705`) — a parser asymmetry worth its own row.
3. **Shape B (`tasks: \|`) still loses the row**, as round 3 disclosed. I
   checked the thing round 3 did not: `perry-lint` grades that register
   **`1 error(s)` — `[bad-type] objectives[2].krs[1].tasks must be a list`**.
   It is not a legal register, and no reader honours it, so `purge` deleting
   the row is consistent rather than lossy. That materially lowers the severity
   round 3 assigned it, and it stays a separate row.
4. **The evidence-citation confound path** (§ 5) belongs in the standing sweep.
5. **A `git archive` scratch copy reddens two git-dependent modules** (§ 1).

## 9. Why this is a PASS

The spec's deliverable is met and its verification clause is satisfied: the
store read is `json.loads` and not a second regex (the regex that remains
locates a line in a *document*, which is what round 2's own FAIL required);
`bin/perry-lint`'s two sites were rewritten rather than deleted in the earlier
rounds and are untouched here; the gate is shown able to go red twice from
independent directions; and the suite shows no new failures against a baseline
I measured twice.

Round 1's defect (per-phase authority, and the exclusive `else:` that let
`purge` delete register-named rows) is closed. Round 2's defect (the block list
defeating a same-physical-line scan) is closed, on a lint-clean register, naming
the item line. Round 3's own defect class — a deliverable that no input made
load-bearing — is closed, and I confirmed it against a second input the round
did not know it had. The guard now refuses exactly what a reader resolves, and
that correspondence follows from the code rather than from the fixtures.

The Bound is wrong about its size. It is wrong in the direction that costs a
refusal a user can clear, never a record that cannot be recovered.

=== VERDICT ===
task: TASK-278
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-278-spec.md
checked: Base reset from the stale d49964e onto e928ed4 (TASK-381) and all four round-3 commits confirmed ancestors of HEAD. Enumerated the register shape space independently from viewer/parsers.py § parse_map / parse_list rather than from round 3's table, and measured 15 cells by rewriting perry/phase/002-linkage.md:69 (line-anchored, asserted on the old text) in a git archive copy at /tmp/v4-278-r3rev, outside the repository: for each cell, perry-lint's grade, whether parse_linkage().kr_for_task() honours the edge, and perry-task purge TASK-087 --dry-run. Invariant held with zero violations — refused in all 11 cells a reader honours (naming the item line 70/71/72 for block lists, and "(line not located)" for the three no locator can reach), proceeded only in the 4 cells no reader resolves, 3 of which perry-lint grades as errors. Closed the invariant as a proof by reading kr_for_task (viewer/parsers.py:1197) against the structural half's loop and showing the guard is a strict superset. Verified round 3's Bound: axis 1's 7 value branches / 4 id-carrying is correct and reproduced; axis 2's "exactly 2" is a behavioural partition, not a count (str.strip removes any run of quote chars); found shape H (`- tasks:` as a list item's first key, viewer/parsers.py:3735) outside the three-axis model entirely, lint-clean and reader-honoured, which the guard nonetheless refuses. Confirmed the M5 comment gap is CLOSED (bin/perry-task:4916; cells D3/D4 locate correctly) and asserted by a named test. Mutation round, 3 planted with a green control on 3 modules, __pycache__ cleared and slept past the whole-second boundary, bin/perry-task restored from git show HEAD:bin/perry-task (my own branch's ref) and byte-compared: V1 comment-skip removed -> red on test_site_3_a_comment_between_block_items_does_not_end_the_scan; V3 declared-minus-located fallback emptied -> red on both quoted-key tests, so the structural half is load-bearing; V2 blank-line skip removed -> GREEN, an unasserted behaviour. Dropped test_purge from grading as unloadable standalone (ModuleNotFoundError: task_writer_support). Independent confound sweep of TASK-087 across tasks.jsonl, BOARD.md, okr.jsonl, linkage.jsonl AND the evidence-citation path that round 3 did not sweep. Rounds 1/2 wins re-measured: krs --phase 001/002/003 each print their own KRs, all three flow probes refuse with byte-identical strings, perry-lint 0 error(s), and a planted kr target 6->99 on P003-O1-KR1 moves the drift verdict 1 -> 2 rows and names the row (restored byte-identical). Full suite run twice in the scratch copy: 120 modules, 3448 tests, settling on exactly the stated baseline of 3 red modules / 4 red tests; the two extra reds in run 1 were proven artifacts of a git archive copy having no git repository, not tree state.
not-checked: bin/perry-lint's two sites (:1200, :1231) — round 3 does not touch perry-lint and I took rounds 1/2's verification of them rather than re-deriving it. The other ~30 register-named rows beyond TASK-028/046/087 were not swept individually; I argued coverage from kr_for_task's structure instead of enumerating rows. I did not mutate against test_linkage_import or test_contract_key_parity (pre-existing reds would make a control meaningless), nor grade any mutation against the full 119/120-module suite — a wider grading can only turn a green red, so V2's green does not rest on the narrowing, but V1's and V3's kills were not checked for collateral. I did not model the interaction with TASK-280's document strip (if phase/<NNN>-linkage.md sheds its schema'd half the union collapses to the store), nor ADR-017 step 2 landing underneath this. No concurrency: no interleaved purge and link. Projects other than Perry, beyond the suite's fixtures. I did not measure how a user actually experiences the "(line not located)" refusal beyond reading the string, and I did not check whether any register outside this repository is written with a quoted or inline key. Whether _tasks_list_regions can over-collect on a shape I did not construct — over-collection costs an over-report, not a deletion, so I treated it as the safe direction as round 3 did.
proof: (n/a — PASS)
=== END VERDICT ===
