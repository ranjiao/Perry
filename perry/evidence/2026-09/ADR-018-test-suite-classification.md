# ADR-018 part C — what the test suite defends against, classified

> Measured on `c5451524410097a41a37797e1d7049a708ee67f3`
> (`main` tip when the round began, "Drop the guards-that-do-not-guard class, and merge row D's fix").
> **This is a measurement, not a deletion.** Nothing was removed, and no test was
> modified. The only file this round writes is this one. What to cut, if
> anything, is the user's decision — as ADR-018 part C itself requires.

## 0. Provenance, and two corrections

**ADR-018 landed while this round was running.** When I reset onto `main` and
began, `perry/decisions/` stopped at `ADR-017`; there was no ADR-018 of any
title, and every occurrence of the string in the tree was scratch output from
tests exercising `perry-decide new --title 'ship it'`. I therefore started from
**ADR-005**, the existing rung-by-blast-radius decision. ADR-018 was written to
`main` at **`e3362a4`** ("ADR-018: calibrate the process to consequence, and
stop at ADR-017's gate") during the round, and `main` has since reached
`e2b59ea`.

**This does not affect a single number below.** `bin/`, `viewer/` and `tests/`
are byte-identical between my base and the current `main` tip:

```
$ git diff c545152 e2b59ea --stat -- bin viewer tests
(no output)
```

So the measurement is a property of `c545152` **and** of `main` as it stands.
Only `perry/` state, `schema/`, and two `work/reference/` pages moved.

### 0.1 Correction to ADR-018 § Context — the denominators

ADR-018's Context table is dated "Measured 2026-09-07" and carries the figures
this round was briefed with. **Two of the three do not reproduce**, at my base or
at `main`, and both errors point the same way — they make the suite look more
disproportionate than it is.

| ADR-018 § Context | measured at `c545152` = `main` | command |
|---|---|---|
| `tests/` 73,863 | **73,863** ✓ exact | `cat tests/*.py \| wc -l` |
| `bin/` + `viewer/` 37,757 | **39,177** code / 39,477 all tracked | `git ls-files bin viewer \| grep -v -E '\.md$\|\.gitignore$' \| xargs wc -l` |
| tests are **1.96×** the code | **1.885×** | `73863 / 39177` |
| skill prose 8,469 — "the product" | **16,208** for all `.md` outside `perry/` and `tests/` | `git ls-files '*.md' \| grep -v -E '^(perry\|tests)/' \| xargs wc -l` |

I could not find any grouping of shipped prose that yields 8,469; the nearest
single grouping is `work/` + `reference/` + `decide/` = 8,509. The consequences
for the ADR's headline claims:

- **"Machinery to product is 13:1"** — on the ADR's own definition of product
  this is `(37757 + 73863) / 8469 = 13.2`. Recomputed at this commit with
  measured numbers it is `(39177 + 73863) / 16208 = **7.0 : 1**`, a little over
  half the stated figure.
- **"the product is 7% of the repository"** — measured, shipped prose is
  **12.5%** of `tests` + `bin` + `viewer` + prose.

The 13:1 ratio is still large and Option 1 was still rejected on other grounds,
so this corrects the ADR's arithmetic without overturning its decision. But it
is the failure `knowledge/verification/numbers-migrate-between-sentences.md`
names, in the Context of the ADR that commissioned this round, so it is recorded
here rather than carried forward again.

### 0.2 Correction to ADR-018 § Chosen part C — the four named modules

Part C states: *"the largest are convention guards rather than behaviour guards
— `test_header_rule_harness` plus its helper at 2,779 lines,
`test_spec_scannability` 1,477, `test_shipped_vocabulary` 1,254,
`test_procedures_call_the_tool` 1,129."* That was explicitly a guess from
filenames. Read in full, **two of the four hold and two do not**:

| named | lines | verdict |
|---|---:|---|
| `test_header_rule_harness` + `header_rule.py` | 2,779 | ✅ **holds.** Both pure convention; the harness touches no Perry command, document, store or payload. |
| `test_procedures_call_the_tool` | 1,129 | ✅ **holds.** Pure convention — a regex scan over the repo's own markdown asserting `findings == []`. |
| `test_spec_scannability` | 1,477 | ❌ **mixed.** 483 lines drive `perry-lint` and assert the `specs` payload a user reads; 847 are convention. |
| `test_shipped_vocabulary` | 1,254 | ❌ **mostly behaviour.** ~1,020 lines execute `--help` on every shipped tool and check templates copied *verbatim* into a user's own repository; only ~180 are convention. |

Of the **6,639 lines** part C names as convention guards, **4,935 (74%)** are
convention and **1,704 are behaviour**. The four are still convention-heavy —
but `test_shipped_vocabulary` is close to the opposite of what it was listed as.

### 0.3 The answer to part C's reopening clause

ADR-018 § What would reopen this includes:

> *The classification round in part C finding that the convention guards are
> mostly behaviour guards after all, which would mean the suite is not the cost
> it looks like.*

**Partially met.** The convention guards are not *mostly* behaviour guards — the
biggest ones are genuinely convention. But the suite as a whole is **74.9%
behaviour and 23.9% convention** (§3.1), so the premise that "a large share
defends against contributors" is true of about **a quarter**, not a majority. And
the convention class costs **less time than it costs lines** — ~15% of
module-seconds against 23.9% of lines (§3.4).

The sharper finding is narrower and was not what the round was sent to find:
**5,630 lines — 7.6% of `tests/` — exist to test the test suite itself** (§3.3),
and two of those modules are the strongest keeps I found (§3.5).

**Under ADR-018 § Chosen A this document is a V3 deliverable**: its "deliverable
is a measurement", which § 0's list places explicitly below the V4 line.


## 1. Baseline — verified, not trusted

Two full runs at `c545152`, same invocation, `PERRY_PROJECT` unset:

```
python3 tests/parallel --times
```

| run | wall | load1 at start | modules | tests | red modules | failed tests |
|---|---|---|---|---|---|---|
| 1 | 292.1s @ 8 workers | 53.0 (7 subagents of my own were running) | 119 | 3425 | **3** | **4** |
| 2 | 135.9s @ 8 workers | 24.4 | 119 | 3425 | **3** | **4** |

The three red modules are identical in both runs and are **exactly the three the
brief predicted**:

- `test_contract_key_parity.py` — 2 failures, `conformance.in_progress_with_no_live_run[].means` not observable
- `test_diagnose.py` — 1 failure, `AssertionError: 'LOAD-03' unexpectedly found … : Perry trips its own LOAD-03` (TASK-380: a true finding about the decision backlog)
- `test_linkage_import.py` — 1 failure, `test_the_store_accounts_for_the_register_in_both_directions`

Per `knowledge/verification/a-single-baseline-run-is-not-a-baseline.md` I did
**not** settle these by re-running modules alone; both numbers come from full
parallel runs at the recorded base commit, and the commit and the invocation are
recorded beside them. The tree was byte-identical before and after
(`git status --porcelain` empty).

**The stale-base check the brief demanded.** My worktree's HEAD was `d49964e`,
an ancestor of `main` by **543 commits** — the `TASK-381` failure mode, and the
eighth instance of it. I reset onto `main` before measuring anything:

```
$ git merge-base --is-ancestor HEAD main && git rev-list --count HEAD..main
543
$ git reset --hard main       # -> c545152
```

Every number in this document is a property of `c545152`.

## 2. Method, and why it was not a regex

Per `knowledge/perry-python-never-parses-document-semantics`, the class of a
module is a **meaning** judgement, so no code made it. All 129 modules were read
in full by seven readers working in parallel, each given the same rubric and the
same decision test:

> **Convention test.** If you deleted the rule the test enforces but left the
> shipped behaviour identical, could any *user* notice? If only a reviewer
> reading the source could, it is convention.
> **Behaviour test.** Does it drive a real command/writer/reader over real input
> and assert on the output a user sees or the state their files end in?

Every module over ~600 lines was classified at TestCase-class or test-method
granularity, and the mixed splits below are reported in lines at that
granularity. The reconciliation is exact: the 129 classified modules sum to
73,863 lines, and every module name and line count was re-verified against disk
after classification (0 mismatches).

One judgement call is worth surfacing because it moves real mass: **a static
scan over *shipped* prose that flags content which is wrong for a reader right
now** (a `§` pointer resolving nowhere, a page no routing surface names, a
`--help` banner naming a withdrawn command) was classified **behaviour** — for a
skill, the markdown *is* the product, which is the premise of ADR-018's own
Context table. A scan that flags content correct today but violating a house
rule about how to write it (duplication, one-home, required vocabulary) was
classified **convention**. If you prefer "did it drive a command?" as the sole
test, roughly 1,400 further lines move from behaviour to convention, chiefly in
`test_pointers_resolve.py`, `test_shipped_vocabulary.py` and half of
`test_reference_pages_are_reachable.py`.

## 3. The five numbers

### 3.1 Total lines by class, and by module count

Two views, because they answer different questions.

**By whole module** (each module assigned to one class):

| class | modules | lines | share of 73,863 |
|---|---:|---:|---:|
| behaviour | 92 | 50,011 | 67.7% |
| convention | 22 | 13,428 | 18.2% |
| mixed | 15 | 10,424 | 14.1% |
| **total** | **129** | **73,863** | 100% |

**By attributed lines** (the 15 mixed modules split into their named halves):

| class | lines | share |
|---|---:|---:|
| behaviour | **55,297** | 74.9% |
| convention | **17,619** | 23.9% |
| shared scaffolding inside mixed modules | 947 | 1.3% |
| **total** | **73,863** | 100% |

**The headline: convention is 17,619 lines — 23.9% of the suite.** That is
about one line in four, not the majority the hypothesis expected. The suite is
predominantly a behaviour suite. The convention mass is real and it is
concentrated (see 3.2), but "a large share defends against contributors" is
**only partly supported**: a quarter, not a half.

Restated against the code it guards: 55,297 behaviour lines against 39,177 lines
of `bin/` + `viewer/` is **1.41 : 1**, which is an unremarkable ratio for a tool
with no dependencies and a refusal path on every writer. The 1.885 : 1 headline
figure is what the convention class adds on top.

### 3.2 The ten largest convention modules

The PMO's filename scan was **half right**. Verified and corrected:

| PMO guess | verdict |
|---|---|
| `test_header_rule_harness.py` (1,706) | ✅ **correct** — pure convention, and the largest. Correct line count. |
| `header_rule.py` (1,073) | ✅ **correct** — pure convention helper. Correct line count. |
| `test_procedures_call_the_tool.py` (1,129) | ✅ **correct** — pure convention. Correct line count. |
| `test_spec_scannability.py` (1,477) | ❌ **wrong — it is mixed.** 483 lines behaviour (`perry-lint`'s `specs` payload, a real user-visible report), 847 convention. |
| `test_shipped_vocabulary.py` (1,254) | ❌ **wrong — it is mostly behaviour.** ~1,020 lines execute `--help` on every shipped tool and check templates copied verbatim into a user's repo. Only ~180 lines are convention. |

Ranked, pure-convention modules only:

| # | lines | module | self-referential |
|---:|---:|---|---|
| 1 | 1,706 | `test_header_rule_harness.py` | **yes** |
| 2 | 1,129 | `test_procedures_call_the_tool.py` | no |
| 3 | 1,073 | `header_rule.py` (helper) | no |
| 4 | 1,027 | `test_tree_guard.py` | **yes** |
| 5 | 784 | `test_header_index_is_the_only_fold.py` | no (4 of its 8 tests police its own bookkeeping) |
| 6 | 701 | `live_state_expectations.py` (helper) | **yes** |
| 7 | 699 | `test_procedures_read_the_contract.py` | no |
| 8 | 695 | `test_contract_key_parity.py` | no |
| 9 | 666 | `test_claims.py` | partly (~85 lines) |
| 10 | 657 | `test_ownership.py` | no |

Because two mixed modules carry more convention than most pure ones, the more
useful ranking is by **convention block** — pure modules plus the convention
halves of mixed ones:

| # | lines | block | self-ref |
|---:|---:|---|---|
| 1 | 1,706 | `test_header_rule_harness.py` (whole) | yes |
| 2 | 1,129 | `test_procedures_call_the_tool.py` (whole) | no |
| 3 | 1,073 | `header_rule.py` (whole) | no |
| 4 | 1,027 | `test_tree_guard.py` (whole) | yes |
| 5 | **930** | `test_one_choke_point.py` (convention half of a mixed module) | no |
| 6 | **847** | `test_spec_scannability.py` (convention half) | no |
| 7 | 784 | `test_header_index_is_the_only_fold.py` (whole) | no |
| 8 | 701 | `live_state_expectations.py` (whole) | yes |
| 9 | 699 | `test_procedures_read_the_contract.py` (whole) | no |
| 10 | 695 | `test_contract_key_parity.py` (whole) | no |

The top ten blocks are **9,591 lines — 54% of all convention lines**. Four
themes account for nearly all of it: the **header-fold rule** (`header_rule.py`
+ `test_header_rule_harness.py` + `test_header_index_is_the_only_fold.py` +
the convention half of `test_one_header_rule.py` = **3,783 lines** enforcing one
rule), the **row-building choke point** (`test_one_choke_point.py` +
`test_row_integrity.py`'s grep apparatus ≈ 1,370), **procedure-prose policing**
(`test_procedures_call_the_tool.py` + `test_procedures_read_the_contract.py` +
`test_ownership.py` ≈ 2,485), and the **suite policing itself** (3.3).

### 3.3 How much of the convention class is self-referential

Self-referential = the test's subject is *other tests*, the suite's own runner
or stopwatch, or the shape of `perry/`'s own evidence and design documents —
not the shipped code in `bin/` and `viewer/` and not the shipped prose.

| module | lines | what it polices |
|---|---:|---|
| `test_header_rule_harness.py` | 1,706 | the test helper `header_rule.py`, and its own corpus's labels and provenance |
| `test_tree_guard.py` | 1,027 | the test suite's own tree-hygiene guard |
| `live_state_expectations.py` | 701 | other test modules' source, for live-state reads |
| `test_parallel_runner.py` | 526 | `tests/parallel`, the suite's own runner |
| `test_live_state_expectations.py` | 501 | the guard above, over checked-in historical test modules |
| `test_durations_provenance.py` | 418 | `tests/durations.json`, the suite's own stopwatch |
| `test_track_axes.py` | 441 | a `perry/design/` document against `modes/*.md` |
| `tree_guard.py` | 310 | (the guard itself) |
| **fully self-referential** | **5,630** | **41.9% of the 13,428 pure-convention lines** |
| `test_claims.py` (partly, ~85 lines of ~666) | 666 | one class polices other test files' entry-point position |
| **including partly self-referential** | **6,296** | **46.9% of pure convention** |

Against the whole suite, **5,630 lines — 7.6% of `tests/` — exist to test the
test suite.** Add the self-referential slivers inside mixed modules
(`test_shipped_vocabulary.py`'s two bookkeeping classes, `test_one_header_rule.py`'s
lines 70–159, `test_i18n.py`'s fixture-policing class, `test_phase_kr_declared_once.py`'s
design-doc half — ~600 lines) and it is **roughly 6,200 lines, 8.4% of the
suite**, whose failure can only ever mean a contributor wrote a *test* the
project decided against.

That is the sharpest finding in this round. It is also not uniformly waste —
see 3.5, where two of these are the strongest keeps I found.

### 3.4 Runtime by class

`tests/durations.json` **cannot answer this**, and says so itself. 101 of its
119 entries carry the provenance block `unstamped-pre-304`, whose own note
reads: *"Two independent reasons to distrust them as a set … as a set they
describe no run that has happened."* Eleven modules have never been measured at
all — including `test_tree_guard.py` and `test_spec_scannability.py`, two of the
largest convention artefacts. And `test_header_rule_harness.py` is recorded at
25.53s against **265.996s and 260.74s measured** at `d49964e`. So I measured.

From the two full runs above (per-module wall seconds; only the 119 `test_*.py`
modules have a runtime — the 10 helpers run inside their importers):

| class | run 1 (load 53) | share | run 2 (load 24) | share |
|---|---:|---:|---:|---:|
| behaviour (88 modules) | 1,825.0s | 79.2% | 846.9s | 80.1% |
| convention (16 modules) | 338.9s | 14.7% | 139.8s | 13.2% |
| mixed (15 modules) | 140.1s | 6.1% | 70.4s | 6.7% |
| **total module-seconds** | **2,303.9s** | | **1,057.1s** | |
| convention-weighted (mixed pro-rated by line share) | 379.1s | **16.5%** | 161.2s | **15.3%** |

**Convention costs less time than it costs lines: ~15–16% of module-seconds
against 23.9% of lines.** The two runs differ by 2.2× in absolute time and agree
to within 1.3 points on the proportions, so the proportion is the trustworthy
number and the absolute seconds are a property of a loaded machine.

The exception matters, and it is the one the brief asked for. **The single
slowest module in the suite is convention:**

| module | run 1 | run 2 | class |
|---|---:|---:|---|
| `test_tree_guard.py` | **149.4s** | **45.3s** | convention, self-referential |
| `test_diagnose.py` | 107.5s | 52.2s | behaviour |
| `test_header_rule_harness.py` | 70.5s | 35.2s | convention, self-referential |
| `test_contract_key_parity.py` | 68.6s | 26.6s | convention |

`test_tree_guard.py` and `test_header_rule_harness.py` together are **80.5s of
run 2's 1,057 module-seconds (7.6%)**, are both self-referential, and are the
1st and 4th largest convention modules. If a cut is made on runtime grounds,
those two are where the time is. Note also that `test_tree_guard.py` costs what
it costs *because* it is honest — it shells out a full `bash tests/run` with a
planted write.

### 3.5 What I would argue to KEEP in the convention class

A round that only finds what it was sent to find is not a measurement, so:

**Keep, strongly.**

1. **`live_state_expectations.py` + `test_live_state_expectations.py` (1,202
   lines, self-referential).** Catches tests that read Perry's own live board as
   their expected value — green today, red on the next ordinary close, and red
   in a way that *misnames its cause*. Eight recorded instances, three arriving
   within a week of a manual sweep. Nothing else catches it: `tree_guard` catches
   a test *writing* to the checkout, not *reading* it. It records a non-empty
   baseline rather than asserting zero, and documents four categories it
   deliberately misses. This is the round's single strongest keep, and it is
   self-referential — which is why "self-referential" is not a synonym for
   "waste".
2. **`tree_guard.py` + `test_tree_guard.py` (1,337 lines, self-referential, and
   the slowest thing in the suite).** TASK-249: a test invoked `perry-task` with
   no `--root`, `intake-sweep` discharged a **real board row in the live
   checkout**, four files moved on every run, and it went unnoticed for months
   because the sweep is idempotent and the second run looks clean. Its
   load-bearing half is a real planted-write run of `bash tests/run` with a
   mutation control, not decoration. Expensive, and I would still pay it.
3. **`test_one_primitive.py` (185 lines).** Asks what a file *does*, not what it
   is called: it catches a tool rebuilding a `bin/lib` primitive (`mkstemp`,
   `flock`, the refusing schema loader) under a new name. Divergent atomic-write
   semantics and unserialised concurrent writes to a user's state are data-loss
   defects. TASK-067 found two offenders no report had named. Carries its own
   anti-vacuity pair. Nothing else in the repo enumerates the writers.
4. **`contract_key_parity.py` + `test_contract_key_parity.py` (1,344 lines).**
   The only mechanical link between a published contract and the payload an
   external front-end codes against — the two-way diff, proved by mutation in
   both directions. `test_contract_invariance.py` records shape only and its own
   docstring concedes "a key emitted and never documented passes it cleanly."
   This is V4 territory under ADR-005: it guards what runs on someone else's
   project.
5. **`test_procedures_call_the_tool.py`'s rule (though not its 1,129 lines).**
   Perry ships prose that agents *execute*. A page telling an agent to hand-edit
   a tool-owned file is closer to a shipped bug than a style violation — 19 such
   steps were measured across 26 pages, two of them naming a gap the tool had
   closed weeks earlier. The rule is ~25 lines; ~500 lines are scanner
   self-tests, several of which exist because an exemption was once widened
   wrongly. Keep the rule, and that is where a cut would go.

**Keep, narrower.** `test_spec_scannability.py`'s `TestTheAgentGetsItsOwnTree`
(~502 lines): it is the only thing holding the worktree-isolation rule, a rule
whose violation already cost a merge (an agent switched the shared checkout; 91
journal lines and four review documents landed on a code branch), and it
defeated three naive guards — softening to "MAY", a retraction three lines below
the pinned blockquote, and a substring-vs-line-membership hole. That is also
`TASK-381`, the failure this very round had to correct for. `test_parallel_runner.py`
(526 lines) guards the *numbers this project's whole review process quotes* —
its scar is "eighty tests stopped running and the number was still large enough
to look right"; if it is unwanted in the product suite the right move is to move
it to a meta-suite, not delete it.

**The clearest cuts, if cuts are wanted** (stated so the reader has both sides):
`test_row_integrity.py`'s ~190-line `SPLIT_RE`/`HAND_ROW_RE` grep apparatus,
which its own successor `test_one_choke_point.py:43` records as having "four
demonstrated blind spots"; `test_router_budget.py`'s citation and reachability
halves (~180 lines), duplicated by two newer and better-generalised modules;
`test_i18n_one_table.py` (166 lines), whose own docstring says the behaviour "is
asserted for real in `test_i18n.py`"; and `test_header_index_is_the_only_fold.py`'s
two hand-maintained censuses, which go red on any unrelated conversion.

## 4. Three defects found in passing

Not asked for, and reported because they are facts about the suite's cost:

1. **`tests/handed_back.py` (146 lines) and `tests/sweep_handed_back_commands.py`
   (253 lines) are dead** — 399 lines with **zero importers**, and neither is
   invoked by `tests/run`, `tests/parallel`, `tests/merge-check` or CI. Both
   target `bin/perry-conform` and `bin/perry-migrate`, **which no longer exist**.
   `handed_back.py`'s docstring names `tests/test_conformance.py` and
   `tests/test_migrate.py` as its importers; neither file exists.
   ```
   $ grep -rn "handed_back" tests bin viewer | grep -v "^tests/handed_back.py:" | grep -v "^tests/fixtures/"
   tests/sweep_handed_back_commands.py:36:    python3 tests/sweep_handed_back_commands.py [--all] <file> [...]
   $ ls bin/perry-conform bin/perry-migrate
   ls: bin/perry-conform: No such file or directory
   ls: bin/perry-migrate: No such file or directory
   ```
2. **`test_one_heading_predicate.py::test_migration_does_not_append_a_second_section`
   is vacuous.** It shells out to `bin/perry-migrate`, which does not exist, via
   a `subprocess.run` with no `check=`, so the return code is discarded, the
   board is never touched, and `assertEqual(board.read_text().count("Top risks"), 1)`
   passes against an unmodified fixture. Its own docstring calls it "the
   dangerous one, because `perry-migrate` acts on lint findings". It has been
   dead since the tool was removed.
3. **`test_i18n_one_table.py::test_a_spelling_the_schema_gains_reaches_the_track_parser`
   cannot fail for the reason it claims** — despite its name and docstring it
   only asserts `first == second` across two calls (idempotence); the
   injected-schema check its comment describes was never written.

All three are consistent with `knowledge/verification/mutate-every-fix-and-distrust-green.md`:
a green that means nothing.


## Bound

**How the population was enumerated.** `ls tests/*.py` at `c545152`, which is
**129 files, 73,863 lines** — the exact figure the brief quotes, and it
reproduces. That set is **129 = 119 `test_*.py` + 10 helper modules** that carry
no tests of their own but are imported by modules that do:

```
$ ls tests/*.py | wc -l                # 129
$ ls tests/test_*.py | wc -l           # 119
$ cat tests/*.py | wc -l               # 73863
$ ls tests/*.py | grep -v '/test_' | xargs wc -l   # 10 files, 3877 lines
```

**All 129 were opened and read.** Every one has a row in §5 with its own
evidence sentence. The classification reconciles exactly: the 129 classified
line counts sum to 73,863, and each name and count was re-verified against disk
afterwards with 0 mismatches.

**`ls tests/*.py` is NOT the whole of `tests/`.** What it excludes, and what
this round therefore did **not** classify:

| excluded | files | lines | why |
|---|---:|---:|---|
| `tests/run`, `tests/parallel`, `tests/merge-check` | 3 | 1,568 | executable scripts with no `.py` extension; they are the runners, not test modules |
| `tests/fixtures/**/*.py` | 4 | 1,673 | fixture data and "before" images (`md_store.before.py` etc.), not tests |
| `tests/durations.json` | 1 | 546 | data |
| `tests/fixtures/**` (all files) | 49 | — | fixture projects |

So the true `tests/` tree is **133 `.py` files / 75,536 lines** plus 1,568 lines
of runner script. The round covers the 129/73,863 the question was asked about;
the other 3,241 lines are named here so the next reader knows they were out of
scope. `tests/parallel` (819 lines) is itself substantially a piece of
convention infrastructure and is *policed by* `test_parallel_runner.py`, which
is inside the population and counted.

**Runtime bound.** Only the 119 `test_*.py` modules have a measurable runtime;
the 10 helpers execute inside their importers and are attributed no seconds. The
runtime table in §3.4 therefore covers 119 of 129 modules, and the 6 pure-
convention *helpers* (`header_rule.py`, `live_state_expectations.py`,
`tree_guard.py`, `one_startable_rule.py`, `contract_key_parity.py`,
`sweep_handed_back_commands.py` — 3,314 lines) contribute convention cost that
is charged to behaviour-class importers in the seconds column. The line-based
convention share (23.9%) is the honest one; the runtime share (~15%) understates
convention slightly for this reason.

## What I did not check

- **I did not verify any test's claim by mutation.** Every "nothing else catches
  this defect" in §3.5 and in the per-module notes rests on reading plus targeted
  greps for the neighbouring guard — not on deleting the guard and confirming the
  suite goes green. For a deletion decision on any specific module, that mutation
  is the check I would want run first, and this round did not run it.
- **I did not re-derive the mixed-module line splits independently.** They come
  from the reading pass at class/method granularity and are approximate to
  perhaps ±10%; the ~947-line residue in §3.1 is shared fixtures and imports that
  the readers did not attribute to either side.
- **I did not investigate the three red modules.** They were verified present
  and identical across two runs and matched against the predicted baseline, and
  no further diagnosis was attempted.
- **I did not check whether the convention rules are actually *true* of the
  repository today** — only what a failure would mean. A convention module that
  is currently passing vacuously (as three in §4 are) would still be classified
  by its stated intent.
- **I did not reconcile ADR-018's 8,469-line skill-prose figure.** I could not
  find a grouping that produces it; the nearest is 8,509. I therefore cannot say
  *which* definition drifted, only that no obvious one reproduces.
- **I did not re-measure anything against the new `main` tip** (`e2b59ea`). I
  established that `bin/`, `viewer/` and `tests/` are byte-identical between
  `c545152` and `e2b59ea`, which is what makes the numbers current; I did not
  re-run the suite there, so the *baseline* (3 red) is asserted for `c545152`
  only. ADR-018 itself and the two `work/reference/` § 0 texts it added landed
  after my base and were read, not measured.
- **I did not edit ADR-018** to correct its Context arithmetic (§0.1), and did
  not create, renumber or reserve any ADR. Those are the user's calls.
- **The absolute seconds in §3.4 are not machine-independent.** Both runs were
  taken under foreign load (load1 53 and 24 on 14 cores) on a machine whose load
  never fell below ~20 during this round. The proportions are stable across the
  two runs; the absolute totals are not, and neither is `tests/durations.json`,
  which §3.4 explains should not be used for this.
- **No test was executed in isolation to attribute a red**, deliberately, per
  `a-single-baseline-run-is-not-a-baseline.md`.

## 5. Per-module classification — all 129

`sec` is run 2 wall seconds (load1 24.4, 8 workers); `—` means a helper module
with no runtime of its own. `mixed split` is `b<behaviour>/c<convention>` lines.
`self-ref` is given for convention and mixed rows only.

| module | lines | sec | class | mixed split | self-ref | evidence — the assertion that decides it |
|---|---:|---:|---|---|---|---|
| `test_diagnose.py` | 2690 | 52.2 | **behaviour** | — | — | Drives `perry-diagnose --json` over fixture projects: "a diagnostic that cries wolf trains its user to skip it". |
| `test_goals_writer.py` | 1907 | 44.4 | **behaviour** | — | — | `assertEqual(path.read_text(), doc.render())` over the real `OKR.md` — the writer must not silently reformat the user's prose. |
| `test_md_store.py` | 1746 | 6.2 | **behaviour** | — | — | "the store holds a different number of KRs than the file has KR lines — a byte-identical render that dropped rows". |
| `test_header_rule_harness.py` | 1706 | 35.2 | **convention** | — | yes | Plants ~110 synthetic probe files into a temp copy of the repo and asserts what `header_rule.py` reports; no Perry command, document, store or payload is touched. |
| `test_spec_scannability.py` | 1477 | 4.9 | **mixed** | b483/c847 | no | Behaviour half runs `perry-lint` and asserts the `specs` payload; the larger half pins `sha256(governed_text(...))` over paragraphs of `work/reference/dispatch.md`. |
| `test_track_register_source.py` | 1400 | 6.6 | **behaviour** | — | — | `perry-task intake` must exit non-zero AND leave no `intake.jsonl` — "the refusal must mean NOTHING was written". |
| `test_linkage_store_readers.py` | 1361 | 7.0 | **behaviour** | — | — | `purge` on a row a register still names must exit 1 — purging destroys a row and `mint_id` never re-issues the id. |
| `test_shipped_vocabulary.py` | 1254 | 2.4 | **mixed** | b1020/c180 | partly | Executes `--help` on every `bin/` tool: "a shipped tool greets the user in a vocabulary that no longer exists". Convention half pins this file's own coverage claims. |
| `test_work_modes.py` | 1204 | 4.3 | **mixed** | b620/c430 | no | Behaviour: `perry-lint --verification` must flag a V2-closed outward-facing row. Convention: "**Prose only.** It greps the triage procedure for column names". |
| `test_task_writer_contracts.py` | 1166 | 26.0 | **behaviour** | — | — | Reading only `## P0/P1/P2` "reported three tasks for a project with dozens … shows the user confident nonsense". |
| `test_procedures_call_the_tool.py` | 1129 | 0.5 | **convention** | — | no | `test_no_procedure_hand_edits_a_tool_owned_file` — a regex scan over the repo's own markdown asserting `findings == []`. |
| `test_register_store_invariant.py` | 1096 | 21.5 | **behaviour** | — | — | "the intake store changed on a refused write" — reproduces `intake.jsonl` going 24 records to 0 at exit 0. |
| `header_rule.py` | 1073 | — | **convention** | — | no | Helper: "Nothing outside `viewer/tables.py § header_index` applies `squash` to a header row" — an AST scan of the repo's own source asserted `== 0`. |
| `test_risks.py` | 1038 | 15.0 | **behaviour** | — | — | `risk-add` wrote the row and `perry-state` reported zero risks — "Every exit a user could reach was closed by that one disagreement". |
| `test_task_writer_core.py` | 1034 | 28.6 | **behaviour** | — | — | Five concurrent `add` calls left two rows: `assertEqual(len(set(ids)), n, "an id was issued twice")`. |
| `test_task_writer_modes.py` | 1032 | 26.1 | **behaviour** | — | — | `assertIn(col, header, f"{col} was not created")` — real columns written into the user's `BOARD.md`. |
| `test_tree_guard.py` | 1027 | 45.3 | **convention** | — | yes | Requires `bash tests/run` to come back red when a planted test module writes into its own checkout — "THE SUITE WROTE INTO THE TREE IT RAN IN". |
| `test_one_choke_point.py` | 997 | 3.3 | **mixed** | b65/c930 | no | Convention: `test_no_tool_builds_a_table_row_outside_viewer_tables` asserts `offenders() == []` over an AST walk. Behaviour: `render_separator(0)` must raise `UnrenderableCell`. |
| `test_review_verdicts.py` | 960 | 10.5 | **behaviour** | — | — | `assertIn("fail-verdict-left-at-review", self.rules())` — real `perry-lint --reviews` findings and `--strict` exit code. |
| `test_store_drift.py` | 957 | 16.7 | **behaviour** | — | — | lint reported 175 of 175 records drifted while `perry-state` said 0 on the same tree. |
| `test_config_store_readers.py` | 908 | 1.6 | **behaviour** | — | — | Every fixture makes `config.md` and `config.jsonl` disagree and asserts the store's answer through `perry-state`. |
| `test_row_integrity.py` | 897 | 1.6 | **mixed** | b330/c440 | no | Behaviour: "a row missing two of seven columns linted clean". Convention: `test_no_tool_writes_a_row_by_hand` greps `bin/` and `viewer/` for f-string row literals. |
| `test_cadence.py` | 880 | 10.5 | **behaviour** | — | — | "…refused with a false statement about a row the tool wrote and `perry-state` lists". |
| `test_intake_store.py` | 870 | 9.6 | **behaviour** | — | — | "the store has to put the section back exactly as it found it" — byte-identity of the rendered `## Intake` section. |
| `test_risks_store.py` | 860 | 9.4 | **behaviour** | — | — | "a migration that cannot reproduce what it replaces has not understood it" — refusals must leave board and store byte-identical. |
| `test_linkage_import.py` | 846 | 6.3 | **behaviour** | — | — | `linkage-write --from-register` output set-compared against the register — "the store is not a faithful account of the register". |
| `test_linkage_writer.py` | 829 | 6.3 | **behaviour** | — | — | `assertEqual("\n".join(restored), before)` — a write must leave every byte it did not touch unchanged. |
| `test_parsers.py` | 814 | 3.6 | **behaviour** | — | — | `assertEqual(t.owner, "Coding Agent", "owner read the Track cell")` on a real board with an extra column. |
| `test_header_index_is_the_only_fold.py` | 784 | 8.5 | **convention** | — | no | "a header cell was folded outside `viewer/tables.py § header_index`, by: {stray}" — a `setprofile` instrument plus two hand-maintained censuses. |
| `test_ns_collision.py` | 776 | 14.1 | **behaviour** | — | — | Runs `perry-lint` and asserts the finding, its evidence path and exit code: "a collision never sets a non-zero exit". |
| `test_v5_signoff.py` | 776 | 14.7 | **behaviour** | — | — | An empty signature must be refused and `test_the_refused_close_wrote_nothing` must hold. |
| `test_asks_store.py` | 768 | 6.3 | **behaviour** | — | — | "the second line came back wearing the FIRST row's question, blocker, status and date". |
| `test_stranded_rows.py` | 756 | 21.1 | **behaviour** | — | — | `conformance["in_progress_with_no_live_run"] == ["TASK-001"]` in the payload a triage agent reads. |
| `test_host_support.py` | 742 | 26.8 | **mixed** | b620/c88 | no | Behaviour: `assertEqual(len(won), min(cap, decided))` over 20 contending `perry-dispatch-limit` processes. Convention: a doc-contract grep class. |
| `test_escalation_union.py` | 719 | 3.6 | **behaviour** | — | — | "declaring a role stopped the project's own term from tripping the pre-flight scan" — a guard silently narrowing what Perry refuses unsupervised. |
| `test_kr_progress_provenance.py` | 704 | 3.9 | **behaviour** | — | — | `test_closing_one_linked_task_makes_it_stale_and_names_that_task` on the real `perry-goals list --json`. |
| `live_state_expectations.py` | 701 | — | **convention** | — | yes | Helper: an AST sweep whose subject is "a check must not read the live project as its expected value" — it judges other test modules' source. |
| `test_procedures_read_the_contract.py` | 699 | 0.3 | **convention** | — | no | `test_no_procedure_restates_a_contract_predicate` — a sentence scan over shipped prose; the flagged prose is not wrong today, only duplicated. |
| `test_knowledge_promotion.py` | 698 | 5.7 | **behaviour** | — | — | "the writer accepted a source the linter reports" — `perry-knowledge promote` refusals and `perry-lint --knowledge` findings. |
| `test_contract_key_parity.py` | 695 | 26.6 | **convention** | — | no | Reads `schema/README.md` prose and holds documented-vs-emitted key diffs to a recorded baseline — a documentation-consistency measurement. |
| `test_register_substitution.py` | 694 | 16.5 | **behaviour** | — | — | `assertEqual(reported(out), staged.n, "the write did not name what it destroyed")`. |
| `test_prioritize.py` | 692 | 9.1 | **behaviour** | — | — | `test_it_emits_an_event_so_the_move_is_not_drift` / `test_a_refusal_writes_nothing`. |
| `test_add_writes_the_edge.py` | 675 | 6.0 | **behaviour** | — | — | SIGKILLs the writer mid-rename and asserts "the edge and the row agree" — a half-landed write to `linkage.jsonl`. |
| `test_store_is_the_write_target.py` | 672 | 11.2 | **behaviour** | — | — | `perry-tasks diff` must report `identical: true` after every kind of write, plus crash-recovery. |
| `test_purge.py` | 671 | 31.3 | **behaviour** | — | — | "`purge` reported success and the record is still there" — store, `list` payload, event log, journal and every refusal path. |
| `test_claims.py` | 666 | 8.9 | **convention** | — | partly | "a hand-maintained second copy is what drifted" — every class is a rule over the repo's own schema, prose or test files; no command is ever run. |
| `test_task_writer_intake.py` | 665 | 24.9 | **behaviour** | — | — | "`{id}` names `{evidence}` and the payload neither resolved it nor reported it" over the real `list --all`. |
| `test_ownership.py` | 657 | 0.1 | **convention** | — | no | "a lane's page instructs a write the signed contract forbids" — every assertion reads a doc or the schema as text; no command is run. |
| `contract_key_parity.py` | 649 | — | **convention** | — | no | Helper: computes "keys documented but not emitted, or emitted but not documented" between contract prose and real payloads. |
| `test_phase_kr_declared_once.py` | 639 | 3.2 | **mixed** | b380/c190 | partly | Behaviour: edit the register and `perry-goals krs` follows. Convention: `test_no_phase_document_carries_a_kr_table_row` greps `phase/*.md`. |
| `test_summary_is_asked_for.py` | 610 | 4.1 | **mixed** | b477/c133 | no | Behaviour: `add` exits 1 with "--summary is required" and writes nothing. Convention: asserts `summary_shape = lib.summary_shape` appears in `bin/perry-lint`. |
| `test_duplicate_ids_are_refused.py` | 603 | 2.7 | **behaviour** | — | — | "the record the write would have destroyed is still there". |
| `test_project_root_resolution.py` | 577 | 34.0 | **behaviour** | — | — | "an empty board was read for Perry itself" — the resolver returning the wrong directory produced `tasks 0 · adrs 0`. |
| `test_contract_invariance.py` | 577 | 5.0 | **behaviour** | — | — | `test_no_key_disappeared` over `perry-task list --all`, `perry-goals list`, `perry-decide list`. |
| `test_board_render.py` | 555 | 20.0 | **behaviour** | — | — | `assertEqual(self.rendered(d), self.board_bytes(d))` plus per-field store mutations that must move the rendered cell. |
| `test_queue_sla.py` | 548 | 8.9 | **behaviour** | — | — | "a row with no clock is a third answer not a pass" — `sla_breaches` / `sla_no_clock` from a real board. |
| `test_restore_check.py` | 533 | 5.2 | **behaviour** | — | — | `ok = all(...)` → `any(...)` was "a false PASS on the interface the tool documents". |
| `test_parallel_runner.py` | 526 | 5.7 | **convention** | — | yes | "`schedule()` is asserted to be a permutation … under every way the hint can be wrong" — the subject is the suite's own runner. |
| `test_task_writer_dependencies.py` | 512 | 24.5 | **behaviour** | — | — | "a review row read as startable" / "the edge lived in the disposable half". |
| `test_track_move.py` | 506 | 22.6 | **behaviour** | — | — | `perry-task track` must update the store record, the rendered board cells, the journal line and the event. |
| `test_decide_writer.py` | 506 | 8.4 | **behaviour** | — | — | `TestNothingWritesAnIndex` asserts the exact set of files on disk after each `perry-decide` subcommand. |
| `test_same_action_linkage.py` | 502 | 1.4 | **behaviour** | — | — | `assertNotEqual(self.m["current"], 100.0)` — a store-only reading publishes a plausible number for a different quantity. |
| `test_live_state_expectations.py` | 501 | 7.0 | **convention** | — | yes | Runs the guard over three checked-in test modules from git history to prove it still detects tests whose expected value is the live project's state. |
| `test_design_handoff.py` | 490 | 2.1 | **behaviour** | — | — | "a row that only mentions the design does not count" — the control for a count that reported a shipped design as pending hand-off. |
| `test_events_feed.py` | 487 | 4.6 | **mixed** | b316/c170 | no | Behaviour: `test_paging_the_whole_log_yields_every_event_exactly_once`. Convention: the writer's emittable kinds must all appear in the contract doc. |
| `test_resume.py` | 475 | 2.1 | **mixed** | b218/c200 | no | Behaviour: "detection must work on a folder with no state files — that is the case that was … losing their work". Convention: `assertIn("Check for an interrupted run", SKILL)`. |
| `test_one_line_break_rule.py` | 472 | 4.9 | **behaviour** | — | — | Byte-exact refusal text a user reads, from a real CLI run. |
| `test_linkage_task_exists.py` | 469 | 2.7 | **behaviour** | — | — | `test_one_absent_id_yields_exactly_one_finding` through the real `--root` seam. |
| `test_okr_store_is_the_source.py` | 453 | 4.5 | **behaviour** | — | — | "ops/2 was minted again, for a different promise" — a deleted row's id silently re-pointing work. |
| `test_track_axes.py` | 441 | 0.1 | **convention** | — | yes | "every slot in every mode contract table has exactly one axis" — a design doc pinned against `modes/*.md`; no code reads either table. |
| `test_answered_ask_is_legible.py` | 433 | 8.8 | **behaviour** | — | — | "the two arrays disagree about an edge" — `depends_on_resolved` built through real writes. |
| `test_one_header_rule.py` | 421 | 5.6 | **mixed** | b125/c220 | partly | Behaviour: a `**File**` header read as a declaration made the tool say "unreadable row" on a correct file. Convention: an equality against zero over one symbol via an AST sweep. |
| `test_durations_provenance.py` | 418 | 0.6 | **convention** | — | yes | "these modules exist and tests/durations.json does not mention them" — an audit of the test suite's own scheduling hint file. |
| `test_linkage_store_declared.py` | 406 | 1.0 | **behaviour** | — | — | `assertIn("drift against the linkage store is unchecked, not clean", line)` — a real census line a user reads. |
| `test_evidence_relation.py` | 397 | 4.7 | **behaviour** | — | — | Every character of a live evidence cell must reach an entry or be a separator, over 100+ real cells. |
| `test_role_delegation.py` | 392 | 2.7 | **behaviour** | — | — | "a subscribed card that is stale is injected *with its flag visible*". |
| `test_heading_defines.py` | 388 | 0.8 | **behaviour** | — | — | "a heading arguing about REL-00 was read as REL-00's home", then `perry-explain --dangling` exit code. |
| `test_id_families.py` | 387 | 1.9 | **behaviour** | — | — | `perry-task` printed "⚠ --next contains DEC-014, SPEC-007, which reads as an id and names nothing" on a legitimate citation. |
| `test_router_budget.py` | 379 | 0.4 | **convention** | — | no | "a budgeted SKILL.md outgrew its cap … do not raise the cap" — a rule over the repo's own file sizes. |
| `test_state_cost.py` | 370 | 13.9 | **behaviour** | — | — | `test_bytes_match_an_independent_sum_of_the_files` and `test_the_tree_is_unchanged_by_a_full_run`. |
| `test_ask_is_a_node.py` | 361 | 12.0 | **behaviour** | — | — | "an id nothing carries is unsatisfied, not satisfied". |
| `test_i18n.py` | 361 | 0.5 | **mixed** | b230/c100 | partly | Behaviour: `perry-state --dashboard` on the zh fixture must render `只做单区域`, `P0=2`. Convention: greps `SKILL.md` for "stays English", "idiom". |
| `test_escalation_boundaries.py` | 359 | 0.3 | **behaviour** | — | — | Four real dispatches were stopped for a human because `main` matched "remains available"; the four measured false positives must be gone. |
| `test_decide_status_enum.py` | 357 | 3.0 | **mixed** | b150/c88 | no | Behaviour: "a proposal was counted as a decision in force" via `perry-decide list`. Convention: three spellings of the enum must agree. |
| `test_role_cards.py` | 357 | 5.3 | **behaviour** | — | — | A card with `## Notes` must yield `role-card-unknown-section`; an empty roles dir must change no byte of the payload. |
| `test_retired_tolerance.py` | 356 | 1.7 | **behaviour** | — | — | "the wrong row is not cleared by guessing column zero". |
| `test_context_budget.py` | 353 | 0.9 | **behaviour** | — | — | `assertEqual((report["verdict"], report["context"]), ("unknown", None))` — a gate that returns "fine" because it found nothing to look at. |
| `test_store_is_canonical.py` | 349 | 12.4 | **behaviour** | — | — | "the bug was in the sentence it printed, and a user who follows Perry's instructions and loses data was failed by the sentence". |
| `test_one_startable_rule.py` | 336 | 4.1 | **mixed** | b147/c130 | no | Behaviour: "`cmd_list` and `_cmd_list_from_board` disagree". Convention: an AST count of the rule's homes under `bin/`. |
| `one_startable_rule.py` | 328 | — | **convention** | — | no | Helper: an AST scan asserting `bin/` states the `startable` rule in exactly one enclosing function. |
| `test_goals_contract.py` | 312 | 1.5 | **behaviour** | — | — | `assertEqual(set(d), self.TOP)` on the real `perry-goals list --json` — the read contract a front-end consumes. |
| `tree_guard.py` | 310 | — | **convention** | — | yes | Helper for `tests/run` step 0: "The tree the suite starts in must be the tree it ends in — byte for byte." |
| `test_heading_title.py` | 309 | 1.6 | **behaviour** | — | — | `TASK-050 supersedes TASK-049` collapsed to the title "supersedes", "and that verb became the id's name". |
| `test_register_minters.py` | 298 | 10.3 | **behaviour** | — | — | `assertEqual(p.mint(cmd, tail), f"{prefix}-002")` after deletion — a reused id inherits a dead row's history. |
| `test_task_store_read_cutover.py` | 298 | 2.2 | **behaviour** | — | — | A store edit and a contradictory board edit — the store value must win and be re-rendered into `BOARD.md`. |
| `test_wip_and_stages.py` | 258 | 1.7 | **behaviour** | — | — | `assertEqual(t["wip_breaches"], [{"stage":"review","count":3,"limit":2}])` from real `perry-state --json`. |
| `sweep_handed_back_commands.py` | 253 | — | **convention** | — | no | Orphan helper: "Exit 1 if any handed-back command lacks the root or interpolates a value raw" — an AST rule over `bin/` source. |
| `test_task_summary.py` | 248 | 8.8 | **behaviour** | — | — | "the compact Board gained a required column" — every unrelated writer must preserve the stored `summary` sentinel. |
| `test_semantics_on_every_payload.py` | 233 | 4.7 | **behaviour** | — | — | Every one of the six shipped read payloads must carry `semantics`, "so a consumer cannot ask it what a minor changed". |
| `test_one_heading_predicate.py` | 229 | 1.7 | **behaviour** | — | — | "`risk-add` on a bolded heading writes into the existing section" — the risks already recorded went invisible to every tool. |
| `test_unlinked_declaration.py` | 226 | 3.6 | **behaviour** | — | — | 48 ids in one argument must exit non-zero, say "takes ONE task id", and leave the register unchanged. |
| `test_stale_blocked.py` | 224 | 7.0 | **behaviour** | — | — | A row whose only dependency closed must come back `blocked_by: []`, `startable: true`. |
| `test_knowledge_cards.py` | 217 | 2.5 | **behaviour** | — | — | `assertIn("card-source-dangling", self.rules(self.knowledge(root)))` on built fixture projects. |
| `task_writer_support.py` | 208 | — | **behaviour** | — | — | Helper for 21 task-writer modules; `Project.run()` shells out to `bin/perry-task … --json` against a temp project. |
| `test_decoration_changes_nothing.py` | 208 | 13.7 | **behaviour** | — | — | "bold every header cell, and assert every reader reports exactly what it reported before" — three real CLIs, payload equality. |
| `test_track_attribution.py` | 199 | 8.6 | **behaviour** | — | — | `perry-diagnose --json` scored `project 7 / pipeline 4` and issued a `MODE-01` warn against a correct cell. |
| `test_role_on_rows.py` | 197 | 1.4 | **behaviour** | — | — | `test_a_roleless_row_is_refused` / `test_a_refusal_writes_nothing` — `perry-task add` rc and `BOARD.md` bytes. |
| `test_one_primitive.py` | 185 | 0.1 | **convention** | — | no | "these carry a second body for a primitive `bin/lib` already implements" — an AST scan of `bin/` for `mkstemp(`, `flock(`. |
| `test_attribution_buckets.py` | 183 | 1.9 | **behaviour** | — | — | "the payload turned finished work into outstanding work" — `unlinked` and `declared_unlinked` must be disjoint. |
| `test_missing_defaults.py` | 172 | 0.9 | **behaviour** | — | — | `tracks["ops"]["missing_defaults"]` must contain `SLA` — the field triage reads. |
| `test_pointers_resolve.py` | 169 | 0.3 | **behaviour** | — | — | "no pointer names a section that is not there" — a shipped page citing a file that does not exist sends the reader nowhere. |
| `test_reference_pages_are_reachable.py` | 167 | 0.1 | **mixed** | b105/c45 | no | Behaviour: a page no routing surface names is a command the user types and cannot reach. Convention: literal-string pins on the project's own review procedure. |
| `test_blank_cell_is_one_rule.py` | 166 | 0.1 | **behaviour** | — | — | "`Depends on: 待定` parsed as a real dependency id" — a task reported as waiting on a row that will never exist. |
| `test_i18n_one_table.py` | 166 | 0.2 | **convention** | — | no | Counts hardcoded schema aliases in read-path tools against a budget of 0; its own docstring says the real behaviour "is asserted for real in `test_i18n.py`". |
| `test_dispatch_limit_honesty.py` | 163 | 2.0 | **behaviour** | — | — | "(no active dispatches)" reads as "nothing is running"; it means "no marker file exists". |
| `test_last_updated_header.py` | 159 | 2.4 | **behaviour** | — | — | An ordinary `add` makes `> Last updated:` today, and `perry-state`'s `board.last_updated` must agree. |
| `test_stage_separators.py` | 156 | 0.9 | **behaviour** | — | — | `split_stages("new,triaged,resolved")` must not return one stage named after the whole list. |
| `test_intake_signal.py` | 151 | 0.9 | **behaviour** | — | — | The `size-cap` message a user reads must say "Do not split" and name the 220 rows. |
| `handed_back.py` | 146 | — | **behaviour** | — | — | ORPHAN helper (no importer): "a refusal that names a command must name it with the root the caller used". |
| `test_explain_typed_tasks.py` | 137 | 1.1 | **behaviour** | — | — | `test_store_title_wins_over_a_plausible_markdown_definition` — stdout, exit code and JSON payload of `perry-explain`. |
| `test_entrance.py` | 135 | 0.1 | **convention** | — | no | `assertNotIn('ln -snf "perry/$name"', setup, "setup is linking lanes as sibling skills again")` — greps five docs; runs nothing. |
| `test_escaped_pipe_corpus.py` | 125 | 1.1 | **behaviour** | — | — | "the columns after the escaped pipe shifted" — every reader asked the same question about the same row at runtime. |
| `test_task_store.py` | 124 | 12.4 | **behaviour** | — | — | "`verify` used to compare the store against the board it had just been built from — a tautology that could never fail". |
| `test_glossary.py` | 120 | 30.6 | **behaviour** | — | — | Runs `perry-explain <term>` for every shipped glossary term and asserts rc 0 and no "not found". |
| `test_count_fields.py` | 115 | 1.7 | **behaviour** | — | — | `assertEqual(d["closed"], sum(1 for t in d["tasks"] if not t["open"]))` against the real `perry-task list --json`. |
| `test_rung_vocabulary.py` | 108 | 31.6 | **behaviour** | — | — | `perry-explain V4` answered "not found" and offered id-shaped noise. |
| `store_fixture.py` | 105 | — | **behaviour** | — | — | Helper for four store modules; builds a temp project and runs `perry-tasks write --from-board`. |
| `contract_declared_types.py` | 104 | — | **behaviour** | — | — | Helper for `test_contract_invariance.py`; a removal or retype breaks a real consumer (aiMark). |
| `test_amend_matches_create.py` | 73 | 0.1 | **behaviour** | — | — | A table written without trailing pipes produced a 7-cell header and a 6-cell separator, rc 0, lint silent. |
