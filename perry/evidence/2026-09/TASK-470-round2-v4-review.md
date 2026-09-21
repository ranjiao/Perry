# TASK-470 — V4 review, round 2 (fresh context)

Date: 2026-09-21. Reviewer: fresh-context review agent (Claude Opus 5). I did not
write this code, and I did not write round 1's review. Criteria:
`perry/evidence/2026-09/TASK-470-spec.md`, which resolves at the base `359a7be1`. The whole
delivery under review is `359a7be1..9c1a2b7c`. Round 2 on its own is `3115d09c..9c1a2b7c`,
merged at `ecfa2245`. The worktree was clean with no commits of its own, and I fast-forwarded it
`0b5bf99e → 49c7c570` under the PMO's authorisation. `9c1a2b7c..49c7c570` touches only
`.perry/events.jsonl`, `perry/journal/2026-09/2026-09-21.md` and `perry/tasks.jsonl`.

Scratch: `$PERRY_SCRATCH` = `${TMPDIR}/perry-scratch/agent-a8dbd60f6ed3696a3`. The host refused
`$(git rev-parse …)` inline, so I ran `git rev-parse --show-toplevel` and `echo $TMPDIR` as
separate commands and then ran the `basename` + `mkdir` step. It holds four disposable
`git archive` copies: `base/` (359a7be1), `r1/` (8ff2ea81), `head/` (9c1a2b7c), and `mut/`
(9c1a2b7c, the only copy I mutated). The harnesses are `offpath.py`, `uniq.py`, `mutate.py`,
`mutate2.py`, `unguarded.py` and `resolve_unguarded.py`. Every output is kept, including the
green ones: `uniq.txt`, `off-*.txt`, `mutations/*.log`, `unguarded-{base,head}.txt` and
`affected.log`.

Per the brief I did not FAIL on the two recorded misses (router 15,308 > 12,288; dispatch
95,758 > 80,037) or on moving the sign-off rationale paragraph. Those are USER-975 and are
recorded in `perry/asks.jsonl`.

## The round-2 fix

- **The restored clause.** It is at `work/SKILL.md:85`, and it is byte-identical to the base's
  `work/SKILL.md:139`: *"Headings and column headers localize through the glossary in
  `schema/state-schema.json § i18n`"*. `schema/state-schema.json` carries `i18n.headings` and
  `i18n.columns`. Because this is standup step 0, it runs on add-task, close-task and dispatch.
- **Removing the `Why:` pointer removed no rule.** The pointer led to
  `reference/startup.md § The pack rule is scoped by route`. That section is history only: USER-974
  principle A, and the account of two V4 rounds. Everything that section states as a rule is still in
  the lane paragraph (`work/SKILL.md:16–29`): never on Explain, mark rather than filter, never
  filter, hide or withhold. `test_startup_routing` pins that paragraph, and mutant M6 shows it does.
  The pointer now sits verbatim at `lane-notes.md § Why the pack rule is scoped by route`, and it
  resolves.
- **The "before continuing" → "first" rewording.** The line now reads *"prompt for top-level
  `/perry` first-time setup first."* It still means "before anything else runs", so no condition,
  branch or refusal changed.
- **F2 (autopilot).** `autopilot.md:196–197` now cites `budget-boundary.md § Budget boundary`,
  which resolves. That page is byte-identical to the base's `subcommands.md § Budget boundary`
  apart from its new H1 and provenance line (checked with `diff`).
- **Bytes.** `work/SKILL.md` is 24,571 bytes (≤ 24,576). I re-ran the bills in all three copies.
  Here are the base and head totals:

  | Command | Base | Head | Change |
  |---|---:|---:|---:|
  | snapshot | 78,456 | 73,395 | — |
  | add-task | 99,947 | 68,283 | −31.68 % |
  | close-task | 92,853 | 64,913 | −30.09 % |
  | dispatch | 114,338 | 95,758 | −16.25 %, accepted miss |
  | plan-phase | 108,906 | 104,530 | — |

  The result file's § Round 2 figures match. Close-task still clears −30 %, with 84 bytes of
  margin. goals is 22,442, decide 23,959 and the router 15,308.

## Criterion 4, re-applied to the whole delivery

**Method.** I did not reuse round 1's harness. For each of the five commands I took the base's
declared load set (`perry-context-budget --bill all --json`, run in `base/`). I split every file into
sentences, list items and table rows, and listed every one (≥ 20 characters, normalised) that is
missing from the head's load set for that command. For each, I recorded where it lives in the head
tree, or that it survives nowhere, which usually means it was reworded:

| Command | Base units | Absent from the head set | Absent everywhere in head |
|---|---:|---:|---:|
| snapshot | 809 | 68 | 42 |
| add-task | 813 | 324 | 171 |
| close-task | 837 | 333 | 169 |
| dispatch | 1,001 | 261 | 172 |
| plan-phase | 962 | 70 | 44 |

After de-duplication that is **452 unique units** (`uniq.txt`), and I read all of them. For every
unit that carried a gate, refusal, ordering step, host behaviour, safety check or file-format rule, I
found where the head's routine path still states it, or confirmed that it is conditional and the
path still says to read it. I also ran full `diff`s of every base load-set file against the head:
router, `work/SKILL.md`, `add-task.md`, `input-quality.md` (against the head page plus the rubrics
page), `dispatch.md`, `dispatch-preflight.md`, `git-boundaries.md`, the base close/drop section
against `task-close.md`, `next.md`, `host-capabilities.md`, `snapshot.md`, `i18n.md`, and the three
goals files. I diffed `decide/SKILL.md` too.

| Command | Classes enumerated | Where each stands at 9c1a2b7c |
|---|---|---|
| all five (router) | Mandatory-first-move steps −2 to 3, recovery gate, interrupted-run gate, Change-only setup prompt | Byte-identical: `diff` shows no hunk in lines 72–134 |
| all five (router) | Hand-off contract (invariant, table, three refusal cases) | Unchanged; only the "recorded at this precision" rationale paragraph moved (USER-975) |
| all five (router) | Host behaviour: native choice UI, Codex fallback, "same labels … selected value" | Router `:175` points to `host-capabilities.md § Prompt rendering`, which step −1 reads on every route; `:77` and `:87` carry equivalent labels and recommendation, and say the selected value does not change |
| all five (router) | Language/file format: files in Document language, chat in Chat language, one language per file, IDs/enums/paths English, quoted artefacts untranslated, chat mixing, field names English | Router `:90`, `:161`, `:171`; only the Chinese example was dropped |
| all five (router) | ID never travels alone; never mint an example ID; never invent state | Router `:166–170` |
| all five (router) | First-time setup steps 1–6: namespace check before any question, config first, State-root question only on collision, no chat-language question, Starting point, tracks only when useful, the order, "do not skip decide init", "if no, stop" | Conditional on `installed: false`. Router `:140` says to read `first-run.md § The procedure` and follow its six steps in order; `first-run.md:13–70` carries all six |
| all five (router) | relocate: refuses a dirty tree, confirms every move, never deletes, never moves what it did not put there, sets State root | Conditional on relocate. Router `:155` keeps the first three; `router-subcommands.md:59` and `:68` keep the other two, reached through "Steps:" |
| all five (router) | Packs absent → software-ops, explicit empty → none, release automation not configured by packs | Conditional; `config.md:194–198` and `:253–259`. The lane's `:192` also keeps "pack activation alone does not enable" release support |
| add-task, close-task, dispatch (lane) | Step 0: all six clauses, including the round-1 glossary clause and the split-layout absolute-path rule | `:85`. "The two may differ" dropped (no rule) |
| same (lane) | Steps 1–8 (hook never overrides; one `perry-state` call; never eyeball a number; exit ≠ 0 → say so and never guess; 1–2 days of journal; unlinked → ask, never fuzzy-match; split-layout git log; in-flight; TL;DR with no leading ID; `next` never reordered) | `:86–135`. Only the payload field list, the `--dashboard` mention and the TL;DR examples were dropped |
| same (lane) | Status set; no `done` without evidence (three places); status-line fields; V4 not closable from the lane; tier-1 hard-cap refusal; tool-mediated writes; write the declared structure + `perry-lint`; unarmed safety gate; never write OKR files; User-Unavailable; hooks are additions only | `:62`, `:78`, `:141–184`, `:231`, `:245–266` |
| same (lane) | R1–R5, including "multiple topics → ask which first", "no batched AskUserQuestion", and the list of mechanical work that skips Phase A | Lane `:253` keeps R1–R5 in short form. The dropped details are in `conversational.md:11`, `:20` and `:38`, and the lane still says that page is loaded on "Every chat reply" (`:42`), exactly as the base did |
| same (lane) | KR-attribution hard gate: resolution order, ask with candidate KRs, `unlinked` out of roll-ups, never fuzzy-match or fabricate, aliases handed to `okr` | Lane `:247`, plus `okr-linkage.md:24–49` and `:76–78` (on the add-task bill) |
| add-task | `--summary`/`--deliverable`/`--verification` refused; do not omit both `--kr` and `--unlinked`; `--unlinked` is not a way past; track moves by command only; exactly one prefix; `route --group`; spec `## ` shape "disarms the gate"; journal keeps bullets | `add-task.md:10`, `:23`, `:40`, `:55`, `:74–76`, `:111–113`, `:151`, `:153`. The `diff` shows only history and measurements removed |
| add-task | Input-quality §4 rubric, "What the pass does NOT do", the one rule | `input-quality.md`, verbatim |
| close-task | Gates 1–3, V5 signoff selection, knowledge capture, the Must-Have hand-off refusal, the drop reason verbatim | `task-close.md`, byte-identical to base `subcommands.md:71–208` except the budget-boundary repoint |
| close-task, dispatch | Budget checkpoints (OK/OVER/unknown, safe boundary, resume) | `budget-boundary.md` is on both bills; `task-close.md:122` and `dispatch.md:13` / `:410` cite it |
| dispatch | Pre-flight 1–4.6; the 4h TTL; the reap warning; release on every failure path; "the judgement is yours"; five steps in writing; 4.5 escalation | `dispatch.md` and `dispatch-preflight.md`: the `diff` removes only incident prose and worked cases |
| dispatch | Time-estimation calibration | Conditional. Dispatch reads only `Estimated cycle` → sync/async (`dispatch.md:182`); the lane names `time-estimation.md` (`:31`) |
| plan-phase | Rubrics §1/§2, advisory + override, ≤ 3 issues | `input-quality-rubrics.md`, verbatim, on the plan-phase bill; `goals/SKILL.md:38`/`:192`, `elicitation.md:298` and `phases.md:276` repointed |
| snapshot | — | The set differs only in the router and two one-line repoints (`next.md:337–338`, `host-capabilities.md:71`); `snapshot.md` and `i18n.md` are byte-identical |

**Routine-path rules stranded at 9c1a2b7c: none.** Every other unit in `uniq.txt` is one of three
things: a history or measurement paragraph now kept in a notes page; a row or body belonging to a
different subcommand (cadence, coordinate, handoff and rollover leave the close-task set because
close-task no longer loads `subcommands.md`, and each is still in that file); or a descriptive
sentence with no rule in it.

## Mutations (rule 2), all on `mut/`

Each mutant was applied at a fixed line number. Before each run I cleared `__pycache__` and waited
1.2 s. Each run covered 11 modules and 208 tests; the full logs are `mutations/*.log`.

| Mutant | Result | Reading |
|---|---|---|
| baseline | green | — |
| M1: delete the restored glossary clause (`work/SKILL.md:85`) | **green** | As the result declares: no guard exists, and code does not judge meaning. Only V4 protects it |
| M2: `lane-notes.md:23` `§ … scoped by routes` | **green** | See N1 |
| M3: autopilot wrapped citation `§ Budget\n boundry` | **green** | Same gap round 1 found (C6). Round 2's F2 fix sits inside it |
| M3b: autopilot `budget-boundry.md` (file half) | **green** | See N1 |
| M3c: the same section typo on one line | red (2 guards) | The guards work on the forms they can see |
| M4: `work/SKILL.md` padded to exactly 38,912 | green | — |
| M4b: padded to 38,913 | red (`TestByteBudget`) | Criterion 6 cap+1 |
| M5: lane step 0 `$PERRY_HOME/reference/i18n-x.md` | **green**, also against `test_claims`, `test_ownership`, `test_actor_required`, `test_shipped_vocabulary`, `test_host_support` and `test_bin_surface` | See N1 |
| M6: drop "Never filter," from the pack paragraph | red (`test_startup_routing`) | The pack rule that remains after the pointer moved is guarded |

Every mutated file was restored from `git show 9c1a2b7c:<path>` bytes, and each restore was compared
byte for byte against those bytes. At the end I ran `diff -r` on `mut/` against the untouched
`head/` archive: no differences. `bin/perry-restore-check` was not used, because the copy is not a
git checkout. The worktree's `git status` was clean throughout.

## Findings that are not the verdict's

- **N1: two forms of citation are invisible to both section guards.** I measured this by mutation
  (M2, M3, M3b and M5 green). The two forms are `$PERRY_HOME/…md § X` and a citation wrapped across
  a line. `CITATION_QUOTED`/`CITATION_BARE` (`tests/test_router_budget.py:78–85`) and `POINTER`
  (`tests/test_pointers_resolve.py`) need the path to start with `[\w./-]`, so a `$` prefix never
  resolves to a shipped page. The class predates TASK-470: the base has 56 prefixed and 21 wrapped
  citations, and the head has 58 and 20. The delivery wrote 12 of the head's prefixed ones and moved
  both round-2 citations into the class. I resolved all 72 unguarded citations in the head with the
  guard's own `_resolves` rule (`resolve_unguarded.py`). Every one the delivery wrote resolves. Two
  pre-existing dangles remain: `task-close.md:17` cites `packs/software-ops/architecture.md §
  close-task gate`, which has no such heading (it was `subcommands.md:83` at base, and the gate's
  body is inline, so no rule is lost), and `schema/goals-list-contract.md:217`. Criterion 6 as
  written is met: cap+1 is red, and a broken pointer in the guarded form is red. I am recording this
  rather than widening the round.
- **N2: locked `DESIGN-020 § 5.7` says *"`reference/input-quality.md`, byte for byte"* does not
  change**, and its Non-Goals repeat it, inherited from DESIGN-011. TASK-470 split that file from
  9,389 to 5,286 bytes, plus a new rubrics page. The rubric text moved verbatim (checked with
  `diff`). §1 remains citable through the stub, as the P004-O2-KR1 wording needs. The design
  document was not edited. I read § 5.7 as the scope of DESIGN-020's own implementation, which is
  why TASK-192, -193 and -194 each carry "keep byte-identical", and not as a standing freeze. No
  behaviour changes either way, so I do not charge it. Whether § 5.7 binds beyond DESIGN-020 is the
  user's reading to confirm, not mine.
- F3 from round 1 (`add-task.md:151` describes a removed scan) still stands, and is older than this
  row.

## Suite

`bash tests/run --tier affected --base 359a7be1` on `49c7c570`, whose shipped tree equals
`9c1a2b7c`, was green: 75 of 161 modules selected (74 run; `test_merge_gate` is held back for the
slow tier), 2,446 tests, 59.9 s. The tree guard reported that nothing moved. The log is
`$PERRY_SCRATCH/affected.log`. That is not a green suite. The PMO's full runs on `9c1a2b7c` and
`ecfa2245` (157 modules / 4,434 tests) are cited, not re-run.

=== VERDICT ===
task: TASK-470
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-470-spec.md
checked: round-2 fix (clause verbatim vs base work/SKILL.md:139; Why-pointer target is rationale only; "first" rewording; autopilot repoint; bytes and all five bills re-run in base/r1/head copies, add-task −31.68 %, close-task −30.09 %); criterion 4 re-applied to the whole delivery: 452 unique base-load-set units across snapshot/add-task/close-task/dispatch/plan-phase read one by one, full diffs of every base load-set file, gates/refusals/ordering/host/safety/file-format classes enumerated per command and located on the new path, no stranded routine-path rule; criteria 1 (no bin/schema/viewer change, six test re-points read), 2, 3, 5 (no procedure duplicated by the round-2 move), 6 (cap+1 red, guarded broken pointer red); 9 mutants on a git-archive copy, restores verified against git show bytes and diff -r; affected tier green on 49c7c570
not-checked: full suite (PMO runs cited); a live agent executing any of the five commands; whether perry-lint reports a non-glossary localized heading; the five delivery test re-points not re-mutated this round (read only; round 1 mutated them); dynamic reads (conversational.md, planning.md, config.md) beyond the rules named above; goals/decide routes other than plan-phase; autopilot, handoff, review and delegate paths beyond the budget-boundary citations; whether DESIGN-020 § 5.7 binds beyond its own implementation (N2, user's reading)
proof: work/SKILL.md:85 carries base work/SKILL.md:139's clause byte-identically; task-close.md:5-142 equals base subcommands.md:71-208 except :122; M4b red at TestByteBudget, M3c red at TestSectionCitationsResolve and test_pointers_resolve; unguarded-citation gap (N1) at tests/test_router_budget.py:78-85 predates 359a7be1
=== END VERDICT ===
