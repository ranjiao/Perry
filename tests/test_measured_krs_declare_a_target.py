"""TASK-415 — a KR Perry MEASURED must carry a `target`, and the two rules
`perry-goals/list/3.1` added are enforced here rather than only written down.

`schema/goals-list-contract.md § A measured `current` always has a `target`
beside it` states the first rule and this module is what makes it a rule.
`perry-goals/list/2.0` removed `progress` because Perry cannot tell which way
a KR runs, so a consumer draws a bar only when `target` and `current` are both
numbers — and the strictest thing a consumer can do with a KR that fails that
is show NOTHING. On 2026-09-09 aiMark did exactly that, and the row it blanked
was `P003-O3-KR2`: the single most rigorously measured value in the register,
recomputed by `bin/lib § same_action_linkage` from `linkage.jsonl` and
`.perry/events.jsonl` on every read, published beside `target: null`. Its
target had been written — as the first three words of `metric`, "Target
100%." — and prose is the one place a consumer may not read a number from.

**Why this is asserted over the payload rather than over the store.** The rule
binds what a CONSUMER sees. A store record can carry a `target` the payload
does not publish (a parse that dropped it) and the consumer would still draw
nothing, so a store-side assertion could be green while the defect it exists
to catch was live on the surface it happens on.

**What is deliberately NOT asserted: the value.** No test here pins `100`.
That is the PMO's call on one row, and a guard on it would redden the day
somebody re-scoped the KR rather than the day the contract broke. What is
pinned is that a measured KR has A target — and, separately, that at least one
KR in the live payload IS measured, because a rule quantified over an empty
set passes for the wrong reason and would have passed before the fix too.

Run: python3 tests/parallel test_measured_krs_declare_a_target
"""

from __future__ import annotations

COVERS = (
    "bin/perry-goals",
    "bin/perry-state",
    "bin/lib/",
    "schema/goals-list-contract.md",
    "perry/",
    ".perry/",
)

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

sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pinned_phase  # noqa: E402


def project(phase: str = pinned_phase.SCORED_PHASE) -> Path:
    """The project the payloads are read from. TASK-441.

    This used to be the live checkout, so the anti-vacuity case below went red
    the day `score-phase 003` cleared `phase/CURRENT`: with no phase current,
    no KR is measured. It is now a copy of the tree with the scored phase
    pinned (`tests/pinned_phase.py`). `TheScoredPhaseIsLoadBearing` reads a
    copy pinned to `(none)` and shows the same case fails there.
    """
    return pinned_phase.pinned_copy(__name__, phase)


def goals_payload(root: Path | None = None) -> dict:
    """`perry-goals list --json` against a copy of this repository's project."""
    r = subprocess.run(
        ["python3", str(GOALS), "list", "--json",
         "--root", str(root or project())],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"perry-goals exited {r.returncode}: "
                             f"{r.stderr[-800:]}")
    return json.loads(r.stdout)


def measured_ids(krs) -> list[str]:
    """Every KR a payload reports `measured: true`. The anti-vacuity case and
    its control both call this."""
    return [k["id"] for k in krs
            if (k.get("current_provenance") or {}).get("measured")]


def state_krs(root: Path | None = None) -> list[dict]:
    """The same KRs off the OTHER publisher.

    Both `perry-state` and `perry-goals` emit a KR's `current` beside its
    `target`, and the rule has to hold on both or a consumer reading the one
    nobody checked gets the blank row back.
    """
    r = subprocess.run(
        ["python3", str(STATE), "--root", str(root or project()),
         "--section", "linkage"],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"perry-state exited {r.returncode}: "
                             f"{r.stderr[-800:]}")
    payload = json.loads(r.stdout)
    return [k for o in (payload.get("linkage") or {}).get("objectives", [])
            for k in o.get("krs", [])]


def offenders(krs) -> list[str]:
    """Every KR that is measured and carries no target. The rule, as a list.

    One function, used by the live assertions AND by the anti-vacuity test
    that feeds it a hand-built offending row — so the thing proven to catch a
    bad row is the same thing run against the real payload, not a paraphrase
    of it.
    """
    out = []
    for k in krs:
        if not (k.get("current_provenance") or {}).get("measured"):
            continue
        if k.get("target") is None:
            out.append(str(k.get("id") or "?"))
    return out


class TheRuleHoldsOnTheLivePayload(unittest.TestCase):
    """The deliverable, on this project, through both publishers."""

    @classmethod
    def setUpClass(cls):
        cls.payload = goals_payload()

    def test_no_measured_kr_is_published_without_a_target(self):
        bad = offenders(self.payload["krs"])
        self.assertEqual(
            bad, [],
            f"`perry-goals list --json` publishes {bad} with "
            f"`current_provenance.measured: true` and `target: null`. A "
            f"consumer draws a bar only when both are numbers "
            f"(`perry-goals/list/2.0` removed `progress`), so these rows "
            f"render as KRs nobody wrote a target for — beside a number "
            f"Perry recomputed from its own event logs on this read. Write "
            f"the target onto the KR record in `perry/linkage.jsonl`; the "
            f"rule is `schema/goals-list-contract.md`, contract `3.1`")

    def test_the_other_publisher_agrees(self):
        bad = offenders(state_krs())
        self.assertEqual(
            bad, [],
            f"`perry-state --section linkage` publishes {bad} measured with "
            f"no target. The two publishers splice the same "
            f"`bin/lib § kr_progress_provenance` mapping in, so a "
            f"disagreement here is a second reader of one rule")

    def test_at_least_one_kr_is_measured(self):
        """Anti-vacuity, and it is not decoration.

        Every assertion above is `for k in krs if measured` — over no measured
        KR they all pass, and they would have passed on 2026-09-09 with the
        defect live. `bin/lib § COMPUTED_KR_METRICS` is what makes the set
        non-empty; the day it is emptied, this reddens and says so rather than
        letting two green tests mean nothing.
        """
        measured = measured_ids(self.payload["krs"])
        self.assertTrue(
            measured,
            "no KR in the live payload reports `measured: true`, so the two "
            "assertions above quantify over an empty set and cannot fail. "
            f"`COMPUTED_KR_METRICS` names {sorted(lib.COMPUTED_KR_METRICS)}")

    def test_the_contract_page_states_the_rule(self):
        """A rule enforced by a test nobody can find from the payload is a
        private habit. The page is where a consumer reads it, and `3.1` is
        the minor it was published under."""
        page = (PERRY_HOME / "schema" /
                "goals-list-contract.md").read_text(encoding="utf-8")
        # TASK-237 3b′: `installed` was added, a minor bump.
        # TASK-237 3c: `installed` narrowed (a store needs `.perry/`), a minor bump.
        # TASK-416: `checks`, `state`, `met`, `fraction` added, a minor bump.
        # TASK-264 D3: `status` and `revisions` added, a minor bump.
        self.assertIn("perry-goals/list/3.6", page)
        self.assertIn("`current_provenance.measured` is `true`, `target` is "
                      "not `null`", page)
        # TASK-237 3b′: `installed` was added, a minor bump.
        # TASK-237 3c: `installed` narrowed (a store needs `.perry/`), a minor bump.
        self.assertEqual(self.payload["contract"], "perry-goals/list/3.6")


class TheCheckCatchesTheRowItWasWrittenFor(unittest.TestCase):
    """`offenders` run against the shape the defect actually had.

    Without this the live tests prove only that today's data is clean, which
    is also what a check that can never fire proves.
    """

    def row(self, *, measured: bool, target):
        return {"id": "P003-O3-KR2", "target": target,
                "current": 34.2,
                "current_provenance": {"state": "measured" if measured
                                       else "asserted",
                                       "measured": measured}}

    def test_a_measured_kr_with_no_target_is_named(self):
        self.assertEqual(
            offenders([self.row(measured=True, target=None)]),
            ["P003-O3-KR2"])

    def test_a_measured_kr_with_a_target_is_not(self):
        self.assertEqual(offenders([self.row(measured=True, target=100)]), [])

    def test_a_target_of_zero_is_a_target(self):
        """`0` is falsy and is a perfectly good target — six of eight phase
        KRs drive a count to zero. A check written as `if not k["target"]`
        would report every one of them, which is why the rule is stated
        against `None` and this test is the one that would catch the slip.
        """
        self.assertEqual(offenders([self.row(measured=True, target=0)]), [])

    def test_an_asserted_kr_with_no_target_is_left_alone(self):
        """The rule binds only where PERRY produced the number. A register
        that gave a `current` and no target is a register a human wrote that
        way, and `P003-O2-KR3` carries no target by design.
        """
        self.assertEqual(offenders([self.row(measured=False, target=None)]),
                         [])


class TheMeasuredPercentIsPublishedToOneDecimal(unittest.TestCase):
    """`3.1`'s other rule — `bin/lib § measured_percent`.

    `13 / 38` went out as `34.21052631578947`: seventeen significant figures
    of a ratio of two small integers, sixteen of them an artefact of binary
    floating point rather than anything measured.
    """

    def test_the_ratio_is_rounded_to_one_decimal(self):
        self.assertEqual(lib.measured_percent(13, 38), 34.2)
        self.assertEqual(lib.measured_percent(1, 3), 33.3)
        self.assertEqual(lib.measured_percent(2, 3), 66.7)

    def test_the_exact_ends_are_published_exactly(self):
        self.assertEqual(lib.measured_percent(0, 38), 0.0)
        self.assertEqual(lib.measured_percent(38, 38), 100.0)

    def test_a_ratio_short_of_the_end_never_rounds_onto_it(self):
        """`1999 / 2000` is `99.95`, which one decimal place rounds to
        `100.0` — a claim that every row was answered, about a phase with a
        row that was not. `0.0` and `100.0` are reserved for the whole facts.
        """
        self.assertEqual(lib.measured_percent(1999, 2000), 99.9)
        self.assertEqual(lib.measured_percent(1, 100000), 0.1)

    def test_an_empty_denominator_is_none_and_not_zero(self):
        """Nothing opened under the gate is not "nothing linked"."""
        self.assertIsNone(lib.measured_percent(0, 0))

    def test_the_number_of_places_is_written_in_one_place(self):
        """The digit is `MEASURED_PERCENT_PLACES`, not a literal in the
        rounding call and a different literal in the docs."""
        self.assertEqual(lib.MEASURED_PERCENT_PLACES, 1)

    def test_the_live_payload_carries_the_rounded_value(self):
        """End to end, through the binary, on this project's own data — the
        unit tests above would all pass with `same_action_linkage` still
        dividing for itself."""
        payload = goals_payload()
        for k in payload["krs"]:
            if not (k.get("current_provenance") or {}).get("measured"):
                continue
            current = k.get("current")
            if current is None:
                continue
            with self.subTest(kr=k["id"]):
                self.assertEqual(
                    current, round(current, lib.MEASURED_PERCENT_PLACES),
                    f"{k['id']} publishes {current!r}, which carries more "
                    f"than {lib.MEASURED_PERCENT_PLACES} decimal place(s)")
                m = k.get("current_measurement") or {}
                self.assertEqual(
                    current, lib.measured_percent(m["numerator"],
                                                  m["denominator"]))

    def test_the_unrounded_ratio_is_still_published(self):
        """The rounding is only safe because nothing is lost: a consumer that
        wants the exact value divides these two, and one that wants to know
        whether the KR is MET compares them."""
        for k in goals_payload()["krs"]:
            if not (k.get("current_provenance") or {}).get("measured"):
                continue
            m = k.get("current_measurement") or {}
            with self.subTest(kr=k["id"]):
                self.assertIsInstance(m.get("numerator"), int)
                self.assertIsInstance(m.get("denominator"), int)


class ThePinnedCopy(pinned_phase.ThePinnedCopyGuards, unittest.TestCase):
    """TASK-441. The payloads above come from a copy, not the checkout."""

    OWNER = __name__


class TheScoredPhaseIsLoadBearing(unittest.TestCase):
    """TASK-441's control. `test_at_least_one_kr_is_measured` passes because
    the copy has a phase current, and not because the anti-vacuity check has
    stopped firing. A copy pinned to `(none)`, which is main after
    `score-phase 003`, publishes no measured KR, so the same predicate fails
    there."""

    def test_with_no_phase_current_no_kr_is_measured(self):
        unpinned = project(pinned_phase.NO_PHASE)
        self.assertEqual(pinned_phase.NO_PHASE,
                         pinned_phase.current_phase(unpinned))
        self.assertEqual([], measured_ids(goals_payload(unpinned)["krs"]))

    def test_with_the_scored_phase_pinned_one_is(self):
        self.assertTrue(measured_ids(goals_payload(project())["krs"]))


if __name__ == "__main__":
    unittest.main()
