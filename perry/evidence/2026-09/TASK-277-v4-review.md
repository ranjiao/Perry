# TASK-277 — V4 review

> Reviewed: merge `b493493` (range `b493493^1..b493493`, base `0724fa6`)
> Criteria: `perry/evidence/2026-09/TASK-277-spec.md` — the only authority here
> Reviewer worktree: `worktree-agent-a0226103415fff483`
> Date: 2026-09-07

## 0. How this round was run, and why it was run on a copy

My worktree's branch head is `d49964e`, which is **before** the merge under
review: `perry/linkage.jsonl` and `tests/test_linkage_import.py` do not exist in
it. `review-constraints.md` forbids `git checkout`, so the reviewed tree was
reconstructed as a scratch copy rather than checked out:

```
git archive b493493 | tar -x -C <scratch>
```

Three independent copies were used — `w277` (baseline), `mut` (mutation),
`play`/`adv/*` (behaviour) — and each was made a git repository of its own so
the suite's `tree_guard` and `_git_tracks` fixtures would work. **Provenance was
proved, not assumed:** each copy's `git write-tree` is
`8013d9c83be013b02f7cf36ac14021b735e83ab7`, byte-identical to
`git rev-parse b493493^{tree}`. Nothing under `/Users/bytedance/proj/Perry`
outside this worktree was written; my own worktree is clean apart from this
document.

Every mutation restore was verified against `git show b493493:<path>` read from
the live object store — never against bytes this harness snapshotted — with
`__pycache__` cleared and a sleep past the whole-second boundary on both sides
of every edit.

## 1. Baseline, measured here, before anything was changed

`bash tests/run` in my own copy of the reviewed tree:

```
116 modules · 3320 tests · 295.7s · 8 workers
✗ 2 of 116 MODULE(S) red
    test_contract_key_parity.py — 2 of 35 failed
    test_diagnose.py            — 1 of 145 failed
```

`python3 bin/perry-lint --root .` on the reviewed tree: **0 error(s), 38
warning(s)**.

Both red modules were re-run **alone** and then re-run alone against a scratch
copy of the merge base `0724fa6`, where they fail identically (2 and 1
failures). They are pre-existing and unrelated to this row: the failing keys are
`conformance.in_progress_with_no_live_run[].means` and a `LOAD-03` self-check.

A first baseline run was discarded: taken on a non-git copy it showed 4 red
modules, the two extra being `test_tree_guard` (8 errors) and
`test_one_header_rule` (1) failing on `git rev-parse HEAD`. Those were artifacts
of my own copy, not findings, and they are recorded here so the discarded number
is not mistaken for a result.

`tests/test_linkage_import.py` alone: **42 tests, OK, 4.5s.**

Machine load average was **7.5–7.7 throughout**. Every duration above is
therefore indicative only, and no timing claim in this review is load-bearing.

## 2. The count — re-derived, not accepted

The exhibit is second-hand (the implementing agent was rate-limited with no
result document; `perry/evidence/2026-09/TASK-277-result.md` is a STUB on both
the merge and on `main`). Every number below was re-derived with a hand-rolled
parser deliberately **not** reusing the importer's own reader.

Register frontmatter, parsed independently:

| kind | register | store `perry/linkage.jsonl` |
|---|---|---|
| `kr` | 6 | 6 |
| `edge` | 15 | 15 |
| `unlinked` | 100 | 100 |
| **total** | **121** | **121** |

Set equality holds in both directions on all three kinds, including the full
`(task, kr)` edge pairs, not just the task ids. The register has no duplicate
`unlinked` entry, no duplicate edge task, and no task appearing as both an edge
and unlinked.

**The store is byte-reproducible from the register.** Re-running
`perry-tasks linkage-write --root . --from-register` on a fresh copy produced a
file whose sha256 is `025ab97c1581f7cb…` — identical to the committed
`perry/linkage.jsonl`. The committed store is the import's output, not a
hand-edited file.

### 2.1 The two spec edges that are not in the store

The spec's literal words are that the 11 edges are *"exactly TASK-203, 209, 067,
229, 095, 233, 247, 099, 050, 215, 262 — neither invented nor dropped"*, and
`TASK-050` and `TASK-099` are not in the store. **They were not dropped by this
row.** The proof is an artifact already in the tree —
`perry/phase/snapshots/2026-09-02-003-linkage-pre-kr2-withdrawal.md` — parsed
with the same independent parser:

| | pre-withdrawal snapshot (`updated 2026-09-02T06:26:55Z`) | register as imported (`2026-09-03T06:06:45Z`) |
|---|---|---|
| kr | 7 | 6 |
| edge | 17 | 15 |
| unlinked | 86 | 100 |

Diffing the two registers structurally:

```
kr removed  : ['P003-O2-KR2']
kr added    : []
edges removed : [('TASK-050', 'P003-O2-KR2'), ('TASK-099', 'P003-O2-KR2')]
edges added   : []
unlinked removed : []
unlinked added   : 14
```

The only structural change is the removal of `P003-O2-KR2`, which took **exactly
its own two edges** with it. Both of the spec's "missing" edges sat under that
KR and under no other. The withdrawal is a recorded user decision, not a
migration artifact: `perry/asks.jsonl` carries `USER-911`, *"answered 2026-09-02:
WITHDRAW P003-O2-KR2"*, with `USER-912` recording how it was written down and
naming the `phase/snapshots/` archive used.

The spec's own baseline of 11 edges was measured earlier on 2026-09-02 than the
snapshot: all 11 appear in the snapshot, alongside the six (`TASK-283`,
`TASK-276/277/278/279/281`) that had been linked in between.

The full reconciliation therefore closes independently:

```
spec baseline (2026-09-02, d49964e)   7 kr + 11 edge + 75 unlinked =  93
  + 6 edges linked before the snapshot        →  7 kr + 17 edge
  − P003-O2-KR2 withdrawn (USER-911)         →  6 kr + 15 edge   (−1 kr, −2 edges)
  + 25 rows added to the board               →       100 unlinked
register and store as imported        6 kr + 15 edge + 100 unlinked = 121
```

**Verdict on the count: a faithful import of a register that moved, not a
dropped edge.** The spec anticipated exactly this and said "Re-measure the
register first and say so in the result if it has moved since" — see finding F3
on the half of that sentence which is not satisfied.

## 3. `via` — enumerated, not sampled

The field that would inflate `P003-O3-KR2`, the KR this design exists to make
honest. DESIGN-015 § 5.2 counts rows linked *in the same action as `add`*, and
the marker is `via: "add"`.

All 121 records were enumerated:

```
via by kind: {('unlinked','link'): 100, ('edge','link'): 15, ('kr', None): 6}
```

**115 of 115 `edge`+`unlinked` records carry `via: "link"`. Zero carry
`via: "add"`.** The 6 `kr` records carry no `via` field at all, which is correct
— a KR is not a declaration by anybody and the schema gives it none of the three
stamp fields. `declared_at` on all 115 is `2026-09-03T06:06:45Z`, the register's
own `updated` stamp, not the migration's clock.

The store that is about to become this KR's authority does not inflate it.

## 4. The register is byte-unchanged — including on a re-run

The one-shot proof: `perry/phase/003-linkage.md` does not appear in
`git diff --stat b493493^1 b493493` at all.

The proof the diffstat cannot give — idempotency — was measured. Three
consecutive `linkage-write --from-register` runs on a fresh copy:

| | register md5 | store sha256 |
|---|---|---|
| committed | `3d9ca8f815ba…` | `025ab97c1581…` |
| after run 1 | `3d9ca8f815ba…` | `025ab97c1581…` |
| after run 2 | `3d9ca8f815ba…` | `025ab97c1581…` |
| after run 3 | `3d9ca8f815ba…` | `025ab97c1581…` |

Unchanged and idempotent. Across **all 21 behavioural cases** in § 6 — including
every refusal — the register was byte-unchanged by the importer every time. The
code carries its own sha256 before/after guard around the write and prints
`003-linkage.md is byte-unchanged (…)`; mutation M9 (§ 5) proves a test catches
it if that ever stops being true.

## 5. Mutation — 14 mutations, 12 red, 1 green, 1 re-run

The prompt named `tests/test_linkage_import.py` as the largest never-mutated
area. It reddens.

| # | file:line | mutation | result |
|---|---|---|---|
| M1 | `bin/perry-tasks:1429` | `LINKAGE_IMPORT_VIA` `"link"`→`"add"` | **RED** `test_via_is_link_and_never_add` |
| M2 | `bin/perry-tasks:1428` | `LINKAGE_IMPORT_ACTOR` `"goals"`→`"work"` | **RED** `test_the_actor_is_the_lane_that_declared_them` |
| M3 | `bin/perry-tasks:1632` | non-empty `agents:`/`projects:` refusal → `if False:` | **RED** ×2 |
| M4 | `bin/perry-tasks:1627` | absent-key refusal → `if False:` | **RED** `test_a_missing_key_is_refused_rather_than_read_as_empty` |
| M5 | `bin/perry-tasks:1613` | day-only `updated` refusal → `if False:` | **RED** |
| M6 | `bin/perry-tasks:1680` | drop the first edge of every KR | **RED** 30 failures |
| M7 | `bin/perry-tasks:1687` | drop the first `unlinked` record | **RED** 30 failures |
| M8 | `bin/perry-tasks:1658` | objective-disagreement refusal → `if False:` | **RED** |
| M9 | `bin/perry-tasks:1520` | make the importer write the register back | **RED** `test_the_register_is_byte_identical_after_an_import` |
| M10 | `bin/perry-tasks:1534` | `linkage: 1` spec-version gate → `if False:` | **GREEN — survived** |
| M11 | `bin/perry-lint:4482` | drop the new `schema` argument at the call site | **RED** ×3 |
| M12 | `bin/perry-lint:4538` | `_matches_a_declared_store` never matches | **RED** ×3 |

Every restore was verified against `git show b493493:<path>`; `bin/perry-tasks`
returned to sha `e5febc75547f` and `bin/perry-lint` to `bafcb0680db3` after each.

**A correction I owe this round.** M9 — the mutation that makes the importer
write the register — left the register in the `mut` copy carrying an extra
trailing newline, because the module exercises the real importer against the
real tree. My harness restored only the file it had edited, so that collateral
byte survived into M10, M11 and M12. I found it with `git status` afterwards,
restored the register from the ref, and **re-ran M10 and M1 on a verified-clean
tree**: M10 survives genuinely (the extra byte is in the body, below the
frontmatter, and changes no derivation) and M1 is genuinely red. The numbers in
the table are the re-verified ones.

## 6. Behaviour — 21 adversarial registers, each on its own fresh copy

Every case got its own `git archive b493493` extraction, so no case could
contaminate the next. After each run I asserted both the store's record count
and whether the store bytes changed.

**Refused, store untouched, register untouched, nothing written** (exit 1):
non-empty `agents:`; non-empty `projects:`; `agents:` key absent entirely;
`linkage: 2`; day-only `updated:`; `updated:` absent; objective id disagreeing
with the KR id; unparseable frontmatter; no frontmatter at all; duplicate `kr`
id; and `linkage-write` without `--from-register`.

**Accepted correctly:** a register that has moved again (one extra `unlinked`
entry → 122 records; one extra edge → 122 records); a register with a whole KR
block removed → 119 records, which is precisely the `P003-O2-KR2` scenario
of § 2.1 reproduced; and a store file that is absent → 121 written fresh.

**Refused with exit 2, correctly declining to overwrite:** a corrupted
(non-JSON) store on disk.

Two of my early "moved register" cases refused for a reason that was **my
fault, not the code's**: I used a `TASK-0NN`-shaped placeholder id, whose shape
`schema/state-schema.json` rightly rejects. Re-run with a well-formed synthetic
id they pass, as recorded above. Recorded here so the refusal is not misread as
a defect.

## 7. `bin/perry-lint` — the 48-line change, and the absent-store census

The change is a genuine bug fix, not scaffolding: without it the very next
`perry-lint` run after the import raises `NS-01` on `perry/linkage.jsonl` and
advises the user to `/perry relocate` **away from Perry's own store**. It fixes
this by reading record shapes out of `schema § stores.declared` keyed on the
declared `discriminator`, rather than adding a fifth hand-written field tuple.
I enumerated the call sites: `looks_like_perry_record` has exactly **one**
production caller (`bin/perry-lint:4482`) and it passes `schema`; the
`schema: dict | None = None` default exists for the four test modules that call
it with one argument. No call site was missed.

The explicitly-unmeasured question — does `unchecked, not clean` still hold with
`perry/linkage.jsonl` **absent**? Measured on the reviewed tree by moving the
file aside and restoring it:

```
store present : · linkage store: 121 valid record(s), comparison incomplete — drift is unchecked, not clean
store absent  : · no `linkage.jsonl` — drift against the linkage store is unchecked, not clean
```

**It holds.** Both lines are honest; neither claims `clean`. Error count was
0 in both states.

## 8. `agents: []` and `projects: []`

Asserted, not silently produced. `LINKAGE_UNIMPORTED_KEYS` drives two distinct
refusals — one for a key that is *absent* and one for a key that is *non-empty*
— and both were confirmed to fire behaviourally (§ 6) and to be covered by
tests (M3, M4). This is the difference the spec asked for: an absent key and an
empty list both yield zero records, and only one of them is a check.

## 9. Findings — none of them a FAIL of this spec

**F1 · The store carries no uniqueness or mutual-exclusion invariant.**
Enumerating the category rather than the instance, there are five ways a
register can contradict itself about a row:

| register input | importer | register lint | store census |
|---|---|---|---|
| duplicate `kr` id | **refused** (two-reader cross-check) | 0 errors | — |
| one task under two KRs | imports both | **error** `linkage-task-single-kr` | "valid" |
| duplicate `edge` (same task, same KR) | imports both, silent | 0 errors | "121 valid record(s)" |
| duplicate `unlinked` entry | imports both, silent | 0 errors | "valid" |
| one task both `edge` **and** `unlinked` | imports both, silent | 0 errors | "valid" |

The last three pass every gate in the system. The third is the one that matters
most: DESIGN-015 § 5.2 derives *never-asked* as "the store holds neither an
`edge` nor an `unlinked` record", and a row holding **both** is a state that
derivation has no reading for.

This is **not a defect of this row**, and I checked rather than assumed: I fed
the same contradictory register to `perry-lint` at the merge base `0724fa6` and
it also reports `0 error(s)`. The gap is a pre-existing register-lint gap that
row B inherits. The importer itself is correct — `linkage_account` is genuinely
multiset-safe (`_multiset_minus`, not a set difference), so it faithfully
mirrors whatever multiplicity the register states, which is exactly its job.
The actual register is clean. **File as a separate row**: the store, or the
register lint, should refuse a task that is both linked and declared unlinked.

**F2 · The `linkage: 1` spec-version gate is untested.** M10 survived: no test
feeds the importer a register declaring a different spec version. The **guard
itself works** — I verified behaviourally that `linkage: 2` is refused with
"Nothing was written" and the store untouched — so this is a test-coverage gap,
not a live defect. It is the one uncovered branch I found in the importer.

**F3 · The result document is a stub, and the spec asked it to speak.** The
spec's verification clause reads "Re-measure the register first **and say so in
the result** if it has moved since." The register moved substantially (93 → 121,
and a withdrawn KR), and `perry/evidence/2026-09/TASK-277-result.md` says
"STUB — in progress" on both the merge and `main`. The measurement was clearly
done — the store proves it — but it is not written down where the spec directs.
The implementing agent was killed by a rate limit, so this is an interrupted
row, not a dishonest one. **This row should not be closed until the result
document records the re-measurement**; § 2.1 of this review can be lifted
wholesale into it.

**F4 · `tests/durations.json` provenance nits.** The new
`task-277-linkage-import` entry says the module is "32 unittest cases"; it is
**42**. Its `ref` is `c924a52`, which the suite's own durations report lists
among "4 entries at refs git could not resolve". Neither affects behaviour.

**F5 · The exhibit's claim that the tests were never mutated is not quite
true.** `test_the_actor_is_the_lane_that_declared_them` carries the docstring
*"Found by a mutation: renaming `actor` left every test green."* At least one
mutation was run by the author. Recorded only because the exhibit is
second-hand and this round was told to distrust it in both directions.

## 10. Verdict reasoning

Against the spec, clause by clause:

- **The count.** Re-derived independently: 121 = 6 + 15 + 100, matching the
  register exactly in both directions. The delta from the stale 93 baseline is
  fully accounted for by a recorded user decision (`USER-911`) and board growth,
  corroborated by a snapshot artifact in the tree rather than by the exhibit.
  The two "missing" edges left with the KR they sat under, before this row ran.
  Not dropped. **Met.**
- **`agents: []` / `projects: []` asserted.** Met, and both refusals fire.
- **`phase/003-linkage.md` byte-unchanged.** Met on the merge, and met on
  re-run, which the diffstat could not show.
- **A count that differs is a failure, not a rounding.** The gate is set
  equality in both directions across all three kinds, not two integers that
  agree. Met.

V4 asks whether this code does the wrong thing on an input the user can produce.
Across 21 adversarial registers I could not make it write a wrong store: every
malformed input is refused with nothing written, every moved register is
followed faithfully, and every refusal leaves both the store and the register
untouched. The one contradictory-register class it passes through (F1) it passes
through *faithfully*, and no gate at the merge base caught that class either.

**PASS.**

=== VERDICT ===
task: TASK-277
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-277-spec.md
checked: Reconstructed the reviewed tree as three scratch copies of b493493, each proved identical by git write-tree = 8013d9c8 (my worktree head is d49964e and lacks the code; checkout is forbidden). Own baseline in-copy: bash tests/run = 116 modules / 3320 tests / 2 red modules (test_contract_key_parity 2, test_diagnose 1), both re-run alone AND re-run alone at merge base 0724fa6 where they fail identically, so pre-existing; perry-lint --root . = 0 errors 38 warnings; test_linkage_import alone 42 tests OK. Load 7.5-7.7 throughout so all durations are indicative only. Re-derived every exhibit number with a hand-rolled parser not reusing the importer's reader: register = 6 kr + 15 edge + 100 unlinked = 121, equal to the store in both directions including full (task,kr) edge pairs; store is byte-reproducible from the register (sha256 025ab97c1581 matches the committed file). Reconciled the 93->121 delta against perry/phase/snapshots/2026-09-02-003-linkage-pre-kr2-withdrawal.md (7 kr + 17 edge + 86 unlinked): the only structural change is P003-O2-KR2 removed taking exactly TASK-050 and TASK-099, corroborated by USER-911/USER-912 in perry/asks.jsonl. ENUMERATED via across all 121 records: 115 of 115 edge+unlinked carry via:link, zero carry via:add, kr carries none; declared_at is the register's own 2026-09-03T06:06:45Z on all 115. 14 mutations, restores all verified against git show b493493:<path> with __pycache__ cleared and whole-second waits: 12 red, 1 green (M10), 1 re-run after I found M9's collateral write to the register and restored it from the ref. 21 adversarial registers each on its own fresh archive extraction, asserting store count, store bytes and register bytes each time. Three consecutive re-runs for idempotency. perry-lint census measured with linkage.jsonl both present and ABSENT (absent still says "unchecked, not clean"). Enumerated all call sites of looks_like_perry_record (one production caller, passes schema).
not-checked: I did not read all 747 lines of tests/test_linkage_import.py line by line — I probed it with 14 mutations of the production code and recorded which tests reddened, so a test that is green for the wrong reason on a branch none of my mutations touched would not have been caught. I did not exercise bin/perry-goals link to see whether the register's only sanctioned writer can itself produce the F1 contradictory registers; I established only that hand-editing produces them and that both gates stay silent. I did not audit the other ~640 lines of the bin/perry-tasks addition that no mutation reached (helpers, --json shapes, the linkage-build and linkage-diff report bodies beyond their exit codes). I did not re-run the full 116-module suite at the merge base — only the two red modules there. I did not touch row C, the six readers in DESIGN-015 § 5.6, or viewer/parsers.py, all out of scope. I did not verify the store against schema/state-schema.json by hand, relying on perry-lint's validator, which is the same function the importer gates on — so a defect in that shared validator would be invisible to both. I did not check any project other than Perry's own, and did not review the Chinese fixture beyond what tests/run covers.
proof: n/a — PASS. Findings filed for separate rows, none of them a breach of this spec: F1 the store has no uniqueness/mutual-exclusion invariant, so a duplicate edge, a duplicate unlinked entry, or a task that is both edge and unlinked imports silently and passes both the register lint and the store census — verified pre-existing by feeding the same register to perry-lint at merge base 0724fa6, which also reports 0 errors; F2 bin/perry-tasks:1534, the `linkage: 1` spec-version gate, survives mutation M10 because no test feeds a differing spec version, though the guard itself was confirmed working behaviourally; F3 perry/evidence/2026-09/TASK-277-result.md is a STUB on both the merge and main while the spec requires the re-measurement to be said in the result, so the row should not be closed until it is written down; F4 tests/durations.json says 32 unittest cases where there are 42 and cites ref c924a52 which git cannot resolve.
=== END VERDICT ===
