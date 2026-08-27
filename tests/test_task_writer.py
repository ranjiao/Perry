"""Contract tests for `bin/perry-task` — the one deterministic write path.

The claim under test: **the tool mechanizes Perry's markdown format; it does not
change it.**

That claim is load-bearing because every reader keys on the format — Perry's own
`perry-state` and `perry-lint`, and at least one external consumer
(aiMark) that Perry does not control. A write tool that normalizes whitespace,
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

from gate import GATE_OFF   # tests/gate.py — why this fixture opts out

PERRY_HOME = Path(__file__).resolve().parent.parent
TOOL = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"


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


#: A board with rows on it, written here so that "the reader found rows" is a
#: fact about this fixture and not about Perry's backlog (TASK-151). The
#: shapes are the ones the format actually produces: full cells, an empty
#: cell, the `—` blank marker, an escaped pipe, a path with slashes, a
#: comma-separated dependency cell, and CJK text. Every row must come back
#: byte-identical through `render_row(split_row(raw))`.
ROUND_TRIP_BOARD = """# Board — round trip

> A fixture. Every row below is hand-written.

## Intake

| Arrived | Request | Outcome |
|---|---|---|
| 2026-08-01 | someone asked for a thing | routed |

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-001 | Every cell full | Coding Agent | open | do the next thing | evidence/2026-08/TASK-001-spec.md |
| TASK-002 | An empty cell and a blank marker | Coding Agent | blocked |  | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-003 | A cell quoting a table: \\| ID \\| Risk \\| | user | open | read the escaped pipes back as one cell | — |
| TASK-004 | 中文标题也要原样回来 | Coding Agent | open | 保持字节一致 | — |

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-005 | Dependencies, comma separated | Coding Agent | open | TASK-001, TASK-002 | — |
| TASK-006 | A long next action that runs well past any column width anyone would align to | Coding Agent | open | keep going, and keep going, and do not wrap | — |
| TASK-007 | Trailing punctuation and a colon: like this | Coding Agent | open | — | — |

## Done this period (leaves the board at next triage)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-008 | Closed, and carries no priority | Coding Agent | done | — | — |

## Top risks

- none
"""

#: The roster `Board.rows()` must find in `ROUND_TRIP_BOARD`, in order.
#: `TASK-008` is deliberately absent: `rows()` is the WRITE path's view and
#: reports only sections that mean a priority, so a reader that started
#: returning the `## Done this period` rows would be a different defect than
#: one that returned nothing, and both are caught here.
ROUND_TRIP_ROW_IDS = ("TASK-001", "TASK-002", "TASK-003", "TASK-004",
                      "TASK-005", "TASK-006", "TASK-007")
ROUND_TRIP_ROW_PRIORITIES = ("P0", "P0", "P1", "P1", "P2", "P2", "P2")


class Project:
    """A throwaway Perry project the tool can write into."""

    def __init__(self, tracks: str = "", board: str = BOARD):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF + tracks)
        (self.root / "BOARD.md").write_text(board)
        self.import_board()

    # `add` requires a deliverable and a verification in production — a task
    # whose only record is a title cannot be picked up by anyone who was not in
    # the conversation that created it. Supplying defaults HERE rather than
    # relaxing the tool keeps 70-odd tests about ids, columns and drift free of
    # noise they do not exercise, while the refusals stay real and are covered
    # by `TestATaskMustCarryItsDefinition`.
    ADD_DEFAULTS = ("--deliverable", "a thing that exists afterwards",
                    "--verification", "the suite is green")

    def run(self, *argv) -> tuple[int, dict | str]:
        if argv and argv[0] == "add" and "--deliverable" not in argv \
                and "--title" in argv:
            argv = (*argv, *self.ADD_DEFAULTS)
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

    def import_board(self) -> None:
        r = subprocess.run(
            ["python3", str(TASKS), "write", "--from-board", "--root",
             str(self.root)], capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stdout + r.stderr)

    def __del__(self):
        self.dir.cleanup()


class TestFormatIsMechanized(unittest.TestCase):
    """V3: the tool reproduces the format, it does not redefine it."""

    def test_every_hand_written_row_in_perrys_own_board_round_trips(self):
        """The real check. Perry's board was written by hand over a whole
        session; if the tool's renderer disagrees with any of it, adopting the
        tool would silently rewrite rows the moment they were touched.

        Quantified over whatever the board holds, and over nothing else.
        `assertGreater(len(rows), 5)` used to stand at the top of it
        (TASK-151) — a proxy for "the corpus is not empty" that was really a
        census: a board that closed its way below six open rows would have
        reddened a test about ROW FORMATTING. The not-empty guard is a
        property of the reader, not of this project's backlog, so it is proved
        below on a board this module wrote.
        """
        board = PT.Board(PERRY_HOME / "perry" / "BOARD.md")
        for _, raw, _ in board.rows():
            self.assertEqual(
                PT.render_row(PT.split_row(raw)), raw,
                "the tool renders this hand-written row differently:\n"
                f"  hand: {raw}\n  tool: {PT.render_row(PT.split_row(raw))}")

    def test_the_round_trip_above_is_reading_rows_at_all(self):
        """TASK-151's other half: the loop above is vacuous over an empty list.

        `Board.rows()` walking away with nothing — a heading renamed, a
        separator the table reader stopped recognising, a priority it no
        longer maps — would leave that test green while checking no row at
        all. So the reader is held to a board whose roster is written down
        HERE, in the shapes the format actually uses: full cells, blank cells,
        the `—` marker, a pipe-free link, and a row in every section the
        walker is supposed to see.
        """
        board = PT.Board(self.write_board(ROUND_TRIP_BOARD))
        rows = board.rows()
        self.assertEqual([cells["id"] for _, _, cells in rows],
                         list(ROUND_TRIP_ROW_IDS),
                         "the reader did not find the rows this fixture "
                         "wrote — the round-trip above may be looping over "
                         "nothing")
        self.assertEqual([priority for priority, _, _ in rows],
                         list(ROUND_TRIP_ROW_PRIORITIES))
        for _, raw, _ in rows:
            self.assertEqual(
                PT.render_row(PT.split_row(raw)), raw,
                "the tool renders this row differently:\n"
                f"  hand: {raw}\n  tool: {PT.render_row(PT.split_row(raw))}")

    def write_board(self, text: str) -> Path:
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = Path(d.name) / "BOARD.md"
        path.write_text(text, encoding="utf-8")
        return path

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

    def test_concurrent_writes_do_not_lose_rows(self):
        """`BOARD.md` is read at `Board.__init__` and written at `commit()`.
        Between those, another process can read the same board — and the second
        rename discards the first process's row.

        Measured before the fix, not theorized: five concurrent `add` calls
        left **two** rows, with `TASK-001` and `TASK-002` each issued twice.
        The event log took all five, because it is opened `O_APPEND`: the
        append-only file survived precisely the race the read-modify-write
        document lost.

        `autopilot` dispatches concurrently by design, so this is a live path.

        The lock has to wrap the read too. One around `commit()` alone would
        still let both processes mint the same id from the same stale board —
        which is why this asserts on unique ids and not only on row count.
        """
        p = Project()
        n = 8
        procs = [subprocess.Popen(
            ["python3", str(TOOL), "add", "--title", f"concurrent {i}",
             "--priority", "P0", *Project.ADD_DEFAULTS,
             "--root", str(p.root), "--json"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for i in range(n)]
        for proc in procs:
            proc.wait()

        rows = [l for l in p.board().split("\n") if l.startswith("| TASK-")]
        ids = re.findall(r"TASK-\d+", p.board())
        self.assertEqual(len(rows), n, f"{n - len(rows)} row(s) were lost")
        self.assertEqual(len(set(ids)), n, f"an id was issued twice: {ids}")
        self.assertEqual(len(p.events()), n)

    def test_locking_leaves_nothing_in_the_project(self):
        """The lock is Perry's only piece of pure runtime state, and it must
        not become the user's problem.

        Its first placement was `state_root/.board.lock`, which showed up as
        `?? .board.lock` in a real Perry project the same night it shipped —
        untracked and unignored, because a consumer repo does not inherit
        Perry's own `.gitignore`. A tool that makes every user edit their
        ignore file to stay clean has pushed its bookkeeping onto them.

        It now lives in the temp dir, keyed by a hash of the state root.
        """
        p = Project()
        before = {x.name for x in p.root.iterdir()}
        p.run("add", "--title", "X", "--priority", "P0")
        after = {x.name for x in p.root.iterdir()}
        # `tasks.jsonl` is not bookkeeping — it is what the write writes
        # (ADR-007, TASK-089). `BOARD.md` already existed, so the store is the
        # one new canonical file a first write creates. The lock is still the
        # thing this test is about, and it is still not here.
        self.assertEqual(
            after - before, {"journal"},
            f"a write left files in the project beyond the journal and the "
            f"store: {sorted(after - before - {'journal'})}")
        self.assertFalse(
            list(p.root.rglob("*.lock")),
            "a lock file was written into the project tree")

    def test_the_event_may_be_lost_but_never_the_row(self):
        """Reaches `commit()` and makes the event append fail, which is the
        only path where the ordering matters.

        Before this, an unwritable `.perry/` produced an uncaught
        `PermissionError` — a traceback, exit 1, and board + journal already on
        disk. Exit 1 is documented as "nothing was written", so a caller
        following the docs would retry and raise a second row for work already
        recorded. The canonical pair is recoverable: ordinary failures roll
        back and a crash is completed on the next locked run. The derived event
        is reported when it goes missing.
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

    `perry-state` and `perry-lint` both resolve headers through it;
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
        # Overwrites the config `Project` wrote, so it has to carry `GATE_OFF`
        # forward itself — `ZH_BOARD` is deliberately not Perry's shape.
        (p.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: 中文\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF)
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

    def test_a_closed_tasks_number_survives_deleting_the_event_log(self):
        """The event log is declared derived and disposable — "delete it and
        what is lost is history resolution and drift detection, not truth."

        That was false for exactly one thing. A closed task is in neither the
        board (its row was removed at close) nor, after a delete, the log — so
        `mint_id`, which read only those two, reissued its number. Every journal
        line, evidence file and commit message naming the old task then
        silently pointed at the new one. **A reused id is truth, not history
        resolution.**

        The journal closes it: canonical, append-only, and carrying a creation
        line for every task ever raised — the one record every procedure here
        forbids editing, including on drop and close.

        Found by demonstrating to the user where task state lives, not by a
        review: closing a task and deleting the log are each ordinary, and only
        doing both in sequence shows it.
        """
        p = Project()
        _, a = p.run("add", "--title", "first")
        p.run("done", a["id"], "--evidence", "x.md", "--rung", "V3")
        (p.root / ".perry" / "events.jsonl").unlink()

        code, b = p.run("add", "--title", "after the log was deleted")
        self.assertEqual(code, 0, b)
        self.assertNotEqual(
            b["id"], a["id"],
            f"{a['id']} was reissued after the disposable log was deleted — "
            f"the journal already carried it")

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

    def test_an_event_without_a_store_record_is_not_a_task(self):
        """The event stream supplies history, never current task identity."""
        p = Project()
        (p.root / ".perry" / "events.jsonl").write_text(
            json.dumps({"ts": "2026-01-01T00:00:00", "event": "done",
                        "id": "TASK-900", "to": "done"}) + "\n")
        _, out = p.run("list", "--all")
        self.assertNotIn("TASK-900", out["untitled"])
        self.assertNotIn("TASK-900", {task["id"] for task in out["tasks"]})

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
        standup after an upgrade must not be a wall of findings.

        **Not broken is not the same as clean (TASK-117).** This asserted
        `drift == 0` and `unrecorded == 0` beside `checked is False` — the two
        numbers that made a consumer reading counts instead of the flag report
        a clean board on a tree nothing had looked at. Silence about a question
        nobody asked is the point; a zero is an answer.
        """
        p = Project()
        d = self._drift(p)
        self.assertFalse(d["checked"])
        self.assertIsNone(d["drift"])
        self.assertIsNone(d["unrecorded"])

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

    def test_drift_is_reported_and_a_write_repairs_from_the_store(self):
        """Projection drift cannot discard store truth after TASK-090."""
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
        code, out = p.run("add", "--title", "must not discard the store")
        self.assertEqual(code, 0, out)
        stored_ids = {json.loads(line)["id"] for line in
                      (p.root / "tasks.jsonl").read_text().splitlines()
                      if line.strip()}
        self.assertIn(a["id"], stored_ids)
        self.assertIn(a["id"], out["projection"]["rows_not_on_board"])


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
        p.import_board()

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


class TestListContract(unittest.TestCase):
    """`perry-task list --json` is published to a program Perry does not own.

    aimark codes against this payload. The point of freezing it is that it does
    NOT move when Perry's storage does — `BOARD.md`'s role is an open question
    (DESIGN-005) and this contract is deliberately not part of it.

    These tests are the thing that makes the promise real: a change to the
    payload breaks CI here rather than breaking a front-end silently, at
    runtime, in another repo.

    Spec: `schema/task-list-contract.md`.
    """

    TASK_KEYS = {
        "role",
        "id", "title", "summary", "owner", "priority", "status", "track", "mode",
        "stage", "stage_since", "arrived", "parent", "commitment",
        "next_action", "evidence", "evidence_paths", "verification", "open",
        "group", "status_text", "created", "updated", "timeline",
        # 1.6 — the dependency edge, and the one question a dashboard asks.
        "depends_on", "blocked_by", "blocks", "startable",
        # 1.12 — the board says blocked and the graph says nothing is.
        "blocked_stale",
        # 1.15 — what each `depends_on` id IS, beside the ids themselves. An
        # ANSWERED ask is in no register a consumer can query — not `tasks[]`,
        # not `asks.items`, not `depends_on_unknown` — and deducing its kind
        # from three arrays it is missing from is set arithmetic, not a
        # contract. A parallel array, because retyping `depends_on` would be a
        # major on the key every consumer of this payload reads.
        "depends_on_resolved",
    }
    TOP_KEYS = {"contract", "semantics", "project_root", "state_root",
                "conformance",
                "intake", "tasks", "open", "closed", "events", "untitled",
                # 1.6 — the three blocks that were readable only through
                # `perry-state --json`, the payload with no version.
                "risks", "asks", "drift"}
    RISKS_KEYS = {"items", "open", "cleared", "source"}
    RISK_KEYS = {"id", "title", "severity", "severity_text", "severity_rank",
                 "source", "opened", "age_days", "status", "cleared_on", "meta"}
    ASKS_KEYS = {"items", "open"}
    ASK_KEYS = {"id", "needed", "blocks", "asked", "idle", "idle_days",
                "status", "priority"}
    DRIFT_KEYS = {"checked", "baseline", "drift", "unrecorded",
                  "unrecorded_sample", "orphaned", "stale_done"}
    INTAKE_KEYS = {"rows", "undischarged", "oldest_undischarged"}
    INTAKE_ROW_KEYS = {"n", "arrived", "request", "outcome", "discharged",
                       "age_days"}
    # 1.13 — the two `conformance` entry shapes that carry a `means` sentence
    # beside the pattern they matched (TASK-142). A bare `{id, cites, status}`
    # triple reads as a wording complaint, and on 2026-08-20 it was read as one
    # on the only two stranded rows on Perry's own board.
    CITATION_KEYS = {"id", "cites", "status", "row_status", "blocked_stale",
                     "readings", "means"}
    # ONE shape for both idle checks: `status` says which produced the entry
    # and the clock is in hours on both, so a consumer needs one code path.
    IDLE_ROW_KEYS = {"id", "status", "last_event", "idle_hours",
                     "threshold_hours", "means"}
    #: `conformance.depends_on_unknown[]`. Tabulated 2026-08-21, when a row on
    #: Perry's own board was blocked on a `USER-` ask and the collection became
    #: non-empty for the first time — until then `tests/contract_key_parity.py`
    #: could not compare it and its two keys sat undocumented, unseen.
    UNKNOWN_DEP_KEYS = {"id", "unknown"}
    #: `semantics[]`. Shipped at 1.7 and described only in prose until
    #: 2026-08-21 (TASK-131) — rule 3 of the contract hands a consumer a loop
    #: over `version`/`fields`/`note` and no row said what any of the three
    #: holds, so the payload's own compatibility signal was the least
    #: documented thing in it.
    SEMANTICS_KEYS = {"version", "fields", "note"}
    #: `tasks[].depends_on_resolved[]` (1.15). `satisfied` is
    #: `dependency_satisfied`'s own answer rather than a second spelling of
    #: it, so this array and `blocked_by` cannot disagree about an edge;
    #: `kind` is `task` | `ask` | `unknown`, and `title` is `""` on the last
    #: of those because inventing one out of a handle is what `risks[].id`
    #: was corrected for at 1.6.
    RESOLVED_EDGE_KEYS = {"id", "kind", "satisfied", "title", "status"}
    #: `conformance.sections_read[]`. Its shape was stated inside the
    #: `conformance` table's Meaning cell, which is prose to both checkers.
    SECTIONS_READ_KEYS = {"heading", "priority", "rows"}
    #: `conformance.evidence_not_found[]`. Same: `{id, paths}` in a Meaning
    #: cell documented the pair to a human and to neither check.
    EVIDENCE_NOT_FOUND_KEYS = {"id", "paths"}
    CONFORMANCE_KEYS = {"sections_read", "sections_skipped",
                        "rows_with_unrecognized_id", "off_enum_status",
                        "rows_with_no_status", "evidence_not_found",
                        "rows_with_no_computable_age",
                        "next_action_cites_closed",
                        "depends_on_unknown", "dependency_cycles",
                        "blocked_without_dependency",
                        # TASK-142. The stranded-row family: a `blocked` row
                        # every one of whose declared dependencies has closed,
                        # an `in_progress` row with no dispatch slot and a
                        # stopped clock, and a `review` row nobody is coming
                        # back to. All three added at 1.13.
                        "blocked_by_closed_rows",
                        "in_progress_with_no_live_run", "review_idle",
                        "has_event_log",
                        "missing_projection"}
    # `field` (1.7) says what `from`/`to` refer to on this event, so a
    # consumer needs no hardcoded set of events that overload the pair.
    EVENT_KEYS = {"ts", "event", "from", "to", "field", "actor"}

    TRACKS = TestModeAwareWrites.TRACKS

    def populated(self) -> "Project":
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "plain project row", "--priority", "P0")
        p.run("add", "--title", "pipeline row", "--track", "blog",
              "--priority", "P1", "--commitment", "blog/1")
        _, c = p.run("add", "--title", "closed row", "--priority", "P2")
        p.run("done", c["id"], "--evidence", "e.md", "--rung", "V3")
        return p

    def payload(self, p: "Project", *extra) -> dict:
        _, out = p.run("list", "--all", *extra)
        return out

    def test_the_version_handle_is_present_and_major_1(self):
        d = self.payload(self.populated())
        self.assertEqual(d["contract"], PT.LIST_CONTRACT)
        self.assertTrue(d["contract"].startswith("perry-task/list/1."),
                        f"major bumped to {d['contract']} — every consumer "
                        f"checking major == 1 now refuses; that is intended "
                        f"only for a removed or retyped key")

    def test_every_declared_key_is_present_on_every_task(self):
        """Rule 1 of the contract: an unknown value is "", null or [] — never a
        missing key. It is what lets a consumer skip a defensive branch per
        field, so it has to hold for closed rows and event-only rows too."""
        d = self.payload(self.populated())
        self.assertTrue(d["tasks"])
        for t in d["tasks"]:
            self.assertEqual(set(t), self.TASK_KEYS,
                             f"{t.get('id')}: missing "
                             f"{self.TASK_KEYS - set(t)}, extra "
                             f"{set(t) - self.TASK_KEYS}")
            for e in t["timeline"]:
                self.assertEqual(set(e), self.EVENT_KEYS)

    def test_the_top_level_shape_is_exact(self):
        d = self.payload(self.populated())
        self.assertEqual(set(d), self.TOP_KEYS,
                         f"missing {self.TOP_KEYS - set(d)}, "
                         f"extra {set(d) - self.TOP_KEYS}")
        self.assertEqual(set(d["conformance"]), self.CONFORMANCE_KEYS)
        self.assertEqual(set(d["intake"]), self.INTAKE_KEYS)
        self.assertEqual(set(d["risks"]), self.RISKS_KEYS)
        self.assertEqual(set(d["asks"]), self.ASKS_KEYS)
        self.assertEqual(set(d["drift"]), self.DRIFT_KEYS)

    def test_open_means_still_on_the_board_not_a_status_value(self):
        """The contract says `open` is the live/closed test, not `status` —
        a consumer that filtered on `status != "done"` would keep showing a
        dropped row forever."""
        p = self.populated()
        d = self.payload(p)
        closed = [t for t in d["tasks"] if not t["open"]]
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]["status"], "done")
        self.assertNotIn(closed[0]["id"], p.board())
        self.assertTrue(all(t["id"] in p.board() for t in d["tasks"] if t["open"]))

    def test_without_all_the_closed_row_is_absent(self):
        p = self.populated()
        ids = {t["id"] for t in self.payload(p)["tasks"]}
        _, open_only = p.run("list")
        self.assertEqual(len(open_only["tasks"]), len(ids) - 1)
        self.assertTrue(all(t["open"] for t in open_only["tasks"]))

    def test_mode_columns_reach_the_payload(self):
        """`commitment` and `stage_since` exist as board columns; a payload
        that dropped them would send a front-end back to the markdown."""
        d = self.payload(self.populated())
        blog = next(t for t in d["tasks"] if t["track"] == "blog")
        self.assertEqual(blog["commitment"], "blog/1")
        self.assertEqual(blog["stage"], "brief")
        self.assertTrue(blog["stage_since"], "the dwell clock is not exposed")
        self.assertTrue(blog["owner"], "owner is missing from the payload")

    def test_created_and_updated_are_timestamps_or_null(self):
        d = self.payload(self.populated())
        for t in d["tasks"]:
            for k in ("created", "updated"):
                self.assertTrue(t[k] is None or isinstance(t[k], str), (t["id"], k))
            if t["timeline"]:
                self.assertEqual(t["updated"], t["timeline"][-1]["ts"])

    def test_a_row_predating_the_event_log_still_carries_every_key(self):
        """The hardest case for rule 1: a board row with no event at all."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | predates everything | User | in_progress | — | — |\n\n## P1", 1))
        t = next(x for x in self.payload(p)["tasks"] if x["id"] == "TASK-900")
        self.assertEqual(set(t), self.TASK_KEYS)
        self.assertIsNone(t["created"])
        self.assertEqual(t["timeline"], [])
        self.assertTrue(t["open"])

    # Reduced from a real Perry project, kept close to the original on purpose:
    # sections named by workstream instead of P0/P1/P2, a 4-column table, an id
    # in strikethrough, a status in the document language, a first cell that is
    # prose rather than a handle, and a reference table that is not work at all.
    MESSY = """# BOARD

## ID prefixes (canonical)

| Prefix | Means |
|---|---|
| DATA-n | data layer |

## Open — 投资线

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| IPS-004 | 政策起草 | User | 起草中 | 起草 v2 |

## Open — 工程线 · phase #004

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| TECH-conftest | `tests/conftest.py` 无隔离 | Coding Agent | not_started | — |

## P2 (低优先 carry)

| ID | Title | Owner | Status |
|---|---|---|---|
| 2 待核项 | GAVI 金额 | User | 半解 |
| ~~DATA-007~~ | 每仓核验时效 | Coding Agent | done |

## Cadence

| ID | Recurring task | Frequency | Next due | Owner | Last evidence |
|---|---|---|---|---|---|
| CAD-01 | weekly review | weekly | 2026-08-20 | User | — |

## Top risks

- something
"""

    def test_a_real_projects_board_is_read_rather_than_mostly_skipped(self):
        """The compatibility case, taken from a live Perry project.

        Reading only `## P0` / `## P1` / `## P2` found the one section whose
        name happened to match, reported three tasks for a project with dozens,
        and pulled rows out of a `## ID prefixes` reference table as though
        they were work. A front-end handed that payload shows the user
        confident nonsense — which is worse than showing nothing.
        """
        d = self.payload(Project(board=self.MESSY))
        ids = {t["id"] for t in d["tasks"]}
        self.assertEqual(ids, {"IPS-004", "TECH-conftest", "DATA-007"},
                         f"workstream sections were not read: {sorted(ids)}")

        by_id = {t["id"]: t for t in d["tasks"]}
        self.assertEqual(by_id["IPS-004"]["group"], "Open — 投资线")
        self.assertEqual(by_id["IPS-004"]["priority"], "",
                         "a section that is not P0/P1/P2 must not be assigned "
                         "a priority the project never stated")
        self.assertEqual(by_id["DATA-007"]["priority"], "P2")
        self.assertEqual(by_id["TECH-conftest"]["next_action"], "—")

    def test_projection_only_rows_do_not_enter_task_conformance(self):
        c = self.payload(Project(board=self.MESSY))["conformance"]
        self.assertEqual(c["sections_skipped"], [])
        self.assertEqual(c["rows_with_unrecognized_id"], [])
        self.assertEqual(c["off_enum_status"], [])
        self.assertFalse(c["has_event_log"])
        self.assertEqual(
            {s["heading"] for s in c["sections_read"]},
            {"Open — 投资线", "Open — 工程线 · phase #004", "P2 (低优先 carry)"})

    def test_cadence_and_risks_are_not_reported_as_tasks(self):
        """They are board sections and they are not work. Counting them is how
        `perry-state`'s drift row got a number no project could drive to zero."""
        d = self.payload(Project(board=self.MESSY))
        self.assertNotIn("CAD-01", {t["id"] for t in d["tasks"]})
        headings = {s["heading"] for s in d["conformance"]["sections_read"]}
        self.assertNotIn("Cadence", headings)

    def test_the_contract_document_lists_exactly_these_keys(self):
        """The spec and the payload are two statements of one thing, which is
        the arrangement that has drifted in every review round of this project.
        Read the document's own tables rather than trusting them."""
        doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        self.assertIn(PT.LIST_CONTRACT, doc, "the doc names a different version")
        documented = set(re.findall(r"^\| `(\w+)` \|", doc, re.M))
        known = (self.TASK_KEYS | self.EVENT_KEYS | self.CONFORMANCE_KEYS
                 | self.INTAKE_KEYS | self.INTAKE_ROW_KEYS
                 | self.RISKS_KEYS | self.RISK_KEYS
                 | self.ASKS_KEYS | self.ASK_KEYS | self.DRIFT_KEYS
                 | self.CITATION_KEYS | self.IDLE_ROW_KEYS
                 | self.UNKNOWN_DEP_KEYS | self.SEMANTICS_KEYS
                 | self.RESOLVED_EDGE_KEYS
                 | self.SECTIONS_READ_KEYS | self.EVIDENCE_NOT_FOUND_KEYS)
        undocumented = known - documented
        self.assertFalse(undocumented,
                         f"payload keys with no row in the contract doc: "
                         f"{sorted(undocumented)}")
        phantom = documented - known
        self.assertFalse(phantom,
                         f"the contract doc documents keys the payload does "
                         f"not emit: {sorted(phantom)}")


class TestFromAimarksProductionReport(unittest.TestCase):
    """Every case here was measured by a consumer against a real project, not
    read out of the spec. Reported 2026-08-17 after aiMark shipped against
    `perry-task/list/1.1`.

    None of it was blocking for them, which is the reason to fix it: they had
    absorbed all of it, and absorbing means guessing at Perry's intent in the
    consumer — which is how the last divergence started.
    """

    BOARD_WITH_EMPHASIS = """# BOARD

## P0
| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-001 | Bold done | User | **done** | — | — |
| TASK-002 | Bold not started | User | **not_started** | — | — |
| TASK-003 | Two states at once | User | **迁移 done，占比目标 not_started** | — | — |
| TASK-004 | Plain | User | in_progress | — | — |

## P1
| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2
| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Done this period (leaves the board at next triage)

| ID | Title | Evidence |
|---|---|---|
| TASK-010 | Finished, and the table has no Status column | `BOARD.md` |
"""

    def payload(self, board: str):
        p = Project(board=board)
        _, out = p.run("list", "--all")
        return p, out

    def test_emphasis_is_stripped_so_the_enum_claim_is_true(self):
        """`**done**` is `done` wearing bold. Formatting is not meaning, and
        17 of 41 rows on one real board carried it — every finished task
        rendered as an unrecognized state by a consumer trusting the enum."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        by = {t["id"]: t for t in d["tasks"]}
        self.assertEqual(by["TASK-001"]["status"], "done")
        self.assertEqual(by["TASK-002"]["status"], "not_started")
        self.assertEqual(by["TASK-001"]["status_text"], "done")

    def test_a_composite_cell_is_not_rounded_to_one_state(self):
        """`迁移 done，占比目标 not_started` is two states. Picking either is a
        lie about the work; `status` goes empty and `status_text` keeps it."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        t = next(x for x in d["tasks"] if x["id"] == "TASK-003")
        self.assertEqual(t["status"], "")
        self.assertEqual(t["status_text"], "")
        self.assertIn(
            "TASK-003",
            [row["id"] for row in d["conformance"]["rows_with_no_status"]])

    def test_open_is_false_for_a_row_whose_status_is_terminal(self):
        """`open` meant "still on the board", which was true when closing
        removed the row. Once the reader saw every section, a project staging
        finished work under its own heading reported those rows as open — 20 of
        them on Perry's own board."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        by = {t["id"]: t for t in d["tasks"]}
        self.assertFalse(by["TASK-001"]["open"], "a `**done**` row read as open")
        self.assertTrue(by["TASK-004"]["open"])

    def test_a_statusless_row_is_open_and_that_assumption_is_declared(self):
        """The honest limit. A table with no `Status` column says nothing, and
        Perry cannot know better — so it must say which rows those are rather
        than let a consumer trust the flag silently."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        t = next(x for x in d["tasks"] if x["id"] == "TASK-010")
        self.assertEqual(t["status"], "")
        self.assertTrue(t["open"])
        self.assertIn(
            "TASK-010",
            [r["id"] for r in d["conformance"]["rows_with_no_status"]],
            "a row Perry cannot classify was not declared as such")

    def test_a_row_list_printed_can_also_be_closed(self):
        """The read path and the write path must agree about what a row is.

        `1.1` taught the reader to see every `## ` section; `find()` was left
        on `P0`/`P1`/`P2`. So on Perry's own board, 20 rows under
        `## Done this period (leaves the board at next triage)` were listed by
        `list` and refused by `done` with "is not an open row on the board" —
        a false statement, about rows the same tool had just printed, that made
        every archived row permanently unclosable.

        Needing a priority is a rule about `add`: a new row has to be filed
        somewhere. It was wrongly applied to the whole write path. Both now go
        through `Board._task_sections()`, because they drifted the moment they
        did not.
        """
        p = Project(board=self.BOARD_WITH_EMPHASIS)
        _, listed = p.run("list", "--all")
        self.assertIn("TASK-010", [t["id"] for t in listed["tasks"]],
                      "the archived row is not even listed")

        code, out = p.run("done", "TASK-010", "--evidence", "BOARD.md")
        self.assertEqual(
            code, 0,
            f"a row `list` printed could not be closed: {out}")
        self.assertNotIn("TASK-010", p.board())

    def test_a_struck_through_id_is_still_findable(self):
        """`~~DATA-007~~` is how a real board retires a row. The reader already
        strips the emphasis; the writer has to match it."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| ~~TASK-900~~ | Retired | User | done | — | — |\n\n## P1", 1))
        code, out = p.run("drop", "TASK-900", "--reason", "superseded")
        self.assertEqual(code, 0, f"a struck-through id was unreachable: {out}")

    def test_evidence_is_split_and_resolved_rather_than_handed_over_raw(self):
        """One real cell: three comma-separated backticked paths, relative to
        the PROJECT root while the contract declared `state_root` — and the
        same column on the same board also used state-relative paths. Nothing
        in the string distinguishes them, so Perry resolves rather than
        shipping the ambiguity downstream."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | Multi | User | done | — | `BOARD.md`, `.perry/config.md`, `nope.md` |\n\n## P1", 1))
        _, d = p.run("list", "--all")
        t = next(x for x in d["tasks"] if x["id"] == "TASK-900")
        self.assertEqual(t["evidence_paths"], ["BOARD.md", ".perry/config.md"])
        self.assertIn({"id": "TASK-900", "paths": ["nope.md"]},
                      d["conformance"]["evidence_not_found"])
        self.assertIn("`BOARD.md`", t["evidence"], "the raw cell was lost")

    def test_a_dash_means_absent_not_a_file_named_dash(self):
        """aiMark briefly rendered an openable document named `perry/—`."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        for t in d["tasks"]:
            if t["evidence"] == "—":
                self.assertEqual(t["evidence_paths"], [])

    def test_the_changelog_names_every_shipped_version(self):
        """aiMark saw 1.0 become 1.1 mid-session and could not tell what had
        been added. "1.x may only add keys" is a strong guarantee; it is more
        useful when a consumer can see what the new keys are."""
        import re
        doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        self.assertIn("## Changelog", doc)
        major_minor = PT.LIST_CONTRACT.rsplit("/", 1)[1]
        # **A whole-heading match, not a substring.** `assertIn("### 1.9", doc)`
        # passes against `### 1.9-removed`, which a mutation demonstrated —
        # the guard would have let the entry be renamed away.
        # The version must end at a word boundary of whitespace or end-of-line,
        # so `### 1.6 — 2026-08-18` matches and `### 1.9-removed` does not.
        headings = set(re.findall(r"^###\s+(\d+\.\d+)(?:\s|$)", doc, re.M))
        self.assertIn(major_minor, headings,
                      f"the current version {major_minor} has no changelog "
                      f"entry of its own; found {sorted(headings)}")
        # **Every shipped minor, not only the current one.** A consumer jumping
        # 1.4 → 1.9 reads the entries between, and one skipped is one it cannot
        # learn about.
        major, minor = (int(x) for x in major_minor.split("."))
        for m in range(minor + 1):
            v = f"{major}.{m}"
            self.assertIn(v, headings, f"no changelog entry for {v}")

    def test_the_semantics_list_is_ordered_oldest_first(self):
        """Its whole use is "everything newer than the minor I tested against",
        which a consumer reads by walking the list. It shipped once as
        1.5, 1.9, 1.7 because an entry was written where it read well rather
        than where it belonged."""
        versions = [e["version"] for e in PT.LIST_SEMANTICS]
        keyed = [tuple(int(x) for x in v.split(".")) for v in versions]
        self.assertEqual(keyed, sorted(keyed), versions)

    def test_every_semantics_entry_names_fields_and_a_reason(self):
        """An entry saying "something changed" is the thing this array exists
        to replace."""
        for e in PT.LIST_SEMANTICS:
            self.assertTrue(e["fields"], e)
            self.assertGreater(len(e["note"]), 80, e)


class TestANewIdJoinsTheFamilyTheBoardAlreadyUses(unittest.TestCase):
    """TASK-060, from aiMark §4. On a board whose 17 rows are `AIM-001`…
    `AIM-017`, `add` minted `TASK-001`.

    Legitimate under the contract — ids are opaque and a board may carry
    several project-declared prefixes — but a user creating a task from a
    front-end watched their board sprout a second id family, and there was no
    flag with which to ask for the first. aiMark passes no id and *cannot*:
    nothing in the surface would let it.

    **The decision, and the failure mode it is avoiding.** Both halves shipped:
    `--prefix` names the family outright, and Perry adopts the board's own
    prefix *only when the board has exactly one*. It deliberately does NOT pick
    the most common one. `~/proj/gimegime-pmo` carries **36** families in its
    task tables, declared in its own `## ID prefixes (canonical)` section, and
    they are not stylistic — `IPS-*`/`ALLOC-*`/`DUE-*` mean 投资线 and
    `TECH-*`/`DATA-*` mean 工程线, filed in separate sections for a reason the
    board states. A plurality winner there mints an id that ASSERTS a
    workstream nobody chose, and an id is permanent. A foreign-looking
    `TASK-001` is visibly Perry's and claims nothing; a wrong-family `IPS-014`
    claims something false.

    So the guard for the category is not "adoption happens" — it is
    `test_a_board_with_several_families_is_not_guessed_at`, which is the case
    adoption must decline.
    """

    HDR = ("| ID | Title | Owner | Status | Next action | Evidence |\n"
           "|---|---|---|---|---|---|\n")

    def board(self, *ids: str) -> str:
        rows = "".join(f"| {i} | row | Coding Agent | not_started | — | — |\n"
                       for i in ids)
        return (f"# BOARD\n\n## P0 (must finish this period)\n\n{self.HDR}{rows}"
                f"\n## P1\n\n{self.HDR}\n## P2\n\n{self.HDR}")

    AIMARK = None  # set in setUp; the shape aiMark reported

    def setUp(self):
        self.AIMARK = self.board(*(f"AIM-{i:03d}" for i in range(1, 18)))

    def test_a_single_family_board_mints_into_its_own_family(self):
        p = Project(board=self.AIMARK)
        code, a = p.run("add", "--title", "from the front-end")
        self.assertEqual(code, 0, a)
        self.assertEqual(a["id"], "AIM-018")

    def test_the_number_continues_the_family_rather_than_restarting_it(self):
        """`mint_id` counted `TASK-` specifically. Adopting `AIM` without
        moving the counter with it would have minted `AIM-001` onto a board
        already holding `AIM-017` — the id reuse the function exists to make
        impossible, arrived by a new route."""
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "X")
        self.assertNotIn(f"| {a['id']} |", self.AIMARK,
                         f"{a['id']} was already a row on this board")
        self.assertEqual(a["id"], "AIM-018")
        _, b = p.run("add", "--title", "Y")
        self.assertEqual(b["id"], "AIM-019")

    def test_an_adopted_id_is_never_reissued_either(self):
        """The uniqueness guarantee is per family, and the journal is what
        makes it survive the disposable log — under `AIM` as under `TASK`."""
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "first")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        (p.root / ".perry" / "events.jsonl").unlink()
        _, b = p.run("add", "--title", "second")
        self.assertNotEqual(b["id"], a["id"],
                            f"{a['id']} was reissued after the derived log went")

    def test_a_board_with_several_families_is_not_guessed_at(self):
        """**The load-bearing one.** Three `IPS-` rows and one `TECH-` row: the
        most common family is `IPS`, and Perry must not take it. The families
        on a real board mean different workstreams, and an id that names the
        wrong one is a false claim that can never be withdrawn."""
        p = Project(board=self.board("IPS-001", "IPS-002", "IPS-003", "TECH-001"))
        code, a = p.run("add", "--title", "X")
        self.assertEqual(code, 0, a)
        self.assertEqual(a["prefix"], "TASK")
        self.assertTrue(a["id"].startswith("TASK-"),
                        f"Perry guessed a workstream from a plurality: {a['id']}")

    def test_a_family_with_no_numbers_is_not_given_one(self):
        """`RW-alpha` and `RW-beta` are one family and there is nothing to
        count from. Minting `RW-001` beside them would invent a numbering the
        project did not choose."""
        p = Project(board=self.board("RW-alpha", "RW-beta"))
        _, a = p.run("add", "--title", "X")
        self.assertEqual(a["prefix"], "TASK")

    def test_a_task_board_still_mints_task(self):
        """The bound. Every project that has never said otherwise is
        untouched — including Perry's own board, whose single family is
        `TASK`."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        self.assertEqual(a["id"], "TASK-001")
        self.assertEqual(a["prefix"], "TASK")

    def test_prefix_names_the_family_outright(self):
        """The half the finding actually asked for: a front-end that cannot
        pass an id must be able to ask for a family."""
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "X", "--prefix", "DOC")
        self.assertEqual(a["id"], "DOC-001")

    def test_prefix_beats_what_the_board_would_have_adopted(self):
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "X", "--prefix", "DOC")
        self.assertEqual(a["prefix"], "DOC")

    def test_prefix_refuses_a_family_the_tool_mints_for_another_register(self):
        """`RX-005` as a task would collide with the risk register's own
        numbering on the same board, and both writers would then be right
        about their own file and wrong about the project."""
        for reserved in ("RX", "USER", "CAD"):
            p = Project(board=self.AIMARK)
            code, out = p.run("add", "--title", "X", "--prefix", reserved)
            self.assertEqual(code, 1, f"--prefix {reserved} was accepted: {out}")
            self.assertNotIn(f"{reserved}-001", p.board())

    def test_prefix_refuses_a_whole_id(self):
        """`--prefix AIM-018` is the obvious mistake, and it has to refuse
        rather than mint `AIM-018-001`."""
        p = Project(board=self.AIMARK)
        code, out = p.run("add", "--title", "X", "--prefix", "AIM-018")
        self.assertEqual(code, 1, out)
        self.assertIn("--prefix", str(out))

    def test_a_multi_segment_prefix_is_allowed(self):
        """`ARCH-V2-*` is a real family on a real board. Each segment starts
        with a letter, which is the rule that separates it from an id."""
        p = Project(board=self.AIMARK)
        code, a = p.run("add", "--title", "X", "--prefix", "ARCH-V2")
        self.assertEqual(code, 0, a)
        self.assertEqual(a["id"], "ARCH-V2-001")

    def test_route_mints_from_the_same_rule_add_does(self):
        """Both verbs mint. A family adopted by one and not the other is the
        same divergence `--group` had, in the id column."""
        p = Project(tracks=TestModeAwareWrites.TRACKS, board=self.AIMARK)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "blog")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "AIM-018")

    def test_route_takes_prefix_too(self):
        p = Project(tracks=TestModeAwareWrites.TRACKS, board=self.AIMARK)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "blog", "--prefix", "DOC")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "DOC-001")

    def test_ids_in_the_non_task_registers_are_not_a_family(self):
        """`## Top risks`, `## Cadence` and `## User Input Queue` carry their
        own prefixes and are not work. Counting them would make every board
        multi-family and adoption would never fire — or worse, a board with one
        `USER-001` and no tasks would adopt `USER`."""
        p = Project(board=self.AIMARK)
        p.run("ask", "--needed", "which staging default?")
        p.run("risk-add", "--title", "a risk")
        _, a = p.run("add", "--title", "X")
        self.assertEqual(a["prefix"], "AIM")


class TestEvidenceIsResolvedForEveryRowNotOnlyLiveOnes(unittest.TestCase):
    """TASK-057, from aiMark's 2026-08-17 contract report.

    `evidence_paths` was resolved inside the board walk, and a closed row is
    not on the board — `done` removes it. So the field was empty for every
    closed row on every project. Measured on Perry's own board: **32 closed
    rows, every one carrying an evidence cell, every one `evidence_paths: []`,
    every file present on disk.**

    Two things made it invisible. `evidence` was populated, so the row did not
    look empty; and `conformance.evidence_not_found` was empty too, so a
    consumer could not tell *"Perry did not resolve this"* from *"the file is
    gone"*. aiMark rendered the document that JUSTIFIES a close as a dead
    link — the one row a reader most wants the artifact for.

    **The category is "a declared field is resolved for every row the contract
    declares it for", not "closed rows work".** A guard written as "a closed
    row resolves its evidence" would pass on a build that resolved closed rows
    and dropped, say, event-only ones. So the load-bearing assertion here is
    `test_no_row_names_an_artifact_the_payload_neither_finds_nor_reports`,
    which is an invariant over every row in the payload, and
    `test_the_same_file_resolves_open_and_closed`, which compares the two
    states on one board against one file.
    """

    def populated(self) -> "Project":
        """One board, one real file, and every row shape that carries a cell:
        open, closed, closed-with-a-file-that-is-gone, and a dash."""
        p = Project()
        _, live = p.run("add", "--title", "still going", "--priority", "P0")
        p.run("evidence", live["id"], "--evidence", "`BOARD.md`")
        _, closed = p.run("add", "--title", "finished", "--priority", "P1")
        p.run("done", closed["id"], "--evidence", "`BOARD.md`", "--rung", "V3")
        _, gone = p.run("add", "--title", "finished, artifact moved",
                        "--priority", "P2")
        p.run("done", gone["id"], "--evidence", "`evidence/2026-07/gone.md`",
              "--rung", "V3")
        p.run("add", "--title", "no evidence yet", "--priority", "P2")
        self.live, self.closed, self.gone = live["id"], closed["id"], gone["id"]
        return p

    def payload(self, p: "Project") -> dict:
        _, d = p.run("list", "--all")
        return d

    def row(self, d: dict, tid: str) -> dict:
        return next(t for t in d["tasks"] if t["id"] == tid)

    def test_a_closed_row_resolves_the_document_that_justifies_its_close(self):
        p = self.populated()
        t = self.row(self.payload(p), self.closed)
        self.assertFalse(t["open"], "the fixture's closed row is not closed")
        self.assertEqual(t["evidence_paths"], ["BOARD.md"])

    def test_the_same_file_resolves_open_and_closed(self):
        """The finding in one assertion: same board, same path, two rows whose
        only difference is that one of them finished."""
        d = self.payload(self.populated())
        self.assertEqual(self.row(d, self.closed)["evidence_paths"],
                         self.row(d, self.live)["evidence_paths"],
                         "a path stopped resolving the day the row closed")

    def test_a_closed_rows_missing_file_is_reported_not_silently_empty(self):
        """The other half. `[]` used to mean both "gone" and "never looked",
        so a consumer had no way to tell a dead link from an unread field."""
        d = self.payload(self.populated())
        self.assertEqual(self.row(d, self.gone)["evidence_paths"], [])
        self.assertIn({"id": self.gone, "paths": ["evidence/2026-07/gone.md"]},
                      d["conformance"]["evidence_not_found"])

    def test_no_row_names_an_artifact_the_payload_neither_finds_nor_reports(self):
        """The invariant, over every row. A non-empty `Evidence` cell must
        produce either a resolved path or a `conformance` entry — `[]` and
        silence together is the state that cannot be interpreted."""
        d = self.payload(self.populated())
        reported = {e["id"] for e in d["conformance"]["evidence_not_found"]}
        self.assertTrue(d["tasks"])
        for t in d["tasks"]:
            if t["evidence"].strip().lower() in PT.ABSENT:
                continue
            self.assertTrue(
                t["evidence_paths"] or t["id"] in reported,
                f"{t['id']} names {t['evidence']!r} and the payload neither "
                f"resolved it nor reported it")

    def test_a_row_with_no_evidence_still_reports_neither(self):
        """The bound: resolving more must not start inventing entries for the
        rows that legitimately cite nothing. aiMark once rendered an openable
        document named `perry/—`."""
        d = self.payload(self.populated())
        reported = {e["id"] for e in d["conformance"]["evidence_not_found"]}
        for t in d["tasks"]:
            if t["evidence"].strip() == "—":
                self.assertEqual(t["evidence_paths"], [])
                self.assertNotIn(t["id"], reported)

    def test_a_finished_row_still_on_the_board_resolves_too(self):
        """The third row shape, and the one that had the field and the cell
        disagreeing: a project that stages finished work under its own heading
        keeps the row, so `evidence` came off the event and `evidence_paths`
        off the board cell. Resolving after the merge makes them one cell."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n"
            "| TASK-900 | Staged | User | done | — | `BOARD.md` |\n\n## P1", 1))
        t = self.row(self.payload(p), "TASK-900")
        self.assertFalse(t["open"])
        self.assertEqual(t["evidence_paths"], ["BOARD.md"])

    def test_the_report_is_ordered_by_id_not_by_where_the_row_sat(self):
        """`evidence_not_found` used to be appended during the board walk, so
        its order was board order — and a closed row has no board position at
        all. Ordered by id, a consumer diffing two payloads of an unchanged
        project sees nothing, whichever section a row moved between.

        The fixture puts the ids on the board in DESCENDING order, so board
        order and id order are different lists and the assertion can fail.
        """
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n"
            "| TASK-903 | c | User | not_started | — | `c-gone.md` |\n"
            "| TASK-902 | b | User | not_started | — | `b-gone.md` |\n"
            "| TASK-901 | a | User | not_started | — | `a-gone.md` |\n\n## P1", 1))
        reported = [e["id"] for e in
                    self.payload(p)["conformance"]["evidence_not_found"]]
        self.assertEqual(reported, ["TASK-901", "TASK-902", "TASK-903"])

    def test_the_report_is_stable_across_two_reads(self):
        p = self.populated()
        self.assertEqual(self.payload(p)["conformance"]["evidence_not_found"],
                         self.payload(p)["conformance"]["evidence_not_found"])


class TestUserInputQueueHasAWriter(unittest.TestCase):
    """TASK-039. The section had readers, a dashboard row, and no writer.

    The cost was measurable rather than argued: **both rows on Perry's own
    board carried `Idle: —`** — the one field the queue exists for, unfilled,
    because a human had to type a number that is wrong the next morning. And
    `perry-state` counted answered rows as pending, so the dashboard reported
    two people waiting on the user when both had been answered the day before.
    """

    def project(self) -> "Project":
        return Project()

    def test_ask_mints_an_id_and_stamps_the_date(self):
        p = self.project()
        code, a = p.run("ask", "--needed", "Staleness threshold", "--blocks", "TASK-005")
        self.assertEqual(code, 0, a)
        self.assertEqual(a["id"], "USER-001")
        self.assertTrue(re.fullmatch(r"\d{4}-\d{2}-\d{2}", a["asked"]))
        self.assertIn("| USER-001 |", p.board())
        self.assertIn("TASK-005", p.board())

    def test_the_section_is_created_after_the_priority_tables(self):
        """`ensure_section` inserted before `## P0`, which is right for
        `## Intake` — it reads above the work it becomes — and wrong here. A
        standup does not open with a list of open questions."""
        p = self.project()
        p.run("ask", "--needed", "X")
        heads = [l for l in p.board().split("\n") if l.startswith("## ")]
        self.assertLess(heads.index("## P0 (must finish this period)"),
                        next(i for i, h in enumerate(heads)
                             if h.startswith("## User Input Queue")))

    def test_a_question_with_no_text_is_refused(self):
        p = self.project()
        code, out = p.run("ask")
        self.assertEqual(code, 1)
        self.assertIn("--needed", str(out))

    def test_answering_records_the_answer_and_the_date(self):
        p = self.project()
        p.run("ask", "--needed", "Threshold?")
        code, out = p.run("answer", "USER-001", "--answer", "30 days")
        self.assertEqual(code, 0, out)
        row = next(l for l in p.board().split("\n") if l.startswith("| USER-001 |"))
        self.assertIn("answered", row)
        self.assertIn("30 days", row)

    def test_answering_without_the_answer_is_refused(self):
        """Flipping the status without recording what was decided leaves the
        row closed and the decision nowhere."""
        p = self.project()
        p.run("ask", "--needed", "X")
        code, out = p.run("answer", "USER-001")
        self.assertEqual(code, 1)
        self.assertIn("--answer", str(out))

    def test_answering_twice_is_refused(self):
        p = self.project()
        p.run("ask", "--needed", "X")
        p.run("answer", "USER-001", "--answer", "first")
        code, out = p.run("answer", "USER-001", "--answer", "second")
        self.assertEqual(code, 1)
        self.assertIn("already answered", str(out))

    def test_ids_are_not_reused_after_an_answer(self):
        p = self.project()
        p.run("ask", "--needed", "one")
        p.run("answer", "USER-001", "--answer", "done")
        _, b = p.run("ask", "--needed", "two")
        self.assertEqual(b["id"], "USER-002")

    def test_idle_is_computed_from_asked_not_read_from_a_typed_cell(self):
        """The whole reason `Asked` exists. A stored age is stale the next
        morning, which is why a real project had already dropped the `Idle`
        column and why both of Perry's own rows read `—`."""
        p = self.project()
        p.run("ask", "--needed", "recent")
        p.run("ask", "--needed", "old", "--arrived", "2020-01-01")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        q = json.loads(r.stdout)["user_input_queue"]
        self.assertEqual(q["count"], 2)
        self.assertEqual(q["oldest"]["id"], "USER-002",
                         "the oldest was not chosen by asked-date")
        self.assertGreater(q["oldest"]["idle_days"], 2000)

    def test_an_answered_row_leaves_the_pending_count(self):
        p = self.project()
        p.run("ask", "--needed", "X")
        p.run("answer", "USER-001", "--answer", "y")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout)["user_input_queue"]["count"], 0)

    def test_a_board_that_already_has_the_section_gains_the_asked_column(self):
        """`ensure_columns` existed for the priority tables from the day mode
        columns landed; its sibling for named sections did not, so the date
        would have been dropped silently — the defect that lost
        `--commitment`."""
        # The fixture already carries the section, in the four-column shape a
        # real project uses — no `Asked`, and no `Idle` either.
        p = Project(board=BOARD.replace(
            "| USER-id | Needed from user | Blocks | Idle | Status |\n|---|---|---|---|---|\n",
            "| USER-id | Needed from user | Blocks | Status |\n|---|---|---|---|\n"
            "| USER-900 | pre-existing | — | pending |\n", 1))
        code, a = p.run("ask", "--needed", "new one")
        self.assertEqual(code, 0, a)
        header = next(l for l in p.board().split("\n") if l.startswith("| USER-id |"))
        self.assertIn("Asked", header)
        old = next(l for l in p.board().split("\n") if l.startswith("| USER-900 |"))
        self.assertEqual(len(old.strip("|").split("|")),
                         len(header.strip("|").split("|")),
                         "an existing row was not widened with the new column")
        self.assertEqual(a["id"], "USER-901", "the pre-existing id was reused")


class TestAgeIsKnownOrDeclaredUnknown(unittest.TestCase):
    """`triage`'s entire staleness mechanism is age comparisons.

    A row with no event and no date cell has no age, and the six standard
    board columns carry no date — so on any board written before the tool
    existed, most rows read as fresh forever. **6 of 9 open rows on Perry's
    own board**, including the two whose `Next action` still described
    blockers that had already been fixed.

    Found while updating `triage` to read the payload: the procedure said
    "measured from `updated`, or from the row's date cells when there is no
    event log", and those date cells do not exist. A fallback naming a source
    that is not there is the defect this project keeps finding — written, this
    time, by the same author who had just written the rule against it.
    """

    #: A board carrying one row the tool never wrote.
    HAND_WRITTEN = (
        "| ID | Title | Owner | Status | Next action | Evidence |\n"
        "|---|---|---|---|---|---|\n"
        "| TASK-900 | predates the tool | User | in_progress | — | — |\n\n## P1")
    PLAIN = ("| ID | Title | Owner | Status | Next action | Evidence |\n"
             "|---|---|---|---|---|---|\n\n## P1")

    def test_a_hand_written_row_is_declared_ageless_not_treated_as_fresh(self):
        """**Amended at contract 1.9, and the amendment is the point.**

        This asserted `TASK-900` appears in `rows_with_no_computable_age` on a
        project with **no event log at all** — where every open row qualifies by
        construction, so the array restated `has_event_log: false` once per row.
        17 of 17 on the consumer that reported it.

        The claim this test exists for — *a hand-written row is declared
        ageless, not treated as fresh* — is unchanged and still asserted. What
        moved is which field carries it when the whole project predates the
        writer. The discriminating case is the test below.
        """
        p = Project(board=BOARD.replace(self.PLAIN, self.HAND_WRITTEN, 1))
        _, d = p.run("list", "--all")
        t = next(x for x in d["tasks"] if x["id"] == "TASK-900")
        self.assertIsNone(t["updated"])
        self.assertFalse(d["conformance"]["has_event_log"])
        self.assertEqual(d["conformance"]["rows_with_no_computable_age"], [],
                         "the flag already says this; the list restated it")

    def test_a_hand_written_row_beside_tool_written_ones_is_still_flagged(self):
        """The case the suppression must not swallow, and the reason it is a
        suppression rather than a deletion: with an event log present, a row
        the tool never wrote is a real finding about **that row** — not a fact
        about the project — and the array is the only thing that names it."""
        p = Project(board=BOARD.replace(self.PLAIN, self.HAND_WRITTEN, 1))
        p.run("add", "--title", "tool written", "--priority", "P0")
        _, d = p.run("list", "--all")
        self.assertTrue(d["conformance"]["has_event_log"])
        self.assertIn("TASK-900",
                      d["conformance"]["rows_with_no_computable_age"])

    def test_a_tool_written_row_has_an_age_and_is_not_flagged(self):
        """The check must run AFTER the event merge. Placed during the board
        walk it flagged rows the tool had just created, because `updated` was
        not filled in yet — measured 9 flagged where 6 was the truth."""
        p = Project()
        _, a = p.run("add", "--title", "tool written", "--priority", "P0")
        _, d = p.run("list", "--all")
        t = next(x for x in d["tasks"] if x["id"] == a["id"])
        self.assertIsNotNone(t["updated"])
        self.assertNotIn(a["id"], d["conformance"]["rows_with_no_computable_age"])

    def test_a_row_with_a_stage_clock_is_ageable_without_events(self):
        """`Stage since` and `Arrived` are dates on the row itself, so a
        pipeline or queue row is ageable even with no event log."""
        p = Project(tracks=TestModeAwareWrites.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        (p.root / ".perry" / "events.jsonl").unlink()
        _, d = p.run("list", "--all")
        self.assertNotIn(a["id"], d["conformance"]["rows_with_no_computable_age"])

    def test_closed_rows_are_not_reported_as_ageless(self):
        """The question is "is this still live", which a closed row answers."""
        p = Project()
        _, a = p.run("add", "--title", "X", "--priority", "P0")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        _, d = p.run("list", "--all")
        self.assertNotIn(a["id"], d["conformance"]["rows_with_no_computable_age"])


class TestNextActionPointingAtFinishedWork(unittest.TestCase):
    """An open row still waiting on something that closed.

    Orthogonal to the age check: a row can have been touched yesterday and
    still cite work that finished. Measured before shipping — it fires once on
    Perry's own board, and it does NOT catch the three rows that motivated the
    whole question, whose `Next action` is prose about a review verdict and
    cites no id. Those are caught by `rows_with_no_computable_age`. Two
    signals; neither replaces the other, and saying otherwise would oversell
    both.
    """

    def board_citing(self, cited: str) -> "Project":
        """A citation in the cell is scanned by `mint_id` — correctly, so a
        number named anywhere is never reissued. The first version of this
        helper hardcoded the id it expected to be minted next and collided
        with its own citation."""
        return Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            f"| TASK-900 | waiting | User | not_started | blocked-by {cited} | — |\n\n## P1", 1))

    def blocked_by_a_closed_task(self):
        """Create the blocker, close it, THEN point the waiting row at it."""
        p = self.board_citing("nothing yet")
        _, a = p.run("add", "--title", "the blocker", "--priority", "P1")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        p.run("status", "TASK-900", "--status", "blocked",
              "--reason", f"blocked-by {a['id']}")
        return p, a["id"]

    def test_a_row_citing_a_closed_task_is_reported(self):
        """The original triple, asserted as a subset since 1.13.

        The entry gained `row_status`, `blocked_stale`, `readings` and `means`
        — TASK-142, because a bare triple reads as a wording complaint and was
        silenced as one on 2026-08-20. `tests/test_stranded_rows.py` holds what
        those four have to say; this stays the check that the three original
        keys never moved.
        """
        p, blocker = self.blocked_by_a_closed_task()
        _, d = p.run("list", "--all")
        found = d["conformance"]["next_action_cites_closed"]
        self.assertEqual(1, len(found))
        self.assertEqual({"id": "TASK-900", "cites": blocker, "status": "done"},
                         {k: found[0][k] for k in ("id", "cites", "status")})

    def test_a_row_citing_an_open_task_is_not_reported(self):
        p = self.board_citing("nothing yet")
        _, a = p.run("add", "--title", "still open", "--priority", "P1")
        p.run("status", "TASK-900", "--status", "blocked",
              "--reason", f"blocked-by {a['id']}")
        _, d = p.run("list", "--all")
        self.assertEqual(d["conformance"]["next_action_cites_closed"], [])

    def test_a_closed_row_citing_a_closed_task_is_not_reported(self):
        """The question is what still needs doing."""
        p, _ = self.blocked_by_a_closed_task()
        p.run("done", "TASK-900", "--evidence", "e.md", "--rung", "V3")
        _, d = p.run("list", "--all")
        self.assertEqual(d["conformance"]["next_action_cites_closed"], [])

    def test_an_id_family_this_payload_cannot_resolve_is_not_claimed_on(self):
        """`DESIGN-` and `USER-` ids are all over these cells. Reporting them
        as "not closed" would assert something the payload cannot know."""
        p = self.board_citing("DESIGN-003")
        _, d = p.run("list", "--all")
        self.assertEqual(d["conformance"]["next_action_cites_closed"], [])


class TestCorrectingANextAction(unittest.TestCase):
    """TASK-041. Found by running a triage rather than by reading code.

    `next_action_cites_closed` reported a row whose next step named work that
    had finished, and there was **no way to correct it**. `status` is the only
    writer of that cell and it refuses a no-op transition — correctly, because
    a journal line asserting `not_started → not_started` records a change that
    did not happen. So the alternatives were a status change the row did not
    warrant, or a hand edit, and the single most common triage action had no
    tool path.

    Relaxing `status` was the wrong fix. A status change and a correction are
    different events; folding them would make "the plan changed" and "the state
    changed" the same journal line forever.
    """

    def test_the_cell_is_rewritten_and_the_status_is_untouched(self):
        p = Project()
        _, a = p.run("add", "--title", "X", "--priority", "P0", "--next", "old plan")
        code, out = p.run("next", a["id"], "--next", "new plan")
        self.assertEqual(code, 0, out)
        row = next(l for l in p.board().split("\n") if l.startswith(f"| {a['id']} |"))
        self.assertIn("new plan", row)
        self.assertNotIn("old plan", row)
        self.assertIn("not_started", row, "the status moved")

    def test_it_is_its_own_event_not_a_status_change(self):
        """A reader has to be able to tell a corrected plan from a moved row."""
        p = Project()
        _, a = p.run("add", "--title", "X", "--priority", "P0")
        p.run("next", a["id"], "--next", "revised")
        self.assertEqual([e["event"] for e in p.events()], ["add", "next"])
        self.assertIn("next action · revised", p.journal())

    def test_rewriting_to_the_same_text_is_refused(self):
        """Same reason `status` refuses a no-op: a journal line recording a
        change that did not happen."""
        p = Project()
        _, a = p.run("add", "--title", "X", "--priority", "P0", "--next", "same")
        code, out = p.run("next", a["id"], "--next", "same")
        self.assertEqual(code, 1)
        self.assertIn("already", str(out))

    def test_an_empty_next_is_refused(self):
        p = Project()
        _, a = p.run("add", "--title", "X", "--priority", "P0")
        code, out = p.run("next", a["id"])
        self.assertEqual(code, 1)
        self.assertIn("--next", str(out))

    def test_a_finished_row_still_on_the_board_is_refused(self):
        """A row that has finished has no next step, and writing one would put
        a live-looking instruction on completed work. `done` removes the row,
        so the case that matters is a board that stages finished work in place
        — which Perry's own did, for twenty rows."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | finished in place | User | done | — | e.md |\n\n## P1", 1))
        code, out = p.run("next", "TASK-900", "--next", "something")
        self.assertEqual(code, 1)
        self.assertIn("finished", str(out))

    def test_it_is_classified_as_a_task_event(self):
        """`TASK_EVENTS` / `SECTION_EVENTS` is a partition, and a subcommand
        that forgets to join one silently stops appearing in `list`."""
        self.assertIn("next", PT.TASK_EVENTS)
        self.assertNotIn("next", PT.SECTION_EVENTS)


class TestTheStageClockHasOneWriter(unittest.TestCase):
    """V4 review 2026-08-17, three blocking findings. 543 tests passed at the
    time and not one of them covered these.

    `Status` and `Stage` are orthogonal by design. Every defect here came from
    a path that forgot that.
    """

    TRACKS = TestModeAwareWrites.TRACKS

    def cells(self, p: "Project", tid: str) -> dict:
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)], PT.split_row(row)))

    def age(self, p: "Project", tid: str, days_ago: str):
        b = p.root / "BOARD.md"
        b.write_text(b.read_text().replace(self.cells(p, tid)["stage since"], days_ago))
        p.import_board()

    def test_start_does_not_restamp_the_stage_clock(self):
        """B-1. `dispatch` calls `start` on every automated run, so an item
        that had sat in `review` for a fortnight reported zero days' dwell —
        blinding pipeline triage's first question, the one aimed at that
        mode's signature failure."""
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        self.age(p, a["id"], "2026-08-01")
        p.run("start", a["id"])
        c = self.cells(p, a["id"])
        self.assertEqual(c["stage since"], "2026-08-01",
                         "starting work moved the stage clock without the "
                         "stage changing")
        self.assertEqual(c["stage"], "brief", "the stage moved")

    def test_a_stage_move_still_restamps_it(self):
        """The other half — removing the restamp entirely would be the 2026-08
        defect the clock was added to fix."""
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog", "--priority", "P0")
        self.age(p, a["id"], "2020-01-01")
        p.run("stage", a["id"], "--stage", "draft")
        self.assertNotEqual(self.cells(p, a["id"])["stage since"], "2020-01-01")

    def test_stage_creates_the_column_it_writes_into(self):
        """B-2b. `replace_row` maps values onto headers, so a missing header
        discards the value and the call still exits 0."""
        p = Project(tracks=self.TRACKS, board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence | Track | Stage |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| TASK-900 | no clock | User | not_started | — | — | blog | brief |\n\n## P1", 1))
        code, out = p.run("stage", "TASK-900", "--stage", "draft")
        self.assertEqual(code, 0, out)
        self.assertIn("Stage since", p.board(), "the column was not created")
        self.assertTrue(self.cells(p, "TASK-900")["stage since"],
                        "the stamp was silently dropped")


class TestRoutingRespectsTheTracksMode(unittest.TestCase):
    """B-2a. `stages[1]` is the QUEUE rule — a queue row skips `new`, which
    means "sitting in intake", because it has just left. A pipeline or inquiry
    row has no such stage to skip, and routing them to `stages[1]` silently
    skipped `brief` / `open`."""

    TRACKS = TestModeAwareWrites.TRACKS

    def routed(self, track: str):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-10")
        _, r = p.run("route", "1", "--track", track, "--priority", "P1")
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |") and "Track" in l)
        row = next(l for l in board.split("\n") if l.startswith(f"| {r['id']} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)], PT.split_row(row)))

    def test_a_pipeline_row_enters_at_the_first_stage(self):
        self.assertEqual(self.routed("blog")["stage"], "brief")

    def test_a_queue_row_still_skips_the_intake_stage(self):
        self.assertEqual(self.routed("ops")["stage"], "triaged")

    def test_a_pipeline_row_gets_the_clock_its_mode_reads(self):
        """Routing gave every row `Arrived` regardless, so a pipeline row
        arrived with no dwell clock — and `rows_with_no_computable_age` could
        not report it, because `arrived` was non-empty."""
        c = self.routed("blog")
        self.assertTrue(c.get("stage since"), "no dwell clock on a pipeline row")

    def test_a_queue_row_keeps_the_arrival_date(self):
        """Every SLA number is `today − Arrived`."""
        self.assertEqual(self.routed("ops")["arrived"], "2026-08-10")


class TestAnIntakeRowTakesExactlyOneOutcome(unittest.TestCase):
    """B-3. Both `modes/queue.md` and `subcommands.md` state the rule; nothing
    enforced it. `answer`, `status`, `stage` and `risk-clear` all refuse a
    repeat transition — this was the fourth implementation and the only one
    that did not.

    Live rather than theoretical: discharged rows stay in intake until the
    review period closes, so the next drain walks them again.
    """

    TRACKS = TestModeAwareWrites.TRACKS

    def test_routing_twice_is_refused(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        _, first = p.run("route", "1", "--track", "ops")
        code, out = p.run("route", "1", "--track", "ops")
        self.assertEqual(code, 1, "a second task was minted for one request")
        self.assertIn("already has an outcome", str(out))
        self.assertIn(first["id"], p.board(), "the first routing was erased")

    def test_resolving_a_routed_row_is_refused(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        p.run("route", "1", "--track", "ops")
        code, _ = p.run("resolve-intake", "1", "--outcome", "dropped",
                        "--reason", "changed our mind")
        self.assertEqual(code, 1)

    def test_resolving_twice_is_refused(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        p.run("resolve-intake", "1", "--outcome", "dropped", "--reason", "no")
        code, out = p.run("resolve-intake", "1", "--outcome", "deferred",
                          "--reason", "later")
        self.assertEqual(code, 1, "a recorded drop was flipped to a defer")

    def test_a_placeholder_outcome_is_not_a_discharge(self):
        """`—` is how the board writes "nothing yet"."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        code, out = p.run("route", "1", "--track", "ops")
        self.assertEqual(code, 0, out)


class TestIntakeIsReadableAndSweepable(unittest.TestCase):
    """V4 review M-5 and M-6.

    M-5: `route <n>` and `resolve-intake <n>` act on a row POSITION, and no
    payload carried one — so the only way to run the drain was to open
    `BOARD.md` and count, twenty lines below the rule forbidding exactly that.

    M-6: `modes/queue.md` says discharged rows leave at the end of the review
    period, and grep found that rule in that one file and nowhere else. It
    matters because the same file rests its overflow argument on it: intake
    pressure is supposed to mean *taking on more than you discharge*, not
    *having discharged a lot*.
    """

    TRACKS = TestModeAwareWrites.TRACKS

    def loaded(self) -> "Project":
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "oldest", "--arrived", "2026-08-01")
        p.run("intake", "--title", "newer", "--arrived", "2026-08-15")
        return p

    def test_the_row_numbers_the_procedure_needs_are_in_the_payload(self):
        _, d = self.loaded().run("list", "--all")
        self.assertEqual([r["n"] for r in d["intake"]["rows"]], [1, 2])
        self.assertEqual(d["intake"]["undischarged"], 2)

    def test_the_oldest_undischarged_row_is_named(self):
        """Triage step 0 works oldest-first, and reports a row still sitting
        after 14 days by elapsed time."""
        i = self.loaded().run("list", "--all")[1]["intake"]
        self.assertEqual(i["oldest_undischarged"], 1)
        self.assertGreater(i["rows"][0]["age_days"], i["rows"][1]["age_days"])

    def test_discharging_moves_a_row_out_of_the_undischarged_count(self):
        p = self.loaded()
        p.run("resolve-intake", "1", "--outcome", "dropped", "--reason", "no")
        i = p.run("list", "--all")[1]["intake"]
        self.assertEqual(i["undischarged"], 1)
        self.assertEqual(i["oldest_undischarged"], 2)
        self.assertTrue(i["rows"][0]["discharged"])

    def test_sweep_moves_discharged_rows_to_the_journal_with_their_outcome(self):
        p = self.loaded()
        p.run("resolve-intake", "1", "--outcome", "dropped", "--reason", "covered elsewhere")
        code, out = p.run("intake-sweep")
        self.assertEqual(code, 0, out)
        self.assertNotIn("oldest", p.board(), "the discharged row is still on the board")
        self.assertIn("newer", p.board(), "an undischarged row was swept")
        self.assertIn("covered elsewhere", p.journal(),
                      "the outcome did not survive leaving the board")

    def test_sweeping_with_nothing_discharged_is_refused(self):
        """A no-op that reports success reads as 'the board is tidy'."""
        code, out = self.loaded().run("intake-sweep")
        self.assertEqual(code, 1)
        self.assertIn("triage step 0", str(out))

    def test_a_project_with_no_intake_section_reports_an_empty_block(self):
        """Not every project is queue-shaped, and that is not an error."""
        _, d = Project().run("list", "--all")
        self.assertEqual(d["intake"]["rows"], [])
        self.assertEqual(d["intake"]["undischarged"], 0)
        self.assertIsNone(d["intake"]["oldest_undischarged"])


class TestWritingToAProjectsOwnSections(unittest.TestCase):
    """V4 review M-8. On the only year-old real project available, `add`
    refused: "BOARD.md has no `## P1` section".

    That board files work under `## Open — 投资线` and `## Open — 工程线 ·
    phase #004`. The read side learned to see every section in 1.1; the write
    side stayed on P0/P1/P2, so arrivals could be recorded and never routed.

    Creating the missing priority section would have been the wrong fix —
    "no automatic rewrite of a project's existing structure" is an Anti-Goal,
    and a board filed by workstream is not malformed. The project says where
    the row goes instead.
    """

    WORKSTREAM = """# BOARD

## Open — 工程线

| ID | Title | Owner | Status |
|---|---|---|---|
| TECH-1 | pre-existing | Coding Agent | not_started |

## Backbone

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""

    def test_a_board_with_no_priority_section_is_refused_with_its_own_headings(self):
        """A refusal that names what the project actually has is the
        difference between a wall and a door."""
        p = Project(board=self.WORKSTREAM)
        code, out = p.run("add", "--title", "X")
        self.assertEqual(code, 1)
        self.assertIn("Open — 工程线", str(out), "the refusal listed no sections")
        self.assertIn("--group", str(out))

    def test_group_files_the_row_under_the_projects_own_heading(self):
        p = Project(board=self.WORKSTREAM)
        code, a = p.run("add", "--title", "new work", "--group", "Open — 工程线")
        self.assertEqual(code, 0, a)
        section = p.board().split("## Backbone")[0]
        self.assertIn(a["id"], section, "the row did not land in the named section")

    def test_a_narrower_section_gains_the_columns_rather_than_losing_the_data(self):
        """Writing only what fits would drop `Next action` silently — exactly
        how `--commitment` was lost."""
        p = Project(board=self.WORKSTREAM)
        _, a = p.run("add", "--title", "new work", "--group", "Open — 工程线",
                     "--next", "the actual next step")
        self.assertIn("the actual next step", p.board())
        old = next(l for l in p.board().split("\n") if l.startswith("| TECH-1 |"))
        header = next(l for l in p.board().split("\n") if l.startswith("| ID |"))
        self.assertEqual(len(PT.split_row(old)), len(PT.split_row(header)),
                         "an existing row was not widened with the new columns")
        self.assertIn("pre-existing", old, "existing data was disturbed")

    def test_a_heading_ending_in_punctuation_resolves(self):
        """`\\b` needs a word char on one side, so `## P2 (低优先 carry)` never
        matched and `--group` refused a section the same tool had just listed."""
        p = Project(board=self.WORKSTREAM.replace(
            "## Open — 工程线", "## P2 (低优先 carry)", 1))
        code, out = p.run("add", "--title", "X", "--group", "P2 (低优先 carry)")
        self.assertEqual(code, 0, out)

    def test_a_priority_board_is_unaffected(self):
        """The default path must not change for a project using P0/P1/P2."""
        p = Project()
        code, a = p.run("add", "--title", "X", "--priority", "P0")
        self.assertEqual(code, 0, a)
        self.assertIn(a["id"], p.board().split("## P1")[0])


class TestANarrowSectionIsWidenedWhicheverFlagNamedIt(unittest.TestCase):
    """Round-5 review B-3. The M-8 widening landed on `--group` alone.

    `add --group P1` widened a four-column section and succeeded; `add
    --priority P1` and `route --priority P1` on **the same section** refused
    with "BOARD.md's columns cannot be resolved". The board does not know which
    flag named it, so two answers is one of them being wrong — and the narrow
    case is if anything MORE likely under a priority heading, since a
    hand-written `## P2 (低优先 carry)` is the shape a project reaches for when
    it wants a short list.

    Measured on a copy of a real adopted project: `intake` wrote the row and
    `route 1 --track ops --priority P2` refused, so `## Intake` filled and could
    never be drained. TASK-020's deliverable 3 is *"`triage` gains a first step:
    drain intake"* — the routing half did not run at all.
    """

    NARROW = """# BOARD

## P1

| ID | Title | Owner | Status |
|---|---|---|---|
| TECH-1 | pre-existing | Coding Agent | not_started |
"""

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | commitments | new->triaged->resolved | — | 5d | monthly | V2 |\n")

    def widths(self, p: Project) -> tuple[str, list[str]]:
        header = next(l for l in p.board().split("\n") if l.startswith("| ID |"))
        return header, [l for l in p.board().split("\n")
                        if l.startswith(("| TECH-1 |", "| TASK-"))]

    def test_add_by_priority_widens_it_the_way_add_by_group_does(self):
        p = Project(board=self.NARROW)
        code, a = p.run("add", "--title", "new work", "--priority", "P1",
                        "--next", "the actual next step")
        self.assertEqual(code, 0, f"the priority path refused a section the "
                                  f"group path accepts: {a}")
        self.assertIn("the actual next step", p.board(),
                      "`Next action` was dropped silently")

    def test_the_two_flags_produce_the_same_header(self):
        """The claim in one assertion: same board, same section, same result."""
        by_group = Project(board=self.NARROW)
        by_group.run("add", "--title", "x", "--group", "P1", "--next", "n")
        by_priority = Project(board=self.NARROW)
        by_priority.run("add", "--title", "x", "--priority", "P1", "--next", "n")
        self.assertEqual(self.widths(by_group)[0], self.widths(by_priority)[0])

    def test_widening_pads_the_rows_that_were_already_there(self):
        p = Project(board=self.NARROW)
        p.run("add", "--title", "new work", "--priority", "P1")
        header, rows = self.widths(p)
        for r in rows:
            self.assertEqual(len(PT.split_row(r)), len(PT.split_row(header)),
                             f"row width diverged from the header:\n  {r}")
        old = next(r for r in rows if r.startswith("| TECH-1 |"))
        self.assertIn("pre-existing", old, "existing data was disturbed")
        self.assertIn("not_started", old, "a cell shifted into another column")

    def test_the_intake_drain_runs_on_a_narrow_pre_existing_board(self):
        """The end-to-end statement, and the one that was failing in the
        field: a section the tool itself creates and fills must be drainable
        onto the board the project already had."""
        p = Project(tracks=self.TRACKS, board=self.NARROW)
        code, _ = p.run("intake", "--title", "客户要对账", "--arrived", "2026-08-05")
        self.assertEqual(code, 0)
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P1")
        self.assertEqual(code, 0, f"the drain refused on a board `intake` had "
                                  f"just filled: {out}")
        row = next(l for l in p.board().split("\n")
                   if l.startswith(f"| {out['id']} |"))
        self.assertIn("2026-08-05", row, "the SLA clock was lost at routing")
        self.assertIn("客户要对账", row)

    def test_an_unreadable_header_is_still_refused_not_widened(self):
        """The bound on the fix. A section whose IDENTITY columns cannot be
        resolved is not a narrow table, it is an unknown one — appending `ID`
        and `Title` beside `甲` and `乙` writes a row with two blank leading
        cells and exits 0, which is `check_header`'s reason for existing wearing
        a disguise. Both flags refuse it."""
        board = self.NARROW.replace("| ID | Title |", "| 甲 | 乙 |")
        for flag in ("--priority", "--group"):
            p = Project(board=board)
            code, out = p.run("add", "--title", "X", flag, "P1")
            self.assertEqual(code, 1, f"{flag} wrote against an unreadable "
                                      f"header: {out}")
            self.assertIn("i18n.columns", str(out))
            self.assertNotIn("TASK-001", p.board())


class TestEveryWriterThatFilesARowReadsGroup(unittest.TestCase):
    """TASK-053. `--group` parsed into `args.group` and `cmd_route` never read
    it, so the intake drain could not run on a board with no `## P0`/`## P1`/
    `## P2` at all — which is `~/proj/gimegime-pmo`'s actual shape.

    The flag was added for `cmd_add`, and `cmd_add` is where it stayed. What
    makes it worse than a missing feature is that `check_priority`'s own
    refusal recommends it — *"pass the whole heading to `--group` instead"* —
    so a user who read the refusal and did exactly what it said got refused a
    second time by the same tool.

    **Why this is a different fixture, not a stronger assertion.** The guard
    that was supposed to cover this is
    `TestANarrowSectionIsWidenedWhicheverFlagNamedIt`'s
    `test_the_intake_drain_runs_on_a_narrow_pre_existing_board`, and its board
    **has a `## P1`**. It grades narrow COLUMNS. A guard whose fixture carries
    the heading cannot fail on the heading being missing, however hard it
    asserts — the round-5 fix repaired one half of "the board does not care
    which flag named the section" and the guard was built out of the half that
    had been repaired. The category here is *a board that does not use
    priority headings*, so the fixture has none.
    """

    # `~/proj/gimegime-pmo`'s shape, minus the rows: work filed under the
    # project's own workstream headings, and not a `## P0`/`## P1`/`## P2`
    # anywhere in the file.
    WORKSTREAM = """# BOARD

## Open — 工程线 · phase #004 W24（流程层）

| ID | Title | Owner | Status |
|---|---|---|---|
| TECH-1 | pre-existing | Coding Agent | not_started |

## Backbone

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""
    HEADING = "Open — 工程线 · phase #004 W24（流程层）"

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | commitments | new->triaged->resolved | — | 5d "
              "| monthly | V2 |\n")

    def drained(self, *extra) -> tuple[Project, int, dict]:
        p = Project(tracks=self.TRACKS, board=self.WORKSTREAM)
        code, _ = p.run("intake", "--title", "客户要对账", "--arrived", "2026-08-05")
        self.assertEqual(code, 0)
        code, out = p.run("route", "1", "--track", "ops", *extra)
        return p, code, out

    def section_of(self, p: Project, heading: str) -> str:
        return p.board().split(f"## {heading}", 1)[1].split("\n## ", 1)[0]

    def test_route_files_the_row_under_the_projects_own_heading(self):
        """The statement of the defect. Before this, exit 1 on every form of
        the command — there was no landing site and no way to name one."""
        p, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, f"the drain refused a board that files work "
                                  f"under its own headings: {out}")
        self.assertIn(out["id"], self.section_of(p, self.HEADING),
                      "the row did not land in the section --group named")
        self.assertNotIn("## P1", p.board(),
                         "a priority section was created on a board that has none")

    def test_the_intake_table_survives_the_drain(self):
        """**The drain bricked the queue after one row, at exit 0.**

        `ensure_section` anchors `## Intake` before `## P0` *or at the end of
        the file*, so on a board with no priority heading — this fixture, and
        `~/proj/gimegime-pmo`'s actual shape — Intake lands **below** every
        landing site. `cmd_route` captured the intake row's line index, then
        `append_row` inserted above it, then wrote the outcome to the now-stale
        index: the separator row was overwritten, the request stayed
        undischarged, and the next `route` refused "`## Intake` has no table".

        Every existing test in this class passed throughout, because they only
        asserted `"routed → <id>" in board`. The corruption is one line above
        the row they were looking at.
        """
        p, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        intake = self.section_of(p, "Intake")
        self.assertRegex(intake, r"(?m)^\|\s*:?-{2,}",
                         f"the intake table lost its separator row:\n{intake}")
        rows = [l for l in intake.split("\n")
                if l.strip().startswith("|") and "---" not in l
                and not l.strip().startswith("| Arrived")]
        self.assertEqual(len(rows), 1, f"the request was duplicated:\n{intake}")
        self.assertIn("routed →", rows[0], "the request was not discharged")

    def test_a_second_drain_still_works(self):
        """The consequence, stated as the thing a user would hit. One drain
        used to leave the section unparseable, so every later arrival could be
        recorded and never routed — `triage` step 1 becomes a step that cannot
        run."""
        p, code, _ = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0)
        code, _ = p.run("intake", "--title", "第二个请求", "--arrived", "2026-08-06")
        self.assertEqual(code, 0)
        code, out = p.run("route", "2", "--track", "ops", "--group", self.HEADING)
        self.assertEqual(code, 0,
                         f"the queue was bricked by the first drain: {out}")

    def test_the_routed_row_still_carries_its_clock(self):
        """`--group` must not buy the landing site by dropping `Arrived` —
        `today − Arrived` is the only clock a queue row has."""
        p, code, out = self.drained("--group", self.HEADING)
        row = next(l for l in p.board().split("\n")
                   if l.startswith(f"| {out['id']} |"))
        self.assertIn("2026-08-05", row, "the SLA clock was lost at routing")
        self.assertIn("客户要对账", row)

    def test_the_intake_row_is_discharged_by_a_grouped_route(self):
        p, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        self.assertIn(f"routed → {out['id']}", p.board())

    def test_route_reports_the_section_it_filed_into(self):
        """A caller that named a section has to be able to read back the one
        the row actually reached."""
        _, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["group"], self.HEADING)
        self.assertEqual(out["priority"], "")

    def test_the_flag_the_refusal_recommends_is_the_flag_that_works(self):
        """The defect's sharpest edge, asserted as a loop rather than as two
        independent facts: take the refusal the tool gives, do exactly what it
        says, and it must not refuse again."""
        p, code, refusal = self.drained()
        self.assertEqual(code, 1, refusal)
        self.assertIn("--group", str(refusal))
        named = [h for h in (self.HEADING, "Backbone") if h in str(refusal)]
        self.assertIn(self.HEADING, named, f"refusal named no usable "
                                           f"section: {refusal}")
        code, out = p.run("route", "1", "--track", "ops", "--group", self.HEADING)
        self.assertEqual(code, 0, f"the tool refused the flag its own refusal "
                                  f"recommended: {out}")

    def test_add_and_route_reach_the_same_section_from_the_same_flag(self):
        """The category, stated once. Every subcommand that FILES A NEW ROW
        takes `--group` and means the same thing by it; a writer that reads
        `--priority` and ignores `--group` is a board Perry can write into and
        then not write into, depending on which verb you used.

        A new row-filing writer belongs in this list.
        """
        for verb in ("add", "route"):
            p = Project(tracks=self.TRACKS, board=self.WORKSTREAM)
            if verb == "add":
                code, out = p.run("add", "--title", "客户要对账",
                                  "--group", self.HEADING)
            else:
                p.run("intake", "--title", "客户要对账", "--arrived", "2026-08-05")
                code, out = p.run("route", "1", "--track", "ops",
                                  "--group", self.HEADING)
            self.assertEqual(code, 0, f"{verb} --group refused: {out}")
            self.assertIn(out["id"], self.section_of(p, self.HEADING),
                          f"{verb} filed the row somewhere else")

    def test_a_group_is_not_silently_upgraded_to_a_priority(self):
        """`route` defaulted `--priority P1` unconditionally. Keeping that
        default alongside `--group` would file the row under a heading that
        does not exist and refuse — the same failure, one line further on."""
        _, code, out = self.drained("--group", self.HEADING)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["priority"], "")

    def test_a_priority_board_routes_exactly_as_before(self):
        """The bound. A project that does use P0/P1/P2 must be untouched, and
        must still get `P1` when it names nothing."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "ops")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["priority"], "P1")
        self.assertIn(out["id"], self.section_of(p, "P1"))

    def test_route_still_refuses_a_priority_that_is_not_one(self):
        """`check_priority` must keep running on the route path — it is the
        function whose refusal sends people to `--group` in the first place."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "ops",
                          "--priority", "P2 (低优先 carry)")
        self.assertEqual(code, 1, out)
        self.assertIn("--group", str(out))


class TestModeColumnsOnBoardsPerryDidNotBuild(unittest.TestCase):
    """m-11: two guards could not fail on the defect they named.
    `test_arrived_survives_routing_out_of_intake` asserted a schema key and
    routed nothing; `test_add_task_sets_the_mode_columns_at_creation` grepped
    prose. The behavioural tests that existed only ever exercised **queue**
    tracks on boards **`add` had just created** — which is why B-2, the
    arrival date dropped on routing, survived a review.

    Both blind spots are the same shape as M-8: Perry's own board is the one
    board Perry never has to adapt to. These tests use a pipeline track, and a
    board written by hand with none of the mode columns present.
    """

    TRACKS = TestModeAwareWrites.TRACKS

    #: Six standard columns, no `Stage`, no `Stage since`, no `Arrived`, no
    #: `Track` — a board that predates work modes entirely, which is every
    #: board of every project that adopts Perry.
    PREEXISTING = """# BOARD

## P0

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-900 | already here | Coding Agent | in_progress | keep going | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""

    cells = TestModeAwareWrites.cells

    def test_add_on_a_pipeline_track_stamps_the_stage_clock(self):
        """The prose guard asserted the string `Stage since` appears in the
        triage procedure. That passes whether or not any write sets it."""
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        code, a = p.run("add", "--title", "post", "--track", "blog",
                        "--priority", "P0")
        self.assertEqual(code, 0, a)
        c = self.cells(p, a["id"])
        self.assertEqual(c["stage"], "brief",
                         "the row landed in no stage, so dwell time has no "
                         "start and triage's first question has no answer")
        self.assertTrue(c["stage since"],
                        "the stage clock was never wound")

    def test_the_columns_are_created_on_a_board_that_never_had_them(self):
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        self.assertIn("stage since", self.cells(p, a["id"]))
        old = next(l for l in p.board().split("\n")
                   if l.startswith("| TASK-900 |"))
        self.assertIn("already here", old,
                      "widening the table disturbed a row that was there first")

    def test_routing_into_a_pipeline_track_carries_the_arrival_date(self):
        """The only routing test covered `ops`, a queue track. A pipeline
        track reads `Arrived` too — it is what says how long a brief sat
        before anyone picked it up."""
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        p.run("intake", "--title", "guest post pitch", "--arrived", "2026-08-01")
        code, out = p.run("route", "1", "--track", "blog", "--priority", "P0")
        self.assertEqual(code, 0, out)
        c = self.cells(p, out["id"])
        self.assertEqual(c["arrived"], "2026-08-01",
                         "the arrival date was replaced with today, or lost")
        self.assertEqual(c["stage"], "brief")
        self.assertTrue(c["stage since"])

    #: An `## Intake` section a human typed straight into the board: the
    #: request and nothing else. `perry-task intake` always stamps a date, so
    #: every test that had ever routed a row supplied one without meaning to.
    HAND_TYPED = PREEXISTING.replace("## P0", """## Intake

| Request | Outcome |
|---|---|
| a request someone typed in | — |

## P0""", 1)

    def test_routing_a_hand_typed_intake_row_does_not_traceback(self):
        """`values['arrived']` was read three lines after a branch that only
        sometimes sets it. On a pipeline track with no arrival date that was
        `KeyError: 'arrived'` — a traceback, not a refusal, on the one intake
        shape every adopting project already has."""
        p = Project(tracks=self.TRACKS, board=self.HAND_TYPED)
        code, out = p.run("route", "1", "--track", "blog", "--priority", "P0")
        self.assertEqual(code, 0, out)
        self.assertTrue(self.cells(p, out["id"])["stage since"],
                        "a pipeline row is measured from `Stage since`; it "
                        "has no arrival date and does not need one")

    def test_routing_one_into_a_queue_track_is_refused_not_crashed(self):
        """A queue row's only clock is `Arrived`. Filing one without a date
        creates a request that can never breach an SLA — which reads as
        compliance rather than as a gap."""
        p = Project(tracks=self.TRACKS, board=self.HAND_TYPED)
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P0")
        self.assertEqual(code, 1)
        self.assertIn("--arrived", str(out), "the refusal named no way out")
        self.assertEqual(self.HAND_TYPED, p.board(),
                         "a refusal is supposed to write nothing at all")

    def test_route_accepts_the_date_the_intake_row_lacks(self):
        p = Project(tracks=self.TRACKS, board=self.HAND_TYPED)
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P0",
                          "--arrived", "2026-07-04")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.cells(p, out["id"])["arrived"], "2026-07-04")

    def test_a_stage_move_restamps_the_clock_on_such_a_board(self):
        p = Project(tracks=self.TRACKS, board=self.PREEXISTING)
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            self.cells(p, a["id"])["stage since"], "2020-01-01"))
        p.import_board()
        code, _ = p.run("stage", a["id"], "--stage", "draft")
        self.assertEqual(code, 0)
        self.assertNotEqual(
            self.cells(p, a["id"])["stage since"], "2020-01-01",
            "the stage moved and the clock did not, so the row reads as "
            "having sat in `draft` since 2020")


class TestRetitle(unittest.TestCase):
    """The gap `next` closed, one column over.

    TASK-021 was filed as "Recurrence register + `OKR.md § Commitments`". The
    second half turned out to belong to a different lane and was split into
    its own row, leaving a title describing work this row would never do —
    and no tool could correct it. `status` refuses a no-op, `next` writes a
    different cell, so the row could not close honestly without a hand edit.
    """

    def test_it_rewrites_the_title_and_touches_nothing_else(self):
        p = Project()
        _, a = p.run("add", "--title", "two things at once", "--priority", "P0")
        before = next(l for l in p.board().split("\n")
                      if l.startswith(f"| {a['id']} |"))
        code, out = p.run("retitle", a["id"], "--title", "one thing")
        self.assertEqual(code, 0, out)
        after = next(l for l in p.board().split("\n")
                     if l.startswith(f"| {a['id']} |"))
        self.assertIn("one thing", after)
        self.assertNotIn("two things at once", after)
        self.assertEqual(
            [c for c in PT.split_row(before)[2:]],
            [c for c in PT.split_row(after)[2:]],
            "retitle changed a cell that is not the title")

    def test_the_same_title_is_refused(self):
        """Same reason `status` refuses a no-op: a journal line asserting a
        change that did not happen."""
        p = Project()
        _, a = p.run("add", "--title", "a name", "--priority", "P0")
        code, _ = p.run("retitle", a["id"], "--title", "a name")
        self.assertEqual(code, 1)

    def test_an_empty_title_is_refused(self):
        p = Project()
        _, a = p.run("add", "--title", "a name", "--priority", "P0")
        code, out = p.run("retitle", a["id"])
        self.assertEqual(code, 1)
        self.assertIn("nobody can find", str(out))

    def test_it_is_its_own_event(self):
        """A reader has to be able to tell "what this is called changed" from
        "where this got to"; folding them loses both facts forever."""
        p = Project()
        _, a = p.run("add", "--title", "a name", "--priority", "P0")
        p.run("retitle", a["id"], "--title", "a better name")
        events = [json.loads(l)["event"]
                  for l in (p.root / ".perry" / "events.jsonl").read_text()
                  .strip().split("\n")]
        self.assertEqual(["add", "retitle"], events)

    def test_the_journal_records_what_it_used_to_be_called(self):
        """A title that changes with no record of the old one makes every
        earlier mention of this row unfindable."""
        p = Project()
        _, a = p.run("add", "--title", "old name", "--priority", "P0")
        p.run("retitle", a["id"], "--title", "new name")
        journal = "\n".join(
            f.read_text() for f in sorted((p.root / "journal").rglob("*.md")))
        # The retitle line specifically. Asserting "old name" appears anywhere
        # in the journal passes on `add`'s own line and cannot fail on the bug
        # it names — a mutation run proved exactly that.
        line = next(l for l in journal.split("\n") if "retitled" in l)
        self.assertIn("old name", line, "no record of what it used to be called")
        self.assertIn("new name", line)


class TestDecoratedHeaders(unittest.TestCase):
    """A board whose header cells are bolded or backticked.

    Perry handles it — `squash()` strips `*` and `` ` `` before a header cell
    becomes a key — and nothing tested it. Deleting that stripping left all
    588 tests green, which is how a coverage gap announces itself: the
    behaviour is right, and nothing would notice it breaking.

    Real projects write `| **ID** | **Title** |`. Losing this makes every
    column resolve to nothing, and `add` would file rows into a table whose
    columns it could not name.
    """

    BOLD = """# BOARD

## P0

| **ID** | **Title** | **Owner** | **Status** | **Next action** | **Evidence** |
|---|---|---|---|---|---|
| TASK-900 | old | Coding Agent | not_started | — | — |
"""

    def test_a_row_can_be_added_to_a_table_with_bolded_headers(self):
        p = Project(board=self.BOLD)
        code, a = p.run("add", "--title", "new work", "--priority", "P0")
        self.assertEqual(code, 0, a)
        row = next(l for l in p.board().split("\n")
                   if l.startswith(f"| {a['id']} |"))
        self.assertEqual(
            len(PT.split_row(row)), 6,
            "the columns did not resolve, so the row was written blind")
        self.assertIn("new work", row)

    def test_the_header_is_left_exactly_as_the_project_wrote_it(self):
        p = Project(board=self.BOLD)
        p.run("add", "--title", "new work", "--priority", "P0")
        self.assertIn("| **ID** | **Title** |", p.board(),
                      "the tool rewrote a header it was only supposed to read")

    def test_an_existing_row_is_still_findable(self):
        p = Project(board=self.BOLD)
        code, _ = p.run("status", "TASK-900", "--status", "in_progress")
        self.assertEqual(code, 0)
        row = next(l for l in p.board().split("\n")
                   if l.startswith("| TASK-900 |"))
        self.assertIn("in_progress", row)

    def test_squash_drops_decoration_and_nothing_else(self):
        self.assertEqual("status", PT.squash("**Status**"))
        self.assertEqual("next action", PT.squash("`Next action`"))
        self.assertEqual("下一步", PT.squash(" **下一步** "),
                         "squash has no language knowledge and must not "
                         "touch anything that is not decoration")


class TestOneRuleOneImplementation(unittest.TestCase):
    """Round-5 review m-6, m-7, m-8 — three values with two writers each.

    Perry has hit this shape often enough to name it: two implementations of
    one rule drift silently, and a value that is both stored and derived is
    wrong for exactly the rows nobody wrote the storing path for.
    """

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| core | project | phase/ | — | — | — | — | V3 |\n"
              "| blog | pipeline | commitments | brief->draft->review->published | review:2 | 5d | 2026-W34 | V5 |\n"
              "| ops | queue | commitments | new->triaged->in_progress->resolved | — | 5d | monthly | V2 |\n"
              "| study | inquiry | questions | open->researching->answered | open:5 | — | — | V4 |\n")

    # -- m-6: the stage vocabulary parser

    def test_perry_task_carries_no_second_stage_parser(self):
        """`split_stages` existed twice, differing only in a loop variable,
        with the docstring explaining the normalization on one copy.

        Three spellings of the separator are in circulation (`->`, `→`, `→`
        with spaces) and "the first stage" / "the terminal stage" are both
        load-bearing, so the two copies were one edit away from disagreeing
        about where every row in a track begins and ends. Replacing
        `perry-state`'s must change `perry-task`'s answer; if it does not,
        there is a second body here.
        """
        ps = PT.perry_state()
        original = ps.split_stages
        try:
            ps.split_stages = lambda cell: ["SENTINEL"]
            self.assertEqual(
                PT.split_stages("brief->draft"), ["SENTINEL"],
                "perry-task carries its own copy of the stage parser")
        finally:
            ps.split_stages = original
        self.assertEqual(PT.split_stages("brief→draft"), ["brief", "draft"])

    def test_stages_of_consumes_the_registers_computed_list(self):
        """`parse_tracks` already computes `stage_list`; `stages_of` ignored it
        and re-split the raw cell. Two readings of one register, and nothing
        asserted they agreed."""
        track = {"track": "blog", "mode": "pipeline",
                 "stages": "this-cell->is-stale",
                 "stage_list": ["brief", "draft"]}
        self.assertEqual(PT.stages_of(PT.load_schema(), track),
                         ["brief", "draft"],
                         "the raw cell was re-parsed instead of the computed "
                         "list the register already carries")

    # -- m-7: where a row is born

    def test_the_entry_stage_rule_has_one_implementation(self):
        self.assertEqual(PT.entry_stage("queue", ["new", "triaged", "done"]),
                         "triaged", "a queue row must skip the intake stage")
        self.assertEqual(PT.entry_stage("pipeline", ["brief", "draft"]), "brief")
        self.assertEqual(PT.entry_stage("inquiry", ["open", "answered"]), "open")
        self.assertEqual(PT.entry_stage("queue", ["only"]), "only")
        self.assertEqual(PT.entry_stage("pipeline", []), "")

    def test_add_and_route_are_born_at_the_same_stage_in_every_mode(self):
        """The expression lived in `cmd_add` and in `cmd_route`, both written
        the same round. A row's entry stage is where its dwell clock starts, so
        the two disagreeing means the same work measured two ways depending on
        which command created it."""
        for track, expected in (("ops", "triaged"), ("blog", "brief"),
                                ("study", "open")):
            p = Project(tracks=self.TRACKS)
            _, a = p.run("add", "--title", "raised", "--track", track,
                         "--priority", "P0")
            p.run("intake", "--title", "arrived", "--arrived", "2026-08-01")
            code, r = p.run("route", "1", "--track", track, "--priority", "P0")
            self.assertEqual(code, 0, r)
            header = next(l for l in p.board().split("\n")
                          if l.startswith("| ID |"))
            keys = [PT.norm(h) for h in PT.split_row(header)]

            def stage_of(tid: str) -> str:
                row = next(l for l in p.board().split("\n")
                           if l.startswith(f"| {tid} |"))
                return dict(zip(keys, PT.split_row(row)))["stage"]

            self.assertEqual(stage_of(a["id"]), expected, f"{track}: add")
            self.assertEqual(stage_of(r["id"]), expected, f"{track}: route")

    # -- m-8: `mode` in the frozen list contract

    def test_mode_is_derived_from_the_track_register(self):
        """It shipped in `perry-task/list/1.4` read back out of the event log,
        so it was blank for exactly the rows `route` creates — on the one mode
        where routing is how a row is normally born."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "vendor spend", "--arrived", "2026-08-01")
        _, r = p.run("route", "1", "--track", "ops", "--priority", "P0")
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        _, out = p.run("list", "--all")
        modes = {t["id"]: t["mode"] for t in out["tasks"]}
        self.assertEqual(modes[r["id"]], "queue",
                         "a routed row still ships a blank mode")
        self.assertEqual(modes[a["id"]], "pipeline")

    def test_mode_survives_the_event_log_being_deleted(self):
        """The log is declared DERIVED AND DISPOSABLE at the top of
        `bin/perry-task`. Nothing in a frozen contract may depend on it for a
        value the markdown already determines."""
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        (p.root / ".perry" / "events.jsonl").unlink()
        _, out = p.run("list", "--all")
        self.assertEqual({t["id"]: t["mode"] for t in out["tasks"]}[a["id"]],
                         "pipeline", "deleting the derived log blanked a "
                                     "value the board determines")

    def test_a_project_with_no_track_register_still_reports_project_mode(self):
        """`parse_tracks`'s own fallback: a project that never heard of tracks
        has exactly one, named `main`, mode `project`. The payload says the
        same rather than an empty string."""
        p = Project()
        _, a = p.run("add", "--title", "X", "--priority", "P0")
        _, out = p.run("list", "--all")
        self.assertEqual(out["tasks"][0]["mode"], "project")


class TestDropRecordsWhereTheRowDied(unittest.TestCase):
    """Round-5 review M-4. `modes/pipeline.md` claimed a dropped item's `Stage`
    cell "keeps the last stage it reached, so the record says where it died".

    `cmd_drop` removes the row, so the cell went with it, and neither the
    journal line nor the event carried the stage. The claim was corrected
    rather than implemented — keeping the row would make every WIP and depth
    count in both mode files start excluding it — but the fact it named is
    real and cheap to keep: three items dying at `review` is a statement about
    the review stage, not about the three items.
    """

    TRACKS = TestOneRuleOneImplementation.TRACKS

    def test_the_journal_line_and_the_event_carry_the_stage(self):
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "post", "--track", "blog",
                     "--priority", "P0")
        code, _ = p.run("stage", a["id"], "--stage", "review")
        self.assertEqual(code, 0)
        code, _ = p.run("drop", a["id"], "--reason", "client pulled the campaign")
        self.assertEqual(code, 0)

        self.assertNotIn(f"| {a['id']} |", p.board(),
                         "drop is supposed to remove the row")
        self.assertIn("at stage: review", p.journal(),
                      "the journal records that it died and not where")
        ev = p.events()[-1]
        self.assertEqual(ev["event"], "drop")
        self.assertEqual(ev["stage"], "review",
                         "the only surviving structured record lost the stage")
        self.assertEqual(ev["reason"], "client pulled the campaign")

    def test_a_project_mode_row_carries_an_empty_stage_rather_than_no_key(self):
        """Project mode has no stages at all. The key is still present: a
        consumer that has to branch on a missing key is one that will forget
        to."""
        p = Project(tracks=self.TRACKS)
        _, a = p.run("add", "--title", "X", "--track", "core", "--priority", "P0")
        p.run("drop", a["id"], "--reason", "duplicate")
        ev = p.events()[-1]
        self.assertIn("stage", ev)
        self.assertEqual(ev["stage"], "")
        self.assertNotIn("at stage:", p.journal(),
                         "an empty stage was rendered into the journal line")


class TestOnePriorityValidator(unittest.TestCase):
    """`cmd_add` refused an unknown priority; `cmd_route` did not, and fed it
    straight into `PRIORITY_RE[...]`.

    So `route --priority "P2 (低优先 carry)"` — a real project's full section
    heading, which is what anyone reading that board would type — raised
    `KeyError` instead of refusing. A traceback where a refusal belongs, for
    the third time in this file.

    The shape is the recurring one: one rule, two implementations, and the
    value is a dict key, so validating it in one place and indexing with it in
    another guarantees the mismatch eventually.
    """

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | commitments | new->triaged->in_progress | — | 5d | monthly | V2 |\n")

    def test_route_refuses_an_unknown_priority_rather_than_crashing(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        code, out = p.run("route", "1", "--track", "ops",
                          "--priority", "P2 (低优先 carry)")
        self.assertEqual(code, 1, out)
        self.assertIn("not one of P0/P1/P2", str(out))

    def test_the_refusal_says_what_to_type_instead(self):
        """A refusal that names no way forward is a wall. The heading IS the
        thing `--group` takes."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        _, out = p.run("route", "1", "--track", "ops", "--priority", "nonsense")
        self.assertIn("--group", str(out))

    def test_add_and_route_refuse_identically(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        _, a = p.run("add", "--title", "x", "--priority", "ZZZ")
        _, r = p.run("route", "1", "--track", "ops", "--priority", "ZZZ")
        self.assertEqual(str(a), str(r),
                         "two callers, two different answers to one question")

    def test_a_valid_priority_still_routes(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P2")
        self.assertEqual(code, 0, out)


class TestTheRungIsWritableAndCorrectable(unittest.TestCase):
    """`add --rung V4` parsed, and wrote nothing. The flag existed, the cell
    did not get it, and the caller had no way to notice. `--rung NONSENSE` was
    accepted the same way.

    A flag that is silently ignored is worse than a missing one: a missing
    flag refuses, and this one reported success.

    And there was no writer at all for an open row — `--rung` lived only on
    `done`, which is far too late to argue about it. Third instance of one
    gap: `next` closed it for `Next action`, `retitle` for `Title`.

    `ADR-005` is what makes it load-bearing. The rung is now a claim about who
    is hurt when the work is wrong, and a claim nobody can correct without a
    hand edit is one nobody corrects.
    """

    def cell(self, p, tid):
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)],
                        PT.split_row(row))).get("verification", "")

    def test_add_writes_the_rung_it_was_given(self):
        p = Project()
        code, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
        self.assertEqual(code, 0, a)
        self.assertEqual("V4", self.cell(p, a["id"]))

    def test_an_unknown_rung_is_refused_not_dropped(self):
        p = Project()
        code, out = p.run("add", "--title", "x", "--priority", "P0",
                          "--rung", "NONSENSE")
        self.assertEqual(code, 1)
        self.assertIn("not one of", str(out))

    def test_the_refusal_does_not_offer_a_rung_it_will_refuse(self):
        """V0 is in the enum so a linter can name it. Listing it as a choice
        advertises a value the next check rejects."""
        p = Project()
        _, out = p.run("add", "--title", "x", "--priority", "P0",
                       "--rung", "NONSENSE")
        self.assertNotIn("V0", str(out))

    def test_v0_is_refused_by_name(self):
        p = Project()
        code, out = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V0")
        self.assertEqual(code, 1)
        self.assertIn("asserted", str(out))

    def test_rung_corrects_an_open_row(self):
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
        code, _ = p.run("rung", a["id"], "--rung", "V5")
        self.assertEqual(code, 0)
        self.assertEqual("V5", self.cell(p, a["id"]))

    def test_the_same_rung_is_refused(self):
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
        code, _ = p.run("rung", a["id"], "--rung", "V4")
        self.assertEqual(code, 1)

    def test_it_is_its_own_event(self):
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        p.run("rung", a["id"], "--rung", "V4")
        events = [json.loads(l)["event"]
                  for l in (p.root / ".perry" / "events.jsonl").read_text()
                  .strip().split("\n")]
        self.assertEqual(["add", "rung"], events)

    def test_add_and_done_answer_the_same_way(self):
        """Two validators for one enum is how they drift. `done` had one and
        `add` had none."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        _, add_out = p.run("add", "--title", "y", "--priority", "P0",
                           "--rung", "ZZZ")
        _, done_out = p.run("done", a["id"], "--evidence", "e", "--rung", "ZZZ")
        self.assertEqual(str(add_out), str(done_out))


class TestTheDelimiterIsACharacterPeopleWrite(unittest.TestCase):
    """`render_row` joined on `|` and escaped nothing, so a cell whose value
    contained a pipe silently became several cells and shifted every column
    after it.

    Not hypothetical: filing a task whose `Next action` quoted a markdown
    header — `` | ID | **Risk** | Opened | Status | `` — turned a 7-cell row
    into a 12-cell row on Perry's own board and pushed the word `Risk` into
    the `Verification` column, where the enum check caught it.

    Two things that make this worse than an ordinary escaping bug, and both
    are asserted below:

    - the corruption **survives** later tool writes. A row is read back with
      `dict(zip(header, cells))`, and a shifted row zips without complaint, so
      the wrong values are read as right and written out again.
    - nothing upstream refuses. The value is the user's prose; the delimiter is
      a character prose contains.
    """

    def test_a_pipe_in_a_value_round_trips(self):
        for cells in (["a", "b | c", "d"],
                      ["a", "|leading", "trailing|"],
                      ["a", "b || c", "d"]):
            with self.subTest(cells=cells):
                self.assertEqual(cells, PT.split_row(PT.render_row(cells)))

    def test_a_row_keeps_its_column_count(self):
        line = PT.render_row(["TASK-001", "quoting | ID | Title |", "Coding Agent"])
        self.assertEqual(3, len(PT.split_row(line)),
                         "a value containing the delimiter became extra cells")

    def test_an_already_escaped_pipe_is_not_double_escaped(self):
        """Reading a hand-written row that already uses markdown's `\\|` and
        writing it back must not grow a second backslash each time."""
        once = PT.render_row(PT.split_row(r"| a | b \| c | d |"))
        twice = PT.render_row(PT.split_row(once))
        self.assertEqual(once, twice, "escaping is not idempotent")

    def test_the_cell_survives_the_whole_write_path(self):
        p = Project()
        code, a = p.run("add", "--title", "x", "--priority", "P0",
                        "--next", "see | ID | Title | Owner | in the board")
        self.assertEqual(code, 0, a)
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {a['id']} |"))
        self.assertEqual(len(PT.split_row(header)), len(PT.split_row(row)),
                         "the row and its header stopped agreeing")
        cells = dict(zip([PT.norm(h) for h in PT.split_row(header)],
                         PT.split_row(row)))
        self.assertIn("| ID | Title | Owner |", cells["next action"])
        self.assertEqual("", cells.get("verification", ""),
                         "a value leaked into the column after it")


class TestOneCellWriterNotFour(unittest.TestCase):
    """`next`, `retitle` and `rung` were three copies of one twenty-line
    function, written weeks apart, each a copy of the one before. The fourth
    was about to be written for `Evidence` — a corrupted cell needed repairing
    and `done --evidence` was the only other writer, so the only way to fix a
    cell was to close the row, which is not a correction but a lie about the
    work.

    Three copies of one rule is the defect class five review rounds found in
    this project's prose. This one was in its own code.

    What is *not* shared is the part that is not boilerplate: each writer keeps
    its own event name, its own journal wording and its own refusal. A reader
    has to be able to tell "the plan changed" from "what this is called
    changed" from "where this got to", and one event name loses all three.
    """

    FIELDS = [("next", "--next", "next action"),
              ("retitle", "--title", "title"),
              ("rung", "--rung", "verification"),
              ("evidence", "--evidence", "evidence")]

    def cell(self, p, tid, key):
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)],
                        PT.split_row(row))).get(key, "")

    def value_for(self, sub):
        return "V5" if sub == "rung" else "a new value"

    def test_each_writes_its_own_cell_and_no_other(self):
        for sub, flag, key in self.FIELDS:
            with self.subTest(sub=sub):
                p = Project()
                _, a = p.run("add", "--title", "x", "--priority", "P0",
                             "--rung", "V4")
                before = {k: self.cell(p, a["id"], k)
                          for _, _, k in self.FIELDS}
                code, out = p.run(sub, a["id"], flag, self.value_for(sub))
                self.assertEqual(code, 0, out)
                for _, _, other in self.FIELDS:
                    if other == key:
                        continue
                    self.assertEqual(before[other], self.cell(p, a["id"], other),
                                     f"{sub} also wrote `{other}`")

    def test_each_is_its_own_event(self):
        """Four subcommands, four event names. Folding them is what makes the
        three facts unrecoverable."""
        seen = []
        for sub, flag, _ in self.FIELDS:
            p = Project()
            _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
            p.run(sub, a["id"], flag, self.value_for(sub))
            events = [json.loads(l)["event"]
                      for l in (p.root / ".perry" / "events.jsonl").read_text()
                      .strip().split("\n")]
            seen.append(events[-1])
        self.assertEqual(len(self.FIELDS), len(set(seen)),
                         f"two writers share an event name: {seen}")

    def test_each_refuses_a_no_op(self):
        for sub, flag, _ in self.FIELDS:
            with self.subTest(sub=sub):
                p = Project()
                _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
                p.run(sub, a["id"], flag, self.value_for(sub))
                code, _ = p.run(sub, a["id"], flag, self.value_for(sub))
                self.assertEqual(code, 1, f"{sub} wrote a value already there")

    def test_each_refusal_says_what_that_subcommand_is_for(self):
        """The unification must not cost the wording. `next` explains that
        clearing it leaves the row with no stated next step; `retitle` that a
        row with no title is one nobody can find."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        _, n = p.run("next", a["id"])
        _, r = p.run("retitle", a["id"])
        self.assertIn("no stated next step", str(n))
        self.assertIn("nobody can find", str(r))

    def test_only_next_refuses_a_finished_row(self):
        """A finished row has no next step. It still has a title, a rung and
        an evidence path, and those stay correctable — a board that stages
        finished work in place is the case that matters, since `done` removes
        the row. Perry's own board did that for twenty rows."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | finished in place | User | done | — | e.md |\n\n## P1", 1))
        self.assertEqual(1, p.run("next", "TASK-900", "--next", "more")[0],
                         "a finished row was given a live-looking next step")
        self.assertEqual(0, p.run("retitle", "TASK-900", "--title", "clearer")[0],
                         "a finished row's title stopped being correctable")

    def test_evidence_repairs_a_cell_without_closing_the_row(self):
        """The case that showed the other three were a pattern."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        code, _ = p.run("evidence", a["id"], "--evidence", "evidence/2026-08/x.md")
        self.assertEqual(code, 0)
        self.assertEqual("evidence/2026-08/x.md", self.cell(p, a["id"], "evidence"))
        self.assertEqual("not_started", self.cell(p, a["id"], "status"),
                         "repairing a cell closed the row")



class TestAClosedRowKeepsItsName(unittest.TestCase):
    """TASK-166. `TASK-029` on this repository is `done`, at `V3`, with real
    evidence, and has no title — and until this row landed, nothing reported it
    and nothing could repair it.

    **The two halves were one shape.** The `untitled` check read the rows
    AFTER they had been filtered to `open`, so the only kind of row that can be
    permanently untitled was the one kind it could not see; and `retitle` is a
    `cell_writer`, which edits a BOARD row, and closing a row REMOVES it from
    the board. The check only looked where the writer could reach, and the
    writer only reached where the check already looked. Fixing either alone is
    worse than fixing neither: a reported row nobody can repair is a permanent
    warning, and a repair path nobody is told to use is dead code.

    **Why `title` and not the other cells.** Every other cell `cell_writer`
    writes is a claim ABOUT the work — where it got to, what is next, who
    checked it, what they checked — and a claim about finished work is finished
    with it. That is why `next` refuses a terminal row on purpose. The title is
    the row's NAME: `reference/user-load.md` forbids handing a reader a bare
    id, and a name is needed for exactly as long as anybody reads the record.
    """

    #: A board that has already let a finished row go — which is what `done`
    #: does, and therefore the state every closed row on a real project is in.
    #: The record survives in `tasks.jsonl`; the projection line does not.
    def closed_row(self) -> tuple[Project, str]:
        p = Project()
        _, a = p.run("add", "--title", "temporary name", "--priority", "P0")
        code, out = p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        self.assertEqual(code, 0, out)
        self.assertNotIn(f"| {a['id']} ", p.board(),
                         "the fixture is wrong: closing did not remove the row")
        return p, a["id"]

    def record(self, p, tid) -> dict:
        text = (p.root / "tasks.jsonl").read_text()
        return next(json.loads(l) for l in text.splitlines()
                    if l.strip() and json.loads(l)["id"] == tid)

    def blank_the_title(self, p, tid) -> None:
        """Reproduce `TASK-029`'s state: a closed record with an empty title.

        Written by hand into the store because no tool path can produce it any
        more — which is the point. It arrived through a migration that no
        longer runs (see `perry/evidence/2026-08/TASK-166-result.md`), and the
        row it left behind still has to be repairable.
        """
        path = p.root / "tasks.jsonl"
        out = []
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["id"] == tid:
                rec["title"] = ""
            out.append(json.dumps(rec, ensure_ascii=False))
        path.write_text("\n".join(out) + "\n")

    # ── half one: the check sees it ───────────────────────────────────────

    def test_an_untitled_closed_row_is_reported_without_all(self):
        """The measurement that opened the row: `untitled` was `[]` on a
        default call and named the row only under `--all` — the flag a triage
        does not pass, on the rows a triage will never look at again."""
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        _, default = p.run("list")
        self.assertIn(tid, default["untitled"],
                      "a closed row with no title is invisible again")
        _, everything = p.run("list", "--all")
        self.assertEqual(default["untitled"], everything["untitled"],
                         "the finding still moves with the flag")

    def test_the_finding_is_not_a_caption_for_the_listing(self):
        """`untitled` names rows that are NOT in `tasks[]` on a default call.
        That is deliberate: it is a finding about the project, not a legend for
        the rows on screen, and the human printer reads the same key."""
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        _, payload = p.run("list")
        self.assertNotIn(tid, [t["id"] for t in payload["tasks"]])
        self.assertIn(tid, payload["untitled"])
        r = subprocess.run(["python3", str(TOOL), "list", "--root",
                            str(p.root)], capture_output=True, text=True)
        self.assertIn(tid, r.stdout,
                      "the surface a human reads still hides it")

    def test_an_open_untitled_row_is_still_reported(self):
        """The half of the check that already worked must keep working."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        self.blank_the_title(p, a["id"])
        _, payload = p.run("list")
        self.assertEqual([a["id"]], payload["untitled"])

    def test_a_titled_project_reports_nothing(self):
        """The check must not have become an unconditional warning."""
        p, tid = self.closed_row()
        _, payload = p.run("list")
        self.assertEqual([], payload["untitled"])

    # ── half two: the writer reaches it ───────────────────────────────────

    def test_retitle_repairs_a_row_the_board_has_let_go_of(self):
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        code, out = p.run("retitle", tid, "--title", "the name it had")
        self.assertEqual(code, 0, out)
        self.assertEqual("the name it had", self.record(p, tid)["title"])
        _, payload = p.run("list")
        self.assertEqual([], payload["untitled"],
                         "repaired and still reported")

    def test_the_repair_leaves_the_row_closed_at_its_rung(self):
        """Verification 4, from the record's side: the door reaches the row,
        and carries one field through it."""
        p, tid = self.closed_row()
        before = self.record(p, tid)
        self.assertEqual(0, p.run("retitle", tid, "--title", "clearer")[0])
        after = self.record(p, tid)
        self.assertEqual("clearer", after["title"])
        for field in [k for k in before if k != "title"]:
            self.assertEqual(before[field], after[field],
                             f"the repair also rewrote {field}")

    def test_no_other_cell_writer_reaches_a_row_off_the_board(self):
        """Verification 4, from the door's side. `off_board_repair` is passed
        by `retitle` and by nothing else; a mutation that passes it to another
        writer reddens this."""
        p, tid = self.closed_row()
        for sub, flag, value in (("next", "--next", "do more"),
                                 ("rung", "--rung", "V5"),
                                 ("evidence", "--evidence", "other.md"),
                                 ("status", "--status", "in_progress"),
                                 ("start", None, None)):
            with self.subTest(sub=sub):
                argv = (sub, tid) + ((flag, value) if flag else ())
                code, out = p.run(*argv)
                self.assertEqual(code, 1, f"{sub} reached a closed row: {out}")
                self.assertIn("not a row on the board", str(out))

    def test_next_still_refuses_a_finished_row_that_is_on_the_board(self):
        """Verification 3. The refusal this row must not weaken is not the
        board one — it is `terminal_ok`, which fires on a project that stages
        finished work in place rather than removing it."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | finished in place | User | done | — | e.md |\n\n## P1", 1))
        code, out = p.run("next", "TASK-900", "--next", "something")
        self.assertEqual(code, 1, out)
        self.assertIn("finished", str(out))
        self.assertEqual(0, p.run("retitle", "TASK-900", "--title", "named")[0],
                         "the title stopped being correctable in place")

    def test_an_open_row_missing_from_the_board_is_still_refused(self):
        """The third guard. "Not on the board" means "finished" only because
        `done` removes the row; an OPEN row that is missing from it is a stale
        projection, and repairing the record here would paper over that."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        board = p.board()
        p_board = "\n".join(l for l in board.split("\n")
                            if not l.startswith(f"| {a['id']} "))
        (p.root / "BOARD.md").write_text(p_board)
        code, out = p.run("retitle", a["id"], "--title", "new")
        self.assertEqual(code, 1, out)
        self.assertIn("rendering failure", str(out))

    def test_the_repair_does_not_reorder_the_store(self):
        """A finished record's position is the order the work happened in.
        Rewriting a name is not a reason to move history — and the generic
        writer path appends, which would move it to the last line."""
        p, tid = self.closed_row()
        _, b = p.run("add", "--title", "later", "--priority", "P0")
        order = lambda: [json.loads(l)["id"] for l in
                         (p.root / "tasks.jsonl").read_text().splitlines()
                         if l.strip()]
        before = order()
        self.assertEqual(0, p.run("retitle", tid, "--title", "renamed")[0])
        self.assertEqual(before, order())

    def test_the_repair_is_recorded_as_a_retitle_and_carries_the_new_name(self):
        """The event log is how a later reader learns the name was repaired
        rather than never missing. `TASK-029`'s own history is why: its only
        event predates the `title` key, and that is exactly what made the
        question "never written, or written and lost?" hard to answer."""
        p, tid = self.closed_row()
        self.blank_the_title(p, tid)
        self.assertEqual(0, p.run("retitle", tid, "--title", "restored")[0])
        ev = p.events()[-1]
        self.assertEqual("retitle", ev["event"])
        self.assertEqual(tid, ev["id"])
        self.assertEqual("", ev["from"])
        self.assertEqual("restored", ev["to"])
        self.assertEqual("restored", ev["title"])
        self.assertIn(f"- [{tid}] retitled", p.journal())

    def test_a_no_op_repair_is_still_refused(self):
        p, tid = self.closed_row()
        code, out = p.run("retitle", tid, "--title", "temporary name")
        self.assertEqual(code, 1, out)
        self.assertIn("already", str(out))

    def test_an_id_nothing_knows_is_still_refused(self):
        p, _ = self.closed_row()
        code, out = p.run("retitle", "TASK-9999", "--title", "x")
        self.assertEqual(code, 1, out)
        self.assertIn("not a task", str(out))

    def test_every_event_this_tool_writes_carries_a_title(self):
        """The question TASK-166 had to answer about `TASK-029` was whether a
        write path can DROP a title. On this repository exactly one event of
        770 has no `title` key — the first line of the log, written before
        `TASK-030` added the field. This pins the answer for today's writer:
        no live path emits a task event without one, so the loss was a
        migration artefact and not a defect that can recur.
        """
        p = Project()
        _, a = p.run("add", "--title", "named", "--priority", "P0")
        p.run("start", a["id"])
        p.run("next", a["id"], "--next", "a step")
        p.run("rung", a["id"], "--rung", "V3")
        p.run("evidence", a["id"], "--evidence", "e.md")
        p.run("retitle", a["id"], "--title", "renamed")
        p.run("summary", a["id"], "--summary", "a summary")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        p.run("retitle", a["id"], "--title", "renamed after closing")
        events = [e for e in p.events() if e.get("id", "").startswith("TASK-")]
        self.assertGreaterEqual(len(events), 9)
        for e in events:
            self.assertIn("title", e, e)
            self.assertTrue(e["title"], e)


class TestADependencyIsQueryable(unittest.TestCase):
    """TASK-063. `blocked` said a row was stopped and never said on what.

    Found by the user running `perry-task list` and seeing a pile of rows with
    no way to tell which could be advanced. Three facts made it unanswerable:
    `add --depends` wrote free text into the journal's definition block, once,
    at creation, never updatable; `status --status blocked` refused without
    `--reason` on the stated ground that "a blocked row with no named
    dependency is a row nobody can unblock" and then put that dependency into
    prose; and `subcommands.md` told triage to find "the same dependency cited
    in >= 2 rows" over data nothing could read.
    """

    def payload(self, p, *extra) -> dict:
        _, out = p.run("list", "--all", *extra)
        return out

    def task(self, p, tid, *extra) -> dict:
        return next(t for t in self.payload(p, *extra)["tasks"] if t["id"] == tid)

    def two(self, p) -> tuple[str, str]:
        _, a = p.run("add", "--title", "first", "--priority", "P0")
        _, b = p.run("add", "--title", "second", "--priority", "P0")
        return a["id"], b["id"]

    # ── the edge is on the board, not in the log ──────────────────────────

    def test_the_edge_survives_deleting_the_event_log(self):
        """The log is DERIVED AND DISPOSABLE. `mode` already cost this project
        one released contract for reading a value out of it: deleting
        `.perry/events.jsonl` blanked the field for every row on the board."""
        p = Project()
        a, b = self.two(p)
        self.assertEqual(0, p.run("depends", b, "--on", a)[0])
        (p.root / ".perry" / "events.jsonl").unlink()
        self.assertEqual([a], self.task(p, b)["depends_on"],
                         "the edge lived in the disposable half")

    def test_the_cell_is_what_the_reader_reads(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        self.assertIn("Depends on", p.board())
        self.assertIn(a, p.board().split("\n")[
            next(i for i, l in enumerate(p.board().split("\n")) if l.startswith(f"| {b} "))])

    # ── the four keys ─────────────────────────────────────────────────────

    def test_blocked_by_names_the_unfinished_half_and_blocks_is_the_reverse(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        self.assertEqual([a], self.task(p, b)["blocked_by"])
        self.assertEqual([b], self.task(p, a)["blocks"],
                         "closing a row does not say what it frees up")

    def test_a_satisfied_dependency_leaves_blocked_by_and_stays_in_depends_on(self):
        """Both halves matter. A dependency that vanished when it was met would
        delete the record of why the row waited; one that kept blocking would
        make `startable` never true."""
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        p.run("done", a, "--evidence", "e.md", "--rung", "V3")
        t = self.task(p, b)
        self.assertEqual([a], t["depends_on"], "the satisfied edge was erased")
        self.assertEqual([], t["blocked_by"])
        self.assertTrue(t["startable"])

    def test_a_dependency_may_point_at_a_closed_task(self):
        """It has to: `done` removes the row, so refusing ids that are no
        longer on the board would mean every satisfied dependency had to be
        deleted from the record in order to be written at all."""
        p = Project()
        a, b = self.two(p)
        p.run("done", a, "--evidence", "e.md", "--rung", "V3")
        self.assertEqual(0, p.run("depends", b, "--on", a)[0],
                         "an edge onto finished work was refused")
        self.assertEqual([], self.task(p, b)["blocked_by"])

    def test_an_id_this_payload_does_not_carry_counts_as_unsatisfied(self):
        """"I do not know" is not "it is done". Reporting such a row startable
        is the one error that sends somebody to work on something blocked."""
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", "DESIGN-006")
        t = self.task(p, b)
        self.assertEqual(["DESIGN-006"], t["blocked_by"])
        self.assertFalse(t["startable"])
        self.assertEqual([{"id": b, "unknown": ["DESIGN-006"]}],
                         self.payload(p)["conformance"]["depends_on_unknown"])

    def test_the_edge_is_one_hop_and_not_the_transitive_closure(self):
        """A waits on B, B waits on C. A's answer is B and only B — A becomes
        startable the moment B closes, and B's history is not A's business."""
        p = Project()
        _, a = p.run("add", "--title", "A", "--priority", "P0")
        _, b = p.run("add", "--title", "B", "--priority", "P0")
        _, c = p.run("add", "--title", "C", "--priority", "P0")
        p.run("depends", a["id"], "--on", b["id"])
        p.run("depends", b["id"], "--on", c["id"])
        self.assertEqual([b["id"]], self.task(p, a["id"])["blocked_by"])

    def test_blocks_is_computed_before_the_track_and_all_filters(self):
        """A row you filtered out still blocks the rows that name it. A graph
        that changed with the caller's flags would be a different graph per
        query."""
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        p.run("done", b, "--evidence", "e.md", "--rung", "V3")
        without_all = next(t for t in self.payload(p, )["tasks"] if t["id"] == a)
        _, out = p.run("list")
        live = next(t for t in out["tasks"] if t["id"] == a)
        self.assertEqual([b], live["blocks"],
                         "a closed dependant disappeared from `blocks` when "
                         "the caller asked for open work only")
        self.assertEqual([b], without_all["blocks"])

    # ── startable: the question a dashboard asks ──────────────────────────

    def test_startable_is_false_for_a_row_whose_own_status_says_it_is_waiting(self):
        """The user's actual complaint: a pile of `review` rows read as work
        that could be picked up. This holds on a board with no declared edge on
        it at all, which is every board that predates 1.6."""
        p = Project()
        a, b = self.two(p)
        p.run("status", a, "--status", "review")
        p.run("status", b, "--status", "blocked", "--reason", "waiting on Apple")
        self.assertFalse(self.task(p, a)["startable"], "a review row read as startable")
        self.assertFalse(self.task(p, b)["startable"])

    def test_startable_is_false_for_a_closed_row(self):
        p = Project()
        a, _ = self.two(p)
        p.run("done", a, "--evidence", "e.md", "--rung", "V3")
        self.assertFalse(self.task(p, a)["startable"])

    def test_startable_is_true_for_open_unblocked_work(self):
        p = Project()
        a, _ = self.two(p)
        self.assertTrue(self.task(p, a)["startable"])

    # ── cycles ────────────────────────────────────────────────────────────

    def test_a_cycle_is_refused_at_write_time(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        code, out = p.run("depends", a, "--on", b)
        self.assertEqual(1, code)
        self.assertIn("cycle", out["refused"])

    def test_a_row_cannot_depend_on_itself(self):
        p = Project()
        a, _ = self.two(p)
        code, out = p.run("depends", a, "--on", a)
        self.assertEqual(1, code)
        self.assertIn("itself", out["refused"])

    def test_a_cycle_only_on_the_projection_is_not_task_truth(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        p.run("depends", a, "--on", "TASK-999")
        board = p.board().replace("| TASK-999 |", f"| {b} |")
        board = board.replace("TASK-999", b)
        (p.root / "BOARD.md").write_text(board)
        d = self.payload(p)
        cycles = d["conformance"]["dependency_cycles"]
        self.assertEqual(cycles, [])
        self.assertEqual(["TASK-999"], self.task(p, a)["depends_on"])

    # ── the write paths ───────────────────────────────────────────────────

    def test_blocked_is_satisfied_by_on_as_well_as_by_reason(self):
        """The refusal was right and the answer landed in prose. `--on` makes
        the same demand and reaches the payload."""
        p = Project()
        a, b = self.two(p)
        code, _ = p.run("status", b, "--status", "blocked", "--on", a)
        self.assertEqual(0, code)
        self.assertEqual([a], self.task(p, b)["depends_on"])

    def test_blocked_with_neither_on_nor_reason_is_still_refused(self):
        p = Project()
        a, _ = self.two(p)
        code, out = p.run("status", a, "--status", "blocked")
        self.assertEqual(1, code)
        self.assertIn("unblock", out["refused"])

    def test_add_depends_writes_a_cell_and_not_only_journal_prose(self):
        p = Project()
        a, _ = self.two(p)
        _, b = p.run("add", "--title", "later", "--priority", "P0",
                     "--depends", a)
        self.assertEqual([a], self.task(p, b["id"])["depends_on"],
                         "--depends still only reached the journal")
        self.assertIn(f"- **Dependencies**: {a}", p.journal())

    def test_prose_in_the_dependency_flag_is_refused(self):
        """Free text here would rebuild, one column to the right, the very
        unreadable `- **Dependencies**: <free text>` line this replaces."""
        p = Project()
        a, _ = self.two(p)
        code, out = p.run("depends", a, "--on", "waiting for the design review")
        self.assertEqual(1, code)
        self.assertIn("not an id", out["refused"])

    def test_clear_records_that_a_row_waits_on_nothing(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        self.assertEqual(0, p.run("depends", b, "--clear")[0])
        self.assertEqual([], self.task(p, b)["depends_on"])

    def test_declaring_the_same_edge_twice_is_refused_as_a_no_op(self):
        p = Project()
        a, b = self.two(p)
        p.run("depends", b, "--on", a)
        code, _ = p.run("depends", b, "--on", a)
        self.assertEqual(1, code)

    # ── the migration worklist ────────────────────────────────────────────

    def test_a_blocked_row_with_no_declared_edge_is_named(self):
        """The honest measure of how far the backfill has got. On Perry's own
        board this is every blocked row: their dependency is prose inside
        `Next action`, where nothing can read it."""
        p = Project()
        a, b = self.two(p)
        p.run("status", a, "--status", "blocked", "--reason", "waiting on Apple")
        p.run("status", b, "--status", "blocked", "--on", a)
        c = self.payload(p)["conformance"]
        self.assertEqual([a], c["blocked_without_dependency"])

    def test_a_cell_a_project_wrote_in_its_own_language_is_read(self):
        """`reference/i18n.md`: a board may be written in the project's own
        language, and a column table that only speaks English would report
        every such row as declaring nothing — which reads as `startable`."""
        p = Project()
        a, b = self.two(p)
        board = p.board().replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n"
            f"| {a} ", "| ID | Title | Owner | Status | Next action | Evidence | 依赖 |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| {a} ", 1)
        board = board.replace(f"| {a} | first | Coding Agent | not_started | — | — |",
                              f"| {a} | first | Coding Agent | not_started | — | — | {b} |")
        (p.root / "BOARD.md").write_text(board)
        p.import_board()
        self.assertEqual([b], self.task(p, a)["depends_on"],
                         "a `依赖` column was invisible to the reader")


class TestTheSectionsAWorkSurfaceShows(unittest.TestCase):
    """TASK-058. `risks`, `asks` and `drift` — written by `perry-task`, and
    readable until 1.6 only through `perry-state --json`, the one payload that
    carries no version at all. `## User Input Queue` is the *needs-you* list.
    """

    def payload(self, p) -> dict:
        _, out = p.run("list", "--all")
        return out

    def test_an_ask_carries_an_integer_age_beside_the_rendered_string(self):
        """`idle` was `"9d"` — displayable, unsortable. The needs-you list is
        what a dashboard sorts on."""
        p = Project()
        _, u = p.run("ask", "--needed", "the signing certificate",
                     "--arrived", "2020-01-01")
        item = next(a for a in self.payload(p)["asks"]["items"] if a["id"] == u["id"])
        self.assertIsInstance(item["idle_days"], int)
        self.assertGreater(item["idle_days"], 1000)

    def test_an_answered_ask_is_not_in_the_needs_you_list(self):
        """One shared predicate decides this. Counting answered rows is how a
        dashboard came to say "2 items waiting on you" about two questions
        answered the same day."""
        p = Project()
        _, u = p.run("ask", "--needed", "a decision")
        self.assertEqual(1, self.payload(p)["asks"]["open"])
        p.run("answer", u["id"], "--answer", "yes")
        self.assertEqual(0, self.payload(p)["asks"]["open"])

    def test_a_bullet_risk_does_not_report_its_severity_letter_as_an_id(self):
        """Measured: `- H · Apple developer agreement expired` arrived as
        `{"id": "H", "title": "· Apple …", "severity": "watch"}`. Three defects,
        one cause — nothing told the parser the first token was a marker."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- H · Apple developer agreement expired")
        (p.root / "BOARD.md").write_text(board)
        r = self.payload(p)["risks"]["items"][0]
        self.assertEqual("", r["id"], "the severity letter was published as an id")
        self.assertEqual("Apple developer agreement expired", r["title"])
        self.assertEqual("H", r["severity_text"])
        self.assertEqual("high", r["severity_rank"])

    def test_two_risks_a_human_ranked_differently_are_ranked_differently(self):
        """`severity` is the STANCE and is `watch` for both. The magnitude the
        project wrote is a second axis, and folding them into one is what made
        an H and an M display identically."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- H · certificate expired\n- L · docs are thin")
        (p.root / "BOARD.md").write_text(board)
        ranks = [r["severity_rank"] for r in self.payload(p)["risks"]["items"]]
        self.assertEqual(["high", "low"], ranks)

    def test_a_risk_line_with_no_marker_keeps_its_first_word(self):
        """The narrowing check. A guard written around `H` alone would let a
        parser eat the first word of every unmarked sentence — which is what it
        used to do: `- Perry is half-adopted` reported `id: "Perry"`."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- Hostname resolution is flaky in CI")
        (p.root / "BOARD.md").write_text(board)
        r = self.payload(p)["risks"]["items"][0]
        self.assertEqual("Hostname resolution is flaky in CI", r["title"])
        self.assertEqual("", r["severity_text"])

    def test_two_risks_with_no_id_both_survive_the_merge(self):
        """The dedup key was the id, so a risk with a falsy one was silently
        discarded — unreachable only while the parser was inventing ids out of
        first words. Removing the invention would have taken every bullet risk
        on every unmigrated project to zero."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- H · certificate expired\n- M · vendor is late")
        (p.root / "BOARD.md").write_text(board)
        self.assertEqual(2, self.payload(p)["risks"]["open"])

    def test_drift_reports_a_row_the_tool_never_wrote(self):
        p = Project()
        p.run("add", "--title", "written by the tool", "--priority", "P0")
        board = p.board().replace(
            "## P1", "| HAND-001 | typed in by hand | User | not_started | — | — |\n\n## P1", 1)
        (p.root / "BOARD.md").write_text(board)
        d = self.payload(p)["drift"]
        self.assertTrue(d["checked"])
        self.assertEqual(1, d["unrecorded"])
        self.assertIn("HAND-001", d["unrecorded_sample"])

    def test_a_project_with_no_event_log_reports_drift_unchecked_not_broken(self):
        """**The name was true and the assertion was not (TASK-117).**

        `unchecked` was pinned by `checked is False` and then contradicted one
        line down by `drift == 0`, which is a finding. Every field that would
        otherwise report an absence is `null` here — rule 1 of this contract
        names `null` as the unknown value, and a consumer that skipped the flag
        now fails on it instead of rendering a clean board.
        """
        p = Project()
        d = self.payload(p)["drift"]
        self.assertFalse(d["checked"])
        for key in ("drift", "unrecorded", "unrecorded_sample",
                    "orphaned", "stale_done"):
            self.assertIsNone(d[key], f"`{key}` answers a question nobody asked")

    def test_the_three_blocks_are_present_on_a_board_that_has_none_of_them(self):
        """Rule 1 of the contract: an unknown value is `""`, `null` or `[]`,
        never a missing key."""
        p = Project(board=BOARD.split("## Cadence")[0])
        d = self.payload(p)
        self.assertEqual([], d["risks"]["items"])
        self.assertEqual([], d["asks"]["items"])
        self.assertEqual(0, d["asks"]["open"])


if __name__ == "__main__":
    unittest.main()
