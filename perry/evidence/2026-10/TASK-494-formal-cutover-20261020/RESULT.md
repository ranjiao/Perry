# Perry 剩余架构切换结果

2026-10-20。本地切换已完成；TASK-492、TASK-493 已完成，TASK-494 等待实际用户 V5 验收。

| 项目 | 已验证结果 |
|---|---|
| Perry | main `7f784906`，版本 **0.1.29**；goals、decide、根看板使用原生 kernel |
| aiMark | main `27586cdb`；原生读取真实 Perry / SkyTonight；用户版本 **0.19.2** 与全部 WIP 保留 |
| Perry 数据 | 原 602 项工作记录和 1200 条事件保留；追加 204 项目标/阶段/设计/决策，再完成计划内 ADR 收尾 |
| SkyTonight 数据 | 原 34 项、68 条事件保留；追加 60 项；真实存储序号 264 |
| 历史 | 旧 journal / JSONL / ADR 头部保持历史原文；不再充当当前状态 |
| 安全 | 原 35 / 56 个高风险片段均保留到结构化策略；角色安全章节缺失、拼错或重复会拒绝派发 |

两项目都有新鲜数据库和源文档备份、固定哈希计划、两次隔离演练、真实重复执行无新增事件、逐字节导出重放证明。原有非相关工作未覆盖；两份派生 export 更新，其原字节已备份。

完整合并树检查通过：Perry full 470 / slow 477 项（各含 1 项 APFS 平台跳过）；release、双 offline receipt、diff 通过。aiMark 包含现有用户工作树的组合验证 1024 项通过，主树 native/contract 123 项通过。当前原生程序在零 Markdown 的隔离环境运行，方法调整只改模板，内核源哈希未变。

独立复核对 TASK-492 / TASK-493 的全部书面标准给出 PASS。真实 native 读取证明 Perry v4 / PH-004、28 个 ADR，SkyTonight v1 / PH-003、0 个 ADR；22 / 12 个未知进度比例保留为 null。ADR-028 及 ADR-025 计划的归档、替代、修订已记录；历史源未被改成当前元数据。

架构证据保留实际修改前基线与 fresh delivery。静态报告仍是 attention：包含已批准的目标修订及命名扫描范围限制，不代表覆盖所有语义；完整源码、替代安全反例和真实数据由独立复核补足。

当前任务状态（native seq 1894）：TASK-492 done；TASK-493 done；TASK-494 review。此前内核修订和 423 项退役/R0096 缩减批准不代替本次最终 V5。未进行远端推送、tag 或发布。

## 核对材料

- [真实切换独立复核](independent-review/final-activation-review.md)
- [Perry 真实迁移证明](Perry/live/verification.json) / [SkyTonight 真实迁移证明](SkyTonight/live/verification.json)
- [实际 aiMark 读取](actual-aimark-reader.json)
- [ADR 收尾](decision-reconciliation.json)
- [独立集成 RESULT](integration/RESULT.json)
- [无 Markdown 与方法数据化证明](markdown-free-and-method-proof.json)
- [原有 WIP 保护](original-wip-after-activation.json)

备份位于本目录各项目的 before.db / before-source。备份用于受控恢复；直接替换现在的数据库会丢失后续新增和 ADR/任务事件，不能自动覆盖。
