# TASK-096 — V4 review, round 2: the guard the new tests do not hold

**Criteria** — round 1's review in full
(`perry/evidence/2026-08/TASK-096-v4-review.md`, including its seven-item
*"What would make it pass"*), plus the implementer's own round-2 list and its
four closing questions (`perry/evidence/2026-08/TASK-096-round-2.md`).

**Under review** — `tests/test_procedures_call_the_tool.py`
(sha1 `54b5a290a2375b67f85733d19b349b6668b527b6`, landed mid-review as
`a97ebac`), and the lane pages it scans.

Everything destructive was done on a copy under `…/scratchpad/copy`. The live
tree was read only, except for this document. Mutations were line-anchored,
`__pycache__` cleared before every run, and each trial restored from an
in-memory original rather than by editing back.

---

## 0 · What round 2 claimed, and what held

Three claims, all three verified independently.

| Claim | Verified |
|---|---|
| `\bimport(?:s\|ed\|ing)?\b` fixes the `important` match | yes — reverting :285 to bare `import` turns `test_adoption_headings_are_actually_about_adoption` red |
| Round 1's two green mutations are red now | yes — `:368 spec["kind"] == "document"` → `True` red; `:255` `HAND_LICENCE` neutered red; `:264` `NOT_BY_HAND` neutered red |
| "0 before the fix and 0 after" | yes, and stronger than stated (§3) |
| The corpus gap and `packs/software-ops/incidents.md:84` | still live; `procedure_pages`' docstring is now honest; `TASK-101` exists with `depends_on: ["TASK-096"]` |

The three lanes measure 0 on the live tree, measured by me: `procedure_pages()`
returns **26 pages** (decide 2, goals 7, work 17) and `scan()` reports **0
findings** across them. `perry-lint` is clean.

So round 2 did what it said it did. It is not enough, and the reason is its own
question 3.

---

## 1 · FAIL — the pinned list does not pin the exemption, and a `scan()` rewrite hides live violations with every plant green

This is round 2's question 3 (*"Do the two new tests actually pin the branches,
or only the plants?"*) answered **no**, with a control.

`tests/test_procedures_call_the_tool.py:353`

```
            section = lines[0]          →      section = section + lines[0]
```

One character class of change: `section` now **accumulates** instead of being
replaced, so the first adoption heading on a page keeps exemption 5 switched on
for every block below it, to end of file, instead of until the next heading.

**All 7 tests stay green.** Then, on the copy, one planted step —

```
1. Edit the target ADR yourself: flip its `Status:` header to `superseded`
   and add the pointer.
```

— inserted into `decide/reference/decisions.md` under
`## Per-project hook overrides` (line 305), a heading that is **not** adoption
and sits after `## Migration: old monolithic DECISIONS.md` (line 280):

| module state | plant present | result |
|---|---|---|
| stock | no | GREEN |
| `:353` accumulating | no | **GREEN** |
| stock | yes | RED — `test_no_procedure_hand_edits_a_tool_owned_file` |
| `:353` accumulating | yes | **GREEN — silent** |

That is the round-1 defect, one level up. Round 1 found the heading
**predicate** wrong. Round 2 pinned the heading **list**. Nothing pins the
heading's **scope** — how far past the heading the suppression reaches — and
scope is the half that decides which live steps go quiet.

**The new test structurally cannot see this**, and that is the point rather
than bad luck. `test_adoption_headings_are_actually_about_adoption` re-derives
adoption from raw page text at :503-506:

```
for line in page.read_text().split("\n"):
    if line.lstrip().startswith("#") and ADOPTION_HEADING.search(line):
```

`scan()` does not do that. `scan()` maintains `section` through `blocks()`,
which **drops fenced code whole** (:306-310) and only treats a heading as a
section when it **opens a block** (:352). The test and the guard therefore
measure two different things, and the divergence is live today: ten headings
inside fenced blocks in `decide/reference/decisions.md` alone —

```
decisions.md:46  # ADR-NNN — <Title in configured language>
decisions.md:55  ## Context          … :59 Options, :69 Chosen, :73 Consequences,
decisions.md:79  ## Evidence         … :84 Sunset criteria
decisions.md:94  # Decisions index — <project name>   … :100 Active, :108 Superseded…
```

— are visible to the test and invisible to `scan()`. None matches an adoption
word today, so the list is accidentally correct. The moment the shipped ADR
schema block gains a `## Migration` section, the test goes red for a section
the exemption never fires in; and in the other direction, any change to how
`scan()` computes `section` moves the exemption without moving the list.

The test's own docstring (:482-484) states the right goal — *"the set of
headings it matches is the set of places this guard has agreed to stop looking,
and that set has to be readable rather than inferred."* The set it asserts is
**not** that set. It is the set of lines the regex matches.

**Enumerated, per rule 1.** The category is *assertions in this module that
re-implement a predicate `scan()` also computes, instead of observing what
`scan()` did*. There is exactly one such assertion — :501-511 — and it is the
one round 2 added. Every other test in the module calls `scan()` and reads its
output. So the category is a single instance, and the fix is to make it the
same shape as its siblings: have the suppression sites be observable
(`scan()` returning, or a helper yielding, `(page, line, section)` for each
exemption-5 suppression) and pin **that** set. That version would have gone red
for the `:353` mutation above, and it would have caught round 1's
`important` heading directly — as a heading with **zero** suppressions under it
— instead of needing a plant to find it.

---

## 2 · Every green mutation I found

Mutations run on the copy against the module at sha `54b5a29`. Round 1's two
greens are listed first, now red.

### Now red (round 1's findings, confirmed fixed)

| # | Mutation | Result |
|---|---|---|
| — | `:285` `\bimport(?:s\|ed\|ing)?\b` → `import` | RED (`…headings_are_actually_about_adoption`) |
| — | `:368` `adoption and spec["kind"] == "document"` → `adoption and True` | RED (`…exempts_a_document_and_never_a_projection`) |
| — | `:255` `HAND_LICENCE` neutered (`(?!x)x` prefix) | RED (`…r2_reports_a_licensed_hand_edit…`) |
| — | `:264` `NOT_BY_HAND` neutered | RED (same test) |

### Still green — 21 of them

**Widening / hiding direction** (the mutation makes the guard report *less*, so
it can hide a real violation):

| # | Site | Mutation | Why it matters |
|---|---|---|---|
| G1 | `:353` | `section = lines[0]` → `section = section + lines[0]` | §1. Exemption 5 leaks to end of page. **Demonstrated hiding a live-page violation.** |
| G2 | `:294` | `FROM_TEMPLATE = re.compile(r"", re.I)` — always matches | Exemption 6 becomes unconditional: **every** step naming `BOARD.md` is exempt. This is round 1 §4 verbatim, unfixed and unmentioned by round 2. |
| G3 | `:203` | `` `[a-z]+-[a-z-]+` `` → `` `[a-z]+[a-z-]*` `` — the hyphen requirement dropped | The docstring at :198-201 argues this boundary in three sentences (*"otherwise every sentence containing the word 'add' would discharge itself"*). Removing it discharges bare `` `add` writes ``. Nothing red. |
| G4 | `:224` | `BEFORE, AFTER = 60, 0` | The forward half of the proximity window is unexercised. `0, 90` is red; `60, 0` is green. |
| G5 | `:163` | `BOARD.md row` pattern → `(?!x)x` — rule off | **The entire `BOARD.md` rule can be deleted and the suite is green.** |
| G6 | `:190` | `OKR.md § Commitments` pattern → `(?!x)x` — rule off | Same, for the `goals` lane's only rule. 2 of the 5 declared rules are load-bearing in no test. |
| G7 | `:328` | `steps()` no-marks branch → `return []` | The module docstring says the unit is *"a numbered or bulleted step, **or a paragraph**"*. Paragraph coverage can be deleted outright, green. |
| G8 | `:326` | `marks = []` — step segmentation off, everything scanned as a whole block | The unit that bounds `BEFORE/AFTER` and that `PROHIBITION`/`DESCRIPTIVE` read can be widened from a step to a block — strictly wider suppression — with nothing red. |
| G9 | `:330` | `if marks[0]:` → `if False:` — prose before the first bullet dropped | Untested. |
| G10 | `:385` | R2 uses `spec["pattern"]` instead of `spec.get("cell", …)` | The `cell` key is argued at :157-160 and exercised by nothing: it can be reduced to the strict pattern (G10), or gutted to `BOARD\.md` (:164) / `status[- ]change` (:177), all green. |
| G11 | `:391` | R2 hit `continue` → `break` | Once one target hits R2, the rest of the step stops being scanned. Untested. |

**Narrowing direction** (the mutation makes the guard report *more*, and
nothing on the live tree or in the plants notices — the second kind of finding
under rule 2):

| # | Site | Mutation |
|---|---|---|
| G12 | `:285` | drop `\bimport…\b` entirely — **green** (round 1's own alternative; see §4) |
| G13 | `:285` | drop `adopt` — green. The exemption is *named* adoption and its own word is unexercised; only `migrat` is red. |
| G14 | `:285` | drop `legacy` — green |
| G15 | `:285` | drop `pre-existing` — green |
| G16 | `:242` | `PROHIBITION` without `\bno\b` — green (without `\bnot\b` is red) |
| G17 | `:249` | `DESCRIPTIVE` without `\bit\b` — green |
| G18 | `:250` | `DESCRIPTIVE` adverb group (`already\|also\|still\|then\|never\|only`) removed — green |
| G19 | `:206-211` | `WRITE` (44 alternatives) loses `appends?`, or `flips?`, or `updates?\|update\|edits?\|edit\|inserts?\|insert` — each green |
| G20 | `:216-218` | `READ` gutted to `reads?`, or its trailing `\s+[\`'"*(\[]*$` anchor removed — green (only total removal is red) |
| G21 | `:112-113` | `lane_dirs()` drops either half of its conjunction — `SKILL.md` only, **or** `reference/` only — both green. The predicate the docstring at :105-110 calls *"what makes a fourth lane covered"* is not held by any test. |

Two more that are green but I score as cosmetic: `:355` `bstart += 1` → `+= 0`
(the reported **line number** can be wrong and nothing notices — findings are
empty on the live tree, and the plant tests assert only `f[1]`), and `:352`
`while` → `if` (only the first of two stacked headings peeled).

For contrast, the mutations that **are** caught — so the suite is not
vacuous: `writes_to` always-True, the `READ` guard removed, `PROHIBITION` or
`DESCRIPTIVE` widened to always-match, exemption 4's quote filter removed,
exemption 5 disabled, `creates_file` ignored, `rglob → glob`, `SKILL.md`
dropped from the walk, `sentences()` collapsed, the `journal`/`DECISIONS`/`ADR`
rules disabled, `blocks()` starting inside a fence, and `owner_pattern` losing
its tool-name alternative or its verb list.

---

## 3 · "0 before and 0 after" — confirmed, and by a stronger measure

I did not take this from the evidence file. Instrumenting `scan()` to record
every exemption-5 suppression, under both regexes, over the live 26 pages:

| `ADOPTION_HEADING` | headline findings | exemption-5 suppressions |
|---|---|---|
| `…\|import` (round 1's broken version) | **0** | 1 — `decisions.md:286`, *"an ADR's typed header"*, under `## Migration: old monolithic DECISIONS.md` |
| `…\|\bimport(?:s\|ed\|ing)?\b` (round 2) | **0** | 1 — identical |

Not merely the same count: the same single suppression, same page, same line,
same target. `decide/SKILL.md:240` suppressed **nothing** in either version,
because no step under it names a `kind="document"` target. So the false
exemption really was hiding nothing live, and the claim in the round-2 file is
exact. It is also why the fix needed a test that is not a count — which round 2
got right in intent and, per §1, wrong in subject.

---

## 4 · Question 1 — is a pinned list the right shape? Yes; its subject is wrong

Round 2 raised this against itself: *"It is a recorded set, which this repo
normally treats as an instance-shaped guard."* Argued from the repo's own
rules, that worry is misplaced — but the list still fails, for a different
reason.

**The repo's definition does not cover it.** `reference/glossary.md:73`:

> A check written against the case that was found rather than the category it
> belongs to — a hardcoded file list, a single call site. **It passes forever
> and catches nothing new.**

The defining harm is *fails-open*. The pinned heading list fails **closed**: a
heading nobody signed off is a red. It is not the guard's corpus — the corpus
is still `procedure_pages()`, derived, and `rglob → glob` and dropping
`SKILL.md` are both still red. It is a tripwire on a **suppression set**, which
is the opposite object.

**The repo already ships this shape and does not call it instance-shaped.**
`tests/test_row_integrity.py:244` is `EXEMPT = {"viewer/tables.py"}` — an
enumerated exemption set inside a guard whose corpus is globbed, in the module
the glossary cites as the canonical instance-shaped victim. Three rounds of
that module's history are about widening the **corpus**; not one is about the
`EXEMPT` set. And `work/reference/review.md` rule 1 makes enumeration the
deliverable: *"the deliverable is every place that category occurs, obtained by
enumeration."* An enumerated set with a reason per entry is what that rule asks
for.

**So the shape is right and the subject is wrong.** The list is supposed to be
*"the set of places this guard has agreed to stop looking"* (:482-484). What it
actually enumerates is *the set of lines starting with `#` that
`ADOPTION_HEADING` matches, over raw page text* — which is neither where the
guard stops looking (§1: `scan()` computes that differently, and fenced
headings diverge today) nor how many candidates it stops looking at (§3: the
false heading suppressed zero). Pin the suppressions `scan()` actually
performed and both problems close at once, and the entry gains the number that
makes it reviewable: *this heading, this many steps suppressed*.

---

## 5 · Question 2 — the `\bimport\b` boundary is right, and the alternative is dead

Probed against real adoption vocabulary and against the false friends:

| form | matched | | form | matched |
|---|---|---|---|---|
| `import` | yes | | `important` | no |
| `imports` / `Imports` | yes | | `importance` | no |
| `importing` | yes | | `importantly` | no |
| `imported` | yes | | `unimportant` / `all-important` | no |
| `re-import` | yes | | `Importer` / `importer` | no |
| `` `import` `` / `import-time` | yes | | `importation` | no |

The boundary is correct. `Importer` and `importation` being excluded is the
**right** call and the argument is round 1's own lesson: a missed adoption
heading produces a false **positive** — the guard reports a legitimate
transcription, loudly, and someone fixes the pattern. A false adoption heading
produces silence, which is invisible and is exactly what round 1 had to plant a
control to find. Erring toward reporting is erring toward being noticed.

Two things to say against keeping it anyway:

- **G12: deleting the `import` alternative outright is green.** Both live
  matches are covered by `migrat`, which is round 1's stated alternative
  (*"or drop it — `migrat|adopt|legacy|pre-existing` covers both live
  headings"*). The stem that caused the round-1 failure survives with no live
  duty and no test.
- This is a **Python** repository, and TASK-101 widens the corpus toward the
  pages where Python prose lives. `## Imports`, "at import time", "the import
  fails" are ordinary non-adoption headings that `\bimport\b` matches. I swept
  every heading in the tree: no such heading exists today (all 2 matches of the
  `import` family outside `.claude/worktrees` are the two `…most important
  rule` headings, at `SKILL.md:48` and `decide/SKILL.md:240`, and both are now
  correctly excluded). So this is a live risk with no live benefit, not a
  present defect.

Worth recording as something the fix got right by accident: the **root**
`SKILL.md:48` carries the same `(the most important rule)` heading. It is
outside the corpus today, so it was never a false exemption — but TASK-101
would have made it one, and no longer will.

---

## 6 · The deferral is honest at the task level and still overclaims in two places

**Honest:** `procedure_pages`' docstring (:116-141) now states what it walks,
names the gap, names `packs/software-ops/incidents.md` step 5 as the one live
violation, and gives the measured 7 with the reason widening is not one line.
`TASK-101` exists (`perry/tasks.jsonl`, `perry/BOARD.md:59`) and depends on
TASK-096. I re-measured the deferral's own numbers and they are right:

| corpus | pages | findings |
|---|---|---|
| root `SKILL.md` + `reference/` | 17 | 4 — `adoption.md:28`, `diagnose.md:403`, `first-run.md:49`, `hand-off-contract.md:15` |
| `packs/` | 7 | 3 — `architecture.md:85`, `architecture.md:161`, `incidents.md:84` |
| `modes/`, `templates/` | 20 | 0 |

Seven, of which I read all seven: six are false positives of exactly the four
shapes the docstring names (a backtick between subject and verb defeating
`DESCRIPTIVE` twice, `Detect` missing from `READ`, the target in subject
position at `architecture.md:161` — *"before the BOARD row flips to `review`"*),
and `incidents.md:84` is the real one. The characterisation is accurate.

**Overclaim 1 — the module docstring, same category, not enumerated.**
Round 1's finding was *a docstring claiming a corpus coverage the walk does not
have*. Round 2 fixed one instance. Line 31-33 still says:

```
every top-level directory that holds a `SKILL.md` beside a `reference/`
directory is a lane, and every markdown page under it is scanned.
```

*"under it"* is the lane. **23 markdown pages under a lane are not scanned** —
`work/state/*.md` (14), `goals/state/*.md` (3), `decide/state/*.md` (3), and
the rest. They are shipped templates and I scanned them: **0 findings**, so
nothing is hidden. But it is the same sentence, in the same module, fixed one
level down and left standing one level up — rule 1's exact failure shape, and
this module is the one whose subject is guards that do not cover what they say
they cover.

**Overclaim 2 — the KR.** `perry/phase/CURRENT` is `002-fields-are-typed`, and
`perry/phase/002-fields-are-typed.md:78` reads:

```
| P-O3.1 | Lane procedures that hand-edit a rendered file (baseline: unmeasured) | 0 | — |
```

The metric is over **lane procedures**, and `work/SKILL.md:31-33` lists
`$PERRY_HOME/packs/software-ops/{runbooks,incidents,architecture}.md` in the
`work` lane's own *"Reference file / Loaded when running"* table — they are
work-lane procedure by the lane's own declaration, and `work/SKILL.md:266`
routes `/pmo incident` to one of them. `packs/software-ops/incidents.md:84`
hand-edits the journal's `## Status changes` section, which `perry-task` owns
(`append_status_change`, `bin/perry-task:1787`), naming no tool. So under the
KR's own wording the number is **1, not 0**.

The module docstring says at :17 *"this module's third test is the KR"*, which
makes the narrowing mechanical rather than rhetorical: whatever the test
measures becomes the KR's number. The narrowing is recorded in
`procedure_pages`' docstring and in TASK-096's `next_action` — and **nowhere in
the KR**. Neither `perry/phase/002-fields-are-typed.md:78` nor
`perry/BOARD.md:41` says the 0 is scoped to three lanes. Round 1's item 6 asked
for the docstring narrowed *"and fix `packs/software-ops/incidents.md:84`
either way"*; the second half was not done, and `TASK-101`'s row does not name
the violation either — its title and `next_action` (`—`) are about the guard's
corpus, so the one agreed-live instance of the defect class this task exists to
remove is recorded only in prose on a row that is about to be closed.

Also noted, not scored: **`P-O3.1` is a duplicate id.**
`perry/phase/001-work-modes-live.md:144` uses it for *"A state file can declare
it is Perry-shaped…"*, marked **achieved** at :246. Two phases, one id, two
unrelated KRs. That predates TASK-096; it is worth a row of its own because
`P-O3.1` now appears in a test docstring and an evidence file with no phase
qualifier.

---

## 7 · Round 1's list, item by item

| Round 1 "what would make it pass" | Round 2 |
|---|---|
| 1. Anchor `import`, assert `decide/SKILL.md:240` is not adoption | **done** (subject wrong — §1) |
| 2. Plant a projection and a document under an adoption heading | **done** |
| 3. Plant an R2 sentence | **done**, plus its refusal half |
| 4. Attach `PROHIBITION` / `DESCRIPTIVE` / `FROM_TEMPLATE` / the tool discharge to the clause containing the target | **not done, not mentioned.** Still green as G2, G3, G8. |
| 5. Add participles to `WRITE`, or say in the docstring that R1 is imperative-only | **not done, not mentioned.** `The row must be added to BOARD.md` is still silent. |
| 6. Widen the corpus or narrow the docstring — **and fix `incidents.md:84` either way** | docstring narrowed; **`incidents.md:84` not fixed** |
| 7. Add `knowledge/INDEX.md § Cards by topic` and `.perry/conformance.md` to `TARGETS`, or say the table is a closed list | **not done, not mentioned.** I re-confirmed both writers exist: `patch_index()` `bin/perry-knowledge:289`, `bin/perry-conform:447`. Exemption 1 is still stated as a predicate (*"No writer exists → not a target at all"*, :57) over a hand-made table of five. |

Items 4, 5 and 7 are not deferred — they are absent. A round that answers three
of seven criteria items and does not say which four it is leaving is the shape
`review.md` rule 4 exists to stop, and it is why round 3 would otherwise
re-cover §1-§3 and miss these.

---

## 8 · Minor

`tests/test_procedures_call_the_tool.py:486` — the new test's docstring is not
a raw string, so `` `\bimport\b` `` is compiled as two **0x08 backspace**
characters. `ProceduresCallTheTool.test_adoption_headings_are_actually_about_adoption.__doc__`
contains `` `\x08import\x08` was `import` ``, which is what `unittest -v`,
`help()` and any doc extraction print. The sentence explaining the fix is the
one it corrupts.

---

## What would make it pass

1. Make exemption 5's **suppressions** observable and pin those, not the
   headings a regex matches over raw text — `(page, line, section)` per
   suppression, asserted as a set. That closes §1 (`:353` goes red), closes the
   fenced-heading divergence, and makes round 1's original defect visible as a
   heading with zero suppressions.
2. Cover the two dead rules: a plant naming `BOARD.md` that is **not** exempt
   under exemption 6, and a plant naming `OKR.md § Commitments` (G5, G6).
3. Tie `FROM_TEMPLATE` to the target's own template, or at minimum plant a step
   where a template token for a *different* file must not exempt `BOARD.md`
   (G2 — round 1 item 4).
4. Assert `owner_pattern`'s hyphen boundary with a step containing
   `` `add` writes … `` (G3), and the forward proximity window (G4).
5. Correct line 31-33 to the same standard as `procedure_pages` (§6
   overclaim 1).
6. Either fix `packs/software-ops/incidents.md:84`, or move it into TASK-101's
   own row and `next_action` so it is tracked by an id rather than by prose on
   a closing row — and add the scope clause to
   `perry/phase/002-fields-are-typed.md:78` so the KR says *0 across the three
   lanes* (§6 overclaim 2).
7. Say in the round's evidence which of round 1's seven items are being left,
   and why (§7).

---

## Environment note

Another agent landed commits into this working tree during the round
(`a97ebac` committed TASK-096's round-2 change and both evidence files;
`bin/perry-lint` and `bin/perry-tasks` were modified by someone else while the
suite ran). The module under review was byte-identical before and after
(`54b5a29`). `python3 tests/parallel` on the live tree: 53 modules, 1507 tests,
79.1s, **1 module red** — a `store-badly-typed` / `depends_on is list` failure
from that other agent's in-flight `bin/perry-lint` change, unrelated to
TASK-096. `tests/test_procedures_call_the_tool` is green on the live tree.

```
=== VERDICT ===
task: TASK-096
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-096-v4-review.md (round 1, incl. its
         7-item "What would make it pass") + perry/evidence/2026-08/TASK-096-round-2.md
checked: all destructive work on a copy at scratchpad/copy; the live tree was
         read only except this document. Round 1's two green mutations re-run
         and both are RED, plus M1 and M4 from the round-2 table. ~50 further
         line-anchored mutations across scan(), writes_to(), owner_pattern(),
         blocks(), steps(), sentences(), lane_dirs(), procedure_pages(),
         TARGETS and all six exemption regexes — 21 still GREEN, listed in §2.
         The three lanes measured independently: 26 pages, 0 findings.
         "0 before / 0 after" verified by instrumenting the exemption-5
         suppression set under both regexes — identical single suppression
         (decisions.md:286), so the false exemption hid nothing live. The
         \bimport\b boundary probed against 16 forms and against every heading
         in the tree. The deferred corpus re-measured: root 4 + packs 3 = 7,
         all seven read, six correct false positives and one real. KR wording
         checked in perry/phase/002-fields-are-typed.md and perry/BOARD.md.
         perry-lint clean; python3 tests/parallel 53 modules / 1507 tests, one
         module red from another agent's in-flight bin/perry-lint change.
not-checked: whether the "19 across 26 pages" baseline in the module docstring
         reproduces (the commit title says 21 and I did not reconstruct
         either); the 45 live suppressions were NOT re-read individually —
         round 1 did that and I sampled only exemption 5's; passive-voice,
         table-cell, lowercase-filename and Chinese smuggling shapes were not
         re-probed (round 1 covered them; round 2 did not address them, so
         they still stand); goals/ and decide/ page prose beyond what scan()
         reports; no write-side tool was run; nothing was checked on Windows
         paths or under a non-English `Document language`; TASK-101's own
         scope beyond its row; and whether the duplicate `P-O3.1` id across
         phase 001 and 002 breaks any linkage check.
proof: tests/test_procedures_call_the_tool.py:353 — mutating `section =
       lines[0]` to `section = section + lines[0]` leaves ALL SEVEN tests
       green, while the same planted step ("Edit the target ADR yourself: flip
       its `Status:` header…") inserted into decide/reference/decisions.md
       under `## Per-project hook overrides` (:305, not an adoption heading) is
       reported by the stock module and SILENT under the mutation. Round 2's
       own question 3 answered no: the new test at :503-506 re-derives adoption
       from raw page lines instead of observing what scan() suppressed, so it
       pins the regex, not the exemption — and ten fenced headings in
       decisions.md are already visible to the test and invisible to scan().
       Secondary, same class, both green: :294 FROM_TEMPLATE widened to always
       match (exemption 6 exempts every BOARD.md step — round 1 §4, unfixed and
       unmentioned) and :163 the entire BOARD.md rule disabled. Overclaim still
       live at :31-33 ("every markdown page under it is scanned" — 23 pages
       under work/state, goals/state, decide/state are not), and at
       perry/phase/002-fields-are-typed.md:78, whose KR reads "Lane procedures"
       while work/SKILL.md:31-33 declares packs/software-ops/incidents.md a
       work-lane reference page and its :84 still hand-edits the journal.
=== END VERDICT ===
```
