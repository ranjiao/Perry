# TASK-413 and TASK-427 — integration acceptance, 2026-09-23 (V4)

Both rows passed an independent V4 on 2026-09-17
(`../autonomous-review/review.md`) and were never integrated. `R-closable-row`
(TASK-483) surfaced them; the user asked for them to be closed (USER-1005), and
closing required the code to reach main first.

| Step | Result | Record |
|---|---|---|
| Candidate | `8972f759` on `codex/autonomous-413-427-20260917`, 369 commits behind main, merges cleanly: `bin/lib/__init__.py`, `tests/test_bin_argument_contract.py`, `tests/test_bin_surface.py` | — |
| V4 | PASS for both rows, 2026-09-17, on that branch | `../autonomous-review/review.md` |
| Architecture review | triggers: listed boundary paths TRUE (`bin/lib/`), others FALSE; fresh reviewer **PASS**, no user decision. Three pre-existing notes recorded | `architecture-review.md` |
| First gate attempt | red under the wrong interpreter: this session's PATH resolved `python3` to 3.9.6, and `test_board_from_declarations`' read-tracing breaks there. Green under 3.11.15, the project's interpreter. Environment, not code | — |
| Release | `release/manage.py patch` → **0.1.22** (`TASK-413-427-autonomous`, task field TASK-427; TASK-413 named in the notes) as `ebcc65e1`, committed with the delivery before the gate | — |
| Full gate | green on tree `3a6a9aa0`, base `2555bebc`, candidate `ebcc65e1`, 158 modules / 4,482 tests | `receipt.json`, `full.log` |
| Integration | `integ/task-413-427` `ebcc65e1` + durations on `integ/task-413-427-final` `7860c721`; `--verify-receipt` VERIFIED | commits |
| Slow gate | 162 modules · 4,585 tests · all green | `slow.log` |
| Merge | refs rechecked; `git merge --ff-only` → main `7860c721`; `VERSION` 0.1.22 | — |

Two PMO ordering mistakes, both caught by the receipt check and corrected: the
allocation was first made after the gate (the candidate changed, so the gate was
re-run), and the durations commit was first placed on the candidate branch
itself (moving the candidate ref; it now sits on `…-final`).

Carried from the architecture review, no rows opened: `lib.scan_argv` has no
production caller, so that half of TASK-427 is inert at the CLI;
`perry-task --xyzzy <subcommand>` returns the usage block before the new
message; thirteen tools without a declared surface still answer `(try --help)`.
