# TASK-236 — round 5, V4 review

> Criteria: `perry/evidence/2026-09/TASK-236-spec.md` — the only authority.
> Under review: `888cf365` ("TASK-236 round 5, USER-929 answer C: the join is
> an identity"), read against its parent `f79b75a6`.
> Authority for the round: `USER-929`, answer C (recorded in `f79b75a6`, on
> `main`). `USER-927` read for the principle it set.
> Reviewer: fresh context. I wrote none of this code and none of rounds 1–4.
> Prior rounds: FAIL, FAIL, FAIL, FAIL. Rounds 1–4 were read in order. None of
> their conclusions is relied on below unless re-derived here.

## 0. Base check — done first, and it was NOT already correct

As the dispatch predicted, the worktree was cut at a commit that contained none
of the code under review.

```
git log --oneline -1                           → 583f024f Merge bin-contract-phase-a: …
git branch --show-current                      → worktree-agent-a3a9f7f6601d6a39b
git status --short                             → (empty — clean)
git merge-base --is-ancestor 888cf365 HEAD     → exit 1: HEAD did NOT contain 888cf365
git log --oneline -1 main                      → 888cf365 TASK-236 round 5, USER-929 answer C: …
git rev-parse 888cf365 main                    → 888cf365612ba70bb37cfe0bb58cb2f120c1c65c (both)
git merge-base --is-ancestor HEAD 888cf365     → exit 0 (a fast-forward is legal)
git rev-list --count HEAD..888cf365            → 139
```

**`888cf365` is `main`'s tip, not a strict ancestor of it**, so the dispatch's
"strict ancestor" wording is literally false. What that condition protects
still holds: the commit is on `main`, nothing past it exists to import, and
HEAD was a strict ancestor of it. I fast-forwarded **my own branch only** —
never `main` or any other branch:

```
git merge --ff-only 888cf365612ba70bb37cfe0bb58cb2f120c1c65c   → 583f024f..888cf365, 135 files
git log --oneline -1                                           → 888cf365 TASK-236 round 5, …
git merge-base --is-ancestor 888cf365 HEAD                     → exit 0 (re-asserted)
```

**Two conflicts between the dispatch and `review-constraints.md`, and how each
was resolved.**

1. The constraints say "Do not commit". The dispatch asks for this verdict to
   be committed on my own branch. I followed the dispatch for this file only:
   staged by explicit path, and no other path was touched.
2. The constraints recommend pointing the live `bin/perry-restore-check` at a
   scratch copy with `--root <copy>`. **That refuses:**
   `perry-restore-check: 888cf365 is not a commit in <scratch>/r5m`, rc 2. It
   resolves the ref inside `--root`, and a `git archive` copy has no objects.
   I did not substitute a weaker check. The comparison stayed against the ref:
   every file was read from `git -C <worktree> show 888cf365:<path>` and
   compared byte for byte (§ 4). The refusal itself is recorded as ROW-4.

**The repository under review was not modified.** Every destructive or writing
check ran in `git archive` exports under the session scratchpad: `r5`
(`888cf365`, probes and suite), `r5p` (`f79b75a6`, the before state) and `r5m`
(`888cf365`, mutations only). Fixture projects lived in scratchpad
directories. No Perry writer ran against this repository. `git status --short`
in the worktree was empty both before and after all the work.

## 1. What the change claims, and the one question V4 asks of it

A makes `overall_kr_model` key a version's objectives by stripped id, refuse a
version where two objectives share one, and place key results by lookup.
Blank ids are deliberately not keys. B adds a pass zero to `mint_objective_ids`
that refuses two titled objectives sharing a title inside one version.

The question: **does this code do the wrong thing on an input the user can
produce?** I found no input on which it does. What follows is the enumeration
behind that answer, and then four things that are real but grade ROW.

## 2. A — is the join now an identity? Enumerated, driven, not read

Every case below ran through the shipped `perry-goals krs --level overall
--json` of the copy, on fixture stores built from literals. "Before" is
`f79b75a6`, "after" is `888cf365`.

| # | store | before | after |
|---|---|---|---|
| 1 | round 4's: 3 KRs, two objectives both `O-1` | rc 0, **6 rows** | rc 1, names `O-1`, `Objective A`, `Objective B` |
| 2 | `O-1` and `O-1 ` (NBSP) | rc 0, **2 rows for 1 KR** | rc 1, collision (`str.strip` removes NBSP) |
| 3 | `O-1` and `o-1` (case), one KR each | rc 0, 1 + 1 | rc 0, 1 + 1, each under its exact id |
| 4 | `O-1` and `O-1​` (ZWSP), 3 KRs naming `O-1` | rc 0, 3 + 0 | rc 0, 3 + 0 |
| 5 | `O-1` and `Ｏ-1` (fullwidth), 1 KR | rc 0, 1 + 0 | rc 0, 1 + 0 |
| 6 | an objective id equal to a KR id in another version, `--version all` | rc 0, 3 placed once | rc 0, 3 placed once |
| 7 | a KR naming an objective id that exists only in another version | rc 1 residual | rc 1 residual |
| 8 | KR `version` padded with a trailing space, default and `all` | rc 1 residual | rc 1 residual |
| 9 | non-string objective `id` (int) | rc 1 validator | rc 1 validator |
| 10 | two blank-id objectives, no KRs | rc 0, empty tables | rc 0, empty tables |
| 11 | duplicate in v1 only, default render (v2) | rc 0, v2 correct | rc 0, v2 correct |
| 12 | live `perry/okr.jsonl`, default / `--version all` | 19 under 5 / 38 under 10 | identical |

**No store placed a key result under an objective it does not name, or under
two.** Cases 3–5 are distinct strings and are rendered as distinct ids. That is
what an identity on the stored string should do, not a gap: nothing is
multiplied, dropped or misattributed, and each KR lands under the one record
carrying exactly its key. Case 10 is round 4's lead, which it did not charge;
I did not charge it either. A zero-width or fullwidth lookalike would be a
store a human cannot read correctly; that concern belongs to the validator,
not to this join, and I did not charge it.

**The three `.strip()` calls, not two.** The comment above the loop says round
4 found "either `.strip()` deletable" and the tests "pin both". The code now
has **three**: the `by_id` loop (`bin/perry-goals:2971`), the KR side (`:3000`)
and the emission loop (`:3005`). All three are pinned: MA3, MA4 and MA5 are red
in § 4. The third matters most. With it deleted, a padded objective id marks
its KRs placed in `rows_for` but emits them nowhere, which is a silent drop the
residual cannot see. `test_a_padded_id_on_the_objective_is_the_same_id` catches
that.

**A before the residual, and the residual after it: can they contradict?**
Driven on the three shapes where both could fire:

| store | wanted | message |
|---|---|---|
| duplicate `O-1` and a blank-keyed KR, same version | default | A only (`888cf365^` gave the residual only) |
| duplicate in v1, orphan in v2 | `--version all` | A for v1. After fixing it, the residual for v2 |
| duplicate in v1, orphan in v2 | default (v2) | residual only. The v1 duplicate is out of scope, consistent with the residual's scoping |

The two never appear in one message. A tells the reader to give each objective
its own id. The residual tells them to give each KR an `objective_id` that
exists. Neither undoes the other, and fixing A's complaint first is the right
order, because until ids are unique no KR can be placed correctly. One
pre-existing blemish, not introduced here: with `--version all` the residual
names a KR id repeated across versions without its version
(`O1-KR1, O1-KR1, O2-KR1`). That text is round 2's.

**Every other join on `objective_id`, enumerated.** `grep -rn objective_id bin
viewer`: the only reader is `bin/perry-goals:3000`. The mint writes the field
(`bin/perry_md_store.py:584`). `viewer/parsers.py:4055/4255` and
`bin/perry-lint:1428` derive objective membership from the KR id's prefix
(`kr_objective_id`), not from this field. There is no second copy of the join.

## 3. B — what can still give two objectives in one version one id

**Titles, through the documented path.** Each row is an `OKR.md` fixture taken
through `perry-okr write --from-file` → `perry-okr migrate-ids`, then
`perry-goals krs`, `perry-okr verify` and `perry-okr diff`, on both copies:

| second heading in the same `## v1` block | before: ids / rows | after: `migrate-ids` |
|---|---|---|
| `Objective 2 — Reliability` (exact twin) | `O-1`,`O-1` / **6 rows for 3** | rc 1 pass zero, store unchanged |
| `Objective 2 — Reliability  ` (trailing spaces) | `O-1`,`O-1` / **4 for 2** | rc 1 pass zero |
| `Objective 2 — Reliability ` (NBSP) | `O-1`,`O-1` / **4 for 2** | rc 1 pass zero |
| `Objective 2: Reliability` (other separator) | `O-1`,`O-1` / **4 for 2** | rc 1 pass zero |
| `Objective 2 — reliability` (case) | `O-1`,`O-2` / 2 | rc 0, `O-1`,`O-2`, 2 rows |
| `Objective 2 — Reli  ability` (internal space) | `O-1`,`O-2` / 2 | rc 0, `O-1`,`O-2`, 2 rows |
| `Objective 2 — Reliability​` (ZWSP) | `O-1`,`O-2` / 2 | rc 0, `O-1`,`O-2`, 2 rows |
| v1 `Reliability`; v2 `Reliability` twice | `O-1`×3 / **4 for 2** in v2 | rc 1, names the v2 block |

Every title variant the scanner normalises (`objective_title` strips the
separator and surrounding whitespace, including NBSP) now refuses. Every
variant it does not normalise gets **distinct** ids, which is the safe
direction: two ids for two objectives is never a doubled row. Before
`888cf365`, five of these rows over-counted at rc 0 with `verify` rc 0,
`diff` `(0, true, true)` and `perry-lint`'s OKR line clean. All eight are
correct after it.

**The stated-id path is the one that still produces a collision (ROW-1, § 5).**
Pass zero keys on `(version, title)`, so two *different* titles in one version
never meet there. Pass one keys `by_title` on title alone and accepts two
different titles that carry the same stated id. Pass two then lends that id
through `reused` (`bin/perry_md_store.py:548`). Driven through the CLI:

```
store:  v1 "X" id O-1 · v2 "Y" id O-1 (a rename, id kept by hand) · v2 "X" id ""
perry-okr migrate-ids   → rc 0, "minted 0 objective id(s) (), reused 1 on a repeated version"
ids after               → v1 X O-1 · v2 Y O-1 · v2 X O-1
perry-goals krs         → rc 1, "O-1 is carried by 'Objective 1 — Y', 'Objective 2 — X'"
```

On `f79b75a6` the same store rendered **4 rows for 2 KRs at rc 0**. So A turns
this into a loud refusal, and that is why it grades ROW rather than FAIL.

**Can a user reach that input without hand-editing ids?** I checked, and I
could not reach it. Rename survival (DESIGN-009 step 5) is not implemented, so
a renamed heading gets a new record with `id: ""`. On a store that already
carries ids, `write --from-file` refuses because every minted id appears in
`would_discard` (R3/R4 below). The only producer I found is a hand edit of
`okr.jsonl`, which round 1 established is how KRs are now authored.

**DESIGN-009 step 1 → step 3 on a correct `OKR.md` still completes.** Measured
on `888cf365` for: two distinct objectives in one block; two blocks restating
both; case variants; internal whitespace; a Chinese document (`目标 1：稳定`,
`目标 2：速度`). In every one, `write --from-file` rc 0 and `migrate-ids` rc 0
with the expected ids. `krs` placed every KR exactly once, default and `all`.
`verify` rc 0, and `diff` rc 0 with both keys `true`. In between steps, `krs`
refuses the step-1 store via the residual, which round 4 already found is not
a break in the documented sequence.
`TestTheObjectiveIdIsMinted.test_the_render_gate_still_holds_after_the_mint`
covers the same on this repository's own unminted store and is green.

## 4. Mutations — line-anchored, in `r5m`, restores checked against the ref

Harness: `<scratchpad>/mut.py`. Each mutation finds its target line inside the
named function's window, asserts it is unique and that the substring occurs
exactly once on that line, and edits only that line. MB5 moves a block located
the same way. `__pycache__` was cleared and 1.2 s waited before every run.
Each restore wrote `git show 888cf365:<path>` bytes back and asserted equality
against them. The file was also asserted equal to the ref **before** each
mutation, so a pre-mutated baseline could not be restored "OK". Modules run
each time: `tests.test_okr_krs_render` (40), `tests.test_md_store` (76) and
`tests.test_handed_back_root` (22). Baseline: all OK.

| # | mutation | line | result |
|---|---|---|---|
| MA1 | `if shared:` → `if False and shared:` | goals:2978 | RED 4 |
| MA2 | blank ids become keys (`if not oid:` → `if False:`) | goals:2972 | RED 4 (`TestABlankJoinKeyIsNotAWildcard`) |
| MA3 | `.strip()` off the `by_id` loop | goals:2971 | RED 2 |
| MA4 | `.strip()` off the KR side | goals:3000 | RED 1 |
| MA5 | `.strip()` off the **emission** loop | goals:3005 | RED 1 |
| MA6 | `if oid else []` deleted | goals:3006 | **GREEN** — ROW-3 |
| MA7 | KR version filter off | goals:2998 | RED 8 |
| MA8 | a duplicate silently overwrites (`if oid in by_id:` → `if False:`) | goals:2974 | RED 4 |
| MA9 | root dropped from A's `migrate-ids` hand-back | goals:2991 | RED 1 (`test_handed_back_root`) |
| MA10 | collision checked across all versions (`for o in vobjs` → `objectives`) | goals:2970 | RED 23 |
| MB1 | `if collisions:` → `if False:` | store:499 | RED 2 |
| MB2 | pass-zero key ignores version | store:497 | RED 9 + 1 error |
| MB3 | threshold `> 1` → `> 2` | store:498 | RED 2 |
| MB4 | root dropped from pass zero's hand-back | store:512 | RED 1 (`test_handed_back_root`) |
| MB5 | pass zero moved above the untitled guard (B3′) | store:473–513 → 463 | RED 1 (`test_the_untitled_guard_runs_before_pass_zero`) |
| MB6 | untitled guard off | store:464 | RED 2 |

**The author's table reproduces**: A1 4, A3 2, A4 1, A5 23, B1 2, B2 9 + 1
error, and B3′ red all match mine.

**Closing state**, independent of the harness: `<scratchpad>/restore_cmp.py`
compared nine paths in each of `r5m` and `r5` against
`git -C <worktree> show 888cf365:<path>`. The paths were `bin/perry-goals`,
`bin/perry_md_store.py`, the three test modules, `perry/okr.jsonl`,
`perry/OKR.md`, `viewer/parsers.py` and `bin/lib/__init__.py`.
**18 of 18 OK, 0 mismatches.**

## 5. Leads, each checked

**Lead 1 — every comment in the diff that says "measured" or quotes a number.**

| claim | where | checked | holds |
|---|---|---|---|
| "measured, three key results rendered as six" | A's refusal text | round 4's store on `f79b75a6`: rc 0, `krs: 6` | yes |
| "Measured: a store of three key results rendered six, at exit 0, with `perry-okr verify`, `diff` and `perry-lint` all clean" | pass-zero comment | documented path on `f79b75a6`: `migrate-ids` rc 0 (`O-1`,`O-1`), `krs` rc 0 6 rows, `verify` 0, `diff` `(0, true, true)`, lint `OKR store: 6 record(s), 0 row(s) drifted` | yes. `perry-lint`'s overall rc is 1 for an unrelated reason, identical in the distinct-title control |
| "Round 4's reviewer deleted it with all 33 tests green" | two test docstrings | `f79b75a6` module = 33 tests; round 4 § 3 records M2/M2b green | yes |
| "Mutating the skip away left all 76 tests green" | result § 3, commit | the skip no longer exists; 76 reproduces as the module size | size yes; the green run is not re-runnable |
| `66 → 68`, both new hand-backs | `test_handed_back_root` | parent 22 OK at 66, child 22 OK at 68; MA9 and MB4 each redden it | yes |
| A1–A5, B1–B3′ counts | result § 5 | § 4 above | yes |
| "the live project 19 under 5 → 19 under 5" | result § 1 | table § 2 row 12 | yes |
| objective `" O-1 "`, KR `"O-1"` → "3 placed" | result § 1 | not run; the pinning test uses 2 KRs | **not checked** |

No false "measured" claim found in code comments.

**Lead 2 — every command a new refusal hands back.** Both are rooted (MA9, MB4
red), and `lib.root_flag` returns `""` only when handed no root, which neither
call site does. **Being rooted is not the same as working.** I ran each one as
printed (`<scratchpad>/recover.py`, R1–R4) and found ROW-2.

**Lead 3 — tests passing on an earlier guard.** Every one of the seven
`TestTheJoinIsAnIdentity` tests and the four new mint tests reddens under a
mutation of the code it is named for:
- `…sharing_an_id_are_refused`, `…names_the_id_and_both_objectives` and
  `…nothing_is_printed_beside_the_refusal`: MA1 and MA8.
- `…one_id_in_two_versions…`: MA10 and MA7.
- `…padded_id_on_the_objective…`: MA3 and MA5.
- `…padded_id_on_the_key_result…`: MA4.
- `…two_padded_spellings…`: MA1 and MA3.
- `…sharing_a_title_in_one_version…` and `…stated_id_does_not_let_a_same_titled_twin…`:
  MB1 and MB3. The stated-id test asserts only `Refused`, but no other guard
  fires on its input, so it is not passing on an earlier one.
- `…one_title_in_two_versions…`: MB2.
- `…untitled_guard_runs_before_pass_zero`: MB5 and MB6.

None passes for the wrong reason.

## 6. Findings — all ROW, each with the consequence that grades it

**ROW-1 — `migrate-ids` still writes a same-version id collision on the
stated-id path, at rc 0, and A's refusal then blames the wrong cause.**
`bin/perry_md_store.py:531` checks the stated ids only between records with
*equal* titles. Pass two then reuses by title (`:548`). So a store where one
id sits on two titles across versions gets that id lent to a third record in
the same version, and the report calls it "reused 1 on a repeated version".
The render refuses the result (§ 3). Its message says `perry-okr migrate-ids`
"used to mint one id for two same-titled objectives … and now refuses to; a
store it wrote before that is the likeliest source". For this store that
misleads twice: the titles differ, and the store was written by the current
tool. **Grade ROW:** the only producer is a hand-edited id. The render refuses
loudly, naming both objectives, and nothing is printed as fact. The id
overwritten was `""`, so no stored value is lost. This is the one place
USER-929's stated purpose for B, "so that Perry's own migration tool stops
producing a store A refuses", is not fully met.

**ROW-2 — both refusals hand the reader a next step that itself refuses.**
Pass zero says "Give each a distinct title in OKR.md and re-run `perry-okr
write --from-file --root <p>` first". Retitling means editing the heading.
`record_key` embeds the heading for the objective and for every KR under it.
So `write --from-file` then refuses with "the whole record would be dropped"
on **every** store pass zero can meet:
- the step-1 store with blank ids (R1: rc 1);
- a store the old tool minted `O-1`/`O-1` (R2: rc 1).

The escape that works, "move okr.jsonl aside and re-run", appears only inside
that second refusal. A's remedy, "Give each objective its own id in the store",
has no tool path at all:
- `migrate-ids` refuses first, on pass zero (R2: rc 1, run exactly as A printed it);
- `write --from-file` refuses (R2: rc 1).

**Grade ROW:** every step refuses loudly, none writes, and the store and file
are unchanged throughout. The reader is misdirected once, never misinformed
about the data.

**ROW-3 — `if oid else []` at `bin/perry-goals:3006` is unreachable.**
`rows_for` is built from `by_id`, and blank ids never enter `by_id`
(`:2972`), so `rows_for.get("", [])` is already `[]`. Deleting the condition
(MA6) leaves all 138 tests green, and no input can tell the two apart. It is
the author's disclosed Lead-1 shape (a guard with nothing to guard), found one
line from A's new code. **Grade ROW:** no behaviour. One consequence worth
knowing: under MA2 (blank ids as keys) this dead condition turns what would be
a cross product into a silent drop. That regression would still be caught
(MA2 is red 4).

**ROW-4 — `bin/perry-restore-check --root <git-archive copy>` refuses**, the
workflow `review-constraints.md § Verify a restore against an independent
source` recommends by name: rc 2, "888cf365 is not a commit in <copy>". The
tool resolves `<ref>` inside `--root`. **Grade ROW:** a reviewer's helper, not
a user input. It is recorded because the next round will hit it too.

## 7. The suite

Run in the `r5` copy (never the worktree): `bash tests/run` →
`130 modules · 3812 tests · 186.7s · 8 workers · ✗ 5 of 3812 TEST(S) failed`.
Tree guard: `✓ nothing under <scratchpad>/r5 moved`. Each red module was
**re-run alone** and reproduced:

- `test_contract_key_parity` — 2 (`…without_the_witness_the_four_are_unobservable`,
  `…same_mutation_is_silent_without_the_witness`). These are the round's named
  standing reds.
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` — clock-dependent,
  the round's named standing red.
- `test_blank_cell_is_one_rule.TestTheSpellingThatWasDropped.test_it_is_not_declared_and_nothing_writes_it`
  — `git ls-files` exits 128: **the copy is not a git repository.**
- `test_one_header_rule.TestAVanishedFileIsSkippedButATrackedOneIsNot.test_git_tracks_answers_both_ways`
  — `_git_tracks` is `False`: **same cause.**

None of the three modules under review is red. The copy ran **3812** tests
where the round reports **3814**. I did not find the two; see below.

## What I did not check

- **The full suite in a git checkout.** It ran only in an archive copy, which
  cannot run the two git-dependent tests. The 3812-vs-3814 gap is unexplained.
- **`perry-okr render --write`**, and the text (non-`--json`) render of A's
  refusal. JSON mode only.
- **Result § 1's `" O-1 "` → "3 placed" row.** Not run.
- **The "76 green with the skip" run.** The skip is gone. I reproduced the
  module size, not the green.
- **Whether any real project (`gimegime-pmo`, `PolyForge`) carries two
  objectives with one title in a block**, or a hand-kept id across a rename.
  Fixtures only.
- **`perry-goals list`, `perry-state` and the viewer on a colliding store.**
  I confirmed they do not join on `objective_id`. I did not render them. The
  validation gap between readers is the user's recorded property (`USER-929`).
- **Unicode normalisation of titles (NFC vs NFD)** beyond NBSP, ZWSP and
  fullwidth ids, and case-folding of ids beyond one case pair.
- **Concurrency**, Windows paths, and a root containing spaces for the two new
  hand-backs (`shlex.quote` is in `lib.root_flag`; not driven).
- **Rounds 1–4 as claims.** Read for shape. Only round 4's `33` and M2/M2b
  greens were re-checked, via the parent's module size and the author's own
  pins.

```
=== VERDICT ===
task: TASK-236
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-236-spec.md
checked: base check first — HEAD was 583f024f and lacked 888cf365; tree clean;
         888cf365 is main's tip (not a strict ancestor), HEAD a strict ancestor
         of it, so my own branch only was fast-forwarded (139 commits) and
         re-asserted. All work in git-archive copies of 888cf365 and
         f79b75a6; the worktree is unmodified apart from this file. A driven
         on 12 hand-built stores before and after: duplicate, NBSP, case,
         ZWSP and fullwidth ids, cross-version id/KR-id clashes, padded
         versions, int ids, the live store (19/5, 38/10) — no KR placed under
         an objective it does not name or under two. B driven through
         write --from-file → migrate-ids → krs/verify/diff on 11 OKR.md
         fixtures including eight title variants, a v1+v2 twin, a
         restated two-version document and a zh document — five
         over-counting cases before, all eight variants correct after; DESIGN-009
         step 1→3 completes on every correct document. The stated-id path
         through the CLI. Every new refusal's hand-back run as printed (R1–R4).
         Sixteen line-anchored mutations (MA1–MA10, MB1–MB6) over three
         modules, 15 red and 1 green, restores asserted against git show
         888cf365 bytes before and after, then 18/18 paths byte-equal to the
         ref by an independent comparison. Every "measured" claim in the diff
         re-derived on f79b75a6. Suite in the copy: 5 reds, each re-run alone
         and attributed.
not-checked: the suite in a git checkout and the 3812-vs-3814 gap;
         perry-okr render --write; the text-mode refusal; result § 1's
         " O-1 " → 3 row; real projects' OKR.md for duplicate titles; list,
         state and viewer on a colliding store; Unicode normalisation beyond
         NBSP, ZWSP and fullwidth; roots with spaces; concurrency; rounds 1–4
         beyond round 4's 33 and M2/M2b.
proof: bin/perry-goals:2970-2991 builds by_id per version and refuses a
         shared id before bin/perry-goals:2996-3003 places any KR by lookup,
         so round 4's store (3 KRs under O-1 twice) goes from rc 0 with 6 rows
         on f79b75a6 to rc 1 naming O-1 and both objectives on 888cf365; MA1,
         MA8 and MA10 redden 4, 4 and 23. bin/perry_md_store.py:494-513
         refuses equal titles in one version before any id is minted, so the
         exact, trailing-space, NBSP and other-separator twins that minted
         O-1,O-1 and rendered 6-for-3 or 4-for-2 at rc 0 (verify 0, diff
         true/true) now stop at rc 1 with the store unchanged; MB1–MB3 and
         MB5 redden. Residuals graded ROW in § 6: bin/perry_md_store.py:531
         and :548 still lend a hand-stated id to a second title in one
         version (rc 0; render then refuses); both refusals hand back a
         command that refuses; bin/perry-goals:3006 `if oid else []` is dead
         (MA6 green); perry-restore-check --root refuses an archive copy.
=== END VERDICT ===
```

## Rows to file — the PMO's call; no identifier minted

1. **`TASK-0NN`** — `mint_objective_ids` pass one (`bin/perry_md_store.py:531`)
   checks stated ids only among equal titles, so pass two (`:548`) can lend
   one hand-stated id to a second title inside one version at rc 0. Either
   refuse a stated id carried by two titles, or run A's per-version uniqueness
   rule on the minted output before writing. Correct A's refusal text, which
   names `migrate-ids` as a past-only source.
2. **`TASK-0NN`** — both round-5 refusals hand back a next step that refuses on
   the store they fired on: `write --from-file` after retitling (record keys
   embed the heading), and A's "give each objective its own id" (no tool does
   it). Name the path that works: move `okr.jsonl` aside, `write --from-file`,
   `migrate-ids`.
3. **`TASK-0NN`** — `bin/perry-goals:3006` `if oid else []` is unreachable
   (MA6 green over 138 tests). Delete it, or state why it stays.
4. **`TASK-0NN`** — `bin/perry-restore-check --root <git-archive copy>` refuses
   with "not a commit", contradicting `review-constraints.md`'s instruction to
   use exactly that. Resolve `<ref>` against the helper's own repository, or
   change the instruction.
