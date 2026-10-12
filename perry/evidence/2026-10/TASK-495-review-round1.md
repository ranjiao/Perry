# Independent architecture review — FAIL

Exact range: `db06e70c..b9a6b2c9dbc912f04097b5906f12bee65b63e512`.
Authority: `bin/perry_architecture/REVIEW-CRITERIA.md` at that head.
Read-only review checkout: `/Users/bytedance/.codex/worktrees/architecture-review/Perry`.
No product edits, state changes, commits or merge performed. Do not merge this head as sound.

## Findings

1. **P1 — Freshness does not bind coverage changes. Criteria 3, 4, 5.** `bin/perry_architecture/scan.py:207-212` fingerprints file IDs/hashes/status and configuration, but omits actual skipped paths/coverage. `checkpoint.py:133-134` treats that fingerprint as the freshness authority. Reproduction: start on app.py and other.py with `excludes=['vendor']`, where vendor does not yet exist; create `vendor/new.py`; rescan with identical options. `skipped_paths` changes to `['vendor/']`, but the snapshot is identical and `verify` returns `fresh: true`. Delivery also returns `normal`, no reasons, `open_report: false`. A newly observed blind spot outside a checked rule neither invalidates the old evidence nor triggers attention. Similarly, an oversized Python candidate has hash null: changing it from 501 to 700 bytes with a 500-byte limit leaves verification fresh. Bind observable coverage to freshness and make source bytes that could not be fingerprinted an explicit verification limitation/refusal, not an unconditional fresh result.

2. **P1 — New unknown references outside rule scopes are silently normal. Criteria 3, 4.** `bin/perry_architecture/checkpoint.py:84-91,154-161`. `unknowns()` only inventories unknowns in supplied rule results; coverage only includes scan/ownership issues. Reproduction: fully assign app.py and other.py, with a forbid-call rule scoped to app.py; checkpoint start with `def other(x): return 1`; change other.py to `def other(x): return x.unknown()`; regenerate current analysis/review and save delivery against the original start. The facts correctly contain an unknown call, but the receipt remains `status: normal`, `reasons: []`. New unresolved imports have the same untracked shape. Compare the global observed blind-spot inventory across checkpoints, independently of the rule scopes; keep repeated existing blind spots quiet.

3. **P2 — Fresh verification ignores the saved HTML report. Criterion 5.** `bin/perry_architecture/checkpoint.py:120-128,131-150`. Loading validates only bundle/receipt JSON. Reproduction: save a valid checkpoint, replace its index.html with `REPORT REPLACED`, verify; then delete index.html, verify again. Both return `fresh: true` with the same report path. The verified receipt can therefore open an unrelated or nonexistent report. Bind the report bytes/payload to the completion receipt and reject missing/mismatched reports before publishing successful verification.

4. **P1 — Manual delegate entry point can omit the checkpoint procedure entirely. Criterion 2.** Changed `work/reference/dispatch.md:298-308` declares manual handoffs use the preamble, but actual consumer `work/reference/delegate.md:130-162` never requires that preamble or checkpoint instructions. Its required fields permit `file diff list + test output + 1-line summary` instead of RESULT, and its roleless code-changing path lists tests/worktree/commit requirements without the new start/delivery checks. Reproduction by following the actual route: `work/SKILL.md:204` routes delegate to delegate.md; render only its mandatory fields for an eligible roleless Python task. The resulting self-contained prompt has no start baseline, durable store, delivery check or checkpoint return fields. The delegated fresh agent does not inherit the dispatcher’s generic work-lane reminder. Wire the actual manual prompt contract and paste-back acceptance to the checkpoint procedure, rather than relying on a reverse reference from automated dispatch documentation.

## Checked and boundaries

- Recovery not blocking; interrupted empty; review checkout clean before and after.
- Inspected scanner/facts/interpretation/rule/checkpoint/CLI implementation, report rendering, changed tests/docs, and the four lifecycle consumers. Target code is parsed, not imported/executed. Interpretation and semantic equivalence remain host judgments.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_architecture_browser`: **32 tests passed** (3.597 s). Existing coverage exercises ordinary code/target staleness, target edit/deletion, tampered bundle/receipt, semantic findings, rules, scoped unknowns and CLI roundtrip.
- Own scratch fixtures independently verified refusal for absent start, task mismatch, checkout mismatch, changed scan settings, stale analysis/review, missing partial-write receipt and changed baseline receipt; normal roundtrip and append-only retry passed; bundle/receipt/HTML survived deletion of the fixture checkout.
- Reproductions and outputs retained under `/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/`: `architecture-independent-repro-1.py`, `.log`; `architecture-independent-finite-1.py`, `.log`. These import the exact review checkout modules and mutate only isolated fixtures. They contain assertions for expected rejection/retention and print the unexpected successful outcomes for findings 1–3.
- `git diff --check db06e70c..HEAD` reports a new blank line at EOF in `bin/perry_architecture/__init__.py:2` (minor hygiene, not one of the correctness findings).
- `python3 release/manage.py check --base db06e70c --ref HEAD`: exit 1, product changes need a release record. This is an outstanding integration prerequisite, not a demand that the author allocate a release; allocation belongs to the integrator.
- Not checked: full/slow combined-main integration gate, release allocation, browser interaction smoke, autonomous future-agent compliance. No repository-wide or merged-tree PASS is claimed. Full gates would not invalidate the concrete counterexamples above.

## Enforcement answer

The start/delivery checks are host workflow instructions. Raw task-state writers are unchanged; they neither invoke the model nor require these architecture receipts. `--verify-checkpoint` checks freshness but accepts no expected task/stage argument; the receiver must match those fields and the previously recorded baseline path manually, as the procedure explicitly instructs. Creating a new start after editing is not mechanically prevented; pre-edit provenance depends on the host's recorded start path. These are disclosed enforcement boundaries, not proof that checks are impossible to skip. Fix the four findings and re-review affected invariants on a new exact head, then run the release and combined-main integration gates before merging.

=== VERDICT ===
task: TASK-495
rung: V4
result: FAIL
criteria: bin/perry_architecture/REVIEW-CRITERIA.md
checked: exact product head b9a6b2c9dbc912f04097b5906f12bee65b63e512 against db06e70c; criteria 1-5 and bounded test/surface review under criterion 6; independent coverage/unknown/report-integrity reproductions and lifecycle entry-point inspection; 32 tests passed
not-checked: integrator release allocation and release checks on final combined tree; full/slow combined-main gates and receipt freshness; browser interaction smoke; future autonomous agent compliance
proof: bin/perry_architecture/scan.py:207 omits observed coverage from freshness; bin/perry_architecture/checkpoint.py:84 and :120 miss global blind spots and HTML integrity; work/reference/delegate.md:130 omits checkpoint prompt requirements; independent reproductions and exact evidence paths are recorded above
=== END VERDICT ===
