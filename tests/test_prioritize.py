"""`perry-task prioritize` — the writer triage's central act did not have.

`perry-task` shipped 22 subcommands and none of them could change a row's
priority. `add` sets it once; `route` — the only other thing that writes a
priority cell — takes an *intake row number*, mints a *new* id, and refuses on
any track in `project` mode. So re-prioritising, which is what `triage`,
`monday-plan`, `friday-review` and `mid-phase-review` all end in, could only be
done by hand-editing `BOARD.md`.

A hand edit lands with **no event**, so `perry-state § reconcile_drift` reports
it as unrecorded drift — the exact failure `DESIGN-004` was written against —
and `priority` is a published field of `perry-task/list` that aiMark's Projects
view sorts on. A front-end could display a priority no caller could change.

Found by trying to execute a triage verdict rather than by reading the code.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import tables as T  # noqa: E402

TOOL = PERRY_HOME / "bin" / "perry-task"
HEADER = ["ID", "Title", "Owner", "Status", "Next action", "Evidence",
          "Verification"]
SEP = "|" + "---|" * len(HEADER)


def row(tid, title="t", owner="o", status="not_started", nxt="do it",
        ev="—", ver="V2"):
    return T.render_row([tid, title, owner, status, nxt, ev, ver])


def board(p0=(), p1=(), p2=(), extra_sections=""):
    return "\n".join([
        "# Board", "",
        "## P0", "", T.render_row(HEADER), SEP, *p0, "",
        "## P1", "", T.render_row(HEADER), SEP, *p1, "",
        "## P2", "", T.render_row(HEADER), SEP, *p2, "",
        extra_sections,
        "## Cadence", "",
        "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
        "|---|---|---|---|---|---|", "",
        "## User Input Queue", "",
        "| ID | Needed from user | Blocks | Asked | Status |",
        "|---|---|---|---|---|", "",
        "## Top risks", "",
        "| ID | Risk | Opened | Severity | Cleared |",
        "|---|---|---|---|---|", "",
    ])


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "perry").mkdir()
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Config\n\nState root: perry/\n", encoding="utf-8")
        self.addCleanup(self.tmp.cleanup)

    def write(self, text):
        (self.root / "perry" / "BOARD.md").write_text(text, encoding="utf-8")

    def read(self):
        return (self.root / "perry" / "BOARD.md").read_text(encoding="utf-8")

    def run_tool(self, *argv):
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        return subprocess.run([sys.executable, str(TOOL), *argv,
                               "--root", str(self.root)],
                              capture_output=True, text=True, env=env)

    def payload(self):
        out = self.run_tool("list", "--all", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def task(self, tid):
        return [t for t in self.payload()["tasks"] if t["id"] == tid][0]

    def section_of(self, tid):
        """Which `## …` heading the row currently sits under."""
        head = None
        for line in self.read().split("\n"):
            if line.startswith("## "):
                head = line[3:].strip()
            elif line.strip().startswith("|") and T.split_row(line)[0] == tid:
                return head
        return None


class TestItMoves(Base):
    def setUp(self):
        super().setUp()
        self.write(board(p2=[row("TASK-001", nxt="a long next action",
                                 ev="evidence/x.md", ver="V4")]))

    def test_the_row_moves_and_keeps_its_id(self):
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.section_of("TASK-001"), "P1")
        self.assertEqual(self.task("TASK-001")["priority"], "P1")

    def test_every_other_cell_survives_the_move(self):
        """A move, not a re-file. Re-adding under a new priority would mint a
        second id — and an id is permanent and never reissued — so the row has
        to carry its own cells across."""
        self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        t = self.task("TASK-001")
        self.assertEqual(t["next_action"], "a long next action")
        self.assertEqual(t["evidence"], "evidence/x.md")
        self.assertEqual(t["verification"], "V4")
        self.assertEqual(t["title"], "t")

    def test_the_move_is_one_row_leaving_and_one_arriving(self):
        before = self.read().count("TASK-001")
        self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        self.assertEqual(before, 1)
        self.assertEqual(self.read().count("TASK-001"), 1,
                         "the row was copied rather than moved")

    def test_it_emits_an_event_so_the_move_is_not_drift(self):
        """The whole reason this subcommand exists. A hand edit lands with no
        event and `perry-state § reconcile_drift` reports it as unrecorded."""
        self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        tl = self.task("TASK-001")["timeline"]
        self.assertTrue(tl, "no timeline")
        last = tl[-1]
        self.assertEqual(last["event"], "prioritize")
        self.assertEqual((last["from"], last["to"]), ("P2", "P1"))

    def test_from_and_to_are_the_section_and_the_event_says_so(self):
        """Every other event uses `from`/`to` for the STATUS. A consumer that
        assumed so would read a move as a status change, so the event carries
        `field: priority` to disambiguate without a per-event special case."""
        self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        events = [json.loads(l) for l in
                  (self.root / ".perry" / "events.jsonl").read_text().splitlines() if l.strip()]
        ev = [e for e in events if e["event"] == "prioritize"][-1]
        self.assertEqual(ev["field"], "priority")
        self.assertEqual(self.task("TASK-001")["status"], "not_started",
                         "the status must not have moved")

    def test_a_dry_run_writes_nothing(self):
        before = (self.root / "perry" / "BOARD.md").read_bytes()
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P1",
                            "--dry-run")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual((self.root / "perry" / "BOARD.md").read_bytes(), before)


class TestItRefuses(Base):
    def setUp(self):
        super().setUp()
        self.write(board(p2=[row("TASK-001")]))

    def test_a_move_to_where_it_already_is_is_refused(self):
        """A no-op that still emitted an event would put a move in the timeline
        that did not happen, and the timeline is what `list` reports as
        history."""
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P2")
        self.assertEqual(out.returncode, 1)
        self.assertIn("already under", out.stderr)

    def test_naming_no_destination_is_refused(self):
        out = self.run_tool("prioritize", "TASK-001")
        self.assertEqual(out.returncode, 1)
        self.assertIn("--priority", out.stderr)

    def test_an_unknown_priority_is_refused(self):
        out = self.run_tool("prioritize", "TASK-001", "--priority", "URGENT")
        self.assertEqual(out.returncode, 1)

    def test_a_row_that_is_not_on_the_board_is_refused(self):
        out = self.run_tool("prioritize", "TASK-999", "--priority", "P1")
        self.assertEqual(out.returncode, 1)
        self.assertIn("TASK-999", out.stderr)

    def test_a_refusal_writes_nothing(self):
        before = (self.root / "perry" / "BOARD.md").read_bytes()
        self.run_tool("prioritize", "TASK-001", "--priority", "P2")
        self.run_tool("prioritize", "TASK-999", "--priority", "P1")
        self.assertEqual((self.root / "perry" / "BOARD.md").read_bytes(), before)


class TestBoardsThatAreNotShapedLikePerrys(Base):
    """The case `route` could not reach, and the reason `--group` exists.

    `~/proj/gimegime-pmo` — the only year-old real project available — files
    work under its own headings and has no `## P0`/`## P1`/`## P2` at all.
    A subcommand that only worked on Perry-shaped boards would be unusable on
    exactly the projects migration is aimed at.
    """

    def setUp(self):
        super().setUp()
        self.write("\n".join([
            "# Board", "",
            "## Open — 工程线", "", T.render_row(HEADER), SEP,
            row("ENG-001", nxt="keep me"), "",
            "## Open — 投资线", "", T.render_row(HEADER), SEP, "",
            "## Cadence", "",
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
            "|---|---|---|---|---|---|", "",
            "## User Input Queue", "",
            "| ID | Needed from user | Blocks | Asked | Status |",
            "|---|---|---|---|---|", "",
            "## Top risks", "",
            "| ID | Risk | Opened | Severity | Cleared |",
            "|---|---|---|---|---|", "",
        ]))

    def test_a_row_moves_between_the_projects_own_headings(self):
        out = self.run_tool("prioritize", "ENG-001", "--group", "Open — 投资线")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.section_of("ENG-001"), "Open — 投资线")
        self.assertEqual(self.task("ENG-001")["next_action"], "keep me")

    def test_no_priority_section_is_created_on_a_board_that_has_none(self):
        """"No automatic rewrite of a project's existing structure" is an
        Anti-Goal. The refusal must name the headings the project does use."""
        out = self.run_tool("prioritize", "ENG-001", "--priority", "P1")
        self.assertEqual(out.returncode, 1)
        self.assertIn("Open — 工程线", out.stderr)
        self.assertNotIn("## P1", self.read())


class TestTheIndexIsCheckedBeforeAnythingIsDeleted(Base):
    """`remove_row` pops by index without looking at what it pops.

    The index is computed before the destination is widened, so its validity
    is an assumption about two other functions — `ensure_columns` and
    `ensure_section_columns` — held across a call, guarding the one operation
    on this board that deletes a line. Today they rewrite in place and never
    insert, so it holds. A widener that ever grew to insert a row would
    silently delete somebody else's task and append this one, and **both
    boards would still parse**.

    This class exists because the mutation written to prove the *ordering*
    came back green: the ordering genuinely does not matter, because `values`
    is extracted before either call. The invariant that does matter is this
    one, and it was invisible until the mutation failed to find anything.
    """

    def test_a_widener_that_inserts_is_refused_and_deletes_nothing(self):
        """Simulated by inserting a line above the row between locate and
        remove — which is exactly what a future `ensure_columns` that grew an
        insert would do."""
        self.write(board(p2=[row("TASK-001"), row("TASK-002")]))
        text = self.read()
        # The guard reads `board.lines[idx]`; shift the board by one line under
        # it by making the widener's own section grow. `--group` on a heading
        # that does not exist is refused earlier, so drive it through the code
        # rather than the CLI.
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        probe = (
            "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r)\n"
            "import importlib.machinery as m\n"
            "t = m.SourceFileLoader('t', %r).load_module()\n"
            "orig = t.widen_target_section\n"
            "def sneaky(board, priority, group, values):\n"
            "    orig(board, priority, group, values)\n"
            "    board.lines.insert(0, '')   # a widener that inserts\n"
            "t.widen_target_section = sneaky\n"
            "sys.exit(t.main(['prioritize','TASK-002','--priority','P1',"
            "'--root', %r]))\n"
        ) % (str(PERRY_HOME / "viewer"), str(PERRY_HOME / "bin"), str(TOOL),
             str(self.root))
        out = subprocess.run([sys.executable, "-c", probe],
                             capture_output=True, text=True, env=env)
        self.assertIn("shifted under the write", out.stdout + out.stderr)
        self.assertEqual(self.read(), text, "a refusal wrote to the board")


class TestWideningReachesTheDestination(Base):
    """A narrow destination gains the columns the row needs.

    Not about ordering — see the class above for why that turned out not to be
    the invariant. This is about the widening happening at all: without it the
    row is appended against a header that never gained the column, and
    whichever cell only the source carried is dropped with no error anywhere.
    """

    def setUp(self):
        super().setUp()
        narrow = ["ID", "Title", "Owner", "Status"]
        self.write("\n".join([
            "# Board", "",
            "## P0", "", T.render_row(narrow), "|" + "---|" * len(narrow), "",
            "## P2", "", T.render_row(HEADER), SEP,
            row("TASK-001", nxt="must survive", ev="evidence/y.md", ver="V3"), "",
            "## Cadence", "",
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
            "|---|---|---|---|---|---|", "",
            "## User Input Queue", "",
            "| ID | Needed from user | Blocks | Asked | Status |",
            "|---|---|---|---|---|", "",
            "## Top risks", "",
            "| ID | Risk | Opened | Severity | Cleared |",
            "|---|---|---|---|---|", "",
        ]))

    def test_the_narrow_destination_gains_the_columns_and_no_cell_is_lost(self):
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        self.assertEqual(out.returncode, 0, out.stderr)
        t = self.task("TASK-001")
        self.assertEqual(t["next_action"], "must survive")
        self.assertEqual(t["evidence"], "evidence/y.md")
        self.assertEqual(t["verification"], "V3")


class TestTheEventIsPartOfTheDeclaredSet(unittest.TestCase):
    def test_prioritize_is_a_task_event_not_a_section_event(self):
        """`TASK_EVENTS` and `SECTION_EVENTS` are asserted to be a partition of
        `COMMANDS`. A new subcommand that lands in neither drops out of the
        payload silently; one that lands in both leaks into it."""
        spec = importlib.util.spec_from_loader(
            "perry_task",
            importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertIn("prioritize", mod.COMMANDS)
        self.assertIn("prioritize", mod.TASK_EVENTS)
        self.assertNotIn("prioritize", mod.SECTION_EVENTS)

    def test_it_is_documented_in_the_usage_banner(self):
        """A subcommand a user cannot discover is one they will hand-edit
        around, which is the failure this whole module is about."""
        doc = TOOL.read_text(encoding="utf-8").split('"""')[1]
        self.assertIn("perry-task prioritize", doc)




class TestAClosedRowKeepsThePriorityItWasMovedTo(Base):
    """A row that has left the board is folded back together from events.

    `cmd_list` rebuilds a closed row with
    `t["priority"] = e.get("priority") or t["priority"]` — there are no cells
    left to read. The `prioritize` event therefore has to carry `priority` and
    `group` the way `add` and `route` do, or the fold silently keeps the `add`
    event's value and the payload reports a priority the row's **own timeline**,
    two lines above, says it moved away from.

    Found by running the lifecycle end to end rather than by reading the code.
    """

    def setUp(self):
        super().setUp()
        self.write(board(p1=[row("TASK-001")]))

    def test_the_closed_row_reports_where_it_was_moved_to(self):
        self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        (self.root / "perry" / "evidence").mkdir(parents=True, exist_ok=True)
        (self.root / "perry" / "evidence" / "e.md").write_text("x", encoding="utf-8")
        out = self.run_tool("done", "TASK-001", "--evidence", "evidence/e.md",
                            "--rung", "V3")
        self.assertEqual(out.returncode, 0, out.stderr)
        t = self.task("TASK-001")
        self.assertFalse(t["open"], "the row should have left the board")
        self.assertEqual(t["priority"], "P0")

    def test_the_field_never_disagrees_with_its_own_timeline(self):
        """The check that would have caught it without knowing the mechanism."""
        self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        (self.root / "perry" / "evidence").mkdir(parents=True, exist_ok=True)
        (self.root / "perry" / "evidence" / "e.md").write_text("x", encoding="utf-8")
        self.run_tool("done", "TASK-001", "--evidence", "evidence/e.md",
                      "--rung", "V3")
        t = self.task("TASK-001")
        moves = [e for e in t["timeline"] if e["event"] == "prioritize"]
        self.assertTrue(moves)
        self.assertEqual(t["priority"], moves[-1]["to"],
                         "the payload disagrees with its own timeline")


if __name__ == "__main__":
    unittest.main()
