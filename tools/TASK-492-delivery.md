# TASK-492 F delivery and activation hand-off

This coding branch owns the process template, goals/decide procedures, the
one-shot adapter and focused tests. It does not own root G/H, an independent
review, live activation, release allocation or human sign-off.

## Measured coding verification

- New tests: 16/16, `PERRY_HOME="$PWD" PERRY_KERNEL_TESTING=1 python3 -m unittest discover -s tests -p test_goals_decide_native.py`.
- Kernel neutral template/vocabulary: 15/15, `PERRY_HOME="$PWD" PERRY_KERNEL_TESTING=1 PYTHONPATH=kernel/tests python3 -m unittest test_vocabulary test_template`.
- `git diff --check`: clean. Full/slow legacy tiers intentionally left to root's combined integration, as dispatched.
- Actual Perry copy: 602 protected items / 1200 events; complete 204-item F plan
  (4 phases, 31 Objectives, 101 KRs, 19 checks, 22 designs, 27 ADRs). Dry-run and
  sparse-prefix refusal leave store unchanged; actual source hash mismatches 0.
  Perry apply/replay parity is NOT passed while the DESIGN-018 floor is missing.
- Actual SkyTonight copy: 34 protected items / 68 original events unchanged;
  60 F items appended (3 phases, 8 Objectives, 24 KRs, 24 checks, 1 design).
  Final seq 264; idempotent rerun adds no event; export→empty import→export bytes
  equal; repeat nonempty import refused; actual source hash mismatches 0.
- Durable artifacts: `/Users/bytedance/proj/Perry/perry/evidence/2026-10/TASK-492-architecture/migration/`.
  Includes exact bounded copied inputs, hashes/plans, commands, pre-state snapshots,
  receipts/logs and SkyTonight's validated native export. No rehearsal DB is an
  activation artifact. The architecture checkpoint paths are returned in RESULT.

## Usage and guarantees

`tools/goals_decide_migrate.py --source <copied-actual-project> --root
<scratch-anchor> --store <scratch-db> --work <external-directory> --dry-run`
reads and emits plan.json, source hashes, exact legacy rows, typed relations,
version-scoped label maps, filename ceilings, warnings and requirements. Both
root/store must be children of work; work must be external to a Git checkout
and distinct from source. Pin PERRY_HOME to the tested checkout. All nested
kernel commands name root/store and set PERRY_KERNEL_TESTING=1.

Add `--apply` to rehearse only on a copied native store. It never imports over
that store; it applies a compatible template and uses native create/move/rel.
On interruption, result.json records partial status and a unique commands-N.json
of writes. Re-query source_key items and reconcile hashes before resuming. An
idempotent rerun writes no event. Unknown types, invalid revisions, dangling or
ambiguous linkage and sparse unsupported filename floors refuse explicitly.

Native task/ask/risk definitions are unchanged. New KRs/designs retain typed
work_items/implemented_by refs, preserving original work item seqs and events.
A new normal contributes_to/implements relation touches both items and therefore
is not used by this additive migration. Imported historical approvals/measurements
are labelled historical, never presented as new consent or rerun evidence.

Perry includes the archived v1 snapshot, all v2–v4 rows, phase records, checks,
measurements and revisions; actual filesystem design/ADR headers include
uncommitted ADR-026/027 and old superseded/archived metadata. IDs remain native
and version-safe; exact legacy IDs stay labels. A conventional alternate KR
spelling is resolved by numeric grammar and explicit version, never title/date.
Ambiguous task overall attribution may resolve only via declared design_refs
whose Linked OKR explicitly names that same KR and one version.

## Actual primitive gap

Perry has no DESIGN-018 file. Preserve exact existing DESIGN IDs by raising its
prefix floor before creating real DESIGN-019; existing CLI cannot do this after
work activation. See TASK-492-kernel-proposal.md. The adapter plans every record
but refuses apply before any store change unless `describe` advertises the
reviewed `template apply` ceilings input. The integration branch must implement
and approve that generic contract, then rerun Perry. No kernel change is authored
here. SkyTonight has contiguous DESIGN-001 and no ADRs, and uses existing CLI.

## H test dispositions and remaining source boundaries

- Old tests that demand exactly three types/template version 1 are superseded by
  F's additive template; retain task/ask/risk semantics and kernel vocabulary and
  lifecycle checks. In particular kernel/tests/test_work_template.py has exact
  row-C-only assumptions; H owns retirement/adaptation, not broad skips here.
- Legacy goals writer suites (commit/link/KR/check/measure/phase/draft) and decide
  writer suites must become read-only boundary tests or retire under H's explicit
  table. This branch adds refusal tests and leaves old failures visible.
- Legacy bin/perry-okr remains outside this agent's ownership. Root must freeze/
  retire its write path before activation. The legacy narrative scaffolds under
  goals/state and decide/state also contain old headers/commands; the new lane
  procedures specify native metadata and narrative bodies only. Root/H must
  reconcile/delete those scaffolds, remaining legacy consumers and source pins.
- Root SKILL, common snapshot/next/config/recovery, work/, schema, setup, release
  and target architecture are unchanged here. Root owns G/H reconciliation.
  Root's current file-ownership table is historical for the migrated lanes.

## Authored release notes (no version allocated)

Changes: Add native objective/KR/check/phase/design/ADR types; switch goals and
decide to kernel structured writes with narrative attachments; freeze legacy
lane writer entry points. Add bounded copied-source migration with version-safe
identities, source hashes, honest unknowns and strict reconciliation.

Upgrade: Review the exact F template/procedures, implement/approve the generic
prefix floor if required, back up native stores and actual source files, rehearse
Perry and SkyTonight from fresh copies, and perform reviewed native additive
writes. Keep old stores/documents as frozen history. Do not copy rehearsal DBs
or import over activated stores.

Breaking: Legacy perry-goals/perry-decide writers now refuse. Root G/H must
replace remaining consumers and old template-only tests before final cutover.
No source/test branch result grants H/V5 acceptance or publishes a release.

## Safe activation sequence (root/decide/integrator)

1. Review this exact commit against TASK-492, plus the bounded kernel proposal.
   Allocate the release only on the integration branch; do not self-merge.
2. Complete G/H owned root/consumer/scaffold changes and approved generic floor
   capability. Run the combined final/full/slow gates and independent review;
   focused coding checks here do not replace those gates.
3. Take fresh read-only online backups/exports of both live native stores and
   copies/hashes of actual legacy files, including uncommitted ADR metadata.
   Compare current native item/event snapshots with the reviewed rehearsal base;
   if moved, rebuild/review a fresh plan rather than replay stale guessed IDs.
4. Rehearse with explicit scratch roots/stores. Require zero source mismatches,
   protected work item/event parity, exact filename ceilings, no-write rerun,
   and export→empty import→export byte equality. Preserve commands and receipts.
5. With the actual reviewed activation authority, root replays reviewed native
   command inputs with live --root/--store and fresh expect values, checking the
   pinned store seq before each step. Reconcile any concurrent write instead of
   blindly retrying. The rehearsal adapter itself deliberately refuses live roots.
   Never import nonempty, copy a rehearsal DB, synthesize history or seed fake IDs.
6. Root/decide resolves current native references in TASK-492-adr-successor.json,
   creates the successor ADR and owned body, adds typed authority/goal links and
   records actual activation evidence/consent. Do not preallocate ADR-028.
7. Export the live store through the kernel, verify old work items/events remain
   unchanged and new mappings/ceilings match, then freeze/retire legacy lanes.
   Keep recovery backups. Goals/phase replanning is a separate user decision.
