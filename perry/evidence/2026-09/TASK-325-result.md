# TASK-325 — result

> Branch: `coding/task-325-summaries`. Baseline: `main` at `a6ca21f`.
> Instruments, both committed: `TASK-325-census.py`, `TASK-325-mutations.py`.

## 0. The worktree was not cut at the baseline

The tool cut this worktree at **`d49964e`**, an ancestor of `main` and 96 files
/ ~17,900 lines behind it. `d49964e` is the commit several of this week's rows
quote as their measurement point, so it is not a random ref — but it is not the
briefed baseline. Everything below was done on a branch cut from `main` at
`a6ca21f`, stated here because the brief asked for the commit to be named
rather than assumed.

## 1. Re-derivation of the filed numbers

Re-measured on `a6ca21f` with the committed census script. Every figure in the
brief holds:

| claim | brief | re-measured on `a6ca21f` | verdict |
|---|---|---|---|
| rows total | 319 | **319** | holds |
| open rows | 114 | **114** | holds |
| rows carrying a summary | 49 | **49** | holds |
| open rows carrying one | 25 | **25** | holds |
| open rows blank | 89 | **89** | holds |
| `--summary` instructions in `work/reference/*.md` | zero | **zero**, across the 8 files that mention the word | holds |
| `perry-lint` checks on the field | zero | **zero** — all 10 mentions are prose or `check_claims`' own summary dict | holds |

Two corrections, neither of which changes the work:

- **The spec's `## Backfill` prose says "90 open rows are blank"; its own
  `## Bound` says 89.** 89 is right. The brief carried the correct figure.
- The spec's "40 of 49 under a wider pattern" re-measures to **39 of 49** with
  a slightly different instrument. That is instrument spread, not disagreement
  — but the conclusion drawn from it is wrong, which is §2.

## 2. THE FINDING: the diagnosis in the spec is not supported by the data

The spec's causal claim is that **"the field degraded into a second title"**.
Measured across all 49 summaries on the board, that is false. Not one of them
is structurally a second title:

```
open rows by rule:
  missing        89
  repeats-title   0
  no-sentence     0
  fragment        0
```

The 49 that exist are, as a population, good: shortest 132 characters / 22
words, median 485 characters / 84 words, and **every one contains at least one
complete sentence**. There is no degraded summary on this board to find.

Worse for the spec, its single named example refutes its own predicate. It
offers *"it opens with a bare id (`TASK-218` opens with `DESIGN-012 I1`)"* as a
structural symptom. Ten of the 49 open with a bare id — TASK-218, 219, 220,
221, 236, 237, 238, 182, and closed 235, 260 — and **all ten are among the best
summaries on the board.** TASK-218's reads in full:

> DESIGN-012 I1. Today each of the four phase-close stages re-reads
> phase/CURRENT, so the moment one stage advances it every later stage aims at
> the wrong phase. That is the 2026-08-28 failure, and it is a data-flow bug
> rather than a documentation one.

A leading citation followed by an explanation is this project's house style.
Had `opens-with-a-bare-id` shipped as proposed, the check would have run at
**zero precision over its entire true-positive set** — ten findings, ten false.
That would have been the third guard-over-English failure here in two days, and
it was avoided by measuring the corpus before writing the check rather than
after.

**So the problem is not degradation. It is absence, and only absence.** The
count that matters is 89, and those rows carry the field because contract 1.11
gave it to them, not because anyone declined to fill it.

## 3. Baseline suite is not green at `a6ca21f`

`python3 tests/parallel -j 4` on the untouched baseline: **110 modules, 3098
tests, 253.0s, exit 1** — one pre-existing failure,
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`,
over dangling `ADR-018` / `ADR-020` references. Unrelated to this row and not
introduced by it. The bar for "no redder than baseline" is therefore **3097 of
3098**, not a green suite.

## 4. What shipped

Three parts, one predicate. `lib.summary_shape` in `bin/lib/__init__.py` is the
**only** definition of what a summary has to be. `bin/perry-task` refuses on it
at write time; `bin/perry-lint` reports on it afterwards. Two copies is how the
tool that refuses and the tool that reports quietly stop agreeing about what
they are for — DESIGN-013's subject — and
`TestOnePlaceDefinesWhatASummaryIs` pins that they answer identically over a
corpus rather than merely importing the same name.

### Part 1 — asking for it. `add` REFUSES; `perry-lint` reports.

**Decision, and it is a hard gate.** `perry-task add` refuses without
`--summary`, exactly as it already refuses without `--deliverable` or
`--verification`. `perry-task summary` holds the same line, so `add`'s refusal
is not one command away from being undone.

`DESIGN-003 § 4` decision 4 — *"advisory first release, hard gate next"* — was
read and does **not** apply. Its stated reason is retroactive invalidation: a
gate on day one would have invalidated every `done` row ever written, since
none carried a rung. **`add` has no retroactive half.** It governs only rows
minted from now on; rows already on the board are untouched by it and are
reported by `perry-lint --summaries` instead. The advisory/hard split therefore
lands on the axis that decision actually cares about — hard where there is no
history, advisory where there is.

The stronger argument is that **the advisory option has already been run on
this exact field, and measured.** `--summary` has been an optional flag on
`add` since contract 1.11: nothing refused it, nothing reported it, no
procedure mentioned it. It reached 25 of 114 open rows. Choosing advisory here
would have been a second run of the experiment that produced the defect.

`--clear` is deliberately **not** gated. A summary that turns out to be wrong
must stay removable, because a confidently wrong summary is worse than an empty
field — the empty field at least tells the reader to go and look. The linter
then reports the row, which is the honest outcome: it is blank, and it is
honestly blank.

### Part 2 — the load-bearing half: the rule lives where an author reads it

A rule that lives only in `subcommands.md` is a rule the next agent does not
know it broke; a rule that lives only in the tool is one nobody reads until it
refuses them. It is now in four places:

- `work/reference/subcommands.md` — `add-task`'s input-quality paragraph names
  the summary check, and a new paragraph says what to write and why, with a
  worked example. Step 1's command block carries `--summary`.
- `reference/input-quality.md § 4.6` — the rubric row, with a note that 4.1,
  4.2 and 4.6 are *also* hard refusals in the tool, and that the tool's half is
  structural only, so a green `add` is not evidence 4.6 passed.
- `schema/task-list-contract.md:134` — the definition now says **who reads it
  and in what language**, the clause whose absence is the whole mechanism (§6).
- `bin/perry-task --help` and `bin/perry-lint --help`.

**Found while editing the procedure, and fixed:** the `add-task` command block
that step 1 tells an agent to copy omitted `--deliverable` and `--verification`
— both hard refusals since well before this row. Pasted verbatim it exits 1.
The documented command did not run, which is one field along from the defect
this row is about.

### Part 3 — the check, and what it does not check

`perry-lint --summaries`, and — following `check_specs`' precedent and its
stated reason, *"a flag nobody types is not a report"* — **the default pass
too**, capped at ten findings with a census line naming the total. `warn` only:
89 blank rows must not turn a project's CI red for a field that was optional
until today.

**CHECKED**, each a fact about bytes:

| rule | what it says |
|---|---|
| `summary-missing` | absent, empty, or whitespace only |
| `summary-repeats-title` | equal to the title after folding case and punctuation, or one contains the other and the difference is under the fragment floor |
| `summary-has-no-sentence` | no sentence terminator anywhere |
| `summary-is-a-fragment` | under five tokens, a CJK character counting as one |

**NOT CHECKED, deliberately** — and this list is in the shipped docstring, not
only here, so widening the check means deleting a stated reason:

- **Whether it opens with a bare id.** The spec proposed this. The corpus
  refutes it: 10 of 49 do and all 10 are good (§2).
- **Whether it contains ids, paths or backticks.** 39 of 49 do. That is a
  summary citing its source.
- **Readability, reading level, vocabulary, hedging, tone.** No test of any
  kind. `TestTheCheckDoesNotJudgeLanguage` asserts that two summaries with
  identical structure and opposite wording get identical verdicts — which is
  what makes the check undefeatable by a synonym, and equally what makes it
  modest. **It does not measure whether a summary is plain language and must
  not be quoted as though it does.**
- **Whether the summary is TRUE of its row.** Nothing structural can.
- **Whether it is shorter than its title.** Considered and rejected: a good
  plain-language gloss of a long shorthand title is often shorter than it,
  which is the outcome this row wants.
- **Closed rows.** 205 of 319. History.

The floor is the one rule that is a proxy rather than a structural fact, and it
is named as such in the docstring. It is set against the corpus: the shortest
genuine summary here is 22 tokens, the floor is 5, and
`test_the_word_floor_has_measured_headroom_over_the_real_corpus` fails if
anybody raises it toward the real population.

## 5. Three defects the suite found in the check itself

None were found by reading. All three would have shipped as a check that is
*wrong* rather than merely modest.

1. **A Chinese summary was refused twice over.** The floor counted
   `str.split()`, which makes `新的稳定说明` exactly **one** word — so any length
   floor refused every Chinese summary ever written. And `summary_fold`
   discarded everything outside ASCII, so every Chinese summary folded to `""`
   — and `"a title".startswith("")` is true, so each one *also* reported as
   repeating its title. Perry declares a document language per project and
   ships zh fixtures, so both were live. A rule that calls itself structural
   while quietly meaning *structural, in English* is the same defect as a
   denylist over English, one layer down. Fold is now `\W` under Unicode;
   length is `summary_tokens`, counting a CJK character as a token.
2. **A bare prefix test made a row titled `"A"` repeat its title with every
   possible summary** — `"a fixture row…"` starts with `"a"`. The rule now
   measures what the summary **adds**: equal after folding, or one contains the
   other and the difference is under the fragment floor. A summary that opens
   by restating its title and then explains for forty words is wordy, not
   defective, and wordiness is a matter of taste this check does not have.
3. **`check_summaries` could kill the whole lint run.** A `status` holding a
   list is unhashable in `in closed`; a non-string `title` reaches `.lower()`;
   and `tasks.jsonl` as a **directory** passes `exists()` and raises on read.
   Every field is coerced and the read is guarded — on a file whose entire
   purpose is to report that the store is malformed.
   `TestOneCheckMayNotKillTheLint` is what caught it.

## 6. The contract: stated, not bumped

`schema/task-list-contract.md` stays at **`perry-task/list/1.18`**, with the
reasoning written into its Changelog against all three of its own rules: rule 2
is untouched (no key added, removed or retyped); `semantics` is for a value
whose *meaning* was corrected and `summary` answers the same question it
answered in 1.11; and this contract governs the READ interface while the change
is a gate on a writing subcommand. The one consumer-visible fact — rows minted
after 2026-09-03 always carry a non-empty `summary` — is a change in the DATA,
not the contract, the same class as a project filing more tasks. Whether that
guarantee should become branchable is a `1.19` with a `semantics` entry, and it
is a decision about the contract rather than about this row; it was
deliberately not taken here.

## 7. Verification

### Coverage

| | before | after |
|---|---|---|
| open rows carrying a summary | 25 of 114 | **99 of 114** |
| open rows blank | 89 | **15** |
| shape findings on rows that carry one | 0 | **0** |

Counted by `TASK-325-census.py`, which shares no code with `bin/perry-lint` on
purpose — if the two ever disagree, that disagreement is the finding. They
agree: 99 / 15 / 0 from both.

### The fifteen left blank, and why

**This is an answer, not an omission.** Writing these would mean reading the
code or the design document, which is re-deriving the row rather than
summarising it — and a confidently wrong summary is worse than an empty field.

| row | why |
|---|---|
| `TASK-112` | title only — "the sign-off drafting guard" is named nowhere in the row |
| `TASK-116` | title only — which "mention list", and which two carve-outs, is not recoverable from the record |
| `TASK-137` | title only — what the first and second queue stages ARE is in the code |
| `TASK-183`, `184`, `185` | D009 steps 3-5 — design-step shorthand, no next action, no spec, no evidence file |
| `TASK-186`, `187`, `188`, `189` | D010 steps 2-5 — same |
| `TASK-190`, `191`, `192`, `193`, `194` | D011 steps 1-5 — same |

The twelve design-step rows are one shape and worth naming as such: a row whose
entire record is `D010 step 3 — a machine-authored spec is fail-closed at the
escalation gate` is legible only to somebody holding DESIGN-010. That is a
finding about how those rows were filed, and the fix is upstream of this row.

### The check fires on a real row, and is silent on one

No row on this board is structurally a second title (§2), so the firing
direction was demonstrated by **reproducing the state on a real row with the
baseline tool**, on a `git archive` copy of `a6ca21f` in scratch:

1. Baseline `perry-task summary TASK-217 --summary "<TASK-217's own title>"` →
   **accepted, rc 0.** The state was reachable before this change.
2. New `perry-lint --summaries` on that copy → **fires on TASK-217**, with
   `summary-repeats-title` and `summary-has-no-sentence`.
3. New `perry-task summary`, same command, pristine copy → **refused.**
4. **Silence control:** on the pristine copy, TASK-217's genuine summary
   produces no finding, and neither do the other 24 — `0 shape finding(s)`
   across every row that carries one.

### Mutations — 11 planted, 11 red, 0 green

Harness at `TASK-325-mutations.py`. It anchors on old text and refuses a stale
anchor rather than no-opping (three anchors went stale during hardening and
were reported, not silently skipped); clears `__pycache__`; crosses the
whole-second boundary; restores from bytes snapshotted **before** each
mutation; and verifies the restore against `git show HEAD:<path>` — an
independent witness, not the bytes it just wrote, which is the circularity
`TASK-256` records.

| | mutation | test that went red |
|---|---|---|
| M1 | `summary-missing` never fires | `test_it_fires_on_a_blank_row_and_names_it` |
| M2 | `summary-repeats-title` removed | `test_add_refuses_a_summary_that_is_only_the_title_again` |
| M3 | `summary-has-no-sentence` removed | `test_add_refuses_a_fragment_and_a_value_with_no_sentence` |
| M4 | fragment floor removed | same |
| M5 | `add`'s required-summary refusal removed | `test_add_refuses_when_summary_is_absent` |
| M6 | `add`'s shape refusal removed | `test_add_refuses_a_summary_that_is_only_the_title_again` |
| M7 | rewrite writer's shape gate removed | `test_summary_refuses_a_second_title` |
| M8 | check dropped from the DEFAULT pass | `test_the_default_pass_reports_it_without_being_asked` |
| M9 | closed rows scanned too | `test_closed_rows_are_not_scanned` |
| M10 | findings promoted to `error` | `test_it_stays_advisory_and_never_makes_the_run_red` |
| M11 | **control** — check flags every summary | `test_it_is_silent_on_a_good_summary` |

M11 matters most: a check that flags everything satisfies M1-M10 and is
useless.

### `perry-explain` on three previously-blank rows

```
TASK-206  —  a write returns no seq, so a poll cannot tell a stale read from a fresh one
  summary    A Perry write returns no sequence number. So a consumer that polls has no
             way to tell whether what it just read already reflects its own write or
             predates it, and a stale read is indistinguishable from a fresh one.

TASK-294  —  every NS-01 warning Perry emits is about a file Perry itself wrote, and
             the remedy each one offers is a no-op
  summary    Every namespace-collision warning Perry emits is about a file Perry itself
             wrote, and the remedy each one offers is a no-op — the warnings say 'move
             Perry's state to its own root' and the state root already IS that root.
             One of the five is a separate bug: a FILE claim whose warning tells the
             reader to move files out of a file. This is why every lint run reported
             warnings that every session skipped as pre-existing; a check that only
             ever cries wolf gets trained out of the reader.

TASK-309  —  a dispatched agent's entire round lives in its context until one final
             commit, so any interruption costs all of it
  summary    Nothing a dispatched agent does reaches disk until its single terminal
             commit, so an interruption at any point before that costs the whole round.
             Measured on 2026-09-02: five agents were dispatched, the laptop was closed,
             all five died at the watchdog and git log across all five branches shows
             zero commits. Between fifteen and thirty minutes of work each, and the only
             surviving trace was the last sentence each had streamed. …
```

**The subjective half is not settled here.** The spec says so itself: whether
these read as plain language to the user is for a human, and this agent cannot
score it on itself.

### The check caught its own author

Four of the 74 drafted summaries opened by restating the title verbatim and
were refused as `summary-repeats-title`. All four were rewritten to lead with
the explanation. Under the later prefix fix (§5.2) those four would no longer
be refused — they add forty-plus words — and the rewrites were kept anyway,
because leading with the title verbatim is still poor prose where it is not a
defect the tool should refuse.

### Write location

Writes landed in this worktree and not the primary checkout. The census reports
`.../worktrees/agent-a5396aeb60307b5e7/perry/tasks.jsonl`; distinctive strings
from the backfill are present there and **absent** from
`/Users/bytedance/proj/Perry/perry/tasks.jsonl`. That primary store *is* dirty
relative to its own branch tip — a different session working on `TASK-323` —
which is exactly why the check was done by content rather than by mtime.

### Suite and lint

- `perry-lint --root .` → **0 errors**, `summaries: 99 of 114 open row(s) carry
  one · 15 blank · 0 shape finding(s)`.
- Suite fallout of the hard gate was real and is worth stating plainly: **130
  failures across 21 modules**, taken to zero. 35 inline `add` call sites gained
  `--summary`; both `Project` harnesses inject a default; `TASK-106`'s
  placeholder summaries were lengthened; its `SUMMARY-SENTINEL` is now a
  sentence *containing* that token; and its `summary=None` case adds-then-clears,
  since `--clear` is deliberately still open while minting a blank row is not.
- `test_store_drift`'s stray-file assertion now filters by **rule**: filtering on
  the filename was exact only while one check ever named `tasks.jsonl`.
- The new module is registered in `tests/durations.json` as `never-measured` —
  the declared value for "nobody has measured this yet" — rather than given a
  fabricated number.
