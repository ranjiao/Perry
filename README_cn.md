# Perry — 虚拟项目办公室

Perry 是一个 skill，包含 goals、work、decide 三条工作线，支持 Claude Code、OpenCode 和 Codex CLI。输入 `/perry` 查看项目，使用各工作线制定目标、执行任务和记录决策。

方法和判断保留在 skill。通用 kernel 将结构化状态写入本地 SQLite，同一项目的 worktree 共享存储；Markdown 保存说明和证据，JSONL 导出用于备份与审查。

新架构已集成，Perry 自身及 SkyTonight 已完成本地切换和具名人类验收，见 [最终记录](perry/evidence/2026-10/TASK-494-formal-cutover-20261020/FINAL.md)。[退役清单](release/retirement/README.md) 保留原始提案以便追溯，实际批准记录单独保存。历史数据和迁移备份保留；公开发布状态仍以安装说明为准。根目录各路径的用途见 [目录说明](README.md#repository-layout)。

[安装](INSTALL.md) · [架构](ARCHITECTURE.md) · [英文入口](README.md) · [工具说明](tools/README.md)
