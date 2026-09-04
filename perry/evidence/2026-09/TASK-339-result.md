# TASK-339 — result: the scanner is gone, and the procedure that replaces it

> Branch: `coding/task-339-remove-the-scanner`, cut from `main` at `651a5ca`.
> Rung claimed: **V3**. Everything below was run in this worktree; every number
> is measured here and none is inherited.
>
> **Read § 4 first if you read only one section.** The row's premise about
> `TASK-107` does not survive measurement, and the correction is the reason the
> procedure is shaped the way it is.

## 1. The corpus, re-derived

Two figures were in circulation and the row said neither was verified. Neither
is right for this tree.

```
$ ls perry/evidence/*/*-spec.md | wc -l
     149

$ for f in perry/evidence/*/*-spec.md; do bin/perry-state --root . --escalation-scan "$f"; done
```

Run through `bin/perry-state --escalation-scan` on `651a5ca`, **before** any
deletion, one process per spec, parsing each JSON payload:

| | measured here, 2026-09-04 | PMO, 2026-09-03 | TASK-290 round 2 |
|---|---|---|---|
| scanned | **149** | 148 | 147 |
| pass | **134** | 133 | — |
| refuse | **15** | 15 | 16 |
| unarmed | **0** | 0 | — |
| union | **35** fragments, `armed: true` | 35 | 35 |

**The PMO's figure reconciles exactly; round 2's does not.** 148 → 149 and
133 → 134 is one file: `TASK-339-spec.md` itself, committed to `main` at
`651a5ca` and passing. The 2026-09-03 census was therefore correct for the tree
it was taken on. Round 2's *147 scanned / 16 refused* reconciles with nothing —
it disagrees on the denominator by two and on the refusal count by one in the
other direction, and no intervening commit moves both that way. Treat it as
superseded.

Exit codes observed: `0` on every pass, `3` on every refusal, `4` never — this
project's hook is armed and every spec was measured against a live 35-fragment
union.

**The fifteen refusals, and what each turned on:**

| Spec | fragments that refused |
|---|---|
| TASK-047, TASK-085, TASK-156, TASK-201, **TASK-139** | `state-schema.json` |
| TASK-100, TASK-196, TASK-197, TASK-235, TASK-276 | `claims`, `state-schema.json` |
| **TASK-107** | `~/.claude/skills`, `ln -s`, `ln -sf`, `ln -snf`, `publish`, `published`, `--force-with-lease`, `rm -rf`, `$perry_home` |
| **TASK-220** | `adopt`, `diagnose`, `relocate` |
| **TASK-108** | `diagnose` |
| **TASK-099**, **TASK-244** | `setup` |

**A correction to the row's Out of scope.** It says *"Nine of the fifteen
refusals turn on"* whether a non-`claims` edit to `schema/state-schema.json`
should escalate. The measured number is **ten** — five refuse on
`state-schema.json` alone and five on `claims` + `state-schema.json`. The
policy question is unchanged and this row still leaves it to the hook; only the
count is corrected.

**45 of the 149 declare no scope at all** (`bin/perry-lint --root .`), and every
one of them scanned `pass` over that armed union. That is the same 45 measured
on 2026-09-02, and it is the reason § 6 keeps a reporting check rather than
deleting one.

## 2. What was deleted

`viewer/parsers.py`, 384 lines: `scan_spec_escalations`, `escalation_occurrences`,
`_discount_reason`, `path_root_is_foreign`, `path_token_around`,
`is_bare_directory_fragment`, `_PATH_CHAR`, `_PATH_RUN`, `_NAME_EDGE`,
`DISCOUNT_LONGER_NAME`, `DISCOUNT_OWN_TREE`, `ESCALATION_TOUCHES`,
`ESCALATION_DISCLAIMS`, `ESCALATION_UNCANCELLABLE`.

`bin/perry-state`: the `--escalation-scan` flag, `SCAN_EXIT`, `escalation_scan()`,
and the usage block that documented the exit codes.

`bin/perry-lint`: the `P.scan_spec_escalations` call in `check_specs`.

`tests/`: 41 tests in `test_escalation_boundaries.py` and the scanner half of
`test_spec_scannability.py`.

**No caller survives.**

```
$ grep -rn "escalation.scan\|escalation_scan\|scan_spec_escalations" bin/ viewer/ tests/ work/
bin/perry-lint:2954      "…`bin/perry-state --escalation-scan` … was removed on 2026-09-04…"
bin/perry-lint:2972      "…(It once also read "and `--escalation-scan` grows a distinct exit code"…)"
bin/perry-state:27       "There is no mode here that scans a spec: `--escalation-scan` was removed…"
work/reference/dispatch.md:14    "Until 2026-09-04 this step was … That command is gone."
work/reference/autopilot.md:162  "There is no command that returns the verdict: `--escalation-scan` was removed…"
tests/test_escalation_boundaries.py  (TestTheSpecScannerIsGone — the guard that it stays gone)
```

**Declared deviation from Verification 4.** That criterion asks the grep to
return "only history and this row's evidence". It returns five live prose
sentences as well, each recording that the command was removed and why. I kept
them deliberately: a reader with the old command in muscle memory types it, and
`unknown argument` with no explanation is a worse artifact than one sentence.
None is a caller — `TestTheSpecScannerIsGone.test_no_caller_survives_in_bin_or_viewer`
holds that, and `test_the_flag_is_rejected_rather_than_quietly_accepted` holds
that the flag exits 2 rather than parsing to a silent `0`.

## 3. The `escalation_union` question — **KEPT**, and here is the argument

`escalation_union`, `hook_escalation_lines`, `escalation_fragments`,
`line_fragments`, `extracts`, `unextractable_lines`, `escalation_pattern` and
`matching_escalations` all stay. So do `RoleCard.escalate_fragments` and the
role-card half.

**They do not do the thing this row removed.** The scanner asked *what does this
document mean* — it took unbounded prose and returned a safety verdict. The
extraction half asks *which spans did the user put in backticks under a named
heading*. Under `ADR-007` that is the typed side of the line, not the prose
side: a bounded, enumerable value space the user wrote down explicitly, in a
delimiter whose whole purpose is to say "this is a token, not a sentence". The
ADR's rule 2 forbids a regex asking prose a question; it does not forbid reading
a list.

**Three consumers survive this row and none of them scans a spec:**

1. `bin/perry-state § build` publishes `project.escalation` — `project`, `roles`,
   `union`, `origins`, `armed`, `unextractable`. That is what shows a user their
   own list, and what step 4.1 of the new procedure tells the agent to read.
2. `bin/perry-state § hook_profile` and `bin/perry-lint`'s
   `hook-high-stakes-armed` report bullets that arm **nothing**. Deleting the
   extractor deletes the only thing that can tell a user their safety list is
   dead prose — `~/proj/gimegime-pmo` reported `armed: true` over five bullets
   producing three fragments (TASK-202). Removing that would be a strict loss
   with nothing gained by this row.
3. `bin/perry-lint § check_verification` matches a closed row's `id + title`
   against the list, to ask whether outward-facing work closed below V5.

**The safety property that would be lost if it went.** `DESIGN-006 § 5.2`: a
role's list is *added* to the project's and never substituted. That is
structural — `origins` says which side each fragment came from — and it is
invisible to a reader who is handed one merged list. A prose procedure telling
an agent "read the hook, then read every role card, and remember a role only
ever adds" restates the rule but cannot detect its violation.

**What KEEPING it costs, stated so this is not read as free.** Item 3 above is
the same defect class this row removed, one surface over: `check_verification`
runs `matching_escalations` against a task's **title**, which is prose, and the
match has no way to tell a mention from an action. `TASK-107`'s own spec names
the measurement — twelve task titles trip it and word edges fixed exactly one;
`TASK-060`'s *"mint_id does not adopt the board's own id prefix"* still trips
`adopt`. **It is a `warn`, never a gate, and it is not in this row's Bound**, so
I have not touched it. It is filed below as a finding I did not fix.

## 4. The six walked cases — and the row's premise about TASK-107 is wrong

Worked by hand against `work/reference/dispatch.md` § 4.1–4.6 as written. The
list screened against is Perry's own `.perry/hook.md § High-stakes operations`,
armed, 35 fragments, no role cards declared.

### The five that must come out ALLOWED

**TASK-099 — ALLOWED.** Fragment found: `setup`, in `## Files in scope`, in
*"setup and hook code that reads repository documents — read."* Tell 5 (the line
states its own verb) and tell 1 (a file in this tree versus the operation). The
section opens *"Read-only survey. The only file this round writes is its own
report."* and the bullet's own trailing word is `read`. The hook's `setup` is
host skill installation; this round reads the code that performs it. Every path
in the section is relative — `bin/`, `viewer/`, `tests/`,
`perry/evidence/2026-09/TASK-099-census.md` — so § 4.3 puts all of them in this
project's own tree.

**TASK-108 — ALLOWED.** Fragment: `diagnose`, in `## Files in scope`, in
`bin/perry-diagnose` and *"focused diagnose tests and fixtures"*. Tell 1. The
hook's entry is *"`diagnose` execute stage"* — Perry running its diagnosis
**into a project it does not own**. `bin/perry-diagnose` is a file in this
repository and editing it runs nothing. The `Out of scope` section names
`bin/perry-lint`, `bin/perry-task`, `bin/perry-conform`, `bin/perry-migrate` and
`schema/state-schema.json` as untouched, which confirms the round's reach.

**TASK-139 — ALLOWED.** Fragment: `state-schema.json`, in `## Files in scope`.
Tell 6. The bullet is *"`schema/state-schema.json` — only if a new field is
declared. **This is the claim surface; changing it is escalated.** If the design
points that way, stop and file the question rather than editing it."*, and
`Out of scope` says *"Editing `schema/state-schema.json`. If shape (a) wins, the
schema edit is escalated and is a separate, user-authorised step."* **The
scanner read this as a self-contradiction and refused it.** It is the opposite:
a spec that has read the gate, named the escalation, and pre-committed to
stopping at it. Refusing it teaches rows that quoting the gate is expensive,
which is the same perverse incentive `.perry/hook.md` names about rewording.
Verdict ALLOWED, **and § 4.6 requires the pre-commitment to be carried into the
delegation prompt verbatim**, so the executing agent inherits the stop.

**TASK-220 — ALLOWED.** Fragments: `adopt`, `diagnose`, `relocate`, in
`## Deliverable`, in *"the `adopt` / `diagnose` precedent the router already
states"* and *"one row in `SKILL.md § Router subcommands` beside `adopt` /
`diagnose` / `relocate`"*. Tell 3 (cited as precedent) and tell 2 (a list
position is data). The paragraph containing them is *"**The router writes no
state file of its own.**"* — the round's own statement that it performs none of
the three. Note this spec offers **no `## Files in scope`**, so § 4.2's
partial-scope note applies: say so, and do not claim the row was fully screened.

**TASK-244 — ALLOWED.** Fragment: `setup`, in `## Deliverable`, in *"the harness
re-does setup per test that could be done once"*. Tell 4, with its substitution
test: *"the harness re-does its preparation per test"* is still true, so this is
the ordinary English noun. The hook's `setup` is host skill installation and no
substitution keeps *"run `/perry preparation`"* true. Every path is relative
(`tests/test_header_rule_harness.py`, `tests/parallel`).

### The sixth — REFUSED, but not for the reason the row gives

**TASK-107 — REFUSED, on § 4.5, and NOT on any of the nine fragments the row
names.**

The row says TASK-107 *"must come out REFUSED … on `~/.claude/skills`, the
`ln -s` variants, `publish`, `rm -rf`, `--force-with-lease`."* I measured where
each of those nine sits, and **every one of them is tell 2 — quoted as data:**

- *"so `~/.claude/skills`, `--force-with-lease` and `$PERRY_HOME` keep matching"*
  — examples of fragments the new matcher must still match.
- *"A right-edge guard cannot match `ln -sf` from `ln -s`, `rm -rfv` from
  `rm -rf`"* — examples of morphology.
- *"The hook already enumerates forms this way (`publish` and `published`, …)"*
  — a quotation of the hook's own list.

TASK-107 installs no host skill, publishes nothing, runs no `rm -rf` and pushes
nowhere. **A procedure that refuses it on those nine is the same procedure that
refuses TASK-244 on the word `setup` and TASK-099 on the word `read`** — it is
precisely the scanner's failure, re-implemented in prose. So the six cases
**cannot be separated by fragment presence at all**, in either direction. That
is the finding, and it is what forced § 4.4 to be a doing-versus-naming test
rather than a better matching rule.

What does refuse TASK-107 is a different thing, and the hook's bullets do not
contain it. Its `## Files in scope` reads *"`.perry/hook.md`,
`work/state/hook_TEMPLATE.md` — the matching rule sentence"*, and `Deliverable`
item 5 says the dropped forms *"are added to `.perry/hook.md` and to the
template's defaults"* while item 1 changes what the gate matches at all. **The
round rewrites the gate that constrains it, and widens it, in the same commit.**
`hook_TEMPLATE.md` is the default high-stakes list every project Perry adopts
receives, so the change reaches other people's projects. An agent that may widen
its own gate has no gate.

That rule is written into the procedure as **§ 4.5, a standing entry**, and it
is stated there rather than added to `.perry/hook.md`, which is the user's file
and out of this row's scope. § 4.5 says in the file itself that the user may
fold it into the hook (in which case the paragraph defers to the bullet) or
strike it. It is written down so the verdict is reproducible either way rather
than depending on a reader's instinct.

**Score: five ALLOWED, one REFUSED — the required split, reached by a different
route than the one the row assumed.**

## 5. The foreign-root case (Verification 3)

Worked against § 4.3, with the two paths written the way a spec actually writes
them — inside markdown emphasis.

| # | As written in a spec | § 4.3 walk | Verdict on the hook's `evidence/` entry |
|---|---|---|---|
| 1 | `perry/evidence/2026-09/` | first character `p`; no anchor; relative | **allowed** — this project's own tree |
| 2 | `**perry/evidence/2026-09/**` | `**` … `**` is a **balanced pair** → emphasis, anchors nothing. The path itself begins `p`. Relative | **allowed** — identical verdict to #1 |
| 3 | `~/other-project/evidence/2026-09/` | a **single unpaired** `~` at the head of the path → home anchor → foreign shape 2 | **REFUSED** |
| 4 | `_~/other-project/evidence/2026-09/_` | `_` … `_` balanced → emphasis; strip nothing, look past it: the path's own head is `~` → foreign | **REFUSED** — same as #3 |
| 5 | `$PERRY_HOME/inputs/` | unpaired `$` at the head → variable anchor → shape 3 | **REFUSED** |
| 6 | `<target>/evidence/` | unresolved root → shape 5 | **REFUSED** |

**The reasoning does not depend on stripping formatting first, and the ordering
is the whole point.** The rule the procedure states is a **pairing** test, not a
stripping pass: an emphasis marker comes in a balanced pair wrapping a span; an
anchor is unpaired and sits at the head of the path. Nothing has to be removed
from the string before the question is answerable, so there is no window in
which the ownership signal can be lost.

That matters because the two failures on record are the two directions of
exactly this collision, and both are cases 2 and 3 above:

- **The code refused case 2.** `path_root_is_foreign` read the head `**perry` as
  containing `*` and called this project's own evidence directory foreign.
- **Narrowing the character class would have allowed case 3.** Round 1 was told
  to narrow `_PATH_CHAR` to filename characters; the implementing agent refused
  and measured that it re-roots `~/other-project/evidence/2026-09/` to
  `project/evidence/2026` and `$PERRY_HOME/inputs/` to `perry_home/inputs/`,
  both of which then read as this project's own tree and stop refusing.

**One character class cannot answer both**, because "ignore the markdown around
the path" and "`~` means someone else's home" are the same character. The
pairing test answers both, and a reader performs it without noticing. That is
the strongest single argument on record for `USER-916`.

`§ 4.3` also keeps the **unresolved root** (shape 5) with its reason attached —
*a root nobody has resolved is not a root known to be this project* — because
`TASK-290-round2-v4-review.md` names it in writing as the clause most likely to
be lost in a rewrite to prose, being the only one not obvious from an example.
`tests/test_spec_scannability.py § TestTheTwoClausesAProseRewriteLoses` is what
fails if it leaves.

## 6. What replaced the scanner in code — and why anything did

`P.SPEC_SCOPE_SECTIONS` + `P.spec_scope_sections(text)`, ~10 lines. It returns
which of `## Files in scope` / `## Deliverable` a document offers, present and
non-empty, resolved through the i18n glossary. It **takes no fragment list**, so
there is nothing it can judge; `TestTheSpecSaysWhetherItDeclaredAScope
.test_it_returns_no_verdict_and_matches_no_fragment` holds that structurally.

**This is a judgement, not an obvious call.** The strict reading of "the
spec-scanning path is gone, and no caller survives" would delete
`spec-scope-unscannable` outright. I kept it, reimplemented, because:

- **The signal survives the deletion and gets more important, not less.** Step
  4.2 tells an agent to read those two sections. 45 of 149 specs offer neither.
  A per-dispatch procedure discovers that one row at a time, at the moment
  someone is trying to dispatch it; `perry-lint --root .` says it about the
  whole corpus in the default pass, before anyone is committed.
- **It is not the thing being removed.** Locating a heading is `ADR-007 § 5b`'s
  *"locate the file and hand it to an agent"*. The hand-off is what step 4 now
  does with the answer.

**Cost, stated:** one Python function still opens a spec. If a later reader
takes that as licence to grow it back into a matcher, this row was for nothing —
which is why `TestTheSpecScannerIsGone` names all twelve removed symbols and
fails if any returns.

## 7. Mutation table

Harness: `anchor by line number **and** assert the old text at that line`,
clear every `__pycache__` before and after, sleep past the whole-second
boundary on both sides of the edit, restore with `git show <ref>:<path>` (one
path per call) and verify the restored bytes equal what `git show` returned.
`bin/perry-restore-check` was **not** used (TASK-256). Final
`git status --porcelain` after the run: empty.

| # | Where | The mutation | Result |
|---|---|---|---|
| M1 | `viewer/parsers.py:4382` | `scan_spec_escalations` comes back under its own name | **red** — `TestTheSpecScannerIsGone.test_the_scanner_and_its_path_machinery_are_gone_from_parsers` |
| M2 | `viewer/parsers.py:4404` | heading lookup stops going through `alias()` (literal `## ` match) | **red** — `TestTheHeadingsAreReadInTheProjectsOwnLanguage.test_the_english_headings_still_work` (+1) |
| M3 | `viewer/parsers.py:4403` | an empty heading counts as a declared scope | **red** — 11 tests, incl. `test_the_procedure_shape_declares_no_scope_and_says_so` |
| M4 | `bin/perry-lint:3053` | the linter spells the section names itself instead of reading `P.SPEC_SCOPE_SECTIONS` | **red** — `TestOneAnswerToWhichSectionsAreScanned.test_the_linter_reads_the_gates_list` |
| M5 | `dispatch.md:56` | delete the **unresolved-root** shape from the foreign-root enumeration | **red** — `TestTheTwoClausesAProseRewriteLoses.test_all_five_foreign_root_shapes_are_named` |
| M6 | `dispatch.md:42` | move ownership detection **after** normalisation ("strip markdown first, then look at the path") | **red** — `…test_ownership_is_decided_before_normalisation` |
| M7 | `dispatch.md:79` | delete tell 4, the doing-vs-naming rule that clears `TASK-244` | **GREEN — the finding** |
| M8 | `dispatch.md:38` | the empty-spec half stops requiring a go-ahead ("treat the row as clean and dispatch it") | **red** — `TestTheProcedureNamesTheShape.test_the_empty_spec_half_still_does_not_refuse_the_row` (+1) |

**M5 was GREEN on the first run, and that is worth recording.** My first guard
asserted `"unresolved root" in step4`. Deleting list item 5 left the phrase
standing in the worked-paths table below it, so the guard read the copy rather
than the clause and passed. A guard whose own mutation passes is worse than no
guard, because it is also believed. Fixed by scoping the assertion to the
numbered enumeration and requiring exactly five items; M5 is red above and the
docstring records why.

### M7 is green, and no test can close it

**A written procedure cannot be held by a test, and this is the honest statement
of that.** M7 deletes one of six doing-versus-naming tells — the one that clears
`TASK-244` — and the full suite stays green. So would deleting the substitution
test inside it, or rewriting the tell so that it no longer separates the case.

I could make M7 red by pinning tell 4 verbatim. **I chose not to, and the reason
matters:** the only text guard that catches a *substantive* weakening of prose
is one that freezes the prose, and a frozen `dispatch.md` cannot be improved. A
sixth round of guarding English is the thing `ADR-007` and `USER-916` are about.
Two clauses are pinned as **presence** (§ 5, M5/M6) precisely because
`TASK-290-round2-v4-review.md` names those two, in writing, as the ones a prose
rewrite loses; everything else is deliberately unheld.

**What holds the rest, stated plainly and without pretending it is a test:**

1. **The six cases in § 4 above, in this file, with their answers and their
   tells.** They are a re-runnable bench for a human or an agent: change the
   procedure, re-walk the six, and if the verdicts move, the change is wrong.
   That is a rubric, which is a V4 instrument, not a V3 one.
2. **`§ 4.6` makes the reasoning a written artifact.** The verdict, the tell and
   the quoted line go into the dispatch evidence file every time. A gate whose
   reasoning is written down is reviewable after the fact; the scanner's never
   was beyond a JSON key.
3. **The scanner's own record is the control.** It had 3,291 tests behind it and
   still moved its verdict on a bold marker. Test count was never what was
   protecting this.

## 8. Suite, lint, and what I did not fix

| | before (`651a5ca`) | after |
|---|---|---|
| `tests/run` | 114 modules · 3291 tests · **all green** | 114 modules · **3251** tests · **all green** |
| `bin/perry-lint --root .` | 0 errors, 37 warnings | **0 errors, 37 warnings** |

−40 tests: 41 scanner tests deleted, plus the reshaped/added guards. No module
was lost.

**The two known reds were not red.** `tests/test_contract_key_parity.py`'s
anti-vacuity controls (TASK-335, a 4-hour idle threshold at `bin/perry-task:6303`
against Perry's own live board) passed on every run today, before and after.
Nothing here changed them; the board had simply been touched recently enough.
Stated so nobody reads "all green" as evidence that TASK-335 is fixed.

### Findings I did **not** fix

1. **`bin/perry-lint § check_verification` still matches prose.** It runs
   `matching_escalations` over a closed row's `id + title` and cannot tell a
   mention from an action — `TASK-060`'s title trips `adopt`. Same defect class,
   one surface over, **not in this row's Bound**, and a `warn` rather than a
   gate. TASK-107's own `Out of scope` already named it as its own row.
2. **Ten of fifteen refusals turn on `schema/state-schema.json`**, not the nine
   the spec states. Whether a non-`claims` edit there should escalate is a hook
   policy question and this row names it and leaves it, per its Out of scope.
   The count is corrected here; the question is not answered.
3. **M7 stands green.** § 7 says why, and what stands in for it.
4. **`work/reference/dispatch.md` is now 398 lines** (was 313). Perry lints a
   tier-1 line cap on some files; `dispatch.md` is not among them today and no
   warning fired, but a procedure that grew 86 lines is a maintenance cost and
   should be said out loud rather than discovered.

### One thing I broke and fixed, recorded because it nearly shipped

My baseline commit used `git add -A`. The worktree was at a **stale commit**
(`d49964e`) and carried uncommitted changes across the branch cut, so that
commit swept in **deletions of three v4 review documents**
(`TASK-067-round6`, `TASK-256-round2`, `TASK-263`, `TASK-308-round1`) and edits
to `perry/BOARD.md`, `perry/tasks.jsonl`, `.perry/events.jsonl` and the 09-04
journal — every one of them a file this row was told not to touch. Caught by
diffing the branch against `main` before writing this document, restored with
`git show main:<path>` one path per call and verified byte-for-byte
(commit "revert state files this row must not touch"). `git diff main --name-only`
now returns exactly the seven files § 9 lists. **`git add -A` on a branch cut
from a stale worktree is not safe on this project**, and the brief's warning
about stale worktrees has a second half that is not in it.

## 9. Files changed

```
bin/perry-lint
bin/perry-state
tests/test_escalation_boundaries.py
tests/test_spec_scannability.py
viewer/parsers.py
work/reference/autopilot.md
work/reference/dispatch.md
perry/evidence/2026-09/TASK-339-result.md   (this file)
```

Not pushed; no PR opened — push is escalated on this project. `main` was never
switched to, merged into, or written.
