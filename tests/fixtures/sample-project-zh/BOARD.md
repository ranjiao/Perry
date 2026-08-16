# Board — 示例项目

> 实时工作记忆。只放当前未完成的工作 — 关闭的任务离开这份文件。
>
> Last updated: 2026-08-16
> 硬上限：≤200 行。超了就跑 `/perry pmo triage`。

## P0（本周期必须完成）

<!-- P0 / P1 / P2 are priority enum values — invariant across languages.
     The column headers and the prose are localized. -->

| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|
| REL-001 | 部署脚本加固 | Coding Agent | in_progress | 补完回滚路径 | evidence/2026-08/REL-001-spec.md |
| REL-002 | 抖动检测器 | Coding Agent | blocked | 等 USER-014 | evidence/2026-08/REL-002-spec.md |

## P1

| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|
| REL-009 | 流水线文档刷新 | PMO Agent | not_started | 起草大纲 | — |

## P2

| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|

## 例行节奏（周期性；不占用 P0 名额）

| 编号 | 例行任务 | 负责人 | 频率 | 下次到期 | 最近证据 |
|---|---|---|---|---|---|
| CAD-001 | 周五复盘 | PMO Agent | weekly | 2026-08-21 | weekly/2026-33.md |

## 用户输入队列

| 用户输入编号 | 需要用户提供 | 阻塞 | 闲置 | 状态 |
|---|---|---|---|---|
| USER-014 | 确认预发布环境的默认值 | REL-002 | 6d | open |

## 主要风险（一行；完整清单在 `PROJECT_STATE.md`）

- **DEPLOY-FLAKE 4.2%** TOP RISK — 预发布运行仍然抖动；阻塞「连续三次全绿」这条 KR。
