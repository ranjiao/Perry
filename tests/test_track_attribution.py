"""Evidence belongs to the track that produced it, not to whichever is first.

`bin/perry-diagnose` used `len(tracks) == 1` as a proxy for **"no register
exists"**. It is also true when the register **declares exactly one track** —
and then every board row, every commitment row and every project-wide file was
scored as that track's, ignoring the `Track` column the scanner already reads
and ignoring `schema/state-schema.json`'s own rule that a blank `Track` means
the implicit `main` track.

A project declaring one `pipeline` track with its ordinary work in untracked
rows scored `project 7 / pipeline 4` and got a `MODE-01` warn **telling the
user to change a `Mode` cell that was correct**, citing objectives and rows
that are not that track's. `perry-lint` accepted the shape and no test covered
it.

Found by a reviewer that had already fixed attribution across *modes* and then
asked whether attribution across *tracks* had ever been examined. It had not.

Run: python3 tests/parallel test_track_attribution
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-diagnose"

BOARD = """# Board

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification | Track | Stage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | ordinary work | C | not_started | — | — | V2 |  |  |
| TASK-002 | more of it | C | not_started | — | — | V2 |  |  |
| TASK-003 | a pipeline item | C | not_started | — | — | V2 | ops | draft |
"""

REGISTER = """# Config

State root: perry

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| ops | pipeline | OKR.md | brief,draft | — | 3d | — | V2 |
"""


class TrackCase(unittest.TestCase):
    def project(self, register: str | None):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "perry").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text(
            register if register else "# Config\n\nState root: perry\n")
        (d / "perry" / "BOARD.md").write_text(BOARD)
        (d / "perry" / "OKR.md").write_text(
            "# OKR\n\n## Objectives\n\n- O1 ship it\n")
        (d / "perry" / "phase").mkdir()
        (d / "perry" / "phase" / "001-a.md").write_text("# Phase 1\n")
        return d

    def modes(self, register):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.project(register)),
             "--json"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        w = json.loads(proc.stdout)["work_modes"]
        return {t["track"]: t for t in w["tracks"]}, w


class TestADeclaredTrackIsNotGivenEverything(TrackCase):
    def test_the_declared_track_is_scored_on_its_own_rows(self):
        tracks, _ = self.modes(REGISTER)
        ops = tracks["ops"]
        self.assertEqual(ops["mode"], "pipeline")
        self.assertEqual(ops["scores"]["project"], 0,
                         "the project's own objectives and phases were "
                         "counted as this track's evidence")

    def test_the_implicit_main_track_is_enumerated(self):
        """Rows with a blank `Track` belong to `main` by the schema's rule, and
        `main` was in nobody's list — so their evidence went to the declared
        track or nowhere."""
        tracks, _ = self.modes(REGISTER)
        self.assertIn("main", tracks)
        self.assertFalse(tracks["main"]["declared"])
        self.assertEqual(tracks["main"]["mode"], "project")

    def test_project_wide_files_go_to_the_project_wide_track(self):
        """`phase/` and `OKR.md`'s objectives describe the whole repository.
        Fixing the first bug sent them to NOBODY, which is the same error
        pointed the other way."""
        tracks, _ = self.modes(REGISTER)
        self.assertGreater(tracks["main"]["scores"]["project"], 0)


class TestNoRegisterBehavesExactlyAsBefore(TrackCase):
    def test_one_implicit_track_gets_everything(self):
        """The unchanged path, and the one every existing project is on. A fix
        that moved this would be a regression dressed as a correction."""
        tracks, w = self.modes(None)
        self.assertFalse(w["register_declared"])
        self.assertEqual(list(tracks), ["main"])
        self.assertGreater(tracks["main"]["scores"]["project"], 0)


class TestPerrysOwnProjectIsUnmoved(unittest.TestCase):
    def test_it_still_reads_one_project_track(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        w = json.loads(proc.stdout)["work_modes"]
        self.assertFalse(w["register_declared"])
        self.assertEqual([t["track"] for t in w["tracks"]], ["main"])


if __name__ == "__main__":
    unittest.main()
