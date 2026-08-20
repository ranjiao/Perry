"""TASK-141 — a stored `blocked` must not mask an empty `blocked_by`.

The claim under test: **`startable` reports the dependency graph, not a cell
that has gone out of date behind it.**

Measured on Perry's own board on 2026-08-20. TASK-037 (waiting on TASK-092) and
TASK-045 (on the TASK-044 → TASK-047 chain) both sat at `status: blocked` with
every dependency closed, and both reported

    status=blocked   blocked_by=[]   startable=False

in one object. `blocked_by` is EMPTY — the payload had already computed that
nothing was blocking them. It could not say so because `startable` read the
stored `status` first:

    task["startable"] = bool(task["open"]
                             and task["status"] not in {"blocked", "review"}
                             and not task["blocked_by"])

so the third term was unreachable for exactly the rows it was there to catch,
and no consumer could see the disagreement. The other half is that
`perry-task done` never looks at its dependents: the ordinary close path CREATES
this state and that line then hid it. Two of the four blocked rows were stale.

**This is not "delete the check", and that is what most of this file is about.**
The other two rows — TASK-050 on TASK-094, TASK-067 on TASK-094 + TASK-095 —
were genuinely blocked and must stay that way, so every fixture here is built
in both directions at once: one row whose dependency closed and one whose
dependency did not, read out of the same payload. The remaining boundaries are
the `blocked` row that declares NO dependency (`conformance.
blocked_without_dependency` — the blocker is prose Perry cannot read, and "I
cannot see it" is not "it closed") and `review`, which waits on a human and so
can never be contradicted by a dependency edge.

**Every fixture is built through the store's own writer** — `add`, `status
--status blocked --on`, `done` — never by hand-editing a board. A hand-edited
board is drift, and it would not exercise the close path that produces the bug.

Run: python3 tests/parallel test_stale_blocked
"""

from __future__ import annotations

import unittest

from test_task_writer import Project


class Board:
    """Two dependents, two blockers, and only one of the blockers closed.

    TASK-002 reproduces TASK-037's shape exactly: `status: blocked`, one
    declared `depends_on`, and that dependency `done` through the ordinary
    close path. TASK-004 is the control that stops this from being "delete the
    check" — same shape, blocker still open.
    """

    def __init__(self):
        self.p = Project()
        for title in ("closed blocker", "dependent of a closed blocker",
                      "open blocker", "dependent of an open blocker"):
            code, out = self.p.run("add", "--title", title, "--priority", "P1")
            assert code == 0, out
        for dependent, blocker in (("TASK-002", "TASK-001"),
                                   ("TASK-004", "TASK-003")):
            code, out = self.p.run("status", dependent, "--status", "blocked",
                                   "--on", blocker)
            assert code == 0, out
        # The ordinary close path, on ONE of the two blockers. Nothing here
        # touches TASK-002, which is the point: the stale state is a side
        # effect of closing something else.
        code, out = self.p.run("done", "TASK-001", "--evidence", "tests/run")
        assert code == 0, out

    def tasks(self) -> dict[str, dict]:
        code, out = self.p.run("list", "--all")
        assert code == 0, out
        return {t["id"]: t for t in out["tasks"]}

    def payload(self) -> dict:
        code, out = self.p.run("list", "--all")
        assert code == 0, out
        return out


class TestAStoredBlockedDoesNotMaskAnEmptyBlockedBy(unittest.TestCase):
    """V3 item 1, both directions, out of one payload."""

    @classmethod
    def setUpClass(cls):
        cls.board = Board()
        cls.tasks = cls.board.tasks()

    def test_the_measurement_itself_no_longer_reproduces(self):
        """TASK-037's shape, rebuilt by the writer. Before the fix this row
        reported `blocked_by=[] startable=False` in the same object."""
        row = self.tasks["TASK-002"]
        self.assertEqual(row["blocked_by"], [],
                         "the dependency closed; nothing should be blocking")
        self.assertTrue(
            row["startable"],
            "TASK-141: a row whose every declared dependency has closed still "
            f"reports startable={row['startable']} while blocked_by="
            f"{row['blocked_by']} — the stored status is masking the graph")

    def test_the_disagreement_is_named_rather_than_silently_recomputed(self):
        row = self.tasks["TASK-002"]
        self.assertTrue(row["blocked_stale"],
                        "the board says blocked and the graph says nothing is; "
                        "a consumer must be able to read that from the payload")

    def test_the_stored_status_is_left_alone(self):
        """The whole cost of taking option 2. `list` reports; it does not
        rewrite a cell nobody asked it to rewrite, so the row still READS
        blocked until somebody acts. If this ever starts failing, a write path
        grew a side effect and it needs an event in the log to be honest."""
        self.assertEqual(self.tasks["TASK-002"]["status"], "blocked")

    def test_a_row_with_an_open_dependency_is_still_blocked(self):
        """The other direction. This is what stops the fix from being a
        deleted check — on Perry's own board TASK-050 and TASK-067 are the
        live instances."""
        row = self.tasks["TASK-004"]
        self.assertEqual(row["blocked_by"], ["TASK-003"])
        self.assertFalse(
            row["startable"],
            "TASK-003 is still open — reporting TASK-004 startable would send "
            "somebody to work on something that is genuinely blocked")
        self.assertFalse(row["blocked_stale"],
                         "nothing is stale here; the blocker really is open")

    def test_closing_the_second_blocker_frees_its_dependent_too(self):
        """Same board, one more ordinary close. The control row crosses over
        only when its own dependency actually closes."""
        code, out = self.board.p.run("done", "TASK-003", "--evidence", "tests/run")
        self.assertEqual(code, 0, out)
        row = self.board.tasks()["TASK-004"]
        self.assertEqual(row["blocked_by"], [])
        self.assertTrue(row["startable"])
        self.assertTrue(row["blocked_stale"])


class TestTheBoundariesThisDoesNotCross(unittest.TestCase):
    """Three shapes that look like the bug and are not."""

    def test_a_blocked_row_that_declares_no_dependency_stays_blocked(self):
        """`conformance.blocked_without_dependency` — the migration worklist.
        Its blocker is in prose Perry cannot read, so `blocked_by` is empty for
        a completely different reason: not "the dependency closed" but "there
        is no dependency to look at." Calling that row startable would be the
        same error as calling an unknown id satisfied."""
        p = Project()
        code, out = p.run("add", "--title", "waiting on something in prose",
                          "--priority", "P1")
        self.assertEqual(code, 0, out)
        code, out = p.run("status", "TASK-001", "--status", "blocked",
                          "--reason", "waiting on a vendor, no row for it")
        self.assertEqual(code, 0, out)
        code, out = p.run("list", "--all")
        row = next(t for t in out["tasks"] if t["id"] == "TASK-001")
        self.assertEqual(row["depends_on"], [])
        self.assertEqual(row["blocked_by"], [])
        self.assertFalse(row["startable"],
                         "no declared edge means Perry cannot see the blocker; "
                         "'I do not know' is not 'it is finished'")
        self.assertFalse(row["blocked_stale"],
                         "nothing has gone stale — nothing was ever declared")
        self.assertIn("TASK-001",
                      out["conformance"]["blocked_without_dependency"],
                      "this row is still the migration worklist's business")

    def test_a_row_in_review_is_untouched(self):
        """`review` waits on a HUMAN, not on a row. No dependency edge can
        contradict it, so there is nothing here for this computation to know —
        and the original user report that put `review` in `waiting` at all was
        'I saw a pile of review rows and thought they could be advanced'."""
        p = Project()
        code, out = p.run("add", "--title", "waiting on a reviewer",
                          "--priority", "P1")
        self.assertEqual(code, 0, out)
        code, out = p.run("status", "TASK-001", "--status", "review")
        self.assertEqual(code, 0, out)
        code, out = p.run("list", "--all")
        row = next(t for t in out["tasks"] if t["id"] == "TASK-001")
        self.assertEqual(row["blocked_by"], [])
        self.assertFalse(row["startable"], "somebody else still has the ball")
        self.assertFalse(row["blocked_stale"])

    def test_a_closed_row_is_never_startable_or_stale(self):
        board = Board()
        row = board.tasks()["TASK-001"]
        self.assertFalse(row["open"])
        self.assertFalse(row["startable"])
        self.assertFalse(row["blocked_stale"])


class TestTheContractAnnouncedIt(unittest.TestCase):
    """A changed MEANING is not covered by "1.x only adds keys"."""

    def test_the_minor_carries_a_semantics_entry_naming_both_fields(self):
        payload = Board().payload()
        entry = next((s for s in payload["semantics"]
                      if s["version"] == "1.12"), None)
        self.assertIsNotNone(
            entry, "startable changed meaning and nothing announced it")
        self.assertEqual(set(entry["fields"]), {"startable", "blocked_stale"})

    def test_the_new_key_is_present_on_every_task_including_closed_ones(self):
        """Rule 1: an unknown value is `false`, never a missing key."""
        for row in Board().payload()["tasks"]:
            self.assertIn("blocked_stale", row, row["id"])
            self.assertIsInstance(row["blocked_stale"], bool)

    def test_the_derived_field_never_lands_in_the_store(self):
        """`blocked_stale` is computed from the graph on every read. A copy of
        it in `tasks.jsonl` would be a second truth that goes stale the same
        way the status did."""
        board = Board()
        store = (board.p.root / "tasks.jsonl").read_text()
        self.assertNotIn("blocked_stale", store)


if __name__ == "__main__":
    unittest.main()
