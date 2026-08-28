"""TASK-142 — the checks for a row that a process bug stranded.

The claim under test: **`conformance` names the rows nothing is moving, and
says what each finding might mean rather than only what it matched.**

Three predicates, each traced to an incident on Perry's own board:

| check | the incident |
|---|---|
| `blocked_by_closed_rows` | TASK-037 and TASK-045 sat `blocked` with every dependency closed. `blocked_without_dependency` tests `not depends_on` — the list being **empty** — and these had a non-empty list whose every entry had closed. **One predicate away**, which is why nothing named them. |
| `in_progress_with_no_live_run` | two agents starved at the 600s watchdog on 2026-08-20; their rows stayed `in_progress` with no dispatch slot and no new event |
| `review_idle` | TASK-100/111/127/133 sat in `review` after their PRs merged, and nothing noticed |

**Item 1 is two-sided on one fixture, and that is the whole design of this
file.** Asserting `blocked_by_closed_rows == ["TASK-002", "TASK-004"]` alone
would pass against an implementation that simply renamed the check next to it.
Every test that names the new array reads `blocked_without_dependency` out of
the same payload in the same assertion, so the two must disagree about the same
rows for the file to be green.

**`blocked_stale` is read, not recomputed.** The rule lives in
`bin/lib § resolve_startability` under an AST guard that counts homes by
enclosing function (`tests/one_startable_rule.py`, TASK-148). This suite proves
the aggregate follows the field rather than restating it: it monkeypatches the
one implementation and watches the conformance array move with it. A second
statement of the predicate would keep answering the old way and this goes red.

**Ageing the clock.** Two of the three checks are "idle ≥ N", so a fixture has
to be older than the threshold. Rows are built through the store's own writer,
exactly as `tests/test_stale_blocked.py` insists; the only thing rewritten
afterwards is `.perry/events.jsonl`, which the contract itself calls disposable
history. Waiting four hours is not a test.

**`$HOME` is the dispatch cache.** `bin/perry-dispatch-limit` keys its markers
on `$HOME/.cache/perry/in-flight/`, so every run here points `$HOME` at a temp
directory — otherwise the developer's own in-flight dispatches decide whether
this suite passes, and `tests/test_host_support.py` already had to reach the
same judgement.

Run: python3 tests/parallel test_stranded_rows
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from test_task_writer import PT, PERRY_HOME, TOOL, Project

SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
IN_PROGRESS_HOURS = SCHEMA["thresholds"]["in_progress_idle_hours"]["value"]
REVIEW_DAYS = SCHEMA["thresholds"]["review_idle_days"]["value"]


def _one_int(pattern: str, path: Path) -> int:
    """The single integer `pattern` captures in `path`, or a failed test.

    Read rather than restated: TASK-160 moved the marker TTL and found the
    number written out in four places, one of which was an assertion that
    therefore could not notice.
    """
    found = re.findall(pattern, path.read_text(), re.M)
    assert len(found) == 1, f"{pattern} matched {len(found)}x in {path.name}"
    return int(found[0])


LIMITER = PERRY_HOME / "bin" / "perry-dispatch-limit"
LIMITER_TTL_DEFAULT = _one_int(
    r"STALE_TTL=\"\$\{PERRY_DISPATCH_STALE_TTL:-(\d+)\}\"", LIMITER)
LONGEST_MEASURED_CYCLE = _one_int(
    r"^LONGEST_MEASURED_CYCLE=(\d+)", LIMITER)


class Sandbox:
    """A project whose dispatch cache and clock this suite controls.

    `Project` runs the tool with the inherited environment, which is right for
    every other suite and wrong for this one: `$HOME` selects the in-flight
    marker directory, and a developer with a real dispatch running would flip
    `in_progress_with_no_live_run` from under the assertions.
    """

    def __init__(self):
        self.project = Project()
        self.home = tempfile.TemporaryDirectory()
        self.markers = Path(self.home.name) / ".cache" / "perry" / "in-flight"
        self.markers.mkdir(parents=True)

    @property
    def root(self) -> Path:
        return self.project.root

    def write(self, *argv) -> tuple[int, dict | str]:
        """A write through the store's own writer, with the real environment.

        Writes stamp events with `datetime.now()`, and nothing here wants to
        interfere with that — `age()` moves the clock afterwards, in one place.
        """
        return self.project.run(*argv)

    def list(self, *argv) -> dict:
        """`list --all`, with `$HOME` pointed at this sandbox's marker cache."""
        env = dict(os.environ)
        env["HOME"] = self.home.name
        result = subprocess.run(
            ["python3", str(TOOL), "list", "--all", *argv,
             "--root", str(self.root), "--json"],
            capture_output=True, text=True, env=env)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    def conformance(self, *argv) -> dict:
        return self.list(*argv)["conformance"]

    def dispatch_marker(self, task_id: str, executor: str = "claude-subagent"):
        """The file `perry-dispatch-limit register` writes, byte for byte.

        Its `task_id` field is what the reader prefers; the filename is the
        fallback for a marker an older script wrote, and both spellings are
        exercised because both are live on real machines.
        """
        path = self.markers / f"{task_id}-{executor}.json"
        path.write_text(json.dumps({"task_id": task_id, "executor": executor}))
        return path

    def age(self, hours: float) -> None:
        """Move every event in the log `hours` into the past.

        The board and the store are untouched: this ages HISTORY, which the
        contract calls disposable, and every idle number in the payload is
        computed from it. A test that instead hand-wrote a `status` cell would
        be measuring drift rather than the check.
        """
        log = self.root / ".perry" / "events.jsonl"
        shifted = []
        for line in log.read_text().split("\n"):
            if not line.strip():
                continue
            event = json.loads(line)
            stamp = datetime.fromisoformat(event["ts"]) - timedelta(hours=hours)
            event["ts"] = stamp.isoformat(timespec="seconds")
            shifted.append(json.dumps(event))
        log.write_text("\n".join(shifted) + "\n")

    def __del__(self):
        self.home.cleanup()


def stranded_board() -> Sandbox:
    """TASK-037's and TASK-045's shapes, rebuilt by the writer, plus controls.

    - `TASK-002` and `TASK-004` reproduce the stranded shape: `blocked`, one
      declared dependency, that dependency closed through the ordinary `done`
      path. Two of them, because the incident was two rows and an array is a
      weaker claim when it holds one element.
    - `TASK-006` is blocked on `TASK-005`, which is **still open** — V3 item 2,
      the live TASK-050-on-TASK-094 shape. It must not be named.
    - `TASK-007` is `blocked` and declares NOTHING. It is
      `blocked_without_dependency`'s row and must stay only that.

    Nothing here touches the stranded rows directly. The state is a side effect
    of closing something else, which is the half of the incident that makes it
    reachable through the ordinary path.
    """
    box = Sandbox()
    titles = ("closed blocker one", "stranded dependent one",
              "closed blocker two", "stranded dependent two",
              "open blocker", "genuinely blocked dependent",
              "blocked on prose nothing can read")
    for title in titles:
        code, out = box.write("add", "--title", title, "--priority", "P1")
        assert code == 0, out
    for dependent, blocker in (("TASK-002", "TASK-001"),
                               ("TASK-004", "TASK-003"),
                               ("TASK-006", "TASK-005")):
        code, out = box.write("status", dependent, "--status", "blocked",
                              "--on", blocker)
        assert code == 0, out
    code, out = box.write("status", "TASK-007", "--status", "blocked",
                          "--reason", "waiting on a vendor, no row for it")
    assert code == 0, out
    for blocker in ("TASK-001", "TASK-003"):
        code, out = box.write("done", blocker, "--evidence", "tests/run")
        assert code == 0, out
    return box


class TestTheNewPredicateIsNotTheOldOne(unittest.TestCase):
    """V3 item 1 and item 2, both sides, out of one payload.

    Every assertion here reads `blocked_by_closed_rows` and
    `blocked_without_dependency` together. The distinction between them IS the
    row: the old check tests an EMPTY `depends_on`, and the stranded rows had a
    non-empty one whose every entry had closed.
    """

    @classmethod
    def setUpClass(cls):
        cls.box = stranded_board()
        cls.conf = cls.box.conformance()

    def test_it_names_exactly_the_two_restored_shapes(self):
        self.assertEqual(
            ["TASK-002", "TASK-004"], self.conf["blocked_by_closed_rows"],
            "the two rows whose every declared dependency has closed — "
            "TASK-037's and TASK-045's shapes — must be named and nothing else")

    def test_and_the_old_check_still_names_none_of_them(self):
        """The other side of item 1, and the one that makes it a distinction.
        `blocked_without_dependency` is about an EMPTY list; these rows have a
        non-empty one. If the two arrays ever overlap, one of them is wrong."""
        old = self.conf["blocked_without_dependency"]
        self.assertNotIn("TASK-002", old)
        self.assertNotIn("TASK-004", old)
        self.assertEqual(
            ["TASK-007"], old,
            "the only row whose blocker is prose Perry cannot read is the one "
            "that declared no dependency at all")

    def test_the_two_arrays_are_disjoint(self):
        """Stated as the property rather than as the two rows, because the
        property is what a future board has to keep."""
        self.assertEqual(
            set(), set(self.conf["blocked_by_closed_rows"])
            & set(self.conf["blocked_without_dependency"]),
            "a row cannot both declare no dependency and declare dependencies "
            "that have all closed")

    def test_a_row_blocked_on_an_open_dependency_is_not_named(self):
        """V3 item 2 — the live TASK-050-on-TASK-094 shape. This is what stops
        the check from being 'report every blocked row'."""
        self.assertNotIn("TASK-006", self.conf["blocked_by_closed_rows"])
        rows = {t["id"]: t for t in self.box.list()["tasks"]}
        self.assertEqual(["TASK-005"], rows["TASK-006"]["blocked_by"],
                         "its blocker really is open")

    def test_a_row_that_declares_no_dependency_is_not_named(self):
        self.assertNotIn("TASK-007", self.conf["blocked_by_closed_rows"])

    def test_a_closed_row_is_never_named(self):
        for tid in ("TASK-001", "TASK-003"):
            self.assertNotIn(tid, self.conf["blocked_by_closed_rows"])


class TestTheAggregateReadsTheFieldRatherThanRestatingIt(unittest.TestCase):
    """V3 item 5. The rule has one home; this proves the array uses it.

    `bin/lib § resolve_startability` states the predicate exactly once, under
    an AST guard that counts homes by enclosing FUNCTION and fails on a second
    one (TASK-148 — two copies once lived in a single file, and a per-file
    count called that one home). `blocked_by_closed_rows` is the aggregate of
    the `blocked_stale` field that function writes.
    """

    def test_the_array_is_exactly_the_rows_carrying_the_field(self):
        payload = stranded_board().list()
        self.assertEqual(
            sorted(t["id"] for t in payload["tasks"] if t["blocked_stale"]),
            payload["conformance"]["blocked_by_closed_rows"],
            "the array must be the aggregate of `tasks[].blocked_stale`, not "
            "a second computation that happens to agree today")

    def test_changing_the_rule_in_bin_lib_moves_the_check(self):
        """The direct proof, and the one a renamed-but-recopied predicate
        fails. The rule's one home is replaced in-process with one that names
        NOTHING; a check that read the field follows it to empty, and a check
        that restated the predicate keeps answering the old way."""
        payload = stranded_board().list()
        tasks = {t["id"]: t for t in payload["tasks"]}
        self.assertEqual(["TASK-002", "TASK-004"],
                         PT.stranded_row_findings(
                             tasks, has_event_log=True, thresholds={},
                             live=set(), now=datetime.now()
                         )["blocked_by_closed_rows"])

        original = PT.lib.resolve_startability
        try:
            def nothing_is_ever_stale(rows) -> None:
                for row in rows:
                    row["blocked_stale"] = False
                    row["startable"] = bool(row["open"] and not row["blocked_by"])
            PT.lib.resolve_startability = nothing_is_ever_stale
            PT.lib.resolve_startability(tasks.values())
            self.assertEqual(
                [], PT.stranded_row_findings(
                    tasks, has_event_log=True, thresholds={}, live=set(),
                    now=datetime.now())["blocked_by_closed_rows"],
                "the aggregate did not follow the rule it claims to read — it "
                "is restating the predicate somewhere of its own")
        finally:
            PT.lib.resolve_startability = original

    def test_the_guard_that_forbids_a_second_statement_is_still_green(self):
        """Imported rather than described: if this row had recomputed the
        predicate it would have had to disable this, and disabling it is the
        visible half of the mistake."""
        import one_startable_rule as guard
        result = guard.measure()
        self.assertTrue(guard.ok(result), guard.report(result))


class TestTheStarvedAgent(unittest.TestCase):
    """V3 item 3, from a fixture and in both directions.

    Two agents starved at the 600s watchdog on 2026-08-20 and their rows stayed
    `in_progress` with no dispatch slot and no new event. Neither signal alone
    is a finding, so both directions are built on one board: a row with no
    marker and an old clock, and a row with a marker and the same old clock.
    """

    @classmethod
    def setUpClass(cls):
        cls.box = Sandbox()
        for title in ("the run that died", "the run that is still going",
                      "the row nobody started"):
            code, out = cls.box.write("add", "--title", title, "--priority", "P1")
            assert code == 0, out
        for tid in ("TASK-001", "TASK-002"):
            code, out = cls.box.write("status", tid, "--status", "in_progress")
            assert code == 0, out
        cls.box.age(IN_PROGRESS_HOURS + 1)
        # TASK-002 is the control: same status, same stale clock, but an
        # executor still holds its slot.
        cls.box.dispatch_marker("TASK-002")

    def test_the_row_with_no_slot_and_a_stale_clock_is_named(self):
        found = self.box.conformance()["in_progress_with_no_live_run"]
        self.assertEqual(["TASK-001"], [row["id"] for row in found])
        self.assertEqual("in_progress", found[0]["status"])
        self.assertGreaterEqual(found[0]["idle_hours"], IN_PROGRESS_HOURS)
        self.assertEqual(IN_PROGRESS_HOURS, found[0]["threshold_hours"])

    def test_a_row_whose_dispatch_slot_is_still_held_is_not_named(self):
        """The half a clock alone cannot see. Without this the check would
        name every long-running dispatch and be turned off within a week."""
        found = self.box.conformance()["in_progress_with_no_live_run"]
        self.assertNotIn("TASK-002", [row["id"] for row in found])

    def test_a_row_that_is_not_in_progress_is_not_named(self):
        found = self.box.conformance()["in_progress_with_no_live_run"]
        self.assertNotIn("TASK-003", [row["id"] for row in found])

    def test_a_marker_past_its_ttl_is_not_a_live_run(self):
        """`perry-dispatch-limit` deletes a marker older than
        `PERRY_DISPATCH_STALE_TTL` — a crashed session's leftover, not
        evidence. The reader applies the same TTL rather than a second one, and
        must not resurrect the slot it is about to clean."""
        box = Sandbox()
        code, out = box.write("add", "--title", "a crashed run", "--priority", "P1")
        self.assertEqual(code, 0, out)
        code, out = box.write("status", "TASK-001", "--status", "in_progress")
        self.assertEqual(code, 0, out)
        box.age(IN_PROGRESS_HOURS + 1)
        marker = box.dispatch_marker("TASK-001")
        stale = datetime.now().timestamp() - 7200
        os.utime(marker, (stale, stale))
        env_ttl = os.environ.get("PERRY_DISPATCH_STALE_TTL")
        os.environ["PERRY_DISPATCH_STALE_TTL"] = "3600"
        try:
            found = box.conformance()["in_progress_with_no_live_run"]
        finally:
            if env_ttl is None:
                os.environ.pop("PERRY_DISPATCH_STALE_TTL", None)
            else:
                os.environ["PERRY_DISPATCH_STALE_TTL"] = env_ttl
        self.assertEqual(["TASK-001"], [row["id"] for row in found],
                         "a marker the writer would delete is not a live run")

    def test_the_filename_spelling_of_a_marker_is_read_too(self):
        """A marker written by a script that did not carry `task_id` in its
        JSON. Both spellings are live on real machines and neither may be the
        one the reader can see."""
        box = Sandbox()
        code, out = box.write("add", "--title", "an older marker", "--priority", "P1")
        self.assertEqual(code, 0, out)
        code, out = box.write("status", "TASK-001", "--status", "in_progress")
        self.assertEqual(code, 0, out)
        box.age(IN_PROGRESS_HOURS + 1)
        (box.markers / "TASK-001-codex.json").write_text("{}")
        self.assertEqual(
            [], box.conformance()["in_progress_with_no_live_run"])

    def test_the_finding_says_what_it_might_mean(self):
        found = self.box.conformance()["in_progress_with_no_live_run"]
        self.assertTrue(found, "nothing was named, so nothing said anything")
        row = found[0]
        self.assertIn("means", row)
        self.assertIn("dispatch slot", row["means"])
        self.assertIn("re-dispatching", row["means"],
                      "the reader has to be told the one thing that is unsafe "
                      "to do on reading this")


class TestTheReviewRowNobodyIsWaitingFor(unittest.TestCase):
    """TASK-100/111/127/133 sat in `review` after their PRs merged.

    `review` waits on a human and no dependency edge can contradict it, which
    is exactly why no other check in this payload can ever see such a row.
    """

    @classmethod
    def setUpClass(cls):
        cls.box = Sandbox()
        for title in ("merged and never closed", "asked for a verdict today"):
            code, out = cls.box.write("add", "--title", title, "--priority", "P1")
            assert code == 0, out
        code, out = cls.box.write("status", "TASK-001", "--status", "review")
        assert code == 0, out
        cls.box.age(REVIEW_DAYS * 24 + 1)
        # Moved AFTER the clock shift, so this row's own event is fresh while
        # TASK-001's is old — one board, both directions.
        code, out = cls.box.write("status", "TASK-002", "--status", "review")
        assert code == 0, out

    def test_the_idle_review_row_is_named(self):
        found = self.box.conformance()["review_idle"]
        self.assertEqual(["TASK-001"], [row["id"] for row in found])
        self.assertEqual("review", found[0]["status"])
        self.assertGreaterEqual(found[0]["idle_hours"], REVIEW_DAYS * 24)
        self.assertEqual(REVIEW_DAYS * 24, found[0]["threshold_hours"])

    def test_a_review_row_touched_today_is_not_named(self):
        found = self.box.conformance()["review_idle"]
        self.assertNotIn("TASK-002", [row["id"] for row in found])

    def test_it_does_not_leak_into_the_in_progress_check(self):
        """Three names for one check would be the finding V3 item 4 asks about.
        A `review` row is stale in one array and absent from the other."""
        conf = self.box.conformance()
        self.assertEqual([], conf["in_progress_with_no_live_run"])
        self.assertEqual([], conf["blocked_by_closed_rows"])

    def test_the_finding_says_what_it_might_mean(self):
        """And says it in DAYS. The payload carries one clock unit for both
        idle checks so a consumer needs one code path; the unit a person reads
        is the sentence's job."""
        found = self.box.conformance()["review_idle"]
        self.assertTrue(found, "nothing was named, so nothing said anything")
        row = found[0]
        self.assertIn("waiting on a human", row["means"])
        self.assertIn("was not closed", row["means"])
        self.assertIn("days", row["means"])

    def test_both_idle_arrays_carry_one_entry_shape(self):
        """`in_progress_with_no_live_run` and `review_idle` differ in which
        status they watch and which threshold they read, not in what an entry
        looks like — and `status` says which produced it without a consumer
        keying on the array it came out of.

        **The one test in this file that reddens for either idle check**, and
        deliberately so: it is about the SHAPE the two share, so it needs both
        of them populated and cannot be pinned to one. Each predicate still has
        tests that only it reddens — `test_the_row_with_no_slot_and_a_stale_
        clock_is_named` and `test_the_idle_review_row_is_named` — which is what
        makes the two separable. A shape assertion that could not see both
        arrays would not be asserting the shape.
        """
        box = Sandbox()
        for title in ("a dead run", "a forgotten verdict"):
            code, out = box.write("add", "--title", title, "--priority", "P1")
            self.assertEqual(code, 0, out)
        code, out = box.write("status", "TASK-001", "--status", "in_progress")
        self.assertEqual(code, 0, out)
        code, out = box.write("status", "TASK-002", "--status", "review")
        self.assertEqual(code, 0, out)
        box.age(REVIEW_DAYS * 24 + 1)
        conf = box.conformance()
        self.assertTrue(conf["in_progress_with_no_live_run"])
        self.assertTrue(conf["review_idle"])
        starved = conf["in_progress_with_no_live_run"][0]
        forgotten = conf["review_idle"][0]
        self.assertEqual(set(starved), set(forgotten))
        self.assertEqual("in_progress", starved["status"])
        self.assertEqual("review", forgotten["status"])


class TestBothIdleChecksAreEmptyWithoutAnEventLog(unittest.TestCase):
    """The 1.9 lesson, applied before it is reported rather than after.

    On a project with no event log every open row qualifies for an idle check
    by construction, and an array that restates `has_event_log: false` once per
    row has named no finding.
    """

    def test_no_event_log_names_nothing(self):
        box = Sandbox()
        code, out = box.write("add", "--title", "a row", "--priority", "P1")
        self.assertEqual(code, 0, out)
        code, out = box.write("status", "TASK-001", "--status", "in_progress")
        self.assertEqual(code, 0, out)
        (box.root / ".perry" / "events.jsonl").unlink()
        conf = box.conformance()
        self.assertFalse(conf["has_event_log"])
        self.assertEqual([], conf["in_progress_with_no_live_run"])
        self.assertEqual([], conf["review_idle"])

    def test_blocked_by_closed_rows_still_works_without_one(self):
        """It is a graph question, not a clock question, so the flag is
        irrelevant to it — and saying so is what stops the three checks from
        being switched off together."""
        box = stranded_board()
        (box.root / ".perry" / "events.jsonl").unlink()
        conf = box.conformance()
        self.assertFalse(conf["has_event_log"])
        self.assertEqual(["TASK-002", "TASK-004"],
                         conf["blocked_by_closed_rows"])


class TestNextActionCitesClosedReportsWhatItMightMean(unittest.TestCase):
    """The requirement that is not a check.

    On 2026-08-20 this fired on exactly TASK-037 and TASK-045 — the two rows
    that turned out to be stranded — and it was read as prose hygiene and
    silenced by rewriting the cells. A `{id, cites, status}` triple looks like
    a wording complaint. It is not one, and the entry now says so.
    """

    @classmethod
    def setUpClass(cls):
        box = Sandbox()
        for title in ("the blocker", "the row that cites it"):
            code, out = box.write("add", "--title", title, "--priority", "P1")
            assert code == 0, out
        code, out = box.write("status", "TASK-002", "--status", "blocked",
                              "--on", "TASK-001")
        assert code == 0, out
        code, out = box.write("next", "TASK-002", "--next", "waiting on TASK-001 to land")
        assert code == 0, out
        code, out = box.write("done", "TASK-001", "--evidence", "tests/run")
        assert code == 0, out
        cls.conf = box.conformance()
        cls.entry = cls.conf["next_action_cites_closed"][0]

    def test_the_original_triple_is_unchanged(self):
        """1.x adds keys. A consumer that read the old three still reads
        them."""
        self.assertEqual("TASK-002", self.entry["id"])
        self.assertEqual("TASK-001", self.entry["cites"])
        self.assertEqual("done", self.entry["status"])

    def test_it_states_both_readings_and_picks_neither(self):
        """The requirement itself. Say what the disagreement might be — the
        prose is stale, or the row is unblocked — and let triage decide."""
        readings = self.entry["readings"]
        self.assertEqual(2, len(readings))
        joined = " ".join(readings).lower()
        self.assertIn("stale prose", joined)
        self.assertIn("unblocked", joined)

    def test_the_sentence_names_the_two_rows_and_the_disagreement(self):
        means = self.entry["means"]
        self.assertIn("TASK-002", means)
        self.assertIn("TASK-001", means)
        self.assertIn("the prose is stale, or the row is unblocked", means)

    def test_it_warns_against_the_thing_that_was_actually_done(self):
        """A check that reports a pattern without its meaning gets suppressed
        by whoever reads it. The cells were rewritten; the entry has to say
        that rewriting them is not the default fix."""
        self.assertIn("Rewriting the cell is not the default fix",
                      self.entry["means"])

    def test_it_carries_what_the_graph_already_knows_about_the_row(self):
        """The correlation that was missed. This row's dependency has closed,
        so `blocked_stale` is true and the second reading is not a guess."""
        self.assertEqual("blocked", self.entry["row_status"])
        self.assertTrue(self.entry["blocked_stale"])
        self.assertIn("already agrees with the second reading",
                      self.entry["means"])
        self.assertIn("TASK-002", self.conf["blocked_by_closed_rows"],
                      "the same row reaches both checks, which is the signal "
                      "that was there on 2026-08-20 and was not read")

    def test_a_hit_whose_row_is_not_stale_says_so_instead_of_guessing(self):
        """The other branch. Nothing in the graph supports either reading, so
        the entry says the cell has to be read by somebody."""
        box = Sandbox()
        for title in ("the blocker", "the row that cites it"):
            code, out = box.write("add", "--title", title, "--priority", "P1")
            self.assertEqual(code, 0, out)
        code, out = box.write("next", "TASK-002", "--next", "picks up after TASK-001")
        self.assertEqual(code, 0, out)
        code, out = box.write("done", "TASK-001", "--evidence", "tests/run")
        self.assertEqual(code, 0, out)
        entry = box.conformance()["next_action_cites_closed"][0]
        self.assertFalse(entry["blocked_stale"])
        self.assertIn("somebody has to read the cell", entry["means"])


class TestTheContractAnnouncedAllOfIt(unittest.TestCase):
    """A key that is emitted and undocumented is what the parity check counts,
    and a MEANING that moved under a consumer is what `semantics` is for."""

    @classmethod
    def setUpClass(cls):
        cls.payload = stranded_board().list()
        cls.doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()

    def test_the_minor_moved(self):
        # The pin moves with every minor. TASK-142 shipped at 1.13 and
        # `semantics` below is what keeps this suite about 1.13; the
        # handle here is only "the doc and the tool agree about today".
        self.assertEqual("perry-task/list/1.18", self.payload["contract"])
        self.assertIn("`perry-task/list/1.18`", self.doc)

    def test_every_new_conformance_key_is_documented(self):
        for key in ("blocked_by_closed_rows", "in_progress_with_no_live_run",
                    "review_idle"):
            self.assertIn(key, self.payload["conformance"], key)
            self.assertIn(f"| `{key}` |", self.doc,
                          f"{key} is emitted and the contract does not "
                          f"declare it — the parity check counts that")

    def test_the_semantics_entry_names_the_array_whose_use_changed(self):
        entry = next((s for s in self.payload["semantics"]
                      if s["version"] == "1.13"), None)
        self.assertIsNotNone(
            entry, "a consumer rendering `next_action_cites_closed` as lint "
                   "has no other way to learn it is not lint")
        self.assertEqual(["conformance.next_action_cites_closed"],
                         entry["fields"])

    def test_the_three_keys_are_always_present_even_on_a_clean_board(self):
        """Rule 1: an unknown value is `[]`, never a missing key."""
        conf = Sandbox().conformance()
        for key in ("blocked_by_closed_rows", "in_progress_with_no_live_run",
                    "review_idle"):
            self.assertEqual([], conf[key], key)

    def test_both_thresholds_are_declared_in_the_schema(self):
        """Not invented beside the check. `perry-lint`, the entry card and this
        payload read one number each."""
        thresholds = SCHEMA["thresholds"]
        for name in ("in_progress_idle_hours", "review_idle_days"):
            self.assertIn(name, thresholds)
            self.assertIn("note", thresholds[name])
            self.assertIn("calibrated", thresholds[name]["note"].lower())

    def test_the_in_progress_threshold_cannot_undercut_the_marker_ttl(self):
        """The threshold must be at least the marker TTL, so this check can
        never name a row that a run of ordinary length is still inside.

        The literal `3600` this assertion used to carry was a third copy of a
        number that has since moved once (TASK-160 raised the TTL to 14400s),
        and a copy that does not move is a test that stops testing. It reads
        the script's own default now — see `TestThresholdsAgree`.
        """
        self.assertGreaterEqual(
            IN_PROGRESS_HOURS * 3600, LIMITER_TTL_DEFAULT,
            f"PERRY_DISPATCH_STALE_TTL defaults to {LIMITER_TTL_DEFAULT}s; an "
            f"idle threshold below it names rows whose marker is still valid")

    def test_triage_step_zero_point_five_lists_all_three(self):
        """`conformance` is only read because the procedure says to read it,
        and a key no procedure names is a key nobody looks at."""
        procedure = (PERRY_HOME / "work" / "reference"
                     / "subcommands.md").read_text()
        for key in ("blocked_by_closed_rows", "in_progress_with_no_live_run",
                    "review_idle"):
            self.assertIn(f"| `{key}` |", procedure, key)
        self.assertIn("Rewriting the cell is not the default fix", procedure,
                      "the procedure told triage this was the cheapest stale "
                      "row to fix, and that is what produced the rewrite")


class TestThresholdsAgree(unittest.TestCase):
    """TASK-160 — the marker TTL is one number with two readers and a
    calibrated neighbour, and none of the three may drift.

    `bin/perry-dispatch-limit` writes and reaps the markers;
    `bin/perry-task § live_dispatch_ids` reads them and deliberately never
    calls the script, *"because a `list --json` that could delete another
    session's slot is a read command with a side effect on shared state"*. That
    refusal is right, and it is exactly what makes drift possible: the reader
    carries its own copy of the default, so nothing but this class notices if
    the two stop matching.

    **The asymmetry is what makes it dangerous.** A reader with the SHORTER TTL
    calls a marker dead while the writer still counts the slot live — so
    `in_progress_with_no_live_run` names a row an agent is actively holding,
    and the entry's own `means` text then invites the PMO to re-dispatch it.
    A second agent on a row a first one still holds is the failure the dispatch
    limit exists to prevent, arriving through the check built to catch it.
    """

    def reader_default(self) -> int:
        """The fallback `live_dispatch_ids` uses when the env var is unset."""
        return _one_int(
            r'os\.environ\.get\("PERRY_DISPATCH_STALE_TTL"\) or (\d+)\)',
            PERRY_HOME / "bin" / "perry-task")

    def test_the_reader_and_the_writer_state_the_same_default(self):
        self.assertEqual(
            LIMITER_TTL_DEFAULT, self.reader_default(),
            "bin/perry-task § live_dispatch_ids and bin/perry-dispatch-limit "
            "disagree about how old a marker may be. Whichever is lower now "
            "decides, and if that is the reader it will name live runs "
            "starved.")

    def test_the_ttl_outlasts_the_longest_cycle_this_project_has_measured(self):
        """The defect itself. A TTL at or below a real cycle length reaps the
        marker of an agent that is still working, and the cap silently stops
        being the cap — 3600s did, against a measured 8100s cycle."""
        self.assertGreater(
            LIMITER_TTL_DEFAULT, LONGEST_MEASURED_CYCLE,
            "a marker may not expire while a run of a length this project has "
            "actually seen is still going")

    def test_the_idle_threshold_is_the_ceiling_the_ttl_was_chosen_under(self):
        """Both bounds at once, so the derivation is checked and not just
        recorded in a comment: the TTL sits strictly above the longest measured
        cycle and at or below the idle threshold it is calibrated against."""
        self.assertLessEqual(LIMITER_TTL_DEFAULT, IN_PROGRESS_HOURS * 3600)

    def test_the_schema_note_states_the_default_it_was_calibrated_against(self):
        """A note naming the wrong number is worse than no note: it is the
        only place a reader is told the two are linked at all."""
        note = SCHEMA["thresholds"]["in_progress_idle_hours"]["note"]
        self.assertIn("PERRY_DISPATCH_STALE_TTL", note)
        self.assertIn(f"{LIMITER_TTL_DEFAULT // 3600}h", note)


class TestOneStatementOfEachCheck(unittest.TestCase):
    """Both `list` paths report the same findings, from one implementation.

    `bin/perry-task` has two list paths — board-derived and store-derived — and
    they stated `startable` twice, 200 lines apart, until TASK-148. These four
    entries are computed once and called twice for the same reason.
    """

    def test_both_list_paths_call_the_one_implementation(self):
        source = (PERRY_HOME / "bin" / "perry-task").read_text()
        self.assertEqual(
            2, source.count("conformance.update(stranded_row_findings("),
            "one definition, called by both list paths")
        self.assertEqual(
            1, source.count("def stranded_row_findings("),
            "a second definition is the failure TASK-148 already paid for")

    def test_the_next_action_loop_is_no_longer_written_out_at_a_call_site(self):
        """It was, twice. The check whose MEANING this row changed is the worst
        possible one to have two copies of."""
        source = (PERRY_HOME / "bin" / "perry-task").read_text()
        self.assertEqual(
            0, source.count('conformance["next_action_cites_closed"].append'),
            "found a call site still appending to the array directly")


if __name__ == "__main__":
    unittest.main()
