# DESIGN-024 first-delivery evidence

This is author evidence, not independent V4 acceptance or a consumer migration.

- Base: `89219446bb50cb7faef2249708d48e9225b5422b`.
- Source candidate: `36d88be74f144c31757e5de32804e2fdb5c8392f` on `codex/design024-procedure-contracts`.
- Source change set: 24 Markdown files; no kernel, CLI, tools, process-template, governing architecture or safety-policy changes.
- Primary checkout records the approved design and task specs; implementation stays in its isolated worktree.
- Architecture checkpoints: not applicable, since this delivery edits Markdown procedures/document templates, not Python product code or governing targets. The retained fixture driver is audit scaffolding using existing CLI/helpers, not a shipped helper or method parser.

## Actual author checks

`bash tests/run` exited 0 on the source candidate's exact content: kernel 288 tests in 33.007s (one skipped), helpers 182 in 112.589s, both stages green. The kernel runner reported the live store unchanged at seq 1913. The source-content commit was made after these checks without another source edit.

`git diff --check` passed. `static-checks.json` records the 24-file scope, 58 local links with no missing file, and SHA256 equality for 74 protected files. Link existence/whitespace are structural checks, not semantic acceptance.

## Ten finite scenarios

Inputs, native command lines, JSON envelopes and actual helper refusals are under `author-traces/`. Its case index names the isolated source root/store and actual fixture IDs; traces preserve the original external paths. No database is copied into this evidence or a live store. External scratch retains the original fixture bytes/store.

| Case | Author observation | Scope/limit |
|---|---|---|
| S01 | Provider native task is done; consumer and package remain not_started; parent relations retained | Native model plus scope interpretation, not automatic package acceptance |
| S02 | Same local number appears in provider-list and integration-list with different native IDs; recheck query/seq unchanged and no creates repeated | Exact-match recheck demonstrated; no real interrupted consumer migration resumed |
| S03 | Four real native query pages at limit 1 share one seq; two explicit role sources and one missing role source retained | Role/source joins are Agent interpretation; no native alias or role index |
| S04 | Dispatch packet requesting cross-domain program edit without owner authority exits nonzero and reports blocked | Actual helper screening; it does not authenticate identity or supply an ACL |
| S05 | Domain document current/revision 2 coexists with native design_draft and exact outside-narrative-root attachment | Validity and approval remain separate; actual symlink safety refusal also retained |
| S06 | Actual custom source command succeeds; integration/device/human gates are not evidenced | Provider pass cannot close package or supply V5 |
| S07 | Criterion inputs retain candidate-A source pass, candidate-B failure and untested gates separately | Candidate-B behavioral failure is synthetic declared input, not a real engine experiment |
| S08 | Software fixture has an actual custom command; non-Git research fixture declares source inspection | No invented Perry runner or numeric measurement for research |
| S09 | A real Git fixture reports untracked file; retained before bytes and later bytes have different SHA256 | One finite source capture, not a full backup or live activation |
| S10 | Startup reports stage commit/step board interrupted adoption with actual partial native receipt | Author stopped: no native reads/writes or automatic resume after this gate |

The initial fixture orchestration incorrectly expected the interrupted card while its intentional escaped symlink still blocked startup. Preserve the original refusal and repair note; removing only that synthetic link exposed the interrupted card correctly. The initial repair assertion also encountered macOS `/var` versus `/private/var` spelling and was corrected by resolving both paths. Those driver mistakes are retained, not product failures or passing cases.

`fixture-driver.py` contains the corrected create-only replay driver. It accepts `--source <actual checkout>` and `--output <new external directory>`; output must not exist. It installs no dependencies, uses explicit test stores and retains the symlink refusal before removing only its fixture link. Independent review must run that corrected driver and record its actual result, not assume it passed because the author edited it.

## Verification boundary and known limitation

The dispatch helper still classifies some lane ownership by path segments. A legitimate domain path can be structurally refused. The new project contract documents this limitation and forbids bypass; no helper/ACL behavior change is claimed. Extending that helper is outside this first delivery.

No source test or synthetic trace proves consumer activation, real engine/LAN/device behavior, human acceptance, published release or integration into main. Release allocation and independent exact-merge verification belong to later integration, under the unchanged release rules. The source candidate is locally committed only.
