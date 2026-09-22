# TASK-423 — V4 round 2, 2026-09-23

Fresh-context reviewer (not round 1's), criteria: the row's statement and
`bin/ARCHITECTURE.md` NN-B1/NN-B2. Range
`e29ea47e0ea0852a9fa2361042836cdc078457c7..64064aa4499ea994ae4efb0d4ead5f6c66c480a8`.
Copied by the PMO from the reviewer's returned text.

## Holds

All four September defects are fixed and each is killed by a line-anchored
mutant, with the base re-measured from a `git archive` copy rather than read:
`perry list --xyzzy` (base exit 0, printed the index) → exit 2 naming the set;
`perry-detect-host --xyzzy` (base exit 0, printed the host) → exit 2;
`perry-explain … --xyzzy` (base exit 0, printed the row) → exit 2;
`perry-goals krs <positional>` exit 1 → 2. No green mutant among them. The new
test pins both halves: dropping the refusal reddens it, and planting round 1's
exact file reddens exactly the two help-hoist subtests and nothing else. The
row's category is closed everywhere — all 20 executables exit 2 on an undeclared
flag and name the token. The `krs` guard reaches no other verb; no caller in the
repo passes an argument to the three tools. Affected tier green (66 modules,
1,871 tests); net +83 (bound +120).

## FAIL

`bin/perry:93-97` — `if error or positionals: … return 2` precedes `if "--help"
in flags:`, so `perry list --help --xyzzy` prints no help and exits 2.
`lib/__init__.py:1114-1127` shows `--help` was already recorded in `seen` when
the scan returned, so the information is in hand and discarded.
`bin/ARCHITECTURE.md:162-167` NN-B1 is severity **hard**.

Enumerated over all 20 executables × 7 vectors: `bin/perry` is **the only one of
twenty** where `--help` in front of a bad token prints no help. This is the
identical shape round 1 FAILed in `perry-detect-host`; round 2 hoisted help there
and left the same ordering in the sibling tool of the same commit. **M6 is
green**: moving the three help lines above the four error lines makes
`perry list --help --xyzzy` print usage at 0, keeps `perry list --xyzzy` at exit
2 naming the set, and leaves `test_bin_argument_contract`, `test_bin_surface`
and `test_architecture_rules` green over 154 tests — nothing pins the
non-compliant order.

The reviewer stated two qualifications against its own verdict: (a) this is not a
regression in help printing — at base `perry list --help` printed the tool index
at exit 0 and never printed help either; (b) the row's summary names `perry list
--xyzzy` among the three tools it fixes, and the nine lines are new code in this
range. It weighted (b) and the round-1 precedent above (a).

**The PMO instructed the author not to change `bin/perry`**, on the strength of
`tests/test_bin_argument_contract.py:836-841` assigning the collision to another
row. The reviewer notes that row is closed, so the collision has no owner.

Non-blocking: `perry-goals krs <stray> --json` writes JSON to stdout at exit 2
while `krs --xyzzy --json` writes prose to stderr; `perry list` newly exits 2 on
`--`, an empty argument and a stray positional (no caller does this); four tools
still accept a stray positional at exit 0 and `perry-explain … ""` discards the
id — all pre-existing and outside the row. Round 1's claim that `bin/perry`
prints help for `--help <bad>` is wrong; the author's correction measures true.

=== VERDICT ===
task: TASK-423
rung: V4
result: FAIL
criteria: the row's statement and bin/ARCHITECTURE.md NN-B1/NN-B2
checked: detached at 64064aa4499ea994ae4efb0d4ead5f6c66c480a8 in an isolated worktree; PATH led by /Users/bytedance/.local/bin (Python 3.11.15); PERRY_HOME=<worktree>, PERRY_PROJECT unset. `bash tests/run --tier affected --base e29ea47e0ea0852a9fa2361042836cdc078457c7` — green, 66 modules, 1871 tests. Enumerated all 20 bin/ executables × 7 vectors on the candidate AND on a `git archive` copy of the base, so every defect and delta was measured. Seven line-anchored mutants, each with `__pycache__` cleared and >1 s waits, each restored and verified with `bin/perry-restore-check`: the four fixes (all red), the refusal dropped with help hoisted (red), round 1's exact file replanted (red, exactly the two help subtests), and the three-line help move in `perry list` (GREEN over 154 tests). All eight perry-goals verbs probed with a stray positional; `krs` at both levels with and without `--json`, plus `--`, an empty argument and `--help` with a stray. Grepped SKILL.md, bin/, reference/, work/, packs/, templates/, modes/, setup/ and tests/run for callers. Happy paths re-run. Net +83.
not-checked: the full suite (only --tier affected, per the round's instruction), so modules outside the affected set were not run under the mutants either; perry-detect-host's detection branches (only the argument front end, only under this host); round 1's conclusions were not relied on and its bin/perry claim was re-derived and found wrong; the September evidence was not read; `perry describe`'s own argument handling; the four pre-existing stray-positional remainders and the empty-argument case were measured but not mutated; whether the PMO's instruction to leave bin/perry untouched was meant to put it outside this round's criteria — judged against NN-B1 as written, the row's own summary, and the 19-tool measured convention.
proof: bin/perry:93-97 — the error return precedes the help branch, so `perry list --help --xyzzy` exits 2 with empty stdout; lib/__init__.py:1114-1127 shows `--help` was already in `seen`. Unpinned: the three-line move is green over 154 tests.
=== END VERDICT ===
