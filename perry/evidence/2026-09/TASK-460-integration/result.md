# TASK-460 local release integration result

- Outcome: required local gates PASS; integrated-to-main: false; unpublished: true.
- Authorization: USER-957; bounded release/artifact work only. No push, tag, publication, main merge, PMO state edit, code fix, or architecture change.
- Checkout: /private/tmp/perry-scratch/Perry/phase004-k4_waa0n/integrate-460
- Integration branch: codex/integrate-task-460-phase004-20260917
- Actual immutable main base: df09680e453fe68aa47360d83eec1cf87e6771fd
- Reviewed code: cb310d87587e4c4fb841620d38209b2394e0e618; parent-prepared integration commit: eac0a1a7 (already present on entry).

## Allocation

- Previous version on actual base: 0.1.4.
- Allocated once: 0.1.5; delivery TASK-460-typed-position-20260917; phase 004-guided; date 2026-09-17; integrator pmo-agent.
- Allocation commit/head: e8f0eb0183a13a69ddd4456368745e2b500ebaf4
- Frozen input ref: codex/task-460-gate-input-20260917 -> e8f0eb0183a13a69ddd4456368745e2b500ebaf4. Preserve unchanged for this receipt.
- Authored notes: counts derive from declared typed checks; ceiling direction comparisons fixed; undeclared checks remain unmeasured. No data migration; users may see unmeasured progress until checks are declared. No breaking CLI changes.
- release/manage.py produced and the release commit contains only release/records.jsonl, VERSION, CHANGELOG.md.
- Working release check, committed check against the actual base, and version check using --tag v0.1.5 all passed. The --tag check validates the expected tag/version string; no tag was created.
- Final-head checks also passed: release-base-check.json and release-version-check.json beside this report.

## Full merge gate

- Command: env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME python3 tests/merge-check --base df09680e453fe68aa47360d83eec1cf87e6771fd delivery=codex/task-460-gate-input-20260917 --tier full -j 4 --record /private/tmp/perry-scratch/integrate-460/phase004/merged-full
- TMPDIR: /private/tmp/perry-scratch/integrate-460/phase004/full-tmp-8niy3eru (fresh external canonical directory).
- Outcome: PASS, exit 0; 154 modules, 4298 tests, 412.0 seconds, 4 workers. One full-gate invocation; no duplicate suite.
- All typed suite stages passed, including syntax/help, fixture lint and tree guard.
- Tested tree: 8cf62293712e8e2e658f979dd5e13634c4bcbead
- Receipt exact path: /private/tmp/perry-scratch/integrate-460/phase004/merged-full/receipt.json
- Log: /private/tmp/perry-scratch/integrate-460/phase004/full.log
- Emitted artifact: /private/tmp/perry-scratch/integrate-460/phase004/merged-full/durations.json
- Artifact SHA-256: dbe66f11971c94b8d608116361909cecd5c13d8f91b6d13c14717e1df7a5a870

## Artifact and separate slow gate

- Imported the emitted durations.json bytes exactly into tests/durations.json in this integration checkout.
- Durations-only commit / final integration SHA: 1f1c6da11f305846b6697d65f4adbd967dbef5b0
- Receipt verification PASS, exit 0: 1 module, 27 tests. Log: /private/tmp/perry-scratch/integrate-460/phase004/verify-receipt.log. Verified unchanged input refs, code identity outside durations.json, exact artifact bytes and provenance.
- The original receipt's artifact_verified=false is the emission-time value; verification is recorded separately in verify-receipt.log, without editing that receipt.
- Slow command: env -u PYTHONPATH -u PERRY_PROJECT -u PERRY_HOME bash tests/run --tier slow --workers 4 --results /private/tmp/perry-scratch/integrate-460/phase004/slow-results.json
- Four-worker configuration is the supported --workers transport read in tests/run; it passes -j 4 to tests/parallel. tests/run --help was never invoked.
- TMPDIR: /private/tmp/perry-scratch/integrate-460/phase004/slow-tmp-6zpbp3jz (separate fresh external canonical directory).
- Slow outcome: PASS, exit 0; 158 modules, 4401 tests, 518.8 seconds, 4 workers; zero failed modules. This includes harness self-tests and validates the final artifact/runner.
- Slow log: /private/tmp/perry-scratch/integrate-460/phase004/slow.log
- Slow machine result: /private/tmp/perry-scratch/integrate-460/phase004/slow-results.json
- Final tree guard PASS; clean git status; git diff --check PASS. Final base/main and frozen-ref SHAs rechecked unchanged.

## Limits and handoff

Both local required gates completed successfully. English sample-fixture lint emitted 9 warnings with 0 errors in each suite; these were not changed. Full timing refresh measures 154 modules; the four deferred harness modules retain their previous provenance. Separate slow results are evidence only and were not imported over the required full artifact. No new code audit or V5 sign-off is claimed. The parent integrator must recheck exact refs and receipt before any separately authorized main merge.

integrated-to-main: false
unpublished: true
