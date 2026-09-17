# TASK-451 independent V4 and architecture review

Criteria: `/Users/bytedance/proj/Perry/perry/evidence/2026-09/TASK-451-spec.md` (read externally; not copied into the candidate).

Exact tested candidate: `232c3e928b7f1468396795e6fb4cff21971aa940`.
Pinned base: `7ffcc6337bc5c8b31d2e8992c251e23299bff1ea`.
Review checkout: `/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/review-task-451`.
Reviewer did not author the implementation. The author's result was treated as claims to verify.

All test/probe children export `PERRY_HOME` to this checkout, unset `PERRY_PROJECT`, and use `TMPDIR=/tmp/perry-scratch/review-task-451/phase004/tmp`. Startup recovery was nonblocking and interrupted runs were empty. Reports, scripts and fixture roots are external. No primary checkout, task state, release, decided architecture, push or merge was changed.

## Bounded inspection

Inspected the immutable six-file diff (`candidate.diff`), repository AGENTS, review constraints and all four review rules, DESIGN-017 decisions and §§5.1–5.3 / A1, root architecture, bin module architecture, current phase O4 bound, schema conventions and runner source. Did not invoke `tests/run --help`.

1. **Root declaration:** `schema/state-schema.json:2257` uses `anchor: code`, `owner: perry`, root cap 500 and the locked per-section authority note. The root claim at `:1377` agrees. The authority note matches DESIGN-017 §5.1, including user confirmation of the component list, Forbidden lines, versions, rules and closure of questions. No architecture document changed.
2. **Module kind:** `schema/state-schema.json:2276` declares one `architecture-module` kind, hard cap 600, with explicit selection and agent-supplied component membership. It adds no module glob claim or component registry. `bin/perry-lint:4673` checks relative path shape, containment after symlink resolution, existence and document structure. It does not infer component membership from prose.
3. **Consumers:** Enumerated the three affected anchor-selection sites: lint claim lookup (`bin/perry-lint:4976`), lint file selection (`:5686`), cost buckets (`bin/perry-state-cost:251`). All call `bin/lib/__init__.py:1124`, which uses `viewer/parsers.py:427` for canonical config reading. `bin/perry-state` and its architecture payload resolver are unchanged, as required for the TASK-452 boundary.
4. **Regression proof:** Schema declaration test is `tests/test_claims.py:103`; cost selection and exact bytes are covered by `tests/test_state_cost.py:195`. Mutation results and restoration are recorded below.

Python/test physical line delta against the pinned base is **0**: lib +9, lint −22, cost 0, claims tests +12, cost tests +1. Exactly two existing test modules changed. The owner/coverage assertions were consolidated, and the cost fixture retains its former claim-visibility assertions while adding root/byte checks. No new dependency or duplicate registry. Comment shortening is not a product failure.

## User-reachable boundary probes

`boundaries.py`, `boundaries.log` and `boundaries.json` preserve commands, outputs and assertions. All probes used disposable external fixtures:

- Both relative `../code` and absolute external code roots support root claims and repeated module selections; valid modules produce zero lint errors.
- A malformed neighboring `foreign/ARCHITECTURE.md` is not selected or reported.
- Empty value, absent value, parent traversal, root architecture supplied as a module, missing file, symlink escape, absolute module path and incompatible `--claims` mode all exit 2.
- Explicit selection works before adoption; a valid module exits 0.
- 600 logical lines pass; 601 logical lines produce `size-cap` and exit 1. This uses the existing linter's newline-split count.
- Candidate tests exercise project-root fallback and relative/absolute in-repository code roots for cost accounting, including a distinct obsolete state-root architecture file and exact selected byte count.

## ARCHITECTURE REVIEW — PASS

Independent assessment under DESIGN-017 §5.3; the author does not supply this judgment.

| Binding rule | Assessment and proof |
|---|---|
| Root §1; §3 allowed directions; bin §3 | **Holds.** The change is stdlib-only, read-only schema consumption. Both tools import a shared library helper; that helper delegates to the existing parser (`bin/lib/__init__.py:1124`). No tool-to-tool import, service, cross-project registry or new state writer. Configured code roots are the explicitly approved split-project location under DESIGN-017 §5.1. |
| Root NN-1; bin §3 one reader | **Holds.** `config_store_settings` remains the only config reader used by the new helper; lint and cost share its result-resolution primitive. |
| Root NN-2 and NN-3 | **Not touched.** No store/projection write path or write-success behavior changes. |
| Root NN-4 | **Holds.** Component selection is supplied by the caller; Python validates typed paths, caps and headings only (`bin/perry-lint:4673`, `:5686`). The authority note is reviewed by an agent, not a semantic prose checker. |
| Root NN-5 | **Holds for the reviewed changes.** New coverage uses temporary roots (`tests/test_claims.py:116`, `tests/test_state_cost.py:195`); smoke tree guard and final exact restoration receipts accompany this review. |
| Root NN-6; DESIGN-017 §5.1/A1 | **Holds.** Only the authorized schema claim and consumer wiring change. Root/module architecture, locked designs and contract versions are unchanged. Implementation authorization is not V5 acceptance. |
| Bin NN-B1/B2/B3 | **Holds for the changed surface.** Existing help/root handling remains, new explicit module option is documented and validated, and conflicting modes refuse (`bin/perry-lint:5255`, `:5307`). Module boundary refusals were exercised through CLI. No project-root precedence change. |
| Bin NN-B4 | **Not materially touched.** Help gains three usage lines for the explicit module option; no unrelated help redesign. |

The older pack's blanket-user wording and root architecture's acknowledged §3/NN-6 tension are not silently rewritten. The reviewed authority declaration follows the user's locked DESIGN-017 A1 scope.

## Not checked

No full or slow tier, merge-result gate, deployment, external migration, Windows behavior, V5 human sign-off, module generation, A3/B/C process/template redesign, or TASK-452 payload resolver implementation. The affected selector widens its module set for schema/shared library changes; that is still an affected-tier receipt, not an integration/full/slow verdict. Combined merge/full/slow gates belong to the main integrator. No user-reachable defect has been found in the bounded inspection and probes; final test outcome follows.

## Final verification receipts

| Check | Result | Receipt |
|---|---|---|
| `bash tests/run --tier smoke` | PASS, exit 0; includes `perry-lint --templates`, syntax/help and tree guard | `smoke.log` |
| `python3 tests/parallel --tier affected --base 7ffcc6337bc5c8b31d2e8992c251e23299bff1ea -j 4` | PASS, exit 0; 154 modules / 4,299 tests, 373.8s | `affected.log` (complete selection block) |
| External CLI boundary probes | PASS | `boundaries.py`, `boundaries.log`, `boundaries.json` |
| Revert entire schema file to `git show 7ffcc633…:schema/state-schema.json`; run the same affected tier once | EXPECTED RED, exit 1; 154 modules / 4,299 tests, 459.7s; exactly `test_claims` and `test_state_cost` red | `mutation.py`, `mutation-affected.log`, `mutation-receipt.json` |
| Restore schema from `git show 232c3e9…:schema/state-schema.json`; `python3 tests/parallel test_claims test_state_cost -j 4` | PASS, exit 0; 2 modules / 52 tests, 18.4s | `restored-targeted.log` |
| All six changed files vs candidate `git show`; clean status; working and pinned diff whitespace checks | PASS | `finalize.py`, `final-hashes.json`, `tested-sha.txt` |

The mutation is an actual whole-schema reversion, not a synthetic changed assertion. `test_architecture_declarations_and_selected_components` becomes an ERROR at `tests/test_claims.py:105` because the reverted schema lacks `architecture-module` (`mutation-affected.log:182`). This is reported as an error, not misrepresented as an assertion failure. The cost test independently reports three assertion failures for fallback, relative and absolute code paths: it sees `perry/ARCHITECTURE.md` instead of the code-root architecture (`tests/test_state_cost.py:207`; `mutation-affected.log:208`). The runner summary is 2 red modules / 4 failed outcomes. Both modules pass before and after the mutation.

Caches were cleared and the process waited 1.1 seconds after mutation and restoration. The restored schema SHA-256 is `f636e83d20a4861f54edabc562bbc28e89d5c193acc8ce8f2a2de31d58cb92e8`, verified against the immutable candidate, not a local snapshot. The base schema hash is `8357997aad8c49e24710eeadd97be29e0072281fd69aefcfbe906a07cc6f05ba`. `final-hashes.json` records exact SHA-256 verification for every changed product/test file and empty final status.

**V4 PASS.** All four bounded acceptance criteria are demonstrated. **ARCHITECTURE REVIEW PASS.** V5 remains pending named human sign-off; no task state was awarded or changed.

=== VERDICT ===
task: TASK-451
rung: V4
result: PASS
criteria: /Users/bytedance/proj/Perry/perry/evidence/2026-09/TASK-451-spec.md
checked: criteria 1-4 on 232c3e928b7f1468396795e6fb4cff21971aa940; immutable six-file diff; DESIGN-017 A1 authority; explicit module kind/cap/no glob claim; three consumer anchor sites; smoke/templates; pinned-base affected 154 modules/4299 tests; isolated CLI boundary fixtures; one whole-schema reverting mutation; restored targeted 52 tests; exact six-file hashes and clean checkout; net Python/test lines 0
not-checked: full/slow or combined merge gate; V5 human sign-off; deployment/external migration; Windows; TASK-452 resolver; module generation; A3/B/C template/process changes; D2 decision hashes
proof: schema/state-schema.json:2257 and :2276; bin/lib/__init__.py:1124; bin/perry-lint:4673 and :4976 and :5686; bin/perry-state-cost:251; tests/test_claims.py:105; tests/test_state_cost.py:207; /tmp/perry-scratch/review-task-451/phase004/{smoke.log,affected.log,boundaries.json,mutation-affected.log,mutation-receipt.json,restored-targeted.log,final-hashes.json}
=== END VERDICT ===
