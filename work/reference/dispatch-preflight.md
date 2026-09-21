# Dispatch eligibility and pre-flight

## 0 · Whether to dispatch at all

Dispatch has a **fixed cost that does not scale down with the change**: a
separate checkout, a pinned base, a brief, a baseline the agent must measure for
itself, a result document, a merge, and a verification pass by whoever merges
it. It also has failure modes the change itself does not have. Measured: `dispatch-notes.md § What dispatch cost in one session`.

**Do it inline when all three hold:**

- the change is **small and already specified** — you can state the edit and its
  acceptance in one sentence each, before starting;
- it needs **no fresh judgement** — nothing about it improves by being decided
  by someone who has not seen your reasoning;
- **you can verify it yourself** with a command whose output you would have
  asked the agent for anyway.

**Dispatch when any of these hold:**

- the work needs **a context you should not be carrying** — a wide enumeration,
  a long file read, a mutation battery;
- it needs **a judgement you are not entitled to make**, because you wrote the
  thing being judged — that is `review.md`, not this page;
- it is **long enough that doing it inline would crowd out the session's own
  work**, which is a real cost and not a stylistic one.

**The test is not size, it is whether a second context earns its setup.** A
forty-line edit you can state and check is cheaper inline even though it is real
work. A five-line edit that needs the whole suite enumerated to know it is right
is not.

## Pre-flight (any failure → refuse and fall back to `delegate`)

1. `evidence/<YYYY-MM>/<TASK-ID>-spec.md` exists.
2. Spec contains `Dispatch mode: auto` (default `manual` — explicit opt-in required).
3. Spec contains `Executor: claude-subagent | opencode-subagent | codex` (not `manual`). **If spec is `Dispatch mode: auto` but `Executor` is missing**, use the host-native choice UI for a one-shot choice; do NOT silently default. Offer `claude-subagent | codex | manual` on Claude Code, `opencode-subagent | codex | manual` on OpenCode, and `codex | manual` on Codex CLI. Persist the answer only if the user explicitly says "save this for next time". A spec pinned to another host's native executor is a hard host mismatch: refuse and request a spec edit or `/perry work delegate`. Matrix: `../../reference/host-capabilities.md`.
4. **Safety re-validation — you perform this judgement, and no command performs it for you.**

   No command renders this verdict: `perry-state --escalation-scan` was removed on 2026-09-04 (`USER-916`; `ADR-007` decision 3 — Python never judges a document's meaning). Why: `dispatch-notes.md § Why no command performs step 4`. The judgement is yours.

   **This is not "read the list and eyeball it".** Work the five steps below in order, and write the answer down where the user can see it. A gate whose reasoning is not written is not reviewable.

   ### 4.1 — Get the list, and check it is armed

   Read `.perry/hook.md § High-stakes operations` **in full — the bullets and the prose around them**, not just the backticked spans. Then read `## Must escalate` in every `.perry/roles/*.md`.

   **The list is the union of the two, and a role only ever ADDS** (`DESIGN-006 § 5.2`, goal 6). A role that could subtract would let hiring one quietly narrow what the project refuses to do unsupervised, and nothing would show it — a narrowed gate passes everything it is asked, cheerfully. With no roles declared the union is the hook's list unchanged.

   `"$PERRY_HOME/bin/perry-state" --section project` still prints both halves and their union under `project.escalation` (`project`, `roles`, `union`, `origins`, `armed`) — it *extracts a declared list*, which is a bounded value space and stays in Python. It does not read the spec and it renders no verdict. Use it to show the user the list; the reading of the spec is yours.

   **If both halves are empty or absent** (`escalation.armed: false`), nothing is being screened. Do not treat that as a pass. Say so in one line — *"no high-stakes list in `.perry/hook.md`, so nothing is being screened; `/pmo` bootstrap writes the default list"* — and require an explicit go-ahead in chat before dispatching. `AskUserQuestion` is not sufficient here; this is a safety gate, per `SKILL.md § User-prompt convention`. (`/pmo autopilot` refuses outright in the same situation — `autopilot.md` pre-flight step 0.)

   **Bullets that arm nothing.** `perry-lint` reports a hook bullet carrying no extractable backticked span. When you read the section yourself that distinction stops mattering for *your* judgement — you can read an unbackticked sentence — but it still matters for what you tell the user, because `escalation.armed` and the delegation prompt are computed from the spans. Read the prose; report the gap.

   ### 4.2 — Get what the round does

   Read the spec's `## Files in scope` and `## Deliverable` in full, then `## Out of scope`.

   - `Files in scope` is the enumerated list of paths the round will write. It is a declaration.
   - `Deliverable` is prose describing the outcome.
   - `Out of scope` is what the spec has stated in writing that it does not do.

   **If neither `Files in scope` nor `Deliverable` is present and non-empty, you have nothing to judge from.** Do not read that as clean. Say so — *"this spec offers neither `## Files in scope` nor `## Deliverable`, so there is nothing here to screen; `add-task.md § add-task` step 3 has the `## ` shape"* — and require an explicit go-ahead in chat, exactly as for an unarmed hook. 45 of Perry's own 149 specs are in that state, so this is common and is not by itself a reason to refuse the row; it is a reason not to claim you screened it. `perry-lint --root .` reports the condition across every spec at once, before any single dispatch reaches this step.

   ### 4.3 — Decide ownership of every path, BEFORE you tidy any text

   **This step comes first and its order is the point.** The characters that identify a foreign root are the same characters you would otherwise strip as formatting noise. `~` in `~/other-project/evidence/` is the marker that says *someone else's home*; `*` in `**perry/evidence/**` is markdown emphasis. Strip formatting first and you lose the ownership signal with it; treat every such character as an anchor and you refuse your own tree. **So classify the root before you normalise anything, and disambiguate by pairing, not by stripping:**

   > An emphasis marker comes in a **balanced pair** wrapping a span — `**perry/evidence/2026-09/**`, `_schema/state-schema.json_`. An anchor is **unpaired and sits at the head of the path itself** — the `~` in `~/other-project/`, the `$` in `$PERRY_HOME/inputs/`, the leading `/` in `/srv/data/`.

   That test needs no stripping pass at all, which is why it is stated this way.

   Then, on the path as written:

   - **Relative is internal, and that is the entire rule.** A relative path resolves against the root of the project this spec belongs to, so `evidence/`, `perry/evidence/2026-09/x.md` and `evidence/**/*-spec.md` all name *this* project's tree and cannot name anyone else's.
   - **Foreign is exactly five shapes:**
     1. absolute — `/srv/data/`
     2. home anchor — `~/.claude/skills`, `~/other-project/evidence/`
     3. variable anchor — `$PERRY_HOME/inputs/`
     4. upward escape — `../sibling/design/`
     5. **unresolved root — `<target>/evidence/`, `{{project}}/design/`.**

   **Shape 5 is a judgement made in the safe direction on purpose, and it is the one clause most likely to be dropped when this rule is rewritten.** A root nobody has resolved is not a root known to be this project. A gate that guesses *"probably mine"* about a placeholder is the guessing this whole step exists to stop. Keep it.

   **Why ownership decides anything at all.** The hook's destructive-filesystem bullet reads *"overwriting a project's **own** `design/`, `evidence/`, `knowledge/`, `inputs/`"* — it is about a tree Perry does not own. So:

   | Path as written in the spec | Root | Verdict on the `evidence/` entry |
   |---|---|---|
   | `perry/evidence/2026-09/` | relative → this project | **allowed** — this project's own tree; the bullet is not about it |
   | `**perry/evidence/2026-09/**` | `**` is a balanced pair → emphasis, not an anchor; head is `perry` → this project | **allowed** — identical to the row above |
   | `~/other-project/evidence/2026-09/` | unpaired `~` at the head → home anchor → foreign | **REFUSED** — a project Perry does not own |
   | `$PERRY_HOME/inputs/` | unpaired `$` at the head → variable anchor → foreign | **REFUSED** |
   | `<target>/evidence/` | unresolved root | **REFUSED** — shape 5 |

   A bare directory name on its own — `design/`, `evidence/` — **cannot say whose directory it is**, so where a spec writes one with no root at all, ask which tree the surrounding sentence puts it in and refuse if the answer is not this one.

   ### 4.4 — For each list entry, ask one question: does this round DO it, or does it only NAME it?

   **Doing refuses. Naming does not.** This is the whole judgement, and it is the one a reader makes effortlessly and a matcher cannot make at all. Six tells, each with a case behind it from this repository's own corpus:

   1. **A file in this tree, versus the operation the hook means.** The hook's `diagnose` is the *`diagnose` execute stage* — Perry running its diagnosis against a project. `bin/perry-diagnose` and `tests/test_diagnose.py` are files in this repository. Editing the file is not running the stage. (`TASK-108`, refused by the scanner on `diagnose`.)
   2. **Quoted as data.** A fragment appearing inside a list of fragments — hook entries being added, matcher examples, test fixtures — is data this round *handles*, not an operation it *runs*. `TASK-107`'s `Deliverable` names `~/.claude/skills`, `ln -s`, `ln -sf`, `ln -snf`, `publish`, `published`, `rm -rf`, `--force-with-lease` and `$PERRY_HOME` — every one of them as an example of what its matcher must still match. That round installs no host skill, publishes nothing and deletes nothing.
   3. **Cited as precedent.** *"the `adopt` / `diagnose` precedent the router already states"*, *"one row beside `adopt` / `diagnose` / `relocate`"* — a reference to behaviour that already exists. (`TASK-220`.)
   4. **The ordinary English word.** `setup` in *"the harness re-does setup per test"* is a common noun; the hook's `setup` is host skill installation. Test: **substitute an everyday synonym and see whether the sentence stays true.** *"the harness re-does its preparation per test"* — still true, so it was the English word. *"run `/perry preparation`"* — false, so that one is the operation. (`TASK-244`.)
   5. **The line states its own verb and the verb is read.** *"setup and hook code that reads repository documents — read."*, under a section opening *"Read-only survey. The only file this round writes is its own report."* A round that has told you its verb has answered this question already. (`TASK-099`.)
   6. **The spec pre-commits to stopping.** *"`schema/state-schema.json` — only if a new field is declared. **This is the claim surface; changing it is escalated.** If the design points that way, stop and file the question rather than editing it."* with `Out of scope` confirming *"Editing `schema/state-schema.json` … is a separate, user-authorised step."* That is a spec that has read the gate and bound itself to it. **Read it as compliance, not as a contradiction** — the scanner read it as one and refused, which taught rows that quoting the gate is expensive. Carry the pre-commitment into the delegation prompt verbatim so the executing agent inherits it.

   **What makes it a DOING**, on the other side:

   - the round's own verb takes the operation as its object — *"the forms … **are added to** `.perry/hook.md`"*, *"both **change in this edit**"*;
   - any foreign-rooted path from 4.3 appears anywhere in scope;
   - the round would run the command, not merely edit the file that contains it.

   **`Files in scope` cannot be cancelled by `Out of scope`; `Deliverable` can.** `Files in scope` is an enumeration of write targets, so a spec that lists a path there and *also* disclaims it has contradicted itself — and a contradiction is not a pass. Report the disagreement to the user and let them resolve it; do not pick the reading that dispatches. This is distinct from tell 6, where the spec resolves its own tension by naming the escalation and pre-committing to stop.

   ### 4.5 — Standing entry: this round does not rewrite the gate that constrains it

   **Not from the hook's bullets, and stated here rather than added there.** `.perry/hook.md`'s content is the user's, and this file does not edit it. But a round whose `Files in scope` names `.perry/hook.md`, `work/state/hook_TEMPLATE.md`, or this step of this file is a round that changes what Perry refuses to do unsupervised — in this project, and for `hook_TEMPLATE.md` in every project Perry adopts afterwards. **Escalate it and say why.** An agent that may widen its own gate has no gate.

   The worked case (`TASK-107`): `dispatch-notes.md § 4.5 applied`.

   If the user would rather have this as a hook bullet, that is theirs to add and this paragraph then defers to it; if they would rather not have it at all, strike this sub-step. It is written down so that the verdict is reproducible either way.

   ### 4.6 — Say the verdict, in writing

   Record, in the dispatch evidence file and in chat:

   - which list you screened against, and whether it was armed;
   - which sections of the spec you read, and whether either was missing;
   - every list entry you found in the spec, each marked **doing** or **naming**, with the tell and the quoted line;
   - the verdict: **allow**, **refuse**, or **ask**.

   **`ask` is a real outcome and the honest one when you are unsure.** In interactive dispatch it is a question to the user in chat. Under `/pmo autopilot` it is a **skip** — see `autopilot.md` pre-flight step 0 and the `Skipped — high-stakes` disposition; autopilot runs unattended, so an unsure judgement there resolves in the safe direction without asking.

5. Spec contains a `Subjective verification:` section (may be `(none)`); items there will be surfaced to the user at completion, never auto-validated.
5a. **Pack eligibility first**: read `$PERRY_HOME/reference/config.md § Pack
    capabilities and controls`. Steps 5a/5b's software checks, architecture prompt
    blocks for every executor and independent
    architecture review in `dispatch.md § Architecture review` apply only when software-ops is selected and
    present, or an explicit project requirement independently requires that
    check. Name the requirement when retained under a disabled pack. Otherwise
    skip those optional blocks/gates; ordinary RESULT, acceptance verification,
    hook safety and Git constraints still apply. No enablement question.

    **Architecture compliance pre-flight** (see `$PERRY_HOME/packs/software-ops/architecture.md § Dispatch integration`):
    - Read root `ARCHITECTURE.md` §1, §3 and §6, plus touched module documents selected as in `dispatch.md § Architecture preamble`. Existing documents are binding, including legacy `Status: draft`. If the file is missing and the spec claims sections, refuse; expose missing context rather than assuming compliance.
    - Read spec's `Touches architecture:` field. For every section ref listed (`§N`, `§N.NN-M`), verify it exists in the doc. Refuse on mismatch (malformed spec).
    - For each touched non-negotiable in §6 marked `Severity: hard` → use `AskUserQuestion` (header = `NN-N`, options): `Proceed — change is reviewed (Recommended only with reason) | Refuse — revise spec | Refuse — escalate to manual delegate`. "Proceed" requires a written one-line justification copied into the dispatch evidence file's header.
    - For soft non-negotiables → single `AskUserQuestion` (header = `Architecture`, multiSelect) listing each soft NN as an option with description = the rule text. Selection = acknowledgement.
    - `Touches architecture: (none)` → no friction at this stage, but integration still evaluates the diff triggers (`dispatch.md § Architecture review`).
5b. **Deployed-task pre-check**: if spec has `Deployed: yes`, verify the spec contains a non-empty `## Observability` section (Success signal / Failure diagnosis / Runbook path). If missing → refuse and ask user to fix the spec first. The runbook file itself is not required to exist yet at dispatch time (often the dispatched task creates it) — only the observability spec field is mandatory.
6. **Concurrency check**: `bash "$PERRY_HOME/bin/perry-dispatch-limit" register <task-id> <executor>`. Exit 0 = slot reserved, proceed. Exit 1 = limit hit; stderr lists what's currently in flight. On limit-hit, use the host-native choice UI: `Wait — show in-flight (Recommended) | Switch to another host-valid executor | Fall back to /perry work delegate`. Defaults are 2 per automated executor and 3 total; overrides are `PERRY_MAX_DISPATCH_CODEX`, `PERRY_MAX_DISPATCH_SUBAGENT`, `PERRY_MAX_DISPATCH_OPENCODE_SUBAGENT`, and `PERRY_MAX_DISPATCH_TOTAL`. On Codex the cap is advisory across separate sessions.
