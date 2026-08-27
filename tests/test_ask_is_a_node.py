"""TASK-162 — a `USER-` ask is a node in the dependency graph.

The claim under test: **the writer and the reader now say the same thing about
a row that waits on a question.**

Before this, they did not. `perry-task depends TASK-114 --on USER-015` was
ACCEPTED at the write and then reported by the reader as
`conformance.depends_on_unknown`; `depends --clear` moved the same row to
`conformance.blocked_without_dependency`, whose own message is *"a row nobody
can unblock"*. Both readings were on Perry's own board on 2026-08-21 and
neither was a lie about the row — which is what made it a decision about the
graph rather than a bug in one check.

The decision is **yes**, and the argument is that Perry already writes this
edge from the other end: `ask --blocks TASK-114` puts the task in the queue
row's `Blocks` cell. What makes something a node is not being a task, it is
having a state this tool can read that reaches a terminal value — a task is
`done`/`dropped`, an ask is `answered`, and a `DESIGN-`/`ADR-` handle is
neither and never will be.

**Why every assertion here reads two fields out of one payload.** The lazy fix
for the live finding is to stop checking, and a test that asserted only
"TASK-002 is not in `depends_on_unknown`" would pass against it. So:

- the row that must be clean is asserted clean in `depends_on_unknown` **and**
  in `blocked_without_dependency`, together — the two shapes the old board had
  to choose between;
- a genuinely unknown id is asserted still reported in the same call, in both
  the task family and the ask family (`UNKNOWN_TASK` and `UNMINTED_ASK` below,
  spelled in two pieces so this module adds nothing to the repository's own
  dangling-id report) — an id the queue does not carry is not made resolvable
  by the queue existing;
- the answered/pending pair is asserted as a pair, because `blocked_stale` and
  `blocked_by_closed_rows` are one field and its aggregate and a fix that moved
  one without the other would leave the payload disagreeing with itself.

Run: python3 tests/parallel test_ask_is_a_node
"""

from __future__ import annotations

import unittest

from test_task_writer import PT, PERRY_HOME, Project


#: A board with no `## User Input Queue` at all. Most projects never ask the
#: user anything, and on those a `USER-` id must read exactly as it did before
#: this feature existed: unknown, and unsatisfied.
NO_QUEUE_BOARD = """# Board — no queue

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Top risks

- none
"""


#: Two ids nothing in this repository will ever carry, **assembled rather than
#: written**. `bin/perry-diagnose § LOAD-02` scans every file here for id-shaped
#: tokens and reports the ones that resolve nowhere, and
#: `perry-task § idish_tokens_that_resolve_nowhere` makes the same complaint at
#: the write site — a test whose whole subject is an unresolvable id would
#: otherwise put two fresh entries into the repository's own dangling report and
#: one fresh row into its open-question count. Spelling them in two pieces keeps
#: this module's contribution to those numbers at zero, which is the only honest
#: way to add a test about a token that must name nothing.
UNKNOWN_TASK = "TASK-" + "9999"
UNMINTED_ASK = "USER-" + "9999"


def payload(project: Project) -> dict:
    code, out = project.run("list", "--all")
    assert code == 0, out
    return out


def task(project: Project, tid: str) -> dict:
    return next(t for t in payload(project)["tasks"] if t["id"] == tid)


def blocked_on_an_ask() -> Project:
    """One task, one ask that blocks it, and the edge declared both ways.

    Built through the tool's own writers — `ask --blocks` for the queue side,
    `status --on` for the task side — because the disagreement this fixes was
    between two of those writers' outputs, and a hand-written board would not
    reproduce it.
    """
    project = Project()
    code, out = project.run("add", "--title", "waits on a paste-back",
                            "--priority", "P1")
    assert code == 0, out
    code, out = project.run("ask", "--needed", "hand the prompt to an agent "
                            "and paste the result back", "--blocks", "TASK-001")
    assert code == 0, out
    assert out["id"] == "USER-001", out
    code, out = project.run("status", "TASK-001", "--status", "blocked",
                            "--on", "USER-001")
    assert code == 0, out
    return project


class TestTheLiveShapeStopsBeingAFinding(unittest.TestCase):
    """V3 item 1, both halves of the choice the board used to have."""

    def setUp(self):
        self.project = blocked_on_an_ask()

    def test_the_row_is_named_by_neither_check(self):
        """The two shapes TASK-114 had to choose between, out of one payload.

        Asserting only the first would pass against a reader that stopped
        resolving ids altogether; asserting only the second would pass against
        one that never had the row.
        """
        conformance = payload(self.project)["conformance"]
        self.assertEqual(conformance["depends_on_unknown"], [])
        self.assertEqual(conformance["blocked_without_dependency"], [])
        self.assertEqual([t["id"] for t in payload(self.project)["tasks"]],
                         ["TASK-001"], "the row itself must still be there")

    def test_the_edge_is_still_declared_on_the_row(self):
        """Clean is not the same as gone. `depends_on` is the record of what
        the row waits on, and a fix that silenced the check by dropping the
        edge would have taken the only pointer to the answer with it."""
        self.assertEqual(task(self.project, "TASK-001")["depends_on"],
                         ["USER-001"])

    def test_the_writer_still_accepts_the_shape_it_documents(self):
        """`depends --on USER-nnn` is the shape the refusal-free path names.
        The other available answer to TASK-162 was to refuse it here."""
        code, out = self.project.run("depends", "TASK-001", "--clear")
        self.assertEqual(code, 0, out)
        code, out = self.project.run("depends", "TASK-001", "--on", "USER-001")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["depends_on"], ["USER-001"])


class TestAGenuinelyUnknownIdIsStillReported(unittest.TestCase):
    """V3 item 2 — the item that stops the lazy fix.

    A reader that answered item 1 by not checking would pass everything above
    and fail here, in both id families.
    """

    def setUp(self):
        self.project = blocked_on_an_ask()

    def test_an_unknown_task_id_reaches_depends_on_unknown(self):
        code, out = self.project.run("depends", "TASK-001",
                                     "--on", f"USER-001, {UNKNOWN_TASK}")
        self.assertEqual(code, 0, out)
        conformance = payload(self.project)["conformance"]
        self.assertEqual(conformance["depends_on_unknown"],
                         [{"id": "TASK-001", "unknown": [UNKNOWN_TASK]}],
                         "the resolvable half must drop out and the unknown "
                         "half must stay — this is one row with two edges")

    def test_an_ask_the_queue_does_not_carry_is_unknown_too(self):
        """The register resolves the asks this project ISSUED, not the shape of
        the id. `UNMINTED_ASK` was never minted and nothing can ever answer
        it, so the ask family gets no blanket pass from the queue existing."""
        code, out = self.project.run("depends", "TASK-001",
                                     "--on", UNMINTED_ASK)
        self.assertEqual(code, 0, out)
        conformance = payload(self.project)["conformance"]
        self.assertEqual(conformance["depends_on_unknown"],
                         [{"id": "TASK-001", "unknown": [UNMINTED_ASK]}])
        self.assertEqual(task(self.project, "TASK-001")["blocked_by"],
                         [UNMINTED_ASK],
                         "an id nothing carries is unsatisfied, not satisfied")

    def test_a_project_with_no_queue_reads_exactly_as_it_did_before(self):
        """No `## User Input Queue`, so no register, so every `USER-` id is a
        handle Perry cannot resolve — the behaviour this repository shipped
        before TASK-162, unchanged for the projects that never ask anything."""
        project = Project(board=NO_QUEUE_BOARD)
        code, out = project.run("add", "--title", "waits on nothing readable",
                                "--priority", "P1")
        self.assertEqual(code, 0, out)
        code, out = project.run("depends", "TASK-001", "--on", "USER-001")
        self.assertEqual(code, 0, out)
        self.assertEqual(payload(project)["conformance"]["depends_on_unknown"],
                         [{"id": "TASK-001", "unknown": ["USER-001"]}])


class TestAnsweredSatisfiesTheEdgeAndPendingDoesNot(unittest.TestCase):
    """V3 item 3 — asserted as a pair in each state, never one at a time.

    `blocked_stale` is a field on the row and `blocked_by_closed_rows` is its
    aggregate (`bin/lib § resolve_startability`, `stranded_row_findings`). They
    are one rule with two readers, and this suite's whole job is to keep them
    from disagreeing about a row whose blocker is a question.
    """

    def setUp(self):
        self.project = blocked_on_an_ask()

    def pair(self) -> tuple[dict, list]:
        data = payload(self.project)
        row = next(t for t in data["tasks"] if t["id"] == "TASK-001")
        return row, data["conformance"]["blocked_by_closed_rows"]

    def test_a_pending_ask_leaves_the_row_blocked(self):
        row, aggregate = self.pair()
        self.assertEqual(row["blocked_by"], ["USER-001"])
        self.assertFalse(row["startable"])
        self.assertFalse(row["blocked_stale"])
        self.assertEqual(aggregate, [],
                         "the field and its aggregate must agree while the "
                         "question is still open")

    def test_an_answered_ask_satisfies_it(self):
        code, out = self.project.run("answer", "USER-001",
                                     "--answer", "here is the pasted result")
        self.assertEqual(code, 0, out)
        row, aggregate = self.pair()
        self.assertEqual(row["blocked_by"], [],
                         "an answered ask is terminal, exactly as a closed "
                         "task is")
        self.assertTrue(row["startable"])
        self.assertTrue(row["blocked_stale"])
        self.assertEqual(aggregate, ["TASK-001"],
                         "the field moved and the aggregate must move with it")

    def test_the_stored_status_is_left_alone(self):
        """1.12's rule, unchanged by 1.14: `list` reports, it does not rewrite
        a cell nobody asked it to rewrite. The row still reads `blocked` and
        `blocked_stale` is how a reader learns the cell is out of date."""
        code, out = self.project.run("answer", "USER-001", "--answer", "done")
        self.assertEqual(code, 0, out)
        self.assertEqual(task(self.project, "TASK-001")["status"], "blocked")

    def test_the_row_is_in_neither_conformance_array_in_either_state(self):
        """The finding TASK-162 opened for must stay gone across the answer.
        A fix that only made the PENDING state clean would let the row come
        back as a finding the moment the question was answered."""
        for _ in range(1):
            conformance = payload(self.project)["conformance"]
            self.assertEqual(conformance["depends_on_unknown"], [])
            self.assertEqual(conformance["blocked_without_dependency"], [])
        code, out = self.project.run("answer", "USER-001", "--answer", "done")
        self.assertEqual(code, 0, out)
        conformance = payload(self.project)["conformance"]
        self.assertEqual(conformance["depends_on_unknown"], [])
        self.assertEqual(conformance["blocked_without_dependency"], [])


class TestAnAskIsANodeAndStillNotATask(unittest.TestCase):
    """The boundary the decision does NOT cross.

    An ask resolves an edge. It does not become a row in `tasks[]`, it does not
    get a `blocks` list of its own in that array, and it cannot close a
    dependency cycle — a question waits on a human and on nothing this tool can
    name.
    """

    def setUp(self):
        self.project = blocked_on_an_ask()

    def test_the_ask_is_not_in_the_task_array(self):
        data = payload(self.project)
        self.assertEqual([t["id"] for t in data["tasks"]], ["TASK-001"])
        self.assertEqual([a["id"] for a in data["asks"]["items"]], ["USER-001"],
                         "it is still a row of the register it belongs to")

    def test_no_cycle_is_reported_through_an_ask(self):
        self.assertEqual(payload(self.project)["conformance"]
                         ["dependency_cycles"], [])

    def test_the_reverse_edge_is_the_asks_own_blocks_cell(self):
        """`blocks` in `tasks[]` stays a task-to-task relation. The other
        direction of this edge was already written, by `ask --blocks`, and is
        where a reader finds it."""
        self.assertEqual(task(self.project, "TASK-001")["blocks"], [])
        ask = payload(self.project)["asks"]["items"][0]
        self.assertEqual(ask["blocks"], "TASK-001")


class TestTheContractAnnouncedTheChange(unittest.TestCase):
    """`schema/task-list-contract.md`'s own rule: a payload key whose MEANING
    moves under a live consumer needs a `semantics` entry, not just a minor.
    TASK-141 set that precedent at 1.12 and this is the same kind of move —
    `blocked_by` did not gain a key, it started resolving a second register.
    """

    DOC = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()

    def test_the_minor_moved(self):
        self.assertEqual(PT.LIST_CONTRACT, "perry-task/list/1.16")
        self.assertIn(PT.LIST_CONTRACT, self.DOC)

    def test_semantics_carries_an_entry_for_it(self):
        entry = next((e for e in PT.LIST_SEMANTICS if e["version"] == "1.14"),
                     None)
        self.assertIsNotNone(entry, "1.14 changed a meaning and said nothing")
        for field in ("blocked_by", "conformance.depends_on_unknown",
                      "conformance.blocked_by_closed_rows"):
            self.assertIn(field, entry["fields"])

    def test_the_note_names_both_states_of_an_ask(self):
        """A `semantics` note that said "asks are now resolved" would leave a
        consumer unable to tell which way a row moves. Both directions are the
        change."""
        note = next(e for e in PT.LIST_SEMANTICS
                    if e["version"] == "1.14")["note"].lower()
        self.assertIn("pending", note)
        self.assertIn("answered", note)

    def test_the_payload_carries_the_semantics_list_to_a_consumer(self):
        """It is served, not only declared in the source — the whole use of the
        array is a front-end reading it out of a live response."""
        versions = [e["version"] for e in payload(Project())["semantics"]]
        self.assertIn("1.14", versions)

    def test_the_document_says_an_answered_ask_satisfies_an_edge(self):
        for phrase in ("`USER-", "answered"):
            self.assertIn(phrase, self.DOC)
        self.assertIn("TASK-162", self.DOC,
                      "the row that decided this is the citation a reader "
                      "follows when the rule surprises them")


class TestOneStatementOfTheEdgeRule(unittest.TestCase):
    """TASK-148's lesson, applied to the rule this row had to change.

    `blocked_by`, `blocks` and `depends_on_unknown` were written out at BOTH
    `list` call sites, ~200 lines apart. TASK-141 already paid for that once
    with `startable`; this change would have been the second fix applied twice.
    A count of assignment sites is the cheap guard.
    """

    SOURCE = (PERRY_HOME / "bin" / "perry-task").read_text()

    def test_blocked_by_is_assigned_in_exactly_one_place(self):
        assignments = self.SOURCE.count('task["blocked_by"] = [')
        self.assertEqual(assignments, 1,
                         "the edge rule has more than one home again")

    def test_both_list_paths_call_the_one_resolver(self):
        self.assertEqual(self.SOURCE.count("resolve_dependency_edges(\n"), 2,
                         "both `list` paths must reach the same rule")


if __name__ == "__main__":
    unittest.main()
