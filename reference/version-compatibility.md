# Version compatibility — which Perry state a project holds, and what today's Perry does with it

For an agent opening a project that Perry may have touched. Perry has no version
number, and **today's Perry is not compatible with older Perry projects. That is
on purpose.** The user decided on 2026-09-14 not to keep the old shapes working.
Older projects are upgraded once, by an agent working in that project, using the
procedure below. This page tells you which shape you are looking at, what each
tool does with it today, and how to upgrade it.

Everything in the tables was measured on 2026-09-14 against Perry `main`
(`8abcec33`, write refusals re-measured at `7523f1fe`), on copies of real project files. Re-measure before relying on a
row, because Perry moves.

## The generations

A Perry project's state has gone through four shapes. The markers on disk tell
them apart.

| Generation | Since | What is on disk | The change |
|---|---|---|---|
| **G0 — markdown** | before 2026-08-19 | `.perry/config.md`, `BOARD.md`, `OKR.md`, `DECISIONS.md`, no `*.jsonl` | the original: every fact lives in a table in a markdown file |
| **G1 — stores beside markdown** | ADR-007, 2026-08-19 | G0 plus `tasks.jsonl`, `okr.jsonl`, `risks.jsonl`, `intake.jsonl`, `asks.jsonl`, `linkage.jsonl`; `BOARD.md` and `OKR.md` rendered from them | the store became canonical and the markdown a projection. `DECISIONS.md` was deleted 2026-08-30 (TASK-235), and the migrator was removed 2026-08-31 (ADR-011) |
| **G2 — config store** | ADR-019, 2026-09-08 | `.perry/config.jsonl` replaces `.perry/config.md`; `BOARD.md` still rendered | nothing reads `.perry/config.md` any more |
| **G3 — board-less** (current) | TASK-237, 2026-09-14 | `.perry/config.jsonl` and the stores (plus `cadence.jsonl`); **no `BOARD.md`** | the board is what `perry-tasks board` prints; `installed` needs `.perry/` |

## What today's Perry does with each shape

"Installed" is `schema/README.md § installed`. A directory is installed when
`.perry/config.jsonl` exists at its root, or when `.perry/` exists at its root
**and** a canonical store exists under its state root. Without
`.perry/config.jsonl`, the state root is the project root: a `State root: perry`
line in `.perry/config.md` is not read.

| Shape on disk | `installed` | Reads (`perry-task list` etc.) | `perry-tasks board` | A `perry-task` write |
|---|---|---|---|---|
| `.perry/config.md` + `perry/BOARD.md`, no stores (G0, `perry/` layout) | `false` | exit 0, empty payload | exit 1 | **refused**: exit 1, nothing written, and the message says to run `perry-config set` first |
| `.perry/config.md` + root `BOARD.md`, no stores (G0, root layout) | `false` | exit 0, empty | exit 1 | **refused**: exit 1, nothing written |
| `.perry/config.md` + stores under `perry/` + `BOARD.md` (G1, `perry/` layout) | `false`: the stores sit under a state root nothing declares | exit 0, empty | exit 1 | refused |
| `.perry/config.md` + stores at the project root (G1, root layout) | `true` | the stores' contents | exit 0 | succeeds |
| `.perry/config.jsonl` + stores + a `BOARD.md`, matching them or not (G2 with a held board) | `true` | the stores' contents only: a register with no store is empty, and the file is not read | exit 0, and the retired-board hint on stderr | succeeds, leaves the file's bytes unchanged, and names the file on stderr (not under `--json` or `--dry-run`). `perry-lint --root` warns `retired-board` |
| `.perry/config.jsonl` + stores, no `BOARD.md` (G3) | `true` | the stores' contents | exit 0 | succeeds, and creates no `BOARD.md` |

## Rules for an agent

1. **Read `installed` before anything else.** Every published read payload
   carries it (`perry-task list`, `perry-task asks`, `perry-task events`,
   `perry-goals list`, `perry-decide list`, `perry-knowledge list`), and so does
   `perry-state --section installed`. On `false`, the directory is not a Perry
   project **for today's tools**, even if it holds Perry files from an older
   generation.
2. **Do not write to a project that reads `installed: false`.** Upgrade it first,
   or ask the user.
3. **Never hand-create a store, and never hand-edit a `*.jsonl`.** Every write
   goes through a `bin/` command.
4. **A leftover `BOARD.md` in an installed project is a retired file**, not a
   second source of truth (TASK-262). No write and no read uses it: only the
   `--from-board` imports read it, to create the stores it has and the project
   does not. `perry-tasks board`, `perry-lint --root` and every successful
   write name it as one that can be deleted. Import any register it holds that
   has no store yet (the upgrade below), then `git rm` it; do not "fix" it by
   editing it, since an edit reaches nothing.
5. **Never write into another project from a Perry session.** Upgrade a project
   from inside that project. When measuring, copy its files into scratch space.

## A write where nothing is installed refuses

Since TASK-237 round 2 (merged at `7523f1fe`, 2026-09-14), every write through
`perry-task`, `perry-tasks`, `perry-okr` or `perry-goals` on a directory whose
`installed` is `false` exits 1 **before doing anything**. It writes no store, no
journal and no event, and `--dry-run` gets the same refusal. The message tells a
pre-ADR-019 project to run `perry-config set` first.

`perry-config set` / `track` are the one exception, because that is how a project
becomes installed (step 1 below).

Measured on a copy of aiMark's G0 files:
- `perry-task ask`, `ask --dry-run`, `add`, `next` and
  `perry-tasks write --from-board` all exit 1;
- zero new files appear;
- `installed` stays `false`;
- a `perry-config set "State root" perry` afterwards installs the project.

Before round 2, the same `ask` exited 0 and created empty stores at the project
root (V4 finding F1).

## Upgrading a project to G3

The upgrade was measured end to end on a copy of a real G0 project, aiMark's
`.perry/config.md` and `perry/BOARD.md`: 17 tasks, 3 asks, 1 cadence row and a
bullet-list `## Top risks`. **Do it on a clean git tree, in the project's own
repository, and commit before and after.** Count the board's rows per section
first, so there is a number to check against.

```bash
# 1. The config store. Copy each setting across from .perry/config.md with
#    `perry-config set <Label> <value>`. Labels: Document language, Chat language,
#    Repo layout, State root, PMO repo path, Code repo path, Last updated.
#    State root comes first: until it is set, the state root is the project root.
perry-config set --root . "State root" perry
perry-config set --root . "Document language" English
#    A `## Tracks` table in config.md becomes one `perry-config track <name> --mode …` per row.

# 2. The task store, from the board.
perry-tasks write --root . --from-board

# 3. Risks. A bullet-list `## Top risks` is converted AND stored by risk-migrate;
#    a table is imported with risks-write.
perry-task risk-migrate --root .              # bullets
perry-tasks risks-write --root . --from-board # a table

# 4. The other registers. A section the board does not have is refused with
#    "there is no `## Intake` section on this board": nothing to import, and not a failure.
perry-tasks asks-write    --root . --from-board
perry-tasks cadence-write --root . --from-board
perry-tasks intake-write  --root . --from-board

# 5. The OKR store, from OKR.md.
perry-okr write --root . --from-file
```

**6. Check the counts before deleting anything.**
- `perry-task list --all --limit 0 --json` lists as many tasks as the board's
  P0/P1/P2 rows. Measured: 17 tasks against 21 id-bearing rows, which were 17
  tasks, 3 `USER-` asks and 1 `CAD-` cadence row.
- `perry-task asks --all --json` returns the `User Input Queue` rows.
- `perry-state --json § cadence` shows the Cadence rows.
- `perry-goals list --json` shows the objectives and KRs. Measured: 3 objectives
  and 10 KRs from 13 OKR records.

**7. Retire the files nothing reads any more.** Delete the board file, which a
G3 project does not have, and `.perry/config.md`, which nobody reads since
ADR-019. `DECISIONS.md` has had no reader since TASK-235; `perry-decide list`
reads `decisions/`.

```bash
git rm perry/BOARD.md .perry/config.md
```

**8. Confirm.**
- `perry-state --section installed` gives `{"installed": true}`.
- `perry-tasks board` exits 0.
- `perry-lint --root .` exits 0 with 0 errors. Measured warnings after the
  upgrade:
  - `summary-missing`, one per imported task, because rows imported from a board
    carry no summary. Fill them with `perry-task summary <id> --summary "…"`.
  - `NS-01` on files under `.perry/` that Perry did not write. Measured:
    `.perry/adoption/…-dossier.md`, left by the adoption workflow ADR-011 removed.
    Move it out, as the warning says.
  - Anything the project's own `.perry/hook.md` already produced.

**Not covered by this procedure. Stop and ask the user.**
- A `phase/<NNN>-linkage.md` document, whose import ADR-019 deleted.
- A board whose tables do not import: the command refuses, and names the
  section and why.
- A project using the two-repo layout (`Repo layout: split`).

## What a consumer reads

For a program such as aiMark rather than an agent. Measured on `main`, 2026-09-14:

| Payload | Contract |
|---|---|
| `perry-task list --json` | `perry-task/list/2.4` |
| `perry-task asks --json` | `perry-asks/list/1.4` |
| `perry-task events --json` | `perry-events/list/1.4` |
| `perry-goals list --json` | `perry-goals/list/3.3` |
| `perry-decide list --json` | `perry-decide/list/2.2` |
| `perry-knowledge list --json` | `perry-knowledge/list/1.3` |

- Check the major version before reading anything else.
- Read each payload's `semantics[]` for the meaning changes behind a minor
  version.
- `perry-state` carries no contract version (only `schema: 1`), so treat it as
  unversioned.
- Each contract's rules are in `schema/*-contract.md`, and `schema/README.md`
  lists them.
