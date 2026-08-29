# TASK-230 — V4 review

**PASS.**

Reviewed `e685c6b`, tip of `coding/task-230-suite-cost`, in the detached worktree
`scratchpad/review-230`. Both that worktree and the author's `scratchpad/wt-230`
were clean at `e685c6b` before and after this round. Every mutation in this
review was applied to a `git archive e685c6b` copy under `scratchpad/rv230/mut`,
never to a reviewed tree. The one thing I ran inside the review worktree was the
suite itself (`python3 tests/parallel --ids … --times`, no `--record`), which
writes nothing into the repository; `git status --porcelain` is empty after it.

---

## 1. The constraint this review exists to enforce: did anything stop being tested?

**No. Verified independently, by a means the author did not use, three ways.**

The author's argument runs entirely through `parse_ids` — its own stderr parser
— so I did not use it. I used `unittest`'s **loader**, which never runs a test
and never touches the runner's code, to enumerate what whole-suite `discover`
*collects*, and compared that against the per-module partition `tests/parallel`
actually executes.

```
$ cd scratchpad/review-230
$ python3 -c "... unittest.defaultTestLoader.discover('tests', top_level_dir='tests') ..."
collected at 78aa67e: 2904          # placeholders: []
collected at e685c6b: 2907          # placeholders: []

$ ls tests/test_*.py | xargs -n1 basename \
    | xargs -P 8 -I{} python3 rv230/one.py {} > permodule.txt   # one process per module
2907
```

| comparison | result |
|---|---|
| whole-suite loader collection vs union of per-module loader collections (`e685c6b`) | 2907 vs 2907, **only-whole 0, only-per-module 0** |
| loader collection @`78aa67e` vs **my own re-implementation** of the id parser run over the author's raw `serial.err` | 2904 vs 2904, **0 / 0** |
| loader collection @`78aa67e` vs each of the author's **12** `--ids` files | 12/12 exactly 2904, **0 / 0** each |
| **my own fresh `tests/parallel --ids` run @`e685c6b`** vs loader collection @`e685c6b` | 2907 vs 2907, **0 / 0** |
| all 12 author id files pairwise | `all 12 id sets identical: True, size 2904` |

So the claim "2904 = 2904, zero on either side, 12 identical sets" is true, and it
is true against a reference that does not pass through the author's code at all.
`schedule()` is `sorted(mods, key=…)` over the glob's own result — a permutation
by construction — and `mods` is computed before and independently of
`durations.json`. Sharding by module changes the order and nothing else.

**Outcome comparison, my run vs the author's serial log** (my parser, not theirs):

```
differing outcomes on shared ids:
  test_risks_store.TestTheReadersAreOneFunction.test_the_bullet_and_placeholder_rules_are_one_object FAIL -> ok
  test_risks_store.TestTheReadersAreOneFunction.test_the_columns_are_one_list                        FAIL -> ok
  test_risks_store.TestTheReadersAreOneFunction.test_the_register_header_predicate_is_one_object     FAIL -> ok
```

Exactly the three pre-existing `assertIs` module-identity failures § 5 names, by
name, and nothing else. § 5 is accurate.

**Total CPU, independently** (from the author's `/usr/bin/time -p` files, and my
own run): alphabetical `user+sys` 501.3s / 500.5s, longest-first 475.8s / 482.6s,
mine 491.1s. Meanwhile the *sum of per-module wall times* swung 766s → 1236s
across the same four runs. Constant CPU under a 1.6x swing in summed wall is the
signature of contention, not of lost work — a genuinely separate argument from
the id-set check, and it holds.

---

## 2. The audit of the inherited commit — all three claims reproduced

### Claim 1: the inherited `--ids` set silently dropped 14 tests — **CONFIRMED**

Reproduced on a **different corpus** than the author used. The author measured on
per-module parallel output; I ran both parser versions over the author's raw
`serial.err` (the serial `discover -v` log, 553 KB):

```
old parser ids: 2890   unique: 2890
new parser ids: 2904   unique: 2904      # unittest's own line: "Ran 2904 tests"
in new but not old: 14
    test_events_feed 2
    test_live_state_expectations 3
    test_migrate 3
    test_one_header_rule 1
    test_one_startable_rule 3
    test_shipped_vocabulary 1
    test_stranded_rows 1
```

Fourteen, across exactly the seven named modules, with the same per-module
distribution. The mechanism is exactly as described: `unittest` prints ` ... `
when the test *starts*, so a `DeprecationWarning` written to stderr pushes the
verdict onto its own line, and the old `_OUTCOME.search` — which requires
` ... <verdict>$` — matched nothing. The old count on the diag run was 2885 of
2899; on the serial log it is 2890 of 2904. Both are 14 short. Self-consistent,
and `ids-diag.tsv` / `ids-longest-1.tsv` are on disk at 2885 lines while every
post-fix file is at 2904. This was a real defect and the audit is right.

### Claim 2: the refusal fires — **CONFIRMED, and I could not defeat it in the way that matters**

End-to-end, in the copy, with `run_module` truncated by one id:

```
$ python3 tests/parallel test_one_header_rule --ids …/refuse.tsv   # control
1 modules · 12 tests · 1.0s · 8 workers
✓ all green                      control rc=0, file written (1255 bytes)

# mutate: "ids": parse_ids(proc.stderr)  ->  parse_ids(proc.stderr)[:-1]
✗ test_one_header_rule.py: unittest ran 12 tests and the id parser accounted for 11
  — `--ids` would understate the set, which is the one thing it may not do.
✗ no --ids file written
mutant rc=1     ids file exists? NO
restored md5 307cdc1f877b422f9cebada39dcb64fb (MD5 MATCH)
```

Attempts to defeat it (`parse_ids` evaluated directly, no writes):

| shape | result | guard |
|---|---|---|
| verdict glued onto un-newlined output (`… ... some output ok`) | 0 ids vs `Ran 1` | **fires** — the author named this shape |
| test writes `Ran 5 tests` to stderr | inflates `ran` | **fires** (fail-safe direction) |
| a *failing* test writes `ok` to stderr | records `('mod.C.test_x','ok')`, count 1 = `Ran 1` | **silent** — outcome column lies |
| a test writes a line shaped `word (dotted.name)` | records `('a.b','FAIL')` — real id lost, fake id gained, count still 1 | **silent** — set corrupted |

Both silent shapes are residual, not blocking, and I say why in § 6. Neither can
turn a red module green: the runner's verdict comes from the subprocess **exit
code** (`r["rc"] != 0`), which never passes through `parse_ids`. And my loader
cross-check proves neither shape occurs on today's suite — the parsed set is
byte-for-byte the collected set.

### Claim 3: the inherited docstring's numbers were unreproducible — **CONFIRMED**

`tests/durations.json`, committed in the same change as the docstring claiming
322/282/234s, records `test_task_writer.py 567.25`, `test_store_drift.py 548.85`,
`test_store_is_canonical.py 463.53`. A 2x disagreement between two artifacts of
one commit. The replacement numbers *are* reproducible in the way the originals
were not: every run has a label, a timestamp, a load average before and after,
a `/usr/bin/time` file, and an id file on disk (`m230/times.txt`,
`m230/campaign.txt`, `m230/cpu-*.txt`, `m230/ids-*.tsv`). I recomputed from
those raw files and got the published numbers. That is the difference.

---

## 3. The A/B: I re-derived the simulation from scratch and it is arithmetically right — but the "0.1s, four of four" is oversold

I wrote my own greedy list-scheduler over each run's own `--times` output and my
own `schedule()`/`sorted()` orderings. Every cell of § 3 reproduces:

```
run           n      sum     max   floor  simAlpha  simHint  simPerf
t-alpha-1    99    766.4   120.1   120.1     179.7    120.1    120.1
t-hint-1     99   1052.8   140.0   140.0     222.9    140.0    140.0
t-alpha-2    99   1235.9   149.2   154.5     241.1    155.4    154.5
t-hint-2     99    978.0   133.1   133.1     210.4    133.1    133.1
```

Identical to the result's table, including the 0.9s loss to perfect knowledge in
`t-alpha-2`. The measured walls were 179.76 / 140.08 / 241.13 / 133.09.

**But two of the four "predictions" are arithmetically forced, not predictions.**
In both longest-first runs the makespan equals the *longest single module's own
measured duration* (140.0 and 133.1) because that module started first and the
run cannot end before it. Simulating it back gives the same number by identity.
Only the two alphabetical runs are non-trivial — there `max` is 120.1 and 149.2
while the simulated and measured makespans are 179.7 and 241.1, so the packing
model really is doing work and really is exact.

So the correct statement is: **the model is validated by two of the four, not
four of four, and that is still enough.** The result's "The model is exact …
four times out of four. That is the reason to believe the other column" (and the
same sentence in `tests/parallel`'s docstring, "**The model is exact**") is an
overclaim about the strength of the evidence, not about the conclusion. The
conclusion survives on the two real validations plus two independent supports:
the measured medians (188.4s alphabetical vs 149.7s longest-first) and the
structural floor argument. **Not blocking; the sentence should be corrected.**

A second, unstated modelling assumption: the counterfactual column assumes
per-module durations are invariant to the schedule. They are not — the summed
module time varied 766s to 1236s across the four runs. The bias runs *against*
longest-first (its heavy modules are measured while contending with each other),
so the 33–37% figure is conservative rather than flattering. Worth a sentence in
the result; not a defect.

---

## 4. Mutation: all five reproduced, and I extended the sweep to every new test

I re-ran all five of the author's mutations at `e685c6b` (they were originally
run at `78aa67e`), in the archive copy, restoring by md5 each time.

| # | mutation | my result |
|---|---|---|
| M1 | `bin/perry-lint:2386` `_board_line_of` matches any cell | `test_store_is_canonical…test_a_closed_row_named_in_depends_on_is_not_a_board_row` **FAILED (failures=1)** |
| M2 | `bin/perry-lint:2684` drop `title` from store-drift comparison | named test **FAILED**; whole module **FAILED (failures=4)** |
| M3 | `viewer/tables.py:142` `render_row` stops escaping `\|` | `test_task_writer…test_the_cell_survives_the_whole_write_path` **FAILED (failures=1)** |
| M4 | `parse_ids` reverts to the inherited shape | **FAILED (failures=3)** incl. the named test |
| M5 | `schedule()` selects instead of reordering | **FAILED (failures=9)** incl. the named test |

M2's anchor in the result (`bin/perry-lint:2680`) points at a five-line block
whose last line appears **four** times in the file (2684, 2833, 2972, 3095 — the
task, risk, intake and ask store-drift checks). The author's harness anchors on
the full five-line block, which is unique, so the mutation landed correctly. My
first attempt used only the last line, the uniqueness assert fired, and the test
came back green — an unplanned live demonstration of exactly the harness property
in § 6.

### Does any guard survive its own deletion?

I mutated **every** production surface the new tests cover, not only the five.
All 25 tests in `tests/test_parallel_runner.py` die under at least one mutation;
none is decorative or vacuous.

```
G1 load_durations stops coercing/filtering  -> 2 red
G5 load_durations stops swallowing          -> 4 red (errors)
G10 load_durations returns {} always        -> 1 red (test_a_good_file_reads_as_the_hint)
G6 drop the same-line outcome branch        -> 6 red
G7 drop the "no open test" guard            -> 1 red
G2 unaccounted reports only undercounts     -> 1 red
G8 unaccounted never reports                -> 2 red
G9 unaccounted always reports               -> 2 red
M4 / M5 as above                            -> 3 / 9 red
```

**One guard does survive its own deletion, and it is this row's own:**

```
G3: in main(),  if short: print("✗ no --ids file written")  ->  if False: …
$ python3 -m unittest discover -s tests -p test_parallel_runner.py
Ran 25 tests in 1.010s
OK
```

Delete the refusal from `main()` and the suite stays green. `unaccounted()` is
unit-tested; **its use — the actual refusal to write and the `return 1` — is
not.** The result's framing, "*Plus one end-to-end proof of the new refusal,
which a unit test cannot give*", is wrong: a unit test can give it trivially by
monkeypatching `P.run_module` and calling `P.main()` with a patched `sys.argv`,
in the same file that already shells out to a subprocess for
`test_every_test_in_the_live_suites_noisiest_module_is_accounted_for`.

Why this does not block: `main()` has **never** had coverage in this file — the
pre-existing zero-test guard survives its own deletion identically
(`empty = []` → `Ran 25 … OK`). The row added a third guard to an already
untested function rather than lowering an existing bar; the refusal demonstrably
fires today (§ 2, reproduced by me); and the property it protects is not the
gate — verdicts come from exit codes. **File it as a follow-up row**: cover
`main()`'s three guards (zero-test, module-red, `--ids` refusal), and delete the
"a unit test cannot give it" sentence.

---

## 5. Baselines — pre-existing, and I confirmed it against a tree that predates the row

`git archive` copies at the fork point `ee0b36a` and at `642e2ca`, running the
named tests directly:

```
===== ee0b36a (fork point, 66 commits back, predates every commit in this row) =====
  test_without_the_witness_the_four_are_unobservable            FAILED (failures=1)
  test_perry_itself_passes_its_own_id_checks                    FAILED (failures=1)
  test_the_queue_register_reconciles_with_the_queue_on_this_repository  FAILED (failures=1)
  test_no_current_in_the_payload_claims_to_be_a_measurement     FAILED (failures=1)
===== 642e2ca ===== identical
```

**None of the five baseline reds is caused by this row** — they reproduce on a
tree that does not contain it. That is a stronger statement than the author's and
it agrees with theirs.

The author's corroborating observation reproduces exactly. Recomputing § 7's
outcome table from the 12 id files:

```
 12/12  alpha=5/5 hint=7/7  test_diagnose … test_the_queue_register_reconciles…
 12/12  alpha=5/5 hint=7/7  test_diagnose … test_perry_itself_passes_its_own_id_checks
 12/12  alpha=5/5 hint=7/7  test_kr_progress_provenance … test_no_current_in_the_payload…
 12/12  alpha=5/5 hint=7/7  test_rung_vocabulary … (skipped)
 11/12  alpha=4/5 hint=7/7  test_contract_key_parity … test_without_the_witness_the_four…
 11/12  alpha=4/5 hint=7/7  test_contract_key_parity … test_the_same_mutation_is_silent…
  1/12  alpha=0/5 hint=1/7  test_host_support … test_concurrent_mixed_registers_do_not_exceed_global_cap
```

The `test_contract_key_parity` pair is red in **4 of 5 alphabetical runs** — it
flipped between two runs of the *same* arm, which rules the schedule out, and it
is red on the fork-point tree too. The author's reasoning is sound and the data
supports it.

My own run reproduces the whole picture: `99 modules · 2907 tests · 246.8s ·
8 workers`, red on exactly `test_contract_key_parity` (2), `test_diagnose` (2),
`test_kr_progress_provenance` (1) — five tests, three modules, nothing else.

---

## 6. Ruling on each declared limit

### Limit 1 — "under two minutes" is not achievable by this approach. **Does not block. The author is right, and the spec contradicts itself.**

The floor argument is `makespan ≥ max(longest module)` and no worker count moves
it. My own run demonstrates it about as cleanly as it can be demonstrated:

```
  seconds  tests  module
   246.74    281  test_task_writer.py        <- the longest module
…
99 modules · 2907 tests · 246.8s · 8 workers  <- the whole run
```

The run ended **0.1s** after its longest module did. Reaching 120s requires
splitting `test_task_writer.py`, and the spec itself says "**shard by file, never
by test method**" in its own Out-of-scope/hazards section. The target and the
constraint cannot both be honoured; the author identified the contradiction,
stated it, and declined to resolve it by violating the constraint. That is the
right call.

The number that actually matters is the one the row was opened on: a **600s**
watchdog. Serial is 589.6s and touches it. The worst of twelve parallel runs was
285.0s, the median 149.7s, and mine 246.8s under load 25→46. The trigger is
addressed with margin. Ship it and file the `test_task_writer.py` split as its
own row, as the author proposes.

### Limit 2 — declining to claim a flakiness effect. **Correct, and the mechanism does not need measuring before this ships.**

1 of 7 against 0 of 5 is not a difference by any test one could apply, and
reporting it as "0% → 14%" would have been the dishonest option. Declining is the
right call and the author volunteering the *adverse* mechanism — longest-first
deliberately starts the eight heaviest modules at once, so peak contention now
coincides with a concurrency test — is the behaviour this project wants.

I rule that it does not block, for three reasons: the flake is pre-existing and
already filed; the run is now 2–4x shorter, so the exposure window is smaller,
not larger; and the counterfactual is not "no flakes", it is the serial suite
that is currently killing dispatches. It is 0/1 in my run.

It should be **filed as a follow-up with a concrete design** — N ≥ 30 runs of
`test_host_support` alone under both schedules — rather than left as a paragraph.
An adverse mechanism named and then not measured is the kind of thing that gets
rediscovered as a mystery in three weeks.

### Limit 3 — the machine was never quiet. **The evidence survives its conditions.**

Load was 17–65 for the author and 20–46 for me; the identical command took 133.1s
and 285.0s for them and 246.8s for me. Wall-clock here is not a measurement and
the author says so first, in § 1, before quoting any number.

What survives is everything load-independent, and that is the load-bearing part:
the id-set equality (a set, not a clock — and I re-derived it from a static
loader, which has no timing component at all); the CPU totals; and the floor
`makespan ≥ max module`, which I reproduced to 0.1s on my own differently-loaded
run. The wall-time saving is the weakest claim and rests on medians plus a model
validated twice; § 3 above states what that is worth. The author's own framing —
"it is a model … a re-measurement on an idle box would be worth someone's ten
minutes" — is the right one.

### Limit 4 — 65 commits behind `main`. **Verified as far as it can be without merging; the expectation is well-founded.**

```
$ git merge-base HEAD main                                 -> ee0b36a
$ git rev-list --count ee0b36a..main                       -> 66      (author said 65; main moved by one since)
$ git log ee0b36a..main -- tests/parallel tests/run \
      tests/test_parallel_runner.py tests/durations.json   -> (empty)
$ git ls-tree -r --name-only main -- tests | grep -c 'test_.*\.py$'  -> 100
```

`main` has touched none of the four files. "Expected clean — expected, not
verified" is the honest phrasing and it is accurate. The one behaviour that
matters after the merge is what happens to `main`'s 100th module, which has no
`durations.json` entry: `schedule()` keys it `-float("inf")`, so it sorts
**first**, the safe direction. I read that and it is true. The totals in the
result describe this branch's 99 modules and will shift on merge; the result says
so. **The merge must still be run and the suite re-run on the merged tree** —
that is a merge-time obligation, not a defect here.

### The `git checkout --` note. **It does not matter, and reporting it was right.**

One `git checkout -- tests/parallel`, in the author's own dedicated worktree, on
its own uncommitted diagnostic edit, on a file it had committed minutes earlier.
`review-constraints.md`'s prohibition sits under "**You are a reader** / The
repository is live", and the harm it names is destroying work that is not yours
and is not recoverable. In a single-purpose worktree containing only the author's
own in-flight change, on a file whose committed state was minutes old, neither
condition applies.

I can corroborate the outcome, not the transcript: `wt-230` is clean at
`e685c6b`, its `tests/parallel` md5 matches the committed blob exactly
(`307cdc1f…`), and every commit's content is intact. I cannot audit what the
discarded diff contained; that is in `not-checked` below. Switching to explicit
`cp`/md5 afterwards was the right correction, and volunteering it rather than
hoping nobody diffed the transcript is exactly the behaviour that makes the rest
of this result document worth believing.

---

## 7. Findings — all non-blocking, all should be filed or fixed before merge

1. **`main()`'s `--ids` refusal survives its own deletion** (§ 4, G3). Delete it
   and the suite is green. Follow-up row; and remove the incorrect sentence "which
   a unit test cannot give".
2. **"The model is exact … four times out of four" is an overclaim** (§ 3). Two of
   the four agreements are arithmetic identities. Correct the sentence in
   `perry/evidence/2026-08/TASK-230-result.md` § 3 **and** in `tests/parallel`'s
   docstring, which repeats it. The conclusion does not change.
3. **An md5 citation that matches nothing.** Result § 6 says the end-to-end
   refusal proof restored `tests/parallel` to md5
   `430637240808773774420e83ca1b593d`. The file's md5 is `ce4fe6e0…` at
   `23e6197`, `7e66ae40…` at `78aa67e`, `307cdc1f…` at `642e2ca` and `e685c6b`.
   The benign reading — that the proof ran on an intermediate working state
   carrying the new guard but not yet the rewritten docstring — is consistent
   with everything else and with the tree being clean and correct now. But as
   written the citation is unverifiable. Say which state it hashes, or drop it.
4. **The headline quotes the favourable subrange.** `tests/parallel`'s docstring
   header and `tests/run`'s comment both say "589.6s serial → 133–150s across 8
   workers", omitting the 247.0s and 285.0s runs that appear four lines further
   down. Mine was 246.8s. A reader of `tests/run` will form a wrong expectation.
   Quote the median (149.7s) or the full range.
5. **Two residual `parse_ids` shapes the accounting guard does not catch** (§ 2):
   a test writing a bare verdict to stderr silently mislabels its own outcome; a
   test writing a line shaped `word (dotted.name)` silently substitutes one id
   for another with the count unchanged. Neither can flip a module's verdict
   (that comes from the exit code) and neither occurs on today's suite (proved by
   the loader comparison). Worth a sentence in `parse_ids`'s docstring beside the
   shape that *is* named.
6. **Cheap hardening, optional:** `main()` never asserts `len(order) == len(mods)`
   at runtime. `schedule()` is a permutation by construction and is covered nine
   ways, so this is belt-and-braces — but it is one line at the point where a
   dropped module would otherwise be invisible.

---

## checked / not-checked

**checked** — id-set equality via an independent `unittest` loader enumeration at
two commits, whole-suite vs per-module, in separate processes (0/0 both ways);
the same set against my own re-implementation of the id parser run over the
author's raw serial log (0/0); the same set against all 12 of the author's `--ids`
files (0/0 each) and against my own fresh `tests/parallel --ids` run (0/0);
pairwise identity of the 12 sets; the outcome diff serial-vs-parallel (exactly
the 3 named `test_risks_store` tests); the 14-dropped-tests audit reproduced on a
different corpus, same 7 modules, same distribution; the `--ids` refusal proved
end-to-end in a copy plus four attempts to defeat it; the § 3 simulation
re-derived from scratch (every cell reproduces) and its two tautological cells
identified; CPU totals from the raw `time -p` files and from my own run; all five
author mutations re-run at `e685c6b`; eight further mutations covering every
production surface the new tests touch (all 25 tests die under at least one; one
guard survives, named above); the mutation harness source read and its
anchor-assert, uniqueness-assert, green-before-assert, pycache-clear, mtime-tick
and md5-restore clauses all confirmed present; the baseline reds reproduced on
the fork point `ee0b36a`; the § 7 outcome table recomputed from the id files
(reproduces digit for digit); the branch-distance and untouched-files claims;
`tests/run`'s step-2 change (comment only, `--serial` escape intact) and its
`[ "$fail" = 0 ]` suppression of step 3's summary; `durations.json` (99 entries,
values as described); `tests/gate.py`/`GATE_OFF` is not reachable from any new
test.

**not-checked** — I did not run a serial `discover` myself (≈590s on a loaded
box); I used the author's raw `serial.err` and parsed it with my own code
instead, plus the static loader enumeration, which together cover the same
question. I did not merge `main` into the branch or run the suite on a merged
tree. I did not re-measure on a quiet machine — the box was at load 20–46
throughout, so my 246.8s wall is one sample and not a contradiction of the
author's median. I did not attempt to reproduce the `test_host_support` flake
(one event in twelve is not something a single review round can move). I did not
audit the author's transcript, so I cannot verify the content of the diff dropped
by the `git checkout --`, only that the resulting tree and commits are intact. I
did not investigate the five pre-existing baseline failures beyond establishing
that they predate this row.
