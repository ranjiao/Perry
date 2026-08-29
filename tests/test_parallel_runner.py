"""`tests/parallel`'s scheduling hint may reorder the work. It may never select it.

TASK-230 gave the runner a stopwatch (`tests/durations.json`) so the long
modules start first. That file is written by a previous run, is not validated
by anything, and lands in the same repository as the modules it names — so the
question this module exists to answer is not "does it make the suite faster"
but **"what is the worst thing a wrong one can do?"**

The answer has to be "a worse schedule", and it has to stay that way, because
this runner already carries a scar from the other answer. Its first version
shelled out to `python3 -m unittest tests.<name>`, which does not put `tests/`
on `sys.path`; eighty tests stopped running, the total came back 1207 against
1287, and **the number was still large enough to look right**. A scheduling
file that can drop a module reintroduces exactly that failure with a more
respectable-looking cause.

So `schedule()` is asserted to be a permutation — same length, same membership
— under every way the hint can be wrong: absent, stale, naming modules that do
not exist, missing modules that do, holding the wrong types, or being garbage
that does not parse. None of those may change WHICH modules run.

Run: python3 tests/parallel test_parallel_runner
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tests" / "parallel"


def _load():
    """Import `tests/parallel`, which has no `.py` extension on purpose."""
    loader = importlib.machinery.SourceFileLoader("perry_tests_parallel",
                                                  str(RUNNER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


P = _load()


class TestTheHintReordersAndNeverSelects(unittest.TestCase):
    """Every wrong hint costs an order and nothing else."""

    def setUp(self):
        self.mods = ["test_a.py", "test_b.py", "test_c.py", "test_d.py"]

    def assertPermutation(self, got, why):
        self.assertEqual(sorted(got), sorted(self.mods), why)
        self.assertEqual(len(got), len(self.mods), why)

    def test_no_hint_at_all_keeps_every_module(self):
        self.assertPermutation(P.schedule(self.mods, {}), "empty hint")

    def test_a_hint_naming_modules_that_do_not_exist_keeps_every_module(self):
        hint = {"test_gone.py": 900.0, "test_also_gone.py": 5.0}
        self.assertPermutation(P.schedule(self.mods, hint), "stale names")

    def test_a_hint_missing_modules_keeps_every_module(self):
        self.assertPermutation(P.schedule(self.mods, {"test_a.py": 3.0}),
                               "partial hint")

    def test_a_hint_covering_everything_keeps_every_module(self):
        hint = {m: float(i) for i, m in enumerate(self.mods)}
        self.assertPermutation(P.schedule(self.mods, hint), "full hint")

    def test_the_live_module_set_survives_the_live_hint(self):
        """The property, against whatever this repository actually holds."""
        live = sorted(p.name for p in (ROOT / "tests").glob("test_*.py"))
        got = P.schedule(live, P.load_durations())
        self.assertEqual(sorted(got), live)


class TestLongestFirstAndUnknownFirstOfAll(unittest.TestCase):
    """The ordering the makespan argument depends on."""

    def test_known_modules_run_longest_first(self):
        mods = ["test_a.py", "test_b.py", "test_c.py"]
        hint = {"test_a.py": 1.0, "test_b.py": 90.0, "test_c.py": 10.0}
        self.assertEqual(P.schedule(mods, hint),
                         ["test_b.py", "test_c.py", "test_a.py"])

    def test_an_unrecorded_module_is_assumed_slow_and_goes_first(self):
        """A new module has no time. Guessing "fast" puts it last, which is
        the one placement whose cost is its whole duration."""
        mods = ["test_known.py", "test_new.py"]
        hint = {"test_known.py": 900.0}
        self.assertEqual(P.schedule(mods, hint)[0], "test_new.py")

    def test_the_order_is_deterministic_for_equal_times(self):
        mods = ["test_b.py", "test_a.py"]
        hint = {"test_a.py": 5.0, "test_b.py": 5.0}
        self.assertEqual(P.schedule(mods, hint), P.schedule(mods, hint))
        self.assertEqual(P.schedule(mods, hint), ["test_a.py", "test_b.py"])


class TestAnUnreadableStopwatchIsNotAnOutage(unittest.TestCase):
    """Reading the hint may not raise. The worst it may do is return nothing."""

    def _with_durations(self, text):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "durations.json"
            path.write_text(text)
            old, P.DURATIONS = P.DURATIONS, path
            try:
                return P.load_durations()
            finally:
                P.DURATIONS = old

    def test_garbage_reads_as_no_hint(self):
        self.assertEqual(self._with_durations("{not json"), {})

    def test_a_json_list_reads_as_no_hint(self):
        self.assertEqual(self._with_durations('["test_a.py"]'), {})

    def test_a_non_numeric_time_reads_as_no_hint(self):
        self.assertEqual(self._with_durations('{"test_a.py": "slow"}'), {})

    def test_a_missing_file_reads_as_no_hint(self):
        with tempfile.TemporaryDirectory() as td:
            old = P.DURATIONS
            P.DURATIONS = pathlib.Path(td) / "nope.json"
            try:
                self.assertEqual(P.load_durations(), {})
            finally:
                P.DURATIONS = old

    def test_a_good_file_reads_as_the_hint(self):
        self.assertEqual(self._with_durations(json.dumps({"test_a.py": 2.5})),
                         {"test_a.py": 2.5})


class TestTheIdParserSeesEveryOutcome(unittest.TestCase):
    """`--ids` is the pass/fail SET. A parser that drops a line understates it.

    The continuation case is the one that matters: `unittest -v` prints the
    test's docstring between the id and its verdict, so the outcome does not
    land on the line that names the test.
    """

    def test_an_outcome_on_the_id_line_is_read(self):
        line = "test_x (test_m.C.test_x) ... ok"
        self.assertEqual(P.parse_ids(line), [("test_m.C.test_x", "ok")])

    def test_an_outcome_after_a_docstring_is_read(self):
        text = ("test_x (test_m.C.test_x)\n"
                "Markdown allows it and real boards use it. This is ... ok\n")
        self.assertEqual(P.parse_ids(text), [("test_m.C.test_x", "ok")])

    def test_failures_errors_and_skips_are_all_read(self):
        text = ("test_a (test_m.C.test_a) ... FAIL\n"
                "test_b (test_m.C.test_b) ... ERROR\n"
                "test_c (test_m.C.test_c) ... skipped 'why'\n"
                "test_d (test_m.C.test_d) ... expected failure\n"
                "test_e (test_m.C.test_e) ... unexpected success\n")
        self.assertEqual(
            P.parse_ids(text),
            [("test_m.C.test_a", "FAIL"), ("test_m.C.test_b", "ERROR"),
             ("test_m.C.test_c", "skipped"),
             ("test_m.C.test_d", "expected"),
             ("test_m.C.test_e", "unexpected")])

    def test_the_summary_lines_are_not_mistaken_for_tests(self):
        text = ("test_x (test_m.C.test_x) ... ok\n\n"
                "----------------------------------------\n"
                "Ran 1 test in 0.061s\n\nOK\n")
        self.assertEqual(P.parse_ids(text), [("test_m.C.test_x", "ok")])


if __name__ == "__main__":
    unittest.main()
