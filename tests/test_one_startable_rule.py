"""TASK-148 — the `startable` rule is stated once, and both list paths call it.

`bin/perry-task` had two statements of the rule, ~200 lines apart, and **both
are reachable**: `cmd_list` serves `perry-task list` on a project that has a
store, and `_cmd_list_from_board` is called at `bin/perry-task:1547` from
`store_records` — the derivation that mints a store for a project without one,
and that `bin/perry-tasks build/write/verify` runs. TASK-141 changed the rule
and had to change it twice.

**This row moved the rule; it did not edit it.** The payloads were diffed
before and after — this repository's own `perry-task list --json`, a fixture
with a store, and the full `_cmd_list_from_board` payload on a fixture without
one — and differ in nothing. What is asserted here is the property that made
the duplication a defect rather than a style complaint: *the two paths agree*.

## The three claims

1. **Both callers are actually reached.** Not "the function is importable" —
   `cmd_list` is exercised through the CLI, and `_cmd_list_from_board` is
   called exactly the way line 1547 calls it, against a project whose store has
   been removed. That is the only route to it, and it is named here so a reader
   does not have to rediscover it.
2. **They agree.** Same dependency graph, same `startable` and `blocked_stale`,
   row for row.
3. **A second copy cannot come back.** `tests/one_startable_rule.py` finds the
   rule's shape in `bin/` by AST and requires exactly one home. It is proved
   against a planted copy rather than trusted, and against the pre-change file
   itself — `git show HEAD~:bin/perry-task` is not available to a test, so the
   plant reproduces its shape instead.

**The fixture is built through the tool's own writer** — `add`, `status
--status blocked --on`, `done` — never by hand-editing a board, because the
stale-`blocked` row this rule exists for is produced by the ordinary close
path and a hand-edited board would not exercise it.

Run: python3 tests/parallel test_one_startable_rule
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import one_startable_rule as guard                      # noqa: E402
from test_task_writer import PT, PERRY_HOME, Project    # noqa: E402


#: The fields the rule decides, read out of a payload as one comparable value.
def rule_rows(payload: dict) -> dict[str, tuple]:
    return {t["id"]: (t["status"], tuple(t["depends_on"]),
                      tuple(t["blocked_by"]), t["startable"], t["blocked_stale"])
            for t in payload["tasks"]}


class Graph:
    """One project, four rows, and only one of the two blockers closed.

    TASK-002 reproduces TASK-037's shape: `status: blocked`, one declared
    dependency, that dependency closed through `done`. TASK-004 is the control
    that keeps this from being "drop the check" — same shape, blocker still
    open. TASK-005 is `blocked` with no declared dependency and TASK-006 is in
    `review`; both are boundaries the rule deliberately does not cross, and a
    payload where every row answered the same way would prove nothing.
    """

    def __init__(self):
        self.project = Project()
        for title in ("closed blocker", "dependent of a closed blocker",
                      "open blocker", "dependent of an open blocker",
                      "blocked on something that is not a task", "in review"):
            code, out = self.project.run("add", "--title", title,
                                         "--priority", "P1")
            assert code == 0, out
        for dependent, blocker in (("TASK-002", "TASK-001"),
                                   ("TASK-004", "TASK-003")):
            code, out = self.project.run("status", dependent, "--status",
                                         "blocked", "--on", blocker)
            assert code == 0, out
        code, out = self.project.run("status", "TASK-005", "--status", "blocked",
                                     "--reason", "waiting on a vendor")
        assert code == 0, out
        code, out = self.project.run("status", "TASK-006", "--status", "review")
        assert code == 0, out
        # The ordinary close path, on ONE of the two blockers. Nothing here
        # touches TASK-002 — the stale state is a side effect of closing
        # something else, which is why it goes unnoticed.
        code, out = self.project.run("done", "TASK-001", "--evidence", "tests/run")
        assert code == 0, out

    # ── caller one: `cmd_list`, through the CLI, with a store on disk ──────

    def from_store(self) -> dict:
        code, out = self.project.run("list", "--all")
        assert code == 0, out
        return out

    # ── caller two: `_cmd_list_from_board`, the only way there ────────────

    def from_board(self) -> dict:
        """`bin/perry-task:1547`, reproduced — a copy of the project with no store.

        `store_records` builds this ctx and makes this call; `perry-tasks
        build` and `perry-tasks write --from-board` are the commands that reach
        it. A project WITH a store never takes this path, so the store is
        removed rather than mocked: the board and the event log are what this
        derivation is defined over.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "no-store"
            shutil.copytree(self.project.root, root)
            stores = list(root.rglob("tasks.jsonl"))
            assert stores, "the fixture never had a store to remove"
            for store in stores:
                store.unlink()
            state_root = PT.lib.resolve_state_root(root)
            board = PT.Board(state_root / "BOARD.md")
            board.refuse_duplicate_task_ids()
            ctx = {"schema": PT.load_schema(), "project_root": root,
                   "state_root": state_root, "config": {"tracks": []},
                   "board": board, "events": PT.read_events(root),
                   "sections": False}
            return PT._cmd_list_from_board(
                PT.parse(["list", "--all", "--root", str(root)]), ctx)


class TestBothListPathsAreReached(unittest.TestCase):
    """Claim 1. Neither path is asserted about until it has been shown to run."""

    @classmethod
    def setUpClass(cls):
        cls.graph = Graph()
        cls.store = cls.graph.from_store()
        cls.board = cls.graph.from_board()

    def test_the_store_path_returns_the_rows(self):
        self.assertEqual(6, len(rule_rows(self.store)))

    def test_the_board_path_returns_the_rows(self):
        """If this ever fails to reach `_cmd_list_from_board`, the finding is
        bigger than this row: it would mean the board-derived path really is
        dead, which an earlier record claimed and TASK-148 disproved."""
        self.assertEqual(6, len(rule_rows(self.board)))

    def test_the_graph_is_not_uniform(self):
        """Anti-vacuity. Two paths that agree because every row answers the
        same way have been compared about nothing."""
        rows = rule_rows(self.store)
        self.assertTrue(any(r[3] for r in rows.values()), "no startable row")
        self.assertTrue(any(not r[3] for r in rows.values()),
                        "no unstartable row")
        self.assertTrue(any(r[4] for r in rows.values()),
                        "no blocked_stale row — the exception is untested")


class TestTheTwoPathsAgree(unittest.TestCase):
    """Claim 2, which is the property the duplication put at risk."""

    @classmethod
    def setUpClass(cls):
        cls.graph = Graph()
        cls.store = rule_rows(cls.graph.from_store())
        cls.board = rule_rows(cls.graph.from_board())

    def test_the_same_rows_are_reported(self):
        self.assertEqual(set(self.store), set(self.board))

    def test_startable_and_blocked_stale_agree_row_for_row(self):
        for tid in sorted(self.store):
            self.assertEqual(
                self.store[tid], self.board[tid],
                f"{tid}: `cmd_list` and `_cmd_list_from_board` disagree — "
                f"store={self.store[tid]} board={self.board[tid]}")

    def test_the_stale_blocked_row_reads_the_same_on_both(self):
        """TASK-141's row, specifically: this is the value that had to be
        fixed twice, so it is the one named here."""
        for payload in (self.store, self.board):
            status, _depends, blocked_by, startable, stale = payload["TASK-002"]
            self.assertEqual("blocked", status)
            self.assertEqual((), blocked_by)
            self.assertTrue(startable)
            self.assertTrue(stale)

    def test_the_genuinely_blocked_row_reads_the_same_on_both(self):
        for payload in (self.store, self.board):
            _status, _depends, blocked_by, startable, stale = payload["TASK-004"]
            self.assertEqual(("TASK-003",), blocked_by)
            self.assertFalse(startable)
            self.assertFalse(stale)

    def test_the_boundaries_read_the_same_on_both(self):
        """A `blocked` row with no declared dependency, and a `review` row.
        Neither is touched by the exception, on either path."""
        for payload in (self.store, self.board):
            for tid in ("TASK-005", "TASK-006"):
                _status, depends, _by, startable, stale = payload[tid]
                self.assertEqual((), depends, tid)
                self.assertFalse(startable, tid)
                self.assertFalse(stale, tid)


class TestTheRuleHasExactlyOneHome(unittest.TestCase):
    """Claim 3. `tests/one_startable_rule.py` is the check; this holds it."""

    def test_bin_states_the_rule_in_exactly_one_place(self):
        result = guard.measure()
        self.assertTrue(
            guard.ok(result),
            "the startable rule is no longer stated exactly once under "
            "`bin/`:\n" + guard.report(result))

    def test_the_one_home_is_importable_by_both_callers(self):
        """A shared home nobody imports is not shared. Both list paths call
        `lib.resolve_startability`, and the function the guard found is it."""
        self.assertEqual(1, guard.measure()["home_count"])
        home = next(iter(guard.measure()["homes"]))
        self.assertIn("resolve_startability", home)
        self.assertTrue(callable(PT.lib.resolve_startability))
        source = (PERRY_HOME / "bin" / "perry-task").read_text()
        self.assertEqual(
            2, source.count("lib.resolve_startability("),
            "both list paths must call the one implementation")

    def test_the_waiting_statuses_are_real_statuses(self):
        """`bin/lib` restates the enum rather than loading the schema, the same
        trade `TASK_STATUSES` makes one screen above it. A restatement needs a
        pin or a typo becomes a status nothing is ever in — which fails open,
        reporting a waiting row as startable."""
        enum = set(PT.load_schema()["enums"]["task_status"])
        self.assertLessEqual(set(PT.lib.WAITING_ON_SOMEBODY_ELSE), enum)
        self.assertEqual(2, len(PT.lib.WAITING_ON_SOMEBODY_ELSE))

    def test_the_scan_reads_every_python_file_under_bin(self):
        """Including `bin/lib/`, one directory down — two sibling guards in
        this suite were measured blind to exactly that."""
        names = {p.name for p in guard.sources()}
        for expected in ("perry-task", "perry-tasks", "__init__.py",
                         "perry_store.py"):
            self.assertIn(expected, names)


class TestTheGuardActuallyFires(unittest.TestCase):
    """Anti-vacuity for claim 3, proved against planted copies rather than
    trusted. A check written and never seen to redden is ceremony."""

    #: The shape as `_cmd_list_from_board` carried it, variable names and all.
    OLD_BOARD_COPY = '''
def _cmd_list_from_board(args, ctx):
    waiting = {"blocked", "review"}
    for t in tasks.values():
        t["blocked_stale"] = bool(t["open"] and t["status"] == "blocked"
                                  and t["depends_on"] and not t["blocked_by"])
        t["startable"] = bool(t["open"] and not t["blocked_by"]
                              and (t["blocked_stale"]
                                   or t["status"] not in waiting))
'''

    #: And as `cmd_list` carried it — same rule, different spelling. A regex
    #: for one of these would not have found the other.
    OLD_STORE_COPY = '''
def cmd_list(args, ctx):
    for task in tasks.values():
        task["blocked_stale"] = bool(task["open"] and task["status"] == "blocked"
                                     and task["depends_on"]
                                     and not task["blocked_by"])
        task["startable"] = bool(task["open"] and not task["blocked_by"]
                                 and (task["blocked_stale"]
                                      or task["status"] not in {"blocked", "review"}))
'''

    def scan(self, text: str):
        return guard.scan_source(text, "planted.py")

    def test_it_finds_the_board_path_copy(self):
        homes = guard.homes(self.scan(self.OLD_BOARD_COPY))
        self.assertEqual(1, len(homes))
        self.assertIn("_cmd_list_from_board", next(iter(homes)))

    def test_it_finds_the_store_path_copy_written_differently(self):
        homes = guard.homes(self.scan(self.OLD_STORE_COPY))
        self.assertEqual(1, len(homes))
        self.assertIn("cmd_list", next(iter(homes)))

    def test_two_copies_in_ONE_file_are_two_homes(self):
        """The defect exactly as it stood: both copies lived in `bin/perry-task`.
        A per-file count would have called that one home and stayed green."""
        homes = guard.homes(self.scan(self.OLD_BOARD_COPY + self.OLD_STORE_COPY))
        self.assertEqual(2, len(homes), sorted(homes))

    def test_a_planted_copy_beside_the_real_one_reddens_the_check(self):
        """The whole `bin/` tree, copied, with a copy of the rule put back into
        a tool. This is the re-introduction the deliverable asks to be watched
        going red — no repository file is touched."""
        with tempfile.TemporaryDirectory() as tmp:
            fake_bin = Path(tmp) / "bin"
            shutil.copytree(PERRY_HOME / "bin", fake_bin,
                            ignore=shutil.ignore_patterns("__pycache__"))
            self.assertTrue(guard.ok(guard.measure(fake_bin)),
                            "the untouched copy should be green")
            (fake_bin / "perry-task").write_text(
                (fake_bin / "perry-task").read_text() + self.OLD_BOARD_COPY)
            after = guard.measure(fake_bin)
            self.assertFalse(guard.ok(after), guard.report(after))
            self.assertEqual(2, after["home_count"], sorted(after["homes"]))

    def test_the_rule_vanishing_also_reddens_the_check(self):
        """The other direction. A guard that passes when its subject is gone is
        the failure this suite keeps finding in its own checks."""
        with tempfile.TemporaryDirectory() as tmp:
            fake_bin = Path(tmp) / "bin"
            fake_bin.mkdir()
            (fake_bin / "nothing.py").write_text("x = 1\n")
            self.assertFalse(guard.ok(guard.measure(fake_bin)))

    def test_a_wider_status_set_is_not_the_waiting_set(self):
        """`perry-state` holds `{"not_started", "in_progress", "blocked",
        "review"}`. It contains both members and is a different claim; matching
        it would make this guard fire on code that never states the rule."""
        found = self.scan(
            'open_states = {"not_started", "in_progress", "blocked", "review"}\n')
        self.assertEqual([], found)

    def test_a_row_template_default_is_not_the_rule(self):
        """`{"startable": False, "blocked_stale": False}` is the blank the rule
        fills. Both list paths carry one and always will."""
        found = self.scan('t = {"startable": False, "blocked_stale": False}\n')
        self.assertEqual([], found)


if __name__ == "__main__":
    unittest.main()
