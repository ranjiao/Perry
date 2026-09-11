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
