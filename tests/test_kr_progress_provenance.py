"""TASK-120 — a KR's `current` is an assertion, and both payloads say so.

**The state this replaces, measured on Perry's own register.** `target` and
`current` are hand-written into `phase/<NNN>-linkage.md` and nothing derived,
checked or aged them. The two readings a consumer could take were wrong in
opposite directions on the same day:

| KR | target | current | read as | actually |
|---|---|---|---|---|
| `P-O1.1` | 1 | 0 | 0% | all four linked tasks closed |
| `P-O2.2` | 0 | 0 | **met** | 13 row splits and 87 header resolutions still live |

The second is the systemic shape: six of the register's eight phase KRs drive a
count to zero, and the register template writes `current: 0`, so a
drive-to-zero KR reads as achieved on the day it is written.

**What this module refuses to test for, because it must never exist.** No
assertion here expects `current` to be derived from `tasks[]`. A KR's metric is
a count of something in the repository, and a closed task does not establish
that the count is zero — only re-running the count does. The linked-task tally
is checked as a count of TASKS, beside `current` and never inside it; the one
test that puts the two together
(`TestBothOfTodaysWrongReadingsFlip.test_a_kr_reading_zero_with_every_task_closed_shows_both`)
asserts that the payload carries the CONTRADICTION, not that it resolves it.

Run: python3 tests/parallel test_kr_progress_provenance
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
GOALS = PERRY_HOME / "bin" / "perry-goals"
STATE = PERRY_HOME / "bin" / "perry-state"

import sys  # noqa: E402

sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402


def goals(root: Path, *argv) -> dict:
    r = subprocess.run(
        ["python3", str(GOALS), "list", *argv, "--root", str(root), "--json"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


def state(root: Path) -> dict:
    r = subprocess.run(
        ["python3", str(STATE), "--json", "--root", str(root)],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


def kr(payload: dict, kr_id: str) -> dict:
    hits = [k for k in payload["krs"] if k["id"] == kr_id]
    assert len(hits) == 1, f"{kr_id}: {len(hits)} rows"
    return hits[0]


# ── a project built for the purpose ───────────────────────────────────────
#
# `phase/002-linkage.md` in this repository is the `goals` lane's file and this
# row does not write it, so every case that needs a particular register builds
# its own project. Both directions of the staleness case run against ONE
# fixture, differing only by an event appended between the two reads.

PHASE = """# Phase #001 — a-phase

> **Owner**: `goals` skill (only writer).
> **Started**: 2026-08-01
> **Status**: active
> **Source**: `OKR.md` v1

## Phase Focus

Drive two counts to zero, and leave a third KR with no number at all.

---

## Objective 1 — Drive two counts to zero

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| P-O1.1 | Rendered from the store | 1 of 1 | |
| P-O1.2 | Readers resolving a header cell | 0 (baseline 5) | |
| P-O1.3 | Never given a number | 0 (baseline unmeasured) | |
"""

LINKAGE = """---
linkage: 1
phase: "001-a-phase"
updated: "{updated}"
objectives:
  - id: O1
    title: "Drive two counts to zero"
    krs:
      - id: P-O1.1
        title: "Rendered from the store"
        metric: "1 of 1"
        target: 1
        current: 0
        stretch: false
        tasks: ["TASK-001", "TASK-002"]
      - id: P-O1.2
        title: "Readers resolving a header cell"
        metric: "0 (baseline 5)"
        target: 0
        current: 0
        stretch: false
        tasks: ["TASK-003"]
      - id: P-O1.3
        title: "Never given a number"
        metric: "0 (baseline unmeasured)"
        target: 0
        stretch: false
        tasks: ["TASK-004"]
unlinked: []
projects: []
---

# Phase #001 — linkage graph
"""

TASKS = [
    {"id": "TASK-001", "title": "One", "status": "done", "priority": "P1"},
    {"id": "TASK-002", "title": "Two", "status": "done", "priority": "P1"},
    {"id": "TASK-003", "title": "Three", "status": "in_progress",
     "priority": "P1"},
    {"id": "TASK-004", "title": "Four", "status": "not_started",
     "priority": "P1"},
]

#: Every state move predates the register's `updated`, so the register is
#: current until a test appends one that does not.
EVENTS = [
    {"ts": "2026-08-10T09:00:00", "event": "done", "id": "TASK-001",
     "from": "review", "to": "done"},
    {"ts": "2026-08-10T10:00:00", "event": "done", "id": "TASK-002",
     "from": "review", "to": "done"},
    {"ts": "2026-08-10T11:00:00", "event": "start", "id": "TASK-003",
     "from": "not_started", "to": "in_progress"},
    # A non-state event AFTER the assertion. `next` carries `from`/`to` holding
    # prose, and a staleness check keyed on the event NAME rather than on the
    # value would call every KR below stale on the strength of this line.
    {"ts": "2026-08-20T12:00:00", "event": "next", "id": "TASK-003",
     "from": "an old next action", "to": "a new next action"},
]

UPDATED = "2026-08-15T12:00:00Z"


def build_project(updated: str = UPDATED) -> Path:
    root = Path(tempfile.mkdtemp())
    (root / ".perry").mkdir()
    (root / ".perry" / "config.md").write_text(
        "# Perry configuration\n\n- State root: .\n")
    (root / ".perry" / "events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in EVENTS))
    (root / "phase").mkdir()
    (root / "phase" / "001-a-phase.md").write_text(PHASE)
    (root / "phase" / "001-linkage.md").write_text(LINKAGE.format(updated=updated))
    (root / "phase" / "CURRENT").write_text("001-a-phase\n")
    (root / "OKR.md").write_text(
        "# OKR — fixture\n\n## Mission\n\nShip it.\n\n---\n\n## v1: 2026-08-01\n")
    (root / "tasks.jsonl").write_text(
        "".join(json.dumps(t) + "\n" for t in TASKS))
    (root / "BOARD.md").write_text(
        "# Board\n\n## P1\n\n| ID | Task | Owner | Status |\n"
        "|----|------|-------|--------|\n"
        + "".join(f"| {t['id']} | {t['title']} |  | {t['status']} |\n"
                 for t in TASKS))
    return root


def append_event(root: Path, event: dict) -> None:
    with open(root / ".perry" / "events.jsonl", "a") as fh:
        fh.write(json.dumps(event) + "\n")


def close_task(root: Path, task_id: str) -> None:
    """Close a task in BOTH stores, the way `perry-task done` would."""
    rows = [json.loads(l) for l in
            (root / "tasks.jsonl").read_text().splitlines() if l.strip()]
    for row in rows:
        if row["id"] == task_id:
            row["status"] = "done"
    (root / "tasks.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows))


class Fixture(unittest.TestCase):
    def setUp(self):
        self.root = build_project()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)


# ── V3 item 1 ─────────────────────────────────────────────────────────────


class TestBothOfTodaysWrongReadingsFlip(Fixture):
    """Read against this repository's OWN register, unchanged.

    `perry/phase/002-linkage.md` belongs to the `goals` lane and TASK-120 does
    not write it. So the assertions here are about the SHAPE the payload
    reports, never about a hand-typed number: what changed is that the payload
    can no longer be read as saying either of the two wrong things.
    """

    def own_repo(self) -> dict:
        return goals(PERRY_HOME)

    def test_no_current_in_the_payload_claims_to_be_a_measurement(self):
        """The `P-O2.2` reading. `target: 0` with `current: 0` read as MET; it
        cannot any more, because nothing in the payload says the zero was
        measured and the payload now says which."""
        payload = self.own_repo()
        for k in payload["krs"]:
            self.assertFalse(
                k["current_provenance"]["measured"],
                f"{k['id']}: a `current` was published as measured data")
        asserted = [k for k in payload["krs"]
                    if k["current_provenance"]["state"] == "asserted"]
        self.assertTrue(asserted, "the register carries no asserted `current`")
        for k in asserted:
            self.assertEqual(k["current_provenance"]["source"],
                             "linkage-register")
            self.assertEqual(k["current_provenance"]["asserted_scope"],
                             "register",
                             "the date belongs to the register, not the KR, "
                             "and the payload must say so")

    def test_a_drive_to_zero_kr_is_not_reported_as_met(self):
        """No key anywhere in a KR row says `met`, `achieved` or `progress`.

        The `2.0` contract removed `progress` for a related reason and this is
        the guard that the provenance work did not quietly reintroduce a
        verdict under another name."""
        for k in self.own_repo()["krs"]:
            for banned in ("progress", "met", "achieved", "percent", "ratio"):
                self.assertNotIn(banned, k, f"{k['id']}: `{banned}` came back")

    def test_a_kr_reading_zero_with_every_task_closed_shows_both(self):
        """The `P-O1.1` reading, on the fixture so the numbers are fixed.

        `current: 0` against `target: 1` with both linked tasks closed. The
        payload's job is to carry BOTH facts, in different units, and to
        resolve neither: `current` stays 0 because only re-running the metric
        may change it, and the task count says two of two are closed.
        """
        k = kr(goals(self.root), "P-O1.1")
        self.assertEqual(k["current"], 0.0)
        self.assertEqual(k["target"], 1.0)
        self.assertEqual(k["current_provenance"]["state"], "asserted")
        self.assertEqual(
            k["linked_task_completion"],
            {"total": 2, "done": 2, "dropped": 0, "open": 0, "unknown": 0})

    def test_the_tally_is_a_count_of_tasks_and_never_a_fraction(self):
        for k in goals(self.root)["krs"] + self.own_repo()["krs"]:
            for name, value in k["linked_task_completion"].items():
                self.assertIsInstance(
                    value, int,
                    f"{k['id']}.{name} is not a whole count of tasks")

    def test_the_same_three_blocks_reach_perry_state(self):
        """One derivation, two payloads. A second implementation is how the
        two would come to disagree about whether a number is stale."""
        rows = [k for o in state(self.root)["linkage"]["objectives"]
                for k in o["krs"]]
        by_id = {k["id"]: k for k in rows}
        self.assertEqual(set(by_id), {"P-O1.1", "P-O1.2", "P-O1.3"})
        from_goals = kr(goals(self.root), "P-O1.1")
        for block in ("current_provenance", "current_staleness",
                      "linked_task_completion"):
            self.assertEqual(by_id["P-O1.1"][block], from_goals[block],
                             f"{block} differs between the two payloads")


# ── V3 item 2 ─────────────────────────────────────────────────────────────


class TestAnUnassertedCurrentIsNullNotZero(Fixture):
    """`P-O1.3` has `target: 0` and no `current` at all.

    This is the systemic defect stated as a test: an unset `current` defaulting
    to `0.0` makes every drive-to-zero KR read as met on the day it is written,
    before any work starts. Reverting the default reddens this.
    """

    def test_the_number_is_null(self):
        k = kr(goals(self.root), "P-O1.3")
        self.assertEqual(k["target"], 0.0)
        self.assertIsNone(k["current"],
                          "an unwritten `current` came back as a number")

    def test_it_is_reported_as_unasserted_rather_than_as_a_value(self):
        k = kr(goals(self.root), "P-O1.3")
        self.assertEqual(k["current_provenance"]["state"], "unasserted")
        self.assertEqual(k["current_provenance"]["asserted_at"], "")
        self.assertEqual(k["current_provenance"]["source"], "")

    def test_an_unasserted_current_is_never_stale(self):
        """There is no number, so there is nothing that could have aged. The
        reason says which — `stale: false` alone would be indistinguishable
        from a number that has been checked."""
        s = kr(goals(self.root), "P-O1.3")["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertFalse(s["evaluated"])
        self.assertIn("never asserted", s["reason"])

    def test_it_is_named_by_the_conformance_block(self):
        conf = goals(self.root)["conformance"]
        self.assertIn("P-O1.3", conf["krs_without_numbers"])
        self.assertNotIn("P-O1.3", conf["krs_with_stale_current"])

    def test_perry_state_counts_it_apart_from_the_asserted_ones(self):
        counts = state(self.root)["attribution"]["kr_currents"]
        self.assertEqual(counts["total"], 3)
        self.assertEqual(counts["asserted"], 2)
        self.assertEqual(counts["unasserted"], 1)
        self.assertEqual(counts["measured"], 0,
                         "something claimed to have measured a KR")


# ── V3 item 3 ─────────────────────────────────────────────────────────────


class TestStalenessDiscriminatesInBothDirections(Fixture):
    """One fixture, two reads, one appended event between them.

    A check that only ever fires is worth as little as one that never does, so
    both directions run against the same register: unchanged it is NOT stale,
    and closing one linked task makes it stale and names that task.
    """

    def test_not_stale_while_nothing_has_moved(self):
        s = kr(goals(self.root), "P-O1.1")["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertTrue(s["evaluated"],
                        "not-stale must mean CHECKED, not `nobody asked`")
        self.assertEqual(s["moved_tasks"], [])
        self.assertEqual(
            s["reason"],
            "no linked task has changed state since 2026-08-15T12:00:00")

    def test_closing_one_linked_task_makes_it_stale_and_names_that_task(self):
        before = kr(goals(self.root), "P-O1.2")["current_staleness"]
        self.assertFalse(before["stale"])
        self.assertEqual(
            before["reason"],
            "no linked task has changed state since 2026-08-15T12:00:00")

        close_task(self.root, "TASK-003")
        append_event(self.root, {"ts": "2026-08-21T09:10:00", "event": "done",
                                 "id": "TASK-003", "from": "in_progress",
                                 "to": "done"})

        after = kr(goals(self.root), "P-O1.2")["current_staleness"]
        self.assertTrue(after["stale"])
        self.assertTrue(after["evaluated"])
        self.assertEqual(
            after["reason"],
            "1 linked task changed state after 2026-08-15T12:00:00: "
            "TASK-003 (in_progress → done)")
        self.assertEqual(after["moved_tasks"],
                         [{"id": "TASK-003", "from": "in_progress",
                           "to": "done", "at": "2026-08-21T09:10:00"}])

    def test_only_the_kr_whose_task_moved_goes_stale(self):
        """Staleness is per KR, not per register. A register-wide flag would
        make one moved task discredit every number in the file."""
        close_task(self.root, "TASK-003")
        append_event(self.root, {"ts": "2026-08-21T09:10:00", "event": "done",
                                 "id": "TASK-003", "from": "in_progress",
                                 "to": "done"})
        payload = goals(self.root)
        self.assertEqual(payload["conformance"]["krs_with_stale_current"],
                         ["P-O1.2"])
        self.assertFalse(kr(payload, "P-O1.1")["current_staleness"]["stale"])

    def test_a_prose_event_after_the_assertion_is_not_a_state_move(self):
        """`next` carries `from`/`to` holding the old and new next action. A
        check keyed on the event NAME rather than on the value would report
        `P-O1.2` stale on the strength of that line, and the fixture has one
        dated after the assertion for exactly this."""
        s = kr(goals(self.root), "P-O1.2")["current_staleness"]
        self.assertFalse(s["stale"], s["reason"])

    def test_perry_state_warns_and_counts_it(self):
        close_task(self.root, "TASK-003")
        append_event(self.root, {"ts": "2026-08-21T09:10:00", "event": "done",
                                 "id": "TASK-003", "from": "in_progress",
                                 "to": "done"})
        payload = state(self.root)
        counts = payload["attribution"]["kr_currents"]
        self.assertEqual(counts["stale"], 1)
        self.assertEqual(counts["stale_ids"], ["P-O1.2"])
        self.assertTrue(
            any("P-O1.2" in w and "no longer be trusted" in w
                for w in payload["warnings"]),
            f"no warning named the stale KR: {payload['warnings']}")


class TestWhatCouldNotBeDecidedSaysSo(unittest.TestCase):
    """`stale: false` with `evaluated: false` means NOBODY ASKED.

    Reporting the two as one is the shape this whole row is about: a payload
    that cannot tell a checked number from an unchecked one will be read as
    having checked.
    """

    def test_a_register_with_no_updated_timestamp_cannot_be_evaluated(self):
        root = build_project(updated="")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        s = kr(goals(root), "P-O1.1")["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertFalse(s["evaluated"])
        self.assertIn("no `updated` timestamp", s["reason"])

    def test_a_project_with_no_event_log_cannot_be_evaluated(self):
        root = build_project()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / ".perry" / "events.jsonl").unlink()
        s = kr(goals(root), "P-O1.1")["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertFalse(s["evaluated"])
        self.assertIn("no event log", s["reason"])
        # And the tally still answers, from the board, rather than reporting
        # two closed tasks as unknown because a derived file is missing.
        self.assertEqual(kr(goals(root), "P-O1.1")["linked_task_completion"],
                         {"total": 2, "done": 2, "dropped": 0, "open": 0,
                          "unknown": 0})

    def test_a_date_only_updated_is_read_as_midnight(self):
        """Errs toward staleness on purpose: a false `recheck this` costs a
        look, a false `this number is fine` costs the number."""
        root = build_project(updated="2026-08-10")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        s = kr(goals(root), "P-O1.1")["current_staleness"]
        self.assertEqual(s["since"], "2026-08-10T00:00:00")
        self.assertTrue(s["stale"], s["reason"])
        self.assertEqual([m["id"] for m in s["moved_tasks"]],
                         ["TASK-001", "TASK-002"])


class TestADanglingEdgeIsNotCountedAsOpen(unittest.TestCase):
    def test_an_id_neither_store_knows_is_unknown(self):
        root = build_project()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        text = (root / "phase" / "001-linkage.md").read_text().replace(
            'tasks: ["TASK-003"]', 'tasks: ["TASK-003", "TASK-999"]')
        (root / "phase" / "001-linkage.md").write_text(text)
        tally = kr(goals(root), "P-O1.2")["linked_task_completion"]
        self.assertEqual(tally, {"total": 2, "done": 0, "dropped": 0,
                                 "open": 1, "unknown": 1})


class TestTheStatusVocabularyIsPinnedToTheSchema(unittest.TestCase):
    """`bin/lib` restates the status enum rather than reading it, so this is
    the pin that stops the two drifting. Three copies of this set already exist
    (`bin/perry_store.py`, `viewer/parsers.py` and now `bin/lib`); a fourth
    unpinned one is how a new status would silently be counted as unknown."""

    def schema(self) -> dict:
        return json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text())

    def test_every_declared_status_is_known_to_the_derivation(self):
        self.assertEqual(set(self.schema()["enums"]["task_status"]),
                         set(lib.TASK_STATUSES))

    def test_the_closed_set_is_the_one_the_store_uses(self):
        sys.path.insert(0, str(PERRY_HOME / "bin"))
        import perry_store
        self.assertEqual(set(perry_store.TERMINAL_STATUSES),
                         set(lib.CLOSED_STATUSES))


if __name__ == "__main__":
    unittest.main()
