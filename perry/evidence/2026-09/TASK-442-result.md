# TASK-442 — result

> Branch: `coding/task-442-next-section` · Base: `bb178072` · Executor: claude-subagent
> Commits: `1791a8c3` step 1 (block, rule file, rule page) · `00fc5a5c` step 2
> (pointers, tests, durations) · `cbd1ea8b` step 3 (contract page and registry) ·
> `1970b6c2` step 4 (the mutation-found test and this file) · `bf9a1d9a` step 5
> (`--help` back under its cap) · `384f27ac` step 6 (§ 7 of this file).
> Round 2: `9a3b7c10` merge of main (`ba11da7a`) · `905fb1bf` command pins ·
> `81b6c43d` the architecture documents · `8c779cca` the round-2 section.
> Round 3: `08929751` the id fix · `eacba06c` the goals lane and the heartbeat
> rule · `9db8d934` `ARCHITECTURE.md` · `58c73b86` the round-3 section.
> Round 4: `99b03e9a` the narrowed §2 rule and the lines the review named ·
> this section.

## Round 4 — the §2 rule is narrowed to the position the next block owns

### R4.1 Why the rule kept failing

§2 said a lane "never reorders, adds or drops a recommendation", without saying
where. Lane documents name a command in roughly thirty places, and most are
legitimate — a step inside a subcommand's own instructions, the remediation a
refusal offers, a bootstrap prompt, a hint in a dashboard row. So each review
round found a different line and the rule could not converge. The user narrowed
it in session on 2026-09-15.

**§2 now says** a lane renders `perry-state --section next` for the next step,
and does not add, drop or reorder a recommendation **in a standup's TL;DR or in
its next-step position**, and it names four kinds of line that sit outside the
rule: procedural steps inside a subcommand, a refusal's remediation, bootstrap
and first-run prompts, and dashboard row hints. First-time setup is the largest
of them and keeps the sentence round 3 added.

**`bin/ARCHITECTURE.md § 1` was not narrowed, because its sentence is not
broader.** It says `perry-state` returns the recommendation "that the lanes
render" and makes no claim about what a lane may otherwise print. Changing it
would add a lane rule to a module document that does not carry one.

### R4.2 The lines the review named

Six examples now describe state, and name no step:

| Line | Now |
|---|---|
| `goals/SKILL.md` TL;DR, KR progress | `TL;DR: Phase #002 commit KRs are at 80%.` |
| `goals/SKILL.md` TL;DR, no phase | `TL;DR: No current phase is set.` |
| `decide/SKILL.md` TL;DR, locked design | `TL;DR: DESIGN-002 is locked and has no implementation tasks yet.` |
| `decide/SKILL.md` TL;DR, open decisions | `TL;DR: DESIGN-003 has 3 open user decisions blocking lock.` |
| `work/SKILL.md` TL;DR, KR progress | `TL;DR: Phase commit KRs are at 80% (#002).` |

`work/SKILL.md`'s line was checked as asked: it is a TL;DR example, so it was
fixed the same way.

The steps those lines used to name are what the next block recommends:
`R-phase-closable` for the KR-progress case (which recommends
`/perry work end-phase-retro`, not `score-phase`), `R-no-phase` for the missing
phase, and `R-design-unhanded` for a locked design.

**The goals bootstrap prompt** keeps its question and now says it is a bootstrap
prompt, outside the next block, citing §2.

### R4.3 Marked, not fixed

Two lines suggest a command after a subcommand finishes:
`goals/SKILL.md`'s `score-phase` row, and `goals/reference/phases.md` step 9.
Both are the proactive closing step `TASK-443` builds. Each now names that task
where it sits, and §7 gains a *Proposed* question saying the closing step
replaces them, rendering `--after score-phase`.

### R4.4 The bound was not swept

The PMO enumerated every other `run` / `suggest` match across the router, the
three lanes and their reference pages, and each falls into one of the four
kinds §2 now names. None was edited, and `git diff` against main shows no change
to any of those files. None of them contradicts the narrowed rule: every one is
a procedural step, a refusal's remediation, a first-run prompt or a template
line, and none writes a standup's TL;DR or its next-step position.

### R4.5 Checks

- Nine modules green alone on the working tree: `test_architecture_rules` (32),
  `test_router_budget` (9), `test_next_section` (43), `test_claims` (31),
  `test_shipped_vocabulary` (52), `test_reference_pages_are_reachable` (6),
  `test_pointers_resolve` (5), `test_diagnose` (158) and
  `test_procedures_call_the_tool` (22).
- Against main, every `ARCHITECTURE.md` hunk is in §2, §4, §7 or §8; §1, §3, §5
  and §6 are byte-identical. It is 400 lines, under its 500-line cap, and
  `bin/ARCHITECTURE.md` is unchanged at 205.
- `SKILL.md` is untouched: 20,457 bytes, as on main.
- Lane sizes: `goals/SKILL.md` 21,385, `work/SKILL.md` 36,035,
  `decide/SKILL.md` 23,633 — each under its budget.
- No id is cited that does not exist on the branch. Nothing in `bin/`, the rule
  file or the tests changed this round.

The full suite runs after this section is committed, on that commit, and its
result is reported in the round-4 RESULT block rather than here.

## Round 3 — the second review FAIL (§2 lanes) and the `test_diagnose` red

### R3.1 The `test_diagnose` red was this branch's

`tests/test_diagnose.py TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
reported five dangling ids, all in this file:

- **A design id and an ask id** were cited in the round-2 section. Neither
  exists on main or on this branch; both were uncommitted in another checkout. The line now says a separate KR design has
  already decided the KR-direction question, without the ids.
- **The three new open questions** were cited by their ids. `ARCHITECTURE.md`
  says an open question is referred to by its section, because that id prefix
  is not a citation family, so the line now says §7.

My round-2 suite ran on `81b6c43d`, before the result-file commit, which is how
the red was missed. On this branch, the open-question ids now appear only in
their own §7 headings, the form the three older questions already take. No
other file cites them. This section names the questions by section for the same
reason.

### R3.2 The review's items

- **(a)** `goals/SKILL.md`'s no-phase line no longer suggests
  `/okr plan-phase`. It says the next block recommends starting a phase
  (`R-no-phase`).
- **(b)** The two soft prompts are described as rules of
  `perry-state --section next`, which the lane does not evaluate:
  - KR-progress is `R-phase-closable`, recommending `/perry work end-phase-retro`
    and not `score-phase`;
  - the heartbeat is `R-phase-heartbeat`.
- **(c) The heartbeat was declared with its fact unknown, not computed.**
  - **Why unknown:** `perry-state` computes no date for the last phase snapshot.
    The payload has no snapshot field, and `viewer/parsers.py` has no snapshot
    reader, so computing one would be a new read of state (NN-1).
  - **The rule:** `R-phase-heartbeat` (spine `project`, lane `goals`,
    `/perry goals snapshot`, `after: []`) with threshold `phase_heartbeat_days`
    set to 14. The schema declares no such threshold. The project's own
    setting is not in the payload, so it is not read.
  - **Placement:** after `R-review-due`, because DESIGN-020's order has no
    place for it.
  - **Where it is recorded:** `reference/next.md` explains it, and the fact is
    listed among the always-unknown ones. `ARCHITECTURE.md` §7 asks, as
    *Proposed*, whether the heartbeat survives, and the §8 TASK-442 entry
    records the choice.
  - **Test:** `test_the_phase_heartbeat_is_declared_and_its_fact_is_unknown`
    shows the fact unknown on an active phase and absent without one. With the
    fact patched known, the rule fires at 14 days with that command, and stays
    quiet at 13. The rule-file bound test pins its place after `R-review-due`.
- **(d)** `ARCHITECTURE.md § 2` (lanes) says first-time setup sits outside the
  next block: `R-setup` recommends only `/perry`, and setup's recommended order
  is the router's. `SKILL.md` is untouched, 20,457 bytes on both main and this
  branch.

**Constraints.** Against main, every `ARCHITECTURE.md` hunk falls in §2, §4, §7
or §8, so §1, §3, §5 and §6 are byte-identical. The document is 379 lines, under
its cap of 500. `goals/SKILL.md` is 21,235 bytes, under 22,528. No new §8 entry
claims a confirmation. On this repository, `perry-state --section next` now
declares 18 rules with no rule errors and lists `phase.days_since_snapshot` as
unknown.

### R3.3 Mutations and modules, before this commit

Every mutation ran on a scratch copy, each against a green unmutated control, with 43 tests:

| Mutation | Result | Named red |
|---|---|---|
| M1–M9, M10 (the round-2 `R-no-okr` command) | all red | as recorded in rounds 1 and 2 |
| **M12** the heartbeat fact made known (99 days) | **red, 1/43** | `test_the_phase_heartbeat_is_declared_and_its_fact_is_unknown` |
| **M13** delete `R-phase-heartbeat` | **red, 3/43** | the heartbeat test, `test_every_rule_id_is_explained_on_the_page_and_nothing_else_is`, `test_the_bound_three_overlays_ten_rules_and_the_replacements` |
| M11 `R-asks-waiting`'s command changed | GREEN | the round-2 finding, unchanged: a command is pinned only where a fixture makes that rule primary |

Nine modules were run alone on the working tree, and all are green:

- `test_next_section`, 43 tests;
- `test_diagnose`, 158;
- `test_architecture_rules`, 32;
- `test_router_budget`, 9;
- `test_reference_pages_are_reachable`, 6;
- `test_shipped_vocabulary`, 52;
- `test_pointers_resolve`, 5;
- `test_contract_key_parity`, 45;
- `test_semantics_on_every_payload`, 14.

The full suite runs after this section is committed, on that commit, and its
result is reported in the round-3 RESULT block rather than here.

## Round 2 — the architecture review FAIL and the PMO's finding

Sections 0–7 below record round 1 and are unchanged.

### R2.1 The ownership move is recorded (the FAIL)

The review FAILed at `ARCHITECTURE.md § 2`. `bin/` still "doesn't own what to
do next", and the lanes still owned it, while this branch makes
`perry-state --section next` decide and the lanes render.

Descriptive lines only (NN-6), in `81b6c43d`, each citing
`perry/design/DESIGN-020-guided-planning.md § 9`, the 2026-09-15 entry,
confirmed by the user in session:

- **§2 `bin/`** owns the next-step recommendation, evaluated from the rule table
  `reference/next-rules.json`. It does not own the rules or the procedure around
  them.
- **§2 lanes** render the recommendation and never reorder, add or drop one. The
  recommendation is no longer theirs to choose.
- **`bin/ARCHITECTURE.md § 1`** says the same, and its §2 `perry-state` node
  names the next block.

The same edit fixed the other lines this branch had made stale:

- **§2 `schema/`**: eight contract pages.
- **§2 `reference/`**: it holds the rule table `bin/` evaluates.
- **§4 read path**: a `--section next --lane / --after` edge and one sentence
  on the narrowed block.
- **§7**: three questions, each marked *Proposed*: `--compact` with
  `--section next` (for `TASK-443`), the contract registry and non-`/list`
  families, and a section that is not the payload's key. The KR-direction
  question was not added: a separate KR design has already decided it.
- **§8**: one entry in each document. Neither contains "User-confirmed".

**§6 is not edited.** The patch script checked this with
`tests/test_architecture_rules.py § decided_text`: §1, §3's Forbidden lines and
§6 read identically before and after, and a second pass that only rewrapped
three long citation lines changed no word. `test_architecture_rules` is green
(32 tests); S7 skips, as it does on main, because no confirmed hash is
recorded yet. The documents are 364 and 205 lines (`wc -l`), against caps of 500 and 600.

### R2.2 The recommended command is pinned (the PMO's finding)

`TestEachFixtureOffersItsCommand` (`905fb1bf`) asserts each fixture's primary
command beside its rule, both in `build_next` and in `--section next`'s output:

| Fixture | Command |
|---|---|
| installed with no OKR | `/perry goals init` |
| OKR with no phase | `/perry goals plan-phase <slug>` |
| active phase, week unknown | `/perry work friday-review` |
| closable phase | `/perry work end-phase-retro` |
| queue track | `/perry work triage` |

All mutations were re-run on scratch copies, each against a green unmutated
control:

| Mutation | Result |
|---|---|
| **M10**, the PMO's: `R-no-okr` offers `/perry work triage` | **red, 2/42**: `test_the_primary_offers_the_command_written_for_each_fixture`, `test_the_command_reaches_the_published_payload_unchanged` |
| M1–M9 | still red, each on its named tests |
| **M11**, control: `R-asks-waiting` offers `/perry work triage` | **GREEN — a finding** |

M11 shows a command is pinned only where a fixture makes that rule primary. The
command of R-recovery, R-interrupted, R-draft-waiting, R-setup, R-asks-waiting,
R-handoff-stale, R-design-unhanded, R-board-over-cap, R-wip-over-limit and the
two commitment rules can change with this suite green. Closing that means a
fixture per rule, or a second copy of the rule table's commands in a test. It
was not done, and no row is opened for it.

### R2.3 Merge of main

`git merge main` (`ba11da7a`) conflicted in `tests/durations.json` only, where
both sides appended a `sources` block. Both are kept. A script checked that
every line and key of either parent survives and that the file parses: 145
modules, 17 sources. `test_durations_provenance` is green, with 145 recorded and
145 on disk.

### R2.4 Full suite on `81b6c43d`

`bash tests/run`, PERRY_PROJECT and PERRY_HOME unset: **142 modules · 4008 tests ·
1 module red · 8 tests failed (4000 / 4008).**

- **The only red:** `test_md_store`, 8 of 76. Re-run alone, the same 8 tests
  fail, the expected base reds that TASK-459 fixes.
- **Now green:** `test_okr_krs_render`, as on main.
- **Other steps:** 1, 3 and 4 pass, and the tree guard reports nothing moved.
- **Nothing new red** beyond `test_md_store`'s 8.

## 0. Base check

- Worktree HEAD at dispatch was `0b5bf99e`.
  `git merge-base --is-ancestor HEAD bb178072` returned 0 and the reverse returned
  1, so HEAD was a strict ancestor. The tree was clean, so
  `git merge --ff-only bb178072` fast-forwarded it, and the branch was created at
  `bb178072`.
- Read in full before changing anything: `ARCHITECTURE.md`, `bin/ARCHITECTURE.md`,
  `perry/evidence/2026-09/TASK-442-spec.md`, `perry/design/DESIGN-020-guided-planning.md`
  (the whole document, including § 5.1–5.4, § 6 phase A and the § 9 entry of
  2026-09-15), and `USER-934` in `perry/asks.jsonl`.

## 1. Baseline at `bb178072`, measured in this worktree

`bash tests/run`, with PERRY_PROJECT and PERRY_HOME unset: **140 modules ·
3934 tests · 2 modules red · 10 tests failed.** Each red module was re-run alone
with `python3 tests/parallel <module>` and failed the same way:

| Module | Alone | What fails |
|---|---|---|
| `test_md_store` | 9 of 76 red | objective ids minted 14 ≠ 10; the store holds 0 KRs against 13 KR lines in `perry/OKR.md` |
| `test_okr_krs_render` | 1 of 40 red | `perry/OKR.md` carries 13 KR table rows (`\| O1-KR1 \| carried → v4 …`) |

Both read this repository's own `perry/OKR.md` / `okr.jsonl`, which the base
commits rewrote to OKR v4 (`15369956`, `bb178072`). Neither touches `perry-state`.

## 2. What was built

1. **`perry-state --section next [--after <subcommand>] [--lane goals|work|decide]`**
   (`bin/perry-state § build_next`). It emits `contract: perry-next/1.0`,
   `semantics: []`, `position[]`, `primary`, `alternates[]` (at most 2, each a
   different command), `unknown[]` and `conformance`. `next` is a key of the full
   `--json` payload on both the installed and the uninstalled branch.
   **`COMPACT` is untouched**, and a test asserts `--compact` carries no `next`.
   `--after` / `--lane` without `--section next`, or a lane outside the three,
   exit 2.
2. **Facts** (`next_facts`) come only from the payload `build()` already returns,
   plus the clock. `today` is a parameter, so tests fix it. New facts:
   `phase.kr_progress.{commit_total,measured,met,unmeasured,met_ratio}`,
   `week.iso`, `today.date`, `today.weekday`. A few facts are derived from values
   the payload already carries:
   - `history.weeks_since_weekly`, `history.*_label`;
   - `board.over_cap_by`;
   - `project.spines`, from `tracks[].mode`;
   - `queue.sla_breaches` and `pipeline.wip_breaches`, from each track's
     `sla_check` / `sla_breaches` / `wip_breaches`.
3. **`reference/next-rules.json`**: 3 overlays, the ten § 5.3 rules in table
   order, and 4 replacements. The replacements are `R-sla-breach` and
   `R-queue-commitment-due` (spine `queue`), and `R-wip-over-limit` and
   `R-pipeline-commitment-due` (spine `pipeline`). The last element is
   `R-board-over-cap`. Each rule has `id`, `when`, `spine`, `lane`, `command`,
   `reason` and `after[]`.
   - Predicates are typed only: fact, operator from `eq ne lt le gt ge in exists
     nonempty`, and a literal or `{"threshold": name}`, combined with `all` /
     `any`.
   - Evaluation is three-valued. A predicate over an unknown fact never fires, and
     the fact goes into `unknown[]` with the ids of the rules it blocked.
   - `schema/state-schema.json § thresholds` declares none of the four thresholds,
     so all four are declared in the rule file with a note:
     `phase_closable_ratio` 0.8, `asks_waiting_days` 5, `weekly_late_weeks` 2,
     `handoff_stale_days` 7. The resolver still consults the schema first, and
     `conformance.thresholds[].source` says which source each came from.
   - A malformed rule is skipped and named in `conformance.rule_errors`.
4. **`reference/next.md`** has one `### <rule id>` per rule (a test holds the two
   lists equal), `§ Rendering`, and `§ What the agent may and may not do`. The
   latter carries the § 9 rule: never reorder, add or drop a recommendation; at
   most one line, marked as the agent's own note. The closing step is not built
   (`TASK-443`).
5. **Pointers.** `reference/snapshot.md` step 5 and the step-5/7 lines of
   `goals/SKILL.md`, `work/SKILL.md` and `decide/SKILL.md` now run
   `perry-state --section next` (with `--lane` in the lanes) and render it per
   `reference/next.md § Rendering`. The router's step-5 phrase is
   `**5** render \`next\` per \`reference/next.md\``. The bytes it adds are paid for
   on the same line (`read the lane file in full first` → `read it in full
   first`): **`SKILL.md` is 20,457 bytes before and after, net +0.**
6. **The contract.** `schema/next-contract.md` has 37 keys documented and 37
   emitted, with 0 missing in either direction, and the witness project makes
   nothing further observable. `schema/README.md` lists it as the eighth read
   contract.
7. **Tests.** `tests/test_next_section.py` holds 40 tests. They cover:
   - the five fixtures, each with its primary written in the test;
   - delete-a-rule, with its control;
   - unknown-never-fires, and three-valued `all` / `any`;
   - overlay order, with its control;
   - determinism, and the block surviving deletion of the project (NN-1);
   - shape and flags;
   - the rule file's bound and its parity with the page;
   - the KR-progress edge cases;
   - review-due and WIP;
   - the five pointer sites and the router byte cap.

   `tests/durations.json` gains one entry and one source block; parsed against
   HEAD, nothing else changed.

## 3. `perry-state --section next` on this repository (2026-09-15, a Tuesday)

Shortened to its decisions. The full block also carries `semantics: []`, the four
thresholds and `rule_errors: []`.

```json
"position": [
  {"step": "goals",  "state": "done",    "label": "OKR v4: 2026-09-15"},
  {"step": "phase",  "state": "done",    "label": "Phase 004, day 1"},
  {"step": "week",   "state": "unknown", "label": "2026-W38 plan: cannot tell"},
  {"step": "review", "state": "late",    "label": "last weekly 2026-W35"}
],
"primary": {"rule": "R-sla-breach", "lane": "work", "command": "/perry work triage",
            "reason": "5 queue item(s) are past their SLA, the longest-waiting being TASK-270",
            "facts": ["installed=true", "queue.sla_breaches=5"]},
"alternates": [
  {"rule": "R-review-due", "command": "/perry work friday-review",
   "reason": "today is Tuesday and the last weekly report is 2026-W35"},
  {"rule": "R-handoff-stale", "command": "/perry work handoff",
   "reason": "project state changed today and the last handoff is 2026-08-30"}
],
"unknown": [
  {"fact": "drafts.drafted", "reason": "plan drafts have no source until TASK-444 builds them", "rules": ["R-draft-waiting"]},
  {"fact": "phase.kr_progress.met_ratio", "reason": "12 of 12 commit key results in phase 004 have no current value or no target", "rules": ["R-phase-closable"]},
  {"fact": "week.planned", "reason": "week plans have no source until TASK-444 records a finalized week", "rules": ["R-week-unplanned"]},
  {"fact": "commitments.due", "reason": "perry-state does not compute which commitments are due", "rules": ["R-queue-commitment-due"]}
],
"conformance": {"rules_declared": 17, "rules_eligible": 15, "rules_fired": 4,
                "filters": {"after": "", "lane": ""}, "today": "2026-09-15"}
```

`R-design-unhanded` also fires, for DESIGN-014 (10 locked designs with no
implementation task). It is the fourth rule to fire and falls outside the two
alternates. `--lane decide` shows it as the primary.

For the `[user-verify]` question on reasons, these are the three sentences above.

## 4. Facts emitted as unknown (NN-1)

**Always unknown**, because `perry-state` computes no source for them. None of
them is inferred from another file.

- `week.planned`: no source until `TASK-444`.
- `drafts.drafted`: no source until `TASK-444`.
- `commitments.due`: `perry-state` computes no due date for commitments. So
  `R-queue-commitment-due` and `R-pipeline-commitment-due` are declared and never
  fire.

**Unknown on a given project**, derived from values already in the payload:

- `phase.kr_progress.*`: the linkage store is unreadable, or describes another
  phase.
- `phase.kr_progress.met_ratio`: the phase has no commit KR, or any commit KR
  lacks a `current` or a `target`.
- `history.weeks_since_weekly`: `latest_weekly` is neither an ISO week nor a date.
- `user_input_queue.oldest_idle_days`: the oldest ask carries no date.
- `queue.sla_breaches`: no queue track has a readable SLA.
- `pipeline.wip_breaches`: no pipeline track declares a WIP limit.

## 5. Mutations

Every mutation ran on its own scratch copy of the tree
(`$PERRY_SCRATCH/mutation-*`, leaving out `.git`, `.claude` and `perry/`). The
copy was removed afterwards, and the unmutated copy was run green first as the
control. The worktree's `bin/perry-state`, `reference/next-rules.json` and
`SKILL.md` were checked against HEAD afterwards: `git diff --stat HEAD` was empty.

| Mutation | Result | Named red |
|---|---|---|
| M1 delete `R-sla-breach` from the rule file | red, 6/39 | fixture primary (queue), delete-a-rule, queue case, bound, page parity |
| M1b delete `R-phase-closable` | red, 7/39 | fixture primary (closable), delete-a-rule, closable facts, met_ratio case, bound, page parity |
| M2 a predicate over an unknown fact is compared anyway | red, 6/39 | unknown-never-fires, three answers, week plan unknown, met_ratio unknown, WIP unknown, unreadable stamp |
| M3 overlays moved below the project rules | red, 4/39 | recovery outranks missing OKR, overlays survive `--lane`, bound, page parity |
| M4 a target of 0 is met by `>=` | red, 1/39 | `test_a_target_of_zero_is_met_only_at_zero` |
| **M5 an alternate may repeat a command** | **GREEN, a finding** | no fixture fired two rules with one command |
| M6 `--lane` also drops the overlays | red, 1/39 | `test_the_overlays_survive_a_lane_filter` |
| M7 `all` ignores an unknown part | red, 18/39 | the fixture primaries, the unknown cases, overlay order |
| M8 `met_ratio` computed while KRs are unmeasured | red, 9/11 classes | a crash, not a pointed assertion: `ZeroDivisionError` in `setUpClass`, when a phase's commit KRs are all unmeasured |
| M9 the router pointer reverted | red, 1/39 | `test_the_router_points_at_the_page_without_growing` |

**M5, re-run after its test was added:** the unmutated copy is green (40 tests),
and M5 is **red, 1/40**:
`TestTheShape.test_an_alternate_never_repeats_a_command_already_offered`. That
test fires five rules. Two of them repeat a command already offered, and it
requires both repeats to be skipped.

## 6. Deviations and findings — for the PMO and the reviewer

1. **Four files outside the spec's Files in scope were edited** (commit
   `cbd1ea8b`, kept separate so it can be judged on its own). The spec's page
   `schema/next-contract.md` with contract `perry-next/1.0` reddened the two tests
   that hard-wire every contract as a `perry-<x>/list` family with a
   `<x>-list-contract.md` page:
   - `tests/test_contract_key_parity.py`: the README-row predicate is now "names a
     `-contract.md` spec" instead of "contains `/list`". The version-pin regex also
     catches `perry-x/1.0`, so the change widens the guard rather than loosening
     it.
   - `tests/test_semantics_on_every_payload.py`: `perry-next` is added to
     `PAYLOADS` and `EMPTY_TODAY`, and a non-list family maps to `<stem>-contract.md`.
   - `tests/fixtures/contract-key-parity.json`: only the new entry is added, and
     `contract_files_discovered` goes 7 → 8. `--record` was not used, because it
     measures the live checkout while the test measures the frozen copy.
   - `tests/fixtures/shipped-semantics.json`: `"perry-next": []`.
2. **`tests/contract_key_parity.py § CONTRACT_ID` matches only three-segment ids**
   (`perry-x/list/1.0`). The baseline therefore keys the new page by its file path
   (`schema/next-contract.md`, `contract: ""`). It was left unedited because it is
   out of scope.
3. **Recommended commands use the direct entrances, not `/perry plan`.**
   `/perry plan` is DESIGN-020 phase F and does not exist, so `R-no-okr`,
   `R-no-phase` and `R-week-unplanned` recommend `/perry goals init`,
   `/perry goals plan-phase <slug>` and `/perry goals plan-week`.
   `R-draft-waiting` keeps `/perry plan`, because it cannot fire until `TASK-444`.
4. **§ 5.4's closing step calls `--section next --after X --compact`, and
   `--compact` with `--section` is refused** (unchanged, per "must not change
   `--compact`"). `TASK-443` has to choose `--section next --after X` or ask for
   the refusal to be lifted.
5. **`unknown[]` entries are objects `{fact, reason, rules}`**, not the strings of
   the § 5.4 sketch, so a renderer can key off `fact`.
6. **"Met" needs a direction no KR record declares.** `current >= target`, except
   that a target of `0` is met only at `0`. Without that exception every
   count-to-zero KR reads as met, which is the failure `bin/lib §
   kr_progress_provenance` describes. The exception is a convention, not a typed
   fact. See the §7 question below.
7. **DESIGN's `spine` is matched against `project.config.tracks[].mode`**, whose
   values are project/pipeline/queue/inquiry. The payload's own `tracks[].spine`
   (`phase/`, `standing`) is DESIGN-008's other axis. Inquiry tracks get no
   replacement rules, because DESIGN-020 names none (Bound remainder).
8. **"A state-changing command ran today"** (`R-handoff-stale`) is read as
   `history.latest_journal_days == 0`, since every mutating command writes a
   journal line (ARCHITECTURE.md § 4).
9. **Suggestions with no rule behind them were dropped from the lanes**, because
   the sites are now pointers and § 9 forbids adding a recommendation:
   - goals: the heartbeat snapshot prompt and the scope-reduction trigger;
   - work: unattributed tasks, board rows without events, un-digested `inputs/`,
     stale knowledge digests, and in-progress rows without evidence;
   - decide: a design `in_review` for N days, and open user decisions.

   `goals/SKILL.md` lines 42–43 still describe the KR-progress and heartbeat
   prompts. They are not step-5 lines and are out of scope. None of this is
   opened as a row.

## 7. Full suite on the final commit

**First full run, on `1970b6c2`:** 141 modules · 3974 tests · 3 modules red ·
11 tests failed. One red was new and belonged to this change:
`test_bin_surface.TestHelpIsUsageFirstAndSmall.test_the_whole_tool_help_is_a_page_not_a_paper`
failed for `perry-state`, because `--help` was 3,240 bytes against its 3,000-byte
cap. Re-run alone, it failed the same way. Step 5 (`bf9a1d9a`) removed the
docstring paragraph that restated the generated usage block and shortened the two
flag summaries. `--help` is now 2,924 bytes. `test_bin_surface` (59),
`test_next_section` (40) and `test_shipped_vocabulary` (52) are each green when
run alone.

**Final run, on `bf9a1d9a`**, with `bash tests/run` and PERRY_PROJECT / PERRY_HOME
unset: **141 modules · 3974 tests · 2 modules red · 10 tests failed
(3964 / 3974 pass).**

- **Failing tests:** the failing test ids are **identical to the baseline's**,
  compared as sorted `FAIL` lines from the two logs with `diff`: the 9 in
  `test_md_store` and the 1 in `test_okr_krs_render` (§ 1).
- **Nothing new:** there is no red beyond the base measurement.
- **Other steps:** step 1 (templates versus the schema) is clean; step 3 (every
  `bin/` script compiles and answers `--help`) and step 4 (sample projects lint)
  pass; step 0, the tree guard, reports that nothing under the worktree moved.

Against the base, the suite gained one module (`test_next_section`) and 40
tests.
