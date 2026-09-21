# Architecture re-review 5: the entry-skills and TASK-471 candidate, after 42556e76

This is the fifth re-review of one integration candidate. The user authorised it.
The prior verdict is `2026-09-21-architecture-rereview-4.md` in this directory.
It was BLOCKED on descriptive wording only (D1 to D5), and it found that the
behaviour follows NN-1 as amended by USER-981. The earlier verdicts it cites are
in this directory too.

The fix is one commit. `git log --oneline 0425f82d..c9262965 -- . ':!perry' ':!.perry'`
lists only 42556e76. c9262965 merges it with 5056aeef, which carries re-review
4's evidence. 42556e76 changes comments and docstrings only, in these files:

- bin/perry-goals, perry-lint, perry-state and perry-task
- viewer/parsers.py
- tests/test_blank_cell_is_one_rule.py, test_goals_objective_add.py,
  test_okr_store_is_the_source.py, test_phase_lifecycle.py and
  test_startup_routing.py

It changes no executable line, and it does not touch ARCHITECTURE.md,
bin/ARCHITECTURE.md, SKILL.md, a lane file or reference/.

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: Claude Code subagent (claude-opus-5), fresh context, worktree agent-a9622d3ac70fcfdb0. I did not write TASK-469/470/471/474/475, the USER-978/980/981 fixes, b99c861a or 42556e76, and I carry none of their conversation. I used no author compliance verdict. Timestamp: 2026-09-21T07:22:09Z
Base: 820da3b1849df4f7155baf976b1045c6590bd129
Head: c9262965e6340c8c77649c002456f381fa84466e
Triggers:
- Listed boundary paths: TRUE. `git diff --name-status 820da3b1 c9262965` changes viewer/parsers.py, SKILL.md, goals/SKILL.md, work/SKILL.md and decide/SKILL.md. schema/ and bin/lib/ are unchanged. Since 0425f82d, parsers.py changes only in read_phase_pointer's docstring (:3037-3039).
- New top-level directory: FALSE. `git ls-tree -d --name-only` lists the same 17 directories at base and at head.
- New bin executable: FALSE. `git diff --raw 820da3b1 c9262965 -- bin schema` has only M entries, and every mode is unchanged (100644 or 100755 on both sides).
- Contract-version change: FALSE. schema/ is unchanged. 42556e76 changes no root architecture section, and no code path.
- Root architecture edit: TRUE, but not since re-review 4. ARCHITECTURE.md is byte-identical at 0425f82d and c9262965. The earlier edits (2225d076 for USER-978, b99c861a for USER-981) were reviewed then.
- Module architecture edit: TRUE, but not since re-review 4. bin/ARCHITECTURE.md is byte-identical at 0425f82d and c9262965.
Context: Root ARCHITECTURE.md at head: §3 Forbidden at :160-167 (a second reader at :161), §6 NN-1 at :243-256 (Known exceptions :250-256) and §8 at :366 (the USER-981 entry is :368-371). Component mapping is unchanged from re-review 4, from the confirmed §2:
  - `bin/` covers the four tools that were edited.
  - `viewer/parsers.py` is its own component.
  - `tests/` covers the five test modules.
  The only declared module document is bin/ARCHITECTURE.md v1, which is unchanged. No trigger fact is unresolved.
Rules:
- ARCHITECTURE.md:43-56 (§1), :100-118 (§2), :157-158 (§3 directions), :162-167 (§3 other Forbidden), :213-240 (§5), :258-303 (NN-2 to NN-6), :318 (OQ-2) — not touched by 42556e76. It changes only comments. Re-review 4's findings (holds) stand.
- ARCHITECTURE.md:161 (§3 Forbidden, a second reader) and :243-256 (§6 NN-1 with its two Known exceptions) — holds for the behaviour. Every read of phase/CURRENT's value in bin/ and viewer/ goes through parsers.read_phase_pointer (parsers.py:3041-3045). I grepped `CURRENT` across bin/ and viewer/. The other hits are prose, the lock path list (perry-goals:4873) and perry-diagnose:2092, which tests only whether the file exists and reads no value. release/manage.py is covered by the exception at :254-256.
- The corrections to re-review 4's findings:
  - D1 — CORRECTED, and the new text holds. The five code comments are now "the pointer reader for `bin/` and `viewer/`": perry-goals:4737, perry-lint:1309-1310, perry-state:1938, and perry-task:2911-2912 and :2930-2931. The class docstring (tests/test_phase_lifecycle.py:537-539) now says the same and names release/manage.py's exception. The stale caller list is gone. tests/test_blank_cell_is_one_rule.py:244 now says "the reader for `bin/` and `viewer/`". I swept the tree outside perry/ for "one reader / only reader": no remaining hit is about phase/CURRENT, apart from the pre-existing root §2 heading (see Notes).
  - D2 — NOT FULLY CORRECTED. The correction adds a false claim. tests/test_phase_lifecycle.py:557-558, in the docstring of test_nothing_else_reads_the_pointer_value, says: "It catches a revert of the perry-task and perry-state sites directly." That holds for perry-task (R3 and R4 turn the method red). It does not hold for perry-state. I restored perry-state's pre-5a08b22b code, `cur_pointer = root / "phase" / "CURRENT"` / `if cur_pointer.exists() and not snap.phase:`, on a scratch copy (R6). The method stays GREEN, because the detector's regex (:584) looks for read_text(, read_bytes( or open( and the old site calls only .exists(). The class goes red only through its behavioural sibling, test_state_does_not_warn_after_a_close (:592). Re-review 4 already recorded that R6 is "guarded by the behavioural test … not by the detector", so the correction states the opposite of the finding it answers. The rest of the new docstring holds:
    - "perry-goals' old read went through a helper … red on that revert only because the old code's comment contained `read_text()`". R1 turns the method red. R1b is the same revert without the comment, and the method stays green.
    - "test_blank_cell_is_one_rule's check for a literal 'no phase' set is what catches that revert". R1b turns test_no_site_decides_blankness_for_itself red.
    - "a read through a helper function" was added to the list of what it cannot see. That is true: R1b and R1c both leave the method green.
    parsers.py:3037-3039 ("a regression guard for some of the sites fixed here; its docstring says which") points at that sentence, so it inherits the error. At class level parsers' phrase is true, because the class does catch R6.
  - D3 — CORRECTED, and the new text holds. tests/test_goals_objective_add.py:117-120 says the old-slug records stay the phase's "to `parsers`' linkage readers and to perry-goals. Not to `perry-state`". parsers groups by number: load_linkage → linkage_records_for_phase (parsers.py:4461-4522, `startswith(f"{number}-")`). perry-goals groups by number too (:4190, :4253 and :4423 use linkage_phase_number). perry-state compares the exact slug (:2315, :2336), as re-review 4's rename probe showed.
  - D4 — CORRECTED, and the new text holds. tests/test_startup_routing.py:304-308 is now scoped to "the entry files that carry the route rule". I counted, with line wrapping folded, the non-perry/ .md files that name "Pack capabilities and controls". Thirteen do. Three are in PACK_SITES: goals/SKILL.md, work/SKILL.md, and reference/config.md, which holds the section. That leaves exactly ten others, so "about ten more pages" holds, and reference/router-subcommands.md is one of them. decide/SKILL.md does not name the procedure. It carries the route rule at :40 ("Run before any subcommand but `help`; a question takes the router's Explain or Query route instead").
  - D5 — CORRECTED, and the new text holds. tests/test_okr_store_is_the_source.py:446-448 says that perry-lint reports a pointer to a missing document as an error, and that load_snapshot continues with no phase. perry-lint:1316-1319 emits a Finding with severity "error" (rule current-phase-resolves). parsers.py:5240-5251 leaves phase=None and still loads the linkage slice by the slug's number.
- ARCHITECTURE.md:368-371 (§8 USER-981 entry: "The pointer reader's claims in `viewer/parsers.py` and its test are narrowed to what they cover") — the class docstring is now narrowed, so re-review 4's partial finding is resolved for it. The test method's new sentence at :557-558 is the D2 residue above, and until it is fixed the entry is not fully true of "its test".
- SKILL.md:48-70 (the V5-signed hand-off contract, decided) — holds, byte for byte. I compared it independently with sig.py (output in sig.out), base 820da3b1 against head c9262965:
  - signature record, 5 lines: fbee743b839fab6a
  - invariant heading: 9c438a5eb94b903c
  - invariant: 29e4aba4384469d3
  - table intro: 3bd4965eb3b9607c
  - ownership table, 5 lines: 2ef99903b5582ee6
  - the "only writer" paragraph: 7245e781829261fc
  - the three refusal cases: d8c71ea2b3361b02
  All are IDENTICAL.
- bin/ARCHITECTURE.md (all sections, including NN-B1 to NN-B4) — not touched since re-review 4. That round's findings (holds) stand.
Decision: BLOCKED. One descriptive mismatch needs correction and re-review. It contradicts no decided rule's substance: the code obeys NN-1 as amended, and the V5 contract is unchanged. D1, D3, D4 and D5 are corrected, and each correction is true. D2's correction introduces a false claim:
  (E1) tests/test_phase_lifecycle.py:557-558, "It catches a revert of the perry-task and perry-state sites directly". This is false for perry-state. The pre-5a08b22b revert (R6) leaves test_nothing_else_reads_the_pointer_value green (probe5.out). Only test_state_does_not_warn_after_a_close (:592) catches it. Bucket: written by this candidate (42556e76), so it counts. The fix is wording only, either of:
    - "It catches a revert of the perry-task sites directly; perry-state's old site read no value (`.exists()`), and `test_state_does_not_warn_after_a_close` below catches its revert."
    - Drop "and perry-state".
    parsers.py:3037-3039 needs no change once the method docstring is right.
User decision required: none.
Not checked:
- I ran no full suite. The PMO ran it green (158/4460) on this exact tree, and 42556e76 changes no executable line. On a scratch copy I ran TestThePointerHasOneReader and test_blank_cell_is_one_rule: first the baseline, then 7 reverts (R1, R1b, R1c, R2, R3, R4, R6). In the copy, test_blank_cell_is_one_rule.TestTheSpellingThatWasDropped errors at baseline and under every revert, because it runs `git ls-files` and the `git archive` copy is not a repository. That is an artefact of the copy, so I read the discriminating test, test_no_site_decides_blankness_for_itself, instead.
- I did not re-run R5 (the load_snapshot revert). The new docstring makes no claim about it, and re-review 4 recorded it as caught.
- I did not re-run re-review 4's rename probe for D3. I checked the grouping code by reading it.
- I did not sweep the candidate's whole diff for category claims again. The sweep covered 42556e76's added lines in full (every one is listed in the Notes), plus a tree-wide "one reader / only reader" grep outside perry/. Re-review 4's sweep of the rest stands.
- After writing this file I ran tests.test_diagnose on the reviewed tree.
=== END COMPLIANCE ===
```

## Supporting notes

### Candidate binding

The worktree was cut from origin/main at 0b5bf99e, with no branch commits and a
clean tree. 0b5bf99e is an ancestor of c9262965, so I fast-forwarded it with
`git merge --ff-only c9262965`, which the PMO authorised. HEAD is
c9262965e6340c8c77649c002456f381fa84466e. I read 42556e76 in full and
re-review 4 in full.

### Every line 42556e76 added, and whether it holds

| Site | Claim | Result |
|---|---|---|
| bin/perry-goals:4737 | "the pointer reader for `bin/` and `viewer/`" | holds |
| bin/perry-lint:1309-1310 | same wording, plus "`release/` holds a recorded exception, USER-981" | holds (ARCHITECTURE.md:254-256) |
| bin/perry-state:1938 | "through the pointer reader for `bin/` and `viewer/`" | holds |
| bin/perry-task:2911-2912, :2930-2931 | same wording | holds |
| tests/test_blank_cell_is_one_rule.py:244 | "the reader for `bin/` and `viewer/`" | holds |
| tests/test_phase_lifecycle.py:537-539 | reader for bin/ and viewer/; release/manage.py reads it at git refs under an NN-1 exception | holds |
| tests/test_phase_lifecycle.py:555-556 | "A regression guard, not a proof that no other reader exists … within five lines" | holds (six-line window :583, the name plus five lines) |
| tests/test_phase_lifecycle.py:557-558 | "catches a revert of the perry-task and perry-state sites directly" | **false for perry-state (E1)** |
| tests/test_phase_lifecycle.py:558-560 | perry-goals' helper read is caught only through the comment's `read_text()` | holds (R1 red, R1b green) |
| tests/test_phase_lifecycle.py:561-562 | test_blank_cell_is_one_rule's literal-set check catches that revert | holds for the exact revert (R1b). A revert that compares against `P.PHASE_POINTER_NONE` by name (R1c) escapes both, as re-review 4 noted. The sentence does not claim otherwise |
| tests/test_phase_lifecycle.py:564-567 | cannot see: other spellings, a read before or more than five lines after, a helper or a subprocess, a git ref; "re-reviews 3 and 4 planted each" | holds item by item. Re-review 4's M10 (a name assembled elsewhere) is still not listed. The list does not claim to be complete, so this is a note |
| tests/test_goals_objective_add.py:117-120 | old-slug records are the phase's to parsers' linkage readers and perry-goals, not perry-state | holds (D3 above) |
| tests/test_okr_store_is_the_source.py:446-448 | perry-lint reports an error; load_snapshot continues | holds (D5 above) |
| tests/test_startup_routing.py:304-308 | entry files carrying the route rule; about ten more pages name it; router-subcommands among them; decide/SKILL.md carries the rule without naming it | holds (D4 above). SKILL.md also carries the rule without naming the procedure. The comment gives decide/SKILL.md as an example, not as the only case, so this is a note |
| viewer/parsers.py:3037-3039 | "a regression guard for some of the sites fixed here; its docstring says which" | true at class level. It inherits E1 through the method docstring it points to |

### Detector probes (scratch)

The harness is `probe5.py` and its output is `probe5.out`. Each revert restores
the exact pre-fix code from 89fa3477^ or 5a08b22b^. Two differ:

- R2 restores the perry-lint pre-USER-980 read and set in the same shape.
- R1c is a synthetic helper read that compares against the set by name.

```
B0 pre: files byte-equal to git show c9262965: OK
B0 class OK; blank_cell: only the no-git artefact (TestTheSpellingThatWasDropped)
R1  perry-goals pre-USER-980, with comment      detector RED;  blank_cell sweep RED
R1b perry-goals pre-USER-980, comment removed   detector OK;   class OK;  blank_cell sweep RED
R1c perry-goals helper read, set by name        detector OK;   class OK;  blank_cell sweep OK
R2  perry-lint pre-USER-980                     detector RED;  blank_cell sweep RED
R3  perry-task _register_state pre-5a08b22b     detector RED
R4  perry-task _current_store_phase pre-5a08b22b detector RED
R6  perry-state exists() pre-5a08b22b           detector OK;   class RED via test_state_does_not_warn_after_a_close
B1 post: files byte-equal to git show c9262965: OK
```

"blank_cell sweep" means test_no_site_decides_blankness_for_itself. After each
revert, the file was written back from `git show c9262965:<path>` and asserted
byte-equal to it. The final check compares all four files against the same
source.

### Scoping of the claims raised

- E1 was written by this candidate (42556e76). It counts.
- Root ARCHITECTURE.md §2 :83 ("### `viewer/parsers.py` — the one reader") and
  the §3 diagram label :145 were present at 820da3b1. They are notes, not
  charges, as in re-review 4.
- The class name `TestThePointerHasOneReader` (tests/test_phase_lifecycle.py:536)
  was written by the candidate (89fa3477). Its docstring now scopes it to bin/
  and viewer/, and the parsers docstring references it by name. This is note
  level, and renaming it would be a larger change than the claim is worth.
- parsers.py:3033-3034, "five sites in four tools", is unchanged since
  re-review 4, which recorded it as holding loosely. It is a note.

### Scratch

The scratch directory is
`$TMPDIR/perry-scratch/agent-a9622d3ac70fcfdb0`, the
`perry-scratch-derivation` result for this worktree. The host refused the
inline `$(git …)` form, so I read `git rev-parse --show-toplevel` and `$TMPDIR`
separately. It holds:

- `copy/` (the `git archive c9262965`)
- `head.tar`
- `cand.diff`
- `onereader.txt`
- `probe5.py` / `.out`
- `sig.py` / `.out`

### Commit versus the constraints

review-constraints.md says a review round does not commit. This round commits
only this evidence file, because the PMO's brief asks for it.
