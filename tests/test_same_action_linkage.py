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


if __name__ == "__main__":
    unittest.main(verbosity=2)
