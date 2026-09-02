# TASK-304 — round 1, V4 review

> Reviewer: fresh V4 reviewer, wrote none of this code
> Branch under review: `coding/task-304-durations-provenance-b` @ `788538b`, 8 commits
> Base: `d49964e` (the OLD `main`; `main` has since moved to `d146c15`)
> Criteria: `perry/evidence/2026-09/TASK-304-spec.md` (read in full, from `main`)
> Measured: 2026-09-02, load 8.3–14.4 across the checks below

Every claim below was re-derived in a scratch tree of my own, never in the
shared checkout. Two pristine extracts (`git archive d49964e` and
`git archive 788538b`) plus one standalone `git init` snapshot of the branch
(`8f1c666`) used as a mutation lab, so `git_ancestor` and `head_ref` had a real
repository to answer for without touching Perry's.

**Verdict: PASS**, with **one blocking merge action**: today's `main` carries
`tests/test_spec_scannability.py`, which this branch's `durations.json` does
not list, so the round's own new red gate fires on the merged tree. One
`sec: null` entry fixes it (finding 5). Four further findings are filings.

The branch meets its criteria against **its own base**, which is what the
brief asked me to measure. Finding 5 is about the tree it is going into, and
it is the guard working rather than the guard failing.

---

## 1. What I re-derived myself

### 1a. The reproduction, at the base, through the runner's own code

Driven through `d49964e`'s `tests/parallel.load_durations()` and `schedule()`
over the live `tests/test_*.py` glob. Load `12.29 9.17 14.59`.

    recorded: 103   on disk: 108
    phantom  (recorded, not on disk): ['test_conformance.py', 'test_migrate.py']
    unlisted (on disk, not recorded): 7 — test_config_store_readers,
      test_context_budget, test_header_index_is_the_only_fold,
      test_phase_kr_declared_once, test_register_store_invariant,
      test_register_substitution, test_tree_guard
    recorded serial total: 1968.9s

The file's own ranking, top five:

    test_migrate.py       97.25  *** DOES NOT EXIST ***
    test_track_move.py    94.96  ON DISK
    test_goals_writer.py  86.22  ON DISK
    test_purge.py         85.95  ON DISK
    test_diagnose.py      83.25  ON DISK

`schedule()`'s actual head over the live glob:

    test_config_store_readers.py            inf
    test_context_budget.py                  inf
    test_header_index_is_the_only_fold.py   inf
    test_phase_kr_declared_once.py          inf
    test_register_store_invariant.py        inf
    test_register_substitution.py           inf
    test_tree_guard.py                      inf
    test_track_move.py                      94.96

**The round's narrower claim is the true one, and the spec's sentence is not.**
`schedule()` sorts the glob, so `test_migrate.py` never enters the run order at
all — it is not "at the head of the schedule". What is true is exactly what
§1 of the result says: the *file's own ranking* is headed by a module that
cannot run, and the *schedule's* real head is seven modules the file never
mentions, sorting as `inf`. I confirmed both halves independently, and the
round is not charged for declining the spec's framing.

### 1b. Nothing was backdated, and no retained figure was altered

`tests/durations.json` at `788538b` has exactly two source blocks. Both carry
`"ref": null`, `"taken": null`, `"workers": null`, `"load1": null`:

- `unstamped-pre-304` — 101 entries
- `never-measured` — 8 entries, every one with `"sec": null`

Diffed old flat map against new `modules` map, entry by entry:

    dropped from old: ['test_conformance.py', 'test_migrate.py']   (the 2 phantoms)
    value changed:    []                                           (none, at all)
    added:            the 8 unmeasured, sec:null

So no figure was moved, rounded, or backdated to a plausible commit. This is
the row's whole subject and it is clean.

### 1c. The schedule genuinely did not change — the strongest single fact

The `permutation: True` claim is true, but it is the weaker statement. I ran
the **base** `schedule()` and the **branch** `schedule()` over the *identical
108-module base glob*:

    schedule over the SAME 108 base modules identical: True
    positions differing: 0

Listing the seven previously-absent modules with `sec: null` bought precisely
what omission bought. The branch's own 109-module head is the same eight
`inf` names in name order (the seven plus this row's new module) followed by
`test_track_move.py 94.96`. **Changing the schedule is out of the Bound and
the schedule did not change.** This is the proof line of the review.

### 1d. All five of the round's mutations, re-run by me

Lab = the branch snapshot as a real git repo. `__pycache__` cleared and a
1.2s sleep past the second boundary before every run. Clean control run
before and after every mutation: `Ran 24 tests … OK`.

| # | mutation I applied | result | named test(s) red |
| --- | --- | --- | --- |
| 1 | deleted `modules["test_board_render.py"]` | **RED (2)** | `test_every_module_on_disk_is_listed`, `test_the_live_file_parses_into_the_declared_shape` |
| 2 | renamed key `test_diagnose.py` → `test_diagnose_renamed_away.py` | **RED (3)** | `test_no_recorded_module_has_been_deleted`, + the 2 above |
| 3 | deleted `format_audit(audit(all_mods, load_document()))` from `main()` | **RED (3)** | all of `TestTheBannerIsWiredIntoMainAndNotJustDefined` |
| 4 | `git_ancestor` → `return True` unconditionally | **RED (1)** | `test_the_real_ancestor_check_answers_for_this_checkout` |
| 5 | `drift()` lines lead with the module name again | **RED (1)** | `test_a_drift_line_never_starts_with_the_runners_module_red_marker` |

Every named test the round claimed is the test that actually went red. The
spec required mutations 1 and 2 with a NAMED test each; both are satisfied and
the failure messages name the offending module, not just the file.

### 1e. The `✗` marker collision, including the case the round did not test

The round's own first version printed the runner's module-RED marker for a
module that had merely never been measured, and `test_tree_guard` caught it.
I re-created the harder case the round did not: a module that is **both absent
from `durations.json` and genuinely red**, alongside one that is **absent and
green**. Planted both into the lab and ran `python3 tests/parallel
test_zz_planted` (narrowed run, exit 1):

    ✗ test_zz_planted_red.py                                  ← main(), correct
      ✗ not in durations.json: test_zz_planted_pass.py — …    ← drift, leads with condition
      ✗ not in durations.json: test_zz_planted_red.py — …     ← drift, leads with condition

Substring check on the ANSI-stripped output:

    '✗ test_zz_planted_pass.py' present?  False   ← the passing plant is never accused
    '✗ test_zz_planted_red.py'  present?  True    ← exactly once, from main()'s own line

The marker cannot collide any more, and a module that is both absent and red
gets exactly one module-RED marker rather than two. Fix confirmed.
`tests/test_tree_guard.py` is byte-identical between base and branch, so the
guard that caught the bug was not adjusted to accommodate it.

### 1f. What runs the report with no flag

`tests/run` is **byte-identical** between base and branch; its step 2 is
`python3 tests/parallel`. The banner is printed unconditionally from `main()`,
after the verdict, over `all_mods` (the whole glob) rather than the narrowed
`mods`. Observed on a bare narrowed run with no flag in the lab:

    1 modules · 24 tests · 0.1s · 8 workers

    durations: 109 recorded · 109 on disk · 0 stamped at an ancestor ref
               · 0 stale · 101 unstamped · 8 unmeasured
      ✓ every module on disk is accounted for
    ✓ all green

`tests/test_durations_provenance.py` matches `tests/test_*.py`, so it is
collected by `tests/run`, by `--serial`, and by `tests/parallel`. 24 tests,
green. Drift is the red gate; the banner does not change the exit status of
`tests/parallel` itself, which is the correct split — the runner may not
become an outage over its own stopwatch.

### 1g. I did run the whole suite, and the one red is not this row

`bash tests/run` in the lab at `788538b` (which differs from the round's
`69ca5eb` only in `TASK-304-result.md`), `PERRY_PROJECT` and `PERRY_HOME`
unset, `__pycache__` cleared, second boundary passed:

    START 23:47:37  load 5.93 8.70 12.37
    109 modules · 3027 tests · 340.8s · 8 workers
    END   23:53:21  load 9.45 15.01 14.88   (load peaked at 33.86 mid-run)
    ✗ test_host_support.py — FAILED (failures=1)
    durations: 109 recorded · 109 on disk · 0 stamped at an ancestor ref
               · 0 stale · 101 unstamped · 8 unmeasured
      ✓ every module on disk is accounted for

The **109 modules / 3027 tests** reproduce the round's after-row exactly. The
one red does not, and it is **not this row's**:

- `tests/test_host_support.py` is **byte-identical to base** on this branch
  (`diff` against the `d49964e` extract: identical). The branch touches four
  files and that is not one of them.
- The failing test is
  `TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`
  — 20 concurrent registrations against `PERRY_MAX_DISPATCH_TOTAL=3`,
  asserting exactly 3 succeed. It got **2**. That is a contention artifact of
  its own harness, and the load average was 20–34 through step 2.
- **Re-run alone at load 5.96: 35 tests, 15.7s, exit 0, `✓ all green`.**

So the failure count attributable to this row is **0**, independently
measured, which is the number the round claimed. I am **not** offering 340.8s
against the round's 307.2s or the baseline's 408.7s as a comparison — different
loads, and TASK-230 already established the 2x swing.

### 1h. `git_ancestor`'s three answers, against real git

In the lab repo:

    head_ref()                        -> 8f1c66627a366d69f2d52e78f26f0c508f3146cf
    git_ancestor(HEAD)                -> True
    git_ancestor('0'*40)              -> None      (returncode 128)
    git_ancestor(<real orphan commit>)-> False     (returncode 1)

I built the orphan commit myself; the round never demonstrated the `False`
path against real git. The mechanism is correct: all three answers are real
and `None` is genuinely distinct from `False`. See finding 1 for what is
nonetheless not guarded.

---

## 2. Findings

### Finding 1 (filing, not the verdict) — a green mutation: `git_ancestor` need never answer `False`

The brief asked whether `test_the_real_ancestor_check_answers_for_this_checkout`
is satisfiable by an implementation that always answers the same way for a
different reason. **It is.** That test asserts only two things:

    self.assertIs(P.git_ancestor(head), True)
    self.assertIsNone(P.git_ancestor("0" * 40))

I applied a sixth mutation the round did not:

    -    return {0: True, 1: False}.get(p.returncode)      # 128 → None
    +    return True if p.returncode in (0, 1) else None

That is a `git_ancestor` which **never reports anything stale** — every
resolvable ref comes back `True`, every unresolvable one `None`. It satisfies
both assertions (HEAD resolves → `True`; the bogus hash is 128 → `None`) and:

    Ran 24 tests in 0.059s
    OK

**Green.** Every injected-verdict test in
`TestStalenessIsDistinguishableFromCurrent` passes an `ancestor=lambda`, so
they test the *reporting* of `False`, never the *production* of it. Nothing in
the suite exercises `git_ancestor` against a ref that is genuinely not an
ancestor, and staleness is defect 3 of three.

**Why this is a filing and not a FAIL.** Three reasons, and I want the next
reader to be able to disagree with me on the record:

1. The real implementation is correct — I proved the `False` path myself
   against an orphan commit (§1h). This is a coverage hole, not a broken
   mechanism.
2. The spec's mutation requirement names exactly two mutations, both on
   `durations.json`, and both are properly guarded. Mutation 4 was
   volunteered above the bar; a volunteered mutation being imperfectly
   discriminating does not put the round below the bar.
3. The check is latent regardless: `0 stamped at an ancestor ref` means
   `git_ancestor` is never called on real file data today, and the round says
   so honestly on every run.

The fix is about five lines — create an orphan commit in a temp repo, assert
`git_ancestor(orphan) is False` — and belongs in whichever row next touches
this file. **Filed, not folded into this verdict.**

### Finding 2 (filing) — the advisory halves have no recorded promotion trigger

Provenance and staleness are reported and never red. The reasoning the round
gives is sound and I accept it: every inherited figure is unstamped, so a
check that reddened on `unstamped` would have to ship switched off, and a
guard that ships disabled is not a guard. The spec agrees in as many words —
*"Reporting is enough for all three."*

But **nothing records the condition under which they harden.** I grepped the
branch for it: `promot|harden|becomes red|once .* stamped|cadence` across
`tests/parallel`, `tests/test_durations_provenance.py` and the result page
returns one hit, and it is §6a candidate 1 — which is about *forcing a
re-measure*, not about promoting the advisory to a gate. `drift()`'s docstring
explains why the split exists; it does not say what would end it.

The precedent is directly on point and cuts **for** the round, not against it:
`TASK-284-round1-v4-review.md:260` raised exactly this — *"The advisory has no
recorded promotion trigger"* — and filed it under **"Observations — not the
FAIL"**. That round's FAIL was for a report nothing invoked, which is the
defect this round's `TestTheBannerIsWiredIntoMainAndNotJustDefined` exists to
prevent and which mutation 3 proves it prevents. So this is a filing here too,
and the natural trigger writes itself: *the first `--record` that stamps a
real ref is the run after which `unstamped` stops being free.*

### Finding 3 (filing) — §7a's closing sentence is false, and I can show it

The brief asked me to look for a third error. The two the round caught are
genuinely fixed — the §4a marker fix holds in the harder case the round did
not test (§1e), and `tests/test_tree_guard.py` was not touched to accommodate
it. The third is on the result page rather than in the code.

**The non-monotonicity claim itself is TRUE.** I did not reproduce the round's
five-variant table; I went to the rule instead and demonstrated the property
directly against `bin/perry-diagnose.split_dangling`, with a synthetic id in a
temp tree:

    C:  one prose mention, no check named
        mentions=['rec.md:3'] report_lines=[] doc_reports_on_a_check=False
        dangling=['TASK-999']            ← RED

    D:  C plus ONE extra mention, on a line whose paragraph names a test
        mentions=['rec.md:3','rec.md:5'] report_lines=[5] doc_reports_on_a_check=True
        dangling=[]                      ← GREEN

Adding a mention turned red into green. It is structural, not incidental:
`split_dangling:817` computes `on_the_record = any(is_report …)` — monotone
increasing in mentions — and `live` negates it, so an added report-shaped
mention can only ever *reduce* liveness.

**But it is deliberate, documented, and — the part the round got wrong —
recorded.** `bin/perry-diagnose:636-688` is a 50-line comment whose subject is
exactly this: the fourth mark exists because TASK-113 "could not be closed
without writing a record, and writing the record reopened it." Both halves are
named as load-bearing, the cost is named rather than hidden, and two tests hold
the boundaries.

§7a ends:

> "A value that is right by accident is indistinguishable from one that is
> right on purpose unless something records which — and neither the durations
> file nor this lint's output records which."

**The second half is false.** `bin/perry-diagnose:903` emits
`user_load.dangling_in_reports`, and `split_dangling` returns precisely those
ids as its second element — my D run returns `reported_only=['TASK-999']`.
That list is the record of which ids came back clean by way of the fourth mark
rather than by resolving. It is exactly the distinction the round says nobody
keeps, and the comment at `:685-688` says so in as many words: *"it is visible:
it lands in `dangling_in_reports`."*

So the round's own diagnosis of its accidental green is available from the tool
it was using. This does not touch the deliverable — §7a is flagged as an
observation the round declined to bank, and the committed variant A is green
for the checkable reason the round gives — but a false sentence on an evidence
page is worth correcting, and it removes the case for a `perry-diagnose` row
built on that sentence. **Filing: strike or correct §7a's last clause; do not
open a `perry-diagnose` row on the strength of it.**

---

### Finding 4 (filing) — `tests/parallel:371` points a reader at the wrong file for the wiring guard

New in this round's diff. `format_audit()`'s docstring says:

    TASK-284 was failed at V4 for adding a report nothing invoked … So this is
    called unconditionally from `main()`, and `tests/test_parallel_runner.py`
    asserts that `main()` calls it …

**`tests/test_parallel_runner.py` asserts no such thing.** It is byte-identical
to base on this branch (`git diff d49964e 788538b -- tests/test_parallel_runner.py`
is empty) and contains no occurrence of `format_audit` or `audit` at all. The
guard is real but it lives in
`tests/test_durations_provenance.TestTheBannerIsWiredIntoMainAndNotJustDefined`,
which mutation 3 proves works.

The other two references to that file in `tests/parallel` — `:128` and `:404`
— are pre-existing and true.

This is the same shape as TASK-284 round 1's observation 1 (`bin/perry-lint:4303`
states a false causal claim; behaviour correct, explanation wrong), which was
filed and not the FAIL. Same disposition. But it is worth naming sharply,
because the docstring is precisely what a maintainer reads to find out whether
the wiring is guarded — and it sends them to a file where it is not. One-word
fix; it should land before merge.

### Finding 5 — **merge-blocking**: the new red gate fires the moment this lands on today's `main`

Not a defect in the round, and the round was **not wrong when it checked** —
`main` moved under it. But the PMO must not merge this without one edit, so it
goes above the observations.

The round reports (§7a) that its `durations.json` audits clean against
`coding/task-247-config-predicate` — `phantom: []`, `unlisted: []`. I confirmed
that branch has **108** test modules and does not contain
`tests/test_spec_scannability.py`, so the claim was true when it was made.

Current `main` (`d146c15`) has **109**, the extra one being
`tests/test_spec_scannability.py`, added by `f4ae08f` (TASK-284) — which is not
at `d49964e` and not on `coding/task-247-config-predicate`. Running the
branch's own `audit()` against the module set the merge would produce:

    merged tree would have 110 test modules
    unlisted: ['test_spec_scannability.py']
    phantom : []
    drift line the merged tree would print:
      not in durations.json: test_spec_scannability.py — it is on disk and
      will sort as inf and run first by accident, not by decision
    test_every_module_on_disk_is_listed RED: True

**So the merge produces a red suite.** This is the row's own guard doing
exactly what it was built to do — a live module the file does not mention is
now reported and red instead of silent — which is a point in the round's
favour, not against it. But it is a merge step, and it is one line:

    "test_spec_scannability.py": {"sec": null, "source": "never-measured"}

`sec: null` is the correct entry: nobody has measured that module either, it
keeps sorting as `inf`, and it changes no ordering (§1c's argument applies
unchanged). **Add it during the merge, or the first `bash tests/run` on the
merged tree is red.**

---

## 3. Observations — filings, not the verdict

1. **§7a is about `bin/perry-diagnose`, not about this row, and it does not
   belong in this round's verdict either way.** The round is explicit that it
   declined to bank the accidental green and kept the variant that is green
   for a checkable reason. That is the right call and it is the honest one —
   it *cost* the round an edit it had already measured as unnecessary. See
   finding 3 for what I verified about the rule and what the round got wrong
   about it. **I did not re-run the round's five variants**; I went to the
   rule directly instead — see §4.

2. **`write_record()` prunes unused source blocks.** A source no entry points
   at is deleted on the next `--record`. That is defensible (litter vs.
   history) but it means the file cannot retain the provenance of a figure it
   has replaced. Worth a sentence in whatever row makes `--record` routine.

3. **`sec: null` is load-bearing and undocumented in the schema itself.** The
   file carries `"schema": 1` but nothing machine-readable says what `null`
   means; the meaning lives in the `never-measured` note and in
   `load_document()`'s docstring. Both are good prose. A future reader
   parsing this file from anywhere else will not see them.

4. **The round's §6a candidate rows are prose on the branch, not filed rows.**
   Consistent with the standing practice that filed rows land on `main` via
   the PMO, and the spec only says a fourth defect *is* a new row rather than
   an extension — which the round respected by not extending. Noting it so
   the PMO knows two candidates are sitting in §6a waiting to be filed.

---

## 4. What I did not check

Stated plainly so the next reader knows the edges of this PASS.

- **I did not re-run the BASE suite at `d49964e`.** The round's before-row is
  108 modules / 3003 tests / 0 failures and I did not reproduce it. I ran the
  **after** suite myself (§1g) and got 109 / 3027, which reproduces the
  round's module and test counts exactly and confirms the +1 / +24 are this
  row's module and its 24 tests. So the *delta* is verified and the *baseline*
  is the round's number.
- **I cleared `test_host_support.py` by re-running it alone once**, at load
  5.96. I did not run it repeatedly to characterise the flake rate, and I did
  not check whether it is a known flake elsewhere in the project's records.
  What I did establish is that it is byte-identical to base and outside this
  row's four files.
- **I did not re-run the §7a variant table.** I never executed
  `bin/perry-diagnose` end to end on variants A–E of the round's own result
  page, so the specific claim that *one* edit (the fence) cleared the lint and
  the §3 rewording was not load-bearing is **unverified by me**. I verified
  the underlying rule instead, at the function (finding 3), which is a
  stronger statement about the mechanism and a weaker one about those five
  trees.
- **I did not attempt the actual merge onto `d146c15`.** I compared module
  sets and ran the branch's `audit()` against the set the merge would produce
  (finding 5), which is what determines whether the new gate fires. I did not
  check for textual conflicts in `tests/parallel` or anywhere else, and I did
  not run the merged tree's suite.
- **I did not re-measure any duration**, and neither did the round. The
  harness figure is still 10x low; that is TASK-244's subject and the spec's
  Remainder, and it is correctly not charged here.
- **I did not exercise `--record` for real.** I read `write_record()` and
  confirmed `head_ref()` returns `None` rather than a guess when git cannot
  answer, but I never wrote a stamped file and then aged it, so the full
  round trip stamp → later `stale` verdict is unproven end to end. Finding 1
  is the sharp edge of the same gap.
- **I did not check `--ids`, `--alphabetical`, or `--serial`** beyond reading
  that `tests/run` is unchanged.
- **I did not read all 24 new tests line by line** — I read
  `TestTheFileIsAboutThisTree`, `TestTheHintIsStillOnlyAHint`,
  `TestStalenessIsDistinguishableFromCurrent`, `TestTheReportNamesWhatIsWrong`
  and `TestTheBannerIsWiredIntoMainAndNotJustDefined` in full, which is all
  five classes, but skimmed two bodies inside them.
- **I did not run `tests/test_tree_guard.py`.** §4a reports it green after the
  fix at "24 tests, 54.8s". That file defines **26** `def test_` methods and
  carries at least one conditional `skipTest`, so the 24 may be right and may
  be a transposition of `test_durations_provenance.py`'s 24. I verified the
  *substance* of §4a a different and stronger way — by planting modules and
  checking the marker directly (§1e) — and did not chase the count.

---

## 5. Why PASS

Against the spec's three defects:

1. **Provenance** — an entry carries a `source`; a source carries `ref`,
   `taken`, `workers`, `load1`. The 101 inherited figures are stamped
   `unstamped-pre-304` with a **null ref** and no value altered. Verified.
2. **Drift** — both conditions reported, and **red**, by a named test that
   goes red under both mutations the spec required. Verified by re-running
   them.
3. **Staleness** — `git_ancestor` answers `True` / `False` / `None`, and I
   confirmed all three against real git including the `False` path the round
   never demonstrated. Reported, not red, which the spec permits in terms.

Against the Bound: enumeration is `durations.json` against the glob; the size
is what the spec says it is (I re-counted 103/108/7/2); the Remainder — the
accuracy of any retained figure — was left alone, and left alone *visibly*.
The schedule over the identical base glob is unchanged in every position, so
the round did not alter the schedule while claiming only to document it.
Automatic regeneration was refused, in line with the spec's explicit
instruction. The fourth-defect candidates went to §6a rather than into the
diff.

The round also reported two errors in its own work rather than hiding them,
and declined an accidental green it had already measured. That is the
behaviour this project keeps asking for.

**Five findings, none of them the verdict, one of them blocking the merge:**

| # | finding | disposition |
| --- | --- | --- |
| 1 | a `git_ancestor` that never answers `False` passes all 24 tests | filing — real implementation verified correct |
| 2 | no recorded promotion trigger for the advisory halves | filing — TASK-284 r1 precedent files this, and the spec permits advisory |
| 3 | §7a's closing sentence is false; `dangling_in_reports` does record which | filing — correct the page, do not open a `perry-diagnose` row on it |
| 4 | `tests/parallel:371` names the wrong file for the wiring guard | filing — one-word fix, should land before merge |
| 5 | `test_spec_scannability.py` is unlisted on today's `main` | **blocking the merge** — add one `sec: null` entry |

Finding 5 is the guard working. It is still one line the PMO has to write
before the merged tree is green.

=== VERDICT ===
task: TASK-304
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-304-spec.md
checked: re-derived the reproduction at d49964e through the runner's own load_durations()/schedule() (103 recorded vs 108 on disk, phantoms test_migrate.py 97.25 + test_conformance.py, 7 unlisted sorting inf, serial total 1968.9s, load 12.29) and confirmed the round's narrower claim is the true one while the spec's "head of the schedule" framing is not; diffed old flat map against new modules map — 0 of 103 values altered, only the 2 phantoms dropped, 8 added with sec:null, and both source blocks carry ref:null so nothing was backdated; ran base schedule() against branch schedule() over the IDENTICAL 108-module base glob — 0 positions differ; re-ran all 5 of the round's mutations in a standalone git-init lab at 788538b with __pycache__ cleared and a 1.2s second boundary passed, all 5 RED on exactly the named tests with a 24-test clean control OK before and after each, plus a 6th of my own that comes back GREEN (git_ancestor mapping returncode 1 to True never reports anything stale); planted a module that is both absent from durations.json and genuinely red and confirmed "✗ <mod>" appears once from main() and never from a drift line while the passing plant is named but never accused; confirmed tests/run is byte-identical to base and its step 2 is python3 tests/parallel so the banner needs no flag; confirmed git_ancestor returns True/None/False against real git including a False from an orphan commit I built; ran bash tests/run myself at 788538b — 109 modules / 3027 tests / 340.8s / 8 workers, load 5.93→9.45 peaking at 33.86, one red (test_host_support.py) which is byte-identical to base, outside this row's four files, and green alone at load 5.96 (35 tests, 15.7s, exit 0); demonstrated split_dangling's non-monotonicity directly (dangling ['TASK-999'] → [] on adding one check-naming mention) and that bin/perry-diagnose:903 emits dangling_in_reports; audited the branch's durations.json against the post-merge module set — unlisted ['test_spec_scannability.py'], so the new gate goes red on merge.
not-checked: did not re-run the BASE suite at d49964e, so the 108 modules / 3003 tests / 0 failures before-row is the round's number and not mine (I reproduced only the after-row, 109/3027); cleared test_host_support.py with a single re-run and did not characterise its flake rate or look for prior records of it; did not execute bin/perry-diagnose end to end on §7a's five variants A-E, so the claim that fencing alone cleared the lint and the §3 rewording was not load-bearing is unverified by me — I verified the underlying rule at the function instead; did not run tests/test_tree_guard.py, whose "24 tests" the round reports against 26 defined methods and at least one conditional skip; did not attempt the actual merge onto d146c15 — I compared module sets and audited against the merged set, but checked no textual conflicts and ran no merged suite; did not exercise --record for real, so the stamp-then-go-stale round trip is unproven end to end; did not check --ids, --alphabetical or --serial; did not re-measure any duration.
proof: tests/parallel:400 schedule() run over the identical 108-module base glob, once with d49964e's load_durations() and once with 788538b's, returns lists identical in every position (0 differing), while tests/durations.json's two source blocks both carry "ref": null and 0 of 103 inherited values changed — the schedule was documented rather than altered, and no provenance was fabricated, which is the whole of the Bound and the whole of this row's subject.
=== END VERDICT ===
