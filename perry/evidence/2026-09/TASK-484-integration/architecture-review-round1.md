# TASK-484 — integration architecture review round 1 (fresh context): BLOCKED

Integrator: PMO, 2026-09-23. Candidate 9eb97225 merged onto main 19d951bb as
`integ/task-484` with the 0.1.23 allocation, head e6c4269c.

Summary of the returned block (fresh-context reviewer, 2026-09-23 02:56 CST):

- **Triggers.** Listed boundary paths TRUE (`schema/next-contract.md`);
  contract-version change TRUE (perry-next 1.3 → 1.4; product 0.1.22 → 0.1.23,
  neither declared in root § 5, so NN-6 is not engaged); the other four FALSE.
- **Holds:** § 1 scope (`project.packs` reads the project's own declaration, not
  this PERRY_HOME's installs); § 2 `bin/` owns the evaluator and `reference/`
  the rules (the `contains` operator is evaluator vocabulary, with the precedent
  that the operator set was never declared in the schema); § 2 `schema/` page
  count; § 3 second reader and NN-1 (`next_facts` opens no file — every fact
  comes from the payload or an existing parser function); § 3 other Forbidden
  lines; NN-2, NN-3 not touched; NN-4 (the severity marker table is closed and
  `""` is an answer, never an inference); NN-5; NN-6 not engaged; § 5 compact
  strictness (`architecture` is projected whole, computed once); bin/, release/
  and tests/ module rules.
- **BLOCKED on two contradictions**, both agent-correctable (no decided section):
  1. `work/reference/digests.md:232` and `:242` still say the undigested-`inputs/`
     suggestion stays out of the next-step position and that the rule table names
     no rule for it. `R-inputs-waiting` (`reference/next-rules.json:302-312`) makes
     both false; a lane following that text drops a recommendation the block
     returns (ARCHITECTURE.md:104-107).
  2. `ARCHITECTURE.md:357-361` (§ 7's eighth open question) still says the rule
     table has a rule for none of the four marked lane lines.
- **Also false, to correct in the same round:**
  3. `reference/next-rules.json:25-28` claims the threshold and `bin/perry-state`'s
     literal are kept equal by `tests/test_next_section.py`. No test reads
     `bin/perry-state`'s `180`; changing it reddens nothing.
  4. `bin/perry-state:2046` warns at `> 180` while the rule fires at `ge 180`
     (`reference/next-rules.json:395`), so at exactly 180 days the recommendation
     arrives a day before the warning — the opposite of the note's own rationale
     and of `reference/next.md:350`.

User decision required: none.

Not checked: the suite (V4's gate); `contains` over a fact that is `None` (it
raises a rule error rather than not firing — unreachable today, since
`project.packs` is always a list); whether `digest` and `architecture-audit` need
`next-close` markers; rule order against § 5.10; root § 2's config-parsing claim
against `bin/perry-state`'s own `parse_config`/`load_packs` (pre-existing).
