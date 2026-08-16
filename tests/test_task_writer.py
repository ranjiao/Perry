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
import os
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
    """The two canonical files together; the derived event may fail alone.

    The class used to be named for a stronger guarantee — "board, journal and
    event, or none of them" — that four surfaces stated and the code never
    provided, and every test in it exercised a *pre-write validation refusal*.
    An assertion satisfied by the setup cannot fail on the behavior it names:
    `add` with no `--title` never reaches `commit()`, so nothing here touched
    the ordering the claim was about. `test_the_event_may_be_lost_but_never_the_row`
    is the one that goes through `commit()`.
    """

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

    def test_the_event_may_be_lost_but_never_the_row(self):
        """Reaches `commit()` and makes the event append fail, which is the
        only path where the ordering matters.

        Before this, an unwritable `.perry/` produced an uncaught
        `PermissionError` — a traceback, exit 1, and board + journal already on
        disk. Exit 1 is documented as "nothing was written", so a caller
        following the docs would retry and raise a second row for work already
        recorded. The loss is allowed to run in exactly one direction: the
        canonical files land together or not at all, and the derived event is
        reported when it goes missing.
        """
        p = Project()
        ev_dir = p.root / ".perry"
        (ev_dir / "events.jsonl").write_text("")
        mode = ev_dir.stat().st_mode
        os.chmod(ev_dir / "events.jsonl", 0o444)
        os.chmod(ev_dir, 0o555)
        try:
            code, out = p.run("add", "--title", "atomicity probe", "--priority", "P0")
        finally:
            os.chmod(ev_dir, mode)
            os.chmod(ev_dir / "events.jsonl", 0o644)

        self.assertNotIn("Traceback", str(out),
                         "an unwritable event log crashed instead of reporting")
        self.assertEqual(code, 0,
                         "the canonical write succeeded; exit 1 would tell the "
                         "caller to retry and duplicate the row")
        self.assertIn("atomicity probe", p.board(), "the row was lost")
        self.assertIn("TASK-001", p.journal(), "the journal line was lost")
        self.assertEqual(p.events(), [], "the event should not have been written")

        # And the row is honestly reported as having no creating event.
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout)["board"]["drift"]["unrecorded"], 1)


ZH_BOARD = """# BOARD

## P0
| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|

## P1
| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|

## P2
| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |
|---|---|---|---|---|---|
"""


class TestALocalizedBoard(unittest.TestCase):
    """`perry-task` was the only component in the stack that never read
    `schema § i18n.columns`.

    `perry-state`, `perry-lint` and the viewer all resolve headers through it;
    the writer keyed rows on hardcoded English. TASK-033 then routed *every*
    board write through the writer — so the migration handed the one component
    that could corrupt a localized board responsibility for all of them.

    The failures were silent and exit 0. `add` wrote a row of empty cells while
    the journal line and the event both asserted the task existed; `start` and
    `status` were board no-ops that still recorded the transition. The tool
    built to eliminate board-vs-history divergence produced it on its first
    write, on any project using the document language Perry advertises.

    No test in the suite had ever run the tool against a localized board, and
    Perry's own board is English — so neither dogfooding nor three review
    rounds could see it.
    """

    def zh(self) -> "Project":
        p = Project(board=ZH_BOARD)
        (p.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: 中文\n"
            "- Repo layout: single\n- State root: .\n")
        return p

    def row(self, p: "Project") -> list[str]:
        line = next(l for l in p.board().split("\n") if l.startswith("| TASK-001 |"))
        return [c.strip() for c in line.strip().strip("|").split("|")]

    def test_add_populates_the_row_rather_than_emptying_it(self):
        p = self.zh()
        code, out = p.run("add", "--title", "本地化测试", "--priority", "P0")
        self.assertEqual(code, 0, out)
        cells = self.row(p)
        self.assertEqual(cells[0], "TASK-001")
        self.assertEqual(cells[1], "本地化测试", "the title did not reach 标题")
        self.assertEqual(cells[3], "not_started", "the status did not reach 状态")
        self.assertNotEqual(cells, [""] * len(cells))

    def test_a_transition_actually_moves_the_cell(self):
        """`start` rebuilt the row from Chinese-keyed cells, matched no English
        header, and wrote it back byte-identical — while the event recorded
        `to: in_progress`. A board no-op that reports success is worse than a
        refusal: it is the divergence, manufactured by the tool."""
        p = self.zh()
        p.run("add", "--title", "任务", "--priority", "P0")
        code, out = p.run("start", "TASK-001")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.row(p)[3], "in_progress",
                         "the event says in_progress and the board does not")

    def test_a_new_column_joins_in_the_boards_own_language(self):
        """Appending `Stage` beside `阶段序列` would leave a header in two
        languages, which `perry-lint`'s localized match regexes then disagree
        about."""
        p = self.zh()
        (p.root / ".perry" / "config.md").write_text(
            (p.root / ".perry" / "config.md").read_text()
            + "\n## Tracks\n\n"
            "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| blog | pipeline | commitments | brief->draft | — | — | — | V5 |\n")
        code, out = p.run("add", "--title", "文章", "--track", "blog", "--priority", "P0")
        self.assertEqual(code, 0, out)
        header = next(l for l in p.board().split("\n") if l.startswith("| 编号 |"))
        self.assertIn("阶段", header, "the new column was added in English")
        self.assertNotIn("Stage", header)

    def test_an_unreadable_header_is_refused_not_blanked(self):
        """A refusal names the header it could not read. A blank row names
        nothing, and exits 0."""
        p = Project(board=ZH_BOARD.replace("| 编号 | 标题 |", "| 甲 | 乙 |"))
        code, out = p.run("add", "--title", "X", "--priority", "P0")
        self.assertEqual(code, 1, f"an unresolvable header was written to: {out}")
        self.assertIn("i18n.columns", str(out))
        self.assertNotIn("TASK-001", p.board())

    def test_drift_is_clean_on_a_board_the_tool_wrote_in_chinese(self):
        """The end-to-end statement: the localized path produces no false
        signal in the detector either."""
        p = self.zh()
        p.run("add", "--title", "甲任务", "--priority", "P0")
        p.run("add", "--title", "乙任务", "--priority", "P1")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        d = json.loads(r.stdout)["board"]["drift"]
        self.assertEqual((d["drift"], d["unrecorded"]), (0, 0), d)


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

    def test_a_routed_row_is_not_reported_as_un_tool_written(self):
        """Round-5 finding 5, and the first time the recurring defect reached
        code rather than prose.

        `reconcile_drift` recognized only `add` as a creating event. `route`
        emits `route`, so every row the tool itself created by promoting an
        intake request was counted `unrecorded` — forever, and it could never
        be detected as `orphaned` either, because the same tuple gates both
        loops. The detector generated the exact false drift it was built to
        catch, and `work/SKILL.md` then instructed the agent to narrate that
        signal as "written by hand since the tool landed."

        The route path is exercised end to end rather than by asserting on the
        tuple: the bug was that two readers disagreed about what creates a row,
        and only a written row can show that.
        """
        p = Project(tracks=TestModeAwareWrites.TRACKS)
        p.run("intake", "--title", "vendor spend reconciliation")
        code, r = p.run("route", "1", "--track", "ops")
        self.assertEqual(code, 0)
        d = self._drift(p)
        self.assertEqual(
            d["unrecorded"], 0,
            f"a row the tool created via `route` was reported as having no "
            f"creating event: {d}")
        self.assertEqual(d["drift"], 0)

        # And the other half of the same tuple: deleting a routed row by hand
        # must still be caught. A fix that made `route` invisible to both loops
        # would pass the assertion above and lose the detection.
        board = p.root / "BOARD.md"
        board.write_text("\n".join(
            l for l in board.read_text().split("\n")
            if not l.startswith(f"| {r['id']} |")))
        d = self._drift(p)
        self.assertIn(r["id"], d["orphaned"],
                      "a routed row deleted by hand went undetected")

    def test_cadence_rows_are_not_counted_as_predating_the_log(self):
        """Round-3 finding B2 — the row set left one round behind the tuple.

        `board.all_tasks` includes `## Cadence`, and `perry-task` has no
        cadence subcommand: `Board.find()` iterates P0/P1/P2 and cannot even
        locate one. So a cadence row was counted `unrecorded` on a board the
        tool wrote entirely — a number no project could ever drive to zero,
        firing at every standup of every board that uses the section the
        template, the schema headings and `work/SKILL.md` all prescribe.

        Unlike the `route` case, this one is unfixable from the user's side,
        which makes it precisely the "a check people learn to ignore is worse
        than no check" failure `reconcile_drift`'s docstring names as its own
        reason for existing.

        Perry's own board ships an EMPTY cadence placeholder, which the
        `if t.id` filter drops — so dogfooding could not surface it. The row
        here is populated on purpose.
        """
        p = Project(board=BOARD + (
            "\n## Cadence\n"
            "| ID | Recurring task | Frequency | Next due | Owner | Last evidence |\n"
            "|---|---|---|---|---|---|\n"
            "| CAD-01 | weekly review | weekly | 2026-08-20 | User | — |\n"))
        p.run("add", "--title", "tool written", "--priority", "P0")
        d = self._drift(p)
        self.assertEqual(
            d["unrecorded"], 0,
            f"a cadence row was reported as predating the log on a board the "
            f"tool wrote entirely, and no user action could ever clear it: {d}")

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


class TestModeAwareWrites(unittest.TestCase):
    """`stage`, `intake`, `route` — the operations DESIGN-003's modes describe
    and nothing could perform.

    Each closes a specific review finding that survived because the rule lived
    in prose: the stage clock nothing wound (round 3, N1), the arrival date the
    routing procedure dropped (round 4, B2), and the `## Intake` section nothing
    created (round 4, F2).
    """

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| core | project | phase/ | — | — | — | — | V3 |\n"
              "| blog | pipeline | commitments | brief->draft->review->published | review:2 | 5d | 2026-W34 | V5 |\n"
              "| ops | queue | commitments | new->triaged->in_progress->resolved | — | 5d | monthly | V2 |\n"
              "| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n")

    def cells(self, p: "Project", tid: str) -> dict:
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)], PT.split_row(row)))

    def test_a_stage_move_restamps_the_clock(self):
        """Status and Stage are orthogonal, so a draft→review move produces no
        status change and would otherwise leave no trace at all.

        The clock is aged first, deliberately. Asserting `stage since` is merely
        non-empty passes whether or not the move updates it — `add` already set
        it — so that assertion cannot fail on the bug it names. A mutation run
        proved exactly that: deleting the restamp left this test green. Aging
        the cell to a past date is what makes the check able to fail.
        """
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        self.assertEqual(self.cells(p, a["id"])["stage"], "brief")

        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            self.cells(p, a["id"])["stage since"], "2020-01-01"))
        self.assertEqual(self.cells(p, a["id"])["stage since"], "2020-01-01")

        code, _ = p.run("stage", a["id"], "--stage", "draft")
        self.assertEqual(code, 0)
        c = self.cells(p, a["id"])
        self.assertEqual(c["stage"], "draft")
        self.assertNotEqual(
            c["stage since"], "2020-01-01",
            "the stage moved and the clock did not — dwell time now reads "
            "from whenever the row was created, which is the defect the "
            "column was added to fix")

    def test_a_stage_outside_the_tracks_vocabulary_is_refused(self):
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        code, out = p.run("stage", a["id"], "--stage", "shipped")
        self.assertEqual(code, 1)
        self.assertIn("vocabulary", str(out))

    def test_a_commitment_reaches_the_board(self):
        """Round-3 finding B3, and round-4's B2 (`Arrived` dropped at routing)
        one column further out.

        `mode_columns` was a hand-maintained per-mode list that omitted
        `Commitment`. `--commitment` was accepted, stored into `values`, and
        then dropped by `append_row`, which maps values onto headers and had no
        header to map it to — exit 0, success message, no cell. That silently
        emptied the scan `modes/queue.md` is built on: "given a commitment due
        this week, which board rows carry its id."

        The list of columns and the list of values were written down
        separately, so they drifted. `columns_for(values)` derives one from the
        other, which is why this cannot recur for a seventh column.
        """
        p = Project(tracks=self.TRACKS)
        code, out = p.run("add", "--title", "Q3 post", "--track", "blog",
                          "--priority", "P0", "--commitment", "blog/1")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cells(p, "TASK-001").get("commitment"), "blog/1",
                         "--commitment was accepted and silently discarded")

        p.run("intake", "--title", "vendor spend")
        code, out = p.run("route", "1", "--track", "ops", "--commitment", "ops/1")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cells(p, out["id"]).get("commitment"), "ops/1")

    def test_a_bad_stage_is_refused_at_creation_too(self):
        """`stage` validated the vocabulary from the day it shipped; `add` and
        `route` took `--stage` verbatim and exited 0.

        The vocabulary was enforced when a row *moved* and not when it was
        *born* — the one moment there is no prior value to fall back on, so the
        bad cell is what the row carries from then on. `subcommands.md` already
        promised this refusal, which made the doc the only place it existed.
        """
        p = Project(tracks=self.TRACKS)
        code, out = p.run("add", "--title", "post", "--track", "blog",
                          "--stage", "shipped", "--priority", "P0")
        self.assertEqual(code, 1, f"an out-of-vocabulary stage was written: {out}")
        self.assertIn("vocabulary", str(out))
        self.assertNotIn("post", p.board(), "a refusal wrote a row anyway")

        p.run("intake", "--title", "req")
        code, out = p.run("route", "1", "--track", "ops", "--stage", "bogus")
        self.assertEqual(code, 1, f"route wrote an out-of-vocabulary stage: {out}")

    def test_moving_to_the_same_stage_is_refused(self):
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        code, _ = p.run("stage", a["id"], "--stage", "brief")
        self.assertEqual(code, 1, "a no-op move would restamp the clock for nothing")

    def test_intake_creates_the_section_that_nothing_created(self):
        """`triage` step 0 gated itself on 'only applies when the section
        exists', so for every queue track ever made it no-opped forever."""
        p = Project(tracks=self.TRACKS)
        self.assertNotIn("## Intake", p.board())
        code, _ = p.run("intake", "--title", "reconcile vendor spend")
        self.assertEqual(code, 0)
        self.assertIn("## Intake", p.board())
        self.assertIn("| Arrived | Request | Outcome |", p.board())

    def test_intake_sits_above_the_work_it_becomes(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        board = p.board()
        self.assertLess(board.index("## Intake"), board.index("## P0"))

    def test_routing_carries_the_arrival_date(self):
        """B2: the procedure that actually routed a row dropped the date its
        own SLA check measures, silently exempting it from the only clock
        governing it."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "vendor spend", "--arrived", "2026-08-14")
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P0")
        self.assertEqual(code, 0, out)
        c = self.cells(p, out["id"])
        self.assertEqual(c["arrived"], "2026-08-14",
                         "the arrival date was replaced with today, or lost")
        self.assertEqual(c["track"], "ops")

    def test_routing_records_where_the_intake_row_went(self):
        """A request whose outcome is not written down is one that gets
        re-asked."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "vendor spend")
        _, out = p.run("route", "1", "--track", "ops")
        intake_row = next(l for l in p.board().split("\n")
                          if "vendor spend" in l and not l.startswith("| TASK-"))
        self.assertIn(out["id"], intake_row)

    def test_routing_into_a_project_track_is_refused(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "x")
        code, out = p.run("route", "1", "--track", "core")
        self.assertEqual(code, 1)
        self.assertIn("queue-mode", str(out))

    def test_routing_a_row_that_does_not_exist_is_refused(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "x")
        code, _ = p.run("route", "7", "--track", "ops")
        self.assertEqual(code, 1)

    def test_the_generated_board_still_lints(self):
        """Everything the tool writes must satisfy the schema it renders from —
        otherwise it is producing files Perry's own reader rejects."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "x", "--arrived", "2026-08-14")
        p.run("route", "1", "--track", "ops", "--priority", "P0")
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        p.run("stage", a["id"], "--stage", "draft")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(p.root)], capture_output=True, text=True)
        self.assertNotIn("error", r.stdout.split("\n")[-2].lower().replace("0 error", ""),
                         f"the tool wrote a board its own linter rejects:\n{r.stdout}")


class TestLaneProceduresCallTheTool(unittest.TestCase):
    """TASK-033 — the riskiest migration in DESIGN-004's plan.

    Its failure mode is not a crash. It is a lane that still tells the agent to
    hand-write a row while the tool exists — two written paths to one piece of
    state, with drift reported against a procedure that *instructed* the agent
    to create it. The drift number would then report a documentation defect as
    if it were an agent's indiscipline, which is worse than no signal.

    §5.7 made this hard-blocked on TASK-031 for that reason: detection has to be
    watching before the procedures change, or a migration and a regression look
    identical.
    """

    @classmethod
    def setUpClass(cls):
        cls.proc = (PERRY_HOME / "work" / "reference" / "subcommands.md").read_text()

    def section(self, name: str) -> str:
        i = self.proc.index(f"### `{name}")
        j = self.proc.find("\n### ", i + 1)
        return self.proc[i:j if j > 0 else len(self.proc)]

    def test_add_task_calls_the_tool(self):
        s = self.section("add-task")
        self.assertIn("perry-task", s)
        self.assertIn("add --title", s)

    def test_close_task_calls_the_tool(self):
        s = self.section("close-task")
        self.assertIn("perry-task", s)
        self.assertIn("done", s)

    def test_no_migrated_procedure_still_describes_the_hand_edit(self):
        """The exact failure this task creates: a procedure that says both."""
        for name, banned in (
            ("add-task", "Add a row to `BOARD.md`** — terse"),
            ("close-task", "**Remove the row from `BOARD.md`**."),
        ):
            self.assertNotIn(
                banned, self.section(name),
                f"`{name}` still instructs a hand-edit for state the tool "
                f"now writes — two written paths to one piece of state")

    def test_routing_goes_through_the_tool(self):
        step0 = self.proc[self.proc.index("Step 0"):self.proc.index("Then walk")]
        self.assertIn("perry-task", step0)
        self.assertIn("route", step0)

    def test_the_stage_invariant_names_the_tool(self):
        i = self.proc.index("Every stage move")
        self.assertIn("perry-task", self.proc[i:i + 400])

    def test_the_procedures_say_what_a_refusal_means(self):
        """A tool that exits 1 without the procedure saying so invites the
        agent to treat a refusal as a failure and fall back to editing."""
        # Whitespace-collapsed: these assertions are about prose, and prose
        # reflows. An earlier version matched raw text, so adding one refusal
        # to the sentence re-wrapped the line and broke a test that had no
        # opinion about the change.
        s = re.sub(r"\s+", " ", self.section("add-task"))
        self.assertIn("Refusals are outcomes", s)
        self.assertIn("do not fall back to editing", s)

    def test_every_command_the_procedures_quote_actually_runs(self):
        """A migrated procedure naming a subcommand the tool does not have
        would be the same unbacked-index defect five reviews kept finding."""
        quoted = set(re.findall(r'perry-task"?\s+(\w+)', self.proc))
        r = subprocess.run(["python3", str(TOOL), "--help"],
                           capture_output=True, text=True)
        for cmd in quoted:
            self.assertIn(f"perry-task {cmd}", r.stdout,
                          f"the procedures call `perry-task {cmd}`, which the "
                          f"tool's own usage does not list")


class TestEveryStatusHasAToolPath(unittest.TestCase):
    """A gap in coverage becomes a permanent false signal once detection exists.

    `dispatch` moves rows into `review` on every run and the tool could not
    write `review`, so every dispatch manufactured a post-tool edit that drift
    detection would report forever — the same self-inflicted-drift shape that
    an unmigrated `drop-task` produced, found by a review one level out.
    """

    STATUSES = ["not_started", "blocked", "in_progress", "review", "done", "dropped"]

    def test_the_schema_enum_is_what_the_tool_accepts(self):
        """Named for a check it did not perform: it compared the schema to a
        hardcoded list and never invoked anything. Now it asks the tool."""
        schema = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
        self.assertEqual(schema["enums"]["task_status"], self.STATUSES)

        p = Project()
        p.run("add", "--title", "X")
        code, out = p.run("status", "TASK-001", "--status", "nonesuch")
        self.assertEqual(code, 1)
        for want in self.STATUSES:
            self.assertIn(want, str(out),
                          f"the tool's refusal does not offer {want!r}")

    def test_blocked_and_review_have_a_tool_path(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        for want, extra in (("review", []), ("blocked", ["--reason", "waiting on USER-001"])):
            code, out = p.run("status", a["id"], "--status", want, *extra)
            self.assertEqual(code, 0, f"{want}: {out}")
            self.assertIn(want, p.board())

    def test_blocked_without_a_named_dependency_is_refused(self):
        """A blocked row with no named dependency is a row nobody can unblock."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, out = p.run("status", a["id"], "--status", "blocked")
        self.assertEqual(code, 1)
        self.assertIn("reason", str(out))

    def test_status_refuses_the_closing_transitions(self):
        """`done` needs evidence and `dropped` needs a reason; letting `status`
        write them would route around both gates."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        for want in ("done", "dropped"):
            code, out = p.run("status", a["id"], "--status", want)
            self.assertEqual(code, 1, want)
            self.assertIn("perry-task", str(out))

    def test_every_accepted_command_runs_and_is_advertised(self):
        """The acceptance guard, the dispatch table and the "expected one of"
        message drifted apart twice.

        First `drop` was accepted and undispatched — a bare KeyError. Then
        `drop`, `status` and `resolve-intake` were dispatched and missing from
        the error message. Both were one list of command names written down
        three times, so `COMMANDS` is now the only copy and this test asserts
        the three readers agree.

        Reached through the CLI, not by importing the dict: what matters is
        that a name a user can type is a name that runs, and only invoking the
        process can show that.

        The "expected one of" half is deliberately weak — that message is
        literally `' / '.join(COMMANDS)`, so asserting it lists every command
        is a tautology. The check that carries weight is against the module
        **docstring**, which is a hand-maintained fourth copy that nothing kept
        in step: `--arrived`, `--owner`, `--commitment` and `--actor` had all
        shipped without it noticing.
        """
        for name in PT.COMMANDS:
            r = subprocess.run(
                ["python3", str(PERRY_HOME / "bin" / "perry-task"), name],
                capture_output=True, text=True)
            self.assertNotEqual(
                r.returncode, 2,
                f"{name!r} is dispatchable but the guard rejects it")
            self.assertNotIn(
                "Traceback", r.stderr,
                f"{name!r} crashed instead of refusing:\n{r.stderr}")

        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-task"), "nonesuch"],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

        usage = re.search(r"^Usage:\n(.*?)\n\n", PT.__doc__ or "", re.M | re.S)
        self.assertIsNotNone(usage, "the docstring's Usage block moved")
        documented = set(re.findall(r"^\s*perry-task\s+([a-z-]+)",
                                    usage.group(1), re.M))
        self.assertEqual(
            documented, set(PT.COMMANDS),
            f"the docstring and COMMANDS disagree — only in docstring: "
            f"{documented - set(PT.COMMANDS)}; missing from it: "
            f"{set(PT.COMMANDS) - documented}")

    def test_drop_requires_a_reason_and_leaves_no_orphan(self):
        """A hand-removed row leaves its `add` event with no row and no close —
        drift's second condition — so every hand drop manufactured false drift
        forever. `drop` was in the argument guard and missing from the dispatch
        table, crashing with a bare KeyError."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, _ = p.run("drop", a["id"])
        self.assertEqual(code, 1, "drop without a reason should refuse")
        code, out = p.run("drop", a["id"], "--reason", "superseded")
        self.assertEqual(code, 0, out)
        self.assertNotIn(a["id"], p.board())
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        d = json.loads(r.stdout)["board"]["drift"]
        self.assertEqual(d["drift"], 0, f"a tool-executed drop produced drift: {d}")

    def test_resolve_intake_covers_the_other_two_outcomes(self):
        p = Project(tracks=TestModeAwareWrites.TRACKS)
        p.run("intake", "--title", "a request")
        code, out = p.run("resolve-intake", "1", "--outcome", "dropped",
                          "--reason", "covered by the handbook")
        self.assertEqual(code, 0, out)
        row = next(l for l in p.board().split("\n") if "a request" in l)
        self.assertIn("dropped", row)
        self.assertIn("handbook", row)

    def test_a_queue_add_creates_the_intake_section(self):
        """`triage` step 0 gated itself on the section existing, and only
        `intake` created it — so the gate no-opped for every queue track."""
        p = Project(tracks=TestModeAwareWrites.TRACKS)
        p.run("add", "--title", "X", "--track", "ops", "--priority", "P0")
        self.assertIn("## Intake", p.board())

    def test_add_honours_arrived_rather_than_silently_ignoring_it(self):
        """The flag was accepted and overwritten with today, writing a wrong
        SLA clock without complaint."""
        p = Project(tracks=TestModeAwareWrites.TRACKS)
        p.run("add", "--title", "X", "--track", "ops", "--priority", "P0",
              "--arrived", "2026-08-01")
        row = next(l for l in p.board().split("\n") if l.startswith("| TASK-001 |"))
        self.assertIn("2026-08-01", row)

    def test_dispatch_and_autopilot_carry_the_invariant(self):
        """Both are loaded on their own, so the rule stated in subcommands.md
        never reaches them — it has to be restated where they are read."""
        for name in ("dispatch", "autopilot"):
            text = (PERRY_HOME / "work" / "reference" / f"{name}.md").read_text()
            self.assertIn("perry-task", text,
                          f"{name}.md never names the tool it must use")
            # Naming it once in a header would satisfy the line above while the
            # body instructed hand-edits throughout. Both files move rows, so
            # both must reach the subcommands that move them.
            for sub in ("start", "status"):
                self.assertRegex(
                    text, rf"perry-task[^\n]*\b{sub}\b|`{sub}`",
                    f"{name}.md moves rows but never reaches `perry-task {sub}`")


if __name__ == "__main__":
    # At the END of the file, not the middle. It used to sit after the fifth of
    # thirteen classes, so `python3 tests/test_task_writer.py` ran five and
    # exited 0 — every drift, localization, mode-aware-write, status-coverage
    # and lane-procedure test silently skipped, with a passing report.
    unittest.main()
