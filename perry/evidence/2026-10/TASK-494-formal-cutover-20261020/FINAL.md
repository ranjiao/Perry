# 剩余架构切换已完成 — 2026-10-20

Ran Jiao 已实际签署最终 V5 验收，并明确要求关闭 TASK-494。Agent 已通过原生内核记录该人类决定；TASK-492、TASK-493、TASK-494 均为 done。

- [实际签署原文及范围](V5-acceptance.json)，[内核关闭事件](V5-transition.json)，[最终任务状态](final-task-states.json)。
- [用户验收的原始结果快照](RESULT.md) 保持原样，其 SHA256 与签署记录一致。该快照中的“等待 V5”现由本次真实签署完成。
- Perry 0.1.29，主分支 `7f7849060d035871160b5be6e0cc9efca0cd6a5f`；aiMark 主分支 `27586cdb5a59ecbed6afda5ed0dc7ada9b981947`，保留用户全部现有 WIP 及 0.19.2 版本修改。
- goals、decide 和根看板已切换到原生 kernel + SQLite；两项目真实增量迁移、批准的旧实现退役和 ADR 整理均已完成。上下文 token 限制已移除，由 Agent 环境和用户决定何时更换 session。

关闭后重新验证：Perry seq 1895、807 items；SkyTonight seq 264、94 items。两项目导出在隔离数据库导入后逐字节一致，原始事件前缀完整；除本次三个任务外，原有条目的持久字段和 seq 均未改变。实际集成的 aiMark 原生读取再次通过。

[最终原生状态及重放证据](post-task-native-verification.json) · [实际 aiMark 读取](actual-aimark-reader.json) · [独立复核](independent-review/final-activation-review.md)

产品集成验证已通过：Perry full 470、slow 477（各有 1 项 APFS 平台跳过），aiMark 合并现有 WIP 后 1024 项及原生相关 123 项。此次收尾只记录真实人类验收和任务状态，没有改产品代码。静态架构证据保持其已声明的覆盖边界；aiMark GUI 未作为本次验证项。全部工作为本地切换，未 push、打 tag 或发布。
