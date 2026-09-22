# TASK-484 — integration acceptance, 2026-09-23 (V4)

DESIGN-020 I (§ 5.10 batch 3): next-step rules for cadence and operations.
Attributed to P004-O1-KR1. Authorized USER-1002.

| Step | Result | Record |
|---|---|---|
| V4 review | one round, **PASS** with notes; net +249 Python/test (bound +250), exactly the six in-scope files, no `state-schema.json`, no router `SKILL.md`, no new subcommand | `../TASK-484-review/v4.md` |
| Candidate | `9eb97225`, then two PMO-ordered correction rounds for false statements the rules made: `31e7ea24`, `7be0ae88` | — |
| Architecture review | four rounds, same trigger set each time. R1 BLOCKED (a lane page said the opposite of what ships), R2 BLOCKED (three false statements round 1's fix introduced), R3 BLOCKED **on the §6 NN-6 marking alone** — no descriptive mismatch and no new false statement left — R4 **PASS** | `architecture-review-round{1,2,3,4}.md` |
| NN-6 blocker | resolved without a user ruling by taking the strict branch: NN-6 grants an agent a §7 addition "marked `proposed`", so the clause is now `*Proposed — partly answered 2026-09-23 (TASK-484):*`. R4 confirmed by word-level diff that §7 against **base** has zero delete or replace opcodes — the rewrap is pure insertion | `701ee4f6` |
| Release | `release/manage.py patch` → **0.1.23** (`TASK-484-operations-next-rules`). Allocated once as `c06c9b7b`, then **re-cut** as `2344182f` after R3 found the third upgrade note ambiguous — it said the day-180 case "already got the recommendation there", which is false read against 0.1.22, a release with no `R-architecture-stale` at all. The record was re-minted through the tool, not edited: R4 verified all fields but `upgrade` byte-identical, and the 23 earlier records byte-identical to base | `2344182f` |
| Full gate | green on tree `1e05cde7`, base `main 65b27e41`, candidate `integ/task-484 2344182f`; 158 modules measured, 4 unmeasured | `receipt.json`, `full.log` |
| Integration | `integ/task-484` `2344182f` + durations on `integ/task-484-final` `bd2c18f4`; receipt **VERIFIED** on `bd2c18f4` (162 recorded, 162 on disk, 0 stale, 0 unstamped) | commits |
| Slow gate | all green, exit 0, in the integration worktree | `slow.log` |
| Merge | refs rechecked (`main 65b27e41`, `integ/task-484-final bd2c18f4`), `git merge --ff-only` → main `bd2c18f4`; `VERSION` 0.1.23; `release/manage.py check --base origin/main --ref HEAD` exit 0 (`origin/main 174f35b2`, six new versions 0.1.18–0.1.23) | — |
| Live state after merge | `perry-state --section next` on this repository: `perry-next/1.4`, no `rule_errors`, 30 rules declared · 28 eligible · 5 fired; primary `R-sla-breach` → `/perry work triage` (3 queue items past SLA, longest TASK-270), alternates `R-dispatchable` → `dispatch TASK-218` and `R-midweek`. `architecture.days_since_review` = 8 | — |

**Integrated, unpublished.**

## What shipped, against the spec

Four rules, not the five § 5.10 declared. `R-rollover` was deliberately not
built and `rollover` is classified **never-recommended** in the coverage guard:
`work rollover` is the phase-transition procedure, reached after `score-phase`
through `R-no-phase`, so a month boundary would start it on a date that says
nothing about whether the phase is over. The deviation was reasoned in the spec
before the work started and is now recorded as a `DESIGN-020 § 9` change entry,
because § 5.10's event table, its `month.rollover_due` fact row, its rule order
and § 6 row I all still declare the rule.

## A note on the logs

`full.log` and `slow.log` hold the tail of each run, not the whole transcript —
both gates were run in the background through a `tail` pipe, which truncated the
captured output. Each ends in its own verdict line and its exit code, and the
full gate's `receipt.json` carries the tree, the base, the candidate and the
module inventory independently. The slow run's module and test totals were lost
to that truncation and are deliberately not quoted above.

## Follow-ups, no rows opened

- `contains` over a `None` fact raises `_RuleError` rather than not firing.
  Unreachable today, since `project.packs` is always a list.
- `work architecture-audit` carries no `next-close` marker while `work digest`
  and `work risk` do. `R-architecture-stale`'s `after` is `[]`, precedented by
  R-setup, R-no-okr and R-phase-heartbeat, so nothing false is claimed.
- Root § 2's config-parsing claim was not checked against
  `parse_config`/`load_packs` — pre-existing, unchanged by this diff.
- `packs/software-ops/architecture.md` declares its own review cadence, not
  checked against the new 180-day threshold.
- Whether an agent may leave a §7 annotation unmarked under a task id is still
  the user's to rule. If the answer is yes, this clause's marking is upgraded;
  it is not a gate on anything.
