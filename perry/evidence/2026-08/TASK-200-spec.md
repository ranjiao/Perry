# TASK-200 — a finance-shaped role card, extracted rather than invented

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `8ce9fcf`

## Why this row exists

`TASK-077` is DESIGN-006's **pass condition**: *"the abstraction survives
contact with a real non-software role, or the extraction report says why not."*
Both outcomes are wins. **A card that shows the model does not fit is worth more
than one that fits by being vague.**

Everything else is already built — phases A through E are all `done`, and the
`Kind: source-of-truth` card type F asks for **already exists**
(`state-schema.json:2112`, `knowledge-list-contract.md:71`,
`perry-knowledge --kind`). What has never been done is the thing the row is
named after: **no non-software role card has ever been written.** All three
shipped cards — `coding`, `research`, `review` — are software-shaped, and the
only pack is `software-ops`.

## The material, which is real and already written

`~/proj/gimegime-pmo` is a quantitative-finance project. **Read it; do not
invent a finance role.** It already carries explicit role definitions:

```
ARCHITECTURE.md:20   | 域 | code | operator | system 角色 | 状态 |
ARCHITECTURE.md:43   Gimegime System Role — 观察 / 审顾问提议 / 记账
                     系统永不下单
ARCHITECTURE.md:51   跑实验 / 学习 / propose promotion
ARCHITECTURE.md:58   按 policy 自动执行 + risk monitor + reconcile
```

Also worth reading: `OKR.md` (three Objectives about capital-pool returns, data
and risk infrastructure, and a controllable agentic system), `BOARD.md`
(投资线 / 工程线 split, `## Cadence`, `## User Input Queue`, `## Top risks`), and
`DECISIONS.md`. Its document language is 中文; **quote it in the original and do
not translate an invariant into English prose** — a translated invariant is a
different invariant.

**`~/proj/gimegime-pmo` is READ-ONLY to you.** Write nothing there.

## The sharp question, and it is the whole row

The role card template has four sections: `## Context`, `## Loads`,
`## May touch`, `## Must escalate`.

**`Must escalate` is where this design either survives or does not.** DESIGN-006
§ 7 records the mechanism and its known failure mode:

> Escalation union silently fails like the unbackticked hook lines did — same
> fix: **only backticked spans extract**; lint warns on a `Must escalate` line
> with zero backticks.

So an escalation entry is a **backticked span** — for a software role,
`bin/perry-task`, `.env`, a path or an identifier the scanner can match against
what a task touches.

**A finance role's central invariant is `系统永不下单` — the system never places
an order.** That is an *action*, not a path. Nothing in a task's file list
matches it.

**Establish, with evidence, whether that invariant can be expressed as a
backticked span the escalation union would actually catch.** If it can, show the
span and what it matches. **If it cannot, say so plainly** — that is the
extraction report DESIGN-006 asked for, and it is a finding about the model, not
a failure of this row.

Do the same, field by field, for `Context`, `Loads` and `May touch`.

## What to produce

`perry/evidence/2026-08/TASK-200-finance-role-card.md`, containing:

1. **The proposed card**, in the shape `work/state/role_card_TEMPLATE.md`
   requires. **Every claim cites the gimegime-pmo file and line it came from.**
   A line you cannot cite is one you invented — cut it or mark it.
2. **A field-by-field verdict**: does this section carry a non-software role
   as-is, with a change, or not at all? Name the concrete case that breaks it.
3. **The `Must escalate` answer above**, with whatever you ran to decide it.

**Write it as a proposal, not as a live card.** Do **not** create
`.perry/roles/` in this repo or anywhere else — the user decided on 2026-08-28
to draft first and run later, and a card on disk is the run starting.

## Files in scope

`perry/evidence/2026-08/` only. `bin/`, `tests/`, `schema/`, `packs/` and the
rest of `perry/` are read-only for this row, as is `~/proj/gimegime-pmo`.

If you find that a **tool** would have to change for the card to be expressible,
that is a finding to report, not a change to make.

## Verification

1. Every card line carries a `file:line` citation into gimegime-pmo.
2. The `Must escalate` verdict is decided by running or reading the extractor,
   not by assertion — name what you read.
3. Nothing is written outside `perry/evidence/2026-08/`; `git status` shows no
   other path.
4. `perry-lint`: 0 errors, 3 warnings — unchanged.

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
