# TASK-439 — result

`perry-task add` refuses a row that answers the KR question neither way.

> Branch: `worktree-agent-a2e8acf37b3cd9fec` · Base: `f3df6219`
> Suite: `bash tests/run` — 3723 tests, **3 failed, all pre-existing and named
> in § 8**. Tree guard clean on every run.
> Rung: V4. `ADR-020`'s gate answers yes (`cmd_add` writes `tasks.jsonl`,
> `linkage.jsonl`, the journal and the event log) and `review.md § 0`'s third
> question answers yes: this row builds a gate on the path every row in the
> project is created through.

## 0 · Base check, first, because three agents in a row were handed stale trees

`git log --oneline -1` reported **`583f024f`** and
`git merge-base --is-ancestor f3df6219 HEAD` **failed** — the worktree was
**116 commits behind** main's tip, the fourth instance of this in a row.

It was a strict ancestor (`git merge-base --is-ancestor HEAD f3df6219`
succeeded), 0 commits ahead, and `git status --porcelain` was empty. So the
documented recovery applied: `git merge --ff-only f3df6219`, on my own branch
only, touching no other checkout. Re-verified afterwards — `f3df6219` is now an
ancestor of `HEAD` and the tree is clean. **All measurements below were taken
after the fast-forward**, per *Measure baselines in the agent's own tree*.

## 1 · The states, before and after, each run against the real binary

Driven through `bin/perry-task` as a subprocess on a throwaway project built
from `tests/test_add_writes_the_edge § Fixture`. Never against this repo's
store.

| # | invocation | before | after |
|---|---|---|---|
| 1 | `--kr <ID>` | exit 0, `edge` record, event `kr: "<ID>"` | **unchanged** |
| 2 | `--unlinked` | exit 0, `unlinked` record, event `kr: null` | **unchanged** |
| 3 | **neither** | **exit 0**, row filed, warning on stderr, event `kr: null`, row permanently in `never_answered` | **exit 1, REFUSED, nothing written** |
| 4 | `--kr ""` | exit 1, refused — message directs the caller to *omit `--kr`* | exit 1, refused, **message rewritten** (§ 4) |
| 5 | `--kr <ID> --unlinked` | exit 1, refused as contradictory | **unchanged** |
| 6 | neither, **no register** | exit 0, row filed, warning | **exit 0, row filed, warning rewritten** (§ 5) |
| 7 | `--unlinked`, **no register** | exit 1, refused | **unchanged** |
| 8 | `--kr <ID>`, **no register** | exit 0, event only, no store record | **unchanged** |

State 3 before:

```
perry-task: warning — TASK-101 was created without `--kr`, so no KR edge was
recorded and the row reads as never-asked. …
```

State 3 after:

```
perry-task: refused — neither --kr nor --unlinked was passed. This project has
a `linkage.jsonl`, so the KR question has an answer and `add` will not file a
row that leaves it blank — omitting both used to file the row behind a warning,
and no longer does. Pass exactly one. `--kr <KR-ID>` attributes this row to
that key result and is the answer to reach for first: resolve the id through
`linkage.jsonl` rather than guessing it, which `reference/okr-linkage.md`
forbids. `--unlinked` is the other answer and says this row serves NO key
result at all — it writes a record that CANNOT BE WITHDRAWN by any
`perry-task` command and that `perry-lint` reports for as long as it stands,
so it is a declaration to mean, not a way to make this refusal go away on a
row whose KR you have not looked up yet. Nothing was written
```

**Where the refusal lives:** `bin/perry-task § cmd_add`, immediately after the
contradiction refusal and the blank-`--kr` refusal, so the three linkage
refusals read as one rule — and **before `mint_id`**, so a refused attempt
burns no id (`ADR-013`: ids are terminal). `test_no_id_was_burned` pins that
position rather than trusting it.

## 2 · The semantic argument

*This section is the row's subjective verification, and it is the deliverable
the spec asked to be named.*

### 2.1 Omission stops being an answer, so the advice that recommended it had to go

Before this change the tool taught omission twice: once by accepting it, and
once — explicitly — in the blank-`--kr` refusal, which told the caller to
*"omit `--kr` for that, which files the row and warns."* After the refusal, that
sentence is advice to run the command that now refuses. **A refusal whose
remedy itself refuses is worse than no remedy**, because it costs the caller a
second round trip to discover that the tool contradicted itself. Both messages
were therefore rewritten in this change rather than deferred (§ 4, § 5).

### 2.2 The blank-`--kr` refusal earns its place — more after this row, not less

The collapse argument is that both states now refuse, so one message would do.
**That argument is wrong, and the reason is `TASK-281` round 3's own evidence.**

Round 3 established that blank-means-omission is the hazard: `--kr "$KR"` with
`KR` unset arrives as `--kr ""`. Consider that caller under each design.

* **Kept separate** (what shipped): they are told *the value you passed is
  empty — check the variable you expanded*, and they fix the variable.
* **Collapsed into one refusal**: they are told *you gave no answer; pass
  `--kr` or `--unlinked`*. A caller who believes they already passed `--kr`
  reads that as "the tool wants the other flag" and plausibly reaches for
  `--unlinked` — writing a **permanent, un-withdrawable** "serves no key
  result" record for a row that does serve one, because a shell variable was
  empty.

So collapsing converts a typo into a wrong canonical store record. The cost of
the collapse **rose** when omission started refusing, because before this row
the same mistake produced merely a warned row. The two refusals share an exit
code and differ in the only thing that matters — the sentence. Kept, and the
message sharpened to name the `$KR` hazard outright;
`test_it_names_the_empty_variable_hazard` pins that it does.

### 2.3 Why this does not make `--unlinked` the easy default

`reference/okr-linkage.md` forbids a guessed attribution, and a refusal that
herds every caller to `--unlinked` buys a worse number than the one it fixes.
The defence is structural, not rhetorical — wording alone would not survive a
caller in a hurry:

1. **No effort gradient.** Both answers cost exactly one flag. There is no
   cheaper way out to drift toward.
2. **No scoreboard gradient.** `P003-O3-KR2` counts `--kr` and `--unlinked`
   *identically* as answered. Choosing `--unlinked` flatters no metric, so
   nothing rewards it.
3. **It is not a universal escape hatch.** `--unlinked` is *refused* on a
   store-less project (state 7), so it cannot be the reflex answer everywhere.
4. **It stays visible.** `bin/perry-lint § linkage-unlinked-exists` files every
   standing declaration at `warn`. A row that takes `--unlinked` acquires a
   permanent record **and** a standing lint warning.
5. **It is irreversible, and the refusal says so before the write**, in the
   same shape the contradiction refusal already uses.

A caller reaching for `--unlinked` to silence the refusal therefore buys
strictly more trouble than looking the KR up. **The honest caveat:** items 1–2
mean the design is neutral between the two answers; it does not *push* toward
`--kr`. Nothing short of refusing `--unlinked` too would, and that is forbidden
by must-not #1's other half. Neutral-with-friction-on-the-lossy-side is the
most this row can buy, and § 7 reports the exposure that friction leaves.

### 2.4 A project with no linkage register — argued, not defaulted

The refusal is **gated on the register existing**. The gate is not a
convenience; it is the condition under which the question has an answer at all:

* `--unlinked` on a store-less project is **refused** by `linkage_add_change`
  — it has no event field and no second home, so accepting it would store the
  declaration nowhere.
* `--kr` on a fresh project can only name a key result **that does not exist**,
  because `/perry goals plan-phase` is what writes the register.

So an unconditional refusal would leave a **guessed `--kr`** as the only way to
file any row at all on a fresh project — forcing precisely the guess
`okr-linkage.md` forbids, in order to enforce a rule about attribution quality.
The gate fires where the question is answerable and stays a warning where it is
not, which is the same rule `linkage_add_change` already applies to
`--unlinked`, read from the other end.

This is pinned by `TestAStoreLessProjectStillFiles`, and its boundary is
mutation-tested: **M3** drops the register guard and reddens it (§ 6).

## 3 · The enumerated caller set

**Enumeration:** every `perry-task add` occurrence in the Bound's directories.
**Order:** alphabetical by path. **Size, derived:** **68 textual occurrences**
— `bin` 17, `work` 6, `goals` 3, `modes` 1, `tests` 41, and **zero** in
`decide/`, `packs/`, `templates/`. Of these, most name the tool in prose; the
*calls* — text that instructs or executes an invocation — are the 9 sites below.
**Last element** in that order: `work/reference/subcommands.md`.

### Changed — would now refuse

| # | site | what it was | judgement |
|---|---|---|---|
| 1 | `bin/README.md:417` | `Usage:` block showing `add` with `[--kr KR-ID]` optional and no mention of `--unlinked` | documented a call that now refuses; rewritten to state one of the two is required, with the register caveat |
| 2 | `tests/test_add_declares_unlinked.py § next_id` | `--dry-run` probe, neither flag | given `--unlinked`, mirroring the crashing run |
| 3 | `tests/test_add_declares_unlinked.py § TestSilenceIsStillNeverAsked` | asserted silence files the row and lands in the denominator | **inverted, not deleted** — silence refused with a register; § 5.2 half repointed at the store-less project |
| 4 | `tests/test_add_writes_the_edge.py § next_id` | `--dry-run` probe, neither flag | given `--kr`, mirroring the crashing run |
| 5 | `tests/test_add_writes_the_edge.py § TestWithoutAKr` | § 5.2's "record and warn", 6 call sites | repointed at the store-less project, where § 5.2 survives; every assertion kept |
| 6 | `tests/test_same_action_linkage.py § …test_omitting_the_flag_still_files_the_row_and_warns` | asserted the old contract by name | inverted; its real guard — *`--kr` did not become mandatory* — repointed onto a new `--unlinked` test |
| 7 | `tests/test_same_action_linkage.py § test_the_fixture_can_actually_file_a_row` | fixture control, neither flag | given `--unlinked`; the control is **stronger** — a bare `add` would now report a good fixture as broken |
| 8 | `tests/test_work_modes.py § …accepts_a_track_only_the_store_declares` | track probe, neither flag | given `--unlinked`; without it the test reads a linkage refusal and reports it as the projection beating the register |
| 9 | `work/reference/subcommands.md:591` | **"omit `--kr` on the `perry-task add` below"** | the lane page instructing the exact call that now refuses — rewritten to pass `--unlinked` |

### Left alone, each judged

* **`perry-task intake` and `route` — the Bound's Remainder, checked rather
  than assumed.** Neither reaches `cmd_add`: `cmd_add` has no caller in the
  file, and line 3805 is the only site emitting an `add` event. `cmd_intake`
  never calls `mint_id` at all. **They are OUT** — but see § 9, because `route`
  *does* open a main-track row, and that is a finding.
* **`bin/lib/__init__.py` (5 occurrences)** — out of scope by instruction.
* **`bin/perry-lint` (5), `bin/perry-goals:1809`, `bin/perry-tasks:1435`,
  `goals/SKILL.md:152`, `goals/reference/linkage.md:8`,
  `goals/reference/phases.md:216`, `modes/queue.md:348`,
  `work/reference/subcommands.md:34, 578, 589, 604, 714`** — all name the tool
  in prose or show a call that already passes `--kr`. None instructs an
  invocation that now refuses. Line 589 in particular already says *"pass the
  same id to `perry-task add --kr <KR-ID>`"* and is correct as written.
* **`perry/**` (the bulk of the 100+ repo-wide hits)** — outside the Bound's
  directory list by design, and correctly so: evidence, journals and the board
  are a **record of what was true when written**. Rewriting them would falsify
  history to match current behaviour.

### Which callers surprised me

1. **`next_id` in both crash-matrix modules.** A `--dry-run` probe whose only
   job is to read back the next id. It broke because the refusal fires
   **before `mint_id`** — which is exactly where it should fire. The lesson:
   **`--dry-run` is not a bypass**, and any caller using it to *derive* an id
   inherits every refusal on the path to that id.
2. **`tests/test_handed_back_root.py` — not a caller at all.** It holds a count
   of paste-able writer hand-backs in `bin/`, and my change moved it **down**
   from 66 to 64, because the reconciliation *removed* two hand-backs (the
   blank message no longer offers `perry-goals link --unlinked`; the warning no
   longer offers `perry-task add --unlinked`). A sweep that only looked for
   invocations would have missed this entirely. Constant updated with both
   reasons recorded, per its own instruction to check a drop rather than assume
   it benign.
3. **`tests/test_summary_is_asked_for.py` — also not a caller.** It asserts
   `"refused" not in stdout+stderr` as a proxy for "the command was not
   refused". My *warning* text ended with the word "refused" on a **successful**
   run, so a green path tripped it. I reworded my warning rather than loosen
   someone else's assertion.
4. **`bin/perry-task`'s own `SURFACE` summary.** `test_bin_surface` caps
   `--help` at 3000 characters; my first one-line summary pushed it to **3008**.
   Shortened, keeping the register caveat, which must stay true.
5. **`work/reference/subcommands.md:591`** — not surprising that it existed, but
   it is the page an agent reads *in order to open a row*, and it instructed the
   refused call in bold. This is the defect the spec predicted this row would
   create, found and fixed inside it.

## 4 · The blank-`--kr` message, reconciled

Before — the remedy refuses after this row, and points at the slower path:

> `--kr '' is blank. It is not a way to say this row serves no KR — omit
> `--kr` for that, which files the row and warns, or use `perry-goals link
> --unlinked …` to declare it outright. …`

After — names `--unlinked`, the flag on *this* command (`TASK-281` round 3's
correction: `link` is the after-the-fact path, and only a declaration made at
`add` is counted by the KR), and names the hazard that justifies keeping the
refusal separate at all:

> `--kr '' is blank. It is not a way to say this row serves no KR — pass
> `--unlinked` for that, which declares it outright in this same `add`. If you
> meant to name a key result, the value you passed is empty: check the variable
> you expanded, because `--kr "$KR"` with `KR` unset arrives here looking
> exactly like this. …`

## 5 · The warning, narrowed and reconciled

The `§ 5.2` warning now has exactly **one** reachable caller: the project with
no linkage register. Its old text offered `perry-goals link --unlinked` and
`perry-task add --unlinked` — and **both refuse on a store-less project**, which
is now the only project that can reach the line. Every remedy it named was a
remedy that refuses. It now names `/perry goals plan-phase`, the only thing
that creates a register.
`test_the_warning_does_not_advise_a_command_that_refuses` pins it.

## 6 · Mutation table

Each mutant applied to `bin/perry-task`, the named module run, the file
restored (verified byte-identical after every round).

| # | mutation | result | named test(s) that reddened |
|---|---|---|---|
| **M1** | **Remove** the refusal — gate can never fire | **red** | `TestTheRefusalIsNotVacuous.test_neither_flag_is_refused`, `…test_the_refusal_names_which_one_means_serves_no_kr`, `TestNothingWasWritten.test_no_row_was_filed`, `…test_no_add_event_was_appended`, `…test_no_id_was_burned`, `TestTheRefusalDoesNotSilentlyDeclare.test_omission_does_not_enter_the_population` |
| **M2** | **Weaken** — stop refusing; treat omission **as** an `--unlinked` declaration (the cheap wrong fix that sends the KR to 100%) | **red** | **`TestTheRefusalDoesNotSilentlyDeclare.test_omission_is_not_a_declaration`** (reddens under M2 and **not** under M1 — the discriminating test), plus `test_the_refusal_is_about_the_kr_question` and M1's set |
| **M3** | **Weaken the boundary** — drop the register guard, so the refusal also fires where the question has no answer | **red** | `TestAStoreLessProjectStillFiles.test_add_still_works_with_no_register`, `…test_the_warning_does_not_advise_a_command_that_refuses` |

**No mutant came back green.** M1 and M2 are distinguished by
`test_omission_is_not_a_declaration`, which is the point of running both: a
suite that could not tell "refusal removed" from "refusal replaced by a silent
declaration" would not be measuring the thing this row is about.

### Anti-vacuity

The spec asks for proof the refusal test would not pass if the refusal never
fired. Three things carry it:

1. **A sibling control on the same fixture.**
   `TestBothRemediesStillWork` drives the *same command line* plus one flag and
   asserts **exit 0** — so a fixture that refused everything cannot keep
   `TestTheRefusalIsNotVacuous` green.
2. **The refusal is identified by subject, not by exit code.**
   `test_the_refusal_is_about_the_kr_question` and
   `test_the_refusal_names_which_one_means_serves_no_kr` read the message, so an
   unrelated refusal (missing `--summary`, bad root) does not satisfy them.
   This is the shape `TASK-281` round 1's refusal test rotted green in.
3. **It is asserted through the reader.** `TestTheRefusalDoesNotSilentlyDeclare`
   goes through `lib.same_action_linkage`, so a writer emitting a record no
   reader counts cannot pass.

**A vacuity defect I caught in my own tests, and it is worth recording.** My
first draft of `TestTheBlankRefusalIsReconciled` drove `self.add(d, title, "")`.
`M.Fixture.add` appends `--kr` only when the value is **truthy**, so the empty
string silently dropped the flag and every one of those tests was driving the
**neither** state, not the blank one. Three assertions passed anyway — and
`test_blank_kr_is_still_refused` passed because my *new* message happens to
contain the word "blank". Only `assertIn("$KR", …)` failed and exposed it. The
flag now goes through `*extra`, where nothing filters it, and the seam is
documented in the helper so the next reader does not re-make it. This is the
sixth instance of this project's signature defect, found inside the change
written to guard against it.

## 7 · The measured increase in `bin/lib/__init__.py:1438`'s exposure

**Reported, not fixed** — `TASK-281`'s finding, `bin/lib/__init__.py` out of
scope by instruction.

**The blind spot.** `:1438` reads `unlinked_at_add` only *inside* the event
loop (`elif tid in unlinked_at_add:`), and that loop's population is built from
`add` events. So an `unlinked` record whose `add` event never landed — a
**half-landed** declaration — is dropped from the KR's population and named by
**no diagnostic**. Its edge twin is computed *outside* the loop
(`store_edge_without_event`, over `edge_at_add.items()`), which is why the edge
side is reported and the declaration side is silent. There is no
`unlinked_without_event`.

**Measured on this repository, at `f3df6219`:**

| | |
|---|---|
| `P003-O3-KR2` | 19 / 59 = **32.2%** (spec quoted 18/58; `TASK-439`'s own row landed between) |
| `linkage.jsonl` records `via: "add"` | 4 `edge`, **15 `unlinked`** |
| live instances of the blind spot | **0** — every `unlinked` record has its `add` event |
| `store_edge_without_event` | `[]` |
| main-track `add` events, all time | **362** |
| of those, took the **neither** path | **343 — 94.8%** |

**The increase.** This row makes `--unlinked` the *only* way to say "serves no
KR" at creation. The path carrying 94.8% of all historical `add` traffic is
closed, and that traffic must redistribute onto `--kr` or `--unlinked`.

* **Lower bound — no increase.** If every future caller names a real KR,
  traffic through the `unlinked` writer is unchanged.
* **Upper bound — 23.9×.** If every caller that would have omitted both now
  declares instead, the writer's records go from **15** to **15 + 343 = 358**.

The blind spot's exposure is **proportional to records written through that
path**, so the bracket on exposure growth is **1× to 23.9×**, on a defect that
is silent by construction and currently has **zero** live instances.

**The only empirical sample available points at the high end, and I am
reporting it with its caveat.** Of the 5 code call sites I had to give an
answer to in § 3, **4 chose `--unlinked`** and 1 chose `--kr`. Every one is a
throwaway probe row that genuinely serves no key result, so this sample says
nothing reliable about real rows — but it is the only measurement of the choice
this refusal actually induces, and it is not reassuring. **Recommendation for
`TASK-281`'s fix: it is now worth doing before the traffic arrives, not after.**

## 8 · The suite

`bash tests/run` — **3723 tests, 3 failed, 2 of 129 modules red.** All three
are pre-existing, named rather than counted, and none is attributed to this
row:

1. `test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable` — `[conformance.in_progress_with_no_live_run[].means]`
2. `test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` — same key
3. `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`

**Tree guard clean on every run** — nothing was written into the repository
while the suite was running.

**One red I did NOT attribute without re-running it alone.**
`test_summary_is_asked_for` appeared red in an intermediate full-suite run and
had been green in the first. Re-run in isolation, it reproduced, and the cause
was mine but not a breakage: my warning text contained the word "refused" and
that module greps combined output for it (§ 3, surprise 3). Fixed by rewording;
green thereafter.

`test_contract_page_snippets.py` is flagged as *not in durations.json*. That is
pre-existing and not mine — it is on disk at `f3df6219` unregistered. My own
module **is** registered (§ 10).

## 9 · Findings I am reporting rather than fixing

1. **`perry-task route` opens a main-track row that this gate cannot see, and
   that `P003-O3-KR2` never counts.** `cmd_route` calls `mint_id` and
   `append_row` — it creates a real board row with a fresh `TASK-` id — but it
   emits `event: "route"`, **not** `add`, and that event carries **no `kr`
   key**. The KR's population is *"rows whose own `add` event carries a `kr`
   key"*, so a routed row is not merely unanswered: it is **invisible to the
   metric entirely**, in neither numerator nor denominator.

   The Bound's Remainder test puts `route` out of scope for the *change* (it
   does not reach `cmd_add`), and I have left it alone. But
   `phase/003-storage-code.md § Definition of Done` item 5 asks for *every*
   main-track row opened after the gate lands to carry an edge or a
   declaration, and **after this row, `route` is the remaining way to open one
   that does not.** The gate is closed on `add` and open on `route`. This
   deserves its own row; I have not opened one, per *do not open new rows by
   default*.

2. **`bin/lib/__init__.py:1438`** — § 7. `TASK-281`'s to fix; this row's job
   was to measure how much bigger it made it, and it did.

3. **The scratchpad is shared between concurrent sessions, and one of them left
   a stdlib shadow.** `…/scratchpad/inspect.py` — another session's analysis
   script — sits on `sys.path[0]` for anything run from that directory, so
   `dataclasses`' `import inspect` picked it up, executed its top-level code,
   and died with `module 'inspect' has no attribute 'signature'`. My first
   baseline run was destroyed by this and its output was another session's.
   Nothing in the repository is affected (that script reads its own sandbox
   copy). I worked from a private subdirectory afterwards. Flagging it because
   a session that did not notice would have mistaken foreign output for its own
   measurement — I nearly did. I also overwrote a same-named `probe.py` that
   another session had left there.

## 10 · Files changed

| file | change |
|---|---|
| `bin/perry-task` | the refusal in `cmd_add`; blank-`--kr` message reconciled; `§ 5.2` warning narrowed and its remedies corrected; `SURFACE` summary for `add` |
| `bin/README.md` | `add` usage block: one of `--kr` / `--unlinked` required, with the register caveat |
| `work/reference/subcommands.md` | the KR-attribution gate bullet: `--unlinked` at `add` instead of "omit `--kr`" |
| `tests/test_add_refuses_without_an_answer.py` | **new** — 18 tests: the refusal, its subject, nothing-written, both remedies, the anti-vacuity and non-declaration controls, the store-less project, the reconciled blank refusal, the untouched contradiction |
| `tests/test_add_writes_the_edge.py` | `next_id` probe; `TestWithoutAKr` repointed at the store-less project |
| `tests/test_add_declares_unlinked.py` | `next_id` probe; `TestSilenceIsStillNeverAsked` inverted and split |
| `tests/test_same_action_linkage.py` | omission test inverted; its guard repointed onto `--unlinked`; fixture control given a flag |
| `tests/test_work_modes.py` | track probe given `--unlinked` |
| `tests/test_handed_back_root.py` | held count 66 → 64, with both withdrawals recorded |
| `tests/durations.json` | new module registered at 3.30s (timed alone ×3, median) |

**Not touched, by instruction:** `bin/lib/__init__.py`,
`schema/state-schema.json`, `P003-O3-KR2`, its metric, and
`perry/linkage.jsonl`'s KR records. No `git add -A` was run; every commit used
explicit paths.

## 11 · What this row does not do

**It does not move `P003-O3-KR2`'s number**, and a reader expecting it to will
mis-read this result. The 40 rows already in `never_answered` are permanent by
the KR's own rule — a later `perry-goals link` writes `via: "link"`, which the
KR excludes by design, and that exclusion *is* the "in the same action as"
clause. The ratio goes `(19+n)/(59+n)`: **22 new answered rows to reach 50%,
342 to reach 90%.** Re-baselining the denominator is the second half of the
decision, and it is a KR change — the `goals` lane's and the user's, not this
row's.

What this row buys is that the number is **honest going forward**: from here,
a main-track row created through `add` on a project with a register cannot be
unanswered.
