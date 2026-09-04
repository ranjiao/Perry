# TASK-339 — V4 review (fresh context)

> Reviewer branch: `review/task-339-v4`, cut from `main` at `c5cbf79`.
> `BASE=$(git merge-base HEAD main)` = `c5cbf793a88f953d736a1734dc3ba0ee7dbeb63c`.
> The work is merged: this worktree's `HEAD` was `d49964e`, an ancestor of `main`,
> and `coding/task-339-remove-the-scanner` (`f8f835a`) is an ancestor of `main`
> via `feabad5`. Reviewed on `main` as it stands.
>
> **Restores were done with `git show c5cbf79:<path>`, single path per call.**
> `bin/perry-restore-check` was not used. Every restore was followed by
> `git status --porcelain` returning empty before the next mutation.
>
> The six named cases in § 1 were walked **before** reading
> `TASK-339-result.md`. Only § 2 onward was written with the round's account open.

---

## 1. The six named specs, walked by hand — **MET**

Walked against `work/reference/dispatch.md § 4.1–4.6` as written, against
`.perry/hook.md § High-stakes operations` (armed, 35 fragments, no
`.perry/roles/` directory exists so the union is the hook's list unchanged).

| Spec | Fragments I found | Step / tell I applied | My verdict |
|---|---|---|---|
| TASK-099 | `setup` (`Files in scope`), `evidence/` | 4.3 all relative → internal; tell 5 — the bullet's own trailing word is `read.` under *"Read-only survey. The only file this round writes is its own report."* | **ALLOWED** |
| TASK-108 | `diagnose` (`bin/perry-diagnose`, "focused diagnose tests"), `state-schema.json` (in `Out of scope` only) | tell 1 — a file in this tree versus the `diagnose` execute stage; the schema path is not a write target | **ALLOWED** |
| TASK-139 | `state-schema.json` (in **both** `Files in scope` and `Out of scope`) | tell 6 — *"This is the claim surface; changing it is escalated… stop and file the question rather than editing it."* The 4.4 contradiction rule is explicitly carved out for this shape | **ALLOWED** |
| TASK-220 | `adopt`, `diagnose`, `relocate` (`Deliverable`) | tell 3 — cited as precedent; also 4.2's partial-scope note, since this spec offers no `## Files in scope` | **ALLOWED** |
| TASK-244 | `setup` ("the harness re-does setup per test") | tell 4 — synonym substitution: *"re-does its preparation per test"* stays true | **ALLOWED** |
| TASK-107 | nine fragments, all in `Deliverable` | tell 2 clears all nine; **§ 4.5** refuses on `Files in scope` naming `.perry/hook.md` + `work/state/hook_TEMPLATE.md`, and `Deliverable` item 5 *"are added to `.perry/hook.md`"* | **REFUSED** |

Five ALLOWED, one REFUSED — the required split, reached independently and by
the same route the round reports.

## 2. Is the procedure reproducible? Three cases the document does not name — **NOT MET (one of three)**

I picked two real specs from the corpus that `dispatch.md` never mentions, and
constructed one to probe an internal conflict I found while walking TASK-107.

**(a) Plainly writes a high-stakes path — `TASK-276`** (unnamed anywhere in
`dispatch.md`). `Files in scope`: *"`schema/state-schema.json` — the `claims[]`
entry and the three record schemas."* `Deliverable`: *"`linkage.jsonl` declared
in `schema/state-schema.json` `claims[]`…"* 4.3: all relative → internal. 4.4
DOING bullet 1 — the round's own verb takes the operation as its object; no
tell-6 pre-commitment; `Out of scope` does not disclaim it. → **REFUSE.**
Decided cleanly. **No guessing.**

**(b) Plainly only cites — `TASK-086`** (unnamed). Fragments `claims`,
`relocate`, `diagnose` all present. `Files in scope` is `bin/perry-lint` +
tests only; `Deliverable` says the round *"READS the claim list that is already
declared there and changes no entry in it"*; `Out of scope` says *"Moving
anyone's files, or running `relocate`. The finding recommends; it never acts."*
Tells 1, 2 and 3 in combination. → **ALLOW.** Decided cleanly. **No guessing.**
(The deleted scanner also passed it, via its discount machinery; the prose
reaches the same answer without any of that machinery.)

**(c) Genuinely borderline — constructed, and it exposes a contradiction in the
document.** A spec with `Files in scope: tests/test_escalation_boundaries.py —
the fixture only` and `Deliverable: the regression fixture asserts that
` `` `~/.claude/skills` `` ` and ` `` `$PERRY_HOME/bin/` `` ` still match, and that
` `` `../sibling/design/` `` ` does not.`

- **§ 4.4 tell 2** ("Quoted as data… matcher examples, test fixtures") → naming
  → **allow**.
- **§ 4.4's DOING list, bullet 2**: *"any foreign-rooted path from 4.3 appears
  **anywhere in scope**"* → those three paths are shapes 2, 3 and 4 → **refuse**.

The document states no precedence between the two, and § 4.5 does not apply.
**I had to guess.** Worse, this is not a corner I invented: it is the document's
own worked example. § 4.4 tell 2 says `~/.claude/skills` and `$PERRY_HOME` in
`TASK-107`'s `Deliverable` are naming, and § 4.5 says TASK-107 is *"**not**
refused by the nine high-stakes fragments its `Deliverable` quotes"* — while the
DOING bullet, read as written, refuses on exactly those two. The round's own
§ 4 walk resolves the conflict silently in favour of tell 2 and the document
never records the resolution.

**The fix is one clause**, and I state it so the reason for the finding is
actionable: scope that bullet to `## Files in scope` — *"any foreign-rooted path
from 4.3 appears in `Files in scope`"* — which is the reading that makes both
halves consistent and matches how the round actually used it.

**Severity.** The ambiguity resolves toward **refuse**, and § 4.6 makes `ask` a
first-class outcome, so a second reader who notices it lands on over-refusal or
a question — never on a dispatch that should have been stopped. **The gate does
not fail open here.** That is why this is recorded as a defect to fix rather
than as the reason for a FAIL.

**Answer: reproducible on the six named cases and on ordinary write/cite cases;
NOT reproducible on a spec that quotes a foreign-rooted path as fixture data.**

## 3. Foreign root: `~/other-project/` refused, `perry/evidence/` allowed, without stripping first — **MET**

`work/reference/dispatch.md § 4.3` is headed *"Decide ownership of every path,
**BEFORE you tidy any text**"* and its first line is *"This step comes first and
its order is the point."* The disambiguation is a **pairing** test, not a
stripping pass:

> An emphasis marker comes in a **balanced pair** wrapping a span… An anchor is
> **unpaired and sits at the head of the path itself**.

followed by *"That test needs no stripping pass at all, which is why it is
stated this way."* The worked table in the file itself carries
`perry/evidence/2026-09/` → allowed, `**perry/evidence/2026-09/**` → allowed
(balanced pair, head is `perry`), `~/other-project/evidence/2026-09/` →
REFUSED (unpaired `~` at the head), `$PERRY_HOME/inputs/` → REFUSED,
`<target>/evidence/` → REFUSED.

Ownership is stated before normalisation, and the reasoning does not require
normalisation at any point. Criterion satisfied as written.

## 4. The five shapes survive, including the unresolved root — **MET**

`dispatch.md:52-56` enumerates all five: absolute, home anchor, variable anchor,
upward escape, and *"5. **unresolved root — `<target>/evidence/`,
`{{project}}/design/`.**"* The safe-direction reason travels with it
(*"A root nobody has resolved is not a root known to be this project"*), and the
prose restatement in `perry/evidence/2026-09/TASK-290-round2-v4-review.md:74-87`
is preserved essentially verbatim, including *"Relative is internal, and that is
the entire rule."*

`tests/test_spec_scannability.py § TestTheTwoClausesAProseRewriteLoses` pins
both clauses as **presence**, scoped to the numbered enumeration, and requires
exactly five items. Verified red by mutation — see § 8, MU1 and MU2.

## 5. No caller survives; the declared deviation — **MET, and the deviation is honest**

```
$ grep -rn "escalation.scan\|escalation_scan\|scan_spec_escalations" bin/ viewer/ tests/ work/ | wc -l
12
```

Twelve hits, not thirteen (same count on `f8f835a` and on `main` — I checked
both with `git grep`). Five are the prose sentences the round declares
(`bin/perry-lint:2954`, `:2972`, `bin/perry-state:27`,
`work/reference/autopilot.md:162`, `work/reference/dispatch.md:14`); the other
seven are inside `TestTheSpecScannerIsGone` and two module docstrings. **The
result document's own wording — *"It returns five live prose sentences as
well"* — is exact.** (The "13 hits / 8 in a guard" figures in the review brief
are a paraphrase and do not match the tree; the round's own text does.)

None of the twelve is a caller. `test_no_caller_survives_in_bin_or_viewer`
sweeps `bin/` and `viewer/` for `scan_spec_escalations`, `escalation_occurrences`
and `P.ESCALATION_TOUCHES`, and
`test_the_flag_is_rejected_rather_than_quietly_accepted` asserts exit 2 plus
`unknown argument` — i.e. the flag cannot come back as a silent `0` that reads
as `pass`. **Keeping five sentences that say the command was removed and why is
a defensible deviation and it is declared as one.**

## 6. `escalation_union` KEPT — the argument judged **SOUND, with one over-citation**

Verified the three surviving consumers exist and none reads a spec:

```
$ bin/perry-state --root . --section project   # project.escalation
keys: ['armed', 'origins', 'project', 'roles', 'unextractable', 'union']
armed: True   union size: 35
$ grep -n matching_escalations bin/perry-lint viewer/parsers.py
viewer/parsers.py:4336: def matching_escalations(...)
bin/perry-lint:1680:    hit = next(iter(P.matching_escalations(hay, stakes)), None)
```

**The argument holds on the merits.** Extracting backticked spans under a named
heading is a bounded, user-declared value space — `ADR-007` rule 1 — not a
regex asking prose a question (rule 2). `USER-916` is about *semantics*
(*"检查文件语义"*), and a list of tokens has none. The structural point is the
strongest part: `DESIGN-006 § 5.2`'s *a role only ever ADDS* is visible in
`origins` and is **invisible** to a reader handed one merged list, so a prose
procedure restates the rule but cannot detect its violation. Deleting the
extractor would also delete the only thing that can tell a user their
high-stakes list is dead prose.

**Over-citation, named.** The round cites `ADR-007` decision 3 — *"The Python
layer never parses a document at all"* — throughout, and the retained extractor
**does** parse a document (`.perry/hook.md`). The round concedes this by
reframing to rules 1 and 2 rather than hiding it, which is the honest move, but
decision 3's literal sentence cuts against the KEEP and the result should say
so plainly rather than leaning on it in both directions.

**The cost is stated by the round and I confirmed it at the source.**
`bin/perry-lint:1674-1685` builds `hay = f"{tid} {title}"` and runs
`matching_escalations` over it — prose, with no way to tell a mention from an
action; `TASK-060`'s title still trips `adopt`. It is a `warn`, never a gate,
and it is outside this row's Bound. **Naming your own residual defect at its
line number is the behaviour this review wants to see.**

## 7. The two corrections that overturn the round's own brief — **BOTH CORRECT**

Re-derived independently. I exported the pre-deletion tree with
`git archive 651a5ca` (the coding branch's base) into the scratchpad and ran the
scanner over all 149 specs, one process per spec, parsing each JSON payload.

```
total specs: 149
verdicts: {'pass': 134, 'refuse': 15}
exit codes: {0: 134, 3: 15}
```

That reproduces the round's corpus table exactly (149 / 134 / 15 / 0, armed,
35 fragments) and confirms the PMO's 2026-09-03 census reconciles at one file
while TASK-290 round 2's *147 / 16* reconciles with nothing.

**Correction A — the nine fragments are all quoted as data. CONFIRMED.** The
scanner's own refusal payload for TASK-107 is
`['$perry_home', '--force-with-lease', 'ln -s', 'ln -sf', 'ln -snf', 'publish',
'published', 'rm -rf', '~/.claude/skills']`. Every one occurs at
`TASK-107-spec.md:62-63`, `:91`, `:93-94` or `:108-110`, and reading those lines
they are, without exception, either an example of what the new matcher must
still match (*"so `~/.claude/skills`, `--force-with-lease` and `$PERRY_HOME`
keep matching"*), an example of morphology (*"cannot match `ln -sf` from
`ln -s`"*), a quotation of the hook's own enumeration (*"The hook already
enumerates forms this way (`publish` and `published`…)"*), or a regression-fixture
list. TASK-107 installs no host skill, publishes nothing, runs no `rm -rf`.
**So the six cases genuinely cannot be separated by fragment presence in either
direction, and the doing-versus-naming shape of § 4.4 is forced.**

**Correction B — ten, not nine. CONFIRMED.**

```
refusals mentioning state-schema.json: 10
['TASK-047', 'TASK-085', 'TASK-100', 'TASK-156', 'TASK-196',
 'TASK-197', 'TASK-201', 'TASK-235', 'TASK-139', 'TASK-276']
```

Five on `state-schema.json` alone, five on `claims` + `state-schema.json`. The
spec's `Out of scope` says nine. The round is right, and it correctly leaves the
underlying policy question to the hook.

## 8. Mutations — 5 planted, 3 red, **2 GREEN**

Harness: anchor by line number **with an assert on the old text at that line**
(one mutation aborted on an anchor miss and applied nothing, which is the harness
working); `__pycache__` cleared before and after; `sleep 1.2` past the
whole-second boundary on both sides; restore with `git show c5cbf79:<path>`,
one path per call; `git status --porcelain` empty confirmed after every restore.

| # | Where | Mutation | Result |
|---|---|---|---|
| MU1 | `dispatch.md:56` | delete list item 5, the **unresolved root** | **red** — `test_all_five_foreign_root_shapes_are_named`: *"the foreign-root enumeration is no longer five items (['1','2','3','4'])"* |
| MU2 | `dispatch.md:40,42` | ownership **after** normalisation (heading + *"normalise the text first, then classify the root"*) | **red** — `test_ownership_is_decided_before_normalisation` |
| MU3 | `dispatch.md:79` | delete **tell 4**, the rule that clears `TASK-244` (replay of the round's declared M7) | **GREEN** — 81 guard tests + all six `dispatch.md`-reading modules stay green |
| MU4 | `dispatch.md:91-98` | **delete the entire § 4.5 standing entry** — the only clause in the document that refuses anything | **GREEN** — 327 tests across `test_spec_scannability`, `test_escalation_boundaries`, `test_claims`, `test_procedures_read_the_contract`, `test_shipped_vocabulary`, `test_diagnose` all pass |
| MU5 | `viewer/parsers.py:4382` | resurrect `scan_spec_escalations` under its own name | **red** — *"`scan_spec_escalations` is back in viewer/parsers.py"* (2 failures) |

**MU3 confirms the round's declared green.** The declaration is honest and the
reasoning for not pinning tell 4 is right: the only guard that catches a
*substantive* weakening of prose is one that freezes the prose, and a frozen
`dispatch.md` cannot be improved.

**MU4 is mine and is the sharper instance.** § 4.5 is the sole clause producing
the one REFUSED verdict the spec requires, and nothing in the suite holds it.
This is **inside the class the round declared** — prose is deliberately unheld
except for the two clauses the earlier reviewer named — and the round's stated
substitute instrument does catch it: delete § 4.5, re-walk the six, and TASK-107
flips to ALLOWED. So MU4 is **an honest limit, not a concealed gap** — but the
round's § 7 illustrates the class with its mildest member. It should have named
its most consequential one.

**The round's own guard-was-green-first incident is reported honestly**, in the
result *and* in the test docstring at
`tests/test_spec_scannability.py § enumeration()`: the first assertion read
`"unresolved root"` out of the worked-paths table below the list and passed
through a deleted clause. It is now scoped to the numbered enumeration and
requires exactly five items — MU1 confirms it is red. *A guard whose mutation
passes is worse than none*, and this one was found and fixed rather than shipped.

## 9. Suite, lint, and the −40 — **MET, re-derived**

```
$ bash tests/run
114 modules · 3251 tests · 178.0s · 8 workers
✓ all green
$ bin/perry-lint --root .
0 error(s), 37 warning(s)
```

Matches the round's figures exactly. **None of the four known unrelated reds
was red** — `test_contract_key_parity` (TASK-335), `test_one_primitive` /
`test_one_choke_point` (TASK-341), `test_host_support` (TASK-313) all passed in
the full run, so no attribution was needed. The round says the same about
TASK-335 and correctly warns that green here is not evidence it is fixed.

**The −40 re-derived from the two changed modules**, base `651a5ca` vs `main`:

| module | at `651a5ca` | now | delta |
|---|---|---|---|
| `tests/test_escalation_boundaries.py` | 64 | 19 | **−45** |
| `tests/test_spec_scannability.py` | 57 | 62 | **+5** |
| | | | **−40** |

3291 − 40 = 3251. ✓ No module was lost (114 both sides).

**One imprecision in the result.** § 2 and § 8 say *"41 scanner tests deleted"*.
Counted per class at the base, the classes deleted outright are
`TestTheSpecScanIsComputed` (6), `TestTheGateAnswersInItsExitCode` (5),
`TestACitedPathIsNotAWrittenOne` (15), `TestTheCharacterClassesTheDiscountHangsOn`
(10), `TestOutOfScopeCannotCancelFilesInScope` (7) and
`TestTheCensusOnThisRepositorysOwnSpecs` (4) = **47**, plus a 6→5 reshape of the
language class and 3 new guards, which is the −45. The headline is right and
every auditable number reconciles; the "41" gloss does not. Minor.

## Findings the round did not record

1. **`.perry/hook.md:9` and `work/state/hook_TEMPLATE.md:9` still describe a
   scan that no longer exists** — *"`/pmo dispatch` scans every spec's
   `Files in scope` / `Deliverable` against this list and refuses on a match"*.
   `.perry/hook.md` is explicitly out of this row's scope, and § 4.5 is right
   that neither file may be edited by an unsupervised round — TASK-339 correctly
   did **not** put them in scope, and would have refused itself if it had. But
   `hook_TEMPLATE.md` ships to every project Perry adopts, so the default
   high-stakes list now advertises a mechanical gate that is gone. The round
   mentions `hook_TEMPLATE.md` only inside its TASK-107 analysis and never lists
   this as a finding. **It needs a user-authorised follow-up row.**
2. **The § 4.4 foreign-root/tell-2 contradiction** (§ 2(c) above). One clause.
3. **`ADR-007` decision 3 is cited on both sides** (§ 6 above).

## Collision watch

`coding/task-285-round4-contradiction-guard` (`e1b0345`) branches from
`d5eaa2f`, which is **after** the TASK-339 merge (`feabad5`), so it already
carries the new `work/reference/dispatch.md`. Its diff against that base touches
only `perry/evidence/2026-09/TASK-285-round4-result.md`. **No collision is
coming from where it stands today**, and its subject (tree isolation, the
`## The tree the agent works in` section) is disjoint from step 4. One thing to
watch: TASK-285's *contradiction guard* and TASK-339's new
*"`Files in scope` cannot be cancelled by `Out of scope`"* rule at
`dispatch.md:89` are about the same idea in the same file; whoever lands round 4
should read § 4.4 before writing a second statement of it.

## Verdict

**PASS.** The decisive criterion is met independently: the six named specs come
out five ALLOWED and one REFUSED when a fresh reader walks the written procedure
by hand, and they come out that way on the **general** tells, not by being
listed — two unnamed corpus specs (`TASK-276`, `TASK-086`) also decide cleanly
in opposite directions. Both corrections that overturn the round's own brief are
correct, and I re-derived each from the pre-deletion scanner rather than taking
them on report: all nine of TASK-107's fragments are quoted as data, and ten —
not nine — of fifteen refusals turn on `state-schema.json`. Every number
reconciles: 149 / 134 / 15 / 0, 3291 → 3251 at 114 modules, 0 lint errors, 12
grep hits of which none is a caller.

What keeps this from being clean is § 2(c): the procedure contradicts itself on
a spec that quotes a foreign-rooted path as fixture data, and the document's own
worked example is the case that trips it. **That criterion is NOT MET.** It does
not overturn the verdict for one reason and I want the reason on the record
rather than assumed: the ambiguity resolves toward **refuse** or toward § 4.6's
`ask`, so the gate degrades to over-refusal and never fails open. It is a
one-clause fix and it should be made before the next dispatch relies on step 4.

The round's disclosure discipline is the other half of the PASS. It falsified
the premise of its own spec and said so at the top of the file; it declared the
green mutation instead of pinning prose to manufacture a red; it recorded that
one of its own guards passed its mutation on first run and fixed it; it stated
what keeping `escalation_union` costs, at the line number where the cost lives;
and it recorded two git mistakes it nearly shipped, including the `git diff main`
trap this project corrected yesterday.

=== RESULT ===
Branch: review/task-339-v4
Verdict: PASS
Criteria met: 8 of 9
Criteria NOT met: Reproducibility on unnamed cases — § 4.4's DOING bullet "any foreign-rooted path from 4.3 appears anywhere in scope" contradicts tell 2 ("quoted as data") on the document's own worked example (TASK-107's `~/.claude/skills` and `$PERRY_HOME`), and no precedence is stated; a second reader can diverge on a spec that quotes a foreign-rooted path as fixture data. Resolves toward refuse/ask, so the gate never fails open. One-clause fix: scope that bullet to `## Files in scope`.
Six named cases, walked by hand: TASK-099 ALLOWED (tell 5), TASK-108 ALLOWED (tell 1), TASK-139 ALLOWED (tell 6), TASK-220 ALLOWED (tell 3), TASK-244 ALLOWED (tell 4), TASK-107 REFUSED (§ 4.5, not on the nine fragments) — five ALLOWED, one REFUSED, the required split
Three unnamed cases you constructed: TASK-276 (writes `schema/state-schema.json` `claims[]`) → REFUSE → no guessing; TASK-086 (reads the claim list, never runs `relocate`, `bin/perry-lint` only in scope) → ALLOW → no guessing; constructed fixture spec quoting `~/.claude/skills`, `$PERRY_HOME/bin/`, `../sibling/design/` as matcher examples with only `tests/` in Files in scope → UNDECIDED → had to guess
Is the procedure reproducible by a second reader: Yes on the six named cases and on ordinary write-versus-cite specs; No on a spec that quotes a foreign-rooted path as data, where §4.4's two halves disagree
Are the round's two corrections to the spec correct: Yes, both, re-derived from the pre-deletion scanner at 651a5ca — all nine TASK-107 fragments are quoted as data (spec lines 62-63, 91, 93-94, 108-110), and ten of fifteen refusals turn on state-schema.json, not nine
Mutations planted: 5, 3 red, 2 GREEN
Tree clean: (empty)
=== END RESULT ===
