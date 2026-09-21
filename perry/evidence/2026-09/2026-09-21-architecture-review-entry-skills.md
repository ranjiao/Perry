# Architecture review — entry skills (TASK-469, TASK-470, TASK-474), integrated candidate

Late gate required by `work/reference/dispatch.md § Architecture review` (the
root and lane `SKILL.md` files changed). The gap was found by
`perry/evidence/2026-09/TASK-473-acceptance.md`. Brief:
`work/reference/review.md § Integration architecture reviewer brief`.
Constraints: `work/reference/review-constraints.md`.

Scope: the product (non-`perry/`, non-`.perry/`) changes of
078d6da2, 86121e40, bb3d97d6, c44d5a64, 256ae459 (TASK-469), 293fba87, 9c1a2b7c
(TASK-470), ebfb2b8d, 92a3448e, e250a0fc (TASK-474). Other commits in the range
(TASK-468, TASK-471, TASK-472, TASK-475) are out of scope.

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: Claude Code subagent (claude-opus-5), fresh context, worktree agent-a42a4733e02f2ce5c; not the author of TASK-469/470/474 and carrying none of their conversation; no author compliance verdict received; timestamp: 2026-09-21T13:59:36+0800
Base: 820da3b1849df4f7155baf976b1045c6590bd129
Head: 4414ddee1041b0d9cdfebe29d47ae3538b337f86
Triggers:
- Listed boundary paths: TRUE. SKILL.md (078d6da2, 86121e40, c44d5a64, 293fba87), goals/SKILL.md (078d6da2, 256ae459, 293fba87, ebfb2b8d), work/SKILL.md (078d6da2, c44d5a64, 256ae459, 293fba87, 9c1a2b7c), decide/SKILL.md (078d6da2, 293fba87). viewer/parsers.py, bin/lib/, schema/ unchanged base..head.
- New top-level directory: FALSE. `git ls-tree -d --name-only` lists the same 17 directories at base and head.
- New bin executable: FALSE. `git diff --raw 820da3b1 4414ddee -- bin`: only M entries, modes 100755→100755 / 100644→100644; no A/R. bin/perry-goals gains a `phase new|activate|close` verb family inside an existing executable.
- Contract-version change: FALSE. schema/ (incl. *-contract.md) unchanged; root §5 versions unchanged (ARCHITECTURE.md unchanged); reference/hand-off-contract.md carries no version declaration. VERSION 0.1.16→0.1.17 is Perry's product release version (f31c5d78, TASK-468, out of scope), not a §5 contract.
- Root architecture edit: FALSE. `git diff 820da3b1 4414ddee -- ARCHITECTURE.md` is empty.
- Module architecture edit: FALSE for the scoped commits. TRUE for the range: bin/ARCHITECTURE.md changed by 5752ff71 (TASK-468) and 6bb4dc6f (TASK-471) — out of this review's scope and not reviewed here.
Context: root ARCHITECTURE.md §1 (43), §2 (58), §3 (138), §5 (211, on demand), §6 (240), identical at base and head. Component mapping from the confirmed §2 list: `SKILL.md + goals/ work/ decide/` (100-118) for all three tasks; `modes/, packs/, reference/, templates/` (120-127) for reference/startup.md, first-run.md, hand-off-contract.md and the relocated pages; `bin/` (60-73) for bin/perry-goals (TASK-474); `tests/` (129-132) for the new test modules. Module documents: bin/ARCHITECTURE.md v1 (identical at base for its §3/§6; its only change is the out-of-scope §2 insert). §2 declares no module document for the lanes, reference/ or tests/ components; their §2 entry is their whole architecture context — named here, not treated as silently present. Unresolved facts: none for the scoped commits.
Rules:
- ARCHITECTURE.md:43-56 (§1 scope: no unattended writes, no meaning judged in code, no state outside the project) — holds — the route table (SKILL.md head lines 74-82) makes Explain write nothing and Query read one projection after the gates; reference/startup.md "The route is the agent's reading of the request. No script classifies it"; perry-goals phase verbs write only under the resolved state root and refuse when it is outside the project (phase_command, bin/perry-goals:4838-4846).
- ARCHITECTURE.md:100-118 (§2 lanes: procedure only; the next block is not added to, dropped or reordered; every figure from a bin/ call) — holds — work/SKILL.md step 7 keeps "The command decides; never add, drop or reorder a recommendation"; router step 5 still renders `next` per reference/next.md; Query route forbids a `next` block and a second read (reference/startup.md § Query); no lane computes a figure.
- ARCHITECTURE.md:101 and :115 (§2 descriptive: "the router (222 lines…)"; setup order is "the router's own (`SKILL.md`, first-time setup step 5)") — descriptive mismatch, not a contradiction — the router is 181 lines at head (225 at base, already off by 3); 293fba87 moved First-time setup steps 1-6 to reference/first-run.md § The procedure (step 5 is now reference/first-run.md:64), so the §2 carve-out cites a location that no longer holds the text. Needs correction (agent may edit §2 per NN-6, :287) and re-review.
- ARCHITECTURE.md:156-157 (§3 allowed directions: lanes → tools → libraries → state) — holds — lanes' steps −3 to −1 now delegate to the router's startup (goals/SKILL.md, work/SKILL.md, decide/SKILL.md "Router startup, once per operation"); no new direct state parse by a lane.
- ARCHITECTURE.md:160 (§3 Forbidden, user-confirmed: "A second reader of any state file. `bin/` never re-implements a parse.") — CONTRADICTS — ebfb2b8d (refined 92a3448e, e250a0fc) adds bin/perry-goals `phase_header` (:4752) which reads a phase document's `Status`/`Started` headers with its own regex `>\s*\*\*<field>\*\*:` (bold, English, blockquote only, HTML comments not stripped), and uses it for the activate scored-gate (:4951) and the close gate (:4981). The one reader, viewer/parsers.py `parse_phase` (:3024, Status at :3037), accepts `Status:`/`**Status**:`/`状态` and strips comments; the same file's KR gate `refuse_closed_kr` already reads Status through `P.parse_phase` (bin/perry-goals:3557). Reproduced on a scratch fixture: a phase doc with `> Status: scored` (or `> **状态**: scored`) — parsers.parse_phase → status 'scored'; `perry-goals phase activate --phase 001 --dry-run --json` → `"activated": true`, rc 0. The writer would point phase/CURRENT at a phase the reader reports as scored — the state the code's own comment says "the enum has no word for".
- ARCHITECTURE.md:161-162 (§3 Forbidden: a lane computing a number) — holds — no counting in the new router/lane text or reference/startup.md; Query answers from `--section`, `perry-explain`, `perry-task list --json`.
- ARCHITECTURE.md:163-165 (§3 Forbidden, user-confirmed: roots from --root, then $PERRY_PROJECT, then the walk up; `bin/lib § resolve_project_root` is the one implementation) — CONTRADICTS (extends a base deviation) — phase_command (bin/perry-goals:4839-4840) re-implements the resolver inline as `--root` else `$PERRY_PROJECT` else `Path.cwd()`, with no walk up, while `--help` (:154) advertises "else walk up from cwd". Same inline copy pre-exists in perry-goals' main path (base :4807, head :5289); TASK-474 adds another body. Scratch fixture, cwd = <project>/sub, no --root/PERRY_PROJECT: perry-goals phase refused "<project>/sub is not an installed Perry project", rc 1; lib.resolve_project_root() from the same cwd → <project>. Fail-safe (refuses, never reaches another project), but a second implementation and a documented order it does not follow.
- ARCHITECTURE.md:166 (§3 Forbidden: an agent writing ARCHITECTURE.md) — not touched — ARCHITECTURE.md unchanged base..head.
- ARCHITECTURE.md:213-221 (§5 bin/ → agent argument surface: exit 0/1/2/3; a flag reaches only subcommands that declare it; refusal is an outcome) — holds — PHASE_FLAGS/PHASE_REQUIRED per mode; undeclared or repeated flag → exit 2 naming the legal set (parse_phase argv parser); refusal → exit 1, JSON on stdout with --json; success exit 0. perry-goals declares no SURFACE, as before (bin/ARCHITECTURE.md:129-131 lists it among the undeclared).
- ARCHITECTURE.md:223-238 (§5 published payload contracts) — not touched — schema/ and perry-state/perry-task unchanged by the scoped commits.
- ARCHITECTURE.md:242-248 (NN-1, user-confirmed: exactly one implementation parses any given state file, in viewer/parsers.py; a bin/ tool imports it) — CONTRADICTS — same evidence as :160 above (phase_header, and phase_pointer :4717 which re-reads phase/CURRENT with its own sentinel set, a refactor of the base `current_phase` copy — itself pre-existing). NN-1's mechanical check (:248) does not catch it: the new hit it prints, `bin/perry-goals:4805 def parse_phase(argv)`, is an argv parser (false positive), and the real reader is named `phase_header`.
- ARCHITECTURE.md:250-259 (NN-2: store is truth; projection rendered; no board file) — holds — phase documents are tier-1 documents with no store; the phase verbs write the document/pointer, then append the event (append_event after write_atomic, bin/perry-goals:5007); no BOARD.md read or written.
- ARCHITECTURE.md:261-267 (NN-3: no reported write that was not performed) — holds — `--dry-run` reports "would write"/`"written": false`; `event_written` reports the event append separately; OSError is converted to a refusal. Note (not a violation): `new` (doc + pointer) and `close` (snapshot + doc + pointer) are sequential atomic writes, not one transaction.
- ARCHITECTURE.md:269-276 (NN-4: bin/ decides nothing about meaning) — holds — the phase verbs judge slugs by regex, line counts against the schema cap, and header presence; the router's route is chosen by the agent, "No script classifies it" (reference/startup.md).
- ARCHITECTURE.md:278-283 (NN-5: suite never writes the tree it runs in) — holds — tests/test_phase_lifecycle.py copies the sample project into `tempfile.mkdtemp` (:60-69); tests/test_startup_routing.py reads shipped pages only.
- ARCHITECTURE.md:285-295 (NN-6: agent may not decide ARCHITECTURE.md) — not touched.
- SKILL.md:48-70 (the V5-signed hand-off contract, decided) — holds — signature record (5 lines), invariant, ownership table (12 lines) and the three refusal cases are byte-identical base→head (compared in scratch). 293fba87 moved the blockquote's second paragraph ("Recorded at this precision on purpose…") to reference/hand-off-contract.md § Why the sign-off is recorded at this precision, and c44d5a64 replaced the "Two changes" summary with a pointer — both rationale/history, not ownership, under the section's own test ("byte-identical ownership set", reference/hand-off-contract.md:6-11). perry-goals phase verbs write only phase/…, phase/CURRENT, phase/snapshots/ (goals-owned) and .perry/events.jsonl; no lane writes outside its own.
- bin/ARCHITECTURE.md:94-95 (§3: a tool never parses a state file itself) — contradicts — same evidence as NN-1.
- bin/ARCHITECTURE.md:100-101 (§3: the lock spans read, decision and write) — holds — phase_command does every read, gate and write inside `project_lock(state_root)`.
- bin/ARCHITECTURE.md:152-155 (NN-B1: --help never runs anything) — holds — phase_main checks `--help`/`-h` anywhere in argv before parsing or locking.
- bin/ARCHITECTURE.md:158-165 (NN-B2: undeclared token refused) — holds — parse_phase exits 2 for any token not in PHASE_FLAGS[mode].
- bin/ARCHITECTURE.md:168-174 (NN-B3, user-confirmed: one resolver, one order, lib.resolve_project_root) — contradicts — same evidence as ARCHITECTURE.md:163-165.
Decision: BLOCKED — decided-section contradictions: (1) root NN-1 (ARCHITECTURE.md:242-248) and §3 Forbidden (:160), with bin/ARCHITECTURE.md:94 — TASK-474 perry-goals `phase_header`/`phase_pointer` re-implement the phase-document and pointer read, and the activate gate disagrees with parsers.parse_phase on reproducible input; (2) root §3 Forbidden (:163-165) and bin NN-B3 (:168-174) — TASK-474 phase_command re-implements project-root resolution without the walk. Descriptive mismatch needing correction and re-review: ARCHITECTURE.md §2 :101 (router line count) and :115 (setup-order location moved by TASK-470). TASK-469 and TASK-470 have no contradiction; the V5 hand-off contract holds.
User decision required: NN-1 and root §3 Forbidden are user-confirmed (ARCHITECTURE.md:3). Question: for TASK-474's phase writer, (a) require the fix — gate decisions read Status/Started via viewer/parsers.parse_phase and the pointer via the parsers' reader, root via lib.resolve_project_root — then re-review (recommended; needs no rule change), or (b) record a known exception to NN-1 / §3 for a writer locating the header line it rewrites (splice position only), which is an architecture change only the user can make. The resolver finding extends a pre-existing perry-goals deviation (base :4807); whether its fix is bundled here or opened separately is the PMO's call, but the rule itself is not in question.
Not checked: full test suite not run (an architecture verdict needs none; no claim here depends on a green run). No mutation. Scope limited to the listed commits' product changes; TASK-468/471 bin/ARCHITECTURE.md edits and TASK-475 perry-goals `objective add` not reviewed (TASK-475's own P.parse_phase use at bin/perry-goals:4390 was only noticed). reference/, work/reference/ relocated pages checked for architecture rules only, not for content loss against TASK-470's own acceptance criteria. Probes ran on a scratch fixture under the perry-scratch derivation, never on the reviewed tree.
=== END COMPLIANCE ===
```

## Supporting notes

### Candidate binding

- Worktree fast-forwarded from 0b5bf99e to `4414ddee` (`git merge --ff-only`,
  PMO-authorised; tree clean, branch had no commits of its own).
- Per-commit scope: `git show --stat <sha> -- . ':!perry' ':!.perry'` for each
  of the ten commits; combined: `git diff 820da3b1 4414ddee -- SKILL.md
  goals/SKILL.md work/SKILL.md decide/SKILL.md bin/perry-goals`
  (perry-goals attributed to TASK-474 via `git diff 820da3b1 e250a0fc --
  bin/perry-goals`; later changes to it are TASK-475, out of scope).

### Scratch

`${TMPDIR}/perry-scratch/agent-a42a4733e02f2ce5c` — the
`perry-scratch-derivation` result for this worktree. The harness refused
`$(git rev-parse --show-toplevel)` inside a compound command, so the basename
was obtained by a separate `git rev-parse --show-toplevel` and used literally;
the path is the same one the block derives. Contents: `skill.base`,
`skill.head`, `sig5.*`, `own.*`, `forbid.*` (hand-off contract byte
comparison), `goals474.diff`, `probe.sh` and its fixture `fx/`.

### Probe output (scratch fixture, `probe.sh`)

```
== P1: a phase doc whose Status header is not bold: > Status: scored
parsers status = 'scored'  started = '2026-09-01'
perry-goals phase activate --phase 001 --dry-run --json → "activated": true, "written": false; rc=0
== P2: 中文 header > **状态**: scored
parsers status = 'scored'
perry-goals phase activate … → "activated": true; rc=0
== P3: root resolution from a subdirectory, no --root, no PERRY_PROJECT
perry-goals phase activate … → refused: "<fx>/proj/sub is not an installed Perry project …"; rc=1
lib.resolve_project_root() = <fx>/proj
perry-goals --help: "--root <path>   project root; default $PERRY_PROJECT, else walk up from cwd"
```

### Pre-existing drift noticed, not attributed to this candidate

- ARCHITECTURE.md:129 "`tests/` — 136 modules": 159 test modules at base, 162
  at head.
- bin/ARCHITECTURE.md edits by TASK-468 (5752ff71) and TASK-471 (6bb4dc6f)
  are a module-architecture-edit trigger in the same range; no
  `ARCHITECTURE COMPLIANCE` block for either was found under
  `perry/evidence/2026-09/`.
