"""`perry-task events` — the log's tail, in log order, with a cursor.

aiMark asked for a project-level feed and proposed `--limit`/`--since` on
`list`. That was rejected on a measurement, not a preference: **three fields in
`perry-task/list` are defined relative to the payload** — `blocks`,
`depends_on_unknown` and `next_action_cites_closed` — so paging `list` silently
changes what they mean per page.

The other half is order. `ts` has seconds precision and ties are real, and
`perry-task/list` promises array order only *within one id*. A flattened
cross-task stream therefore has no authoritative order unless the log's own
order is the answer.

Run: python3 tests/parallel test_events_feed
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-task"

BOARD = """# Board

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | first | Claude | not_started | — | — | V2 |
| TASK-002 | second | Claude | not_started | — | — | V2 |
"""


class FeedCase(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "perry").mkdir()
        (self.dir / ".perry").mkdir()
        (self.dir / ".perry" / "config.md").write_text("State root: perry\n")
        (self.dir / "perry" / "BOARD.md").write_text(BOARD)

    def log(self, *events):
        (self.dir / ".perry" / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n")

    def feed(self, *args):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "events", *args,
             "--root", str(self.dir), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        return json.loads(proc.stdout)

    def ev(self, n, **kw):
        base = {"ts": f"2026-08-18T10:00:{n:02d}", "event": "status",
                "id": "TASK-001", "from": "a", "to": "b"}
        base.update(kw)
        return base


class TestOrderIsLogOrder(FeedCase):
    def test_ties_are_preserved_in_the_order_written(self):
        """**Two events one second apart is not the hard case — two in the SAME
        second is.** `ts` cannot order them, so the log must."""
        self.log(self.ev(0, id="TASK-001", to="first"),
                 self.ev(0, id="TASK-002", to="second"),
                 self.ev(0, id="TASK-001", to="third"))
        got = [e["to"] for e in self.feed()["events"]]
        self.assertEqual(got, ["first", "second", "third"])

    def test_seq_is_the_position_in_the_log(self):
        self.log(*[self.ev(n) for n in range(5)])
        self.assertEqual([e["seq"] for e in self.feed()["events"]],
                         [0, 1, 2, 3, 4])


class TestPagingDoesNotOverlapOrSkip(FeedCase):
    def setUp(self):
        super().setUp()
        self.log(*[self.ev(n, to=f"s{n}") for n in range(10)])

    def test_two_pages_partition_the_log(self):
        a = self.feed("--limit", "4")
        b = self.feed("--limit", "4", "--since", a["cursor"])
        first = [e["seq"] for e in a["events"]]
        second = [e["seq"] for e in b["events"]]
        self.assertEqual(first, [0, 1, 2, 3])
        self.assertEqual(second, [4, 5, 6, 7])
        self.assertEqual(set(first) & set(second), set())

    def test_more_is_false_at_the_end(self):
        last = self.feed("--limit", "10")
        self.assertFalse(last["more"])
        self.assertEqual(self.feed("--limit", "10",
                                   "--since", last["cursor"])["count"], 0)

    def test_a_bad_limit_is_refused_not_guessed(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "events", "--limit", "zero",
             "--root", str(self.dir)], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 1)


class TestRotationIsDetectedNotHidden(FeedCase):
    """**The flag exists before rotation does, on purpose.**

    Log rotation is TASK-070's territory and is not built. A consumer written
    against a feed that cannot yet rotate should not need changing on the day
    it can — and a feed that silently restarted after rotation would look like
    a burst of new activity, which is the failure this prevents.
    """

    def test_a_cursor_whose_event_is_gone_reports_rotated(self):
        self.log(*[self.ev(n) for n in range(5)])
        cursor = self.feed("--limit", "2")["cursor"]
        self.log(*[self.ev(n) for n in range(90, 95)])   # rotated beneath it
        out = self.feed("--since", cursor)
        self.assertTrue(out["rotated"])
        self.assertEqual(out["events"][0]["seq"], 0, "it must restart, not skip")

    def test_an_unrotated_cursor_does_not_claim_rotation(self):
        self.log(*[self.ev(n) for n in range(5)])
        out = self.feed("--since", self.feed("--limit", "2")["cursor"])
        self.assertFalse(out["rotated"])


class TestTheFieldsThatWereInvisible(FeedCase):
    def test_reason_is_exposed(self):
        """Populated on 16 events in Perry's own log and readable through no
        contract surface until this one."""
        self.log(self.ev(0, event="drop", reason="superseded by ADR-006"))
        self.assertEqual(self.feed()["events"][0]["reason"],
                         "superseded by ADR-006")

    def test_the_title_is_the_one_written_at_the_time(self):
        """**The title trap.** A retitled task's earlier events still carry the
        old name — correct for a history view, wrong the moment a front-end
        renders it as the row's current name. The key says which it is."""
        self.log(self.ev(0, title="the old name"),
                 self.ev(1, event="retitle", title="the new name"))
        got = [e["title_then"] for e in self.feed()["events"]]
        self.assertEqual(got, ["the old name", "the new name"])

    def test_owner_and_role_ride_along_when_present(self):
        self.log(self.ev(0, event="done", owner="Claude", role="coding"))
        e = self.feed()["events"][0]
        self.assertEqual((e["owner"], e["role"]), ("Claude", "coding"))


class TestItIsReadOnly(FeedCase):
    def test_it_writes_nothing(self):
        self.log(*[self.ev(n) for n in range(3)])
        before = {p: p.read_bytes()
                  for p in self.dir.rglob("*") if p.is_file()}
        self.feed("--limit", "2")
        after = {p: p.read_bytes()
                 for p in self.dir.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_an_empty_log_is_an_empty_feed_not_an_error(self):
        self.assertEqual(self.feed()["count"], 0)
        self.assertEqual(self.feed()["total"], 0)


if __name__ == "__main__":
    unittest.main()
