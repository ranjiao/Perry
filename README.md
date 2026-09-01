# Perry — your virtual project office

> *Perry runs the office. You run the project.*

**[中文文档 →](README_cn.md)**

Perry is one skill for **Claude Code**, **OpenCode**, and **Codex CLI** that keeps track of your project for you: what you're trying to achieve, what's being worked on right now, what's blocking you, and what was decided and why.

You talk to it with **one command: `/perry`**.

It keeps everything in plain markdown files inside your project folder, so you can read them, edit them, and commit them like any other file. Nothing is hidden in a database.

---

## What it does for you

| You want to… | Perry gives you |
|---|---|
| Know where the project stands | A one-screen snapshot every time you type `/perry` |
| Set goals and actually track them | An OKR file, plus a "current phase" with its own goals |
| Run a task list without a tracker | A board of open tasks with owners, priorities and blockers |
| Stop losing context between sessions | A daily journal and a handoff note you can start tomorrow from |
| Remember why you chose something | A decision log (one file per decision) |
| Think a feature through before building | A design doc / RFC with the open questions listed for you to answer |
| Hand work to an AI agent | Written task specs and one-command dispatch to another agent session |
| Digest a PDF, spreadsheet or long doc | A short structured summary Perry can cite later instead of re-reading it |

Perry is built for **one person or a small team**. It gives you structure without meetings, tickets, or process for its own sake.

It is also not only for software. A content calendar, an operations queue and a research question have different shapes, and Perry knows four of them — see [Four kinds of work](#four-kinds-of-work).

---

## Install

`setup` finds whichever host you have (`claude`, `opencode`, and/or `codex`) and installs the one Perry skill for it.

Paste this into a fresh Claude Code, OpenCode, or Codex CLI session:

```
Install the Perry skill from https://github.com/ranjiao/Perry.

Steps:
1. Run: git clone https://github.com/ranjiao/Perry.git ~/perry && ~/perry/setup --yes-deps
2. Read setup's output. If it lists "Skipped installs" or asks for Xcode CLT / Homebrew, tell me — those need my permission.
3. Confirm /perry is available.
```

Or install it yourself:

```bash
git clone https://github.com/ranjiao/Perry.git ~/perry && ~/perry/setup
```

`~/perry` is only a suggestion — any folder works.

**Options:** `setup --claude`, `setup --opencode`, or `setup --codex` to force hosts; combine flags to install several. Add `--local` for a project-local Claude Code/OpenCode install.

**Update:** `cd ~/perry && git pull` (Perry also reminds you about once a week).

Details, dependencies and host differences: **[INSTALL.md](INSTALL.md)**.

---

## Getting started

### Starting a new project

Type `/perry` in your project folder. It will ask two quick questions (what language to write in, and how your repo is laid out), then walk you through:

```
/perry goals init              # a short interview → your goals
/perry goals plan-phase <name> # goals for the current stretch of work
/perry work                    # sets up the task board
/perry goals plan-week         # proposes 3–5 tasks for this week; you approve
```

That's roughly 15 minutes and you're set up.

### You already have a project

Perry currently has **no automated adoption or migration path**. `/perry adopt`
is not an available import workflow: its migrator and conformance ledger were
removed after this repository recorded zero migrations and zero conformance
disagreements (`TASK-261`, [ADR-011](perry/decisions/ADR-011-the-representation-layer-comes-out.md)).

Use `/perry diagnose` for a read-only analysis of an existing project. If you
then choose Perry, initialize Perry's own state explicitly; do not expect it to
rewrite or import the existing board.

### Not sure Perry is even what you need

```
/perry diagnose
```

This looks at how your project is set up for working with AI agents and tells you what's actually wrong — sessions stepping on each other, too many stale markdown files, no way to tell what's done. It also names which of the [four kinds of work](#four-kinds-of-work) your project's work actually looks like, from what's on your board rather than from what you called it — and says *cannot tell* when the signals aren't there, instead of guessing.

It works on **any** folder, and "your setup is fine, change nothing" is a perfectly normal answer. It never installs Perry without asking.

---

## Everyday use

Just type `/perry` to see where things stand. From there:

| I want to… | Type |
|---|---|
| See the whole picture | `/perry` |
| See what's available | `/perry help` |
| Plan this week | `/perry goals plan-week` |
| Add a task | `/perry work add-task` |
| Check what's stuck | `/perry work triage` |
| Mark something done | `/perry work close-task <id>` |
| Give a task to an AI agent | `/perry work dispatch <id>` |
| Write down a decision | `/perry decide adr <topic>` |
| Write this week's status | `/perry work friday-review` |
| Save context before you stop | `/perry work handoff` |
| Start a design doc | `/perry decide new <name>` |

You can drop the lane name when it's unambiguous — `/perry plan-week` and `/perry goals plan-week` are the same thing.

---

## The three lanes

Everything lives under `/perry`. Inside it there are three areas, so Perry knows which kind of work you mean.

The lanes used to be called `okr`, `pmo` and `design`. **Those names still work and always will** — `/perry pmo triage` and `/perry work triage` are the same thing — but the current names are the ones below, and they are what `/perry help` prints.

### `goals` — what you're trying to achieve  (alias: `okr`)

Two levels. **Overall goals** (`OKR.md`) are your mission and 1–3 objectives; they change rarely, and old versions stay in the file so you can see how your thinking moved. **The current phase** (`phase/002-release-pipeline.md`) is what you're doing right now.

A phase is **not a month**. It ends when its key results are hit — that might be 3 days or 8 weeks. No calendar theater, no month-end retro for work that finished on day 5.

| Command | Does |
|---|---|
| `init` | Interview → your overall goals |
| `plan-phase <name>` | Start a new phase |
| `plan-week` | Propose this week's tasks |
| `snapshot` | Save the current phase state without ending it |
| `score-phase` | Close the phase and score each key result |
| `revise` / `pivot` | Change the goals (deliberately a bit of work, so pivots are visible) |
| `dashboard` | Detail per objective |

### `work` — getting things done  (alias: `pmo`)

The task board, the daily journal, status reports and handoffs. This is where most of your day happens.

| Command | Does |
|---|---|
| `triage` | Walk the board, flag anything stale or stuck |
| `add-task` / `close-task` / `drop-task` | Task lifecycle |
| `delegate <id>` | Write a prompt you paste into another agent session |
| `dispatch <id>` | Send the task to an agent and collect the result automatically |
| `autopilot` | Dispatch everything that's safe to dispatch while you're away |
| `digest <file>` | Turn a PDF / spreadsheet / long doc into a short summary Perry can reuse |
| `monday-plan` / `midweek-check` / `friday-review` | Weekly rhythm |
| `mid-phase-review` / `end-phase-retro` | Phase checkpoints |
| `handoff` | Write a note so tomorrow's session starts informed |
| `risk` / `nudge` | Review risks; chase things waiting on you |
| `incident <name>` | Record what broke in production and what you changed |

Recording a decision used to live in this lane. It moved to `decide` on 2026-08-16, so that a settled decision and the document that settles it have one owner between them — it is `/perry decide adr <topic>` now, and the old form is gone rather than aliased.

### `decide` — decide before you build  (alias: `design`)

For anything worth thinking through first: multi-part changes, hard-to-undo choices, or anything with several open questions only you can answer. Perry drafts the doc, lists the decisions you need to make, then walks you through them one at a time.

| Command | Does |
|---|---|
| `new <name>` | Start a design doc |
| `resolve <id>` | Answer the open questions one by one |
| `adr <topic>` | Record a decision on its own — context, options, consequences |
| `lock <id>` | Freeze it; Perry proposes the tasks to build it |
| `revise` / `supersede` / `drop` | Change it later |
| `status` | Where each doc stands |

---

## Four kinds of work

Not every project is a software sprint, and the question worth asking at a review is different for each kind. Perry has four **modes**. A project that declares nothing gets `project`, which is what everything above describes.

| Mode | Ends when | The spine is | Triage asks first |
|---|---|---|---|
| `project` | the goal is met — the phase's key results are largely hit | your objectives in `OKR.md`, and the current `phase/` | is this still the right task? what is marked done with nothing to show for it? |
| `pipeline` | the item ships, or is explicitly dropped | commitments — each with a date, and someone it was promised to | which item is aging in which stage, and who is waiting on it? |
| `queue` | it doesn't. It is steady state, reviewed on a period | standing promises, plus a response time to measure them against | what missed its response time, what keeps recurring, what should become a runbook? |
| `inquiry` | the question is answered — or abandoned, which is a real answer | the open root questions | which branch is still open, and which claim has no source behind it? |

Roughly: writing, content and client deliverables → `pipeline`. Operations, support, admin — anything that *arrives* instead of being planned → `queue`. Research, analysis, meeting and market intelligence → `inquiry`. Building a thing → `project`.

What the mode changes: what closes the horizon, whether the calendar is binding or advisory, what the throttle is (priorities in a project, a per-stage limit in a pipeline, depth and age in a queue, a cap on open questions in an inquiry), what triage asks first, and what Perry pre-selects as the level of proof when you finish an item. Non-`project` modes also give board rows a `Stage` column alongside `Status` — where the item is in *this* track's sequence, as opposed to whether it is blocked or done.

You declare a mode in `.perry/config.md`, in a table called the track register:

```markdown
## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| blog | pipeline | commitments | brief→draft→review→approved→published | review:2 | 5d | 2026-W34 | V5 |
| ops | queue | commitments | new→triaged→in_progress→resolved | — | 1d | monthly | V2 |
```

One project can run several tracks at once, in different modes — a `pipeline` of client deliverables next to the `queue` that feeds it. A project with no `## Tracks` section has one implicit track called `main` in `project` mode, and behaves exactly as it did before modes existed. That is deliberate: nothing you already have changes because this exists.

`Default rung` is how much proof an item needs before it counts as finished — `V2` a structural check, `V3` a reproducible run, `V4` a fresh reviewer against written criteria, `V5` a named human signing off. Perry pre-selects the mode's default when you close an item; **this release reports, it does not refuse.**

`/perry diagnose` reads your board and tells you which of the four your work actually looks like, and what it read to decide that.

Full rules, one file each: [modes/project.md](modes/project.md) · [modes/pipeline.md](modes/pipeline.md) · [modes/queue.md](modes/queue.md) · [modes/inquiry.md](modes/inquiry.md).

---

## A few rules Perry actually enforces

These exist because they're what stops a project quietly going wrong.

- **"Done" needs proof.** You can't mark a task done without pointing at something real — a file, a commit, command output. "Looks good" and "the agent says it's finished" are rejected.
- **Each file has one owner.** The goal files, the board and the design docs are written by different lanes and never by each other. This is what keeps things from being overwritten.
- **Important files stay short.** The files *you* need to read — goals, phase, architecture — have size limits. When something would overflow, Perry moves the detail into a side file and leaves a summary. The point is that you can still read them in one sitting.
- **Perry never makes up a number.** If it doesn't know, it prints `—` and asks you.
- **IDs always come with names.** You'll see `REL-002 ("Flake detector")`, never a bare code you'd have to look up.

---

## What Perry writes into your project

All plain markdown, all yours:

```
your-project/
├── .perry/config.md        your settings (language, layout, tracks)
├── perry/                  ← everything below lives here by default
│   ├── OKR.md              overall goals
│   ├── phase/              the current stretch of work + saved snapshots
│   ├── BOARD.md            open tasks, right now
│   ├── journal/            what happened each day
│   ├── decisions/          one file per decision, with the reasoning
│   ├── design/             design docs / RFCs
│   ├── evidence/           proof that tasks were finished
│   ├── weekly/             weekly status reports
│   ├── handoff/            notes to your next session
│   └── inputs/ + knowledge/  documents you gave Perry, and its summaries
└── ...                     your actual project files, untouched
```

**Perry's files go in a `perry/` subfolder by default**, so names like `design/`, `evidence/` and `knowledge/` stay yours. `.perry/` itself stays at the top — it is what marks the folder as a Perry project, so it cannot sit behind the pointer that says where everything else went. If you'd rather have it all at the top level, `/perry relocate .` moves it there — and back, if you change your mind. That is one command either way, and it shows you every `from → to` before it moves anything.

A few more appear only if you use them: `ARCHITECTURE.md` (a system overview you own, that every dispatched agent must respect), `runbook/` (how to operate what you've deployed), `incidents/` (what went wrong in production).

**Everything is optional and created on demand.** Perry doesn't scaffold 20 folders on day one.

---

## Reading it comfortably

Markdown is great to write and diff, less great to read once there's a lot of it. Use **[aiMark](https://github.com/ranjiao/aimark)** — point it at your project folder; it renders everything live and understands Perry's structure. Reloads the moment a file changes.

Perry itself stays stdlib Python with no dependencies, and reading is deliberately somebody else's job: it had a local web console of its own until 2026-08, and deleting it is what made that sentence true.

---

## Working in another language

Perry is written in English; your project doesn't have to be. At first-time setup it records two separate settings:

- **Document language** — what gets written into files: goals, task titles, journal entries, decisions, design docs.
- **Chat language** — what Perry says to you in conversation. Defaults to mirroring whatever you type.

They're separate on purpose: an English open-source project you think about in Chinese works fine, and so does the reverse.

Some things stay English in every language, so tools keep working: IDs (`REL-002`), status words (`in_progress`, `blocked`), file names, dates, paths and command names. So a Chinese board row reads:

```
| REL-002 | 抖动检测器 | Coding Agent | blocked | 等 USER-014 | evidence/… |
```

Any language works for prose. Details, and how to switch later: [reference/i18n.md](reference/i18n.md).

---

## A typical project, start to finish

```
/perry goals init                 # set your goals
/perry goals plan-phase mvp       # goals for this stretch
/perry goals plan-week            # this week's tasks — you approve them
/perry                            # every morning: where are we

... work ...
/perry work dispatch REL-002      # hand a task to an agent
/perry work close-task REL-002    # done, with evidence
/perry decide adr caching         # write down why you chose Redis
/perry work friday-review         # this week's status
/perry work handoff               # before you stop

/perry work end-phase-retro       # key results mostly hit → wrap up
/perry goals score-phase          # score it
/perry goals plan-phase beta      # next phase
```

---

## Questions

**Do I have to use all of it?** No. Plenty of people only use the board and the journal. Every file is created when first needed.

**Does it work without a git repo?** Yes. Git makes the history nicer but nothing requires it.

**Can I use it for non-code projects?** Yes — research, writing, ops, business planning. Those are not a bolt-on: they are the [four modes](#four-kinds-of-work), each with its own horizon, throttle and triage. `/perry diagnose` recognises them from what's on your board.

**Can Perry drive the board I already have?** Not currently. `/perry diagnose`
can read and assess it, but `/perry adopt` has no import implementation after
the migration layer was removed ([ADR-011](perry/decisions/ADR-011-the-representation-layer-comes-out.md)).
Initialize Perry's state separately rather than expecting the existing board
to be migrated.

**What if my project already has a `design/` folder?** Nothing collides — Perry's own files live under `perry/` by default, so your `design/` stays yours. Setup checks for the collision before it writes anything, and only asks if you tell it to use the project root instead.

**Can I add my own commands?** Yes. A new lane is a folder with a `SKILL.md` that declares which files it owns and never writes to anyone else's. That single rule is what lets the set grow.

---

## More

- **[INSTALL.md](INSTALL.md)** — install details, dependencies, and host differences
- **[reference/i18n.md](reference/i18n.md)** — writing in another language
- **[modes/](modes/)** — the four kinds of work, one file each: what ends them, what the spine is, what triage asks
- **[reference/diagnose.md](reference/diagnose.md)** — how the project audit works
- **[reference/adoption.md](reference/adoption.md)** — how adopting an existing project works
- **[schema/README.md](schema/README.md)** — the file format, if you're building something that reads Perry's files
