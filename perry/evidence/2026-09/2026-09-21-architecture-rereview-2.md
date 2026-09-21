# Architecture re-review 2: entry skills and TASK-471, one candidate, after USER-978 and USER-980

This is the second re-review. It covers both earlier streams, now bound to one
candidate:

- `2026-09-21-architecture-review-entry-skills.md` and
  `2026-09-21-architecture-rereview-entry-skills.md` (TASK-469, TASK-470 and
  TASK-474, plus TASK-475 where it touches the same rules).
- `2026-09-21-architecture-review-task-471.md` and
  `2026-09-21-architecture-rereview-task-471.md`.

The gate is `work/reference/dispatch.md § Architecture review`. The brief is
`work/reference/review.md § Integration architecture reviewer brief`, and the
constraints are in `work/reference/review-constraints.md`.

The scope is everything the four earlier reviews covered, plus the fixes since
16124fb0. `git log --oneline 16124fb0..82893086 -- . ':!perry' ':!.perry'` lists
these commits:

| Commit | Change |
|---|---|
| abb1160d | bin/ARCHITECTURE.md correction |
| 89fa3477 | USER-978/980: a pointer reader, and the writer checks the parser |
| ccf02a04 | TASK-475 round 3: phase-number comparison |
| b0223587 | test pin for close's write site |
| 567d5872 | merge |

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: Claude Code subagent (claude-opus-5), fresh context, worktree agent-a26b1b08804766e42. I did not write TASK-469/470/471/474/475 or the USER-978/980 fixes and carry none of their conversation. I used no author compliance verdict. Timestamp: 2026-09-21T06:36:15Z
Base: 820da3b1849df4f7155baf976b1045c6590bd129
Head: 82893086b7d48b4fd9df0765acddbc60537f5fa3
Triggers:
- Listed boundary paths: TRUE. `git diff --name-status 820da3b1 82893086` changes these listed paths: viewer/parsers.py (89fa3477, the new `read_phase_pointer`), SKILL.md, goals/SKILL.md, work/SKILL.md and decide/SKILL.md (TASK-469/470/474). bin/lib/ and schema/ are unchanged.
- New top-level directory: FALSE. `git ls-tree -d --name-only` lists the same 17 directories at base and head (scratch dirs.base / dirs.head, `diff` empty).
- New bin executable: FALSE. `git diff --raw 820da3b1 82893086 -- bin` has only M entries: bin/ARCHITECTURE.md and bin/README.md at 100644→100644, and perry-context-budget, perry-goals and perry-lint at 100755→100755. Nothing is added or renamed, and no mode changed.
- Contract-version change: FALSE. schema/ is unchanged. Root §5 (:212-240) is unchanged, because the ARCHITECTURE.md hunks are at :98, :112, :246, :309 and :354 only (§2, §6 NN-1, §7 OQ-2, §8). parsers.py gains a function but no version declaration. reference/hand-off-contract.md has no version.
- Root architecture edit: TRUE. 2225d076 (USER-978) is the only ARCHITECTURE.md commit in the range. No commit touches the file after 16124fb0.
- Module architecture edit: TRUE. bin/ARCHITECTURE.md changed in 6bb4dc6f (TASK-471), 2225d076 (USER-978) and abb1160d (correction, new since the first re-reviews).
Context: Root ARCHITECTURE.md at head, which is identical to 16124fb0: §1 :43, §2 :58, §3 :139 (Forbidden :161-167), §5 :212 (on demand), §6 :241, §7 :301, §8 :362. Header :3 confirms §1, §3 Forbidden, §5 versions, §6 and §7. Component mapping, from the confirmed §2: `bin/` covers perry-goals, perry-lint, perry-context-budget, bin/ARCHITECTURE.md and bin/README.md. `viewer/parsers.py` is its own §2 component (:83-91), "the one reader". `SKILL.md + goals/ work/ decide/` covers the router and lane edits. `modes/, packs/, reference/, templates/` covers reference/*.md. `tests/` covers the test modules. The only module document is bin/ARCHITECTURE.md v1 at head (header :3 confirms §6 and §7). §2 declares none for parsers, the lanes, reference/ or tests/, and under USER-978 (3) (ARCHITECTURE.md:314-319) that is not missing context. Unresolved facts: none.
Rules:
- ARCHITECTURE.md:43-56 (§1 scope) — holds. The fixes add no writer outside the project and no meaning judged in code. The phase verbs still refuse a state root outside the project root (bin/perry-goals:4868-4871).
- ARCHITECTURE.md:100-118 (§2 lanes) and SKILL.md router — holds. The lane text is unchanged since 16124fb0, and both §2 corrections from the first review still hold.
- ARCHITECTURE.md:157-158 (§3 allowed directions) — holds. perry-goals (:4739-4740) and perry-lint (:1311) import `P.read_phase_pointer`. parsers.py imports only stdlib and `tables` (:14-45), nothing from bin/.
- ARCHITECTURE.md:161 (§3 Forbidden, user-confirmed: "A second reader of any state file") — phase documents: holds. phase/CURRENT: CONTRADICTS, pre-existing, not in the diff. See NN-1 below.
- ARCHITECTURE.md:162-163 (§3 Forbidden: a lane computing a number) — holds. No lane or router text changed since 16124fb0.
- ARCHITECTURE.md:164-166 (§3 Forbidden: roots come from --root, then $PERRY_PROJECT, then the walk; one resolver) — holds. phase_command :4868 and main :5331 call `lib.resolve_project_root`, and neither fix touched them.
- ARCHITECTURE.md:167 (§3 Forbidden: an agent writing ARCHITECTURE.md) — holds. The root document is unchanged after 16124fb0, and the first re-reviews accepted 2225d076's edits as user-decided (USER-978 (2), (3)) or descriptive (§2, §8).
- ARCHITECTURE.md:213-221 (§5 argument surface) — holds. PHASE_FLAGS and PHASE_REQUIRED are unchanged. `refuse_unless_parsed` refuses through the existing `refusal` (exit 1, JSON with --json, "Nothing was written").
- ARCHITECTURE.md:223-240 (§5 payload contracts and versions) — not touched.
- ARCHITECTURE.md:243-249 (§6 NN-1, user-confirmed: exactly one implementation parses any state file, in viewer/parsers.py):
  (a) Phase document headers in the phase verbs — holds. P5 and P7 now refuse, rc 1, with nothing written; see Probes. Both writes of a phase document are checked through `P.parse_phase` before any write: new at bin/perry-goals:4949, before :4952-4953, and close at :5037, before :5040-5042. The check covers every Status and Started value the payload reports (new :4954-4957 "started" and "status"; close "status"). `phase_header` survives only as a splice locator. `splice_header` discards the value it returns (`n, _ = hit`, :4811), and new (:4926) and close (:5025) use it only to refuse a spelling the writer cannot rewrite. Activate's gate is `P.parse_phase` (:4989). It writes and reports only the pointer, and `read_phase_pointer` reads that back as written (P10c, P10d).
  (b) phase/CURRENT — CONTRADICTS. `parsers.read_phase_pointer` (viewer/parsers.py:3030-3042) now serves perry-goals `phase_pointer` (:4731-4740, hence `current_phase` :1556-1570, TASK-475's `objective add` :4392 and `link`), perry-lint `check_cross_file` (:1311) and `load_snapshot` (parsers.py:5236). Three other readers remain outside parsers:
      - bin/perry-task:2911-2912 (`_register_state`) and :2930-2931 (`_current_store_phase`) each read the file themselves: `read_text(encoding="utf-8").strip()`, no-phase judged by `linkage_phase_number`. P12: a pointer with one stray 0xff byte is read by parsers (errors=replace) and raises UnicodeDecodeError here. These date from f79b75a6 (2026-09-13) and 054aac6c (2026-09-08).
      - bin/perry-state:1938-1940 treats the file's existence as a pointer and warns "phase/CURRENT points at a phase file that does not exist." whenever the file exists and no phase parsed. That disagrees with the one reader on `(none)`, which is exactly what the in-scope `phase close` writes (:5042). P11: after a successful close, `read_phase_pointer` gives '', perry-lint is silent, and `perry-state --json` carries that warning. This read dates from 5c6dc8ff (2026-08-14).
    Neither tool is in the diff. But the candidate claims the opposite. The parsers.py:3033 docstring says "**The one reader of the pointer**", 89fa3477's subject says "phase/CURRENT has one reader", and tests/test_phase_lifecycle.py `test_no_tool_keeps_its_own_no_phase_set` checks only perry-goals and perry-lint. USER-980 named "perry-goals (and perry-lint where it reads the pointer the same way)" on an enumeration that missed these sites. bin/perry-diagnose:2092 tests only that the file exists, to detect an adoptable layout, and reads no value. I do not count it as a parse.
  (c) NN-1 Known exception (:250-252) — holds, unchanged. The grep check (:249) still lists only argv or cell parsers (bin/perry-goals:4831 `parse_phase(argv)` is a false positive) and still cannot see a reader not named `parse_*`.
- ARCHITECTURE.md:254-263 (NN-2) — holds. The phase verbs write the document and pointer, then append the event (:5047-5051). No board.
- ARCHITECTURE.md:265-271 (NN-3: no reported write that was not performed) — holds. The first re-review's NN-3 finding is resolved: P5, P7, P8 (prose "Release Status: blocked" above the bold header) and P9 (`> 启动:` above the bold Started) each refuse, rc 1, with nothing written, and the refusal carries the parser's reading. The control run P10 (new → close → re-activate) reports only what the parser then reads.
- ARCHITECTURE.md:273-280 (NN-4) — holds. `refuse_unless_parsed` compares strings mechanically, and TASK-475 compares phase numbers through `P.linkage_phase_number`.
- ARCHITECTURE.md:282-287 (NN-5) — holds. The new tests use `Fixture.project` (tempfile.mkdtemp copy) and `tempfile.mkdtemp` (TestThePointerHasOneReader).
- ARCHITECTURE.md:289-299 (NN-6) — holds. The root is unchanged after 16124fb0.
- ARCHITECTURE.md:314-319 (§7 OQ-2) — holds, unchanged.
- SKILL.md:48-70 (the V5-signed hand-off contract, decided) — holds. The signed content is byte-identical to 820da3b1. Compared in scratch (sig.py): signature record 5/5 lines, sha256 prefix fbee743b839fab6a on both sides; invariant heading 9c438a5e…, invariant 29e4aba4…, table intro 3bd4965e…, ownership table 5/5 lines 2ef99903…, the three refusal cases 7245e781…; all IDENTICAL. Two things differ from base: the rationale paragraph ("Recorded at this precision…") moved to reference/hand-off-contract.md, which the user accepted (USER-975), and the "Two changes" summary became a pointer (:68). No commit after 16124fb0 touches SKILL.md.
- bin/ARCHITECTURE.md:77-80 (§2, edited by abb1160d) — the correction holds: "the one tool with a recorded NN-1 exception" is true, because NN-1 :250-252 lists only perry-context-budget. The same sentence's "runs no external program" (:78) is a DESCRIPTIVE MISMATCH. bin/perry-context-budget:119 runs `subprocess.run(["bash", str(detect)], …)`, and the same document's §2 (:69-71) says so. Earlier reviews called this "loose". Against the brief's question, "does not claim what the code does not do", it is a false claim. It needs a small wording fix, for example "runs no program outside Perry" or "runs only bin/perry-detect-host".
- bin/ARCHITECTURE.md:98-104 (§3 "A tool never parses a state file itself", and the added list) — the description holds. All three direct reads it lists exist at head: bin/perry-lint:3125-3134 decodes asks.jsonl line by line; bin/perry-tasks:266-269 decodes tasks.jsonl; bin/perry-task:5511-5517 decodes okr.jsonl. The list does not claim to be complete ("Not the only direct read"). The rule itself is contradicted by the pointer reads in NN-1 (b), which the list does not name.
- bin/ARCHITECTURE.md:109-110 (§3 the lock spans read, decision and write) — holds. Both `refuse_unless_parsed` calls run inside `project_lock(state_root)` (:4876).
- bin/ARCHITECTURE.md:161-183 (NN-B1 to NN-B3) — holds. phase_main and PHASE_FLAGS are unchanged, and the resolver is as in ARCHITECTURE.md:164-166.
- TASK-475 (ccf02a04) against the same rules — holds. objective add's reused-id check (:4420-4423) and kr add's objective lookup (:4190) and KR cap (:4250-4253) compare `P.linkage_phase_number` on both sides, which is the grouping `parsers.linkage_records_for_phase` uses. The pointer comes through `current_phase` → `read_phase_pointer`, and Status through `P.parse_phase` (:4394).
Decision: BLOCKED.
  (1) Decided-section contradiction of root §6 NN-1 (ARCHITECTURE.md:243-249) and §3 Forbidden (:161), with bin/ARCHITECTURE.md:98. phase/CURRENT is still read outside viewer/parsers.py by bin/perry-task:2911-2912 and :2930-2931, and by bin/perry-state:1938-1940. perry-state disagrees with the one reader on `(none)`, the value every in-scope `phase close` writes (P11 is a false warning after each close). The contradiction is pre-existing and outside the diff, but the candidate states the opposite in code (parsers.py:3033), in 89fa3477 and in a test that checks only two tools.
  (2) Descriptive mismatch needing correction and re-review: bin/ARCHITECTURE.md:78 "runs no external program".
  Resolved since the first re-reviews:
  - P5 and P7, now refused, which also resolves NN-3.
  - phase_pointer's own sentinel set, replaced by the parsers reader.
  - bin/ARCHITECTURE.md's "the one tool that reads a state file itself".
  The V5 contract holds, byte for byte.
User decision required: none new. NN-1 is the rule, it has no exception for these sites, and USER-980 already chose "a shared reader, imported" for this file. The fix changes no rule: perry-task's two sites call `P.read_phase_pointer`, and perry-state warns only when `P.read_phase_pointer(root)` is non-empty and no phase parsed. One condition applies. If the PMO reads USER-980's "perry-goals (and perry-lint …)" as the complete list, the user must choose between extending it to perry-task and perry-state (recommended) and recording NN-1 exceptions for them. Whether the fix joins this candidate or is carried as a named follow-up that this gate then records is the PMO's call. Under the brief, this block stays BLOCKED until then.
Not checked:
- I ran no full suite. The PMO ran it green (158/4459) on the round-3 tree that 82893086 contains, and no claim here depends on a run. I ran `tests.test_diagnose` only after writing this file, as the brief asks.
- There was no mutation round.
- The pre-existing phase-document header reader in perry-lint (:927-928; P13 shows it rejecting `> **Status**: active (reopened …)` that the parser reads as active) is outside the diff and not charged. See the notes.
- TASK-470's relocated reference pages were not re-read for content loss.
- perry-context-budget was not executed.
- All probes ran on copies of tests/fixtures/sample-project under the perry-scratch derivation, never on the reviewed tree.
=== END COMPLIANCE ===
```

## Supporting notes

### Candidate binding

The worktree was cut from origin/main at 0b5bf99e, with no branch commits and a
clean tree. I fast-forwarded it to 82893086 with `git merge --ff-only`, which
the PMO authorised. The fix commits were read in full: abb1160d, 89fa3477,
ccf02a04 and b0223587. USER-978 and USER-980 were read from `perry/asks.jsonl`
(lines 79 and 81).

### Every reader of phase/CURRENT and of phase-document headers in bin/ and viewer/ at head

| Site | Reads | Through | Status |
|---|---|---|---|
| viewer/parsers.py:3030 `read_phase_pointer` | phase/CURRENT | itself (the one reader) | new, USER-980 |
| viewer/parsers.py:5236 `load_snapshot` | phase/CURRENT | `read_phase_pointer` | fixed |
| bin/perry-goals:4731 `phase_pointer` (+ `current_phase` :1556) | phase/CURRENT | `P.read_phase_pointer` | fixed |
| bin/perry-lint:1311 `check_cross_file` | phase/CURRENT | `P.read_phase_pointer` | fixed |
| bin/perry-task:2911 `_register_state` | phase/CURRENT | own `read_text().strip()` | **second reader** (f79b75a6) |
| bin/perry-task:2930 `_current_store_phase` | phase/CURRENT | own `read_text().strip()` | **second reader** (054aac6c) |
| bin/perry-state:1938 | phase/CURRENT existence as a pointer | own `exists()` | **disagrees on `(none)`** (5c6dc8ff) |
| bin/perry-diagnose:2092 | phase/CURRENT existence (adoption layout) | `is_file()` | no value read |
| viewer/parsers.py:3045 `parse_phase` | phase doc Status/Started | itself | the one reader |
| bin/perry-goals:3557, :4394, :4989, :5022, :4783 | phase doc Status (and Started) | `P.parse_phase` | holds |
| bin/perry-goals:4758 `phase_header` / :4799 `splice_header` | header line position | own regex; value discarded; result re-read by `P.parse_phase` | locator only |
| bin/perry-lint:927-928 schema `header_fields` | phase doc Status/Started (every schema file) | own regex `([^\n]+)` | pre-existing second reader (ad5f65dc, 2026-08-16), not charged |
| bin/perry-decide:426 | `Status` line | own regex | a decision document, not a phase document |

### Probes (scratch `probe.py` → `probe.out`, `probe13.py` → `probe13.out`)

```
P5  close: bold Status only in a comment, real '> Status: active'
    rc=1 "would read as Status 'active' … not 'scored'" — parser 'active', pointer unchanged
P7  new: bold headers only in a comment, real '> Started: {{YYYY-MM-DD}}' '> Status: scored'
    rc=1 "would read as Status 'scored', Started '{{YYYY-MM-DD}}' … not 'active' / '2026-09-21'" — no doc, pointer ''
P8  close: prose 'Release Status: blocked' above the bold header
    rc=1 "would read as Status 'blocked'" — nothing written
P9  new: '> 启动: 2019-01-01' above the bold Started
    rc=1 "Started '2019-01-01' … not '2026-09-21'" — nothing written
P10 control from the shipped template: new rc=0 (parser active / today, pointer 003-probe);
    close rc=0 (parser scored, CURRENT b'(none)\n', pointer ''); activate 003 rc=1 "is scored";
    activate 002 --dry-run rc=0
P11 after a successful close: read_phase_pointer '' ; perry-lint silent on CURRENT;
    perry-state --json: "phase/CURRENT points at a phase file that does not exist."
P12 CURRENT = b'002-release-pipeline\xff\n': parsers → '002-release-pipeline�';
    perry-task's inline read → UnicodeDecodeError
P13 '> **Status**: active (reopened 2026-09-02)': parser 'active'; perry-lint rc=1 bad-enum
    "`Status: active (reopened 2026-09-02)` is not one of ['active', 'scored']" (same for '（重开）')
```

The scratch directory is `$TMPDIR/perry-scratch/agent-a26b1b08804766e42`, the
`perry-scratch-derivation` result for this worktree. The host refused the inline
`$(git …)` form, so I read the worktree basename separately and used it
literally. It holds `probe.py`, `probe.out`, `probe13.py`, `probe13.out`,
`sig.py`, `skill.base`, `skill.head`, `dirs.base`, `dirs.head` and the
fixtures under `fx/`.

### Pre-existing drift, not charged to this candidate

- **P13, perry-lint reading phase headers.** perry-lint's schema-driven
  header-field check reads a phase document's Status and Started with its own
  regex. P13 shows it disagreeing with `parse_phase`. This is the same open
  question as the three store reads bin/ARCHITECTURE.md §3 lists: is a schema
  conformance read an NN-1 parse? The user may want to rule on all four at once.
- **ARCHITECTURE.md §2 line counts.** §2 :84 gives parsers.py as "5,228 lines"
  (it has 5,661 at head). The §3 diagram (:150) gives "tests/ — 136 modules".
- **bin/ARCHITECTURE.md:75-76.** It says perry-codex-preflight is "the only
  dependency in this directory (`codex`, `git`, `timeout`)", but perry-churn,
  perry-diagnose, perry-restore-check, perry-state-cost and perry-task also run
  `git`. The sentence predates the base and the diff does not touch it.
- **Commit versus the constraints.** review-constraints.md says a review round
  does not commit. This round commits only this evidence file because the PMO's
  brief asks for it.
