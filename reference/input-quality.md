# Input quality pass (shared across okr / pmo / design)

Perry's three skills each accept user-authored content that lands in tier 1 files
(`OKR.md`, `phase/<NNN>-<slug>.md`, `design/<ID>-<slug>.md`) or in a task record (`tasks.jsonl`).
This file, with `input-quality-rubrics.md` for §1–§3, is the **single source of truth for the input-quality rubric** every
skill runs before writing that content. SKILL.md files name the pass and link
here; they do not inline the rubric.

Voice fits Perry's ethos: `okr` is already *"interview-style, Socratic,
friction-friendly … pushes back on vague KRs"*. The quality pass is that push-back,
made systematic and reusable — **not** a validator that rewrites the user's words.

## The one rule: prompt, don't rewrite

The pass is **advisory + override**, never silent rewrite, never (on its own) a hard block:

1. **Surface at most 3 issues** — the highest-value ones for this doc. More than 3 reads as nagging; the user tunes out. If the draft is clean, say so in one line and proceed.
2. **Each issue names the field, says why in one line, and shows a concrete bad→good rewrite.** Never "this is vague" with no fix.
3. **The user decides**: fix, or write as-is. Writing as-is is an **override** — record a one-line reason in the journal / `## Changes` (whichever the owning skill uses). Never overrule the user.
4. **Layer on top of, don't replace, existing hard gates.** `design lock` (no open User Decisions), `pmo` evidence-for-`done`, and tier-1 size caps stay hard refusals. The quality pass is the softer, earlier coaching step; it runs *before* those gates, at draft/input time.
5. **User-facing prompt language follows the `Document language` setting in `.perry/config.jsonl`.** This file (Perry source) is English; the rubric labels below are for the agent, the message it renders to the user is in the configured language.

### When each skill runs the pass

| Skill | Runs the pass at | Against rubric |
|---|---|---|
| `okr` | `init` (before writing `OKR.md`), `plan-phase` (before writing the phase file), `plan-week` (per proposed task) | §1 Overall OKR · §2 Phase OKR · §4 Task |
| `design` | `new` (Problem/Goals/Non-Goals first pass) and `lock` pre-flight (whole doc) | §3 Design doc |
| `pmo` | `add-task` (per new BOARD row) | §4 Task |

### Rendering the pass (Claude Code)

Collect the ≤3 issues, then render one `AskUserQuestion` (header `"Input quality"`,
`multiSelect: true`) whose options are the issues to fix, plus the user can pick
"Other → write as-is". On Codex, numbered free-text per `host-capabilities.md`.
If zero issues: print `✓ Input quality: clean` and continue — no prompt.

---

## §1–§3 — goal and design rubrics

The Overall OKR (§1), Phase OKR (§2) and Design doc (§3) rubrics are `input-quality-rubrics.md`, loaded by the `goals` and `decide` passes that run them; the rule above governs them unchanged.

## §4 — Task rubric (task record / `plan-week` proposal / `add-task`)

| # | Check | Bad | Good |
|---|---|---|---|
| 4.1 | **Verification is falsifiable** — a test that can fail, not "looks good" (mirrors PMO Evidence Standards) | "Verify it works" | "`pytest tests/pipeline/ -q` passes; artifact at `evidence/…`" |
| 4.2 | **Deliverable is an artifact, not an activity** | "Work on the migration" | "`migrations/007_*.sql` merged + rollback tested" |
| 4.3 | **Single owner from the Owner model** — not "team" / unassigned | "Owner: someone" | "Owner: Coding Agent" |
| 4.4 | **Priority is justified** — P0 must plausibly block a Must-Have | everything P0 | P0 only if it blocks a DoD Must-Have; else P1/P2 |
| 4.5 | **Linked to a KR** (from `plan-week`) — orphan tasks are scope creep | no `kr:` tag | `kr:P<NNN>-O1-KR2` |
| 4.6 | **Summary is written for a stranger** — why the row exists and what is true when it is done, in plain language, for somebody who was not in this conversation. The title is shorthand; this is what `perry-explain` prints. | the title again, or `D009 step 3` | "Perry ships two opposite orderings of the phase-close pipeline. Nothing picks one, so whoever runs it picks by which page they read." |

> **4.1, 4.2 and 4.6 are also hard refusals in `perry-task add`** (`--verification`, `--deliverable`, `--summary`). They are listed here as well because this pass runs *before* the tool does, and catching them in conversation is cheaper than catching them at the command line. The tool's half of 4.6 is **structural only** — it refuses a summary that folds to the title, has no sentence, or is under five words. Whether the prose is genuinely readable is this pass's job and a human's, not the tool's; do not treat a green `perry-task add` as evidence that 4.6 passed.

---

## What the pass does NOT do

- **Does not rewrite the user's Mission / Problem / Objective prose.** It suggests; the words stay the user's.
- **Does not enforce anything §-numbered as a hard block** — the only hard blocks in Perry remain: `design lock` gate, `pmo` no-`done`-without-evidence, tier-1 size caps.
- **Does not run on tier 2/3 files** (journal, evidence, renders) — those are agent-internal or disposable.
- **Does not re-run every turn.** Once per input event (init / plan-phase / plan-week / new / lock / add-task).
