# Perry — 虚拟项目办公室

Perry 是一个 skill，包含 goals、work、decide 三条工作线，支持 Claude Code、OpenCode 和 Codex CLI。输入 `/perry` 查看项目，使用各工作线制定目标、执行任务和记录决策。

方法和判断保留在 skill。通用 kernel 将结构化状态写入本地 SQLite，同一项目的 worktree 共享存储；Markdown 保存说明和证据，JSONL 导出用于备份与审查。

当前源码是 DESIGN-023 H 的退役候选，尚不代表正式启用或用户验收。旧命令和 schema 的逐项去向、待确认删除及消费者阻塞见 [退役清单](release/retirement/README.md)。历史项目文件保持原样。

[安装](INSTALL.md) · [架构](ARCHITECTURE.md) · [英文入口](README.md) · [工具说明](tools/README.md)
