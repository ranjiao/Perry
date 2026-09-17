# Diagnose explanations

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

**Which register those entries were read from is on the block, not the
entries: `work_modes.tracks_source`.** Five of its values are the ones
`perry-state` carries for the same store (`reference/snapshot.md`, step 3b),
read through the same function. The sixth belongs to this scan:

| `tracks_source` | means | what to do |
|---|---|---|
| `store` | `.perry/config.jsonl` is usable and declares at least one track; one entry per track | report per track |
| `store-default` | the store is usable (an empty store included) and declares no track; one entry for DESIGN-003's implicit `main` | report the project as a whole |
| `absent` | there is no config store; one entry for the implicit `main` | report the project as a whole; a project nobody has configured looks like this |
| `unreadable` | a store is present and could not be read; the one entry is the implicit `main` as a **stand-in**, and every track the store declares went unscanned | say the register could not be read, send the user to `perry-lint`, and do not present the verdict as the project's per-track shape. The scan raises no finding for this, so the report has to |
| `invalid` | a store is present, parses, and holds a record that does not validate; the same stand-in as `unreadable` | the same as `unreadable` |
| `unavailable` | the work-mode scan itself could not run. `available` is `false`, `register_declared` is `false` and `tracks` is `[]` | say work mode was **not measured**. Never report it as "no tracks" or as the implicit `main` |

`tests/test_tracks_source_documented.py` holds this table to what the scan
emits, in both directions.

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
