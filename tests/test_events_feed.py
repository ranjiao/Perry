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

**WHICH END, and why this file now says so out loud (1.1, TASK-168).** Every
text described the tail — this docstring's first line, `schema/events-list-
contract.md` line 1 and § Why this exists, `--help`, and that page's own paging
example — while the code returned the HEAD. Nothing here disagreed with the
code, so the drift lived for three days and was found by a consumer, not by the
suite: the tests below all used logs shorter than the default limit, where head
and tail are the same window, and the one that did page asserted `[0,1,2,3]`
because that is what it saw. `TestTheFirstPageIsTheTail` is the pin that makes
the next drift a failure rather than a document.

**WHICH KINDS, and why the answer is no longer a hand-kept list (TASK-171).**
The same page's `event` key table listed fourteen values; the writer could emit
twenty-five, and `ask`, `answer` and `intake` had been in this project's own log
for days. `TestTheDocumentedKindsAreTheWriters` at the bottom of this file
derives the emittable set from `bin/perry-task` and compares it both ways, so a
kind added to the writer reddens the suite on the commit that adds it. That is
the direction the table rotted in — nobody deleted a row, somebody added a kind.

Run: python3 tests/parallel test_events_feed
"""

from __future__ import annotations

import ast
import importlib.machinery
import importlib.util
import json
import pathlib
import re
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


class TestTheFirstPageIsTheTail(FeedCase):
    """**The direction, pinned. This is the test that was missing.**

    `perry-task events --json --limit 6` on a 733-event log returned `seq`
    0 through 5 — the OLDEST events in the project, five days stale — while
    three texts and a code comment in the contract's own example promised the
    tail. A consumer that trusted the documentation shipped a "recent activity"
    panel of the oldest events it had; the one that found it read 437 KB per
    project to slice the end itself.

    **Every case here uses a log LONGER than the window**, which is the one
    thing the pre-1.1 tests never did: on a log shorter than `--limit` the head
    and the tail are the same rows and the bug is invisible.
    """

    def setUp(self):
        super().setUp()
        self.log(*[self.ev(n, to=f"s{n}") for n in range(30)])

    def test_a_limited_window_is_the_newest_events_not_the_oldest(self):
        got = self.feed("--limit", "6")
        self.assertEqual([e["seq"] for e in got["events"]],
                         [24, 25, 26, 27, 28, 29])
        self.assertEqual([e["to"] for e in got["events"]],
                         ["s24", "s25", "s26", "s27", "s28", "s29"])

    def test_the_default_window_is_the_newest_events_too(self):
        """No `--limit` is the same question with the default of 20, and it is
        the call a "recent activity" panel actually makes."""
        self.assertEqual([e["seq"] for e in self.feed()["events"]],
                         list(range(10, 30)))

    def test_the_window_is_still_ascending_log_order_within_the_page(self):
        """The tail, **not** the log reversed. A consumer rendering newest-first
        reverses it itself; a payload that arrived pre-reversed would break the
        `seq` contiguity every other test here relies on."""
        seqs = [e["seq"] for e in self.feed("--limit", "6")["events"]]
        self.assertEqual(seqs, sorted(seqs))

    def test_the_last_event_of_the_page_is_the_last_line_of_the_log(self):
        self.assertEqual(self.feed("--limit", "3")["events"][-1]["to"], "s29")


class TestPagingDoesNotOverlapOrSkip(FeedCase):
    def setUp(self):
        super().setUp()
        self.log(*[self.ev(n, to=f"s{n}") for n in range(10)])

    def test_two_pages_partition_the_log(self):
        """Since 1.1 the cursor walks BACKWARDS — there is nothing after the
        tail to page to, so older is the only direction left."""
        a = self.feed("--limit", "4")
        b = self.feed("--limit", "4", "--since", a["cursor"])
        first = [e["seq"] for e in a["events"]]
        second = [e["seq"] for e in b["events"]]
        self.assertEqual(first, [6, 7, 8, 9])
        self.assertEqual(second, [2, 3, 4, 5])
        self.assertEqual(set(first) & set(second), set())

    def test_paging_the_whole_log_yields_every_event_exactly_once(self):
        """**The check that catches a bad tail-first flip.** Skipping or
        repeating one event at a window boundary is the obvious way to get this
        wrong, and it survives a spot check of two pages: the boundary is only
        wrong by one."""
        seen, cursor, pages = [], None, 0
        while True:
            pages += 1
            self.assertLess(pages, 20, "paging did not terminate")
            page = self.feed(*(["--limit", "3"]
                               + (["--since", cursor] if cursor else [])))
            seen = [e["seq"] for e in page["events"]] + seen
            if not page["more"]:
                break
            cursor = page["cursor"]
        self.assertEqual(seen, list(range(10)),
                         "the pages are not the log, in order, exactly once")

    def test_the_cursor_is_the_oldest_event_in_the_window(self):
        """It is the boundary the NEXT page ends at, so it must name the end
        the next page grows from — the oldest row here, not the newest."""
        page = self.feed("--limit", "4")
        self.assertEqual(page["cursor"].split(":", 1)[0],
                         str(page["events"][0]["seq"]))

    def test_more_is_false_at_the_end(self):
        last = self.feed("--limit", "10")
        self.assertFalse(last["more"])
        self.assertEqual(self.feed("--limit", "10",
                                   "--since", last["cursor"])["count"], 0)

    def test_more_is_true_while_older_events_remain(self):
        self.assertTrue(self.feed("--limit", "4")["more"])

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

    def test_it_restarts_at_the_newest_window_not_at_the_head(self):
        """Since 1.1, "restart" means *where a feed with no cursor starts* —
        the tail. Restarting at the head would answer a rotation by handing the
        consumer the oldest events in the project labelled as a fresh page,
        which is the exact defect 1.1 removed. The log here is longer than the
        window, which is what makes the two answers different."""
        self.log(*[self.ev(n, to=f"s{n}") for n in range(30)])
        cursor = self.feed("--limit", "4")["cursor"]
        self.log(*[self.ev(n, to=f"s{n}") for n in range(60, 90)])
        out = self.feed("--limit", "4", "--since", cursor)
        self.assertTrue(out["rotated"])
        self.assertEqual([e["seq"] for e in out["events"]], [26, 27, 28, 29])

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


class TestTheFlipWasAnnouncedNotSilent(FeedCase):
    """**Same key, same type, different rows.** `1.x` only adds keys and that
    rule is unbroken — which is exactly why it does not cover this change, and
    why the minor had to move and `semantics` had to carry an entry. A silent
    flip is the failure mode a consumer cannot detect at all.
    """

    def setUp(self):
        super().setUp()
        self.log(*[self.ev(n) for n in range(3)])

    def test_the_minor_moved(self):
        self.assertEqual(self.feed()["contract"], "perry-events/list/1.1")

    def test_the_payload_carries_a_semantics_array(self):
        self.assertIsInstance(self.feed().get("semantics"), list)

    def test_the_current_minor_has_an_entry_naming_the_fields_that_moved(self):
        entry = next((s for s in self.feed()["semantics"]
                      if s["version"] == "1.1"), None)
        self.assertIsNotNone(entry, "1.1 changed a meaning and must say so")
        self.assertEqual(set(entry["fields"]), {"events", "cursor", "more"})
        self.assertTrue(entry["note"].strip(), "the note is what gets shown")

    def test_semantics_is_ordered_oldest_minor_first(self):
        """It is read as "everything newer than the minor I tested against",
        which is a slice only while it is sorted. `perry-task/list` shipped
        1.5, 1.9, 1.7 once."""
        got = [s["version"] for s in self.feed()["semantics"]]
        self.assertEqual(got, sorted(
            got, key=lambda v: tuple(int(x) for x in v.split("."))))

    def test_the_contract_document_states_the_same_version(self):
        page = (ROOT / "schema" / "events-list-contract.md").read_text()
        self.assertIn("perry-events/list/1.1", page.splitlines()[0])


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


# ── the documented kinds vs the kinds the writer can emit ─────────────────────
#
# **The table this pins went stale by eleven names.** `schema/events-list-
# contract.md` listed fourteen values of `event`; `bin/perry-task` could emit
# twenty-five, and three of the missing eleven (`ask`, `answer`, `intake`) were
# already in this project's own log when the gap was found — by a reader, not by
# the suite. Re-writing the list by hand would have fixed 2026-08-21 and nothing
# after it, because a hand-kept list is exactly what drifted.
#
# So the set is DERIVED FROM THE WRITER, from two sources unioned:
#
#   1. `TASK_EVENTS | SECTION_EVENTS` — the registers `bin/perry-task` keeps as
#      a partition of its own writing subcommands, checked to BE that partition
#      by `tests/test_cadence.py`. A new subcommand that emits an event cannot
#      reach `COMMANDS` without landing in one of these two.
#   2. Every `"event": "<literal>"` written at a commit site, read out of the
#      source's AST, plus the event-name argument of every `cell_writer(...)`
#      call — the helper four subcommands (`next`, `retitle`, `rung`,
#      `evidence`) get their whole write path from, where no literal appears in
#      a dict at all.
#
# Neither source alone is enough, and that is the point of taking both. Source 1
# misses a kind written at a raw commit site by something that is not a
# subcommand; source 2 misses a kind whose write path is a helper this file has
# not been taught about. A new kind has to evade BOTH to reach the log
# undocumented, and the direction that matters is the one that let this table
# rot: ADDING a kind and not documenting it.

CONTRACT = ROOT / "schema" / "events-list-contract.md"

#: A row of § The event kinds. The first cell is the kind AND the subcommand
#: that writes it, `` `add` · `perry-task add` ``, for two reasons: naming the
#: writer is half of what makes the row checkable, and a first cell of nothing
#: but backticked identifiers is how `tests/contract_key_parity.py § key_tables`
#: recognises a KEY table. Twenty-five event names read as payload keys would be
#: twenty-five documented paths the payload does not carry.
KIND_ROW = re.compile(
    r"^\|\s*`([a-z][a-z-]*)`\s*·\s*`perry-task ([a-z][a-z-]*)`\s*\|")

#: The two subheadings § The event kinds hangs its tables under. Named so the
#: parity guard below can ask about those tables and no others — the page's
#: `An event` table declares `rung`, `evidence` and `track`, which really are
#: payload keys and really should be read as such.
KIND_TABLE_HEADINGS = ("The kinds that describe a task row",
                       "The kinds that describe something else")


def documented_kinds() -> dict[str, str]:
    """`{kind: subcommand}`, from § The event kinds, fences excluded."""
    out, fenced = {}, False
    for line in CONTRACT.read_text().splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = KIND_ROW.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def written_literals() -> set[str]:
    """Every event name spelled at a write site in `bin/perry-task`."""
    tree = ast.parse(TOOL.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        # `{"ts": ..., "event": "done", ...}` — the shape every commit site has.
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (isinstance(key, ast.Constant) and key.value == "event"
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, str)):
                    found.add(value.value)
        # `cell_writer(field, flag, event, why, ...)` — third positional, or the
        # keyword. Four subcommands write through it and spell no dict here.
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "cell_writer"):
            if len(node.args) > 2 and isinstance(node.args[2], ast.Constant):
                found.add(node.args[2].value)
            for kw in node.keywords:
                if kw.arg == "event" and isinstance(kw.value, ast.Constant):
                    found.add(kw.value.value)
    return found


def emittable_kinds(mod) -> set[str]:
    return set(mod.TASK_EVENTS) | set(mod.SECTION_EVENTS) | written_literals()


class TestTheDocumentedKindsAreTheWriters(unittest.TestCase):
    """§ The event kinds equals what `bin/perry-task` can put in the log."""

    @classmethod
    def setUpClass(cls):
        loader = importlib.machinery.SourceFileLoader("perry_task_kinds",
                                                      str(TOOL))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        cls.mod = importlib.util.module_from_spec(spec)
        loader.exec_module(cls.mod)

    def test_the_document_lists_every_kind_the_writer_can_emit(self):
        """The direction that let the table rot: a NEW kind, undocumented.

        Verified by adding a kind to `bin/perry-task` — both as a bare
        `"event": "..."` at a commit site and as a name in `SECTION_EVENTS` —
        and confirming this goes red before the document is touched.
        """
        missing = emittable_kinds(self.mod) - set(documented_kinds())
        self.assertEqual(
            missing, set(),
            f"`bin/perry-task` can emit {sorted(missing)} and "
            f"`schema/events-list-contract.md § The event kinds` does not list "
            f"them. A consumer branching on `event` has no way to learn they "
            f"exist. Add a row; do not delete the kind to make this pass")

    def test_the_document_lists_no_kind_the_writer_cannot_emit(self):
        extra = set(documented_kinds()) - emittable_kinds(self.mod)
        self.assertEqual(
            extra, set(),
            f"documented event kinds {sorted(extra)} that no write site and "
            f"neither register can produce — a promise about something that "
            f"cannot happen")

    def test_every_documented_kind_names_a_real_subcommand(self):
        """The second cell half of the row. A kind whose writer is misspelled
        is a row a reader cannot act on, and the misspelling is invisible to
        the set comparison above."""
        unknown = {kind: sub for kind, sub in documented_kinds().items()
                   if sub not in self.mod.COMMANDS}
        self.assertEqual(unknown, {},
                         "documented as written by a subcommand that does not "
                         "exist")

    def test_the_task_field_is_documented_as_sometimes_not_a_task(self):
        """`intake` and its three siblings write an EMPTY `task`: they are
        written against a section, not against a row. A consumer that groups
        this feed by `task` and drops the empty key loses them silently, so the
        page has to say so rather than leave `task` reading "the id this event
        is about"."""
        text = CONTRACT.read_text()
        self.assertIn("not always a `TASK-` id", text)
        for kind in ("intake", "resolve-intake", "intake-sweep",
                     "risk-migrate"):
            self.assertIn(kind, text)

    def test_the_kind_tables_are_not_read_as_key_tables(self):
        """The pin on the shape of the rows above.

        `tests/contract_key_parity.py` treats a table row whose first cell is
        nothing but backticked identifiers as a declaration of payload KEYS.
        Reformatting these rows to a bare `` `add` `` first cell would hand
        that check twenty-five event names as documented paths this payload
        does not emit — KR-O2.4 would move for a reason that has nothing to do
        with the payload. Kept honest here rather than discovered there.
        """
        text = CONTRACT.read_text()
        for heading in KIND_TABLE_HEADINGS:
            self.assertIn(f"### {heading}", text,
                          "the guard below is anchored on this heading")
        sys.path.insert(0, str(ROOT / "tests"))
        import contract_key_parity as parity   # noqa: PLC0415
        leaked = {k for heading, keys in parity.key_tables(text)
                  if heading in KIND_TABLE_HEADINGS for k in keys}
        self.assertEqual(
            leaked, set(),
            f"§ The event kinds is being read as a key table: {sorted(leaked)}")

if __name__ == "__main__":
    unittest.main()
