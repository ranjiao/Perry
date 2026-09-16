"""A copy of this repository's state root holding only what a reader reads.

**Why this exists (TASK-448 round 3, `USER-942`).** Several modules wanted "a
real, large project" to run a reader or a renderer against, and the cheapest
way to get one was `shutil.copytree(ROOT / "perry")`. That copies the stores —
and also `evidence/`, `journal/`, `design/` and `decisions/`, none of which the
readers in those modules touch. `DESIGN-021 § 5.2` then has to believe them:
a module whose fixture is the whole state root `COVERS` the whole state root,
so every merge that writes an evidence file selects it. `perry/evidence/`
changed in 46 of the 50 merges TASK-448 replayed, and those modules carry 67 of
the suite's module-seconds.

So the copy is made of named parts instead, and each caller says which parts it
needs. The stores are what a store reader reads; `documents=True` adds `OKR.md`
and `phase/`, which is what a payload reader additionally reads.

**This is not a smaller fixture, it is the same fixture minus what nothing
read.** A module that genuinely reads the rest — `perry-task list` resolving an
evidence cell against the tree, `perry-lint --claims` walking the claimed
paths, a check whose subject is this repository's own conformance — must keep
copying the whole thing, and several do. See `TASK-448-result.md`.

**`stores=` is the second round of exactly that, and the first round left the
work undone (TASK-448 cleanups).** Round 3 stopped copying `evidence/` and
friends but kept copying all seven stores everywhere, and TASK-448's own
mutation table records that `copy_state` copying NO stores left
`test_board_render` and `test_task_store` green. The reason is
`tests/printed_board.py`: those two modules put the board this repository's
stores PRINT on disk and then run `write --from-board`, so the live rows reach
them through the board and the copied `*.jsonl` files are opened by nothing, or
opened and discarded. Each caller now names the stores it reads, and a caller
that names none copies none:

    stores=True            every store in `STORES` (the default)
    stores=False           no store at all — the caller's rows arrive some
                           other way, or it is the no-store case on purpose
    stores=("tasks",)      exactly these, by store name

`skip=` is gone with the same argument. It named store files to leave OUT, and
its only two callers were the no-store cases, which say `stores=False` now; a
parameter no caller passes is the dead weight this module exists to remove.
"""

from __future__ import annotations

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The canonical stores, as `ARCHITECTURE.md § 4` lists them. `cadence.jsonl`
#: is included by name and simply absent here, which is the same thing a
#: project without one looks like.
STORES = ("tasks", "asks", "risks", "intake", "cadence", "linkage", "okr")

#: Project-root state. `events.jsonl` is derived and disposable (`§ 4`), so a
#: caller that does not read it can leave it out and get a copy that no
#: concurrent `perry-task` write can change under it.
ANCHOR = ("config.jsonl", "events.jsonl")


def copy_state(dest: pathlib.Path, *,
               stores: bool | tuple[str, ...] = True,
               documents: bool = False, events: bool = True,
               root: pathlib.Path = ROOT) -> pathlib.Path:
    """Copy this repository's state root into `dest`, by parts.

    `stores` is `True` for all of `STORES`, `False` for none, or a tuple of
    store names (`("tasks",)`) for exactly those. Returns the state directory
    inside `dest`.
    """
    wanted = _wanted_stores(stores)
    state_root = _state_root(root)
    state = dest / state_root
    state.mkdir(parents=True, exist_ok=True)
    (dest / ".perry").mkdir(parents=True, exist_ok=True)

    for name in ANCHOR:
        if name == "events.jsonl" and not events:
            continue
        src = root / ".perry" / name
        if src.exists():
            shutil.copy2(src, dest / ".perry" / name)

    for store in wanted:
        name = f"{store}.jsonl"
        src = root / state_root / name
        if src.exists():
            shutil.copy2(src, state / name)

    if documents:
        okr = root / state_root / "OKR.md"
        if okr.exists():
            shutil.copy2(okr, state / "OKR.md")
        phase = root / state_root / "phase"
        if phase.is_dir():
            shutil.copytree(phase, state / "phase", dirs_exist_ok=True)
    return state


def _wanted_stores(stores: bool | tuple[str, ...]) -> tuple[str, ...]:
    """`stores=` resolved to store names, refusing a name that is not one.

    A typo'd store name would otherwise copy nothing and look exactly like a
    caller that asked for nothing — the silent half of the defect this whole
    module is about.
    """
    if stores is True:
        return STORES
    if stores is False:
        return ()
    unknown = [s for s in stores if s not in STORES]
    if unknown:
        raise ValueError(
            f"copy_state(stores=...): {unknown} name no store. The stores are "
            f"{list(STORES)}, by store name and without the `.jsonl`.")
    return tuple(stores)


def _state_root(root: pathlib.Path) -> str:
    """The `state_root` setting, read from the config store rather than assumed.

    `.perry/config.jsonl` is the register (`ADR-019`); this repository sets it
    to `perry`, and a reader that hardcoded that would be a second declaration
    of it.
    """
    config = root / ".perry" / "config.jsonl"
    if not config.exists():
        return ""
    import json
    for line in config.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("key") == "state_root":
            return record.get("value", "")
    return ""
