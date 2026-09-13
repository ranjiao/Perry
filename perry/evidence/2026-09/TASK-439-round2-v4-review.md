# TASK-439 — round 2, V4 review

Fresh-context review against `perry/evidence/2026-09/TASK-439-spec.md`. I did
not write this code, I am not round 1, and I am not bound by round 1's
conclusions — including its PASSes.

> Reviewer base after the recovery in § 0: `fc6df1d6` · the row's original work
> at `85e34b20` / `c7618a96`, both ancestors of HEAD, verified · suite
> `python3 tests/parallel` — **130 modules, 3776 tests, 3 failed, all
> pre-existing and named in § 6** · every destructive probe on a
> `git archive` copy in the scratch directory; the repository under review was
> never written.

**Verdict: FAIL**, on two findings. The first is round 1's FAIL-1 in a second
shape: the corrected sentence names a reader that exists, and that reader is
**phase-scoped**, so the promise *"for as long as it stands"* is still false and
27 standing declarations on this project are already invisible to it. The
second is independent of round 1 and of round 2: on a project state
`goals/reference/phases.md` itself prescribes, the gate refuses **both** honest
answers and accepts only a fabricated `--kr`, silently. § 3 says what I could
not break, and most of this row is still right.

## 0 · Base check — a measured result, recorded here because it is evidence for a different row

`work/reference/dispatch.md § the brief carries three things` shipped two days
ago as the mitigation for a recurring stale worktree base. This round is an
independent test of it, so what the brief gave me and what I did are written
down rather than only reported.

**What the brief carried:** the base I must contain, `fc6df1d6`; `main`'s tip at
dispatch time, `fc6df1d60eabefe4d77d5a1b98a397a77eef1c3d`; and what to do when
they differ.

**What I asserted, before reading anything else:**

| check | result |
|---|---|
| `git log --oneline -1` | **`583f024f`** — "Merge bin-contract-phase-a…" |
| `git merge-base --is-ancestor fc6df1d6 HEAD` | **failed** — the base was not in my tree |
| `git merge-base --is-ancestor HEAD fc6df1d6` | succeeded — strict ancestor |
| `git rev-list --count 583f024f..fc6df1d6` | **128 commits behind** |
| `git rev-list --count fc6df1d6..583f024f` | **0 ahead** |
| `git status --porcelain` | empty |
| `git merge-base --is-ancestor fc6df1d6 main` | succeeded |

`583f024f` contained **neither `85e34b20` nor `c7618a96`** — not merely an old
tree, a tree with **none of the code this round exists to review**. That is the
same class as the two 2026-09-12 cases the bullet records, and the same stale
base.

**What I did:** `git merge --ff-only fc6df1d6`, **on my own branch
`worktree-agent-ac76f4d098e828e3e` only**. No other branch and no other
checkout was touched, and `main` was not moved. Re-asserted afterwards:
`fc6df1d6` is an ancestor of HEAD, `85e34b20` and `c7618a96` likewise, tree
clean. **Every measurement in this document was taken after the
fast-forward.**

The protocol cost one command and produced the right tree. Recorded as the
bullet asks: I checked, and it was **not** fine.

## 1 · What round 2 claims, re-measured — the numbers reproduce exactly

On a `git archive fc6df1d6` copy of this project, one row added, nothing else
run:

| row added with | `declared_unlinked` | `linked` | `perry-lint` lines saying "unlinked" |
|---|---|---|---|
| — (before) | 116 | 2 | 0 |
| `--unlinked` | **117** (contains the new id) | 2 | 0 |
| `--kr P003-O3-KR2` | 116 | **3** | 0 |

Round 2's § 1 table is accurate, its `143` is accurate (the store holds 143
`kind: unlinked` records), and round 1's underlying charge is accurate: the two
flags are indistinguishable to `perry-lint`. **The reader round 2 substituted
does exist and does discriminate.** What it does not do is what the sentence
promises. That is § 2 FAIL-1.

The other clause of the same sentence I checked from scratch, because no round
has: *"a record that CANNOT BE WITHDRAWN by any `perry-task` command"`*. Driven
through the whole terminal path — `add --unlinked`, then `done`, then `purge`,
which describes itself as *"DELETE a terminal record from the store"* — the
declaration survives all three. `purge` removes the row from `tasks.jsonl` and
leaves the `unlinked` record standing; `declared_unlinked` still reports it;
and `perry-lint § linkage-unlinked-exists` *then* warns, because the id is no
longer a record. **That clause is true, and it is true in the strongest way:
the only `perry-task` command that deletes cannot reach it.**

## 2 · Findings

### FAIL-1 — the corrected reader is phase-scoped, so "for as long as it stands" is false a second time

`bin/perry-task:3726-3731` now prints, to any caller who omits both flags:

> `--unlinked` … writes a record that CANNOT BE WITHDRAWN by any `perry-task`
> command **and that `perry-state --section attribution` counts under
> `declared_unlinked` for as long as it stands**

`attribution.declared_unlinked` is `link.unlinked` (`bin/perry-state:2158`), and
`link` is **not the store**. It is `P.load_linkage(root, phase)`, which passes
the records through `viewer/parsers.linkage_records_for_phase`
(`viewer/parsers.py:4137-4139`):

```
if kind == "unlinked":
    at = str(r.get("phase") or "")
    return not at or at.startswith(prefix)
```

`prefix` is the **current** phase's `<NNN>-`. `perry-task add --unlinked` writes
`phase` on every record it creates (`bin/perry-task:2788`), so every declaration
this row's remedy produces is scoped to the phase it was made under and leaves
`declared_unlinked` at the next `plan-phase`.

**Measured two ways.**

*On this project, today.* 143 standing declarations in the store;
`perry-state --section attribution` reports 116.

| phase the declaration was made under | records | reported by the named reader |
|---|---|---|
| `003-storage-code` (current) | 116 | 116 |
| `002-fields-are-typed` | 4 | **0** |
| `001-work-modes-live` | 23 | **0** |

**27 standing declarations are already invisible to the reader the refusal
names.** They are not withdrawn, not stale and not dangling — every one names a
live row. They are simply in a past phase.

*On a fixture, driven forward through a phase boundary.* `add --unlinked` writes
`{"kind": "unlinked", "task": "<TASK-ID>", "phase": "003-storage", …,
"via": "add"}`. While 003 is current, `declared_unlinked` reports the id. Then
the two steps `goals/reference/phases.md § plan-phase` prescribes — update
`phase/CURRENT`, append the new phase's `objective` and `kr` records — with the
old records untouched, exactly as `§ score-phase` step 6 requires
(*"the scored phase's records stay in `linkage.jsonl` and are never
rewritten"*):

```
declared_unlinked while 003 is current : ['<TASK-ID>']
declared_unlinked once 004 is current  : []
the store record on disk               : 1, unchanged
```

**Why this fails the row rather than being a wording nit — the same argument
round 1 made, one layer down.** `§ What it must not do` item 1 requires the
report to establish that the refusal does not make `--unlinked` the easy
default. The result's own five reasons concede items 1 and 2 are *neutral* and
item 3 covers store-less projects only, so **standing visibility is still the
only non-neutral friction in the whole argument** — and a friction that expires
at the next `plan-phase` is not the friction claimed. The code comment escalates
it further, to *"a permanent line in the standup's attribution count"*
(`bin/perry-task:3696-3697`) and *"straight from the store, permanently"*
(`bin/perry-task:3708`). Neither word survives the phase filter.

**Which of `review.md § 0`'s three questions this answers yes to.** The second:
*make a tool report a wrong answer to someone with no way to tell.* The refusal
is product output, it is the surface at which the caller decides between a
reversible answer and an irreversible one, and it states a falsehood about the
tool's own behaviour that the caller has no way to check. Arguably also the
third — the claim is the load-bearing support for the gate's own must-not — but
the second is sufficient and is the one I charge.

**The enumeration, and one correction to a lead I was given.** Round 1
enumerated four sites for the tool-name error. Round 2 closed three of them and
re-opened two in this second shape:

| site | kind | state |
|---|---|---|
| `bin/perry-task:3729` | **product output** — the refusal a caller reads | **false again** (scope) |
| `bin/perry-task:3694-3697` | the comment carrying the must-not #1 argument | **false again** ("permanent line") |
| `bin/perry-task:3708-3710` | the new paragraph recording the correction | **false again** ("straight from the store, permanently") |
| `work/reference/subcommands.md:591` | **lane page an agent reads in order to open a row** | **false again** ("for as long as it stands") |
| `perry/evidence/2026-09/TASK-439-result.md:61, 125-127` | the original report | **old clause still standing, unmarked** — ROW-4 |
| `perry/BOARD.md:96`, `perry/journal/2026-09/2026-09-13.md:10-11` | the record | carries "straight from the store, permanently" — ROW-4 |

**`bin/perry-lint:1507-1509` is NOT a site, and the lead that it might be is
wrong.** Its comment — *"`perry-state § attribution` reports `declared_unlinked`
straight from this list (TASK-228)"* — is locally accurate: `perry-lint` loops
over **every phase in the store** (`bin/perry-lint:1382-1386`,
`for slug in store_phases: link = P.load_linkage(root, own)`), so "this list"
is that iteration's per-phase slice, and the very next paragraph says so
outright: *"**Each declaration is swept ONCE, under its own phase** … a
phase-001 declaration is reported against phase 001."* Round 2 lifted the words
*"straight from this list"* out and left behind the sentence immediately after
them that supplies the phase qualifier. The comment is right; the reading of it
was not.

That comparison is also the cleanest statement of the defect: **`perry-lint`
iterates every phase but reports only dangling ids; `perry-state § attribution`
reports every id but only for the current phase. Neither reader reports a
healthy standing declaration made under a past phase** — which is precisely
what the refusal promises one of them does.

**What would change my mind:** a reader — any `perry-state` section, flag or
`--json` path — that names a live `via: "add"` declaration from a phase that is
not current. I read `linkage_records_for_phase`, `load_linkage`,
`perry-state`'s `attribution` block and `perry-lint`'s sweep, and measured the
27 on this project. Show me that reader and FAIL-1 collapses to the word
"permanently".

### FAIL-2 — where the store has no KR for the current phase, the gate refuses both honest answers and accepts only a guess

The refusal fires on one condition (`bin/perry-task:3716-3717`):

```
and (ctx["state_root"] / P.LINKAGE_STORE).exists()
```

But `--unlinked` is available on a *different* condition. `linkage_add_change`
calls `_current_store_phase` and refuses when it comes back empty
(`bin/perry-task:2780-2787`), and `_current_store_phase`
(`bin/perry-task:2794-2811`) returns `""` unless `phase/CURRENT` exists, names a
number, **and** the store holds a `kind: kr` record for that number.

**Those are not the same condition, and the gap is reachable.** Measured, four
states, each on its own throwaway project:

| state | neither flag | `--unlinked` | `--kr <an invented id of the right shape>` |
|---|---|---|---|
| healthy control (CURRENT=003, store has 003 KRs) | refused (the gate) | **filed** | filed |
| **`phase/CURRENT` cleared** — `phases.md § score-phase` step 7 | refused (the gate) | **refused** | **filed, exit 0** |
| **phase rollover** (CURRENT=004, store has only 003 KRs) | refused (the gate) | **refused** | **filed, exit 0** |
| **one unparseable line in `linkage.jsonl`** | refused (the gate) | **refused** | **filed, exit 0** |
| **merge-conflict markers in `linkage.jsonl`** | refused (the gate) | **refused** | **filed, exit 0** |

The `--unlinked` refusal in all four is *"`linkage.jsonl` declares no key result
for the current phase"*.

**The second row of that table is not a state I invented.**
`goals/reference/phases.md § score-phase` step 7 says, verbatim, to *"clear
`phase/CURRENT` (delete the file or write `(none)`) **until the next
`plan-phase`**"*, and step 9 then suggests `plan-phase` as a separate later
action. The window between them is a documented, expected, open-ended state of
every Perry project — and it is exactly when carry-over rows get opened. The
third row is the same window seen from inside `plan-phase`, whose steps 1 and 2
(`phase/CURRENT`, then the register) are agent-authored and explicitly exempt
from a deterministic writer. The fourth and fifth are a hand-edited or
half-merged store, which `perry-lint` has a check for precisely because it
happens.

**What the only remaining path costs.** On the rollover project, the sole
accepted invocation:

```
$ perry-task add --title … --kr <an invented id of the right shape>
perry-task: wrote <TASK-ID> (add) → tasks.jsonl + … + linkage.jsonl + …
$ echo $?
0
```

- **stderr is empty.** No warning that the id names no record anywhere. The
  `--kr` comment at `bin/perry-task:3589-3591` is explicit that resolvability is
  *"deliberately NOT checked here"* — a defensible decision on its own, and the
  decision this row turns into the only door.
- It appends `{"kind": "edge", "task": "<TASK-ID>", "kr": "<the invention>",
  …, "via": "add"}` to the canonical store — a fabricated edge, written by the
  same writer whose `unlinked` twin the refusal calls un-withdrawable.
- **`lib.same_action_linkage` counts it as answered: numerator 0 → 1,
  denominator 0 → 1.** The guess moves `P003-O3-KR2`, the KR this gate exists to
  make honest.
- `perry-state --section attribution` disagrees with it: `linked=0`, and the row
  sits in `never_asked`. Two readers, two answers, for one row.
- `perry-lint` exits 0 with **zero** lines naming the invented KR or the row.

**And it is a regression, not an inherited state.** The same five states driven
against `f3df6219:bin/perry-task` (the parent of `85e34b20`), in a full
`git archive` copy of that tree so the old tool imports its own `bin/lib`:
**all five filed the row, with the warning.** Before this change the caller got
an honest `kr: null` and a row in `never_answered`; after it, the cheapest —
and in four of five states the only — way to file anything is a fabricated
attribution that no diagnostic names.

**Why this is the row's defect and not `--kr`'s.** Unvalidated `--kr` is a
recorded, deferred decision and I am not charging it. What this row owns is
that it closed the two answers that were honest here while keeping a gate keyed
to a condition that does not imply the question is answerable. The spec's
`§ What it must not do` item 4 asked for exactly this to be *argued rather than
defaulted* — *"a fresh project has no KRs to name; the refusal must have an
answer for it"* — and the argument that was written
(`bin/perry-task:3672-3685`) reasons about a project with **no store**, which is
a strictly narrower set. The residual warning's own comment states the
assumption out loud: *"BOTH of those refuse on a store-less project, which is
now the only project that can reach this line"* (`bin/perry-task:3930-3933`).
The store-less project is not the only one where both remedies refuse.

**Which of `review.md § 0`'s three questions.** The first — *destroy or corrupt
state that cannot be recreated*: an `edge` record in `linkage.jsonl` naming a
KR that exists nowhere, appended by the `add` path, counted by the KR's own
reader, reported by no check. And the third — *weaken a gate standing between a
user and that*: the gate is what leaves it as the only move.

**What would change my mind:** a guard I did not find that makes one of those
four states unreachable, or a diagnostic that names the fabricated edge. I ran
`perry-lint` on the result and grepped its output for both the invented id and
the row id; zero hits.

### ROW-3 — `test_the_declaration_stands_across_a_second_read` does not pin standing, and the phase scope is unpinned in both directions

Round 2's § 3 table says this test pins *"'for as long as it stands', not a
one-shot line on the add run"*. It reads `declared_unlinked` twice in a row on
the same unchanged project. Nothing in it changes state between the reads, so
what it pins is that the reader is idempotent — a real property, and not the
one claimed.

Three mutations demonstrate the gap (§ 4): making `declared_unlinked` drop a
done/dropped row (**M6, green**), writing the declaration with no `phase` field
at all (**M8, green**), and making `declared_unlinked` read the whole store
instead of the phase slice (**M9, green**). M9 is the sharpest: it would make
the refusal's sentence **true**, and the module cannot tell.

**Grade: ROW.** I checked whether the behaviour M6 probes is actually broken and
it is not — § 1 shows the declaration surviving `done` and `purge` intact — so
this is not a test green while the code is broken, which `review.md § 0` sends
to V4. It is a test that does not measure what its own table says. M8 and M9 I
am **not** grading separately: they are corroboration of FAIL-1, which is where
the green-while-broken really is.

### ROW-4 — the false clause still stands, unmarked, in the record

`perry/evidence/2026-09/TASK-439-result.md:61` and `:125-127` still assert the
original sentence and its defence item 4 — *"`bin/perry-lint
§ linkage-unlinked-exists` files every standing declaration at `warn`"* — with
no marker, and round 2's § 2 and § 5 disposition tables do not mention the file.
`perry/BOARD.md:96` and `perry/journal/2026-09/2026-09-13.md:10-11` now carry
the replacement claim *"straight from the store, permanently"*, which FAIL-1
measures as false.

**Grade: ROW.** `review.md § 0` is explicit that a false statement in something
nobody executes — an evidence file, a result, a commit message — is a correction
to file and never a FAIL, and that the round should not spend itself hunting
them. Filed, not folded into FAIL-1. It matters only because this project has a
worked precedent for marking such a sentence in place rather than rewriting the
record.

## 3 · What I tried to break and could not

Reported so round 3 does not re-cover it.

- **Round 1's green MUT-B is genuinely closed.** Narrowing the refusal to
  `track == "main"` is now **RED** on
  `TestTheRefusalIsDeliberatelyTrackIndependent.test_a_non_main_track_is_refused_too`
  (§ 4, M5). The scope is pinned.
- **ROW-2's factual clause is true, and I drove it rather than reading it.**
  Round 2 argues track-independence partly on *"an intake row promoted to `main`
  later carries its blank answer with it and nothing on the promotion path goes
  back and asks."* `cmd_track` (`bin/perry-task:4503`) is the promotion path and
  contains **no** reference to `kr` or `unlinked` anywhere in its body. Driven:
  `perry-task track <TASK-ID> --track main --reason …` exits 0, and neither
  stdout nor stderr mentions the KR question. So `track` is the promotion path
  and it does not ask, and the argument for track-independence stands on this
  point. `stage` moves within a track only.
- **Round 1's ROW-3 is right, and I re-derived it rather than accepting it.**
  `route` takes the intake row NUMBER, not an id, which is why a first probe of
  mine could not address it. Driven: `route 1 --track main` → **exit 1**,
  *"track 'main' is mode `project`; routing is a queue-mode operation"*
  (`bin/perry-task:6301-6302`); `route 1 --track intake` → exit 0, event
  `route`, track `intake`, **no `kr` key**. So routed rows are not in
  `P003-O3-KR2`'s population and cannot be, and leaving `route` alone was
  correct. Round 2's acceptance of the correction is sound.
- **The refusal is still before `mint_id`.** Round 1 measured it; rule 3 says a
  prior PASS narrows where to look last, not that it is exempt. Re-read:
  `mint_id` is at `bin/perry-task:3749`, the refusal at `:3716`. M7 (disabling
  the guard with the parse intact) reddens
  `TestNothingWasWritten.test_no_id_was_burned`,
  `…test_no_row_was_filed` and `…test_no_add_event_was_appended` — nine tests in
  all — so the position is pinned by tests that can fail.
- **The `143` count is right**, and so is the reason `perry-lint` was left
  alone. 143 `kind: unlinked` records, 139 distinct ids, 127 written
  `via: "link"` and 16 `via: "add"`. Warning on all of them would warn on a
  correct answer, and I could not construct a version of that change that does
  not. Declining to make `perry-lint` the reader was the right call; naming
  `perry-state § attribution` without its phase qualifier was not.
- **The `--unlinked` half of the un-withdrawability claim survives the whole
  terminal path**, including `purge`. See § 1.
- **The anti-vacuity control does work.** M3 (`--kr` also writes an unlinked
  record) reddens `test_a_linked_row_is_not_declared` and
  `TestBothRemediesStillWork.test_kr_is_accepted_and_counted`. The new class is
  not green against a build that declares everything.

## 4 · Mutation table — nine planted, every restore verified against the ref

**Every mutation was planted in a `git archive fc6df1d6` copy in the scratch
directory, never in the repository under review** (`review-constraints.md § You
are a reader`). Each was **line-anchored** — never `str.replace` on a repeated
string — `__pycache__` cleared and **1.3 s waited past the whole-second
boundary** before both the plant and the restore, and each restore written from
and verified against `git show fc6df1d6:<path>` read out of the live
repository — an independent source, not bytes this harness snapshotted. The
module was re-run green after every restore.

| # | mutation | result | named test(s) that reddened |
|---|---|---|---|
| **M1** | refusal message names `perry-lint` again (round 1's FAIL-1 replanted) | **red** | `test_the_message_no_longer_names_perry_lint`, `test_the_message_names_the_reader_that_does_report_it` |
| **M2** | lane page reverted to its false sentence | **red** | `test_the_lane_page_names_the_same_reader_as_the_refusal` |
| **M3** | `--kr` also writes an `unlinked` record (anti-vacuity) | **red** | `test_a_linked_row_is_not_declared`; `TestBothRemediesStillWork.test_kr_is_accepted_and_counted` |
| **M4** | `perry-state` reports `declared_unlinked: []` | **red** | `test_the_named_reader_actually_reports_the_declaration`, `test_the_declaration_stands_across_a_second_read` |
| **M5** | refusal narrowed to `track == "main"` (**round 1's GREEN MUT-B**) | **red** | `TestTheRefusalIsDeliberatelyTrackIndependent.test_a_non_main_track_is_refused_too` |
| **M6** | `declared_unlinked` drops a row once it is `done`/`dropped` | **🟢 GREEN** | **none — ROW-3** |
| **M7** | the neither-flag refusal disabled, parse intact | **red** | 9, incl. `TestNothingWasWritten.test_no_id_was_burned`, `test_no_row_was_filed`, `test_no_add_event_was_appended`, `TestTheRefusalIsNotVacuous.test_neither_flag_is_refused` |
| **M8** | the declaration written with **no `phase` field** — which would make the refusal's sentence TRUE | **🟢 GREEN** | **none — corroborates FAIL-1** |
| **M9** | `declared_unlinked` read **store-wide** instead of phase-scoped — the other way to make the sentence true | **🟢 GREEN** | **none — corroborates FAIL-1** |

**Disclosed, because a reader should not have to find it.** My first M7 replaced
the head of a multi-line `if` with `if False:` and left the continuation line
dangling, so the module failed to **load** and reported
`unittest.loader._FailedTest`. That is a broken plant, not a red about the
guard, and it is not counted as one — M7 above is the re-done plant that
falsifies the first conjunct and leaves the parse intact.

**Three mutations came back green and `review.md § 2` rule 2 says a green
mutation is a finding either way.** M6 is graded ROW-3. M8 and M9 are not
separate findings: together they say the phase scope of the declaration's
visibility is unmeasured in **both** directions — no test can tell whether the
record carries a `phase` at all, and no test can tell whether the reader is
phase-scoped or store-wide. That is the blind spot FAIL-1 lives in, and it is
why the corrected sentence could be written, tested six ways, and still be
false.

**No file in the repository under review was modified at any point.**
`git status --porcelain` is empty as I write this. The mutated files live only
in the scratch copy.

## 5 · Scope and enumeration notes

- **The caller sweep is round 1's and I did not re-derive it.** Round 2 changed
  no call site, so the set is unchanged from the tree round 1 swept at 76
  occurrences over the Bound's eight directories. I did re-check the two claims
  that gate it: `cmd_add` has no in-file caller (`grep -n "cmd_add("` returns
  the definition only) and `cmd_track` reaches no KR logic.
- **The category for the new false claim is enumerated in § 2 FAIL-1** — two
  product surfaces, two code comments, and the record. `reference/okr-linkage.md`
  :33-36 mentions `declared_unlinked` but states the TASK-228 disjointness rule,
  not a permanence claim; it is correct as written.
- **Disclosed: the scratch directory is shared.** Another session overwrote a
  file of mine there mid-round, with an unrelated harness for a different row.
  My run had already read its own bytes and its output is intact and
  self-identifying, and I re-ran nothing on the strength of it — but the
  collision is real, it is the second shape of the hazard
  `work/reference/dispatch.md § 14` records, and later probes here use
  round-unique filenames. **I killed nothing and signalled nothing**; seeing an
  unexplained result is a reason to read.

## 6 · The suite

`python3 tests/parallel` on the merged tree: **130 modules · 3776 tests ·
74.8s · 8 workers — 3 failed, 2 of 130 modules red.** Identical to round 2's
report, including the totals.

**Each red re-run module-alone before attributing it**, because an order- or
clock-dependent red attributed to the wrong cause is a mistake this project has
made repeatedly:

1. `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable` — `[conformance.in_progress_with_no_live_run[].means]`
2. `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` — same key
3. `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` — clock-dependent

All three reproduce alone, none is in a module this change touches, and
**nothing in this review is attributed to them**. `test_add_refuses_without_an_answer`
is **27 tests, all green**, as round 2 reports.

## 7 · What I did not check

- **Any `perry-state` invocation other than `--section attribution`** on a
  fixture, and no `--json` whole-payload read. FAIL-1 rests on that section plus
  a source read of `load_linkage` / `linkage_records_for_phase` / `perry-lint`'s
  sweep; a second reader I missed would reduce it to the word "permanently".
- **Whether any phase-less `unlinked` record exists in this project's store** —
  `linkage_records_for_phase` travels those with every phase, so they would be
  the one exempt population. I counted by phase and all 143 carry one, but I did
  not audit the import path that produced the 127 `via: "link"` records.
- **Whether the four FAIL-2 states occur in this repository's own history.** I
  established reachability from `goals/reference/phases.md`'s own prescribed
  steps and drove each state on a fixture; I did not search the git history for
  a commit where `phase/CURRENT` and the register actually disagreed.
- **`--kr` validation as a defect in itself.** Deliberately deferred by
  `bin/perry-task:3589-3591` to another row; I charge only that this row makes
  it the sole door.
- **`bin/lib/__init__.py`** beyond reading `same_action_linkage` — out of scope
  by the spec, not mutated. I therefore did not re-derive round 1's § 6
  exposure bracket or the result's repo-level percentages.
- **Whether a project can declare a track literally named `main` in `queue`
  mode**, which is the only configuration in which `route` could put a row on
  `main` at all. Round 1 named this gap too and did not construct one; neither
  did I.
- **ROW-4 from round 1** (the `M.Fixture.add` falsy-`kr` seam). Round 1 swept it
  and found one instance; I did not re-sweep.
- **Windows paths, non-UTF-8 roots, concurrent `add`,** and `perry-goals link`
  in any form.
- **`tests/durations.json`.** The runner reports `test_contract_page_snippets.py`
  missing from it on every run, in the copy and in the live tree alike. Not this
  row's, and not investigated.

## 8 · What a PASS needs

FAIL-1 is one qualifier in one sentence, at two product surfaces and two
comments: `declared_unlinked` reports a declaration **while the phase it was
declared under is current**, and the must-not #1 argument has to be re-made
against that weaker fact rather than against "permanently" — or a reader that is
genuinely phase-independent has to be named. M8 and M9 say the tests cannot
currently tell the two apart, so whichever way it goes needs a test that drives
the reader **across a phase boundary**, not twice on an unchanged project.

FAIL-2 is a condition mismatch: the gate fires on `linkage.jsonl` existing, and
the honest answers are available only when the store declares a KR for the
current phase. Aligning those two — refusing where the question is answerable,
warning where it is not, which is the rule the comment already claims to
follow — is the small version. Deciding instead that a guessed `--kr` is
acceptable in that window is a different and larger decision, and it belongs to
whoever owns `--kr` validation, not to a third round here.

ROW-3 and ROW-4 go out as rows.

**One measured consequence of this verdict, stated because it changes what the
next step is.** With this block in place, `perry-lint --reviews` reports
`review-rounds-exhausted` for TASK-439: two FAILed V4 rounds on row-failing
criteria, never PASSed, against a limit of 2 from `schema § thresholds`. So
**a third round is not what this row needs** — the finding's own instruction is
to file the ask, name the two readings and let the user choose. I am a reader
and do not open rows or file asks (`review-constraints.md`), so this is a
pointer, not an action. It also reports that 1 of the 2 counted blocks carries
no readable `grade:` — round 1's, not this one's; mine is written and reads
`FAIL`, so it is counted deliberately rather than by default.

I will say what I think the principle is, since § 6 asks somebody to pick one
and the round that measured it is the cheapest place to state it: **both FAILs
are the same mistake in two places — the code treats "`linkage.jsonl` exists"
as equivalent to "this project's register can answer the KR question for the
current phase", and it is not.** `perry-state`'s reader and
`linkage_add_change`'s writer both key off the phase; only the gate keys off the
file. Align the gate with the phase and FAIL-2 goes away and FAIL-1's sentence
becomes checkable; leave them misaligned and a third round will find a third
face of it.

```
=== VERDICT ===
task: TASK-439
rung: V4
result: FAIL
grade: FAIL — `§ What it must not do` item 1 (the refusal's standing-visibility
         claim, still false at both product surfaces) and item 4 (`add` must
         keep working where the KR question cannot be answered); both charged
         FAIL against `review.md § 0` questions 2 and 1 respectively, neither
         graded down
criteria: perry/evidence/2026-09/TASK-439-spec.md
checked: base asserted and recovered per dispatch.md (583f024f, 128 behind,
         containing neither 85e34b20 nor c7618a96; ff-only on my own branch,
         re-asserted); round 2's 116->117 / 2->3 / zero-lint-lines reproduced on
         a git archive copy; the 143 store count reproduced and split by phase
         (116/4/23); a declaration driven across a phase boundary on a fixture;
         5 project states x 3 invocations driven against fc6df1d6 AND against a
         full archive of f3df6219; the forced-guess path's store record,
         same_action_linkage numerator, attribution and perry-lint output all
         read; the un-withdrawability clause driven through add --unlinked ->
         done -> purge; cmd_track driven and read for the promotion-path
         claim; route driven on both tracks, re-deriving round 1's ROW-3;
         9 mutations planted IN A SCRATCH COPY, every restore written from and
         verified against `git show fc6df1d6:`; suite 130 modules / 3776 tests /
         3 pre-existing reds, each re-run module-alone; repository never written
not-checked: perry-state sections other than attribution, and no --json whole
         payload; whether any phase-less `unlinked` record exists in this store;
         whether the four FAIL-2 states occur in this repo's own history;
         --kr validation as a defect in itself; bin/lib/__init__.py beyond
         same_action_linkage, so round 1's exposure bracket is unre-derived;
         whether a queue-mode track can be named `main`, the only config in
         which route could reach it; round 1's ROW-4 test seam; Windows paths;
         concurrent add; perry-goals link
proof: FAIL-1 — bin/perry-task:3729 tells the caller `perry-state --section
         attribution` counts the declaration under `declared_unlinked` "for as
         long as it stands", and bin/perry-state:2158 reports `link.unlinked`,
         which is P.load_linkage's PHASE SLICE: viewer/parsers.py:4137-4139
         keeps an `unlinked` record only when its own `phase` matches
         phase/CURRENT, and bin/perry-task:2788 stamps that phase on every
         record `add --unlinked` writes. Measured: this project holds 143
         standing declarations (116 under 003-storage-code, 4 under
         002-fields-are-typed, 23 under 001-work-modes-live) and the named
         reader reports 116 — 27 live declarations it does not report. On a
         fixture, a declaration reported while 003 is current reports [] once
         004 opens, with the store record unchanged on disk. M8 (no `phase`
         field) and M9 (store-wide read) are both GREEN, so the scope is
         unpinned in both directions. work/reference/subcommands.md:591 carries
         the same claim.
         FAIL-2 — bin/perry-task:3716-3717 gates the refusal on
         `linkage.jsonl` existing, while bin/perry-task:2780-2787 refuses
         `--unlinked` unless _current_store_phase (:2794-2811) finds a `kind:
         kr` record for phase/CURRENT. In the gap — phase/CURRENT cleared,
         which goals/reference/phases.md § score-phase step 7 prescribes; a
         phase rollover; an unparseable line or merge-conflict markers in the
         store — both honest answers refuse and `--kr <an invented id>` is
         accepted at exit 0 with EMPTY stderr, appending {"kind":"edge",…,
         "via":"add"} for a KR no record declares. lib.same_action_linkage
         counts it 0/0 -> 1/1; perry-state reports linked=0 and the row in
         never_asked; perry-lint exits 0 with zero lines naming either. All
         five states filed the row with a warning against f3df6219, the parent
         of 85e34b20.
=== END VERDICT ===
```
