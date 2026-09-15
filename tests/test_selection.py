"""`tests/selection.py` — DESIGN-021 § 5.2, one case per rule. TASK-448.

The selector decides which test modules a change runs, and every way it can be
wrong in the unsafe direction is a module that should have run and did not. So
each rule below has a case that goes red when the rule is removed or inverted,
and the widening rules — the ones that turn a narrow selection into the whole
suite — are checked with a change that a narrow rule would ALSO have matched,
so a selector that consults the narrow rules first cannot pass them.

The last two classes are about the live tree rather than the function:

* `TestTheLiveSuiteDeclares` is the guard § 5.2 item 5 asks for — the list of
  modules with no `COVERS` — and it is expected empty. It also refuses a
  prefix that names nothing in the repository, because a typo in a prefix is
  a module that is never selected by the path it meant.
* `TestTheRunEntry` runs the real `tests/run --tier affected --dry-run` in a
  throwaway git repository and asserts it selects, prints, and runs nothing.

Run: python3 -m unittest tests.test_selection
"""

from __future__ import annotations

COVERS = ("tests/selection.py", "tests/run")

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import selection as S

ROOT = pathlib.Path(__file__).resolve().parent.parent

DECLS = {
    "test_task.py": ("bin/perry-task",),
    "test_prose.py": ("SKILL.md", "reference/"),
    "test_everything.py": S.ALL,
    "test_undeclared.py": None,
}


def picked(changed, decls=DECLS):
    return S.select(changed, decls)


class TestWideningRules(unittest.TestCase):
    """Each rule selects the whole suite, and is checked before the narrow
    rules: every change below also touches `bin/perry-task`, which
    `test_task.py` covers, so a narrow match alone would not be the full set."""

    def assert_full(self, path, kind):
        sel = picked(["bin/perry-task", path])
        self.assertTrue(sel.full, f"{path} did not widen: {sel}")
        self.assertIn((kind, path), sel.widened)
        self.assertEqual(sorted(sel.modules), sorted(DECLS))

    def test_a_path_under_bin_lib_selects_the_full_suite(self):
        self.assert_full("bin/lib/__init__.py", S.BIN_LIB)

    def test_viewer_parsers_selects_the_full_suite(self):
        self.assert_full("viewer/parsers.py", S.PARSERS)

    def test_a_path_under_schema_selects_the_full_suite(self):
        self.assert_full("schema/task-list-contract.md", S.SCHEMA)

    def test_a_tests_helper_selects_the_full_suite(self):
        self.assert_full("tests/inproc.py", S.TESTS_HELPER)

    def test_a_tests_path_that_is_not_a_module_is_a_helper_at_any_depth(self):
        self.assert_full("tests/fixtures/sample-project/BOARD.md",
                         S.TESTS_HELPER)
        self.assert_full("tests/fixtures/test_like_a_module.py",
                         S.TESTS_HELPER)

    def test_a_path_no_covers_matches_selects_the_full_suite(self):
        self.assert_full("packs/software-ops/architecture.md", S.UNMATCHED)

    def test_all_does_not_count_as_matching_a_path(self):
        """If `ALL` matched every path, one `ALL` module would switch the
        unmatched rule off for the whole suite."""
        sel = picked(["packs/x.md"],
                     {"test_everything.py": S.ALL, "test_undeclared.py": None})
        self.assertTrue(sel.full)
        self.assertEqual(sel.widened, ((S.UNMATCHED, "packs/x.md"),))

    def test_a_prefix_matches_from_the_start_of_the_path_only(self):
        sel = picked(["work/bin/perry-task"])
        self.assertIn((S.UNMATCHED, "work/bin/perry-task"), sel.widened)


class TestNarrowRules(unittest.TestCase):

    def test_a_changed_test_module_selects_itself(self):
        sel = picked(["tests/test_prose.py"])
        self.assertFalse(sel.full, sel.widened)
        self.assertEqual(sel.modules["test_prose.py"],
                         "changed: tests/test_prose.py")
        self.assertNotIn("test_task.py", sel.modules)

    def test_a_covers_prefix_selects_its_module(self):
        sel = picked(["reference/glossary.md"])
        self.assertFalse(sel.full, sel.widened)
        self.assertEqual(sel.modules["test_prose.py"],
                         "covers reference/: reference/glossary.md")
        self.assertNotIn("test_task.py", sel.modules)

    def test_a_prefix_is_a_plain_string_prefix(self):
        """`bin/perry-task` also matches `bin/perry-tasks`: more, not less."""
        self.assertIn("test_task.py", picked(["bin/perry-tasks"]).modules)

    def test_covers_all_is_selected_on_every_change(self):
        sel = picked(["SKILL.md"])
        self.assertFalse(sel.full, sel.widened)
        self.assertEqual(sel.modules.get("test_everything.py"), "COVERS = ALL")

    def test_a_module_with_no_covers_is_always_selected(self):
        sel = picked(["SKILL.md"])
        self.assertFalse(sel.full, sel.widened)
        self.assertEqual(sel.modules.get("test_undeclared.py"), "no COVERS")

    def test_a_deleted_test_module_selects_nothing_and_does_not_widen(self):
        sel = picked(["tests/test_gone.py"])
        self.assertFalse(sel.full, sel.widened)
        self.assertEqual(sorted(sel.modules),
                         ["test_everything.py", "test_undeclared.py"])

    def test_nothing_changed_selects_only_all_and_undeclared(self):
        self.assertEqual(sorted(picked([]).modules),
                         ["test_everything.py", "test_undeclared.py"])


class TestDeclarations(unittest.TestCase):

    def test_a_tuple_of_prefixes(self):
        self.assertEqual(S.read_covers('COVERS = ("bin/perry-task", "SKILL.md")\n'),
                         ("bin/perry-task", "SKILL.md"))

    def test_all(self):
        self.assertIs(S.read_covers("from selection import ALL\nCOVERS = ALL\n"),
                      S.ALL)

    def test_absent(self):
        self.assertIsNone(S.read_covers("X = 1\n"))

    def test_read_from_source_without_importing_it(self):
        src = 'raise SystemExit("importing this module ends the process")\n' \
              'COVERS = ("viewer/tables.py",)\n'
        self.assertEqual(S.read_covers(src), ("viewer/tables.py",))

    def test_only_a_top_level_assignment_counts(self):
        self.assertIsNone(S.read_covers(
            "def f():\n    COVERS = ('bin/',)\n"))

    def test_anything_else_is_refused_rather_than_guessed(self):
        for src in ('COVERS = "bin/perry-task"\n', "COVERS = ()\n",
                    "COVERS = (1,)\n", 'COVERS = ("/bin/perry-task",)\n',
                    'COVERS = ("../x",)\n', "COVERS = EVERYTHING\n",
                    'COVERS = tuple(["bin/"])\n'):
            with self.subTest(src=src), self.assertRaises(S.DeclarationError):
                S.read_covers(src)


class TestShareAndOutput(unittest.TestCase):
    DURATIONS = {"test_task.py": 60.0, "test_prose.py": 30.0,
                 "test_everything.py": 10.0}          # test_undeclared unmeasured

    def lines(self, changed):
        sel = picked(changed)
        return S.dry_run_lines("B", "H", changed, sel, DECLS, self.DURATIONS)

    def test_the_share_counts_selected_module_seconds(self):
        sel = picked(["SKILL.md"])
        self.assertEqual(S.share(sel, DECLS, self.DURATIONS), (40.0, 100.0))

    def test_one_line_per_selected_module_with_its_rule(self):
        out = self.lines(["SKILL.md"])
        body = [l for l in out if l.startswith("  test_")]
        self.assertEqual(len(body), 3, out)
        self.assertTrue(any("test_prose.py" in l and "covers SKILL.md" in l
                            for l in body), out)

    def test_over_half_is_wide(self):
        out = self.lines(["bin/perry-task"])            # 60 + 10 of 100
        self.assertIn("this change is wide", out)

    def test_half_or_less_is_not_wide(self):
        out = self.lines(["SKILL.md"])                   # 30 + 10 of 100
        self.assertNotIn("this change is wide", out)
        self.assertIn("(40.0%)", out[-1])


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run(["git", "-c", "commit.gpgsign=false",
                           "-c", "core.hooksPath=/dev/null", *args],
                          cwd=cwd, env=env, capture_output=True, text=True,
                          check=True, timeout=60).stdout


class TestTheGitLayer(unittest.TestCase):

    def test_a_rename_reports_both_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q")
            (pathlib.Path(tmp) / "old.md").write_text("x\n" * 20)
            git(tmp, "add", "-A")
            git(tmp, "commit", "-qm", "one")
            git(tmp, "mv", "old.md", "new.md")
            git(tmp, "commit", "-qm", "two")
            self.assertEqual(
                sorted(S.changed_paths("HEAD~1", "HEAD", pathlib.Path(tmp))),
                ["new.md", "old.md"])

    def test_an_unknown_ref_is_a_git_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q")
            with self.assertRaises(S.GitError):
                S.changed_paths("no-such-ref", "HEAD", pathlib.Path(tmp))


class TestTheLiveSuiteDeclares(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.decls = S.declarations(ROOT)

    def test_no_module_is_without_covers(self):
        """§ 5.2 item 5's guard. The list may only shrink; today it is empty."""
        undeclared = [m for m, d in self.decls.items() if d is None]
        self.assertEqual(undeclared, [],
                         "these test modules declare no COVERS: "
                         + ", ".join(undeclared))

    def test_the_guard_saw_the_whole_suite(self):
        on_disk = sorted(p.name for p in (ROOT / "tests").glob("test_*.py"))
        self.assertEqual(sorted(self.decls), on_disk)
        self.assertGreater(len(on_disk), 100)

    def test_every_prefix_names_something_in_the_repository(self):
        tracked = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True, timeout=60)
        if tracked.returncode != 0:
            raise unittest.SkipTest("not a git checkout")
        paths = tracked.stdout.splitlines()
        dangling = sorted({(m, p) for m, d in self.decls.items()
                           if isinstance(d, tuple) for p in d
                           if not any(q.startswith(p) for q in paths)})
        self.assertEqual(dangling, [], "COVERS prefixes that name nothing")

    def test_every_covers_all_says_why_on_the_line_above(self):
        missing = []
        for m, d in self.decls.items():
            if d is not S.ALL:
                continue
            lines = (ROOT / "tests" / m).read_text().splitlines()
            i = next(i for i, l in enumerate(lines)
                     if l.startswith("COVERS = ALL"))
            if i == 0 or not lines[i - 1].startswith("#"):
                missing.append(m)
        self.assertEqual(missing, [])


PROBE = textwrap.dedent('''\
    import pathlib, unittest

    class TestProbe(unittest.TestCase):
        def test_writes_a_marker(self):
            pathlib.Path(__file__).with_name("RAN").write_text("ran")
    ''')


class TestTheRunEntry(unittest.TestCase):
    """`bash tests/run --tier affected --base <ref> --dry-run`, for real.

    A throwaway repository holding the real `tests/run`, `tests/selection.py`,
    `tests/tree_guard.py` and `tests/parallel`, and one probe module that
    writes a marker when it runs. Two commits, so `HEAD~1` exists.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = pathlib.Path(cls.tmp.name)
        tests = cls.root / "tests"
        tests.mkdir()
        for name in ("run", "selection.py", "tree_guard.py", "parallel",
                     "module_run.py", "durations.json"):
            shutil.copy(ROOT / "tests" / name, tests / name)
        (tests / "test_probe.py").write_text(
            'COVERS = ("README.md",)\n' + PROBE)
        (cls.root / "README.md").write_text("one\n")
        git(cls.root, "init", "-q")
        git(cls.root, "add", "-A")
        git(cls.root, "commit", "-qm", "one")
        (cls.root / "README.md").write_text("two\n")
        git(cls.root, "commit", "-qam", "two")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_it(self, *flags):
        marker = self.root / "tests" / "RAN"
        marker.unlink(missing_ok=True)
        env = {k: v for k, v in os.environ.items()
               if k not in ("PERRY_PROJECT", "PERRY_HOME")}
        proc = subprocess.run(["bash", "tests/run", *flags], cwd=self.root,
                              env=env, capture_output=True, text=True,
                              timeout=120)
        return proc, marker.exists()

    def test_the_dry_run_prints_the_selection_and_runs_nothing(self):
        proc, ran = self.run_it("--tier", "affected", "--base", "HEAD~1",
                                "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(ran, "the dry run ran a test module")
        self.assertIn("dry run, no test runs", proc.stdout)
        self.assertIn("test_probe.py  covers README.md: README.md", proc.stdout)
        self.assertIn("selected 1 of 1 modules", proc.stdout)

    def test_the_control_a_plain_run_does_run_the_probe(self):
        """Without this, a probe that never writes would pass the case above."""
        proc, ran = self.run_it("--only", "test_probe")
        self.assertTrue(ran, proc.stdout + proc.stderr)

    def test_a_tier_without_dry_run_is_refused_and_runs_nothing(self):
        for flags in (("--tier", "affected", "--base", "HEAD~1"),
                      ("--tier", "full"),
                      ("--tier", "affected", "--dry-run")):
            with self.subTest(flags=flags):
                proc, ran = self.run_it(*flags)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertFalse(ran)


if __name__ == "__main__":
    unittest.main()
