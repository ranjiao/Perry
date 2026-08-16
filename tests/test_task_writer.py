"""Contract tests for `bin/perry-task` — the one deterministic write path.

The claim under test: **the tool mechanizes Perry's markdown format; it does not
change it.**

That claim is load-bearing because every reader keys on the format — Perry's own
`perry-state` and `perry-lint`, the viewer, and at least one external consumer
(aimark) that Perry does not control. A write tool that normalizes whitespace,
reorders columns or realigns pipes would be a silent breaking change to all of
them, and it would look like an improvement while doing it.

DESIGN-004's spec phrased the V3 check as "replay the open rows through
`perry-task add` and diff". That turned out to be unexecutable: the tool mints
IDs and deliberately does not accept one, so a replay cannot reproduce the
original numbering. The check that means the same thing and can actually run is
the round-trip below — every hand-written row, split and re-rendered by the
tool's own functions, must come back byte-identical.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
TOOL = PERRY_HOME / "bin" / "perry-task"


def load_tool():
    spec = importlib.util.spec_from_loader(
        "perry_task", importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PT = load_tool()

BOARD = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|

## Top risks

- none
"""


class Project:
    """A throwaway Perry project the tool can write into."""

    def __init__(self, tracks: str = "", board: str = BOARD):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + tracks)
        (self.root / "BOARD.md").write_text(board)

    def run(self, *argv) -> tuple[int, dict | str]:
        r = subprocess.run(
            ["python3", str(TOOL), *argv, "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def board(self) -> str:
        return (self.root / "BOARD.md").read_text()

    def events(self) -> list[dict]:
        p = self.root / ".perry" / "events.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().split("\n") if l.strip()]

    def journal(self) -> str:
        for p in (self.root / "journal").rglob("*.md"):
            return p.read_text()
        return ""

    def __del__(self):
        self.dir.cleanup()


class TestFormatIsMechanized(unittest.TestCase):
    """V3: the tool reproduces the format, it does not redefine it."""

    def test_every_hand_written_row_in_perrys_own_board_round_trips(self):
        """The real check. Perry's board was written by hand over a whole
        session; if the tool's renderer disagrees with any of it, adopting the
        tool would silently rewrite rows the moment they were touched."""
        board = PT.Board(PERRY_HOME / "perry" / "BOARD.md")
        rows = board.rows()
        self.assertGreater(len(rows), 5, "no rows to check — is the board empty?")
        for _, raw, _ in rows:
            self.assertEqual(
                PT.render_row(PT.split_row(raw)), raw,
                "the tool renders this hand-written row differently:\n"
                f"  hand: {raw}\n  tool: {PT.render_row(PT.split_row(raw))}")

    def test_the_shipped_template_round_trips_too(self):
        board = PT.Board(PERRY_HOME / "work" / "state" / "BOARD_TEMPLATE.md")
        for _, raw, _ in board.rows():
            self.assertEqual(PT.render_row(PT.split_row(raw)), raw)


class TestAtomicThreeWayWrite(unittest.TestCase):
    """Board, journal and event — or none of them."""

    def test_add_writes_all_three(self):
        p = Project()
        code, out = p.run("add", "--title", "Ship it", "--priority", "P0")
        self.assertEqual(code, 0, out)
        self.assertIn("| TASK-001 | Ship it |", p.board())
        self.assertIn("[TASK-001]", p.journal())
        self.assertEqual(len(p.events()), 1)
        self.assertEqual(p.events()[0]["event"], "add")

    def test_a_refusal_writes_nothing(self):
        p = Project()
        before, ev = p.board(), len(p.events())
        code, out = p.run("add", "--priority", "P0")  # no --title
        self.assertEqual(code, 1)
        self.assertIn("refused", out)
        self.assertEqual(p.board(), before, "a refused call still touched the board")
        self.assertEqual(len(p.events()), ev)
        self.assertEqual(p.journal(), "")

    def test_dry_run_touches_nothing(self):
        p = Project()
        before = p.board()
        code, out = p.run("add", "--title", "X", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.board(), before)
        self.assertEqual(p.events(), [])


class TestWhatTheToolComputes(unittest.TestCase):
    """DESIGN-004 §5.2 — every field an agent currently supplies and gets wrong."""

    def test_ids_are_minted_and_never_collide(self):
        p = Project()
        ids = []
        for i in range(3):
            _, out = p.run("add", "--title", f"task {i}")
            ids.append(out["id"])
        self.assertEqual(ids, ["TASK-001", "TASK-002", "TASK-003"])
        self.assertEqual(len(set(ids)), 3)

    def test_a_closed_task_keeps_its_number(self):
        """Reading only the board would hand a live id to a second task and
        silently re-point every reference to the first."""
        p = Project()
        _, a = p.run("add", "--title", "first")
        p.run("done", a["id"], "--evidence", "x.md", "--rung", "V3")
        self.assertNotIn(a["id"], p.board(), "closed row should leave the board")
        _, b = p.run("add", "--title", "second")
        self.assertNotEqual(b["id"], a["id"],
                            "a closed task's id was reused — every reference to "
                            "the first now silently points at the second")

    def test_timestamps_are_observed_not_asserted(self):
        p = Project()
        p.run("add", "--title", "X")
        ts = p.events()[0]["ts"]
        self.assertRegex(ts, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")

    def test_a_bad_rung_is_refused_before_anything_is_written(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        before = p.board()
        code, out = p.run("done", a["id"], "--evidence", "e.md", "--rung", "V9")
        self.assertEqual(code, 1)
        self.assertIn("V9", str(out))
        self.assertEqual(p.board(), before)

    def test_v0_is_refused_by_name(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, out = p.run("done", a["id"], "--evidence", "e.md", "--rung", "V0")
        self.assertEqual(code, 1)
        self.assertIn("asserted", str(out))

    def test_done_without_evidence_is_refused(self):
        """Perry's oldest rule, now enforced at write time rather than reported
        after the fact."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, out = p.run("done", a["id"])
        self.assertEqual(code, 1)
        self.assertIn("evidence", str(out))


class TestModeColumns(unittest.TestCase):
    """The container creation four review rounds kept finding missing."""

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| core | project | phase/ | — | — | — | — | V3 |\n"
              "| blog | pipeline | commitments | brief->draft->published | review:2 | 5d | 2026-W34 | V5 |\n"
              "| ops | queue | commitments | new->triaged->resolved | — | 5d | monthly | V2 |\n"
              "| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n")

    def test_a_project_track_adds_no_columns(self):
        """DESIGN-003 goal 7: declaring nothing costs nothing."""
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "X", "--track", "core")
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        self.assertNotIn("Stage", header)
        self.assertNotIn("Track", header)

    def test_a_pipeline_track_gets_stage_and_its_clock(self):
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "X", "--track", "blog", "--priority", "P0")
        board = p.board()
        header = [l for l in board.split("\n") if l.startswith("| ID |")][0]
        for col in ("Track", "Stage", "Stage since"):
            self.assertIn(col, header, f"{col} was not created")
        row = [l for l in board.split("\n") if l.startswith("| TASK-001 |")][0]
        self.assertIn("brief", row, "Stage was not set to the first declared stage")

    def test_a_queue_track_gets_arrived_not_stage_since(self):
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "X", "--track", "ops", "--priority", "P0")
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        self.assertIn("Arrived", header)
        self.assertNotIn("Stage since", header)

    def test_an_inquiry_track_gets_parent(self):
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "Q", "--track", "study", "--priority", "P0",
              "--parent", "TASK-000")
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        self.assertIn("Parent", header)

    def test_adding_a_column_preserves_every_existing_row(self):
        """The rows that were there before must not lose data when the header
        grows — they gain an empty cell, not a shifted one."""
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "plain one", "--track", "core", "--priority", "P0")
        p.run("add", "--title", "mode one", "--track", "blog", "--priority", "P0")
        rows = [l for l in p.board().split("\n") if l.startswith("| TASK-")]
        header = [l for l in p.board().split("\n") if l.startswith("| ID |")][0]
        width = len(PT.split_row(header))
        for r in rows:
            self.assertEqual(len(PT.split_row(r)), width,
                             f"row width diverged from the header:\n  {r}")
        self.assertIn("plain one", p.board())

    def test_an_undeclared_track_is_refused(self):
        p = Project(tracks=self.TRACKS)
        code, out = p.run("add", "--title", "X", "--track", "nope")
        self.assertEqual(code, 1)
        self.assertIn("nope", str(out))


class TestLifecycle(unittest.TestCase):
    def test_start_moves_status_and_records_both_ends(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, _ = p.run("start", a["id"])
        self.assertEqual(code, 0)
        self.assertIn("in_progress", p.board())
        ev = p.events()[-1]
        self.assertEqual((ev["from"], ev["to"]), ("not_started", "in_progress"))

    def test_starting_twice_is_refused(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        p.run("start", a["id"])
        code, _ = p.run("start", a["id"])
        self.assertEqual(code, 1)

    def test_done_takes_the_rung_from_the_tracks_default(self):
        p = Project(tracks=TestModeColumns.TRACKS)
        _, a = p.run("add", "--title", "X", "--track", "blog", "--priority", "P0")
        _, out = p.run("done", a["id"], "--evidence", "e.md")
        self.assertEqual(out["rung"], "V5", "pipeline's declared default rung was ignored")

    def test_the_event_log_is_disposable(self):
        """DESIGN-004 §5.3: delete it and Perry still works. This is the
        constraint that keeps the tool from becoming a database with a markdown
        export."""
        p = Project()
        p.run("add", "--title", "X")
        board_before = p.board()
        (p.root / ".perry" / "events.jsonl").unlink()
        code, out = p.run("list")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.board(), board_before)
        code, _ = p.run("add", "--title", "Y")
        self.assertEqual(code, 0, "the tool could not write without its own log")


if __name__ == "__main__":
    unittest.main()


class TestJournalAppendsChronologically(unittest.TestCase):
    """A day's journal accumulates one `## Status changes` per entry.

    Appending to the first one buries an 18:33 change inside the block written
    at 09:00. Perry's own journal had seventeen such sections on the day this
    tool shipped, and the tool's first real write landed on line 12 of a
    1026-line file. An append-only record is only chronological if new lines
    land at the end of it.
    """

    MULTI = ("# 2026-08-16\n\n## Status changes\n\n- [TASK-001] a → b · early\n\n"
             "## Notes\n\nprose\n\n---\n\n## Second entry\n\n"
             "## Status changes\n\n- [TASK-002] a → b · later\n\n## Notes\n\nmore prose\n")

    def test_the_line_lands_in_the_last_section(self):
        out = PT.append_status_change(self.MULTI, "- [TASK-003] a → b · newest")
        idx_new = out.index("TASK-003")
        idx_later = out.index("TASK-002")
        self.assertGreater(idx_new, idx_later,
                           "the new line was inserted before an older one")

    def test_earlier_sections_are_untouched(self):
        out = PT.append_status_change(self.MULTI, "- [TASK-003] a → b · newest")
        head = out[:out.index("## Second entry")]
        self.assertNotIn("TASK-003", head)
        self.assertIn("TASK-001", head)

    def test_a_journal_with_no_section_gets_one(self):
        out = PT.append_status_change("# 2026-08-16\n", "- [TASK-001] a → b")
        self.assertIn("## Status changes", out)
        self.assertIn("TASK-001", out)

    def test_an_empty_journal_gets_a_heading_too(self):
        out = PT.append_status_change("", "- [TASK-001] a → b")
        self.assertTrue(out.startswith("# "))
        self.assertIn("TASK-001", out)


class TestFullTaskSet(unittest.TestCase):
    """`list --all` — the question a front-end must answer and BOARD.md cannot.

    The board holds open work only; closed rows leave it. Until this, the full
    set existed solely as a reconstruction from date-sharded journal prose — a
    reader would have to parse every file in every month and rebuild each task's
    timeline. One call replaces that, which is what lets a consumer stay
    ignorant of Perry's file formats.
    """

    def test_closed_tasks_are_reconstructed_from_events(self):
        p = Project()
        _, a = p.run("add", "--title", "will close")
        _, b = p.run("add", "--title", "stays open")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        _, out = p.run("list", "--all")
        ids = {t["id"]: t for t in out["tasks"]}
        self.assertIn(a["id"], ids, "a closed task vanished from the full set")
        self.assertFalse(ids[a["id"]]["open"])
        self.assertTrue(ids[b["id"]]["open"])
        self.assertEqual(out["open"], 1)
        self.assertEqual(out["closed"], 1)

    def test_a_closed_task_keeps_its_title_and_evidence(self):
        """A bare id is what `reference/user-load.md` forbids handing a reader.
        The event log has to carry enough to name what it is talking about."""
        p = Project()
        _, a = p.run("add", "--title", "the flake detector")
        p.run("done", a["id"], "--evidence", "evidence/x.md", "--rung", "V3")
        _, out = p.run("list", "--all")
        t = next(x for x in out["tasks"] if x["id"] == a["id"])
        self.assertEqual(t["title"], "the flake detector")
        self.assertEqual(t["evidence"], "evidence/x.md")
        self.assertEqual(t["verification"], "V3")

    def test_without_all_only_open_tasks_are_returned(self):
        p = Project()
        _, a = p.run("add", "--title", "closes")
        p.run("done", a["id"], "--evidence", "e.md")
        _, out = p.run("list")
        self.assertEqual([t["id"] for t in out["tasks"] if not t["open"]], [])

    def test_every_task_carries_its_timeline(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        p.run("start", a["id"])
        p.run("done", a["id"], "--evidence", "e.md")
        _, out = p.run("list", "--all")
        t = next(x for x in out["tasks"] if x["id"] == a["id"])
        self.assertEqual([e["event"] for e in t["timeline"]],
                         ["add", "start", "done"])

    def test_an_untitled_id_is_reported_rather_than_papered_over(self):
        """Events written before the `title` field exists cannot name their
        task. Saying so beats printing a bare id and hoping."""
        p = Project()
        (p.root / ".perry" / "events.jsonl").write_text(
            json.dumps({"ts": "2026-01-01T00:00:00", "event": "done",
                        "id": "TASK-900", "to": "done"}) + "\n")
        _, out = p.run("list", "--all")
        self.assertIn("TASK-900", out["untitled"])

    def test_the_live_board_wins_over_the_event_stream(self):
        """A row still on the board is the truth; events are derived. If they
        disagree, the markdown is canonical — §5.3."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        p.run("start", a["id"])
        _, out = p.run("list", "--all")
        t = next(x for x in out["tasks"] if x["id"] == a["id"])
        self.assertTrue(t["open"])
        self.assertEqual(t["status"], "in_progress")


class TestPerryStateReadsTheLog(unittest.TestCase):
    def _state(self, root: Path) -> dict:
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(root), "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)

    def test_the_events_block_reports_the_log(self):
        p = Project()
        p.run("add", "--title", "X")
        ev = self._state(p.root)["board"]["events"]
        self.assertTrue(ev["present"])
        self.assertEqual(ev["total"], 1)
        self.assertEqual(ev["by_event"], {"add": 1})

    def test_no_log_is_zeroes_not_an_error(self):
        """A pre-DESIGN-004 project has no log and must not be reported as
        broken for it."""
        p = Project()
        ev = self._state(p.root)["board"]["events"]
        self.assertFalse(ev["present"])
        self.assertEqual(ev["total"], 0)

    def test_a_corrupt_line_does_not_lose_the_rest(self):
        p = Project()
        p.run("add", "--title", "X")
        log = p.root / ".perry" / "events.jsonl"
        log.write_text(log.read_text() + "{ not json\n" +
                       json.dumps({"ts": "2026-01-01T00:00:00", "event": "start",
                                   "id": "TASK-001"}) + "\n")
        ev = self._state(p.root)["board"]["events"]
        self.assertEqual(ev["total"], 2, "a corrupt line took a valid one with it")


class TestDriftReconciliation(unittest.TestCase):
    """DESIGN-004 §5.4 — the check that makes the tool worth building.

    Without it, `perry-task` is a convenience and the discipline problem is
    untouched: §3 says so outright. This is where that claim is made good or
    exposed as another unbacked assertion.

    The implementation corrects the spec's wording in one place. A board row
    with no creating event is NOT drift — it could be a hand-edit, or it could
    simply predate the tool, and nothing on a row distinguishes them. Perry's
    own board had 29 such rows the day `perry-task` shipped. Reporting those as
    drift would make the first standup after every upgrade a wall of noise about
    work done correctly under the old rules, and a check people learn to ignore
    is worse than no check. So `unrecorded` is context and `drift` counts only
    the two unambiguous conditions.
    """

    def _drift(self, p: "Project") -> dict:
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)["board"]["drift"]

    def test_a_board_the_tool_wrote_entirely_has_no_drift(self):
        p = Project()
        p.run("add", "--title", "A", "--priority", "P0")
        p.run("add", "--title", "B", "--priority", "P0")
        d = self._drift(p)
        self.assertEqual(d["drift"], 0)
        self.assertEqual(d["unrecorded"], 0)

    def test_an_event_whose_row_was_deleted_by_hand_is_reported(self):
        """The mutation did not land in the markdown — or someone removed it
        without closing it. Either way the two records disagree."""
        p = Project()
        p.run("add", "--title", "A", "--priority", "P0")
        _, b = p.run("add", "--title", "B", "--priority", "P0")
        board = p.root / "BOARD.md"
        board.write_text("\n".join(
            l for l in board.read_text().split("\n")
            if not l.startswith(f"| {b['id']} |")))
        d = self._drift(p)
        self.assertEqual(d["drift"], 1)
        self.assertIn(b["id"], d["orphaned"])

    def test_a_closed_task_is_not_reported_as_orphaned(self):
        """`done` removes the row on purpose. Reporting that as a lost mutation
        would make every correct close look like a defect."""
        p = Project()
        _, a = p.run("add", "--title", "A", "--priority", "P0")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        d = self._drift(p)
        self.assertEqual(d["drift"], 0, f"a correct close was reported: {d}")

    def test_a_project_with_no_log_is_not_reported_as_broken(self):
        """Every project predates the tool at the moment it upgrades. The first
        standup after an upgrade must not be a wall of findings."""
        p = Project()
        d = self._drift(p)
        self.assertFalse(d["checked"])
        self.assertEqual(d["drift"], 0)
        self.assertEqual(d["unrecorded"], 0)

    def test_rows_predating_the_log_are_context_not_drift(self):
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | written by hand | Coding Agent | not_started | — | — |\n\n## P1", 1))
        p.run("add", "--title", "tool-written", "--priority", "P0")
        d = self._drift(p)
        self.assertEqual(d["drift"], 0, "a pre-tool row was counted as drift")
        self.assertEqual(d["unrecorded"], 1)
        self.assertIn("TASK-900", d["unrecorded_sample"])
        self.assertTrue(d["baseline"], "no baseline to judge unrecorded rows against")

    def test_drift_is_reported_never_refused(self):
        """A user editing their own markdown is legitimate. Perry notices; it
        does not object, and nothing exits non-zero."""
        p = Project()
        _, a = p.run("add", "--title", "A", "--priority", "P0")
        board = p.root / "BOARD.md"
        board.write_text("\n".join(
            l for l in board.read_text().split("\n")
            if not l.startswith(f"| {a['id']} |")))
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        code, _ = p.run("add", "--title", "still works")
        self.assertEqual(code, 0, "drift blocked a write")
