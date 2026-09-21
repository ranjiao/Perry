# TASK-470 — V4 review (fresh context)

Date: 2026-09-21. Reviewer: fresh-context review agent (Claude Opus 5). I did not
write this code. Criteria: `perry/evidence/2026-09/TASK-470-spec.md`, which resolves
at the base `359a7be1`. Range under review: `359a7be1..8ff2ea81` (implementation
`293fba87`, evidence `437725e5`, decisions `8ff2ea81`; merged at `dc3e1f51`).
Worktree fast-forwarded `0b5bf99e → c66fcaad` under the PMO's authorisation, clean
tree, no commits of its own. `8ff2ea81..c66fcaad` touches no shipped page (PMO
state, TASK-472 evidence, and a comment-only edit to `tests/test_spec_scannability.py`).

Scratch: `$PERRY_SCRATCH` = `${TMPDIR}/perry-scratch/agent-a5a207790f16f85ae`. I
derived it from the `perry-scratch-derivation` block, but the host refused
`$(git rev-parse …)` inline, so I ran `git rev-parse --show-toplevel` on its own
and then the `basename` + `mkdir` part. Two disposable copies live there:
`base/` (`git archive 359a7be1`) and `head/` (`git archive 8ff2ea81`). Every
mutation went into `head/` and nowhere else.

Per the brief I did not FAIL on the two recorded misses (router ≤ 12,288;
dispatch ≤ 80,037) or on moving the sign-off rationale paragraph (USER-975).

## Criterion 4 — the routine-path walk (the priority)

**What I did.** For each of the five commands I compared the **base** declared
load set (from `perry-context-budget --bill all --json` run in `base/`) with the
**head** load set, and listed every non-trivial line (≥ 25 characters,
whitespace-normalised) that the base set carried and the head set does not
(`offpath.py`, 687 lines across the three `work` commands, plus the snapshot
and plan-phase sets). Each line is tagged with where it lives now. I then
classified each group by hand. A second pass (`vanished.py`) listed every
removed line that survives **nowhere** in the head tree: 162 of 450. I read all
162.

| Group moved off a routine load set | Lines | Now reached by | Verdict |
|---|---:|---|---|
| Router First-time setup steps 1–3 → `first-run.md § The procedure` | 63 | Router: "Read `reference/first-run.md § The procedure` and follow its six steps in order". An explicit read instruction, and the step only runs on `installed: false` | reached, conditional |
| `okr-linkage.md` graph, record rules, integrity invariants → `linkage-store.md` | 54 | Written only through `perry-task add --kr` / `perry-goals link`; checked by `perry-lint`. The resolution order, the ask and the unavailable-user rule stay in `okr-linkage.md § The one rule` (in the add-task bill) | conditional (store shape) |
| `subcommands.md` cadence/handoff/rollover bodies no longer in the close-task set | 44 | not needed by close-task; still in `subcommands.md` for their own commands | not routine for close-task |
| `work/SKILL.md` Axis A/B tables → `state-files.md § Two file models` | 33 | The lane keeps the one-line form of each axis and the **tier-1 refusal**. Checked verbatim | reached for the rule; tables are reference |
| `add-task.md` histories → `add-task-notes.md` | 30 | Every rule sentence is still in `add-task.md` (read hunk by hunk) | rationale only |
| `input-quality.md` §1–§3 → `input-quality-rubrics.md` | 27 | add-task runs §4, which stayed. plan-phase: `phases.md` / `elicitation.md` / `setup.md` now say "run `input-quality-rubrics.md § 2`", and the page is in the plan-phase bill | reached |
| `git-boundaries.md` Time Estimation → `time-estimation.md` | 8 | dispatch reads only `Estimated cycle` → sync/async (`dispatch.md:182`, unchanged). Estimates are for a user's question | conditional |
| `dispatch-preflight.md` / `dispatch.md` incidents → `dispatch-notes.md` | 7 + | every rule, gate and default kept at its old site: 4h TTL, reap warning, release on every failure path, "the judgement is yours", work the five steps, 4.5's standing entry | rationale only |
| `work/SKILL.md` → `lane-notes.md` | 12 | the rule form of each passage is still in the lane (hand-edit reported not refused, V4 rule, `perry-explain V4`) | rationale only |
| Budget boundary (`subcommands.md § handoff`) → `budget-boundary.md` | — | Declared on the close-task **and** dispatch index rows. `task-close.md:122` and `dispatch.md:13` / `:410` name it at the step that needs it | reached |
| Router: per-host tool names, auto-update detail, Packs absent/empty, release-automation line, relocate "never moves a file it did not put there", adopt stage list | — | `host-capabilities.md § Prompt rendering` (read at router step −1 on every Change route); router step 0 still says "throttled to once per 7 days"; `config.md` lines 48 and 254–259; `router-subcommands.md § /perry relocate` "What it never does" (router: "Steps: …"); `adoption.md` ("Read references first") | reached |

Gates and refusals I confirmed still sit on the new path, by reading the head
bytes: tier-1 hard-cap refusal (`work/SKILL.md:79`); no `done` without evidence
(`:150`, `:185`, `:246`); V4 rows cannot close from the lane (`:63`); the KR
attribution hard gate, including ask-else-`unlinked` and never fuzzy-match
(`:248` and `okr-linkage.md:10–56`); the unarmed-safety-gate refusal (`:252`); the
recovery and interrupted-run gates (router steps 2–3, byte-identical to base);
close-task gates 1–3, the V5 signoff procedure and the knowledge capture point
(`task-close.md`, verbatim from base apart from one repointed citation, checked
by string diff); dispatch pre-flight steps 1–4.6, the 4h TTL, the reap warning
and the budget checkpoints; `--summary`/`--deliverable`/`--verification`
refusals; `--unlinked` "not a way past the refusal" and "cannot be withdrawn";
spec `## ` shape "disarms the gate"; track moves by command only; the
`AskUserQuestion`-is-not-a-permission-grant rule that `dispatch-preflight.md:52`
cites (`SKILL.md § User-prompt convention`, still present).

**One rule is stranded (F1).** Base `work/SKILL.md:139` (standup step 0, loaded by
add-task, close-task and dispatch) said: *"Headings and column headers localize
through the glossary in `schema/state-schema.json § i18n`."* Head
`work/SKILL.md:86` dropped it. It survives only in `reference/i18n.md § 2`
("Use the glossary spelling, not a synonym"), which is in none of the three
`work` bills. The lane cites that page only as `contract: $PERRY_HOME/reference/i18n.md`,
which is a citation, not an instruction to read it. Meanwhile the new step 0
says files use `Document language` and lists what stays English, and headings
are not on that list. On a non-English project, then, the routine path no
longer says that a heading an agent writes (a P0/P1 spec's `## Deliverable` /
`## Files in scope` / `## Out of scope`, all glossary entries) must use the declared spelling.
The relocation map row "Standup step 0 wording" says every clause stayed, and
does not list this one. The consequence is partly mitigated: the lane still
carries "Write the declared structure … a renamed heading … silently zeroes a
dashboard row … run `perry-lint`" (`work/SKILL.md:250`). I did not verify that
`perry-lint` reports a non-glossary localized heading, so I claim no more
mitigation than that.

## Other criteria

- **Criterion 1 (reuse).** No change under `bin/`, `schema/` or `viewer/`, and none to
  `tests/test_router_budget.py` (`git diff --stat 359a7be1 8ff2ea81 -- tests bin schema viewer`).
  Base frozen at `359a7be1`. Met.
- **Criterion 2.** Re-measured: router 15,308 (miss accepted, USER-975); work 24,563,
  goals 22,442 and decide 23,959, all ≤ 24,576. Tier caps unchanged. Met apart from the recorded exception.
- **Criterion 3.** I re-ran the bill tool in both copies: snapshot 78,456 → 73,395;
  add-task 99,947 → 68,275 (−31.7 %); close-task 92,853 → 64,905 (−30.1 %);
  dispatch 114,338 → 95,750 (−16.3 %, accepted miss); plan-phase 108,906 →
  104,530. All equal the result file, and so do the twelve sha256 prefixes. **Shared paths count once**,
  checked by mutation: declaring `budget-boundary.md` twice on the close-task row
  moved the total by +33 (the added text), not +2,181; declaring `$PERRY_HOME/SKILL.md`
  on that row moved it by +30, not +15,308. Conditional and dynamic reads are listed separately. Met.
- **Exceptions described truthfully.** USER-975 in `perry/asks.jsonl` matches the result: 15,308 vs 12,288,
  and −24.85 % vs −39.7 %; 95,750 vs 80,037 (114,338 × 0.7). The 93,569 / −18.2 % counterfactual is right, and so is the claim that the
  base dispatch row did not declare the budget checkpoint that dispatch required. Truthful.
- **Criterion 5 (no duplicated procedure body).** Across the four entry files and
  every `reference/` page in all four trees, no line of 100 characters or more is duplicated
  that was not already duplicated at base. The one base duplicate went (the closing-step line between goals and work). The
  new notes and split pages share no ≥ 60-character line with any procedure page, except the
  4-line `perry-config set` block in `first-run.md` / `decide/SKILL.md`, which was
  there at base. The router's setup summaries of steps 4–6, which duplicated
  `first-run.md`, were removed. Met.
- **V5-signed content.** I diffed base `SKILL.md` lines 48–80 against head lines 48–71.
  The only differences are the removed "Recorded at this precision" paragraph
  (accepted) and the pointer line after the table, which is outside the signed
  scope. Signer, date, checked scope, invariant, ownership table and the three
  refusal cases are byte-identical. The paragraph is verbatim in `hand-off-contract.md`.
- **Pointer exactness.** Every citation of a created or split page resolves to an
  existing heading (48). The other 10 use the `§ N` rubric-number convention,
  which base used for the same pages. Moved blocks checked line by line: rubrics,
  linkage store, time estimation, budget boundary, Axis A/B and setup steps 1–3
  all arrive with 0 lines missing. `task-close.md` equals the base close/drop section except for
  one repointed citation.
- **Criterion 6 (negative proofs), re-run by me.** C1 router padded to exactly 20,480 → green; C2 20,481 →
  red; C3 `work/SKILL.md` at 38,913 → red; C4 index row → `task-closed.md` → red
  (`TestEveryDeclaredSubcommandHasAProcedure`, 2 failures) and the bill exits 1; C5
  router pointer → `§ The procedures` → red (`TestSectionCitationsResolve`).
  No budget was raised and no guard was removed.
- **The five re-pointed tests, mutated.** A1 (drop `--claims` from the procedure) red; A2 (router no
  longer names `§ The procedure`) red, 4 failures; A3 (default root `perry` → `state`) red;
  A3b (declaration deleted) red; A4 (close-task no longer cites `promotion.md`) red;
  A5 (hand-edit sentence planted in close-task) red; A5b (close-task section
  emptied) red; A6 (ADR procedure planted in `task-close.md`) red; A7 (revert
  `task-close.md` out of `test_task_writer_contracts`' list) red, 2 errors. A8
  (revert it out of `test_work_modes`' list) stays green, **which is expected**: its
  positive asserts do not need the page. A8b (revert plus the A6 plant) stays green,
  which shows the added path is what makes the negative guard see the moved text. Each re-pointed test still tests what it tested.

## Findings that are not the verdict's

- **F2.** `work/reference/autopilot.md:196` still cites `subcommands.md § Budget boundary`.
  It resolves only through the stub (`See budget-boundary.md …`), one extra hop,
  and the relocation map's list of repointed citations omits it. Separately, the section-citation guard
  cannot see a citation wrapped across a line: mutant C6 (`§ Budget\n boundry`)
  **survived**, and the same typo on one line (C6b) was killed. The guard gap predates
  this row, and autopilot is not one of the five commands.
- **F3.** The rewritten paragraph at `work/reference/add-task.md:151` still describes the
  output of a scan that was removed on 2026-09-04 (`touches: {}`, `verdict: pass`,
  exit 0). The claim predates TASK-470, but this change rewrote the paragraph and kept it.

## Suite

`bash tests/run --tier affected --base 359a7be1` on `c66fcaad`: green. 74 modules,
2,446 tests, 57.1 s; tree guard reported nothing moved. `test_host_support` did not go red.
Log: `$PERRY_SCRATCH/affected.log`. I did not re-run the full suite; the PMO's
full run on `dc3e1f51` (157 modules / 4,434 tests) is cited, not re-verified.

Restores: each mutant's file was rewritten from `git show 8ff2ea81:<path>` and
compared byte for byte against that. At the end the whole `head/` copy was
`diff -r`'d against a fresh `git archive 8ff2ea81`, with no differences.
`bin/perry-restore-check` was not used, because the copy is not a git checkout.
Harness and full logs of every mutant, pass or fail: `$PERRY_SCRATCH/mutate.py`,
`$PERRY_SCRATCH/mutations/*.log`. The worktree's `git status` was clean throughout.

=== VERDICT ===
task: TASK-470
rung: V4
result: FAIL
grade: ROW — criterion 4, the work lane's standup step 0 dropped "headings and column headers localize through the glossary" from the add-task/close-task/dispatch load sets; the relocation map says every clause stayed
criteria: perry/evidence/2026-09/TASK-470-spec.md
checked: criteria 1-6 against 359a7be1..8ff2ea81; five base vs head load sets diffed line by line (offpath.py, vanished.py), every off-path group classified by hand; bills re-run in both archive copies and matched, shared-path-once proven by two mutations; V5-signed block byte-diffed; moved blocks verified verbatim; 20 mutants on a git-archive copy (9 against the five re-pointed tests, cap+1/cap-0/broken-pointer/broken-section, shared-path), all as expected except C6 (pre-existing guard gap, F2); affected tier green on c66fcaad
not-checked: full suite (PMO run cited, not re-run); a live agent executing any of the five commands; whether perry-lint reports a non-glossary localized heading (F1's only mitigation); dynamic-read table row by row; add-task-notes.md block-by-block (covered only by the vanished-line scan); goals/decide routes other than plan-phase; autopilot, handoff, review and delegate paths beyond F2
proof: work/SKILL.md:86 (head) omits base work/SKILL.md:139 "Headings and column headers localize through the glossary in `schema/state-schema.json § i18n`"; the rule survives only at reference/i18n.md:77-97, which is outside the add-task, close-task and dispatch bills and is cited from the lane only as "contract:"
=== END VERDICT ===
