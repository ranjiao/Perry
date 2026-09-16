# DESIGN-022: A KR is measured through declared checks, and only a command measures them

> Status: locked
> Date: 2026-09-15 · Locked: 2026-09-16
> Author: Perry maintainer   · Implementation owner: TBD
> Linked OKR: O2-KR3 (a deterministic writer per lane) / P004-O2-KR2
> Supersedes: —   · Superseded by: —
> Sign-off: User Decisions 1–4 answered by Ran Jiao in session on 2026-09-15, all at the recommended option; recorded as `USER-937`. Decision 4 authorizes the `check` and `measurement` kinds on `linkage.jsonl` in `schema/state-schema.json` and nothing else.
> Revisits: `schema/state-schema.json § stores.declared[linkage.jsonl]`, `schema/goals-list-contract.md` (the `2.0` removal of `progress`), `bin/lib/__init__.py § kr_progress_provenance` and `§ COMPUTED_KR_METRICS`, `bin/perry-goals`, `bin/perry_store.py` (the two ordering rules), `bin/perry-state § phase.kr_progress`, `goals/reference/linkage.md`, `work/reference/subcommands.md § friday-review`, `goals/reference/phases.md § score-phase`, `goals/SKILL.md § Cap phase KRs at 4 per Objective`, `DESIGN-020 § 5.2–5.3`, `perry/phase/004-guided.md § KR-progress trigger`

## 1. Problem

**Perry cannot say how far along any KR is, and three rules that depend on it
therefore never fire.**

### 1.1 The numbers, measured 2026-09-15 from `perry/linkage.jsonl` and `perry/okr.jsonl`

| Level | KRs | with `target` | with `current` | with `asserted_at` |
|---|---|---|---|---|
| Phases 001–003 | 22 | 20 | 18 | 0 |
| Phase 004 | 12 | 7 | **0** | 0 |
| OKR v4 overall | 14 | — (no field) | — (no field) | — |

Every `current` in phases 001–003 was typed in by hand, the crossing `USER-912`
records, and none carries the date it was arrived at. Phase 004's records were
appended without one, correctly, because nothing may write one:

- `goals/reference/linkage.md § Not invent a number` forbids a typed `current`.
  `bin/perry-goals link` only **appends** records, and no append sets a number
  on a KR that already exists.
- When the phase 003 mid-phase review re-measured two KRs on 2026-09-08, the
  numbers went to `evidence/2026-09/2026-09-08-kr-remeasurement.md` instead of
  the register (`TASK-231`).
- `bin/lib § COMPUTED_KR_METRICS` recomputes a KR's metric from Perry's own
  stores on every read. It is the one legitimate source, and it names one KR:
  `P003-O3-KR2`.

### 1.2 What waits on it

1. **`DESIGN-020 § 5.3` rule 4, `R-phase-closable`.** It fires on
   `phase.kr_progress.met / measured ≥ 0.8`. With 0 measured it can never fire.
   `TASK-442` (merged `fb64e30b`) computes it from `current` and `target` alone:
   `bin/perry-state § next_kr_progress` counts a KR met when `current >= target`,
   except that a target of `0` is met only at `0`. That rescues drive-to-zero
   KRs and misreads **every non-zero ceiling**: `P004-O3-KR3` aims to take a
   length from 1,702 down to ≤ 400, and `1702 >= 400` reads as met today.
2. **`phase/004-guided.md § KR-progress trigger`.** At phase day 21
   (2026-10-06), fewer than half of the commit KRs carrying a measured `current`
   collapses Objective 3. Today it would collapse, whatever the work had done.
3. **`score-phase` step 1** pre-selects each KR's status "based on observed
   metric vs target". There is no observed metric, so the agent reads prose.

### 1.3 Why a `current` field is not enough

- **Direction is unknown.** `perry-goals/list/2.0` removed `progress` on
  2026-08-17 because Perry cannot tell which way a KR runs, and a ceiling drawn
  as a bar reports a risk budget as partly achieved. `P004-O4-KR1`'s "total ≤
  1,054 module-seconds" is exactly that: its baseline is its target.
- **There is no baseline.** `TASK-416`: a hand-measured `current: 0` and a
  template `0` nobody touched are byte-identical. A count that went from four
  to one is three quarters done only if the four is recorded, and today it
  lives in `metric` prose.
- **Six of phase 004's twelve KRs carry more than one number.** Examples:
  `P004-O4-KR1` (median ≤ 60 s, full suite once per merge, total ≤ 1,054 s) and
  `P004-O3-KR2` (100% recorded, median ask ≤ 600 characters). Splitting them
  would give Objective 3 five KRs and Objective 4 six, against
  `goals/SKILL.md`'s cap of 4 per Objective.
- **Overall KRs do not roll up.** Of v4's 11 commit KRs, 4 are restated
  exactly by a phase 004 KR (`O1-KR2`, `O1-KR3`, `O2-KR2`, `O3-KR1`). 5 are
  served only in part (e.g. `O3-KR2` adds "100% of boundary merges reviewed").
  2 have no phase KR at all (`O4-KR1`, `O4-KR2`).
- **Overall KR ids are not unique.** `O1-KR1` exists in v2, v3 and v4 of
  `okr.jsonl`, so a number keyed by the bare id would be ambiguous.
- **The store appends.** Setting `current` on an existing `kr` record is a
  rewrite, and the store's one rewrite today is the retraction of an
  `unlinked` record.

## 2. Goals

1. Every commit KR at both levels can declare one or more typed **checks**,
   each with `direction`, `target` and, where the direction needs one,
   `baseline`. A check with no measurement reports *unmeasured*, never `0`.
2. A measured value enters the store only as an appended **measurement**
   record written by a command, carrying `asserted_at` and its source: a
   registered computation, or an evidence file that exists.
3. `met` and, where the direction allows one, a fraction are **derived at read
   time** from typed fields. Neither is stored and no agent judges them
   (`ADR-007`, `NN-4`).
4. `R-phase-closable` and phase 004's day-21 trigger are computable from the
   payload on three fixtures: 0 KRs measured, half measured, all met.
5. A check measured longer ago than a threshold is reported as due, and
   `/perry` recommends measuring it (`DESIGN-020` rule table).
6. `TASK-231` and `TASK-416` close as consequences of this design, and
   `TASK-264`'s writer is the one that declares checks.
7. The per-Objective KR cap is untouched: no KR is split to fit this design.

## 3. Non-Goals

- **No stored progress, score or Objective percentage.** Everything derived is
  derived on read. `score-phase` still asks the user per KR, now with a typed
  pre-selection.
- **No agent decides whether a KR is met.** The comparison is typed or absent.
- **No shell command stored in a store and executed from it.** A check measured
  by code is registered in `COMPUTED_KR_METRICS`, which is reviewed code, not
  data.
- **No rewrite of any existing record.** Phases 001–003 keep their `target` /
  `current` as written. They are published as today and report no position.
- **No change to `okr.jsonl`**, and none to `objective`, `edge`, `unlinked`,
  `project` or `agent` records.
- **No history view, trend or chart.** Measurements accumulate as records; a
  reader for them as a series waits for a consumer (§ 8).

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Does Perry publish a KR's position? | Met + fraction by declared direction (Recommended) / Met only, no fraction / Numbers only, as today | Met + fraction by declared direction | 2026-09-15 |
| 2 | KRs carrying several numbers | Typed checks under one KR (Recommended) / Split within the 4-per-Objective cap / One primary number, rest prose | Typed checks under one KR | 2026-09-15 |
| 3 | Overall v4 KRs | Own checks and measurements (Recommended) / Roll up from linked phase KRs | Own checks and measurements | 2026-09-15 |
| 4 | Change `state-schema.json` | Authorize two new record kinds (Recommended) / Not now; design waits | Authorize two new record kinds | 2026-09-15 |

- **1.** Reverses `perry-goals/list/2.0`'s removal of `progress`, but only
  where the project has declared the direction the removal said Perry cannot
  know. "Met only" still unblocks `R-phase-closable` and the day-21 trigger,
  and draws no bars. "Numbers only" leaves both rules unfireable.
- **2.** Checks keep phase 004 at 12 KRs and every condition typed. Splitting
  within the cap means Objective 4 drops two of its seven numbers and
  Objective 3 drops one. A primary number keeps the others as unmeasured prose,
  which is the gap this design exists to close.
- **3.** Roll-up measures 4 of 11 commit KRs exactly; the other 7 stay
  unmeasured until their deadlines (latest 2026-11-17). Own checks cost nothing
  beyond decision 4, because they live in the same records (§ 5.1).
- **4.** `state-schema.json` is on `.perry/hook.md § High-stakes operations`
  (the claim surface). This row is that authorization, scoped to the `check`
  and `measurement` kinds in § 5.1 on `linkage.jsonl`. No existing field or
  claim changes.

## 5. Architecture

### 5.1 Two appended record kinds on `linkage.jsonl` (decisions 2, 3, 4)

Numbers about a KR live in `linkage.jsonl` whatever the KR's level.
`okr.jsonl` keeps the KR's words. Both kinds are appended and never rewritten.

```json
{"kind": "check", "kr": "P004-O4-KR1", "okr_version": "", "id": "total",
 "label": "suite total, module-seconds", "direction": "at_most",
 "target": 1054, "baseline": null, "declared_at": "…", "actor": "goals"}

{"kind": "measurement", "kr": "P004-O4-KR1", "okr_version": "", "check": "total",
 "value": 1054.3, "asserted_at": "…", "evidence": "evidence/2026-09/….md",
 "computed": false, "actor": "goals"}
```

| Field | Rule |
|---|---|
| `kr` + `okr_version` | the KR. `okr_version` is `""` for a phase KR (its id is unique) and the version label for an overall KR, because `O1-KR1` exists in v2, v3 and v4 |
| `id` / `check` | a slug, unique within the KR |
| `direction` | `increase` · `decrease` · `at_least` · `at_most` · `done` |
| `baseline` | number; required for `increase` / `decrease`, null otherwise |
| `target` | number; `done` targets 1 |
| `value` | number |
| `evidence` | a path under `evidence/`; required unless `computed` |
| `computed` | true only when written by a `COMPUTED_KR_METRICS` function's recorder |

A re-declared check (same `kr`, `okr_version` and `id`) supersedes the earlier
one from its `declared_at`. The current value of a check is its measurement
with the latest `asserted_at`. Both are ordering rules over typed fields, stated
once in `perry_store` and read by every reader.

`increase` / `decrease` move from a baseline toward a target and may draw a
fraction. `at_least` / `at_most` are limits: met or not, never a fraction, which
is the ceiling `2.0` refused to draw. `done` is a milestone with value 0 or 1.

### 5.2 Derived on read, never stored (decision 1)

One function beside `kr_progress_provenance` in `bin/lib`, called by every
reader:

```
per check
  state     unmeasured   no measurement
            due          latest asserted_at older than thresholds.kr_measure_due_days (7),
                         or a linked task moved after it (current_staleness)
            measured     otherwise
  met       increase, at_least: value >= target      decrease, at_most: value <= target
            done: value == 1                          null when unmeasured
  fraction  increase/decrease only: clamp((value - baseline) / (target - baseline), 0, 1);
            null otherwise; the ends reserved as in contract 3.1

per KR (over its checks; a KR with no checks reports state "undeclared")
  state     worst of its checks: undeclared < unmeasured < due < measured
  met       true when every check is met; null when any is unmeasured
  fraction  the check's fraction when the KR has exactly one check; null otherwise

per Objective
  commit KRs measured / total and met / total; stretch KRs excluded; no mean
```

`perry-goals/list` gains `checks[]`, `state`, `met` and `fraction` as keys, a
minor version; `target` and `current` keep their meaning for records that carry
them. `perry-state § phase.kr_progress` counts `state` and `met` from the same
function, so `DESIGN-020`'s rule and the day-21 trigger read one answer. Under
decision 1's "met only" option, `fraction` is omitted and nothing else changes.

### 5.3 The writer (goals lane, inside `TASK-264`)

```
perry-goals check <KR-ID> [--okr-version V] --id S --direction D --target N [--baseline N] --label "…"
perry-goals measure <KR-ID> [--okr-version V] --check S --value N --evidence <path>
```

- `check` belongs with `TASK-264`'s add, restate and withdraw verbs, and refuses
  inconsistent declarations: `increase` with `target <= baseline`, `decrease`
  with `target >= baseline`, `done` with a target other than 1, and a baseline
  on a limit.
- `measure` appends one `measurement` record and one `measure` event. It
  refuses when:
  - the check is not declared;
  - the KR is in `COMPUTED_KR_METRICS`, because a computed value is never typed;
  - the evidence path does not exist;
  - the KR's phase is scored, or its OKR version is not current;
  - the KR id without `--okr-version` names more than one overall KR.
- Every refusal names the command that would make it pass.

### 5.4 Code-measured checks

A check Perry can count from its own stores or repository is registered in
`COMPUTED_KR_METRICS`, keyed by `kr` and check id. Its value is recomputed on
read, as `P003-O3-KR2`'s is today, and never typed. Phase 004 candidates:
`P004-O1-KR3`'s weekly lag and handoff age (from `perry-state § history`) and
`P004-O3-KR2`'s share of decisions recorded (from `asks.jsonl`). Registering
one is an implementation row, not a store write.

### 5.5 Cadence (DESIGN-020 amendment)

- **New rule `R-kr-due`**: active phase, and any commit KR whose `state` is
  `undeclared`, `unmeasured` or `due` → `/perry goals measure <KR-ID>` (or
  `check` when undeclared). It sits after `R-week-unplanned` and before
  `R-asks-waiting`. Added through a `DESIGN-020 § 9 Changes` entry at hand-off.
- **`friday-review`** lists due checks from the payload and asks for
  measurements. It does not measure on its own.
- **`score-phase` step 1** pre-selects `achieved` when `met`, `partial` when a
  fraction exists and is below 1, and asks without a pre-selection otherwise.

### 5.6 Declaring phase 004's and v4's checks

After the writer lands, as a goals-lane action the user approves per Objective.
It is a declaration, not a restatement: no KR's words change.

| KR | Checks |
|---|---|
| `P004-O1-KR1` | fixture states `increase` 0 → 5 |
| `P004-O1-KR2` | subcommands carrying the closing step `at_least` the guard's count |
| `P004-O1-KR3` | weekly lag `at_most 1` · handoff age `at_most 7` |
| `P004-O2-KR1` | issues on the SkyTonight OKR `at_most 0` |
| `P004-O2-KR2` | writer landed `done` · hand appends after it `at_most 0` |
| `P004-O2-KR3` | fixture behaviours `increase` 0 → 2 |
| `P004-O3-KR1` | snapshot lines `at_most 12` · snapshot characters `at_most 1200` |
| `P004-O3-KR2` | decisions recorded `at_least 100` · median ask `decrease` 2101 → 600 |
| `P004-O3-KR3` | p90 next-action length `decrease` 1702 → 400 |
| `P004-O4-KR1` | affected-tier median `at_most 60` · full suite per merge `done` · total `at_most 1054` |
| `P004-O4-KR2` | structural rules `increase` 0 → 7 |
| `P004-O4-KR3` | pages over budget `decrease` 3 → 0 · context bills `increase` 0 → 5 |

`P004-O4-KR2`'s target of 7 needs a separate restatement after `USER-936`
deferred S2: either 6, or 7 with S2 carried to phase 005.

## 6. Implementation plan

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | `check` and `measurement` kinds in the schema (decision 4); ordering rules in `perry_store`; `lib` derivation (§ 5.2); `perry-goals/list` minor; fixtures | `TASK-416` widened | Coding Agent |
| B | `check` and `measure` verbs (§ 5.3) and the `measure` event | `TASK-264` widened; `TASK-231` closes with it | Coding Agent |
| C | `perry-state § phase.kr_progress` from § 5.2; reconcile `TASK-442`'s `met` | new row at hand-off | Coding Agent |
| D | `R-kr-due`, `friday-review` and `score-phase` steps (§ 5.5); `COMPUTED_KR_METRICS` keyed by check (§ 5.4) | new row at hand-off | Coding Agent |
| E | Declare phase 004's and v4's checks through the writer (§ 5.6) | goals lane, no task row | PMO + user |

A before B, B before E; C and D after A. `TASK-231` depends on `TASK-155`,
which is dropped; that edge is repointed to `TASK-264` at hand-off.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| A wrong `direction` makes `met` wrong while looking authoritative | `met` is rendered beside `metric` prose; `check` refuses inconsistent declarations | declarations are user-approved per Objective (§ 5.6) |
| An invented value gets in through `measure` | `--evidence` must exist; the record and event name who and when | evidence reviews follow `ADR-018`; a computed check cannot be typed |
| `TASK-442`'s shipped `met` (`current >= target`, zero only at zero) misreads every non-zero ceiling — `P004-O3-KR3` reads met at 1,702 against ≤ 400 | phase C fixtures: `decrease` 1702 → 400 is not met at 1702 and is met at 400; `at_most 0` is met at 0 and not at 3 | phase C replaces `next_kr_progress`'s comparison with § 5.2's, which reads the declared `direction` |
| Two readers order measurements differently | fixture with two measurements out of file order | one ordering rule in `perry_store`, no reader sorts for itself |
| A fraction confuses a consumer that read `2.0`'s removal | contract change log | `fraction` is a new key, null without a declared direction; `progress` is not reused |
| Many checks per KR dilute the cap by other means | `perry-goals krs` prints check counts | § 5.6 declares at most 3 per KR; more is raised at `plan-phase`'s input-quality pass |
| Schema consent delays everything | decision 4 unresolved at lock | nothing in B–E starts before A |

## 8. Open questions (optional)

- Whether `perry-goals krs` shows a check's last two measurements as a trend.
  The records exist from phase B onward; the view waits for a consumer.
- Whether an overall KR restated exactly by a phase KR (4 of 11 today) should
  mirror the phase KR's measurements rather than be measured twice. It is left
  measured twice until the duplication is observed to cost something.

## 9. Changes (append-only after lock)

## 10. References

- `perry/linkage.jsonl`, `perry/okr.jsonl` — counts in § 1.1, 2026-09-15
- `schema/goals-list-contract.md § 2.0`, `§ 3.0`, `§ 3.1`
- `bin/lib/__init__.py § kr_progress_provenance`, `§ COMPUTED_KR_METRICS`, `§ computed_kr_current`
- `goals/reference/linkage.md`, `goals/reference/phases.md § score-phase`, `goals/reference/pivots.md`, `goals/SKILL.md § Style rules`
- `DESIGN-015 § 5.1`, `DESIGN-020 § 5.2–5.3`, `ADR-007`, `ADR-018`, `ADR-019`
- `TASK-264`, `TASK-231`, `TASK-416`, `TASK-442`, `USER-912`, `USER-936`
- `evidence/2026-09/2026-09-08-kr-remeasurement.md`, `evidence/2026-09/TASK-442-spec.md`
