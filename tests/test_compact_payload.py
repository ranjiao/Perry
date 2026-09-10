"""DESIGN-016 B1 — `perry-state --compact` is a projection, and it carries the vocabulary.

`SKILL.md` step 3 mandated `perry-state --json`. That payload was 186,856
bytes when DESIGN-016 was written and 258,981 five days later, of which
`board.tasks` is 159KB — and the standup reads counts, not rows. The bill this
sits against is 99.1% `cache_read`, so the cost is the payload times every turn
after it.

Two claims, and the second is the one that keeps `--compact` from becoming a
second answer to "what is the state":

- **It carries what the standup and the writers need** — the dashboard's
  numbers, and the project's VOCABULARY: which tracks are declared, what mode
  each is, which stages are legal on it (DESIGN-016 § 1.7). That last read used
  to cost `--section project`, 11,681 bytes, three levels down.
- **Every value in it is the full payload's own.** `perry-state § COMPACT` is
  the projection declared once; `project_compact` walks it and so does this
  module. A field added to the spec is asserted here without editing this file,
  and a field computed rather than projected fails.

Run: python3 tests/parallel -j 4 test_compact_payload
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(PERRY_HOME / "tests"))

import inproc  # noqa: E402
from task_writer_support import Project  # noqa: E402

STATE = inproc.load("perry-state")


def payloads(root: Path) -> tuple[dict, dict]:
    full = json.loads(inproc.run("perry-state", ["--root", str(root), "--json"]).stdout)
    narrow = json.loads(inproc.run("perry-state", ["--root", str(root), "--compact"]).stdout)
    return full, narrow


class TestItIsAProjectionAndNothingElse(unittest.TestCase):
    """Walk the spec: every value in the narrow payload is the full one's."""

    @classmethod
    def setUpClass(cls):
        cls.p = Project()
        cls.p.run("add", "--title", "a row to count")
        cls.full, cls.narrow = payloads(cls.p.root)

    def _narrow_at(self, key: str):
        cur = self.narrow
        for step in key.split("."):
            self.assertIsInstance(cur, dict, f"{key} is not reachable")
            self.assertIn(step, cur, f"{key} is missing from --compact")
            cur = cur[step]
        return cur

    #: `generated_at` is `datetime.now()` inside each invocation, and this
    #: class makes two — so a run that straddles a second boundary compared two
    #: honest stamps and failed. Measured at about 17 ms apart on an empty
    #: project, which is ~1.7% of runs and worse under eight workers; it fired
    #: once in six suite runs during a V4 review. Excluded here and asserted
    #: for its SHAPE below, which is the claim that can be made about a clock.
    CLOCK = ("generated_at",)

    def test_the_clock_exclusion_holds_exactly_one_name(self):
        """`CLOCK` is the one place this file may skip a declared field, so it
        is bounded here rather than trusted.

        A second name added to it drops that field out of BOTH projection
        walks, silently and with every test still green. A clock is the only
        thing that can honestly be excluded from a value comparison; anything
        else added here is a field going untested, and a round found the
        exclusion mechanism before it found a second name in it.
        """
        self.assertEqual(self.CLOCK, ("generated_at",))

    def test_every_declared_field_matches_the_full_payload(self):
        """The projection is applied to the FULL payload here and compared to
        what the tool emitted.

        **This one cannot see a defect INSIDE `project_value`, and that is on
        purpose now rather than by accident.** It calls the function under
        test to build its own expectation, so it asserts `f(x) == f(x)`: what
        it pins is that the tool RAN the projection over the declared fields,
        not that the projection is right. A V4 reviewer proved the gap by
        adding 1 to every integer `project_value` returns and watching all
        3,440 tests stay green while `--compact` reported a board of 239 lines
        against `--json`'s 238.

        The rule itself is checked by `test_the_six_kinds_are_checked_against_a
        _second_opinion` below, which reimplements the six kinds by hand. The
        split is deliberate: the FIELD LIST stays single-sourced from
        `STATE.COMPACT`, so the two files cannot disagree about which fields
        exist, while the RULE gets an independent second author.
        """
        for key, path, how in STATE.COMPACT:
            if key in self.CLOCK:
                continue
            with self.subTest(field=key):
                self.assertEqual(
                    self._narrow_at(key),
                    STATE.project_value(STATE._at(self.full, path), how))

    @staticmethod
    def _second_opinion(value, how):
        """The six projection kinds, written again and deliberately not shared.

        Reimplemented from `DESIGN-016 § 1.7` and the `COMPACT` declaration,
        not from `bin/perry-state § project_value`. If this ever imports that
        function, the test below becomes the tautology it exists to replace.
        """
        if how == "value":
            return value
        if how == "count":
            if isinstance(value, list):
                return len(value)
            if isinstance(value, dict):
                return len(value)
            return None
        kind, arg = how
        if kind == "fields":
            if not isinstance(value, list):
                return None
            out = []
            for item in value:
                if isinstance(item, dict):
                    out.append({name: item.get(name) for name in arg})
            return out
        if kind in ("objectives", "objectives_with_progress"):
            if not isinstance(value, list):
                return None
            out = []
            for o in value:
                if not isinstance(o, dict):
                    continue
                row = {"title": o.get("title")}
                if kind == "objectives_with_progress":
                    row = {"id": o.get("id"), "title": o.get("title")}
                krs = o.get("krs")
                row["krs"] = [{name: kr.get(name) for name in arg}
                              for kr in (krs if krs else [])]
                out.append(row)
            return out
        if kind == "fields_of_dict":
            if not isinstance(value, dict):
                return None
            return {name: value.get(name) for name in arg}
        if kind == "subdict":
            if not isinstance(value, dict):
                return None
            return {k: TestItIsAProjectionAndNothingElse._second_opinion(
                STATE._at(value, path), sub) for k, path, sub in arg}
        raise ValueError(f"unknown projection {how!r}")

    def test_the_six_kinds_are_checked_against_a_second_opinion(self):
        """Every declared field, projected by a body this file owns.

        The population is `STATE.COMPACT`, and every one of its `how` values
        must be reachable here — an unknown kind raises rather than passing,
        so a seventh projection added to the tool fails this until somebody
        writes it down twice.
        """
        for key, path, how in STATE.COMPACT:
            if key in self.CLOCK:
                continue
            with self.subTest(field=key):
                want = self._second_opinion(STATE._at(self.full, path), how)
                self.assertEqual(self._narrow_at(key), want)

    def test_the_clock_field_is_projected_like_everything_else(self):
        """**One invocation, so the clock is deterministic.**

        The first fix for the flake excluded `generated_at` from the walk and
        left a case whose body called `datetime.fromisoformat` and asserted
        NOTHING — a hard-coded `"2020-01-01T00:00:00"` would have passed it,
        and `--compact`'s stamp stopped being compared with `--json`'s at all.
        A V4 review found that. The flake came from making two invocations;
        projecting the full payload in-process makes one.
        """
        from datetime import datetime
        projected = STATE.project_compact(self.full)
        self.assertEqual(projected["generated_at"], self.full["generated_at"],
                         "the projection did not carry the stamp verbatim")
        datetime.fromisoformat(self.narrow["generated_at"])
        self.assertNotEqual(self.narrow["generated_at"], "",
                            "the tool emitted an empty stamp")

    def test_a_scalar_is_carried_verbatim_and_a_list_is_counted(self):
        """The control: the case above passes if `project_value` is the
        identity, so at least one field of each kind is checked by hand."""
        self.assertEqual(self.narrow["project"]["name"],
                         self.full["project"]["name"])
        self.assertEqual(self.narrow["board"]["tasks"],
                         len(self.full["board"]["tasks"]))
        self.assertNotEqual(self.narrow["board"]["tasks"],
                            self.full["board"]["tasks"])

    def test_the_spec_reaches_something_in_a_real_payload(self):
        """The control: a spec of paths that all resolve to `None` would pass
        every case above and say nothing."""
        live = [k for k, path, _ in STATE.COMPACT
                if STATE._at(self.full, path) is not None]
        # **A floor, not a half.** `> len(COMPACT) // 2` let up to 22 of the
        # 53 declared paths start resolving to None — a key renamed in
        # `build()` — with both walks still agreeing, because both fetch the
        # source with `STATE._at(self.full, path)` and both would get None.
        # 48 resolve on this fixture; the 5 that do not are the phase and
        # linkage paths a scratch project has no data for, and they are named
        # so a sixth cannot join them quietly.
        self.assertGreaterEqual(len(live), 48,
                                "declared paths stopped resolving")
        dark = {k for k, path, _h in STATE.COMPACT
                if STATE._at(self.full, path) is None}
        self.assertEqual(
            dark, {"phase", "linkage.phase", "linkage.objectives",
                   "linkage.unlinked", "risks.top"},
            "a declared path resolved to nothing on a fresh project, and this "
            "file's synthetic cases are the only evidence for its kind")

    def test_it_holds_no_key_the_spec_did_not_declare(self):
        """Every path, not just the top-level name.

        This compared `k.split(".")[0]`, so a key emitted under `board.`,
        `project.` or `risks.` that the declaration never names was invisible:
        the parent was declared, and the parent was all it looked at.
        """
        def paths(node, prefix=""):
            if not isinstance(node, dict):
                return {prefix}
            out = set()
            for k, v in node.items():
                out |= paths(v, f"{prefix}.{k}" if prefix else k)
            return out

        declared = {k for k, _p, _h in STATE.COMPACT}
        # A declared key whose value is itself a dict — `subdict`, or a scalar
        # that happens to be an object — owns everything under it; the walk
        # stops there rather than descending into data the spec did not shape.
        emitted = set()
        for key in self.narrow:
            if key in declared:
                emitted.add(key)
                continue
            emitted |= {p for p in paths(self.narrow[key], key)}
        undeclared = {p for p in emitted
                      if p not in declared
                      and not any(p.startswith(d + ".") for d in declared)}
        self.assertEqual(undeclared, set(),
                         "--compact emits a key the declaration does not name")


class TestItCarriesTheVocabulary(unittest.TestCase):
    """What a caller needs before writing a row (DESIGN-016 § 1.7)."""

    def setUp(self):
        import config_store
        self.p = Project(tracks=[
            config_store.track("main", "project"),
            config_store.track("intake", "queue",
                               stages="new→triaged→done", wip="6", sla="5d"),
        ])
        _full, self.narrow = payloads(self.p.root)

    def test_every_declared_track_is_named_with_its_mode(self):
        tracks = {t["track"]: t for t in self.narrow["project"]["tracks"]}
        self.assertEqual(set(tracks), {"main", "intake"})
        self.assertEqual(tracks["intake"]["mode"], "queue")

    def test_the_stages_legal_on_a_track_are_in_it(self):
        tracks = {t["track"]: t for t in self.narrow["project"]["tracks"]}
        self.assertEqual(tracks["intake"]["stage_list"],
                         ["new", "triaged", "done"])
        self.assertTrue(tracks["intake"]["stages_declared"])

    def test_the_diagnosis_of_a_track_is_not_in_it(self):
        """`stage_counts` and the breach lists belong to `--section project`;
        this payload is the vocabulary, not the verdict."""
        for track in self.narrow["project"]["tracks"]:
            self.assertNotIn("sla_check", track)
            self.assertNotIn("wip_breaches", track)


class TestTheStandupCanActuallyRenderFromIt(unittest.TestCase):
    """Completeness, named by hand — the other direction from the projection
    test above, and the one that was missing.

    Every case in this module walks `COMPACT`, so deleting an entry deletes its
    own assertion: a V4 review dropped `project.packs` from the spec and the
    whole suite stayed green, and that is the structural reason `linkage` — the
    only machine-readable KR progress, which `reference/snapshot.md` step 4
    renders a percentage from — was missing from the first `--compact` and
    nothing said so. This list is written out, so removing a field from the
    spec reddens here.
    """

    @classmethod
    def setUpClass(cls):
        cls.p = Project()
        cls.p.run("add", "--title", "a row for the dashboard to count")
        _full, cls.narrow = payloads(cls.p.root)

    #: `(dotted path, which step of `reference/snapshot.md` reads it)`.
    NEEDED = (
        ("project.name", "step 4, the header"),
        ("project.tracks", "step 3b, one mode file per distinct mode"),
        ("project.packs", "step 3c, the display glossary"),
        ("okr.present", "step 4, the OKR line"),
        ("okr.version", "step 4, the OKR line"),
        ("okr.objectives", "step 4, one line per objective"),
        ("linkage.objectives", "step 4, <%> and <KRs done>/<KRs total>"),
        ("phase", "step 4, the phase line"),
        ("board.p0", "step 4, open tasks"),
        ("board.p1", "step 4, open tasks"),
        ("board.p2", "step 4, open tasks"),
        ("board.blocked", "step 4, open tasks"),
        ("user_input_queue", "step 4, the User Input Q line"),
        ("risks.top", "step 4, the top risk"),
        ("decisions", "step 4, the last decision"),
        ("history", "step 4, last weekly and last handoff"),
        ("installed", "step 3, the first-time-setup branch"),
        ("recovery", "step 2, the recovery hazard"),
        ("interrupted", "step 2, the interrupted-run gate"),
    )

    def _at(self, path: str):
        cur = self.narrow
        for step in path.split("."):
            self.assertIsInstance(cur, dict, f"{path}: {step} is not reachable")
            self.assertIn(step, cur, f"{path} is missing from --compact")
            cur = cur[step]
        return cur

    def test_every_field_the_standup_reads_is_present(self):
        for path, why in self.NEEDED:
            with self.subTest(field=path, read_by=why):
                self._at(path)

    def test_a_kr_carries_a_number_to_render_a_percentage_from(self):
        """`linkage.objectives[].krs[]` must carry `current` and `target`;
        `attribution.kr_currents` is a roll-up over the phase and cannot answer
        per objective."""
        objectives = self.narrow["linkage"]["objectives"]
        if not objectives:
            self.skipTest("the fixture project declares no phase KRs")
        for kr in objectives[0]["krs"]:
            self.assertIn("current", kr)
            self.assertIn("target", kr)


class TestItIsSmallerByTheOrderOfMagnitudeThatWasThePoint(unittest.TestCase):

    def setUp(self):
        self.p = Project()
        for n in range(12):
            self.p.run("add", "--title", f"a row that makes the board big {n}")
        self.full_text = inproc.run(
            "perry-state", ["--root", str(self.p.root), "--json"]).stdout
        self.narrow_text = inproc.run(
            "perry-state", ["--root", str(self.p.root), "--compact"]).stdout

    def test_it_is_a_small_fraction_of_the_full_payload(self):
        self.assertLess(len(self.narrow_text), len(self.full_text) / 3,
                        f"compact {len(self.narrow_text)} vs full "
                        f"{len(self.full_text)} bytes")

    def test_it_does_not_grow_with_the_board(self):
        """The property that makes it a standup read: task ROWS are counted,
        not carried, so twelve more of them cost one integer."""
        before = len(self.narrow_text)
        for n in range(12):
            self.p.run("add", "--title", f"another row on the same board {n}")
        after = len(inproc.run(
            "perry-state", ["--root", str(self.p.root), "--compact"]).stdout)
        self.assertLess(after - before, 200,
                        f"twelve rows added {after - before} bytes")

    def test_the_row_count_is_still_reported(self):
        """The control for the case above: counted, not dropped."""
        narrow = json.loads(self.narrow_text)
        self.assertEqual(narrow["board"]["tasks"],
                         len(json.loads(self.full_text)["board"]["tasks"]))


class TestTheTwoNarrowingsDoNotCombine(unittest.TestCase):

    def test_compact_with_section_is_refused(self):
        p = Project()
        out = inproc.run("perry-state",
                         ["--root", str(p.root), "--compact", "--section", "board"])
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("--compact", out.stderr)


class TestAProjectWithNoStateStillAnswers(unittest.TestCase):

    def test_installed_false_survives_the_projection(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = inproc.run("perry-state", ["--root", td, "--compact"])
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertFalse(json.loads(out.stdout)["installed"])


class TestEveryProjectionKindIsFedDataThatDistinguishesIt(unittest.TestCase):
    """The rule itself, on synthetic values, independent of any project.

    **Why this is not redundant with the class above.** That one runs against
    `Project()` — a scratch project with no phase and no linkage — so three of
    the declared kinds (`objectives_with_progress`, `objectives`, `subdict`)
    receive `None` or an empty list and every implementation of them agrees.
    A V4 reviewer made `objectives_with_progress` put each KR's `target` into
    its `current` slot, watched the live project report a key result at 100%
    that is actually at 43%, and watched all 3,440 tests stay green. The
    projection was not untested; it was tested on data that could not tell.

    So each kind is fed a value built to distinguish it: counts get a list
    whose length differs from its contents, field-pickers get an extra key
    that must be dropped, and `current`/`target` are given DIFFERENT numbers,
    which is the exact discrimination the live board happened not to make in
    five of its six key results.
    """

    #: One synthetic input per kind, and what a correct projection returns.
    #: Written from the declaration, not from `project_value`.
    #:
    #: **Every collection here holds MORE THAN ONE element, and that is the
    #: point.** The first version of this dict gave each kind one objective,
    #: one key result and two scalar `subdict` children. A V4 round appended
    #: `[:1]` to the KR comprehension and to the objective comprehension and
    #: the whole suite stayed green — `--compact` reported ONE key result per
    #: phase objective where `--json` reported two on
    #: `tests/fixtures/sample-project` and three on this project, and
    #: `reference/snapshot.md` step 4 renders `<KRs done>/<KRs total>` from
    #: exactly that list. A projection tested at cardinality one cannot tell a
    #: correct implementation from one that keeps only the first of anything,
    #: which is the same defect the class above was written to fix, one level
    #: up: the rule had a second author and the data could not tell.
    CASES = {
        "value": (7, 7),
        "count": ([10, 20, 30], 3),
        ("fields", ("a", "b")): (
            [{"a": 1, "b": 2, "drop": 3}, {"a": 4, "b": 5, "drop": 6}],
            [{"a": 1, "b": 2}, {"a": 4, "b": 5}]),
        ("fields_of_dict", ("a", "b")): (
            {"a": 1, "b": 2, "drop": 3}, {"a": 1, "b": 2}),
        ("objectives", ("id", "current", "target")): (
            [{"title": "T1", "drop": "x",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0, "drop": "x"},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}],
            [{"title": "T1",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}]),
        ("objectives_with_progress", ("id", "current", "target")): (
            [{"id": "O1", "title": "T1", "drop": "x",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0, "drop": "x"},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"id": "O2", "title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}],
            [{"id": "O1", "title": "T1",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"id": "O2", "title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}]),
    }

    def test_each_kind_maps_its_input_to_the_declared_output(self):
        for how, (given, want) in self.CASES.items():
            with self.subTest(kind=how if isinstance(how, str) else how[0]):
                self.assertEqual(STATE.project_value(given, how), want)
                self.assertEqual(
                    TestItIsAProjectionAndNothingElse._second_opinion(
                        given, how), want)

    def test_no_collection_in_the_cases_has_one_element(self):
        """The anti-vacuity control for the control.

        Without this, the fix for a cardinality finding is to add a second
        element once and let the next author drop it back. Every list-shaped
        input above must hold at least two, and at least one nested list must
        too, or the cases stop being able to see a projection that keeps only
        the first of anything.
        """
        nested = 0
        for how, (given, _) in self.CASES.items():
            if not isinstance(given, list):
                continue
            with self.subTest(kind=how if isinstance(how, str) else how[0]):
                self.assertGreaterEqual(len(given), 2, "one element cannot tell")
            for item in given:
                if isinstance(item, dict) and len(item.get("krs", ())) >= 2:
                    nested += 1
        self.assertGreaterEqual(
            nested, 2, "no case nests a collection of two, so a projection "
                       "that keeps only the first KR would pass")

    def test_the_nested_kind_carries_its_children(self):
        """`subdict`, with a COMPOSITE child.

        Both children used to be scalar kinds, so a `subdict` that stopped
        projecting its children and carried them verbatim was green: a scalar
        projected is a scalar carried. The `krs` child below is the whole point
        — it must come back narrowed, and it cannot if the recursion is gone.
        """
        how = ("subdict", (("n", "inner.n", "value"),
                           ("c", "inner.items", "count"),
                           ("o", "inner.objs",
                            ("objectives", ("id", "current")))))
        given = {"inner": {"n": 4, "items": ["a", "b"],
                           "objs": [{"title": "T", "drop": "x",
                                     "krs": [{"id": "K1", "current": 1.0,
                                              "drop": "x"},
                                             {"id": "K2", "current": 2.0}]}]}}
        want = {"n": 4, "c": 2,
                "o": [{"title": "T", "krs": [{"id": "K1", "current": 1.0},
                                             {"id": "K2", "current": 2.0}]}]}
        self.assertEqual(STATE.project_value(given, how), want)
        self.assertEqual(
            TestItIsAProjectionAndNothingElse._second_opinion(given, how),
            want)

    def test_every_kind_the_declaration_uses_has_a_case_here(self):
        """The bound. A seventh projection fails this until it is written twice."""
        declared = {h if isinstance(h, str) else h[0] for _, _, h in STATE.COMPACT}
        covered = {h if isinstance(h, str) else h[0] for h in self.CASES}
        covered.add("subdict")
        self.assertEqual(declared - covered, set(),
                         "a projection kind reached the tool and not this file")

    def test_a_wrong_projection_is_visible_here(self):
        """The anti-vacuity control: the cases can tell right from wrong.

        Each assertion above would pass against an identity function if the
        inputs and outputs were equal. They are not, and this says so —
        except for `value`, which IS the identity and is the one kind whose
        input must equal its output.
        """
        for how, (given, want) in self.CASES.items():
            if how == "value":
                self.assertEqual(given, want, "`value` is the identity")
                continue
            with self.subTest(kind=how if isinstance(how, str) else how[0]):
                self.assertNotEqual(given, want)


if __name__ == "__main__":
    unittest.main()
