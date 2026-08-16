# Perry — 你的虚拟项目办公室

> *Perry 管办公室，你管项目。*

**[English →](README.md)**

一个面向 **Claude Code** 和 **Codex CLI** 的技能，把「虚拟 PMO + OKR + RFC 管家」这套工作方式固化下来，省得你每个会话都要重新交代一遍。**只有一个命令：`/perry`。** 目标、执行和设计文档是它内部的三条车道，分别通过 `/perry okr …`、`/perry pmo …`、`/perry design …` 进入 —— Perry 刻意不去占用你技能命名空间里的 `/okr` 和 `/design`，因为这些是别的工具也会用的常用词。

> 本文是 [README.md](README.md) 的中文版，内容一一对应。命令、文件名、字段名和状态值在任何语言下都保持英文原样 —— 原因见 [「换一种语言工作」](#换一种语言工作)。

## 🚀 一条命令安装

`setup` 会自动探测你装了哪些 agent 宿主（PATH 里的 `claude` 和/或 `codex`），并为探测到的那些安装 Perry。如果你只用其中一个，不需要加任何参数。

### 粘贴到一个全新的 Claude Code 或 Codex CLI 会话里

```
Install the Perry skill set from https://github.com/ranjiao/Perry.

Steps:
1. Run: mkdir -p ~/proj && git clone https://github.com/ranjiao/Perry.git ~/proj/Perry && ~/proj/Perry/setup --yes-deps
2. Read setup's output. If it lists "Skipped installs" or asks for Xcode CLT / Homebrew, surface those to me as TODOs — those need my consent (GUI / sudo).
3. Confirm /perry is available (it is the only command — okr, pmo and design are lanes inside it).
```

Agent 的 Bash 工具不是 TTY，所以 `setup` 会自动切到**自动跳过模式** —— 依赖检查照跑，缺什么会告诉你，但不会卡在 Y/N 提示或 sudo 密码上。加上 `--yes-deps` 表示同意自动安装那些可以无交互装好的东西。需要 GUI（Xcode CLT）或 sudo（Homebrew）的条目会在最后列成 TODO 交给你自己处理。

> **克隆到哪里**：上面例子里的 `~/proj/Perry` 只是一个建议的默认位置。Perry 放在任何地方都能工作（比如 `~/.claude/perry`、`~/code/perry`、`/opt/perry`）—— `setup` 脚本通过 `$(dirname "$0")` 解析自己的位置，然后照样写好宿主侧的符号链接。把第 1 步里的路径换成你喜欢的位置即可；本文后面的所有命令只要你保持一致地替换，效果完全相同。

> 已经装过 Perry？这样更新：
> `cd <你克隆 Perry 的目录> && git pull`

### 选择宿主

下表用 `~/proj/Perry/setup` 作为标准示例 —— 如果你把 Perry 放在别处，**请替换成你自己的克隆路径**。

| 命令 | 安装的内容 |
|---|---|
| `<perry-clone>/setup` | 自动探测：为 PATH 里存在的 `claude` / `codex` 安装。两个都有就都装。都没有则报错并给出选项。 |
| `<perry-clone>/setup --claude` | 只为 Claude Code 安装（`~/.claude/skills/`）。 |
| `<perry-clone>/setup --codex` | 只为 Codex CLI 安装（`~/.agents/skills/`）。 |
| `<perry-clone>/setup --claude --codex` | 不管探测结果，两个都装。 |

Agent 驱动的安装流程、全新 Mac 的依赖矩阵（Xcode CLT / Homebrew / Node 等）、以及 Codex 的各项降级方案（用自由文本提示替代 `AskUserQuestion`、异步派发改用 shell `&` 等），见 **[INSTALL.md](INSTALL.md)**。

## Perry 做什么

Perry 把**目标设定**、**执行管理**和**设计文档管理**配成一套，让个人或小团队项目拿到它需要的结构，而不必承受通常随之而来的官僚成本。三条车道，一个心智模型，一个命令：

| 车道 | 角色 | 拥有（唯一写入方） | 从同伴读取 |
|-------|------|------|------------------|
| **`okr`** | 「为什么」—— 目标设定伙伴 | `OKR.md`（带版本，含运行原则 + 反目标）、`phase/<NNN>-<slug>.md`（当前阶段 OKR —— **不绑日历**；焦点、规则、成本上限、用户承诺、降级、缩圈、目标、完成定义、本阶段不做）、`phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md`（自动 + 手动快照） | `BOARD.md`、`evidence/<YYYY-MM>/retro.md` |
| **`pmo`** | 「怎么做」—— 执行管家 | `BOARD.md`（实时工作记忆，≤200 行）、`journal/<YYYY-MM>/<YYYY-MM-DD>.md`（每日历史，只追加）、`PROJECT_STATE.md`、`DECISIONS.md`（索引）+ `decisions/ADR-NNN-<slug>.md`（一决策一文件）、`evidence/<YYYY-MM>/`、`weekly/<YYYY-WW>.md`、`handoff/<YYYY-MM-DD>.md`、`inputs/` + `knowledge/<topic>/`（外部文档摘要） | `OKR.md`、`phase/<NNN>-<slug>.md` |
| **`design`** | 「已定下」—— RFC 管家 | `design/<DESIGN-ID>-<slug>.md`（问题、目标、非目标、用户决策、架构、实施计划、风险、变更） | `OKR.md`、`phase/<NNN>-<slug>.md`、`BOARD.md` |

三条车道在进入的那一刻都会强制先跑一次快照 / 站会，所以你每次都是从文件的真实状态出发，而不是从感觉出发。

**为什么是一个命令而不是四个。** 这三条车道过去是作为并列技能安装的（`/okr`、`/pmo`、`/design`）。现在不是了。宿主的技能命名空间是所有已安装工具共享的，`design` 会和 `design-review`、`design-consultation`、`design-html`、`design-shotgun` 以及整个 `design:` 插件家族撞名，`okr` 会和 `lark-okr` 撞名。在一个不属于自己的命名空间里抢一个常用英文词，和往项目已有的 `design/` 目录里写东西是同一种错误 —— 而且实际使用中大家本来就是敲 `/perry` 然后让它路由。升级时 `setup` 会把旧的并列链接删掉。

## 三条车道如何协作

```
  ┌────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
  │ OKR.md (versioned) │  ──▶ │ phase/<NNN>-<slug>.md   │  ──▶ │ Weekly task proposals   │
  │  Mission           │      │  (current phase OKR)    │      │  tagged with KR ids,    │
  │  Operating Princ.  │      │  Phase Focus            │      │  Owner, Priority, DoD   │
  │  Anti-Goals        │      │  Operating Rules        │      └────────────┬────────────┘
  │  1–3 O + KRs       │      │  Cost Ceiling           │                   │ user approval
  └────────────────────┘      │  User Commitments       │                   ▼
                               │  Degradation            │      ┌─────────────────────────┐
                               │  Scope Reduction        │      │ PMO appends rows to     │
                               │  Definition of Done     │      │ BOARD + writes journal  │
                               │  Not Doing              │      │  · runs standup         │
                               │  (NOT calendar-bound;   │      │  · triages weekly       │
                               │   phase ends on KRs)    │      │  · delegates / dispatches│
                               └─────────────────────────┘      │  · writes evidence/     │
                                                                 │  · publishes weekly/    │
                                                                 │  · writes handoff/      │
                                                                 └─────────────────────────┘
```

**交接规则（最重要的契约）：**
- `okr` **写** `OKR.md` 和 `phase/`。周任务只**提议**，从不自己写。
- `pmo` **写** `BOARD.md`、`journal/`、`PROJECT_STATE.md`、`DECISIONS.md`、`evidence/`、`weekly/`、`handoff/`。**读** OKR 和设计文档作为上下文。
- `design` **写** `design/<DESIGN-ID>-<slug>.md`。锁定时**提议**实施任务，从不自己写。
- 每条车道都可以自由读其他车道的文件；没有任何车道写自己范围之外的文件。这是一份**文件归属**契约，不是技能注册契约 —— 所以收敛成一个命令并没有改变它。

## OKR 阶段 —— 为什么没有月度周期

Perry 的 OKR 分两层，且完全不受日历束缚：

1. **总体 OKR**（`OKR.md`）—— 带版本，无时间边界。使命、运行原则、1–3 个目标 + KR、反目标。通过 `okr revise` 修改（追加一个新的 `## v<N>` 块；旧版本保留可读，便于审计）。
2. **当前阶段**（`phase/<NNN>-<slug>.md`）—— 活跃的战术承诺。**不绑日历**。一个阶段在它的 KR 大体达成时结束，而不是在某个日期到来时结束。

```
phase/
├── CURRENT                                       ← 一行指针："002-release-pipeline"
├── 001-system-build.md                           ← 已评分（已关闭）
├── 002-release-pipeline.md                        ← 活跃（当前；被 CURRENT 指向）
└── snapshots/
    ├── 2026-05-01-001-system-build-final.md     ← 终态快照，score-phase 时写入
    ├── 2026-05-13-002-release-pipeline.md        ← 心跳快照（阶段中途）
    └── 2026-05-27-002-release-pipeline.md        ← 又一次心跳
```

### 为什么用阶段而不是月份

由 agent 推进的项目，往往第一周就把按月划定的 KR 做完了，然后花三周做无用功来填满日历。「月」是人类团队节奏的单位，不是项目状态的单位。Perry 用**阶段 OKR** 取代月度 OKR，因此：

- **结束阶段的是 KR，不是日历。** 工作第 5 天就做完了，就不必再演一场「月末复盘」。
- **阶段长度由项目决定**，典型是 2–6 周。有的阶段 3 天，有的 8 周。都正常。
- **阶段快照保留历史**（手动 + 心跳），而不强加一个僵硬的评审周期。
- **编号让顺序和检索保持干净** —— `001`、`002`……由 `plan-phase` 自动分配。用户选的 slug 说明这个阶段在做什么（`system-build`、`release-pipeline`、`pre-production-hardening`）。

### 用什么取代日历纪律

OKR 站会里会浮出两个软提示。两个都不强制：

- **KR 进度提示** —— 当 ≥80% 的 `commit` 型 KR 已达成 → *「要不要 `/perry okr score-phase` 然后开下一个阶段？」*
- **心跳提示** —— 距上次快照 ≥ `phase_heartbeat_days`（默认 14，可在 `.perry/config.md` 覆盖）→ *「跑一下 `/perry okr snapshot` 把当前状态存下来。」*

两个你都可以无视。重点不是执行某种节奏 —— 而是确保没有阶段在无人察觉中无限延长，也没有大块工作从未被快照过。

### 阶段生命周期命令

| 命令 | 什么时候用 | 写什么 |
|---|---|---|
| `/perry okr plan-phase <slug>` | 开启新阶段。自动分配 `#NNN = max + 1` | `phase/<NNN>-<slug>.md`（10 个必备章节）+ 更新 `phase/CURRENT` |
| `/perry okr snapshot` | 心跳 / 转向前 / 里程碑留存 | `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>.md`（**不**结束阶段） |
| `/perry okr score-phase` | 关闭当前阶段 | 逐 KR 评分 → `phase/<NNN>-<slug>.md § Retro` + `evidence/<YYYY-MM>/retro.md` + 自动写一份带 `-final` 后缀的快照；清空 `phase/CURRENT` |
| `/perry pmo mid-phase-review` | 中点检查（或任何你想查的时候） | `evidence/<YYYY-MM>/midphase-review-<NNN>-<slug>.md`；若缩圈规则已武装则执行 |
| `/perry pmo end-phase-retro` | 阶段收尾复盘（通常紧接着跑 `score-phase`） | `evidence/<YYYY-MM>/retro.md`（被 `okr score-phase` 消费） |
| `/perry pmo rollover` | `score-phase` 之后：清理 BOARD 上的延续项 | 交接给 OKR；由用户运行 `plan-phase <next-slug>` |

### 阶段缩圈规则 —— 两类触发器

在阶段 OKR 里，`阶段缩圈规则` 章节声明**一旦进度滑坡，这个阶段将如何自动砍范围**。挑一个或两个都要 —— 先触发的那个生效。**不允许基于日历日期的触发器。**

- **阶段日触发** —— 「若到阶段第 `N` 天（从 `plan-phase` 写入之日算起）点名的 USER-XXX 仍未关闭，目标 N 收缩为它唯一的必达项。」
- **KR 进度触发** —— 「若到阶段第 `N` 天，承诺型 KR 达成度低于 `X%`，范围收缩到下面点名的必达项。」

### OKR 跨阶段防火墙

`okr plan-phase` 会读取最新的 `architecture/audit-history/<date>.md` 和 `ARCHITECTURE.md § Open questions`（如果这些文件存在）。在每一条未解决的漂移项被明确处理之前，它**拒绝写入**新的阶段 OKR —— 处理方式可以是：变成一条 KR、通过编辑 `ARCHITECTURE.md` 接受它、用一条 ADR 明确推迟、或者写进 `本阶段不做` 并给出理由。架构文档是那根杠杆；OKR 的 `plan-phase` 是那个周期性的强制函数，防止漂移在一个个阶段之间悄悄累积。

### 什么仍然绑日历（这些是存储，不是项目状态）

一个阶段可以横跨任意数量的 journal 月份 / evidence 月份 / ISO 周 —— 它们和阶段是正交的：

- `journal/<YYYY-MM>/<YYYY-MM-DD>.md` —— 每日日记；同一个阶段日在一条日记里可能是 5 月 5 日周一，在另一条里是 6 月 13 日周五
- `evidence/<YYYY-MM>/<TASK-ID>-*.md` —— 按月分桶只是为了好检索，不是为了划范围
- `weekly/<YYYY-WW>.md` + `/perry okr plan-week` —— 「周」作为战术规划中任务批次的粒度

## 文件模型 —— 按读者分三层

Markdown 很适合**产出**状态（agent 编辑、git diff、注入 LLM 提示词）；它不适合**消费**超过 100 行的状态。Perry 的解法是按**谁来读**给每个文件分类 —— 并且不试图自己去当那个读者。

| 层 | 用途 | 格式 | 硬上限 | 例子 |
|---|---|---|---|---|
| **1 —— 用户读写** | 战略性；用户**必须**读原始形态 | markdown | 每文件有 | `OKR.md` ≤200 · `ARCHITECTURE.md` ≤500 · `phase/<NNN>-<slug>.md` ≤300 · `runbook/<component>.md` ≤150 · `.perry/{config,hook}.md` |
| **2 —— agent 内部状态** | 持续变动的活状态，agent 频繁读写 | markdown | 无（原有软上限保留） | `BOARD.md` · `journal/` · `evidence/` · `decisions/` · `incidents/` · `weekly/` · `handoff/` · `PROJECT_STATE.md` · `phase/snapshots/` · `phase/<NNN>-linkage.md` · `architecture/audit-history/` · `knowledge/` |
| **3 —— 消费界面** | 富态地阅读状态 | （不是 Perry 的产出） | — | **aiMark** · `bin/perry-viewer` |

**第 1 层的硬上限不可协商。** 当一次 OKR / PMO 写入会把某个第 1 层文件顶过上限时，技能会**拒绝写入**，并把溢出部分挤进一个兄弟文件（通常是 `evidence/<YYYY-MM>/...-appendix.md` 或 `architecture/sections/§<N>-<topic>.md`），主文件只留 §-章节索引 + 每节一段摘要。目的是保住第 1 层「一次坐下能读完」这个属性。

**Perry 不写第 3 层。** 它曾经写过 —— `/perry pmo render` 会往 `perry-views/` 里生成一次性 HTML —— 那个功能已经删掉了。渲染是前端的活，用语言模型来做又慢又贵，而且每次跑出来的东西都不一样。

- **[aiMark](https://github.com/ranjiao/aimark)** 是首选界面：把它指向项目目录，它会监听每个文件、实时渲染 markdown，并且原生理解 Perry 的结构（OKR → KR → 任务 → agent）。技能一写文件它就重载。
- **`bin/perry-viewer`** 作为零配置的本地兜底保留 —— 一个可选的、只读的 localhost Flask 控制台（Today / Board / OKR / Phase / Risks / Atlas / Pulse / Architecture），每次请求都重新读你的 markdown。首次运行会自动装好自己的 venv；Ctrl-C 停止；没有常驻进程。完全无视它，你就不会多背任何依赖。见 `viewer/README.md`。

Perry 对第 3 层的全部义务，就是**按声明的结构**写好第 1、2 层，让读者不用猜就能解析。那个结构就是 `schema/state-schema.json`，`bin/perry-lint` 是执行它的人 —— 既对 Perry 自己的解析器，也对任何读同一批文件的前端。见 [schema/README.md](schema/README.md)。

要点：让 markdown 继续做**对生产者友好**的事实源（它擅长的地方 —— diff、编辑、注入），让真正的前端做**对消费者友好**的展示层（它擅长的地方 —— 表格、SVG、筛选、热重载）。不要跟 markdown 的短板硬碰硬；绕过去。

## 关键概念

**状态模型（PMO）：** `not_started · blocked · in_progress · review · done · dropped`。一个任务不能在没有 `evidence/<YYYY-MM>/<TASK-ID>-*.md` 下的证据文件、或可引用产物（commit 哈希、命令输出、看板路由）的情况下被标为 `done`。

**负责人模型（PMO）：** `User · PMO Agent · Coding Agent · Research Agent · Review Agent · User + Agent`。这个集合是显式的，好让 PMO 能给其他 Claude 会话写出像样的委派提示词；只有用户能做的决定，在用户输入队列里是一等公民。

**节奏（PMO）：** 周一规划 → 周中检查 → 周五复盘 → 阶段中评审 → 阶段末复盘。每一个都是一个子命令。节奏类工作记在 `## 例行节奏` 下，不占用 P0 名额。

**证据必需（PMO）：** 每一个 `done` 都指向一个真实产物。「看起来没问题」「应该能跑」「agent 觉得做完了」被明确拒绝。

**版本化（OKR）：** `OKR.md` 会累积 `## v1`、`## v2` 等带日期的版本块。`okr revise` 追加新版本；旧版本保持可读。转向要付出摩擦成本，而不是被静悄悄地改掉。

**反目标（OKR）：** 在总体和阶段两个层面都是一等承诺。每次复盘都检查有没有被违反。

**成本上限（OKR，按阶段或总体）：** 数字 + 软回退阈值 + 硬上限 + 接线状态（`已在代码中生效` vs `仅文档`）。仅文档的上限在被真正接线之前，每次快照都会被标为未决风险。

**交接文档（PMO）：** `handoff/<YYYY-MM-DD>.md` 是会话之间的桥。存在交接文档时，每个 PMO 会话的第一句话都是：「读 `handoff/<latest>.md`，然后告诉我你的状态。」它取代了往回翻聊天记录。

**外部文档摘要（PMO）：** `inputs/` 是用户丢给 PMO 的 PDF / Excel / 截图 / 粘贴文本的原始落地区。`/perry pmo digest <path>` 读源文件、起草结构化摘要（TL;DR + 带引用的关键事实 + 未决问题 + PMO 必须记住的东西 + 章节地图），通过 `AskUserQuestion` 与用户核对关键事实，然后把源文件和摘要一起移进 `knowledge/<topic>/`。后续的规格 / 决策 / 日记按路径引用这份摘要，而不再重读源文件。摘要带 `Status: active | eternal | archived | superseded` 字段；归档评审在 `mid-phase-review` 和 `end-phase-retro` 中自动跑。**范围有界** —— 设计目标是每个项目 5–30 份活跃摘要；这是人类式的记笔记，不是 RAG。完整规格见 `pmo/reference/digests.md`。

**决策拆分（PMO）：** 项目根的 `DECISIONS.md` **只是索引**（≤200 行）：一张列出所有 ADR 的表，含 ID / 标题 / 类型 / 日期 / 状态 + 指向单决策文件的链接。完整推理放在 `decisions/ADR-NNN-<slug>.md` —— 一决策一文件，含 Context / Options / Chosen / Consequences / Evidence / Sunset criteria。`/perry pmo decide <topic>` 用配置的文档语言创建新 ADR；`--supersede` / `--expire` / `--archive` 管理生命周期（状态变化时文件不移动，只翻转 header 字段）。站会只读索引 —— 单决策内容按需加载。和 BOARD.md vs `journal/` 是同一个扩展模式。见 `pmo/reference/decisions.md`。

**自动驾驶（PMO）：** `/perry pmo autopilot` 从上到下走一遍 BOARD，把每一条「可安全派发」的行都派出去，直到预算耗尽（默认 10 次派发 / 2 小时 / 3 次失败）。每个项目的第一次运行强制是 dry-run + 简报。硬安全护栏：绝不自动置 `done`、绝不修改规格、绝不越过 hook 的安全清单、绝不自动重试。停止信号：关闭会话 或 `touch ~/.cache/perry/autopilot.stop`。见 `pmo/reference/autopilot.md`。

**反漂移纪律 —— ARCHITECTURE.md / runbook / 事故记录（PMO）：** 当代码由 agent 写时，用户会同时失去架构掌控力和运维掌控力。Perry 的对策（全部**可选、惰性创建** —— 首次使用时才生成，不在 bootstrap 时创建）：

- **`ARCHITECTURE.md`（核心那一份）** —— 项目根下一份用户拥有、agent 只读的文档。固定 8 章结构（使命与范围 / 组件 / 边界与依赖 / 数据流 / 契约 / 不可协商项 / 未决问题 / 变更日志）。每个被派发的 agent 都会在提示词里拿到全文，并且必须产出一份 `ARCHITECTURE COMPLIANCE` 声明，列出它触及的 §-章节。在 `close-task` 能翻成 `done` 之前，一个**独立的评审 agent**（另一个 Claude 子 agent 或一次 codex 调用）会读同一份文档加上 diff，对抗性地反驳主 agent 的声明 —— `PASS` 或 `FAIL`。`FAIL` 时 `close-task` 拒绝关闭。这就是那个保证机制：一个触及架构的任务，在文档与 diff 的一致性检查通过之前无法关闭。代价是每次派发多一次小的 LLM 调用。见 `pmo/reference/architecture.md`。
- **`runbook/<component>.md`** —— 每个已部署组件一个文件，四个必备章节（它做什么 / 怎么判断它健康 / 常见故障 + 现成操作 / 升级路径）。任务规格声明 `Deployed: yes | no`；`close-task` 拒绝在没有对应 runbook 的情况下关闭一个 `Deployed: yes` 的任务。见 `pmo/reference/runbooks.md`。
- **`incidents/<YYYY-MM-DD>-<slug>.md`** —— 每次线上故障一份事后记录。`/perry pmo incident close` 强制一个 3 问闸门（知识 / **架构** / runbook）：每个问题都必须产出一个具体产物，或者一个带理由的明确跳过。「架构」那问追问的是：这次事故是否说明 `ARCHITECTURE.md` 写错了、缺了、或者过期了。见 `pmo/reference/incidents.md`。
- **`/perry pmo health-check`** —— 元执行器，把 `architecture-audit` + `runbook-check` + 摘要过期 + 事故模式合成一份报告，写到 `evidence/<YYYY-MM>/health-check-<date>.md`。由 `mid-phase-review` 和 `end-phase-retro` 内联调用。见 `pmo/reference/health-check.md`。

这四者协同工作：`ARCHITECTURE.md` 是用户掌控的脊柱；事故揭示脊柱哪里错了；runbook 让用户不必读 agent 写的代码也能运维；health-check 是周期性的现实校验。它们都不是强制的，但每一个都是 Perry 用来让 agent 建造的项目留在用户控制之下的契约。`okr plan-phase` 里的跨阶段防火墙（见 § OKR 阶段）是那个强制未解决漂移在下个阶段开启时被处理的机制。

## 换一种语言工作

Perry 是用英文写的；你的项目不必是。首次配置会往 `.perry/config.md` 写入两个**互相独立**的设置：

| 设置 | 管什么 | 默认值 |
|---|---|---|
| `Document language` | 一切**写进文件**的内容 —— OKR 叙述、看板标题、日记、ADR 推理、设计文档、委派提示词 | English |
| `Chat language` | 一切**在对话里说**的内容 —— 仪表盘、TL;DR、建议动作、每个问题的选项文字 | `follow user`（跟随你输入的语言） |

它们分开，是因为常见情况本来就需要它们分开：一个你用中文思考的英文开源项目；或者一个文档是中文、但状态行你看英文完全没问题的内部项目。

**任何语言下都不翻译的东西**：ID（`REL-002`、`KR-O1.2`）、枚举值（`in_progress`、`blocked`）、文件名和阶段 slug、`P0`/`P1`/`P2`、日期、路径、命令名。所以一条中文看板行长这样：

```markdown
## P0（本周期必须完成）

| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|
| REL-002 | 抖动检测器 | Coding Agent | blocked | 等 USER-014 | evidence/2026-08/REL-002-spec.md |
```

叙述和列头本地化了，机器读的 token 一个没动。章节标题和列头通过 `schema/state-schema.json § i18n` 里声明一次的词表解析，`bin/perry-lint`、`viewer/parsers.py` 和任何外部前端都读同一份 —— 因此**一个中文项目能干净通过 lint，并产出和英文项目完全相同的仪表盘 payload**，`tests/fixtures/sample-project-zh/` 就是保证这一点的固件。

没有词表的语言，叙述部分依然完整支持 —— 设 `Document language: Français`，所有标题和叙述都会是法语，章节标题保持英文。要教 Perry 本地化一门新语言的结构，只需改 schema 加一个固件：见 [reference/i18n.md](reference/i18n.md)。项目中途换语言的规则也在那里（Perry **不会**回溯翻译，以及为什么）。

## 典型流程（首次，任何项目）

```
/perry okr        → init                              # 访谈：使命、运行原则、
                                                 # 1–3 个目标 + KR、反目标、版本 v1
/perry okr        → plan-phase <slug>                 # 完整阶段 OKR；自动分配 #NNN
/perry okr        → plan-week                          # 为本 ISO 周提议 3–5 个候选任务
                                                 # 用户批准其中一部分

/perry pmo        → （自动）写 BOARD 行 + 完整任务定义到 journal/<YYYY-MM>/<today>.md，跑站会
... 日常工作 ... /perry pmo close-task ... /perry pmo decide ... /perry pmo delegate <id> ...
/perry pmo        → digest <inputs/...>                # 每当用户丢进外部文档（PDF/Excel/笔记）
/perry pmo        → autopilot                          # 你不在时批量派发够条件的规格
/perry pmo        → friday-review                      # 写 weekly/<YYYY-WW>.md
/perry pmo        → handoff                            # 停下之前写 handoff/<today>.md

/perry okr        → snapshot                           # 心跳快照（或 14 天后自动提示）
/perry pmo        → mid-phase-review                   # 阶段中点；若缩圈规则已武装则执行
/perry pmo        → end-phase-retro                    # KR 大体达成时；写 evidence/<YYYY-MM>/retro.md

/perry okr        → score-phase                        # 消费复盘，填阶段文件的 Retro，写快照
/perry pmo        → rollover                           # 清理 BOARD 延续项，交接给 OKR
/perry okr        → plan-phase <next-slug>             # 下一个阶段开始（自动 #NNN+1）
```

## 项目文件布局（所有技能 bootstrap 之后）

```
<project_root>/
├── .perry/
│   ├── config.md                       ← 文档语言 + 对话语言、仓库布局（single | split）、状态根
│   └── hook.md                         ← 项目专属附加规则（可选）
├── OKR.md                              ← okr（总体，带版本）
├── phase/
│   ├── CURRENT                          ← okr（一行指针：当前阶段的 <NNN>-<slug>）
│   ├── 001-system-build.md              ← okr（阶段 #001，已评分）
│   ├── 002-release-pipeline.md           ← okr（阶段 #002，活跃 —— 当前）
│   └── snapshots/
│       ├── 2026-05-01-001-system-build-final.md    ← score-phase 时的终态快照
│       └── 2026-05-13-002-release-pipeline.md       ← 心跳快照
├── BOARD.md                             ← pmo（实时工作记忆；≤200 行；关闭的任务会离开）
├── journal/
│   └── 2026-05/
│       ├── 2026-05-01.md                ← pmo（当天的状态变更 / 新任务 / 决策）
│       ├── 2026-05-02.md
│       └── ...                          ← 一天一个文件；当天结束后只追加
├── PROJECT_STATE.md                     ← pmo（跨阶段仪表盘）
├── DECISIONS.md                         ← pmo（只是索引，≤200 行）
├── decisions/
│   ├── ADR-001-pmo-bootstrap.md         ← pmo（一决策一文件；Context/Options/Chosen/Consequences）
│   ├── ADR-002-cache-backend.md          ← Status: active | superseded | expired | archived（header 字段；文件不移动）
│   └── ...
├── design/
│   └── DESIGN-001-process-mgmt.md       ← design（RFC）
├── evidence/
│   └── 2026-05/
│       ├── TASK-001-deliverable-name.md          ← pmo（单任务产物）
│       ├── midphase-review-002-release-pipeline.md
│       └── retro.md                              ← 被 okr `score-phase` 消费
├── weekly/
│   └── 2026-W18.md                      ← pmo（状态报告）
├── handoff/
│   └── 2026-05-01.md                    ← pmo（会话之间的桥）
├── inputs/                              ← 外部文档的原始落地区（临时）
│   └── 2026-05-07-vendor-acme-q1-report.pdf   ← 等着被 /perry pmo digest
├── knowledge/                           ← 消化后的组织化文库
│   ├── INDEX.md                                ← pmo（自动维护的目录）
│   ├── _shared/
│   │   └── USER-002-constraints-digest.md     ← 项目宪法级（eternal）
│   ├── vendor-acme/
│   │   ├── 2025-12-09-contract.pdf            ← 从 inputs/ 移过来
│   │   └── 2025-12-09-contract-digest.md      ← PMO 的结构化摘要
│   └── research/
│       └── kubernetes-best-practices-2024-digest.md
│
│   # 下面四个是可选的 —— 首次使用时惰性创建，不在 bootstrap 时创建。
├── ARCHITECTURE.md                      ← 用户拥有的系统设计唯一事实源。
│                                         注入每个被派发 agent 的提示词。
│                                         独立评审 agent 会对照它核验每次代码改动。
├── architecture/
│   └── audit-history/
│       └── 2026-05-13.md                        ← 每次审计的报告（机械扫描 + LLM 一致性扫描）
├── runbook/                             ← 已部署组件的可运维性（仅当有规格标了 `Deployed: yes`）
│   ├── INDEX.md                                 ← 自动维护的目录
│   └── deploy-daemon.md                         ← 每组件：做什么 / 健康 / 故障 / 升级
├── incidents/                           ← 事后记录（仅当你用 /perry pmo incident）
│   ├── INDEX.md
│   └── 2026-05-12-deploy-stuck.md               ← 时间线 + 根因 + 修复 + 衍生改动
│
└── ... (你真正的项目文件)
```

## 确定性层（不涉及 LLM）

Perry 的状态活在 markdown 里，但**读取**它的是普通代码。四个只依赖标准库的脚本做那些 LLM 不该做的事：

| 脚本 | 做什么 | 谁在用 |
|---|---|---|
| `bin/perry-state` | 一趟读完整个项目，输出仪表盘模型（`--json`）或预格式化的行（`--dashboard`）。 | 所有技能的站会仪式；任何需要计数的子命令 |
| `bin/perry-lint` | 对照 `schema/state-schema.json` 校验状态文件 —— 章节、表格列、状态词表、ID 模式、跨文件关联完整性。`--templates` 校验 Perry 自己的模板。 | Bootstrap、任何结构性写入之后、CI |
| `bin/perry-diagnose` | 度量一个项目**为 agent 工作组织得如何** —— 上下文负载对预算、文档引用图、并发信号、追踪脊柱 —— 并输出带稳定 ID 的发现。可以在**任何**目录上跑，是不是 Perry 项目都行。 | `/perry diagnose` 的第 0 阶段 |
| `bin/perry-explain` | 把一个 ID（`REL-002`、`ADR-003`、`P-O1.2`）解析成它是什么、在哪里定义、在哪些地方被引用。`--all` 打印术语表，`--dangling` 列出被引用但无处定义的 ID。它读的是 markdown 实际使用的形状，所以在**任何**项目上都能用。 | 任何时候一个 ID 不带标题出现；`/perry diagnose` 的 `LOAD-*` 发现 |

为什么这重要：在此之前，仪表盘上的每个数字都是 agent 读十几个文件用眼睛数出来的 —— 既贵，又恰好是那种会悄悄出错的事。现在数字是算出来的，agent 只负责讲述，而 `—` 意味着「确实不知道」而不是「没去看」。

```bash
bin/perry-state --dashboard        # 现在的状态是什么
bin/perry-lint --root .            # 每个状态文件格式是否良好
bin/perry-diagnose --root . --text # 这个项目的结构究竟合不合理
bash tests/run                     # 整套测试（只用标准库，不需要 venv）
```

`schema/state-schema.json` 是 SKILL.md 的文字、`state/*_TEMPLATE.md` 和 `viewer/parsers.py` 三方都必须一致遵守的唯一契约 —— 见 [schema/README.md](schema/README.md)。`tests/` 钉住这份一致性；`--templates` 检查就是模板和解析器分道扬镳时会失败的那个。

## `/perry diagnose` —— 这个项目本身搭得对吗？

上面所有内容都预设了这个项目应该按 Perry 的方式来跑。`/perry diagnose` 问的是更前面那个问题，可以在**任何**目录上跑 —— 包括从没装过 Perry 的目录，也包括那些诚实答案是「别动它」或者「你需要的是三个文件，不是一个 PMO」的项目。

它瞄准 agent 驱动的项目实际崩掉的三种方式：

| 失效 | 长什么样 | 靠什么修 |
|---|---|---|
| **会话互相干扰** | 两个会话改同一个文件；其中一个的工作消失了。Git `index.lock` 报错。 | 隔离阶梯上能扛住你**实际观察到**的争用的最低那一档 —— 常常就是「一次只跑一个」 |
| **文档丛林** | 40 个 markdown 文件，一半过期，两个互相矛盾，没人找得到该看哪个。 | 一套分层纪律，对每次会话加载的量设硬预算，外加一个 agent 优先读的索引 |
| **目标漂移** | 活动量很足，但说不出什么算做完了、或者这些做了有没有意义。 | 一根外部化的目标脊柱、一份决策日志，以及一个 agent 真能跑起来的检查 |

```bash
/perry diagnose              # 扫描 → 访谈 → 开方 → 执行，逐项确认
/perry diagnose --dry-run    # 开完方就停，什么都不改
/perry diagnose --recheck    # 上次之后漂移了什么
```

六个阶段，管辖规则是：**每一条处方都能追溯到一个发现，每一个发现都能追溯到一次度量或你说过的一句话。** 没有任何东西因为 Perry 喜欢就被开出来。两种结果始终是一等公民：零发现，以及一份纯粹做减法的处方。

背后的研究 —— 隔离阶梯、分层预算、三种原型（软件、知识库、运营/内容），以及对证据薄弱之处的明确交代 —— 在 [reference/project-archetypes.md](reference/project-archetypes.md)。流程在 [reference/diagnose.md](reference/diagnose.md)。每种原型可直接运行的脚手架在 [templates/](templates/)，其中包括为两种原生缺乏验证环节的原型补上的真实验证回路（知识库用 `kb-lint`，运营/内容用 `deliverable-lint`）。

## 在它之上设计你自己的技能

Perry 的构建方式让你可以在不破坏内核的前提下扩展它。一些自然的补充方向：

- **`research-journal`** —— 拥有 `RESEARCH.md`；消费某个领域 MCP；把发现喂给 OKR 转向。
- **`risk-review`** —— 通过领域 MCP 做周期性检查；一旦触发就经由 PMO 提 P0 任务。
- **`experiment-runner`** —— 在子会话里协调批处理作业；把与 KR 相关的数字报回 OKR。

往这个家族里加新技能的规则：在你的 `description:` frontmatter 里声明你拥有哪些文件、只读哪些文件，并且绝不写入另一个技能拥有的文件。就这一条纪律，让这套东西能扩展到两个成员以上。
