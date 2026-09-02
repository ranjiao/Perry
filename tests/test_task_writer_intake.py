"""Task-writer contract tests, split for module-level parallelism."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from task_writer_support import (
    BASIC_MODE_TRACKS, BOARD, MODE_TRACKS, PERRY_HOME, PT, Project,
    ROUND_TRIP_BOARD, ROUND_TRIP_ROW_IDS, ROUND_TRIP_ROW_PRIORITIES, TASKS,
    TOOL, ZH_BOARD, mode_cells,
)

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
            # `lib.is_blank_cell`, not `PT.ABSENT` — TASK-213 retired that
            # set as the fourth copy of the blank-cell list, and the one rule
            # also knows the declared Chinese spellings and the decorated
            # forms.
            if PT.lib.is_blank_cell(t["evidence"]):
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
        p = Project(tracks=MODE_TRACKS)
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


class TestAnIntakeRowTakesExactlyOneOutcome(unittest.TestCase):
    """B-3. Both `modes/queue.md` and `subcommands.md` state the rule; nothing
    enforced it. `answer`, `status`, `stage` and `risk-clear` all refuse a
    repeat transition — this was the fourth implementation and the only one
    that did not.

    Live rather than theoretical: discharged rows stay in intake until the
    review period closes, so the next drain walks them again.
    """

    TRACKS = MODE_TRACKS

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

    TRACKS = MODE_TRACKS

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

    TRACKS = MODE_TRACKS

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


if __name__ == "__main__":
    unittest.main()
