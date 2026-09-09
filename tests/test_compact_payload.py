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

    def test_every_declared_field_matches_the_full_payload(self):
        """The projection is applied to the FULL payload here and compared to
        what the tool emitted. Restating the rules in this file would let the
        two drift into agreeing about different things."""
        for key, path, how in STATE.COMPACT:
            if key in self.CLOCK:
                continue
            with self.subTest(field=key):
                self.assertEqual(
                    self._narrow_at(key),
                    STATE.project_value(STATE._at(self.full, path), how))

    def test_the_clock_field_is_a_stamp_of_its_own_run(self):
        """What is true of `generated_at` across two invocations: both are ISO
        timestamps of the moment each ran, not the same string."""
        from datetime import datetime
        for payload in (self.full, self.narrow):
            datetime.fromisoformat(payload["generated_at"])

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
        self.assertGreater(len(live), len(STATE.COMPACT) // 2,
                           "most of the spec resolved to nothing")

    def test_it_holds_no_key_the_spec_did_not_declare(self):
        declared = {k.split(".")[0] for k, _p, _h in STATE.COMPACT}
        self.assertEqual(set(self.narrow) - declared, set())


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


if __name__ == "__main__":
    unittest.main()
