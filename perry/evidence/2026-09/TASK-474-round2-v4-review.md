# TASK-474 — V4 review, round 2: the phase lifecycle writer

Date: 2026-09-20. Reviewer: an independent V4 round. I did not write this code,
I did not start from the author's verdict, and I did not start from round 1's
FAIL either — the five findings it returned are where I looked *last*.

- **Under review**: `6dedc6e0..1cec479a` (branch `coding/task-474-round2`),
  merged to `main` at `8b6078f7`. `git diff 1cec479a 8b6078f7` is empty, so the
  merge result and the branch head are the same tree; everything below was
  measured at `8b6078f7`.
- **Criteria**: `perry/evidence/2026-09/TASK-474-spec.md`, whose Bound is the
  nine numbered acceptance criteria. I re-derived a verdict on all nine, not
  only on the five the round repaired.
- **Where I worked**: my review worktree could not be fast-forwarded to the head
  under review (the harness refused the merge as a shared-resource change), so
  the code under review was read and mutated in a disposable local clone at
  `…/scratchpad/r2rev`, checked out at `8b6078f7`. This document is committed in
  the worktree. Nothing was run against `/Users/bytedance/proj/Perry/perry`, and
  every verb ran against copies of `tests/fixtures/sample-project` under
  `…/scratchpad/probes/`.

## Verdict in one line

**FAIL.** The repair of F1/F2 changed which *splitter* the phase writer uses and
guarded that spelling structurally, but the category is "two spellings of one
line-break rule disagree", and the surviving spelling is the *reader*: the
writer reads its inputs with `read_bytes().decode()` while `bin/perry-lint`,
`close` and `Okr` read with `Path.read_text()`, which translates `\r` to `\n`.
F2's exact symptom — `phase new` writes a document its own linter immediately
rejects as over-cap — still reproduces. Separately, F5's fix has no test: I
reverted the reorder and the whole affected tier stayed green, which is not what
the author's mutant table reports.

## Baseline

```
bash tests/run --tier affected --base 6dedc6e0
60 modules · 1876 tests · 56.9s · green   ← green in the affected tier is NOT a green suite
```

The tree guard reported nothing moved. I did not run the full or slow tiers; the
author claims a full run of 156 modules / 4406 tests at `92a3448e` and I did not
reproduce it.

## Method

Every mutation is anchored by **line number** with the anchor's current text
asserted before the edit (never `str.replace`). `__pycache__` is purged and the
clock advanced past a whole second on **both** sides of every edit. Every
restore is written from `git show 8b6078f7:<path>` — the ref, not bytes this
harness snapshotted — and then verified with `bin/perry-restore-check 8b6078f7
<path>`, which reported `✓ … matches 8b6078f7` on all eight.

| # | Mutation | Result |
|---|---|---|
| MR-F1a | `phase_header` back to `splitlines()` (`bin/perry-goals:4668`) | **killed** — 26 failures incl. `TestExoticLineBreaks` both shapes and the structural guard |
| MR-F1b | drop `splice_header`'s re-check (`:4695-4698`) — *the author reports this survived their first attempt* | **killed**, and as `FAIL` on both arms, not `ERROR` |
| MR-F2 | cap gate back to `splitlines()` (`:4795`) | **killed** — `TestTheCapBoundary` at 301 plus the structural guard |
| MR-F3 | narrow `CRITERION_7_PATHS` to `("phase",)` — *the author reports this survived their first attempt* | **killed** — both hash controls, 3 failures |
| MR-MC | round 1's actual M-C: `new`'s still-active refusal overwrites `linkage.jsonl` **and** `okr.jsonl` before raising (`:4757`) | **killed** — `test_new_is_refused_while_a_phase_is_active` |
| MR-F4 | delete `close`'s already-scored refusal (`:4871-4873`), round 1's M-E | **killed** — the new refusal test |
| MR-F5 | restore `activate`'s old gate order, scored before active (`:4827-4831` moved back below `:4842`) | **GREEN — finding R1**, and green across all 60 affected modules / 1876 tests |
| MR-X1 | make `close` read `read_bytes().decode()` instead of `read_text()` (`:4866`) | **GREEN** — nothing pins criterion 5's byte clause in either direction |

## The two mutations I was told to re-run myself

**`splice_header`'s re-check (the author's F1b) is real now.** Deleting
`bin/perry-goals:4695-4698` fails `TestSpliceHeaderRefusesAnIndexItCannotTrust`
on **both** subtests — `shape='past the end'` and `shape='the wrong line'` — and
both are reported as `FAIL`, which is what `review.md` rule 2 requires and what
the author says their first kill was not. The test reaches the guard by
monkeypatching `phase_header` through `tests/inproc.load`, which is the only way
in: with both functions splitting the same way no CLI input can make the index
wrong, so the guard is unreachable from outside and the direct test is the only
thing that can kill it. That is an honest solution to a real problem, and it is
correctly labelled as such in the test's own docstring.

One residual, reported not as a defect but so the next round does not have to
rediscover it: if that re-check ever *did* fire inside `close`, it would raise
`Refused` out of the `splice_header` call at `bin/perry-goals:4884` —
**after** `close`'s snapshot write at `:4882` has already landed. The exit code improves from an unhandled
`IndexError` to a clean 1; the half-written state round 1 described is
unchanged. Computing `splice_header(text, "Status", "scored")` before the first
`write_atomic` would remove that risk entirely. Unreachable today, so not a
finding.

**The criterion-7 control no longer reads the constant under test.**
`TestTheHashCoversWhatCriterionSevenNames.NAMED_BY_CRITERION_7`
(`tests/test_phase_lifecycle.py:299`) is written out independently of
`Fixture.CRITERION_7_PATHS` (`:90`), and `test_the_constant_lists_what_criterion_seven_names`
compares the two. MR-F3 narrowing the constant now fails three tests. I also ran
round 1's **behavioural** M-C rather than only the author's constant-narrowing
proxy — making a refusal actually overwrite both stores — and it is red. F3 is
fixed in substance, not only in appearance.

## Findings

### R1 — FAIL to verify. F5's fix is untested, and the result file reports it killed

- Fix: `bin/perry-goals:4827-4831` (the active-phase gate) moved above the
  scored gate at `:4837-4842`.
- Mutation: move it back — exactly the hunk the diff added, reversed.
- Result: `python3 tests/parallel test_phase_lifecycle` → **25 tests, all
  green**. Escalated to `bash tests/run --tier affected --base 6dedc6e0` →
  **60 modules, 1876 tests, green**.

The reason no test can see the order: the only test that reaches the
active-phase gate is
`tests/test_phase_lifecycle.py:201` `test_activate_is_refused_while_another_phase_is_active`,
and it plants `003-another.md` as a byte copy of `002-release-pipeline.md`,
whose `**Status**` is `active` — not `scored`. Under either order the scored gate
does not fire, so the sentence the caller reads is the same either way. The
shape F5 is *about* — target scored **and** another phase holding the pointer —
has no test at all. `tests/test_phase_lifecycle.py:214`
`test_activate_is_refused_on_a_scored_phase` closes 002 first, which empties
`CURRENT`, so it reaches the scored gate under both orders too.

`perry/evidence/2026-09/TASK-474-round2-result.md` § Mutation proof says
"F5 `activate` gate order restored | killed — the active-phase refusal test",
under a heading that says "No survivors". That claim is false, and it is the
same shape of claim round 1 already had to correct in the round-1 result file
("12 mutants … No survivors" was true only of the twelve chosen).

The *behaviour* is right: I confirmed by hand that with 002 active and 003
scored, `activate --phase 003` now names 002. And the scored refusal is still
reachable after the reorder — `active == ""` is the path that reaches it, which
is the path the existing scored test takes — so the reorder made nothing
unreachable. The defect is in the verification, not in the code.

### R2 — FAIL. Criterion 3: the cap gate still disagrees with `bin/perry-lint`

The repair changed the splitter and left the reader mismatched.

- `bin/perry-goals:4795` — `cap, lines = phase_cap(), len(text.split("\n"))`,
  where `text` comes from `read_body` at **`bin/perry-goals:4428`**:
  `body = src.read_bytes().decode("utf-8")`. No newline translation.
- `bin/perry-lint:844` — `raw = path.read_text(errors="replace")`; `:846`
  `lines = raw.split("\n")`; gate `:849` `if cap and len(lines) > cap`.
  `Path.read_text()` opens in universal-newline mode, so a lone `\r` **is** a
  line break to the linter and **is not** one to the writer.

Measured on fixture copies, body sized so the writer counts exactly the cap:

```
CR=0 target=300: WROTE   writer-count 300   linter-count 300   lint: clean
CR=1 target=300: WROTE   writer-count 300   linter-count 301
      ✗ phase/003-sized.md [size-cap] 301 lines, over the tier-1 cap of 300.
CR=2 target=299: WROTE   writer-count 299   linter-count 301
      ✗ phase/003-sized.md [size-cap] 301 lines, over the tier-1 cap of 300.
CR=5 target=300: WROTE   writer-count 300   linter-count 305
      ✗ phase/003-sized.md [size-cap] 305 lines, over the tier-1 cap of 300.
```

This is round 1's F2 verbatim — "at exactly the cap the writer writes a document
its own project immediately rejects" — with the trigger narrowed from *every
file ending in a newline* to *any file carrying a lone `\r`*. The author's own
new test asserts the right thing (`"wrote a document its own linter rejects at
{n}"`, `tests/test_phase_lifecycle.py:428`) and cannot see it, because
`body_of_exactly` builds pure-LF bodies.

The character is not exotic to this change. `TestExoticLineBreaks.EXOTIC`
(`tests/test_phase_lifecycle.py:339`) is
`"\x0b\x0c\x1c\x1d\x1e\x85  \r"` — the author already treats a lone
`\r` as an input the phase writer must survive, on the header path, and did not
carry it to the cap path. Of the nine, `\r` is the only one `read_text()` also
breaks on, which is exactly why it is the one that survives the fix.

**Enumeration of the category** (rule 1 — every site, not the next one). The
category is not "`.splitlines()` appears" but "two spellings of the line-break
rule disagree", and it has two axes: how the string is split, and how the bytes
became a string.

| Site | How bytes become text | How lines are counted/indexed | Agrees with `perry-lint`? |
|---|---|---|---|
| `bin/perry-goals:4428` `read_body` | `read_bytes().decode()` — **no translation** | — | **no** — feeds R2 |
| `bin/perry-goals:4668` `phase_header` | (caller's) | `split("\n")` | yes |
| `bin/perry-goals:4688` `splice_header` | (caller's) | `split("\n")` + re-check | yes |
| `bin/perry-goals:4795` cap gate | text from `read_body` | `split("\n")` | **no** — R2 |
| `bin/perry-goals:4650` `phase_pointer` | `read_text()` | `.strip()` only | n/a |
| `bin/perry-goals:4837` `activate` scored read | `read_text()` | via `phase_header` | read-only, harmless |
| `bin/perry-goals:4866` `close` document read | `read_text()` — **translates** | `split("\n")` | **inconsistent with the writer** — R3 |
| `bin/perry-goals:394` `Okr.__init__` (the named reference) | `read_text()` | `split("\n")` | pre-existing, same blind spot |
| `bin/perry-lint:844` `check_file` | `read_text(errors="replace")` | `split("\n")` | (the authority) |
| `bin/perry-lint:513`, `:1946` | `read_text(errors="replace")` | `split("\n")` | consistent with `:844` |
| `tests/test_phase_lifecycle.py:243-244` | `read_text()` | `splitlines()` | blind to R3 by construction |

The new structural guard cannot reach any of this.
`test_the_phase_functions_never_call_splitlines`
(`tests/test_phase_lifecycle.py:456`) scans `bin/perry-goals` between
`source.index("def phase_docs(")` — `bin/perry-goals:4610` — and
`source.index("COMMANDS = {")` — `:4956`. **What it does not cover:**

1. `read_body` at `:4422-4434`, which is where the writer's asymmetry actually
   lives — 188 lines above the window's start.
2. `Okr` / `write_atomic` / everything else in `bin/perry-goals`.
3. Every other file. `bin/perry-lint`, which owns the cap, is not scanned.
4. The test module itself, which uses `splitlines()` at `:243-244`.
5. The `read_text()` / `read_bytes()` axis entirely — it greps for the literal
   `.splitlines()` and nothing else, so the spelling that defeats it today is
   invisible to it.
6. Any line containing a backtick, or starting with `#` or `*`, is filtered out
   — so a `.splitlines()` inside an f-string that also carries a backtick (the
   house style for every refusal message in this file) is not reported.

It is a real guard against the exact recurrence it names, and its window is
narrow enough that a reader could reasonably think it covers the writer's line
discipline. It does not.

### R3 — criterion 5's "the rest of the document's bytes are unchanged" fails on a document the writer itself writes

`close` reads the phase document with `Path.read_text()`
(`bin/perry-goals:4866`) and writes the translated string back at `:4883-4884`, and
writes the same translated string as the snapshot at `:4882`. The round trip is
reachable through the supported verbs alone, with no hand-editing:

```
$ perry-goals phase new --slug crlf-probe --body-file <CRLF body> --actor t --root <copy>
perry-goals: wrote phase/003-crlf-probe.md · phase 003-crlf-probe · active
  document after `new`: 179 CRLF, 8059 bytes, both headers stamped
$ perry-goals phase close --actor t --root <copy>
  document after `close`: 0 CRLF, 7880 bytes
  non-Status lines changed: 179 of 180
  snapshot is a byte copy of the document as it stood: False
```

`read_body` preserves the body's bytes, so `phase new` will write a CRLF phase
document; `close` then silently re-encodes the whole file. With a lone `\r`
instead it is worse than lossy: the CR becomes a newline and a content line is
split in two (99 lines in, 100 out), on a fixture I measured directly.

Two things hold this back from being the finding I fail the row on:

- Criterion 5 names `Okr.splice_cell` as the discipline to copy, and
  `Okr.__init__` (`bin/perry-goals:394`) reads with `read_text()` too. The
  writer copied the reference implementation faithfully, blind spot included.
  Fixing it here without fixing `Okr` would leave the project with two
  disciplines again, which is the disease.
- Nothing pins it either way: MR-X1, which makes `close` read bytes and
  therefore *does* preserve them, is green across the module. The criterion's
  byte clause is unasserted in both directions.

`test_close_snapshots_flips_status_in_place_and_clears_the_pointer`
(`tests/test_phase_lifecycle.py:229`) compares `snap.read_text()` to a
`read_text()` snapshot and compares `splitlines()` lists — both sides
translated, so the comparison cannot see this by construction.

### R4 — the author's "no survivors" claim, judged

Six mutants are claimed with no survivors. Five of the six I reproduced are
genuinely killed, including the two the author reports as having survived a
first attempt. The sixth, F5, survives — at module level and across the whole
affected tier. "No survivors" is therefore not true of the six as a set, for the
second round running.

### R5 — coverage the reviewer asked me to judge against the criteria only

Round 1 observed, and this round did not change, that nine of the sixteen
refusals `phase_command` can raise have a test. I judged that against the
written criteria and it is **not a reason to fail the row**: the spec's Bound is
the nine numbered criteria, and the Verification section asks for one test per
refusal *named in criteria 2, 3, 4, 5 and 6* — not per refusal the code can
raise. Counted against that narrower obligation:

| Criterion | Refusal it names | Test |
|---|---|---|
| 2 | `new`, no overall OKR | `test_new_is_refused_without_an_overall_okr` |
| 3 | `new`, over the tier-1 cap | `test_new_is_refused_over_the_tier_one_cap…` + `TestTheCapBoundary` |
| 4 | `new`/`activate` while another is active | `test_new_is_refused_while_a_phase_is_active`, `test_activate_is_refused_while_another_phase_is_active` |
| 5 | `close`, not the active phase | `test_close_is_refused_on_a_phase_that_is_not_the_active_one` |
| 5 | `close`, already scored | **new this round** — `test_close_is_refused_on_a_phase_that_is_already_scored` |
| 6 | `--dry-run` writes nothing, all three modes | `test_dry_run_writes_nothing_in_any_mode` |
| 6 | no `--actor` exits 2, all three modes | `test_every_mode_exits_two_without_an_actor` |

Every refusal the criteria name has a test, and each is red under its own
mutation except the F5 *ordering* property discussed in R1 — which no criterion
names as a separate refusal. The author's decision not to widen past the Bound
mid-round is the right one and I am not marking it against them. The seven
unnamed refusals (`new` bad-slug / missing-header / target-exists,
`activate` unknown-number / already-active / scored, `close` nothing-active /
unknown-number / missing-header / snapshot-exists) remain untested; that is a
row to file, not a defect in this one.

## Criteria, one verdict each (the spec's Bound)

| AC | Verdict | Why |
|---|---|---|
| 1 | **Met** | next number, body, one locked write, `Started`/`Status` stamped and `phase/CURRENT` written. Re-measured on bodies carrying `\x0c`, `\r` and ` `: exit 0, both headers stamped, `CURRENT` correct. F1's core repair works. |
| 2 | Met | `new` refuses naming the missing overall OKR; nothing moves (hash) |
| 3 | **Not met** | cap number read from the schema, but the count still disagrees with the linter that owns the cap on any body carrying a lone `\r` — R2. At 300 written lines with one CR, `phase new` exits 0 and `perry-lint` reports `[size-cap] 301 lines, over the tier-1 cap of 300`. |
| 4 | Met, unverified | `new` and `activate` both refuse and both name the active phase, including when the target is also scored; the reorder left no refusal unreachable. But the fix that made it true is not pinned by any test — R1. |
| 5 | **Not met as written** | snapshot, in-place flip and pointer clear all happen, and the already-scored refusal now has a test that dies under its own mutation (MR-F4 red). The criterion's "the rest of the document's bytes are unchanged" fails on any CR/CRLF document, and `phase new` will write one — R3. |
| 6 | Met | all three modes take `--dry-run` and move no byte under any criterion-7 path; all three exit 2 without a non-empty single-line `--actor` |
| 7 | **Met** | `CRITERION_7_PATHS` now covers `phase/`, `linkage.jsonl` and `okr.jsonl`; the control is written out independently of the constant (MR-F3 red on three tests) and round 1's behavioural M-C is red (MR-MC). The absent-file case is covered deliberately. This is the round's cleanest repair. |
| 8 | Met | `goals/reference/phases.md § Writing it` now documents `phase new/activate/close` and still says the overall OKR "has no writer"; `planning.md § Finalize is unavailable for the overall OKR`; `goals/SKILL.md` both rows now say "overall-OKR finalize unavailable"; `setup.md` routes phase finalize through `perry-goals phase new`. Nothing implies `draft finalize` on `okr/first` works. |
| 9 | Met | `DRAFT_MISSING` (`bin/perry-goals:4361-4363`) is one clause, the overall-OKR one; the TASK-264 clause is gone |

`git diff --check 6dedc6e0 1cec479a` is clean.

## On the author's own result file

Treated as claims, checked rather than accepted.

- Base, branch and head are what they say; `git diff 1cec479a 8b6078f7` is empty.
- The two self-referential-test stories are true and the fixes are real, not
  cosmetic — both mutations are red for me, and F1b's is red as a `FAIL` on both
  arms, not an `ERROR`.
- "No survivors" is false: F5's mutant survives the whole affected tier.
- "F1 … one spelling of the line-break rule" is the claim that does not hold.
  The change unified one axis of the rule and left the other — `read_bytes()`
  versus `read_text()` — split, which is what R2 and R3 are.
- The "Not fixed, and why" section is correct and I endorse it: the six untested
  unnamed refusals are a row, not a silent addition here.

## What I did not check

- **The full and slow tiers.** Only `--tier affected --base 6dedc6e0` (60
  modules / 1876 tests), plus single-module runs under mutation. The author's
  claimed full run of 156 modules / 4406 tests at `92a3448e` is unreproduced.
- **Concurrency.** `project_lock` is taken and I did not race two `phase`
  invocations, nor test crash recovery beyond the R3 round trip.
- **Non-English phase documents.** `phase_header` still matches an ASCII
  `**Started**` / `**Status**` literal; the i18n glossary in
  `schema/state-schema.json § i18n` was not exercised against it. If a localized
  phase template spells those cells differently, `new` refuses with
  "the body carries no `> **<field>**:` header line" and `close` refuses with
  "carries no `> **Status**:` header line to flip" — I did not confirm whether
  any shipped template does.
- **`refuse_write_unless_installed` / ADR-019** on a pre-ADR-019 project. Only
  `tests/fixtures/sample-project` was used.
- **The `phase-new|activate|close` event records** against any consumer or
  schema. I confirmed none is appended on `--dry-run` and that `payload`
  carries `event_written`; I did not validate the record's shape.
- **`tests/durations.json`** and whether its two "unmeasured" entries satisfy
  `tests/parallel`'s own rules. The run accepted them.
- **Whether `Okr.__init__`'s own `read_text()` is a live defect elsewhere.** I
  noted it only because criterion 5 names `Okr.splice_cell` as the standard;
  I did not look for a reachable failure on the `OKR.md` path, and nothing in
  this row's Bound asks me to.
- **The guards round 1 verified and this round did not touch** —
  `test_blank_cell_is_one_rule`'s `EXEMPT` key and
  `test_okr_store_is_the_source`'s ordered write-site list. Both are green in
  the affected tier here and I did not re-construct their fire cases; round 1
  did (M-A2, M-B) and the round-2 diff does not touch either file.
- **Whether R2 is reachable from any body a human would actually write.** I
  produced the lone `\r` deliberately. I did not survey real inputs for it; the
  argument that it matters is that `bin/perry-lint` is the authority on the cap
  and the writer's gate must agree with it, not that CR-only prose is common.

=== VERDICT ===
task: TASK-474
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-474-spec.md
checked: read the merged change at 8b6078f7 in a disposable clone (git diff 1cec479a 8b6078f7 empty, so branch head and merge are one tree); ran `bash tests/run --tier affected --base 6dedc6e0` green (60 modules / 1876 tests / 56.9s) as the baseline, and a green affected tier is not a green suite; eight line-anchored mutations with the anchor text asserted before each edit, __pycache__ purged and the clock advanced past a whole second on both sides, each restore written from `git show 8b6078f7:<path>` and verified by `bin/perry-restore-check 8b6078f7 <path>` (all eight ✓); re-ran the author's two self-referential mutants myself — dropping splice_header's re-check (bin/perry-goals:4695-4698) is red as FAIL on both subtests, and narrowing CRITERION_7_PATHS is red on three tests — and also ran round 1's behavioural M-C, a refusal that overwrites linkage.jsonl and okr.jsonl, which is now red; reverted F5's gate reorder and escalated it to the whole affected tier; enumerated every line-splitting AND every bytes-to-text site the change touches or relies on, across bin/perry-goals, bin/perry-lint and the test module, and established which axis still disagrees; measured the cap boundary at 299/300/301 written lines against bin/perry-lint itself rather than against the author's test, with 0, 1, 2 and 5 lone CRs in the body; ran the `new`(CRLF body) → `close` round trip end to end and byte-compared the document and the snapshot; re-derived a verdict on all nine criteria including the four the round did not touch (8 and 9 re-read at this head); ran `perry-lint --reviews` over this document — the verdict block parses, no verdict-malformed. Everything ran on copies of tests/fixtures/sample-project; nothing ran against /Users/bytedance/proj/Perry/perry.
not-checked: the full and slow tiers (only --tier affected --base 6dedc6e0), so the author's 156-module / 4406-test claim is unreproduced; concurrent or racing `phase` invocations and crash recovery beyond the CRLF round trip; any non-English phase template against phase_header's ASCII `**Started**`/`**Status**` literal; `refuse_write_unless_installed` on a pre-ADR-019 project; the shape of the `phase-new|activate|close` event records against any consumer or schema; whether tests/durations.json's two unmeasured entries satisfy tests/parallel's own rules; whether `Okr.__init__`'s identical `read_text()` is a live defect on the OKR.md path; the two guard modules round 1 verified by mutation (test_blank_cell_is_one_rule, test_okr_store_is_the_source), which this diff does not touch and which are green here unmutated; how common a lone-CR body is in practice.
proof: bin/perry-goals:4795 — the cap gate counts `len(text.split("\n"))` where `text` comes from `read_body` at bin/perry-goals:4428, `src.read_bytes().decode("utf-8")`, which does not translate newlines; bin/perry-lint:844 reads `path.read_text(errors="replace")`, which does, and counts at bin/perry-lint:846 with the gate at bin/perry-lint:849. On a fixture copy, a body the writer counts as exactly 300 lines and that carries one lone `\r`: `perry-goals phase new --slug sized --body-file … --actor t` exits 0 and writes, and `perry-lint --root <copy>` then reports `[size-cap] 301 lines, over the tier-1 cap of 300` against the document it just wrote — round 1's F2 symptom unchanged, trigger narrowed (criterion 3). Also bin/perry-goals:4827-4831 — moving the active-phase gate back below the scored gate at bin/perry-goals:4842, i.e. reverting F5's fix exactly, leaves `python3 tests/parallel test_phase_lifecycle` green at 25 tests and `bash tests/run --tier affected --base 6dedc6e0` green at 60 modules / 1876 tests; the only test that reaches that gate, tests/test_phase_lifecycle.py:201, plants a copy whose `**Status**` is `active`, so neither order changes its message, and perry/evidence/2026-09/TASK-474-round2-result.md reports this mutant "killed — the active-phase refusal test" under a "No survivors" heading. Also bin/perry-goals:4866 — `close` reads the document with `read_text()` and writes the translated string back at bin/perry-goals:4883-4884 and as the snapshot at bin/perry-goals:4882: `phase new` with a CRLF body writes 8059 bytes with 179 CRLF, and `phase close` returns 7880 bytes with 0 CRLF, 179 of 180 non-Status lines changed and a snapshot that is not a byte copy of the document as it stood, against criterion 5's "the rest of the document's bytes are unchanged".
=== END VERDICT ===
