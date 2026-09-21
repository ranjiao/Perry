# Architecture re-review — entry skills (TASK-469, TASK-470, TASK-474) after USER-978

Re-review of `perry/evidence/2026-09/2026-09-21-architecture-review-entry-skills.md`
(BLOCKED). Gate: `work/reference/dispatch.md § Architecture review`. Brief:
`work/reference/review.md § Integration architecture reviewer brief`.
Constraints: `work/reference/review-constraints.md`.

Scope: the product (non-`perry/`, non-`.perry/`) changes of TASK-469
(078d6da2, 86121e40, bb3d97d6, c44d5a64, 256ae459), TASK-470 (293fba87,
9c1a2b7c), TASK-474 (ebfb2b8d, 92a3448e, e250a0fc), the USER-978 fix
(2225d076, 8a9d5ec1, e381c870 — `git log --oneline 90b88d0b..16124fb0 -- .
':!perry' ':!.perry'`), and TASK-475 (72e819c2, 132aa1b5, c6d706ea, integrated
at 3ba47d05 / 7d7e9605) where it touches the same rules in `bin/perry-goals`.

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: Claude Code subagent (claude-opus-5), fresh context, worktree agent-a81aa376fc817a51f; not the author of TASK-469/470/474/475 or of the USER-978 fix, carrying none of their conversation; no author compliance verdict used; timestamp: 2026-09-21T14:14:45+0800
Base: 820da3b1849df4f7155baf976b1045c6590bd129
Head: 16124fb062c3ca1863fdaf5f834c2cb423158732
Triggers:
- Listed boundary paths: TRUE. SKILL.md, goals/SKILL.md, work/SKILL.md, decide/SKILL.md changed (TASK-469/470/474). viewer/parsers.py, bin/lib/, schema/ unchanged base..head (`git diff --stat 820da3b1 16124fb0 -- viewer schema bin/lib` empty).
- New top-level directory: FALSE. `git ls-tree -d --name-only` identical at base and head (17 directories).
- New bin executable: FALSE. `git diff --raw 820da3b1 16124fb0 -- bin`: M only (bin/ARCHITECTURE.md, bin/README.md 100644; bin/perry-context-budget, bin/perry-goals 100755→100755).
- Contract-version change: FALSE. schema/ unchanged; the ARCHITECTURE.md hunks (2225d076) touch §2, §6 NN-1, §7 OQ-2, §8 only — §5 unchanged; reference/hand-off-contract.md carries no version declaration.
- Root architecture edit: TRUE. 2225d076 (USER-978) — the only commit touching ARCHITECTURE.md in the range.
- Module architecture edit: TRUE. bin/ARCHITECTURE.md changed by 2225d076 (in scope) and by 5752ff71 (TASK-468), 6bb4dc6f (TASK-471) (out of scope; TASK-471's has its own review, 2026-09-21-architecture-review-task-471.md).
Context: root ARCHITECTURE.md head §1 (:43), §2 (:58), §3 (:139, Forbidden :161-167), §5 (:212, on demand), §6 (:241), §7 (:301), §8 (:362); header :3 names §1, §3 Forbidden, §5 versions, §6, §7 as user-confirmed. Component mapping (confirmed §2): `SKILL.md + goals/ work/ decide/` for TASK-469/470 and the lane edits of TASK-474; `modes/, packs/, reference/, templates/` for reference/*.md; `bin/` for bin/perry-goals (TASK-474, TASK-475, fix) and bin/ARCHITECTURE.md; `tests/` for tests/test_phase_lifecycle.py, test_startup_routing.py. Module documents: bin/ARCHITECTURE.md v1 (head; §6 and §7 byte-identical to base). §2 declares no module document for the lanes, reference/ or tests/ — per USER-978 (3), now root §7 OQ-2 :314-319, that is not missing context. Unresolved facts: none.
Rules:
- ARCHITECTURE.md:161 (§3 Forbidden, user-confirmed: "A second reader of any state file. `bin/` never re-implements a parse.") — CONTRADICTS — prior finding (1) is fixed for the gates it named: activate (bin/perry-goals:4966-4967) and close (:4999) now decide scored-ness through `P.parse_phase` (8a9d5ec1); probes P1/P2 refuse `> Status: scored` and `> **状态**: scored`. But `phase_header` (:4761-4779) still reads the phase document's `Status`/`Started` header lines with its own regex (`>\s*\*\*<field>\*\*:`, bold English only, HTML comments not stripped) and its answer still decides what is written and reported: close gates on it (:5002) and rewrites the line it finds (`splice_header` :4782, called :5015); new locates and rewrites both headers with it (:4908-4914) and never reads the result back through the parser. The two readers pick different lines. P5 (scratch): a phase whose real header is `> Status: active` with a bold `> **Status**: active` inside a multi-line HTML comment above it — `phase close` rc 0, `"status": "scored"`, `"written": true`, pointer set to `(none)`, snapshot written; the comment line was rewritten, `parsers.parse_phase` still reads `active`, and `phase activate --phase 002` then succeeds. P7: `phase new` with the bold Started/Status lines only inside a comment and real `> Started: {{YYYY-MM-DD}}` / `> Status: scored` — rc 0, reports `"started": "2026-09-21"`, `"status": "active"`, writes phase/CURRENT = 003-probe; the parser reads status `scored`, started `{{YYYY-MM-DD}}` — the pointer names a phase the one reader calls scored, the state the code's own comment (:4955-4958) says "the enum has no word for".
- ARCHITECTURE.md:161 / :243-249, pointer — CONTRADICTS (pre-existing, carried forward) — `phase_pointer` (bin/perry-goals:4726-4743) reads phase/CURRENT itself (its own PHASE_NONE sentinel set :4695) and is the pointer read for every phase-verb gate (:4862) and, via `current_phase` (:1556-1570), for TASK-475's `objective add` (:4388) and `link`. Base had the same copy in `current_phase`; TASK-474 consolidated it (tests/test_blank_cell_is_one_rule.py:247-251 records it). The previous review cited it under NN-1; the USER-978 fix does not touch it. No divergence reproduced: the sentinel set and strip match parsers.load_snapshot (viewer/parsers.py:5215-5218), and viewer/parsers.py exposes no pointer reader a tool could import.
- ARCHITECTURE.md:164-166 (§3 Forbidden, user-confirmed: roots from --root, $PERRY_PROJECT, then the walk; `bin/lib § resolve_project_root` the one implementation) — holds — prior finding (2) is fixed. Every root lookup in bin/perry-goals at head: phase_command :4851 `lib.resolve_project_root(v.get("--root"))`; main :5305 `lib.resolve_project_root(args.root)` (the older inline copy, base :4806-4807, removed as USER-978 (1) decided); draft_command :4583 takes the required `--root` only (DRAFT_FLAGS :4436-4441, no fallback; TASK-444, untouched by this range). P3: from <project>/sub/deeper with no --root and no PERRY_PROJECT, `phase close --dry-run` rc 0 on the project and `list --json` rc 0. `--help` :156 ("else walk up from cwd") is now true. No other bin/ root lookup is touched by the range.
- ARCHITECTURE.md:162-163 (§3 Forbidden: a lane computing a number) — holds — unchanged from the prior review; no counting in router/lane text or reference/startup.md.
- ARCHITECTURE.md:167 (§3 Forbidden: an agent writing ARCHITECTURE.md) — holds — 2225d076's edits are either user-decided (NN-1 Known exception = USER-971 answer verbatim in substance; §7 OQ-2 note = USER-978 (3), which says "record under §7 OQ-2"; §8 entry = USER-978 (2)) or descriptive §2 (NN-6 :291-295). No change to §1, §3 (incl. Forbidden), §5 or any confirmed §6 rule text beyond the added Known exception.
- ARCHITECTURE.md:100-118 (§2 lanes) — holds — both prior descriptive mismatches are corrected: :101-102 drops the router line count and cites tests/test_router_budget.py's byte cap (SKILL.md 20480, test_router_budget.py:45); :114-116 cites `reference/first-run.md § The recommended order for a new project` (first-run.md:62), which the router's first-time setup reaches via § The procedure (SKILL.md:140, first-run.md:44 "Steps 4–6 are the next two sections"). Lane-procedure findings of the prior review unchanged (no lane change in the fix).
- ARCHITECTURE.md:156-157 (§3 allowed directions) — holds — unchanged from prior review; the fix adds `P.parse_phase` and `lib.resolve_project_root` imports only in the allowed direction.
- ARCHITECTURE.md:213-221 (§5 argument surface) — holds — PHASE_FLAGS/PHASE_REQUIRED unchanged by the fix; TASK-475 `objective` declares its flags (KR_WRITER_FLAGS["objective"]).
- ARCHITECTURE.md:223-238 (§5 payload contracts / versions) — not touched.
- ARCHITECTURE.md:243-252 (NN-1, user-confirmed) — CONTRADICTS — same evidence as the two :161 findings. The added Known exception (:250-252, perry-context-budget's one config key) is USER-971's decision, written as USER-978 (2) authorised — holds as an edit. NN-1's grep check (:249) still prints the argv parser `bin/perry-goals:4814 def parse_phase(argv)` (false positive) and still misses `phase_header` / `phase_pointer`.
- ARCHITECTURE.md:254-263 (NN-2) — holds — unchanged; phase docs/pointer written, then the event.
- ARCHITECTURE.md:265-271 (NN-3: no command reports a write it did not perform) — contradicts, as a consequence of the :161 finding — P5's `close` reports `"status": "scored"` for a document the one reader still reads as active (it wrote a comment line); P7's `new` reports `"status": "active"`, `"started": <today>` for a document the reader reads as scored with a placeholder start date. Fail-safe cases hold: P4 (`> Status: active`) and P6 (`> **状态**: active`) close refuses "no `> **Status**:` header line to flip", rc 1, nothing written.
- ARCHITECTURE.md:273-280 (NN-4) — holds — unchanged.
- ARCHITECTURE.md:282-287 (NN-5) — holds — the fix's new tests (TestStatusIsReadByTheOneReader, TestTheProjectRootIsTheSharedOne) copy the sample project into tempfile.mkdtemp via Fixture.project; subprocesses run with cwd inside that copy.
- ARCHITECTURE.md:289-299 (NN-6) — holds — see :167 above.
- ARCHITECTURE.md:314-319 (§7 OQ-2) — holds — the addition is USER-978 (3) as answered; "Shape, cap, owner and drift stay open" deletes nothing.
- SKILL.md:48-71 (the V5-signed hand-off contract) — holds for the signed content; the section is NOT byte-identical as a whole — the signature record (5 lines), the invariant, the ownership table and the three refusal cases are byte-identical to 820da3b1 (scratch diff of base :48-78 vs head :48-71). Two paragraphs differ: the sign-off blockquote's second paragraph ("Recorded at this precision on purpose…", added in the signing commit e8952d64) moved to reference/hand-off-contract.md:13-24 by 293fba87, and the "Two changes from the previous contract" summary became a pointer (c44d5a64/293fba87). Under the section's own test (reference/hand-off-contract.md:6-11, :50-55: the ownership set) it holds; under a literal "the section is byte-identical" test it does not. The USER-978 fix does not touch SKILL.md.
- bin/ARCHITECTURE.md:98-99 (§3: a tool never parses a state file itself) — contradicts — same evidence as ARCHITECTURE.md:161.
- bin/ARCHITECTURE.md:104-105 (§3: the lock spans read, decision and write) — holds — every parse_phase read added by the fix is inside `project_lock(state_root)` (:4859).
- bin/ARCHITECTURE.md:156-160 (NN-B1) — holds — phase_main unchanged.
- bin/ARCHITECTURE.md:162-170 (NN-B2) — holds — unchanged.
- bin/ARCHITECTURE.md:172-178 (NN-B3, user-confirmed) — holds — see ARCHITECTURE.md:164-166.
- bin/ARCHITECTURE.md:73-80 (§2, edited by 2225d076) — descriptive mismatch, not a contradiction — "It is also the one tool that reads a state file itself" is not true of the tree: bin/perry-goals reads phase/CURRENT (:4742) and phase documents' headers (:4761) itself, and bin/perry-lint reads phase/CURRENT itself (:1309-1311). It can say "the one sanctioned exception". Needs correction (agent-editable §2) and re-review.
Decision: BLOCKED — decided-section contradiction: root NN-1 (ARCHITECTURE.md:243-249) and §3 Forbidden (:161), with bin/ARCHITECTURE.md:98 — bin/perry-goals `phase_header` still reads the phase document's Status/Started header lines for `close` and `new`, and disagrees with parsers.parse_phase on reproducible input so that close reports a phase scored that the reader reads active (P5) and new activates a phase the reader reads scored (P7); NN-3 (:265-271) follows from it. The prior root-resolution contradiction and both prior §2 descriptive mismatches are resolved. Carried forward, pre-existing: `phase_pointer`'s own read of phase/CURRENT (NN-1), which the fix did not address. New descriptive mismatch: bin/ARCHITECTURE.md:77-79 "the one tool that reads a state file itself".
User decision required: none for the phase_header finding — USER-978 (1) already decided "switch to the shared readers" for Status/Started; this is that decision not yet applied to `new` and to the written value in `close`. Named fix (not implemented here): after splicing, read the spliced text through `P.parse_phase` and refuse, writing nothing, unless it reports what the writer claims (close: status `scored`; new: status `active` and started == today) — so the writer keeps its line locator but the parser remains the only judge of what the document says. For the pointer: the PMO confirms whether USER-978's "switch to the shared readers" covers phase/CURRENT (the prior review's option (a) named "the pointer via the parsers' reader"; the USER-978 question text named only Status/Started and the root). If it does, the fix is a pointer reader in viewer/parsers.py imported by perry-goals; if not, the question to the user is: add that reader, or record an NN-1 Known exception for the phase/CURRENT sentinel copies.
Not checked: full suite not run (the PMO ran it green on this tree, 158/4452; no claim here depends on a run). No mutation round. perry-context-budget's config read (the NN-1 Known exception's truth) belongs to the TASK-471 re-review, not checked here. TASK-470's relocated reference pages checked for architecture rules only, not for content loss. perry-lint/perry-state direct reads of phase/CURRENT are outside this diff and not assessed as findings of this candidate. Probes ran on scratch copies of tests/fixtures/sample-project under the perry-scratch derivation, never on the reviewed tree.
=== END COMPLIANCE ===
```

## Supporting notes

### Candidate binding

- Worktree fast-forwarded from 0b5bf99e to `16124fb0` (`git merge --ff-only`,
  PMO-authorised; tree clean, the branch had no commits of its own).
- Fix commits read in full: `git show 2225d076`, `git show 8a9d5ec1 --
  bin/perry-goals`, test additions of 8a9d5ec1 and e381c870. TASK-475:
  `git diff e250a0fc c6d706ea -- bin/perry-goals`.
- USER-978 and USER-971 read from `perry/asks.jsonl` (lines 72 and 79).

### Every phase-document / pointer reader and root lookup in bin/perry-goals at head

| Site | Reads | Through |
|---|---|---|
| :1556 `current_phase` | phase/CURRENT | `phase_pointer` (own read) |
| :3557 `refuse_closed_kr` | phase doc Status | `P.parse_phase` |
| :4388-4390 `cmd_objective` (TASK-475) | pointer; phase doc Status | `current_phase`; `P.parse_phase` |
| :4726 `phase_pointer` | phase/CURRENT | own read, own sentinel set |
| :4761 `phase_header` / :4782 `splice_header` | phase doc / body header lines | own regex |
| :4908-4914 `phase new` | body's Started/Status lines | `phase_header` only |
| :4966 `phase activate` gate | phase doc Status | `P.parse_phase` (fixed) |
| :4999 `phase close` scored gate | phase doc Status | `P.parse_phase` (fixed) |
| :5002, :5015 `phase close` flip | phase doc Status line | `phase_header` / `splice_header` |
| :4583 `draft_command` root | `--root` (required) | no fallback; untouched |
| :4851 `phase_command` root | --root / env / walk | `lib.resolve_project_root` (fixed) |
| :5305 `main` root | --root / env / walk | `lib.resolve_project_root` (fixed) |

### Scratch

`$TMPDIR/perry-scratch/agent-a81aa376fc817a51f` — the
`perry-scratch-derivation` result for this worktree (the host refused the
inline `$(git …)` form, so the worktree basename was read separately and used
literally). Contents: `probe.sh`, `status.py` (prints `parsers.parse_phase`'s
status/started), `edit.py`, `probe.out`, fixtures `fx/p1`…`fx/p7`,
`skill.base`, `sec.base`, `sec.head`, `dirs.base`, `dirs.head`.

### Probe output (abridged from `probe.out`)

```
P1 '> Status: scored'      parser status 'scored' → phase activate refused "is scored", rc=1
P2 '> **状态**: scored'     parser status 'scored' → phase activate refused "is scored", rc=1
P3 cwd <project>/sub/deeper, no --root, no PERRY_PROJECT → phase close --dry-run rc=0; list --json rc=0
P4 '> Status: active'      parser 'active' → close refused "no `> **Status**:` header line to flip", rc=1
P5 comment holds '> **Status**: active', real header '> Status: active'
   close → rc=0 "status": "scored", "written": true, "event_written": true
   after: comment line now '> **Status**: scored', real line '> Status: active'
          parser status 'active'; CURRENT=(none); activate --phase 002 --dry-run → "activated": true, rc=0
P6 '> **状态**: active'     parser 'active' → close refused, rc=1
P7 body: bold Started/Status only in a comment; real '> Started: {{YYYY-MM-DD}}' '> Status: scored'
   new → rc=0 "started": "2026-09-21", "status": "active", "activated": true
   after: parser status 'scored', started '{{YYYY-MM-DD}}'; CURRENT=003-probe
```

P5 and P7 are constructed inputs — a phase document with a commented-out bold
header above a plain one. The prior BLOCKED rested on inputs of the same kind
(`> Status: scored`), and the rule does not depend on frequency: two readers of
one header that can disagree is what NN-1 forbids.

### Pre-existing drift noticed, not attributed to this candidate

- ARCHITECTURE.md §2 (:130) and §3 diagram (:150) "tests/ — 136 modules": 162 test modules at head.
- bin/ARCHITECTURE.md:73-80: the new sentence says perry-context-budget "runs
  no external program", while :69-71 says it runs `bin/perry-detect-host` as a
  subprocess. Readable as "no program outside Perry", but worth one word.
- review-constraints.md says a review round does not commit; this round
  committed only this evidence file because the PMO's brief asked for it.
