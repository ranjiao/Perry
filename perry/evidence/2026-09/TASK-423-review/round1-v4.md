# TASK-423 — V4 on the rebased candidate, round 1, 2026-09-23

Fresh-context reviewer (Claude subagent, own worktree). Criteria: the row's
statement and `bin/ARCHITECTURE.md` NN-B1/NN-B2 (there is no spec file). Range
`e29ea47e0ea0852a9fa2361042836cdc078457c7..95bc6504a9ac69f3656657d65ee84edfb9951e0b`.
Copied by the PMO from the reviewer's returned text.

## What holds

All four defects the row names are fixed, each killed by a line-anchored mutant
(restores verified with `bin/perry-restore-check` against `git show 95bc6504`):
M1 the `krs` positional guard (`bin/perry-goals:5296`) → red, 5 tests;
M2 `bin/perry-detect-host:28` exit 2 → 0 → red, 3; M3 `bin/perry:96` → red, 2;
M4 `bin/perry-explain:996` → red, 2; M5 dropping `--dangling` from the legal set
→ red. No green mutants among the five. Base defects re-measured independently.
The conflict resolution is clean: the `own`/`stray` block is byte-identical to
the base's and the new guard sits above it. Net +39 (bound +120). Affected tier
green (66 modules, 1,871 tests).

**Category enumeration**, 20 executables × 6 vectors: the undeclared-flag axis is
now fully closed (all 20 exit 2 and name the token). Stray positionals remain
at exit 0 on four tools (`perry-dispatch-limit list`, `perry-config show`,
`perry-decide list`, `perry-knowledge list`) — pre-existing, outside the row.
`perry-explain TASK-001 --root <p> ""` discards the id and prints the manual at
exit 0 (`bin/perry-explain:1054-1056`) — pre-existing. `perry-goals krs` refuses
a positional at every level, with and without `--json`; no other verb is
affected; no caller in the repo passes an argument to `perry-detect-host`.

## FAIL

`bin/perry-detect-host:23-31` validates the whole argument vector and exits 2 at
`:28` **before** the help branch at `:32-37`. So `perry-detect-host --help
--xyzzy` prints nothing and exits 2, where the base printed help and exited 0.
Measured across all 20 executables, this is **the only tool of 20** where
`--help <bad token>` does not print help — the other 19, including `bin/perry`
itself, do. `bin/ARCHITECTURE.md:162-167` NN-B1 is severity **hard**: "`-h` /
`--help` in any argument position prints and exits, before dispatch and before
any lock."

Two mutants show it is durable, not incidental:
- **M6 is green**: reordering `bin/perry:93` so `--help` wins over the scan error
  — making that tool NN-B1-compliant like its peers — leaves
  `test_bin_argument_contract`, `test_bin_surface` and `test_architecture_rules`
  green (154 tests). The same choice is pinned in one tool and unpinned in the other.
- **M7 isolates the pin**: hoisting the help branch above the validation loop in
  `perry-detect-host` (a bad token with no `--help` still exits 2) leaves the whole
  undeclared-flag sweep green; the only red is this round's new test at
  `tests/test_bin_argument_contract.py:1103-1106`.

`tests/test_bin_argument_contract.py:836-841` already records this collision as
open and belonging to another row ("The inconsistency is real and is TASK-411,
not a silent narrowing here"). The row under review says nothing about `--help`.

Smaller, non-blocking: `perry-goals krs <stray> --json` writes `{"refused": …}`
to stdout at exit 2, while `krs --xyzzy --json` writes a bare line to stderr —
one tool, one exit code, two contracts for a `--json` consumer.

=== VERDICT ===
task: TASK-423
rung: V4
result: FAIL
criteria: the row's statement and bin/ARCHITECTURE.md NN-B1/NN-B2
checked: detached at 95bc6504a9ac69f3656657d65ee84edfb9951e0b in an isolated worktree, PATH led by /Users/bytedance/.local/bin (Python 3.11.15), PERRY_HOME=<worktree>, PERRY_PROJECT unset. `bash tests/run --tier affected --base e29ea47e0ea0852a9fa2361042836cdc078457c7` (66 modules, 1871 tests, green). Enumerated all 20 bin/ executables against six vectors — an undeclared flag, a stray positional, `--help` then a bad token, a bad token then `--help`, `--`, an empty argument — with the suite's LEAD/NO_ROOT leads and a throwaway Project fixture. `perry-goals krs` with a positional at `--level phase`, `--level overall`, an invalid level, with and without `--json`, plus `krs --`, `krs ""`, `krs --help extra`; every other perry-goals verb with and without a stray positional. `bin/perry list` with `--`, a path-like positional and an empty argument. `perry-detect-host` bare, and through `bin/perry-context-budget --json`. Base behaviour re-measured by extracting the base's three tools to scratch and running them. Seven line-anchored mutants (M1-M7), each with __pycache__ cleared and >1s waits, each restored from `git show 95bc6504:<path>` and verified with bin/perry-restore-check; tree clean afterwards. Grepped SKILL.md, bin/, reference/, work/, packs/, templates/ and tests/run for callers. Net Python/test lines from `git diff --numstat`: +39.
not-checked: the full suite (only --tier affected, per the round's instruction). `bin/perry-detect-host`'s detection branches themselves (host override, environment sniffing, the parent-process walk) — only the argument front end, and only under this host. The September evidence was not relied on (rule 3). The base defect for `perry-explain --xyzzy` was read from the diff, not executed. The stray-positional and empty-argument remainders on four other tools were measured but not mutated, since none is touched by this change. Whether the other row would prefer the refusal-wins resolution; I judged against NN-B1 as written and the 19-tool measured convention.
proof: bin/perry-detect-host:23-31 (the validation loop exits 2 at :28 before the help branch at :32-37); the pin is tests/test_bin_argument_contract.py:1103-1106
=== END VERDICT ===
