"""`tests/durations.json` must describe the tree in front of it, and say where it came from.

TASK-230 gave `tests/parallel` a longest-first schedule and measured **33-37%
of wall time** coming out of it. That makes `tests/durations.json` load-bearing
— and until TASK-304 **nothing in the file distinguished a fresh number from
one that had drifted**, and nothing anywhere reported that it had.

What that cost, measured at `d49964e`:

* 103 modules recorded against **108 on disk**. Seven live modules were
  unmentioned. An unmentioned module sorts as `inf` and runs first, which is
  the right placement — arrived at by omission rather than by decision, so
  nothing distinguished it from an entry somebody had deleted.
* **Two recorded modules did not exist**, and one of them, `test_migrate.py` at
  97.25, was the **largest entry in the file** — the head of its own ranking
  was a module deleted when USER-910 took migration out. `test_conformance.py`
  went in `TASK-261`. Neither deletion touched this file and nothing noticed
  for months.
* `test_header_rule_harness.py` was recorded at **25.53s** and measured
  **265.996s** and **260.74s** at `d49964e`, the very commit that wrote the
  file. Ten times low, so it sorted late and became the tail — the exact
  pathology the schedule exists to avoid.

**The sharpest argument for the stamp is not any of those numbers.** `TASK-244`
is bringing that harness module to roughly 34s. At that point `25.53` looks
plausible again, and a file of bare numbers cannot tell *accidentally correct*
from *measured*. Provenance can.

## What is red here, and what is only reported

Red — drift, the two directions of "this file is not about this tree":

* a module on disk that the file does not mention,
* a recorded module that no longer exists,
* an entry whose `source` names a block the file does not define.

Reported, never red — provenance and staleness:

* how many figures carry a ref, how many are stale, how many are unstamped.

That split is deliberate. **Every figure the file inherited is unstamped**, so
a check that reddened on unstamped entries would have to be disabled on the day
it landed, and a guard that ships switched off is not a guard. Making the count
visible on every run is what TASK-304 asked for; re-measuring 108 modules under
a load average that has been above 20 all evening would substitute one wrong
number for another and is explicitly out of that row's bound.

## What runs this

Nothing has to be typed. This module is `tests/test_*.py`, so:

* `bash tests/run` runs it in step 2, through `tests/parallel`;
* `bash tests/run --serial` runs it through `python3 -m unittest discover`;
* `python3 tests/parallel` runs it with no arguments at all.

`tests/parallel` *additionally* prints the whole audit as a banner after every
run, again with no flag — `TestTheBannerIsWiredIntoMainAndNotJustDefined`
below is what holds that, because this repository has already failed a V4 round
(TASK-284) for adding a report nothing invoked.

Run: python3 tests/parallel test_durations_provenance
"""

from __future__ import annotations

COVERS = ("tests/durations.json", "tests/parallel")

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tests" / "parallel"


def _load():
    """Import `tests/parallel`, which has no `.py` extension on purpose."""
    loader = importlib.machinery.SourceFileLoader("perry_tests_parallel_prov",
                                                  str(RUNNER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


P = _load()


def _live():
    """The live glob and the live document — what a run would actually see."""
    mods = sorted(p.name for p in (ROOT / "tests").glob("test_*.py"))
    return mods, P.load_document()


def _audit(mods, doc):
    """Audit with the ref check stubbed, so these tests do not depend on git.

    The staleness verdict has its own tests below against a fake `ancestor`.
    Mixing it in here would make a drift assertion fail on a machine with no
    git, which is a false red about the wrong thing.
    """
    return P.audit(mods, doc, ancestor=lambda ref: True)


class TestTheFileIsAboutThisTree(unittest.TestCase):
    """Drift, both directions. This is the red gate.

    Both conditions were silent before TASK-304 and both are named here, with
    the offending module in the message — "durations.json is wrong" is not
    something anyone can act on.
    """

    def test_no_recorded_module_has_been_deleted(self):
        """`test_migrate.py` at 97.25 held the head of this file's ranking.

        A deleted module's time is not a stale hint, it is a fossil: there is
        no run it could ever describe again.
        """
        mods, doc = _live()
        report = _audit(mods, doc)
        self.assertEqual(
            report["phantom"], [],
            "tests/durations.json records modules that are not on disk: "
            f"{report['phantom']}. Delete the entries — a deleted module's "
            "recorded time can never again describe a run.")

    def test_every_module_on_disk_is_listed(self):
        """Seven were not, at `d49964e`.

        Listing a module with `sec: null` is a complete answer: it says
        "nobody has measured this", it still sorts as `inf` and runs first,
        and it is distinguishable from an entry somebody removed. What is not
        allowed is silence.
        """
        mods, doc = _live()
        report = _audit(mods, doc)
        self.assertEqual(
            report["unlisted"], [],
            "these modules exist and tests/durations.json does not mention "
            f"them: {report['unlisted']}. Each will sort as inf and run first "
            "by accident rather than by decision. Add an entry — `sec: null` "
            "is a valid one and means exactly 'not measured'.")

    def test_merge_result_sources_declare_existing_inputs_and_tested_tree(self):
        mods, doc = _live()
        self.assertEqual(_audit(mods, doc)["invalid_sources"], [],
                         "merge-result stamps need full input SHAs, tested tree and full/slow tier")

    def test_every_entry_names_a_source_the_file_defines(self):
        """Provenance that cannot be dereferenced is not provenance."""
        mods, doc = _live()
        report = _audit(mods, doc)
        self.assertEqual(
            report["dangling"], [],
            "these entries name a source block the file does not define: "
            f"{report['dangling']}")

    def test_the_live_file_parses_into_the_declared_shape(self):
        mods, doc = _live()
        self.assertIsNone(doc["unreadable"], "tests/durations.json is not "
                                             "readable as JSON")
        self.assertFalse(doc["legacy"], "tests/durations.json is still in the "
                                        "pre-TASK-304 flat shape, which "
                                        "cannot carry provenance")
        self.assertEqual(doc["schema"], P.SCHEMA)
        self.assertEqual(sorted(doc["modules"]), sorted(set(mods) |
                                                        set(doc["modules"])))


class TestTheHintIsStillOnlyAHint(unittest.TestCase):
    """TASK-304 changed the file's SHAPE. It may not have changed its power.

    `tests/test_parallel_runner.py` holds "a hint may reorder the work, never
    select it" against the old shape. The same line is re-asserted here
    against the new one, because a richer file is exactly the kind of change
    that turns a sort key into a source of truth by accident.
    """

    def test_reading_the_new_shape_yields_only_a_sort_key(self):
        mods, doc = _live()
        got = P.schedule(mods, P.load_durations())
        self.assertEqual(sorted(got), sorted(mods))
        self.assertEqual(len(got), len(mods))

    def test_an_unmeasured_module_sorts_first_exactly_as_an_absent_one_did(self):
        """`sec: null` has to be worth precisely what omission was worth.

        If it were not, listing the seven unmentioned modules would have
        silently changed the schedule while claiming only to document it.
        """
        mods = ["test_known.py", "test_new.py"]
        listed = {"schema": 1, "sources": {"s": {"ref": "abc"}}, "legacy": False,
                  "unreadable": None,
                  "modules": {"test_known.py": {"sec": 900.0, "source": "s"},
                              "test_new.py": {"sec": None, "source": "s"}}}
        absent = {"test_known.py": 900.0}
        as_listed = {k: r["sec"] for k, r in listed["modules"].items()
                     if r["sec"] is not None}
        self.assertEqual(P.schedule(mods, as_listed),
                         P.schedule(mods, absent))
        self.assertEqual(P.schedule(mods, as_listed)[0], "test_new.py")

    def test_the_new_shape_survives_being_garbage(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "d.json"
            path.write_text('{"schema": 1, "modules": "not a dict"')
            doc = P.load_document(path)
            self.assertEqual(doc["modules"], {})
            self.assertIsNotNone(doc["unreadable"])

    def test_a_non_numeric_second_reads_as_unmeasured_not_as_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "d.json"
            path.write_text(json.dumps(
                {"schema": 1, "sources": {},
                 "modules": {"test_a.py": {"sec": "slow", "source": "s"}}}))
            doc = P.load_document(path)
            self.assertIsNone(doc["modules"]["test_a.py"]["sec"])

    def test_the_flat_pre_304_shape_is_still_readable(self):
        """An old file costs an order, not an outage — and reports as legacy."""
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "d.json"
            path.write_text(json.dumps({"test_a.py": 2.5}))
            doc = P.load_document(path)
            self.assertTrue(doc["legacy"])
            self.assertEqual(doc["modules"]["test_a.py"]["sec"], 2.5)
            self.assertIsNone(doc["modules"]["test_a.py"]["source"])


class TestStalenessIsDistinguishableFromCurrent(unittest.TestCase):
    """Defect 3: a figure taken where HEAD does not descend from is different.

    `ancestor` is injected, so these are about the verdict rather than about
    this checkout's history — which changes on every commit and would make the
    assertions describe the day they were written.
    """

    def _doc(self, ref):
        return {"schema": 1, "legacy": False, "unreadable": None,
                "sources": {"s": {"ref": ref}},
                "modules": {"test_a.py": {"sec": 1.0, "source": "s"}}}

    def test_merge_result_needs_both_existing_input_ancestors(self):
        doc = self._doc("a" * 40)
        doc["sources"]["s"].update(kind="merge-result", base="b" * 40,
                                   tree="c" * 40, tier="full")
        current = P.audit(["test_a.py"], doc, ancestor=lambda ref: True)
        self.assertEqual(len(current["current"]), 1)
        stale = P.audit(["test_a.py"], doc, ancestor=lambda ref: ref != "b" * 40)
        self.assertEqual(len(stale["stale"]), 1)
        self.assertEqual(stale["current"], [])

    def test_merge_result_requires_tree_and_full_or_slow_scope(self):
        doc = self._doc("a" * 40)
        doc["sources"]["s"].update(kind="merge-result", base="b" * 40,
                                   tree="not-a-tree", tier="full")
        report = P.audit(["test_a.py"], doc, ancestor=lambda ref: True)
        self.assertTrue(P.drift(report))
        doc["sources"]["s"].update(tree="c" * 40, tier="affected")
        report = P.audit(["test_a.py"], doc, ancestor=lambda ref: True)
        self.assertTrue(P.drift(report))

    def test_a_figure_at_an_ancestor_ref_is_current(self):
        r = P.audit(["test_a.py"], self._doc("abc"), ancestor=lambda ref: True)
        self.assertEqual(r["current"], [("test_a.py", "abc")])
        self.assertEqual(r["stale"], [])

    def test_a_figure_at_a_ref_head_does_not_descend_from_is_stale(self):
        r = P.audit(["test_a.py"], self._doc("abc"), ancestor=lambda ref: False)
        self.assertEqual(r["stale"], [("test_a.py", "abc")])
        self.assertEqual(r["current"], [])

    def test_a_ref_git_cannot_resolve_is_unverifiable_and_not_stale(self):
        """The third answer. Calling it stale because git was absent would be
        the same silent wrongness this module exists to remove."""
        r = P.audit(["test_a.py"], self._doc("abc"), ancestor=lambda ref: None)
        self.assertEqual(r["unverifiable"], [("test_a.py", "abc")])
        self.assertEqual(r["stale"], [])
        self.assertEqual(r["current"], [])

    def test_a_figure_whose_source_has_no_ref_is_unstamped(self):
        doc = self._doc(None)
        r = P.audit(["test_a.py"], doc, ancestor=lambda ref: True)
        self.assertEqual(r["unstamped"], ["test_a.py"])

    def test_the_ancestor_check_is_asked_once_per_ref_not_once_per_module(self):
        """108 subprocess calls to answer one question would be a real cost."""
        asked = []
        doc = {"schema": 1, "legacy": False, "unreadable": None,
               "sources": {"s": {"ref": "abc"}},
               "modules": {f"test_{i}.py": {"sec": 1.0, "source": "s"}
                           for i in range(20)}}
        P.audit(sorted(doc["modules"]), doc,
                ancestor=lambda ref: asked.append(ref) or True)
        self.assertEqual(asked, ["abc"])

    def test_the_real_ancestor_check_answers_for_this_checkout(self):
        """The injected verdicts above prove the reporting, not the plumbing.

        `git_ancestor` has to actually work, so: HEAD is an ancestor of
        itself, and a ref that cannot exist is unverifiable rather than an
        exception. Skipped where there is no git rather than failed.
        """
        head = P.head_ref()
        if head is None:
            self.skipTest("no git in this environment")
        self.assertIs(P.git_ancestor(head), True)
        self.assertIsNone(P.git_ancestor("0" * 40))


class TestTheReportNamesWhatIsWrong(unittest.TestCase):
    """A drift report that does not name the module is not actionable."""

    def _report(self, modules, on_disk, sources=None):
        doc = {"schema": 1, "legacy": False, "unreadable": None,
               "sources": sources if sources is not None else {"s": {"ref": "abc"}},
               "modules": modules}
        return P.audit(on_disk, doc, ancestor=lambda ref: True)

    def test_a_phantom_module_is_named_in_the_drift_lines(self):
        r = self._report({"test_gone.py": {"sec": 9.0, "source": "s"}},
                         ["test_a.py"])
        lines = "\n".join(P.drift(r))
        self.assertIn("test_gone.py", lines)
        self.assertIn("test_a.py", lines)

    def test_an_unlisted_module_is_named_in_the_drift_lines(self):
        r = self._report({}, ["test_a.py"])
        self.assertIn("test_a.py", "\n".join(P.drift(r)))

    def test_a_dangling_source_is_named_with_its_source_id(self):
        r = self._report({"test_a.py": {"sec": 1.0, "source": "nope"}},
                         ["test_a.py"], sources={})
        self.assertIn("nope", "\n".join(P.drift(r)))

    def test_a_clean_file_produces_no_drift_lines(self):
        """So the assertions above cannot pass by complaining about
        everything, which is how a check gets 'fixed' into uselessness."""
        r = self._report({"test_a.py": {"sec": 1.0, "source": "s"}},
                         ["test_a.py"])
        self.assertEqual(P.drift(r), [])
        self.assertIn("every module on disk is accounted for",
                      "\n".join(P.format_audit(r)))

    def test_a_drift_line_never_starts_with_the_runners_module_red_marker(self):
        """**A regression, and it was a real false signal.**

        `main()` prints `✗ {mod}` to mean "this module is RED". The first
        version of `drift()` produced `✗ {mod}: on disk, and …` for a module
        that had merely never been measured — the same marker, for a module
        that had passed.

        `tests/test_tree_guard.py` caught it: `TestThePlantedWrite` plants a
        new module into a copied repo, runs the suite narrowed to it, and
        asserts `✗ {planted module}` is absent because the plant is supposed
        to pass. A brand-new module is by definition not in `durations.json`,
        so the banner accused a passing module of failing.

        That test takes 160s and reaches this through two subprocesses. This
        one is the direct statement of the rule: no drift line may begin with
        a module name, so the runner's one marker keeps meaning one thing.
        """
        r = self._report({"test_gone.py": {"sec": 9.0, "source": "s"}},
                         ["test_planted.py"])
        lines = P.drift(r)
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertFalse(
                line.startswith(("test_", "tests/")),
                f"a drift line leads with a module name: {line!r} — printed "
                f"after main()'s '✗ ' prefix this is indistinguishable from "
                f"the marker that means the module FAILED")
        joined = "\n".join(P.format_audit(r))
        self.assertNotIn("✗ test_planted.py", joined)
        self.assertNotIn("✗ test_gone.py", joined)
        self.assertIn("test_planted.py", joined)   # still named, just not first

    def test_the_banner_states_the_counts_a_reader_needs(self):
        r = self._report({"test_a.py": {"sec": 1.0, "source": "s"},
                          "test_b.py": {"sec": None, "source": "s"}},
                         ["test_a.py", "test_b.py"])
        banner = "\n".join(P.format_audit(r))
        self.assertIn("2 recorded", banner)
        self.assertIn("2 on disk", banner)
        self.assertIn("1 unmeasured", banner)


class TestTheBannerIsWiredIntoMainAndNotJustDefined(unittest.TestCase):
    """`format_audit()` being right is not the same as anything calling it.

    **This is the shape TASK-284 was failed at V4 for**, and the shape a V4
    round already found once in `tests/parallel` itself: a guard with unit
    tests and no caller. So `main()` is driven directly, with `run_module`
    stubbed so no test actually runs, and the banner is asserted to appear in
    what it printed — without any flag being passed.
    """

    def _main(self, argv_extra=()):
        stub = {"rc": 0, "ran": 1, "sec": 0.1, "err": "",
                "ids": [("m.C.t0", "ok")]}
        old_run, old_argv = P.run_module, sys.argv
        P.run_module = lambda name: dict(stub, mod=name)
        sys.argv = ["parallel", "test_durations_provenance", *argv_extra]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = P.main()
        finally:
            P.run_module, sys.argv = old_run, old_argv
        return rc, buf.getvalue()

    def test_a_plain_run_with_no_flags_prints_the_durations_audit(self):
        rc, printed = self._main()
        self.assertEqual(rc, 0)
        self.assertIn("durations:", printed,
                      "main() ran without printing the durations audit — the "
                      "report exists and nothing invokes it, which is the "
                      "defect TASK-284 was failed for")
        self.assertIn("on disk", printed)

    def test_the_audit_covers_the_whole_tree_even_when_the_run_is_narrowed(self):
        """`--only` narrows which modules RUN. The file still describes all of
        them, so an audit scoped to the narrowed set would report six missing
        entries that are not missing, and hide any that are."""
        _, printed = self._main()
        on_disk = len([p for p in (ROOT / "tests").glob("test_*.py")])
        self.assertIn(f"{on_disk} on disk", printed)

    def test_the_audit_does_not_change_the_exit_status(self):
        """The runner may not become an outage over its own stopwatch. This
        module is what makes drift red; the banner only tells you."""
        rc, printed = self._main()
        self.assertEqual(rc, 0)
        self.assertIn("durations:", printed)


if __name__ == "__main__":
    unittest.main()
