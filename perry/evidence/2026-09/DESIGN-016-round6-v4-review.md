# DESIGN-016 — V4 round 6

Three fresh reviewers, dispatched 2026-09-10 against
`perry/evidence/2026-09/DESIGN-016-spec.md`, the first round run under the
graded criteria — eight of the fourteen may fail a row, seven produce a filed
row instead. Base `08452bb5`.

**Two PASS, three FAIL**, and every FAIL is above `review.md § 0`'s line. That
is the grading working: round 4 returned seven FAILs and four were polish.

## TASK-364 and TASK-408 — PASS

The first PASSes either row has had. What the round established rather than
took:

- The `perry-task` direction-B AST walk does not over-report. **142 of 142**
  non-universal declared pairs matched as read, `INDIRECT` empty, and an
  exhaustive census over **1,178** wrongly-declarable combinations found **0**
  blind spots.
- Criterion 12's negative space re-derived at **1,277** pairs and executed
  through the real tools in both argument orders — **2,554 invocations, 0
  accepted**, every one carrying the correct refusal.
- All three published surfaces are byte-identical dicts for all six tools and
  all 57 subcommands.
- `UNIVERSAL` is not a self-agreeing copy, and the round proved *why*: every
  tool's intersection-of-all-subcommand-flags is empty, so any name added to
  or removed from either side shows up on at least one subcommand.

## The three FAILs, and what each cost

**TASK-364 / TASK-408's fix had covered one branch of two.** `describe_surface`
has a whole-tool branch and a single-subcommand branch, and the test read only
the first — the same headline as the round-3 fix it was answering. The
single-subcommand branch answers all 57 subcommands and is what
`bin/README.md` publishes. `usage_lines` was a third spelling, also uncompared:
emptying it left the suite green while `perry-task add --help` named no flags
at all. Three builders are now one, and the usage line is compared as an exact
set — `assertIn` could see under-reporting and not over-reporting, and
over-reporting is the direction that sends a reader to a refusal.

**TASK-360: the positional refusal stopped one position short, on a false
claim in its own comment.** It said the id is the only positional any of
`perry-task`'s thirty subcommands accepts. Nine never read `args.id`:

    perry-task ask USER-001 --needed "the STAGING password, corrected"
      → exit 0, USER-001 untouched, a SECOND row USER-002 minted

`takes_id` is declared in `SURFACE` now and a test holds it against what each
handler reads by AST. The first version also sliced the positionals twice, so
it refused nothing at all — and disabling it outright was green on 3,466 tests.

**TASK-407: `--root` with its value missing was still dropped by two more
tools**, and `perry-goals commit … --root` wrote into the cwd's project with
the named one untouched. The sweep that found the first four could not see
these two: it probed `<tool> --root` with no subcommand, where "expected one
of …" returns 2 for an unrelated reason — the right exit code for the wrong
reason. It leads with a real subcommand now, and a control checks those leads
are accepted. `--root ""` was the same wrong answer through the commonest
shell idiom there is, and is refused in `parse_surface`.

**TASK-362: the third distinct way this criterion was self-checked.** Round 4
found the RULE was verified with the function under test. Round 5 found the
DATA could not tell a correct projection from one that keeps only the first of
anything. Round 6 found the PAIRING: every walk resolved its expectation
through the very `path` it was checking, so **46 of 53 declared pairs could be
repointed with the full suite still green**. Both sides are anchored on the key
now. Underneath it was a fixture gap — five declared paths are `None` on a
scratch project and are the only route to three of the six projection kinds,
`tests/fixtures/sample-project` reaches all five, and no test ran `--compact`
against it. The one case asserting that `current` and `target` reach
`--compact` had **never executed**: it skipped when the fixture had no phase
KRs, and its only fixture never has any.

## Verdicts

```
=== VERDICT ===
task: TASK-364
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: c7 both directions on perry-task by mutation (declare-unread RED,
         unread-declared RED), derivation not vacuous (142/142 pairs matched,
         INDIRECT empty, 1,178-combination over-report census = 0 blind spots);
         c12 re-derived at 1,277 pairs and probed end-to-end through the real
         tools in both argument orders (2,554 invocations, 0 accepted, all
         exit 2), guard live under two mutations; c14a on both describe_surface
         branches and on the shared builder, all 57 subcommand payloads equal
         to declaration union universal; UNIVERSAL proven non-tautological
         because every tool's intersection-of-all-subcommand-flags is empty
not-checked: the other five tools' per-subcommand AST direction checks
         (TASK-411, out of scope by instruction); criteria 1-6, 8-11, 13;
         Windows paths; the honesty probe's --help/--describe entries, which
         parse_surface makes structurally universal rather than testing
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-408
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: c14a on bin/perry — `perry list --json` tools[], `perry describe
         <tool>` and `perry describe <tool> <sub>` compared as whole dicts
         against each tool's own `--describe --json` for all 6 tools and all
         57 subcommands (identical), and each against declaration union
         universal (0 mismatches); tool-level flags == surface_flags on all 6;
         undeclared list = 13, matching the Bound; both describe_surface
         branches and the shared builder all reddened by mutation
not-checked: criterion 14b's architecture claim beyond the four surfaces above
         (graded ROW); criterion 11's README examples (graded ROW);
         `perry list` human output beyond the existing per-tool parse
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-360
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 3 across all 30 perry-task subcommands (9 never read
         args.id, enumerated); criterion 2a by exhaustive --help/-h position
         sweep over 9 writing invocations on scratch copies; criterion 4a by
         six mutations plus an empirical dry-run sweep of all 8 perry-tasks
         writers and 27 perry-task subcommands (0 wrote); the refusal
         disabled outright on the FULL suite — green
not-checked: the 13 tools declaring no SURFACE; Bound F shapes other than
         unknown-flag and missing-value; non-UTF-8 or Windows paths;
         concurrency
proof: bin/perry-task:7745 refuses only read["extra"][1:]; read["extra"][0] is
       bound to a.id at :7724 and 9 of the 30 subcommands never read it, so the
       first positional is accepted, dropped and reported as a success. The
       comment at :7740-7742 asserts the opposite and is what makes the refusal
       stop where it does. `perry-task ask USER-001 --needed "…"` exits 0,
       ignores USER-001 and mints USER-002.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-407
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 10a, Bound F shape "missing required value", over the
         14-tool --root population re-probed WITH a valid subcommand (12
         correct, 2 wrong); every unguarded argv value-read in all 20 Bound-B
         executables enumerated by source scan
not-checked: the remaining five Bound F shapes on the twenty executables;
         perry-state-cost's --breakdown/--samples drop, confirmed in source but
         unreachable in the fixture
proof: bin/perry-goals:2841 `setattr(a, flags[t], argv[i] if i < len(argv)
       else None)` — the identical line removed from four other tools — leaves
       a valueless flag as no flag, exit 0; the same line is
       bin/perry-knowledge:605. `perry-goals commit --track main --promise …
       --root` run from inside a DIFFERENT project exits 0 and writes
       okr.jsonl and .perry/events.jsonl into the cwd's project.
       tests/test_bin_argument_contract.py:920 cannot see either: it probes
       `<tool> --root` with no subcommand, where "expected one of …" returns 2
       for an unrelated reason.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-362
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criteria 5 and 13. 25 mutations. All 5 round-5 fixes attacked and all
         hold (cardinality, order, subdict recursion, full-path key walk, CLOCK
         bound). Criterion 13: 8 vocabulary mutations, all red; a mode the
         schema does not know is reported faithfully. Criterion 5: all 53
         declared (key, path) pairs enumerated against
         tests/fixtures/sample-project copied to /tmp
not-checked: the 5,000-token half of criterion 5 (bytes measured, not
         tokenised); SKILL.md step 3's call site; --compact against an
         unreadable or non-UTF-8 store; the i18n fixture; the full suite on 44
         of the 46 green pairs, measured on a 9-module set with 2 confirmed on
         all 122
proof: tests/test_compact_payload.py:175, :108-110 and :209-210 build the
       expectation with STATE._at(self.full, path), taking `path` from the same
       COMPACT entry under test, so the declaration is both question and
       answer. Repointing bin/perry-state:2298 at "phase.objectives" makes
       --compact report current:null/target:null for all three key results of
       tests/fixtures/sample-project while --json reports current:1.0/
       target:3.0, and the full suite stays at its 3 known reds. 46 of 53
       pairs are green this way; :346, the only case asserting current/target
       reach --compact, skips on its only fixture.
=== END VERDICT ===
```
