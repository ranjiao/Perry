# Style rules, the user-prompt convention, hooks and auto-update

Tier 1. Loaded on demand from `SKILL.md § Style rules`. The router keeps the
one-line form of each rule; the reasoning, the worked examples and the
`AskUserQuestion` conventions live here.

Extracted from `SKILL.md` on 2026-08-18 (TASK-064) to keep the tier-0
router inside its byte budget. The prose is carried over unchanged.

## Style rules

- **Lead with the dashboard, not narration.**
- **Numbers, IDs, file paths.** Not paragraphs.
- **An ID never travels alone.** The first time an ID appears in any user-facing output, it carries its human name: `REL-002 ("Flake detector") is blocked on USER-014 ("Confirm staging env default")`, never `REL-002 blocked on USER-014`. Later mentions in the same response may use the bare ID, and a table with a Title column already satisfies this. Perry mints `REL-`, `ADR-`, `DESIGN-`, `P<NNN>-O<n>-KR<n>`, `USER-`, `CAD-`, `SRC-`, `CL-`, `RX-` and phase numbers — that is a private vocabulary issued to someone who never agreed to learn it, and an unresolvable ID is a dead end in the middle of a sentence the user is trying to act on. Use `bin/perry-explain <ID>` to resolve one, `--all` for the glossary. Full rule in `reference/user-load.md`.
- **Never ask a question the user cannot evaluate.** Before offering options, check whether the user can predict what will be different for them under each. If not, reframe in consequences, or decide it yourself and say so, or narrow to two — see `reference/user-load.md § The three exits`. Depth of analysis and usefulness of a question come apart completely once the subject leaves the user's expertise, and this gets *worse* as the agent gets better.
- **Never mint an example ID that resolves to nothing.** Writing a concrete
  `SRC-<number>` or `TASK-<number>` in prose to illustrate a shape creates a
  reference Perry's own `LOAD-02` check reports as dangling — correctly, because a reader cannot tell
  an illustration from a real cross-reference. Use the placeholder form
  (`SRC-n`, `TASK-NNN`, `<DESIGN-ID>`) in every example. This rule exists
  because Perry violated it three times in one session while writing the
  documentation that forbids it — and a fourth time in the sentence recording
  the third. That fourth one is the tension worth naming: **writing down that
  you cited a nonexistent ID requires not citing it again.** Describe it
  ("a source id in an example"), never quote it. The check cannot tell an
  incident report from a live cross-reference, and it should not try — a
  checker that special-cased prose about itself would be one exemption away
  from useless.
- **Mark a deliberately-quoted obsolete ID with `[[old-form]]`.** A document
  that prints a migrated-away id as the *artifact under discussion* — the
  collision it demonstrates, the draft a decision rejected, the input a
  rejection test is handed — must not be rewritten into the new form; doing
  so deletes the thing it exists to record. It must carry `[[old-form]]` on
  the same line, so `grep -E '<the old shape>' $(git ls-files)` returns
  deliberate survivors and nothing else. Inside a fenced block or a verbatim
  quotation, where an inline marker would corrupt what is being shown, the
  marker goes in the sentence that introduces the block. **Never reword a
  verbatim quotation to avoid needing the marker** (`TASK-142`'s `means`
  text). Introduced by TASK-180's phase-KR id migration, 2026-08-28.
- **Cite the file** for every claim.
- **Never invent state.** Print `—` and ask.
- **Write in the configured languages.** Chat replies follow `Chat language` (or the user's own language when unset); files follow `Document language`. IDs, enum values, file paths, slugs and command names stay English in every language, so a Chinese dashboard line reads `REL-002（"抖动检测器"）blocked，等 USER-014`. Never translate a quoted artifact — a path, a command, an error message, or the user's own words. **A file stays in one language end to end. A chat reply mixes**: a technical term with no settled equivalent in the chat language stays English — `交付了 contract 2.0`, not `交付了契约 2.0` — and an English idiom is never translated word for word, it is replaced by a plain description of what happened. The test is "would someone doing this job say it out loud?" Perry failed this for a whole session while following every other rule here; `reference/i18n.md § Writing chat prose in a language that is not English` has the specifics.
- **Don't duplicate child skills' logic.** This file routes; the children own their domains.

## User-prompt convention (AskUserQuestion)

Whenever a Perry skill (top-level or any child) needs the user to make a choice with **2–4 distinct options**, prefer the host's structured choice tool over free-text "what do you want?" prompts. Claude Code uses `AskUserQuestion`; OpenCode uses `question`. Both render clickable choices with a free-text fallback.

> **Host translation**: OpenCode maps Claude's `multiSelect: true` to `multiple: true`; field names are not portable even when the behavior is. Codex has no choice tool, so render the same options as a numbered free-text prompt per `$PERRY_HOME/reference/host-capabilities.md`. The chosen value and downstream writes are unchanged.

### When to use it

- Any subcommand that branches based on a user choice with a small bounded option set (e.g., `/perry goals score-phase` per-KR `achieved | partial | missed | dropped`, `/perry work triage` per-row `apply | edit | skip`, `/perry decide resolve` per-User-Decision row).
- First-time setup choices (document language, repo layout).
- Per-spec dispatch choice when the spec doesn't pin an executor (`/perry work dispatch` offers the host-valid subset of `claude-subagent | opencode-subagent | codex | manual`).
- Multi-select when you offer up to 4 candidate items the user may approve all/some/none of (Claude: `multiSelect: true`; OpenCode: `multiple: true`).

### When NOT to use it

- Open-ended questions that need a sentence or paragraph (e.g., "What is this project's mission?"). Free-text only.
- Choice sets larger than 4 options. Either narrow first (recommend 1–4 + leave "Other" as the auto-filled fallback), or split into two `AskUserQuestion` calls.
- Confirmations that should always block on explicit user words (e.g., authorizing a high-stakes operation per the project hook). The auto-update check, `/perry work dispatch` pre-flight refusals, and similar safety gates STILL ask in chat — `AskUserQuestion` is not a permission grant.

### Conventions

- **2–4 options per question.** No more, no fewer.
- **Label ≤ 5 words.** The tool enforces this; long descriptions go in the `description` field, not `label`. Labels and descriptions are written in the **chat** language; an option whose value lands in a file (a status, an executor, an enum) shows the invariant token alongside the localized wording — `跳过 (skip)` — so the user can connect the button they pressed to the word that appears in the file.
- **Recommended option first.** Append `(Recommended)` to the label so the user sees which one Perry suggests.
- **Header chip ≤ 12 chars** (e.g., "Executor", "Status", "KR-1.2").
- **Each option's `description` carries the trade-off** — what happens, what it implies, what's lost. Don't make the user guess.
- **The trade-off is stated in consequences, not mechanism.** "Runs on your laptop with no setup, but breaks if two people use it at once" is decidable. "SQLite vs Postgres" is not, unless the user already knows. If an option cannot be expressed in something the user will experience, that is the signal it should not be a question — see `reference/user-load.md`.
- **Offer the escape hatch on anything the user may not be equipped for.** "Or I pick and tell you what I picked" as an explicit option. If they take it, don't re-ask a variant later. Two deferrals in a session means stop offering choices and switch to recommendations they can veto — and say that's what you're doing.
- **Cap open decisions at three at a time.** Past that, queue and say so. A decision backlog stalls everything downstream or lets it proceed on a guess, and afterwards nobody can tell which happened.
- **Anything decided on the user's behalf gets logged** as agent-decided, with what would trigger a revisit. Asking less is only acceptable if those calls stay visible and reversible.
- **Optional `preview`** for showing a code/template snippet (e.g., showing what the rendered task block will look like before they approve).
- Mutually exclusive options unless the host's multi-select field is enabled.

### Concrete pattern: child skills with structured option lists

For child skills whose state files already enumerate options (notably `design/<DESIGN-ID>-*.md`'s `User Decisions` table), write the Options column in **pipe-separated short labels** so `decide` can map each cell directly to `AskUserQuestion` options without rephrasing:

```
| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Cache backend | Redis | Memcached | DynamoDB | TBD | — |
```

Each piped token becomes one `AskUserQuestion` option label.

## Per-project hooks (optional)

If your project has specific roadmap files, MCP tools, agent roles, cost ceilings, or promotion stages, add a hook block to **the children's** `SKILL.md` files (`goals/SKILL.md`, `work/SKILL.md`, `decide/SKILL.md` each have a `## Per-project hooks` section). The top-level Perry skill stays project-agnostic.

Project hook files live at the project root (not in the skill folder), so a single Perry installation can serve many projects without entanglement. The recommended location is `<project_root>/.perry/hook.md`; children read it on every invocation.

## Auto-update

Every Perry skill invocation runs `bin/perry-update-check` as the first action. The script:
- Throttles itself to **once per 7 days** via `$PERRY_HOME/.update-check` mtime; most invocations exit immediately with no output.
- Detects "dev mode" — symlink install, dirty working tree, or non-`main` branch — and in that case **only fetches and reports**; it never auto-pulls (so it can't trample your WIP if you're editing Perry source).
- For "consumer mode" (real directory, clean tree, on `main`), does an ff-only `git pull` from `origin/main`.
- Always exits 0 (network failure, unresolved merge, etc. → notify and continue; never block the standup).

Manual trigger: `bash "$PERRY_HOME/bin/perry-update-check" --force` (bypasses throttle).

The script is invoked from the standup ritual of every lane, so any `/perry …` invocation covers it. If the skill source is not a git checkout (e.g., extracted from a tarball), the check exits silently.
