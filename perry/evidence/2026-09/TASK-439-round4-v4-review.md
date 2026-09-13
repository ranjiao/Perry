# TASK-439 — round 4, V4 review (covering rounds 3 and 4)

Under review: `d8dc6ae8` (round 3, `USER-928` answer **A**) and `852ce858`
(round 4, answer **C**), together. Criteria:
`perry/evidence/2026-09/TASK-439-spec.md`. I wrote neither commit, and I am
bound by neither round 1's nor round 2's conclusions.

**Result: FAIL**, on two findings, both in the half A changed. C is
substantially right and is charged only at ROW.

---

## 0 · Base check — it was wrong, and it was recoverable

Recorded here rather than only in the reply, because "I checked and it was
fine" and "I did not check" are different answers and only one is evidence.

The dispatch predicted the fault and the prediction was correct.

| step | command | result |
|---|---|---|
| HEAD as cut | `git log --oneline -1` | **`583f024f`** — "Merge bin-contract-phase-a", 128 commits behind |
| does it carry the work | `git merge-base --is-ancestor 852ce858 HEAD` | **exit 1 — no** |
| tree state | `git status --porcelain` | **clean, no output** |
| strict ancestor of `main` | `git merge-base --is-ancestor HEAD 3d2ec784` | exit 0 — yes |
| branch | `git rev-parse --abbrev-ref HEAD` | `worktree-agent-afb7e1e32ec56ab7d` |

All three preconditions held, so I fast-forwarded **my own branch only** —
never `main`, never another branch — with `git merge --ff-only 3d2ec784`.
131 files, 27283 insertions. Re-asserted after:

```
3d2ec784 TASK-236 round 4: a blank join key is not a wildcard
852ce858 ancestor exit=0
d8dc6ae8 ancestor exit=0
```

So this is the fifth consecutive dispatch from this session to arrive at
`583f024f`. That is not a flake; it is the worktree tool's branch point, and
it will keep happening until something changes upstream of the review round.
It belongs to whichever row owns the dispatch path, not to this one.

**Method note.** `perry-task add` is a write tool, so nothing in this round
was run against the project under review. Every probe drives the real binary
against a **temporary project** built by the suite's own fixture
(`tests/test_add_writes_the_edge.py § Fixture.project`) and addressed with
`--root <tmpdir>`, which is what the module's own tests do. Every mutation was
made in a `git archive` scratch copy under the session scratchpad, never in the
live tree. `bin/perry-restore-check 3d2ec784 …` confirms the live tree is
byte-identical to the ref for all four files in scope (§ 4).

---

## 1 · What reproduces, and what the rounds got right

I re-measured both rounds' central claims before looking for defects.

- **Round 4's disclosed green mutation is genuinely fixed.** I re-ran M4 myself
  — `viewer/parsers.py:4139`, the `unlinked` branch of
  `linkage_records_for_phase`, forced to `return True`, which is option B
  simulated — in a scratch copy at `3d2ec784`. Module went **RED**, 1 of 32,
  and the failure is `test_the_named_reader_is_phase_scoped`, the test round 4
  names. The phase-004 register it added is doing the work it claims. This is
  the best thing in either commit and it survives an independent re-run.
- **Round 4's M5 control reproduces and is correctly green.** Disabling the
  empty-slice `None` guard (`viewer/parsers.py:4143` → `if False:`) leaves all
  32 green, which is what it must do once the test stops going through that
  door.
- **C's deletion is clean on the two surfaces it names.** The live refusal
  (captured from the real binary, § 2 P1) carries `CANNOT BE WITHDRAWN` and no
  visibility clause; `work/reference/subcommands.md:591` likewise.
- **Round 3's warning split has both branches reachable**, and the store-less
  branch says something true of the project it fires on (§ 2, P8).
- **The gate still refuses where the register answers** — P1, rc=1, and the
  message is about the KR question rather than something incidental.

Round 4 is, on its own, a good round. Both findings below land on A.

---

## 2 · FAIL-1 — a `linkage.jsonl` that will not parse silently stands the gate down, and the row is lost to the KR forever

**The behaviour.** `_current_store_phase` (`bin/perry-task:2794`) asks
`P.load_linkage_store(state_root)`, and that reader **returns `None` for a
malformed store exactly as it does for an absent one** — by its own docstring
and its `except (OSError, ValueError): return None`
(`viewer/parsers.py:3952-3953`). So a store that exists, is full of key
results for the current phase, and merely will not parse makes
`_current_store_phase` return `""`, which A made the gate's stand-down
condition.

**Measured, driving the real binary.** Same fixture throughout; the only
variable is the state of `linkage.jsonl` and `phase/CURRENT`.

| # | state | rc | row filed? |
|---|---|---|---|
| P1 | valid store, current phase declared — **control** | 1 | no, refused |
| P2 | `phase/CURRENT` deleted (the prescribed window) | 0 | yes, warned |
| P3 | `CURRENT` = `004-next`, store declares only 003 | 0 | yes, warned |
| **P4** | **store + one unparseable line** | **0** | **yes, warned** |
| **P5** | **store wrapped in git merge-conflict markers** | **0** | **yes, warned** |
| P6 | `phase/CURRENT` empty | 0 | yes, warned |
| P7 | `phase/CURRENT` = `3-storage` (unpadded) | 0 | yes, warned |
| P8 | no store at all — **control for the other branch** | 0 | yes, warned |

**It is a regression, not an inherited hole.** The same eight probes against
`d8dc6ae8^`, extracted to a scratch copy with `git archive`:

```
[PRE-A]  P4 one unparseable line     rc=1  REFUSED
[PRE-A]  P5 merge-conflict markers   rc=1  REFUSED
[POST-A] P4 one unparseable line     rc=0  FILED ['TASK-0NN']
[POST-A] P5 merge-conflict markers   rc=0  FILED ['TASK-0NN']
```

Before A the gate keyed off `.exists()`, which is true of a corrupt store, so
it refused and nothing was lost. A replaced that with a predicate that cannot
tell "the register has no answer" from "the register could not be read".

**What the caller is told is false about a file they can see.** The stderr in
P4 and P5 is, verbatim, the between-phases branch:

> `linkage.jsonl` declares no key result for the current phase, so there is
> nothing to name and an `unlinked` declaration would have no phase to be made
> against — the window `goals/reference/phases.md § score-phase` step 7 opens,
> until the next `plan-phase`

Every clause of that is wrong for a corrupt store. The store *does* declare key
results for the current phase. The caller is *not* in the between-phases
window. And the remedy it names — `/perry goals plan-phase` writes the register
— does not fix an unparseable file and would append to it. This is the same
defect class the row has now FAILed on twice: **a sentence that is false about
a file the caller can see.** Round 3 split that sentence precisely to stop
telling one caller something untrue and introduced a third caller it tells
something untrue.

**The asymmetry that made round 2's FAIL-2 a FAIL is reproduced in the new
window.** In the corrupt state the honest answer is still refused:

```
[POST-A] P4b unparseable + --unlinked   rc=1  REFUSED
         "linkage.jsonl declares no key result for the current phase …"
```

So a caller who reads the warning and tries to answer honestly is turned away,
exactly as in the window A was written to fix — and the accepted paths are
silence, or a `--kr` nothing validates.

**The consequence is permanent.** The filed row is not merely warned about. Its
`add` event carries `kr: null`, which puts it in the KR's denominator as asked
and unanswered, and the spec's own § *What this row does NOT do* says such rows
are permanent because a later `perry-goals link` writes `via: "link"`, which
`P003-O3-KR2` excludes by design. Measured through the KR's own reader
(`lib.same_action_linkage`) on the P4 fixture:

```
numerator  : 0
denominator: 1
never_answered: ['TASK-0NN']
```

(`TASK-0NN` stands for the id the fixture project minted inside its own
temporary directory; no id was minted on this board.)

**The input is one a user produces.** `linkage.jsonl` is an append-only store
written by two lanes, on a project whose own memory records two checkouts
minting the same id because their locks never saw each other. A conflict marker
or a half-written line is the ordinary failure of that arrangement, not an
exotic one. `load_linkage_store` also returns `None` on `OSError`, so a
permissions or I/O fault reaches the same branch.

**The category, enumerated (rule 1), not the next instance.**
`_current_store_phase` returns falsy in exactly five states, and the gate plus
the warning attribute all five to one. Read off `bin/perry-task:2802-2811`:

| # | why it returns `""` | stand-down right? | message true? |
|---|---|---|---|
| 1 | `phase/CURRENT` absent | yes — the prescribed window | yes |
| 2 | `CURRENT` present but not `^\d{3}` (empty, `main`, `3-storage`) | arguable | **no** where the store does declare KRs for a phase |
| 3 | store **absent** → `None` | yes | yes — separate branch, P8 |
| 4 | **store MALFORMED or unreadable → `None`** | **no** | **no** |
| 5 | store parses, no `kr` record for `<NNN>-` | yes — the real gap | yes |

Two of five are wrong; #4 is the one that loses data. The gate is a single
condition with no track branch, so `--track intake` reaches it identically —
the spec's named remainder is inside this finding, not beside it.

**What would make it pass.** Distinguish the two `None`s. The stand-down
belongs to states 1, 3 and 5; states 2 and 4 should refuse, naming the actual
problem — `perry-lint § check_linkage_store` already exists to say *why* a
store will not parse, and the refusal can point at it.

---

## 3 · FAIL-2 — removing the phase match from `_current_store_phase` leaves the entire suite green

Round 4's own best finding was a guard that passed through the wrong door. The
dispatch asked me to look for the same shape in the other new tests. It is in
round 3's class, uncorrected.

**The mutation.** `bin/perry-task:2809`, anchored by line number, in the
scratch copy:

```python
-                and str(rec.get("phase") or "").startswith(f"{number}-")):
+                and str(rec.get("phase") or "").startswith("")):
```

That deletes the phase match entirely: the function now returns the first `kr`
record's phase whatever phase it belongs to. It is the exact negation of the
property the class `TestTheGateKeysOffThePhaseNotTheFile` is named for and that
the commit message states — *"the gate now asks `_current_store_phase`, the
same predicate the writer asks, read from the store's own `kr` records"*.

**Result: GREEN.** Module 32/32 green. Then the whole suite, twice, in the same
scratch copy, `__pycache__` cleared before each run:

```
mutated  : 130 modules · 3794 tests · ✗ 5 failed
baseline : 130 modules · 3794 tests · ✗ 5 failed
```

The two runs are **the same five tests by name** — `test_contract_key_parity`
×2 and `test_resume`'s clock-dependent one (the session's standing reds), plus
`test_one_header_rule`'s git-dependent test and a `test_blank_cell_is_one_rule`
error, both of which are artefacts of a `git archive` copy not being a git
repository and are present in the baseline identically. **Nothing reddens.**

**Why the tests cannot see it.** The class's fixture is

```python
def gap(self):
    d = self.project(store_edges={}, store_unlinked=[])
    (d / "phase" / "CURRENT").write_text("")
    return d
```

With `CURRENT` empty, `linkage_phase_number("")` is falsy and the function
returns at `bin/perry-task:2806` — **the store is never read**. So every test
in the class exercises door 2 of the table in § 2 and none exercises door 5,
the one the class is named for. The docstring says the fixture is *"a project
whose store has no records for the current phase"*; it is a project with no
current phase.

A narrower mutation confirms the boundary rather than assuming it: changing the
function's final `return ""` to `return slug` reddens only two tests, both
`store-less-project` tests, because the store-less path is the only one with
coverage that reaches past line 2806.

**This is a product finding, not a test-tidiness one**, and `review.md § 2`'s
table puts it at V4 explicitly: *"a mutation comes back green — the guard does
not work, or the test does not test it."* The product consequence is concrete:
`_current_store_phase` is **also the writer's predicate**
(`bin/perry-task:2780`), so under this mutation a `--unlinked` declaration made
while phase 004 is current is stamped `phase: "003-storage-code"` — a record
filed under a phase it was not made in, which is the harm `ADR-019` added
`unlinked.phase` to prevent and which `schema/state-schema.json:990` documents.
Nothing in 3794 tests notices.

---

## 4 · ROW findings — real, reported, and not charged against the row

Graded ROW per `review.md § 2`'s table, which sends a false statement in
something nobody executes to its own row rather than to this verdict.

### ROW-3 — C deleted the claim from two surfaces; there is a third, and it carries round 1's original wording

`bin/README.md:436-439`, in the `Usage:` block for `perry-task add`:

> `--unlinked` declares that it serves none, writes a record no `perry-task`
> command can withdraw, and **is reported by `perry-lint` for as long as it
> stands**.

That is FAIL-1's *round 1* form — the `perry-lint` naming, charged and
measured false in round 1 — still standing after a round whose stated
deliverable was *"deleted from both product surfaces, because round 1
enumerated the category"*. I verified the falsehood at source rather than
inheriting it: `bin/perry-lint:1519-1520` `continue`s on any declared id present in
`tasks.jsonl`, so a healthy declaration is reported by nothing there.

It is a product surface, not an archive: `bin/perry-task:16` names
`bin/README.md` the canonical home of the tool's argument contract, and
`tests/test_bin_surface.py` audits it. Round 1's own caller sweep edited this
block and listed it; the § 2 enumeration table did not, and round 4 inherited
the count. The new guard
(`test_the_lane_page_makes_no_visibility_claim_either`) reads only
`work/reference/subcommands.md` and its docstring repeats *"two product
surfaces"*, so it cannot catch this. Its own assertion string —
`assertNotIn("for as long as it stands", …)` — is the literal text
`bin/README.md:439` still carries.

### ROW-4 — "there is no third reader" is an enumeration claim and it is false

Round 4 rests C on there being exactly two readers. There are more, and one is
not phase-scoped at all:

- **`bin/lib/__init__.py:1376-1378`**, in `same_action_linkage`, builds
  `unlinked_at_add` from raw `kind == "unlinked"` records with **no phase
  filter of any kind**, and publishes the ids at `:1499` as
  `declared_unlinked_at_add`. Measured live, read-only:
  `perry-state --root . --json` →
  `linkage.objectives[2].krs[0].current_measurement.declared_unlinked_at_add`
  = **16 task ids**. `perry-goals list --json` carries the same field.
- `perry-state --section linkage` (`bin/perry-state:2176`) is a second named
  surface for the same phase-scoped count; the round names only
  `--section attribution`.
- `perry-goals link --unlinked` prints *"already declared unlinked"*
  (`bin/perry-goals:1619`).

This does **not** overturn C. The store-wide reader is nested inside a KR that
only renders while its phase is current, so the deleted sentence was still not
true of the default surfaces, and the user chose C on its merits. What is wrong
is the enumeration the comment and the result assert, and the guard test pins
only the phase-scoped reader — it would stay green if the store-wide one began
listing past-phase declarations.

### ROW-5 — the same category of claim survives inside `perry-lint`'s own finding text

`bin/perry-lint:1523-1526` tells the caller that an id no row carries is
*"still reported under `declared_unlinked`"* by
`perry-state --section attribution`. That loop sweeps each declaration under
its **own** phase, so for a phase-001 declaration swept while 003 is current
the sentence is false in exactly the way round 2 measured. Same category, a
surface neither round enumerated.

### ROW-6 — two small ones in the same function

`bin/perry-task:2803` reads `phase/CURRENT` with an unguarded `read_text`; an
`OSError` there escapes as a traceback rather than a `Refused`, unlike every
other read on this path. And
`test_the_honest_answer_is_not_refused_while_the_row_is_filed` asserts the
opposite of what its name says — its body requires that `--unlinked` **is**
refused. The docstring reconciles it; the name will mislead the next reader of
the class.

---

## 5 · Mutation table — every restore verified against the ref

`__pycache__` cleared before every run; all mutations anchored by line number
in a `git archive` scratch copy; the live tree never written.

| # | file:line | mutation | expected | result |
|---|---|---|---|---|
| M4 | `viewer/parsers.py:4139` | `unlinked` phase check → `return True` (option B simulated) | red | **RED** — `test_the_named_reader_is_phase_scoped`, 1 of 32 |
| M5 | `viewer/parsers.py:4143` | empty-slice `None` guard → `if False:` | green (control) | **GREEN** — correct |
| M-G | `bin/perry-task:2811` | final `return ""` → `return slug` | — | RED, 2 tests, **both store-less** |
| **M-H** | **`bin/perry-task:2809`** | **phase prefix match → `startswith("")`** | **red** | **GREEN — § 3's finding, module and full suite** |

Restores verified against an independent source, never against snapshotted
bytes. Scratch copy: `shasum -a 256` against `git show 3d2ec784:<path>` —
`viewer/parsers.py` and `bin/perry-task` both identical. Live tree:

```
bin/perry-restore-check 3d2ec784 viewer/parsers.py bin/perry-task \
    tests/test_add_refuses_without_an_answer.py work/reference/subcommands.md
  ✓ all four match 3d2ec784          exit=0
```

`perry-restore-check --root <scratch copy>` is not usable here — it resolves
the ref inside the named directory and a `git archive` extract is not a
repository (`3d2ec784 is not a commit in …`, exit 2). I hand-rolled the
comparison against `git show` from the live repository instead, which is the
same independent source, and say so rather than substituting a weaker check.

---

## 6 · The suite

Baseline and mutated runs, scratch copy at `3d2ec784`: **130 modules · 3794
tests · ~75s · 8 workers**, five red in both, identical by name. Three are the
session's standing reds the rounds name (`test_contract_key_parity` ×2,
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`). The other two —
`test_one_header_rule.…test_git_tracks_answers_both_ways` and
`test_blank_cell_is_one_rule.…test_it_is_not_declared_and_nothing_writes_it` —
are artefacts of running from a non-git copy and appear in the baseline
identically. Named rather than counted, and no mutation verdict in § 5 rests on
them.

The rounds' own counts (3791 and 3789) differ from mine because they ran
against their own commits; I did not try to reconcile the difference and it is
not load-bearing for anything here.

---

## 7 · What I did not check

- **The live project's own board.** No write tool was run against it, so I did
  not observe the gate on real data — every measurement is on a fixture project
  or a scratch copy. The 116-of-143 and 16-id figures are the only live
  readings, both from read-only `perry-state`.
- **Whether refusing on an unreadable store is the right remedy for FAIL-1.** I
  showed the current behaviour is wrong and that the pre-A behaviour did not
  lose data. I did not design or test the fix, and the choice between refusing,
  refusing-with-a-lint-pointer, and something else is the author's.
- **State 2 of § 2's table beyond a single probe.** I confirmed `3-storage` and
  an empty `CURRENT` both stand the gate down, but I did not enumerate what
  writes `phase/CURRENT`, so I cannot say how reachable a malformed pointer is
  without a hand edit. It is charged at the bottom of the finding, not the top.
- **`perry-goals krs --phase <past>` as a route back to a closed phase's
  declarations.** Named in ROW-4 from reading the call chain; I did not run it.
- **`route`.** I established that `intake` reaches `cmd_add` and the gate has no
  track branch; I did not separately drive `perry-task route`.
- **Windows or non-POSIX paths, and concurrent `add` under the lock.**
- **Rounds 1 and 2's own verdict documents as artifacts.** I read them for the
  history of the sentence and took none of their conclusions as settled; I did
  not audit them.
- **`perry-lint --reviews --strict` on this document.** It is the pre-check and
  runs before dispatch, not inside the round.

---

## 8 · What a PASS needs

1. `_current_store_phase`'s two `None`s separated, so a store that cannot be
   read refuses instead of standing the gate down — and a message that names
   the parse failure rather than the between-phases window.
2. A test in `TestTheGateKeysOffThePhaseNotTheFile` whose fixture leaves
   `phase/CURRENT` naming a real phase and gives the store records for a
   *different* one, so M-H reddens. The class's current fixture cannot reach
   the property it is named for.
3. A test for the malformed-store state, which today has no coverage at all.
4. ROW-3 and ROW-4 filed, or the `bin/README.md` sentence removed with the
   other two — the deletion is a one-line change and the guard already knows
   the literal string to look for.

```
=== VERDICT ===
task: TASK-439
rung: V4
result: FAIL
grade: FAIL — `§ Verification` item 3 (mutation) and `§ What it must not do`
       item 4 (`add` must keep working, with an argued answer, where the
       register cannot answer): a malformed `linkage.jsonl` is neither the
       store-less project item 4 argues about nor the between-phases window A
       argues about, and the gate treats it as both
criteria: perry/evidence/2026-09/TASK-439-spec.md
checked: base was 583f024f, 128 behind, clean, strict ancestor of main —
         fast-forwarded own branch only to 3d2ec784, both commits re-asserted
         as ancestors; eight gate states driven through the real binary on
         fixture projects (--root tmpdir), the same eight replayed against
         d8dc6ae8^ from a git archive copy to establish the regression;
         the KR's own reader (lib.same_action_linkage) on the corrupt-store
         filing; four line-anchored mutations in a scratch copy with the full
         suite run baseline-and-mutated (3794 tests each, five red in both,
         identical by name); round 4's disclosed M4 fix re-run independently
         and confirmed RED on the named test; C's deletion verified on both
         surfaces it names and the category re-enumerated across the tree;
         bin/perry-lint:1519 and bin/lib/__init__.py:1377 read at source;
         perry-state --json read-only for the 116-of-143 and 16-id figures;
         all restores verified against git show 3d2ec784:<path>
not-checked: the live board under any write tool; the design of the FAIL-1
         fix; what writes phase/CURRENT, so state 2's reachability is unbounded;
         perry-goals krs --phase on a closed phase; perry-task route as a
         separate entry point; Windows paths; concurrent add under the lock;
         rounds 1 and 2's documents as artifacts
proof: FAIL-1 — bin/perry-task:3764 stands the gate down on
       `_current_store_phase(...)` falsy, and bin/perry-task:2807 reaches that
       via P.load_linkage_store, which returns None for a MALFORMED store as
       well as an absent one (viewer/parsers.py:3952-3953). Input: append
       "{this is not json}" — or a git conflict marker — to a linkage.jsonl
       that declares key results for the current phase. `add` with neither flag
       then exits 0 and files the row (pre-A: exit 1, refused), the warning
       built at bin/perry-task:3991-3999 and printed at :4000 tells the caller
       the store "declares no key
       result for the current phase … the window § score-phase step 7 opens"
       which is false of that store, `--unlinked` is still refused, and the
       row's add event carries kr: null, putting it in never_answered
       permanently by P003-O3-KR2's own rule.
       FAIL-2 — bin/perry-task:2809's phase prefix match, replaced by
       startswith(""), leaves 3794 of 3794 tests green (baseline and mutated
       runs red on the same five by name). The property
       TestTheGateKeysOffThePhaseNotTheFile is named for is unpinned, because
       its gap() fixture clears phase/CURRENT and returns at :2806 without ever
       reading the store.
=== END VERDICT ===
```
