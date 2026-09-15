"""A copy of this repository with its current phase pinned. TASK-441.

`score-phase 003` (`7bffe58e`) cleared `perry/phase/CURRENT` to `(none)`, and
six modules went red with 13 tests. Each asserted against **this repository's
live current phase**: that a phase is current, that its register carries a
measured KR, an asserted `current`, or phase objectives in a payload. The window
between `score-phase` and `plan-phase` is a legitimate state of a project, so a
suite that is red inside it is testing the calendar and not the code.

This is `TASK-335`'s shape (`tests/test_contract_key_parity.py § the frozen
copy`), generalised to the one fact those six modules need:

- **`copy_of_perry`** copies the whole tree, leaving out `.git`, `.claude` and
  `__pycache__`. It is the whole tree and not the stores alone because
  `perry-task list` resolves evidence cells against files anywhere in the
  project, and `TASK-335` measured this copy equal to the checkout.
- **`pin_phase`** writes `phase/CURRENT` **inside the copy**. The value is
  `SCORED_PHASE`, the phase that was current when every one of these tests was
  written. A scored phase's `objective` and `kr` records stay in
  `perry/linkage.jsonl` for good, so this pin keeps working after phases 004,
  005 and later are planned and scored.
- **`refuse_the_checkout`** runs before the first write, and raises when the
  target is the checkout or a path inside it.
- **`pinned_copy`** builds one copy per test module and removes it when that
  module's tests end.

The tools under test are still the checkout's own `bin/`. Only the project
they are pointed at with `--root` is the copy.
"""

from __future__ import annotations

import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The phase every test in the six modules was written against. It was current
#: from 2026-08-28 until `score-phase 003` on 2026-09-15, and it carries the
#: one computed KR (`P003-O3-KR2`) and the asserted `current`s they read.
SCORED_PHASE = "003-storage-code"

#: What `score-phase` writes, and what a control pins to show the pin above is
#: load-bearing. It is written explicitly rather than read from the checkout,
#: so the control does not change meaning when `plan-phase 004` runs.
NO_PHASE = "(none)"

#: `.perry/config.jsonl` puts this project's state root at `perry/`.
CURRENT = pathlib.Path("perry") / "phase" / "CURRENT"

#: What the copy leaves out: git's data, `.claude/` (in the main checkout it
#: holds whole worktrees of other sessions), and bytecode.
NOT_STATE = shutil.ignore_patterns(".git", ".claude", "__pycache__")


def refuse_the_checkout(root: pathlib.Path) -> None:
    """Raise when `root` is this checkout or inside it.

    Runs before any write into a copy. A copy step that returned the checkout
    itself would otherwise rewrite Perry's own `phase/CURRENT`, and main has to
    stay between phases.
    """
    here, live = pathlib.Path(root).resolve(), ROOT.resolve()
    if here == live or live in here.parents:
        raise AssertionError(f"refusing to write {here}: it is Perry's "
                             f"checkout, not a copy of it")


def copy_of_perry(dest: pathlib.Path) -> pathlib.Path:
    shutil.copytree(ROOT, dest, ignore=NOT_STATE, symlinks=True)
    return dest


def current_phase(root: pathlib.Path) -> str:
    return (pathlib.Path(root) / CURRENT).read_text(encoding="utf-8").strip()


def pin_phase(root: pathlib.Path, phase: str) -> pathlib.Path:
    """Write `phase` into the copy's `phase/CURRENT`, after the guard.

    The pointer has to exist already, since a copy of this project has one.
    The phase document has to exist too, unless the pin is `NO_PHASE`. Either
    missing means the layout moved, and writing a new file would pin nothing.
    """
    refuse_the_checkout(root)
    pointer = pathlib.Path(root) / CURRENT
    if not pointer.is_file():
        raise AssertionError(f"{pointer} does not exist; the copy is not "
                             f"shaped like this project")
    if phase != NO_PHASE and not (pointer.parent / f"{phase}.md").is_file():
        raise AssertionError(f"no phase document {phase}.md under "
                             f"{pointer.parent}")
    pointer.write_text(phase + "\n", encoding="utf-8")
    return pathlib.Path(root)


_COPIES: dict[tuple[str, str], pathlib.Path] = {}


def pinned_copy(owner: str, phase: str = SCORED_PHASE) -> pathlib.Path:
    """One copy of the tree for `owner` (a test module's `__name__`), with
    `phase` current in it. Built on first use and removed when that module's
    tests end."""
    key = (owner, phase)
    if key not in _COPIES:
        tmp = tempfile.TemporaryDirectory(prefix="perry-pinned-phase-")
        root = copy_of_perry(pathlib.Path(tmp.name) / "perry")
        pin_phase(root, phase)
        _COPIES[key] = root

        def cleanup():
            _COPIES.pop(key, None)
            tmp.cleanup()

        unittest.addModuleCleanup(cleanup)
    return _COPIES[key]


class ThePinnedCopyGuards:
    """Mixed into one `TestCase` per module. The host sets `OWNER` to its
    module's `__name__`.

    - The copy the module reads is not the checkout.
    - The copy has the scored phase current in it.
    - The guard refuses the checkout, and a path inside it.

    The last case calls only the guard, never a writer, so a guard that
    stopped refusing fails here without writing anything.
    """

    OWNER = ""

    def pinned_root(self) -> pathlib.Path:
        """The copy the host module reads. A module that already builds its
        own copy (`test_contract_key_parity § frozen_copy`) overrides this."""
        return pinned_copy(self.OWNER)

    def test_the_copy_is_not_the_checkout(self):
        root = pathlib.Path(self.pinned_root()).resolve()
        self.assertNotEqual(ROOT.resolve(), root)
        self.assertNotIn(ROOT.resolve(), root.parents)

    def test_the_copy_reads_the_scored_phase(self):
        self.assertEqual(SCORED_PHASE, current_phase(self.pinned_root()))

    def test_the_pin_refuses_the_checkout(self):
        for target in (ROOT, ROOT / "perry", ROOT / "perry" / "phase"):
            with self.subTest(str(target)):
                with self.assertRaises(AssertionError):
                    refuse_the_checkout(target)
        refuse_the_checkout(self.pinned_root())
