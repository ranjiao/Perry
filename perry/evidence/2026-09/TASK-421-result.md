# TASK-421 — result

> Written incrementally and committed as it was produced, per the brief.
> Branch: `task-421-scratch-collisions`, cut from `70458893`.

## 0 · Conditions of this round

**Scratch path used.** `/private/tmp/claude-501/-Users-bytedance-proj-Perry/b59246e8-0d9c-4c63-9ac3-03f73fedf40b/scratchpad/task421-<pid>-<epoch>/`

**Why I believe it was private, and the part of that belief that is wrong.** The
parent — the directory this session was handed as "your scratchpad" — is *not*
private. It held **519 entries when I arrived**, with mtimes spanning 2026-09-09
to 2026-09-11, including `baseline.txt`, `mutate.py`, `merge368.log`, and a
`probe.py` last written at **13:31-13:37 today**. That `probe.py` is the
TASK-368 collision described in the brief, still sitting there. So the directory
advertised as session-private is shared in fact, and I confirmed it by listing
it rather than by trusting its name.

What is private is the **leaf** I created inside it, whose name carries my
shell's pid and an epoch second. That is uniqueness by *my* good behaviour —
exactly the mechanism this row exists to say does not work. **I am the sixth
agent told to pick a careful name, and the reason I did not collide is that I
picked one, not that I could not.** That is the finding, not the mitigation.

**Suite baseline, measured in this worktree, at `70458893`, before any edit:**

```
2 of 124 MODULE(S) red
3 of 3578 TEST(S) failed
```

- `test_contract_key_parity` — 2 of 35. Data-dependent on the live board
  (recorded 2026-08-30 in the journal).
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` — 1 of 49.
  Clock-dependent.

Neither is mine and neither is touched by this row. Two other agents (TASK-436,
TASK-431) were running concurrently; this baseline was taken in my own tree, not
in the primary checkout.

## 1 · The sweep — every place a dispatched agent is told where to put a scratch file

**Size: 8.** Search terms: `scratchpad`, `scratch`, `tmp`, `/tmp`, `temp`,
`TMPDIR`, `mktemp`, `tempfile`, `working file`, `working dir`, `workspace`,
`sandbox`, `baseline.txt`, `copy the project`, `a copy`, `git archive`,
`.scratch`, `namespace`, `shared dir|tree|checkout`. Swept `AGENTS.md`,
`SKILL.md`, `ARCHITECTURE.md`, `work/`, `reference/`, `modes/`, `packs/`,
`templates/`, `decide/`, `goals/`, `schema/`, `state/`, `.perry/`, `bin/*.md`,
`.github/`, `.gitignore`, then the whole repo excluding `.git/`,
`perry/journal/` and `perry/evidence/`.

| # | Site | What it says | Names a location? |
|---|---|---|---|
| 1 | `AGENTS.md:57` | "a long or repeated step goes in a **scratchpad file**, not the prompt" | **no** |
| 2 | `work/reference/review-constraints.md:18-20` | "copy the project to a **scratch directory** and work there" | **no** |
| 3 | `work/reference/review-constraints.md:27` | "**Plant into a copy.**" | **no** |
| 4 | `work/reference/review-constraints.md:88-92` | "a `git archive` **scratch copy**… point the live repository's helper at the copy with `--root <copy>`" | **no** |
| 5 | `work/reference/digests.md:52` | "a working file at `inputs/<basename>-digest.draft.md`" | yes — in-repo, keyed by input basename |
| 6 | `work/reference/dispatch.md:277` | "**Capture stdout to a temp file**" | **no** |
| 7 | `reference/host-capabilities.md:91-92` | `/tmp/perry-dispatch-<task-id>.log` / `.pid` | yes — `/tmp`, keyed by task id |
| 8 | `work/reference/autopilot.md:227` | poll `/tmp/perry-dispatch-<id>.log` | yes — consumer of #7 |

**Last element** (the lowest-precedence document that still tells an agent a
path): `work/reference/autopilot.md:227`, which only reads a path #7 wrote.

### The sweep's actual finding, and it corrects the spec's premise

**Nothing in the repository ever told an agent to namespace inside a shared
scratchpad.** Six of the eight sites name no location at all, and the two that
do (#7, #8) are the *dispatcher's* log, already keyed by task id, and have never
collided. The shared-scratchpad instruction that caused all five collisions was
**improvised per dispatch, in prompts, by a PMO that had no shipped rule to
quote** — which is why five different agents received five versions of the same
bad advice. The defect was a **gap**, not a wrong line, and that is a different
repair: you cannot fix a gap by editing the offending sentence, because there
isn't one.

This also explains the failure's persistence. Advice that lives only in a
hand-written prompt is re-authored every dispatch, so it degrades exactly the
way `review-constraints.md`'s own header warns: *"a constraint list retyped per
round is a constraint list that loses an entry per round."*

### Every destructive-command prohibition already written down

Enumerated so the new one joins them rather than starting a second list. Prose
rules addressed to an agent: `review-constraints.md` 13-16, 36-38, 39, 41-47,
50-52, 95-99 · `AGENTS.md` 22, 38-39, 42-43, 47-49, 52-53, 55 ·
`git-boundaries.md` 19, 21, 22 · `delegate.md` 159, 160, 161 ·
`dispatch.md` 238, 257 · `subcommands.md` 906 · `autopilot.md` 232 ·
`reference/diagnose.md` 567. Mechanically-matched backticked fragments:
`.perry/hook.md` 28-35 · `work/state/hook_TEMPLATE.md` 17, 21, 41, 43 ·
`packs/software-ops/roles/*.md`.

**`pkill`, `killall` and `kill -9` appeared in none of them.** `grep -riE
"pkill|killall|kill -9"` over every document surface returned hits only in
TASK-421's own board row and journal entry.

## 2 · Fix (1) — the signal prohibition

Landed in `work/reference/review-constraints.md § The repository is live`, in
the same bullet list as its neighbours. The section's premise sentence was
widened by one clause, because a rule about signals under a heading about the
repository needs the machine named:

> Other work is in the tree, including uncommitted work you cannot see the
> purpose of. **And other work is in the process table**, including runs started
> by sessions you cannot enumerate.
>
> - **Never `git checkout`, `git stash`, `git reset`, or `git clean`.** Each one
>   can destroy work that is not yours and not recoverable.
> - **Never `pkill`, `killall`, or `kill -9`.** A pattern kill cannot tell your
>   process from someone else's, and you cannot see who else is working. To stop
>   something you started, stop it by its own job or pid — never by a pattern.
> - Reading history is fine: `git log`, `git diff`, `git show`.
> - Do not commit, push, or open a PR. The round's output is a verdict.

Same shape as the `git checkout` bullet: **Never `X`, `Y`, `Z`.** followed by
the reason in one sentence. A short paragraph under the list carries the
2026-09-10 incident and the sentence that generalises it — *seeing a result you
cannot explain is a reason to stop and read, not a reason to signal* — because
the agent that ran the `pkill` did so in response to output it could not
account for, and killing processes could not have fixed a path collision.

## 3 · Fix (2) — where it landed, and why it is not advice

### What I found before deciding

**There is no code to change.** Confirmed rather than assumed: nothing under
`bin/`, no `.py`, no shell script constructs a dispatched agent's prompt or
computes a working directory for it. `grep -E "git worktree|worktree add"` over
`bin/` and `setup` returns **zero hits** — `isolation: "worktree"` is a flag the
dispatching agent is told to pass to the `Agent` tool. `bin/perry-dispatch-limit`
is a marker-file semaphore over `~/.cache/perry/in-flight/<TASK-ID>-<EXECUTOR>.json`
and never sees a prompt, a spec, a repo path or a directory. The prompt is
assembled from prose at `dispatch.md:254`.

So a mechanism that *enforces* a path at dispatch time cannot be built here
without building a dispatcher, which this row is not. The spec anticipated that
answer and asked me to argue it from the dispatch path's actual shape. That is
the argument.

### But "no code" does not mean "only advice"

The five failures share one mechanism: **the agent had to invent a unique
name.** That is the step that fails, because it depends on the agent's care and
five agents' care was insufficient. The fix removes the step rather than
repeating the instruction:

```sh
# perry-scratch-derivation — do not edit without re-reading TASK-421
PERRY_SCRATCH="${TMPDIR:-/tmp}/perry-scratch/$(basename "$(git rev-parse --show-toplevel)")"
mkdir -p "$PERRY_SCRATCH"
```

**The distinguishing component is minted by the dispatching tool, not chosen by
the agent.** The worktree directory name already exists, already differs per
dispatch, and the agent only reads it. An agent that then writes the dumbest
possible filename — `$PERRY_SCRATCH/baseline.txt`, the exact name that collided
four times — still cannot collide.

**Outside the repository is the other half**, and it settles TASK-385's open
question in the second of the two directions that row offered. `tests/header_rule.py`
admits any Python-parseable file it finds anywhere under the repo root as a real
reader (`NOT_A_READER` is only `tests`, `.git`, `__pycache__`, `.perry`,
`.claude`), and `tests/tree_guard.py` reports the tree as moved. `${TMPDIR:-/tmp}`
is unreachable by both, because both walk `rglob` from the repo root. So the
isolation costs no test its coverage and needs no exclusion added anywhere.

### Where it landed

- `work/reference/dispatch.md` — new `### Where the agent puts a scratch file`,
  inside the region pinned by `test_spec_scannability.py::TestTheAgentGetsItsOwnTree`,
  above the paragraph where normative text stops.
- `work/reference/dispatch.md § Executor: claude-subagent` — a bullet requiring
  the block verbatim in every rendered prompt, beside the `isolation: "worktree"`
  bullet. This is the prompt-construction site the spec asked me to find.
- `tests/test_spec_scannability.py` — `GOVERNED_SHA` re-pinned to
  `3780eb88a43b…` (span 7,572 chars / 126 lines; 6,422 pinned, 1,150 free), a
  deliberate second edit in the same commit, as that file prescribes.
- `AGENTS.md:57` — folded into the existing scratchpad bullet. See § 4
  verification item 2, the fifth collision.
- `tests/test_scratch_is_per_agent.py` — new, 10 tests.
- `tests/durations.json` — the new module registered.

### Is it advisory? Partly, and here is the exact line

**Honest answer: the instruction is still text an agent can ignore, and no code
stops it.** What changed is not enforceability but *what obedience requires*.
Before: obedience required judgement the agent had to exercise correctly every
time. After: obedience requires pasting a line whose correctness does not depend
on the agent at all. Those are different failure rates, and the second is
checkable — `test_scratch_is_per_agent` executes the shipped snippet in two real
git repositories and asserts the paths differ, so the *mechanism* is pinned even
though the *compliance* is not.

Per the brief's instruction to make the advice impossible to miss rather than
one line among many: it is a normative blockquote with its own heading inside a
byte-pinned region, it is a required prompt-construction bullet, and it is on
the always-loaded startup page. It is in three places that a session reads
before it does anything, and a test goes red if any of the three loses it.

## 4 · Verification

### 1 — Two agents, two paths, shown

Three agents were dispatched concurrently while this row ran (TASK-436,
TASK-431, and this one). Derived from the read-only `git worktree list`; I did
not `cd` into the other two agents' trees, per the brief:

```
TASK-436   $TMPDIR/perry-scratch/agent-a166fb97950b55bc5/baseline.txt
TASK-431   $TMPDIR/perry-scratch/agent-ac4d74a2e14651260/baseline.txt
TASK-421   $TMPDIR/perry-scratch/agent-ae7985c20a95a9b3e/baseline.txt
distinct roots: 3 of 3
```

The same derivation applied to the worktrees the historical rounds still occupy
(`r5a`/`r5b`/`r5c`, `r6a`/`r6b`/`r6c`, `fixA`/`fixB`) yields **8 distinct roots
of 8**, against the **1 of 8** they actually shared.

`test_scratch_is_per_agent` does this for real rather than by arithmetic: it
creates two genuine git repositories, executes the snippet extracted from
`dispatch.md` in each, and asserts the outputs differ, that the same filename
under each is two files, that the path is stable across invocations, and that it
is outside the repository.

**Under what conditions they can still collide.** One condition, and it is the
same hole as the worktree rule rather than a new one: an agent dispatched
**without** `isolation: "worktree"` resolves `--show-toplevel` to the shared
checkout, so two such agents get the same scratch root. The flag is mandatory
and byte-pinned, so this is the existing guarantee's boundary, not an additional
one. A second, narrower condition: two worktrees with the same basename under
different parents would collide, because the derivation takes the basename
rather than the full path. The Agent tool mints `agent-<16 hex>` names, so this
does not arise in practice, but a hand-created worktree could.

### 2 — The five collisions, replayed, one by one

| # | Collision | Prevented? | Why |
|---|---|---|---|
| 1 | round 4 — `r4b`/`r4c` both wrote `scratchpad/baseline.txt` | **Yes** | Distinct worktrees → distinct roots. The filename need not change. |
| 2 | round 5 — same | **Yes** | `r5a`/`r5b`/`r5c` are distinct worktrees; derivation gives 3 distinct roots. |
| 3 | round 6 — same | **Yes** | `r6a`/`r6b`/`r6c`, likewise. |
| 4 | 2026-09-10 — clobber escalating into `pkill -f 'tests/run'` | **Yes, both halves, by different fixes** | Fix (2) prevents the clobber (`fixA`/`fixB` are distinct worktrees). Fix (1) prohibits the escalation independently, so the kill is forbidden even if some other clobber occurs. |
| 5 | 2026-09-11 — TASK-368's `probe.py` overwritten **by another session** | **Yes by the mechanism; only after the `AGENTS.md` edit by placement** | See below. |

**Collision 5 is the one that tests the fix, and it is why the count matters.**
The derivation keys on the checkout root, and a non-dispatched session's root is
the primary checkout — distinct from every agent worktree — so the *mechanism*
separates sessions and subagents alike. But the *placement* did not:
`dispatch.md § Executor: claude-subagent` governs how a PMO writes a prompt for
someone else. A session doing its own work never reads that bullet about itself.
**A fix that had stopped at `dispatch.md` would have prevented collisions 1-4
and missed 5** — exactly what the brief predicted.

That is why `AGENTS.md:57` was amended. It is the always-loaded startup page
every session reads, dispatched or not, and its existing line — *"a long or
repeated step goes in a scratchpad file"* — named no location, which is the
sentence under which collision 5 happened. With that edit the answer is yes for
all five; without it, four of five.

### 3 — The constraint is where the others are

Quoted in full in § 2 above, beside its neighbours. It is bullet 2 of 4 in the
same list; `test_it_sits_with_the_other_prohibitions_not_in_a_second_list`
asserts it follows the `git checkout` bullet inside the same section, so a later
edit that relocates it to a list of its own goes red.

### 4 — Mutation

The fix does admit tests, so it was mutated rather than excused. **Ten
mutations, ten red.** Each applied to the live document, the named modules run,
then restored and the restore verified against `git show HEAD:<path>` — an
independent source, not the bytes the harness snapshotted
(`review-constraints.md § Verify a restore against an independent source`). Each
mutation also asserted the file matched `HEAD` *before* it was applied, so a
file already carrying someone's mutation would have aborted the run rather than
been restored to it.

| # | Mutation | Verdict | Test that caught it |
|---|---|---|---|
| M1 | snippet → fixed shared path | RED | `test_two_worktrees_derive_two_scratch_roots`, `test_the_same_filename_in_both_is_still_two_files`, `test_the_snippet_names_no_fixed_directory` |
| M2 | snippet → `$$`-seeded (not re-derivable) | RED | `test_the_path_is_stable_across_invocations_in_one_tree` |
| M3 | sentinel deleted, snippet unfindable | RED (ERROR ×4) | extraction raises — deleting the mechanism is not a way to go quiet |
| M4 | scratch moved inside the worktree | RED | `test_the_scratch_root_is_outside_the_repository` |
| M5 | normative blockquote gutted to "should try to keep tidy" | RED | `test_the_rule_is_stated_and_says_derived_and_outside`, `test_the_governed_regions_are_pinned` |
| M6 | prompt-construction bullet removed | RED | `test_the_prompt_construction_list_requires_the_block`, `test_the_governed_regions_are_pinned` |
| M7 | signal prohibition removed entirely | RED | all three of `TestTheSignalProhibitionIsWrittenDown` |
| M8 | reason gutted, rule kept | RED | `test_the_rule_states_its_reason` |
| M9 | `killall` dropped from the three | RED | `test_all_three_signal_commands_are_named` |
| M10 | signal rule moved to a second list below the section | RED | `test_it_sits_with_the_other_prohibitions_not_in_a_second_list` |

**Two of these were GREEN on the first pass, and both were findings.**

- **M4 was GREEN, and the bug was in my own test.** `test_the_scratch_root_is_outside_the_repository`
  compared `str(got).startswith(str(tree) + "/")`. On macOS `tempfile` hands back
  `/var/folders/…` while git answers `--show-toplevel` with its realpath
  `/private/var/folders/…`, so the check compared two spellings of one directory
  and never matched. **The test asserted nothing**, and passed happily while the
  derivation was mutated to put scratch inside the worktree — the precise defect
  TASK-385 exists about. Fixed by resolving both sides; M4 is now red. Found by
  mutation, not by review, and it is the reason to mutate a test you just wrote.
- **M7 was GREEN because fix (1) had no test at all.** A prohibition nothing
  checks is the failure mode `review-constraints.md`'s own header describes. I
  added `TestTheSignalProhibitionIsWrittenDown` (3 tests) rather than write
  "documentation-only, cannot be mutated" — because it could be, and M8-M10 show
  the guard discriminates between removing the rule, removing its reason, and
  relocating it.

### 5 — What a sixth collision would look like, and whether anything would report it

**Shape.** Not two agents writing one path — that now requires either a dispatch
that omitted `isolation: "worktree"`, or a session that ignored three separate
written instructions. The realistic sixth is **a tool that writes a fixed path of
its own**, below the level any of this reaches: `bin/lib/__init__.py:176` puts
`perry-task`'s write lock at `<tempdir>/perry-task-<hash-of-state-root>.lock`
(keyed by state root, so it is safe), and `reference/host-capabilities.md:91`
puts the codex dispatch log at `/tmp/perry-dispatch-<task-id>.log` (keyed by task
id — **but two rounds of the same task id dispatched to codex would share it**,
and nothing keys that by round). That is the nearest remaining fixed path and I
did not change it.

**Would anything report it? No — and that is unchanged by this row.** This is
the part of the spec's "Why" that no fix here addresses: the 2026-09-10
collision *"is known only because the agent that did it reported itself"*, and
so is the 2026-09-11 one. There is still no detector. A clobbered file still
parses, a mutation harness reading someone else's baseline still prints a
result, and the round has no way to tell the result came from another agent's
file. The fix makes the collision much harder to cause; it does nothing to make
one visible. **Anyone reading this should assume a sixth would again be found
only by a self-report, or not at all.** Per the spec's "must not silence the
symptom", I did not make anything quieter — but I also did not make anything
louder, and a detector is a separate row.

### 6 — TASK-385's shape happened again, to me, and the suite caught it

Worth recording because it is the same failure mode the brief is about. My first
`AGENTS.md` edit added the scratch rule as a **new bullet**, taking the file from
60 lines to 61, and turned
`test_entrance.TestRepositoryAgentStartup.test_agents_file_stays_one_screen` red:
`AssertionError: 61 not less than or equal to 60`. **An agent obeying its brief
reddened the suite it is measured against** — TASK-385 in miniature, one day
later, in a different file.

Two things it demonstrates. First, the full suite earned its cost here: the
targeted modules I had been running were all green, and only `tests/run` saw it.
Second, it is the good version of the outcome — a *named* test with a stated
budget and a reason, failing loudly and immediately, rather than a silent
clobber. Fixed by folding the sentence into the existing bullet instead of
adding a line; the file is back at 60 and the test is green.

## 5 · A row worth filing (I did not write the task store)

1. **`/tmp/perry-dispatch-<task-id>.log` collides across rounds of one task.**
   `reference/host-capabilities.md:91-92` and `autopilot.md:227`. Two codex
   dispatches of the same task id — a round 2 re-dispatch, which is routine —
   write and poll one log and one pid file. Same shape as this row, one layer
   down, and not covered by the derivation because the dispatcher writes it
   before any worktree exists.
2. **Nothing detects a scratch clobber.** Both known instances were self-
   reported. A round whose baseline was written by another agent still prints a
   number. This is the detector TASK-421 deliberately does not build.
3. **`.perry/hook.md § High-stakes operations` does not list signals.** The hook
   is the list the dispatch pre-flight matches *mechanically* (backticked spans),
   so `pkill` there would arm the gate rather than only inform a reader. I did
   **not** add it: the spec's `Bound` asked for the prohibition in **one** place
   phrased like its neighbours, and `.perry/` is this project's own escalation
   configuration, where an edit changes what Perry-the-project refuses to do
   unsupervised. That is a decision for the project, not for this row.

## 6 · What I did not check

- **Whether any agent actually obeys the new instruction.** Nothing here
  measures compliance, only that the mechanism is correct if followed. The first
  real evidence will be the next concurrent dispatch.
- **The other executors' prompts.** The prompt-construction bullet was added to
  `§ Executor: claude-subagent` only. `opencode-subagent` says "build the same
  complete prompt as `claude-subagent`" so it inherits by reference, but `codex`
  has its own enumerated prompt list and I did **not** add the block there. A
  codex dispatch will not carry it. That is a real gap and I am naming it rather
  than claiming coverage.
- **`reference/host-capabilities.md` and `work/reference/autopilot.md` were read
  but not changed** — see § 5 item 1.
- **The two red modules in the baseline** (`test_contract_key_parity`,
  `test_resume.TestStaleRuns`) were not diagnosed. They are red at `70458893`
  before any edit of mine, and I re-ran them alone to confirm rather than
  attributing them to the parallel runner or to the two concurrent agents.
- **Windows / non-POSIX.** The derivation is a POSIX shell one-liner using
  `${TMPDIR:-/tmp}`. Perry is developed on macOS; I did not check that this is
  right on a host where `TMPDIR` is unset and `/tmp` is not writable.
- **Whether `$TMPDIR` is itself per-session on this machine.** It resolved to a
  per-user `/var/folders/…` path. If some host exports a per-session `TMPDIR`,
  the derivation is *more* isolated than claimed, not less — but I did not
  verify the claim in the safe direction for other hosts.

## 7 · Two things that happened after the report was first written

### The codex gap, closed rather than only named

§ 6 originally recorded, as a limitation, that `§ Executor: codex` enumerates
its own prompt contents and did not name the scratch block — so a codex dispatch
would ship without it. That section is **outside** the region pinned by
`TestTheAgentGetsItsOwnTree` (the span ends at `### Executor: opencode-subagent`),
so closing it cost no re-pin. It now requires the block, with the reason stated:
a codex session reads no startup page, so `AGENTS.md` does not reach it and the
prompt is the only carrier.

`test_every_executor_that_enumerates_its_prompt_requires_the_block` now checks
both executors that enumerate. `opencode-subagent` is deliberately not checked —
it says *"build the same complete prompt as `claude-subagent`"* and inherits by
reference, so asserting on it would pin a sentence that is not there.

This matters for the fifth collision's verdict. With `AGENTS.md` and both
enumerated prompts carrying the rule, the three ways an agent can arrive —
dispatched as a subagent, dispatched to codex, or a session working on its own —
all now carry it. Before this edit, one of the three did not.

### I collided with my own test run, in the row about collisions

While a full `tests/run` was in flight I edited `work/reference/dispatch.md` and
`tests/test_scratch_is_per_agent.py` to close the codex gap. `tests/tree_guard.py`
step 0 asserts the tree the suite started in is the tree it ends in, and it
walks the whole worktree — `perry/evidence/` and `work/` included; its
`IGNORE_DIRS` is only `.git`, `__pycache__`, `.claude`, `.gstack`. So that run
was measuring a tree that changed underneath it, and **its result is not
evidence of anything**. I discarded it and re-ran on a quiet tree rather than
report a number I could not stand behind.

The guard caught it and named every file, which is what a working detector looks
like:

```
0. tree guard — the tree the suite started in is the tree it ends in
tests/tree_guard.py: THE SUITE WROTE INTO THE TREE IT RAN IN — the checkout is
not what it was when the run started
  M perry/evidence/2026-09/TASK-421-result.md   (changed)
  M tests/test_scratch_is_per_agent.py   (changed)
  M work/reference/dispatch.md   (changed)
```

Note what it did **not** do: it reported the writes as a failure of the suite
and suggested the usual cause (a Perry write-side tool invoked without
`--root`). The real cause was a human-shaped one it cannot see — an agent
editing files by hand while its own suite ran. The guard still did its job,
because it reports the *condition* rather than guessing the *cause*, and the
condition was true.

Worth writing down because of what it is not. It is **not** the collision this
row is about: it was one agent against its own run, inside its own worktree, and
no other agent's work was at risk. But the mechanism is the same one — *a
long-running reader and a concurrent writer sharing a path* — and it shows the
shape survives the fix, because the fix separates **agents** from each other and
does nothing about an agent racing itself. The discipline that covers this one is
different and older: do not write the tree while the suite is reading it. I knew
that and did it anyway, which is the honest version of why "tell the agent to be
careful" keeps failing.

### M11, and the final suite

Closing the codex gap added a claim, so it was mutated too. **Eleven mutations,
eleven red.**

| # | Mutation | Verdict | Test that caught it |
|---|---|---|---|
| M11 | the block removed from `§ Executor: codex`'s prompt list | RED | `test_every_executor_that_enumerates_its_prompt_requires_the_block` |

**Final `tests/run`, on a quiet tree, everything committed:**

```
2 of 125 MODULE(S) red
3 of 3589 TEST(S) failed
0. tree guard — nothing under <this worktree> moved
```

Against the baseline of `2 of 124` / `3 of 3578` at `70458893`: **the same three
failures, by name** (`test_contract_key_parity` ×2, `test_resume.TestStaleRuns`
×1), `+1` module and `+11` tests, all mine. Both pre-existing reds were re-run
**alone** to confirm they reproduce outside the parallel runner rather than
being attributed to it or to the two concurrent agents — they do, identically.
No regression.
