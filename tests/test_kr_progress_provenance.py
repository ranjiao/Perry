"""TASK-120 — a KR's `current` is an assertion, and both payloads say so.

**The state this replaces, measured on Perry's own register.** `target` and
`current` are hand-written into the linkage register and nothing derived,
checked or aged them. The two readings a consumer could take were wrong in
opposite directions on the same day:

| KR | target | current | read as | actually |
|---|---|---|---|---|
| `P002-O1-KR1` | 1 | 0 | 0% | all four linked tasks closed |
| `P002-O2-KR2` | 0 | 0 | **met** | 13 row splits and 87 header resolutions still live |

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pinned_phase  # noqa: E402


def own_project(phase: str = pinned_phase.SCORED_PHASE) -> Path:
    """This repository's own project, as a copy with `phase` current. TASK-441.

    `TestBothOfTodaysWrongReadingsFlip` used to read the live checkout, so
    `score-phase 003` clearing `phase/CURRENT` left it no asserted `current`
    to check. `TestTheScoredPhaseIsLoadBearing` shows that with `(none)`.
    """
    return pinned_phase.pinned_copy(__name__, phase)


def asserted_currents(payload: dict) -> list[dict]:
    """The KRs whose `current` a payload reports as asserted. The anti-vacuity
    check and its control both call this."""
    return [k for k in payload["krs"]
            if k["current_provenance"]["state"] == "asserted"]


def goals(root: Path, *argv, tz: str = "") -> dict:
    """`perry-goals list --json`, optionally read in a named zone.

    `tz` sets `TZ` for the CHILD only, which is what makes TASK-144's cases
    reproducible: the rule for a zoneless stamp is "the reading machine's local
    time", so a test of that rule has to name the machine's zone rather than
    inherit whatever the runner happens to be in.
    """
    env = {**os.environ, "TZ": tz} if tz else None
    r = subprocess.run(
        ["python3", str(GOALS), "list", *argv, "--root", str(root), "--json"],
        capture_output=True, text=True, env=env)
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
# `perry/linkage.jsonl` in this repository is the `goals` lane's file and this
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
| P001-O1-KR1 | Rendered from the store | 1 of 1 | |
| P001-O1-KR2 | Readers resolving a header cell | 0 (baseline 5) | |
| P001-O1-KR3 | Never given a number | 0 (baseline unmeasured) | |
"""

#: The graph, as `linkage.jsonl` records. `asserted_at` is per KR and only on
#: a KR that HAS a `current` — `P001-O1-KR3` has neither, which is the case
#: `TestAnUnassertedCurrentIsNullNotZero` reads.
#:
#: **This was `phase/001-linkage.md` with one file-level `updated:` stamp
#: until ADR-019**, and that stamp was what every KR's assertion date was read
#: from. TASK-155 is that defect; the fixture carries the date per KR now
#: because the store does.
def linkage_records(asserted_at: str) -> list[dict]:
    krs = [
        {"kind": "kr", "phase": "001-a-phase", "objective": "O1",
         "id": "P001-O1-KR1", "title": "Rendered from the store",
         "metric": "1 of 1", "target": 1, "current": 0, "stretch": False},
        {"kind": "kr", "phase": "001-a-phase", "objective": "O1",
         "id": "P001-O1-KR2", "title": "Readers resolving a header cell",
         "metric": "0 (baseline 5)", "target": 0, "current": 0,
         "stretch": False},
        {"kind": "kr", "phase": "001-a-phase", "objective": "O1",
         "id": "P001-O1-KR3", "title": "Never given a number",
         "metric": "0 (baseline unmeasured)", "target": 0, "stretch": False},
    ]
    for rec in krs:
        if "current" in rec and asserted_at:
            rec["asserted_at"] = asserted_at
    edges = [("TASK-001", "P001-O1-KR1"), ("TASK-002", "P001-O1-KR1"),
             ("TASK-003", "P001-O1-KR2"), ("TASK-004", "P001-O1-KR3")]
    return [
        {"kind": "objective", "phase": "001-a-phase", "id": "O1",
         "title": "Drive two counts to zero"},
        *krs,
        *({"kind": "edge", "task": task, "kr": kr_id,
           "declared_at": "2026-08-01T00:00:00Z", "actor": "goals",
           "via": "link"} for task, kr_id in edges),
    ]


TASKS = [
    {"id": "TASK-001", "title": "One", "status": "done", "priority": "P1"},
    {"id": "TASK-002", "title": "Two", "status": "done", "priority": "P1"},
    {"id": "TASK-003", "title": "Three", "status": "in_progress",
     "priority": "P1"},
    {"id": "TASK-004", "title": "Four", "status": "not_started",
     "priority": "P1"},
]

#: Every state move predates each KR's `asserted_at`, so the numbers are
#: current until a test appends a move that is not.
#:
#: **Zone-bearing on purpose (TASK-144).** These stamps are days away from the
#: assertion, so no case here turns on the offset — and writing them with a
#: zone is what keeps that true on a runner in any zone. The two shapes the
#: offset actually decides, and the rule the log's 798 zoneless lines are read
#: by, are `TestOneClockAcrossTheOffset` below, which pins `TZ` per read.
EVENTS = [
    {"ts": "2026-08-10T09:00:00Z", "event": "done", "id": "TASK-001",
     "from": "review", "to": "done"},
    {"ts": "2026-08-10T10:00:00Z", "event": "done", "id": "TASK-002",
     "from": "review", "to": "done"},
    {"ts": "2026-08-10T11:00:00Z", "event": "start", "id": "TASK-003",
     "from": "not_started", "to": "in_progress"},
    # A non-state event AFTER the assertion. `next` carries `from`/`to` holding
    # prose, and a staleness check keyed on the event NAME rather than on the
    # value would call every KR below stale on the strength of this line.
    {"ts": "2026-08-20T12:00:00Z", "event": "next", "id": "TASK-003",
     "from": "an old next action", "to": "a new next action"},
]

UPDATED = "2026-08-15T12:00:00Z"


def build_project(updated: str = UPDATED) -> Path:
    """`updated` is now each asserted KR's own `asserted_at` (ADR-019).

    The parameter keeps its name because every caller passes it for the same
    reason it always did — *when the numbers in this register were arrived
    at* — and that is exactly what the field means now. What changed is that
    the value lands on the KR records instead of on a file header, so passing
    `""` means "no KR records an assertion date" rather than "the file has no
    header stamp".
    """
    root = Path(tempfile.mkdtemp())
    (root / ".perry").mkdir()
    (root / ".perry" / "config.md").write_text(
        "# Perry configuration\n\n- State root: .\n")
    (root / ".perry" / "events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in EVENTS))
    (root / "phase").mkdir()
    (root / "phase" / "001-a-phase.md").write_text(PHASE)
    (root / "linkage.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n"
                for r in linkage_records(updated)))
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

    `perry/linkage.jsonl` belongs to the `goals` lane and TASK-120 does
    not write it. So the assertions here are about the SHAPE the payload
    reports, never about a hand-typed number: what changed is that the payload
    can no longer be read as saying either of the two wrong things.
    """

    def own_repo(self) -> dict:
        return goals(own_project())

    def test_no_asserted_current_claims_to_be_a_measurement(self):
        """The `P002-O2-KR2` reading. `target: 0` with `current: 0` read as MET; it
        cannot any more, because nothing in the payload says the zero was
        measured and the payload now says which.

        **Narrowed by TASK-281, and narrowed rather than deleted.** This used to
        read "no `current` in the payload claims to be a measurement", which was
        true because no tool in Perry re-ran a KR's metric. DESIGN-015 § 6 row F
        makes exactly one of them re-run — `P003-O3-KR2`, from `linkage.jsonl`
        and `.perry/events.jsonl` — so the blanket form is now false for a
        reason the project intended.

        What the guard was FOR survives intact and is what is asserted here: a
        number that came out of the register must never be published as though
        something counted it. The exemption is not a free pass — it is exactly
        `lib.COMPUTED_KR_METRICS`, and a KR claiming `measured` while absent
        from that table fails, which is the case this test was written to catch.
        """
        payload = self.own_repo()
        for k in payload["krs"]:
            if k["current_provenance"]["measured"]:
                self.assertIn(
                    k["id"], lib.COMPUTED_KR_METRICS,
                    f"{k['id']}: published as measured data while nothing "
                    f"re-runs its metric")
                continue
            self.assertNotEqual(
                k["current_provenance"]["state"], "measured",
                f"{k['id']}: state `measured` without `measured: true`")
        asserted = asserted_currents(payload)
        self.assertTrue(asserted, "the register carries no asserted `current`")
        for k in asserted:
            self.assertEqual(k["current_provenance"]["source"],
                             "linkage-store")
            # **`asserted_scope` is `kr` or `""`, and never `register` —
            # TASK-155.** It read `register` until ADR-019 because the date
            # came from `phase/<NNN>-linkage.md`'s one file-level `updated:`
            # stamp, shared by every KR in the phase, and the scope was
            # emitted beside it so a reader could not mistake it for this KR's
            # own. The date is per KR now, so the scope says so — and `""`
            # with an empty `asserted_at` is the third answer the payload must
            # keep being able to give: nobody recorded when.
            self.assertIn(k["current_provenance"]["asserted_scope"],
                          ("kr", ""),
                          "an assertion date belongs to a KR, never to a file")
            self.assertEqual(
                bool(k["current_provenance"]["asserted_at"]),
                k["current_provenance"]["asserted_scope"] == "kr",
                f"{k['id']}: `asserted_scope` and `asserted_at` disagree "
                f"about whether a date was recorded")

    def test_a_drive_to_zero_kr_is_not_reported_as_met(self):
        """No key anywhere in a KR row says `met`, `achieved` or `progress`.

        The `2.0` contract removed `progress` for a related reason and this is
        the guard that the provenance work did not quietly reintroduce a
        verdict under another name."""
        for k in self.own_repo()["krs"]:
            for banned in ("progress", "met", "achieved", "percent", "ratio"):
                self.assertNotIn(banned, k, f"{k['id']}: `{banned}` came back")

    def test_a_kr_reading_zero_with_every_task_closed_shows_both(self):
        """The `P002-O1-KR1` reading, reproduced on the fixture (whose own KR is
        `P001-O1-KR1`) so the numbers are fixed.

        `current: 0` against `target: 1` with both linked tasks closed. The
        payload's job is to carry BOTH facts, in different units, and to
        resolve neither: `current` stays 0 because only re-running the metric
        may change it, and the task count says two of two are closed.
        """
        k = kr(goals(self.root), "P001-O1-KR1")
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
        self.assertEqual(set(by_id), {"P001-O1-KR1", "P001-O1-KR2", "P001-O1-KR3"})
        from_goals = kr(goals(self.root), "P001-O1-KR1")
        for block in ("current_provenance", "current_staleness",
                      "linked_task_completion"):
            self.assertEqual(by_id["P001-O1-KR1"][block], from_goals[block],
                             f"{block} differs between the two payloads")


# ── V3 item 2 ─────────────────────────────────────────────────────────────


class TestAnUnassertedCurrentIsNullNotZero(Fixture):
    """`P001-O1-KR3` has `target: 0` and no `current` at all.

    This is the systemic defect stated as a test: an unset `current` defaulting
    to `0.0` makes every drive-to-zero KR read as met on the day it is written,
    before any work starts. Reverting the default reddens this.
    """

    def test_the_number_is_null(self):
        k = kr(goals(self.root), "P001-O1-KR3")
        self.assertEqual(k["target"], 0.0)
        self.assertIsNone(k["current"],
                          "an unwritten `current` came back as a number")

    def test_it_is_reported_as_unasserted_rather_than_as_a_value(self):
        k = kr(goals(self.root), "P001-O1-KR3")
        self.assertEqual(k["current_provenance"]["state"], "unasserted")
        self.assertEqual(k["current_provenance"]["asserted_at"], "")
        self.assertEqual(k["current_provenance"]["source"], "")

    def test_an_unasserted_current_is_never_stale(self):
        """There is no number, so there is nothing that could have aged. The
        reason says which — `stale: false` alone would be indistinguishable
        from a number that has been checked."""
        s = kr(goals(self.root), "P001-O1-KR3")["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertFalse(s["evaluated"])
        self.assertIn("never asserted", s["reason"])

    def test_it_is_named_by_the_conformance_block(self):
        conf = goals(self.root)["conformance"]
        self.assertIn("P001-O1-KR3", conf["krs_without_numbers"])
        self.assertNotIn("P001-O1-KR3", conf["krs_with_stale_current"])

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
        s = kr(goals(self.root), "P001-O1-KR1")["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertTrue(s["evaluated"],
                        "not-stale must mean CHECKED, not `nobody asked`")
        self.assertEqual(s["moved_tasks"], [])
        self.assertEqual(
            s["reason"],
            "no linked task has changed state since 2026-08-15T12:00:00Z")

    def test_closing_one_linked_task_makes_it_stale_and_names_that_task(self):
        before = kr(goals(self.root), "P001-O1-KR2")["current_staleness"]
        self.assertFalse(before["stale"])
        self.assertEqual(
            before["reason"],
            "no linked task has changed state since 2026-08-15T12:00:00Z")

        close_task(self.root, "TASK-003")
        append_event(self.root, {"ts": "2026-08-21T09:10:00Z", "event": "done",
                                 "id": "TASK-003", "from": "in_progress",
                                 "to": "done"})

        after = kr(goals(self.root), "P001-O1-KR2")["current_staleness"]
        self.assertTrue(after["stale"])
        self.assertTrue(after["evaluated"])
        self.assertEqual(
            after["reason"],
            "1 linked task changed state after 2026-08-15T12:00:00Z: "
            "TASK-003 (in_progress → done)")
        self.assertEqual(after["moved_tasks"],
                         [{"id": "TASK-003", "from": "in_progress",
                           "to": "done", "at": "2026-08-21T09:10:00Z"}])

    def test_only_the_kr_whose_task_moved_goes_stale(self):
        """Staleness is per KR, not per register. A register-wide flag would
        make one moved task discredit every number in the file."""
        close_task(self.root, "TASK-003")
        append_event(self.root, {"ts": "2026-08-21T09:10:00Z", "event": "done",
                                 "id": "TASK-003", "from": "in_progress",
                                 "to": "done"})
        payload = goals(self.root)
        self.assertEqual(payload["conformance"]["krs_with_stale_current"],
                         ["P001-O1-KR2"])
        self.assertFalse(kr(payload, "P001-O1-KR1")["current_staleness"]["stale"])

    def test_a_prose_event_after_the_assertion_is_not_a_state_move(self):
        """`next` carries `from`/`to` holding the old and new next action. A
        check keyed on the event NAME rather than on the value would report
        `P001-O1-KR2` stale on the strength of that line, and the fixture has one
        dated after the assertion for exactly this."""
        s = kr(goals(self.root), "P001-O1-KR2")["current_staleness"]
        self.assertFalse(s["stale"], s["reason"])

    def test_perry_state_warns_and_counts_it(self):
        close_task(self.root, "TASK-003")
        append_event(self.root, {"ts": "2026-08-21T09:10:00Z", "event": "done",
                                 "id": "TASK-003", "from": "in_progress",
                                 "to": "done"})
        payload = state(self.root)
        counts = payload["attribution"]["kr_currents"]
        self.assertEqual(counts["stale"], 1)
        self.assertEqual(counts["stale_ids"], ["P001-O1-KR2"])
        self.assertTrue(
            any("P001-O1-KR2" in w and "no longer be trusted" in w
                for w in payload["warnings"]),
            f"no warning named the stale KR: {payload['warnings']}")


class TestWhatCouldNotBeDecidedSaysSo(unittest.TestCase):
    """`stale: false` with `evaluated: false` means NOBODY ASKED.

    Reporting the two as one is the shape this whole row is about: a payload
    that cannot tell a checked number from an unchecked one will be read as
    having checked.
    """

    def test_a_kr_with_no_asserted_at_cannot_be_evaluated(self):
        """An asserted number with no recorded assertion date.

        This read `no `updated` timestamp` until ADR-019, when the file-level
        stamp every KR shared became a per-KR field. The guarantee it buys is
        stronger now and is the reason `asserted_at` is not defaulted: the
        answer to "when was this measured" can be *nobody wrote it down*, and
        that has to be distinguishable from *just now*. Defaulting the field
        to the time of any write — which is what reading the register's
        `updated:` amounted to — makes every number read fresh, which is
        TASK-155."""
        root = build_project(updated="")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        got = kr(goals(root), "P001-O1-KR1")
        self.assertEqual(got["current_provenance"]["state"], "asserted")
        self.assertEqual(got["current_provenance"]["asserted_at"], "")
        self.assertEqual(got["current_provenance"]["asserted_scope"], "")
        s = got["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertFalse(s["evaluated"])
        self.assertIn("no `asserted_at` is recorded", s["reason"])

    def test_one_krs_assertion_date_does_not_move_another_krs(self):
        """TASK-155, as a property rather than as a comment.

        The defect: `phase/<NNN>-linkage.md` carried ONE `updated:` stamp and
        `kr_progress_provenance` read it as every KR's assertion date, so
        re-dating the file — which every `perry-goals link` write did —
        marked every number in the phase freshly asserted. Here `P001-O1-KR2`
        is re-dated past the move that made `P001-O1-KR1` stale, and
        `P001-O1-KR1` must not follow it."""
        root = build_project()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        append_event(root, {"ts": "2026-08-16T09:00:00Z", "event": "done",
                            "id": "TASK-001", "from": "in_progress",
                            "to": "done"})
        before = kr(goals(root), "P001-O1-KR1")["current_staleness"]
        self.assertTrue(before["stale"], before["reason"])

        store = root / "linkage.jsonl"
        rows = [json.loads(line) for line in
                store.read_text().splitlines() if line.strip()]
        for row in rows:
            if row.get("id") == "P001-O1-KR2":
                row["asserted_at"] = "2026-08-30T00:00:00Z"
        store.write_text("".join(json.dumps(r) + "\n" for r in rows))

        after = kr(goals(root), "P001-O1-KR1")["current_staleness"]
        self.assertTrue(after["stale"],
                        "re-dating P001-O1-KR2 marked P001-O1-KR1 fresh — "
                        "one field is carrying two KRs' assertion dates again")
        self.assertEqual(after["since"], before["since"])
        self.assertEqual(
            kr(goals(root), "P001-O1-KR2")["current_provenance"]["asserted_at"],
            "2026-08-30T00:00:00Z")

    def test_a_project_with_no_event_log_cannot_be_evaluated(self):
        root = build_project()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / ".perry" / "events.jsonl").unlink()
        s = kr(goals(root), "P001-O1-KR1")["current_staleness"]
        self.assertFalse(s["stale"])
        self.assertFalse(s["evaluated"])
        self.assertIn("no event log", s["reason"])
        # And the tally still answers, from the board, rather than reporting
        # two closed tasks as unknown because a derived file is missing.
        self.assertEqual(kr(goals(root), "P001-O1-KR1")["linked_task_completion"],
                         {"total": 2, "done": 2, "dropped": 0, "open": 0,
                          "unknown": 0})

    def test_a_date_only_asserted_at_is_read_as_midnight(self):
        """Errs toward staleness on purpose: a false `recheck this` costs a
        look, a false `this number is fine` costs the number."""
        root = build_project(updated="2026-08-10")
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        s = kr(goals(root), "P001-O1-KR1")["current_staleness"]
        self.assertEqual(s["since"], "2026-08-10T00:00:00Z")
        self.assertTrue(s["stale"], s["reason"])
        self.assertEqual([m["id"] for m in s["moved_tasks"]],
                         ["TASK-001", "TASK-002"])


# ── TASK-144: one clock ───────────────────────────────────────────────────


#: The register asserts at this instant. Everything below is placed relative
#: to it, in UTC, and then written in the zone the case is about.
ASSERTED = "2026-08-21T10:04:08Z"


class TestOneClockAcrossTheOffset(unittest.TestCase):
    """The skew, in both of the directions an offset can produce it.

    Measured on the machine that filed TASK-144, which is UTC+8:

        event log   '2026-08-28T02:15:22'    no zone — LOCAL wall clock
        register    '2026-08-21T10:04:08Z'   UTC

    and `current_staleness` compared the two AS TEXT. Every case here spans the
    offset — the answer text-comparison gives is the opposite of the true one —
    because a case inside the offset proves nothing about a clock.

    Each read names its `TZ`, so these run the same on a machine in any zone.
    """

    def project(self) -> Path:
        root = build_project(updated=ASSERTED)
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        return root

    def stale(self, root: Path, tz: str, kr_id: str = "P001-O1-KR2") -> dict:
        return kr(goals(root, tz=tz), kr_id)["current_staleness"]

    def test_the_since_it_compares_against_is_the_registers_own_instant(self):
        """`since` is emitted, so it carries its zone. A payload that publishes
        a zoneless timestamp is this row's defect at the contract boundary."""
        s = self.stale(self.project(), "Asia/Shanghai")
        self.assertEqual(s["since"], "2026-08-21T10:04:08Z")

    def test_an_earlier_move_that_reads_later_in_local_text_is_not_stale(self):
        """**UTC+8, and the direction the text comparison gets wrong here.**

        The move is at `04:04:08Z` — six hours BEFORE the assertion, so the
        number is fine. Written where it happened it reads `12:04:08+08:00`,
        two hours after the register's text, and
        `"2026-08-21T12:04:08" > "2026-08-21T10:04:08"` reported it stale.
        """
        root = self.project()
        close_task(root, "TASK-003")
        append_event(root, {"ts": "2026-08-21T12:04:08+08:00", "event": "done",
                            "id": "TASK-003", "from": "in_progress",
                            "to": "done"})
        s = self.stale(root, "Asia/Shanghai")
        self.assertFalse(
            s["stale"],
            "a task that moved six hours BEFORE the assertion was reported as "
            f"moving after it — the offset, read as text: {s['reason']}")
        self.assertTrue(s["evaluated"])
        self.assertEqual(s["moved_tasks"], [])

    def test_a_later_move_that_reads_earlier_in_local_text_is_stale(self):
        """**UTC-7, and the direction that costs the number rather than a look.**

        The move is at `12:04:08Z` — two hours AFTER the assertion, so the
        number is stale. Written where it happened it reads `05:04:08-07:00`,
        five hours before the register's text, and
        `"2026-08-21T05:04:08" <= "2026-08-21T10:04:08"` reported it FRESH.
        """
        root = self.project()
        close_task(root, "TASK-003")
        append_event(root, {"ts": "2026-08-21T05:04:08-07:00", "event": "done",
                            "id": "TASK-003", "from": "in_progress",
                            "to": "done"})
        s = self.stale(root, "America/Los_Angeles")
        self.assertTrue(
            s["stale"],
            "a task that moved two hours AFTER the assertion was reported "
            f"fresh — the offset, read as text: {s['reason']}")
        self.assertEqual(s["moved_tasks"],
                         [{"id": "TASK-003", "from": "in_progress",
                           "to": "done", "at": "2026-08-21T12:04:08Z"}])

    def test_a_zoneless_entry_is_read_as_the_reading_machines_local_time(self):
        """The rule the log's existing zoneless lines are read by, stated as a
        test rather than only in a docstring: `datetime.now()` wrote them, so
        they hold local wall clock, and ONE line therefore answers differently
        in two zones — which is the cost of not rewriting them, paid visibly."""
        root = self.project()
        close_task(root, "TASK-003")
        append_event(root, {"ts": "2026-08-21T12:04:08", "event": "done",
                            "id": "TASK-003", "from": "in_progress",
                            "to": "done"})
        east = self.stale(root, "Asia/Shanghai")
        self.assertFalse(east["stale"],
                         "read as +08:00 that is 04:04:08Z, before the "
                         f"assertion: {east['reason']}")
        west = self.stale(root, "America/Los_Angeles")
        self.assertTrue(west["stale"],
                        "read as -07:00 that is 19:04:08Z, after the "
                        f"assertion: {west['reason']}")
        self.assertEqual([m["at"] for m in west["moved_tasks"]],
                         ["2026-08-21T19:04:08Z"])

    def test_the_two_writers_stamp_a_zone_and_the_log_stamps_a_local_one(self):
        """The write side of the same decision. The log keeps its LOCAL wall
        clock and gains the offset — so the text of the log goes on rising
        across the lines that predate this — and the register keeps its `Z`."""
        def stamp(fn: str, tz: str) -> str:
            r = subprocess.run(
                ["python3", "-c",
                 "import sys; sys.path.insert(0, sys.argv[1]); import lib; "
                 f"print(lib.{fn}())", str(PERRY_HOME / "bin")],
                capture_output=True, text=True,
                env={**os.environ, "TZ": tz})
            assert r.returncode == 0, r.stderr[-2000:]
            return r.stdout.strip()

        self.assertRegex(stamp("event_stamp", "Asia/Shanghai"),
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")
        self.assertRegex(stamp("event_stamp", "America/Los_Angeles"),
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-0[78]:00$")
        self.assertRegex(stamp("register_stamp", "Asia/Shanghai"),
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_no_tool_stamps_a_zoneless_time_any_more(self):
        """The writers go through `lib`, so there is nowhere else for a naive
        stamp to be minted. A new `datetime.now().isoformat()` in a writer is
        what would put the second shape back into the append-only log."""
        for tool in ("perry-task", "perry-goals"):
            source = (PERRY_HOME / "bin" / tool).read_text()
            self.assertNotIn(
                'datetime.now().isoformat(', source,
                f"bin/{tool} mints a zoneless stamp of its own")

    #: Every way Python has of turning a zone into an answer. A file that
    #: contains one of these is deciding what a timestamp MEANS, and exactly
    #: one file in the tree is allowed to do that.
    ZONE_AWARE = ("astimezone", "timezone.utc", "tzinfo", "utcoffset",
                  'rstrip("Z")', "rstrip('Z')", "utcnow")

    def test_the_converter_has_exactly_one_home(self):
        """**Verification 4, as a search rather than a claim.**

        A second converter is this project's most-paid-for defect: the skew
        TASK-144 removed came back the moment anybody wrote a comparison
        without reading the row. So no file in `bin/` or `viewer/` may contain
        a zone construct at all except `bin/lib/__init__.py`, and inside it
        `ts_moment` is the one function that decides — `ts_key` is its string
        face and calls it.
        """
        home = (PERRY_HOME / "bin" / "lib" / "__init__.py")
        source = home.read_text()
        self.assertEqual(1, source.count("def ts_moment("))
        self.assertEqual(1, source.count("def ts_key("))
        self.assertEqual(1, source.count("def event_stamp("))
        self.assertEqual(1, source.count("def register_stamp("))

        scanned = 0
        for path in sorted((PERRY_HOME / "bin").rglob("*")) + sorted(
                (PERRY_HOME / "viewer").glob("*.py")):
            if (not path.is_file() or path == home
                    or "__pycache__" in path.parts
                    or path.suffix in (".pyc", ".json", ".md")):
                continue
            text = path.read_text(errors="replace")
            if not (text.startswith("#!") or path.suffix == ".py"):
                continue
            scanned += 1
            for token in self.ZONE_AWARE:
                self.assertNotIn(
                    token, text,
                    f"{path.relative_to(PERRY_HOME)} decides what a zone "
                    f"means ({token!r}); `bin/lib § ts_moment` is the one "
                    f"place that may")
        self.assertGreater(scanned, 5, "the scan found almost no tools to read")


class TestADanglingEdgeIsNotCountedAsOpen(unittest.TestCase):
    def test_an_id_neither_store_knows_is_unknown(self):
        root = build_project()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        with open(root / "linkage.jsonl", "a") as fh:
            fh.write(json.dumps({"kind": "edge", "task": "TASK-999",
                                 "kr": "P001-O1-KR2",
                                 "declared_at": "2026-08-01T00:00:00Z",
                                 "actor": "goals", "via": "link"}) + "\n")
        tally = kr(goals(root), "P001-O1-KR2")["linked_task_completion"]
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


class TestThePinnedCopy(pinned_phase.ThePinnedCopyGuards, unittest.TestCase):
    """TASK-441. `own_repo` reads a copy, not the checkout."""

    OWNER = __name__


class TestTheScoredPhaseIsLoadBearing(unittest.TestCase):
    """TASK-441's control. The anti-vacuity line of
    `test_no_asserted_current_claims_to_be_a_measurement` holds because the
    copy has a phase current. In a copy pinned to `(none)`, the register
    publishes no asserted `current`, so the same predicate fails there."""

    def test_with_no_phase_current_no_current_is_asserted(self):
        unpinned = own_project(pinned_phase.NO_PHASE)
        self.assertEqual(pinned_phase.NO_PHASE,
                         pinned_phase.current_phase(unpinned))
        self.assertEqual([], asserted_currents(goals(unpinned)))

    def test_with_the_scored_phase_pinned_some_are(self):
        self.assertTrue(asserted_currents(goals(own_project())))


if __name__ == "__main__":
    unittest.main()
