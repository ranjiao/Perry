# Perry — 你的虚拟项目办公室

[English](README.md) · [安装与更新](INSTALL_cn.md)

Perry 是一个 Agent skill，用于制定目标、管理工作和记录决策，支持 Claude Code、OpenCode 和 Codex CLI。Agent 负责方法和判断，小型本地内核记录结构化项目状态。

## Perry 能做什么

| 工作线 | 用途 |
|---|---|
| `goals` | 目标、关键结果、测量和阶段 |
| `work` | 任务、依赖、问题、风险和验证证据 |
| `decide` | 设计讨论、已批准设计和架构决策记录 |

这三条工作线都属于同一个 `perry` skill，不需要分别安装。工作模式（modes）说明工作如何推进；可选领域包（packs）补充领域流程。它们不提供后台执行器，也不授权外部操作。

## 开始使用

安装说明覆盖 macOS 和 Linux，尚未验证 Windows 原生安装。

1. 安装 Python 3.11 或更新版本、Git 和一个支持的 Agent 宿主。Perry 的 Python 代码只使用标准库，不需要 `pip install`。
2. 按[安装说明](INSTALL_cn.md)操作。有已发布版本时可选择发布版，也可以明确选择 `main` 上的开发源码。安装只是将源码目录链接到宿主，不会初始化项目。
3. 在宿主中打开**你自己的项目目录**，加载 `perry`，要求它初始化新项目或检查已有项目。Claude Code 的入口是 `/perry`；其他宿主使用各自的 skill 调用方式。

例如：“这是一个新的研究项目。帮我选择最小目录结构并初始化 Perry，项目文档使用中文。”Agent 会先检查已有文件，确认布局和边界，再按需初始化。详见[新项目组织指南](reference/new-projects.md)。

Perry 源码仓库是安装的工具，不是你的项目模板。其中的 `perry/` 目录保存 Perry 自身的开发记录。

## 已有项目与数据存储

旧 Markdown/JSONL 项目需要经过审查的迁移方案。更新已安装的 skill、应用进程模板或在查看器中打开项目，**都不会迁移项目数据**。详见[已有项目](INSTALL_cn.md#已有项目)。

原生条目、关系和事件存入 SQLite。Git worktree 共享 Git 公共目录中的存储；非 Git 项目使用 `.perry/perry.db`。说明和证据仍是 Markdown，放在约定的文档根目录下。内核生成的 JSONL 导出用于备份与审查。普通 Git commit 不包含 `.git` 下的 SQLite 存储；保存项目时需要导出状态，并备份引用的文档。

## 开发者说明

`bin/perry` 是原生 JSON CLI，与在 Agent 中输入的指令不同。运行 `bin/perry --help` 或 `bin/perry describe` 查看接口；辅助工具位于 `tools/`。旧的 `perry-task`、`perry-state` 和 `perry-goals` 命令已退役。

`bash tests/run` 运行内核与辅助工具测试；`bash tests/run --tier slow` 增加隔离 Git 集成自测。这些测试验证源码行为，不代表用户项目已完成迁移或人类验收。

[架构](ARCHITECTURE.md) · [原生契约](reference/kernel.md) · [项目中立设计](reference/design-principles.md) · [辅助工具](tools/README.md) · [维护者发布规则](release/README.md)

## 仓库目录

| 路径 | 用途 |
|---|---|
| `bin/`, `kernel/` | CLI 入口与通用状态引擎 |
| `SKILL.md`, `goals/`, `work/`, `decide/` | Agent 路由与三条工作线；工作线流程和叙事模板 |
| `reference/`, `modes/`, `packs/` | 共享规则、工作模式与领域流程 |
| `templates/` | `scaffolds/` 为独立文档起点，`process/` 为原生进程数据，`internal/` 为 Perry 内部流程与策略模板 |
| `tools/`, `tests/` | skill 辅助工具与测试；内核测试位于 `kernel/` |
| `release/` | 版本记录、发布工具和历史退役记录 |
| `perry/`, `.perry/` | Perry 自身的开发文档、证据、导出和项目偏好；不应复制到新项目 |
