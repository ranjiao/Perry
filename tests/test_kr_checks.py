"""TASK-416 — a KR's checks and measurements are records, and `met` is derived.

DESIGN-022 § 5.1 adds two appended record kinds to `linkage.jsonl` — `check`
and `measurement` — and § 5.2 derives a position from them on every read:
per check `state` / `met` / `fraction`, per KR the fold of its checks, per
Objective COUNTS. `bin/lib § kr_checks` states the two ordering rules once and
`bin/lib § kr_position` is the one derivation; `perry-goals list` (3.5) and
`perry-goals krs` publish it.

**The finding this row was opened for.** A hand-measured `current: 0` and a
template `0` nobody touched were byte-identical. After this row "someone
measured 0" is a `measurement` record and "nobody measured" is its absence,
and absence reads `unmeasured` / `undeclared` with `met: null` — never `0`
and never `false`. `TestAbsentIsNeverZeroOrFalse` holds that.

Each fixture in the spec's Verification § 4 asserts an exact value, and each
of § 5's four mutations is red on a named test here (the table is in
`perry/evidence/2026-09/TASK-416-result.md`).

Every write goes to a temporary root (NN-5).

Run: python3 tests/parallel test_kr_checks
"""

from __future__ import annotations

COVERS = (
    "bin/lib/",
    "bin/perry-goals",
    "bin/perry-lint",
    "viewer/parsers.py",
    "schema/state-schema.json",
    "schema/goals-list-contract.md",
    "tests/fixtures/witness-project/",
)

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
GOALS = PERRY_HOME / "bin" / "perry-goals"
LINT = PERRY_HOME / "bin" / "perry-lint"
WITNESS = PERRY_HOME / "tests" / "fixtures" / "witness-project"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())

sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402

NOW = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)


def stamp(days_ago: float = 0.0, hours_ago: float = 0.0) -> str:
    return (NOW - timedelta(days=days_ago, hours=hours_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def check(cid="c", *, kr="P004-O3-KR3", okr_version="", direction="decrease",
          target=400, baseline=1702, declared_at=None, label="a check"):
    return {"kind": "check", "kr": kr, "okr_version": okr_version, "id": cid,
            "label": label, "direction": direction, "target": target,
            "baseline": baseline,
            "declared_at": declared_at or stamp(days_ago=2),
            "actor": "goals"}


def measurement(value, *, cid="c", kr="P004-O3-KR3", okr_version="",
                asserted_at=None, evidence="evidence/2026-09/x.md"):
    return {"kind": "measurement", "kr": kr, "okr_version": okr_version,
            "check": cid, "value": value,
            "asserted_at": asserted_at or stamp(days_ago=1),
            "evidence": evidence, "computed": False, "actor": "goals"}


def position(records, kr="P004-O3-KR3", okr_version="", **kw):
    entries = lib.kr_checks(records).get((kr, okr_version), [])
    return lib.kr_position(entries, now=NOW, due_days=7, **kw)


def one_check(value, **check_kw):
    """The position of a KR with one check measured at `value`."""
    return position([check(**check_kw), measurement(value)])


class TestDecreaseFixture(unittest.TestCase):
    """`decrease` 1702 → 400 — `P004-O3-KR3`, the row TASK-442's
    `current >= target` reads as met at 1,702."""

    def test_not_met_at_the_baseline(self):
        got = one_check(1702)
        self.assertEqual((got["met"], got["fraction"]), (False, 0.0))

    def test_met_at_the_target(self):
        got = one_check(400)
        self.assertEqual((got["met"], got["fraction"]), (True, 1.0))

    def test_half_way(self):
        got = one_check(1051)
        self.assertEqual((got["met"], got["fraction"]), (False, 0.5))

    def test_past_the_target_is_met_and_clamped(self):
        got = one_check(12)
        self.assertEqual((got["met"], got["fraction"]), (True, 1.0))

    def test_behind_the_baseline_is_clamped_to_zero(self):
        got = one_check(2000)
        self.assertEqual((got["met"], got["fraction"]), (False, 0.0))

    def test_an_end_is_reserved_for_the_exact_case(self):
        """3.1's reserved ends: a value strictly between never reads 1.0."""
        got = one_check(400.5)
        self.assertFalse(got["met"])
        self.assertLess(got["fraction"], 1.0)
        self.assertGreater(one_check(1701.9)["fraction"], 0.0)


class TestIncreaseFixture(unittest.TestCase):
    def test_increase_zero_to_five(self):
        kw = dict(direction="increase", target=5, baseline=0)
        self.assertEqual(one_check(0, **kw)["fraction"], 0.0)
        self.assertEqual(one_check(5, **kw)["met"], True)
        self.assertEqual(one_check(2, **kw)["fraction"], 0.4)
        self.assertEqual(one_check(2, **kw)["met"], False)

    def test_a_declaration_that_runs_the_wrong_way_draws_no_fraction(self):
        got = one_check(3, direction="increase", target=1, baseline=5)
        self.assertIsNone(got["fraction"])


class TestAtMostZeroFixture(unittest.TestCase):
    """`at_most 0` — a limit: met or not, never a fraction."""

    kw = dict(direction="at_most", target=0, baseline=None)

    def test_met_at_zero(self):
        got = one_check(0, **self.kw)
        self.assertEqual((got["met"], got["fraction"]), (True, None))

    def test_not_met_at_three(self):
        got = one_check(3, **self.kw)
        self.assertEqual((got["met"], got["fraction"]), (False, None))

    def test_at_least_is_the_other_limit(self):
        kw = dict(direction="at_least", target=100, baseline=None)
        self.assertEqual(one_check(100, **kw)["met"], True)
        self.assertEqual(one_check(99, **kw)["met"], False)
        self.assertIsNone(one_check(100, **kw)["fraction"])


class TestDoneFixture(unittest.TestCase):
    kw = dict(direction="done", target=1, baseline=None)

    def test_met_at_one(self):
        self.assertEqual(one_check(1, **self.kw)["met"], True)

    def test_not_met_at_zero(self):
        got = one_check(0, **self.kw)
        self.assertEqual((got["met"], got["fraction"]), (False, None))


class TestAbsentIsNeverZeroOrFalse(unittest.TestCase):
    """The whole finding TASK-416 was opened for."""

    def test_a_kr_with_no_check_is_undeclared_and_met_is_null(self):
        got = position([])
        self.assertEqual(got, {"checks": [], "state": "undeclared",
                               "met": None, "fraction": None})

    def test_a_measurement_with_no_declared_check_declares_nothing(self):
        got = position([measurement(0)])
        self.assertEqual((got["state"], got["met"]), ("undeclared", None))

    def test_a_check_with_no_measurement_is_unmeasured(self):
        got = position([check()])
        self.assertEqual((got["state"], got["met"], got["fraction"]),
                         ("unmeasured", None, None))
        self.assertIsNone(got["checks"][0]["measurement"])

    def test_two_checks_one_unmeasured(self):
        records = [check("a", direction="at_most", target=0, baseline=None),
                   check("b"),
                   measurement(0, cid="a")]
        got = position(records)
        self.assertEqual((got["state"], got["met"], got["fraction"]),
                         ("unmeasured", None, None))
        self.assertEqual([c["state"] for c in got["checks"]],
                         ["measured", "unmeasured"])

    def test_a_measured_zero_is_not_an_absent_value(self):
        """`at_most 0` measured at 0 is met; unmeasured is null. Before this
        row the two were the same bytes on disk."""
        kw = dict(direction="at_most", target=0, baseline=None)
        self.assertIs(one_check(0, **kw)["met"], True)
        self.assertIsNone(position([check(**kw)])["met"])


class TestTheKrFold(unittest.TestCase):
    def test_every_check_met_is_met_and_two_checks_draw_no_fraction(self):
        records = [check("a", direction="at_most", target=12, baseline=None),
                   check("b"), measurement(10, cid="a"),
                   measurement(400, cid="b")]
        got = position(records)
        self.assertEqual((got["state"], got["met"], got["fraction"]),
                         ("measured", True, None))

    def test_one_unmet_check_is_not_met(self):
        records = [check("a", direction="at_most", target=12, baseline=None),
                   check("b"), measurement(10, cid="a"),
                   measurement(1702, cid="b")]
        self.assertIs(position(records)["met"], False)

    def test_state_is_the_worst_check(self):
        records = [check("a"), check("b"),
                   measurement(500, cid="a", asserted_at=stamp(days_ago=1)),
                   measurement(500, cid="b", asserted_at=stamp(days_ago=9))]
        self.assertEqual(position(records)["state"], "due")

    def test_checks_keep_first_declared_order(self):
        records = [check("b"), check("a"), check("b", target=300,
                                                 declared_at=stamp(days_ago=1))]
        self.assertEqual([c["id"] for c in position(records)["checks"]],
                         ["b", "a"])


class TestTheOrderingRules(unittest.TestCase):
    """Both rules, out of file order — `lib.kr_checks` is the one place."""

    def test_a_redeclared_check_supersedes_by_declared_at(self):
        later = check(target=300, declared_at=stamp(days_ago=1))
        earlier = check(target=400, declared_at=stamp(days_ago=5))
        # The later declaration is written FIRST in the file.
        got = position([later, earlier, measurement(350)])
        self.assertEqual(got["checks"][0]["target"], 300)
        self.assertIs(got["met"], False)
        self.assertEqual(len(got["checks"]), 1)

    def test_the_latest_asserted_at_measurement_wins_regardless_of_file_order(self):
        newest = measurement(400, asserted_at=stamp(days_ago=1))
        oldest = measurement(1702, asserted_at=stamp(days_ago=3))
        got = position([check(), newest, oldest])
        self.assertEqual(got["checks"][0]["measurement"]["value"], 400)
        self.assertIs(got["met"], True)

    def test_offsets_are_compared_as_moments_not_as_text(self):
        """`…T20:00:00+08:00` is 12:00Z, earlier than `…T13:00:00Z`, though
        its text sorts later. TASK-144's defect, one store over."""
        a = measurement(400, asserted_at="2026-09-15T13:00:00Z")
        b = measurement(1702, asserted_at="2026-09-15T20:00:00+08:00")
        self.assertEqual(
            position([check(), a, b])["checks"][0]["measurement"]["value"],
            400)

    def test_equal_moments_fall_back_to_the_later_line(self):
        a = measurement(1702, asserted_at=stamp(days_ago=1))
        b = measurement(400, asserted_at=stamp(days_ago=1))
        self.assertEqual(
            position([check(), a, b])["checks"][0]["measurement"]["value"],
            400)

    def test_an_unreadable_timestamp_never_beats_a_readable_one(self):
        good = measurement(400, asserted_at=stamp(days_ago=3))
        bad = measurement(1702, asserted_at="last Tuesday")
        got = position([check(), good, bad])
        self.assertEqual(got["checks"][0]["measurement"]["value"], 400)


class TestAnOverallKrIsKeyedByItsVersion(unittest.TestCase):
    """`O1-KR1` exists in v2, v3 and v4 of `okr.jsonl`."""

    def test_v3_and_v4_do_not_mix(self):
        records = [
            check("x", kr="O1-KR1", okr_version="v3: 2026-09-01",
                  direction="done", target=1, baseline=None),
            measurement(1, cid="x", kr="O1-KR1", okr_version="v3: 2026-09-01"),
            check("x", kr="O1-KR1", okr_version="v4: 2026-09-15",
                  direction="done", target=1, baseline=None),
        ]
        v3 = position(records, kr="O1-KR1", okr_version="v3: 2026-09-01")
        v4 = position(records, kr="O1-KR1", okr_version="v4: 2026-09-15")
        self.assertEqual((v3["state"], v3["met"]), ("measured", True))
        self.assertEqual((v4["state"], v4["met"]), ("unmeasured", None))
        self.assertEqual(position(records, kr="O1-KR1")["state"], "undeclared")


class TestDue(unittest.TestCase):
    def test_a_measurement_older_than_seven_days_is_due(self):
        got = position([check(), measurement(400,
                                             asserted_at=stamp(days_ago=7,
                                                               hours_ago=1))])
        self.assertEqual(got["state"], "due")
        # Due is about age, not about met: the value still counts.
        self.assertIs(got["met"], True)

    def test_seven_days_to_the_second_is_not_yet_due(self):
        got = position([check(), measurement(400,
                                             asserted_at=stamp(days_ago=7))])
        self.assertEqual(got["state"], "measured")

    def test_a_linked_task_moved_after_the_measurement_is_due(self):
        events = [{"id": "TASK-447", "from": "in_progress", "to": "done",
                   "ts": stamp(hours_ago=2)}]
        records = [check(), measurement(400, asserted_at=stamp(days_ago=1))]
        self.assertEqual(position(records, task_ids=["TASK-447"],
                                  events=events)["state"], "due")
        self.assertEqual(position(records, task_ids=["TASK-999"],
                                  events=events)["state"], "measured")

    def test_an_unreadable_asserted_at_is_due(self):
        got = position([check(), measurement(400, asserted_at="soon")])
        self.assertEqual(got["state"], "due")

    def test_the_threshold_is_the_schema_s_seven(self):
        self.assertEqual(SCHEMA["thresholds"]["kr_measure_due_days"]["value"],
                         7)
        self.assertEqual(lib.kr_measure_due_days(), 7.0)


class TestTheObjectiveSummaryIsCounts(unittest.TestCase):
    """Per Objective: commit KRs measured / total and met / total. No mean."""

    krs = [
        {"stretch": False, "state": "measured", "met": True, "fraction": 1.0},
        {"stretch": False, "state": "due", "met": False, "fraction": 0.5},
        {"stretch": False, "state": "unmeasured", "met": None,
         "fraction": None},
        {"stretch": False, "state": "undeclared", "met": None,
         "fraction": None},
        {"stretch": True, "state": "measured", "met": True, "fraction": 1.0},
    ]

    def test_exact_counts(self):
        self.assertEqual(lib.objective_kr_summary(self.krs), {
            "total": 4, "measured": 2, "met": 1,
            "by_state": {"undeclared": 1, "unmeasured": 1, "due": 1,
                         "measured": 1}})

    def test_every_value_is_an_integer_count(self):
        got = lib.objective_kr_summary(self.krs)
        for key in ("total", "measured", "met"):
            self.assertIs(type(got[key]), int, key)
        self.assertNotIn("fraction", got)
        self.assertNotIn("mean", got)

    def test_stretch_krs_are_excluded(self):
        only_stretch = [k for k in self.krs if k["stretch"]]
        self.assertEqual(lib.objective_kr_summary(only_stretch)["total"], 0)


class TestNoMetricProseIsRead(unittest.TestCase):
    """NN-4: the derivation compares typed values only."""

    def test_metric_and_label_change_nothing(self):
        a = one_check(1051, label="≤ 400 characters (baseline 1,702)")
        b = one_check(1051, label="met, obviously, 100%")
        self.assertEqual({k: v for k, v in a.items() if k != "checks"},
                         {k: v for k, v in b.items() if k != "checks"})

    def test_a_number_written_as_text_is_not_a_number(self):
        got = position([check(), measurement("400")])
        self.assertIsNone(got["met"])
        self.assertIsNone(got["fraction"])


class TestTheSchemaDeclaresTheTwoKinds(unittest.TestCase):
    """USER-937 decision 4: two kinds and one threshold, nothing else."""

    records = SCHEMA["stores"]["declared"]["linkage.jsonl"]["records"]

    def test_check_fields(self):
        self.assertEqual(set(self.records["check"]["fields"]), {
            "kind", "kr", "okr_version", "id", "label", "direction", "target",
            "baseline", "declared_at", "actor"})

    def test_measurement_fields(self):
        self.assertEqual(set(self.records["measurement"]["fields"]), {
            "kind", "kr", "okr_version", "check", "value", "asserted_at",
            "evidence", "computed", "actor"})

    def test_the_direction_pattern_is_the_derivation_s_set(self):
        pattern = self.records["check"]["fields"]["direction"]["pattern"]
        self.assertEqual(pattern,
                         "^(" + "|".join(lib.KR_CHECK_DIRECTIONS) + ")$")


class LintedStore(unittest.TestCase):
    """`perry-lint` against a temp copy of the witness project."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kr-checks-"))
        self.root = self.tmp / "p"
        shutil.copytree(WITNESS, self.root)
        self.store = self.root / "linkage.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def append(self, *records):
        with open(self.store, "a") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")

    def run_tool(self, tool, *args):
        env = {k: v for k, v in os.environ.items()
               if k not in ("PERRY_PROJECT",)}
        return subprocess.run([sys.executable, str(tool), *args,
                               "--root", str(self.root)],
                              capture_output=True, text=True, env=env,
                              timeout=120)


class TestLintAcceptsTheDesignShape(LintedStore):
    def malformed(self) -> str:
        out = self.run_tool(LINT).stdout
        return "\n".join(line for line in out.splitlines()
                         if "linkage-store-malformed" in line
                         or "linkage store:" in line)

    def test_a_null_baseline_on_a_limit_is_not_malformed(self):
        self.append(check(kr="P001-O1-KR1", direction="at_most", target=0,
                          baseline=None),
                    measurement(0, kr="P001-O1-KR1"))
        self.assertIn("0 malformed", self.malformed())

    def test_a_direction_outside_the_five_is_malformed(self):
        self.append(check(kr="P001-O1-KR1", direction="sideways"))
        self.assertIn("linkage-store-malformed", self.malformed())


class TestPerryGoalsPublishesThePosition(LintedStore):
    def goals(self, *args) -> dict:
        got = self.run_tool(GOALS, *args, "--json")
        self.assertEqual(got.returncode, 0, got.stderr)
        return json.loads(got.stdout)

    def rows(self):
        return self.goals("list")["krs"]

    def test_the_contract_is_3_5(self):
        # TASK-264 D3 moved it to 3.6 (`status`, `revisions`); 3.5's four
        # keys are unchanged, which the tests below still hold.
        self.assertEqual(self.goals("list")["contract"],
                         "perry-goals/list/3.6")

    def test_a_kr_whose_record_carries_numbers_and_no_check_is_undeclared(self):
        """Phases 001–003's shape: `target` and `current` on the `kr` record,
        no check. They read exactly as before, and position is null."""
        self.store.write_text("\n".join(
            line for line in self.store.read_text().splitlines()
            if '"kind": "check"' not in line
            and '"kind": "measurement"' not in line) + "\n")
        for row in self.rows():
            # Every `kr` record in the witness carries target 4, current 2,
            # and the register's numbers are keyed by bare id.
            self.assertEqual((row["target"], row["current"]), (4.0, 2.0))
            self.assertEqual(row["current_provenance"]["state"], "asserted")
            self.assertEqual((row["checks"], row["state"], row["met"],
                              row["fraction"]),
                             ([], "undeclared", None, None), row["id"])

    def test_the_overall_kr_reads_its_own_version_only(self):
        self.append(check("other", kr="O1-KR1", okr_version="v0: elsewhere",
                          direction="done", target=1, baseline=None),
                    measurement(1, cid="other", kr="O1-KR1",
                                okr_version="v0: elsewhere"))
        by = {(r["level"], r["id"]): r for r in self.rows()}
        self.assertEqual([c["id"] for c in by[("overall", "O1-KR1")]["checks"]],
                         ["collections"])
        self.assertEqual(by[("phase", "O1-KR1")]["state"], "undeclared")
        self.assertEqual(by[("phase", "P001-O1-KR1")]["fraction"], 0.5)

    def test_a_fresh_measurement_publishes_measured_and_met(self):
        fresh = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.append(measurement(4, cid="collections", kr="P001-O1-KR1",
                                asserted_at=fresh))
        row = {(r["level"], r["id"]): r
               for r in self.rows()}[("phase", "P001-O1-KR1")]
        self.assertEqual((row["met"], row["fraction"]), (True, 1.0))
        # WIT-001 and WIT-002 last moved on 2026-08-06, before `fresh`.
        self.assertEqual(row["state"], "measured")

    def test_krs_json_carries_the_same_four_keys(self):
        krs = [k for o in self.goals("krs")["objectives"] for k in o["krs"]]
        by = {k["id"]: k for k in krs}
        self.assertEqual(by["P001-O1-KR1"]["fraction"], 0.5)
        self.assertEqual((by["O1-KR1"]["state"], by["O1-KR1"]["met"]),
                         ("undeclared", None))


if __name__ == "__main__":
    unittest.main()
