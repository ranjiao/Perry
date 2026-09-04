# TASK-308 round 1 — V4 fresh-context review

- **Reviewer**: fresh-context V4 reviewer (did not write this code)
- **Branch**: `review/task-308-v4`, cut from `main`
- **Under review**: `perry/evidence/2026-09/TASK-308-result.md`, merged to `main` at `48015283`
- **Criteria**: `perry/evidence/2026-09/TASK-308-spec.md` § Verification

## Criterion 1 — the before-state, re-derived — **MET**

I re-derived the census from the filesystem with my own matcher, not the round's.

```
$ ls perry/evidence/*/*-spec.md | wc -l
     148
$ python3 -c "import glob,re; specs=sorted(glob.glob('perry/evidence/*/*-spec.md')); \
  rx=re.compile(r'^#{2,}\s*Bound\s*$',re.M); b=[p for p in specs if rx.search(open(p).read())]; \
  print('total',len(specs),'bound',len(b),'unbound',len(specs)-len(b))"
total 148 bound 25 unbound 123
```

`bin/perry-lint --root .` prints, today:

```
· bounds: 123 of 148 spec(s) carry no `## Bound` — a round against those has no
          finite set to check and no last element (`perry-lint --specs --json`
          names every one)
```

**123 of 148 — exactly what the PMO saw on 2026-09-03.** My independent regex
(`^#{2,}\s*Bound\s*$`) and the lint's own `_BOUND_RE` (`^#{2,}\s*Bound\b`,
`bin/perry-lint:2184`) agree on the count, so the census does not depend on the
matcher being lenient.

**Every historical figure in the spec and the result also re-derives.** I walked
each cited ref with `git ls-tree` + `git show`, reading nothing from either
document:

| ref | specs | bound | unbound | claimed by | matches |
|---|---|---|---|---|---|
| `47fa45a` | 144 | 17 | 127 | spec § Why this row exists | yes |
| `548f206` | 146 | 19 | 127 | result § Before-state | yes |
| `9c9670e` | 147 | 20 | 127 | result § Notes 4 | yes |

The result corrected the spec's stale 144/17 to 146/19 and said the *missing*
count was unchanged at 127. Both halves of that are true. This is the opposite
of the copy-forward failure the brief warned about: the round re-measured and
published the correction.

**`criteria-unbounded` reporting 0 also reproduces.** I extracted the pre-change
binary and ran it against today's tree:

```
$ git show 548f206:bin/perry-lint > /tmp/old-perry-lint.py   # copied to bin/ to resolve `lib`
$ python3 bin/old-perry-lint-tmp --root .        →  0 error(s), 26 warning(s)
    grep -c criteria-unbounded  → 0
    grep -c spec-unbounded      → 0
$ python3 bin/old-perry-lint-tmp --root . --reviews | grep -c criteria-unbounded → 0
$ ./bin/perry-lint --root .                      →  0 error(s), 37 warning(s)
```

26 → 37 is +11 = 10 named + 1 remainder, exactly the after-state the result
claims. The cause is structural and I read it myself: in the pre-change file the
`criteria-unbounded` finding at `:2466` sits inside
`for fields, line in parse_verdicts(text):` at `:2412` — it cannot execute for a
spec no verdict block cites. (Temp copy removed; tree clean.)

## Criteria 2, 3, 5, 6 — established on **my own** fixture

I did not take the round's tests as evidence for its own property. I wrote an
independent fixture from the spec's Verification items and ran it against the
shipped binary: `scratchpad/fixture.py`, 27 checks. It builds its own minimal
project, writes its own bounded/unbounded spec pair, and invokes the real
`bin/perry-lint`.

**My anti-accident assertion is stricter than the round's.** Theirs rejects a
fixture containing `=== VERDICT ===` or a file named like a review. Mine also
rejects any file containing `verdict:`, `criteria:`, `rung:`, `PASS` or `FAIL`,
so a green result cannot be explained by the verdict-side check having fired.
The fixture passes that assertion, and my run separately confirms
`criteria-unbounded` is absent from the findings while `spec-unbounded` is
present — so I know which half spoke.

### Criterion 2 — the property — **MET**

```
PASS  C2 fixture contains NO review artefact of any kind  []
PASS  C2 spec-unbounded reported by the DEFAULT pass
PASS  C2 stats unbounded == 1
PASS  C2 the finding names the spec path
PASS  C2 it appears in HUMAN output too, not only --json
PASS  C2 no verdict-side rule fired (proving which half spoke)
```

My `lint()` helper asserts `--specs` and `--reviews` are both absent from the
argv, so this is the default invocation — the point of the row.

### Criterion 3 — the control — **MET**

```
PASS  C3 control fixture also has NO review artefact
PASS  C3 a bounded spec is SILENT
PASS  C3 stats unbounded == 0
PASS  C3 the two fixtures differ ONLY in the bound
PASS  C3 in a MIXED tree it names only the unbounded one
PASS  C3 mixed tree stats: 2 specs, 1 unbounded
```

The mixed-tree case is mine, not the round's, and is the sharper control: in one
run over two specs the check names the unbounded one and only it. A check firing
on all 148 could not produce that.

### Criterion 5 — severity — **MET**, and the argument holds

**Option chosen: `warn`, named list capped at `DRIFT_ROWS_SHOWN` (10) plus one
remainder finding, exact count in `stats`, every path under
`perry-lint --specs --json`.** Measured, not read:

```
PASS  C5 severity is warn, not error                      ['warn']
PASS  C5 the NAMED list is capped at 10                   got 10
PASS  C5 exactly one remainder finding
PASS  C5 the remainder states the true tail (25-10=15)
PASS  C5 the COUNT is not capped (stats says 25)          got 25
PASS  C5 --specs --json names every one (25, uncapped)    got 25
```

On the real tree: `0 error(s), 37 warning(s)`, exit **0** plain and **1** under
`--strict`. Eleven lines, not 123. The spec's explicit prohibition — "report 127
warnings and call it done" — is not what shipped.

**Does the justification hold? Yes, on three independent grounds.**

1. It is not a new answer. `check_specs` already reports 45 unscannable specs as
   10 + 1 through the same `cap`, `check_summaries` does it for 89, and the six
   store-drift checks share `DRIFT_ROWS_SHOWN`, whose own comment gives this
   exact reason ("a hundred warnings saying one thing is a check people learn to
   scroll past"). `reference/diagnose.md` rates a wall of red as strictly worse
   than no check; the cap is this codebase's settled response, and inventing a
   second one here would be the defect.
2. The rejection of "specs newer than a date" is self-referentially correct and
   I checked the reasoning rather than the prose: such a set is not enumerable,
   so you cannot state its last element — the check would violate the very rule
   it enforces.
3. The rejection of "only rows at `review` or being dispatched" is the strongest
   part of the argument, because it would reintroduce the exact defect: scoping
   to board state makes the spec-side check consult a row's status the way the
   verdict-side one consults a verdict. **And it is pinned, not merely argued** —
   `test_the_spec_side_check_reads_no_verdict` strips the docstring and comment
   lines and asserts `check_specs`'s *code* mentions none of `parse_verdicts`,
   `BOARD.md`, `events.jsonl`, `tasks.jsonl`. I ran it; it passes. That is the
   property that makes the check fire in time, held by a test rather than by
   intent.

`warn` over `error` follows the row's own `Out of scope` ("report, do not
refuse"), the `DESIGN-003 § 4` decision-4 and TASK-284 `scope_scanned`
precedents, and avoids retroactively blocking 123 existing rows. `--strict`
still promotes per run, so a dispatcher can opt into being stopped without that
choice being imposed. The argument is in the `check_specs` docstring, not only
in the result document.

**One correction to my own first run.** My fixture initially reported the
default exit code as 1. That was my fixture's defect, not the rule's: a minimal
project with no `BOARD.md` emits `missing-file` and two `missing-header-field`
errors. I re-ran both arms and got the *identical* three errors in the bounded
control, which has zero warnings — so `spec-unbounded` contributes nothing to
the exit code. Confirmed directly on the real tree: `perry-lint --root .` exits
0 with 37 warnings.

### Criterion 6 — presence and shape only — **MET**

This is the "what this must not become" clause, and it is the one I probed
hardest. The check is a single `if not _BOUND_RE.search(...)` against
`_BOUND_RE = re.compile(r"^#{2,}\s*Bound\b", re.M)` (`bin/perry-lint:2184`).
There is no scoring path, no content inspection, no classifier.

```
PASS  C6 a WORTHLESS bound ('TBD.') is accepted — no quality judgement
PASS  C6 an EMPTY bound section is accepted — presence only
PASS  C6 shape not substring — prose mentioning Bound is STILL reported
PASS  C6 shape not substring — a bullet `- **Bound**:` is STILL reported
PASS  C6 shape not substring — a bare `Bound:` line is STILL reported
PASS  C6 a nested `### Bound` counts (matches the verdict-side reading)
PASS  C6 only `*-spec.md` is judged (a result file is not)
```

The **empty-section** case is mine and it is the decisive one: a `## Bound`
heading with nothing under it at all is accepted. A checker that had drifted
even slightly toward quality would have to reject that. It does not. This is
presence-and-shape and nothing else — the fifth guard-over-English attempt did
not happen here.

## Criterion 4 — the verdict-side check still fires, both documented — **MET**

Both halves exist and both are documented as the spec required.

- **Spec-side** `spec-unbounded`, `bin/perry-lint:3068`: *"**Which question this
  one answers**: this spec has no finite set to check, and no round has been
  dispatched against it yet"*, and names the verdict-side half as answering a
  different question, "deliberately not unified".
- **Verdict-side** `criteria-unbounded`, `bin/perry-lint:2391` (the check itself
  now at `:2487`, one line below the `:2458` the brief cites — the file shifted
  as the docstring grew; it is the same check, still inside
  `for fields, line in parse_verdicts(text):` at `:2436`): *"**The question this
  one answers**: this round scored against an unbounded criterion"*, followed by
  **"Do not unify them (TASK-308)"** and the concrete reason each is a real loss.

The verdict-side check fires on its own case, verified by running it:

```
$ python3 -m unittest tests.test_review_verdicts.TestTheCriteriaMustBeBounded -v
test_a_criteria_file_with_no_bound_is_reported ... ok
test_a_criteria_file_with_a_bound_is_not ... ok
test_a_nested_bound_still_counts ... ok
test_a_closed_row_is_not_condemned_retroactively ... ok
test_a_missing_criteria_file_is_one_finding_not_two ... ok
Ran 5 tests — OK

$ python3 -m unittest tests.test_spec_scannability.TestBothHalvesOfTheBoundRuleSurvive -v
Ran 4 tests — OK
```

The unification risk is guarded structurally, not just by prose:
`test_both_checks_are_present_in_the_source` fails if either is deleted;
`test_each_docstring_says_which_question_it_answers` fails if either docstring
stops naming its question and TASK-308; `test_they_share_one_matcher` asserts
exactly one `_BOUND_RE = re.compile` and exactly two `_BOUND_RE.search` call
sites, so the two checks cannot drift into two answers about what a bound is.

The docstring also records the *concrete* blind spot that makes keeping both a
real loss rather than a theoretical one: `spec-unbounded` cannot see a criteria
file that is not a `*-spec.md`, and one such file exists.

## Criterion 7 — full suite; `perry-lint --root .` at 0 errors — **MET**

```
$ tests/run
114 modules · 3291 tests · 206.9s · 8 workers
✗ 1 of 114 MODULE(S) red
✗ 2 of 3291 TEST(S) failed
  ✗ test_contract_key_parity.py — 2 of 35 test(s) failed
    FAIL: test_without_the_witness_the_four_are_unobservable
          [conformance.in_progress_with_no_live_run[].means]
    FAIL: test_the_same_mutation_is_silent_without_the_witness
          [conformance.in_progress_with_no_live_run[].means]
tree guard: ✓ nothing under the worktree moved
```

**Exactly the two known reds, and they are not this row's.** Both are the
`in_progress_with_no_live_run` anti-vacuity controls that decay against
wall-clock time — `bin/perry-task:6300-6308`, the `idle >= in_progress_limit`
4-hour threshold measured against Perry's own live board. That is TASK-335,
which is already an open row titled *"Two contract-parity tests fail because the
witness cannot make a collection observable"*. I checked they cannot be this
row's: `grep -c "perry-lint\|spec_scannability\|spec-unbounded\|_BOUND_RE"
tests/test_contract_key_parity.py` returns **0** — the failing module does not
reference the changed code at all, and `git log` shows its last three commits
are TASK-235, TASK-205 and a timezone change, none of them TASK-308.

The suite is larger than the round measured (114 modules / 3291 tests vs its
113 / 3179) because `main` advanced by roughly forty commits between the round
and this review. The tree guard passed.

```
$ ./bin/perry-lint --root .        →  0 error(s), 37 warning(s)   rc=0
$ ./bin/perry-lint --root . --strict                              rc=1
```

**0 errors, as the criterion requires**, measured at my HEAD `9c6ce22`.

## The corpus moved three times during this review — what my numbers are pinned to

`main` advanced under me twice while I worked (two HTTP 403 kills, server-side).
A figure carried forward without its commit is the exact defect this project hit
repeatedly this week, so every census below names the commit it was measured at,
and I derived all of them myself with `git ls-tree` + `git show`, reading no
number out of either document:

| commit | specs | bound | **without** | who cites it |
|---|---|---|---|---|
| `47fa45a` | 144 | 17 | **127** | the spec, § Why this row exists |
| `548f206` | 146 | 19 | **127** | the result, § Before-state |
| `9c9670e` | 147 | 20 | **127** | the result, § Notes 4 |
| `7f890f9` | 148 | 25 | **123** | **my branch point — my own census** |
| `651a5ca` | 149 | 26 | **123** | `main` mid-review |
| `1d3fd17` | 149 | 26 | **123** | `main` at time of writing |

**My census is measured at `7f890f9`, my branch point: 148 specs, 123 without a
bound** — identical to the `123 of 148` the PMO saw on 2026-09-03, and identical
to what `bin/perry-lint --root .` prints at my HEAD `9c6ce22`.

Every cited historical figure re-derives exactly at the commit that cites it.
Nothing was copied forward wrongly. The one spec added since my branch point
(`TASK-339-spec.md`) carries a `## Bound` at its line 117, which is why the
*unbounded* count holds at 123 while the total moves — the same pattern the
round documented for 47fa45a→548f206. The corpus moving does not touch the
finding.

## The spec's false `## Bound` claim about TASK-067 — **it changed nothing**

The spec's own `## Bound` Remainder says non-spec criteria files exist "and
TASK-067 uses one". **I verified that is false**, rather than taking it:

```
$ ls -1 perry/evidence/*/TASK-067-spec.md
perry/evidence/2026-09/TASK-067-spec.md              ← TASK-067 HAS a -spec.md

$ grep -rl "^## What must be true when this is done" perry/evidence/
perry/evidence/2026-08/TASK-042-spec.md
perry/evidence/2026-08/TASK-050-spec.md
perry/evidence/2026-08/TASK-065-extraction.md

$ ... | grep -i task-067
NONE — the spec's Bound claim is FALSE
```

Three files carry that heading. Two are `*-spec.md` and so are already inside
the pass's scope. **Exactly one is not: `TASK-065-extraction.md`.** No TASK-067
file carries it. The PMO wrote the error.

**Did it change what the round built? No — and I checked the build, not the
prose.** Three reasons:

1. **The Remainder clause asked for a count and a deferral, not a behaviour.**
   It said report the count of non-`*-spec.md` criteria files and leave whether
   the pass should reach them to a new row. The round reported **count: 1**,
   naming `TASK-065-extraction.md`. I re-derived that count independently and
   got 1. The deliverable was the number, and the number is right regardless of
   which task was named as the example.
2. **The pass's scope is unchanged and correct.** `check_specs` selects
   `sorted(edir.rglob("*.md"))` filtered by `SPEC_FILE_RE = re.compile(r"-spec\.md$")`
   (`bin/perry-lint:2922`, used at `:3042`). It reads `*-spec.md` and nothing
   else — which is what Deliverable item 1 specified. A wrong example could only
   have misled the round into widening or narrowing that scope, and it did
   neither.
3. **The round caught the error itself and said so.** Result § Notes 2 states
   the claim does not hold, gives the correct file, and separates the Bound's
   wrong *claim* from its right *point* — that such files exist and are outside
   this row. That is the correction being published rather than inherited.

The error is real and worth recording against the PMO's spec-writing, not
against this round. If anything it argues *for* what shipped: the concrete
blind-spot file is written into the verdict-side check's docstring as the reason
deleting that half would be a real loss, and that reasoning is correct even
though the spec named the wrong task.

## Mutations re-run independently — **5 planted, 5 red, 0 GREEN**

I re-ran five of the round's seven with my own harness
(`scratchpad/mutate.py`), not theirs. The brief asked for at least two.

Protocol, obeyed on every one: anchored by line number **with an assert on the
old text at that line**; `__pycache__` cleared and a 1.1 s sleep past the
whole-second boundary around every apply and restore; restored with
`git show HEAD:bin/perry-lint` **single path only**; and the restore verified by
comparing `git hash-object` of the file against `git rev-parse HEAD:<path>` —
never against a harness snapshot, which is the circular check TASK-256 names.
**`bin/perry-restore-check` was not used**, per the brief.

```
=== baseline: clean tree, tests green ===
  bin/perry-lint blob da2e89c15c51 == HEAD:bin/perry-lint da2e89c15c51 · tree clean
  baseline GREEN  test_the_whole_point
  baseline GREEN  test_the_word_alone_is_not_a_bound
  baseline GREEN  test_a_spec_that_has_a_bound_is_silent
  baseline GREEN  TestTheCriteriaMustBeBounded
  baseline GREEN  TestBothHalvesOfTheBoundRuleSurvive
```

| # | mutation | anchor | paired test | result |
|---|---|---|---|---|
| M1 | `if False and …` — revert the new call site | `:3095` | `test_the_whole_point` | **RED** (failures=1) |
| M2 | `if True or …` — fire on every spec | `:3095` | `test_a_spec_that_has_a_bound_is_silent` | **RED** (failures=1) |
| M3 | `"Bound" not in` — substring, not the shape regex | `:3095` | `test_the_word_alone_is_not_a_bound` | **RED** (failures=2) |
| M7 | `if False:` — delete the verdict-side half | `:2487` | `TestTheCriteriaMustBeBounded` | **RED** (failures=5) |
| M7b | same mutation, against the anti-unification guard | `:2487` | `TestBothHalvesOfTheBoundRuleSurvive` | **RED** (failures=1) |

```
=== summary ===
  5 mutations · 5 red · 0 GREEN
  final tree: ''
```

Every restore reported `blob da2e89c15c51 == git da2e89c15c51 · tree clean`.

M7b is the one I added beyond the round's pairing, and it is the one that
matters for criterion 4's durability: disabling the verdict-side call site drops
`_BOUND_RE.search` from two sites to one and `test_they_share_one_matcher` goes
red. So "unify the two checks into one" is caught mechanically, not left to the
docstring's request.

**I verified my own harness cannot produce a false green.** A line-number anchor
without a text assert silently no-ops when the file shifts, and a no-op mutation
looks red-free. `scratchpad/anchorguard.py` feeds the correct anchor text at the
adjacent lines `3094`, `3096` and at `2458` (the line the brief cites, which the
file has since shifted past):

```
would have mutated                       # 3095, the true anchor
guard fired at line 3094: ANCHOR MISS …
guard fired at line 3096: ANCHOR MISS …
guard fired at line 2458: ANCHOR MISS …
anchor guard verified — a shifted line raises rather than no-opping
tree: ''
```

### On the round's own reported GREEN

The result document reports that round 1 produced one green mutation (M6, the
dead loop, paired with the *control*) and chased it rather than waving it off.
I re-derived its reasoning and it is correct: a control's job is to catch the
check **over**-firing, and a check that reports nothing is trivially silent on a
bounded spec too, so the control cannot detect a dead check. The pairing was
wrong, the check was not — the round demonstrated this by re-running the dead
check against the main property test, the whole class and the module, all red.
Declaring a green and diagnosing it is the behaviour the mutation discipline
asks for; it is not a defect in this round.

## Verdict

PLACEHOLDER_VERDICT
