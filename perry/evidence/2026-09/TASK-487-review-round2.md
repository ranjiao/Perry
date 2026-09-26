# TASK-487 — review round 2: V4 FAIL, architecture PASS, on a408a4db

Candidate: `c1e3f38ca2706f00e106ddf976a5ae435115416b..a408a4dbf58fa8ac8f031d6afe8a40d75a154cc1`.
This is round 3 of the work, fixing round 1's findings (`TASK-487-review-round1.md`).

Both reviewers were fresh-context agents, each in its own isolated worktree. A
rate limit stopped the first attempt at both, and they were relaunched at
08:3x on 2026-09-25. Neither attempt had written anything.

After the round, the reviewer worktree was clean and `.git/perry` was absent.

## V4 review round 2 — result: FAIL

- **The defect behind the FAIL — D1.**
  `kernel/tests/test_input_classes.py:227–237` asserts `(1, "io_error")` for
  `query --store /tmp/never.db` run from a working directory whose name is not
  UTF-8. The kernel never reads the working directory when `--store` is
  absolute, so it answers `store_missing`. The reviewer showed this by driving
  `bin/perry-kernel` `main()` with a patched `os.getcwd`.
  - On macOS the test is skipped, because APFS refuses the name.
  - On Linux it runs. `.github/workflows/ci.yml:31` runs `bash tests/run` on
    ubuntu, so criteria 2 and 11 fail there.
- **Criteria:** 1, 3–8 and 10–12 PASS; 2 FAIL (through D1).
- **Mutants:**
  - 56 run in the worktree: 51 caught, 5 survived — A3 `store.py:551`, B4
    `commands.py:1086`, C6 `cli.py:152` (equivalent), E9 `commands.py:1045`
    (ceiling cap untested), E15 `commands.py:1058` (hash pattern untested).
  - Round 1's survivors: M08, M15, M17, M19, M38 and M45 are now caught; M24's
    code was deleted.
- **Other findings (not criterion failures):**
  - **D2:** an id longer than 4,300 digits still returns `internal`, from the
    `int()` at `store.py:68`. It is reachable through `expect`, `query after` and
    import events.
  - **D3:** the 2^53 cap covers import (`commands.py:993`, `:1045`) but not the
    live mint (`:502`). After an imported ceiling of 2^53, one `create` mints
    past the cap, and the kernel's own export of that store is then refused on
    import.
  - **D4:** with `PERRY_STORE=""` and `PERRY_KERNEL_TESTING` unset, the kernel
    writes the derived shared store (`paths.py:69`, `:177–180`). This is pinned
    on purpose by `test_an_empty_environment_variable_counts_as_unset`. Only
    `PERRY_PROJECT` follows the `bin/lib` rule. **The user decides.**
  - **D5:** `export` deletes a project file whose name matches its temp pattern
    and reports `unchanged` (`commands.py:893`, `:918`). The spec requires a
    refusal (`kernel/ARCHITECTURE.md:175`, `:428–429`, `:474`).
  - **Flaky test:** `test_concurrent_inits` (`test_concurrency.py:163–169`)
    failed with `store_busy` in 1 of about 106 loaded runs. `store_busy` is a
    documented outcome, but the test does not accept it.
  - **`--root` precedence:** an undecodable `PERRY_PROJECT` refuses even when a
    valid `--root` is given (`paths.py:82`).
  - **Changed error codes:** seven error codes changed from b47cd005. No test
    pinned the old ones, and kernel § 5.1 was not updated.
  - **Stale text:** `test_resolver_agreement.py:4–5` still says "only second
    implementation", and `kernel/ARCHITECTURE.md:575` still calls the
    live-store question open.

```
=== VERDICT ===
task: TASK-487
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-487-spec.md
checked: criteria 1-8 and 10-12, the carried items and the Bound at a408a4db; baseline kernel suite 181 OK (1 skip) and --tier affected 24 modules/594 tests green; 56 line-anchored mutants in my worktree, each followed by run.py and --tier affected (J1 kernel suite only), restored from git show and verified with perry-restore-check: 51 caught (all 50 tier runs red), 5 survived (A3 store.py:551, B4 commands.py:1086, C6 cli.py:152 equivalent, E9 commands.py:1045, E15 commands.py:1058); 2 more in scratch copies (L3 prevention off, B3+B4 both caught); round-1 survivors M08/M15/M17/M19/M38/M45 now caught, M24 code deleted; md-free copy (1,210 *.md removed) 181 OK on macOS; b47cd005's 145 tests pass against the candidate package; error-code diff b47cd005 vs a408a4db over 18 inputs; --help 10 ways, no files; resolver copies enumerated in bin/ and viewer/; doc counts (21 executables, 163 modules, 6+14 SURFACE); test_durations_provenance 27 OK; worktree clean, HEAD a408a4db, .git/perry absent
not-checked: an actual Linux run (D1 shown by driving the real wrapper main() with os.getcwd patched, since docker is not running and needs approval); --tier full, bash tests/run and tests/merge-check; the slow-tier modules test_merge_gate and test_parallel_runner; the tier for J1 (a bin/lib mutant could redirect root-suite writers into the checkout); Python other than 3.11 and SQLite other than the local one; concurrency beyond 6 processes; crash atomicity; the user approvals (taken from the brief); whether root § 8's "each confirmed by the user" is true; criterion 8 against a real perry.json (it does not exist)
proof: kernel/tests/test_input_classes.py:235-237 asserts (1, "io_error") for `query --store /tmp/never.db` from a non-UTF-8 cwd, but the kernel returns store_missing (paths.py:175-176 resolves an absolute --store without the cwd; demonstrated through bin/perry-kernel main(), probes/p5b_main.py). The test skips on APFS and runs on ubuntu, where .github/workflows/ci.yml:31 runs bash tests/run, so the suite does not pass there (criterion 2) and test_kernel_suite turns the root suite red (criterion 11)
=== END VERDICT ===
```

## Architecture review round 2 — Decision: PASS

- **Triggers:**
  - a new bin executable, and edits to the root and module architecture
    documents: true;
  - boundary paths, a new top-level directory, and a contract version: false.
    The 36 error codes match kernel § 5.1 exactly.
- **Rules:** every rule holds, and none of them contradicts a decided section:
  - root § 1, § 3 including the rewritten sunset, and NN-1 to NN-6;
  - `bin/` § 3, NN-B1 to NN-B4 and OQ-B1;
  - kernel § 3 and NN-K1 to NN-K10, checked against the code. The empty-value
    refusal is fixed.
- **Round 1's descriptive mismatches:** all fixed.
- **New descriptive mismatches** (they need correction but do not block):
  - kernel § 5.1:175, § 5.8:428–429, § 5.9:473–475 and `errors.py:56–57` say
    export refuses foreign entries, while the code deletes its own leftover
    temp files;
  - kernel § 8:589 overstates § 5.9;
  - the kernel § 3 diagram at :76;
  - root § 8:396 omits the § 3 diagram edit;
  - `test_resolver_agreement.py:4–5`;
  - `bin/README.md:103–105` does not mention perry-lint's walk-less branches.
- **User decision required, not blocking:** root § 3:181 and NN-B3 list the
  existing resolver copies without perry-lint's eight per-mode `--root`-or-cwd
  branches (`bin/perry-lint:5307`, `5345`, `5381`, `5416`, `5437`, `5475`,
  `5511`, `5543`). Should they be named?
- **Record for provenance:** the user's in-session answers to round 1's (a) and
  (b) were:
  - (a) make the § 3 sunset exact;
  - (b) carry the sunset into NN-B3 and correct the OQ-B1 count.

  Both were given on 2026-09-25 through the choice prompt, choosing the
  recommendation each time. Until now they were recorded only in commit
  14d402e5's message.

## Next, per `work/reference/review.md § 5` and § 6

A FAIL moves the row to `in_progress`. This is the row's first V4 FAIL; round
1 was a PASS. One more fix round is therefore within the rules. A second FAIL
would be a decision for the user, not a third round.

## The user's answers, 2026-09-25 (choice prompt, recommendation each time)

- **D4:** an empty `PERRY_STORE` is **refused**, exactly as `--store ""` is. An
  empty `PERRY_PROJECT` is still treated as unset, as `bin/lib` treats it.
- **The resolver-copy list:** name perry-lint's eight walk-less per-mode
  branches, in both root § 3 and NN-B3. The change must be line-neutral.
- **Next:** round 4, then V4 round 3 and a fresh architecture review, then the
  merge gate. Another V4 FAIL goes to the user (`review.md § 6`).
