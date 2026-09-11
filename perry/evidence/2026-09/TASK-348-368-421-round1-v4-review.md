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
