# TASK-484 — integration architecture re-review (round 2): BLOCKED

Integrator: PMO, 2026-09-23. Corrected candidate 31e7ea24 merged onto main
e2ca3ac5 as `integ/task-484` ed82ff51 with the 0.1.23 allocation.

Summary of the returned block (fresh-context reviewer, 2026-09-23 03:21 CST;
mutations run in a `git archive` copy, the reviewed checkout untouched):

**Round 1's four findings are repaired and verified.** `work/reference/digests.md`
now says the next-step position carries `R-inputs-waiting` and that the lane
renders what the command returns; the shipped rule matches the page, and
`operations.inputs_oldest` really is the bare name `digest <path>` takes. § 7's
eighth question is annotated add-only — the only `-` line is re-emitted verbatim —
and the annotation is **true**: the four are the expired-sunset ADR, the
`DECISIONS.md` migration, the undigested `inputs/` line and the stale-digest
count, and of the 30 rule ids only `R-inputs-waiting` is one of them. The
threshold is now pinned (changing the constant reddens `TestTheRuleFile`), and
the boundary crosses on one day (`>= ARCHITECTURE_REVIEW_DAYS` against `ge 180`).

**Holds:** § 1 scope (`project.packs` reads the project's own config, never this
PERRY_HOME's manifests); § 2 `bin/` owns the recommendation and `reference/` the
rules; § 2 lanes; § 3 Forbidden lines; NN-1 (no file opened in `next_facts`; the
document is dated once and republished); NN-4; NN-5; § 5 compact strictness;
bin/, release/ and tests/ module rules; the rule order and page claims;
`next-contract.md`'s 1.4 block; the coverage guard's reclassification.

**BLOCKED on three descriptive mismatches, all new this round:**
1. `reference/next.md:351-353` says a project declaring no pack never gets the
   rule. False: `bin/perry-state:207-213` defaults to `["software-ops"]` when the
   config holds no `Packs` record, and this round's own fixture is the
   counterexample (`tests/config_store.py:42-45` has no `Packs` key, yet the
   `architecture_stale` fixture's primary is `R-architecture-stale`).
   `schema/next-contract.md`'s 1.4 block states it correctly, so the diff
   contradicts itself. The same shorthand is in `CHANGELOG.md:11` and in the
   0.1.23 record's note — and the record is what the CHANGELOG projects from.
2. `ARCHITECTURE.md:384-385`'s parenthetical claims the two § 8 entries below
   predate the preamble's cite-by-section rule. That rule was added
   2026-09-09 (commit 9bbd25a9); both entries are dated 2026-09-21.
3. `reference/next-rules.json:27` attributes the at-or-over boundary pin to
   `TestTheRuleFile`, which stays green when `bin/perry-state:2053` is reverted
   to `>`; the red comes from `TestCadenceAndOperations`.

**User decision required — § 6 NN-6 (`ARCHITECTURE.md:295-296`), a user-confirmed
rule:** "It may ADD to §6 and §7, marked `proposed`." May an agent add a
"*Partly answered 2026-09-23 (TASK-484):*" clause to § 7's eighth question under
a task id, or must an agent's § 7 addition be marked `proposed`, with an
answered/closed annotation reserved for a user id (as USER-978, USER-987 and
USER-989 all are)? The clause's content is add-only and verified true; the
question is the marking and the authority.

Not checked: the full suite (V4's gate; the reviewer ran two modules and two
mutations in a copy); whether `contains` over a `None` fact should not fire
rather than raise (unreachable today); rule order against DESIGN-020 § 5.10
itself; `packs/software-ops/architecture.md`'s own review cadence; root § 2's
config-parsing claim (pre-existing); whether `digest` and `architecture-audit`
need `next-close` markers.
