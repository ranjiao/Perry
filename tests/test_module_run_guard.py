"""The guard that makes a module which never ran say so. TASK-430.

Every assertion here is made against **real `unittest` output captured from a
real subprocess**, never against a hand-written string. A guard verified
against a fixture of its author's idea of the output is a guard that agrees
with the author; the shape being detected is emitted by the standard library
and the standard library is what produces it here.

The two halves that matter are `TestGuardFires` and `TestGuardDoesNotFire`,
and the second is the more important one. **Anti-vacuity is the whole of this
row.** A guard that refuses every `Ran 1 test` would catch the defect and also
condemn the eleven modules in this suite that legitimately hold exactly one
test — and it would look identical on a green run. So the placeholder shape is
distinguished from a genuine single test, and both directions are asserted.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import concurrent.futures as cf
import ast
import importlib.machinery
import importlib.util
import pathlib
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest

import module_run

PERRY_HOME = pathlib.Path(__file__).resolve().parent.parent
TESTS = PERRY_HOME / "tests"
RUNNER = TESTS / "parallel"


def load_runner():
    """Import `tests/parallel`, which has no `.py` extension on purpose."""
    loader = importlib.machinery.SourceFileLoader("perry_tests_parallel_g",
                                                  str(RUNNER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def run_unittest(cwd: pathlib.Path, args: list[str]) -> subprocess.CompletedProcess:
    """`python3 -m unittest <args>` in `cwd`, output captured."""
    return subprocess.run([sys.executable, "-m", "unittest", *args],
                          capture_output=True, text=True, cwd=cwd, timeout=180)


def scratch_suite(tmp: str, body: str, name: str = "test_probe") -> pathlib.Path:
    """A throwaway `tests/`-shaped tree holding one module. Never in the repo.

    The suite's step 0 tree guard hashes the checkout, so a test that plants a
    module into `tests/` to see what happens would fail the whole run for
    doing it. Everything here is built under a temp dir instead.
    """
    root = pathlib.Path(tmp)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    p = root / "tests" / f"{name}.py"
    p.write_text(textwrap.dedent(body))
    return p


#: A module that imports a sibling by bare name — the exact shape 58 modules in
#: this repository have — plus the sibling it needs. Run via `discover` the
#: import resolves; run via `-m unittest tests.<name>` it does not.
SIBLING_HELPER = """
    VALUE = 7
"""
IMPORTS_A_SIBLING = """
    import unittest

    from probe_helper import VALUE


    class TestUsesSibling(unittest.TestCase):
        def test_one(self):
            self.assertEqual(VALUE, 7)

        def test_two(self):
            self.assertEqual(VALUE + 1, 8)

        def test_three(self):
            self.assertEqual(VALUE * 2, 14)
"""

#: A module with exactly ONE test that really runs and really passes. This is
#: the case the guard may not condemn: it also reports `Ran 1 test`.
EXACTLY_ONE_REAL_TEST = """
    import unittest


    class TestJustTheOne(unittest.TestCase):
        def test_only(self):
            self.assertTrue(True)
"""

#: Exactly one test, and it FAILS. `Ran 1 test` + `FAILED (failures=1)` — the
#: closest a genuine run gets to the placeholder's own output.
EXACTLY_ONE_FAILING_TEST = """
    import unittest


    class TestJustTheOne(unittest.TestCase):
        def test_only(self):
            self.assertEqual(1, 2)
"""


class TestGuardFires(unittest.TestCase):
    """A module that did not load is named as such, from real output."""

    def _broken_run(self) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            scratch_suite(tmp, SIBLING_HELPER, name="probe_helper")
            scratch_suite(tmp, IMPORTS_A_SIBLING, name="test_probe")
            return run_unittest(pathlib.Path(tmp), ["tests.test_probe"])

    def test_the_shape_reproduces_at_all(self):
        """The premise: this invocation really does report `Ran 1 test`.

        If this ever stops being true the rest of this file is guarding a
        defect that no longer exists, and it should say so here rather than
        keep passing quietly somewhere below.
        """
        proc = self._broken_run()
        self.assertIn(module_run.PLACEHOLDER, proc.stderr)
        self.assertEqual(module_run.ran_count(proc.stderr), 1,
                         f"expected the placeholder's `Ran 1 test`:\n{proc.stderr}")
        self.assertNotEqual(proc.returncode, 0)

    def test_load_failures_names_the_module(self):
        proc = self._broken_run()
        self.assertEqual(module_run.load_failures(proc.stderr), ["test_probe"])

    def test_verdict_is_produced_and_says_the_count_is_not_a_result(self):
        proc = self._broken_run()
        verdict = module_run.load_failure_verdict("test_probe", proc.stderr)
        self.assertIsNotNone(verdict)
        self.assertIn("did not load", verdict)
        self.assertIn("not a result", verdict)

    def test_run_module_raises_instead_of_returning_a_number(self):
        """**The measurement case, through the real entry point.**

        A caller that wanted a count gets an exception — the one return value
        that cannot be averaged into a result. TASK-341's poller returned 0
        and was believed.

        `discover` closes the sibling-import cause but not the class, so the
        module planted here fails on a name that exists nowhere at all.
        """
        with tempfile.TemporaryDirectory() as tmp:
            scratch_suite(tmp, "\nimport no_such_sibling_anywhere\n",
                          name="test_probe")
            with self.assertRaises(module_run.ModuleDidNotRun) as caught:
                module_run.run_module("test_probe", root=pathlib.Path(tmp))
        self.assertIn("did not load", str(caught.exception))
        self.assertIn("not a result", str(caught.exception))


class TestGuardDoesNotFire(unittest.TestCase):
    """**The half that keeps the guard from being a blanket refusal.**

    `Ran 1 test` is not the signal. The placeholder is.
    """

    def _run_scratch(self, body: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            scratch_suite(tmp, body, name="test_probe")
            return run_unittest(pathlib.Path(tmp),
                                ["discover", "-s", "tests", "-p",
                                 "test_probe.py", "-v"])

    def test_a_module_with_exactly_one_passing_test_is_not_condemned(self):
        proc = self._run_scratch(EXACTLY_ONE_REAL_TEST)
        self.assertEqual(module_run.ran_count(proc.stderr), 1,
                         proc.stderr)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(module_run.load_failures(proc.stderr), [])
        self.assertIsNone(
            module_run.load_failure_verdict("test_probe", proc.stderr),
            "one legitimate test reports `Ran 1 test` too; the guard may not "
            "refuse it, or it becomes a blanket ban that looks green")

    def test_a_module_with_exactly_one_FAILING_test_is_not_condemned(self):
        """The nearest neighbour: `Ran 1 test` AND a non-zero exit."""
        proc = self._run_scratch(EXACTLY_ONE_FAILING_TEST)
        self.assertEqual(module_run.ran_count(proc.stderr), 1, proc.stderr)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(module_run.load_failures(proc.stderr), [],
                         "a failing test is a result; only a module that never "
                         "loaded is not")
        self.assertIsNone(
            module_run.load_failure_verdict("test_probe", proc.stderr))

    def test_the_smallest_real_module_in_this_suite_is_tolerated(self):
        """The tolerance, against a REAL module at the low boundary.

        **The first version of this test asserted that the suite contains a
        module with exactly one test, and that assertion was false** — it went
        red on its first run. Measured 2026-09-12 across 132 modules, the
        smallest is `test_i18n_one_table` with 2; none has exactly 1. So the
        single-test case above is exercised only against scratch modules, and
        saying so is better than a test that reads as though a live module
        proved it.

        What a live module can prove is the boundary: the smallest module this
        suite actually has goes through `run_module` and comes back as a
        count. If a genuine one-test module ever lands, the assertion below
        picks it up as the new minimum with no edit.
        """
        counts = {p.stem: len(test_methods(p))
                  for p in sorted(TESTS.glob("test_*.py"))}
        counts.pop("test_module_run_guard", None)   # never run ourselves
        self.assertTrue(counts)
        smallest = min(counts, key=lambda k: (counts[k], k))
        r = module_run.run_module(smallest)
        self.assertIsNone(module_run.load_failure_verdict(smallest, r["err"]))
        self.assertGreaterEqual(r["ran"], 1)
        self.assertEqual(r["rc"], 0, r["err"][-2000:])

    def test_run_module_returns_a_count_for_a_single_test_module(self):
        """`run_module` on a module holding exactly one real test.

        The same shape the placeholder wears — `Ran 1 test` — reaching the
        real entry point and coming back as a NUMBER rather than an exception.
        This is the assertion that would break if the guard were ever
        "simplified" to `if ran == 1: refuse`.
        """
        with tempfile.TemporaryDirectory() as tmp:
            scratch_suite(tmp, EXACTLY_ONE_REAL_TEST, name="test_probe")
            r = module_run.run_module("test_probe", root=pathlib.Path(tmp))
        self.assertEqual(r["ran"], 1)
        self.assertEqual(r["rc"], 0)

    def test_a_healthy_repository_module_returns_a_count(self):
        """A real module from this suite, through `run_module`.

        Deliberately NOT this module: `run_module` spawns a subprocess that
        runs the named module, so naming the caller recurses without bound.
        `test_amend_matches_create` is the cheapest module on record (0.06s).
        """
        r = module_run.run_module("test_amend_matches_create")
        self.assertGreater(r["ran"], 1)
        self.assertEqual(r["rc"], 0, r["err"][-2000:])


def test_methods(path: pathlib.Path) -> list[str]:
    """Names of `test_*` methods declared inside classes in `path`.

    Syntactic — the file is parsed, never imported and never executed, so this
    costs nothing and cannot be perturbed by what a module does at import.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    out = []
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        for m in cls.body:
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and m.name.startswith("test"):
                out.append(m.name)
    return out


class TestEitherSignalAloneIsEnough(unittest.TestCase):
    """The two signals are OR-ed, and each is load-bearing on its own.

    `load_failures` reads two independent spellings of the same event: the
    loader's synthesised test id, and the `ImportError: Failed to import test
    module:` sentence. Both appear in today's CPython, so a mutation that
    deletes either regex leaves the guard green — which would make one of them
    decoration. These two tests remove the OTHER signal from real captured
    output and require the survivor to carry the detection alone.

    That is not a hypothetical: the id spelling already changed once
    (`_FailedTest` gained a `.<name>` suffix in 3.11), and a guard that needs
    both signals would have gone quietly vacuous on that release.
    """

    def setUp(self):
        with tempfile.TemporaryDirectory() as tmp:
            scratch_suite(tmp, SIBLING_HELPER, name="probe_helper")
            scratch_suite(tmp, IMPORTS_A_SIBLING, name="test_probe")
            self.stderr = run_unittest(pathlib.Path(tmp),
                                       ["tests.test_probe"]).stderr
        self.assertIn(module_run.PLACEHOLDER, self.stderr)
        self.assertIn("Failed to import test module", self.stderr)

    def test_the_placeholder_id_alone_is_enough(self):
        stripped = "\n".join(l for l in self.stderr.splitlines()
                             if "Failed to import test module" not in l)
        self.assertNotIn("Failed to import test module", stripped)
        self.assertEqual(module_run.load_failures(stripped), ["test_probe"])

    def test_the_import_error_sentence_alone_is_enough(self):
        stripped = "\n".join(l for l in self.stderr.splitlines()
                             if module_run.PLACEHOLDER not in l)
        self.assertNotIn(module_run.PLACEHOLDER, stripped)
        self.assertEqual(module_run.load_failures(stripped), ["test_probe"])


class TestTheRunnerSaysIt(unittest.TestCase):
    """`tests/parallel` actually prints the verdict.

    A classifier with unit tests and no caller is the same defect wearing a
    different hat — `tests/parallel`'s own `format_audit` docstring says so
    about TASK-284. So this drives the runner's real `failure_block` with a
    result carrying real placeholder output and requires the sentence to come
    out. Deleting the wiring from `failure_block` turns this red.
    """

    def setUp(self):
        self.P = load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            scratch_suite(tmp, SIBLING_HELPER, name="probe_helper")
            scratch_suite(tmp, IMPORTS_A_SIBLING, name="test_probe")
            self.stderr = run_unittest(pathlib.Path(tmp),
                                       ["tests.test_probe"]).stderr

    def _block(self, err: str, ran: int) -> str:
        r = {"mod": "test_probe.py", "rc": 1, "ran": ran, "sec": 0.1,
             "err": err, "ids": self.P.parse_ids(err)}
        return re.sub(r"\033\[[0-9;]*m", "", self.P.failure_block(r))

    def test_the_block_says_the_module_did_not_load(self):
        out = self._block(self.stderr, 1)
        self.assertIn("did not load", out)
        self.assertIn("not a result", out)

    def test_the_block_stays_quiet_for_an_ordinary_red_module(self):
        """Anti-vacuity for the wiring: a module that RAN and failed must not
        be described as one that never loaded."""
        with tempfile.TemporaryDirectory() as tmp:
            scratch_suite(tmp, EXACTLY_ONE_FAILING_TEST, name="test_probe")
            err = run_unittest(pathlib.Path(tmp),
                               ["discover", "-s", "tests", "-p",
                                "test_probe.py", "-v"]).stderr
        out = self._block(err, 1)
        self.assertNotIn("did not load", out)


class TestDottedInvocationWorks(unittest.TestCase):
    """`tests/__init__.py`'s job, asserted against the real repository.

    **Deleting `tests/__init__.py` turns this class red**, which is the only
    reason that file may be claimed to do anything: `discover` never imports
    it, so nothing else in the suite would notice its absence.
    """

    def test_a_sibling_importing_module_runs_via_the_dotted_name(self):
        proc = run_unittest(PERRY_HOME, ["tests.test_risks"])
        ran = module_run.ran_count(proc.stderr)
        self.assertEqual(module_run.load_failures(proc.stderr), [],
                         f"`python3 -m unittest tests.test_risks` failed to "
                         f"load — tests/__init__.py is the thing that makes "
                         f"this work.\n{proc.stderr[-2000:]}")
        self.assertGreater(
            ran or 0, 1,
            f"the placeholder reports `Ran 1`; this module has dozens of "
            f"tests.\n{proc.stderr[-2000:]}")
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])

    def test_every_sibling_importing_module_imports_under_the_dotted_name(self):
        """**The population, derived rather than sampled.**

        Every `tests/*.py` is attempted as `tests.<name>` in a FRESH
        interpreter — fresh because a module that puts `tests/` on `sys.path`
        itself would otherwise rescue every module imported after it and the
        sweep would understate. Import only: no tests are run, nothing is
        written.
        """
        mods = sorted(p.stem for p in TESTS.glob("*.py") if p.stem != "__init__")
        self.assertGreater(len(mods), 100, "the glob found almost nothing")
        snippet = ("import importlib, sys\n"
                   "try:\n"
                   "    importlib.import_module('tests.%s')\n"
                   "except ModuleNotFoundError as e:\n"
                   "    print('MISSING:' + (e.name or '?'))\n"
                   "else:\n"
                   "    print('OK')\n")

        def probe(name: str) -> tuple[str, str]:
            p = subprocess.run([sys.executable, "-c", snippet % name],
                               cwd=PERRY_HOME, capture_output=True,
                               text=True, timeout=180)
            tail = (p.stdout or "").strip().splitlines()
            return name, (tail[-1] if tail else f"NO-OUTPUT: {p.stderr[-300:]}")

        with cf.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(probe, mods))
        broken = [(n, v) for n, v in results if v != "OK"]
        self.assertEqual(
            broken, [],
            "these modules cannot be imported as `tests.<name>`; "
            "tests/__init__.py exists to make every one of them work:\n  "
            + "\n  ".join(f"{n}: {v}" for n, v in broken))


if __name__ == "__main__":
    unittest.main()
