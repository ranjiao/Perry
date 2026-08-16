"""`bin/perry-goals list --json` — DESIGN-005 step 2, `perry-goals/list/1.0`.

The third read contract, and the last one a front-end needs before it can show
a whole project without opening a markdown file.

The tool composes `viewer/parsers.py § load_snapshot` and parses nothing of its
own. That is the point rather than a shortcut: a second parser of one file is
the defect this project has hit twice, most recently when `perry-task` placed
board cells by resolved header name while `viewer/parsers.py` read them by
position, and a board with one extra column reported every task's owner as its
track with the linter calling it clean.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME") or Path(__file__).resolve().parent.parent)
TOOL = PERRY_HOME / "bin" / "perry-goals"
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "sample-project"


def run(root: Path, *argv) -> tuple[int, dict | str]:
    r = subprocess.run(
        ["python3", str(TOOL), "list", *argv, "--root", str(root), "--json"],
        capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return r.returncode, r.stdout + r.stderr


class TestShape(unittest.TestCase):

    TOP = {"contract", "project_root", "state_root", "conformance",
           "okr", "phase", "krs", "linkage", "counts"}
    KR = {"id", "level", "objective", "text", "metric", "qualifier",
          "linked_to", "stretch", "target", "current", "progress", "tasks"}
    CONF = {"okr_present", "phase_present", "linkage_present",
            "krs_without_metric", "krs_without_progress",
            "krs_not_in_linkage", "duplicate_kr_ids"}

    def test_the_shape_is_exact(self):
        code, d = run(FIXTURE)
        self.assertEqual(code, 0, d)
        self.assertEqual(set(d), self.TOP)
        self.assertEqual(set(d["conformance"]), self.CONF)

    def test_every_kr_carries_every_key(self):
        _, d = run(FIXTURE)
        self.assertTrue(d["krs"])
        for k in d["krs"]:
            self.assertEqual(set(k), self.KR,
                             f"{k.get('id')}: missing {self.KR - set(k)}")

    def test_version_handle(self):
        _, d = run(FIXTURE)
        self.assertTrue(d["contract"].startswith("perry-goals/list/1."))

    def test_level_filter(self):
        _, d = run(FIXTURE, "--level", "phase")
        self.assertTrue(d["krs"])
        self.assertEqual({k["level"] for k in d["krs"]}, {"phase"})

    def test_a_bad_level_is_refused(self):
        code, out = run(FIXTURE, "--level", "nonesuch")
        self.assertEqual(code, 1)
        self.assertIn("nonesuch", str(out))


class TestDerivedFieldsAreReallyDerived(unittest.TestCase):
    """The trap that caught this tool during its own first run.

    `present`, `day` and `kr_total` are NOT fields on the parser dataclasses —
    `perry-state` computes them in its own builder. Reading them as
    `getattr(okr, "present", False)` returns the default on *every* project and
    reports nothing: a live OKR with five objectives came back
    `okr_present: false`, and the payload looked entirely well-formed.

    A defaulted `getattr` on a field that does not exist is a silent wrong
    answer, which is the shape every review round of this project has found.
    These tests assert the values are real rather than defaults.
    """

    def test_a_project_with_an_okr_reports_it_present(self):
        _, d = run(FIXTURE)
        self.assertTrue(d["okr"]["present"])
        self.assertTrue(d["conformance"]["okr_present"])
        self.assertTrue(d["okr"]["version"], "version came back empty")
        self.assertTrue(d["okr"]["mission"], "mission came back empty")

    def test_phase_day_is_computed_from_started_not_defaulted(self):
        _, d = run(FIXTURE)
        ph = d["phase"]
        self.assertIsNotNone(ph)
        self.assertIsInstance(ph["day"], int)
        self.assertGreater(ph["day"], 0,
                           "phase day is 0 or None — the `started` date was "
                           "not read, or the field does not exist")

    def test_kr_total_matches_the_krs_actually_listed(self):
        _, d = run(FIXTURE)
        phase_krs = [k for k in d["krs"] if k["level"] == "phase"]
        self.assertEqual(d["phase"]["kr_total"], len(phase_krs),
                         "the phase's KR count and its KR list disagree")

    def test_no_field_in_the_payload_is_silently_absent(self):
        """Every declared key present on every project state, including the
        one with nothing in it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n- State root: .\n")
            code, d = run(root)
            self.assertEqual(code, 0, d)
            self.assertEqual(set(d), TestShape.TOP)
            self.assertFalse(d["okr"]["present"])
            self.assertIsNone(d["phase"])
            self.assertEqual(d["krs"], [])
            self.assertEqual(d["counts"]["krs"], 0)


class TestRealProjectShapes(unittest.TestCase):
    """A project's goals file is prose a human argues with, and it drifts.

    Measured on a live Perry project: KR ids of three different conventions in
    one file (`KR6`, `KR-G1`, `KR1`), the same id used twice at the same level,
    a status written in Chinese, and not one KR carrying a metric the parser
    recognizes. None of that is an error and all of it must be reportable.
    """

    def okr_project(self, body: str) -> Path:
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n")
        (root / "OKR.md").write_text(body)
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        return root

    # The real `OKR.md` shape: a `## vN: <date>` version heading, `### Objective
    # N — <title>`, and a five-column KR table. A live project reuses ids across
    # objectives exactly like this.
    OKR = """# OKR — Duplicate ids

## Mission

Ship the thing.

---

## v3: 2026-01-01

### Objective 1 — First objective

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR1 | Do the thing | count = 3 | no | 2026-09-01 |

### Objective 2 — Second objective

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| KR1 | Same id, different objective | count = 4 | no | 2026-09-01 |
"""

    def test_a_duplicate_kr_id_is_reported_rather_than_collapsed(self):
        """A front-end cannot key by id when the file reuses one. Silently
        de-duplicating would drop a KR the user wrote; silently keying by it
        would render one row twice."""
        _, d = run(self.okr_project(self.OKR))
        self.assertEqual(d["conformance"]["duplicate_kr_ids"], ["KR1"])
        self.assertEqual(len([k for k in d["krs"] if k["id"] == "KR1"]), 2,
                         "a duplicate id was collapsed, losing a KR")

    def test_krs_with_no_measurable_progress_are_named(self):
        """Without a linkage register there is no target and no current, so
        progress is `null` — not zero. A front-end rendering 0% would be
        asserting no progress on work it knows nothing about."""
        _, d = run(self.okr_project(self.OKR))
        self.assertTrue(d["krs"])
        for k in d["krs"]:
            self.assertIsNone(k["progress"])
        self.assertEqual(sorted(set(d["conformance"]["krs_without_progress"])),
                         ["KR1"])
        self.assertFalse(d["conformance"]["linkage_present"])


class TestContractDocAgrees(unittest.TestCase):

    def test_the_document_lists_exactly_the_keys_emitted(self):
        doc = (PERRY_HOME / "schema" / "goals-list-contract.md").read_text()
        _, d = run(FIXTURE)
        self.assertIn(d["contract"], doc, "the doc names a different version")
        documented = set(__import__("re").findall(r"^\| `(\w+)` \|", doc, 8))
        known = TestShape.KR | TestShape.CONF | {
            "contract", "project_root", "state_root", "okr", "phase", "krs",
            "linkage", "counts", "present", "version", "mission",
            "operating_principles", "anti_goals", "objectives", "number",
            "slug", "status", "started", "day", "kr_total", "cost_ceiling",
            "updated", "error", "phase"}
        undocumented = (TestShape.KR | TestShape.CONF) - documented
        self.assertFalse(undocumented,
                         f"payload keys with no row in the contract doc: "
                         f"{sorted(undocumented)}")
        phantom = documented - known
        self.assertFalse(phantom,
                         f"the doc documents keys the payload never emits: "
                         f"{sorted(phantom)}")


if __name__ == "__main__":
    unittest.main()
