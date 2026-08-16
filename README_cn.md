# Perry — 你的虚拟项目办公室

> *Perry 管办公室，你管项目。*

**[English →](README.md)**

Perry 是一个面向 **Claude Code** 和 **Codex CLI** 的技能，帮你把项目盯住：你想达成什么、现在在做什么、什么卡住了、当初为什么那样决定。

你只用一个命令跟它打交道：**`/perry`**。

所有内容都以普通 markdown 文件存在你的项目目录里，你可以照常阅读、编辑、提交。没有任何东西藏在数据库里。

> 本文是 [README.md](README.md) 的中文版，内容一一对应。命令、文件名、字段名和状态值在任何语言下都保持英文原样 —— 原因见 [「换一种语言工作」](#换一种语言工作)。

---

## 它能帮你做什么

| 你想…… | Perry 给你 |
|---|---|
| 知道项目现在到哪一步了 | 每次输入 `/perry`，一屏的现状快照 |
| 定目标，并且真的跟得住 | 一份 OKR，外加当前阶段自己的目标 |
| 不用 Jira 也能管任务 | 一块任务板，带负责人、优先级和阻塞项 |
| 会话之间不再丢上下文 | 每日日志，加一份能让明天直接接上的交接记录 |
| 记住当初为什么这么选 | 一份决策记录（一个决策一个文件） |
| 动手之前先把方案想清楚 | 一份设计文档 / RFC，把需要你拍板的问题列出来 |
| 把活交给 AI agent | 写好的任务说明书，以及一条命令派发给另一个 agent 会话 |
| 消化 PDF、表格或长文档 | 一份结构化摘要，之后 Perry 引用摘要而不必重读原文 |

Perry 是给**一个人或小团队**用的。它提供结构，但不带来会议、工单和为流程而流程的东西。

---

## 安装

`setup` 会自动找到你装了哪个 agent（`claude` 和/或 `codex`）并为它安装。

把这段粘贴到一个全新的 Claude Code 或 Codex CLI 会话里：

```
Install the Perry skill set from https://github.com/ranjiao/Perry.

Steps:
1. Run: mkdir -p ~/proj && git clone https://github.com/ranjiao/Perry.git ~/proj/Perry && ~/proj/Perry/setup --yes-deps
2. Read setup's output. If it lists "Skipped installs" or asks for Xcode CLT / Homebrew, tell me — those need my permission.
3. Confirm /perry is available.
```

也可以自己装：

```bash
git clone https://github.com/ranjiao/Perry.git ~/proj/Perry && ~/proj/Perry/setup
```

`~/proj/Perry` 只是个建议位置 —— 放哪个目录都行。

**可选参数：** `setup --claude` 或 `setup --codex` 指定单个宿主，`setup --claude --codex` 两个都装。

**更新：** `cd ~/proj/Perry && git pull`（Perry 大约每周也会提醒你一次）。

安装细节、依赖、以及 Claude Code 和 Codex 的差异，见 **[INSTALL.md](INSTALL.md)**。

---

## 上手

### 全新的项目

在项目目录里输入 `/perry`。它会先问两个小问题（文档用什么语言写、仓库怎么摆），然后带你走完：

```
/perry okr init              # 一段简短访谈 → 你的目标
/perry okr plan-phase <名字> # 当前这一段工作的目标
/perry pmo                   # 建好任务板
/perry okr plan-week         # 提出本周 3–5 个任务，你来确认
```

大概 15 分钟，就配置好了。

### 已经在做的项目

别从白纸开始 —— Perry 可以直接读现成的东西：

```
/perry adopt
```

它会读你的 README、路线图、git 历史、已有的设计笔记、TODO 和 issue，然后**提议**目标、任务和决策。你不点头，它什么都不写。

### 还不确定要不要用 Perry

```
/perry diagnose
```

它会看你这个项目和 AI agent 协作的方式哪里有问题 —— 多个会话互相踩、markdown 文件堆成一片没人看、没法说清什么算做完了。它能跑在**任何**目录上，而且「你现在挺好，什么都别动」是一个完全正常的结论。它绝不会不问就给你装 Perry。

---

## 日常怎么用

想知道现状，输入 `/perry` 就够了。接下来：

| 我想…… | 输入 |
|---|---|
| 看全局 | `/perry` |
| 看有哪些能力 | `/perry help` |
| 规划本周 | `/perry okr plan-week` |
| 加一个任务 | `/perry pmo add-task` |
| 看什么卡住了 | `/perry pmo triage` |
| 标记完成 | `/perry pmo close-task <id>` |
| 把任务交给 AI agent | `/perry pmo dispatch <id>` |
| 记下一个决策 | `/perry pmo decide <主题>` |
| 写本周状态 | `/perry pmo friday-review` |
| 收工前保存上下文 | `/perry pmo handoff` |
| 起一份设计文档 | `/perry design new <名字>` |
| 在浏览器里看实时视图 | `/perry pmo viewer` |

子命令不产生歧义时可以省略车道名 —— `/perry plan-week` 和 `/perry okr plan-week` 是一回事。

---

## 三条车道

所有东西都在 `/perry` 下面。它内部分成三块，这样 Perry 知道你说的是哪类事。

### `okr` — 目标

分两层。**总体目标**（`OKR.md`）是你的使命和 1–3 个 Objective，很少改动；改了旧版本也留在文件里，你能看见自己的想法是怎么变的。**当前阶段**（比如 `phase/002-release-pipeline.md`）是你眼下正在做的事。

一个阶段**不等于一个月**。它在关键结果基本拿到时结束 —— 可能是 3 天，也可能是 8 周。不用为了凑日历演戏，也不用给第 5 天就干完的活办月末复盘。

| 命令 | 作用 |
|---|---|
| `init` | 访谈 → 总体目标 |
| `plan-phase <名字>` | 开启一个新阶段 |
| `plan-week` | 提出本周任务 |
| `snapshot` | 保存当前阶段状态，但不结束它 |
| `score-phase` | 关闭阶段，逐条给关键结果打分 |
| `revise` / `pivot` | 改目标（刻意留了点摩擦，让转向是看得见的） |
| `dashboard` | 按 Objective 看细节 |

### `pmo` — 把事推进

任务板、每日日志、决策、状态报告和交接。你一天里大部分时间都在这儿。

| 命令 | 作用 |
|---|---|
| `triage` | 从头到尾过一遍任务板，挑出停滞或卡住的 |
| `add-task` / `close-task` / `drop-task` | 任务的增、结、弃 |
| `delegate <id>` | 生成一段提示词，你贴到另一个 agent 会话里 |
| `dispatch <id>` | 把任务发给 agent，并自动收回结果 |
| `autopilot` | 你不在的时候，把所有可安全派发的任务批量发出去 |
| `digest <文件>` | 把 PDF / 表格 / 长文档变成 Perry 之后可以直接引用的摘要 |
| `decide <主题>` | 记录一个决策（背景、选项、后果） |
| `monday-plan` / `midweek-check` / `friday-review` | 每周节奏 |
| `mid-phase-review` / `end-phase-retro` | 阶段中检和收尾复盘 |
| `handoff` | 写一份交接，让明天的会话一开局就知道情况 |
| `risk` / `nudge` | 过风险；催那些在等你的事 |
| `incident <名字>` | 记录线上出了什么问题、你改了什么 |
| `viewer` | 打开项目的实时浏览器视图 |

### `design` — 先想清楚再动手

用在值得先琢磨的事情上：牵扯多个部分的改动、不好回滚的选择、或者有若干只有你能拍板的问题。Perry 起草文档、列出需要你决定的问题，然后一个一个陪你过。

| 命令 | 作用 |
|---|---|
| `new <名字>` | 新建一份设计文档 |
| `decide <id>` | 逐条回答未决问题 |
| `lock <id>` | 定稿；Perry 顺势提出实现任务 |
| `revise` / `supersede` / `drop` | 之后再改 |
| `status` | 每份文档现在处于什么状态 |

---

## Perry 真正会拦你的几条规矩

它们存在，是因为这几件事恰好是项目悄悄跑偏的地方。

- **「完成」要有凭据。** 拿不出实物就不能标完成 —— 一个文件、一个 commit、一段命令输出都行。「看着没问题」和「agent 说做完了」会被直接拒绝。
- **每个文件只有一个写入方。** 目标文件、任务板和设计文档由不同车道写，互不越界。这是防止互相覆盖的根本。
- **要紧的文件保持短。** 需要**你**亲自读的那些（目标、阶段、架构）有长度上限。快超了，Perry 会把细节挪进旁边的文件，只留摘要。目的就是让你一坐下还能读完。
- **Perry 不编数字。** 不知道就打 `—`，然后问你。
- **ID 永远带着名字出现。** 你看到的是 `REL-002（"抖动检测器"）`，不会是一串还得你去查的编号。

---

## Perry 会在你项目里写什么

全是普通 markdown，全归你：

```
your-project/
├── .perry/config.md        你的设置（语言、仓库布局）
├── OKR.md                  总体目标
├── phase/                  当前阶段 + 历史快照
├── BOARD.md                此刻的开放任务
├── journal/                每天发生了什么
├── DECISIONS.md            决策索引
├── decisions/              一个决策一个文件，含推理过程
├── design/                 设计文档 / RFC
├── evidence/               任务做完的凭据
├── weekly/                 周状态报告
├── handoff/                给下个会话的交接
├── inputs/ + knowledge/    你给 Perry 的文档，以及它的摘要
└── ...                     你自己的项目文件
```

还有几个只在你用到时才出现：`ARCHITECTURE.md`（你自己掌握的系统总览，每个被派发的 agent 都必须遵守）、`runbook/`（已上线组件怎么运维）、`incidents/`（线上出了什么事）。

**全部是可选的，用到才创建。** Perry 不会在第一天就给你铺 20 个目录。

---

## 舒服地读这些内容

markdown 写起来和 diff 起来很好，但量一大就不好读了。两个选择：

- **[aiMark](https://github.com/ranjiao/aimark)** —— 指向你的项目目录，它会实时渲染所有文件，并且原生理解 Perry 的结构。文件一变立刻刷新。
- **`/perry pmo viewer`** —— 零配置的本地页面（Today / Board / OKR / Phase / Risks / Architecture）。只读，跑在你自己机器上，Ctrl-C 就停。第一次运行会自装环境；完全不用它，你也不会多背任何依赖。

---

## 换一种语言工作

Perry 本身是英文写的，你的项目不必是。首次配置时它会记下两个**互相独立**的设置：

- **Document language（文档语言）** —— 写进文件的内容：目标、任务标题、日志、决策、设计文档。
- **Chat language（对话语言）** —— Perry 在对话里跟你说的话。默认跟随你输入的语言。

分开是有意的：一个用中文思考的英文开源项目没问题，反过来也一样。

有些东西在任何语言下都保持英文，这样工具才读得懂：ID（`REL-002`）、状态值（`in_progress`、`blocked`）、文件名、日期、路径和命令名。所以一行中文任务板是这样的：

```
| REL-002 | 抖动检测器 | Coding Agent | blocked | 等 USER-014 | evidence/… |
```

任何语言都能用来写正文。细节以及之后怎么切换语言，见 [reference/i18n.md](reference/i18n.md)。

---

## 一个项目从头到尾长这样

```
/perry okr init                 # 定目标
/perry okr plan-phase mvp       # 这一段工作的目标
/perry okr plan-week            # 本周任务 —— 你来确认
/perry                          # 每天早上：我们到哪儿了

...干活...
/perry pmo dispatch REL-002     # 把任务交给 agent
/perry pmo close-task REL-002   # 完成，附凭据
/perry pmo decide caching       # 记下为什么选了 Redis
/perry pmo friday-review        # 本周状态
/perry pmo handoff              # 收工前

/perry pmo end-phase-retro      # 关键结果基本拿到 → 收尾
/perry okr score-phase          # 打分
/perry okr plan-phase beta      # 下一个阶段
```

---

## 常见问题

**必须全套都用吗？** 不必。很多人只用任务板和日志。每个文件都是第一次需要时才创建。

**没有 git 仓库能用吗？** 能。有 git 历史会更好看，但没有任何功能强制要求。

**能用在非代码项目上吗？** 能 —— 研究、写作、运维、业务规划都行。`/perry diagnose` 还会识别这些不同类型的项目。

**我的项目已经有 `design/` 目录了怎么办？** Perry 会问你。你可以把它的文件全部放进一个子目录（比如 `perry/`），你自己的目录树一动不动。

**能加自己的命令吗？** 能。一条新车道就是一个带 `SKILL.md` 的目录，声明自己拥有哪些文件，且绝不写别人的文件。就靠这一条规矩，这套东西才能长大。

---

## 更多

- **[INSTALL.md](INSTALL.md)** —— 安装细节、依赖、Claude Code 与 Codex 的差异
- **[reference/i18n.md](reference/i18n.md)** —— 换语言工作
- **[reference/diagnose.md](reference/diagnose.md)** —— 项目体检是怎么做的
- **[reference/adoption.md](reference/adoption.md)** —— 接管已有项目是怎么做的
- **[schema/README.md](schema/README.md)** —— 文件格式，如果你要写东西来读 Perry 的文件
