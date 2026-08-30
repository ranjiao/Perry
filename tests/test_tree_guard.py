"""`tests/tree_guard.py` — and the plant that shows it can actually fail.

A "the tree must not move" check is exactly the kind of guard that rots. It is
green on every honest run, which is every run, so nothing ever exercises the
branch that fails — and a guard whose failing branch is never taken is
indistinguishable from a guard that has been broken for a year. This project
has failed three rows in two days for shipping one.

So the load-bearing test here is not the unit coverage of `manifest` and
`compare` below it. It is `TestThePlantedWrite`, which copies this repository
to a scratch directory, drops a test module into the copy that writes into the
copy's own root, runs the **real** `bash tests/run` there, and requires that
the suite comes back red naming the two paths that moved. Its mutation half
neuters `tree_guard.compare` in a second copy and requires the same planted run
to come back GREEN — because a red that would have been red anyway proves
nothing about the guard.

The planting is into a COPY, never the live checkout: `work/reference/
review-constraints.md` says so, and the reason is that for the seconds the
plant exists, anything else running the suite sees a real, reproducible-looking
failure about nothing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tree_guard as TG

PERRY_HOME = Path(__file__).resolve().parent.parent

#: A module the runner will discover in the copy. It writes into the root it
#: finds — a `M` (an existing file changed) and a `+` (a file created), which
#: are two of the three verdicts `compare` can reach. `perry/BOARD.md` is the
#: file TASK-249's real defect moved.
PLANT = '''"""Planted by tests/test_tree_guard.py. Writes into its own root on
purpose — this module exists to be caught, and it only ever lives in a copy."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestAModuleThatWritesIntoTheLiveRoot(unittest.TestCase):
    def test_the_write_itself_passes(self):
        """It passes. That is the point: the module is GREEN and the suite
        must still come back red, because the tree moved."""
        with open(ROOT / "perry" / "BOARD.md", "a", encoding="utf-8") as fh:
            fh.write("\\n<!-- planted by TASK-249's guard test -->\\n")
        (ROOT / ".perry" / "task-249-planted.txt").write_text("planted\\n")
        self.assertTrue((ROOT / ".perry" / "task-249-planted.txt").exists())
'''

#: The control. Same shape, same runner path, writes only into a temp dir —
#: which is what every well-behaved module in this suite does. Without it, a
#: red planted run could mean "the guard works" or "`--only` is broken".
CONTROL = '''"""Planted by tests/test_tree_guard.py. Writes into a temp dir,
like every well-behaved module here. The suite must come back GREEN."""

import tempfile
import unittest
from pathlib import Path


class TestAModuleThatWritesWhereItShould(unittest.TestCase):
    def test_it_writes_into_a_temp_root(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "BOARD.md").write_text("a board in a temp root\\n")
            self.assertTrue((Path(d) / "BOARD.md").exists())
'''

PLANT_MODULE = "test_zz_task_249_planted_write.py"
CONTROL_MODULE = "test_zz_task_249_control.py"


def copy_repo(dest: Path) -> Path:
    """This repository, minus `.git` and the bytecode caches, in a scratch dir.

    `__pycache__` is excluded rather than copied: a stale `.pyc` beside a
    source file its mtime no longer matches is its own class of false result,
    and the copy has no reason to carry one.
    """
    shutil.copytree(PERRY_HOME, dest, symlinks=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                  "*.pyc", "*.pyo"))
    return dest


def run_suite(root: Path, module: str) -> subprocess.CompletedProcess:
    """`bash tests/run --only <module>` in `root` — the real runner.

    Not `tree_guard.py` called directly: what is under test is whether the
    SUITE fails, which is a property of `tests/run`'s wiring as much as of the
    guard. TASK-249's defect was in wiring, not in an algorithm.
    """
    return subprocess.run(
        ["bash", "tests/run", "--only", module.removesuffix(".py")],
        cwd=str(root), capture_output=True, text=True)


class TestThePlantedWrite(unittest.TestCase):
    """The guard fails the suite on a write to the live root — and would not
    fail it if the guard were gone."""

    def test_a_module_that_writes_into_the_root_turns_the_suite_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / PLANT_MODULE).write_text(PLANT)
            r = run_suite(root, PLANT_MODULE)
            out = r.stdout + r.stderr

            self.assertNotEqual(
                r.returncode, 0,
                "the planted module wrote into the root and the suite came "
                "back green — the guard is not wired into tests/run:\n" + out)
            self.assertIn("THE SUITE WROTE INTO THE TREE IT RAN IN", out)
            self.assertIn("M perry/BOARD.md", out,
                          "the guard failed the suite but did not name the "
                          "file that changed:\n" + out)
            self.assertIn("+ .perry/task-249-planted.txt", out,
                          "the guard failed the suite but did not name the "
                          "file that was created:\n" + out)
            # The module itself passed. If the suite were red because the
            # PLANT failed rather than because the tree moved, this test would
            # be measuring nothing.
            self.assertNotIn("✗ " + PLANT_MODULE, out,
                             "the planted module itself failed:\n" + out)

    def test_the_same_run_is_green_when_the_guard_is_neutered(self):
        """**The mutation.** One line of `tree_guard.py` — the comparison
        itself — is replaced with the empty answer, and the identical planted
        run must come back green. If it stays red, the red in the test above
        is coming from somewhere else and that test is vacuous.
        """
        anchor = "    lines = compare(before, manifest(root))"
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            guard = root / "tests" / "tree_guard.py"
            src = guard.read_text()
            self.assertEqual(
                src.count(anchor), 1,
                f"the mutation anchor is not unique in tree_guard.py: "
                f"{src.count(anchor)} occurrence(s) of {anchor!r} — resolve "
                f"it before trusting this test")
            guard.write_text(src.replace(
                anchor, "    lines = []  # MUTATION by test_tree_guard.py"))

            (root / "tests" / PLANT_MODULE).write_text(PLANT)
            r = run_suite(root, PLANT_MODULE)
            out = r.stdout + r.stderr

            self.assertEqual(
                r.returncode, 0,
                "with the guard neutered the planted run should be green — "
                "if it is red, something OTHER than the guard is failing it "
                "and the test above proves nothing:\n" + out)
            # And the write really did happen, so the green above is the
            # guard's absence and not the plant failing to fire.
            self.assertIn("planted by TASK-249's guard test",
                          (root / "perry" / "BOARD.md").read_text())

    def test_a_module_that_stays_in_a_temp_root_is_green(self):
        """The control. Same runner, same `--only` path, no write to the root
        — so a red here would mean the mechanism, not the plant."""
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            r = run_suite(root, CONTROL_MODULE)
            out = r.stdout + r.stderr
            self.assertEqual(r.returncode, 0,
                             "a well-behaved module turned the suite red:\n"
                             + out)
            self.assertIn("nothing under", out)


class TestTheManifest(unittest.TestCase):
    """What `manifest` records, and what it deliberately does not."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        (self.root / "a.txt").write_text("one\n")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "b.txt").write_text("two\n")

    def test_a_changed_file_is_M(self):
        before = TG.manifest(self.root)
        (self.root / "a.txt").write_text("ONE\n")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  M a.txt   (changed)"])

    def test_a_created_file_is_plus_and_a_removed_file_is_minus(self):
        before = TG.manifest(self.root)
        (self.root / "c.txt").write_text("three\n")
        (self.root / "sub" / "b.txt").unlink()
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  + c.txt   (created)",
                          "  - sub/b.txt   (removed)"])

    def test_a_file_rewritten_with_the_same_bytes_is_not_a_change(self):
        """Content, not mtime. A test that reads and rewrites a file
        unchanged has not moved the tree, and reporting it would train
        everyone to ignore this guard."""
        before = TG.manifest(self.root)
        (self.root / "a.txt").write_text("one\n")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)), [])

    def test_an_empty_directory_created_is_a_change(self):
        before = TG.manifest(self.root)
        (self.root / "fresh").mkdir()
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  + fresh   (created)"])

    def test_a_relinked_symlink_is_a_change_without_following_it(self):
        (self.root / "link").symlink_to("a.txt")
        before = TG.manifest(self.root)
        (self.root / "link").unlink()
        (self.root / "link").symlink_to("sub/b.txt")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  M link   (changed)"])

    def test_bytecode_and_caches_are_not_recorded(self):
        """Running the suite compiles the suite. If `__pycache__` counted, the
        guard would be red on every first run and switched off by the end of
        the week."""
        before = TG.manifest(self.root)
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "x.cpython-313.pyc").write_bytes(b"\x00")
        (self.root / "sub" / "d.pyc").write_bytes(b"\x00")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "index").write_bytes(b"\x00")
        self.assertEqual(TG.compare(before, TG.manifest(self.root)), [])

    def test_the_ignore_list_is_the_documented_one(self):
        """A guard is weakened by growing its ignore list, and that is the
        cheapest way to make a red run green. Any addition has to change this
        line, which is a place a reviewer looks."""
        self.assertEqual(
            set(TG.IGNORE_DIRS),
            {".git", "__pycache__", ".pytest_cache", ".mypy_cache",
             ".ruff_cache", "node_modules"})
        self.assertEqual(TG.IGNORE_SUFFIXES, (".pyc", ".pyo"))


class TestTheCLI(unittest.TestCase):
    """`snapshot` / `verify`, the two verbs `tests/run` actually calls."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "tree"
        self.root.mkdir()
        (self.root / "a.txt").write_text("one\n")
        self.store = Path(self.tmp.name) / "manifest.json"

    def cli(self, *argv) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PERRY_HOME / "tests" / "tree_guard.py"),
             *argv], capture_output=True, text=True)

    def test_verify_is_zero_on_an_unchanged_tree(self):
        self.assertEqual(
            self.cli("snapshot", str(self.root), str(self.store)).returncode, 0)
        r = self.cli("verify", str(self.root), str(self.store))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")

    def test_verify_is_one_and_names_the_path(self):
        self.cli("snapshot", str(self.root), str(self.store))
        (self.root / "a.txt").write_text("two\n")
        r = self.cli("verify", str(self.root), str(self.store))
        self.assertEqual(r.returncode, 1)
        self.assertIn("M a.txt", r.stderr)
        self.assertIn("perry-task", r.stderr,
                      "the failure should say where writes like this come "
                      "from, not just that one happened")

    def test_a_bad_invocation_is_two_not_a_traceback(self):
        r = self.cli("verify", str(self.root))
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
