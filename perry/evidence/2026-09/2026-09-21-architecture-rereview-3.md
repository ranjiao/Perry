# Architecture re-review 3: the entry-skills and TASK-471 candidate, after 5a08b22b

This is the third re-review of one integration candidate. The earlier verdicts
are in this directory:

- `2026-09-21-architecture-review-entry-skills.md`
- `2026-09-21-architecture-rereview-entry-skills.md`
- `2026-09-21-architecture-review-task-471.md`
- `2026-09-21-architecture-rereview-task-471.md`
- `2026-09-21-architecture-rereview-2.md`, which was BLOCKED

Re-review 2 had two blockers:

1. phase/CURRENT was still read outside viewer/parsers.py, by bin/perry-task
   (two sites) and bin/perry-state.
2. bin/ARCHITECTURE.md said perry-context-budget "runs no external program".

The fix since then is one commit. `git log --oneline 82893086..de595d1f -- . ':!perry' ':!.perry'`
lists only 5a08b22b, "USER-980, completed: perry-task and perry-state read
phase/CURRENT through parsers". It changes five files: bin/ARCHITECTURE.md,
bin/perry-state, bin/perry-task, tests/test_phase_lifecycle.py and
viewer/parsers.py.

The gate is `work/reference/dispatch.md § Architecture review`. The brief is
`work/reference/review.md § Integration architecture reviewer brief`. The
constraints are in `work/reference/review-constraints.md`.

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: Claude Code subagent (claude-opus-5), fresh context, worktree agent-adcc316ac42b1f62f. I did not write TASK-469/470/471/474/475, the USER-978/980 fixes or 5a08b22b, and I carry none of their conversation. I used no author compliance verdict. Timestamp: 2026-09-21T06:50:58Z
Base: 820da3b1849df4f7155baf976b1045c6590bd129
Head: de595d1f8a5f57bc0a1e0ee0da65b7aae9223c4e
Triggers:
- Listed boundary paths: TRUE. `git diff --name-status 820da3b1 de595d1f` changes viewer/parsers.py (read_phase_pointer and its docstring), SKILL.md, goals/SKILL.md, work/SKILL.md and decide/SKILL.md. schema/ and bin/lib/ are unchanged.
- New top-level directory: FALSE. `git ls-tree -d --name-only` lists the same 17 directories at base and head (scratch dirs.base and dirs.head; `diff` is empty).
- New bin executable: FALSE. `git diff --raw 820da3b1 de595d1f -- bin` has only M entries. bin/ARCHITECTURE.md and bin/README.md are 100644→100644. perry-context-budget, perry-goals, perry-lint, perry-state and perry-task are 100755→100755. perry-state and perry-task are new to the diff since re-review 2, through 5a08b22b.
- Contract-version change: FALSE. schema/ is unchanged, and so is root §5 (:212-240). The ARCHITECTURE.md hunks are at §2, §6 NN-1 Known exceptions, §7 OQ-2 and §8. VERSION and release/records.jsonl change Perry's product version, not a contract version. The perry-context-budget JSON change that the record describes is not a §5 contract. perry-state's `warnings` loses a false entry, and no field or version changes.
- Root architecture edit: TRUE. 2225d076 (USER-978) is unchanged since re-review 2, and 5a08b22b does not touch ARCHITECTURE.md.
- Module architecture edit: TRUE. bin/ARCHITECTURE.md changed in 6bb4dc6f, 2225d076, abb1160d and now 5a08b22b (§2 :73-79, §8 :207-210).
Context: Root ARCHITECTURE.md at head. §1 is at :43, §2 at :58, §3 at :139 (allowed directions :157-158, Forbidden :160-167), §5 at :212 (read on demand), §6 at :241 (NN-1 :243-252), §7 at :301 and §8 at :362. Header :3 confirms §1, §3 Forbidden, §5 versions, §6 and §7. Component mapping, from the confirmed §2:
  - `bin/` covers perry-goals, perry-lint, perry-state, perry-task, perry-context-budget, bin/ARCHITECTURE.md and bin/README.md.
  - `viewer/parsers.py` is its own component, "the one reader" (:83-91).
  - `release/` (:75-81) is not in the diff, but a reader of the file under review lives there (see NN-1).
  - `SKILL.md + goals/ work/ decide/` covers the router and lane edits.
  - `modes/, packs/, reference/, templates/` covers reference/*.md.
  - `tests/` covers the test modules.
  The only module document is bin/ARCHITECTURE.md v1. Its header :3 confirms §6 and §7, and :5 now reads "Last reviewed: 2026-09-21". §2 declares no module document for parsers, release/, the lanes, reference/ or tests/, and under USER-978 (3) (ARCHITECTURE.md:314-319) that is not missing context. One fact is unresolved: whether NN-1 reaches release/, which reads Perry's own state at a git ref (see below).
Rules:
- ARCHITECTURE.md:43-56 (§1 scope) — holds. 5a08b22b adds no writer and judges no meaning. The two changed tool sites are read-only.
- ARCHITECTURE.md:100-118 (§2 lanes) — holds. The router's cap is tests/test_router_budget.py BUDGETS["SKILL.md"] (:45). The router points to `reference/first-run.md § The procedure` (SKILL.md:140), whose steps 4-6 are "the next two sections" (first-run.md:44), and those include `§ The recommended order for a new project` (:62). The sentence at :113-115 holds through that chain.
- ARCHITECTURE.md:157-158 (§3 allowed directions) — holds. perry-state (:1940) and perry-task (:2912, :2930) import `P.read_phase_pointer`. parsers.py imports only the stdlib and `tables` (:14-45).
- ARCHITECTURE.md:161 (§3 Forbidden, user-confirmed: "A second reader of any state file. `bin/` never re-implements a parse.") — for phase/CURRENT in bin/: holds, and blocker (1) of re-review 2 is resolved. See the enumeration in the notes. Outside bin/, release/manage.py:274-281 is a second reader. See NN-1 (b).
- ARCHITECTURE.md:162-163 (§3 Forbidden: a lane computing a number) — holds. No lane text changed after 82893086.
- ARCHITECTURE.md:164-166 (§3 Forbidden: roots and the one resolver) — holds. perry-goals :4868 and :5331 call `lib.resolve_project_root`. 5a08b22b does not touch root resolution.
- ARCHITECTURE.md:167 (§3 Forbidden: an agent writing ARCHITECTURE.md) — holds. Root is unchanged after 2225d076, which the earlier reviews accepted as user-decided (USER-978) or descriptive.
- ARCHITECTURE.md:213-221 (§5 argument surface) and :223-240 (payload contracts) — not touched by 5a08b22b. The earlier findings (holds) stand.
- ARCHITECTURE.md:243-252 (§6 NN-1, user-confirmed: "exactly one implementation parses any given state file, and it lives in viewer/parsers.py"):
  (a) phase/CURRENT in bin/ and viewer/ — holds. Every read of the pointer's VALUE in bin/ (recursive, including bin/lib) and viewer/ (parsers.py and tables.py) now goes through `parsers.read_phase_pointer` (parsers.py:3030-3044). The callers are load_snapshot (:5238), perry-goals phase_pointer (:4731-4740, which also serves current_phase :1564 and phase_command :4879), perry-lint check_cross_file (:1311), perry-state build (:1940) and perry-task _register_state (:2912) and _current_store_phase (:2930). perry-goals' `pointer` path is used only to write (:4953, :4996, :5042). bin/perry-diagnose:2092 calls `is_file()` to detect an adoptable layout and reads no value. perry-state no longer takes the file existing to mean "points at a phase", and F1 shows the new test kills that regression.
  (b) phase/CURRENT outside bin/ and viewer/ — CONTRADICTS. This is pre-existing and outside the diff. release/manage.py:33 sets `PHASE_POINTER = "perry/phase/CURRENT"`, and its `check_base.pointer` (:274-281) reads the value at a git ref (`read(root, PHASE_POINTER, sha)`, :163-171 via `git show`). It decodes strictly (`.decode("utf-8")`, where parsers uses `errors="replace"`) and keeps its own "no phase" set, `("", "(none)", "none", "—")` (:278). That set is a literal copy of PHASE_POINTER_NONE (parsers.py:3027), which is the defect USER-980 removed from perry-goals and perry-lint. The reader runs on every CI build (.github/workflows/ci.yml:26) and dates from f89370e5 (2026-09-16), before the base. The candidate says the opposite. parsers.py:3033 says "**The one reader of the pointer's value**", and 5a08b22b says the test is "derived over every file in bin/ and viewer/". The test's detector cannot see release/manage.py, for two reasons: it scans only bin/ and viewer/parsers.py, and even inside its scope it misses this shape (probes M2, M4 and M8).
  (c) NN-1 Known exceptions (:250-252) — holds, unchanged. It lists only perry-context-budget.
- ARCHITECTURE.md:254-263 (NN-2) — not touched by 5a08b22b. The earlier finding (holds) stands.
- ARCHITECTURE.md:265-271 (NN-3: no reported write that was not performed) — holds. 5a08b22b changes only reads. perry-state stops reporting a false condition after `phase close` (F1).
- ARCHITECTURE.md:273-280 (NN-4) — holds. `linkage_phase_number(read_phase_pointer(...))` is a mechanical comparison.
- ARCHITECTURE.md:282-287 (NN-5) — holds. test_state_does_not_warn_after_a_close copies SAMPLE into `tempfile.mkdtemp` and passes `--root`, and PERRY_PROJECT is stripped from the env (tests/test_phase_lifecycle.py:581-600).
- ARCHITECTURE.md:289-299 (NN-6) — holds. Root is unchanged in 5a08b22b, and the bin/ARCHITECTURE.md edits are §2 and §8, which are descriptive.
- ARCHITECTURE.md:314-319 (§7 OQ-2) — holds, unchanged.
- SKILL.md:48-70 (the V5-signed hand-off contract, decided) — holds. The signed content is byte-identical to 820da3b1. I compared it independently in scratch (sig.py → sig.out): signature record 5/5 lines, sha256 prefix fbee743b839fab6a on both sides; invariant heading 9c438a5e…, invariant 29e4aba4…, table intro 3bd4965e…, ownership table 5/5 lines 2ef99903…, the three refusal cases d8c71ea2… (the whole only-writer paragraph 7245e781…); all IDENTICAL. At base the blockquote runs on for 7 more lines, the rationale that USER-975 accepted moving to reference/hand-off-contract.md. No commit after 82893086 touches SKILL.md.
- bin/ARCHITECTURE.md:64-70 (§2, "What perry-context-budget reads outside the project") — holds. perry-context-budget:117-122 runs `bash perry-detect-host` with timeout=10, and OSError or a timeout gives "unknown". "The only `bin/` tool that executes another one": no other bin/ tool runs a bin/ tool as a subprocess. perry-update-check:159 execs release/update.py, which is not a bin/ tool. See the notes on bin/perry's in-process forwarding.
- bin/ARCHITECTURE.md:74-79 (§2, corrected by 5a08b22b) — holds, and blocker (2) of re-review 2 is resolved. perry-codex-preflight is the only tool that runs `codex` (:77, :126) and the only one that touches a model. perry-context-budget "runs one program, bin/perry-detect-host through bash": :119 is its only subprocess call. It is the one tool with a recorded NN-1 exception, which is true (ARCHITECTURE.md:250-252).
- bin/ARCHITECTURE.md:207-210 (§8 entry added by 5a08b22b) — DESCRIPTIVE MISMATCH. It says perry-codex-preflight was said to be the only tool depending on git, "which five others also run". Six bin/ tools run git: perry-churn (:256, :723), perry-diagnose (:166), perry-restore-check (:83), perry-state-cost (:105), perry-task (:4350) and perry-update-check (:128). perry-codex-preflight itself runs no git (0 occurrences), so "others" is also wrong. The §2 body it describes (:74-76) is correct. Only the change-log sentence is wrong.
- bin/ARCHITECTURE.md:98-105 (§3 "A tool never parses a state file itself", and its list of direct reads) — the description holds. perry-lint:3129 (asks.jsonl), perry-tasks:269 (tasks.jsonl) and perry-task:5509-5511 (okr.jsonl) exist at head, and the list claims no completeness. The rule's pointer contradictions in bin/ are gone (NN-1 (a)).
- bin/ARCHITECTURE.md:109-110 (§3, the lock spans read, decision and write) and :161-183 (NN-B1 to NN-B3) — not touched by 5a08b22b. The earlier finding (holds) stands.
Decision: BLOCKED.
  (1) Decided-section contradiction of root §6 NN-1 (ARCHITECTURE.md:245-246) and §3 Forbidden (:161). release/manage.py:274-281 parses phase/CURRENT's value with its own copy of the "no phase" set and a strict decode. It is pre-existing and outside the diff, but the candidate states the opposite at viewer/parsers.py:3033 ("The one reader of the pointer's value"). This is the same pattern that blocked re-review 2, one directory further out. The candidate's own detector cannot see it (M2, M4, M8, and release/ is not scanned).
  (2) Descriptive mismatch needing correction: bin/ARCHITECTURE.md:209-210 "which five others also run". Six tools run git, and perry-codex-preflight is not among them.
  Resolved since re-review 2:
  - Blocker (1) in bin/ and viewer/: perry-task :2912 and :2930 and perry-state :1940 now call `P.read_phase_pointer`, and the false warning after `phase close` is gone (F1, F2).
  - Blocker (2): bin/ARCHITECTURE.md:77-79.
  The V5 contract holds, byte for byte.
User decision required: yes, for NN-1's reach. release/ is its own §2 component (:75-81). It reads Perry's own pointer at two git refs, which `read_phase_pointer(state_root)` cannot serve, and root §3 (:157-158) draws no direction from release/ to viewer/parsers. The fix is one of these, and both are decisions on a confirmed section (NN-6, :292-295):
  (a) parsers gains a value-level function (the "no phase" decision over a pointer's bytes, which read_phase_pointer then uses), release/manage.py imports it, and §3 records the release → parsers direction. Recommended, because it is the USER-980 shape.
  (b) NN-1 records a Known exception for release/manage.py's git-ref read, and parsers.py:3033 narrows its claim to "the one reader in bin/ and viewer/".
  Either way, the parsers docstring (:3036) and the test docstring (tests/test_phase_lifecycle.py:554-555) should stop saying "every file in bin/ and viewer/". The detector scans only bin/'s top level and viewer/parsers.py (:559-560); bin/lib/ and viewer/tables.py are not scanned (M5, M6). The PMO may also judge (2) alone too small to hold the candidate. It is a one-word correction to a change-log line.
Not checked:
- I ran no full suite. The PMO ran it green (158/4460) on this exact tree. I ran only the TestThePointerHasOneReader class on a scratch copy (3 tests OK), and tests.test_diagnose after writing this file, as the brief asks.
- release/manage.py's disagreement with parsers is shown from the code (:277 strict decode against parsers.py:3043 errors="replace"; the :279 PHASE fullmatch). I did not execute it: `check_base` needs a two-commit repository with release records, and I judged the code citation sufficient.
- The phase-document header reader in perry-lint (:927-928) and the stale §2 counts remain pre-existing notes and are not charged. See the notes.
- TASK-470's relocated reference pages were not re-read for content loss. They are unchanged since re-review 2.
- Every probe ran on a `git archive de595d1f` copy under the perry-scratch derivation, never on the reviewed tree.
=== END COMPLIANCE ===
```

## Supporting notes

### Candidate binding

The worktree was cut from origin/main at 0b5bf99e, with no branch commits and a
clean tree. I fast-forwarded it to de595d1f with `git merge --ff-only`, which
the PMO authorised. HEAD is de595d1f8a5f57bc0a1e0ee0da65b7aae9223c4e. I read
5a08b22b in full, and USER-978 and USER-980 from `perry/asks.jsonl` (lines 79
and 81).

### Every read of phase/CURRENT's value at head

Method: `grep -rnI CURRENT bin viewer` (recursive, which includes bin/lib and
viewer/tables.py), `git grep CURRENT` over the tree outside perry/, .perry/,
tests/ and *.md, `grep read_phase_pointer|POINTER`, and a search for unfiltered
`glob("*")`, `rglob("*")`, `iterdir()`, `listdir` and `os.walk` that could reach
`phase/` without naming the file. The two `rglob("*")` sites (perry-task:5527
evidence scan, perry-lint:2563 glossary dirs) filter by suffix or live outside
the state tree.

| Site | What it reads | Through | Status |
|---|---|---|---|
| viewer/parsers.py:3030 `read_phase_pointer` | value | itself | the one reader in bin/ and viewer/ |
| viewer/parsers.py:5238 `load_snapshot` | value | `read_phase_pointer` | holds |
| bin/perry-goals:4731 `phase_pointer` (current_phase :1564, phase_command :4879) | value; the path only to write (:4953, :4996, :5042) | `P.read_phase_pointer` | holds |
| bin/perry-lint:1311 | value | `P.read_phase_pointer` | holds |
| bin/perry-state:1940 | value | `P.read_phase_pointer` | **fixed** (5a08b22b) |
| bin/perry-task:2912 `_register_state` | value | `P.read_phase_pointer` | **fixed** (5a08b22b) |
| bin/perry-task:2930 `_current_store_phase` | value | `P.read_phase_pointer` | **fixed** (5a08b22b) |
| bin/perry-diagnose:2092 | existence (adoption layout) | `is_file()` | no value read |
| **release/manage.py:274-281 `check_base.pointer`** | **value at a git ref** | **own strict decode + own "no phase" set** | **second reader** (f89370e5, pre-base) |

### Every reader of phase-document header fields at head

This is unchanged since re-review 2, because 5a08b22b touches no phase-document
reader.

| Site | What it reads | Through |
|---|---|---|
| viewer/parsers.py:3047 `parse_phase` | Status, Started | itself, the one reader |
| bin/perry-goals :3557, :4394, :4783, :4989, :5022 | Status (and Started) | `P.parse_phase` |
| bin/perry-goals :4758 `phase_header` and :4799 `splice_header` | header line position only | own regex; the value is discarded and the result re-read by `P.parse_phase` (:4949, :5037) |
| bin/perry-lint:927-928 schema `header_fields` | Status/Started of every schema file | own regex, pre-existing (ad5f65dc) |

**perry-lint:927 is still a pre-existing note, not a contradiction charged to
this candidate.** No sentence the candidate added claims one reader of phase
headers. bin/ARCHITECTURE.md:102-105 explicitly leaves schema and store
conformance reads as "not yet decided". perry-lint is not in 5a08b22b, and
89fa3477's hunk is at :1311. The user may still want to rule on it together with
the three store reads that §3 lists.

**The §2 line counts are still pre-existing notes.**

- Root ARCHITECTURE.md:84 says parsers.py has "5,228 lines". It had 5,642 at
  base and has 5,663 at head, so the count was already stale at base, and the
  candidate did not write it.
- ":130/:150 136 modules" means 159 test_*.py files at base and 162 at head.
- bin/ARCHITECTURE.md:57-59 gives 2,169 / 2,237 / 1,806 lines. The files have
  2,880 / 2,347 / 1,853 at head, and that table is not in the candidate's diff.

The candidate did change bin/ARCHITECTURE.md:5 to "Last reviewed: 2026-09-21".
That is a date, not a claim that the counts were re-measured. So I record it
here and do not treat it as a contradiction.

### Could the new detector miss a read? Yes, and it misses one real one

`tests/test_phase_lifecycle.py § test_nothing_else_reads_the_pointer_value`
(:553-579) works like this:

- It keeps lines containing the literal `"CURRENT"`, with double quotes.
- It flags one when `read_text(`, `read_bytes(` or `open(` appears in that line
  or the five lines after it.
- The files it scans are the top-level files of bin/ (`iterdir()` with
  `is_file()`) plus viewer/parsers.py only.

I planted each shape below as a new file in a scratch copy, ran the one test,
and removed the file. The results are in `detector_probe.py` →
`detector_probe.out`. The baseline was OK, and so was the run after the last
removal.

```
M0 control: "CURRENT" + read_text on the same line, in bin/     CAUGHT
M1 single-quoted 'CURRENT'                                       MISSED
M2 one string "phase/CURRENT"  (release/manage.py:33's shape)    MISSED
M3 open( on the line before the name                             MISSED
M4 path bound, read 7 lines later (manage.py reads 244 later)    MISSED
M5 a file in bin/lib/                                            MISSED
M6 a file in viewer/ other than parsers.py                       MISSED
M7 read through a subprocess (cat)                               MISSED
M8 read at a VCS ref via `show` (manage.py's mechanism)          MISSED
```

The one real reader it misses is release/manage.py:274-281. The detector has
three separate reasons not to see it: the directory is not scanned (like M5 and
M6), the name is spelled `"perry/phase/CURRENT"` (M2), and the read is 244 lines
from the name (M4). None of M1 and M3-M7 exists in the tree today; I checked by
the enumeration above, not by the detector. The detector is a useful tripwire
for the exact shape the two fixed perry-task sites had. It is not a derivation
over "every file in bin/ and viewer/", which is what its docstring (:554-555)
and parsers.py:3036 say.

### The fixes, mutated back (scratch copy)

Results are in `fix_mutants.py` → `fix_mutants.out`. Each restore was asserted
byte-equal to the pre-mutation copy, and the copy is a `git archive` of
de595d1f.

```
F1 perry-state reverts to `cur_pointer.exists()`            KILLED by test_state_does_not_warn_after_a_close
F2 perry-task _register_state reverts to its own read_text  KILLED by test_nothing_else_reads_the_pointer_value
```

The detector would not have caught F1, because `exists()` is not a read. The
behavioural test catches it, so the pair covers both old defects.

### Category claims the candidate added, grepped

- **"The one reader of the pointer's value"** (parsers.py:3033) is false at head
  because of release/manage.py:274-281. It is true within bin/ and viewer/.
- **"Five sites in four tools used to read it themselves, with three copies of
  the 'no phase' set among them"** (parsers.py:3033-3035) is loose. The five
  sites in bin/ are goals, lint, task ×2 and state. Of the three set copies,
  one was load_snapshot's, which is not among those five sites. A fourth copy
  still exists in release/manage.py:278. This is a code comment, not an
  architecture sentence, so it is corrected with (1).
- **"derives the claim over every file in bin/ and viewer/"** (parsers.py:3036;
  test :554-555; 5a08b22b message) is false in scope: bin/lib/ and
  viewer/tables.py are not scanned (M5, M6).
- **"It is the only `bin/` tool that executes another one; nothing is imported"**
  (bin/ARCHITECTURE.md:69-70) holds for subprocess execution. bin/perry forwards
  to another tool in-process (`load(path)` then `module.main`, bin/perry:152-158,
  2ba2c565, 2026-09-09). That is execution by import, and it also contradicts
  bin/ARCHITECTURE.md:106's "A tool never imports another tool — except
  perry-tasks and perry-task". Both predate the base and neither is in the
  diff. I note them and do not charge them.
- **"the only tool here that depends on `codex` and the only thing here that
  touches a model"** (:75-76) holds. perry-context-budget reads
  `~/.codex/sessions/` files but does not run codex. perry-dispatch-limit only
  names the executor.
- **"which five others also run"** (:209-210) is false: six tools run git, and
  preflight runs none. This is blocker (2).

### Scratch

The scratch directory is `$TMPDIR/perry-scratch/agent-adcc316ac42b1f62f`, the
`perry-scratch-derivation` result for this worktree. The host refused the inline
`$(git …)` form, so I read `git rev-parse --show-toplevel` and `$TMPDIR`
separately and used the literal path. It holds:

- `copy/` (the `git archive de595d1f`)
- `detector_probe.py` / `.out`
- `fix_mutants.py` / `.out`
- `sig.py` / `.out`
- `skill.base` / `skill.head`
- `dirs.base` / `dirs.head`

### Commit versus the constraints

review-constraints.md says a review round does not commit. This round commits
only this evidence file, because the PMO's brief asks for it.
