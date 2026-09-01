# Perry — 你的虚拟项目办公室

> *Perry 管办公室，你管项目。*

**[English →](README.md)**

Perry 是一个面向 **Claude Code**、**OpenCode** 和 **Codex CLI** 的单一技能，帮你把项目盯住：你想达成什么、现在在做什么、什么卡住了、当初为什么那样决定。

你只用一个命令跟它打交道：**`/perry`**。

所有内容都以普通 markdown 文件存在你的项目目录里，你可以照常阅读、编辑、提交。没有任何东西藏在数据库里。

> 本文是 [README.md](README.md) 的中文版，内容一一对应。命令、文件名、字段名和状态值在任何语言下都保持英文原样 —— 原因见 [「换一种语言工作」](#换一种语言工作)。

***

## 它能帮你做什么

| 你想……          | Perry 给你                       |
| ------------- | ------------------------------ |
| 知道项目现在到哪一步了   | 每次输入 `/perry`，一屏的现状快照          |
| 定目标，并且真的跟得住   | 一份 OKR，外加当前阶段自己的目标             |
| 不用 Jira 也能管任务 | 一块任务板，带负责人、优先级和阻塞项             |
| 会话之间不再丢上下文    | 每日日志，加一份能让明天直接接上的交接记录          |
| 记住当初为什么这么选    | 一份决策记录（一个决策一个文件）               |
| 动手之前先把方案想清楚   | 一份设计文档 / RFC，把需要你拍板的问题列出来      |
| 把活交给 AI agent | 写好的任务说明书，以及一条命令派发给另一个 agent 会话 |
| 消化 PDF、表格或长文档 | 一份结构化摘要，之后 Perry 引用摘要而不必重读原文   |

Perry 是给**一个人或小团队**用的。它提供结构，但不带来会议、工单和为流程而流程的东西。

它也不只适用于写代码。内容日历、运维工单、研究课题，三者的形状本来就不一样。Perry 认识其中四种，见[四种工作形态](#四种工作形态)。

***

## 安装

`setup` 会自动找到已安装的宿主（`claude`、`opencode` 和/或 `codex`），并为它安装唯一的 Perry skill。

把这段粘贴到一个全新的 Claude Code、OpenCode 或 Codex CLI 会话里：

```
Install the Perry skill from https://github.com/ranjiao/Perry.

Steps:
1. Run: git clone https://github.com/ranjiao/Perry.git ~/perry && ~/perry/setup --yes-deps
2. Read setup's output. If it lists "Skipped installs" or asks for Xcode CLT / Homebrew, tell me — those need my permission.
3. Confirm /perry is available.
```

也可以自己装：

```bash
git clone https://github.com/ranjiao/Perry.git ~/perry && ~/perry/setup
```

`~/perry` 只是个建议位置 —— 放哪个目录都行。

**可选参数：** `setup --claude`、`setup --opencode` 或 `setup --codex` 指定宿主；多个参数可组合。Claude Code 和 OpenCode 可加 `--local` 安装到当前项目。

**更新：** `cd ~/perry && git pull`（Perry 大约每周也会提醒你一次）。

安装细节、依赖和宿主差异，见 **[INSTALL.md](INSTALL.md)**。

***

## 上手

### 全新的项目

在项目目录里输入 `/perry`。它会先问两个小问题（文档用什么语言写、仓库怎么摆），然后带你走完：

```
/perry goals init              # 一段简短访谈 → 你的目标
/perry goals plan-phase <名字> # 当前这一段工作的目标
/perry work                    # 建好任务板
/perry goals plan-week         # 提出本周 3–5 个任务，你来确认
```

大概 15 分钟，就配置好了。

### 已经在做的项目

别从白纸开始 —— Perry 可以直接读现成的东西：

```
/perry adopt
```

它会读你的 README、路线图、git 历史、已有的设计笔记、TODO 和 issue，然后**提议**目标、任务和决策。你不点头，它什么都不写。

**adopt 写出 Perry 自己的状态，只做一次。** 以前 Perry 会在运行时迁就你原有的文件格式。它的 bug 大多出在这里：两处代码对同一张表的读法不一致，中间悄悄丢掉一行。所以这份灵活性被有意放弃了，理由记在 [ADR-004](perry/decisions/ADR-004-mandatory-migration.md)。现在的规矩是：**`/perry adopt` 把你已有的东西当证据读，据此写出 Perry 的结构；它不会就地改写你的文件。** ADR-004 当初还让每个写工具拒绝未被声明合规的文件，那道门禁已经删除（`TASK-261`）—— 23 次声明里它一次都没和实时检查产生过分歧，现在没有任何写入会因为缺一份声明被拒。

「可读」不是安慰奖。`/perry diagnose` 在任何目录上都能跑，而读一个没迁移的项目，恰恰是你判断该不该迁的依据。迁移本身欠你四件事：动手之前先给出完整 diff、不丢任何一行和任何一个 ID、留一个可回退的还原点、以及绝不做你没让它做的事。

### 还不确定要不要用 Perry

```
/perry diagnose
```

它会看你这个项目和 AI agent 协作的方式哪里有问题 —— 多个会话互相踩、markdown 文件堆成一片没人看、没法说清什么算做完了。它还会说出你的活属于[四种工作形态](#四种工作形态)里的哪一种：依据是你板子上真实的样子，不是你给它起的名字；证据不足就直说「看不出来」，不猜。

它能跑在**任何**目录上，而且「你现在挺好，什么都别动」是一个完全正常的结论。它绝不会不问就给你装 Perry。

***

## 日常怎么用

想知道现状，输入 `/perry` 就够了。接下来：

| 我想……           | 输入                            |
| -------------- | ----------------------------- |
| 看全局            | `/perry`                      |
| 看有哪些能力         | `/perry help`                 |
| 规划本周           | `/perry goals plan-week`      |
| 加一个任务          | `/perry work add-task`        |
| 看什么卡住了         | `/perry work triage`          |
| 标记完成           | `/perry work close-task <id>` |
| 把任务交给 AI agent | `/perry work dispatch <id>`   |
| 记下一个决策         | `/perry decide adr <主题>`      |
| 写本周状态          | `/perry work friday-review`   |
| 收工前保存上下文       | `/perry work handoff`         |
| 起一份设计文档        | `/perry decide new <名字>`      |

子命令不产生歧义时可以省略车道名 —— `/perry plan-week` 和 `/perry goals plan-week` 是一回事。

***

## 三条车道

所有东西都在 `/perry` 下面。它内部分成三块，这样 Perry 知道你说的是哪类事。

三条车道原来叫 `okr`、`pmo`、`design`。**这些旧名字仍然有效，而且会一直有效** —— `/perry pmo triage` 和 `/perry work triage` 是同一件事。但现在的正式名字是下面这三个，`/perry help` 打出来的也是这三个。

### `goals` — 你想达成什么（别名 `okr`）

分两层。**总体目标**（`OKR.md`）是你的使命和 1–3 个 Objective，很少改动；改了旧版本也留在文件里，你能看见自己的想法是怎么变的。**当前阶段**（比如 `phase/002-release-pipeline.md`）是你眼下正在做的事。

一个阶段**不等于一个月**。它在关键结果基本拿到时结束 —— 可能是 3 天，也可能是 8 周。不用为了凑日历演戏，也不用给第 5 天就干完的活办月末复盘。

| 命令                 | 作用                    |
| ------------------ | --------------------- |
| `init`             | 访谈 → 总体目标             |
| `plan-phase <名字>`  | 开启一个新阶段               |
| `plan-week`        | 提出本周任务                |
| `snapshot`         | 保存当前阶段状态，但不结束它        |
| `score-phase`      | 关闭阶段，逐条给关键结果打分        |
| `revise` / `pivot` | 改目标（刻意留了点摩擦，让转向是看得见的） |
| `dashboard`        | 按 Objective 看细节       |

### `work` — 把事推进（别名 `pmo`）

任务板、每日日志、状态报告和交接。你一天里大部分时间都在这儿。

| 命令                                                | 作用                                   |
| ------------------------------------------------- | ------------------------------------ |
| `triage`                                          | 从头到尾过一遍任务板，挑出停滞或卡住的                  |
| `add-task` / `close-task` / `drop-task`           | 任务的增、结、弃                             |
| `delegate <id>`                                   | 生成一段提示词，你贴到另一个 agent 会话里             |
| `dispatch <id>`                                   | 把任务发给 agent，并自动收回结果                  |
| `autopilot`                                       | 你不在的时候，把所有可安全派发的任务批量发出去              |
| `digest <文件>`                                     | 把 PDF / 表格 / 长文档变成 Perry 之后可以直接引用的摘要 |
| `monday-plan` / `midweek-check` / `friday-review` | 每周节奏                                 |
| `mid-phase-review` / `end-phase-retro`            | 阶段中检和收尾复盘                            |
| `handoff`                                         | 写一份交接，让明天的会话一开局就知道情况                 |
| `risk` / `nudge`                                  | 过风险；催那些在等你的事                         |
| `incident <名字>`                                   | 记录线上出了什么问题、你改了什么                     |

记录决策以前也归这条车道。2026-08-16 它挪到了 `decide`，为的是让「一个已定的决策」和「定下它的那份文档」归同一个写入方。现在是 `/perry decide adr <主题>`，旧写法是删掉，不是设了别名。

### `decide` — 先想清楚再动手（别名 `design`）

用在值得先琢磨的事情上：牵扯多个部分的改动、不好回滚的选择、或者有若干只有你能拍板的问题。Perry 起草文档、列出需要你决定的问题，然后一个一个陪你过。

| 命令                              | 作用                |
| ------------------------------- | ----------------- |
| `new <名字>`                      | 新建一份设计文档          |
| `resolve <id>`                  | 逐条回答未决问题          |
| `adr <主题>`                      | 单独记一个决策：背景、选项、后果  |
| `lock <id>`                     | 定稿；Perry 顺势提出实现任务 |
| `revise` / `supersede` / `drop` | 之后再改              |
| `status`                        | 每份文档现在处于什么状态      |

***

## 四种工作形态

不是每个项目都是一轮软件冲刺。活的种类不同，复盘时值得问的问题也不同。Perry 认四种 **mode**。什么都不声明的项目走 `project`，也就是上面通篇在讲的那一种。

| Mode       | 什么时候算完                | 主线是什么                     | triage 先问什么                  |
| ---------- | --------------------- | ------------------------- | ---------------------------- |
| `project`  | 目标达成 —— 当前阶段的关键结果基本拿到 | `OKR.md` 里的 Objective 和当前 `phase/` | 这条还是该做的事吗？哪些标了完成却拿不出东西？      |
| `pipeline` | 东西交出去了，或者明确不做了        | commitments —— 每条都有日期，也有承诺给谁 | 哪件卡在哪个 stage 上、卡了多久、谁在等？     |
| `queue`    | 不会完。它是常态，按周期复盘        | 长期承诺，加一个用来衡量的响应时限         | 什么超了时限、什么反复出现、什么该写成 runbook？ |
| `inquiry`  | 问题答完了 —— 或者放弃，放弃也是答案  | 还开着的根问题                   | 哪条支线还开着？哪个结论没有来源？            |

大致对应：写作、内容、给客户的交付物 → `pipeline`。运维、支持、行政 —— 任何**送上门**而不是自己排期的活 → `queue`。研究、分析、会议和市场情报 → `inquiry`。做一个东西出来 → `project`。

mode 改变的是这些：什么东西能让这一段收尾；日期是硬约束还是参考；用什么控节奏（`project` 用优先级，`pipeline` 用每个 stage 的在制上限，`queue` 用积压量和等待时长，`inquiry` 用同时开着的问题数上限）；triage 第一个问什么；以及你结掉一件事时 Perry 默认要求多少证据。非 `project` 的三种还会给板子加一列 `Stage`，和 `Status` 并存 —— `Stage` 说这件东西走到本条 track 的第几步，`Status` 说它是卡住了还是做完了。

mode 声明在 `.perry/config.md` 里，一张叫 track register 的表：

```markdown
## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| blog | pipeline | commitments | brief→draft→review→approved→published | review:2 | 5d | 2026-W34 | V5 |
| ops | queue | commitments | new→triaged→in_progress→resolved | — | 1d | monthly | V2 |
```

一个项目可以同时跑几条 track，各走各的 mode —— 一条 `pipeline` 管客户交付，旁边一条 `queue` 给它供料。没有 `## Tracks` 这一节的项目，等于有一条隐含的 track 叫 `main`、mode 是 `project`，行为和没有 mode 这套东西之前一模一样。这是特意保证的：你已有的东西不会因为这个功能而变。

`Default rung` 是「算完成之前要拿出多少证据」：`V2` 一次结构检查，`V3` 一次可复现的运行，`V4` 一个不知前情的 reviewer 对着写好的验收标准过一遍，`V5` 一个具名的人签字。你结掉一件事时，Perry 会按 mode 的默认值预选。**这个版本只是报告，不会拦你。**

`/perry diagnose` 会读你的板子，告诉你这些活实际看着像四种里的哪一种，以及它是根据什么看出来的。

四份完整规则，一种一份：[modes/project.md](modes/project.md) · [modes/pipeline.md](modes/pipeline.md) · [modes/queue.md](modes/queue.md) · [modes/inquiry.md](modes/inquiry.md)。

***

## Perry 真正会拦你的几条规矩

它们存在，是因为这几件事恰好是项目悄悄跑偏的地方。

- **「完成」要有凭据。** 拿不出实物就不能标完成 —— 一个文件、一个 commit、一段命令输出都行。「看着没问题」和「agent 说做完了」会被直接拒绝。
- **每个文件只有一个写入方。** 目标文件、任务板和设计文档由不同车道写，互不越界。这是防止互相覆盖的根本。
- **要紧的文件保持短。** 需要**你**亲自读的那些（目标、阶段、架构）有长度上限。快超了，Perry 会把细节挪进旁边的文件，只留摘要。目的就是让你一坐下还能读完。
- **Perry 不编数字。** 不知道就打 `—`，然后问你。
- **ID 永远带着名字出现。** 你看到的是 `REL-002（"抖动检测器"）`，不会是一串还得你去查的编号。

***

## Perry 会在你项目里写什么

全是普通 markdown，全归你：

```
your-project/
├── .perry/config.md        你的设置（语言、仓库布局、tracks）
├── perry/                  ← 默认下面这些都放在这里
│   ├── OKR.md              总体目标
│   ├── phase/              当前阶段 + 历史快照
│   ├── BOARD.md            此刻的开放任务
│   ├── journal/            每天发生了什么
│   ├── decisions/          一个决策一个文件，含推理过程
│   ├── design/             设计文档 / RFC
│   ├── evidence/           任务做完的凭据
│   ├── weekly/             周状态报告
│   ├── handoff/            给下个会话的交接
│   └── inputs/ + knowledge/  你给 Perry 的文档，以及它的摘要
└── ...                     你自己的项目文件，原样不动
```

**Perry 的文件默认放在 `perry/` 子目录里**，这样 `design/`、`evidence/`、`knowledge/` 这些名字还是你的。`.perry/` 本身留在顶层：它是「这是一个 Perry 项目」的标记，也存着「其余东西放在哪」这个指针，所以它不能躲到指针后面去。你要是更想全摊在顶层，`/perry relocate .` 一条命令搬过去；反悔了再搬回来，也是一条命令。它动手之前会把每一条 `from → to` 摆给你看。

还有几个只在你用到时才出现：`ARCHITECTURE.md`（你自己掌握的系统总览，每个被派发的 agent 都必须遵守）、`runbook/`（已上线组件怎么运维）、`incidents/`（线上出了什么事）。

**全部是可选的，用到才创建。** Perry 不会在第一天就给你铺 20 个目录。

***

## 舒服地读这些内容

markdown 写起来和 diff 起来很好，但量一大就不好读了。用 **[aiMark](https://github.com/ranjiao/aimark)** —— 指向你的项目目录，它会实时渲染所有文件，并且原生理解 Perry 的结构。文件一变立刻刷新。

Perry 自己只用标准库、不带任何依赖，「读」这件事是刻意交出去的：它本来自带一个本地 web 控制台，2026-08 把那个删掉之后，上面这句话才真的成立。

***

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

***

## 一个项目从头到尾长这样

```
/perry goals init                 # 定目标
/perry goals plan-phase mvp       # 这一段工作的目标
/perry goals plan-week            # 本周任务 —— 你来确认
/perry                            # 每天早上：我们到哪儿了

...干活...
/perry work dispatch REL-002      # 把任务交给 agent
/perry work close-task REL-002    # 完成，附凭据
/perry decide adr caching         # 记下为什么选了 Redis
/perry work friday-review         # 本周状态
/perry work handoff               # 收工前

/perry work end-phase-retro       # 关键结果基本拿到 → 收尾
/perry goals score-phase          # 打分
/perry goals plan-phase beta      # 下一个阶段
```

***

## 常见问题

**必须全套都用吗？** 不必。很多人只用任务板和日志。每个文件都是第一次需要时才创建。

**没有 git 仓库能用吗？** 能。有 git 历史会更好看，但没有任何功能强制要求。

**能用在非代码项目上吗？** 能 —— 研究、写作、运维、业务规划都行。这不是外挂上去的：它们就是[四种 mode](#四种工作形态)，各有各的收尾条件、节奏控制和 triage 问法。`/perry diagnose` 会从你板子上的样子把它们认出来。

**Perry 能直接驱动我现有的板子吗？** 不是就地驱动。`/perry adopt` 把它当证据读，在旁边写出 Perry 自己的状态，之后 Perry 驱动的是后者。Perry 已经不再在运行时迁就任意文件格式了（[ADR-004](perry/decisions/ADR-004-mandatory-migration.md)）—— 那份灵活性正是它丢数据的那类 bug 的来源。没被 adopt 过的项目仍然可读、可以 diagnose，只是不被驱动。

**我的项目已经有** **`design/`** **目录了怎么办？** 不会撞上 —— Perry 自己的文件默认就在 `perry/` 下面，你的 `design/` 还是你的。setup 在写任何东西之前先查一遍冲突，只有你坚持要用项目根目录时它才会问。

**能加自己的命令吗？** 能。一条新车道就是一个带 `SKILL.md` 的目录，声明自己拥有哪些文件，且绝不写别人的文件。就靠这一条规矩，这套东西才能长大。

***

## 更多

- **[INSTALL.md](INSTALL.md)** —— 安装细节、依赖、Claude Code 与 Codex 的差异
- **[reference/i18n.md](reference/i18n.md)** —— 换语言工作
- **[modes/](modes/)** —— 四种工作形态，一种一份：什么让它结束、主线是什么、triage 先问什么
- **[reference/diagnose.md](reference/diagnose.md)** —— 项目体检是怎么做的
- **[reference/adoption.md](reference/adoption.md)** —— 接管已有项目是怎么做的
- **[schema/README.md](schema/README.md)** —— 文件格式，如果你要写东西来读 Perry 的文件
