# TASK-284 — round 2, V4 review

- **Criteria**: `perry/evidence/2026-09/TASK-284-spec.md`, read from
  `coding/task-247-config-predicate` (the branch under review does not carry
  it).
- **Under review**: `coding/task-284-round2b` at `a2da1c8`, 11 commits on
  round 1's `cbc2d8f`, base `d49964e`. Six files in the diff.
- **Round 1's review**: `perry/evidence/2026-09/TASK-284-round1-v4-review.md`
  (**FAIL**), read from the same ref.
- **Reviewer**: fresh context, did not write this code, isolated worktree.
- **Method**: all four trees (`d49964e`, `cbc2d8f`, `a2da1c8`,
  `coding/task-247-config-predicate`) extracted with `git archive` into a
  private scratch directory and worked on there. **The repository under review
  was never modified and no fixture was planted into it.** Every mutation was
  applied to the scratch copy and restored from a pristine copy kept outside
  the tree, verified byte-identical afterwards.
- **A note on refs, for the next reader.** `perry-lint --reviews` on this
  worktree reports `citation-not-on-branch` for this file's `criteria:` line.
  That is expected and not a defect in the review: this worktree is cut from
  `d49964e`, and `TASK-284-spec.md` lives on `coding/task-247-config-predicate`
  (now also merged to `main` at `cc1ae11`). The exhibit resolves on `main`; it
  does not resolve here. Round 1's review is in the same position.
- **Result**: **PASS.** Round 1's FAIL is closed at both ends — the procedure
  now prevents the defect at its source, and the report now reaches a reader on
  a command people actually run. I re-derived every load-bearing number myself
  rather than adopting the round's account of it.

---

## 1 · Verification item 2, met — the item round 1 could not meet

This is the criteria's own acceptance check and the reason round 1 failed:

> *"A spec written by following `add-task` verbatim, from scratch, scans with a
> non-empty `touches` when its scope names a high-stakes fragment. Write one
> and show it."*

I read the **amended** `work/reference/subcommands.md § add-task` step 3 and
wrote my own spec from it — my own words and my own scope, not round 2's
worked example — then ran the real binary on it:

```
$ python3 bin/perry-state --root . --escalation-scan .../TASK-901-spec.md
"scope_scanned": ["Files in scope", "Deliverable"],
"touches": {"Deliverable": ["git push","origin","gh release","published","rm -rf"]},
"refuse":  ["git push","origin","gh release","published","rm -rf"],
"verdict": "refuse",  "fragments_scanned": 35
EXIT=3
```

**`touches` is non-empty, the gate refuses, exit 3.** Item 2 is met.

**The control pair, my own, identical scope words in the two shapes:**

| shape | `scope_scanned` | `touches` | `verdict` | exit |
|---|---|---|---|---|
| `## Deliverable` (what step 3 now prescribes) | `["Files in scope","Deliverable"]` | 5 fragments | `refuse` | **3** |
| `- **Deliverable**: …` (the old step 3's only reading) | `[]` | `{}` | `pass` | **0** |

Both rows return the identical result under `d49964e`'s binary as under the
branch's, which is the point: **no code moved, the procedure did.** The defect
round 1 demonstrated — a P0 auto-dispatch that force-pushes and `rm -rf`s
returning exit 0 — is now produced only by disobeying a step that names the
shape and says why.

## 2 · The census, re-derived independently, with refs

I wrote my own counter that **does not import `viewer/parsers.py`**: it
replicates `_section`'s regex (`^## <alt>[^\n]*\n(.+?)(?=^## |\Z)`) plus the
non-empty-body rule, and reads each ref's **own** `schema/state-schema.json`
heading glossary.

| ref | sha | `*-spec.md` | scannable | **unscannable** |
|---|---|---|---|---|
| `d49964e` — the branch's base | `d49964eee339` | 119 | 74 | **45** |
| `cbc2d8f` — round 1 | `cbc2d8f1860a` | 119 | 74 | **45** |
| `a2da1c8` — **under review** | `a2da1c8035bf` | 119 | 74 | **45** |
| `coding/task-247-config-predicate` — live now | `052b25fc5241` | 135 | 90 | **45** |
| `main` — moved tonight | `cc1ae118e0f9` | 135 | 90 | **45** |

**Every figure round 2 reports is correct.** The unscannable **set** is
byte-identically the same 45 files on all five refs (`diff` of the sorted path
lists: identical). Shape split, on all five: **19** `### Deliverable` /
**26** no section / **0** bullet — and I confirmed round 2's added detail that
**19 of 19** of the `###` ones sit under a `## Schema` umbrella heading.

Two notes on refs, since the criteria ask for them:

- Round 2's correction of round 1 is right: round 1's live figure of 134/89/45
  was one commit stale; 135/90/45 is correct.
- `coding/task-247-config-predicate` has moved again since round 2 measured —
  it is `052b25f` now, not the `89295085` round 2 cites. My count at `052b25f`
  is the same 135/90/45. **Current `main` (`cc1ae11`) is also 135/90/45**, so
  the promotion trigger's counter has not moved.

**Fix 2 is correctly refused, again.** 0 of the 45 use the bullet shape, so
widening `_section` to read bullets closes none of them. I re-measured this
rather than carrying it forward.

## 3 · The report has a reader — measured before and after

`perry-lint --root .`, no flags, on the two scratch trees:

| tree | tail of the default run |
|---|---|
| `cbc2d8f` (round 1) | `0 error(s), 5 warning(s)` — **zero** `spec-scope-unscannable` lines |
| `a2da1c8` (round 2) | `0 error(s), 16 warning(s)` — **ten named**, plus `⚠ evidence/ … and 35 further spec(s)`, plus the summary line `· specs: 45 of 119 present the escalation gate no scope to scan` |

10 named + 35 counted = 45, and the cap never suppresses the count:
`perry-lint --specs --root . --json` returns `specs_scanned 119, unscannable
45, findings 45` — uncapped, as claimed.

**Reachability grep**, the exact directory list round 1 used
(`work/ modes/ decide/ goals/ reference/ packs/ SKILL.md AGENTS.md tests/run`):
**0 occurrences of `--specs` on `cbc2d8f`, 2 on `a2da1c8`**
(`subcommands.md:723`, `dispatch.md:20`). Confirmed. The stronger claim is the
one that needs no grep, and it holds: the check runs in the default pass.

`work/reference/dispatch.md` step 4 now names `scope_scanned` beside
`refuse` / `green_lit` / `origins`, gives `[]` a rule, requires the same
**explicit go-ahead in chat** the `unarmed` half requires, and states that the
exit code deliberately does not change. `bin/perry-state`'s
`SCAN_EXIT = {"pass": 0, "refuse": 3, "unarmed": 4}` is byte-identical to the
base, and `viewer/parsers.py` is **byte-identical to round 1's**
(md5 `235a60b6…` on both) — so round 1's 1712-comparison parity is carried
forward as a fact about the same file, not as a claim needing re-derivation.

## 4 · The mutations — all eight re-run by me, plus two more

Round 2 reports that the `dispatch.md` guard was **green twice** on its own
subject before it was fixed. I did not take that on trust. I rebuilt all eight
mutations independently, plus **both** green variants it describes, each
applied to the scratch copy and restored from a pristine copy:

| # | mutation | my result |
|---|---|---|
| 1 | default-pass wiring removed | **RED** (4 failures) |
| 2 | naming cap removed | **RED** |
| 3 | promotion trigger deleted | **RED** (2 failures) |
| 4 | `load_glossary` put back in the `--specs` branch | **RED** |
| 5 | step 3 reverted to "the same schema" | **RED** |
| 6 | step 3's *why* paragraph deleted | **RED** |
| 7 | `cmd_add`'s render-site comment deleted | **RED** |
| 8a | `dispatch.md` step 4 paragraph **deleted** | **RED** |
| 8b | same paragraph in a **closed** `<!-- … -->` (green mutation #1) | **RED** |
| 8c | same paragraph after an **unclosed** `<!--` (green mutation #2) | **RED** |

Baseline green, all ten red, restored green, and all four mutated files
byte-identical to pristine afterwards. `__pycache__` cleared and the clock
advanced past the whole-second boundary before every run.

**Both holes round 2 reported on itself are genuinely closed.** `visible()`'s
`<!--.*?(?:-->|\Z)` — terminating a comment at end-of-file as well as at
`-->` — is what makes 8c red, and it is the right fix for the right reason.

The guard file itself: **29 tests, all pass, no skips** (13 from round 1 + 16
new), on the branch head. Confirmed by running it.

## 5 · Nothing was reworded, and nothing was fixed by weakening a test

Both are hard requirements and both hold.

- **`git diff cbc2d8f..a2da1c8 -- perry/evidence/`** is exactly one file: this
  round's result document. **No spec was edited.** `tests/fixtures/` is not in
  the diff at all, so the two unscannable fixture specs were left alone, as
  claimed and as `.perry/hook.md` requires.
- The whole diff is six files; the only test file among them is
  `tests/test_spec_scannability.py`, and it has **2 deleted lines in 291** —
  both inside a docstring, restating the census with the ref it was taken at.
  No assertion was removed or loosened.
- **Run 2's real defect was fixed in the right place.** `b1bc2de`, the commit
  whose message says the suite found a real defect, touches
  **only `perry/evidence/2026-09/TASK-284-round2-result.md`** — 1 file
  changed. `tests/test_diagnose.py` is untouched on this branch. The evidence
  file was corrected; the test was not.
- **The green run is effectively the head.** The suite ran at `85ea58a`; the
  head `a2da1c8` adds 23 lines to the result markdown and nothing else. Since
  that commit lands `## `-shaped headings into a file under `evidence/`, I
  checked the check it could plausibly break: `tests/test_diagnose.py` at the
  head is **145 tests, OK** — including the id-resolution test that caught run
  2's defect. I also confirmed the result file's own honesty note: handed to
  the gate directly it does scan `scope_scanned: ['Files in scope',
  'Deliverable']`, `verdict: refuse` — and it is correctly **excluded** by the
  `-spec\.md$` pattern, since `--specs --json` scans 119 files and this is not
  one of them.

## 6 · The suite, run by me at the branch head

`bash tests/run` in the scratch copy of `a2da1c8`, clean tree, `PERRY_PROJECT`
and `PERRY_HOME` both unset so the suite's own step-0a refusal does not apply:

```
START 23:40:16 load: 4.14 7.53 14.34
109 modules · 3032 tests · 301.1s · 8 workers
✓ all green            ← step 2, the parallel set
✓ all green            ← the EXIT-trap banner, after the tree guard
END   23:45:19 load: 12.99 8.94 12.98
WALL_SECONDS=303 EXIT=0
```

**109 modules / 3032 tests / exit 0**, which reproduces round 2's run 3
(109 / 3032 / 310.7s) module-for-module and test-for-test. The tree guard's
closing line confirms nothing under the tree moved. `tests/test_parsers.py` was
**not** red — the criteria note it as red on `main` for an unrelated reason,
and it is green at this base, as round 2 says.

Two incidental confirmations from the log, both of the new default-pass line
behaving as designed on a project that is not Perry: the fixture project prints
`· no *-spec.md under evidence/ — the dispatch escalation gate has nothing to
read here`, distinct from both the "not checked" and the "all *n* offer" cases.

## 7 · The other two claims

- **(c) is right.** The `load_glossary(schema)` call is removed rather than
  re-explained, and the property it was falsely credited with holds without
  it: my own localized spec, `## 交付物` naming `git push` / `origin` /
  `rm -rf`, returns `scope_scanned: ["Deliverable"]`, `refuse` on all three,
  `verdict: refuse`. Localization comes from `parsers._i18n()`, as the new
  comment says.
- **(d) is a reasonable call, recorded where it can be found.** The promotion
  trigger lives in `check_specs`' docstring and is guarded by two tests, one of
  which asserts the trigger does **not** route through rewording. Declining to
  open an ADR because the `decide` lane owns `perry/decisions/` and no user is
  present to lock one is consistent with how this project treats decision
  records, and the trigger's counter is verifiable: it is 45 on `main` today.

---

## Finding — one, and it does not reach FAIL

**A third way to disable the `dispatch.md` paragraph leaves its guard green: a
markdown code fence.** The brief asked me to look for this, and it is there.

I wrapped the `scope_scanned` paragraph in `` ``` `` fences in the scratch
copy. `visible()` strips `<!-- … -->` (closed or unclosed) but knows nothing
about fences, so the bytes stay inside the step-4 slice and
`TestTheProcedureNamesTheShape.test_dispatch_step_4_gives_scope_scanned_a_reader`
stays **green**, exit 0, 0 failures — the same signature as the two holes round
2 found and fixed.

**Why this is a filing and not the FAIL.** The two holes round 2 closed were
holes because an HTML comment renders as *nothing*: the guard said "a reader
sees this" while no reader could. A fenced paragraph still renders, and is
still read — by a person scrolling step 4 and by the agent that consumes
`dispatch.md` as its procedure. So this probe does not reproduce the defect
class; it marks the outer edge of what a text-presence guard can do, and that
edge is **stated in the test file itself**: *"nothing here can tell a correct
paragraph from a plausible one."* Charging a FAIL for it would be charging the
round for the acknowledged limit of the technique the criteria did not ask it
to exceed. Worth a row; not worth a round.

Four other probes I ran for the same reason all came back **RED**, which is
the more informative result: the paragraph moved out of step 4 entirely;
the default-pass wiring left in place but put under `if False:`; the `· specs:`
summary line deleted while the findings stay; and step 3's worked `## `
example removed while its prose stays. The guards are not merely grepping for
one keyword each.

---

## Observations — filings, not part of the verdict

1. **`viewer/parsers.py`'s own docstring now carries the refuted premise and a
   stale quotation of step 3.** `scan_spec_escalations` still says
   *"`add-task` step 3 says the spec carries 'the same schema' as the journal
   block, `perry-task add` renders that block as bullets … Following the
   procedure produced the hole"*, and *"45 of the 132"*. After this round step
   3 no longer says that, and round 1 itself refuted the bullet premise. Round
   2 corrected exactly this text in `bin/perry-lint`'s `check_specs` docstring
   and deliberately did not touch `viewer/parsers.py` — a defensible scope
   call, since touching it would have put the parity claim back in play — but
   the two docstrings now disagree with each other, and the parser's is the
   wrong one. A documentation row of its own.
2. **`visible()` does not strip code fences** (the finding above), and the same
   helper is the basis of every text guard in the file.
3. **The un-earned number is disclosed and does not matter here.** Round 2
   cites round 1's `108 modules / 3003 tests` base result rather than
   re-running a baseline, and says so in as many words. It does not affect the
   verdict: the delta it supports (`+16 tests`) is directly checkable from the
   test file — 13 tests on `cbc2d8f`, 29 on the head, both of which I ran — and
   the claim that matters is that the head is green, which I verified myself
   rather than inferring from a baseline. Declining a ~500s run under load 37
   for a number nothing in the diff bears on is a defensible trade, and it was
   labelled rather than laundered.
4. **The advisory's counter has not moved** — 45 on `main` at `cc1ae11` — so
   the promotion trigger recorded in (d) is at the start of its wait, not near
   its end. Nothing to do; worth knowing when somebody re-reads that paragraph.

---

## What I did not check

- **The contents of the 45**, again. Like round 1, I classified them by heading
  shape only. How many of the 45 would actually refuse if they were scannable
  is still unmeasured, and it is still the number that would say whether
  advisory is the right default.
- **The 16 `_section` call sites.** Irrelevant to this round for the same
  reason as round 1 — fix 2 was refused and `viewer/parsers.py` is
  byte-identical to round 1's — but I did not enumerate them.
- **Round 1's 1712-comparison parity harness was not re-run.** I verified the
  premise that makes re-running unnecessary (`viewer/parsers.py` and
  `bin/perry-state` byte-identical between `cbc2d8f` and `a2da1c8`) rather than
  the conclusion.
- **`--specs` under `--quiet`, with `--state-root`, and on a project whose
  state root is not the project root.** Round 2 reports fixing a
  `resolve_state_root` skip that had been hiding on macOS; I ran the guard file
  and saw no skips, but I did not build that case myself.
- **Whether the amended step 3 is the *best* wording**, only that it is
  unambiguous enough that I could follow it cold and produce a scanning spec.
- **`perry-diagnose` / `perry-lint` on any project other than Perry itself**,
  and any non-macOS path handling.
- **Round 2's runs 1 and 2, and their reds, were not reproduced.** I ran the
  full suite once, at the head, green. I did **not** re-run the base suite
  either — so like round 2 I have no independently measured baseline, and I am
  relying on the diff's shape (no runtime file outside `bin/perry-lint` is
  touched) rather than on a measured before/after.
- **The suite was run once, not repeatedly.** A single green run does not rule
  out an order-dependent or flaky module; round 2's own run 1 red was an
  environment artefact of exactly that kind.

=== VERDICT ===
task: TASK-284
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-284-spec.md
checked: Verification item 2 met with MY OWN spec written cold from the amended add-task step 3 — scope_scanned ["Files in scope","Deliverable"], 5 fragments, verdict refuse, exit 3, against exit 0/touches {} for the identical words in the old bullet shape, and both rows identical under d49964e's binary so no code moved; census re-derived with my own counter that never imports viewer/parsers.py, reading each ref's own schema glossary — 119/74/45 at d49964e, cbc2d8f and a2da1c8, 135/90/45 at coding/task-247-config-predicate (052b25f, moved since round 2 cited 89295085) and at main cc1ae11, the same 45 files on all five by sorted-path diff, split 19 `###` / 26 none / 0 bullet with 19 of 19 under a `## Schema` umbrella; default `perry-lint --root .` 0 errors/5 warnings and zero spec-scope-unscannable lines on cbc2d8f versus 0 errors/16 warnings with ten named, a counted tail of 35 and the `· specs: 45 of 119` summary line on a2da1c8, while --specs --json stays uncapped at 119/45/45 findings; `--specs` reachability grep over work/ modes/ decide/ goals/ reference/ packs/ SKILL.md AGENTS.md tests/run 0 on cbc2d8f and 2 on a2da1c8; viewer/parsers.py byte-identical between cbc2d8f and a2da1c8 (md5 235a60b6…) and SCAN_EXIT literal unchanged, so round 1's parity is carried by identity; ALL EIGHT of round 2's mutations rebuilt and re-run by me plus both self-reported green variants — 10 of 10 RED, baseline green, restored green, all four mutated files byte-identical to a pristine copy after, __pycache__ cleared and past the second boundary each time; four further probes (paragraph moved out of step 4, wiring under `if False:`, summary line deleted, step 3's worked example deleted) all RED; guard file 29 tests OK no skips; test_diagnose 145 tests OK at the head; b1bc2de fixes only the result markdown so the test was not weakened; git diff cbc2d8f..a2da1c8 -- perry/evidence/ is one file and tests/fixtures/ is absent from the diff, so no spec was reworded; localized `## 交付物` spec scans and refuses on git push/origin/rm -rf without load_glossary; and `bash tests/run` by me on a scratch copy of the head, clean tree, 109 modules · 3032 tests · 301.1s · 8 workers, 303s wall, load 4.14 -> 12.99, exit 0 with both `all green` banners and the tree guard reporting nothing moved, reproducing round 2's run 3 module-for-module
not-checked: the contents of the 45, so their real blast radius is still unmeasured; the 16 `_section` call sites; round 1's 1712-comparison parity harness was not re-run — I verified the byte-identity that makes it unnecessary instead of the conclusion; `--specs` under --quiet, with --state-root, and on a project whose state root differs from the project root, including the macOS resolve_state_root skip round 2 reports fixing; whether step 3's wording is the best available rather than merely unambiguous enough to follow cold; perry-lint/perry-diagnose on any project but Perry itself; non-macOS paths; round 2's runs 1 and 2 and their reds were not reproduced; I did NOT re-run the base suite either, so like round 2 I hold no independently measured baseline and lean on the diff's shape instead; and the suite was run once, which does not rule out an order-dependent or flaky module
proof: a spec I wrote cold from the amended `work/reference/subcommands.md § add-task` step 3 returns `verdict: refuse`, exit 3 on five high-stakes fragments where round 1's verbatim-procedure spec returned `verdict: pass`, exit 0 — the criteria's Verification item 2, unmet in round 1 and met here — while `bin/perry-lint`'s default `--root .` pass, which printed `0 error(s), 5 warning(s)` and no finding over 45 unscannable specs on `cbc2d8f`, now prints ten named `spec-scope-unscannable` warnings, a counted tail of 35 and `· specs: 45 of 119`, with `work/reference/dispatch.md:20` naming `scope_scanned` and requiring the same explicit chat go-ahead as `unarmed`
=== END VERDICT ===
