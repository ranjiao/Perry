# TASK-439 — round 1, V4 review

Fresh-context review against `perry/evidence/2026-09/TASK-439-spec.md`.
I did not write this code and I am not here to agree with it.

> Reviewer base: `52a57adf` · row's work merged at `c7618a96` (ancestor of HEAD,
> verified) · suite `bash tests/run` — **3757 tests, 3 failed, all pre-existing
> and named in § 7** · tree guard clean on every run.

**Verdict: FAIL**, on one finding: the refusal message states a falsehood about
the tool's own behaviour, and that falsehood is the load-bearing support for the
spec's `§ What it must not do` item 1. Most of this row is right, and § 3 says
which parts I could not break.

## 0 · Base check, first

`git log --oneline -1` reported **`583f024f`** and
`git merge-base --is-ancestor 52a57adf HEAD` **failed**. The worktree was **125
commits behind** main's tip — the **sixth** agent in a row handed a stale tree,
and worse than the round under review, which was handed 116.

It was a strict ancestor (`git merge-base --is-ancestor HEAD 52a57adf`
succeeded), 0 commits ahead, `git status --porcelain` empty. So the documented
recovery applied: `git merge --ff-only 52a57adf`, **on my own branch only**,
touching no other checkout. Re-verified: `52a57adf` is now an ancestor of HEAD,
`c7618a96` likewise, tree clean. **Every measurement below was taken after the
fast-forward.** Before it, this worktree did not contain the code I was sent to
review.

## 1 · The eight states, measured — I drove all eleven

Driven through `bin/perry-task` as a subprocess on throwaway projects built from
`tests/test_add_writes_the_edge § Fixture`, never against this repo's store. The
result's before/after table is a claim; this is the measurement, and **the
after-column reproduces exactly**.

| # | invocation | register | exit | rows | events | `add` event | new linkage |
|---|---|---|---|---|---|---|---|
| 1 | `--kr <ID>` | yes | 0 | 1→2 | +1 | `kr='P003-O1-KR1'` | `(edge, add)` |
| 2 | `--unlinked` | yes | 0 | 1→2 | +1 | `kr=None` | `(unlinked, add)` |
| 3 | **neither** | yes | **1** | 1→1 | **+0** | none | none |
| 4 | `--kr ""` | yes | 1 | 1→1 | +0 | none | none |
| 5 | `--kr <ID> --unlinked` | yes | 1 | 1→1 | +0 | none | none |
| 6 | `--kr <ID>` | **no** | 0 | 1→2 | +1 | `kr='P003-O1-KR1'` | none (event only) |
| 7 | `--unlinked` | **no** | 1 | 1→1 | +0 | none | none |
| 8 | **neither** | **no** | **0** | 1→2 | +1 | `kr=None` | none — **warned** |
| 9 | `--kr ""` | **no** | 1 | 1→1 | +0 | none | none |
| 10 | `--kr <ID> --unlinked` | **no** | 1 | 1→1 | +0 | none | none |
| 11 | `--kr "   "` | yes | 1 | 1→1 | +0 | none | none |

State 3 writes **nothing** — no row, no event, no id. `TestNothingWasWritten`'s
claim that the refusal precedes `mint_id` holds under measurement, not just
under its own assertion.

States 9 and 10 are the two the round's table omits, and both behave correctly:
the blank and contradiction refusals are **not** gated on the register, which is
right — neither of them needs a register to be wrong.

## 2 · Findings

### FAIL-1 — the refusal tells the caller something false about the tool, and it is the sentence the whole must-not #1 argument rests on

`bin/perry-task:3711-3713` prints, to any caller who omits both flags:

> `--unlinked` … writes a record that CANNOT BE WITHDRAWN by any `perry-task`
> command **and that `perry-lint` reports for as long as it stands**

**The clause after "and" is false.** `bin/perry-lint § linkage-unlinked-exists`
(`bin/perry-lint:1518-1520`) reads:

```
for tid in (link.unlinked or []):
    if store_ids is None or not tid or tid in store_ids:
        continue
```

It files a `warn` **only when the declared id is NOT a record in
`tasks.jsonl`** — a dangling declaration: a typo, or a purged row. A healthy
`--unlinked` row is `tid in store_ids`, hits the `continue`, and is reported by
nothing.

**Measured, not read.** I built two identical fixtures, added one row to each —
one with `--unlinked`, one with `--kr <ID>` — and ran `perry-lint` on both:

| row added with | lint lines mentioning "unlinked" | lint exit before → after |
|---|---|---|
| `--unlinked` | **0** | 1 → 1 |
| `--kr <ID>` | 0 | 1 → 1 |

The `--unlinked` row and the `--kr` row are **indistinguishable to `perry-lint`**.
There is no standing warning. There is no `unlinked_without_event` either (the
result says so itself in § 7).

**Why this fails the row rather than being a prose defect.** `§ What it must not
do` item 1 requires the report to say why the refusal does not make `--unlinked`
the easy default. The result's § 2.3 gives five reasons and concedes in its own
"honest caveat" that items 1 and 2 are *neutral* — they do not push toward
`--kr`. Item 3 covers store-less projects only. That leaves **item 4 as the only
standing friction on the lossy side**, and item 4 is this false claim:

> 4. **It stays visible.** `bin/perry-lint § linkage-unlinked-exists` files every
>    standing declaration at `warn`. A row that takes `--unlinked` acquires a
>    permanent record **and** a standing lint warning.

Remove the falsehood and the defence is: two neutral items, one narrow item, and
a warning sentence that is itself half untrue. The criterion's required argument
is not established. The round's own empirical sample — 4 of 5 call sites chose
`--unlinked` (§ 7 of the result) — points the same way.

**Category enumerated, not the next instance** (review.md § 2 rule 1). Four
sites, and the row **introduced** the third:

| site | kind |
|---|---|
| `bin/perry-task:3712` | **product output** — the refusal a user reads |
| `bin/perry-task:3694`, `:3697` | code comment asserting it |
| `work/reference/subcommands.md:591` | **lane page an agent reads in order to open a row** — `git show 85e34b20` shows this row added the line *"`perry-lint` reports every standing declaration"* |
| `TASK-439-result.md:61`, `:125-127` | the report |

Only the first is a V4 FAIL; per review.md § 2 the comment and the result are
rows. But `subcommands.md:591` is a scripted instruction page this row made
false, which is the defect class the spec itself predicted this row would create
(`§ Files in scope`, third bullet) — found, and created rather than fixed.

**What would change my mind:** any `perry-lint` invocation — any flag
combination, `--json`, `--strict`, a different section — that names a *live*
`via: "add"` unlinked declaration. I ran the default invocation on a fixture and
grepped `bin/perry-lint` for `unlinked` and `declar`; I found one check and it is
the dangling one. Show me a second reader and FAIL-1 collapses to a wording nit.

### ROW-2 — the refusal fires on tracks `P003-O3-KR2` never counts, and no test pins the scope

`bin/perry-task:3699-3701` gates the refusal on the register existing and on
nothing else. It does **not** gate on track, and it fires before
`track = track_of(...)` at `:3725`. But the metric it serves is track-filtered:
`bin/lib/__init__.py:1293` is `same_action_linkage(..., *, track: str = "main")`
and `:1419` skips every event whose track is not `main`.

Measured on the `intake` track of a project that has a register:

| invocation | exit | new linkage record | KR population / num / denom |
|---|---|---|---|
| `--track intake`, neither flag | **1 — refused** | none | `[]` / 0 / 0 |
| `--track intake --unlinked` | 0 | `(unlinked, add, TASK-101)` | `[]` / 0 / 0 |

The KR reads **0/0 either way**. So on a non-main track the refusal buys the
metric nothing, and the cheapest way past it writes a permanent, un-withdrawable
record for a row the metric never had. That is must-not #1's hazard in its
purest form — *"buys a worse number than the one it fixes"* — except here it
buys no number at all. It also falsifies the round's defence item 2 (*"the KR
counts `--kr` and `--unlinked` identically as answered"*) on this track: it
counts **neither**, so there is no scoreboard reason to spend the minute.

**`MUT-B` came back GREEN** (§ 4): narrowing the refusal to `main` only changed
nothing any test could see. The scope is unpinned in both directions.

**Grade: ROW.** `§ Deliverable` item 1 is unqualified by track, so refusing on
every track is literally what the spec asked for. The defect is a scope choice
shipped without argument and without a test, in a row whose spec explicitly
demanded the *other* boundary (`§ What it must not do` item 4) be argued rather
than defaulted. It needs its own row and its own decision, not a third round here.

**What would change my mind:** a rule I did not find that puts non-main-track
rows in some KR's population, which would make the refusal load-bearing there.

### ROW-3 — the `route` gap the result reports is not reachable as described

Result § 9 finding 1 claims `route` *"opens a main-track row"* that the gate
cannot see, and calls it *"the remaining way to open one"*. **Measured, it is
not.** `cmd_route` (`bin/perry-task:6283-6284`) refuses first:

```
route --track main    → exit 1: "track 'main' is mode `project`; routing is a
                                 queue-mode operation (`modes/queue.md`)"
route --track intake  → exit 0: event="route" track="intake" — no `kr` key
```

`main` is mode `project` in every standard config, and mode `project` is exactly
what `route` refuses. So routed rows are not in `P003-O3-KR2`'s population and
cannot be — not because the event lacks a `kr` key, but because they cannot be
on the `main` track at all.

**Leaving `route` alone was right**, and more clearly right than the round
argued: it is not a hole in the gate, it is a different door into a different
room. The Remainder judgement itself is correct and I re-derived it — `cmd_add`
has no in-file caller and `bin/perry-task:3891` is the only site emitting an
`add` event, so neither `intake` nor `route` reaches `cmd_add`.

**Grade: ROW** — review.md § 0 is explicit that a false statement in an evidence
file is a correction to file, never a FAIL. Filing it matters because as written
it would send a future row chasing a defect that is not there.

### ROW-4 — the vacuity seam is documented in the caller, not in the shared helper

The round's disclosed defect is real and its fix is real: `TestTheBlankRefusalIsReconciled.blank()`
now routes `--kr ""` through `*extra`, and `MUT-A` proves those tests can fail
(§ 4). But `M.Fixture.add` at `tests/test_add_writes_the_edge.py:246` **still
silently drops a falsy `kr`**:

```
if kr:
    argv += ["--kr", kr]
```

with no comment. The result § 6 says *"the seam is documented in the helper so
the next reader does not re-make it"* — it is documented in the **caller's**
docstring (`tests/test_add_refuses_without_an_answer.py:255-264`), in a different
file. A third module importing `M.Fixture` gets no warning at the point of use.

I swept for siblings with the same shape and found **none**: the only other blank
probes are `tests/test_same_action_linkage.py:1000-1009`, which pass `--kr ""`
and `--kr "   "` through a `*extra` signature (`_add`, `:964`) that filters
nothing. So the disclosed defect has exactly one instance and it is fixed.
**Grade: ROW**, test hygiene — review.md § 0 keeps untidy tests off this rung.

## 3 · What I tried to break and could not

Reported because a round that only lists defects makes round 2 re-cover this
ground.

- **The blank-`--kr` keep is right, and the two messages are distinguishable.**
  I judged the collapse question independently and reach the round's answer.
  A caller who typed `--kr "$KR"` with `KR` unset gets *"`--kr '' is blank …
  check the variable you expanded, because `--kr "$KR"` with `KR` unset arrives
  here looking exactly like this"* — which names the actual cause. The collapsed
  alternative would say *"neither was passed"* to someone who believes they
  passed `--kr`, and the plausible next move is `--unlinked`, which is
  irreversible. The reasoning holds and `MUT-A` shows it is pinned in **three**
  modules, not one.
- **The no-register argument is sound and I agree with it.** I pressed the
  opposite case and could not make it work: on a fresh project `--unlinked` is
  refused by `linkage_add_change` (state 7, measured) and `--kr` can only name a
  KR that does not exist, so an unconditional refusal leaves a **guessed `--kr`**
  as the only way to file any row — the exact guess `reference/okr-linkage.md`
  forbids. There is no third answer for the caller to pass, which is what an
  unconditional refusal would require me to name, and I cannot name one. The
  gate fires where the question is answerable. `MUT-D` reddens six tests across
  three modules.
- **The anti-vacuity is genuine.** `MUT-E` replaces the refusal with an
  unrelated one: `test_neither_flag_is_refused` stays green (it only checks a
  non-zero exit) while `test_the_refusal_is_about_the_kr_question` and
  `test_the_refusal_names_which_one_means_serves_no_kr` go red. The subject-matter
  assertions are doing real work.
- **The discriminating-test claim is accurate.** My first parallel run
  under-reported it, so I re-ran `MUT-F` against the named class directly:
  `test_omission_is_not_a_declaration` fails with
  `Lists differ: ['TASK-101'] != []` and `test_omission_does_not_enter_the_population`
  with `1 != 0`. M1/M2 really are distinguished.
- **The caller sweep holds.** See § 5.

## 4 · Mutation table — six planted, every restore verified

Baseline `sha256(bin/perry-task)` = `031ff1747e6f56451fb9fad87d2e0eb8ec33d37878970255668b7546cba3a56d`.
Every mutation was line-anchored (never `str.replace`), `__pycache__` cleared and
a 1.2 s wait past the second boundary on both the mutate and the restore, and
each restore verified **twice**: sha256 against baseline **and**
`bin/perry-restore-check HEAD bin/perry-task`, which compares against
`git show HEAD:bin/perry-task` — an independent source, not my own snapshot.

| # | mutation | result | named test(s) that reddened | restore |
|---|---|---|---|---|
| **MUT-A** | delete the blank-`--kr` refusal block entirely (**the collapse**) | **red** | `TestTheBlankRefusalIsReconciled.test_blank_kr_is_still_refused`, `…test_it_names_the_empty_variable_hazard`; `ABlankKrIsRefusedBeforeItReachesTheEvent.test_an_empty_kr_is_refused_the_same_way`, `…test_nothing_was_written`; `TestTheContradictionIsRefused.test_a_blank_kr_alone_is_still_refused_for_its_own_reason` | sha match ✓ · restore-check exit 0 ✓ |
| **MUT-B** | narrow the refusal to `track == "main"` only | **🟢 GREEN** | **none — finding, § 2 ROW-2** | sha match ✓ · restore-check exit 0 ✓ |
| **MUT-C** | delete the false *"`perry-lint` reports it"* clause from the message | **🟢 GREEN** | **none — corroborates FAIL-1: the false sentence is unpinned** | sha match ✓ · restore-check exit 0 ✓ |
| **MUT-D** | drop the no-register guard | **red** | `TestAStoreLessProjectStillFiles.test_add_still_works_with_no_register`, `…test_the_warning_does_not_advise_a_command_that_refuses`; `TestWithoutAKr.test_the_row_is_created_and_not_refused`, `…test_the_row_reports_never_asked_and_not_declared_unlinked`; `TestAStoreLessProjectRefusesTheDeclaration.test_the_control_the_same_fixture_can_file_a_row`; `TestSilenceIsStillNeverAsked.test_with_no_register_silence_still_files_and_warns` | sha match ✓ · restore-check exit 0 ✓ |
| **MUT-E** | refuse, but for an unrelated reason (**anti-vacuity**) | **red** | `TestTheRefusalIsNotVacuous.test_the_refusal_is_about_the_kr_question`, `…test_the_refusal_names_which_one_means_serves_no_kr`; `ABlankKrIsRefusedBeforeItReachesTheEvent.test_omitting_the_flag_is_refused` | sha match ✓ · restore-check exit 0 ✓ |
| **MUT-F** | omission silently becomes an `--unlinked` declaration (**the cheap wrong fix**) | **red** | `TestTheRefusalDoesNotSilentlyDeclare.test_omission_is_not_a_declaration`, `…test_omission_does_not_enter_the_population` (focused run); `TestSilenceIsStillNeverAsked.test_a_row_with_neither_flag_is_refused`, `…test_silence_writes_no_linkage_record_at_all`; + MUT-E's set | sha match ✓ · restore-check exit 0 ✓ |

**Two mutations came back green**, and per review.md § 2 a green mutation is a
finding either way. MUT-C is the weaker of the two — it corroborates FAIL-1
rather than standing alone, since no test *should* be asserting a false
sentence. **MUT-B is the real one**: an entire scope dimension of a new gate is
unmeasured.

`bin/perry-task` is byte-identical to `HEAD` as I write this, verified a seventh
time after the last restore. **No file I mutated was left changed.** I planted
mutations in `bin/perry-task` only.

## 5 · The caller sweep, re-derived

**Enumeration** (the Bound's directories): `grep -rn "perry-task add" bin work
goals decide modes packs templates tests` → **76 textual occurrences** on
`52a57adf` (bin 23, work 12, goals 3, modes 1, tests 46, and **zero** in
`decide/`, `packs/`, `templates/`). The round derived 68 on `f3df6219` with a
narrower pattern; the difference is pattern and base, not a missed site, and the
Bound deliberately declines to fix a number.

**No caller was missed, and the suite is the proof for `tests/`.** A test caller
that would now refuse reddens. `bash tests/run` on the merged tree returns
**exactly the three pre-existing reds** and nothing else (§ 7). For the
non-`tests/` half I read every one of the 39 sites individually:

- **`bin/README.md:417`** — the `Usage:` block, rewritten. Verified on disk.
- **`work/reference/subcommands.md:591`** — the lane page, rewritten from *"omit
  `--kr`"* to `--unlinked`. Verified. **This is also FAIL-1's third site**: the
  rewrite is correct about the flag and false about the lint consequence.
- **`work/reference/subcommands.md:34, 578, 589, 604, 714`**, `bin/perry-lint`
  (5), `bin/perry-goals:1809`, `bin/perry-tasks:1435`, `bin/README.md:594`,
  `bin/perry-task:2656, 3914, 5188`, `goals/SKILL.md:152`,
  `goals/reference/linkage.md:8`, `goals/reference/phases.md:216`,
  `modes/queue.md:348` — prose, or a call that already passes `--kr`. Correct as
  written; I checked `:589` in particular, which already says *"pass the same id
  to `perry-task add --kr <KR-ID>`"*.
- **`bin/lib/__init__.py` (5)** — out of scope by instruction.
- **The Remainder, checked rather than assumed.** `cmd_add` has **no in-file
  caller** (`grep -n "cmd_add("` returns only the definition at `:3483`), and
  `:3891` is the **only** site emitting `"event": "add"`. `cmd_intake` and
  `cmd_route` reach neither. **They are OUT**, and § 2 ROW-3 corrects what the
  result says about why.
- **`perry/**`** — outside the Bound by design, and right: rewriting a journal
  to match current behaviour falsifies the record.

## 6 · The exposure question, checked

`§ 7` of the result owes a number, not a fix, and it delivers one. I did not
re-derive the 1×–23.9× bracket — see § 8 — but I did check the claim it rests
on: `bin/lib/__init__.py:1438` reads `unlinked_at_add` only inside the event
loop (`elif tid in unlinked_at_add:` at `:1436-1437` on this base), while
`store_edge_without_event` is computed outside it over `edge_at_add.items()`.
The asymmetry is real and there is no `unlinked_without_event`. `bin/lib/__init__.py`
is out of scope and I did not touch it.

**ROW-2 enlarges this exposure further than the result accounts for**: every
non-main-track row that now takes `--unlinked` to get past a refusal that buys
its metric nothing is another record through the blind-spot writer.

## 7 · The suite

`bash tests/run` on the merged tree: **3757 tests, 3 failed, 2 of 129 modules
red.** All three are the pre-existing reds I was told to expect, named rather
than counted, and **nothing is attributed to them**:

1. `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable` — `[conformance.in_progress_with_no_live_run[].means]`
2. `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` — same key
3. `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

**Tree guard: `✓ nothing moved`** on every run. I wrote nothing into the
repository while the suite was running — the mutation rounds were run strictly
after the clean-tree baseline completed, one at a time, each with its restore
verified before the next began.

The result reports 3723 tests against 3757 here; the base differs (`f3df6219`
vs `52a57adf`) and the three named reds are identical. Not a defect.

## 8 · What I did not check

- **Any `perry-lint` invocation other than the default** on a fixture — no
  `--strict`, `--json`, `--reviews`, `--specs`. FAIL-1 rests on the default run
  plus a source read of the only two matching checks; a second reader I missed
  would collapse it.
- **The 1×–23.9× exposure bracket** in result § 7, and the repo-level numbers
  (19/59, 362 add events, 94.8%). I checked the mechanism, not the arithmetic.
- **`bin/lib/__init__.py`** beyond reading `same_action_linkage` — out of scope
  by instruction, not mutated.
- **`tests/durations.json`**, `tests/test_handed_back_root.py`'s 66→64 constant,
  and the `SURFACE` 3000-character cap. I confirmed the suite is green on all
  three; I did not re-derive the numbers.
- **Windows paths, non-UTF-8 roots, concurrent `add`.**
- **`perry-goals link` / `link --unlinked`** — out of scope by the spec.
- **Whether a project can declare a track literally named `main` in `queue`
  mode**, which is the only configuration in which ROW-3's `route` gap could
  become reachable. I did not construct one.

## 9 · What a PASS needs

FAIL-1 is one clause in one sentence, plus its three echoes. The fix is to make
the message true — either delete the `perry-lint` clause, or add the check that
makes it true and say which. Both are small; they are **not the same decision**,
and the second is a `bin/perry-lint` change this row's scope does not carry.
`work/reference/subcommands.md:591` must move with it. Then ROW-2 and ROW-3 go
out as rows, not as a second round here.

```
=== VERDICT ===
task: TASK-439
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-439-spec.md
checked: 11 states driven on throwaway projects (the spec's 3 + register/no-register
         crosses + `--kr "   "`), each exit code, row count, event `kr` key and
         linkage record measured; 6 mutations planted, all restores verified by
         sha256 and `perry-restore-check` against `git show HEAD:`; caller set
         re-derived at 76 occurrences over the Bound's 8 directories, `cmd_add`
         shown to have no in-file caller and `:3891` the only `add`-event site;
         `perry-lint` run on matched `--unlinked` and `--kr` fixtures; suite
         3757 tests, 3 pre-existing reds, tree guard clean
not-checked: non-default `perry-lint` invocations; result § 7's 1x-23.9x bracket
         and repo-level counts; `bin/lib/__init__.py` beyond reading
         `same_action_linkage`; durations.json and the 66->64 constant; Windows
         paths; concurrent `add`; a `queue`-mode track named `main`
proof: bin/perry-task:3712 tells the caller `--unlinked` writes a record "that
         `perry-lint` reports for as long as it stands". bin/perry-lint:1518-1520
         files `linkage-unlinked-exists` only when the declared id is NOT in
         `tasks.jsonl` (`if ... or tid in store_ids: continue`), so a healthy
         declaration is reported by nothing — measured: an `--unlinked` row and a
         `--kr` row produce identical `perry-lint` output, 0 lines naming either.
         MUT-C deleting the clause is GREEN. The claim is `§ What it must not
         do` item 1's only non-neutral support (result § 2.3 item 4), and this
         row propagated it into work/reference/subcommands.md:591, the page an
         agent reads in order to open a row.
=== END VERDICT ===
```
