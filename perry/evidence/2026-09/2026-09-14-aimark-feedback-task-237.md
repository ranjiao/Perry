# aiMark feedback on TASK-237, verified by the PMO

**Source:** `/Users/bytedance/proj/aimark/doc/perry-feedback-task-237.md`, aiMark's
reply to the 2026-09-14 update prompt. aiMark measured on `e1b171d2`.
**Verified:** the PMO reproduced every claim on `e1b171d2`, the same day, before
acting.

## What aiMark did

aiMark's production code went from 8 `BOARD.md` dependencies to 0:
- project detection uses `perry-state --section installed`;
- the board drawer renders `perry-tasks board`;
- the watch list swaps `BOARD.md` for the stores;
- a temporary shortfall defence covers asks and risks.

It reports 947 of 950 tests passing. The 3 reds are its own open decisions,
covered in § 4 below.

## Findings, each reproduced

| # | aiMark's claim | PMO measurement |
|---|---|---|
| 2.1 | `perry-tasks board` on a non-Perry directory exits 0 and prints an empty skeleton | exit 0, 2,172 B, first line `# Board — {{project name}}`, empty stderr |
| 2.2 | every read surface returns exit 0 and an empty, valid payload on a non-Perry directory, with no signal that the directory is not a project | exit 0 on `perry-task list --json`, `perry-task asks --all --json`, `perry-goals list --json`, `perry-decide list --json` and `perry-knowledge list --json`. None of their keys says "not a project"; `perry-state` alone reports `installed: false` |
| 2.2 | `schema/asks-list-contract.md § Exit codes` says exit 1 when the register cannot be read | the text says "`1` refused — the register could not be read". A directory with no register at all reads as empty at exit 0 |
| 2.3 | `installed` is true for a directory holding only `BOARD.md`, and `perry-state` carries no contract | `{"installed": true}` at exit 0. The payload's only version marker is `schema: 1`; there is no `contract` string and no `semantics[]` |
| 2.4 | `perry-asks/list` is the only published read payload without `state_root` | its keys are all, answered, asks, contract, count, open, project_root and semantics. list, goals, decide and knowledge all carry `state_root` |
| 2.4 | `list § risks` carries `source` | `{'open': 2, 'cleared': 2, 'source': 'table'}` with the file present |
| 2.5 | `board` prints the template's `{{…}}` placeholders | confirmed. This is D1 layout choice C1 |
| § 4 | `add` began requiring `--kr` / `--unlinked` with no contract version change | this is `TASK-396` (perry-task has no published write contract), which is already open. No new row |

## Decisions (user, 2026-09-14)

1. **Non-Perry directory: A.** Every published read payload gains an
   `installed` boolean. That is additive, a minor bump, and documented per
   contract. `perry-tasks board` refuses on a non-installed project with exit 1
   and a reason on stderr.
2. **`installed` criterion: A.** A project is installed when
   `.perry/config.jsonl` exists or any canonical store exists. `BOARD.md` alone
   no longer counts. The criterion is written into the contracts and changes
   with 3b.
3. **`board` placeholders: fill the project name and drop the instruction
   prose.** The title takes the project's name from a `.perry/config.jsonl`
   setting if one is declared, and the project directory's name otherwise.
   Measured: this repository's config store has no name setting (its keys are
   document_language, chat_language, repo_layout, state_root, pmo_repo_path,
   code_repo_path and last_updated), so the directory name is what prints. No
   config key is added; that would be a schema change. The template text
   written for a human filling the file in is not printed. This changes D1's
   choice C1.

All three are folded into TASK-237 3b (spec Amendment 2026-09-14 (4)), and no
row is opened.

**Already in flight:** § 2.4's two requests, a `semantics[]` entry on
`perry-task/list` and `perry-asks/list` announcing the store read, and
`state_root` on `perry-asks/list`. They were added to the running 3a dispatch
as an additive widening of its contract limit.
