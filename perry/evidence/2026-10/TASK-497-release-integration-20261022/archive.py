from pathlib import Path
import json,shutil,subprocess,hashlib
run=Path(__file__).parent;root=Path('/Users/bytedance/proj/Perry');base='3f663a10379a9bf9d2b33678e8950456bddfbbdf';candidate='c4fbc75de7ea067e9360d9df7a74b7ebe3fe5934'
def git(*args):return subprocess.check_output(['git',*args],cwd=root).decode().strip()
merge=git('rev-parse','HEAD');receipt=json.loads((run/'merge-slow/receipt.json').read_text())
assert git('rev-parse',f'{merge}^1')==base and git('rev-parse',f'{merge}^2')==candidate
assert git('rev-parse',f'{merge}^{{tree}}')=='3580d10dbcf49b50edc9b9dc48d2bf8ce6b58423'
archive=root/'perry/evidence/2026-10/TASK-497-release-integration-20261022';archive.mkdir(exist_ok=False)
for p in run.iterdir():
 if p.is_file() and p.suffix in {'.json','.log','.py','.md'}:shutil.copy2(p,archive/p.name)
shutil.copytree(run/'merge-slow',archive/'merge-slow')
meta=Path('/var/folders/6g/dpvy7sgj7918yj3pqwnvy5q00000gn/T/perry-scratch/Perry/design024-release-metadata-review-jkwe0ob_')
shutil.copytree(meta,archive/'independent-release-review')
text=f'''# DESIGN-024 independent local integration — 2026-10-22

**Integrated, unpublished.** Three bounded procedure deliveries were independently integrated by the PMO release integrator. Actual user authority in this chat was: “继续安排独立集成，按发布规则检查并合并这版实现”. The integrator did not author the product source. No push, tag, PR, public release or consumer migration was performed.

## Immutable subjects and allocation

- Actual main base: `{base}`.
- Product source: `3fb8839723c7b744ff610d837f3ab47c3adc33b9`; source base `89219446bb50cb7faef2249708d48e9225b5422b`.
- Isolated integration branch: `codex/design024-release-integration`; final integration candidate `{candidate}`.
- Actual primary-main no-ff merge: `{merge}`; checked merged tree `3580d10dbcf49b50edc9b9dc48d2bf8ce6b58423`.
- Final product version `0.1.32`; phase `004-guided` unchanged. [Canonical records](../../../..//release/records.jsonl) and deterministic VERSION/CHANGELOG remain product authority.

| Task and delivery | Patch |
|---|---|
| TASK-498 Project verification and artifact ownership contracts — `TASK-498-design024-project-contracts-20261022` | 0.1.30 |
| TASK-499 Established-project reconciliation and existing-capability identity lookup — `TASK-499-design024-reconciliation-lookup-20261022` | 0.1.31 |
| TASK-500 Scoped acceptance and ten-case conformance evidence — `TASK-500-design024-scoped-acceptance-20261022` | 0.1.32 |

The package TASK-497 Deliver DESIGN-024 general procedure contracts receives no fourth delivery record. Existing ledger bytes are an unchanged prefix; all three IDs were absent before allocation. [Allocation inputs/results](allocate.py) and individual TASK notes are retained here. No new phase or major version was allocated.

## Independent evidence and actual gates

The original [four source V4 PASS verdicts](../TASK-497-conformance/review-round-2/review.md) remain tied to exact source `3fb8839`; prior FAIL remains preserved. [Source identity](source-identity.json) compares all 24 product Markdown paths and four criteria byte for byte. All 74 kernel/bin/tools/process-template/governing-architecture/safety files are unchanged from source base; 58 local links resolve. Current-main PMO evidence was not altered by the source integration. The source delta is exactly 24 product paths plus the three release files.

The new release allocations received a separate [independent metadata review](independent-release-review/review.md), preserved verbatim with its raw JSON. That review supplies no replacement source verdict or human sign-off.

| Gate | Actual result |
|---|---|
| Startup and policy | Nonblocking recovery, no interrupted run or draft error; reviewed project policy and additive role union retained. Native source acceptance captured at store_seq1944. [Capture](startup.capture.json) |
| Direct complete full suite | Exit 0: kernel 288 tests (one skipped), helpers 182. Shared live store unchanged at seq1944; source guard clean. [Log](direct-full.log), [command](direct-full.json) |
| Release actual-base/final-ref check | Exit 0 with versions 0.1.30/31/32 and exact24 product paths. [Result](release-final.log) |
| Exact disposable slow merge suite | Exit 0: complete kernel/helpers stages plus offline integration self-tests. Exact counts and timings are retained in [suite.log](merge-slow/suite.log); this is the new native suite, not the retired corpus. [Receipt](merge-slow/receipt.json) |
| Receipt reconstruction | Exit 0. [Verification](receipt-verify.log) reconstructs the immutable inputs and identical merged tree; transcript/hash retained. This unsigned receipt proves test binding, not consent or evaluator independence. |
| Primary freshness and actual merge | Main remained `{base}` and clean before `git merge --no-ff {candidate}`. Actual merge parents and tree were checked against the receipt. [Command/results](actual-merge.json) |
| Whitespace and postmerge source | `git diff --check` passes; actual merged tree equals the checked tree. Product/version/protected comparisons are retained in [postmerge checks](postmerge.json). |

## Architecture, portability and limits

Independent inspection of governing ARCHITECTURE.md §§1/2/3/6 and the combined source diff confirms that reconciliation, ownership and acceptance meaning stays in skill procedures/narratives. Opaque refs, actual authority, recovery, source isolation and independent/human gates remain explicit. Kernel concepts/commands, process data, tools, dependencies and governing targets are unchanged. Code-backed architecture start/delivery checkpoints are not applicable to this Markdown method delivery; no invented scan result or metric is supplied.

Maintained source examples remain project-neutral; no consumer path or application becomes a requirement. English skill procedure surfaces follow existing document language. Existing English/Chinese README/INSTALL surfaces are unchanged. Existing dispatch lexical false-refusals are disclosed and remain unfixed; no bypass or ACL capability is claimed.

This integration proves local product source and release metadata only. Consumer activation, installed package, engine/device/LAN/runtime behavior and actual human visual/V5 acceptance are excluded. The exact committed driver and ten-case source review remain isolated synthetic evidence; explicit synthetic Resume is not real user consent.

## Archival and native receipt boundary

This report and verbatim raw artifacts are a separate PMO-only archive **after** the checked merge. Its later archival commit is not represented as the tested tree, and it adds no product delivery/version. Product, protected and release bytes remain equal to the checked merge. No circular self-commit or self-receipt hash is claimed.

The native parent remains done/V4 with its original independent reviewer/evidence. A hashed attachment to this report and an updated integration next_action are recorded through explicit-root native calls with factual actor/session and fresh expect. The resulting native records and optimistic write receipts are retained alongside this report; no terminal task is reopened. Candidate/reviewer/integrator worktrees remain retained for receipt recovery.

Scratch source: `{run}`. Initial scratch inspection failed on Git's quoted Unicode path presentation; NUL-delimited enumeration corrected the inspector before the successful comparisons. There was no product-source failure or fix. Update-check ran in developer report-only mode and produced no output; no checkout update occurred.
'''
(archive/'README.md').write_text(text.replace('../../../..//','../../../../'))
print(archive)
