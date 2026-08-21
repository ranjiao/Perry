# TASK-114 — delegation prompt for an aiMark coding agent (v2)

> Rendered 2026-08-21. **Supersedes `TASK-114-delegation-prompt.md`, which must
> not be sent.** Perry did not execute this work.
> Paste the block below into a fresh session **in the aiMark repository**.
> This project has declared no role cards, so the roleless fallback applies.

## Why v1 was withdrawn

Three of v1's load-bearing claims were false when it was written or became
false the next day. Recorded here rather than deleted, because "the prompt was
measured against the wrong thing" is the finding, not an embarrassment:

| v1 said | actually |
|---|---|
| aiMark reads `perry-task/list/**1.2**` | **1.9** — `src/perry-cli.ts:72`, `CONTRACT_TESTED.task`. The `1.2` in `AIMARK.md:80` is a **closed task's title**, not a live pin. |
| the current contract is **1.11** | **1.14** — `schema/task-list-contract.md:3` |
| "the pin is scattered enough that a nine-version drift went unnoticed — put the version string in exactly one constant" | **it is already exactly one constant**, with a doc comment explaining why the three payloads are three separate numbers. v1's acceptance item 3 was satisfied before the agent started. |

v1 also gave `perry-goals/list` as `2.0`; it is **2.1**.

---

You are working in the aiMark repository at `/Users/bytedance/proj/aimark`. Perry
lives in a separate repository at `/Users/bytedance/proj/Perry`, which is
**read-only to you** — read its contract documents, change nothing in it.

## The task

aiMark's read path is anchored at `perry-task/list/**1.9**` and
`perry-goals/list/**2.0**`. Perry is at **`1.14`** and **`2.1`**. Move the
anchor, and — this is the actual work — **act on the two entries in between
that changed a value's MEANING rather than adding a key.**

aiMark's own comment on that constant states the bar:

> *"it is only honest if it is bumped when the changes are actually read and
> acted on."*

Bumping the number without acting on 1.12 and 1.14 would make that comment a
lie, and would be worse than leaving it at 1.9, where it is at least true.

This is a **version catch-up, not an architecture change.** Three things are
deliberately out of scope, each for its own reason:

- **Do not remove aiMark's markdown parsing.** The OKR chain view parses
  `OKR.md`, `BOARD.md` and `phase/NNN-linkage.md` in process. Deleting that is a
  separate, larger piece of work gated on a Perry change that has not landed
  (`perry/OKR.md § KR-O4.1`, target 0 lines by 2026-09-30). Touching it now means
  doing it twice.
- **Do not add a write path.** Perry has no write contract for outside
  consumers yet — its writers are CLI tools. Anything you build now would be
  built against a shape that does not exist.
- **Do not change what aiMark renders**, except where 1.12 or 1.14 makes the
  current rendering *wrong* — see below. Same task set, same screens otherwise.

## Do not rebuild the pin

`src/perry-cli.ts` already carries everything v1 asked to be built:

- `TASK_CONTRACT_MAJOR` / `GOALS_CONTRACT_MAJOR` / `DECIDE_CONTRACT_MAJOR` —
  three numbers on purpose, per `DESIGN-005 § 4` decision 5.
- `CONTRACT_TESTED = { task: "1.9", goals: "2.0", decide: "1.0" }` — the anchor.
- `isAheadOfTested()` and `changedSince(semantics, tested)` — it already reads
  the payload's `semantics` array and already keeps an unparseable version
  string rather than dropping it.

**Read that file before you write anything.** If you find yourself adding a
second version constant, or a second way to compare minors, stop — you have
started rebuilding something that exists.

## What to read, in this order

All paths are in the Perry repository.

1. `schema/task-list-contract.md` — the contract at 1.14. Read `## Changelog`
   entries **1.10 through 1.14**; that range is your whole job.
2. `schema/goals-list-contract.md` — at 2.1. Its changelog is a table; the
   `2.1` row is additive.
3. `schema/decide-list-contract.md` — `1.0`, unmoved. Read only to confirm.
4. `schema/events-list-contract.md` — `1.0`. Only if aiMark shows history.

Run the tools yourself against a real project rather than inferring payloads
from documents:

```
cd /Users/bytedance/proj/Perry
python3 bin/perry-task   list --all --json --root /Users/bytedance/proj/aimark
python3 bin/perry-goals  list --json      --root /Users/bytedance/proj/aimark
python3 bin/perry-decide list --json      --root /Users/bytedance/proj/aimark
```

All three work. `perry-task` prints a `SyntaxWarning: invalid escape sequence
'\w'` from `bin/perry-task:1282` on **stderr** — it is noise in a docstring, not
a failure, and stdout is clean JSON. Do not "fix" it; it is Perry's file.

## What actually moved, 1.9 → 1.14

**Two of these change meaning without changing a key.** Those are the ones a
consumer cannot discover by diffing payload shapes, and they are why this task
is not a one-line edit.

### 1.10 — `status_text` became a legacy display alias — MEANING

The key and its string type are unchanged. What moved: raw Markdown decoration
and off-enum prose in `BOARD.md` are now projection bytes, not task truth, and
from 1.10 `status_text` is always byte-equal to `status`.

**Act on it:** if aiMark reads `status_text` anywhere to recover raw board text
— decoration, an off-enum word, anything the typed enum would not carry — that
code is now reading a copy of `status` and must stop. Displaying it is fine.

### 1.11 — `tasks[].summary` added — ADDITIVE

Optional stable explanation of why a task exists. `""` means unset. Perry
**never** infers it from `title`, `next_action`, evidence or journal prose.

**Act on it:** if aiMark synthesises a description from those, replace it with
this field rather than keeping both. Display when non-empty; otherwise show the
title alone.

### 1.12 — `blocked_stale` added, `startable` MEANING changed

Before 1.12, `startable` read the row's stored `status` before the dependency
graph it had already computed, so a row whose every dependency had closed
reported `status=blocked`, `blocked_by=[]`, `startable=false` — three values in
one object, the first contradicting the second, with no key to see it by.

Such a row is now `startable: true` and carries `blocked_stale: true`. **The
stored `status` is deliberately left reading `blocked`** until a human or a
later write clears it.

**Act on it:** anywhere aiMark decides "can this be started" or greys out a row,
it must read `startable`, not `status`. A row that shows as blocked *and*
startable is not a bug in the payload — `blocked_stale` is the flag that says
so, and a UI that hides it re-creates the exact invisibility 1.12 removed.

### 1.13 — three `conformance` keys, and four keys per `next_action_cites_closed` entry — ADDITIVE

- added `conformance.blocked_by_closed_rows`,
  `conformance.in_progress_with_no_live_run`, `conformance.review_idle`.
- each `next_action_cites_closed` entry gained `row_status`, `blocked_stale`,
  `readings` and `means`.

That last one has a history worth knowing: as a bare `{id, cites, status}`
triple the array read as a wording complaint, and on 2026-08-20 it fired on two
genuinely stranded rows and **was silenced by rewriting the cells**. Each entry
now states both readings and picks neither.

**Act on it only if aiMark surfaces `conformance`.** If it does, `readings` and
`means` are prose meant for a person and must not be collapsed into a verdict.
Both new idle checks are **empty when `has_event_log` is false** — that is not
"no findings", and rendering it as a clean bill is the misreading to avoid.

### 1.14 — a `USER-` ask is a node in the dependency graph — MEANING

`blocked_by`, `startable`, `blocked_stale`, `conformance.depends_on_unknown`
and `conformance.blocked_by_closed_rows` all changed meaning. No key moved.

The graph now resolves against **two** registers, not one: a `USER-` id from the
user-input queue is a real node, because `pending` / `answered …` is a state
Perry can read that reaches a terminal value.

- a **pending** ask leaves the row in `blocked_by` — not startable.
- an **answered** ask satisfies the edge: `startable: true`,
  `blocked_stale: true`, and the ask id appears in `blocked_by_closed_rows`.
- an id **neither register carries** is unchanged — a mistyped task number, a
  `USER-` id never minted, every `DESIGN-`/`ADR-` handle — still
  `depends_on_unknown`, still unsatisfied.

**Act on it:** if aiMark assumes every id in `blocked_by` or
`blocked_by_closed_rows` is a task and looks it up in the task list, a `USER-`
id will miss and render as blank, "unknown", or a broken link. An ask is **not**
a row in `tasks[]` and never will be — it has no entry to find. Render it from
the user-input queue the payload already carries, or as a plainly-labelled
question, but do not resolve it against `tasks[]` and do not treat the miss as
a data error.

This entry exists **because of TASK-114 itself** — the row this prompt serves
was blocked on `USER-015`, and both available spellings tripped a check. That
is why v1, rendered the day before, could not mention it.

### goals 2.0 → 2.1 — ADDITIVE

Four keys, none removed or retyped: `krs[].current_provenance`,
`krs[].current_staleness`, `krs[].linked_task_completion`, and
`conformance.krs_with_stale_current`. `current` is unchanged in type and value.

**Act on it:** the payload now says that `current` is **an author's assertion,
not a measurement** (`current_provenance.measured` is always `false` today), and
says when a linked task has moved since it was asserted. If aiMark draws any
KR progress indicator, it is drawing an assertion, and 2.1 is the first version
that lets it say so. A stale or unasserted number rendered identically to a
fresh one is the thing these keys exist to prevent.

`current_provenance.asserted_scope` is `"register"`: the register timestamps
**itself**, not each KR, so `asserted_at` is not the date that KR's number was
arrived at. The granularity ships with the date precisely so a consumer does
not take one for the other.

## Acceptance

1. `CONTRACT_TESTED.task` is `"1.14"` and `.goals` is `"2.1"`, and the diff
   shows the code that made each meaning-change entry safe. A bump with no
   accompanying change to how `startable` or `blocked_by` is consumed fails
   this item.
2. `startable` — not `status` — decides whether a row reads as startable, and
   `blocked_stale` is visible somewhere rather than swallowed.
3. A `USER-` id in `blocked_by` renders as a question, not as a missing task.
   Prove it with a fixture; Perry's own board has one (`TASK-114` → `USER-015`).
4. `summary` is read where a synthesized description used to be, and no
   synthesis remains.
5. The version anchor is still in exactly one place — proven by a search — and
   there is still exactly one minor comparison.
6. The diff touches no rendering of the OKR chain view, proven by the file list.
7. aiMark renders the same task set it renders today. Capture before and after.
8. aiMark's own test suite is no redder than before you started. **Measure the
   baseline yourself; do not take it on trust.**

## Report back

State what you changed, the before/after render comparison, the search proving
the single anchor, and — most valuable — **anything in the contract that did not
match what aiMark assumed.** A place where the document and the consumer
disagree is a finding for Perry, not just for aiMark, and this task exists
because the last such gap went unnoticed for five minors.
