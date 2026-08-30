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

**Three things here exist because a V4 reviewer defeated the first version.**
`test_all_three_ignore_lists_are_the_documented_ones` — the first version
pinned two of the three lists, and blinding `IGNORE_NAMES` to `events.jsonl`
and `intake.jsonl` left all thirteen tests green.
`test_the_four_files_of_this_row_are_never_invisible` pins the same thing by
consequence rather than by name, so a fourth list invented tomorrow is caught
too. And `TestTheEnvironmentTheGuardCanSee` covers the vector the tree
comparison structurally cannot see: `$PERRY_PROJECT` aimed at a second
checkout, where all four files moved over there while step 0 truthfully
reported this tree unmoved.

The planting is into a COPY, never the live checkout: `work/reference/
review-constraints.md` says so, and the reason is that for the seconds the
plant exists, anything else running the suite sees a real, reproducible-looking
failure about nothing.
"""

from __future__ import annotations

import os
import re
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


def run_suite(root: Path, module: str,
              perry_project: str | None = None) -> subprocess.CompletedProcess:
    """`bash tests/run --only <module>` in `root` — the real runner.

    Not `tree_guard.py` called directly: what is under test is whether the
    SUITE fails, which is a property of `tests/run`'s wiring as much as of the
    guard. TASK-249's defect was in wiring, not in an algorithm.

    `PERRY_PROJECT` is stripped unless a test asks for it, so that an ambient
    one in the outer runner's environment cannot decide the answer here.
    """
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    if perry_project is not None:
        env["PERRY_PROJECT"] = perry_project
    return subprocess.run(
        ["bash", "tests/run", "--only", module.removesuffix(".py")],
        cwd=str(root), capture_output=True, text=True, env=env)


class TestTheEnvironmentTheGuardCanSee(unittest.TestCase):
    """**The fourth defeat vector, and it was live on this machine.**

    The guard hashes `$ROOT` and only `$ROOT`. `perry-task` resolves its
    project root from `$PERRY_PROJECT` *before* the cwd — so an agent running
    the suite in a worktree with `$PERRY_PROJECT` exported at the main checkout
    sends every un-rooted write into that other tree, and step 0 truthfully
    reports THIS one unmoved. A reviewer demonstrated it: all four files moved
    in a second checkout while step 0 printed `✓ nothing under … moved`.

    `tests/run` refuses to start in that environment. It does not silently
    re-point the variable — exporting `PERRY_PROJECT="$ROOT"` was tried first
    and reddens nine tests in `test_config_store_readers` that need it ABSENT.
    """

    def test_a_foreign_perry_project_refuses_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            victim = Path(tmp) / "victim"
            victim.mkdir()
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            r = run_suite(root, CONTROL_MODULE, perry_project=str(victim))
            out = r.stdout + r.stderr

            self.assertEqual(r.returncode, 2,
                             "the suite ran with PERRY_PROJECT aimed at "
                             "another tree:\n" + out)
            self.assertIn("refusing to run", out)
            self.assertIn(str(victim), out,
                          "the refusal must name the directory it is "
                          "refusing:\n" + out)
            self.assertNotIn("schema drift guard", out,
                             "the refusal has to come BEFORE step 1 — after "
                             "it, tests have already run:\n" + out)

    def test_perry_project_equal_to_the_root_is_allowed(self):
        """The refusal must not be satisfied by refusing everything. Pointed
        at the tree the guard watches, the variable is harmless — that is the
        state `cd "$ROOT"` already produces — and the run proceeds.

        Note what this passes: `root.resolve()`, which is the ONE spelling
        that cannot trip a raw string comparison against `pwd -P`. It is kept
        as the plain case; the test below is the one that exercises the
        spellings a reviewer found refused.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            r = run_suite(root, CONTROL_MODULE,
                          perry_project=str(root.resolve()))
            out = r.stdout + r.stderr
            self.assertEqual(r.returncode, 0, out)
            self.assertIn("nothing under", out)

    def test_other_spellings_of_this_root_are_this_root(self):
        """**The test above was built so that it could not observe the bug.**

        `tests/run` computed `$ROOT` with `pwd -P` and compared
        `$PERRY_PROJECT` to it as a raw string, while `bin/perry-task` does
        `Path(...).resolve()`. Two environments that name this very tree were
        therefore refused, measured on `8dfd25e`: a symlink alias of the root,
        and the root with a trailing slash. Both would have written INSIDE the
        tree step 0 hashes — a false refusal in a guard whose argument for
        refusing is that it costs nothing — and the test above could not see
        either, because `root.resolve()` is exactly the spelling that survives
        a raw comparison.

        So: each accepted spelling asserted accepted, and — in the same test,
        because "accept everything" is the way a resolution fix goes wrong —
        a genuinely foreign root and a foreign root reached through a symlink
        asserted still refused.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_repo(Path(tmp) / "repo")
            (root / "tests" / CONTROL_MODULE).write_text(CONTROL)
            alias = Path(tmp) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            foreign = Path(tmp) / "victim"
            foreign.mkdir()
            foreign_alias = Path(tmp) / "victim-alias"
            foreign_alias.symlink_to(foreign, target_is_directory=True)

            for label, value in (("a symlink alias of the root", str(alias)),
                                 ("the root with a trailing slash",
                                  str(root) + "/"),
                                 ("the unresolved root", str(root))):
                with self.subTest(spelling=label):
                    r = run_suite(root, CONTROL_MODULE, perry_project=value)
                    out = r.stdout + r.stderr
                    self.assertEqual(
                        r.returncode, 0,
                        f"{label} names the tree the guard watches and every "
                        f"un-rooted write would land inside it, and the suite "
                        f"refused to run:\n{out}")
                    self.assertIn("nothing under", out)

            for label, value in (("a foreign root", str(foreign)),
                                 ("a foreign root through a symlink",
                                  str(foreign_alias)),
                                 ("a root that does not exist",
                                  str(Path(tmp) / "nowhere"))):
                with self.subTest(spelling=label):
                    r = run_suite(root, CONTROL_MODULE, perry_project=value)
                    out = r.stdout + r.stderr
                    self.assertEqual(
                        r.returncode, 2,
                        f"resolving the comparison must not turn it into "
                        f"accept-everything: {label} was allowed to run:\n"
                        f"{out}")
                    self.assertIn("refusing to run", out)


class TestTheDocstringSaysWhichMechanismShipped(unittest.TestCase):
    """**A narrow pin, and narrow on purpose.**

    "the docstring matches the code" is not mechanically checkable, and a test
    claiming to check it would be the decoration this row keeps finding. This
    checks exactly one proposition, and it is the one that went wrong.

    `tests/run` can close the ambient `$PERRY_PROJECT` case in one of two
    mutually exclusive ways:

        RE-AIM   `export PERRY_PROJECT="$ROOT"`, so that every un-rooted write
                 lands in the tree the guard watches; or
        REFUSE   print and `exit 2` before step 1.

    Round 2 of the V4 review found `tests/run` REFUSING while `tree_guard.py`'s
    "What it does NOT catch, said plainly" list still described the RE-AIM —
    tried, and rejected for reddening nine tests — as the thing that shipped.
    A reader consulting the one list whose job is to say what is uncovered was
    told a mechanism was in place that was not.

    So: read which of the two `tests/run` implements, require exactly one, and
    require the bullet that describes it to name that one and not the other.
    It fails in both directions — rewriting the bullet back to the RE-AIM is
    red, and switching `tests/run` to re-aim without touching the bullet is
    red too.

    **What it does not check:** every other sentence in either file, and
    whether the description is any good. One class of rot, caught cheaply.
    """

    BULLET = "- **A write to a DIFFERENT checkout.**"

    #: (name, does `tests/run` implement it, word the bullet must use, word
    #: the bullet must then NOT use). The two words are each other's forbidden
    #: word, which is what makes the pair mutually exclusive in prose too.
    def _implemented(self, run_src):
        found = []
        # anchored at a line that is not a comment: `tests/run` DISCUSSES
        # exporting in a comment block, and discussing is not shipping.
        if re.search(r"^[^#\n]*\bexport[ \t]+PERRY_PROJECT=", run_src, re.M):
            found.append("re-aim")
        if "refusing to run: PERRY_PROJECT" in run_src:
            found.append("refuse")
        return found

    def setUp(self):
        self.run_src = (PERRY_HOME / "tests" / "run").read_text()
        doc = TG.__doc__ or ""
        self.assertEqual(
            doc.count(self.BULLET), 1,
            f"the bullet this test reads is not uniquely identifiable in "
            f"tree_guard.py's docstring ({doc.count(self.BULLET)} "
            f"occurrence(s) of {self.BULLET!r}) — fix that before trusting "
            f"any verdict here")
        start = doc.index(self.BULLET)
        self.bullet = doc[start:doc.index("\n- **", start + 1)]

    def test_tests_run_implements_exactly_one_of_the_two_mechanisms(self):
        found = self._implemented(self.run_src)
        self.assertEqual(
            len(found), 1,
            f"tests/run implements {found or 'neither'} of the two ways to "
            f"close the ambient PERRY_PROJECT case; the docstring can only "
            f"describe one of them, so this test cannot say which is right "
            f"until the source does")

    def test_the_bullet_names_the_mechanism_that_shipped(self):
        shipped = self._implemented(self.run_src)[0]
        says, must_not = {"refuse": ("refuses", "export"),
                          "re-aim": ("export", "refuses")}[shipped]
        low = self.bullet.lower()
        self.assertIn(
            says, low,
            f"tests/run {shipped}s, and tree_guard.py's '{self.BULLET}' "
            f"bullet never says so:\n\n{self.bullet}")
        self.assertNotIn(
            must_not, low,
            f"tests/run {shipped}s, and the bullet still describes the other "
            f"mechanism — the one that was tried and withdrawn — as the thing "
            f"that ships:\n\n{self.bullet}")


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

    def test_all_three_ignore_lists_are_the_documented_ones(self):
        """A guard is weakened by growing its ignore list, and that is the
        cheapest way to make a red run green.

        **There are THREE lists and the first version of this test pinned
        two.** A V4 reviewer set `IGNORE_NAMES = {".DS_Store",
        "events.jsonl", "intake.jsonl"}` — blinding the guard to two of the
        four files this whole row is about — and all thirteen tests stayed
        green. Naming two of three is how a pin becomes decoration.

        `.claude` and `.gstack` joined `IGNORE_DIRS` deliberately and this
        assertion is what made that deliberate: both are created by the agent
        harness this project is developed under, from outside the suite and in
        the middle of a run, and neither has a tracked file. The rule they
        satisfy — *this checkout actually produces it, and no test may
        legitimately write it* — is stated once in `tree_guard.py`'s docstring
        and is the same rule that keeps `.pytest_cache` and friends OUT.
        """
        self.assertEqual(set(TG.IGNORE_DIRS),
                         {".git", "__pycache__", ".claude", ".gstack"})
        self.assertEqual(TG.IGNORE_SUFFIXES, (".pyc", ".pyo"))
        self.assertEqual(set(TG.IGNORE_NAMES), {".DS_Store"})

    def test_the_four_files_of_this_row_are_never_invisible(self):
        """The pin above catches a list that GREW, by name. This catches the
        same attack by CONSEQUENCE, and it does not care which of the three
        lists was used — or whether a fourth is invented.

        `perry-task intake-sweep` writes exactly these four. If the manifest
        cannot see a change to one of them, the guard cannot fail on the thing
        it was built to fail on, whatever the mechanism.
        """
        four = ["\u002eperry/events.jsonl", "perry/BOARD.md",
                "perry/intake.jsonl", "perry/journal/2026-08/2026-08-30.md"]
        for rel in four:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text("before\n")
        before = TG.manifest(self.root)
        for rel in four:
            (self.root / rel).write_text("after\n")
        moved = {l.split()[1] for l in TG.compare(before, TG.manifest(self.root))}
        self.assertEqual(moved, set(four),
                         "the manifest is blind to one of the four files "
                         "TASK-249's sweep writes")

    def test_a_permission_change_is_a_change(self):
        """`chmod +x` on a shipped script changes what the tree is without
        changing a byte of it, and what this repository ships is executable.
        How many is not stated here — see the test below."""
        import os as _os
        before = TG.manifest(self.root)
        _os.chmod(self.root / "a.txt", 0o755)
        self.assertEqual(TG.compare(before, TG.manifest(self.root)),
                         ["  M a.txt   (changed)"])

    def test_the_executables_this_repository_ships_carry_their_mode(self):
        """The set is DERIVED from the tree, and no count is written down.

        This docstring and `tree_guard.manifest`'s both said the repository
        ships **eleven** executables. `git ls-tree -r HEAD | awk '$1=="100755"'
        | wc -l` says 24, 18 of them under `bin/`; `find . -type f -perm -u+x
        -not -path './.git/*' | wc -l` agrees. A number in a comment is a claim
        nothing checks, and replacing 11 with 24 would be the same defect one
        value later — so this asserts the SHAPE of the set instead and lets the
        size be whatever it is on the day.
        """
        m = TG.manifest(PERRY_HOME)
        execs = {rel for rel, tok in m.items()
                 if tok.startswith("f:") and int(tok.split(":")[1], 8) & 0o111}
        self.assertTrue(execs, "the manifest recorded no executable at all")
        # The bit the manifest reports is the bit on disk — otherwise this
        # test would be reading its own answer back.
        for rel in sorted(execs):
            self.assertTrue(os.access(PERRY_HOME / rel, os.X_OK),
                            f"manifest says {rel} is executable; the "
                            f"filesystem disagrees")
        # Every shipped `bin/perry-*` is one. A stripped bit there is a
        # broken install, which is exactly why the mode is in the token.
        shipped = {rel for rel, tok in m.items()
                   if rel.startswith("bin/perry-") and tok.startswith("f:")}
        self.assertTrue(shipped, "no bin/perry-* files found at all")
        self.assertEqual(
            shipped - execs, set(),
            "shipped bin/ scripts carrying no executable bit")
        # And the ones outside `bin/` that the manifest docstring describes.
        for rel in ("setup", "tests/run", "tests/parallel",
                    "templates/knowledge-base/bin/kb-lint",
                    "templates/ops/bin/deliverable-lint"):
            self.assertIn(rel, execs,
                          f"{rel} is described as a shipped executable and "
                          f"the manifest does not see its bit")


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
