# Diagnose — auditing and refactoring how a project works with agents

Loaded when `/perry diagnose` fires. Not loaded on routine snapshots, on
`/perry adopt`, or on first-time setup.

`adopt` converts a project **into** Perry. `diagnose` asks a prior question:
**is this project's working structure sound at all?** The answer is often "yes,
leave it alone", sometimes "you need three files", and only sometimes "adopt
Perry". A diagnostic that always prescribes its own product is an installer
wearing a lab coat, and users learn to discount it within two runs.

The research this stands on — the three failure modes, the isolation ladder,
the tier discipline, the archetypes — is in
[project-archetypes.md](project-archetypes.md). This file is the procedure.

## The one rule: measure, ask, then prescribe — and prescribe the smallest thing

**Every prescription must trace to a finding, and every finding must trace to a
measurement or an answer the user gave.** No prescription may originate in
Perry's taste.

This is the same class of gate as `adopt`'s *evidence proposes, the user
declares*, and it exists for a sharper reason here. Diagnosis is inherently
judgmental: an agent asked to critique a folder will always find something to
say, and structure is the easiest thing in the world to recommend more of.
Without this rule, `/perry diagnose` becomes a machine that converts any
project into a heavier project.

Two corollaries:

- **"Do nothing" is a first-class outcome.** So is "you have too much
  structure, here is what to delete." If the scan produces no findings and the
  interview surfaces no pain, say so and stop. That run was a success.
- **The user's maintenance tolerance is a hard ceiling, not an input to
  balance.** A user who says they will maintain two files gets a two-file
  prescription, even when the scan justifies six. An unmaintained organ is
  worse than an absent one — it reports stale state that everything downstream
  believes.

## The second rule: explain the mechanism, every time

**Assume the user has read none of this.** They have not read
`project-archetypes.md`, they did not choose the thresholds, and they may never
have heard of a worktree or a context budget. A finding they cannot evaluate is
one they will either obey blindly or ignore, and both are worse outcomes than
having said nothing.

So every finding and every prescription arrives with **why it bites** — the
mechanism, in terms of something the user has plausibly already experienced.
`bin/perry-diagnose` carries one per finding ID in its `WHY` table and prints
it above the remedy; the interview and the prescription stages owe the user the
same, in the agent's own words.

**Four rules for writing one:**

1. **Mechanism, never authority.** "The agent starts quietly ignoring some of
   your rules, and you can't tell which" is useful. "This exceeds the
   recommended budget" tells the user only that a document they've never read
   disagrees with them.
2. **Their vocabulary, not Perry's.** Never say tier 0, rung, spine, archetype,
   progressive disclosure, or context rot to a user who hasn't used those words
   first. Say "the file that gets loaded at the start of every session".
3. **Two sentences inline.** Depth on request, never by default. The user came
   with a broken project, not for a seminar — and a report that lectures gets
   skimmed, which loses the findings too.
4. **Lead with the symptom they've felt.** "You've probably had the experience
   of telling the agent something twice and it still doing the old thing" earns
   attention that "instruction adherence decays past ~200 lines" does not.

**Calibrate from evidence, never by asking.** Do not ask the user how
experienced they are — it is an awkward question and the answer is unreliable.
Read it from what is already in front of you: their own words in the interview,
whether the project already uses worktrees or skills, whether the docs use the
vocabulary. Someone who says "I just open two terminals and hope" needs the
mechanism spelled out; someone who says "we tried worktrees but merging got
messy" needs you to skip straight to the integration step. Adjust silently.

### What the scan reports about work mode

A project's **shape** is the first thing an audit should name, because it is
what every later question is asked in terms of. `DESIGN-003 § 5.1` defines four
— `project`, `pipeline`, `queue`, `inquiry` — and `modes/*.md` says what tells
them apart: what closes the horizon, and what the spine is. The scan carries a
`work_modes` block, one entry per declared track, or one for the project as a
whole where no `## Tracks` register exists.

Each entry is **two separate facts, and they are not merged**:

| Field | Means |
|---|---|
| `declared_mode` + `declared` | what the register says, and whether anybody actually wrote it. `declared: false` is the implicit `main` track — a default, not a claim |
| `mode` + `confidence` | what the observable work fits. `null` is a real value |

**`null` is "cannot tell", and it is said out loud.** Three of the four modes
are recognised off columns and files a project may simply not have — `Arrived`,
`Stage since`, `Parent`, `## Intake`, an answer file. A scanner that fell back
to `project` whenever it saw none of them would print a verdict for every folder
on earth having measured none of them, which is the failure this file names one
heading up wearing the other face: a signal that never clears is worse than no
check, and so is a verdict that never abstains. The payload keeps two flavours
of it apart — `confidence: none` means nothing distinguishing was found at all,
`confidence: low` means two modes tied — and both are reported as *cannot tell*
rather than rounded up.

**Two of those columns have two owners, and the scan scores them for both.**
`modes/*.md` is the source the scanner is derived from, and read line by line it
gives `Stage since` to pipeline (the *stage clock*) **and** to inquiry (the
*question clock*, whose triage step measures the same subtraction), and
`Commitment` to pipeline (the *commitment link*) **and** to queue (the cell a
routed intake row takes, and the promise an SLA breach is named with). A signal
two modes own cannot tell those two apart — so it is scored for each of them, at
a reduced weight, which leaves the margin between its own owners at exactly
zero. It still separates them from the other two modes, which is why it is
scored at all rather than dropped. The report that follows from this: a board
whose only mode-ish column is `Stage since` is **cannot tell**, not pipeline.
That case was a live defect — a correctly-declared `inquiry` track of root
questions, whose `Parent` cells are legitimately empty and whose stage
vocabulary is its own, scored `pipeline: 3, inquiry: 0` and was reported as
mislabelled.

**`high` costs more than one column.** The scan's floor for it is a score no
single signal can reach, plus a lead of a whole structural signal over the
runner-up — so a `high` verdict always rests on at least two signals, and on at
least one that exactly one mode owns. Anything that scores but clears neither
bar is `medium`: a mode worth naming in the report, on evidence too thin to
contradict a user with. This matters because `MODE-01` fires on `high` alone.

**Report the mode with the evidence that produced it, never bare.** "Looks like
`queue` — the board carries eleven rows with an `Arrived` date and `## Intake`
has four requests waiting" is a claim the user can check and argue with. "Looks
like `queue`" is one they can only take or leave.

**Say what a number means before you use it.** A threshold stated bare reads as
arbitrary and invites dismissal. One clause is enough: "roughly 200 lines, which
is about where models start following instructions unreliably". Then add that it
is a default they can argue with — see the honesty note in stage 0.

### Plain-language glossary

When a term genuinely has to be introduced, introduce it this way and move on.
Never define more than one per exchange.

The table below is written in English because this file is; **say each one in
the chat language.** `bin/perry-diagnose` also emits English — it is a
deterministic tool whose output is read by CI and by external readers, so it is
not localized. Translate its findings on relay and keep the stable parts
verbatim: the finding ID (`LOAD-003`), the file path, the line number, and the
exact command to re-run. A translated finding ID is one the user cannot search
for. The diagnosis file written at the end follows `Document language` like
every other Perry artifact. Full rule: `reference/i18n.md § Scripts speak
English; the agent relays`.

| Term | Say this |
|---|---|
| Always-loaded file | "The file the agent reads at the start of every session, before it knows what you want." |
| Context window | "How much the agent can hold in mind at once. It gets less reliable well before it's full, not just at the end." |
| Skill | "A folder of instructions the agent only opens when the task matches its description — so it costs nothing until it's relevant." |
| Worktree | "A second checkout of the same repo in a different folder, so two sessions can work without touching the same files." |
| Append-only | "A file where you only ever add to the bottom, never edit. Two sessions can write to one at the same time without clobbering each other." |
| Verification loop | "One command the agent can run to find out whether the work is actually done, instead of deciding for itself that it looks done." |
| Evidence | "A link to the thing that proves it — the test output, the file, the sign-off. Not a claim that it's finished." |
| Goal drift | "The agent stays busy but slowly stops working on what you actually wanted, because the goal got summarized away." |
| Orphaned document | "A file nothing links to, so nothing will ever lead the agent to it." |

### Where explanation goes in each stage

- **Stage 0, opening the report.** Before the finding list, one short paragraph
  in plain language: what was measured, and the single thing that matters most
  here. Not a summary of the research.
- **Stage 2, the interview.** Questions are already outcome-framed, so they
  need no preamble. But when an answer reveals a mechanism the user hasn't
  seen — "we just both edit and fix it after" — name it in one sentence and
  move on. Do not stack up teaching moments.
- **Stage 3, each prescription.** Two lines: what changes, and what stops going
  wrong once it has. A user who cannot see the second line has no basis to
  approve the first.
- **Stage 4, on completion.** Say what should now be different in their
  day-to-day, concretely. "The agent should stop needing the same correction
  twice" beats "always-loaded context reduced to 44 lines" — though give the
  number too, since it is the evidence.

**Offer the depth, don't deliver it unasked.** Close the report with one line
pointing at `reference/project-archetypes.md` for anyone who wants the
reasoning and the sources. Most users never will, and the report has to work
completely for them.

### The other half of this rule

Explaining a finding well is worthless if the *decision* it leads to is one the
user cannot make. [user-load.md](user-load.md) covers that half and binds this
skill as much as the others:

- **Never ask a question the user cannot evaluate.** Before offering
  prescription options, check whether they can predict what will be different
  for them under each. If not: reframe in consequences, decide it and say so,
  or narrow to two.
- **An ID never travels alone.** That includes this skill's own `CTX-01` /
  `RX-3` codes — a prescription table listing bare finding IDs re-commits the
  exact problem `LOAD-01` reports. Every ID in the report carries its title.
- **Two deferrals means stop asking.** If the user answers "whatever you think"
  twice, switch to recommendations they can veto and say that is what you are
  doing. In a skill whose whole output is a list of proposed changes, this is
  the difference between a plan they own and one they nodded at.
- **The prescription list is itself a decision backlog.** Cap what you put in
  front of them, and let the maintenance ceiling from Q6 do the cutting.

## Command surface

```
/perry diagnose [--depth=quick|standard|deep] [--only=<lanes>] [--dry-run]
                [--resume] [--recheck]
```

| Flag | Effect |
|---|---|
| `--depth` | `quick` = scan + report, no interview. `standard` (default) = scan + interview + prescription. `deep` = adds per-document triage of the doc graph. |
| `--only` | Comma-separated lanes: `context,docs,concurrency,tracking`. Default all. |
| `--dry-run` | Stop after the prescription. Writes the diagnosis doc, executes nothing. |
| `--resume` | Continue an interrupted run from the doc's `stage:` + `step:`. A **shorthand**: `SKILL.md` step 2 detects the interrupted run without it, so this only skips the card. |
| `--recheck` | Re-run the scan against a previously diagnosed project and diff. See § 5. |

Runs on **any folder**. Perry state is optional and, when present, is just
another input.

## Stages

Six stages. Each records its position before handing on — `stage:` for which
stage, `step:` for where inside it.

### The resume contract

Identical to the one in [adoption.md](adoption.md#the-resume-contract), and for
the same reason: this pipeline front-loads a six-question interview, and users
close windows. **DISCOVERABLE** (found at entry, no flag — `SKILL.md § Mandatory
first move` step 2 owns it), **POSITIONED** (re-enter at `step`, not the top of
`stage`), **LOSSLESS** (a user answer is durable the instant it is given).

LOSSLESS was already half-solved here and is worth naming, because `adopt` had
to be retrofitted with what this file already did: `interview[].answer` is
declared *"verbatim; prescriptions cite it"*, so answers have always outlived
the exchange that produced them. Write the entry **as each question is
answered**, not when the interview ends.

Two things are specific to this pipeline:

**A resumed run re-validates `restore_point`; it never trusts it.** The field
records a branch or a backup directory created before the first change. Between
sessions the branch can be deleted, renamed, or merged away. Stage 4 may not
begin while `restore_point` is null, and a *stale* restore point is worse than a
null one — it reads as protection that is not there. Check it exists; if it does
not, create a new one and overwrite the field before continuing.

**Measurements are re-taken, not reused.** `measurements` is a snapshot of the
project at scan time. Resuming days later against a tree that has moved means
prescribing from stale numbers. On resume at any stage past `scan`, re-run
`bin/perry-diagnose` and diff: if a finding the prescription rests on has
closed itself, say so and drop the item rather than executing it.

### 0 · Scan (deterministic, read-only)

```
python3 "$PERRY_HOME/bin/perry-diagnose" --root . --json
```

Stdlib-only, read-only, exit 0 always. Returns the measurements: context load
against budget, the document reference graph, concurrency signals, tracking
spine, archetype signals, and a `findings[]` array with stable IDs.

**Every number in the report comes from this payload.** A field it doesn't
carry prints `—`. Do not eyeball a line count, do not estimate a doc count, and
do not assert an archetype the payload scored as `none`.

Render the scan verbatim first (the script's `--text` mode is the canonical
shape), then continue. The user seeing raw measurements before any opinion is
what makes the opinion credible.

**Thresholds are defaults, not laws.** The payload carries `thresholds`; when a
finding rests on one, say which and let the user push back. `reference/
project-archetypes.md § Part 5` records where the evidence is thin, and that
honesty is load-bearing — a user who catches the tool over-claiming once
discounts everything it says afterward.

### 1 · Read (what the scan can't measure)

The scan knows shapes, not meaning. Read, at `standard` depth:

- every tier-0 file, in full;
- the goal spine candidates the payload named;
- the index, if one exists;
- the three largest documents;
- for a git repo, `git log --oneline -30` — what the project is *actually*
  doing, versus what its docs say it's doing.

The gap between those last two is usually the most useful finding of the whole
run, and no script can compute it.

### 2 · Interview (the real requirement)

**Skip any question the scan already answered.** Asking a user something
visible in their own filesystem is how a consultation loses credibility in the
first thirty seconds.

Cap at **six questions**. Use `AskUserQuestion` (numbered free-text on Codex,
per `host-capabilities.md`). Each is outcome-framed: it asks about pain the
user has felt, not about architecture they may not have vocabulary for.

Set `step:` to the question about to be asked (`q1`…`q6`, or `audience` /
`attachment`) and append to `interview[]` the moment it is answered. On resume,
**skip every question that already has an `interview[]` entry** — including the
situational two — and re-render the collected answers back to the user before
continuing, so they can see what survived. Re-asking a question the user already
answered is the single fastest way to lose them a second time.

| # | Question | Ask when | What it settles |
|---|---|---|---|
| **Q1 · Output** | "What does this project actually produce, and who consumes it?" | Archetype confidence is `low` or `none`. | The archetype. **The user's answer always overrides the scan's guess** — the scan reads folder names, the user knows the project. |
| **Q2 · Collision** | "When you have two things to work on at once, what do you do today — wait, run two sessions in the same folder, or something else?" | Always. | Current isolation rung. Note that "wait" is a legitimate answer, not a confession. |
| **Q3 · Loss** | "In the last month, how many times did agent work get overwritten, lost, or redone because two sessions collided?" | Always. | The escalation trigger. **< 2 means do not prescribe isolation machinery**, whatever the branch count says. |
| **Q4 · Retrieval** | "Last time you needed to know why something was decided the way it was — where did you look, and did you find it?" | Always. | Whether the doc pile functions as memory, and whether a decision log is missing or merely unused. |
| **Q5 · Done** | "Take one thing currently in flight. How would you know it's finished? What would have to be true?" | Always. | The verification gap. If the answer is "it looks right" or "I read it", there is no loop, and that is usually the single highest-value finding in the run. |
| **Q6 · Tolerance** | "How much process are you willing to keep current every week — two files, five, or a full board?" | Always, and **ask it last**. | The ceiling on the prescription. Ask it after the pain is on the table, so the answer is informed rather than defensive. |

Two more, situational:

- **Audience** — "Who else reads these files: just you, teammates, or only the
  agent?" Ask when the project has more than one contributor in `git log`.
  Multi-reader projects need explicit written contracts where a solo project
  can rely on the user's memory.
- **Attachment** — "Anything here you want left alone no matter what?" Ask
  before any execute stage. Cheap, and it prevents the one mistake that ends
  trust permanently.

Record every answer verbatim in the diagnosis doc. Prescriptions cite them the
same way findings cite measurements.

### 3 · Prescribe

Compose the prescription in this fixed order, because each layer constrains the
next:

1. **Confirm the archetype** (`software` / `knowledge-base` / `ops` /
   `none-of-these`). `none-of-these` is real — say so and prescribe from the
   invariants in `project-archetypes.md § Part 4` alone rather than forcing a
   template.
2. **Check the invariants first.** The six in Part 4 apply to every project. A
   project failing an invariant has a problem no template fixes, so those
   findings outrank archetype-fit findings every time.
3. **Apply the maintenance ceiling from Q6.** Rank candidate changes by
   findings closed per unit of ongoing upkeep, then cut the list at the
   ceiling. State what you cut and why — a user who sees the deferred items can
   ask for them later.
4. **Size against the minimum viable spine.** If the project is below the floor
   (`project-archetypes.md § Part 2`), prescribe the floor and nothing more. If
   it is far above the floor with no matching pain, prescribe **subtraction**.
5. **Route Perry honestly.** Perry earns a prescription when the project needs
   goal cascade, cross-session handoff, or evidence-backed tracking, and the
   user's tolerance is a board or more. Otherwise recommend three files and say
   plainly that Perry would be overkill. Only then does `/perry adopt` follow.

Each prescription item carries:

```
| # | Change | Closes | Cost | Reversible | Needs |
|---|--------|--------|------|-----------|-------|
| 1 | Split CLAUDE.md: keep 38 rule lines, move 210 lines to skills/ | CTX-01 | ~10 min | yes (moves only) | approval |
```

`Closes` is a finding ID or a quoted interview answer. **An item that closes
neither does not go on the list** — that is the one rule, enforced at the point
it is easiest to violate.

### 4 · Execute (gated)

Execution is opt-in per item. The user picks which to run; a bulk "all" is
allowed but is never the default.

Execution is one item at a time, and `step:` carries which — `rx-<n>`, matching
the prescription id. Write it before the item runs and record the resulting
`moves[]` as each move happens rather than batching at the end; a run that dies
mid-execute must leave a `moves[]` that describes the tree as it actually is.
On resume, skip prescription items whose `status` is already `done`.

**Five safety rules, all mandatory:**

1. **A restore point before the first change.** In a git repo: commit any dirty
   tree first (ask), then create `perry/diagnose-<YYYY-MM-DD>`. Not a repo:
   copy every file that will be touched to
   `.perry/diagnose/<YYYY-MM-DD>-backup/`, preserving relative paths. Never
   begin without one. **On a resumed run, verify the recorded one still
   exists** — a branch that was deleted between sessions leaves a field that
   reads as protection and is not.
2. **Move, never delete.** Demoting a document means moving it and leaving a
   pointer behind. Merging means one file absorbing another's content, with the
   source moved to an archive path — not removed. Deletion is only ever
   *proposed*, as a follow-up task the user performs. Every move is recorded
   `from → to` in the diagnosis doc, which is what makes the whole run
   reversible by hand.
3. **Content is rewritten only with the content in view.** Never regenerate a
   file the agent has not read in full. Splitting a 900-line rules file means
   reading all 900 lines and deciding where each goes — not writing a fresh
   file from an impression of it. The user's words survive the refactor; only
   their location changes.
4. **Perry state goes through its owning skill.** If the prescription touches
   `OKR.md`, `BOARD.md`, or `design/`, route through `/okr`, `/pmo`, `/design`
   as `adopt` does. Diagnose writes exactly one file of its own —
   `.perry/diagnose/<YYYY-MM-DD>-diagnosis.md` — and one class of change on
   its own authority: non-Perry documents in the project's own tree.
5. **Anything outward-facing stops and asks.** Rewriting a public README,
   touching CI config, or changing anything that runs on push is confirmed
   separately from the batch approval, in its own words.

**Then verify, in the same run:** re-run `bin/perry-diagnose` and show
before/after on the finding counts. A refactor that doesn't move the numbers
either didn't work or wasn't needed, and both are worth saying out loud. If the
project is a Perry project, `bin/perry-lint --root .` must also pass before the
run is called complete.

### 5 · Recheck

`/perry diagnose --recheck` re-runs stages 0–1 against a previously diagnosed
project and diffs against the last diagnosis doc:

```
🔄 Diagnose recheck · <project> · <N>d since last

   Findings closed        : 4  (CTX-01, DOC-02, TRK-03, TRK-04)
   Findings reopened      : 1  (CTX-01 — always-loaded back to 240 lines)
   New findings           : 2
   Prescribed, not done   : 3  (items 4, 6, 7)
   Declined last time     : 2  (not re-proposed)
```

**Declined items are memory.** A prescription the user rejected stays in the
doc as `status: declined` and is not raised again unless its finding materially
changes. Re-proposing the same rejected advice every quarter is exactly how a
tool trains its user to skip it.

Reopened findings are the interesting line: `CTX-01` coming back means the
tier-0 file regrew, which is a *process* finding (nothing is enforcing the
budget), not a repeat of the original.

## Finding catalog

Every ID `bin/perry-diagnose` can emit. A stable ID with nowhere to look it up
is a worse experience than prose, so this table is the lookup, and the test
suite fails if the scanner gains an ID that is not listed here.

Each ID also carries a plain-language **why it bites** in the scanner's `WHY`
table, printed above the remedy in `--text` and available as `findings[].why`
in the payload. Use it, or better it — but never present a finding without one.

| ID | Severity | Fires when | Usual prescription |
|---|---|---|---|
| `CTX-01` | error | Always-loaded files exceed the line budget. | The demotion |
| `CTX-02` | warn | `CLAUDE.md` and `AGENTS.md` both exist, neither a symlink. | Keep one, symlink the other |
| `CTX-03` | error | A tier-0 file names a path that no longer resolves. | Fix or drop the reference |
| `CTX-04` | warn | No always-loaded instruction file at all. | The spine install (rules file) |
| `CTX-05` | warn | The only tier-0 file is empty. | Fill it, or delete the placeholder |
| `DOC-01` | warn | ≥30% of docs are reachable from nothing (only past 12 docs). | The orphan sweep |
| `DOC-02` | error | ≥12 documents and no index. | The index build |
| `DOC-03` | warn | Two documents claim the same title. | Merge; reference, don't copy |
| `DOC-05` | info | A document exceeds the single-doc line cap. | Fine in tier 2; a problem if it loads unconditionally |
| `CON-01` | warn | Parallel work is evident and no isolation rule is written down. | The lane declaration |
| `CON-02` | info | Files with very high commit churn — the contention surface. | Split live state from append-only history |
| `CON-03` | info | Multiple worktrees with no named integration step. | Name the merge reviewer |
| `TRK-01` | error | No goal spine. | The spine install |
| `TRK-02` | warn | Every goal file is older than the staleness threshold. | Update or retire it |
| `TRK-03` | error | No check the agent can run. | The constructed check |
| `TRK-04` | warn | No decision log. | The spine install (decisions file) |
| `LOAD-01` | warn | Many short codes in use and no way to look them up. | Add a glossary, or ship `bin/perry-explain` |
| `LOAD-02` | warn | Codes referenced in documents but defined nowhere. | Resolve, define, or drop each |
| `LOAD-03` | warn | Open decisions queued on the user past the threshold. | Triage; decide the reversible ones |
| `LOAD-04` | info | A code is defined but carries no readable name. | Title it where it's defined |
| `NS-01` | warn | A directory Perry claims holds files Perry did not write. | Relocate the state root, or move the file |
| `MODE-01` | warn | A track's **declared** work mode disagrees with what the board shows, with a clear margin. | Correct the `Mode` cell, or correct the work |
| `FIT-01` | info | Far more process than work. | The subtraction |
| `FIT-02` | info | Below the minimum viable spine. | The floor, and nothing more |

`NS-01` is the only finding about Perry's own footprint rather than the
project's structure, and it covers a gap the state root cannot. The root is
chosen once, at setup; a project adopted at `.` that later adds its own
`design/proposal.md` would otherwise have that file reported as *malformed
Perry state* — the user's own document called broken, which is exactly what
`State root:` exists to prevent, arriving by a route it does not reach.

It stays `warn` and never `error`. There is no per-path opt-out by design
(`perry/design/DESIGN-002-namespace-collision.md` decision #2 was taken
strictly), so a user may knowingly keep one file in a claimed folder — and a
permanent red for a deliberate choice is how a check trains its user to skip it.
The two remedies are `/perry relocate <path>` or moving the file; both are
reversible, and the first is one command. Before adoption the equivalent
question is answered by `perry-lint --claims`, which asks *where the state root
should go* rather than *what has encroached on it*.

`MODE-01` is the one finding whose input is a claim the user made rather than a
measurement of the tree, so the report has to hold both halves at once and say
which is which. It is described in § What the scan reports about work mode
below; the short version is that it fires only when the register **declared** a
mode, the evidence points somewhere else, and the margin is wide. Under any
other combination the honest output is the mode line, not a finding.

*Wide* is a stated number, not an impression: `confidence: high`, which no
single column can produce and which no evidence shared between two mode
contracts can produce on its own. One column used to be enough, and one of the
columns it counted belonged to the mode being accused.

The `LOAD-*` family measures something different from the rest: not whether the
project is well-formed, but whether a **human** can still follow it. See
[user-load.md](user-load.md) — the contract those findings enforce, which also
governs how this skill's own interview behaves.

Interview findings get IDs in the same shape, prefixed by the question that
produced them, and carry `source: interview` in the diagnosis doc.

## Prescription patterns

The changes that actually come up, with the shape each takes.

**The demotion** (CTX-01, most common by far). A tier-0 file past budget. Read
it in full, sort every line into three piles: *changes agent behavior* (stays),
*procedure for a recurring task* (becomes a skill in tier 1), *reference*
(becomes a document in tier 2, linked from the index). Typical outcome is 200+
lines down to 30–50. Nothing is lost; the budget is recovered.

**The index build** (DOC-02). Generate `index.md` — or the archetype's
equivalent — listing every tier-2 document with a one-line purpose. Then add
one line to the tier-0 file telling the agent to read it first. The index is
the cheapest high-value artifact in this entire skill.

**The orphan sweep** (DOC-01). Present orphans in batches of ≤ 8 with their
first heading and age. Three outcomes per doc: link it from the index, move it
to an archive directory, or mark it for deletion (the user deletes). Never
auto-delete.

**The lane declaration** (CON-01). Write the isolation rung into the tier-0
file as a short explicit section: which rung, what each session owns, where the
integration step is. For rung 1, that is an ownership table. This is a
five-line change that prevents the failure mode the user actually complained
about.

**The spine install** (TRK-01). The minimum viable spine, three files, nothing
more, unless Q6 licensed more.

**The constructed check** (TRK-03, hardest and highest value). Code projects
already have one; wire it into the workflow. Non-code projects need one built —
a structural linter over the artifact format, a fresh-context reviewer against
written criteria, or a recorded human sign-off. Prescribe exactly one, the
cheapest that fits, and make it runnable in a single command.

**The subtraction** (FIT-01). Rank existing organs by "when did this last
change a decision?" Anything unused for a quarter gets proposed for archive.
This prescription is uncomfortable to give and is frequently the right one.

## What diagnose never does

- **Never prescribes without a finding or an interview answer behind it.**
- **Never deletes a file.** Moves and pointers only; deletion is the user's.
- **Never rewrites a document it has not read in full.**
- **Never exceeds the maintenance ceiling** the user gave in Q6.
- **Never asserts an archetype** the scan scored `none` and the user did not
  confirm.
- **Never names a work mode the evidence does not distinguish.** `cannot tell`
  is printed as itself, and a mode nobody declared is never reported as wrong.
- **Never treats Perry adoption as the default outcome** — it is one
  prescription among several, and frequently the wrong one.
- **Never runs the execute stage without a restore point** — or with one it has
  not re-verified on a resumed run.
- **Never re-asks an interview question that already has an answer.** The answer
  is re-rendered for confirmation, never discarded and re-put.
- **Never resumes without being asked to.** Detection is automatic; continuation
  is the user's call.
- **Never prescribes from stale measurements.** A run resumed days later
  re-scans first.
- **Never touches another project's files.** The scan resolves one root and
  stays inside it.
- **Never reports a correctly-structured project as broken** to justify the
  run. Zero findings is a valid, and good, result.
- **Never states a finding the user has no way to evaluate.** No jargon without
  a gloss, no threshold without what it means, no prescription without what
  stops going wrong once it lands.
- **Never lectures.** Two sentences of mechanism, then the remedy. The research
  is offered as a link, not delivered unasked.

## See also

- [project-archetypes.md](project-archetypes.md) — the research: three failure
  modes, the isolation ladder, tier discipline, the three archetypes, and where
  the evidence is thin.
- [../templates/](../templates/) — runnable scaffolds the prescribe and execute
  stages copy from.
- [adoption.md](adoption.md) — the neighbouring pipeline, for when diagnosis
  concludes that Perry is in fact the right prescription.
- [host-capabilities.md](host-capabilities.md) — `AskUserQuestion` → numbered
  free-text on Codex; applies to the whole interview.
- [../state/diagnosis_TEMPLATE.md](../state/diagnosis_TEMPLATE.md) — the one
  file this pipeline writes.
