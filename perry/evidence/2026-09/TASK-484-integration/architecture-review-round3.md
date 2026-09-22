# TASK-484 — architecture compliance, round 3 (BLOCKED)

Independent reviewer, fresh context, not the author and not the integrator; no
author compliance attestation. 2026-09-23 03:45 CST. Base
`65b27e41`, head `c06c9b7b`. Copied by the PMO from the reviewer's returned
text; the headings are the reviewer's.

## Triggers

- **Listed boundary path touched — TRUE.** `schema/next-contract.md` (+28/-2), a
  published contract page (§2 `schema/`).
- **Root architecture edit — TRUE.** `ARCHITECTURE.md` +16/-1. Exactly one `-`
  line (`  rule.`), and its text is re-emitted at the head of the replacing
  line, so nothing is deleted from the document's prose. Sections touched: §7
  (the eighth open question) and §8 (new top entry). No other section. File
  461 → 475 lines, under the ≤500 cap.
- **Contract-version change — TRUE, twice.** `perry-next/1.3 → 1.4` and product
  `0.1.22 → 0.1.23`. **Neither is declared in root §5** — §5's only versioned
  contract is `perry-task list --json` 2.4; the `perry-state --json`/`--compact`
  contract carries no version and `perry-next` is named nowhere in §5. NN-6's
  "a contract version in §5" clause is therefore not engaged.
- New directory, new executable, module architecture edit — all FALSE
  (`bin/ARCHITECTURE.md` is not in the diff).

## Rules

Every root rule §1–§8 was read at head and mapped to the diff. All hold:

- **§1 Mission & scope** — every new fact is mechanical. `project.packs` is the
  project's own declaration, not this installation's inventory: `perry-state`
  takes `packs[].name` from `project.config` and keeps the name with
  `present: False` for an uninstalled pack. Re-derived by probe against head's
  `parse_config`: `Packs: other-pack` → `names=['other-pack'] present=[False]`.
  No cross-project state is reached.
- **§2 `bin/` owns the recommendation, `reference/` the rules** — the evaluator
  is in `bin/`; the table, the new threshold and the four new rules are
  declared in `reference/next-rules.json`. The `contains` operator is evaluator
  vocabulary declared in the rule file's own note, where the operator set has
  always been declared.
- **§2 lanes: a lane renders the next step, does not add, drop or reorder** —
  **round 1's finding, now repaired.** `work/reference/digests.md` states that
  the next-step position carries `R-inputs-waiting` and that the lane renders
  what `perry-state --section next` returns, in the order returned. The base
  text said the opposite. The stale-digest paragraph still keeps that state off
  the position, correctly: no rule and no fact exist for it (27 rules
  enumerated, none names it).
- **§2 `tests/`** — two modules edited, none added or removed.
- **§3 allowed directions and the four `Forbidden` lines** — no second reader;
  no lane computes a number; no tool reaches another project
  (`PERRY_HOME/packs/<name>/pack.md` is Perry's own install, and
  `project.packs` deliberately does not depend on it).
- **§5 `--compact` is a strict projection of `--json`** — `COMPACT` projects the
  architecture row, so the new `days_since_review` key flows through as a
  projection; `project_compact` selects and never recomputes, and `rev` is
  computed once and used by both the warning and the payload.
- **§5 the schema → both sides** — not touched.
  `schema/state-schema.json § thresholds` genuinely has no
  `architecture_review_days` entry (enumerated: `in_progress_idle_hours`,
  `knowledge_stale_days`, `kr_measure_due_days`,
  `review_fail_rounds_before_escalation`, `review_idle_days`,
  `session_context_ceiling`, `stale_run_days`), which is what the rule file
  claims.
- **NN-1 one reader per state file** — `next_facts` opens no file. `cadence`,
  `ops` and `risks.top.severity_rank` come from the payload, and
  `architecture.days_since_review` is republished from the single `days_since`
  call the stale-review warning already made. The document is dated once, not
  twice.
- **NN-2, NN-3** — not touched; the diff adds no writer.
- **NN-4 deterministic tools decide nothing about meaning** — `risks.top_rank`
  is a closed nine-entry table in `viewer/parsers.py`, matched only as a
  standalone first token. The high markers are exactly `H`, `高`, `🔴`, which is
  what `reference/next.md` and the CHANGELOG both list — exhaustive, re-derived
  from the table. `""` is an answer, never an unknown, and `URGENT: …` ranks
  `""`.
- **NN-5 the suite never writes into the tree it runs in** — the new fixtures
  write into `build()`'s temporary root.
- **NN-6** — **open, not resolvable from the file.** See the blocker below. The
  §8 entry is descriptive and within NN-6's free grant. No §1, §3-`Forbidden`,
  §5-version or §6 rule is changed.
- **§7 open questions** — holds on content, open on marking. The annotation's
  content is re-derived true: the four marked lane lines are the expired-sunset
  ADR, the `DECISIONS.md` migration, the undigested `inputs/` line and the
  stale-digest count; of the 27 rules + 3 overlays only `R-inputs-waiting` is
  one of them, so "a rule for none of the four" now holds for three. Citation
  hygiene is respected: the new §7 clause and the new §8 entry name the section
  and `TASK-484`, never an open question's id.
- **§8 change log** — every clause re-derived. "The preamble has asked since
  2026-09-09": `git log -S"never by its id" -- ARCHITECTURE.md` returns exactly
  one commit, `9bbd25a9`, authored and committed 2026-09-09. "The two entries
  below were written after that and name theirs": the USER-989 entry landed in
  `5651e663` and the USER-987 entry in `664ca039`, both 2026-09-21, and both
  write the section with its question number. This is round 2's second finding —
  the base claim was that the entries *predate* the rule — and it is repaired.

## Round 2's three findings, re-derived independently

1. **Pack default** — repaired and true. Probe of head's `parse_config` on the
   reviewer's own temp roots: no `Packs` record → `['software-ops']`;
   `Packs: none` / `''` / `无` / `—` → `[]`; `Packs: other-pack` →
   `['other-pack']` (present False); `Packs: software-ops, other-pack` → both.
   `reference/next.md` and its facts row are true, and the CHANGELOG and the
   release record say the same thing in the same terms.
2. **§8 dating** — repaired and true (evidence above).
3. **Test-class split** — repaired and true, verified by mutation in a
   `git archive` copy of `c06c9b7b`, restored each time against
   `git show c06c9b7b:bin/perry-state`. Baseline 11 tests OK. Mutant A,
   `>= ARCHITECTURE_REVIEW_DAYS` → `> ARCHITECTURE_REVIEW_DAYS`:
   `TestTheRuleFile` 7 tests OK, `TestCadenceAndOperations` FAILS at `age=180`
   with `(True, True) != (False, True)`. Mutant B,
   `ARCHITECTURE_REVIEW_DAYS = 180 → 200`: both red. That is exactly the split
   the rule file now claims, and the renamed
   `test_the_architecture_age_is_one_number_and_the_rule_says_at_or_over`
   claims only the rule's half.

## Cross-document agreement

The 0.1.23 record's `notes`, `upgrade` and `breaking` are byte-identical to the
rendered CHANGELOG block (compared programmatically); `VERSION` is 0.1.23. The
pack sentence, the three high markers, the at-or-over boundary, the `contains`
operator and the `rollover` classification are stated consistently across the
release note, the CHANGELOG, `reference/next.md` and `schema/next-contract.md`.
The declared order in `DESIGN-020 § 5.10` is exactly the shipped order.

## Decision — BLOCKED

No descriptive mismatch remains and no new false statement was found. The single
blocker is the unresolved §6 NN-6 marking question, a user-confirmed rule, which
stops acceptance at the user decision gate rather than by another correction
round.

**User decision required.** NN-6, user-confirmed: "an agent writes and rewrites
the descriptive sections (§2, §4, §5's shapes, §8) freely. It may ADD to §6 and
§7, marked `proposed`, and may delete from neither." May an agent add the clause
"*Partly answered 2026-09-23 (TASK-484):*" to §7's eighth open question under a
task id, or must every agent addition to §7 be marked `proposed`, with an
answered/partly-answered/closed annotation reserved for a user id? The reviewer
states explicitly that this is not answerable from the file alone: the sentence
granting agents §7 additions requires `proposed`, while the sentence listing
what must be asked of the user first ("§1, a `Forbidden` line in §3, a contract
version in §5, or a confirmed rule in §6") does not mention §7 at all, and the
two clauses do not settle each other. The file's precedent points one way
without deciding it: every non-`proposed` §7 annotation at head names a user id,
and every agent-authored §7 entry is marked proposed under `TASK-442`. The
clause's content is verified true and add-only; only the marking and the
authority are open.

## Not checked

The full suite — V4's gate; the reviewer ran, in the archive copy only,
`tests.test_next_section` + `tests.test_next_closing` (66 tests, OK) and the
three contract modules (98 tests, OK). Also not checked: `contains` over a
`None` fact (it raises `_RuleError` rather than not firing — unreachable today,
since `project.packs` is always a list); whether `work architecture-audit`
should carry a `next-close` marker (`R-architecture-stale`'s `after` is `[]`,
precedented by R-setup, R-no-okr and R-phase-heartbeat, so nothing false is
claimed); root §2's config-parsing claim against `parse_config`/`load_packs`
(pre-existing, unchanged by this diff); `packs/software-ops/architecture.md`'s
own review cadence.

## Two observations, not treated as findings

a. `DESIGN-020 § 5.10` (user-accepted, USER-994) still declares `R-rollover` and
   the fact `month.rollover_due` in batch 3, while this diff reclassifies
   `rollover` as never-recommended. The deviation is scoped and reasoned in
   `perry/evidence/2026-09/TASK-484-spec.md`, the diff states it honestly, and
   the reason is true, but the design document is now out of date and nothing in
   the diff updates it.
b. The third 0.1.23 upgrade-note bullet ends "…it already got the recommendation
   there". Read against 0.1.22 that is false, because the base rule file
   contains no `R-architecture-stale` at all (zero matches in
   `git show 65b27e41:reference/next-rules.json`); it is true only read as a
   statement about the shipped release's two halves. Judged ambiguous rather
   than false; a one-word edit would remove the ambiguity.

## PMO action on this round

Both observations were acted on. (b) was corrected by re-cutting the 0.1.23
record through `release/manage.py patch` — commit `2344182f`. The blocker was
resolved by taking the strict branch of the reviewer's question rather than
waiting on the user: NN-6 permits an agent's §7 addition "marked `proposed`", so
marking it satisfies the strict reading and the permissive reading alike —
commit `701ee4f6`. Round 4 re-checked exactly those two commits. (a) is recorded
as a `DESIGN-020 § 9` change entry on main.
