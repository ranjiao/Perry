"""`--slow` and `HARNESS_SELF_TESTS`, held by tests that run by DEFAULT.

**Why this module exists rather than more cases in `test_parallel_runner`.**
That module is itself in `HARNESS_SELF_TESTS`, so anything asserted there is
deferred behind the very flag it would be asserting. TASK-400's V4 round found
the shape live: `--record` on a default run rewrote `durations.json` from 121
modules to 118, and the module that gates that file — `test_durations_provenance`
— is one of the three the change had just deferred. `bash tests/run` printed
"all green" over a file this repository's own check refuses.

The same round mutated the feature and found it unheld: breaking `--slow` in
`tests/parallel` and swallowing it again in `tests/run` were **both green**,
and a repo-wide grep for `--slow` or `HARNESS_SELF_TESTS` matched nothing in
121 modules. Four acceptance criteria were true and held by nothing.

So: these cases live in a module the default run executes, and they cost
milliseconds because `run_module` is stubbed — no module is actually run.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_loader = SourceFileLoader("parallel", str(ROOT / "tests" / "parallel"))
P = module_from_spec(spec_from_loader("parallel", _loader))
_loader.exec_module(P)


def _select(argv: list[str]) -> tuple[int, list[str]]:
    """Run `main()` with every module stubbed. Returns (rc, modules asked for).

    The selection is what this module is about, so the stub records the names
    `main` hands to `run_module` and returns a canned green result. Nothing is
    executed and nothing is timed.

    **`DURATIONS` is redirected to a temp file, and this is not a precaution.**
    Two cases below pass `--record`, which reaches `write_record` — and
    `write_record` writes `P.DURATIONS`, the LIVE `tests/durations.json`. With
    the stub returning a canned `sec: 0.01`, a plain `bash tests/run` rewrote
    all 123 real module times as `0.01` and left the tree dirty; step 0's tree
    guard caught it every run, which is what the guard is for. Measured
    2026-09-09 on `65780a73`: 123 of 123 entries `0.01`, stamped as
    `tests/parallel --record -j 8` by a run that passed no such flag.
    """
    asked: list[str] = []

    def stub(name: str) -> dict:
        asked.append(name)
        return {"mod": name, "rc": 0, "ran": 1, "sec": 0.01,
                "err": "OK\n", "ids": [(f"{name[:-3]}.C.t", "ok")]}

    old_run, old_argv, old_durations = P.run_module, sys.argv, P.DURATIONS
    P.run_module = stub
    sys.argv = ["parallel", *argv]
    buf = io.StringIO()
    with tempfile.TemporaryDirectory() as td:
        P.DURATIONS = pathlib.Path(td) / "durations.json"
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc = P.main()
        finally:
            P.run_module, sys.argv = old_run, old_argv
            P.DURATIONS = old_durations
    return rc, sorted(asked)


def _on_disk() -> set[str]:
    return {p.name for p in (ROOT / "tests").glob("test_*.py")}


class TestTheSetIsWhatItSaysItIs(unittest.TestCase):
    def test_the_three_names_resolve_to_files_on_disk(self):
        """A deferred module that does not exist defers nothing and hides a
        typo: the filter is a membership test on a name, so a misspelling is
        silently a no-op."""
        missing = sorted(P.HARNESS_SELF_TESTS - _on_disk())
        self.assertEqual(missing, [], f"named but absent: {missing}")

    def test_restore_check_is_not_in_the_set(self):
        """`test_restore_check` tests `bin/perry-restore-check`, a PRODUCT tool
        and the one a mutation round depends on. It was considered and kept in
        the default run deliberately; the line is what a module tests, not what
        it costs."""
        self.assertNotIn("test_restore_check.py", P.HARNESS_SELF_TESTS)


class TestTheDefaultRunAndSlowDifferByExactlyTheSet(unittest.TestCase):
    def test_a_default_run_asks_for_everything_except_the_set(self):
        rc, asked = _select([])
        self.assertEqual(rc, 0)
        self.assertEqual(set(asked), _on_disk() - P.HARNESS_SELF_TESTS)

    def test_slow_asks_for_the_whole_tree(self):
        rc, asked = _select(["--slow"])
        self.assertEqual(rc, 0)
        self.assertEqual(set(asked), _on_disk())

    def test_the_difference_is_the_set_and_nothing_else(self):
        """Stated as a difference rather than as two memberships, so a module
        appearing in one run and not the other cannot pass both cases above by
        being wrong in the same direction twice."""
        _, plain = _select([])
        _, slow = _select(["--slow"])
        self.assertEqual(set(slow) - set(plain), P.HARNESS_SELF_TESTS)
        self.assertEqual(set(plain) - set(slow), set())


class TestNamingAModuleReachesIt(unittest.TestCase):
    """`--only test_tree_guard` must run it. Answering "no test module matches"
    about a file sitting on disk is a lie, and the first implementation of the
    filter did exactly that by running before `--only`."""

    def test_a_deferred_module_can_be_named(self):
        for name in sorted(P.HARNESS_SELF_TESTS):
            with self.subTest(module=name):
                rc, asked = _select([name.removesuffix(".py")])
                self.assertEqual(rc, 0)
                self.assertEqual(asked, [name])

    def test_an_absent_name_is_still_refused(self):
        """The control: the refusal path stays reachable, so the case above
        cannot pass by accepting everything."""
        rc, asked = _select(["test_no_such_module_anywhere"])
        self.assertEqual(rc, 2)
        self.assertEqual(asked, [])


class TestRecordCoversTheWholeTree(unittest.TestCase):
    """TASK-400's V4 FAIL, as a test.

    `durations.json` is a statement about every module on disk —
    `test_durations_provenance` reads it that way — so recording from a
    narrowed run writes a file that is wrong about the tree rather than stale.
    """

    def test_record_asks_for_every_module_even_on_a_default_run(self):
        rc, asked = _select(["--record"])
        self.assertEqual(rc, 0)
        self.assertEqual(set(asked), _on_disk())

    def test_only_still_skips_recording_rather_than_widening(self):
        """A caller who named one module did not ask to re-time the tree, and
        `--record --only X` must not silently become a whole-tree run."""
        rc, asked = _select(["--record", "test_slow_selector"])
        self.assertEqual(rc, 0)
        self.assertEqual(asked, ["test_slow_selector.py"])


class TestRunForwardsTheFlag(unittest.TestCase):
    """`tests/run` matched only `--only`, `--serial` and `--lint` and dropped
    everything else silently, so a flag that works on `tests/parallel` and is
    swallowed by `tests/run` satisfies nothing. Mutating the forwarding branch
    away was green before this case existed.

    The tree is built once for the class: `git archive` for the scaffolding
    the script's earlier steps need, then **the working tree's own `tests/run`
    copied over it**, because archiving HEAD would test the last commit rather
    than the file in front of the author. `tests/parallel` is replaced by a
    stub that records the argv it was handed and does nothing else.
    """

    tmp = None
    root = None

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "t"
        cls.root.mkdir()
        archive = subprocess.run(["git", "archive", "HEAD"], cwd=ROOT,
                                 capture_output=True, timeout=120)
        if archive.returncode != 0:
            raise unittest.SkipTest("not a git checkout")
        subprocess.run(["tar", "-x", "-C", str(cls.root)],
                       input=archive.stdout, timeout=120, check=True)
        shutil.copy(ROOT / "tests" / "run", cls.root / "tests" / "run")
        (cls.root / "tests" / "parallel").write_text(
            "#!/usr/bin/env python3\n"
            "import sys, json, pathlib\n"
            "pathlib.Path('argv.json').write_text(json.dumps(sys.argv[1:]))\n"
        )

    @classmethod
    def tearDownClass(cls):
        if cls.tmp is not None:
            cls.tmp.cleanup()

    def _argv_reaching_parallel(self, *flags: str) -> list[str]:
        got = self.root / "argv.json"
        got.unlink(missing_ok=True)
        env = dict(os.environ)
        env.pop("PERRY_PROJECT", None)
        subprocess.run(["bash", "tests/run", *flags], cwd=self.root, env=env,
                       capture_output=True, text=True, timeout=300)
        return json.loads(got.read_text()) if got.exists() else []

    def test_slow_reaches_the_runner(self):
        self.assertIn("--slow", self._argv_reaching_parallel("--slow"))

    def test_a_plain_run_does_not_pass_it(self):
        """The control, so the case above cannot pass by always sending it."""
        self.assertNotIn("--slow", self._argv_reaching_parallel())


if __name__ == "__main__":
    unittest.main()
