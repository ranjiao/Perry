# Independent review — TASK-413, TASK-427, TASK-423

Date: 2026-09-17. Fresh-context review against the written criteria read first at `/Users/bytedance/proj/Perry/perry/evidence/2026-09/autonomous-review-criteria.md`. No implementation receipts or earlier verdicts were used.

## Scope and isolation

Pinned base: `edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e`.

- TASK-413 / TASK-427: `8972f7599012c8a676414b5324f904a968f5e517`; exactly `bin/lib/__init__.py`, `tests/test_bin_argument_contract.py`, `tests/test_bin_surface.py`.
- TASK-423: `05ad0f3b1b25dcd58dd49f4f1fd2de1a774364e9`; exactly `bin/perry`, `bin/perry-detect-host`, `bin/perry-explain`, `bin/perry-goals`, `tests/test_bin_argument_contract.py`, `tests/test_okr_krs_render.py`.

Each candidate was extracted from its immutable Git archive into a separate local clone under this report's directory, with HEAD and index pinned to that commit. No checkout/reset/stash/clean command was used. Changed source bytes were independently compared with `git show`; see `candidate-413-427-source-check.json` and `candidate-423-source-check.json`. Mutation uses a third copy, `mutation-413`. Fixture writes are to temporary projects; no task-state transition, implementation, merge, push, or publication was performed against the primary project.

Read `work/reference/review-constraints.md`, all of `work/reference/review.md`, and all of `ARCHITECTURE.md`. Startup recovery was nonblocking, interrupted work was empty, and reviewer Git status was clean. Source inspection was limited to the enumerated diffs and their parser, fixture, runner, and contract dependencies.

**Explicit exclusions:** combined integration of the two deliveries, release acceptance, publication, V5/human approval, unrelated repository cleanup, and the slow harness self-tests. These are separate candidate reviews, not a claim about merged-state correctness.

## Independently observed behavior

### TASK-413

The added regression is at [tests/test_bin_argument_contract.py:684](candidate-413-427/tests/test_bin_argument_contract.py#L684), with the decisive independent numeric assertion at line 704. It creates two terminal records and four open records. No product counting code changes in this commit: [bin/perry-task:7888](candidate-413-427/bin/perry-task#L7888) counts the selected open population before truncation, and lines 7900–7916 render the window warning and bound.

The separate reviewer harness `probes.py` checks complete tuples rather than relying on the implementation's expected values:

| Invocation | total/open_total/closed_total | window open/closed | returned | truncated |
|---|---|---|---|---|
| `--all --limit 1` | 6 / 4 / 2 | 0 / 1 | 1 | true |
| `--all --limit 3` | 6 / 4 / 2 | 1 / 2 | 3 | true |
| `--all --limit 0` | 6 / 4 / 2 | 4 / 2 | 6 | false |
| open-only `--limit 1` | 4 / 4 / 0 | 1 / 0 | 1 | true |

For every truncated call, stderr names the correct returned/total pair and `bound.open_total` of 4. The unlimited call has no truncation warning. Fixture byte snapshots match before/after reads. Evidence: `probes-413-427.log`.

Mutation is anchored at the exact asserted source line 7888, replacing the count with `open_total = total`. The new regression fails for limits 1, 3 and 0 at line 704 (`6 != 4`); see `mutation-413-targeted.log`. The harness clears bytecode caches, waits past the timestamp second boundary, and restores from an independent `git show` source, then checks against a fresh `git show` read. See `mutation.py` and `mutation-driver.log` for the complete execution record.

### TASK-427

[bin/lib/__init__.py:942](candidate-413-427/bin/lib/__init__.py#L942) derives selected-subcommand suggestions through existing `subcommand_flags` (line 828), including common/universal flags. Lines 946–950 label the pre-subcommand union as **Declared flags (select a subcommand for its accepted set)**. The flat scanner derives its union from `bools`, `values`, and help aliases at line 1124. These changes construct an error string and return through the existing refusal path; they do not change successful parsing or dispatch.

The reviewer independently checked the four CLI cases (`perry-task add`, `perry-task list`, `perry-config show`, `perry-state`) for exit 2, appropriate inclusion/exclusion, both help aliases, and identical fixture bytes. An independent synthetic two-subcommand declaration verified that each suggestion excludes the other command's flag and that a flag before the subcommand receives the declared-set label. Evidence: `probes-413-427.log`. Added regression cases are at `tests/test_bin_argument_contract.py:141` and `tests/test_bin_surface.py:1444`.

### TASK-423

- [bin/perry:91](candidate-423/bin/perry#L91) scans list arguments before enumeration and returns 2 on unknown tokens or stray positionals.
- [bin/perry-detect-host:23](candidate-423/bin/perry-detect-host#L23) validates every argument before help or host detection. All three tested help/bad-token orderings refuse without stdout.
- [bin/perry-explain:993](candidate-423/bin/perry-explain#L993) rejects unknown dash-prefixed tokens before root lookup and normal answer rendering.
- [bin/perry-goals:3823](candidate-423/bin/perry-goals#L3823) rejects `krs` positionals at the invocation boundary, before context/model loading; JSON is exactly a refused object and status is 2. The old handler-level exit-1 refusals are removed at the phase/overall readers, without changing valid calculations.

Independent probes cover unknown `--xyzzy` on all three readers; both levels of `krs` in text/JSON; host help followed by a bad flag; valid list JSON/tools/help, host normal/help, and explain V4. The twenty-tool regression sweep was independently invoked with its enumeration assertion and no exceptions. All passed; temporary fixture bytes remained unchanged. Evidence: `probes-423.log`. Valid KR rendering and existing refusal cases are also covered by the affected tier, including the temporary-root fixture at `tests/test_okr_krs_render.py:194` and the updated bad-invocation expectation at line 388.

## Independent architecture audit

Architecture is unchanged from the pinned base in both commits. PASS below applies to the finite diff and its dependencies, not to all pre-existing code.

| Binding section | 8972f759 | 05ad0f3b | Evidence and reasoning |
|---|---|---|---|
| §2 components (`ARCHITECTURE.md:58`) | PASS | PASS | Argument behavior stays within deterministic `bin/` tools and shared library; tests assert their results. No lane computes numbers or takes store ownership. |
| §3 dependencies (`ARCHITECTURE.md:138`) | PASS | PASS | No new imports, state reader, cross-project lookup, or reverse dependency. `perry list` reuses the already imported `lib.scan_argv`; other changes only affect existing argument branches. |
| §5 contracts (`ARCHITECTURE.md:211`) | PASS | PASS | TASK-427 keeps accepted flag scope declaration-driven; TASK-423 makes bad invocations exit 2 and preserves the required JSON refusal object; TASK-413 changes no payload or count implementation. |
| §6 NN-1/2/3 (`ARCHITECTURE.md:242`) | PASS | PASS | No new canonical reader or writer and no successful-write claim introduced; argument refusals precede substantive work. |
| §6 NN-4 (`ARCHITECTURE.md:269`) | PASS | PASS | Token membership, positional cardinality, and typed boolean counting only. No prose interpretation or semantic judgment is introduced. |
| §6 NN-5 (`ARCHITECTURE.md:278`) | PASS | PASS | Added tests use temporary `Project` roots (`tests/task_writer_support.py:169`) or synthetic dictionaries; KR test uses a temporary fixture (`tests/test_okr_krs_render.py:194`). Reviewer mutations are isolated. Runtime tree-guard outcomes are recorded below. |
| §6 NN-6 / §7 (`ARCHITECTURE.md:285`, `:297`) | PASS | PASS | No architecture, confirmed rule, schema version, or open-question resolution is edited or implicitly claimed. All existing open questions remain outside this bounded change. |

The rest of the architecture was read: mission, data flow, and change log introduce no additional conflict with these diffs.

## Execution evidence

All logs and runnable reviewer harnesses are beside this report. The required invocation is `PERRY_HOME=<candidate> bash tests/run --tier affected --base edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e`, from that candidate directory. The selector's exact module/rule lists are saved in `selection-413-427.log` and `selection-423.log`.

The initial logs `affected-413-427.log` and `affected-423.log` are **invalid candidate evidence**: inherited `PERRY_HOME` pointed at `/Users/bytedance/proj/Perry`, as their template check explicitly shows. They are retained for transparency and excluded from verdict evidence. The isolated reruns explicitly set the candidate tool home. No implementation receipt substitutes for these reviewer-run checks.

Confirmed TASK-423 affected-tier result: **exit 0; 63 modules, 1,738 tests**, plus clean template, syntax/help and final tree guards. Evidence: `affected-423-isolated.log:76` (module/test summary), final lines 88–90 (tree guard and tier PASS). The measured 1,222.9 seconds is this loaded review environment, not a product performance assessment.

Confirmed TASK-413/427 affected-tier result: **exit 0; 154 modules, 4,304 tests** (`affected-413-427-isolated.log:177`), with final tree guard PASS at line 189 and tier PASS at line 191. The selector initially lists all 158 modules because `bin/lib/` is a full-selection dependency, then holds back the four slow harness self-tests.

The mutation affected tier completed **exit 1; 154 modules, 4,304 tests**, with exactly the new mixed-status regression failing (three limit subcases, `6 != 4`; `mutation-413-affected.log:179` and `:207`). The tree guard passed (`:219`), treating the deliberate pre-run mutant as its starting state. Restore was independently verified against committed source, and the restored targeted regression completed **exit 0** (`mutation-driver.log:5`–`:6`, `restored-413-targeted.log`). The original immutable candidate tier and the restored targeted test provide separate positive controls.

Final source checks: reviewer, both candidates, and restored mutation copy have clean Git status and `git diff --check` exit 0; the restored counting source matches `git show 8972f759:bin/perry-task`. See `final-source-check.json`. Both finite commit diffs also pass `git diff --check` against the pinned base.

No in-scope defect found. Architecture **PASS for both diffs**. This is not combined integration, release, or publication acceptance.

Additional verification: the extra post-restore affected-tier rerun was interrupted by SIGTERM (driver return -15, followed by its expected assertion failure; `mutation-driver.log:7`–`:12`). It is **not a passing tier**, regardless of the shell cleanup banner in `restored-413-affected.log`. Its tree guard reports no changes. This interrupted extra run is excluded from verdict evidence: the immutable candidate affected tier, mutant affected tier, independently verified restore, and restored targeted regression all completed as recorded above. No product failure is inferred from the signal, and no post-restore affected-tier completion is claimed.

=== VERDICT ===
task: TASK-413
rung: V4
result: PASS
criteria: perry/evidence/2026-09/autonomous-review-criteria.md
checked: criteria 1-3 on isolated 8972f759 against edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e; independent four-open/two-terminal fixture, all four requested windows and stderr; 154-module affected tier PASS; open_total=total mutation caught by both new regression and affected tier; restored from git show and restored regression PASS; architecture sections 2,3,5,6,7 PASS
not-checked: combined integration, release, publication, V5, slow harness self-tests; extra post-restore affected tier was interrupted by SIGTERM and is not claimed complete
proof: 8972f759 tests/test_bin_argument_contract.py:704 fails with 6 != 4 after mutation at bin/perry-task:7888; mutation-413-affected.log:179; affected-413-427-isolated.log:177; mutation-driver.log:6; restored-413-targeted.log:7; probes-413-427.log; final-source-check.json
=== END VERDICT ===

=== VERDICT ===
task: TASK-427
rung: V4
result: PASS
criteria: perry/evidence/2026-09/autonomous-review-criteria.md
checked: criteria 1-3 on isolated 8972f759 against edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e; four unknown-flag CLI cases, both help aliases, fixture-byte equality, synthetic scoped and pre-subcommand declarations; existing valid/refusal regression coverage in 154-module affected tier PASS; architecture sections 2,3,5,6,7 PASS
not-checked: combined integration, release, publication, V5, slow harness self-tests, unrelated CLI surface expansion
proof: 8972f759 bin/lib/__init__.py:942 derives subcommand suggestions from the existing declaration, :947 labels the unselected union, :1124 derives scanner flags; tests/test_bin_argument_contract.py:141; tests/test_bin_surface.py:1444; probes-413-427.log; affected-413-427-isolated.log:177 and :189
=== END VERDICT ===

=== VERDICT ===
task: TASK-423
rung: V4
result: PASS
criteria: perry/evidence/2026-09/autonomous-review-criteria.md
checked: criteria 1-3 on isolated 05ad0f3b against edf6b143a1b6cf8de3f2d84c53bc5e5d9cebf41e; three reader unknown flags, phase/overall krs positionals in text/JSON, host help plus bad token, valid invocation controls, complete twenty-executable sweep with no exceptions; 63-module affected tier PASS; architecture sections 2,3,5,6,7 PASS
not-checked: combined integration, release, publication, V5, full/slow suite outside the 63 selected modules, unrelated reader or help-order behavior
proof: 05ad0f3b bin/perry:91, bin/perry-detect-host:23, bin/perry-explain:993, bin/perry-goals:3823; probes-423.log; affected-423-isolated.log:76 (1738 tests), :88 (unchanged tree), :90 (PASS)
=== END VERDICT ===
