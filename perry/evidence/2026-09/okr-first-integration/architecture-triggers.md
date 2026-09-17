# Exact-candidate architecture trigger facts

Base: `d345fe4e0c3c61d890926a64339b2d119c845acc`
Head: `9ab2d9b08084a5617acc668edeac955e222df10a`
Authority: `work/reference/dispatch.md:464-511`; explicit integration brief requires this selection.
Evidence: `final.diff`, `final-name-status.txt`, `final-summary.txt`, `final-modes.txt`, `final-tree-base.txt`, `final-tree-head.txt`, and `architecture-facts.json`.

| # | Trigger | Result | Facts at exact base/head |
|---|---|---|---|
| 1 | Listed boundary paths | false | `viewer/parsers.py`, `bin/lib/`, `schema/`, root `SKILL.md`, and `goals/`, `work/`, `decide/` lane `SKILL.md` retain identical Git objects. Changed goals/work reference pages are not the listed lane SKILL paths. |
| 2 | New top-level directory | false | Both trees have the identical 17-directory set recorded in `architecture-facts.json`; every final diff entry is M. |
| 3 | New bin executable | false | The only changed bin path is existing `bin/perry-lint`, mode 100755 at both base and head. No executable is added, renamed in or gains executable mode. All 15 changed paths retain their modes; `final-summary.txt` is empty. |
| 4 | Contract-version change | false | Root architecture §5, the complete schema tree and shared bin/lib tree are byte-identical. `schema/task-list-contract.md` remains `perry-task/list/2.4`. The changed linter constant is an advisory Unicode-character length threshold, not a contract-version declaration. VERSION changes 0.1.5 at base to 0.1.9 at head through the four retained/new product deliveries; that product release increment is not a runtime API contract version change. |
| 5 | Root architecture edit | false | `ARCHITECTURE.md` retains blob `169dc2ff91d62b585de4fb47f6b384e70938688b` in both trees, including its confirmed component index and §5 declarations. |
| 6 | Module architecture edit | false | Both root §2 indexes identify `bin/ARCHITECTURE.md` as the component module document; it retains blob `46c791cc11610a3768084522dc6429a52d395035`. No component module architecture file is added, removed, renamed or changed. Changed `packs/software-ops/architecture.md` is the shipped architecture procedure, in the §2 packs/reference component; it is not an indexed component architecture document. |

Architecture trigger: none.

Component mapping from unchanged `ARCHITECTURE.md` §2:

- `bin/perry-lint` -> deterministic tools (`ARCHITECTURE.md:60-73`); indexed module document `bin/ARCHITECTURE.md` exists and is unchanged.
- `release/records.jsonl`, `VERSION`, `CHANGELOG.md` -> product releases (`ARCHITECTURE.md:75-81`); index points to procedure `release/README.md`, not a standalone component architecture document.
- `goals/reference/*`, `work/reference/*` -> lanes (`ARCHITECTURE.md:100-118`); no standalone module architecture document is indexed.
- `packs/software-ops/architecture.md`, `reference/*` -> packs/reference (`ARCHITECTURE.md:120-127`); no standalone module architecture document is indexed.
- `tests/*` -> tests (`ARCHITECTURE.md:129-132`); no standalone module architecture document is indexed.

The absence of standalone documents for some confirmed components does not turn trigger 6 into true or unknown: that trigger asks whether a component architecture file changed. No trigger selects a fresh architecture review for this candidate. If a later candidate does trigger review, PMO must resolve the review's required context and obtain an independent review; this record awards no architecture compliance verdict, V4, V5, human sign-off or task closure.
