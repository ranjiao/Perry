# TASK-484 — architecture compliance, round 4 (PASS)

Same independent reviewer as round 3, resumed with its round-3 context; not the
author and not the integrator; no author compliance attestation. 2026-09-23
03:54 CST. Base `65b27e41`, head `2344182f` (branch `integ/task-484`; the
worktree was confirmed at that SHA). Copied by the PMO from the reviewer's
returned text.

## Scope of this round

`git diff 9ac0271f..2344182f` only — commits `701ee4f6` (the §7 marking) and
`2344182f` (the 0.1.23 re-allocation). Files: `ARCHITECTURE.md` (+13/-11),
`CHANGELOG.md` (+21), `VERSION` (0.1.22 → 0.1.23), `release/records.jsonl`
(+1). Round 3's findings on the integration commit `9ac0271f` stand and were not
re-derived. Round 3's head `c06c9b7b` is superseded, not amended: `9ac0271f` is
unchanged and the two new commits sit on top of it.

Triggers for this diff: root architecture edit TRUE (§7 and §8, one hunk);
contract-version change TRUE for the product version only (`perry-next/1.4` is
unchanged by these two commits and is not declared in root §5, verified in round
3); listed boundary path, new directory, new executable and module architecture
edit all FALSE.

## Rules

- **NN-6 (user-confirmed) — holds; round 3's blocker is cleared.** The §7 clause
  now reads `*Proposed — partly answered 2026-09-23 (TASK-484):*`. The addition
  is marked `proposed`, so the strict branch of round 3's question is satisfied
  and the permissive branch a fortiori; no user ruling is needed to land it. The
  compound marking is a new spelling in this file — the five existing agent
  markings are a bare `*Proposed*` under `TASK-442` — but NN-6 requires the
  marking, not a byte-exact form, and the compound reads correctly as an agent
  proposing a partial answer for the user to confirm.
- **NN-6's "may delete from neither" — holds; the §7 rewrap deletes nothing.**
  Word-level comparison of §7, whitespace-normalised: `9ac0271f` → head has
  exactly one non-insert opcode, `*Partly` → `*Proposed — partly` (703 → 705
  words), i.e. the two new words plus the recasing of `Partly` inside the
  marker; every other byte is line-wrapping. Against the **base** (`65b27e41` →
  head) §7 has **zero** delete or replace opcodes — pure insertion, 649 → 705
  words. This is the check that matters, since a rewrap could otherwise launder
  a loss that only shows against main.
- **§8 change log (descriptive, NN-6's free grant) — holds, and its new sentence
  is true.** "The clause is marked `proposed` because that is what §6 NN-6
  grants an agent for a §7 addition" matches NN-6 verbatim in substance. "The
  two annotations in §7 that are not so marked each name a user id" is true **by
  enumeration, not by sampling**: every status annotation in §7 at head is
  `*Closed 2026-09-21 (USER-987).*` (first question),
  `*Partly answered 2026-09-21 (USER-978):*` (second question), five
  `*Proposed*` under `TASK-442`, and the new
  `*Proposed — partly answered 2026-09-23 (TASK-484):*`; the third question
  carries none, and `*After a subcommand*` / `*In a standup's next-step
  position*` are emphasis inside the eighth question's body, not annotations.
  Exactly two are not marked `proposed`, and each names a user id. The retained
  parenthetical was verified in round 3 and is unchanged.
- **Preamble citation rule — holds.** The new marking and the new §8 sentence
  cite by section and by `TASK-484`, a member of `lib.PERRY_CITATION_FAMILIES`;
  no open question's id is introduced.
- **Header cap (≤500 lines) — holds.** 477 lines at head, 461 at base.
- **"No other section is edited" (§8's own claim) — holds.** The whole
  `ARCHITECTURE.md` diff against base is a single hunk, `@@ -367,10 +367,26 @@`,
  spanning the end of §7 and the head of §8.
- **§2 `release/` (typed records, deterministic projections) — holds.** The
  record was replaced, not edited in place, in the sense that matters: comparing
  the 0.1.23 records at `c06c9b7b` and head field by field, `notes`, `breaking`,
  `version`, `date`, `task`, `delivery`, `kind`, `phase`, `decision` and
  `integrator` are byte-identical and only `upgrade` differs. Record count 24 at
  both, 23 at base; the 23 earlier records are byte-identical to base **and** to
  `c06c9b7b`. `VERSION` is 0.1.23. The CHANGELOG's three sections are
  byte-identical to the record's three fields, so the projection is faithful,
  and the only line that differs from `c06c9b7b`'s CHANGELOG is the one upgrade
  bullet.
- **§5 `perry-state` contracts, schema → both sides** — not touched; no code,
  rule-file, contract-page or test change in this diff.

## The corrected upgrade note, read against 0.1.22 — true

It now reads: "A project whose `ARCHITECTURE.md` is exactly 180 days past its
last review now gets the standup warning on that day rather than the next, which
is the same day the new `R-architecture-stale` recommends the audit." Both
halves hold against the base: base `bin/perry-state` compares `rev > 180` and
head compares `rev >= ARCHITECTURE_REVIEW_DAYS`, so the warning does move onto
day 180; and "the new `R-architecture-stale`" is correct and no longer asserts
that 0.1.22 recommended anything — round 3 confirmed the base rule file contains
no architecture rule at all. Round 3's observation (b) is resolved; the sentence
now has only one reading and it is the true one.

## Decision — PASS

No contradiction, no descriptive mismatch, no missing context in this diff.
Round 3's single blocker is resolved by `701ee4f6` on the strict reading of
NN-6, so acceptance is no longer held at the user decision gate.

**User decision required: none.** The user may still later rule that an unmarked
task-id annotation is permitted in §7, in which case the marking can be
upgraded; that is an optional later edit, not a gate on this candidate.

## Not checked

The full suite (the integrator's gate, running separately — not run here, as
instructed). `release/manage.py check --base 65b27e41 --ref HEAD`, which the
integrator reports exits 0 and which the reviewer did not re-run; it verified
the same three properties directly instead — record append-only against base,
field-level equality of the replaced record, and byte-equality of the CHANGELOG
projection to the record. Everything outside `9ac0271f..2344182f` was carried
from round 3 by instruction and not re-derived.

Round 3's two standing observations remain: `DESIGN-020 § 5.10` still declares
`R-rollover` and `month.rollover_due` in batch 3 while the shipped batch
reclassifies `rollover` as never-recommended (the design document is not updated
by this candidate — the PMO recorded it as a `§ 9` change entry on main), and
the `contains` operator over a `None` fact raises rather than not firing
(unreachable today).
