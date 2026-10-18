"""TASK-167 — `perry-task purge`, the store's only removal path.

**What made this a row rather than a cleanup.** Three rows titled `t`, added
and dropped inside sixty seconds while somebody smoke-tested `perry-task add`
on 2026-08-18, sat in `perry/tasks.jsonl` reading `status: dropped`. They were
invisible on `BOARD.md` — dropped rows are not rendered — and present in every
`list --json` payload a consumer reads. And there was no way to take them out:
`drop` *sets a status*, which is what put them in that state; there was no
`purge`, no `remove`, no `forget`.

So the deliverable is the mechanism. Everything below is proved on a fixture
project this module builds, never on Perry's own state — a refusal asserted
against the store living around the test is a check that stops meaning
anything the week somebody edits that store.

Run: python3 -m unittest discover -s tests -p test_purge.py
"""

from __future__ import annotations

COVERS = (
    "bin/perry-task",
    "bin/perry-lint",
    "bin/perry-explain",
    "bin/perry-state",
    "schema/events-list-contract.md",
    "schema/task-list-contract.md",
)

import json
import re
import subprocess
import unittest
from kernel_work_support import ACTOR, ready, task
from pathlib import Path

from task_writer_support import PT, Project, PERRY_HOME

TOOL = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"
REASON = "smoke-test row; never work"


class TestNativeTerminalRetention(unittest.TestCase):
    def test_done_and_dropped_records_remain_queryable_and_never_free_their_ids(self):
        sb = ready(self)
        done, dropped = task(sb), task(sb)
        sb.move(done, "done", set={"evidence": "proof.md"})
        sb.move(dropped, "drop", set={"reason": "user removed scope"})
        self.assertEqual(sb.get(done)["state"], "done")
        self.assertEqual(sb.get(dropped)["state"], "dropped")
        self.assertEqual(task(sb), "TASK-003")
        self.assertEqual(sb.ok("query", data={"type": "task"})["total"], 3)
        for command in ("item purge", "item delete", "item remove"):
            seq = sb.seq()
            out = sb.run(command, data={"actor": ACTOR, "id": done})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), seq)
            self.assertEqual(sb.get(done)["state"], "done")

    def test_retired_purge_preserves_open_terminal_unknown_and_referenced_ids(self):
        p = Project()
        p.seed_task("TASK-001", status="dropped")
        p.seed_task("TASK-002", depends_on=["TASK-001"])
        before = {str(f.relative_to(p.root)): f.read_bytes() for f in p.root.rglob("*") if f.is_file()}
        for tid in ("TASK-001", "TASK-002", "TASK-404"):
            for args in ((), ("--reason", "smoke test"), ("--reason", "smoke test", "--dry-run")):
                code, out = p.run("purge", tid, *args)
                self.assertEqual(code, 1, out)
                self.assertIn("read-only", out["refused"])
                self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                                  for f in p.root.rglob("*") if f.is_file()}, before)


class TestArchivedPurgeRead(unittest.TestCase):
    def test_import_does_not_resurrect_an_archived_purged_id(self):
        p = Project()
        p.seed_task("TASK-002", title="terminal record that stays", status="dropped")
        events = []
        for tid in ("TASK-001", "TASK-002"):
            for name, status in (("add", "not_started"), ("drop", "dropped")):
                events.append({"event": name, "id": tid, "title": "historical row", "to": status,
                               "actor": "fixture", "ts": "2026-09-01T00:00:00Z"})
        events.append({"event": "purge", "id": "TASK-001", "title": "historical row",
                       "actor": "fixture", "reason": "historical smoke test", "ts": "2026-09-01T00:00:00Z"})
        (p.root / ".perry/events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
        out = subprocess.run(["python3", str(TASKS), "write", "--from-board", "--root", str(p.root)],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        code, rows = p.run("list", "--all")
        self.assertEqual(code, 0, rows)
        self.assertEqual([r["id"] for r in rows["tasks"]], ["TASK-002"])
        code, out = p.run("events", "--limit", "100")
        self.assertEqual(code, 0, out)
        purges = [e for e in out["events"] if e["event"] == "purge"]
        self.assertEqual(len(purges), 1)
        self.assertEqual(purges[0]["reason"], "historical smoke test")


class TestItIsDeclaredEverywhereItHasToBe(unittest.TestCase):

    def test_it_is_dispatchable_and_classified_as_a_task_event(self):
        self.assertIn("purge", PT.COMMANDS)
        self.assertIn("purge", PT.TASK_ROW_COMMANDS)
        self.assertIn("purge", PT.TASK_EVENTS)
        self.assertNotIn("purge", PT.SECTION_EVENTS)
        self.assertNotIn("purge", PT.READ_ONLY_COMMANDS)

    def test_the_pair_it_carries_is_declared(self):
        self.assertEqual(PT.EVENT_FIELD["purge"], "status")

    def test_the_usage_banner_advertises_it(self):
        """A subcommand a user cannot discover is one they will hand-edit
        around — and hand-editing the store is the thing this row exists
        against."""
        # The usage block is GENERATED from `PT.SURFACE` since DESIGN-016 C2,
        # so being discoverable means being declared — which is also what puts
        # it in `perry list` and `--describe`.
        self.assertIn("purge", {s["name"] for s in PT.SURFACE["subcommands"]})
        out = subprocess.run(["python3", str(TOOL), "--help"],
                             capture_output=True, text=True).stdout
        self.assertRegex(out, r"(?m)^\s+purge\s", "purge is not in the usage")

    def test_the_events_contract_documents_the_kind(self):
        page = (PERRY_HOME / "schema" / "events-list-contract.md").read_text()
        self.assertIn("`purge` · `perry-task purge`", page)

    def test_the_two_names_are_not_confusable(self):
        """TASK-167 decision 1. `drop` records a decision about the WORK and
        leaves the record; `purge` removes the RECORD. Neither name is a
        prefix of the other, so no abbreviation or completion reaches both."""
        self.assertFalse("purge".startswith("drop"))
        self.assertFalse("drop".startswith("purge"))
        self.assertIsNot(PT.COMMANDS["purge"], PT.COMMANDS["drop"])


class TestABlankLineInTheLogIsTolerated(unittest.TestCase):
    """TASK-167's second half, and the whole of it.

    `.perry/events.jsonl` carries a blank line — on Perry's own log, at line 67
    — and the file is APPEND-ONLY, so the row is not "remove the line". It is
    "prove every reader tolerates one, and open a finding if any does not".

    Proved on a log this test writes, so it goes on meaning something after
    somebody rotates or appends to Perry's own. Every reader is exercised
    through its shipped entry point, not by asserting that a `strip()` appears
    in the source.
    """

    def with_blank_lines(self) -> Project:
        p = Project()
        p.seed_task("TASK-001", title="a row before the gap", status="dropped")
        p.seed_task("TASK-002", title="a row after the gap")
        (p.root / ".perry/events.jsonl").write_text("".join(json.dumps({
            "event": name, "id": tid, "title": title, "to": status,
            "ts": "2026-09-01T00:00:00Z", "actor": "fixture"}) + "\n"
            for name, tid, title, status in (("add", "TASK-001", "a row before the gap", "not_started"),
                ("drop", "TASK-001", "a row before the gap", "dropped"),
                ("add", "TASK-002", "a row after the gap", "not_started"))))
        b = {"id": "TASK-002"}
        log = p.root / ".perry" / "events.jsonl"
        lines = log.read_text().split("\n")
        body = [l for l in lines if l.strip()]
        # A blank line at the head, in the middle, at the tail, and two in a
        # row — every position a hand-edit or a lost write can leave one.
        gapped = ([""] + body[:1] + [""] + body[1:2] + ["", ""] + body[2:]
                  + ["", ""])
        log.write_text("\n".join(gapped))
        self.assertGreater(len([l for l in log.read_text().split("\n")
                                if not l.strip()]), 4)
        self.p, self.live = p, b["id"]
        return p

    def test_the_writers_own_reader_skips_it(self):
        p = self.with_blank_lines()
        events = PT.read_events(p.root)
        self.assertTrue(events)
        self.assertIn(self.live, [e.get("id") for e in events])

    def test_list_still_answers(self):
        p = self.with_blank_lines()
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertIn(self.live, [t["id"] for t in out["tasks"]])
        self.assertTrue(out["conformance"]["has_event_log"])

    def test_the_events_feed_still_answers(self):
        p = self.with_blank_lines()
        code, out = p.run("events")
        self.assertEqual(code, 0, out)
        self.assertGreater(out["total"], 0)

    def test_drift_reconciliation_still_answers(self):
        """The reader with its own second parse of the file — `perry-state §
        reconcile_drift` re-reads `events.jsonl` line by line rather than
        going through `read_events`, so it is a distinct tolerance claim."""
        p = self.with_blank_lines()
        # Board-less (TASK-262 round 4a): `drift` over a held `BOARD.md` is
        # about that file, which no write re-renders any more, so it would
        # count the rows these writes made as orphaned. The file is retired.
        (p.root / "BOARD.md").unlink()
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        drift = json.loads(r.stdout)["board"]["drift"]
        self.assertTrue(drift["checked"])
        self.assertEqual(drift["drift"], 0)

    def test_the_linter_still_answers(self):
        p = self.with_blank_lines()
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(p.root)], capture_output=True, text=True)
        self.assertNotIn("Traceback", r.stderr)

    def test_retired_writes_preserve_every_gap_without_normalizing_history(self):
        p = self.with_blank_lines()
        before = {str(f.relative_to(p.root)): f.read_bytes() for f in p.root.rglob("*") if f.is_file()}
        for argv in (("add", "--title", "a new row"), ("start", self.live),
                     ("drop", self.live, "--reason", "probe"),
                     ("purge", "TASK-001", "--reason", REASON)):
            code, out = p.run(*argv)
            self.assertEqual(code, 1, out)
            self.assertIn("read-only", out["refused"])
            self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                              for f in p.root.rglob("*") if f.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
