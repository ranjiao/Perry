# OKR of All Time

本文档包含整个系统的长期 OKR，用于指导用户和 Agent 对系统进行持续迭代。

> ⚠ **本文件的 Anti-Goals 含硬性约束**。
> **这些是 OKR 层的意图表述，不是权威规则** —— 当前有效的规则一律以 **`policy/`** 为准。

## Operating Principles

- **两动机（v4 明示）**：PRIMARY = **Insurance**；收益是 **floor 不是主目标**。
- verify-don't-assume：facts 必须查证，不靠假设。

## v2: 2026-04-30

### Objective 1: 维持整个资金池的长期稳定收益

整体资产收益是项目的最终目标。

- KR1: paper 账户上至少 1 个策略组合连续运行 ≥ 3 个完整月份。
- KR2 (Phase 1, 系统建设期): OOS 区间年化净收益 6-10%，最大回撤 ≤ 15%。
- KR3 (Phase 2, 升级目标): paper 年化净收益目标上调至 10-20%。

### Objective 2: 建设可靠的数据、风险和执行基础设施

- KR1: 统一数据看板上线，连续 4 周数据无中断。
- KR2: 抓取链路覆盖 raw、cleaned、feature 三层。

### Anti-Goals

长期不做的事项：

- 不为了短期收益放宽风险门、删减审计或绕过用户授权。
- 不把单次回测高收益视为策略已验证。

## v4: 2026-05-29

> 反映 Architecture v2.0。核心转变：**主从换位**。

### Objective 1: Insurance — 不被坑 + 决策可解释（PRIMARY）

- KR1: advisor-checker 处理真实 RM 提议，累计识破/修正 ≥3 笔。
- KR2: policy 偏离及时捕获 —— 超 tolerance 100% 生成提示。

## Commitments

> Promises to a named party by a date. The spine for pipeline- and queue-mode
> tracks (DESIGN-003 § 5.5).

| Id | Track | Promise | To whom | Due | Status | By when note |
|----|-------|---------|---------|-----|--------|--------------|
| research/1 | research | Weekly candidate memo | 用户 | 2026-09-30 | active | 每周五之前 |
| ops/1 | ops | Reconcile the BoS statement | RM | 3d | done | — |

## Versioning

| Version | Date | What changed | Why |
|---|---|---|---|
| v2 | 2026-04-30 | First long-horizon OKR. | 之前只有月度目标。 |
| v4 | 2026-05-29 | 主从换位；account-domain 替代 two-leg。 | Architecture v2.0 落地。 |
