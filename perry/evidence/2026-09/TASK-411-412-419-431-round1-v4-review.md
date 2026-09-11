# TASK-411, TASK-412, TASK-419, TASK-431 — round 1, V4

> Reviewer: fresh context. Did not write any of this code.
> Branch: `v4-round-411-412-419-431`, from `main` at `076ae21a`.
> Worktree: `.claude/worktrees/agent-a4cba585579eac7c4`
> Scratch: `/private/tmp/claude-501/-Users-bytedance-proj-Perry/b59246e8-0d9c-4c63-9ac3-03f73fedf40b/scratchpad/v4quad-411-412-419-431/`
> (agent-suffixed path nobody else would pick; a full `git clone` of the
> worktree lives under it as `clone/` and every destructive check runs there,
> `review-constraints.md § You are a reader`)
> Written incrementally and committed as each section was measured.

All four rows are the same question — **a guard was added; does it bite?** —
and that is the question this document answers, four times.

## 0 · Baseline, taken in this tree before anything else

`bash tests/run` at `076ae21a`, no edits in the tree, `git status` clean:

```
126 modules · 3655 tests · 165.8s · 8 workers
✗ 4 tests failed
    test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable
        .test_without_the_witness_the_four_are_unobservable
    test_contract_key_parity.TestTheWitnessedKeysRedden
        .test_the_same_mutation_is_silent_without_the_witness
    test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
    test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale
0. tree guard — nothing under the worktree moved
```

**All four of the declared known reds fired here**, including
`test_diagnose`'s, which TASK-412's and TASK-431's results both record as
*green* in their trees. That difference is explained and is not a finding for
either row: the diagnose red is `user_load.dangling ==
['USER-920', 'V4-1', 'V4-2', 'V4-3']`, and the three `V4-N` tokens are minted
identifiers in `perry/evidence/2026-08/TASK-027-round4-review.md` and
`-round5-`, which are on `main` and were not on either agent's branch base.
They belong to TASK-436's territory, not to any row in this round.

So the bar for "this reviewer broke nothing" is: exactly these four.

### How every mutation below was run

`…/scratchpad/v4quad-411-412-419-431/mutate.py`, against the **clone**, never
this worktree. It anchors by line number *and* a substring that must occur
exactly once on that line, refusing rather than mutating otherwise; clears
`__pycache__` and sleeps 1.2 s past the whole-second boundary either side;
restores by writing back the bytes of `git show HEAD:<path>` — not the bytes it
snapshotted; and verifies with `bin/perry-restore-check`. It also refuses to
start if the file already differs from the ref, so a corrupted baseline cannot
be restored onto and reported OK. **Every mutation below ended
`restore-check rc=0`.**

## 1 · TASK-412 — the page's own block is what the tests run now

### 1.1 · The repair is real, verified rather than believed

The result says its first mutation round came back green on two cases because
they recomputed `pair(a) > pair(b)` in the test instead of executing the page,
and that `commit d6b91201` repaired it with a `drive()` helper. **Verified at
the source, not from the claim.** `tests/test_contract_page_snippets.py:315`
`drive()` builds a synthetic payload, `exec`s
`compile(snippet(), …)` — where `snippet()` is the page's fenced text, read off
disk — and returns the block's own namespace together with whatever the block
actually passed to `warn`. Both repaired cases go through it, and
`test_the_drift_gate_is_a_ceiling_per_major_over_the_forward_space` asserts on
`ns["tested"]`, a value that exists only inside the block.

Then mutated. Seven, applied one at a time to the **page**, each reddening a
named test. Three are the result's own (a, c, d); **four are mine and none of
them appears in its table** (b, e, f, g):

| # | line | mutation | result |
|---|---|---|---|
| a | `:592` | the string compare restored at the call site — the exact case that was green in the first round | **RED** `test_the_filter_warns_about_exactly_the_entries_newer_than_the_pin`: `['1.2'…'1.9','2.0'] != ['2.0']` |
| **b** *(mine)* | `:592` | `> tested` → `>= tested`, an off-by-one nobody restored | **RED** same test, twice — `['1.18','2.0'] != ['2.0']` at pin 1.18 and `['2.0'] != []` at pin 2.0 |
| c | `:589` | the ceiling back across majors, `max(SUPPORTED.values())` | **RED** 6 failures, `(2,18) != (2,0)` |
| d | `:592` | `TESTED_MINOR_STR` restored — the name bound nowhere | **RED** 2 failures + 12 errors; `test_it_references_no_name_the_page_does_not_supply` names it directly |
| **e** *(mine)* | `:830` | the marker's *reason* changed to `I do not want to run it` | **RED** `test_a_marker_cannot_hide_a_broken_block`: *"gives a reason this module does not know how to check"* |
| **f** *(mine)* | `:111` | the payload block types `open` as `"3"` instead of `3` | **RED** `test_the_jsonc_blocks_describe_the_live_payload`: *"types `open` as str; the payload returns int"* |
| **g** *(mine)* | `:663` | a **seventh** fenced block inserted into live prose, carrying a marker the module does know | **RED** ×3 — the bounded count (`7 != 6`), the indent-aware-vs-naive case (`6 != 5`), *and* the no-runner-no-marker case, because the marker's position test correctly refused to excuse a block above `## Changelog` |

Mutation **b** is the one worth keeping: an off-by-one at the call site is what
a later author edits into this block, it is not in the result's table, and the
guard caught it in both directions. Mutation **e** is the answer to the
question the result invites — the `not-executable` reason is an *enumerated*
allowlist checked against the block's own position, not a string anybody can
write. Mutation **g** shows the count is a real bound and not decoration.

### 1.2 · What I could not shake

- The three green-by-construction cases the result names are exactly the three
  I found: `test_the_string_compare_is_wrong_on_this_very_space` is a
  description and says so in its own docstring; it stayed green under mutation
  a, as its docstring predicts. **An ungrudged green that announces itself is
  not a finding** — it is the honest label § 2 rule 2 asks for.
- 20 tests in the module, 20 green at `HEAD` in the clone before every
  mutation and after every restore.

### 1.3 · One finding, and it is not TASK-412's

`bin/perry-restore-check --root DIR` does **not** resolve a relative `<path>`
against `DIR`. It resolves it against the process cwd and then refuses,
printing *"The restore did NOT put the file back"* for a file that was in fact
correctly restored:

```
$ cd <scratch> && perry-restore-check --root <scratch>/clone HEAD schema/task-list-contract.md
The restore did NOT put the file back. Do not report this round's result until it does.
  ✗ <scratch>/schema/task-list-contract.md: … is not under <scratch>/clone
rc=1
```

Its own `--help` says `--root DIR  repository to resolve <path> and <ref>
against`. The wrong answer is **loud** — exit 1, and the message names both
paths — and it errs toward "your restore failed", which is the safe direction,
so by § 0 it fails no row. It is out of scope for all four rows here; I hit it
because `review-constraints.md` recommends exactly this invocation to a
reviewer working from a copy. Reported, not filed (see § 5).

## 2 · TASK-419 — the counter, and the page it changed under me

### 2.1 · The page that governs this round, read as a diff

`git diff b5b7d023^1 b5b7d023 -- work/reference/review.md` is **purely
additive**: one new `### grade:` subsection inside § 3 and one paragraph in
§ 6. No existing sentence is edited, no required key is added or removed, and
`VERDICT_KEYS` in `bin/perry-lint` is byte-identical — so every verdict block
already on disk, and the four at the end of this document, are shaped exactly
as they were before the row landed. **The row changed the page that judges me
and did not move the bar it judges me by.** That is the honest way to do it,
and it is what the spec demanded ("changing § 3 is part of this row and must be
argued, not slipped in").

### 2.2 · The corpus census, re-derived rather than read

Independently, with the linter's own `parse_verdicts` over every `*.md` under
`perry/evidence/`, in the clone at `076ae21a`:

```
blocks 112 · PASS 47 · FAIL 62 · neither 3 · carrying a `grade:` 0
```

The result claims 111 / 46 / 62 / 3 at its base `70458893`; the extra block is
one PASS that landed between its base and `main`, and **the two numbers this
row rests on — 62 FAILs and 0 regradeable — are exactly right.** The "0 of 62"
is not an estimate: no block in the corpus carries the key at all.

`--reviews --json` on the live corpus today reports `review-rounds-exhausted`
on **one** row, and its message carries the aside the row promised:

> … 2 of the 2 counted carry no readable `grade:`, so the criterion they were
> charged against is undeterminable and they count by default
> (work/reference/review.md § 3).

The row it fires on is not the one the result names as its second, and that is
the result's own prediction coming true rather than a discrepancy: § 3 of the
result says TASK-362's finding "has a fuse in it" and goes silent the moment
its round-11 PASS merges. It has merged. **A round that predicted its own
measurement would decay, said so, and refused to pin a test to it is the
behaviour this page wants**, and it is why nothing here is red.

### 2.3 · The "provably equivalent mutant" — the claim is true

M10 swaps

```python
undeterminable = [b for b in charged if fail_grade(b[1]) is None]
#                          ^^^^^^^                      for  ^^^^^
undeterminable = [b for b in fails   if fail_grade(b[1]) is None]
```

**Proof, checked rather than accepted.** `charged = [b for b in fails if
fail_grade(b[1]) != "ROW"]`, so `fails \ charged` is exactly the blocks whose
`fail_grade` is the string `"ROW"`; `"ROW" is None` is false, so no block in
that difference can pass the filter. `fail_grade` is pure — it reads one key
and matches one regex — so the two comprehensions denote the same list, in the
same order, for every input.

Then measured anyway, because a proof about code is a claim about the code you
think is there. 19 grade spellings (`None`, `""`, `ROW`, `row`, `rOw`, `ROW.`,
`ROW,x`, `**ROW**`, `ROWS`, `row-grade`, `2b`, `PASS`, `FAILS`, `FAIL`,
`fail - c3`, `ROW - criterion 2b`, `  ROW  `, `Row - x`, `ROW—c`), every
combination at lengths 1–3, **7,239 cases, 0 differing.** Script:
`…/scratchpad/v4quad-411-412-419-431/m10.py`.

**The claim stands, and declaring it beat writing a test for it.** § 2 rule 2
says a green mutation is a finding either way; this is the third answer, and
the row is right that a test written to kill M10 would be asserting something
untrue. What makes it defensible is the part next to it: the row found that the
*denominator* standing beside the equivalent expression was **not** equivalent
and had nothing holding it, and added a test. A round that had stopped at "M10
is equivalent" would have missed that.

### 2.4 · Mutations — three, all red, two of them mine

| # | line | mutation | result |
|---|---|---|---|
| a | `perry-lint:3005` | the revert — `charged = list(fails)`, count blocks again | **RED**, 6 tests, incl. `test_two_ROW_grade_fails_do_not_exhaust_the_row` and `test_the_undeterminable_denominator_is_the_counted_rounds` |
| **b** *(mine)* | `perry-lint:3008` | `if len(charged) < limit` → `<= limit` — the threshold silently raised from 2 to 3, which is the row's first "must not" | **RED**, 8 failures + 7 errors, incl. `test_two_fails_and_no_pass_is_reported` and all three ask-clearing cases |
| **c** *(mine)* | `perry-lint:2320` | `fail_grade` returns `"ROW"` instead of `None` for a token it cannot read — an unreadable grade quiets the guard, the one direction the row may not move | **RED** `test_a_grade_that_is_neither_word_counts`, `test_fail_grade_returns_None_for_everything_it_cannot_read` |

Mutation **b** is the one I most expected to survive, because the threshold is
read from three places and a boundary shift is the classic silent one. It did
not survive; the row's existing cases pin the boundary.

### 2.5 · Two ways the guard can be turned off, both real, neither fatal

Probed directly through `parse_verdicts` + `fail_grade`
(`…/scratchpad/v4quad-411-412-419-431/grade_probe.py`):

**(i) A bare `grade: ROW`, with no criterion beside it, is accepted and
counts as filed.** § 3 says in bold: *"The rest of the line is the criterion,
and it is not optional prose — a grade with no criterion beside it is a claim
with nothing to check it against."* Nothing implements that sentence. This is
the repository's signature defect — a rule stated in prose that nothing
implements — landing in the same commit that names it. **It is mitigated by
being declared**: the same sentence assigns the check to "the next reviewer",
so the enforcement mechanism is stated rather than assumed. Reported, not
fatal; a one-line `if not the rest of the line: verdict-malformed` would close
it, and would cost nobody anything, since the corpus has zero graded blocks.

**(ii) A continuation line that begins `grade:` is silently promoted to the
`grade` field, and eats the rest of the line it was continuing.** Given

```
not-checked: whether the round should have written a
    grade: ROW would have been my instinct but I did not decide
```

`parse_verdicts` returns `grade='ROW would have been my instinct…'`,
`fail_grade` reads `ROW`, the block stops counting toward
`review-rounds-exhausted`, **and `not-checked` is truncated to "whether the
round should have written a"**. No `verdict-malformed` fires, because `ROW` is
perfectly readable.

The promotion itself is `parse_verdicts`' pre-existing behaviour — it applies
to every key and predates this row by a long way — and the row did not touch
it. What this row changed is the *consequence*: before TASK-419, an accidental
key promotion corrupted a field a human reads; after it, one can silently
switch off a gate. The trigger is a reviewer writing an indented sentence that
starts with the word `grade` and a colon, inside their own verdict block, on a
row that already has two FAILs. That is an input a user can produce, and it is
not one anybody will produce often.

Both go in § 5 as reports. Neither fails the row: the row's deliverable — the
counter reads the criterion, silence counts, and the finding says how many it
could not determine — is intact under every mutation I could aim at it.

## 3 · TASK-431 — the repair, and where the fourth-list guard stops

### 3.1 · The repair at `3ae5fbfc` is sound, and I checked the failure it had

The first attempt left the loop body after a `continue`, unreachable, and the
test passed in 0.018 s checking nothing. **That is the failure mode I checked
for first, and by mutation rather than by reading the indentation.** The
repaired `test_it_is_not_declared_and_nothing_writes_it` was driven with the
dropped pair planted three ways, each alone, each removed afterwards, all in
the clone:

| plant | guard |
|---|---|
| a **tracked** file, real characters (`INSTALL.md:3`, via the line-anchored harness) | **RED** — `[] != ['INSTALL.md']` |
| a **tracked** file, real characters (`bin/lib/__init__.py`, appended) | **RED** — `[] != ['bin/lib/__init__.py']` |
| an **untracked** file under `bin/`, real characters | green — *this is the re-scope working as intended* |
| a **tracked** `.py` file spelling the pair as `"—/—"` | green — **not one of the three mutations the repair commit names** |

The loop body is reachable and the guard bites. The `git ls-files` domain is
the right call and I agree with the reasoning in the commit message: a
hand-written skip list would have needed the next untracked directory
remembered.

The `\u`-escape row is a real gap and a very small one. The guard is a textual
`in` over file contents, so a Python file that writes the pair with escapes is
invisible. `—/—` is undeclared, `grep` finds nothing in the tree that writes
it in any spelling, and the escaped form is not something anybody writes by
accident. Named here so the next round does not have to find it.

### 3.2 · The substantive fixes — three mutations, all red, all mine to run

| # | site | mutation | result |
|---|---|---|---|
| c | `bin/perry-state:331` | `split_stages` back to `if not cell or cell == "—"` | **RED** ×2 — `test_blankness_is_tested_before_separator_normalisation` *and* `test_no_site_decides_blankness_for_itself`, which reports the reborn site by name: `{('bin/perry-state','split_stages',('—',)): 1}` |
| d | `bin/perry-state:620` | `missing_defaults` back to its own 7-element literal | **RED**, 17 failures; the sweep names it: `('bin/perry-state','missing_defaults',('-','n/a','tbd','–','—'))` |
| **e** *(mine)* | `bin/lib/__init__.py:266` | `_blank_key` stops normalising the typed cell, so decorated forms (`~n/a~`, `**—**`) stop reducing | **RED**, 28 failures, incl. `test_a_blank_marker_followed_by_a_date_still_yields_none` — *"a `Due` cell reading `~n/a~` before a date reported that date as due"* |

Mutation **e** is the one I added because it attacks the *one rule* rather
than a caller, and it is the shape that would make every one of the nine
converted sites quietly wrong at once. Twenty-eight tests across the viewer and
the `bin/` halves caught it.

The reported consequence is gone, re-derived here rather than read:
`tests/repro_blank_stages.py` in the clone prints
`0 of 20 blank spellings were read as a DECLARED stage list`, and
`stages_declared` is `False` for every one. (The result's prose says *"0 of
21"*; the script on `main` enumerates 20. An off-by-one in an evidence file,
§ 0's "false statement in something nobody executes" — noted, not a FAIL.)

### 3.3 · Finding — the fourth-list guard has a shape-shaped hole

**This is the one mutation in the whole round that came back green where I
did not expect it**, and § 2 rule 2 says a green mutation is a finding either
way.

Ten shapes of "a fourth hardcoded blank-cell list", each appended alone to a
tracked file under `bin/`, restored from `git show HEAD:<path>` and verified
(`…/scratchpad/v4quad-411-412-419-431/plant_list.py`):

| shape | guard |
|---|---|
| `cell in {"", "—", "n/a", "tbd"}` inline | **RED** |
| `_B = {...}` at module level, read elsewhere | **RED** |
| `_B = ("", "—", "n/a", "tbd")` tuple, read elsewhere | **RED** |
| `_B = {"": 1, "—": 1, …}`, read as dict keys | **RED** |
| `cell == "" or cell == "—" or cell == "n/a"` — no container at all | **RED** |
| `cell in frozenset({"", "—", "n/a", "tbd"})` | **GREEN** |
| `_B = frozenset({...})` at module level, read elsewhere | **GREEN** |
| `_B = set([...])` at module level, read elsewhere | **GREEN** |
| `cell.startswith(("—", "n/a", "tbd"))` | green — prefix, a category the row exempts by argument |
| built at runtime with `.add()` | green — **declared** in the result's § 10.2 |

The mechanism: the sweep classifies a literal by climbing the parent chain to
an `ast.Compare`, and **a `Call` node ends the climb**. So `frozenset({…})`
and `set([…])` — the two most ordinary ways to spell an immutable module-level
constant — hide the identical set from a guard whose docstring says *"a list is
a literal"*. That sentence is what the exemption for the residual rests on, and
these are literals.

I checked whether this is a *missed site* or a *latent hole*, because those are
different findings. **Latent.** An AST sweep for blank-cell literals whose
climb reaches a `Call` first returns 115 occurrences in `bin/` + `viewer/`
today and **0 of them are wrapped in a container constructor** — they are
`.replace`, `.split`, `.join`, `.startswith`, f-strings and `print`, i.e. the
WRITE direction the row already classified. The codebase's own idiom for a set
is a bare literal, which the guard catches. Script:
`…/scratchpad/v4quad-411-412-419-431/call_wrapped.py`.

**Why this is reported and does not fail the row.** It does not corrupt state,
no tool answers wrongly today, and the gate is strictly stronger than the
nothing that stood there before. § 1 of `review.md` is also explicit that *"the
guard cannot be evaded"* is not a bounded criterion and that a further evasion
shape is a new row rather than this one — and the spec's Verification 5 asked
for exactly one thing, *"add a new hardcoded list somewhere in `bin/` and show
the sweep test find it"*, which is discharged. The honest statement is: **the
guard bites on every shape this codebase actually writes, and misses two it
does not.** Closing it is one `isinstance(cur, ast.Call)` → keep climbing when
the callee is `set`/`frozenset`/`tuple`/`list`/`dict`.

One consequence worth naming, because it is the hole already concealing
something: `bin/lib/__init__.py:286` carries
`_BLANK_CELLS.update(_blank_key(v) for v in {"—", "-", "–", "n/a", "none",
"无"})` — a **six-spelling hardcoded list inside the one rule itself**, the
degraded-mode default for an unreadable schema. It is commented, deliberate,
and correct. It is also invisible to the sweep for exactly the reason above,
so the row's "every container is now accounted for" was measured by an
instrument that cannot see it.

### 3.4 · Finding — the guard writes the live checkout, on a machine running 8 workers

`tests/test_blank_cell_is_one_rule.py:266
test_the_sweep_can_see_a_fourth_list_when_one_is_added` proves the guard bites
by writing `MY_OWN_BLANKS = {…}` into **`bin/perry-context-budget` in the tree
the suite is running in**, running the sweep, and restoring in a `finally`.

`review-constraints.md § You are a reader` has a paragraph about precisely
this, learned the hard way: *"for the seconds it exists, the shared checkout
has a file that makes that guard legitimately red, and anything else running
the suite — the author's own gate, another reviewer — sees a failure that is
real, reproducible-looking, and about nothing."* That page addresses reviewers;
this is a test. But `tests/parallel` runs **8 workers over one tree**, step 3 of
`tests/run` compiles every script under `bin/` and asks it for `--help`, and
TASK-411's own new `tests/surface_reads.py` parses every file in `bin/` —
including `bin/perry-context-budget`. There is a window in which another worker
reads a planted file. The `finally` also does not run if the process is killed,
and this machine has other agents on it.

I did **not** reproduce an interference failure; I am reporting the window, not
a red I saw. The fix is the one the row already used everywhere else: plant
into a copy. The sweep is parameterised on `PERRY_HOME`, so the test can
`git archive` or copy `bin/` to a temp dir and point the sweep at it.

### 3.5 · What held

- 40 tests in the module, green before and after every mutation.
- `SWEEP.read_sites()` returns 9 sites on `main`, and all 9 are in `EXEMPT`
  with a written reason. `test_the_exemptions_are_all_still_real` guards the
  other direction, which is the part most allowlists omit.
- The `EXEMPT` allowlist is keyed by `(file, function, spellings)` and **not by
  line number** — the row was bitten by `test_handed_back_root`'s line-keyed
  exemption and did not reproduce that mistake in its own guard. That is the
  detail that most persuaded me the round understood what it had found.

## 4 · TASK-411 — no criteria file, and what could still be checked

### 4.1 · § 1, stated first because it bounds everything below

**There is no `TASK-411-spec.md`.** `find perry -name '*411*'` returns the
result and this review, and nothing else. `review.md § 1` refuses a round
without written criteria for a stated reason — *"a fresh reviewer with no
written criteria invents its own bar"* — and the result itself records the
adjacent gap: it was written by the PMO from a transcript, after the row moved
to review, because the agent produced tests and no document.

I cannot repair this from inside the round: criteria written after the fact are
*"a negotiation with the result"*, and I am not the author. So I did the only
thing left that is honest — **I judged against the result document's own
falsifiable claims, treating them as the bar, and I am saying so here rather
than presenting an inferred bar as a criteria file.** The verdict block's
`criteria:` names the result for that reason, and its `not-checked:` says it.
That this row got a V4 with no criteria is a § 1 pre-check finding for the PMO,
not a defect in the code.

### 4.2 · The three headline numbers, re-derived in the clone

| claim | re-derived | agrees |
|---|---|---|
| 149 pairs in the universe, 63 called read, **42.3%** | 149 / 63 / 42.3% | yes |
| the 15 blind pairs are `--register` on twelve prefixed verbs + `--write` on three `*-diff` verbs | exactly those 15, enumerated from the derived table | yes |
| the negative space: **1,279 probes, 1,279 refused, 0 accepted** | 1,279 probes, 0 accepted, over `perry-config`, `perry-okr`, `perry-task`, `perry-tasks` | yes |

### 4.3 · "0 false positives", falsified rather than re-read

The result says the 63 were *"audited against source"*. A human audit is not
something a second human audit checks, so I built an independent falsifier
(`…/scratchpad/v4quad-411-412-419-431/fp_probe.py`). A claimed read means the
flag's spelling can reach code the subcommand runs, so a **necessary**
condition is that the spelling is in the chain file at all: for each claimed
`(tool, flag)` group, the chain file is copied with that flag's literal
replaced everywhere by a spelling nothing uses, the reader is re-run, and the
pair must be gone.

```
claimed (tool, flag) groups: 17
  probed by literal removal: 10   -> pairs surviving their own literal's removal: 0
  no literal to remove:       7
```

**My first run reported seven false positives and my probe was what was
wrong.** The seven are `perry-config track`'s `--cycle --default-rung --mode
--sla --spine --stages --wip`, and `bin/perry-config:39` mints them:
`TRACK_FLAGS = {f"--{f.replace('_','-')}": f …}`. They are never spelled as
literals anywhere, so there is nothing to remove and the probe says nothing
about them. They are separated out above rather than counted. Audited by hand
instead: `bin/perry-config:293` `track_values = {TRACK_FLAGS[f]: v for f, v in
read["values"].items() if f in TRACK_FLAGS}` sits in `cmd_track` and nowhere
else — a true read, and exclusively `track`'s.

**So: 56 of the 63 falsified by mechanism, 7 audited by hand, 0 false
positives.** I agree with the number.

The two documented over-report traps were asked directly rather than assumed
(`…/traps.py`), because they are where a lazier reader would be wrong:

```
perry-tasks  diff   --write   in reads? False     <- lazy argument binding holds
perry-config show   --dry-run in reads? False     <- the prologue does not leak
```

### 4.4 · Mutations — three, all red, one mine

| # | target | mutation | result |
|---|---|---|---|
| a | `bin/perry-config:245` | `show` declares `--dry-run`, which no branch of `show` reads | **RED** direction B: `['--dry-run'] != []` |
| b | `bin/perry_md_store.py:1246` | `render` drops `--write` from its declaration while still reading it | **RED** direction A: `['--write'] != []`, *and* the blind-pair case names it as direction A's failure rather than its own |
| **c** *(mine)* | `tests/surface_reads.py:312` | **the reader itself**: `body_active = active if sel is None else (active & sel)` → `body_active = active`, so branch narrowing stops narrowing | **RED** ×2 — `test_the_derivation_finds_what_the_source_plainly_reads` (*"every flag came back read for every subcommand"*) and the ratchet: *"direction B is now blind on 60 pairs, up from the 15 measured"* |

Mutation **c** is the one I cared about, because a guard whose *derivation*
can rot into a vacuous "yes" makes direction B pass forever while measuring
nothing, and that is the shape DESIGN-016 was opened on. It is held from two
independent sides: a positive/negative pair of literal assertions, and the
blind-pair ceiling. The ceiling is the better of the two — it noticed 60
without being told what 60 would look like.

### 4.5 · Finding — the blind-pair argument is a generalisation from one probe

`tests/test_bin_surface.py:537`, in the docstring that carries the whole
argument for the 15-pair hole:

> "**None of the fifteen is § 1.4's defect, and that is checkable rather than
> asserted.** The blind pairs are exactly the ones where the tool does consult
> the flag, so declaring one gets it honoured or refused out loud — not
> accepted and dropped. Probed 2026-09-11: `--register` added to
> `risks-build`'s declaration …"

One probe, on one of the two kinds, and the conclusion is stated over all
fifteen. **I probed the other kind and it does not hold.** The same docstring
already names the mechanism two lines above — `--write` on the `*-diff` verbs
is read *"in its storeless branch before it looks at `byte_compare`"* — and the
storeless branch is one of two paths.

Measured, on a throwaway project copy with a valid one-row `risks.jsonl`
(`…/blind15.py`, `…/blind15b.py`, `…/blind15c.py`; `bin/perry-tasks` restored
from `git show HEAD:` and verified after every run):

| state | `perry-tasks risks-diff --write`, with `--write` declared |
|---|---|
| **no risks store** | rc 2, a JSON refusal on stderr naming the store and why. **Honoured loudly** — the claim holds |
| **valid risks store present** | **rc 0, stdout byte-identical to `risks-diff` without the flag, no file on disk changed.** Accepted and silently dropped |

`bin/perry-tasks:513` is the line: `if not byte_compare:` guards the only
remaining `write_board` read, and `byte_compare` is `cmd == "risks-diff"`, so
for a `*-diff` verb with a store present the flag is consulted by nothing.

**What this does and does not mean.** No user can hit it today: `--write` is
not declared on any `*-diff` verb, and the parser's refusal is unusually good —
`"--write is not accepted by 'risks-diff', and 'risks-diff' would have ignored
it."` What is wrong is the *justification* for the guard's declared hole: three
of the fifteen blind pairs are pairs where adding the declaration would produce
exactly the accepted-and-silently-dropped defect the whole design exists to
end, and the guard would stay green.

§ 2's table sends this to a row rather than a FAIL — *"a comment … misstates
something → file a row, never a FAIL on this one"* — and the guard's executable
part is honest: it measures the blind spot, caps it at 15, and my vacuity
mutation proved the cap bites. The remainder is measured and listed, which
`§ 1`'s TASK-050 precedent says discharges. **The sentence is what needs
correcting, and a fourth blind pair of this kind would be a new row.**

### 4.6 · What held

- 59 tests in `test_bin_surface.py`, green at `HEAD` before and after every
  mutation and after every restore.
- `INDIRECT` is empty and `test_the_escape_hatch_is_empty` asserts the
  emptiness rather than looping over it — the right shape, because a loop over
  an empty dict passes as entries arrive.
- The negative-space census has an anti-vacuity control beside it
  (`test_the_control_is_that_the_flag_works_where_it_is_declared`) and a floor
  on the probe count, so "0 accepted" cannot be bought by refusing everything
  or by probing three pairs.
- The result **corrected the row's own claim** about the suite being at
  baseline for the `perry-config track` / `--wip` case. A round that contradicts
  its own row is a round that measured.

## 5 · Every finding, graded against § 0 — and none of them meets the bar

**I am not filing any of these.** The round was told not to open rows, and this
project is not opening them by default; below is what I found, what I think it
is worth, and the decision is the PMO's.

§ 0's bar, applied to each: *does it destroy unrecoverable state, make a tool
report a wrong answer nobody can detect, or weaken a gate standing between a
user and either of those?* **Nine findings, and my answer is no to all nine.**
That is not a soft answer — it is the one the measurements support, and each
line says what would change it.

| # | row | finding | § 0 | would change my mind |
|---|---|---|---|---|
| 1 | 431 | `frozenset({…})` / `set([…])` hide a fourth blank-cell list from the guard; the climb stops at a `Call` | **no** — latent; 0 of 115 call-wrapped literals in the tree are container constructors, and the codebase's own idiom is a bare literal | one such site existing today. I looked; there is none |
| 2 | 419 | a `checked:`/`not-checked:` continuation line beginning `grade:` is promoted to the field, silently switching off `review-rounds-exhausted` **and** truncating the line it continued | **no** — needs a reviewer to write one specific indented sentence on their own two-FAIL row | a corpus block where it has already happened. There is none: 0 of 112 carry a `grade:` |
| 3 | 411 | *"None of the fifteen is § 1.4's defect"* is generalised from one probe; with a risks store present, a declared `--write` on a `*-diff` verb exits 0 and silently writes nothing | **no** — § 2's table sends a misstatement to a row, and no `*-diff` verb declares `--write` | `--write` appearing in a `*-diff` declaration |
| 4 | 431 | the fourth-list guard proves itself by **writing `bin/perry-context-budget` in the live checkout**, while `tests/parallel` runs 8 workers over that one tree and other agents share the machine | **no** — a flakiness and shared-tree risk, not a product answer. I did not reproduce an interference red | an observed red in another module during a parallel run |
| 5 | 419 | § 3 says in bold that the criterion beside a `grade:` *"is not optional prose"*, and nothing implements it: a bare `grade: ROW` quiets the guard | **no** — the same sentence names the enforcement mechanism (the next reviewer), so it is declared rather than assumed | making it required; it would cost nothing today |
| 6 | — | `bin/perry-restore-check --root DIR` resolves a relative `<path>` against the **cwd**, not `DIR`, then prints *"The restore did NOT put the file back"* for a file that was restored. Its `--help` says otherwise | **no** — loud, and wrong in the safe direction | it ever answering "restore OK" wrongly. It cannot; it refuses instead |
| 7 | 411 | **no criteria file exists for the row at all** (`find perry -name '*411*'` returns the result and this review) | not a code defect — `review.md § 1`, a pre-check that should have stopped the dispatch | — |
| 8 | 431 | `bin/lib/__init__.py:286` carries a six-spelling hardcoded fallback set inside `is_blank_cell` itself, invisible to the sweep for finding 1's reason | **no** — deliberate, commented, correct: the degraded mode for an unreadable schema | it drifting from the schema's list without anything noticing |
| 9 | 431, 412 | two evidence-file numbers: the result says *"0 of 21"* where the script on `main` enumerates 20; the dropped-pair guard is textual, so a `"—/—"` spelling evades it | **no** — § 0's *"a false statement in something nobody executes"* | — |

**If the PMO files only two, I would file 1 and 4**, both on TASK-431: the
first because closing it is one `isinstance(cur, ast.Call)` clause and the
guard is the row's whole forward-looking value, and the second because it is
the only finding here that can make *somebody else's* run red for no reason,
on a machine that currently has several.

## 6 · What this round did not check, across all four rows

Beyond each row's own `not-checked:` line below:

- **Nothing was run that writes the Perry task store.** No row was moved; four
  rows still sit at `review` and need the calls in `review.md § 5`.
- **I ran `tests/run` whole for the baseline, not `--serial`**, so an
  order-dependent red would not have surfaced. Per-module control runs before
  every mutation were single-module and clean.
- **Every destructive check ran in a `git clone` of this worktree**, not in the
  tree under review, and not in `/Users/bytedance/proj/Perry`. That clone
  carries no `.claude/worktrees/`, so I did **not** reproduce the 52-nested-
  checkout condition that made TASK-431's guard red on `main` — I verified the
  repair's mechanism (`git ls-files` as the domain, and the loop body being
  reachable) rather than the original failure.
- **I did not re-run the full suite after my mutations.** Every mutation ended
  `perry-restore-check rc=0` against `git show HEAD:<path>`, every planting
  script re-asserted the bytes, and `git status --porcelain` in the clone is
  empty. The only file this branch adds is this document.
- **TASK-412**: I did not exercise the `jsonc` recursion into arrays, the two
  excused changelog transcripts, or `bin/perry-task`'s payload beyond what the
  page's snippets touch — all three are already in the result's own
  `not-checked`, and I did not widen them.
- **TASK-419**: I did not check `--reviews --strict`'s exit code over a graded
  corpus, and I did not regrade any of the 62 ungraded FAILs.
- **TASK-431**: I did not run `perry-lint` against any real board outside
  `tests/fixtures/`, and I did not diff the three `phase/CURRENT` copies'
  behaviour.
- **TASK-411**: I did not run the 1,279 negative-space probes as subprocesses
  through each tool's own `main`; like the test, I asked `lib.parse_surface`.
  I also did not audit `perry-state` and `perry-diagnose`, which
  `is_chain_tool` skips structurally — the result names that gap and nothing
  holds them there.

=== VERDICT ===
task: TASK-411
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-411-result.md
checked: no criteria file exists for this row, so the result's own falsifiable
         claims were the bar and that is stated in § 4.1. 0 false positives
         falsified not re-read — 56 of 63 pairs lose their pair when their
         literal is removed from the chain file, 7 are minted from
         bin/perry-config:39 and were audited by hand at bin/perry-config:293;
         149/63/42.3% and 1,279 probes / 0 accepted both re-derived in a
         clone; the two over-report traps asked directly (perry-tasks diff
         does not read --write, perry-config show does not read --dry-run);
         3 mutations all RED, one mine against the reader itself
         (tests/surface_reads.py:312, branch narrowing disabled) which
         reddened the blind-pair ceiling at 60 pairs; the blind-pair argument
         probed on its second kind and found false — see § 4.5
not-checked: perry-state and perry-diagnose, which is_chain_tool skips
         structurally and nothing holds; the negative space as subprocesses
         rather than through lib.parse_surface; whether the 15-pair ceiling is
         the right number rather than a record; the row's own board status
=== END VERDICT ===

=== VERDICT ===
task: TASK-412
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-412-spec.md
checked: the drive() repair verified at source, not from the claim — both
         repaired cases exec the page's own fenced block and assert on
         ns["tested"], a name that exists only inside it; 7 mutations to
         schema/task-list-contract.md, all RED, 4 of them mine and none in the
         result's table (>= at :592, a bogus not-executable reason at :830, a
         wrong declared type at :111, a seventh fenced block at :663);
         the marker's reason is an enumerated allowlist checked against the
         block's position; the bounded count of 6 is a real bound; 20 tests
         green at HEAD before and after every restore, all restores verified
         with perry-restore-check against git show HEAD
not-checked: the jsonc shape check's recursion into arrays; the two excused
         changelog transcripts as faithful records; bin/perry-task audited for
         behaviour the page does not mention; the forward version space's
         order independently of (int, int) — all four already named in the
         result's own § 9 and not widened here
=== END VERDICT ===

=== VERDICT ===
task: TASK-419
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-419-spec.md
checked: the review.md § 3 diff read as a diff — purely additive, no existing
         sentence edited, VERDICT_KEYS byte-identical, so the page that judges
         this round did not move the bar it judges by; the corpus re-derived
         with the linter's own parse_verdicts (112 blocks, 62 FAIL, 0 carrying
         a grade), so "0 of 62 regradeable" is exact; the M10 equivalent-mutant
         claim proved in one line and then measured anyway over 19 grade
         spellings at lengths 1-3, 7,239 cases, 0 differing; 3 mutations all
         RED, two mine (< limit -> <= limit, the silent threshold raise; and
         fail_grade returning ROW for an unreadable token); the live finding
         carries the undeterminable aside
not-checked: --reviews --strict's exit code over a graded corpus; any regrade
         of the 62 ungraded FAILs; whether 2 is still the right threshold now
         that the numerator changed, which the row itself names as a question
         it creates and does not answer
=== END VERDICT ===

=== VERDICT ===
task: TASK-431
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-431-spec.md
checked: the 3ae5fbfc repair checked by mutation rather than by reading its
         indentation — the dropped pair planted in a tracked file is RED
         twice, in an untracked file green, which is the git ls-files re-scope
         working; 3 mutations on the substantive fixes all RED, incl. mine
         against the one rule itself (bin/lib/__init__.py:266, _blank_key
         stops normalising: 28 tests red); the consequence re-derived, 0 of 20
         spellings read as a declared stage list; SWEEP.read_sites() returns 9
         sites and all 9 are in EXEMPT with a written reason, keyed by
         function and not by line; the fourth-list guard driven with 10 shapes
         — 5 RED, and frozenset({…})/set([…]) GREEN, which is § 3.3
not-checked: the 52-nested-checkout condition that made the guard red on main,
         because the clone carries no .claude/worktrees/ — the repair's
         mechanism was verified, not the original failure; perry-lint against
         any real board outside tests/fixtures/; whether the three
         phase/CURRENT copies currently disagree; non-Python readers and
         runtime-assembled sets, both already in the result's § 10
=== END VERDICT ===
