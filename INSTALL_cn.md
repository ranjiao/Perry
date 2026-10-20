# 安装与使用 Perry

[English](INSTALL.md) · [项目介绍](README_cn.md)

Perry 是一个 Agent skill，包含 `goals`、`work`、`decide` 三条工作线。安装 skill 和初始化项目状态是两件事。

## 前置依赖

以下命令面向 macOS 或 Linux。Windows 原生安装尚未验证；仅安装 Bash 不代表所有辅助工具都兼容。

使用 Python 3.11 或更新版本、Git、Bash、curl、Perl，以及至少一个已安装且在 `PATH` 中可用的宿主：`claude`、`opencode` 或 `codex`。Python 标准库提供 SQLite，Perry 不需要额外 Python 包。Setup 检查 `python3` 是否存在，但不检查版本，请先运行：

```bash
python3 --version
git --version
```

只有所选宿主或可选 Codex 执行器需要时，才需要 Node.js/npm。Homebrew 和 `timeout`/`gtimeout` 是可选安装或执行辅助工具，不是内核依赖。必要工具应按其各自说明安装。

## 选择源码并安装

安装后的 skill 是指向源码目录的符号链接，因此需要保留源码 clone。选择尚未占用的目录，例如 `~/perry`；它与要管理的项目目录分开。以下两条源码路线**选一条**。

### 已发布版本

从 [GitHub Releases](https://github.com/ranjiao/Perry/releases) 选择实际存在的稳定版本 tag。运行前替换 `vX.Y.Z`：

```bash
git clone --branch vX.Y.Z https://github.com/ranjiao/Perry.git ~/perry
~/perry/setup
```

仅有 Git tag 或源码中的 `VERSION` 不代表已经发布。如果页面没有稳定 Release，这条安装路线尚不可用；setup 不会创建发布。通过 tag 克隆后 Git 处于 detached HEAD，这是此路线的正常状态。

### 开发源码

如果你明确选择当前尚未发布的源码，运行：

```bash
git clone --branch main https://github.com/ranjiao/Perry.git ~/perry
~/perry/setup
```

`main` 可能包含比已发布版本更新的改动。在已有项目使用前，应查看该 checkout 的 README、升级说明和测试。

### 选择宿主

不指定宿主时，setup 检测 `PATH` 中的宿主，并为所有检测到的宿主安装。也可以明确选择：

| 命令 | 全局 skill 链接 |
|---|---|
| `~/perry/setup --claude` | `~/.claude/skills/perry` |
| `~/perry/setup --opencode` | `~/.config/opencode/skills/perry` |
| `~/perry/setup --codex` | `~/.agents/skills/perry` |

可以组合这些参数。从**目标项目目录**运行时，`--local` 将 Claude Code 和 OpenCode 的安装位置改为 `./.claude/skills/perry`、`./.opencode/skills/perry`；Codex 仍使用全局位置。Setup 只创建 `perry` 链接，清除可识别的旧 Perry 工作线链接，并保留冲突目录或指向其他位置的链接。出现冲突表示安装不完整，应先检查输出中的路径。

```bash
~/perry/setup --codex --check-deps-only
~/perry/setup --codex --no-deps
```

第一条只报告依赖，即使退出码为零也需要阅读输出。第二条跳过检查并创建链接，不会安装缺失工具。`--yes-deps` 允许支持的可选安装操作，不会绕过必要工具缺失，也不提供认证信息。不带该参数时，非交互 shell 会跳过需要询问的可选安装。

## 验证安装

只检查所选宿主的链接，例如：

```bash
test -L ~/.agents/skills/perry
test -f ~/.agents/skills/perry/SKILL.md
~/perry/bin/perry --help
~/perry/bin/perry describe
```

后两条是只读原生 CLI 检查，不需要项目存储。Claude Code 或 OpenCode 用户将链接替换为上表对应位置。宿主尚未发现 skill 时，重新打开或重新加载宿主。链接和 CLI 检查成功，不代表已认证的宿主会话已经能够执行 Agent 任务。

## 第一个项目

在宿主中打开你自己的项目目录，加载唯一的 `perry` skill。Claude Code 使用 `/perry`；Codex CLI 可在 `/skills` 中选择 `perry` 或提及 `$perry`；OpenCode 使用其 skill 调用方式。`/perry goals …`、`/perry work …`、`/perry decide …` 是给 Agent 的指令，不是 shell 命令。

对全新项目，要求 Agent 初始化 Perry。它会先检查已有路径和恢复状态，确认文档/聊天语言、布局、领域包和高风险操作边界，再记录项目偏好、初始化原生存储并应用随附的进程模板。只创建当前需要的条目和叙事文档。具体流程见[首次使用](reference/first-run.md)和[项目组织](reference/new-projects.md)，不要自行按顺序执行一串工作线初始化命令。

Perry setup 不提供模型认证、宿主订阅、后台调度器或 push、部署权限。可用交互由当前会话实际提供的宿主工具决定，详见[宿主能力](reference/host-capabilities.md)。

## 已有项目

先告诉 Agent 这是已有项目。旧文档旁没有原生存储，表示需要迁移，不能当作空白新项目。更新 skill 或应用 `templates/process/perry.json` 都不会导入旧记录。

先盘点实际来源和归属，确认当前条目与历史文档的映射，在隔离存储试迁并验证身份、关系和导出重放，再经过明确授权、备份和消费方检查后正式切换。保留原始证据和批准来源，不重新激活旧目标，不推断过去的同意，不补造测量。

目前没有通用的旧 Markdown/JSONL 一键迁移命令。随附的[计划应用工具](tools/reviewed-plan-migration.md)只消费专门准备且经过审查的计划，不是自动旧格式解析器。不要把演练数据库复制到 live store，也不要导入已有数据的存储。其他边界见[兼容性说明](reference/version-compatibility.md)。

## 保存项目状态

Git 项目的原生 SQLite 存储位于 Git 公共目录下，worktree 共享该存储；非 Git 项目使用项目锚点下的 `.perry/perry.db`。叙事文档仍放在约定的文档根目录。普通 Git push 不会上传 `.git` 下的数据库。

完成初始化后，从实际项目目录运行已获授权的导出：

```bash
~/perry/bin/perry export --root "$PWD"
```

内核将 `items.jsonl` 和 `events.jsonl` 写入存储所记录的 `<document-root>/export/`。需要备份两个原始文件和引用的文档。导出是项目数据，应自行决定哪些内容可以提交或分享。恢复通过原生 import 写入空存储，并进行项目专项检查；仅 Git clone 不会恢复 live store。详见[原生契约](reference/kernel.md)。

## 更新或卸载

已发布版本的安装可显式检查和更新：

```bash
bash ~/perry/tools/update-check.sh --force --channel release --strict
```

工具校验官方 Release 元数据、tag 和 `VERSION`。没有稳定发布时保持 checkout 不变，不会改用 `main`。不带 `--strict` 时，拒绝可能只报告原因而不返回失败退出码。未提交修改、功能分支、本地提交或降级会阻止自动发布版更新。有效的 detached 发布 tag 可以更新到较新发布。符号链接安装的默认检查只报告状态。跟随 `main` 的开发者自行用 Git 管理源码；更新已安装代码不会迁移项目状态。如果宿主缓存 skill 指令，更新后重新加载。

卸载时只删除**自己选择安装的 skill 符号链接**，例如：

```bash
rm ~/.agents/skills/perry
```

其他宿主使用安装表中的对应链接。删除前确认它确实是 Perry 符号链接，不要递归删除 skills 目录。项目状态和源码 clone 均保留。维护者另见[发布规则](release/README.md)。
