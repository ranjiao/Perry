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

COVERS = ("tests/parallel", "tests/durations.json", "tests/module_run.py")

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
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

    def test_an_empty_hint_is_exactly_the_pre_task_230_alphabetical_order(self):
        """What `--alphabetical` reproduces, so the A/B is a real A/B.

        The measured saving is only meaningful if the "before" arm is the
        schedule that actually shipped before. It was `sorted(glob)`, and an
        empty hint reproduces it exactly rather than approximately.
        """
        mods = ["test_c.py", "test_a.py", "test_b.py"]
        self.assertEqual(P.schedule(mods, {}), sorted(mods))

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

    def test_a_test_that_wrote_to_stderr_is_still_counted(self):
        """**The fourteen that went missing.** `unittest` prints ` ... ` when
        the test STARTS, so anything the test writes to stderr lands between
        that and the verdict — and the verdict ends up alone on a line. The
        first version required ` ... ` on the same line, matched nothing, and
        dropped the test from the set entirely. Real shape, copied out of
        `test_one_header_rule` on the live suite.
        """
        text = ("test_value_normalizers_are_not_flagged "
                "(test_m.C.test_value_normalizers_are_not_flagged)\n"
                "**The judgement in this module.** ... "
                "<unknown>:939: DeprecationWarning: invalid escape sequence\n"
                "<unknown>:85: DeprecationWarning: invalid escape sequence\n"
                "ok\n")
        self.assertEqual(
            P.parse_ids(text),
            [("test_m.C.test_value_normalizers_are_not_flagged", "ok")])

    def test_a_bare_verdict_with_no_test_open_is_not_a_test(self):
        """`OK` and a stray `ok` in a traceback must not invent an id."""
        self.assertEqual(P.parse_ids("ok\nFAIL\nOK\n"), [])

    def test_stderr_noise_does_not_bleed_one_verdict_onto_the_next_test(self):
        text = ("test_a (test_m.C.test_a)\nwarning here\nok\n"
                "test_b (test_m.C.test_b) ... FAIL\n")
        self.assertEqual(P.parse_ids(text),
                         [("test_m.C.test_a", "ok"), ("test_m.C.test_b", "FAIL")])

    def test_a_module_whose_ids_do_not_add_up_is_named(self):
        """The guard that turns a silent undercount into a refusal.

        Without this the failure is invisible by construction: `--ids` writes
        whatever the parser found, and a set short by fourteen looks exactly
        like a set that is right.
        """
        results = [{"mod": "test_a.py", "ran": 3, "ids": [1, 2, 3]},
                   {"mod": "test_b.py", "ran": 9, "ids": [1, 2]}]
        self.assertEqual([r["mod"] for r in P.unaccounted(results)],
                         ["test_b.py"])

    def test_a_module_that_adds_up_is_not_named(self):
        self.assertEqual(
            P.unaccounted([{"mod": "test_a.py", "ran": 2, "ids": [1, 2]}]), [])

    def test_more_ids_than_tests_is_also_a_mismatch(self):
        """Over-counting is not the safe direction of the same bug — it means
        the parser invented an id, and a set with a test in it that did not run
        is as wrong as one missing a test that did."""
        self.assertEqual(
            [r["mod"] for r in
             P.unaccounted([{"mod": "test_a.py", "ran": 1, "ids": [1, 2]}])],
            ["test_a.py"])

    def test_every_test_in_the_live_suites_noisiest_module_is_accounted_for(self):
        """The property, run against a real module rather than a fixture.

        `--ids` is the pass/fail SET the whole verification story rests on, and
        the failure it must not have is understating it. `Ran N` is unittest's
        own count; the ids come from the verbose stream. Two independent
        origins, and they have to agree.
        """
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests",
             "-p", "test_one_header_rule.py", "-v"],
            capture_output=True, text=True, cwd=ROOT)
        ran = sum(int(line.split()[1]) for line in proc.stderr.splitlines()
                  if line.startswith("Ran "))
        self.assertTrue(ran, "the reference module ran nothing")
        self.assertEqual(len(P.parse_ids(proc.stderr)), ran,
                         "the id parser did not account for every test the "
                         "module ran")


def twice_failing_stderr(pad: int = 40) -> str:
    """`unittest -v` output for a module whose TWO tests both failed.

    Copied line for line from a real run of a two-failure module on
    2026-09-02, with the assertion body parameterised so the test can push the
    FIRST failure's `FAIL:` header out of any tail window it likes. That
    header falling out is the whole defect: at `[-25:]` the excerpt showed one
    header for two failures and said nothing.
    """
    first = "\n".join(f"first-failure detail line {i:02d}" for i in range(pad))
    bar, dash = "=" * 70, "-" * 70
    return (
        "test_first_failure (test_zz.TwiceFailing.test_first_failure) ... FAIL\n"
        "test_second_failure (test_zz.TwiceFailing.test_second_failure) ... FAIL\n"
        "\n"
        f"{bar}\n"
        "FAIL: test_first_failure (test_zz.TwiceFailing.test_first_failure)\n"
        f"{dash}\n"
        "Traceback (most recent call last):\n"
        '  File "/tmp/test_zz.py", line 10, in test_first_failure\n'
        "    self.fail(...)\n"
        "AssertionError: FIRST failure\n"
        f"{first}\n"
        "\n"
        f"{bar}\n"
        "FAIL: test_second_failure (test_zz.TwiceFailing.test_second_failure)\n"
        f"{dash}\n"
        "Traceback (most recent call last):\n"
        '  File "/tmp/test_zz.py", line 13, in test_second_failure\n'
        "    self.fail(...)\n"
        "AssertionError: SECOND failure\n"
        "\n"
        f"{dash}\n"
        "Ran 2 tests in 0.001s\n"
        "\n"
        "FAILED (failures=2)\n")


def twice_failing_result(pad: int = 40) -> dict:
    err = twice_failing_stderr(pad)
    return {"mod": "test_zz.py", "rc": 1, "ran": 2, "sec": 0.1, "err": err,
            "ids": P.parse_ids(err)}


class TestARedModulesFailureCountSurvivesTheExcerpt(unittest.TestCase):
    """TASK-251. **A failure that only exists inside a 25-line window is a
    failure the runner can lose, and it lost one.**

    The block printed for a red module used to be the module name and
    `err.strip().splitlines()[-25:]`, with nothing marking the cut. On
    2026-08-30 the TASK-249 agent found the mechanism while retracting a
    failure count this output had produced: a module that fails twice keeps
    the SECOND failure's `FAIL:` header inside the window and loses the
    FIRST's, so a reader counting headers counts one failure where there were
    two — and every spec in this project asks the agent to report a baseline
    failure count taken from exactly here.

    So the counts and the names are computed from the WHOLE stream and printed
    ABOVE the excerpt, and the excerpt says when it is a window and how big a
    bite it took. These tests hold both halves; the class after this one holds
    the part that is wired into `main()`, because a helper with unit tests and
    no asserted caller is this repository's named defect shape.
    """

    def test_the_first_failure_is_named_even_when_its_header_is_truncated_away(self):
        """The reproduction, as an assertion.

        `pad=40` puts the first `FAIL:` header 47 lines above the end, well
        outside the 25-line window — exactly as the live repro did.
        """
        r = twice_failing_result(pad=40)
        block = P.failure_block(r)
        self.assertNotIn("FAIL: test_first_failure", P.excerpt(r["err"]),
                         "the fixture does not reproduce the truncation this "
                         "test is about — raise pad")
        self.assertIn("test_zz.TwiceFailing.test_first_failure", block,
                      "the first failure is nowhere in what the runner prints")
        self.assertIn("test_zz.TwiceFailing.test_second_failure", block)

    def test_the_block_states_two_tests_failed(self):
        self.assertIn("2 of 2 test(s) failed",
                      P.failure_block(twice_failing_result(pad=40)))

    def test_the_excerpt_says_how_many_lines_it_dropped(self):
        """The elision is announced, with a number, or it is silent again.

        This is the assertion a bare `[-25:]` slice cannot satisfy.
        """
        err = "\n".join(f"line {i}" for i in range(60))
        out = P.excerpt(err, limit=25)
        self.assertIn("35 earlier line(s) elided of 60", out)
        self.assertEqual(out.splitlines()[-1], "line 59")
        self.assertEqual(len(out.splitlines()), 26, "notice + 25 lines")

    def test_output_that_fits_is_printed_whole_and_claims_no_elision(self):
        """The other direction, so the test above cannot pass by shouting
        'truncated' at every module."""
        err = "\n".join(f"line {i}" for i in range(25))
        out = P.excerpt(err, limit=25)
        self.assertEqual(out, err)
        self.assertNotIn("elided", out)

    def test_the_default_window_is_the_one_the_runner_uses(self):
        long_err = "\n".join(f"line {i}" for i in range(100))
        self.assertEqual(P.excerpt(long_err), P.excerpt(long_err, P.TAIL_LINES))
        self.assertIn("elided", P.excerpt(long_err))

    def test_failing_ids_reads_fails_and_errors_and_nothing_else(self):
        r = {"ids": [("m.C.a", "ok"), ("m.C.b", "FAIL"), ("m.C.c", "ERROR"),
                     ("m.C.d", "skipped"), ("m.C.e", "expected")]}
        self.assertEqual(P.failing_ids(r),
                         [("m.C.b", "FAIL"), ("m.C.c", "ERROR")])

    def test_unittest_own_tally_is_read_from_its_verdict_line(self):
        self.assertEqual(P.unittest_bad_count("FAILED (failures=2)\n"), 2)
        self.assertEqual(
            P.unittest_bad_count("FAILED (failures=1, errors=3)\n"), 4)
        self.assertEqual(
            P.unittest_bad_count("FAILED (errors=1, skipped=9)\n"), 1)
        self.assertEqual(P.unittest_bad_count("OK\n"), None)

    def test_a_module_with_no_verdict_line_is_not_reported_as_zero_failures(self):
        """**None is not zero.** A module that died before unittest could
        total anything has an unknown failed-test count, and printing `0 of 0
        test(s) failed` under a red module is the same class of wrong number
        this row exists to remove.
        """
        r = {"mod": "test_zz.py", "rc": 7, "ran": 0, "sec": 0.1,
             "err": "boom, about to die\n", "ids": []}
        block = P.failure_block(r)
        self.assertIn("NOT known", block)
        self.assertNotIn("0 of 0 test(s) failed", block)

    def test_a_disagreement_between_the_two_counts_is_named_and_the_larger_wins(self):
        """Two origins for one number, and the runner may not quietly pick.

        unittest's own tally and the id parser's are independent. The parser
        is the one that has understated before — fourteen ids missing out of
        2899, see `parse_ids` — so the larger is reported and the
        disagreement is printed rather than smoothed over.
        """
        r = {"mod": "test_zz.py", "rc": 1, "ran": 9, "sec": 0.1,
             "err": "FAILED (failures=3)\n", "ids": [("m.C.a", "FAIL")]}
        self.assertEqual(P.failed_test_count(r), 3)
        block = P.failure_block(r)
        self.assertIn("3 of 9 test(s) failed", block)
        self.assertIn("unittest counted 3", block)
        self.assertIn("id parser named 1", block)


class TestTheTwoCountsAreWiredIntoMainAndNamedApart(unittest.TestCase):
    """`failure_block` being right is not the same as `main()` printing it.

    The class below this one already carries that scar: a V4 round deleted a
    guard's USE and the whole suite stayed green, because the helper had unit
    tests and its caller had none. So `main()` is driven here with
    `run_module` stubbed, and the two numbers are asserted to reach stdout as
    two separately-labelled numbers — because `N module(s) red` alone, read as
    a test count, is one of the three numbers TASK-251 is about.
    """

    def _main(self, results: list[dict]) -> tuple[int, str]:
        by_mod = {r["mod"]: r for r in results}
        old_run, old_argv = P.run_module, sys.argv
        P.run_module = lambda name: by_mod[name]
        sys.argv = ["parallel"] + [r["mod"].removesuffix(".py")
                                   for r in results]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = P.main()
        finally:
            P.run_module, sys.argv = old_run, old_argv
        return rc, buf.getvalue()

    def test_a_twice_failing_module_reports_two_failed_tests_in_one_red_module(self):
        """The reproduction, end to end through `main()`.

        One MODULE red and TWO TESTS failed are different numbers. Both are
        printed, both are labelled, and neither is read off the excerpt.
        """
        r = dict(twice_failing_result(pad=40), mod="test_parallel_runner.py")
        rc, out = self._main([r])
        self.assertEqual(rc, 1)
        self.assertIn("1 of 1 MODULE(S) red", out)
        self.assertIn("2 of 2 TEST(S) failed", out)
        self.assertIn("test_zz.TwiceFailing.test_first_failure", out)
        self.assertIn("test_zz.TwiceFailing.test_second_failure", out)

    def test_main_announces_the_elision_rather_than_slicing_silently(self):
        r = dict(twice_failing_result(pad=40), mod="test_parallel_runner.py")
        _, out = self._main([r])
        self.assertIn("earlier line(s) elided", out)

    def test_a_green_run_prints_neither_count(self):
        """So the two assertions above cannot pass by printing failures
        unconditionally."""
        r = {"mod": "test_parallel_runner.py", "rc": 0, "ran": 3, "sec": 0.1,
             "err": "OK\n", "ids": [(f"m.C.t{i}", "ok") for i in range(3)]}
        rc, out = self._main([r])
        self.assertEqual(rc, 0)
        self.assertNotIn("MODULE(S) red", out)
        self.assertNotIn("TEST(S) failed", out)


class TestTheRefusalIsWiredIntoMainAndNotJustDefined(unittest.TestCase):
    """`unaccounted()` being right is not the same as `main()` using it.

    **A V4 round found this by deleting the guard**: change `if short:` to
    `if False:` in `main()` and the entire suite stayed green, because
    `unaccounted()` had unit tests and its USE had none. That is this project's
    named defect shape — a guard that survives its own deletion is not a guard
    — and it is the same shape the row before this one was failed for.

    So `main()` is driven directly here, with `run_module` replaced by a stub
    so no test actually runs. Both halves of the refusal are asserted, because
    they are two separate lines and either can be deleted alone: the file is
    NOT written, and the exit status is NOT zero.
    """

    def _main(self, ran, ids, out_path):
        """Run `main()` for one module whose `ran`/`ids` counts are as given."""
        stub = {"mod": "test_one_header_rule.py", "rc": 0, "ran": ran,
                "sec": 0.1, "err": "", "ids": [(f"m.C.t{i}", "ok")
                                               for i in range(ids)]}
        old_run, old_argv = P.run_module, sys.argv
        P.run_module = lambda name: dict(stub, mod=name)
        sys.argv = ["parallel", "--ids", str(out_path), "test_one_header_rule"]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = P.main()
        finally:
            P.run_module, sys.argv = old_run, old_argv
        return rc, buf.getvalue()

    def test_a_short_count_writes_no_file_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "ids.tsv"
            rc, printed = self._main(ran=12, ids=11, out_path=out)
            self.assertFalse(out.exists(),
                             "main() wrote a set it could not account for")
            self.assertNotEqual(rc, 0,
                                "main() exited 0 on a set it could not "
                                "account for")
            self.assertIn("test_one_header_rule.py", printed)
            self.assertIn("12", printed)
            self.assertIn("11", printed)

    def test_a_count_that_adds_up_writes_the_file_and_exits_zero(self):
        """The other direction, so the test above cannot pass by refusing
        everything — which is how a guard gets 'fixed' into uselessness."""
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "ids.tsv"
            rc, _ = self._main(ran=12, ids=12, out_path=out)
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists(), "main() refused a set that added up")
            self.assertEqual(len(out.read_text().splitlines()), 12)


if __name__ == "__main__":
    unittest.main()
