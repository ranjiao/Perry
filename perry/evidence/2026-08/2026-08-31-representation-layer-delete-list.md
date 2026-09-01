# The representation layer — what to delete, in what order, and what it is holding up

> Analysis, 2026-08-31. Not a task row. Written to be cited by the rows it
> proposes, and to be argued with before any of them are filed.

## Why this list exists

Every task on this board that has ground in V4 is in one architectural layer.
The 14 rows kicked back two or more times, with their subject:

> **Written as a list, not a table, on purpose.** A markdown table whose first
> cell is a row id is harvested by `perry-explain` as Perry state — the first
> draft of this file did exactly that, gave `TASK-050` the title `11`, and
> silently turned `tests/test_heading_title.py` green by displacing the real
> entry. An analysis document in a folder Perry claims is the `NS-01` hazard,
> and this paragraph is what it cost to learn twice.

- **11 rounds** — `TASK-050`, header-cell normalization: md table parsing
- **6 rounds** — `TASK-095`, remove the parser for three stores
- **5 rounds** — `TASK-203`, an ordinary write does not update its store: dual write
- **5 rounds** — `TASK-234`, `.perry/conformance.md` is a hand-rolled table parser
- **4 rounds** — `TASK-249`, `tests/run` writes Perry state: intake dual write
- **2–4 rounds each** — `TASK-089`, `093`, `067`, `091`, `241`, `233`, `044`,
  `042`, `019`, `020`, `027`, `028`: dual write, drift, md parsing, migration

**Not one is about OKR or task management as a domain.** All of them are about
markdown-as-canonical, its parsers, its drift detection, or its conformance
ledger.

The three gates that exist to service that architecture, measured on this
repository's own history:

**drift** — `perry-lint` reports `0 row(s) drifted` on all six stores and
always has. Every non-zero reading anywhere in this repo comes from a V4
reviewer deliberately corrupting a store to demonstrate a bug. It has caught
zero real incidents, and it generated TASK-031, 067, 093, 203 and 243. It is
still evadable: TASK-243, filed 2026-08-30 — *"a count-preserving substitution
destroys canonical records silently, and the drift report goes DOWN as it
happens."* It guards a behaviour `AGENTS.md` already forbids and no agent
performs.

**the ADR-004 conformance gate** — `.perry/conformance.jsonl` holds 23 records.
All 23 are `route: declare`. All 23 are Perry's own files. **Zero migrations,
zero disagreements.** Its entire value proposition is that a stored declaration
and a live shape check *can disagree, and that disagreement is a finding*. That
requires a foreign project that drifts, and Perry has never been run on one.

**lint** — today: 0 errors, 4 warnings, and all four are `NS-01` on files you
deliberately put in `phase/`, `evidence/`, `handoff/` and `knowledge/`. Live
signal-to-noise 0:4. Its schema half is the part that works and is not on this
list.

## The list is ordered, because two targets are load-bearing today

`perry_md_store.py` is not a drift helper. `perry-goals` and `perry-config`
call `md_store.derive`, `md_store.render` and `md_store.store_text` on the real
write path. `perry-conform` is imported by `perry-task` as a live gate. Neither
can be deleted before the read/write side stops going through markdown, which
is what phase 003 Objective 2 and TASK-236/237 are for.

So: three tiers, each with a precondition that can be checked.

---

## Tier A — deletable now

**Precondition: none.** Nothing computes a different answer without these.

| target | lines | note |
|---|---|---|
| `bin/perry-conform` | 974 | the ADR-004 declaration gate |
| `perry_conform()` + the write-gate in `bin/perry-task` | ~60 | `bin/perry-task:6897–6920` and its call sites |
| `.perry/conformance.jsonl`, `.perry/conformance.md` | 23 records | |
| `tests/test_conformance.py` | 2,882 | |
| `tests/mutate_task_234.py` | 568 | |
| open rows TASK-223, 246, 248 | — | all three are defects *in* the gate |

**≈ 4,500 lines, and three open rows close as `dropped` rather than `done`.**

> **Do not confuse two things called conformance.** This deletes the ADR-004
> *file declaration* gate. It does **not** touch the `conformance.*` fields in
> `perry-task list --json` (`evidence_not_found`, `depends_on_unknown`,
> `blocked_by_closed_rows`, …) — those are read-time integrity reporting, they
> are a published contract in `schema/task-list-contract.md`, and they are
> useful. Deleting them would be a real regression.

---

## Tier B — after phase 003 Objective 2 lands

**Precondition:** no code path reads a rendered markdown file as authority.
Checkable: `P003-O2-KR1`'s four `parse_tracks` call sites move to
`.perry/config.jsonl`, and `perry-goals` stops deriving from `OKR.md`.

| target | lines |
|---|---|
| `check_store_drift` + `_empty_store_drift_stats` | 244 |
| `check_risk_store_drift` + helper | 149 |
| `check_intake_store_drift` + helper | 123 |
| `check_ask_store_drift` + helper | 149 |
| `check_md_store_drift` + two helpers | 164 |
| `_order_drift` | 49 |
| the six census report lines in the default pass | ~40 |
| `tests/test_store_drift.py` | 966 |
| the drift halves of `test_risks_store` / `test_asks_store` / `test_okr_store_is_the_source` / `test_register_substitution` | ~1,200 |

**≈ 3,100 lines.** Drift only has a job while a rendered file can be authority.
When nothing reads one, a hand edit is a no-op, not a hazard — and the check
becomes a check on a file nobody consults.

---

## Tier C — after TASK-236 and TASK-237

**Precondition:** `OKR.md` and `BOARD.md` stop existing as parsed files and
become what a command prints. Both rows are already on the board.

| target | lines |
|---|---|
| `bin/perry_md_store.py` | 1,203 |
| `bin/perry-migrate` | 2,393 |
| `tests/test_md_store.py` | 1,277 |
| `tests/test_migrate.py` | 2,900 |
| `tests/test_one_header_rule.py` | 327 |
| `tests/test_header_index_is_the_only_fold.py` | 775 |
| `tests/test_store_is_canonical.py` | 356 |
| `tests/test_last_updated_header.py` | 160 |
| `tests/test_stranded_rows.py` | 757 |
| remaining rows TASK-095, 067, 199, 246, 247, 252 | — |

**≈ 10,100 lines.**

> Migration deserves its own argument. `perry-migrate` exists to move somebody
> else's project onto Perry's shape. **It has never done that** — the
> conformance log's 23 records carry zero `route: migrate`. TASK-097 ("migrate
> the two real projects, at V5") has been `not_started` throughout. If the
> answer to "have we ever migrated a foreign project" stays no, migration is a
> feature written entirely on speculation, and the cheap replacement for a
> personal tool is an importer you re-run, not a lossless recoverable
> dry-runnable migrator.

---

## What it adds up to

| | product code | tests |
|---|---|---|
| Tier A | ~1,030 | ~3,450 |
| Tier B | ~920 | ~2,170 |
| Tier C | ~3,600 | ~6,550 |
| **total** | **~5,550** | **~12,170** |

Against today's `bin/` at 33,413 lines and `tests/` at 69,371, that is **17% of
the product code and 18% of the tests** — and it is the 17% that produced 11 of
the 14 high-rework rows.

The second-order effect is larger than the line count. **21 of the 69 open rows
on this board are representation-layer.** Tiers A–C close or drop 9 of them
outright, and the rest stop generating successors.

## What this list does not propose

- **Not a rewrite.** The asset is the prose — the lane split, what V1–V6 mean,
  the hand-off contract, "an agent cannot self-award its own rung". None of it
  is in the code being deleted.
- **Not touching `perry-lint`'s schema pass.** That half works.
- **Not touching `perry-task list --json`'s `conformance.*` payload.** See the
  Tier A note.
- **Not deciding TASK-097.** Whether Perry is ever pointed at a foreign project
  is a product question, and it is the one that decides Tier C's migration half.
  It should be answered by a person, not derived from this list.

## The one thing to check before filing any of this

Tier A rests on a claim that is falsifiable in one command:

```
grep -c '"route": *"migrate"' .perry/conformance.jsonl     # expected: 0
```

If that is ever non-zero — on this project or any other — Tier A is wrong and
the gate has done the job it was built for. It has not yet.
