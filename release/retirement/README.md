> Historical source-stage inventory. The proposal labels and original pending
> statements below are retained for provenance, not as a current blocker list.
> Actual user approvals and final local activation/V5 acceptance are recorded in
> `perry/evidence/2026-10/TASK-494-formal-cutover-20261020/FINAL.md`.
> Current source layout is documented in the root README. Archived F preparation
> inputs live in [pre-cutover-notes/](pre-cutover-notes/); the removed viewer is
> documented in [viewer.md](viewer.md). Inventory JSON/TSV bytes remain unchanged.

# DESIGN-023 H retirement candidate

This is a finite source proposal at immutable base
`b9be4d39f52ce1266534215b999c9db408b03bc5`. It does not authorize live activation,
record independent acceptance, or supply the user's H/V5 sign-off.

- [disposition.json](disposition.json): exactly 610 original tool/check/schema/
  test/contract rows, final destination paths, rationale and source hashes. Every
  row remains `PROPOSAL`; dropped rows are never called accepted or complete.
- [source-inventory.json](source-inventory.json): compact immutable independent
  index with every row key, source hash and original check expression/red scenario.
  The original 10 MB scratch inventory's SHA256 is retained for provenance.
- [dropped-checks.tsv](dropped-checks.tsv): all 423 concrete deletion proposals,
  including test/source files. Each requires the actual user decision.
- [path-migrations.tsv](path-migrations.tsv) and
  [check-disposition.tsv](check-disposition.tsv): compact review tables.
- [manual red review](manual-red-review.md) and
  [disposition resolution](manual-disposition-resolution.json): 22 supported author
  red demonstrations; 58 exact old-check replacements were not demonstrated and
  are now explicit deletion proposals, preserving their partial/pending history.
- [consumers.json](consumers.json): all 1,508 inventory consumer file hits, source
  hashes and referenced lines/symbols. Historical text is preserved. F/G-owned
  and external call sites remain visible integration blockers.
- [actual H file changes](source-changes.json): original/candidate hashes for
  edited source files, plus separately reviewable root architecture/docs.
- [test disposition](../../tests/test-disposition.json): every legacy test file
  and native test source at the base. The new [suite](../../tests/README.md)
  replaces the old corpus; this is not an old full/slow pass.
- [reference disposition](reference-disposition.json) and
  [real reference red runs](reference-red-demonstrations.json): source procedure
  migration and three refused isolated CLI fixtures.

Audit the finite identities, source hashes, existing successor paths, unchanged
kernel production code and single native wrapper:

```sh
python3 tools/retirement_audit.py --root /absolute/candidate
```

The audit does not infer semantic equivalence, consumer migration or acceptance.
[The procedure](../../reference/retirement-checks.md) names remaining manual
checks. Pending row-specific demonstrations are not hidden behind a skip.

## Reviewable behavior changes

`bin/perry` replaces both the forwarding index and `bin/perry-kernel`. No hidden
legacy aliases survive. Old schema/contracts, obsolete typed-state tools and the
full viewer parser retire only inside this candidate. The immutable source base
retains every deleted byte for review and rollback of source.

Retained host helpers live in `tools/`. Shell scripts remain shell. Knowledge,
roles and churn have [explicit new major read shapes](../../tools/helper-contracts.md).
Knowledge promotion is authored skill work, role-card migration must precede
agents-register retirement, and URL/task provenance requires actual source/native
review. Document preferences move to user-owned prose only after a real decision;
old configuration stays frozen input. These choices remain subject to H review.

## Integration and acceptance blockers

1. Independently review every semantic replacement and its concrete red evidence.
   Accept or reject each exact-check deletion proposal rather than mistaking a
   partial example for equivalence. The source audit is only structural.
2. Combine F and G deliveries with this H candidate. Root owns router/startup/
   dashboard files and F owns goals/decide/template/importer. They were deliberately
   not edited here. Detach F's importer from the removed library/parser, align
   exact helper/CLI names, and run the meaningful full/slow suite on the actual
   combined tree using independent `tests/merge-check` receipts.
3. Migrate and test required aiMark native probe, goals/decide adapters and
   knowledge/role/churn consumers. This executor edits no external project.
4. Allocate the product version and run `release/manage.py check --base ... --ref ...`
   on the integration branch. H does not allocate a competing delivery record.
5. Prepare Perry and SkyTonight source/store/export/backup receipts and rollback
   limits. Source deletion is reversible via Git; shared-store mutation has a
   separate restore boundary. No migration or live activation ran here.
6. Present the immutable combined candidate, finite dropped-check table, viewer
   disposition, changed contracts/targets, verification gaps and rollback limits
   to the actual named user for H/V5. Never infer that signature from the request
   to implement, a helper packet or an agent's passing test result.

## Combined-source corrections (historical proposal basis)

The source now assembles F/G and the reviewed native plan application seam.
Current accounting is in source-changes.json and consumers.json; original
610 inventory identities and hashes stay unchanged. The audit recognizes only
the exact two-file prefix-floor proposal and reports PENDING_USER_APPROVAL.
This is source accounting, not kernel approval or activation permission.

Combined safety review withdrew the R0090 architecture-cap demonstration: the
old predicate checked journal/evidence caps. R0090, R0094 and R0095 are now
explicit exact-threshold/grammar drop proposals (423 proposed drops total).
R0096 retains required May touch/Must escalate safety sections; mandatory
Context/Loads grammar retirement remains a separate user decision. See
combined-corrections.json. Original manual bytes are preserved in
historical-manual-red-review-H.json. Current safety helper fixtures and actual
independent review must replace, never silently rebind, old hook-packet evidence.

No source deletion on main, external live activation or H/V5 acceptance has
occurred. Full/slow results at earlier exact source are historical when later
source changes; use final exact candidate receipts before integration.

## Recorded user decisions — 2026-10-20

The user accepted all423 exact drop rows and R0096 Context/Loads grammar
retirement in the reviewed951c2789 snapshot, and authorized preserving aiMark
WIP while integrating its native adapter. The prefix-floor revision was separately
approved in DESIGN-023. The reviewed423 rows and R0096 still match this source
byte-for-byte. Actual replies and the approved snapshot hash are preserved in
`perry/evidence/2026-10/TASK-494-review-candidate/approval.json`.

The original source ledger and read-only audit intentionally remain PROPOSAL: they
do not authenticate or award human acceptance. Their historical pending fields
are superseded by the separate user decision record; final H/V5 remains pending
until actual local activation, independent integration and outcome verification.
