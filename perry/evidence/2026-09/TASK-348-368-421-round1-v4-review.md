# TASK-348 · TASK-368 · TASK-421 — round 1, V4

> Reviewer: fresh-context V4, one round, three independent rows
> (`work/reference/review.md § 4`). Bound by `work/reference/review-constraints.md`.
> Branch: `v4-review-348-368-421`, cut from `main` at **`076ae21a`**.
> Worktree: `.claude/worktrees/agent-ab29516bf06aa709f`. The shared checkout at
> `/Users/bytedance/proj/Perry` was never touched.
> Scratch: `…/scratchpad/v4-round-348-368-421-ab29516b/` (session-scoped, and
> the basename carries this worktree's id so no sibling agent picks it).
> **No board row was filed by this round.** Findings are below; which of them
> clear `review.md § 0`'s bar is named in § 0 and left to the PMO.

## Baseline, taken in this worktree before any mutation

`bash tests/run` on `076ae21a`, clean tree, exit 1:

```
✗ 3 of 126 MODULE(S) red
✗ 4 of 3655 TEST(S) failed
```

| red | matches the brief's known list |
|---|---|
| `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable` | yes |
| `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` | yes |
| `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` | yes |
| `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` | yes |

**No fifth failing test.** One non-test red is in the suite output and the brief
did not name it, so it is recorded here rather than absorbed:

```
✗ not in durations.json: test_contract_page_snippets.py — it is on disk and
  will sort as inf and run first by accident, not by decision
```

Every mutation below is judged against this baseline, and any module that was
red here is re-run **alone** before a result is attributed to it.

**Closing run, after the round, on the same clean tree:** `3 of 126 MODULE(S)
red · 4 of 3655 TEST(S) failed`, the same four, and the tree guard reports
`✓ nothing under …/agent-ab29516bf06aa709f moved`. **The red set is unchanged
and this round wrote nothing into the tree it judged.** Every mutation in this
document was applied to a `git archive` copy under the scratch path above, never
to this worktree and never to `/Users/bytedance/proj/Perry`;
`bin/perry-restore-check main bin/perry-task bin/perry-lint bin/perry-tasks
bin/perry_store.py work/reference/dispatch.md
work/reference/review-constraints.md AGENTS.md` passes all eight, and
`git diff --stat main` is this review document and nothing else.

*(Aside, because it bears on this document's own hygiene: the `test_diagnose`
red is `['USER-920', 'V4-1', 'V4-2', 'V4-3'] != []`, and `V4-1`…`V4-3` are
finding labels minted by the `TASK-027` round-4/5 review documents — the exact
cost `review-constraints.md § Do not mint identifiers` names. This round's
findings are therefore numbered in prose and carry no id-shaped label.)*

---

# 1 · TASK-348 — the call-site census of 22 files

Criteria: `perry/evidence/2026-09/TASK-348-spec.md`
Under review: `perry/evidence/2026-09/TASK-348-result.md` (2,689 lines), against
the 22 files at the commit it pins.

## 1.1 The commit question, answered first

The spec's `## Bound` pins **`583f024f`**. The report measured **`7f43a11c`**
and says so in its own first section, on the ground that all 22 files are
byte-identical at the two commits. **Checked, and it is true:**

```
git diff --stat 583f024f 7f43a11c -- <the 22 paths>   → empty
```

So every line number in the report is valid at the pinned commit. Note for
whoever reads the report next, which the report could not have known: **`main`
has since moved past `7f43a11c` and seven of the 22 files have changed**
(`lib/__init__.py`, `perry-diagnose`, `perry-explain`, `perry-knowledge`,
`perry-restore-check`, `perry-state`, `viewer/parsers.py` — +281/−37). The
census is a measurement of a commit, and it must be read against `7f43a11c`,
not against the working tree. Everything below was checked against files
extracted from `7f43a11c`, never against the checkout.

## 1.2 The arithmetic, re-derived independently

This is the criterion the spec makes central — *"The category counts plus the
support bucket sum to each file's line count. An unexplained remainder fails."*
I did not read the report's checker output and believe it. I wrote my own
harvester and my own support extractor
(`scratchpad/…/audit348.py`), pointed it at the **published § 10 tables** and at
the **pinned files**, and recomputed everything from scratch.

Result, all 23 tables (the 22 in scope plus `bin/perry`):

```
files with tables: 23
… every file …                                    CLOSES
```

for every one of: no overlapping regions, no unclaimed code line, no
out-of-range line, no zero-code region, **every row's published `code` column
equal to what my extractor computes for that row's span**, and every per-file
block count equal to my recomputation. Grand totals over all 23 files:

```
  TYPED 6,455 · TRANSPORT 167 · AGENT 847 · OBSOLETE 3,546
  SUPPORT  cli-plumbing 2,769 · imports 355 · docstring 5,930
           comment 4,851 · blank 2,356 · shebang 18
  TOTAL 27,294
```

Subtract `bin/perry` (162 lines, 15 of them TYPED) and that is **exactly § 4.1**:
TYPED 6,440 / TRANSPORT 167 / AGENT 847 / OBSOLETE 3,546 / total 27,132.

The Bound's size figure is confirmed independently too — `wc -l` over the 22
pinned files is **27,132**, and every one of the 22 per-file counts matches the
spec's own list.

**This is the strongest thing in the round.** The report's claim that its tables
*are* the region list, harvestable and re-checkable by a reader who trusts
nothing in it, is true: I harvested them and got its numbers back with an
extractor it did not write.

## 1.3 The honesty claim, tested rather than praised

§ 1d says: 3 files read line by line, 19 delegated (18,627 lines, 69%), ten
delegated regions audited at `random.seed(348)`, one wrong, *"the four category
totals are robust to errors of this size … but an individual row is not."*

I sampled **my own 14 delegated regions** at a different seed (4321) over the
739 delegated rows, and read each against the pinned code.

| verdict | n |
|---|---:|
| correct as published | 13 |
| disputable, 5 lines, argued below | 1 |
| wrong | 0 |

The disputable one is `bin/perry-goals:2621-2629`, called **TYPED** — *"the new
commitment's field values"*. It builds `values` keyed by `Id` / `Track` /
`Promise` / `To whom` / `Due` / `By when note` / `Status` / `Discharged by`,
i.e. by the **header-cell spellings of the rendered `## Commitments` table**,
and lines 2641–2647 consume it as `[values.get(c, "") for c in order]` into
`okr.append_table_row`. Under the report's own uniform rule for
`bin/lib/__init__.py` — *"produces/consumes a markdown cell, row, column, table
or heading → OBSOLETE, whatever it is called"* — these 5 lines lean OBSOLETE.
The defence is real and I record it rather than calling the row wrong: the
values survive the migration re-keyed, and the report put the header read, the
widen and the render immediately next door at `2630-2647` as OBSOLETE, so the
split is a considered one rather than a rounding.

**The claim is confirmed.** A second sample, a different seed, a different
reader: one arguable region in fourteen, worth five lines out of 11,000. The
report's posture — totals robust, individual row not — is the correct one and
it is stated in the report before the results rather than after.

Spot-checks of the other verification criteria, all met:

- **method stated per file** — § 1e, all 22, each naming the discriminator and
  the constructs split by statement map rather than rounded.
- **ambiguous regions listed rather than resolved silently** — § 8, twelve of
  them, each with the cost of the other ruling in lines.
- **negative control** — § 9, ten, in both directions. Its one *empirical*
  control I re-ran: `bin/perry-state --section risks` does return
  `"source": "table"` on this repo while `perry/risks.jsonl` holds 4 records.
  True as published.
- **`bin/perry-conform` does not exist** — confirmed, `ls` returns nothing.
- **"fifteen code files reference `resolve_state_root`"** — confirmed exactly:
  17 files match, minus `bin/README.md` and `bin/ARCHITECTURE.md`, which the
  report itself already says it excluded and why.

## 1.3b The two headline answers, re-derived

The spec makes these the reason the row is P0, so they were recomputed from the
two censuses' own totals rather than read.

**Question 1 — does `TASK-263`'s ratio hold outward?** Every figure checks:
base 5,566 and 11,000, composed 16,566 over 40,127 physical lines;
OBSOLETE:AGENT of **3.05** in `TASK-263`, **4.19** across the 22, **3.68**
composed. So *"the ratio holds and strengthens"* is right. And *"OBSOLETE is the
largest category"* does **not** survive going outward: TYPED is 6,440 against
OBSOLETE's 3,546, a factor of **1.82** — the report says 1.8 — and TYPED is the
largest of the four both in the 22 and in all 24 files composed. The report's
own subsidiary claims check too: the top five files carry **2,861 of 3,546**
obsolete lines (81%), and exactly **ten** files carry none, totalling **4,021**
lines.

**Question 2 — is "condemned in full" true?** 1,775 obsolete lines in 8,505 —
**20.9%** of lines, **45.5%** of the three files' own four-category base of
3,901. "Condemned in full" therefore overstates by **4.79×**, which is the
report's *"about 5x"*. And in `viewer/parsers.py`, the largest single entry in
`DESIGN-014 § 5.1` category B, the largest category really is **TYPED (870)**,
not OBSOLETE (771).

Both answers are arithmetically sound on the census I verified in § 1.2. Their
*force* rests on the category boundary, which is judgement and which § 1.3
sampled rather than re-derived.

## 1.4 Finding — § 6.1's exclusivity claim is false, in the sub-claim the spec asked for

This is the one thing I found that the row had not already absorbed.

§ 6.1 is the finding the spec explicitly requested (*"If a condemned file
carries typed operations nothing else implements, that is a finding"*). Its
first sub-claim:

> `viewer/parsers.py § config_store_records` is **the only reader of
> `.perry/config.jsonl`** in the tree
> … 1. **The only `.perry/config.jsonl` reader and validator** … **No second
> implementation exists.**

**Two other direct readers exist, both under `bin/`, at the pinned commit.**

1. `bin/perry-config § read_records:47-75` — reaches the store itself:
   `store.load_store(path)` then `store.validate_records(on_disk)`, where
   `store` is `bin/perry_md_store.py`. It does **not** go through
   `parsers.config_store_records`. It is a reader *and* a validator, which is
   the exact phrase the sub-claim uses.
2. `bin/perry-context-budget § ceiling:119-140` — opens the store, splits it,
   `json.loads` per line, filters `kind == "setting"`, with **no validation at
   all**. Its own docstring states the duplication as deliberate: *"Read
   directly rather than through `viewer.parsers` on purpose: this tool answers a
   question about the SESSION and must keep working in a directory that is not a
   Perry project at all."*

The report read both files itself — § 1e records `perry-config` as *"R, every
path traced to the file it opens. The only document it touches is
`.perry/config.jsonl`"* and `perry-context-budget` as *"the ceiling comes from
flag/env/store/schema"*. So the evidence to contradict the claim is inside the
same report, two sections apart.

**What it does and does not change.** § 6.2's conclusion — *"Tier B cannot
delete these three files"* — survives, because `perry-config`'s reader still
runs through `perry_md_store` (condemned file 3) and the other four sub-claims
(root resolution, the YAML subset, the ADR reader, the linkage-store reader)
are untouched by this. What changes is the shape of the `config.jsonl` item on
§ 6.2's "something has to own" list: it is not one implementation needing a new
home, it is **three readers of one store, one of them unvalidated**, and a row
written off § 6.1 as it stands would go looking for a single call site and find
three. The narrower claim — *the only reader that goes through `parsers.py`* —
is true and is what the sentence should have said.

**Under `review.md § 0` this is reported and does not fail the row.** It
destroys no state, weakens no gate, and makes no *tool* report a wrong answer —
it is a false statement in a file nobody executes, which § 0 and § 2's table
both route to *file the correction as a row*, never to a FAIL.

## 1.5 Two smaller things, neither a finding

- § 0 says `583f024f..7f43a11c` "is four commits". It is five
  (`git log --oneline` over that range), or three excluding merges. Prose, and
  § 0 of `review.md` puts prose out of scope; recorded only so the next reader
  does not re-derive it.
- **The row arguably should not have been at V4 at all.** `review.md § 0`'s
  *do not send* list names *"work whose deliverable is a measurement rather than
  a change"* explicitly, and this row writes one report and changes no
  behaviour. That is a dispatch observation for the PMO, not a judgement on the
  work, and it is on § 0's own terms *"a decision to record, not an instinct to
  follow"*. I ran the round I was given.

## 1.6 What I could not check on TASK-348

The honest limit is the same one the report names about itself, one level up: I
sampled 14 of 739 delegated regions. **I did not read the other 725, and I did
not read any of the 18,627 delegated lines in full.** My arithmetic check is
total and independent; my *judgement* check is a sample. A reader who needs one
specific region to be right before deleting on it should re-read that region —
which is precisely what § 1d already tells them.

---

# 2 · TASK-368 — eight test modules onto the in-process seam

Criteria: `perry/evidence/2026-09/TASK-368-spec.md`
Under review: `perry/evidence/2026-09/TASK-368-result.md`, the four commits
`5653904f`, `2e67cde6`, `70e4fd75`, `bfc983ea`, merged as `fef35967`.

The spec names the defect this row is most likely to ship, and it names it
precisely: *"A conversion that makes a test faster and blind … because the
in-process path shares module globals the subprocess did not."* So the round is
that question and nothing else.

## 2.1 How the mutations were run

**On a copy, never on the project under review.** `git archive main` into
`…/scratchpad/…/copy`. The shared checkout at `/Users/bytedance/proj/Perry` was
not touched at any point, and neither was this worktree's own `bin/`.

The harness (`scratchpad/…/mutate.py`) implements rule 2 literally:

- **anchored by line number**, never `str.replace` on a repeated string — each
  mutation asserts the expected text is on the line it is about to overwrite,
  and prints the line it found;
- **`__pycache__` cleared and 1.3 s slept** before the run and again after the
  restore, because CPython validates bytecode on mtime-in-whole-seconds plus
  size (`PYTHONDONTWRITEBYTECODE` is set as well);
- **a pre-flight that would catch `TASK-325`'s defect**: before mutating, the
  copy's file is compared to bytes captured with `git show main:<path>` in the
  live worktree *before the harness existed*. A file already carrying a
  mutation fails here rather than being "restored" onto the mutation;
- **the restore verified against those same independent bytes**, never against
  a snapshot the harness took itself.

Every run below printed `restore verified against git show main:<path> -> True`.

**One correction to my own method, recorded because it is the shape rule 2
warns about.** `tests/test_track_move.py` carries **no `unittest.main()`** — it
is the only one of the 129 test modules on `main` that does not — so
`python3 tests/test_track_move.py` executes nothing and exits **0**. My first
pass scored it GREEN on a run that never happened. The harness now invokes
every module the way `tests/run` does, `python3 -m unittest discover -s tests -p
<module>.py`, and the module is 30 tests. *(The missing `unittest.main()` is
**not** this row's: `git show 7f43a11c:tests/test_track_move.py` has no
`__main__` either. It is a standing trap for exactly the check the spec's
verification 3 asks for, and it is reported in § 0 below.)*

## 2.2 The eight mutations, re-run rather than read

I did not take the report's table. I located each site myself, mutated it, and
counted. **All eight reproduce, with the report's exact numbers.**

| # | module | my mutation, by file:line | report says | **I measured** |
|---|---|---|---|---|
| 1 | `test_track_move` | `bin/perry-task:4462` `arrived = args.arrived or prev_arrived or today` → `arrived = ""` | 5 of 30 | **RED, 5 of 30** |
| 2 | `test_register_store_invariant` | `bin/perry-task:2382` first statement of `refuse_to_shrink` → `return` | 34 of 46 | **RED, 34 of 46** |
| 3 | `test_register_substitution` | `bin/perry-task:2213` `lost.append(record)` → `pass` | 23 of 26 | **RED, 23 of 26** |
| 4 | `test_store_drift` | `bin/perry-lint:3697` (just after `stats["store_present"] = True`) → `return []` | 17 of 46 | **RED, 17 of 46** |
| 5 | `test_store_is_canonical` | `bin/perry-tasks:309-311` `return write_board_or_refuse(…)` → `return 0` | 1 of 12 | **RED, 1 of 12** |
| 6 | `test_board_render` | `bin/perry_store.py:395` `escape = desc.get("escape", True)` → `escape = False` | 5 of 14 | **RED, 5 of 14** |
| 7 | `test_design_handoff` | `bin/perry-task:1899` `rec["design_refs"] = design_refs.get(rec["id"], [])` → `pass` | 1 of 25 | **RED, 1 of 25** |
| 8 | `test_linkage_store_declared` | `bin/perry-lint:4687` `_JSONL_STORE_LABEL` renamed | 4 of 21 | **RED, 4 of 21** |

Not one green. The eight per-module test totals I observed — 30/46/26/46/12/14/25/21 —
are also exactly the denominators of the report's `--ids` table, which is an
independent corroboration of that table's counts (not of the id names).

**My own green mutation, and what it was.** Before finding the site for #7 I
mutated `bin/perry-task:3000` — `target["design_refs"] = list(event["design_refs"])`
— and `test_design_handoff` came back **GREEN, 0 of 25**. Applying the report's
own rule (*"a green mutation is a finding about the mutation until…"*): line
3000 is in the event-application path, not in `store_records`, which is the
function the report's mutation names and which lives at 1844–1899. I had
mutated the wrong site. Mutating the right one reddened. Recorded because it is
the discipline, not because it is a defect — and because it means **the carry at
`bin/perry-task:3000` was not exercised by this module**, which is a fact for
whoever next needs it rather than a finding against this row.

## 2.3 The blindness hazard, enumerated rather than sampled

This is the one place I could push past what the report did. Rule 1 says
enumerate the category. The report examined **one** global — `bin/perry-lint`'s
`_TRACK_CONTEXTS` — and instrumented it. I enumerated every module-level mutable
container in every tool the eight modules drive in-process (`perry-task`,
`perry-tasks`, `perry-lint`, `perry_store`, `perry-state`, `perry-okr`,
`perry_md_store`, `parsers`, `lib`), by AST, together with every `lru_cache`:

```
bin/perry-lint      13 module-level mutable dicts/lists
viewer/parsers.py    4 lru_cache'd functions
bin/lib/__init__.py  1 (_BLANK_CELLS)
everything else      none
```

Twelve of `perry-lint`'s thirteen are populated by one function, `load_glossary`,
and **`load_glossary(schema)` is fed only from the installed
`schema/state-schema.json`** — the same bytes on every call, merged across all
languages, never from the project root. None of the three lint-converted modules
supplies a different schema (checked: they read `ROOT / "schema" /
"state-schema.json"` themselves and override no `PERRY_HOME`). `parsers`' four
caches key on the schema and on a column name; `lib`'s `_BLANK_CELLS` on the
schema enum.

So **exactly one is keyed by the root — `_TRACK_CONTEXTS`, at
`bin/perry-lint:694`, `key = str(root)`, cleared nowhere — which is precisely
what the report said.** Its sentence *"`bin/perry-lint` has one genuinely
root-keyed global"* survives an enumeration it did not itself run. The other
twelve satisfy `tests/inproc.py`'s stated bar (*"either root-independent or reset
per call"*) on the first limb.

And I re-derived the consultation count rather than accepting it. Instrumenting
`_track_context` in the copy and running the three lint-converted modules through
`discover`:

```
test_store_drift             rc=0  cumulative consultations: 0
test_store_is_canonical      rc=0  cumulative consultations: 0
test_linkage_store_declared  rc=0  cumulative consultations: 0
TOTAL _track_context consultations: 0
restore verified against git show main:bin/perry-lint -> True
```

**Zero, independently.** The conversions are not blind through this channel, and
the uncleared cache remains a latent `bin/` defect that this row was correctly
forbidden to fix.

## 2.4 The other criteria

| criterion | result |
|---|---|
| every converted module green; suite red set unchanged | **met** — all 8 green in my copy; my full-suite baseline carries the 4 known reds and no converted module is among them |
| **no `bin/` or `viewer/` file changed** | **met, verified per commit.** `git show --stat <sha> -- bin/ viewer/` is empty for all four of `5653904f`, `2e67cde6`, `70e4fd75`, `bfc983ea`. The `bin/perry-restore-check` change visible in the merge range is `1cb6ff93`, TASK-426's, not this row's |
| no module left half-converted | **met** — 0 raw `subprocess.run/Popen/check_output` remain in any of the 8 modules or in `tests/store_fixture.py` |
| no module converted without a step-1 number | **met** — 8 converted, all with a boundary share |
| the 40% gate applied consistently | **met** — lowest converted 46.5%, highest rejected 29.9%; no straddle |
| rejected modules reported with numbers | **met** — 5, with medians of 3 and the reason |
| suite total wall-clock, worker count stated | **met** — 8 workers, stated, and the report gives five repeats rather than one |
| `--ids` set diff empty | **not re-derived by me** — see § 2.5 |

The `test_ns_collision` rejection deserves naming as work rather than as a
box ticked: 86% subprocess and **29% boundary**, rejected. That is the row
declining the conversion its own title would have demanded, which is what the
spec's procedure exists to produce.

## 2.5 What I could not check on TASK-368

- **The `--ids` set diff.** I confirmed every per-module *count* (30/46/26/46/
  12/14/25/21) independently, and the whole-suite before/after equality is the
  one number I would have to re-run the pre-conversion suite to reproduce. I
  did not check that the id *names* are the same set, only that the
  cardinalities the report publishes are the ones the modules really have.
- **The timing numbers.** Boundary shares, per-module wall clock and the 174.5s
  suite total are measurements on the author's machine under a stated load
  average. I did not re-derive any of them, and a timing figure re-measured here
  would be a different machine's number, not a check of theirs.
- **Mutation coverage beyond one test per module.** The spec asks for at least
  one named mutation per converted module and that is what exists and what I
  verified. Eight mutations do not establish that the 220 tests in those modules
  are all still load-bearing; they establish that each module still reddens for
  the reason it exists.
- **The five rejected modules' boundary shares.** Taken as reported.

---

# 3 · TASK-421 — scratch isolation and the signal prohibition

Criteria: `perry/evidence/2026-09/TASK-421-spec.md`
Under review: `perry/evidence/2026-09/TASK-421-result.md`, and the shipped fix
in `work/reference/dispatch.md`, `work/reference/review-constraints.md`,
`AGENTS.md`, `tests/test_scratch_is_per_agent.py`.

## 3.1 The sweep, re-run independently

The report's central claim is a correction to its own row's premise: **size 8,
six of the eight name no location, and nothing in the repository ever told an
agent to namespace inside a shared scratchpad.** I re-ran the sweep at the
Bound's pinned commit `fe0292fb` with my own term set over every `.md` outside
`perry/journal/` and `perry/evidence/`, and then over `bin/`, `templates/`,
`setup/`, `viewer/`, `packs/`, `modes/` and `.claude/`.

**It holds.** My sweep returns every one of the eight sites the report tabulates
— `AGENTS.md:57`, `review-constraints.md:19`, `:27`, `:89`, `digests.md:52`,
`dispatch.md:277`, `host-capabilities.md:91-92`, `autopilot.md:227` — each
spot-checked against the pinned bytes and each saying what the table says it
says. Everything else my sweep surfaced falls into three buckets, none of them
an instruction about scratch paths:

- **`namespace` in the `DESIGN-002` sense** — the *host project's* namespace,
  an unrelated subject (`SKILL.md`, `reference/first-run.md`, six ADRs, five
  designs). A term overlap, not a site.
- **prose describing past collisions** — `perry/BOARD.md` rows `TASK-289`,
  `TASK-372`, `TASK-373`, `TASK-385`, `TASK-391`, `TASK-298`; `ADR-018`;
  `DESIGN-016`. These *record* the incidents; none instructs.
- **test fixtures** — two `/tmp/sample` strings under
  `tests/fixtures/interrupted-adoption/`.

The only non-`.md` hit in the whole tree is `bin/perry-lint:2291`,
`_CITE_SCRATCH = ("scratchpad", "scratch", "tmp", "/tmp")` — a filter for
citations that point at scratch paths, not a constructor of one. So the report's
"there is no code to change" survives an independent search.

**One nuance about the word "corrects".** The report says the sweep *"corrects
the spec's premise"*. The spec's own *Why* already places the instruction in the
prompts — *"Every prompt in that session handed out one scratchpad directory"* —
so the two documents never actually disagree about where the bad advice lived;
what the Bound asked was whether the repository carried it too, and the answer
is no. The finding is real and useful, and "corrects" overstates a disagreement
that is not there. Prose, and `review.md § 0` puts prose out of scope.

## 3.2 The guard, mutated rather than read

The row's own claim is that its fix *does* admit a test, and that it mutated it
ten times. I re-ran four of them myself, on the `git archive` copy, with the
same harness discipline as § 2.1 — line-anchored, `__pycache__` cleared and
settled, pre-flight against the ref's bytes, restore verified against the same
independent source.

Baseline in the copy: `test_scratch_is_per_agent` — **11 tests, green**.

| my mutation | site | result | caught by |
|---|---|---|---|
| the derivation → a fixed shared path (**the exact shape that collided five times**) | `dispatch.md:229` | **RED, 3 of 11** | `test_two_worktrees_derive_two_scratch_roots`, `test_the_same_filename_in_both_is_still_two_files`, `test_the_snippet_names_no_fixed_directory` |
| the derivation → PID-seeded, not re-derivable | `dispatch.md:229` | **RED, 2 of 11** | `test_the_path_is_stable_across_invocations_in_one_tree`, `test_the_snippet_names_no_fixed_directory` |
| **scratch moved INSIDE the worktree** | `dispatch.md:229` | **RED, 1 of 11** | `test_the_scratch_root_is_outside_the_repository` |
| `killall` dropped from the three signal commands | `review-constraints.md:39` | **RED, 1 of 11** | `test_all_three_signal_commands_are_named` |

Every restore printed `verified against <the ref> -> True`.

**The third row is the one that mattered to check**, and it is why I picked it:
the report says this mutation came back GREEN on its first pass because the
assertion compared a `/var/folders/…` path against git's realpath
`/private/var/…` and so matched nothing — a test that asserted nothing while
passing. **That repair is real.** The mutation reddens now, on exactly the named
test, in a tree the author never touched.

Verification 3 I checked by reading the shipped file: the new bullet is bullet
**2 of 4** in `review-constraints.md § The repository is live`, directly after
the `git checkout` bullet, in the same list, phrased like its neighbours and
carrying its reason — and `test_it_sits_with_the_other_prohibitions_not_in_a_second_list`
is what holds it there.

Also confirmed: `tests/test_scratch_is_per_agent` is registered in
`tests/durations.json`; `AGENTS.md` is back to 60 lines; the
`perry-scratch-derivation` block appears **three** times in `dispatch.md` — the
section, the `claude-subagent` prompt bullet, and the `codex` prompt list — so
the codex gap § 6 names as open is in fact closed by § 7, and the report says so.
`tests/header_rule.py` walks `root.rglob("*")` from the repo root with
`NOT_A_READER = ("tests", ".git", "__pycache__", ".perry", ".claude")`, so the
temp directory is genuinely unreachable by it and the TASK-385 conflict really
is dissolved rather than suppressed.

## 3.3 Finding — a third collision condition the report does not name

Verification 1 requires: *"If they can still collide, say under what
conditions."* The report names **two**: a dispatch that omitted
`isolation: "worktree"`, and two worktrees sharing a basename under different
parents. There is a **third**, and it is silent.

Run the shipped block with a cwd that is not inside a git repository, and the
`rev-parse --show-toplevel` call fails, `basename` of the empty result is empty,
and the derivation degenerates to **one shared directory** with no error:

```
inside the agent worktree            -> [/var/folders/…/T//perry-scratch/agent-ab29516bf06aa709f]
inside a git-archive copy (no .git)  -> [/var/folders/…/T//perry-scratch/]
a plain directory, no repo           -> [/var/folders/…/T//perry-scratch/]
```

Measured, not reasoned — that is the shipped one-liner from
`work/reference/dispatch.md:229`, run in three real directories on this machine.

**Why it is reachable rather than theoretical.** `review-constraints.md § You
are a reader`, lines 18-20, instructs *every reviewer* to *"copy the project to
a scratch directory and work there"*, and `§ Verify a restore` builds that copy
with `git archive`, which carries no `.git`. An agent that works "there" and
re-derives its scratch path from that cwd gets the shared directory back again,
for exactly the population of agents this row exists to separate. Two of them
collide precisely as before, and nothing says so: the path looks plausible and
the block has no failure mode.

**Under `review.md § 0` I believe this one clears the bar**, and I say so rather
than deciding it. Applying § 0's middle limb in the row's own words: a clobbered
scratch file *"still parses, a mutation harness reading someone else's baseline
still prints a result, and the round has no way to tell the result came from
another agent's file"* — that is a tool reporting a wrong answer to someone with
no way to detect it. **It is the one finding in this round that I think should
become a row**, and the repair looks like one line: fail loudly, or fall back to
a name that cannot be empty. The decision is the PMO's.

**It does not FAIL the row.** The shipped mechanism is correct where a
dispatched agent actually runs it, its guard discriminates under four
independent mutations I ran myself, and deliverable 2 — *a private scratch path
per dispatched agent* — is delivered. What is incomplete is an enumeration
inside a verification narrative: two conditions named where there are three.
`§ 0` routes an incomplete statement in an evidence file to a correction with
its own id, never to a FAIL on this one, and a FAIL here would buy a sentence at
the price of a round.

## 3.4 An observation about this round's own dispatch

Reported as data, because the row's § 6 says the first real evidence of
compliance will be the next concurrent dispatch, and this is it.

**This round's own prompt did not carry the `perry-scratch-derivation` block.**
It said *"Use a scratch path nobody else would pick and say what you used"* —
which is the ask-the-agent-to-be-careful pattern the row's § 3 argues it
removed, not the derivation the row shipped. I complied by inventing a name: the
step the fix exists to delete.

This is not a defect in TASK-421; the row itself predicted it in § 6 (*"Nothing
here measures compliance"*) and in § 3 (*"the instruction is still text an agent
can ignore"*). It is the first datapoint on that prediction, and it is negative.
Whether that is worth a row is the PMO's call; I note only that the mechanism's
value is bounded by a prompt-construction step that this dispatch did not
perform. I can see only my own prompt and make no claim about the other two
rows' dispatches.

## 3.5 What I could not check on TASK-421

- **Six of the ten mutations.** I re-ran four (the fixed path, the PID seed,
  scratch-inside-the-worktree, and `killall` dropped). I did not re-run M3
  (sentinel deleted), M5 (blockquote gutted), M6 (prompt bullet removed), M7
  (prohibition removed), M8 (reason gutted), M10 (rule relocated), or the M11
  added in § 7. The four I chose include the one the report reports as having
  been silently green, which is the one whose repair most needed an independent
  witness.
- **The historical replay.** The eight worktrees `r4b`/`r4c`, `r5a-c`,
  `r6a-c`, `fixA`/`fixB` — I did not confirm those directories still exist or
  that their basenames are distinct. The arithmetic is trivially right *if* the
  names are what the report says; I checked the derivation, not the roster.
- **Whether any other agent obeys the block.** Unmeasurable from here, and § 3.4
  is the only datapoint I have.
- **Non-POSIX hosts**, and whether the temp directory is per-session on any host
  but this one. The report already flags both.
- **The dispatch-log residual** in `reference/host-capabilities.md:91` — I
  confirmed the report names it and did not test the two-rounds-one-task-id
  collision it describes.

---

# 4 · Verdicts

`review.md § 0` applied per finding: none of the three rows carries a defect
that destroys unrecoverable state, and the only one I believe makes a tool
report an undetectable wrong answer is § 3.3, which is a residual condition in a
shipped mechanism rather than a broken one. **No board row was filed by this
round.** The two findings I believe clear § 0's bar for a *new row* are § 1.4
(the false exclusivity claim, because a row written off it would go looking for
one call site and find three) and § 3.3 (the silent degeneration outside a
repository). Both decisions are the PMO's.

```
=== VERDICT ===
task: TASK-348
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-348-spec.md
checked: all 23 published region tables re-harvested from the document and
         recomputed with my own support extractor against the files at
         7f43a11c — 0 overlaps, 0 unclaimed code lines, 0 zero-code regions,
         0 code-column mismatches, every per-file block equal to my
         recomputation, totals exactly 6,440/167/847/3,546 over 27,132 lines;
         the 22-file line count re-derived as 27,132; 583f024f and 7f43a11c
         byte-identical over all 22 paths; 14 delegated regions sampled at a
         fresh seed (13 correct, 1 disputable at 5 lines); the empirical
         negative control re-run — perry-state --section risks does report
         "source": "table" while risks.jsonl holds 4 records; bin/perry-conform
         absent; the 15 resolve_state_root files counted
not-checked: the other 725 delegated regions and all 18,627 delegated lines —
         my arithmetic check is total, my judgement check is a sample; the
         destinations in § 7 beyond the five I traced; DESIGN-014 § 5.1's own
         numbers; whether TASK-263's two files were measured correctly
proof: n/a — PASS. Reported, not failing (§ 0): § 6.1's "the only reader of
         .perry/config.jsonl … No second implementation exists" is false.
         bin/perry-config:47-75 read_records calls load_store and
         validate_records directly, and bin/perry-context-budget:119-140
         parses the store itself with no validation, its docstring calling the
         duplication deliberate
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-368
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-368-spec.md
checked: all 8 mutations re-derived by me on a git-archive copy, anchored by
         line number, bytecode caches cleared and settled past the second
         boundary, every restore verified against the ref rather than against
         my own snapshot — all 8 RED with the report's exact counts (5/30,
         34/46, 23/26, 17/46, 1/12, 5/14, 1/25, 4/21); the blindness hazard
         ENUMERATED by AST over all 9 driven tools (13 mutable module globals
         in perry-lint, 12 fed only from the installed schema, exactly 1 keyed
         by root, as claimed); _track_context consultations independently
         re-instrumented to 0 over the 3 lint-converted modules; no bin/ or
         viewer/ file touched by any of the row's 4 commits (the
         perry-restore-check change in the merge range is 1cb6ff93,
         TASK-426's); 0 raw subprocess calls left in the 8 modules or
         store_fixture; the 40% gate consistent — 46.5% lowest converted,
         29.9% highest rejected, no straddle
not-checked: the --ids set MEMBERSHIP — I verified every per-module
         cardinality independently, not the id names, and did not re-run the
         pre-conversion suite; every timing figure, including the 174.5s suite
         total and all boundary shares, which are the author's machine; the 5
         rejected modules' numbers; mutation coverage beyond the one test per
         module the spec asks for
proof: n/a — PASS. Reported, not failing (§ 0): tests/test_track_move.py
         carries no unittest.main() — alone among 129 test modules — so
         invoking it directly runs nothing and exits 0. It scored my own first
         pass a false green. PRE-EXISTING, not this row's: the file at
         7f43a11c has no __main__ either, and tests/run uses discover, so no
         gate is weakened
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-421
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-421-spec.md
checked: the sweep re-run independently at fe0292fb with my own term set over
         every .md outside journal/ and evidence/ and over bin/ templates/
         setup/ viewer/ packs/ modes/ .claude/ — all 8 sites reproduced, no
         ninth, and no instruction anywhere to namespace inside a shared
         scratchpad, so the row's correction of its own premise holds; the
         only non-.md hit is bin/perry-lint:2291 _CITE_SCRATCH, a filter and
         not a constructor; 4 of the 10 mutations re-run by me on a copy, all
         RED on the named tests, including the scratch-inside-the-worktree one
         the report reports as silently green before its realpath repair; the
         signal prohibition confirmed as bullet 2 of 4 beside the git checkout
         bullet, with its reason; durations.json registration, AGENTS.md at 60
         lines, the block present 3 times in dispatch.md so the codex gap is
         closed; header_rule.py walks from the repo root, so the temp
         directory really is out of its reach
not-checked: mutations M3, M5, M6, M7, M8, M10 and the M11 of § 7; that the 8
         historical worktrees still exist with the basenames the replay
         assumes; compliance by any other agent; non-POSIX hosts and whether
         the temp directory is per-session elsewhere; the two-rounds-one-task-id
         collision on the codex dispatch log
proof: n/a — PASS. Reported, not failing (§ 0), and the finding I believe most
         clears § 0's bar for a NEW row: work/reference/dispatch.md:229, run
         with a cwd outside a git repository, yields one shared scratch
         directory — silently, because basename of the failed rev-parse is
         empty. Measured in three real directories. Reachable because
         review-constraints.md:18-20 tells every reviewer to work in a
         git-archive copy, which carries no .git. Verification 1 names two
         collision conditions; this is a third
=== END VERDICT ===
```
