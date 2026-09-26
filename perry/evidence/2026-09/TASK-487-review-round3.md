# TASK-487 — review round 3: V4 PASS and architecture PASS, on 0b14b8dd

Candidate: `c1e3f38ca2706f00e106ddf976a5ae435115416b..0b14b8dd745b6a0dab14af2228b9bf19ac6e0ae5`.
This is the work's round 4. It fixes the round-2 FAIL recorded in `TASK-487-review-round2.md`.

Both reviewers were fresh-context agents, each in its own isolated worktree. At the end of the round:
- the reviewers' worktrees were clean at 0b14b8dd;
- `.git/perry` was absent;
- the kernel runner had reported the live store absent before and after every run.

## V4 review round 3 — PASS (the verdict block is verbatim)

**Criteria.** Criteria 1–8 and 10–12 PASS. The carried items and the widened
Bound hold.

**D1 on Linux semantics.** Shown through the real `bin/perry-kernel` `main()`,
with `os.getcwd` patched to return a surrogate name and a file-system spy
attached:
- 16 cases, 7 of which read the cwd, made 0 file-system calls with the odd cwd;
- the answers match the test's pins;
- a mutant copy validated both the spy and the twin test.

**Other checks.**
- **Concurrency:** `test_concurrency` passed 440 of 440 runs.
- **Error-code differential:** 71 inputs were compared between a408a4db and
  0b14b8dd. 21 answers changed, all explained, and none gives exit 3.
- **D5 token:** the reviewer probed forging, collision, a store with no token,
  a crash, a dry run and transaction membership.
- **D4 and precedence:** checked against NN-K5 and `bin/lib`. An empty
  `PERRY_STORE` is `usage` whether or not testing is set.

**Mutants.** 33 were run: 26 caught, and all 26 also turned the tier red. 7
survived: R11 `commands.py:1018`, R20 `:907`, R26 `store.py:253`, R28 `:239`,
R29 `:105`, R32 `store.py:626`, and R33 `cli.py:152`, which is equivalent to
the original.

**Round 2's survivors.** E9, E15 and B4 are now caught. C6 is equivalent. A3's
code was deleted, and F1 below shows that code was not dead.

**Findings outside the criteria.** None fails a criterion.

- **F1.** The A3 filter at `store.py:623–626` was live. A no-op
  `rel:parent:W-001:W-002` change (`before: true`, `after: true`) replays as
  `export_invalid` at 0b14b8dd, where a408a4db accepted it. The kernel never
  writes such a change, and no test pins either behaviour. The comment at
  `:623–625` is false.
- **F2.** The import id cap at `commands.py:1018` lost its only test. The test
  `test_input_classes.py:471` is now refused earlier, by D2's 18-digit bound at
  `store.py:75`. This is a coverage regression.
- **F3.** Recording a token at export for a store that has none
  (`commands.py:907`) is untested. If it broke, the kernel would fail safe.
- **F4.** The `Store.open` retries (`store.py:239`, `:253`) are untested, and the
  deadline has only a lower-bound test (`test_concurrency.py:299`). Reading the
  code, the total wait can pass 5 s.
- **F5.** Kernel § 5.1 (lines 145–178) and the § 5.6 `item create` row (line 343)
  omit `id_exhausted`. Kernel § 8:589 misstates § 5.9. Neither § 5.1 nor § 5.7
  says that an empty `PERRY_STORE` is `usage`.
- **F6.** A damaged `export_token` gives `io_error`, not `store_corrupt`
  (`commands.py:901`).

```
=== VERDICT ===
task: TASK-487
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-487-spec.md
checked: criteria 1-8 and 10-12, carried items and the widened Bound at 0b14b8dd; kernel run.py 199 tests OK (1 skip) at baseline and after all restores, live store absent before/after; --tier affected 24 modules/594 tests green (NOT a green suite); md-free git-archive copy (1,210 *.md removed) 199 OK; D1 on Linux semantics through the real bin/perry-kernel main() with os.getcwd patched to a surrogate name and an fs spy: 16 cases (7 cwd readers), 0 fs calls with the odd cwd, answers match the pins, spy and twin test validated red on a mutant copy; 33 line-anchored mutants in my worktree, each followed by run.py and --tier affected, restored from git show and verified by perry-restore-check (33/33): 26 caught (26/26 tier red), 7 survived (R11 commands.py:1018, R20 :907, R26 store.py:253, R28 :239, R29 :105, R32 store.py:626, R33 cli.py:152 equivalent); round-2 survivors: E9 and E15 caught, B4 caught, C6 equivalent, A3 deleted but not dead (probe_a3.py); 71-input error-code differential a408a4db vs 0b14b8dd on scratch copies (50 same, 21 changed, all explained, no exit 3); D5 token probes (no-token store, crash, dry run, shared dir, token absent from 5 envelopes, token inside the existing transaction); D4 and --root precedence against NN-K5 and bin/lib; test_concurrency 440/440 (100 quiet, 100 beside a mutation run, 240 in 8 parallel loops); perry-lint's nine sites and the README resolver list enumerated against the code; git diff --check clean; worktree clean at 0b14b8dd; .git/perry absent
not-checked: an actual Linux run (docker needs approval; D1 was shown with os.getcwd patched and an fs spy instead); --tier full, bash tests/run and tests/merge-check; the slow-tier harness modules; Python other than 3.11.15 and SQLite other than 3.50.4; concurrency beyond 6 processes per race; power-loss atomicity of the token write; the user's in-session approvals (taken from the brief and the round-2 document); criterion 8 against a real perry.json (none exists yet); --help ways beyond the suite's own (the wrapper is unchanged since round 2); the author's own 17 mutants
proof: every criterion holds: 199/199 kernel tests with every *.md removed; the undecodable cwd never reaches the file system (paths.py:28, :51), so the Linux-only test answers as pinned; 26 caught mutants all reddened --tier affected; live store absent before and after every run. Outside the criteria: F1 store.py:623-626 (the A3 filter was live: a no-op rel:parent replay is now export_invalid); F2 commands.py:1018 untested since D2 (test_input_classes.py:471 is shadowed by store.py:75); F3 commands.py:907; F4 store.py:239, :253, :105 and test_concurrency.py:299; F5 kernel/ARCHITECTURE.md:145-178, :343, :589 omit id_exhausted or misstate section 5.9; F6 commands.py:901
=== END VERDICT ===
```

## Architecture review round 3 — Decision: PASS

- **Triggers.** A new bin executable, a root architecture edit and a module
  architecture edit are true. Boundary paths, a new top-level directory and a
  contract-version change are false: the surface stays at 1.0, unreleased, and
  root § 5 changes shape only.
- **Rules held.** Every rule holds against the code:
  - root § 1, § 3 including the sunset and its copy list, and NN-1 to NN-6;
  - `bin/` § 3 and NN-B1 to NN-B4;
  - kernel § 3 and NN-K1 to NN-K10, including this round's token, retry and
    snapshot changes, "one transaction per command", and environment
    precedence.
- **User-decided text.** Everything the user decided matches: the § 3 sunset,
  NN-B3, OQ-B1 and the empty `PERRY_STORE` refusal.
- **Round-2 descriptive mismatches.** All are fixed except kernel § 8:589, which
  is partly fixed.
- **New descriptive mismatches** (they need correction but do not block):
  - kernel § 5.7:413 leaves `export_token` out of the `meta` key list;
  - kernel § 5.6:343 leaves `id_exhausted` out;
  - DESIGN-023 § 5.3:277–278 says "nothing but `import` reads the export".
    This is now recorded in DESIGN-023 § 9.
- **User questions** (they do not block):
  - **(a)** Should the resolver-copy list name `bin/perry-churn § detect_perry`
    (`:305–341`)? It walks up to the first `.perry/`, bounded by git, and takes
    no `--root` and no environment variable.
  - **(b)** Did "line-neutral" apply only to the root document? NN-B3 grew by 3
    lines in `bin/ARCHITECTURE.md`, which went from 270 to 274 lines against a
    cap of 600.

The full COMPLIANCE block is in the session transcript. It is bound to
0b14b8dd.

## Where the findings go

These are recorded in the next rows' specs. No new row is opened.

- **TASK-489** (V4, import correctness):
  - F1: decide whether a no-op parent replay is accepted, pin it with a test,
    and correct the comment at `store.py:623–625`;
  - F2: restore a test of the import id cap;
  - F3: test token recording at export;
  - F6: a damaged `export_token` should give `store_corrupt`;
  - F4: test the `Store.open` retries and the deadline's upper bound.
- **TASK-488** (documents): F5, plus the architecture review's new descriptive
  mismatches (added to its spec on 2026-09-26).

## Merge gate and merge

**Merge gate.** From the primary checkout:

```
env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME python3 tests/merge-check --base main delivery=coding/task-487-kernel-core --tier full --record <scratch>/merge-487-20260926-111714
```

- The gate printed `✓ all green` and then `✓ exact merged tree passed full`.
- Its receipt reports base main `999ca0ed`, candidate `0b14b8dd`, and tested
  tree `8ba58a5d7191aa72a4090e501cb3dec5b3adc52c`.
- It did not run the four slow-tier harness modules, by design.
- The durations artifact stays in scratch and was **not imported** into
  `tests/durations.json`. Importing it is deferred integration work.

**Merge.**

- Just before merging, the refs were rechecked: main was still `999ca0ed` and
  the branch still `0b14b8dd`, so the binding held.
- `git merge --no-ff coding/task-487-kernel-core` produced `afa054af`, whose
  tree `8ba58a5d` is identical to the tree the gate tested.
- The author's worktree was removed. Both `coding/task-487-kernel-core` and the
  tool-made branch were deleted.
- `.git/perry` is absent. Nothing was pushed.

**TASK-487 closes at V4** on the round-3 PASS (`review.md § 5`).
