"""Contract tests for work modes and the verification ladder — DESIGN-003.

The claim under test: **a project's shape is a declaration, and declaring
nothing must cost nothing.**

DESIGN-003 generalizes Perry past the software project by making shape a
property of a *track* rather than of the whole project. The risk that comes with
that is not subtle — every existing Perry project was written before tracks
existed, and a schema that requires the new structure would invalidate all of
them at once. So the design's goal 7 is explicit: absent a declaration,
everything is a single `project`-mode track and today's behavior is
bit-identical.

That property is what most of this file tests, and the mechanism that delivers
it is worth naming because it is easy to break later: **the new structure is
declared through `tables[]`, not through `headings[]`.** `bin/perry-lint`
treats every entry in `headings[]` as required, but skips a `tables[]` spec
whose section is absent (`if not bodies: continue`). So `## Tracks` in
`.perry/config.md` and `## Intake` in `BOARD.md` validate strictly when present
and cost nothing when absent. Moving either into `headings[]` would silently
turn an opt-in into a migration.

The second half tests that opting in is actually checked — a schema that
accepts `mode: kanban` or `rung: V9` is documentation, not a contract.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
LINT = PERRY_HOME / "bin" / "perry-lint"

MODES = ["project", "pipeline", "queue", "inquiry"]
RUNGS = ["V0", "V1", "V2", "V3", "V4", "V5", "V6"]


def file_spec(file_id: str) -> dict:
    for f in SCHEMA["files"]:
        if f["id"] == file_id:
            return f
    raise AssertionError(f"no files[] entry with id {file_id!r}")


def table_spec(file_id: str, under_fragment: str) -> dict | None:
    for t in file_spec(file_id).get("tables", []):
        if under_fragment in t["under"]:
            return t
    return None


def lint(root: Path) -> str:
    r = subprocess.run(
        ["python3", str(LINT), "--root", str(root)],
        capture_output=True, text=True,
    )
    return r.stdout + r.stderr


class TestEnums(unittest.TestCase):
    def test_mode_enum_is_exactly_the_four_shapes(self):
        """Decision 1 chose four over two or three. A fifth is a design
        revision, not a schema edit — mode determines spine, triage and default
        rung, so adding one silently would leave three of those undefined."""
        self.assertEqual(SCHEMA["enums"]["mode"], MODES)

    def test_verification_rungs_are_ordered_v0_to_v6(self):
        self.assertEqual(SCHEMA["enums"]["verification_rung"], RUNGS)

    def test_every_mode_declares_its_semantics(self):
        """A mode with no declared spine/closure/default rung is a label."""
        declared = SCHEMA["work_modes"]["modes"]
        self.assertEqual(sorted(declared), sorted(MODES))
        for name, m in declared.items():
            for field in ("ends_when", "unit", "spine", "calendar", "default_rung"):
                self.assertTrue(m.get(field), f"{name} is missing {field}")
            self.assertIn(m["default_rung"], RUNGS, f"{name} default_rung")

    def test_every_rung_is_documented(self):
        self.assertEqual(sorted(SCHEMA["verification"]["rungs"]), sorted(RUNGS))

    def test_calendar_is_binding_exactly_where_the_design_says(self):
        """`okr/SKILL.md § Why phases, not months` is right for project mode
        and wrong for the 33.4% — month-end close and a filing deadline ARE
        the calendar. DESIGN-003 §1.4 B1."""
        cal = {n: m["calendar"] for n, m in SCHEMA["work_modes"]["modes"].items()}
        self.assertEqual(cal["pipeline"], "binding")
        self.assertEqual(cal["queue"], "binding")
        self.assertEqual(cal["project"], "advisory")
        self.assertEqual(cal["inquiry"], "advisory")

    def test_default_track_is_project_mode(self):
        """Goal 7: declaring nothing reproduces today's Perry exactly."""
        self.assertEqual(SCHEMA["work_modes"]["default_mode"], "project")
        self.assertEqual(SCHEMA["work_modes"]["default_track"], "main")


class TestOptInIsFree(unittest.TestCase):
    """The new structure must be invisible to a project that never opts in."""

    def test_tracks_is_a_table_spec_not_a_required_heading(self):
        spec = file_spec("config")
        self.assertNotIn(
            "Tracks",
            json.dumps(spec.get("headings", [])),
            "## Tracks in headings[] would make it required and invalidate "
            "every pre-DESIGN-003 project",
        )
        self.assertIsNotNone(table_spec("config", "Tracks"))

    def test_intake_is_a_table_spec_not_a_required_heading(self):
        spec = file_spec("board")
        self.assertNotIn("Intake", json.dumps(spec.get("headings", [])))
        self.assertIsNotNone(table_spec("board", "Intake"))

    def test_track_and_verification_are_not_required_board_columns(self):
        """`bin/perry-lint` errors on any column in `columns[]` that a table
        lacks. Track and Verification are validated via enum_columns /
        optional_columns instead, which are skipped when the column is absent."""
        t = table_spec("board", "P[012]")
        self.assertNotIn("Track", t["columns"])
        self.assertNotIn("Verification", t["columns"])
        self.assertIn("Verification", t["enum_columns"])
        self.assertEqual(t["enum_columns"]["Verification"], "verification_rung")

    def test_design_003_adds_no_new_claimed_path(self):
        """Goal 5, tightened during `decide` from 'at most one' to zero.
        Intake lives inside BOARD.md, which claims[] already covers; tracks
        live inside .perry/, likewise. DESIGN-002's rule under pressure."""
        claimed = {c["path"] for c in SCHEMA["claims"]}
        self.assertIn("BOARD.md", claimed)
        self.assertIn(".perry/", claimed)
        for path in ("INTAKE.md", "TRACKS.md", "packs/", "modes/", "sources/"):
            self.assertNotIn(
                path, claimed,
                f"{path} would be a new claim on a namespace Perry was not given",
            )

    def test_shipped_fixtures_declare_no_tracks(self):
        """If a fixture opted in, the no-op guarantee would stop being tested
        by the rest of the suite."""
        for name in ("sample-project", "sample-project-zh"):
            cfg = PERRY_HOME / "tests" / "fixtures" / name / ".perry" / "config.md"
            if cfg.exists():
                self.assertNotIn("## Tracks", cfg.read_text())


class TestOptInIsChecked(unittest.TestCase):
    """Declaring a track must be validated, or the enum is decoration."""

    def _project(self, tracks_block: str) -> str:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n"
                "- Document language: English\n"
                "- Repo layout: single\n"
                "- State root: .\n"
                f"{tracks_block}"
            )
            return lint(root)

    HEADER = (
        "\n## Tracks\n\n"
        "| Track | Mode | Spine | Stages / SLA | Default rung |\n"
        "|---|---|---|---|---|\n"
    )

    def test_valid_tracks_lint_clean(self):
        out = self._project(
            self.HEADER
            + "| core | project | phase/ | — | V3 |\n"
            + "| docs | pipeline | commitments | draft→review→published | V5 |\n"
            + "| issues | queue | standing | 5-day SLA | V2 |\n"
            + "| why | inquiry | questions | — | V4 |\n"
        )
        self.assertNotIn("bad-enum", out)

    def test_unknown_mode_is_rejected(self):
        out = self._project(self.HEADER + "| issues | kanban | standing | — | V2 |\n")
        self.assertIn("bad-enum", out)
        self.assertIn("kanban", out)

    def test_unknown_rung_is_rejected(self):
        out = self._project(self.HEADER + "| core | project | phase/ | — | V9 |\n")
        self.assertIn("bad-enum", out)
        self.assertIn("V9", out)

    def test_missing_mode_column_is_rejected(self):
        out = self._project(
            "\n## Tracks\n\n| Track | Spine |\n|---|---|\n| core | phase/ |\n"
        )
        self.assertIn("table-columns", out)


class TestTrackParsing(unittest.TestCase):
    """`bin/perry-state` must never hand the router an empty track list.

    The router has no "no tracks declared" branch by design — every project
    reports at least the implicit `main` track — so an empty list here would
    turn into a silent no-mode-loaded session rather than a visible error.
    """

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "perry_state",
            importlib.machinery.SourceFileLoader(
                "perry_state", str(PERRY_HOME / "bin" / "perry-state")),
        )
        self.ps = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ps)

    def test_no_tracks_section_yields_the_implicit_main_track(self):
        got = self.ps.parse_tracks("# Perry configuration\n\n- Repo layout: single\n")
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["track"], "main")
        self.assertEqual(got[0]["mode"], "project")
        self.assertFalse(got[0]["declared"])

    def test_declared_tracks_are_parsed_in_order(self):
        got = self.ps.parse_tracks(
            "## Tracks\n\n"
            "| Track | Mode | Spine | Stages / SLA | Default rung |\n"
            "|---|---|---|---|---|\n"
            "| core | project | phase/ | — | V3 |\n"
            "| docs | pipeline | commitments | draft→review | V5 |\n"
        )
        self.assertEqual([t["track"] for t in got], ["core", "docs"])
        self.assertEqual([t["mode"] for t in got], ["project", "pipeline"])
        self.assertEqual(got[1]["default_rung"], "V5")
        self.assertTrue(all(t["declared"] for t in got))

    def test_an_empty_tracks_table_still_yields_the_default(self):
        got = self.ps.parse_tracks(
            "## Tracks\n\n| Track | Mode |\n|---|---|\n"
        )
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["track"], "main")

    def test_a_later_section_does_not_bleed_into_tracks(self):
        got = self.ps.parse_tracks(
            "## Tracks\n\n"
            "| Track | Mode |\n|---|---|\n| core | project |\n\n"
            "## Why the state root is not `.`\n\n"
            "| Not | A track |\n|---|---|\n| x | y |\n"
        )
        self.assertEqual([t["track"] for t in got], ["core"])

    def test_chinese_tracks_heading_is_recognized(self):
        got = self.ps.parse_tracks(
            "## 轨道\n\n| 轨道 | 模式 |\n|---|---|\n| core | queue |\n"
        )
        self.assertEqual(got[0]["track"], "core")
        self.assertEqual(got[0]["mode"], "queue")


class TestI18n(unittest.TestCase):
    def test_new_columns_have_a_chinese_alias(self):
        """A column with no glossary entry silently zeroes its dashboard row in
        a Chinese project — `reference/i18n.md`."""
        cols = SCHEMA["i18n"]["columns"]
        for name in ("Track", "Mode", "Verification", "Default rung",
                     "Arrived", "Request"):
            self.assertIn(name, cols, f"{name} missing from i18n.columns")
            self.assertTrue(cols[name].get("zh"))

    def test_track_section_headers_accept_chinese(self):
        self.assertIn("轨道", table_spec("config", "Tracks")["under"])
        self.assertIn("收件", table_spec("board", "Intake")["under"])


if __name__ == "__main__":
    unittest.main()
