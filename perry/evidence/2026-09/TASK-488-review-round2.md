# TASK-488 — round 2: result, architecture review, and the user's gate

Candidate: `4a6d13231aaf5cd5ed651022b0d4f58208eb8baa..16f96d691a383a86f0dff89af6f214cbe0fe01f4`
(branch `coding/task-488-work-template`). Spec: `TASK-488-spec.md` § Round 2 and
§ Round 2, continued. Design: DESIGN-023 decisions 13 and 14.

## Round 2 result, as re-verified by the PMO

- **Commits.**
  - `fc9c5001` prunes the template to decision 13 and rewrites
    `kernel/tests/test_work_template.py`.
  - `4608b6b8` makes Goal 1's grep match string literals and adds
    `templates/process/` to `COVERS`. The executor stopped here: the task
    field `summary` was a literal in `kernel/perry_kernel/surface.py`, as
    `describe`'s per-command key.
  - `0dee0e69` renames that key to `purpose`. `surface` stays 1.0, which is
    unreleased.
  - `0eb4cbbb` rewrites the kernel § 3 Forbidden line.
  - `16f96d69` adds the risk create guard.
- **Criterion 7.** The executor listed each type, field, state, move and guard
  against decision 13. Nothing is missing, and nothing extra beyond the id
  prefixes.
- **Criterion 8.** 30 mutants: all 25 guard mutants reddened a refusing test.
  2 of the 5 that add something outside decision 13 are caught only by the
  exact-match test.
- **Kernel suite at `16f96d69`.** Re-run by the PMO in the executor's clean
  worktree: OK, with 1 existing skip. The live store was absent before and
  after.
- **Affected tier (executor).** Green for `--tier affected`. It widened to the
  full suite (159 modules, 4,489 tests) because `tests/selection.py` quotes the
  `§` path. This is not a green suite.
- **Criterion 5.** `perry-lint --architecture-module kernel/ARCHITECTURE.md`
  reports 0 errors. The lint's module checks, run from a scratch script on both
  kernel documents, report 0 errors, and a control copy over the cap reported
  1.
- **Accepted behaviour.** A task has one `reason` field, so a `drop` from
  `blocked` can pass on the block's reason.
  `test_a_blocked_tasks_reason_satisfies_drop` pins this, and decision 13
  records it.

## Architecture review — BLOCKED on the user gate, then answered

**Trigger facts.** Root architecture edit and module architecture edit are
true. The other four triggers are false: listed boundary paths, a new
top-level directory, a new bin executable and a contract-version change.

**The block.** The reviewer was a fresh-context Claude subagent in its own
worktree. The block is verbatim:

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: fresh-context Claude subagent (claude-opus-5-5) in worktree agent-a151d27f1b71e391a; not the TASK-488 author, and given no author verdict; timestamp: 2026-09-29 11:38 +0800
Base: 4a6d13231aaf5cd5ed651022b0d4f58208eb8baa
Head: 16f96d691a383a86f0dff89af6f214cbe0fe01f4
Triggers:
(1) Listed boundary paths: false. `--name-status` has no `viewer/parsers.py`, `bin/lib/`, `schema/`, root `SKILL.md` or lane `SKILL.md`.
(2) New top-level directory: false. The `git ls-tree -d` top-level lists are identical at base and head. `templates/` exists at base (README, knowledge-base/, ops/, software/), and `kernel/architecture/` is nested.
(3) New bin executable: false. `--raw` shows `bin/ARCHITECTURE.md` as 100644→100644, and every added file is 100644.
(4) Contract-version change: false. `SURFACE = "1.0"` sits at `surface.py:15` in both trees, root §5 (`:227-254`) is unchanged, and `schema/` is untouched. The new `perry.json` declares format 1 and version 1, which is a new file, not a changed declaration. The shape does change: `commands[]` key `summary`→`purpose` (`surface.py:56`, `:231`). 1.0 is unreleased: the last record in `release/records.jsonl` is dated 2026-09-23, before the kernel merged (afa054af, 2026-09-26), and nothing outside `kernel/` reads the key.
(5) Root architecture edit: true. Only commit 4dc3a4dc touches it, at `:181`, `:272`, `:284` and `:396`.
(6) Module architecture edit: true. `kernel/ARCHITECTURE.md` (4dc3a4dc, 0dee0e69, 0eb4cbbb), the new `kernel/architecture/sections/§5-contracts.md`, and `bin/ARCHITECTURE.md`.
Context: I read root §1, §3 and §6 at both SHAs (their line numbers are identical, and the file is 499 lines in both). I read §2 and §5 on demand. Component mapping: `kernel/**` maps to `kernel/ARCHITECTURE.md` plus its section file; `bin/ARCHITECTURE.md` maps to `bin/`; `templates/process/perry.json` falls under §2 `:136-143`, which declares no module document, so none is missing (the kernel §3 diagram at `:74` places it on the skill side); `tests/test_kernel_suite.py` falls under `tests/` (`:145-148`), which also has no module document. Gate sources: DESIGN-017 §5.1 (`:205-218`, "User confirms … the Forbidden lines", "the question reaches the user before the change lands"), `packs/software-ops/architecture.md:142-144` (documents bind regardless of draft labels; task authors cannot award the gate), and DESIGN-023 §7 (base `:380`, "the user approves a kernel change in a revision. Never inside a task"; eaba79a2 `:457`). No trigger fact is unknown.
Rules:
- ARCHITECTURE.md:45-56 (§1) — holds — additions are stdlib JSON data and tests; no host, service or cross-project state.
- ARCHITECTURE.md:172-173 (§3 allowed directions) — holds — no new import; `kernel/perry_kernel` never references `templates/` (git grep empty).
- ARCHITECTURE.md:176 (§3 Forbidden: second reader) — holds — `perry.json` is not a state file, and only tests read it.
- ARCHITECTURE.md:177-178 (§3 Forbidden: lane computing) — not touched.
- ARCHITECTURE.md:179-181 (§3 Forbidden: resolver, and its sunset) — holds — the only change adds `bin/perry-churn § detect_perry`, as the user decided on 2026-09-26 (spec "Carried, decided by the user 2026-09-26"; TASK-487 review round 3, question (a)). The line count is unchanged (499→499). The claims check out against `bin/perry-churn:305-342`: it walks to the first `.perry/`, stops at the git top level, takes `-C`, and reads no `--root` and no environment variable.
- ARCHITECTURE.md:182 (§3 Forbidden: an agent writing this file) — holds — the agent typed only user-decided text plus a §8 line, which NN-6 `:312-316` permits (TASK-486 and TASK-487 precedent).
- ARCHITECTURE.md:258-272 (NN-1) — holds — the rule body is unchanged; the sunset now reads "only `export`, to decide `unchanged`, and `import` read the export", as the user decided on 2026-09-25 (spec; DESIGN-023 §9, 2026-09-26 entry), and matches kernel `:93-95`.
- ARCHITECTURE.md:274-284 (NN-2) — holds — same wording change, same decision.
- ARCHITECTURE.md:286-292 (NN-3) — not touched — no write path changed.
- ARCHITECTURE.md:294-301 (NN-4) — not touched — no `bin/` code changed.
- ARCHITECTURE.md:303-308 (NN-5) — holds — the new tests use a Sandbox or a mkdtemp directory. The kernel suite on a git-archive copy of head gave 238 OK and 1 skip, and the live store was absent before and after.
- ARCHITECTURE.md:310-320 (NN-6) — holds for root — the changed §3 Forbidden line and §6 sunsets were decided first; §1 and the §5 versions are untouched; §8 was appended.
- bin/ARCHITECTURE.md:101-115 (§3) — not touched.
- bin/ARCHITECTURE.md:171-185 (NN-B1, NN-B2) — not touched.
- bin/ARCHITECTURE.md:187-213 (NN-B3) — holds — the sunset uses root §3's words exactly, decided by the user on 2026-09-26; the file is 277 of 600 lines.
- bin/ARCHITECTURE.md:215-221 (NN-B4) — not touched.
- kernel/ARCHITECTURE.md:12-27 (§1) — holds.
- kernel/ARCHITECTURE.md:54-68 (§2 budget) — holds — the kernel still has 8 concepts, 10 command groups in use (cap 12), 4 guard kinds and 9 field kinds; the template uses only `required` and `actor` guards.
- kernel/ARCHITECTURE.md:82 (allowed directions) — holds.
- kernel/ARCHITECTURE.md:85-86 (stdlib only, no markdown) — holds — no new import; the kernel suite passes 238 OK and 1 skip on a head copy with all 1,216 `*.md` files removed.
- kernel/ARCHITECTURE.md:87-89 (runs no command) — not touched.
- kernel/ARCHITECTURE.md:90-92 (base :89-91, Forbidden: naming a template-declared name) — contradicts — the base line, "matches whole words", is a decided Forbidden line. Against it, head kernel source has hits: `open` in commands.py, guards.py, store.py and surface.py; `reason` in cli.py; `summary` in surface.py. The candidate passes only because commit 0eb4cbbb rewrote the line to "string literal", where my own scan finds 0 hits in 12 files. That rewrite has no user confirmation, only the decision-13 delegation. It also weakens the check: `dict(done=True, summary=s)` and `class S: done = 1` give no finding with the candidate's `hits()`.
- DESIGN-023 §7 (base :380 / eaba79a2 :457, kernel change needs user approval in a revision) — contradicts — commit 0dee0e69 changes `kernel/perry_kernel/surface.py`. Its only basis is the PMO's second 2026-09-29 entry (`:526-532`), written after round 2 stopped at 4608b6b8. That entry "corrects" the delegated decision as first recorded, which said "The kernel's code and concept budget are unchanged" (`:524-525`).
- kernel/ARCHITECTURE.md:93-95 (any other path) — not touched.
- kernel/ARCHITECTURE.md:136-140 (NN-K1) — holds against head §3's literal check only; its outcome depends on the question below.
- kernel/ARCHITECTURE.md:142-146 (NN-K2) — holds — shown by the md-free run.
- kernel/ARCHITECTURE.md:148-186 (NN-K3 to NN-K8) — not touched — `usage()` swaps the key it reads, and the help text is unchanged.
- kernel/ARCHITECTURE.md:188-191 (NN-K9) — holds — the live store `/Users/bytedance/proj/Perry/.git/perry` was absent before and after every run.
- kernel/ARCHITECTURE.md:193-197 (NN-K10) — not touched.
- §5-contracts.md:754-765 (§5.6 `describe` and versioning) — holds — `purpose` is named, no version bump, 1.0 is shown unreleased, and nothing outside `kernel/` consumes the key.
- §5-contracts.md whole file against base §5 — holds — the move is faithful. The only differences from base are the carried items the user decided on 2026-09-25 and 2026-09-26, plus the `purpose` line; spot-checked against `commands.py:882` and `:886` and `values.py:19`.
Decision: BLOCKED — `kernel/ARCHITECTURE.md:90-92` and DESIGN-023 §7 fail on the user decision gate. Every root and `bin/` rule holds.
User decision required: kernel §3 Forbidden line (`kernel/ARCHITECTURE.md:90-92`) plus DESIGN-023 §7. The question: "On 2026-09-29 you delegated decision 13, which fields and process logic the first template keeps. Does that delegation also cover (a) narrowing Goal 1's check and the kernel §3 Forbidden line from whole words to string literals? That lets `open`, `reason` and `summary` appear in kernel source as identifiers, keyword names and prose, and lets a template-named key built by `dict(done=...)` go unflagged. Does it also cover (b) the kernel code change that follows: `describe`'s per-command key `summary` renamed to `purpose` inside the unreleased `surface` 1.0, with no version bump? Or should the template keep round 1's non-colliding names (`gist`, `active`, `block_reason`, and so on), with the whole-word check and `kernel/perry_kernel/` both left unchanged?"
Not checked: the user's in-session decisions of 2026-09-25, 2026-09-26 and 2026-09-29, which I took from TASK-488-spec.md and DESIGN-023 (header `:9`, §9) — no USER- row exists for them; `bash tests/run`, `--tier affected`, `tests/merge-check` and the merge with current main (eaba79a2); perry-lint's architecture modes; template-guard mutants (criterion 8); whether decision 13's list is the right method; Python other than the host's; Linux.
=== END COMPLIANCE ===
```

**The user's answer, 2026-09-29, in session.** The PMO put both parts of the
question in plain terms and recommended option A:
- **A.** Match string literals, and rename the kernel's key. The names stay
  `summary`, `reason` and `open`. The cost: a template name used as a Python
  identifier in kernel source is not caught.
- **B.** Keep round 1's names and leave the kernel unchanged.

Ran Jiao answered **"A"**, and DESIGN-023's header and § 9 record it. This
answers the "User decision required" line above. The candidate is unchanged at
`16f96d69`, and every other rule holds, so the gate passes on the same
candidate.

## Descriptive drift the review reported (non-blocking), and where it goes

- **Root § 2's `templates/` entry** (`ARCHITECTURE.md:136–143`) does not
  describe `templates/process/`. Its "a track's mode" becomes false at phase E.
  This goes to TASK-490.
- **`bin/ARCHITECTURE.md:236`** cites `bin/perry-churn:305–341`, but
  `detect_perry` ends at `:342`. This goes to TASK-490.
- **Kernel NN-K1** (`kernel/ARCHITECTURE.md:136–140`) says the kernel names no
  template field. Its check is now the literal grep. The user accepted that
  narrowing, and nothing needs to change.
- **"Whole words"** survives only in a history entry in kernel § 8, which is
  correct.
