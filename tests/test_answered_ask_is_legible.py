"""TASK-170 — an answered `USER-` ask was in no register a consumer could query.

1.14 made an ask a node in the dependency graph and got every edge right. What
it left is a **reader's** problem: a satisfied dependency stays in the record —
that is the whole reason 1.14 resolves it instead of reporting it unknown — but
an *answered* ask leaves `asks.items` by design, is not a row in `tasks[]`, and
since 1.14 is deliberately not in `conformance.depends_on_unknown` either. On
this repository, `TASK-040.depends_on == ["USER-016"]` beside
`asks: {"items": [], "open": 0}`.

The id **is** derivable: in `depends_on`, in no register, absent from
`depends_on_unknown` — it can only be an answered ask. aiMark noticed exactly
that and **refused to implement it**, because inferring an entity's kind from
three arrays it is missing from is set arithmetic, not a contract. This module
is the contract that replaces the arithmetic.

## Why the fix is at the edge and not in the register

The smaller-looking change is to widen `asks.items` so answered asks stay in
it carrying their `answered …` status. It is the wrong one, and every
assertion in `TestTheNeedsYouRegisterDidNotMove` is one half of the reason:

- the contract row for `items` reads *"the unanswered asks"* and the row for
  `open` reads `len(items)`, so widening `items` forces a choice between
  breaking that documented identity and inflating the count;
- `bin/perry-state § answered` — the predicate that does the filtering — was
  extracted to module level **because a dashboard said "2 items waiting on
  you" about two questions answered the same day**;
- `asks.open` is not a private number. `tests/test_diagnose.py §
  test_the_queue_register_reconciles_with_the_queue_on_this_repository` pins it
  against `perry-diagnose`'s `user_load.open_decisions_by_register.queue`.

A key that keeps its name and changes what it holds is the 1.10 `status_text`
lesson, and the question actually being asked — *what is this id in my
`depends_on`* — is about an **edge**. Answering it in the register would still
leave a consumer doing *"not in `tasks[]`, so try the asks"*.

So `depends_on` keeps its type and its contents and `depends_on_resolved` is a
**parallel array** beside it. Retyping `depends_on` into a list of objects
would be a breaking change on the key every consumer of this payload reads,
which is a major, not a minor.

## The guard that matters most

`TestNoEdgeWasReDecided`. 1.14 is correct and this row makes an
already-resolved edge legible; it must not move `startable`, `blocked_by` or
`blocked_stale` by so much as one row. That is asserted structurally — the two
arrays are built from the one `dependency_satisfied` and are compared against
each other on every row of a fixture that carries all three kinds of edge —
rather than by trusting a diff someone ran once.

Run: python3 tests/parallel test_answered_ask_is_legible
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from test_task_writer import PT, PERRY_HOME, Project
from test_one_startable_rule import Graph


#: Two ids nothing in this repository will ever carry, **assembled rather than
#: written**, for the reason `tests/test_ask_is_a_node.py` gives at length:
#: `bin/perry-diagnose § LOAD-02` scans every file here for id-shaped tokens
#: and reports the ones that resolve nowhere, so a module whose subject is an
#: unresolvable id would otherwise raise this project's own dangling count.
UNKNOWN_TASK = "TASK-" + "9998"
UNMINTED_ASK = "USER-" + "9998"


def payload(project: Project) -> dict:
    code, out = project.run("list", "--all")
    assert code == 0, out
    return out


def task(project: Project, tid: str) -> dict:
    return next(t for t in payload(project)["tasks"] if t["id"] == tid)


def edges(project: Project, tid: str) -> dict[str, dict]:
    return {e["id"]: e for e in task(project, tid)["depends_on_resolved"]}


def every_kind_of_edge() -> Project:
    """One row waiting on all four things a `depends_on` entry can name.

    Built through the tool's own writers, never by hand-editing a board: the
    state this row is about — an *answered* ask still named by a dependency —
    is produced by the ordinary `ask` / `answer` path, and a hand-written
    queue would not exercise the `answered` predicate that decides it.

    TASK-001 open, TASK-002 closed, USER-001 answered, USER-002 pending, plus
    two ids no register carries.
    """
    project = Project()
    for title in ("still open", "already closed"):
        code, out = project.run("add", "--title", title, "--priority", "P1")
        assert code == 0, out
    code, out = project.run("done", "TASK-002", "--evidence", "n/a")
    assert code == 0, out

    code, out = project.run("ask", "--needed", "which staleness threshold",
                            "--blocks", "TASK-003")
    assert code == 0, out
    assert out["id"] == "USER-001", out
    code, out = project.run("ask", "--needed", "confirm the store cutover",
                            "--blocks", "TASK-003")
    assert code == 0, out
    assert out["id"] == "USER-002", out

    code, out = project.run("add", "--title", "waits on everything",
                            "--priority", "P0")
    assert code == 0, out
    assert out["id"] == "TASK-003", out
    code, out = project.run("depends", "TASK-003", "--on",
                            "TASK-001, TASK-002, USER-001, USER-002, "
                            f"{UNKNOWN_TASK}, {UNMINTED_ASK}")
    assert code == 0, out
    code, out = project.run("answer", "USER-001", "--answer", "30 days")
    assert code == 0, out
    return project


class TestTheAnsweredAskIsLegibleAtTheEdge(unittest.TestCase):
    """V3 item 1: resolvable to the question text, in one lookup.

    Asserted on a fixture *and* on this repository below, because the finding
    was measured here and a fixture-only assertion would pass against a reader
    that never met a real answered ask.
    """

    @classmethod
    def setUpClass(cls):
        cls.project = every_kind_of_edge()

    def test_the_answered_ask_is_still_absent_from_all_three_registers(self):
        """The premise, asserted rather than assumed. If any of these three
        stopped being true the gap would have closed somewhere else and this
        module would be testing a fix for a problem that had moved."""
        data = payload(self.project)
        self.assertNotIn("USER-001", [t["id"] for t in data["tasks"]])
        self.assertNotIn("USER-001", [a["id"] for a in data["asks"]["items"]])
        self.assertNotIn(
            "USER-001",
            [u for row in data["conformance"]["depends_on_unknown"]
             for u in row["unknown"]])

    def test_the_edge_says_what_the_id_is(self):
        edge = edges(self.project, "TASK-003")["USER-001"]
        self.assertEqual(edge["kind"], "ask")
        self.assertTrue(edge["satisfied"])

    def test_the_edge_carries_the_question_text(self):
        """V3 item 1 in full: *"resolve it to the question text"*. A `kind`
        alone would name the register and still send the consumer to look the
        id up in one that no longer carries it."""
        self.assertEqual(edges(self.project, "TASK-003")["USER-001"]["title"],
                         "which staleness threshold")

    def test_the_edge_carries_the_answer_verbatim(self):
        self.assertIn("30 days",
                      edges(self.project, "TASK-003")["USER-001"]["status"])

    def test_a_pending_ask_is_the_same_shape_and_the_opposite_verdict(self):
        """V3 item 2, at the edge. The two states must stay distinguishable —
        a fix that made an answered ask legible by making it look pending
        would have traded one gap for a worse one."""
        edge = edges(self.project, "TASK-003")["USER-002"]
        self.assertEqual(edge["kind"], "ask")
        self.assertFalse(edge["satisfied"])
        self.assertEqual(edge["title"], "confirm the store cutover")

    def test_a_task_edge_says_task_and_carries_its_title(self):
        by_id = edges(self.project, "TASK-003")
        self.assertEqual(by_id["TASK-001"]["kind"], "task")
        self.assertFalse(by_id["TASK-001"]["satisfied"])
        self.assertEqual(by_id["TASK-001"]["title"], "still open")
        self.assertEqual(by_id["TASK-002"]["kind"], "task")
        self.assertTrue(by_id["TASK-002"]["satisfied"])

    def test_an_id_no_register_carries_says_unknown_and_invents_nothing(self):
        """`""`, not a title manufactured out of the handle. That invention is
        what `risks[].id` was corrected for at 1.6, where the severity letter
        became the id and every board's H and M displayed as `watch`."""
        for dep in (UNKNOWN_TASK, UNMINTED_ASK):
            edge = edges(self.project, "TASK-003")[dep]
            self.assertEqual(edge["kind"], "unknown", dep)
            self.assertFalse(edge["satisfied"], dep)
            self.assertEqual(edge["title"], "", dep)
            self.assertEqual(edge["status"], "", dep)

    def test_the_array_is_parallel_to_depends_on_and_not_a_retype(self):
        """Same order, same length, and `depends_on` still a list of strings.
        Making each entry an object would have been a MAJOR on the key every
        consumer reads; the whole point of a parallel array is that a consumer
        that does not want it pays nothing."""
        row = task(self.project, "TASK-003")
        self.assertTrue(all(isinstance(d, str) for d in row["depends_on"]))
        self.assertEqual([e["id"] for e in row["depends_on_resolved"]],
                         row["depends_on"])

    def test_every_task_carries_the_key_even_with_no_dependencies(self):
        """The contract's own rule: every declared key is ALWAYS present, so a
        consumer needs no missing-key branch."""
        for row in payload(self.project)["tasks"]:
            self.assertIn("depends_on_resolved", row, row["id"])
            self.assertIsInstance(row["depends_on_resolved"], list, row["id"])


class TestNoEdgeWasReDecided(unittest.TestCase):
    """V3 item 3, and the guard this row lives or dies by.

    1.14 is correct. This minor makes an already-resolved edge legible and must
    not move `startable`, `blocked_by` or `blocked_stale` on any row. The
    property is asserted structurally rather than by trusting a one-off diff:
    `blocked_by` is *derived from* `depends_on_resolved`, so the two cannot
    disagree unless somebody restates the rule.
    """

    @classmethod
    def setUpClass(cls):
        cls.project = every_kind_of_edge()

    def test_blocked_by_is_exactly_the_unsatisfied_edges(self):
        for row in payload(self.project)["tasks"]:
            self.assertEqual(
                row["blocked_by"],
                [e["id"] for e in row["depends_on_resolved"]
                 if not e["satisfied"]],
                f"{row['id']}: the two arrays disagree about an edge")

    def test_the_1_14_verdicts_are_unchanged_on_every_kind_of_edge(self):
        """Spelled out rather than derived, so this fails if the rule itself
        moves: open task and pending ask block, closed task and answered ask
        do not, and an id no register carries blocks — *"I do not know"* is not
        *"it is done"*."""
        self.assertEqual(task(self.project, "TASK-003")["blocked_by"],
                         ["TASK-001", "USER-002", UNKNOWN_TASK, UNMINTED_ASK])
        self.assertFalse(task(self.project, "TASK-003")["startable"])

    def test_the_unknown_ids_are_still_reported_unknown(self):
        """A second register to resolve against did not weaken the check, and
        neither did a per-edge `kind`. `unknown` at the edge and
        `depends_on_unknown` at the payload are the same finding said twice for
        two readers, and they must name the same ids."""
        data = payload(self.project)
        self.assertEqual(data["conformance"]["depends_on_unknown"],
                         [{"id": "TASK-003",
                           "unknown": [UNKNOWN_TASK, UNMINTED_ASK]}])
        self.assertEqual(
            sorted(e["id"] for e in task(self.project, "TASK-003")
                   ["depends_on_resolved"] if e["kind"] == "unknown"),
            sorted([UNKNOWN_TASK, UNMINTED_ASK]))

    def test_the_edge_rule_still_has_exactly_one_home(self):
        """`tests/test_ask_is_a_node.py` counts the assignment; this counts the
        DECISION. `satisfied` must be `dependency_satisfied`'s own answer, not
        a second spelling of it that could drift — TASK-148 paid for that once
        with `startable` and TASK-162 nearly paid for it again."""
        source = (PERRY_HOME / "bin" / "perry-task").read_text()
        self.assertEqual(source.count("def dependency_satisfied("), 1)
        self.assertEqual(source.count('task["blocked_by"] = ['), 1,
                         "the edge rule has more than one home again")


class TestBothListPathsCarryIt(unittest.TestCase):
    """TASK-148's lesson applied to a new key rather than to a rule.

    `cmd_list` serves a project that has a store; `_cmd_list_from_board` is the
    derivation `perry-tasks build` runs for one that does not. A key added to
    one template and not the other is a payload whose shape depends on which
    command minted it — and `tests/test_one_startable_rule.py`'s `Graph` is
    already the harness that reaches both, so this reuses it rather than
    building a third fixture for the same two callers.
    """

    @classmethod
    def setUpClass(cls):
        graph = Graph()
        cls.store = graph.from_store()
        cls.board = graph.from_board()

    def resolved(self, payload: dict) -> dict:
        return {t["id"]: t.get("depends_on_resolved", "MISSING KEY")
                for t in payload["tasks"]}

    def test_the_key_is_on_every_row_of_both_payloads(self):
        for name, data in (("store", self.store), ("board", self.board)):
            for tid, value in self.resolved(data).items():
                self.assertIsInstance(value, list, f"{name} path, {tid}")

    def test_the_two_paths_resolve_the_same_edges(self):
        self.assertEqual(self.resolved(self.board), self.resolved(self.store),
                         "`cmd_list` and `_cmd_list_from_board` disagree "
                         "about what a dependency is")

    def test_the_fixture_actually_carries_a_resolved_and_an_open_edge(self):
        """Two identical empty payloads would agree about nothing. TASK-002
        waits on a closed row and TASK-004 on an open one."""
        by_id = self.resolved(self.store)
        self.assertEqual([(e["kind"], e["satisfied"]) for e in by_id["TASK-002"]],
                         [("task", True)])
        self.assertEqual([(e["kind"], e["satisfied"]) for e in by_id["TASK-004"]],
                         [("task", False)])


class TestTheNeedsYouRegisterDidNotMove(unittest.TestCase):
    """V3 item 2 and item 5: `asks` still means what every reader of it means.

    This is the option that was NOT taken, asserted so that taking it later is
    a deliberate act with a red test in front of it rather than a quiet
    widening of a live list.
    """

    @classmethod
    def setUpClass(cls):
        cls.project = every_kind_of_edge()

    def test_only_the_pending_ask_is_in_the_needs_you_list(self):
        data = payload(self.project)
        self.assertEqual([a["id"] for a in data["asks"]["items"]],
                         ["USER-002"],
                         "an answered ask came back into the needs-you list")

    def test_open_still_counts_only_what_is_waiting_on_the_user(self):
        """The number behind *"2 items waiting on you"* about two questions
        answered the same day, which is why `answered` is shared code."""
        data = payload(self.project)
        self.assertEqual(data["asks"]["open"], 1)
        self.assertEqual(data["asks"]["open"], len(data["asks"]["items"]),
                         "the contract documents `open` as `len(items)`")

    def test_the_answered_ask_is_reachable_without_being_in_that_list(self):
        """Both halves together. Asserting only the first would pass against a
        fix that closed the gap by dropping the ask from the record."""
        self.assertNotIn("USER-001",
                         [a["id"] for a in payload(self.project)
                          ["asks"]["items"]])
        self.assertEqual(edges(self.project, "TASK-003")["USER-001"]["kind"],
                         "ask")

    def test_the_filter_is_still_the_one_shared_predicate(self):
        source = (PERRY_HOME / "bin" / "perry-task").read_text()
        self.assertIn("if not ps.answered(u)]", source,
                      "the needs-you list stopped using the shared predicate")


class TestOnThisRepositoryAndNotAFixture(unittest.TestCase):
    """V3 item 1's own words: *"Prove it against this repository, not a
    fixture."* This is the board the finding was measured on, and TASK-040 is
    the row it was measured with."""

    @classmethod
    def setUpClass(cls):
        proc = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"),
             "list", "--all", "--json"],
            capture_output=True, text=True, timeout=180, cwd=str(PERRY_HOME))
        assert proc.returncode == 0, proc.stderr
        cls.data = json.loads(proc.stdout)
        cls.rows = {t["id"]: t for t in cls.data["tasks"]}

    def test_the_gap_this_row_opened_for_is_still_the_live_shape(self):
        self.assertEqual(self.data["asks"], {"items": [], "open": 0},
                         "this board's asks are all answered — if that has "
                         "changed, re-measure before trusting the rest")
        self.assertEqual(self.rows["TASK-040"]["depends_on"], ["USER-016"])

    def test_user_016_resolves_to_its_question_text_in_one_lookup(self):
        edge, = self.rows["TASK-040"]["depends_on_resolved"]
        self.assertEqual(edge["id"], "USER-016")
        self.assertEqual(edge["kind"], "ask")
        self.assertTrue(edge["satisfied"])
        self.assertIn("risks.jsonl", edge["title"])
        self.assertTrue(edge["status"].strip().strip("*` ").lower()
                        .startswith("answered"))

    def test_the_other_answered_ask_on_this_board_resolves_too(self):
        """USER-015 as well as USER-016 — one row resolving could be a
        coincidence of that row's cell."""
        edge, = self.rows["TASK-114"]["depends_on_resolved"]
        self.assertEqual((edge["id"], edge["kind"], edge["satisfied"]),
                         ("USER-015", "ask", True))

    def test_the_contract_moved_and_the_document_says_why(self):
        """V3 item 4. A pure key addition is a plain minor: nothing existing
        changed meaning, so `semantics` gains no entry for it.

        The claim is **the absence of a 1.15 entry**, and that is what is
        asserted. It was originally written as "the array's last word is
        1.14's", which said the same thing only while 1.15 was the newest
        version — 1.16 (TASK-117) moved five values' meaning and correctly
        added an entry, and the old form would have called that a regression
        in this row. An assertion that encodes a moment rather than the rule
        is the defect this repository has spent the most nights on.
        """
        self.assertEqual(PT.LIST_CONTRACT, "perry-task/list/1.17")
        self.assertEqual(self.data["contract"], PT.LIST_CONTRACT)
        doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        self.assertIn("`perry-task/list/1.17`", doc)
        self.assertIn("### 1.15 —", doc)
        self.assertIn("depends_on_resolved", doc)
        self.assertNotIn("1.15", [e["version"] for e in PT.LIST_SEMANTICS],
                         "1.15 adds a key and moves no meaning, so a "
                         "`semantics` entry would be a false alarm")
        self.assertIn("1.14", [e["version"] for e in PT.LIST_SEMANTICS],
                      "1.14's entry is what 1.15 was measured against")


if __name__ == "__main__":
    unittest.main()
