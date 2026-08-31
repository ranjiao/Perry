"""Two readers of one register gave two answers, and the mode's own step could
not run off either.

`TASK-019`'s surviving findings, from the V4 re-review:

1. On a queue track with a blank `Stages` cell, `perry-state` reported
   `stage_list: []` while `perry-task` birthed every row at the mode's default
   entry stage. The reader said the track had no stage vocabulary while the
   writer was placing rows into one.
2. `grep -i wip bin/perry-task` returned nothing. `modes/pipeline.md` calls WIP
   the mode's central control **and says out loud that it has no check** — so
   this half was an honest concession, not a contradiction. What it left behind
   was worse: triage step 2 ("stages at their WIP limit") was doable only by
   eyeballing a board the triage procedure forbids eyeballing, because
   `viewer/parsers.py § Task` carried **neither `track` nor `stage`** and
   `perry-state` reads the board through it.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402

STATE = PERRY_HOME / "bin" / "perry-state"
TASK = PERRY_HOME / "bin" / "perry-task"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())

CONFIG = ("# Perry configuration\n\n- State root: perry\n"
          + "\n## Tracks\n\n"
          "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
          "|---|---|---|---|---|---|---|---|\n{rows}")
HEAD = ("| ID | Title | Owner | Status | Next action | Evidence | "
        "Verification | Track | Stage |\n"
        "|---|---|---|---|---|---|---|---|---|\n")


class Base(unittest.TestCase):
    def project(self, rows: str, board_rows: str = "", heading: str = "P1") -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            CONFIG.format(rows=rows), encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text(
            f"# Board\n\n## {heading}\n\n" + HEAD + board_rows, encoding="utf-8")
        return root

    def state(self, root: Path) -> dict:
        r = subprocess.run([sys.executable, str(STATE), "--json",
                            "--root", str(root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def tracks(self, root: Path) -> dict:
        return {t["track"]: t for t in
                self.state(root)["project"]["config"]["tracks"]}

    def task(self, root: Path, *args: str) -> dict:
        r = subprocess.run([sys.executable, str(TASK), *args, "--root", str(root),
                            "--json"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)


class TestTheReaderAndTheWriterAgreeAboutStages(Base):
    ROW = "| ops | queue | OKR.md | — | — | 3d | 1w | V2 |\n"

    def test_a_blank_stages_cell_reports_the_modes_vocabulary(self):
        """`[]` said the track had no stages. It has the mode's — which is
        exactly what the writer uses."""
        t = self.tracks(self.project(self.ROW))["ops"]
        self.assertEqual(t["stage_list"],
                         ["new", "triaged", "in_progress", "resolved"])

    def test_and_says_the_project_did_not_declare_them(self):
        """The other question stays answerable, rather than one field trying to
        mean both."""
        t = self.tracks(self.project(self.ROW))["ops"]
        self.assertFalse(t["stages_declared"])

    def test_a_declared_vocabulary_is_reported_as_declared(self):
        t = self.tracks(self.project(
            "| ops | queue | OKR.md | a,b,c | — | 3d | 1w | V2 |\n"))["ops"]
        self.assertEqual(t["stage_list"], ["a", "b", "c"])
        self.assertTrue(t["stages_declared"])

    def test_the_writer_births_a_row_inside_what_the_reader_reports(self):
        """The property the disagreement broke, asserted across both tools."""
        root = self.project(self.ROW)
        subprocess.run([sys.executable, str(TASK), "add", "--title", "t",
                        "--deliverable", "d with a test", "--verification", "v",
                        "--next", "n", "--track", "ops", "--root", str(root)],
                       capture_output=True, text=True)
        r = subprocess.run([sys.executable, str(TASK), "list", "--all",
                            "--json", "--root", str(root)],
                           capture_output=True, text=True)
        stage = json.loads(r.stdout)["tasks"][0]["stage"]
        self.assertIn(stage, self.tracks(root)["ops"]["stage_list"],
                      "the writer put a row in a stage the reader denies exists")

    def test_the_defaults_come_from_the_schema(self):
        src = STATE.read_text(encoding="utf-8")
        self.assertIn("default_stages", src)
        self.assertNotIn('"new->triaged', src)


class TestTheBoardReaderCanSeeTheModeColumns(Base):
    def test_track_and_stage_resolve_by_header_name(self):
        """They were absent from `Task`, so `perry-state` — the standup's and
        triage's reader — could not see either, while `perry-task/list` parsed
        both with its own reader."""
        board = ("# Board\n\n## P1\n\n" + HEAD +
                 "| T-1 | a | o | in_progress | n | — | V3 | rel | review |\n")
        t = P.parse_board(board).all_tasks[0]
        self.assertEqual((t.track, t.stage), ("rel", "review"))

    def test_a_board_without_the_columns_still_parses(self):
        board = ("# Board\n\n## P1\n\n"
                 "| ID | Title | Owner | Status | Next action | Evidence |\n"
                 "|---|---|---|---|---|---|\n"
                 "| T-1 | a | o | in_progress | n | — |\n")
        t = P.parse_board(board).all_tasks[0]
        self.assertEqual((t.track, t.stage), ("", ""))
        self.assertEqual(t.owner, "o", "columns shifted")


class TestWipOverflowIsNowAScriptCatch(Base):
    ROW = "| rel | pipeline | phase/ | brief,draft,review,done | review:2 | 5d | 2w | V3 |\n"
    ROWS = ("| T-1 | a | o | in_progress | n | — | V3 | rel | review |\n"
            "| T-2 | b | o | in_progress | n | — | V3 | rel | review |\n"
            "| T-3 | c | o | in_progress | n | — | V3 | rel | review |\n"
            "| T-4 | d | o | in_progress | n | — | V3 | rel | draft |\n")

    def test_a_stage_over_its_limit_is_named_with_both_numbers(self):
        t = self.tracks(self.project(self.ROW, self.ROWS))["rel"]
        self.assertEqual(t["wip_breaches"],
                         [{"stage": "review", "count": 3, "limit": 2}])

    def test_the_whole_distribution_is_reported_not_only_the_breach(self):
        """Triage step 2 asks for the oldest item per stage as well; a count
        that only appeared on breach would make the ordinary case unreadable."""
        t = self.tracks(self.project(self.ROW, self.ROWS))["rel"]
        self.assertEqual(t["stage_counts"], {"review": 3, "draft": 1})

    def test_a_track_that_declared_no_wip_reports_no_breach(self):
        """Silence where the project made no promise. Inventing a limit is the
        mistake `no_default` exists to prevent."""
        t = self.tracks(self.project(
            "| rel | pipeline | phase/ | a,b | — | 5d | 2w | V3 |\n",
            self.ROWS))["rel"]
        self.assertEqual(t["wip_breaches"], [])
        self.assertEqual(t["stage_counts"], {"review": 3, "draft": 1})

    def test_closed_rows_do_not_count_against_a_limit(self):
        rows = self.ROWS + (
            "| T-5 | e | o | done | n | — | V3 | rel | review |\n")
        t = self.tracks(self.project(self.ROW, rows))["rel"]
        self.assertEqual(t["stage_counts"]["review"], 3,
                         "a finished row was counted as work in progress")

    def test_at_the_limit_counts_as_a_breach(self):
        """`modes/pipeline.md` says stages *at* their limit, not over — the
        stage is full and the next arrival is the problem."""
        rows = ("| T-1 | a | o | in_progress | n | — | V3 | rel | review |\n"
                "| T-2 | b | o | in_progress | n | — | V3 | rel | review |\n")
        t = self.tracks(self.project(self.ROW, rows))["rel"]
        self.assertEqual([b["stage"] for b in t["wip_breaches"]], ["review"])

    def test_the_mode_file_records_which_of_its_three_checks_landed(self):
        """It conceded all three were norms without checks. A concession that
        stops being true and stays written is the defect this project keeps
        finding."""
        doc = (PERRY_HOME / "modes" / "pipeline.md").read_text(encoding="utf-8")
        self.assertIn("wip_breaches", doc)
        self.assertIn("still norms the agent upholds", doc)


class TestCustomTaskGroupsReachTheStateReader(Base):
    PIPELINE = ("| rel | pipeline | phase/ | brief,draft,review,published | "
                "review:1 | 5d | 2w | V5 |\n")
    QUEUE = ("| ops | queue | commitments | new,triaged,in_progress,resolved | "
             "triaged:1 | 3d | 1w | V2 |\n")

    def test_pipeline_add_is_visible_to_tasks_open_counts_and_wip(self):
        root = self.project(self.PIPELINE, heading="Release train")
        added = self.task(
            root, "add", "--title", "publish notes", "--deliverable",
            "published notes with a test", "--verification", "fresh review",
            "--next", "draft them", "--track", "rel", "--stage", "review",
            "--group", "Release train")

        payload = self.state(root)
        rows = {t["id"]: t for t in payload["board"]["tasks"]}
        self.assertIn(added["id"], rows)
        self.assertEqual(payload["board"]["open"], 1)
        self.assertEqual((rows[added["id"]]["track"], rows[added["id"]]["stage"]),
                         ("rel", "review"))
        track = {t["track"]: t for t in payload["project"]["config"]["tracks"]}["rel"]
        self.assertEqual(track["stage_counts"], {"review": 1})
        self.assertEqual(track["wip_breaches"],
                         [{"stage": "review", "count": 1, "limit": 1}])

    def test_queue_route_is_visible_after_it_leaves_intake(self):
        root = self.project(self.QUEUE, heading="Support lane")
        self.task(root, "intake", "--title", "customer request",
                  "--arrived", "2026-08-05")
        routed = self.task(root, "route", "1", "--track", "ops",
                           "--group", "Support lane")

        payload = self.state(root)
        rows = {t["id"]: t for t in payload["board"]["tasks"]}
        self.assertIn(routed["id"], rows)
        self.assertEqual(payload["board"]["open"], 1)
        self.assertEqual(rows[routed["id"]]["stage"], "triaged")
        track = {t["track"]: t for t in payload["project"]["config"]["tracks"]}["ops"]
        self.assertEqual(track["stage_counts"], {"triaged": 1})
        self.assertEqual(track["wip_breaches"],
                         [{"stage": "triaged", "count": 1, "limit": 1}])

    def test_non_task_and_malformed_sections_stay_out_of_all_tasks(self):
        non_task = ("# Board\n\n## Reference\n\n"
                    "| ID | Description | Owner | Status |\n"
                    "|---|---|---|---|\n"
                    "| REF-1 | not work | team | current |\n")
        malformed = ("# Board\n\n## Broken group\n\n"
                     "| ID | Title | Owner | Status |\n"
                     "| TASK-1 | no separator | team | in_progress |\n")
        self.assertEqual(P.parse_board(non_task).all_tasks, [])
        self.assertEqual(P.parse_board(malformed).all_tasks, [])

    def test_a_reference_table_beside_a_task_table_is_not_read_as_work(self):
        board = ("# Board\n\n## Release train\n\n"
                 "| ID | Description | Owner | Status |\n"
                 "|---|---|---|---|\n"
                 "| REF-1 | glossary row | team | current |\n\n"
                 + HEAD +
                 "| TASK-1 | real work | team | in_progress | next | — | V3 | "
                 "rel | review |\n")
        self.assertEqual([t.id for t in P.parse_board(board).all_tasks], ["TASK-1"])


if __name__ == "__main__":
    unittest.main()
