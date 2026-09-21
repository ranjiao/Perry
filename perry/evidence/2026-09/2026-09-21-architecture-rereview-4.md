# Architecture re-review 4: the entry-skills and TASK-471 candidate, after b99c861a

This is the fourth re-review of one integration candidate. The earlier verdicts
are in this directory:

- `2026-09-21-architecture-review-entry-skills.md`
- `2026-09-21-architecture-rereview-entry-skills.md`
- `2026-09-21-architecture-review-task-471.md`
- `2026-09-21-architecture-rereview-task-471.md`
- `2026-09-21-architecture-rereview-2.md` (BLOCKED)
- `2026-09-21-architecture-rereview-3.md` (BLOCKED)

Re-review 3 had two blockers:

1. release/manage.py reads phase/CURRENT's value at git refs with its own
   "no phase" set, while viewer/parsers.py claimed "the one reader of the
   pointer's value".
2. bin/ARCHITECTURE.md §8 said git is run by "five others". Six tools run it,
   and perry-codex-preflight is not one of them.

The user answered USER-981 (`perry/asks.jsonl` line 82): record an NN-1 Known
exception for release/manage.py's git-ref reads of phase/CURRENT, narrow
parsers' docstring and the reader test to the scope they cover, and add no new
component dependency.

The fix is one commit. `git log --oneline de595d1f..0425f82d -- . ':!perry' ':!.perry'`
lists only b99c861a. It changes ARCHITECTURE.md, bin/ARCHITECTURE.md,
bin/perry-goals (comments only), tests/test_phase_lifecycle.py and
viewer/parsers.py (docstring only).

The gate is `work/reference/dispatch.md § Architecture review`. The brief is
`work/reference/review.md § Integration architecture reviewer brief`. The
constraints are in `work/reference/review-constraints.md`.

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: Claude Code subagent (claude-opus-5), fresh context, worktree agent-ab702ff82a8d04c11. I did not write TASK-469/470/471/474/475, the USER-978/980/981 fixes or b99c861a, and I carry none of their conversation. I used no author compliance verdict, and I did not rely on the author's own claim sweep. Timestamp: 2026-09-21T07:09:12Z
Base: 820da3b1849df4f7155baf976b1045c6590bd129
Head: 0425f82d19ccb3db5b23ffe50c6cd355cbafc047
Triggers:
- Listed boundary paths: TRUE. `git diff --name-status 820da3b1 0425f82d` changes viewer/parsers.py, SKILL.md, goals/SKILL.md, work/SKILL.md and decide/SKILL.md. schema/ and bin/lib/ are unchanged. Since de595d1f, parsers.py changes only in the read_phase_pointer docstring (:3033-3038).
- New top-level directory: FALSE. `git ls-tree -d --name-only` gives the same 17 directories at base and head (scratch dirs.base and dirs.head; `diff` is empty).
- New bin executable: FALSE. `git diff --raw 820da3b1 0425f82d -- bin` has only M entries. bin/ARCHITECTURE.md and bin/README.md are 100644→100644. perry-context-budget, perry-goals, perry-lint, perry-state and perry-task are 100755→100755.
- Contract-version change: FALSE. schema/ is unchanged. The root ARCHITECTURE.md hunks fall in §2 (:98, :112), §6 NN-1 (:246), §7 (:309) and §8 (:354). None is in §5 (:212-240). VERSION and release/records.jsonl change Perry's product version, not a contract version. b99c861a changes no code path.
- Root architecture edit: TRUE. 2225d076 (USER-978) is unchanged. b99c861a adds NN-1's second Known exception (ARCHITECTURE.md:254-256) and a §8 entry (:368-371).
- Module architecture edit: TRUE. bin/ARCHITECTURE.md changed in 6bb4dc6f, 2225d076, abb1160d and 5a08b22b, and now b99c861a at §2 :79, §3 :101-102 and §8 :207-211.
Context: Root ARCHITECTURE.md at head. §1 is at :43, §2 at :58, §3 at :139 (allowed directions :157-158, Forbidden :160-167), §5 at :212 (read on demand), §6 at :241 (NN-1 :243-256), §7 at :305 (OQ-2 :318) and §8 at :366. Header :3 confirms §1, §3 Forbidden, §5 versions, §6 and §7. Component mapping, from the confirmed §2:
  - `bin/` covers perry-goals, perry-lint, perry-state, perry-task, perry-context-budget, bin/ARCHITECTURE.md and bin/README.md.
  - `viewer/parsers.py` is its own component (:83-91).
  - `release/` (:75-81) is not in the code diff. NN-1 now names it.
  - `SKILL.md + goals/ work/ decide/` covers the router and lane edits.
  - `modes/, packs/, reference/, templates/` covers reference/*.md.
  - `tests/` covers the test modules.
  The only declared module document is bin/ARCHITECTURE.md v1. Its header :3 confirms §6 and §7. release/ARCHITECTURE.md exists (f5656a1c), but root §2 :75-81 declares release/README.md as its "Procedure" and no module document. Under OQ-2 (:318) that is not missing context. I read it anyway. Its §3 says release/ uses "Python's standard library and Git" and describes project stores as "read through viewer/parsers.py in the root component map". That agrees with the new NN-1 exception. No trigger fact is unresolved.
Rules:
- ARCHITECTURE.md:43-56 (§1 scope) — holds. b99c861a changes only text. It adds no writer and judges no meaning.
- ARCHITECTURE.md:100-118 (§2 lanes) — holds, unchanged since re-review 3.
- ARCHITECTURE.md:157-158 (§3 allowed directions) — holds. The user's "no new component dependency" is kept: release/ changes only records.jsonl in the candidate, and release/manage.py imports only the stdlib (:6-18). No file imports viewer/ from release/.
- ARCHITECTURE.md:161 (§3 Forbidden, "A second reader of any state file") — holds under the recorded exception. release/manage.py:274-281 is still a second reader, and NN-1 now records it (:254-256) by user decision. That is the same arrangement the perry-context-budget exception has had since USER-978.
- ARCHITECTURE.md:162-167 (§3 Forbidden: a lane computing a number, roots, an agent writing ARCHITECTURE.md) — holds. b99c861a changes no lane, and it changes the root only as USER-981 decided (see NN-6).
- ARCHITECTURE.md:213-240 (§5) — not touched.
- ARCHITECTURE.md:243-256 (§6 NN-1, user-confirmed):
  (a) The new Known exception (:254-256) — holds. It says what USER-981 decided and no more. It covers only release/manage.py's git-ref reads of phase/CURRENT, and it adds no dependency. Each clause matches the code. "At two git refs": `pointer(base_sha)` and `pointer(head_sha)` (:285), through `read(root, PHASE_POINTER, sha)` → `git show` (:163-171). "With its own 'no phase' set": `("", "(none)", "none", "—")` (:278). "Serves a working tree": parsers.py:3040-3043 reads `Path(state_root)/"phase"/"CURRENT"`. "release/ does not import viewer/": manage.py:6-18. The exception does not mention the strict `.decode("utf-8")` (:277) or the PHASE fullmatch (:279). Both belong to the same read, so leaving them out does not widen what the exception covers.
  (b) phase/CURRENT in bin/ and viewer/ — holds. The code is unchanged since re-review 3. Every read of the value goes through read_phase_pointer.
  (c) The candidate's own category claims about the pointer reader — CONTRADICT the recorded exception in seven places that b99c861a did not narrow. See the enumeration (D1).
- ARCHITECTURE.md:258-291 (NN-2 to NN-5) — not touched by b99c861a. The earlier findings (holds) stand.
- ARCHITECTURE.md:293-303 (NN-6) — holds. USER-981 decided the §6 edit before it landed. The §8 entry is descriptive, but its last sentence is only partly true (D1).
- ARCHITECTURE.md:318 (§7 OQ-2) — holds, unchanged.
- ARCHITECTURE.md:368-371 (§8 entry added by b99c861a) — DESCRIPTIVE MISMATCH, partial. "§6 NN-1 gains a second Known exception" is accurate. "The pointer reader's claims in viewer/parsers.py and its test are narrowed to what they cover" is true of parsers.py:3033-3038 and of the test method's docstring (:554-563). It is not true of the same test class's docstring, tests/test_phase_lifecycle.py:537-538, which still reads "is the one reader of `phase/CURRENT`".
- SKILL.md:48-70 (the V5-signed hand-off contract, decided) — holds, byte for byte. I compared it independently (sig.py → sig.out; base 820da3b1 against head 0425f82d):
  - signature record, 5 lines: fbee743b839fab6a on both sides
  - invariant heading: 9c438a5e…
  - invariant: 29e4aba4…
  - table intro: 3bd4965e…
  - ownership table, 5 lines: 2ef99903…
  - the whole "only writer" paragraph: 7245e781…
  - the three refusal cases: d8c71ea2…
  All are IDENTICAL. No commit after de595d1f touches SKILL.md, a lane file or reference/.
- bin/ARCHITECTURE.md:62-70 ("It is the only `bin/` tool that executes another one; nothing is imported") — holds for subprocess execution. The only subprocess call sites in bin/ are git (perry-churn, perry-diagnose, perry-restore-check, perry-state-cost, perry-task), bash perry-detect-host (perry-context-budget:119) and `exec python3` of release/update.py (perry-update-check:159). bin/perry forwards to a tool in process (`load`, then `module.main`, :45-52 and :150-158). "Executes" is ambiguous there, and the clause "nothing is imported" shows the sentence means subprocess execution. This is a note, not a charge.
- bin/ARCHITECTURE.md:72-81 (§2) — holds. ":79 the one tool in `bin/` with a recorded NN-1 exception" is true: NN-1 lists perry-context-budget and release/manage.py. The heading ":72 The one tool that reaches outside" is pre-existing (base :62), and its own body names a second tool. That is a note.
- bin/ARCHITECTURE.md:99-105 (§3, "A tool never parses a state file itself") — the description holds. ":101-102 The one recorded exception in `bin/` … `release/manage.py` holds the other, outside `bin/`" is true: NN-1 has exactly two entries.
- bin/ARCHITECTURE.md:207-211 (§8 entry, corrected by b99c861a) — holds, and blocker (2) of re-review 3 is resolved. Before 5a08b22b, §2 said preflight "is the only dependency in this directory (`codex`, `git`, `timeout`)" (5a08b22b^, bin/ARCHITECTURE.md:75-76). So "listed `git` among `perry-codex-preflight`'s dependencies" is accurate. "It runs none" is also accurate: the three matches in preflight are "digits" and two github URLs. "Several other tools here do" is accurate: six do.
- bin/ARCHITECTURE.md:106, :162-190 (NN-B1 to NN-B4) — not touched by b99c861a. The earlier findings stand.
Decision: BLOCKED. Descriptive mismatches need correction and re-review. None of them contradicts a decided rule's substance: the code obeys NN-1 as amended. What remains is text that says something other than NN-1 now says, and USER-981 asked for that text to be narrowed.
  (D1) "One reader" claims that b99c861a did not narrow. Each one contradicts ARCHITECTURE.md:254-256:
    - bin/perry-goals:4737 "the pointer's one reader (NN-1, USER-980)"
    - bin/perry-lint:1309, same wording
    - bin/perry-state:1938 "through its one reader (NN-1, USER-980)"
    - bin/perry-task:2911 and :2929 "the pointer's one reader (NN-1, USER-980)"
    - tests/test_phase_lifecycle.py:537-538, the reader test's class docstring: "`parsers.read_phase_pointer` is the one reader of `phase/CURRENT`; perry-goals and perry-lint call it". USER-981 named this test for narrowing, and the caller list is also stale: perry-state and perry-task call it too.
    - tests/test_blank_cell_is_one_rule.py:244 "made `parsers.read_phase_pointer` its one reader"
    It is the same claim parsers.py:3033 dropped. The commit message says every "one/only/every" claim was narrowed, and these seven lines each contain "one reader". The sweep missed them.
  (D2) The narrowed test docstring (tests/test_phase_lifecycle.py:554-563) is true item by item, but its first sentence overstates. I probed every blind spot it lists on a scratch copy (probe4.out):
    - 'CURRENT': MISSED
    - "phase/CURRENT": MISSED
    - a read before the name: MISSED
    - a read 6 lines after the name: MISSED (5 lines after: CAUGHT)
    - a read through a subprocess: MISSED
    - a read at a git ref: MISSED
    "Scans every file under bin/ and viewer/" is also true. bin/lib/, viewer/ other than parsers.py and a non-.py file in bin/ are all CAUGHT, and all 28 files decode as UTF-8, so the `continue` at :570 skips none.
    "A regression guard for the five sites fixed" is not true of perry-goals' site. Its pre-fix code read the pointer through the `phase_text` helper. The method catches that revert (R1) only because the old comment contained the text "read_text()". With the comment removed (R1b, probe4b.out), the whole TestThePointerHasOneReader class is green. The suite still catches R1b, but only through test_blank_cell_is_one_rule's literal-set sweep (probe4c.out), and a revert that compared against `P.PHASE_POINTER_NONE` by name would escape both. The docstring's "cannot see" list leaves out a read through a helper (M9) and a name assembled elsewhere (M10). The helper case is the shape one of the five guarded sites had. parsers.py:3037-3038 "guards the sites fixed here" inherits the same gap. perry-state's site (R6) is guarded by the behavioural test test_state_does_not_warn_after_a_close, not by the detector.
  (D3) tests/test_goals_objective_add.py:114-117: after a rename, the records filed under the old slug "are still the phase's to every reader". This is FALSE. perry-state's next_kr_progress (:2315) and next_kr_withdrawn (:2336) compare the exact slug. In a scratch probe (rename_probe.out), after renaming 005-fresh to 005-renamed and repointing CURRENT, perry-goals `krs` still lists P005-O1-KR1, but perry-state reports "the linkage store describes phase 005-fresh, not the current phase 005-renamed" and gives no KR counts. perry-state's comparison predates the base (1791a8c3, 2026-09-15). The sentence is the candidate's. perry-goals' own comments were narrowed to "as the linkage readers group" (:4185, :4416), and those hold.
  (D4) tests/test_startup_routing.py:304-306: "Every file that names the pack procedure … Enumerated rather than sampled". This is FALSE. reference/router-subcommands.md:93-94 is the `/perry help` section itself, and it names `reference/config.md § Pack capabilities and controls`, but it is not in PACK_SITES. Ten lane reference pages and packs/software-ops/pack.md:57 name it too. decide/SKILL.md is in PACK_SITES but does not name it. The intended category, "files an Explain-route agent reads", is narrower, and the comment should say so.
  (D5) tests/test_okr_store_is_the_source.py:445-446: "a pointer naming a document that does not exist, which every reader of `phase/CURRENT` would refuse on". This is loose. load_snapshot (parsers.py:5238-5242) sets phase=None and continues, and release/manage.py's `pointer` does not check that the document exists. perry-lint and perry-state report it, and neither refuses.
  Resolved since re-review 3:
  - Blocker (1): NN-1 records the exception as USER-981 decided, and parsers.py:3033-3038 is narrowed.
  - Blocker (2): bin/ARCHITECTURE.md:207-211.
  The V5 contract holds, byte for byte.
User decision required: none. Every item is descriptive, and narrowing the text fixes it. D3 has an optional behavioural side: perry-state could group by phase number as perry-goals and parsers do. That would be a code change outside this candidate, and the PMO may want to file it instead of only narrowing the sentence.
Not checked:
- I ran no full suite. The PMO ran it green (158/4460) on this exact tree. On a scratch copy I ran TestThePointerHasOneReader (the baseline and 20 mutants), test_blank_cell_is_one_rule plus test_phase_lifecycle (one mutant), and one throwaway probe test built on test_goals_objective_add's fixture. After writing this file I ran tests.test_diagnose on the reviewed tree.
- The category sweep covered lines that 820da3b1..0425f82d added in bin/, viewer/, tests/ (not durations.json) and root ARCHITECTURE.md: 211 lines matching one|only|every|never|no other|all (claims.txt). Most are code (`all(`), numerals ("one record per content block") or historical narrative. The Notes list every one I judged to be a category claim, with its result. I did not sweep bin/README.md's added prose, the lane files or the reference pages (outside the brief's list). The one lane-reference fact I used is the D4 enumeration.
- The Claude-identity statements in perry-context-budget (":25 as Claude never does") depend on host behaviour I did not observe. I checked them only for consistency with the code: HOST_IDENTITY (:57) maps only codex-cli.
- release/manage.py's pointer read was not executed, as in re-review 3. The exception text was checked against the code.
- Every probe ran on a `git archive 0425f82d` copy under the perry-scratch derivation. Each restore was asserted byte-equal to `git show 0425f82d:<path>`.
=== END COMPLIANCE ===
```

## Supporting notes

### Candidate binding

The worktree was cut from origin/main at 0b5bf99e, with no branch commits and a
clean tree. I fast-forwarded it to 0425f82d with `git merge --ff-only`, which
the PMO authorised. HEAD is 0425f82d19ccb3db5b23ffe50c6cd355cbafc047. I read
b99c861a in full, USER-981 in `perry/asks.jsonl` (line 82), and re-review 3.

### The author's sweep, checked

The commit message says: "perry-goals comments: 'the one reader' → 'the
sanctioned reader'; 'every reader/tool' → the readers actually checked". That
is true of the four perry-goals lines it changed (:4185, :4416, :4867,
:4985-4986). It is not true of the rest of the candidate. The seven "one
reader" lines in D1 were added by the same candidate (89fa3477, 5a08b22b), and
all of them match the pattern the author says was grepped.

### Category claims the candidate added, and whether each holds

Only lines that are category claims are listed here. The other matches are
code, numerals or history.

| Site | Claim | Category | Result |
|---|---|---|---|
| ARCHITECTURE.md:254-256 | release/manage.py reads at two git refs, own set; release/ does not import viewer/ | NN-1 exceptions | holds |
| ARCHITECTURE.md:368-371 | parsers' and its test's claims narrowed | the reader test's claims | partial: the class docstring :537 is not narrowed (D1) |
| bin/ARCHITECTURE.md:69-70 | only bin/ tool that executes another | bin/ subprocess callers of bin/ tools | holds (bin/perry forwards in process: note) |
| bin/ARCHITECTURE.md:75-76 | only tool depending on codex / touching a model | bin/ tools | holds (re-review 3) |
| bin/ARCHITECTURE.md:79 | the one tool in bin/ with a recorded NN-1 exception | NN-1 exceptions in bin/ | holds |
| bin/ARCHITECTURE.md:101-102 | the one recorded exception in bin/; release/ holds "the other" | NN-1 exceptions | holds (exactly two) |
| bin/ARCHITECTURE.md:207-211 | preflight runs no git; several others do | bin/ git users | holds (six) |
| viewer/parsers.py:3033-3035 | five sites in four tools, three copies of the set | pre-fix value readers | holds loosely: goals, lint, task ×2, load_snapshot = 5 sites in 4 files (parsers is not a "tool"). Three sets: goals, lint, load_snapshot |
| viewer/parsers.py:3037-3038 | the test "guards the sites fixed here" | the five sites | not for perry-goals in its helper shape (D2) |
| bin/perry-goals:4737, perry-lint:1309, perry-state:1938, perry-task:2911, :2929 | "the pointer's one reader" | readers of phase/CURRENT's value | **false** after USER-981 (D1) |
| tests/test_phase_lifecycle.py:537-538 | "is the one reader of phase/CURRENT; perry-goals and perry-lint call it" | readers / callers | **false** (D1) |
| tests/test_blank_cell_is_one_rule.py:244 | "its one reader" | readers | **false** (D1) |
| tests/test_phase_lifecycle.py:554-563 | regression guard for five sites; the cannot-see list | detector coverage | list true item by item; "guard for the five" false for perry-goals' helper form (D2) |
| tests/test_phase_lifecycle.py:574 | "the one real reader, in parsers" | readers inside the scan | holds (inside bin/ and viewer/) |
| tests/test_goals_objective_add.py:114-117 | old-slug records "still the phase's to every reader" | linkage readers | **false**: perry-state (D3) |
| tests/test_startup_routing.py:304-306 | "Every file that names the pack procedure" | files naming config.md § Pack | **false** (D4) |
| tests/test_okr_store_is_the_source.py:435-441 | six sites, one lock, all under phase/ | phase_command writes | holds (six `write_atomic` at :4952-4953, :4996, :5040-5042; one `project_lock` at :4876) |
| tests/test_okr_store_is_the_source.py:445-446 | "every reader of phase/CURRENT would refuse on" | pointer readers | loose (D5) |
| tests/test_phase_lifecycle.py:659-670 | exactly one splitlines() | perry-goals call sites | holds by the test's own assertion |
| bin/perry-goals:3388-3389 | store declares no objective revision kind; ids never reused | linkage kinds; per-phase ids | holds: six kinds (schema linkage_store description). Reuse is refused per phase number (:4419-4428) |
| bin/perry-goals:4762-4765 | "nine other boundaries" | splitlines() boundaries besides \n and \r\n | holds (8 listed plus lone \r) |
| bin/perry-goals:4791 (refusal text), :4947 | "to every reader" | phase-header Status readers | loose: perry-lint:927 reads Status with its own regex (a pre-existing second reader, noted in re-review 3). It is note-level, not charged |
| bin/perry-goals:4185, :4416, :4867, :4985 | narrowed by b99c861a | — | hold |
| bin/perry-context-budget:5-9, :127, :413, :428 | ONE session, never the newest, one transcript, exactly one | binding | holds against bind() (:412-430). locate() returns every name match and len != 1 refuses |
| viewer/parsers.py:5243 | "The store is the only authority" | — | pre-existing comment, re-indented. Not a candidate claim |

### Detector probes (scratch)

The harnesses are `probe4.py`, `probe4b.py` and `probe4c.py`, with output in the
matching `.out` files. Site reverts put back the exact pre-fix code from
89fa3477^ and 5a08b22b^.

```
B0 baseline: detector OK, behavioural OK
R1 perry-goals pre-USER-980 (with its comment)   detector CAUGHT   (comment says "read_text()")
R1b perry-goals pre-USER-980 (comment removed)   class MISSED; suite CAUGHT only by test_blank_cell_is_one_rule
R2 perry-lint pre-USER-980                       detector CAUGHT
R3 perry-task _register_state pre-5a08b22b       detector CAUGHT
R4 perry-task _current_store_phase pre-5a08b22b  detector CAUGHT
R5 parsers load_snapshot pre-USER-980            detector CAUGHT
R6 perry-state exists() pre-5a08b22b             detector MISSED; behavioural CAUGHT
M1 'CURRENT' MISSED · M2 "phase/CURRENT" MISSED · M3 read before name MISSED
M4 read +6 lines MISSED · M4b read +5 lines CAUGHT · M5 bin/lib CAUGHT
M6 viewer/ other file CAUGHT · M6b non-.py in bin/ CAUGHT · M7 subprocess MISSED
M8 git show MISSED · M9 helper read MISSED · M10 assembled name MISSED
B1 after all restores: OK; every restore byte-equal to git show 0425f82d:<path>
```

### Rename probe (D3)

This is a throwaway test in the scratch copy's tests/, deleted after the run.
Its output is `rename_probe.out`.

```
BEFORE rename: phase.slug 005-fresh,   linkage.phase 005-fresh, objectives [O1]
AFTER  rename: phase.slug 005-renamed, linkage.phase 005-fresh, objectives [O1]
perry-goals krs after rename: ['P005-O1-KR1']
perry-state after: "the linkage store describes phase 005-fresh, not the current phase 005-renamed"
```

### Pre-existing notes, not charged

- Root ARCHITECTURE.md §2 :83-85 ("the one reader", "Parse every state file",
  "5,228 lines") and the §3 diagram label :145 date from before the base. With
  two recorded NN-1 exceptions, "the one reader" is now a heading that its own
  §6 qualifies. The user may want it reworded the next time §2 is edited.
- Root header :5 still says "Last reviewed: 2026-09-15".
- bin/ARCHITECTURE.md:72's heading "The one tool that reaches outside" is from
  the base, and its body now names two tools.
- perry-lint:927-928's own phase-header regex and the three undecided direct
  store reads at bin/ARCHITECTURE.md:102-105 are unchanged.

### Scratch

The scratch directory is `$TMPDIR/perry-scratch/agent-ab702ff82a8d04c11`, the
`perry-scratch-derivation` result for this worktree. The host refused the inline
`$(git …)` form, so I read `git rev-parse --show-toplevel` and `$TMPDIR`
separately. It holds:

- `copy/` (the `git archive 0425f82d`)
- `cand.diff`
- `claims.txt`
- `probe4.py` / `.out`, `probe4b.py` / `.out`, `probe4c.py` / `.out`
- `rename_probe.out`
- `sig.py` / `.out`
- `dirs.base` / `dirs.head`

### Commit versus the constraints

review-constraints.md says a review round does not commit. This round commits
only this evidence file, because the PMO's brief asks for it.
