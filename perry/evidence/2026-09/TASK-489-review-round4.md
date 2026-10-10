# TASK-489 — review round 4: V4 PASS (narrow, § Round 6) and architecture PASS, on a5c3bdc8

Candidate: `9509170c78ef47d4c0ee907f0b71e7a2df2f2dbc..a5c3bdc83ab3eb33c9e4e95380f9196d016ca7d7`.
This round reviews round 6, `44cfbb53..a5c3bdc8`, which is the user's option A
of 2026-10-09. Two fresh-context reviewers ran, each in its own isolated
worktree. Both reported that both projects' `.git/perry` were absent before and
after.

## V4 — PASS (narrow check, spec § Round 6 item 3)

**Item 1: mixed events.**
- The reviewer listed every place that builds an event: the 7 kernel commands,
  import replay, and the importer's synthetic export. None of them mixes a
  template change with an item change.
- More than 30 crafted exports let no forbidden value through. They covered
  orders and splits across events, `ceiling:` and `state_root` beside a
  template change, untyped value rows, and changes to `rel:` and `attach:`.
- The mutant that disables the rule is killed.

**Item 2: recovery marker.**
- 18 runs on scratch copies, covering both project shapes, three marker
  shapes and three flag sets, all exit 1 with the refusal.
- In every run the marker, the project files and their mtimes are unchanged,
  and no work directory is created.
- Two mutants are killed.

**`items.jsonl`.** Byte-identical to round 5: `a516bd22…` for this repository
and `a8ce77e9…` for SkyTonight. Both projects reconciled.

**Findings, not FAIL** (carried to the next change):
1. Mutants K2–K6 drop single keys from the rule's key list. They survive,
   because every round-6 test event holds `type`, `state` and a field. The
   reviewer found no behaviour hole.
2. The `type_of` docstring (`commands.py` ~1169–1174) still credits round 5
   alone for "order never decides".
3. A template change in the same event as `ceiling:` or `state_root` is
   accepted. The reviewer found no forbidden-value path through it, and
   nothing writes such an event.

```
=== VERDICT ===
task: TASK-489
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-489-spec.md
checked: § Round 6 items 1–2 and the items.jsonl identity, on a5c3bdc8 detached in my own worktree, with python3.11. Item 1: listed every event write site (7 kernel commands, import replay, and the importer's export at bin/perry-kernel-migrate:563-619); none mixes a template change with an item change. Ran 30+ crafted exports at head through the kernel test harness: template alone then item in all 6 orders; item then template; item, template, update; ceiling+template both orders and with item changes; state_root+template; untyped value rows (3 shapes) then a template; template plus field, state, rel or attach on an existing item; two templates in one event; relation then a template that removes its kind; template with items=[new id]. None let a forbidden value through. Mutant K1 (commands.py:1117 rule disabled) killed. Item 2: scratch copies of this repository (107 asks) and SkyTonight (0 asks), 3 marker shapes (valid empty, staged commit, malformed) x 3 flag sets (--work, plan-only, --work --json) = 18 runs; all exit 1 with the pending-marker refusal; marker bytes, project sha256 and mtimes unchanged; work directory never created. Mutants R1 (:846 if False) and R2 (:845 wrong root) killed. items.jsonl from a5c3bdc8 on scratch copies: a516bd22… and a8ce77e9…, byte-identical to round 5; both reconciled, criteria 1-5 true. Affected tier green (160 modules, 4551 tests; not a green suite). git diff --check clean. Restores verified with bin/perry-restore-check against a5c3bdc8. Both .git/perry paths absent before and after.
not-checked: Criteria re-derived in rounds 1-3 (out of scope). The full suite (tests/run --tier full) was not run. The scratch copy of this repository was taken from the current main checkout, not from c1db1f29; its hash still matches. A marker that is a dangling symlink (scan_recovery uses exists(), which follows symlinks) was not tested. A marker appearing during the asks read was checked only through the author's mocked test, not by hand. Required-field and guard changes across template versions were not probed (outside round 6).
proof: Mixed-event rule at kernel/perry_kernel/commands.py:1116-1122; recovery check at bin/perry-kernel-migrate:845-852. Findings, not FAIL: (1) partial-rule mutants K2-K6 at commands.py:1118-1119 (drop field:, type/state, rel:, attach:, state+field) survive the whole kernel suite, because every round-6 test event holds type, state and a field, so the rule's parts are untested apart; no behaviour hole found. (2) the type_of docstring (commands.py ~1169-1174) still rests the "order never decides" claim on round 5 alone. (3) template+ceiling: and template+state_root events, and a mid-history state_root change, are accepted on replay; no forbidden-value path, and the spec bars only item changes. Logs: $TMPDIR/perry-scratch/agent-a98434c34a593dedd/{suite.log,mut-*.log,mutfull-*.log,adv/,rep-*.json}.
=== END VERDICT ===
```

## Architecture review round 5 — PASS

**Result.** No contradiction and no missing context, so the user has nothing
to decide.
- **Triggers.** "New bin executable" and "module architecture edit" are true.
  The other four triggers are false.
- **`describe`.** Byte-identical at base and head: sha256 `fc8104c4…`, 21,403
  bytes.
- **Rules that hold:**
  - Goal 1 and NN-K1: the new literals are kernel change keys, not template
    names;
  - NN-K4: no new command, flag, key or error code;
  - root § 3 and NN-1: `parsers.scan_recovery` is an existing reader.
- **Not touched:** DESIGN-023 § 7, because the change is a structural export
  check, not a method rule.

**Descriptive drift** (non-blocking, carried to the next change):
- `bin/ARCHITECTURE.md:118–119` and the refusal message say "a file under the
  project". The comparison covers only the state root and `.perry/`.
- `bin/ARCHITECTURE.md:108–110` does not say that `scan_recovery` also reads
  dossier frontmatter.
- The "Last reviewed" dates in both module headers are stale.
- `bin/README.md:62` is awkward wording.

The full COMPLIANCE block is in the session transcript of 2026-10-10.

## Disposition

V4 passes on `a5c3bdc8`. With the narrow check of round 6, every criterion is
scored PASS by a fresh reviewer: criteria 1–5 were re-derived in rounds 1–3,
and rounds 4–6 left `items.jsonl` byte-identical. Architecture passes on the
same head. Next come the merge gate and the merge.
