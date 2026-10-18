"""Task-writer contract tests, split for module-level parallelism."""

from __future__ import annotations

COVERS = (
    "bin/perry-task",
    "bin/perry-state",
    "modes/pipeline.md",
    "modes/queue.md",
)

import json
import os
import re
import subprocess
import tempfile
import unittest
from legacy_read_fixtures import seed_task, set_task, seed_ask, set_ask, seed_intake, rows, write
from kernel_work_support import ACTOR, ready, task
from pathlib import Path

from task_writer_support import (
    BASIC_MODE_TRACKS, BOARD, MODE_TRACKS, PERRY_HOME, PT, Project,
    ROUND_TRIP_BOARD, ROUND_TRIP_ROW_IDS, ROUND_TRIP_ROW_PRIORITIES, TASKS,
    TOOL, ZH_BOARD, mode_cells,
)

def snapshot(p):
    return {str(f.relative_to(p.root)): f.read_bytes() for f in p.root.rglob("*") if f.is_file()}


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
        live = seed_task(p, title='still going', priority='P0')
        set_task(p, live['id'] , event_name='evidence', evidence='`BOARD.md`')
        closed = seed_task(p, title='finished', priority='P1')
        set_task(p, closed['id'] , event_name='done', evidence='`BOARD.md`', verification='V3', status='done')
        gone = seed_task(p, title='finished, artifact moved', priority='P2')
        set_task(p, gone['id'] , event_name='done', evidence='`evidence/2026-07/gone.md`', verification='V3', status='done')
        seed_task(p, title='no evidence yet', priority='P2')
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


class TestNativeAskLifecycle(unittest.TestCase):
    def test_question_answer_and_dependency_are_native_and_auditable(self):
        sb = ready(self)
        ask = sb.create("ask", fields={"question": "Threshold?"})
        tid = task(sb)
        sb.ok("rel add", data={"actor": ACTOR, "kind": "blocks", "from": ask, "to": tid})
        self.assertEqual(sb.get(tid)["blocked_by"], [ask])
        self.assertFalse(sb.run("item move", data={"actor": ACTOR, "id": ask, "transition": "answer"}).ok)
        sb.move(ask, "answer", set={"answer": "30 days"})
        self.assertEqual(sb.get(ask)["fields"]["answer"], "30 days")
        self.assertEqual(sb.get(tid)["blocked_by"], [])
        self.assertFalse(sb.run("item move", data={"actor": ACTOR, "id": ask, "transition": "answer", "set": {"answer": "second"}}).ok)
        self.assertEqual(sb.create("ask", fields={"question": "Next?"}), "USER-002")
        self.assertFalse((sb.root / ".perry/events.jsonl").exists())

    def test_question_is_required_and_refusal_does_not_consume_id(self):
        sb = ready(self)
        self.assertFalse(sb.run("item create", data={"actor": ACTOR, "type": "ask", "fields": {}}).ok)
        self.assertEqual(sb.create("ask", fields={"question": "Required input"}), "USER-001")

    def test_archived_asked_dates_drive_pending_age_and_answers_leave_count(self):
        p = Project()
        seed_ask(p, needed="recent")
        old = seed_ask(p, needed="old", asked="2020-01-01")
        import inproc
        def queue():
            result = inproc.run("perry-state", ["--root", str(p.root), "--json"])
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)["user_input_queue"]
        q = queue()
        self.assertEqual(q["count"], 2)
        self.assertEqual(q["oldest"]["id"], old["id"])
        self.assertGreater(q["oldest"]["idle_days"], 2000)
        set_ask(p, old["id"], answer="resolved")
        self.assertEqual(queue()["count"], 1)

    def test_frozen_ask_commands_cannot_write_a_parallel_queue(self):
        p = Project()
        before = snapshot(p)
        for args in (("ask", "--needed", "X"), ("answer", "USER-001", "--answer", "yes")):
            code, out = p.run(*args)
            self.assertEqual(code, 1, out)
            self.assertIn("read-only", out["refused"])
            self.assertEqual(snapshot(p), before)


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
        seed_task(p, title='tool written', priority='P0')
        _, d = p.run("list", "--all")
        self.assertTrue(d["conformance"]["has_event_log"])
        self.assertIn("TASK-900",
                      d["conformance"]["rows_with_no_computable_age"])

    def test_a_tool_written_row_has_an_age_and_is_not_flagged(self):
        """The check must run AFTER the event merge. Placed during the board
        walk it flagged rows the tool had just created, because `updated` was
        not filled in yet — measured 9 flagged where 6 was the truth."""
        p = Project()
        a = seed_task(p, title='tool written', priority='P0')
        _, d = p.run("list", "--all")
        t = next(x for x in d["tasks"] if x["id"] == a["id"])
        self.assertIsNotNone(t["updated"])
        self.assertNotIn(a["id"], d["conformance"]["rows_with_no_computable_age"])

    def test_a_row_with_a_stage_clock_is_ageable_without_events(self):
        """`Stage since` and `Arrived` are dates on the row itself, so a
        pipeline or queue row is ageable even with no event log."""
        p = Project(tracks=MODE_TRACKS)
        a = seed_task(p, title='post', track='blog', priority='P0')
        (p.root / ".perry" / "events.jsonl").unlink()
        _, d = p.run("list", "--all")
        self.assertNotIn(a["id"], d["conformance"]["rows_with_no_computable_age"])

    def test_closed_rows_are_not_reported_as_ageless(self):
        """The question is "is this still live", which a closed row answers."""
        p = Project()
        a = seed_task(p, title='X', priority='P0')
        set_task(p, a['id'] , event_name='done', evidence='e.md', verification='V3', status='done')
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
        a = seed_task(p, title='the blocker', priority='P1')
        set_task(p, a['id'] , event_name='done', evidence='e.md', verification='V3', status='done')
        set_task(p, 'TASK-900' , event_name='status', status='blocked', next_action=f"blocked-by {a['id']}")
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
        a = seed_task(p, title='still open', priority='P1')
        set_task(p, 'TASK-900' , event_name='status', status='blocked', next_action=f"blocked-by {a['id']}")
        _, d = p.run("list", "--all")
        self.assertEqual(d["conformance"]["next_action_cites_closed"], [])

    def test_a_closed_row_citing_a_closed_task_is_not_reported(self):
        """The question is what still needs doing."""
        p, _ = self.blocked_by_a_closed_task()
        set_task(p, 'TASK-900' , event_name='done', evidence='e.md', verification='V3', status='done')
        _, d = p.run("list", "--all")
        self.assertEqual(d["conformance"]["next_action_cites_closed"], [])

    def test_an_id_family_this_payload_cannot_resolve_is_not_claimed_on(self):
        """`DESIGN-` and `USER-` ids are all over these cells. Reporting them
        as "not closed" would assert something the payload cannot know."""
        p = self.board_citing("DESIGN-003")
        _, d = p.run("list", "--all")
        self.assertEqual(d["conformance"]["next_action_cites_closed"], [])


class TestCorrectingANativeNextAction(unittest.TestCase):
    def test_correction_and_clear_leave_state_unchanged_and_no_op_has_no_event(self):
        sb = ready(self)
        tid = task(sb, next_action="old plan")
        before = sb.get(tid)
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"next_action": "revised"}, "expect": {tid: before["seq"]}})
        got = sb.get(tid)
        self.assertEqual(got["state"], before["state"])
        self.assertEqual(got["fields"]["next_action"], "revised")
        self.assertEqual({k:v for k,v in got["fields"].items() if k != "next_action"},
                         {k:v for k,v in before["fields"].items() if k != "next_action"})
        event = sb.ok("events")["events"][-1]
        self.assertEqual(event["changes"], [{"key": "field:next_action", "before": "old plan", "after": "revised"}])
        out = sb.run("item update", data={"actor": ACTOR, "id": tid, "set": {"next_action": "revised"}})
        self.assertEqual(out.env["effect"], "unchanged")
        self.assertEqual(sb.get(tid)["seq"], got["seq"])
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"next_action": None}})
        self.assertIsNone(sb.get(tid)["fields"]["next_action"])

    def test_historical_next_event_remains_a_task_event(self):
        self.assertIn("next", PT.TASK_EVENTS)
        self.assertNotIn("next", PT.SECTION_EVENTS)


class TestNativeIntakeRouting(unittest.TestCase):
    def test_routing_updates_one_item_instead_of_minting_a_second_identity(self):
        sb = ready(self)
        tid = task(sb, track="intake")
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"track": "main"}})
        self.assertEqual(sb.get(tid)["fields"]["track"], "main")
        out = sb.run("item update", data={"actor": ACTOR, "id": tid, "set": {"track": "main"}})
        self.assertEqual(out.env["effect"], "unchanged")
        self.assertEqual(sb.ok("query")["total"], 1)
        sb.move(tid, "drop", set={"reason": "duplicate request"})
        self.assertEqual(sb.get(tid)["state"], "dropped")
        self.assertFalse(sb.run("item move", data={"actor": ACTOR, "id": tid, "transition": "start"}).ok)

    def test_legacy_route_resolve_and_sweep_never_rewrite_archived_intake(self):
        p = Project(tracks=MODE_TRACKS)
        seed_intake(p, title="a request")
        before = snapshot(p)
        for args in (("route", "1", "--track", "ops"), ("resolve-intake", "1", "--outcome", "dropped", "--reason", "duplicate"), ("intake-sweep",)):
            code, out = p.run(*args)
            self.assertEqual(code, 1, out)
            self.assertIn("read-only", out["refused"])
            self.assertEqual(snapshot(p), before)


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
        seed_intake(p, title='oldest', arrived='2026-08-01')
        seed_intake(p, title='newer', arrived='2026-08-15')
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
        archived = rows(p, "intake.jsonl")
        archived[0].update(outcome="dropped — no", discharged=True)
        write(p, "intake.jsonl", archived)
        i = p.run("list", "--all")[1]["intake"]
        self.assertEqual(i["undischarged"], 1)
        self.assertEqual(i["oldest_undischarged"], 2)
        self.assertTrue(i["rows"][0]["discharged"])

    def test_sweep_is_frozen_even_when_archived_rows_are_discharged(self):
        p = self.loaded()
        archived = rows(p, "intake.jsonl")
        archived[0].update(outcome="dropped — covered elsewhere", discharged=True)
        write(p, "intake.jsonl", archived)
        before = snapshot(p)
        code, out = p.run("intake-sweep")
        self.assertEqual(code, 1, out)
        self.assertIn("read-only", out["refused"])
        self.assertEqual(snapshot(p), before)

    def test_a_project_with_no_intake_section_reports_an_empty_block(self):
        """Not every project is queue-shaped, and that is not an error."""
        _, d = Project().run("list", "--all")
        self.assertEqual(d["intake"]["rows"], [])
        self.assertEqual(d["intake"]["undischarged"], 0)
        self.assertIsNone(d["intake"]["oldest_undischarged"])


class TestNativeDropAudit(unittest.TestCase):
    def test_drop_records_prior_state_and_reason_without_a_journal_write(self):
        sb = ready(self)
        tid = task(sb)
        sb.move(tid, "start")
        sb.move(tid, "submit")
        sb.move(tid, "drop", set={"reason": "client pulled campaign"})
        event = sb.ok("events")["events"][-1]
        self.assertIn({"key": "state", "before": "review", "after": "dropped"}, event["changes"])
        self.assertEqual(sb.get(tid)["fields"]["reason"], "client pulled campaign")
        self.assertNotIn("stage", sb.get(tid)["fields"])
        self.assertFalse((sb.root / "journal").exists())


if __name__ == "__main__":
    unittest.main()
