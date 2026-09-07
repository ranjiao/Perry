"""TASK-281 — `P003-O3-KR2` is counted, not typed, and the count is over the
rows that answered **in their own `add`**.

DESIGN-015 § 6 row F. The KR reads *"rows opened during phase 003 that take a
KR edge or an `unlinked` declaration in the same action as `add`"*, and until
this row its value was prose in `phase/003-linkage.md`'s `metric:` field — a
number a person typed, which cannot be wrong in a way anything detects.

**What this module exists to catch, and it is not the total.** The same-action
clause is an EVENT property, not a store property (DESIGN-015 § 5.2 and § 5.3).
A row added without `--kr` and linked an hour later by a separate `perry-goals
link` call has an `edge` record in `linkage.jsonl` and is in the population, and
it must NOT count. A computation that reads only the store cannot tell that row
from one linked at `add` — it will publish a plausible-looking number for a
different quantity, and every total it prints will look reasonable.

So the central case here (`TheSameActionPropertyIsWhatIsCounted`) puts BOTH
rows in the population deliberately: if the later-linked row were excluded from
the denominator instead of from the numerator, an assertion that it "does not
count" would pass for the wrong reason. `test_both_rows_are_in_the_population`
is the guard on that confound, and
`test_a_store_only_reading_would_count_them_both` states the failure mode as an
assertion rather than as a comment.

**What is deliberately NOT asserted.** No test here pins the live repository's
value. Today it is 0 of 1, and the moment somebody files a row with `--kr` it
is 1 of 2 — a guard that pinned 0.0 would be red for the project succeeding.
The live-repo tests assert SHAPE: that the number is `measured` rather than
`asserted`, and that the two readers publish the same one.

Run: python3 tests/parallel test_same_action_linkage
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
GOALS = PERRY_HOME / "bin" / "perry-goals"
STATE = PERRY_HOME / "bin" / "perry-state"
REGISTER = PERRY_HOME / "perry" / "phase" / "003-linkage.md"
STORE = PERRY_HOME / "perry" / "linkage.jsonl"

sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402

KR = "P003-O3-KR2"


def add_event(task_id: str, *, kr="__absent__", track: str = "main") -> dict:
    """One `add` event.

    `kr="__absent__"` writes NO `kr` key — a row opened before row D's gate
    existed. That is a different fact from `kr=None`, which is the gate running
    and the question going unanswered, and the whole population turns on the
    difference.
    """
    event = {"ts": "2026-09-05T10:00:00Z", "event": "add", "id": task_id,
             "title": task_id, "track": track, "actor": "agent"}
    if kr != "__absent__":
        event["kr"] = kr
    return event


def edge(task_id: str, kr: str, via: str) -> dict:
    return {"kind": "edge", "task": task_id, "kr": kr, "via": via,
            "actor": "agent", "declared_at": "2026-09-05T11:00:00Z"}


def unlinked(task_id: str, via: str) -> dict:
    return {"kind": "unlinked", "task": task_id, "via": via,
            "actor": "agent", "declared_at": "2026-09-05T11:00:00Z"}


# ── the property the row is about ─────────────────────────────────────────


class TheSameActionPropertyIsWhatIsCounted(unittest.TestCase):
    """Two rows, both asked, answered in different actions.

    `TASK-901` was linked by its own `add`. `TASK-902` was added under the gate
    without `--kr` — so its event carries `kr: null` — and linked an hour later
    by `perry-goals link`, which writes `via: "link"`. Both are in the
    population. Only the first answered in the action the KR names.
    """

    def setUp(self):
        self.events = [add_event("TASK-901", kr="P003-O1-KR1"),
                       add_event("TASK-902", kr=None)]
        self.records = [edge("TASK-901", "P003-O1-KR1", "add"),
                        edge("TASK-902", "P003-O1-KR1", "link")]
        self.m = lib.same_action_linkage(self.records, self.events)

    def test_both_rows_are_in_the_population(self):
        """The confound guard, and it runs FIRST.

        If `TASK-902` were merely absent from the denominator, every other
        assertion in this class would pass while the computation was blind to
        the property it is supposed to measure.
        """
        self.assertEqual(sorted(self.m["population"]),
                         ["TASK-901", "TASK-902"])
        self.assertEqual(self.m["denominator"], 2)

    def test_the_row_linked_in_its_add_counts(self):
        self.assertIn("TASK-901", self.m["linked_at_add"])

    def test_the_row_linked_by_a_later_separate_call_does_not_count(self):
        self.assertNotIn("TASK-902", self.m["linked_at_add"])
        self.assertNotIn("TASK-902", self.m["declared_unlinked_at_add"])
        self.assertIn("TASK-902", self.m["never_answered"])

    def test_the_number_is_one_of_two(self):
        self.assertEqual(self.m["numerator"], 1)
        self.assertEqual(self.m["denominator"], 2)
        self.assertEqual(self.m["current"], 50.0)

    def test_a_normally_linked_row_is_not_reported_as_a_broken_transaction(self):
        """Closes mutation M02. `TASK-902`'s edge is `via: "link"` — an
        ordinary later link, not a half-landed `add`. Accepting any `via` into
        the at-add edge set left every one of this class's other assertions
        green while turning routine linking into a false integrity alarm,
        because `store_edge_without_event` is the only thing that set feeds."""
        self.assertEqual(self.m["store_edge_without_event"], [])

    def test_a_store_only_reading_would_count_them_both(self):
        """The failure mode, stated as an assertion.

        Both rows hold an `edge` record naming the same KR. A computation that
        answered from `linkage.jsonl` alone would see two linked rows out of
        two and publish 100% — a number that looks right and measures whether
        the rows were EVER linked, which is not what the KR asks.
        """
        store_only = [r["task"] for r in self.records if r["kind"] == "edge"]
        self.assertEqual(sorted(store_only), ["TASK-901", "TASK-902"])
        self.assertNotEqual(self.m["current"], 100.0)


class AnUnlinkedDeclarationIsAnAnswerWhenItsOwnAddMadeIt(unittest.TestCase):
    """The numerator's second half. "No KR" is an answer; when it was given
    still decides whether it counts."""

    def test_declared_unlinked_by_its_own_add_counts(self):
        m = lib.same_action_linkage([unlinked("TASK-903", "add")],
                                    [add_event("TASK-903", kr=None)])
        self.assertEqual(m["declared_unlinked_at_add"], ["TASK-903"])
        self.assertEqual((m["numerator"], m["denominator"]), (1, 1))

    def test_the_same_declaration_swept_in_later_does_not(self):
        """`via: "link"` — `perry-goals link --unlinked`, in a batch, after the
        fact. This is how all 100 of the live store's `unlinked` records were
        made, and it is exactly what the KR does not credit."""
        m = lib.same_action_linkage([unlinked("TASK-904", "link")],
                                    [add_event("TASK-904", kr=None)])
        self.assertEqual(m["declared_unlinked_at_add"], [])
        self.assertEqual((m["numerator"], m["denominator"]), (0, 1))


# ── the population ────────────────────────────────────────────────────────


class ThePopulationIsTheGateAndNotThePhasesWholeIntake(unittest.TestCase):
    """`phase/003-storage-code.md § Definition of Done` item 5, restated
    2026-08-31: *every `main`-track row opened after the gate lands*. Row D
    changed the shape of the `add` event, and that shape change is the only
    mark of the gate that lives in the data this KR is computed from."""

    def test_a_row_opened_before_the_gate_is_not_in_the_denominator(self):
        m = lib.same_action_linkage([], [add_event("TASK-905")])
        self.assertEqual(m["population"], [])
        self.assertIsNone(m["current"])

    def test_the_gate_signature_is_the_key_and_not_its_value(self):
        """`kr: null` IS the gate: § 5.2's "record and warn". Reading the
        population with `.get("kr")` instead of `"kr" in event` would collapse
        every unanswered row into the pre-gate set and leave the denominator
        holding only the rows that already count — which reports 100% for a
        gate nobody is answering."""
        m = lib.same_action_linkage([], [add_event("TASK-906", kr=None)])
        self.assertEqual(m["population"], ["TASK-906"])
        self.assertEqual(m["current"], 0.0)

    def test_a_row_off_the_main_track_is_not_counted(self):
        m = lib.same_action_linkage(
            [], [add_event("TASK-907", kr=None, track="side")])
        self.assertEqual(m["population"], [])

    def test_a_row_is_counted_once_however_many_add_events_it_has(self):
        m = lib.same_action_linkage(
            [], [add_event("TASK-908", kr=None), add_event("TASK-908", kr=None)])
        self.assertEqual(m["population"], ["TASK-908"])
        self.assertEqual(m["denominator"], 1)


# ── the control ───────────────────────────────────────────────────────────


class APhaseWithNoRowsOpenedHasNoDenominator(unittest.TestCase):
    """The control the spec asks for. Nothing opened under the gate is an
    ABSENCE, and both of the numbers an absence tempts you into — 0 because
    nothing is linked, 100 because nothing is unlinked — are inventions."""

    def setUp(self):
        self.m = lib.same_action_linkage([], [])

    def test_it_reports_no_denominator(self):
        self.assertEqual(self.m["denominator"], 0)

    def test_it_does_not_divide_by_zero(self):
        self.assertIsNone(self.m["current"])

    def test_it_does_not_report_one_hundred_percent(self):
        self.assertNotEqual(self.m["current"], 100.0)

    def test_it_does_not_report_zero_percent_either(self):
        self.assertNotEqual(self.m["current"], 0.0)

    def test_it_is_still_measured_and_not_unasserted(self):
        """"Measured to have no denominator" and "nobody typed a number" are
        different facts. If an empty population reported `unasserted`, the KR
        would be indistinguishable from the five that are still typed."""
        p = lib.kr_progress_provenance(None, [], computed=self.m)
        self.assertEqual(p["current_provenance"]["state"], "measured")
        self.assertTrue(p["current_provenance"]["measured"])
        self.assertIsNone(p["current"])

    def test_a_no_denominator_answer_says_why(self):
        self.assertIn("no denominator", self.m["reason"])


class AMeasuredNumberCannotGoStale(unittest.TestCase):
    """Closes mutation M15. Nothing asserted the staleness block a computed KR
    gets, so flipping it to `evaluated: False` — "we could not tell whether
    this number is still good" — was green.

    It is not a cosmetic field. `bin/perry-state § stale_krs` counts KRs whose
    staleness says `stale`, and the register-wide staleness machinery exists
    because an ASSERTED number ages between the day it was typed and the day
    it is read. A recomputed number has no such interval, and saying "could
    not be evaluated" about it invites exactly the recheck it does not need.
    """

    def setUp(self):
        m = lib.same_action_linkage(
            [], [add_event("TASK-910", kr="P003-O1-KR1")])
        self.p = lib.kr_progress_provenance(
            None, [], register_updated="2026-09-03T06:06:45Z", computed=m)

    def test_the_question_was_answered_not_skipped(self):
        self.assertTrue(self.p["current_staleness"]["evaluated"])

    def test_it_is_not_stale(self):
        self.assertFalse(self.p["current_staleness"]["stale"])

    def test_the_reason_names_recomputation(self):
        self.assertIn("recomputed on every read",
                      self.p["current_staleness"]["reason"])

    def test_it_carries_no_assertion_date_to_age_from(self):
        self.assertEqual(self.p["current_provenance"]["asserted_at"], "")
        self.assertEqual(self.p["current_provenance"]["asserted_scope"], "")
        self.assertEqual(self.p["current_staleness"]["since"], "")


# ── the half-landed transaction ───────────────────────────────────────────


class AStoreEdgeWhoseEventDisagreesIsSurfacedNotCounted(unittest.TestCase):
    """§ 5.3 writes the edge and the event under one `commit()`. If they ever
    disagree, the store says a row was linked at `add` and the event says it
    was not — and folding that into the numerator would let a desync RAISE the
    score that is supposed to expose it."""

    def setUp(self):
        self.m = lib.same_action_linkage(
            [edge("TASK-909", "P003-O1-KR1", "add")],
            [add_event("TASK-909", kr=None)])

    def test_it_is_not_counted(self):
        self.assertEqual(self.m["numerator"], 0)

    def test_it_is_named(self):
        self.assertEqual(self.m["store_edge_without_event"], ["TASK-909"])


# ── the register, and the two readers ─────────────────────────────────────


LINKAGE_DOC = """---
linkage: 1
phase: "003-fixture"
updated: "2026-09-03T06:06:45Z"
objectives:
  - id: O3
    title: "A fixture objective"
    krs:
      - id: P003-O3-KR2
        title: "Rows that answered in their own `add`"
        metric: "computed; see bin/lib § same_action_linkage"
        stretch: false
        linked: "KR-O2.3"
        tasks: []
unlinked: ["TASK-911"]
agents: []
projects: []
---

# Fixture register
"""


class PerryStateReallyReadsTheStore(unittest.TestCase):
    """Closes mutation M13, and the mutation is worth recording.

    Blanking `perry-state`'s `load_linkage_store` call was GREEN against the
    live repository — because this project has zero `unlinked` records with
    `via: "add"` today, so the store contributes nothing to the live number and
    the whole numerator comes from the event log. Every live-repo assertion in
    this module passed while half the computation's inputs were unplugged.

    That is the shape the spec warns about: a number that looks right because
    the data happens not to exercise the path. The fix is a project where the
    store's half is the ONLY thing that can answer — one row, its `add` event
    carrying `kr: null`, and its `unlinked` declaration made by that same
    `add`. Read correctly the KR is 1 of 1; with the store unplugged it is 0.
    """

    def setUp(self):
        import tempfile, shutil
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n")
        (self.root / ".perry" / "events.jsonl").write_text(
            json.dumps(add_event("TASK-911", kr=None)) + "\n")
        (self.root / "phase").mkdir()
        (self.root / "phase" / "003-fixture.md").write_text(
            "# Phase #003 — fixture\n\n> **Started**: 2026-08-28\n")
        (self.root / "phase" / "003-linkage.md").write_text(LINKAGE_DOC)
        (self.root / "phase" / "CURRENT").write_text("003-fixture\n")
        (self.root / "OKR.md").write_text(
            "# OKR — fixture\n\n## Mission\n\nShip it.\n\n---\n\n## v1: 2026-08-01\n")
        (self.root / "linkage.jsonl").write_text(
            json.dumps({"kind": "kr", "phase": "003-fixture", "objective": "O3",
                        "id": KR, "title": "Rows that answered in their own `add`",
                        "stretch": False, "linked": "KR-O2.3"}) + "\n"
            + json.dumps(unlinked("TASK-911", "add")) + "\n")
        (self.root / "tasks.jsonl").write_text(
            json.dumps({"id": "TASK-911", "title": "a row",
                        "status": "not_started", "priority": "P1",
                        "track": "main"}) + "\n")
        (self.root / "BOARD.md").write_text(
            "# Board\n\n## P1\n\n| ID | Task | Owner | Status |\n"
            "|----|------|-------|--------|\n"
            "| TASK-911 | a row |  | not_started |\n")

    def kr(self) -> dict:
        r = subprocess.run(
            ["python3", str(STATE), "--root", str(self.root),
             "--section", "linkage"],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError(f"perry-state exited {r.returncode}: "
                                 f"{r.stderr[-800:]}")
        payload = json.loads(r.stdout)
        for o in (payload.get("linkage") or {}).get("objectives", []):
            for k in o.get("krs", []):
                if k["id"] == KR:
                    return k
        raise AssertionError(f"{KR} missing: {r.stdout[:400]}")

    def test_the_store_only_answer_reaches_the_payload(self):
        k = self.kr()
        self.assertEqual(k["current_measurement"]["declared_unlinked_at_add"],
                         ["TASK-911"])
        self.assertEqual(k["current"], 100.0)

    def test_the_denominator_came_from_the_event_log(self):
        """Both files, not one. The row is in the population because its `add`
        event carries the gate's `kr` key — nothing in the store says so."""
        self.assertEqual(self.kr()["current_measurement"]["denominator"], 1)


class TheRegisterNoLongerAssertsIt(unittest.TestCase):
    def test_the_kr_record_carries_no_current(self):
        records = [json.loads(l) for l in
                   STORE.read_text().splitlines() if l.strip()]
        rec = next(r for r in records
                   if r.get("kind") == "kr" and r.get("id") == KR)
        self.assertNotIn("current", rec)

    def test_the_metric_prose_asserts_no_current_value(self):
        """The prose that used to carry the number is gone from the live
        register. Asserted by its exact former text, so a re-introduction is
        caught rather than a paraphrase being argued about."""
        text = REGISTER.read_text()
        old = "100% of rows added this phase (baseline 0 — the edge is a separate step nobody takes)"
        # The old sentence survives only inside the new prose's own account of
        # what it replaced, which is quoted in backticks.
        self.assertNotIn(f'metric: "{old}"', text)
        self.assertIn("NO CURRENT VALUE IS WRITTEN HERE", text)


class TheDispatchTableIsTheWholeOfWhatIsComputed(unittest.TestCase):
    """The Bound. Five of the six KRs stay asserted; whether they should also
    be computed is TASK-231's question."""

    def test_exactly_one_kr_is_computed(self):
        self.assertEqual(list(lib.COMPUTED_KR_METRICS), [KR])

    def test_an_uncomputed_kr_dispatches_to_nothing(self):
        self.assertIsNone(lib.computed_kr_current(
            "P003-O1-KR1", linkage_records=[], events=[]))

    def test_an_uncomputed_kr_keeps_its_asserted_provenance(self):
        p = lib.kr_progress_provenance(6.0, [], register_updated="2026-09-03T06:06:45Z")
        self.assertEqual(p["current_provenance"]["state"], "asserted")
        self.assertFalse(p["current_provenance"]["measured"])
        self.assertNotIn("current", p)


class BothReadersPublishTheOneNumber(unittest.TestCase):
    """The deliverable's last clause: *the two cannot disagree because only one
    exists*. `perry-state` and `perry-goals` both publish a KR's `current`, and
    before this row a computation added to one of them would have left the
    other reporting the register.

    Shape, never value: the live number moves the moment a row is filed with
    `--kr`, and a guard that pinned it would be red for the project working.
    """

    @staticmethod
    def _run(argv: list[str]) -> dict:
        r = subprocess.run(["python3", *argv], capture_output=True, text=True,
                           cwd=str(PERRY_HOME))
        if r.returncode != 0:
            raise AssertionError(f"{argv} exited {r.returncode}: {r.stderr[-800:]}")
        return json.loads(r.stdout)

    def state_kr(self) -> dict:
        payload = self._run([str(STATE), "--root", str(PERRY_HOME),
                             "--section", "linkage"])
        for o in (payload.get("linkage") or {}).get("objectives", []):
            for k in o.get("krs", []):
                if k["id"] == KR:
                    return k
        raise AssertionError(f"{KR} missing from perry-state linkage section")

    def goals_kr(self) -> dict:
        payload = self._run([str(GOALS), "list", "--root", str(PERRY_HOME),
                             "--json"])
        for k in payload.get("krs", []):
            if k["id"] == KR:
                return k
        raise AssertionError(f"{KR} missing from perry-goals krs")

    def test_perry_state_reports_it_measured(self):
        k = self.state_kr()
        self.assertEqual(k["current_provenance"]["state"], "measured")
        self.assertTrue(k["current_provenance"]["measured"])

    def test_perry_goals_reports_it_measured(self):
        k = self.goals_kr()
        self.assertEqual(k["current_provenance"]["state"], "measured")
        self.assertTrue(k["current_provenance"]["measured"])

    def test_the_two_agree_on_the_number(self):
        self.assertEqual(self.state_kr()["current"], self.goals_kr()["current"])

    def test_the_number_matches_recomputing_it_here(self):
        """The published number against this module's own read of the two
        files. A payload that computed something else — or that fell back to
        the register — differs here."""
        sys.path.insert(0, str(PERRY_HOME / "viewer"))
        import parsers as P  # noqa: E402
        records = P.load_linkage_store(PERRY_HOME / "perry")
        events = [json.loads(l) for l in
                  (PERRY_HOME / ".perry" / "events.jsonl")
                  .read_text(errors="replace").splitlines() if l.strip()]
        expected = lib.same_action_linkage(records, events)
        self.assertEqual(self.state_kr()["current"], expected["current"])

    def test_the_other_five_krs_are_not_reported_measured(self):
        payload = self._run([str(STATE), "--root", str(PERRY_HOME),
                             "--section", "linkage"])
        others = [k for o in (payload.get("linkage") or {}).get("objectives", [])
                  for k in o.get("krs", []) if k["id"] != KR]
        self.assertTrue(others, "no other KRs found — the Bound cannot be checked")
        for k in others:
            self.assertFalse(k["current_provenance"]["measured"],
                             f"{k['id']} became measured; the Bound is one KR")


# ══ ROUND 2 ═══════════════════════════════════════════════════════════════
#
# The V4 FAIL. Round 1 shipped a numerator that read the EVENT alone:
#
#     if event.get("kr") is not None:
#         linked.append(tid)
#
# Two things followed, both reproduced on real data before anything was
# changed, and every guard below reddens on an input a user can type.


class TheNumeratorTakesBothHalvesOrNeither(unittest.TestCase):
    """§ 5.3 writes the store edge and the `add` event under ONE `commit()`,
    so "linked in the same action" means **the transaction landed whole**.

    Either half alone is a desync, and the direction matters. Round 1 counted
    the event's half alone, so a desync RAISED the score; a desync must only
    ever be able to lower it, because the KR exists to expose exactly this.
    """

    def test_an_event_claiming_a_kr_with_no_store_edge_does_not_count(self):
        m = lib.same_action_linkage([], [add_event("TASK-920",
                                                   kr="P003-O1-KR1")])
        self.assertEqual(m["linked_at_add"], [])
        self.assertEqual((m["numerator"], m["denominator"]), (0, 1))

    def test_it_is_surfaced_rather_than_silently_dropped(self):
        """Not counted is not enough — an unexplained absence is how a
        half-landed transaction goes unnoticed for a phase."""
        m = lib.same_action_linkage([], [add_event("TASK-920",
                                                   kr="P003-O1-KR1")])
        self.assertEqual(m["event_kr_without_store_edge"], ["TASK-920"])

    def test_both_halves_present_is_what_counts(self):
        m = lib.same_action_linkage(
            [edge("TASK-922", "P003-O1-KR1", "add")],
            [add_event("TASK-922", kr="P003-O1-KR1")])
        self.assertEqual(m["linked_at_add"], ["TASK-922"])
        self.assertEqual((m["numerator"], m["denominator"]), (1, 1))
        self.assertEqual(m["event_kr_without_store_edge"], [])
        self.assertEqual(m["store_edge_without_event"], [])

    def test_a_store_edge_naming_a_different_kr_is_not_corroboration(self):
        """The third disagreement, and the one easiest to wave through: both
        files have a record for the row, so a membership-only check passes
        while the two name different KRs."""
        m = lib.same_action_linkage(
            [edge("TASK-921", "P003-O1-KR2", "add")],
            [add_event("TASK-921", kr="P003-O1-KR1")])
        self.assertEqual(m["linked_at_add"], [])
        self.assertIn("TASK-921", m["event_kr_without_store_edge"])
        self.assertIn("TASK-921", m["store_edge_without_event"])

    def test_a_padded_kr_on_the_event_still_matches_the_stripped_record(self):
        """`linkage_edge_change` strips before writing, so a reader that did
        not strip would fail to match its own writer's output and report every
        padded `--kr` as a desync."""
        m = lib.same_action_linkage(
            [edge("TASK-923", "P003-O1-KR1", "add")],
            [add_event("TASK-923", kr="  P003-O1-KR1  ")])
        self.assertEqual(m["linked_at_add"], ["TASK-923"])


class WhitespaceCannotRaiseTheNumber(unittest.TestCase):
    """**The V4 FAIL, stated as an assertion, on the input that produced it.**

    `perry-task add --kr "   "` wrote a truthy `kr` onto the event while
    `linkage_edge_change` stripped it to `""` and wrote no edge. Measured on
    `339f553` against the live repository: **15.38% (2/13) → 21.43% (3/14)**
    with zero records added to the store and no warning printed.

    The row is still in the POPULATION — its `add` event carries the gate's
    `kr` key, so the gate did run on it — which is why the number must go
    DOWN. A guard that only checked "it is not in the numerator" would also
    pass if the row had been dropped from the denominator, and that is the
    confound this class is shaped around.
    """

    BASE_EVENTS = [add_event("TASK-930", kr="P003-O1-KR1"),
                   add_event("TASK-931", kr=None)]
    BASE_RECORDS = [edge("TASK-930", "P003-O1-KR1", "add")]
    PROBE = add_event("TASK-932", kr="   ")

    def setUp(self):
        self.before = lib.same_action_linkage(self.BASE_RECORDS,
                                              self.BASE_EVENTS)
        self.after = lib.same_action_linkage(self.BASE_RECORDS,
                                             self.BASE_EVENTS + [self.PROBE])

    def test_the_baseline_is_what_it_looks_like(self):
        self.assertEqual(self.before["current"], 50.0)

    def test_the_probe_row_is_in_the_population(self):
        """The confound guard. If typing spaces merely removed the row from
        the denominator, every other assertion here would pass while the
        number was still moving on an input nobody should be able to move it
        with."""
        self.assertIn("TASK-932", self.after["population"])
        self.assertEqual(self.after["denominator"],
                         self.before["denominator"] + 1)

    def test_it_lowers_the_number_it_used_to_raise(self):
        self.assertLess(self.after["current"], self.before["current"])

    def test_it_adds_nothing_to_the_numerator(self):
        self.assertEqual(self.after["numerator"], self.before["numerator"])
        self.assertNotIn("TASK-932", self.after["linked_at_add"])

    def test_the_row_is_named_as_a_desync(self):
        self.assertIn("TASK-932", self.after["event_kr_without_store_edge"])


class TheStoreIsLoadBearingOnTheLiveNumber(unittest.TestCase):
    """**M13, closed against production behaviour instead of a fixture.**

    Round 1 closed M13 — `perry-state` stops reading the store — with
    `PerryStateReallyReadsTheStore`, whose fixture holds
    `{"kind":"unlinked","via":"add"}`. **No writer in Perry can produce that
    record** (`UNLINKED_AT_ADD_HAS_NO_WRITER`), so the mutation reddened
    against a project Perry cannot create while production behaviour was
    untouched: on the live repository the whole numerator came from the event
    log, and unplugging the store moved nothing. Measured: deleting every
    `via: "add"` record — 123 to 121, which `perry-tasks linkage-write
    --from-register` does as a matter of course — left the published figure at
    exactly 15.38%.

    These two run against the LIVE repository, where the `edge` half is
    reachable and populated, and they are the reason the same mutation now
    reddens on real data.
    """

    def live(self):
        sys.path.insert(0, str(PERRY_HOME / "viewer"))
        import parsers as P  # noqa: E402
        records = P.load_linkage_store(PERRY_HOME / "perry")
        events = [json.loads(l) for l in
                  (PERRY_HOME / ".perry" / "events.jsonl")
                  .read_text(errors="replace").splitlines() if l.strip()]
        return records, events

    def test_stripping_the_store_empties_the_numerator(self):
        """Not vacuous, and not pinned to today's data: under a computation
        that reads both files this holds for ANY store, because nothing can be
        linked-at-add without a `via: "add"` edge. Under a computation that
        answers from the event log it fails the moment one row is filed with
        `--kr` — which is the whole of M13."""
        records, events = self.live()
        without = lib.same_action_linkage(
            [r for r in records if r.get("via") != "add"], events)
        self.assertEqual(without["linked_at_add"], [])
        self.assertEqual(without["numerator"], 0)

    def test_every_counted_row_is_backed_by_a_store_edge(self):
        """Shape, never value — the live number moves when a row is filed."""
        records, events = self.live()
        m = lib.same_action_linkage(records, events)
        backed = {str(r.get("task") or "") for r in records
                  if r.get("kind") == "edge" and r.get("via") == "add"}
        for tid in m["linked_at_add"]:
            self.assertIn(tid, backed,
                          f"{tid} is in the numerator with no `via: \"add\"` "
                          f"edge — the numerator is answering from the event "
                          f"log alone")


class TheDesyncDetectorIsNotGatedOnTheEventItDetects(unittest.TestCase):
    """**`store_edge_without_event` used to be gated on the `add` event.**

        if tid in seen and tid not in set(linked)

    `seen` is the population, and the population is built FROM the `add`
    event — so the detector built to find "the store landed and the event did
    not" could only see rows whose event had landed. `TASK-279`'s V4 drove the
    crash matrix to seven points and found this reporting empty at two of
    them: the event append is `open(..., "a")`, not a canonical rename, so the
    shipped harness never kills there and a crash at that point leaves the
    store's half alone in the tree.

    Three shapes, of which only the middle one was ever reported.
    """

    def test_a_store_edge_with_no_add_event_at_all_is_reported(self):
        """Shape A — the crash destroyed the event outright."""
        m = lib.same_action_linkage(
            [edge("TASK-701", "P003-O1-KR1", "add")],
            [add_event("TASK-700", kr=None)])
        self.assertEqual(m["store_edge_without_event"], ["TASK-701"])

    def test_a_store_edge_whose_event_carries_kr_null_is_reported(self):
        """Shape B — the one the old gate could see."""
        m = lib.same_action_linkage(
            [edge("TASK-702", "P003-O1-KR1", "add")],
            [add_event("TASK-702", kr=None)])
        self.assertEqual(m["store_edge_without_event"], ["TASK-702"])

    def test_a_store_edge_whose_event_lost_its_kr_key_is_reported(self):
        """Shape C — the event survived truncated. The population gate
        (`"kr" not in event`) dropped it before the detector ever ran."""
        m = lib.same_action_linkage(
            [edge("TASK-703", "P003-O1-KR1", "add")],
            [add_event("TASK-703")])
        self.assertEqual(m["store_edge_without_event"], ["TASK-703"])

    def test_a_matched_pair_is_not_reported(self):
        """The control. A detector that fires on everything is not a
        detector, and un-gating is exactly the change that could cause it."""
        m = lib.same_action_linkage(
            [edge("TASK-704", "P003-O1-KR1", "add")],
            [add_event("TASK-704", kr="P003-O1-KR1")])
        self.assertEqual(m["store_edge_without_event"], [])
        self.assertEqual(m["linked_at_add"], ["TASK-704"])

    def test_a_later_link_is_not_reported_as_a_desync(self):
        """`via: "link"` is the ordinary path, not a half-landed
        transaction. This is round 1's M02, kept."""
        m = lib.same_action_linkage(
            [edge("TASK-705", "P003-O1-KR1", "link")],
            [add_event("TASK-705", kr=None)])
        self.assertEqual(m["store_edge_without_event"], [])


class TheUnlinkedAtAddPathHasNoWriter(unittest.TestCase):
    """**The honest statement, pinned to the code rather than to today's data.**

    `same_action_linkage`'s second numerator path wants
    `{"kind":"unlinked","via":"add"}`. Nothing in Perry writes one: `via` is a
    hardcoded literal at all three writers of the store — `perry-task
    § linkage_edge_change` writes `"add"` on `edge` records ONLY,
    `perry-goals § linkage_store_text` and `perry-tasks
    § LINKAGE_IMPORT_VIA` both write `"link"` — there is no `--via` flag, and
    there is no `perry-task add --unlinked` for the declaration to be made by.

    Round 1 read that emptiness as a fact about **today's data** (*"this
    project has zero such records today"*). It is a fact about the **code**,
    and the difference is why M13's closure did not reach production. So the
    claim is asserted BEHAVIOURALLY here — by driving the writer and the CLI —
    rather than by grepping for a literal, and it reddens the day somebody
    implements the flag `DESIGN-015 § 5.5` asks for.
    """

    def test_the_constant_and_the_measurement_agree(self):
        self.assertTrue(lib.UNLINKED_AT_ADD_HAS_NO_WRITER)
        m = lib.same_action_linkage([], [add_event("TASK-940", kr=None)])
        self.assertFalse(m["declared_unlinked_at_add_reachable"])

    def test_the_only_via_add_writer_emits_edge_records_only(self):
        """Driven, not grepped. `linkage_edge_change` is the one site that
        writes `via: "add"`; ask it for a record and look at the `kind`."""
        task = _perry_task()
        import tempfile, shutil
        d = Path(tempfile.mkdtemp(prefix="perry-unlinked-writer-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "linkage.jsonl").write_text("")
        change = task.linkage_edge_change(
            d, {"event": "add", "id": "TASK-941", "kr": "P003-O1-KR1",
                "actor": "agent"})
        self.assertIsNotNone(change, "the one via:add writer wrote nothing")
        self.assertEqual(change[2]["kind"], "edge")
        self.assertEqual(change[2]["via"], "add")

    def test_an_add_with_no_kr_writes_no_record_at_all(self):
        """The other half of the same fact: there is no branch in which the
        `via: "add"` writer emits an `unlinked` record. A row that answers
        "no KR" at `add` produces nothing for the store to hold."""
        task = _perry_task()
        import tempfile, shutil
        d = Path(tempfile.mkdtemp(prefix="perry-unlinked-writer-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "linkage.jsonl").write_text("")
        self.assertIsNone(task.linkage_edge_change(
            d, {"event": "add", "id": "TASK-942", "kr": None,
                "actor": "agent"}))

    def test_perry_task_add_has_no_unlinked_flag(self):
        """The CLI half, through the real binary. When this goes red the flag
        exists, `UNLINKED_AT_ADD_HAS_NO_WRITER` has stopped being true, and
        the constant's comment has to be rewritten rather than the test
        relaxed."""
        d = _fixture_project(self)
        r = _add(d, "a probe row", "--unlinked")
        self.assertNotEqual(r.returncode, 0,
                            "`perry-task add --unlinked` was accepted; the "
                            "unlinked-at-add path now has a writer")
        # The REASON, not just the exit code — otherwise this passes for any
        # broken fixture, which is the same green-for-the-wrong-reason this
        # module exists to avoid. The control is the sibling test below, which
        # files a row through the same fixture and expects exit 0.
        self.assertIn("unknown argument '--unlinked'", r.stdout + r.stderr)

    def test_the_fixture_can_actually_file_a_row(self):
        """The control on the test above. If `_fixture_project` ever stopped
        producing a usable project, `--unlinked` would still be 'rejected' and
        the reachability claim would rot green."""
        d = _fixture_project(self)
        self.assertEqual(_add(d, "a control row").returncode, 0)

    def test_the_second_numerator_path_is_still_wired(self):
        """Left connected on purpose, so it starts counting on its own the
        day a writer appears. This is the ONE assertion in this module that
        rests on a record Perry cannot produce, and it is labelled as such
        rather than being read as evidence about the live number."""
        m = lib.same_action_linkage([unlinked("TASK-943", "add")],
                                    [add_event("TASK-943", kr=None)])
        self.assertEqual(m["declared_unlinked_at_add"], ["TASK-943"])


# ── the writer: `--kr` is checked before it is stamped on an event ─────────


def _perry_task():
    """`bin/perry-task` as a module."""
    import importlib.machinery
    import importlib.util
    sys.path.insert(0, str(PERRY_HOME / "bin"))
    loader = importlib.machinery.SourceFileLoader(
        "perry_task_under_test", str(PERRY_HOME / "bin" / "perry-task"))
    spec = importlib.util.spec_from_loader("perry_task_under_test", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def _fixture_project(case: unittest.TestCase) -> Path:
    """A throwaway copy of `tests/fixtures/sample-project`."""
    import tempfile, shutil
    d = Path(tempfile.mkdtemp(prefix="perry-kr-arg-")) / "project"
    shutil.copytree(PERRY_HOME / "tests" / "fixtures" / "sample-project", d)
    case.addCleanup(shutil.rmtree, d.parent, ignore_errors=True)
    return d


def _add(d: Path, title: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "add",
         "--root", str(d), "--title", title, "--deliverable", "an artifact",
         "--verification", "a falsifiable check somebody else can run",
         "--summary", "One sentence of plain language for a reader who was "
                      "not in the conversation that filed it.", *extra],
        capture_output=True, text=True, cwd=str(PERRY_HOME))


class ABlankKrIsRefusedBeforeItReachesTheEvent(unittest.TestCase):
    """**The writer half of the same defect, end to end through the CLI.**

    `bin/lib.same_action_linkage` now refuses to count a row the store does
    not back, so a blank `--kr` can no longer move the number. But a writer
    that stamps onto an event a value its own store-writer will silently
    discard is a desync generator whatever the reader does, and the fix
    belongs at the write.

    **Refused rather than warned**, and the axis is the flag's PRESENCE.
    Omitting `--kr` still files the row and still warns — this does NOT make
    `--kr` mandatory, which is a decision `DESIGN-015 § 5.2` did not take —
    and `test_omitting_the_flag_still_files_the_row_and_warns` is the guard
    on that, because a refusal that also broke the no-flag path would have
    quietly made the flag required.
    """

    def setUp(self):
        self.d = _fixture_project(self)
        self.events = self.d / ".perry" / "events.jsonl"
        self.before = (self.events.read_text() if self.events.exists() else "")

    def test_a_whitespace_only_kr_is_refused(self):
        r = _add(self.d, "a whitespace probe", "--kr", "   ")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("is blank", r.stdout + r.stderr)

    def test_an_empty_kr_is_refused_the_same_way(self):
        r = _add(self.d, "an empty probe", "--kr", "")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("is blank", r.stdout + r.stderr)

    def test_the_refusal_says_how_to_say_no_kr_instead(self):
        """A refusal that does not name the supported alternative is how a
        caller ends up passing something worse."""
        out = _add(self.d, "a whitespace probe", "--kr", "  ").stdout + \
            _add(self.d, "a whitespace probe", "--kr", "  ").stderr
        self.assertIn("--unlinked", out)

    def test_nothing_was_written(self):
        """`Nothing was written` is a claim, so it is checked rather than
        read. A refusal that had already appended the `add` event would leave
        exactly the row this KR must not count."""
        _add(self.d, "a whitespace probe", "--kr", "   ")
        after = self.events.read_text() if self.events.exists() else ""
        self.assertEqual(after, self.before)

    def test_omitting_the_flag_still_files_the_row_and_warns(self):
        """§ 5.2's "record and warn", untouched. This is the assertion that
        stops the refusal above from silently making `--kr` mandatory."""
        r = _add(self.d, "a row with no kr at all")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("without `--kr`", r.stdout + r.stderr)

    def test_a_padded_kr_is_stripped_rather_than_refused(self):
        """Only the EMPTY case is a refusal. A padded but real id is a value,
        and it is normalised once so the event and the store record cannot
        disagree about it."""
        r = _add(self.d, "a padded kr row", "--kr", "  P003-O1-KR1  ")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        events = [json.loads(l) for l in
                  self.events.read_text().splitlines() if l.strip()]
        adds = [e for e in events if e.get("event") == "add"]
        self.assertEqual(adds[-1]["kr"], "P003-O1-KR1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
