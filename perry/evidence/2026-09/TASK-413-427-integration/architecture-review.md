# TASK-413 / TASK-427 — integration architecture review (fresh context)

Integrator: PMO, 2026-09-22. Candidate `8972f759` (branch
`codex/autonomous-413-427-20260917`, V4 PASS in September, never integrated;
369 commits behind main) merged `--no-ff` onto main `2555bebc` as
`integ/task-413-427` `705898df` (three files: `bin/lib/__init__.py`,
`tests/test_bin_argument_contract.py`, `tests/test_bin_surface.py`).

Summary of the returned block (fresh-context reviewer, 2026-09-22 17:47 UTC):

- **Triggers.** Listed boundary paths TRUE (`bin/lib/`). New directory, new
  executable, contract-version change, root and module architecture edits:
  FALSE. Root § 5 declares the input shape, four exit codes and two invariants,
  not the wording of an exit-2 diagnostic; exit 2 is unchanged (probed).
- **Root rules.** § 5:214 and § 5:224 hold (no payload code changes; the new
  test asserts fields the task-list contract already publishes, which nothing in
  `tests/` asserted before — TASK-413's premise). NN-1, NN-2 and the § 3
  Forbidden lines not touched. NN-3 holds (the refusal is byte-compared to prove
  no write). NN-4 holds (`sorted(set(flags) | {'-h'})`, no "did you mean").
  NN-5 holds. NN-6 not touched.
- **Module rules.** NN-B1 holds (`-h`/`--help` still precedes the
  undeclared-token branch). **NN-B2 holds and is what the change delivers**:
  "exits 2 and names the legal set" was previously met only by exit 2. Probed:
  `perry-task list --xyzzy` now prints the accepted flags. § 5's `SURFACE`
  declaration stays the single source (the message is derived through
  `subcommand_flags`/`surface_flags`). § 4's descriptive line becomes true of the
  code. NN-B3 not touched; NN-B4 holds. tests/ rules hold.

**Decision: PASS.** User decision required: none.

Non-blocking notes, all pre-existing:
1. `lib.scan_argv` (`bin/lib/__init__.py:1086`) has no production caller — that
   half of TASK-427 is inert at the CLI; the reachable improvement is
   `parse_surface`.
2. `bin/perry-task:8697-8704` returns the usage block when no subcommand was
   given, so `perry-task --xyzzy list` never shows the new tool-wide label.
   `perry-tasks`, `perry-config` and `perry-okr` do print it.
3. Thirteen tools with no `SURFACE` still print `(try --help)`; NN-B2 is scoped
   to declared surfaces, and bin § 7's first open question already holds that gap.

Not checked: the suite, the September V4, the adequacy of the new tests, and
`bin/ARCHITECTURE.md`'s list of SURFACE-declaring tools (pre-existing detail).
