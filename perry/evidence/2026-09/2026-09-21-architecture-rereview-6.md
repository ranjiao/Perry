# Architecture re-review 6: the E1 correction, after 35b10830

This is the sixth re-review of one integration candidate. The user authorised it with a
narrow scope. The prior verdict is `2026-09-21-architecture-rereview-5.md` in this directory.
It found everything else holding and was BLOCKED on one false docstring clause, E1. Its
COMPLIANCE block is the baseline this round confirms against.

The scope has three parts:

1. Is the E1 fix true?
2. Did anything else change since re-review 5's head?
3. If nothing else changed, re-review 5's other verdicts carry forward.

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: Claude Code subagent (claude-opus-5), fresh context, worktree agent-aa8029031c22ab68d. I did not write TASK-469/470/471/474/475, the USER-978/980/981 fixes, b99c861a, 42556e76 or 35b10830, and I carry none of their conversation. I used no author compliance verdict. Timestamp: 2026-09-21T07:29:03Z
Base: 820da3b1849df4f7155baf976b1045c6590bd129
Head: 6c2cbc79ad4bda582ffb5fb5e5d5ee8bb57a27eb
Triggers:
- Listed boundary paths: FALSE since re-review 5. `git diff --stat c9262965 6c2cbc79 -- . ':!perry' ':!.perry'` lists exactly one file, tests/test_phase_lifecycle.py (+4 -1). Across the whole tree, the only other change is perry/evidence/2026-09/2026-09-21-architecture-rereview-5.md (re-review 5's own verdict). Nothing under viewer/, schema/, bin/ or bin/lib/, and no SKILL.md, changed. Re-review 5's finding (TRUE for base..head, reviewed) stands.
- New top-level directory: FALSE. No path outside tests/ and perry/ changed.
- New bin executable: FALSE. Nothing under bin/ changed.
- Contract-version change: FALSE. schema/ is unchanged, and the one change is inside a docstring.
- Root architecture edit: FALSE since re-review 5. ARCHITECTURE.md is unchanged between c9262965 and 6c2cbc79.
- Module architecture edit: FALSE since re-review 5. bin/ARCHITECTURE.md is unchanged.
Context: Same as re-review 5. Root ARCHITECTURE.md §3 Forbidden :160-167 (a second reader, :161), §6 NN-1 :243-256, and the §8 USER-981 entry :368-371. The change is in `tests/`. No trigger fact is unresolved.
Rules:
- E1, tests/test_phase_lifecycle.py:555-571 (the docstring of test_nothing_else_reads_the_pointer_value): CORRECTED, and the new text holds. The fix is 35b10830, merged at 6c2cbc79. Its diff is one hunk, entirely inside that docstring. It replaces "of the perry-task and perry-state sites directly." with four lines. I checked each claim they make:
  - "It catches a revert of the perry-task sites directly". This holds. I reverted bin/perry-task to 16124fb0 on a scratch copy (R-task). test_nothing_else_reads_the_pointer_value goes RED, and it lists bin/perry-task:2911 and :2930, the two sites.
  - "perry-state's old code only called `.exists()`". This holds. `git diff 16124fb0 6c2cbc79 -- bin/perry-state` shows `cur_pointer = root / "phase" / "CURRENT"` / `if cur_pointer.exists() and not snap.phase:`. The old code reads no value.
  - "which it does not look for". This holds. The detector's regex (:587) is `read_text\(|read_bytes\(|open\(`. Under R-state the method stays GREEN.
  - "`test_state_does_not_warn_after_a_close` below catches that revert". This holds. Under R-state that method goes RED: perry-state emits "phase/CURRENT points at a phase file that does not exist." after `phase close`. The method is defined below, at :595.
  - "(both checked by running the reverts, architecture re-review 5, E1)". This holds. Re-review 5 ran R3/R4 (perry-task) and R6 (perry-state) in probe5, and this round re-ran both as whole-file reverts.
  - The rest of the docstring is byte-identical to c9262965. Re-review 5 found it held (perry-goals' helper read, the blank_cell check, and the cannot-see list).
- ARCHITECTURE.md:368-371 (the §8 USER-981 entry: the claims are narrowed in `viewer/parsers.py` "and its test"). This now holds. The E1 residue that re-review 5 recorded against it is gone. parsers.py:3037-3039 ("its docstring says which") points at a docstring that is now true.
- Every other rule verdict in re-review 5's block carries forward, because (2) holds:
  - ARCHITECTURE.md §1, §2, §3 directions, the other §3 Forbidden entries, §5, NN-2 to NN-6 and OQ-2: holds.
  - §3:161 and §6 NN-1 with its two Known exceptions: holds for the behaviour.
  - D1, D3, D4 and D5: corrected and true.
  - SKILL.md:48-70, the V5-signed hand-off contract: holds.
  - bin/ARCHITECTURE.md: holds.
  None of the files these verdicts rest on changed between c9262965 and 6c2cbc79.
Decision: PASS. E1 is corrected, and every claim in the new text holds under a revert probe. Nothing else outside perry/ changed since re-review 5's head. The candidate follows NN-1 as amended by USER-981, and its descriptive claims about the pointer reader and its guard are now true.
User decision required: none.
Not checked:
- I ran no full suite, as the scope specifies. The change is inside a docstring, so no executable line changed. On a scratch copy I ran the three methods of TestThePointerHasOneReader at baseline and under each revert.
- I did not re-run re-review 5's other probes (R1, R1b, R1c, R2 and R5), its signature comparison, or its category-claim sweep. They rest on files unchanged since c9262965.
- bin/perry-restore-check could not verify the scratch restores. With `--root <copy>` it refuses because a `git archive` copy has no commits (exit 2). I hand-rolled the check instead: after each restore, the harness asserts both tools are byte-equal to `git show 6c2cbc79:bin/<tool>`, which I extracted separately. I also compared the copy's tests/test_phase_lifecycle.py with `git show 6c2cbc79` using cmp.
- After writing this file I ran tests.test_diagnose on the reviewed tree.
=== END COMPLIANCE ===
```

## Supporting notes

### Candidate binding

The worktree was cut from origin/main at 0b5bf99e, with no branch commits and a clean
tree. 0b5bf99e is an ancestor of 6c2cbc79, 448 commits behind. I fast-forwarded it with
`git merge --ff-only 6c2cbc79`, which the PMO authorised, and HEAD is 6c2cbc79ad4b. The
commits since re-review 5's head, from `git log --oneline c9262965..6c2cbc79`:

- 8756b8a6 and 194a7ad2 are re-review 5's evidence.
- 35b10830 is the E1 fix, one file, +4 -1.
- 6c2cbc79 merges them.

### The pre-fix reference

The brief names 16124fb0 as the pre-fix version. Re-review 5 used 5a08b22b^ (77c3544f).
`git diff --stat 16124fb0 77c3544f -- bin/perry-task bin/perry-state` is empty. So a
whole-file revert to 16124fb0 is the same revert re-review 5 applied site by site.

### Probe table (scratch)

The harness is `probe6.py`. Its output is `probe6.out`, and the full stderr of every run
is in `probe6.log`. Each run is a single `python3 -m unittest` of one method of
tests.test_phase_lifecycle.TestThePointerHasOneReader, run in the copy with
PERRY_PROJECT unset.

| Run | every_no_phase_spelling | nothing_else_reads (detector) | state_does_not_warn_after_a_close |
|---|---|---|---|
| B0 baseline | OK | OK | OK |
| R-task: bin/perry-task at 16124fb0 | OK | **RED**: `['bin/perry-task:2911', 'bin/perry-task:2930', 'viewer/parsers.py:3041']` | OK |
| R-state: bin/perry-state at 16124fb0 | OK | OK | **RED**: warning "phase/CURRENT points at a phase file that does not exist." |

The restore checks passed at every step:

- before any revert (B0 pre)
- after R-task
- after R-state
- at the end (B1 post)

Each check found both tools byte-equal to `git show 6c2cbc79:bin/<tool>`. The file mode
was kept on each write.

This matches what the new docstring says, and it reproduces re-review 5's R3/R4 and R6.

### Notes, not charges

- The new text splits the test's name across a line break inside its backticks
  (`` `test_state_does_not_warn_ `` / `` after_a_close` ``). A grep for the full name
  will not find the reference. It is readable, and it is not a false claim.
- parsers.py:3037-3038 says "its docstring says which". The sites are named in the
  method's docstring, not the class docstring. Re-review 5 accepted this reading, and it
  is unchanged here.
- Re-review 5's notes stand unchanged:
  - root §2 :83 "the one reader" (pre-existing)
  - the class name TestThePointerHasOneReader
  - parsers.py "five sites in four tools"
  - the cannot-see list omitting M10

### Scratch

The scratch directory is `$TMPDIR/perry-scratch/agent-aa8029031c22ab68d`, the
`perry-scratch-derivation` result for this worktree. The host refused the inline
`$(git …)` form, so I read `git rev-parse --show-toplevel` and `$TMPDIR` separately. The
directory was empty at start. It holds:

- `copy/` (the `git archive 6c2cbc79`)
- `head.tar`
- `refs/` (`git show` of both tools at 6c2cbc79 and at 16124fb0)
- `probe6.py`, `.out` and `.log`

### Commit versus the constraints

review-constraints.md says a review round does not commit. This round commits only this
evidence file, because the PMO's brief asks for it.
