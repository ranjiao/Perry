"""The four tiers of DESIGN-021 § 5.1, held by what each one actually runs.

TASK-449. `tests/selection.py` decides which modules a tier contains and
`tests/run` decides which steps it takes, so this module asserts both halves —
and asserts them as **traces of real runs**, not as readings of the source.

Three failures this module exists to catch, each of them a mutation the row was
required to prove red:

1. **`--tier affected` quietly running the full set.** The printed selection and
   the modules that ran would be different sets with nothing on screen saying
   so, which is this repository's oldest failure shape: a number large enough
   to look right. Held by `TestTheAffectedTierRunsTheSelection`.
2. **`--tier smoke` skipping the tree guard.** NN-5 is "every exit path", and a
   tier is a new exit path. Held by `TestEveryTierRunsInsideTheTreeGuard`.
3. **Bare `tests/run` diverging from `--tier full`.** The spec's first "must
   not": a caller that passes no `--tier` sees no difference. Held by
   `TestBareRunAndFullAreTheSameRun`, as a comparison of two traces — because
   "identical" is a claim about two runs, not about two lines of source.

**The tree is built, not archived.** `TestRunForwardsTheFlag` in
`test_slow_selector` unpacks `git archive HEAD`, which is right for a case about
one flag reaching one runner. This module runs `tests/run` a dozen times and
cares about which STEPS ran, so it builds a minimal tree whose every moving
part is a stub that records the argv it was handed: the trace is then the whole
truth about the run, and the module costs about a second.

Run: python3 tests/parallel test_tiers
"""

from __future__ import annotations

COVERS = ("tests/run", "tests/parallel", "tests/selection.py")

import json
import os
import pathlib
import re
import shutil
import subprocess
import textwrap
import unittest

import selection as S

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The stub runner. It is also IMPORTED — `tests/selection.py` reads the slow
#: tier's membership and the stopwatch out of `tests/parallel` rather than
#: re-declaring either — so it has to answer as a module as well as record as a
#: script.
PARALLEL_STUB = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, pathlib, sys

    HARNESS_SELF_TESTS = frozenset({"test_slowpoke.py"})

    def load_durations():
        return {"test_probe.py": 2.0, "test_other.py": 3.0,
                "test_slowpoke.py": 50.0}

    if __name__ == "__main__":
        with open("trace.txt", "a") as fh:
            fh.write("parallel " + json.dumps(sys.argv[1:]) + "\\n")
    ''')

GUARD_STUB = textwrap.dedent('''\
    #!/usr/bin/env python3
    import sys
    with open("trace.txt", "a") as fh:
        fh.write("guard " + sys.argv[1] + "\\n")
    print("  (stub guard)")
    ''')

LINT_STUB = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, sys
    with open("trace.txt", "a") as fh:
        fh.write("lint " + json.dumps(sys.argv[1:]) + "\\n")
    print("  (stub lint)")
    ''')

#: Enough of a module to be discovered and declared. None of them ever runs:
#: `tests/parallel` is a stub, which is the point — this module is about which
#: modules are ASKED for.
MODULE = 'COVERS = ("{covers}",)\nimport unittest\n'

#: Every script `tests/run` step 3 compiles and asks `--help`, and the four it
#: only syntax-checks with `bash -n`.
PY_SCRIPTS = ("bin/perry-state", "bin/perry-lint", "bin/perry-diagnose",
              "bin/perry-explain", "bin/perry-restore-check",
              "templates/knowledge-base/bin/kb-lint",
              "templates/ops/bin/deliverable-lint")
SH_SCRIPTS = ("bin/perry-detect-host", "bin/perry-update-check",
              "bin/perry-dispatch-limit", "bin/perry-codex-preflight")

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def git(root: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, timeout=60,
                   capture_output=True)


class Tree:
    """A minimal checkout holding the real `tests/run` and stubs for the rest."""

    def __init__(self, root: pathlib.Path):
        self.root = root
        (root / "tests").mkdir(parents=True)
        (root / "bin").mkdir()
        for name in ("run", "selection.py"):
            shutil.copy(ROOT / "tests" / name, root / "tests" / name)
        (root / "tests" / "parallel").write_text(PARALLEL_STUB)
        (root / "tests" / "tree_guard.py").write_text(GUARD_STUB)
        (root / "tests" / "test_probe.py").write_text(
            MODULE.format(covers="README.md"))
        (root / "tests" / "test_other.py").write_text(
            MODULE.format(covers="docs/"))
        (root / "tests" / "test_slowpoke.py").write_text(
            MODULE.format(covers="README.md"))
        for rel in PY_SCRIPTS:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(LINT_STUB)
        for rel in SH_SCRIPTS:
            (root / rel).write_text("#!/usr/bin/env bash\ntrue\n")
        (root / "README.md").write_text("one\n")
        (root / "docs").mkdir()
        (root / "docs" / "page.md").write_text("page\n")
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qm", "one")
        (root / "README.md").write_text("two\n")
        git(root, "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qam", "two")

    def run(self, *flags: str) -> dict:
        """`bash tests/run <flags>`, as a trace of what it did."""
        trace = self.root / "trace.txt"
        trace.unlink(missing_ok=True)
        env = {k: v for k, v in os.environ.items()
               if k not in ("PERRY_PROJECT", "PERRY_HOME")}
        proc = subprocess.run(["bash", "tests/run", *flags], cwd=self.root,
                              env=env, capture_output=True, text=True,
                              timeout=300)
        out = ANSI.sub("", proc.stdout)
        lines = trace.read_text().splitlines() if trace.exists() else []
        return {
            "rc": proc.returncode,
            "out": out,
            "err": ANSI.sub("", proc.stderr),
            # the step banners, which are what "step for step" means here
            "steps": [l.strip() for l in out.splitlines()
                      if re.match(r"^[0-9]\.", l.strip())
                      or l.strip().startswith("3, 4.")],
            "guard": [l for l in lines if l.startswith("guard ")],
            "lint": [json.loads(l[5:]) for l in lines if l.startswith("lint ")],
            "parallel": [json.loads(l[9:]) for l in lines
                         if l.startswith("parallel ")],
        }


class TreeCase(unittest.TestCase):
    tmp = None
    tree = None

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.tmp = tempfile.TemporaryDirectory()
        cls.tree = Tree(pathlib.Path(cls.tmp.name) / "t")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


# ── the module set each tier names ───────────────────────────────────────

DISK = ["test_a.py", "test_b.py", "test_c.py", "test_slowpoke.py"]
SLOW = {"test_slowpoke.py"}


def sel(*names) -> S.Selection:
    return S.Selection({n: "picked" for n in names}, ())


class TestTierModules(unittest.TestCase):
    """`tier_modules` is pure, so each tier's membership is one assertion."""

    def test_smoke_runs_no_module(self):
        self.assertEqual(S.tier_modules("smoke", DISK, SLOW), ((), ()))

    def test_full_is_the_disk_minus_the_slow_tier(self):
        run, held = S.tier_modules("full", DISK, SLOW)
        self.assertEqual(run, ("test_a.py", "test_b.py", "test_c.py"))
        self.assertEqual(held, ())

    def test_slow_is_the_whole_tree(self):
        run, _ = S.tier_modules("slow", DISK, SLOW)
        self.assertEqual(run, tuple(DISK))

    def test_affected_is_exactly_what_the_selector_picked(self):
        """Mutation 1's home. A runner that ignored the selection and ran the
        full set would return three modules here instead of one."""
        run, held = S.tier_modules("affected", DISK, SLOW, sel("test_b.py"))
        self.assertEqual(run, ("test_b.py",))
        self.assertEqual(held, ())

    def test_affected_never_exceeds_full(self):
        """A widened selection names every module on disk, the slow tier
        included. Running it as `affected` would make the cheap tier more
        expensive than the expensive one — 62.5 s of `test_tree_guard.py`
        inside an executor's iteration loop."""
        run, held = S.tier_modules("affected", DISK, SLOW, sel(*DISK))
        self.assertEqual(run, ("test_a.py", "test_b.py", "test_c.py"))
        self.assertEqual(held, ("test_slowpoke.py",))
        self.assertEqual(set(run), set(S.tier_modules("full", DISK, SLOW)[0]))

    def test_a_held_back_module_is_named_and_not_merely_dropped(self):
        """The drop is printed. A selection that names a module the run then
        skipped, silently, is the divergence this whole file guards."""
        p = S.Plan("affected", ("test_a.py",), sel("test_a.py", "test_slowpoke.py"),
                   ("test_slowpoke.py",), ())
        lines = S.plan_lines(p, decls={"test_a.py": ("x",)}, durations={},
                             base="B")
        self.assertTrue(any("held back — test_slowpoke.py" in l
                            for l in lines), lines)

    def test_a_selection_naming_a_deleted_module_selects_nothing_extra(self):
        run, _ = S.tier_modules("affected", DISK, SLOW, sel("test_gone.py"))
        self.assertEqual(run, ())

    def test_an_unknown_tier_is_refused(self):
        with self.assertRaises(S.TierError):
            S.tier_modules("quick", DISK, SLOW)
        with self.assertRaises(S.TierError):
            S.plan("quick")

    def test_affected_without_a_base_is_refused(self):
        with self.assertRaises(S.TierError):
            S.plan("affected")

    def test_the_four_names_are_the_four_names(self):
        self.assertEqual(S.TIERS, ("smoke", "affected", "full", "slow"))


class TestTheLiveTiersAgreeWithTheRunner(unittest.TestCase):
    """The live tree: `full` must be the set a bare `tests/parallel` runs.

    Stated against the runner's own two lines rather than against a copy of
    them, so a change to `HARNESS_SELF_TESTS` moves both together.
    """

    def test_full_is_what_a_bare_parallel_run_asks_for(self):
        on_disk = S.modules_on_disk(ROOT)
        slow = S.harness_self_tests(ROOT)
        run, _ = S.tier_modules("full", on_disk, slow)
        self.assertEqual(set(run), set(on_disk) - set(slow))
        self.assertTrue(slow, "the slow tier is empty — nothing is deferred")

    def test_slow_adds_back_exactly_the_harness_self_tests(self):
        on_disk = S.modules_on_disk(ROOT)
        slow = S.harness_self_tests(ROOT)
        full, _ = S.tier_modules("full", on_disk, slow)
        whole, _ = S.tier_modules("slow", on_disk, slow)
        self.assertEqual(set(whole) - set(full), set(slow))
        self.assertEqual(set(full) - set(whole), set())


# ── what each tier RUNS, as a trace ──────────────────────────────────────

class TestBareRunAndFullAreTheSameRun(TreeCase):
    """Mutation 3. The spec's first "must not", as a trace comparison."""

    def test_the_two_runs_are_step_for_step_identical(self):
        bare = self.tree.run()
        full = self.tree.run("--tier", "full")
        for key in ("rc", "steps", "guard", "lint", "parallel"):
            with self.subTest(key=key):
                self.assertEqual(bare[key], full[key])

    def test_and_that_run_reached_every_step(self):
        """The control: two runs that both did nothing would pass above."""
        bare = self.tree.run()
        self.assertEqual(bare["guard"], ["guard snapshot", "guard verify"])
        self.assertEqual(bare["parallel"], [[]])
        self.assertIn(["--templates"], bare["lint"])
        self.assertTrue(any(s.startswith("4. sample projects")
                            for s in bare["steps"]), bare["steps"])

    def test_slow_and_tier_slow_are_the_same_run(self):
        flag = self.tree.run("--slow")
        tier = self.tree.run("--tier", "slow")
        for key in ("rc", "steps", "guard", "lint", "parallel"):
            with self.subTest(key=key):
                self.assertEqual(flag[key], tier[key])
        self.assertEqual(flag["parallel"], [["--slow"]])


class TestTheSmokeTier(TreeCase):

    def test_it_runs_the_lint_and_the_scripts_and_no_module(self):
        got = self.tree.run("--tier", "smoke")
        self.assertEqual(got["rc"], 0, got["out"] + got["err"])
        self.assertIn(["--templates"], got["lint"])
        self.assertEqual(got["parallel"], [],
                         "the smoke tier ran a test module")
        self.assertTrue(any(s.startswith("3. bin/ scripts")
                            for s in got["steps"]), got["steps"])

    def test_it_does_not_lint_the_sample_projects(self):
        """Step 4 is not one of § 5.1's three, and it says so rather than
        leaving a run that looks whole and was not."""
        got = self.tree.run("--tier", "smoke")
        self.assertTrue(any(s.startswith("4. skipped")
                            for s in got["steps"]), got["steps"])
        self.assertNotIn(["--root", "tests/fixtures/sample-project"],
                         got["lint"])

    def test_its_green_says_it_is_not_a_green_suite(self):
        got = self.tree.run("--tier", "smoke")
        self.assertIn("NOT a green suite", got["out"])
        self.assertNotIn("all green", got["out"])


class TestTheAffectedTierRunsTheSelection(TreeCase):
    """Mutation 1. What `tests/run` hands the runner is the tier and the base,
    and the runner reads the set from `tests/selection.py` — asserted here at
    the boundary, and in `TestTierModules` as the function."""

    def test_the_base_reaches_the_runner(self):
        got = self.tree.run("--tier", "affected", "--base", "HEAD~1")
        self.assertEqual(got["rc"], 0, got["out"] + got["err"])
        self.assertEqual(got["parallel"],
                         [["--tier", "affected", "--base", "HEAD~1"]])

    def test_it_also_runs_the_smoke_checks(self):
        """§ 5.1: affected is the selection PLUS smoke, and a change that
        stopped a shipped script compiling would otherwise reach merge."""
        got = self.tree.run("--tier", "affected", "--base", "HEAD~1")
        self.assertIn(["--templates"], got["lint"])
        self.assertTrue(any(s.startswith("3. bin/ scripts")
                            for s in got["steps"]), got["steps"])

    def test_a_red_runner_is_a_red_tier(self):
        """A tier that swallowed the runner's exit status would report green
        over a red module — the one thing a shorter run may not do."""
        runner = self.tree.root / "tests" / "parallel"
        keep = runner.read_text()
        runner.write_text(keep.replace('fh.write("parallel "',
                                       'sys.exit(1) or fh.write("parallel "'))
        try:
            got = self.tree.run("--tier", "affected", "--base", "HEAD~1")
        finally:
            runner.write_text(keep)
        self.assertEqual(got["rc"], 1, got["out"])
        self.assertIn("failures above", got["out"])

    def test_its_green_says_it_is_not_a_green_suite(self):
        got = self.tree.run("--tier", "affected", "--base", "HEAD~1")
        self.assertIn("NOT a green suite", got["out"])


class TestEveryTierRunsInsideTheTreeGuard(TreeCase):
    """Mutation 2. NN-5 says every exit path, and a tier is a new exit path."""

    def test_each_tier_snapshots_and_verifies(self):
        for flags in (("--tier", "smoke"),
                      ("--tier", "affected", "--base", "HEAD~1"),
                      ("--tier", "full"),
                      ("--tier", "slow"),
                      ("--tier", "smoke", "--dry-run"),
                      ("--tier", "affected", "--base", "HEAD~1", "--dry-run"),
                      ("--tier", "full", "--dry-run"),
                      ("--lint",), ()):
            with self.subTest(flags=flags):
                got = self.tree.run(*flags)
                self.assertEqual(got["guard"],
                                 ["guard snapshot", "guard verify"],
                                 got["out"] + got["err"])

    def test_a_red_guard_reddens_a_smoke_run(self):
        """The control: the guard is not merely invoked, its verdict is read."""
        guard = self.tree.root / "tests" / "tree_guard.py"
        keep = guard.read_text()
        guard.write_text(keep + "import sys\nif sys.argv[1] == 'verify':"
                                " sys.exit(1)\n")
        try:
            got = self.tree.run("--tier", "smoke")
        finally:
            guard.write_text(keep)
        self.assertEqual(got["rc"], 1, got["out"])


class TestTheDryRunOfEveryTier(TreeCase):

    def test_no_tier_runs_a_module_under_dry_run(self):
        for flags in (("--tier", "smoke", "--dry-run"),
                      ("--tier", "affected", "--base", "HEAD~1", "--dry-run"),
                      ("--tier", "full", "--dry-run"),
                      ("--tier", "slow", "--dry-run")):
            with self.subTest(flags=flags):
                got = self.tree.run(*flags)
                self.assertEqual(got["rc"], 0, got["out"] + got["err"])
                self.assertEqual(got["parallel"], [])
                self.assertEqual(got["lint"], [])
                self.assertIn("no test ran", got["out"])

    def test_the_affected_dry_run_still_prints_the_selection(self):
        got = self.tree.run("--tier", "affected", "--base", "HEAD~1",
                            "--dry-run")
        self.assertIn("dry run, no test runs", got["out"])
        self.assertIn("test_probe.py", got["out"])

    def test_the_full_dry_run_counts_the_modules_it_would_run(self):
        got = self.tree.run("--tier", "full", "--dry-run")
        self.assertIn("tier full", got["out"])
        self.assertIn("2 of 3 modules", got["out"])


class TestTheRefusals(TreeCase):

    def test_an_unknown_tier_exits_two_before_anything_runs(self):
        got = self.tree.run("--tier", "quick")
        self.assertEqual(got["rc"], 2)
        self.assertEqual(got["guard"], [], "it started the run first")
        self.assertIn("unknown tier", got["err"])

    def test_affected_without_a_base_exits_two(self):
        got = self.tree.run("--tier", "affected")
        self.assertEqual(got["rc"], 2)
        self.assertEqual(got["parallel"], [])
        self.assertIn("--base", got["err"])

    def test_a_base_without_the_affected_tier_is_refused(self):
        """Accepted-and-dropped is a defect (DESIGN-016 goal 12): a caller who
        passed `--base` to `--tier full` believes the run was narrowed."""
        got = self.tree.run("--tier", "full", "--base", "HEAD~1")
        self.assertEqual(got["rc"], 2)
        self.assertIn("--base", got["err"])

    def test_an_unknown_argument_after_the_tier_is_refused(self):
        got = self.tree.run("--tier", "full", "--jobs", "4")
        self.assertEqual(got["rc"], 2)


# ── the runner's own tier entry ──────────────────────────────────────────

class TestTheParallelRunnerTakesTheSameNames(unittest.TestCase):
    """`tests/parallel --tier <name>`, with every module stubbed out.

    Loaded and driven the way `test_slow_selector` drives it, because that is
    the only way to ask "which modules would it have run" without running any.
    """

    @classmethod
    def setUpClass(cls):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader(
            "perry_tests_parallel_tiers", str(ROOT / "tests" / "parallel"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        cls.P = importlib.util.module_from_spec(spec)
        loader.exec_module(cls.P)

    def _ask(self, argv, changed=None):
        """(rc, modules asked for). `changed` stands in for the git diff."""
        import contextlib
        import io
        import sys
        import tempfile
        P = self.P
        asked: list[str] = []

        def stub(name: str) -> dict:
            asked.append(name)
            return {"mod": name, "rc": 0, "ran": 1, "sec": 0.01,
                    "err": "OK\n", "ids": [(f"{name[:-3]}.C.t", "ok")]}

        old = (P.run_module, sys.argv, P.DURATIONS, P.selection.changed_paths)
        P.run_module = stub
        sys.argv = ["parallel", *argv]
        if changed is not None:
            P.selection.changed_paths = lambda *a, **k: list(changed)
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            P.DURATIONS = pathlib.Path(td) / "durations.json"
            try:
                with contextlib.redirect_stdout(buf), \
                        contextlib.redirect_stderr(buf):
                    rc = P.main()
            finally:
                (P.run_module, sys.argv, P.DURATIONS,
                 P.selection.changed_paths) = old
        return rc, sorted(asked), buf.getvalue()

    def _on_disk(self):
        return {p.name for p in (ROOT / "tests").glob("test_*.py")}

    def test_tier_full_asks_for_what_a_bare_run_asks_for(self):
        rc, asked, _ = self._ask(["--tier", "full"])
        self.assertEqual(rc, 0)
        self.assertEqual(set(asked),
                         self._on_disk() - self.P.HARNESS_SELF_TESTS)

    def test_tier_slow_asks_for_the_whole_tree(self):
        rc, asked, _ = self._ask(["--tier", "slow"])
        self.assertEqual(rc, 0)
        self.assertEqual(set(asked), self._on_disk())

    def test_tier_affected_asks_for_the_selection_and_not_the_tree(self):
        """Mutation 1 at the runner: a narrow change must ask for a narrow
        set. `tests/selection.py` is the only reader of the declarations."""
        rc, asked, out = self._ask(
            ["--tier", "affected", "--base", "X"],
            changed=["tests/test_tiers.py"])
        self.assertEqual(rc, 0, out)
        self.assertIn("test_tiers.py", asked)
        # Not an equality: a handful of other modules declare a `tests/test_`
        # prefix and are selected by the same path, which is the selector
        # erring toward running more and is not this case's business. What it
        # is about is the order of magnitude — a set, not the tree.
        self.assertLess(len(asked), len(self._on_disk()) // 4,
                        f"{len(asked)} of {len(self._on_disk())} modules")

    def test_a_widened_change_asks_for_the_full_tier_and_no_more(self):
        rc, asked, out = self._ask(
            ["--tier", "affected", "--base", "X"],
            changed=["viewer/parsers.py"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(set(asked),
                         self._on_disk() - self.P.HARNESS_SELF_TESTS)

    def test_it_prints_what_it_selected_before_it_runs_it(self):
        _, _, out = self._ask(["--tier", "affected", "--base", "X"],
                              changed=["tests/test_tiers.py"])
        self.assertIn("tier affected", out)
        self.assertIn("test_tiers.py", out)
        self.assertIn("NOT a green suite", out)

    def test_smoke_is_refused_rather_than_answered_with_a_green(self):
        """`0 modules · 0 tests · ✓ all green` is a green from a run that
        verified nothing, which is the one answer this runner may not give."""
        rc, asked, out = self._ask(["--tier", "smoke"])
        self.assertEqual(rc, 2)
        self.assertEqual(asked, [])
        self.assertIn("tests/run --tier smoke", out)

    def test_a_tier_refuses_to_combine_with_the_flags_that_also_select(self):
        for argv in (["--tier", "full", "--slow"],
                     ["--tier", "full", "--record"],
                     ["--tier", "full", "test_tiers"]):
            with self.subTest(argv=argv):
                rc, asked, _ = self._ask(argv)
                self.assertEqual(rc, 2)
                self.assertEqual(asked, [])

    def test_a_base_without_a_tier_is_refused(self):
        rc, asked, _ = self._ask(["--base", "X"])
        self.assertEqual(rc, 2)
        self.assertEqual(asked, [])

    def test_affected_without_a_base_is_refused(self):
        rc, asked, _ = self._ask(["--tier", "affected"])
        self.assertEqual(rc, 2)
        self.assertEqual(asked, [])


if __name__ == "__main__":
    unittest.main()
