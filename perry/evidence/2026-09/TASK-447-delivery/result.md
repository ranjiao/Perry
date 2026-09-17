# TASK-447 coding result and migration proposal

Coding implementation is complete on its feature branch; live migration and task acceptance remain with PMO. No V4/V5, task closure, release allocation, push, merge or publication was performed.

=== RESULT ===
- Branch: `codex/task-447-phase004-20260917`
- Checkout: `/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-447`
- Exact base: `3034c249b8f116c5e1ae975685bbf9358a4471b2`
- Exact coding commit: `cf4b49cdd39ac1a7cbf28777fcedfb696f98fcd8`
- Commit parent equals the pinned base; final checkout is clean.
- Product scope: only `bin/perry-lint` and `tests/test_summary_is_asked_for.py`.
- Behavior: existing lexical guide is 400 Unicode code points, counted with Python `len(str)`, and its constant/comment/output now describe characters rather than bytes. Existing warning severity, unrelated guides and write paths are unchanged.
- Four boundary fixtures: ASCII and Chinese at 400 (no finding) and 401 (exactly one warning).
- Line accounting against base: lint -17, tests +17, combined Python/test net 0 (26 insertions / 26 deletions). No existing tests removed and no dependencies added. This delivery contributes zero to the phase net; no unrelated phase accounting audit was performed.

## Validation receipts

All suite subprocesses inherited canonical `PERRY_HOME=/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-447`, absent `PERRY_PROJECT`, and task-specific `TMPDIR=/private/tmp/perry-scratch/task-447/phase004/tmp`. Suites ran sequentially with at most four workers. Runner source was read; `tests/run --help` was never invoked.

| Check | Actual result | Receipt |
|---|---|---|
| Candidate `python3 tests/parallel test_summary_is_asked_for -j 4` | PASS: 1 module, 28 tests, 4.4s | `targeted.log` |
| Committed `bash tests/run --tier smoke` | PASS, including built-in tree guard | `smoke.log` |
| Committed `python3 tests/parallel --tier affected --base 3034c249b8f116c5e1ae975685bbf9358a4471b2 -j 4` | PASS: 71/158 modules, 2,144 tests, 100.4s | `affected.log` (complete printed selection and selection reasons retained) |
| External tree guard around affected | snapshot/verify passed | manifest `affected-tree.json`; final verify in `final-checks.log` |
| Threshold-only mutation 400 → 1000 | Expected FAIL: two 401-character subtests, ASCII and Chinese; 400 cases remain green | `mutation-red.log` |
| Restore original committed lint bytes and repeat named boundary test | PASS: 1 test with four subtests | `mutation-restored.log`, `mutation-proof.log` |
| Final diff/scope/base/tree checks | PASS | `final-checks.log` |

Named regression: `test_summary_is_asked_for.TestTheLinterReportsWhatTheWriterRefuses.test_next_action_400_401_unicode_character_boundary`.

Mutation/restoration command:

```sh
python3 -m unittest discover -s tests -p test_summary_is_asked_for.py -k next_action_400_401 -v
```

`mutation-proof.py` is the retained bounded experiment: replace only the constant, run the regression, restore exact original bytes in `finally`, rerun, and compare restored bytes to the original committed file. Restored lint SHA-256: `e047bd1f25ffef1571fdfad38ea9f30476a6bed1f724d2306e8e3aab87719b20`.

No full/slow suite was run; the integrator owns merged full/slow validation. Green on this coding base is not a merged-state result.

## Migration proposal — not applied

All artifacts in this directory are scratch-only and excluded from the product commit:

- `migration.json`: 33 entries, each with `task_id`, `title`, exact `original_next_action`, authored `proposed_next_action`, and `rationale`.
- `TASK-447-next-action-accounts.md`: evidence draft with sections named `TASK-NNN`; every original is retained verbatim, including the original status claims and retractions.
- `migration-validation.json`: exact capture comparison, section round-trip checks, source hashes and calculated lengths.
- `authored-proposals.json`: manually authored action/rationale text; Python only transports these strings and validates equality/lengths, never summarizes prose.
- `assemble-proposal.py`: reproducible transport and validation.

Authoritative input is the supplied captured `next-actions-source.json`; only the bounded 33-row projection's prose was loaded for drafting. All projected originals, titles and statuses match their authoritative captured rows. Source SHA-256: `1b9f63e27ad3c58a8d68ed6411adf3add8db4f26d1bfdef612d44bb938b4d98a`.

Every replacement includes `perry/evidence/2026-09/TASK-447-next-action-accounts.md#task-NNN` (with its actual lowercase task ID). Maximum proposed length is 367 code points, pointer included. The source has 100 open rows, nearest-rank p90 1,672 and maximum 2,218. Applying these proposals only to that captured snapshot projects p90 343 and maximum 377. These are **projected values, not live migration verification**.

Important retained qualifications:

- TASK-173 still requires the four User Decisions and carries captured blockers TASK-184/TASK-185.
- Historical dependency statements in TASK-066/242/252 are retained for reconciliation, not silently upgraded to current typed blockers.
- TASK-334's account says CLOSED AND VERIFIED while captured status is not_started; its replacement calls out the discrepancy without changing status.
- TASK-371/378 retain the TASK-278 exoneration and retraction; TASK-436 keeps the merged `9c30782a` part separate from unfinished part 2.
- TASK-380 still requires the user's decision; TASK-387 keeps the schema fix gated. Other measured SHAs and verification qualifications remain in the actions where relevant and in every full original account.

PMO handoff for acceptance criteria 3–4:

1. Re-read the live `perry-task list --json` contract. Before each write compare the row's current next_action exactly with `original_next_action`, and inspect current status/blockers/verification for changed conditions.
2. If any row changed, retain the newly read account and have an agent re-author/review that row; do not apply the stale proposal or truncate it automatically. No claim of live reconciliation is made here.
3. Persist reviewed originals to `perry/evidence/2026-09/TASK-447-next-action-accounts.md` before applying approved replacements via `bin/perry-task`. Coding wrote no live or copied PMO store and no PMO evidence in the repository.
4. Re-read the live contract after all writes, verify it is complete, and measure nearest-rank p90 using Python string length. Save the capture and command output as the PMO acceptance receipt.

Example read/measurement commands for PMO to execute on its live root (not executed by Coding):

```sh
bin/perry-task list --root /Users/bytedance/proj/Perry --json > /private/tmp/perry-scratch/task-447/phase004/live-after.json
python3 /private/tmp/perry-scratch/task-447/phase004/measure-p90.py /private/tmp/perry-scratch/task-447/phase004/live-after.json
```

The measurement script refuses a truncated/incomplete open contract. Its method is ascending `len(next_action)` values and index `ceil(0.9*n)-1`; it is deterministic measurement, not semantic analysis. If current open rows exceed the read bound, PMO must obtain a complete contract before reporting the figure.

## Release handoff

Delivery ID suggestion: `TASK-447-first`. Change note: Next-action lint warnings now use a 400-Unicode-character guide and accurately name the unit. Upgrade note: existing longer actions warn; preserve their accounts in evidence before replacing them with concise pointers. No write-time refusal or schema change. Version allocation remains exclusively with the integrator.

=== ARCHITECTURE COMPLIANCE ===
Touched sections: §2 (bin and tests), §3 (existing dependency boundaries), §4 (canonical state boundary), §5 (existing task-list read contract), §6.NN-1, §6.NN-2, §6.NN-3, §6.NN-4, §6.NN-5, §6.NN-6.
Compliance check:
- §2: The existing deterministic linter changes one lexical threshold; the existing test module verifies its behavior without adding a component.
- §3: No dependency direction changes or new imports, readers, schemas or claims are introduced.
- §4: No live or copied PMO store is written; PMO alone will apply reviewed text through the existing task writer.
- §5: Proposal validation uses the supplied task-list contract unchanged and does not alter any published contract version.
- §6.NN-1: Product state parsing continues through the existing reader; scratch validation consumes exported JSON rather than parsing canonical state files.
- §6.NN-2: The evidence draft and migration JSON are proposals only, never substitutes for canonical store writes.
- §6.NN-3: Receipts distinguish coding verification, projected migration measurements and pending live writes; no unapplied migration is reported as complete.
- §6.NN-4: Product logic counts code points only; the agent authored all natural-language summaries and Python only transports/measures them.
- §6.NN-5: Boundary fixtures write solely into temporary Project roots; smoke and affected tree guards passed, and the deliberate bounded mutation was restored exactly.
- §6.NN-6: Neither decided nor descriptive architecture was edited.
New §7 questions opened: (none).
This is the existing executor attestation procedure; independent review and PMO acceptance remain pending. TASK-455 is not presumed accepted, and this session awards no V4/V5.
=== END COMPLIANCE ===
