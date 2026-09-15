"""`perry-state --section next` tells the next step from a declared rule file.

TASK-442, `DESIGN-020 § 5.2–5.4` and § 6 phase A. Perry's "suggest next
actions" lived at five sites as example sentences with no state behind them,
so two agents reading one project recommended different things. The judgement
now lives in `bin/perry-state § build_next`: typed facts from the payload,
rules from `reference/next-rules.json`, the same answer for the same state.

What this module holds, and the mutation each part answers:

- **Five fixture projects, each with its primary rule written here** — installed
  with no OKR, an OKR with no phase, an active phase whose week plan cannot be
  told, a closable phase, and a queue track. `TestDeletingARuleReddensItsFixture`
  removes each one's rule from a COPY of the rule file and requires the primary
  to change, with the unmodified copy as its control.
- **A fact the payload cannot tell never fires** (`TestAnUnknownFactNeverFires`).
- **Overlays win** (`TestOverlaysComeFirst`): a recovery hazard outranks a
  missing OKR, and a copy with the overlays moved below the rules shows the
  order is what decides it.
- **Same state, same block** (`TestSameStateSameAnswer`), and **nothing but the
  payload is read** (`TestNothingButThePayloadIsRead`, ARCHITECTURE.md § NN-1).

Every project is built under a temporary root (NN-5). The clock the new facts
read is fixed at `WEDNESDAY`; the payload's own day counts use the real date,
so each fixture dates its rows relative to today.

Run: python3 tests/parallel test_next_section
"""

from __future__ import annotations

import copy
import json
import pathlib
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import config_store  # noqa: E402
import inproc  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / "reference" / "next-rules.json"
PAGE = ROOT / "reference" / "next.md"
STATE = inproc.load("perry-state")

#: The clock the new facts read. A Wednesday, so `R-review-due` fires only
#: through the weekly-report branch unless a test moves it.
WEDNESDAY = date(2026, 9, 16)
FRIDAY = date(2026, 9, 18)

#: The router's size at the base commit. `SKILL.md`'s net bytes must not grow.
ROUTER_BYTES_AT_BASE = 20457

OKR_MD = """# OKR — Next fixture

> **Owner**: `goals` lane (only writer).
> **Period**: 6 months
> **Status**: Active

## Mission

Be a project the next block can read.

## Operating Principles

- Nothing here is worked.

## Anti-Goals

- Not a second Perry.

---

## v1: 2026-06-01

### Objective 1 — Hold still

| Id | KR | Metric / Target | Stretch? | Deadline |
|----|----|------------------|----------|----------|
| O1-KR1 | A number | 1 of 1 | no | 2026-12-01 |

## Versioning log

| Version | Date | Change |
|---|---|---|
| v1 | 2026-06-01 | Written for TASK-442. |
"""

PHASE_SLUG = "001-fixture"
PHASE_MD = """# Phase #001 — fixture

> **Owner**: `goals` lane (only writer).
> **Started**: 2026-09-01
> **Status**: active
> **Source**: `OKR.md` v1

## Phase Focus

Hold still.
"""


def kr(kid: str, *, target=None, current=None, stretch=False) -> dict:
    record = {"kind": "kr", "phase": PHASE_SLUG, "objective": "O1", "id": kid,
              "title": f"key result {kid}", "metric": "a count",
              "stretch": stretch}
    if target is not None:
        record["target"] = target
    if current is not None:
        record["current"] = current
        record["asserted_at"] = "2026-09-02T00:00:00Z"
    return record


def task(tid: str, *, track: str, arrived: str) -> dict:
    return {"id": tid, "title": f"row {tid}", "owner": "Coding Agent",
            "status": "not_started", "priority": "P1", "track": track,
            "stage": "", "stage_since": "", "arrived": arrived,
            "verification": "V2", "evidence": "", "next_action": "pick it up",
            "depends_on": [], "commitment": "", "parent": "", "group": "P1",
            "role": "", "created": "2026-09-01T09:00:00", "order": None,
            "summary": "a queue row old enough to breach"}


def jsonl(rows: list[dict]) -> str:
    return "".join(json.dumps(r) + "\n" for r in rows)


def new_root(owner) -> pathlib.Path:
    root = pathlib.Path(tempfile.mkdtemp(prefix="next-section-"))
    owner.addClassCleanup(shutil.rmtree, root, ignore_errors=True)
    return root


def build(owner, name: str) -> pathlib.Path:
    """One of the five fixture projects, written under a temporary root."""
    root = new_root(owner)
    tracks = None
    if name == "queue_track":
        tracks = [config_store.track("intake", "queue", sla="5d")]
    config_store.write_config(root, tracks=tracks)
    if name == "installed_no_okr":
        return root
    (root / "OKR.md").write_text(OKR_MD, encoding="utf-8")
    if name == "queue_track":
        old = (date.today() - timedelta(days=30)).isoformat()
        (root / "tasks.jsonl").write_text(
            jsonl([task("TASK-001", track="intake", arrived=old)]),
            encoding="utf-8")
        return root
    if name == "okr_no_phase":
        return root
    (root / "phase").mkdir()
    (root / "phase" / "CURRENT").write_text(PHASE_SLUG + "\n", encoding="utf-8")
    (root / "phase" / f"{PHASE_SLUG}.md").write_text(PHASE_MD, encoding="utf-8")
    objective = {"kind": "objective", "phase": PHASE_SLUG, "id": "O1",
                 "title": "Hold still"}
    if name == "active_phase_week_unknown":
        krs = [kr("P001-O1-KR1", target=3)]
    else:   # closable_phase
        krs = [kr("P001-O1-KR1", target=3, current=3),
               kr("P001-O1-KR2", target=0, current=0),
               kr("P001-O1-KR3", target=5, stretch=True)]
    (root / "linkage.jsonl").write_text(jsonl([objective, *krs]),
                                        encoding="utf-8")
    return root


def payload_of(root: pathlib.Path, *extra: str) -> dict:
    proc = inproc.run("perry-state", ["--json", *extra, "--root", str(root)],
                      cwd=ROOT)
    if proc.returncode != 0:
        raise AssertionError(f"perry-state exited {proc.returncode}: "
                             f"{proc.stderr[-400:]}")
    return json.loads(proc.stdout)


#: Each fixture and the rule that must be its primary. Written here, not read
#: from the rule file, so a rule that moves or goes quiet is a failure.
EXPECTED = {
    "installed_no_okr": "R-no-okr",
    "okr_no_phase": "R-no-phase",
    "active_phase_week_unknown": "R-review-due",
    "closable_phase": "R-phase-closable",
    "queue_track": "R-sla-breach",
}


class Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roots = {name: build(cls, name) for name in EXPECTED}
        cls.payloads = {name: payload_of(root)
                        for name, root in cls.roots.items()}

    def next_of(self, name: str, **kw) -> dict:
        return STATE.build_next(self.payloads[name],
                                today=kw.pop("today", WEDNESDAY), **kw)


def rules_doc() -> dict:
    return json.loads(RULES.read_text(encoding="utf-8"))


def write_rules(owner: unittest.TestCase, doc: dict) -> pathlib.Path:
    path = pathlib.Path(tempfile.mkdtemp(prefix="next-rules-")) / "rules.json"
    owner.addCleanup(shutil.rmtree, path.parent, ignore_errors=True)
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def recommended(block: dict) -> list[str]:
    return ([block["primary"]["rule"]] if block["primary"] else []) + [
        a["rule"] for a in block["alternates"]]


class TestEachFixtureHasItsPrimary(Fixtures):

    def test_the_primary_is_the_rule_written_for_each_fixture(self):
        for name, rule in EXPECTED.items():
            with self.subTest(fixture=name):
                block = self.next_of(name)
                self.assertEqual([], block["conformance"]["rule_errors"])
                self.assertIsNotNone(block["primary"], f"{name}: nothing fired")
                self.assertEqual(rule, block["primary"]["rule"])

    def test_every_fixture_is_an_installed_project(self):
        """Anti-vacuity: an uninstalled fixture would answer R-setup for all."""
        for name, got in self.payloads.items():
            with self.subTest(fixture=name):
                self.assertTrue(got["installed"])

    def test_the_week_plan_is_named_as_unknown_where_a_phase_is_active(self):
        block = self.next_of("active_phase_week_unknown")
        unknown = {u["fact"]: u for u in block["unknown"]}
        self.assertIn("week.planned", unknown)
        self.assertIn("R-week-unplanned", unknown["week.planned"]["rules"])
        self.assertNotIn("R-week-unplanned", recommended(block))
        self.assertEqual("unknown", block["position"][2]["state"])

    def test_the_closable_phase_counts_commit_key_results_only(self):
        block = self.next_of("closable_phase")
        self.assertEqual(["installed=true", "phase.status=active",
                          "phase.kr_progress.met_ratio=1"],
                         block["primary"]["facts"])
        self.assertIn("2 of 2 commit key results in phase 001",
                      block["primary"]["reason"])

    def test_a_queue_project_is_never_told_to_plan_a_phase_or_a_week(self):
        block = self.next_of("queue_track")
        self.assertEqual(["queue"], sorted(
            {t["mode"] for t in self.payloads["queue_track"]["project"]
             ["config"]["tracks"]}))
        commands = [block["primary"]["command"]] + [
            a["command"] for a in block["alternates"]]
        self.assertFalse([c for c in commands if "plan-phase" in c
                          or "plan-week" in c], commands)
        self.assertNotIn("week.planned", {u["fact"] for u in block["unknown"]})
        self.assertIn("TASK-001", block["primary"]["reason"])


class TestDeletingARuleReddensItsFixture(Fixtures):

    def test_each_fixtures_primary_depends_on_its_own_rule(self):
        for name, rule in EXPECTED.items():
            doc = rules_doc()
            control = write_rules(self, doc)
            with self.subTest(fixture=name, copy="unchanged"):
                self.assertEqual(rule, self.next_of(
                    name, rules_path=control)["primary"]["rule"])
            without = copy.deepcopy(doc)
            for section in ("overlays", "rules"):
                without[section] = [r for r in without[section]
                                    if r["id"] != rule]
            self.assertEqual(
                len(doc["overlays"]) + len(doc["rules"]) - 1,
                len(without["overlays"]) + len(without["rules"]),
                f"{rule} is not declared exactly once")
            got = self.next_of(name, rules_path=write_rules(self, without))
            with self.subTest(fixture=name, copy=f"without {rule}"):
                self.assertNotEqual(rule, (got["primary"] or {}).get("rule"))


class TestAnUnknownFactNeverFires(Fixtures):

    def synthetic(self, rules: list[dict]) -> pathlib.Path:
        doc = {"thresholds": {}, "overlays": [], "rules": [
            {"spine": "any", "lane": "work", "command": f"/perry work {r['id']}",
             "reason": "fixture", "after": [], **r} for r in rules]}
        return write_rules(self, doc)

    def test_a_predicate_over_an_unknown_fact_does_not_fire_and_is_listed(self):
        path = self.synthetic([
            {"id": "R-over-unknown",
             "when": {"fact": "week.planned", "op": "eq", "value": False}},
            {"id": "R-over-unknown-negated",
             "when": {"fact": "week.planned", "op": "ne", "value": True}},
            {"id": "R-known", "when": {"fact": "installed", "op": "eq",
                                       "value": True}},
        ])
        block = self.next_of("okr_no_phase", rules_path=path)
        self.assertEqual("R-known", block["primary"]["rule"])
        self.assertEqual([], block["alternates"])
        self.assertEqual([{"fact": "week.planned",
                           "reason": block["unknown"][0]["reason"],
                           "rules": ["R-over-unknown",
                                     "R-over-unknown-negated"]}],
                         block["unknown"])
        self.assertIn("TASK-444", block["unknown"][0]["reason"])

    def test_three_answers_all_and_any(self):
        """`all` with a false part is false and lists nothing; `any` with a
        true part fires; `all` with only true and unknown parts is unknown."""
        path = self.synthetic([
            {"id": "R-all-false", "when": {"all": [
                {"fact": "installed", "op": "eq", "value": False},
                {"fact": "commitments.due", "op": "gt", "value": 0}]}},
            {"id": "R-all-unknown", "when": {"all": [
                {"fact": "installed", "op": "eq", "value": True},
                {"fact": "drafts.drafted", "op": "gt", "value": 0}]}},
            {"id": "R-any-true", "when": {"any": [
                {"fact": "week.planned", "op": "eq", "value": False},
                {"fact": "installed", "op": "eq", "value": True}]}},
        ])
        block = self.next_of("okr_no_phase", rules_path=path)
        self.assertEqual("R-any-true", block["primary"]["rule"])
        self.assertEqual(["installed=true"], block["primary"]["facts"])
        self.assertEqual({"drafts.drafted": ["R-all-unknown"]},
                         {u["fact"]: u["rules"] for u in block["unknown"]})

    def test_met_ratio_is_unknown_while_a_commit_key_result_is_unmeasured(self):
        block = self.next_of("active_phase_week_unknown")
        unknown = {u["fact"]: u for u in block["unknown"]}
        self.assertIn("phase.kr_progress.met_ratio", unknown)
        self.assertIn("1 of 1 commit key results",
                      unknown["phase.kr_progress.met_ratio"]["reason"])
        self.assertNotIn("R-phase-closable", recommended(block))


class TestOverlaysComeFirst(Fixtures):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = build(cls, "installed_no_okr")
        # A pending transaction nothing can parse: `recovery.blocking`.
        (root / ".perry-task-transaction.json").write_text("{not json",
                                                           encoding="utf-8")
        cls.payloads["hazard"] = payload_of(root)

    def test_a_recovery_hazard_outranks_a_missing_okr(self):
        self.assertTrue(self.payloads["hazard"]["recovery"]["blocking"])
        block = self.next_of("hazard")
        self.assertEqual("R-recovery", block["primary"]["rule"])
        # The missing OKR still fires; it is demoted, not dropped.
        self.assertEqual("R-no-okr", block["alternates"][0]["rule"])

    def test_the_order_is_what_decides_it(self):
        """The control. The same rules with the overlays moved below the
        sequence put the missing OKR first."""
        doc = rules_doc()
        moved = {**doc, "overlays": [], "rules": doc["rules"] + doc["overlays"]}
        block = self.next_of("hazard", rules_path=write_rules(self, moved))
        self.assertEqual("R-no-okr", block["primary"]["rule"])

    def test_the_overlays_survive_a_lane_filter(self):
        block = self.next_of("hazard", lane="decide")
        self.assertEqual("R-recovery", block["primary"]["rule"])


class TestSameStateSameAnswer(Fixtures):

    def test_the_same_payload_evaluated_twice_is_identical(self):
        for name in EXPECTED:
            with self.subTest(fixture=name):
                self.assertEqual(json.dumps(self.next_of(name)),
                                 json.dumps(self.next_of(name)))

    def test_the_same_project_read_twice_yields_the_same_block(self):
        root = self.roots["closable_phase"]
        first = STATE.build_next(payload_of(root), today=WEDNESDAY)
        second = STATE.build_next(payload_of(root), today=WEDNESDAY)
        self.assertEqual(json.dumps(first), json.dumps(second))


class TestNothingButThePayloadIsRead(Fixtures):
    """NN-1. `build_next` answers from the payload and the clock; with the
    project gone from disk it still gives the same block."""

    def test_the_block_survives_the_project_being_deleted(self):
        root = build(self, "closable_phase")
        got = payload_of(root)
        before = json.dumps(STATE.build_next(got, today=WEDNESDAY))
        shutil.rmtree(root)
        self.assertEqual(before,
                         json.dumps(STATE.build_next(got, today=WEDNESDAY)))


class TestTheShape(Fixtures):

    KEYS = {"contract", "semantics", "position", "primary", "alternates",
            "unknown", "conformance"}

    def test_the_block_carries_every_declared_key(self):
        for name in EXPECTED:
            block = self.next_of(name)
            with self.subTest(fixture=name):
                self.assertEqual(self.KEYS, set(block))
                self.assertEqual("perry-next/1.0", block["contract"])
                self.assertEqual(["goals", "phase", "week", "review"],
                                 [p["step"] for p in block["position"]])
                self.assertLessEqual(len(block["alternates"]), 2)
                commands = [block["primary"]["command"]] + [
                    a["command"] for a in block["alternates"]]
                self.assertEqual(len(commands), len(set(commands)))

    def test_next_is_a_key_of_the_full_payload_on_both_branches(self):
        self.assertIn("next", self.payloads["okr_no_phase"])
        bare = new_root(self)
        got = payload_of(bare)
        self.assertFalse(got["installed"])
        self.assertEqual("R-setup", got["next"]["primary"]["rule"])

    def test_compact_is_unchanged(self):
        proc = inproc.run("perry-state", [
            "--compact", "--root", str(self.roots["okr_no_phase"])], cwd=ROOT)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertNotIn("next", json.loads(proc.stdout))
        self.assertFalse(any(key == "next" or key.startswith("next.")
                             for key, _p, _h in STATE.COMPACT))

    def test_section_next_prints_the_payloads_block(self):
        root = self.roots["okr_no_phase"]
        proc = inproc.run("perry-state", ["--section", "next", "--root",
                                          str(root)], cwd=ROOT)
        self.assertEqual(0, proc.returncode, proc.stderr)
        got = json.loads(proc.stdout)
        self.assertEqual(["next"], list(got))
        self.assertEqual(payload_of(root)["next"], got["next"])

    def test_an_alternate_never_repeats_a_command_already_offered(self):
        """Found by mutation: no fixture fires two rules with one command, so
        dropping the narrowing was green. Four rules fire here; the second
        repeats the primary's command and the fourth repeats the third's."""
        def rule(rid, command):
            return {"id": rid, "spine": "any", "lane": "work",
                    "command": command, "reason": "fixture", "after": [],
                    "when": {"fact": "installed", "op": "eq", "value": True}}
        doc = {"thresholds": {}, "overlays": [], "rules": [
            rule("R-first", "/perry work triage"),
            rule("R-same-as-first", "/perry work triage"),
            rule("R-second", "/perry work handoff"),
            rule("R-same-as-second", "/perry work handoff"),
            rule("R-third", "/perry work nudge")]}
        block = self.next_of("okr_no_phase", rules_path=write_rules(self, doc))
        self.assertEqual("R-first", block["primary"]["rule"])
        self.assertEqual(["R-second", "R-third"],
                         [a["rule"] for a in block["alternates"]])
        self.assertEqual(5, block["conformance"]["rules_fired"])

    def test_nothing_fired_is_a_null_primary_not_an_invented_one(self):
        doc = {"thresholds": {}, "overlays": [], "rules": []}
        block = self.next_of("okr_no_phase", rules_path=write_rules(self, doc))
        self.assertIsNone(block["primary"])
        self.assertEqual([], block["alternates"])


class TestFlags(Fixtures):

    def run_state(self, *argv: str):
        return inproc.run("perry-state", [*argv, "--root",
                                          str(self.roots["closable_phase"])],
                          cwd=ROOT)

    def test_lane_keeps_that_lanes_rules_and_the_overlays(self):
        proc = self.run_state("--section", "next", "--lane", "goals")
        self.assertEqual(0, proc.returncode, proc.stderr)
        block = json.loads(proc.stdout)["next"]
        self.assertEqual({"after": "", "lane": "goals"},
                         block["conformance"]["filters"])
        overlays = {r["id"] for r in rules_doc()["overlays"]}
        lanes = {r["id"]: r["lane"] for r in rules_doc()["rules"]}
        for rule in recommended(block) + [r for u in block["unknown"]
                                          for r in u["rules"]]:
            with self.subTest(rule=rule):
                self.assertTrue(rule in overlays or lanes[rule] == "goals")
        self.assertNotIn("R-phase-closable", recommended(block))

    def test_after_keeps_the_rules_that_may_fire_after_that_subcommand(self):
        block = self.next_of("closable_phase", after="plan-phase")
        doc = rules_doc()
        allowed = {r["id"] for r in doc["overlays"]} | {
            r["id"] for r in doc["rules"] if "plan-phase" in r["after"]}
        for rule in recommended(block) + [r for u in block["unknown"]
                                          for r in u["rules"]]:
            self.assertIn(rule, allowed)
        self.assertNotIn("R-phase-closable", recommended(block))

    def test_the_narrowing_flags_are_refused_without_section_next(self):
        for argv in (("--after", "close-task"), ("--lane", "work"),
                     ("--section", "board", "--lane", "work")):
            with self.subTest(argv=argv):
                proc = self.run_state(*argv)
                self.assertEqual(2, proc.returncode)
                self.assertIn("--section next", proc.stderr)

    def test_an_unknown_lane_is_refused_by_name(self):
        proc = self.run_state("--section", "next", "--lane", "okr")
        self.assertEqual(2, proc.returncode)
        self.assertIn("goals, work, decide", proc.stderr)


class TestTheRuleFile(unittest.TestCase):

    DESIGN_TABLE = ("R-setup", "R-no-okr", "R-no-phase", "R-phase-closable",
                    "R-week-unplanned", "R-asks-waiting", "R-review-due",
                    "R-handoff-stale", "R-design-unhanded", "R-board-over-cap")
    REPLACEMENTS = {"R-sla-breach": "queue", "R-queue-commitment-due": "queue",
                    "R-wip-over-limit": "pipeline",
                    "R-pipeline-commitment-due": "pipeline"}

    def setUp(self):
        self.doc = rules_doc()
        self.ids = [r["id"] for r in self.doc["overlays"] + self.doc["rules"]]

    def test_the_bound_three_overlays_ten_rules_and_the_replacements(self):
        self.assertEqual(["R-recovery", "R-interrupted", "R-draft-waiting"],
                         [r["id"] for r in self.doc["overlays"]])
        sequence = [r["id"] for r in self.doc["rules"]]
        self.assertEqual(list(self.DESIGN_TABLE),
                         [i for i in sequence if i in self.DESIGN_TABLE])
        self.assertEqual(set(self.DESIGN_TABLE) | set(self.REPLACEMENTS),
                         set(sequence))
        self.assertEqual("R-board-over-cap", sequence[-1])
        spines = {r["id"]: r["spine"] for r in self.doc["rules"]}
        for rid, spine in self.REPLACEMENTS.items():
            self.assertEqual(spine, spines[rid])
        for rid in ("R-no-phase", "R-phase-closable", "R-week-unplanned"):
            self.assertEqual("project", spines[rid])

    def test_every_rule_id_is_explained_on_the_page_and_nothing_else_is(self):
        headings = re.findall(r"^### (R-[a-z-]+)\s*$",
                              PAGE.read_text(encoding="utf-8"), flags=re.M)
        self.assertEqual(self.ids, headings)

    def test_every_rule_is_well_formed_and_names_only_declared_facts(self):
        seen: set = set()
        for rule in self.doc["overlays"] + self.doc["rules"]:
            with self.subTest(rule=rule["id"]):
                self.assertEqual([], STATE.next_rule_problems(rule, seen))
                seen.add(rule["id"])
                self.assertTrue(rule["command"].startswith("/perry"))

    def test_a_threshold_comes_from_the_schema_when_the_schema_declares_it(self):
        schema = json.loads((ROOT / "schema" / "state-schema.json").read_text(
            encoding="utf-8"))["thresholds"]
        _values, listed = STATE.next_thresholds(self.doc)
        self.assertEqual(sorted(self.doc["thresholds"]),
                         [t["name"] for t in listed])
        for entry in listed:
            with self.subTest(threshold=entry["name"]):
                self.assertEqual("schema" if entry["name"] in schema
                                 else "rule-file", entry["source"])
                if entry["source"] == "rule-file":
                    self.assertTrue(self.doc["thresholds"][entry["name"]]
                                    ["note"].strip())

    def test_a_rule_naming_something_that_is_not_a_fact_is_an_error(self):
        problems = STATE.next_rule_problems(
            {"id": "R-x", "when": {}, "spine": "any", "lane": "work",
             "command": "/perry work {no.such.fact}", "reason": "r",
             "after": []}, set())
        self.assertTrue(any("no.such.fact" in p for p in problems), problems)
        with self.assertRaises(STATE._RuleError):
            STATE.next_evaluate({"fact": "no.such.fact", "op": "eq",
                                 "value": 1}, {}, {}, {})

    def test_a_kind_mismatch_is_an_error_and_not_a_coercion(self):
        with self.assertRaises(STATE._RuleError):
            STATE.next_evaluate({"fact": "board.lines", "op": "gt",
                                 "value": "3"}, {"board.lines": 5}, {}, {})
        truth, _f, _u = STATE.next_evaluate(
            {"fact": "installed", "op": "eq", "value": 1},
            {"installed": True}, {}, {})
        self.assertFalse(truth)


class TestKrProgress(unittest.TestCase):
    """`met` over typed numbers. No `metric` prose decides a direction."""

    @staticmethod
    def payload(*krs: dict) -> dict:
        return {"phase": {"slug": "001-x"},
                "linkage": {"phase": "001-x",
                            "objectives": [{"krs": list(krs)}]}}

    def test_a_target_of_zero_is_met_only_at_zero(self):
        counts, why = STATE.next_kr_progress(self.payload(
            {"current": 3, "target": 0, "stretch": False},
            {"current": 0, "target": 0, "stretch": False}))
        self.assertEqual("", why)
        self.assertEqual({"commit_total": 2, "measured": 2, "met": 1,
                          "unmeasured": 0}, counts)

    def test_stretch_is_not_counted_and_a_missing_number_is_unmeasured(self):
        counts, _why = STATE.next_kr_progress(self.payload(
            {"current": 1, "target": 5, "stretch": True},
            {"current": None, "target": 5, "stretch": False},
            {"current": 4, "target": None, "stretch": False},
            {"current": 6, "target": 5, "stretch": False}))
        self.assertEqual({"commit_total": 3, "measured": 1, "met": 1,
                          "unmeasured": 2}, counts)

    def test_a_register_for_another_phase_is_unknown_not_zero(self):
        got = {"phase": {"slug": "002-y"},
               "linkage": {"phase": "001-x", "objectives": []}}
        counts, why = STATE.next_kr_progress(got)
        self.assertEqual({}, counts)
        self.assertIn("001-x", why)


class TestReviewAndWip(Fixtures):

    def with_weekly(self, week: str) -> dict:
        got = copy.deepcopy(self.payloads["okr_no_phase"])
        got["history"]["latest_weekly"] = week
        return got

    def rules_fired(self, got: dict, today: date) -> list[str]:
        return recommended(STATE.build_next(got, today=today))

    def test_this_weeks_report_is_quiet_midweek_and_due_on_friday(self):
        this_week = STATE.iso_week(WEDNESDAY)
        self.assertNotIn("R-review-due",
                         self.rules_fired(self.with_weekly(this_week), WEDNESDAY))
        self.assertIn("R-review-due",
                      self.rules_fired(self.with_weekly(this_week), FRIDAY))

    def test_a_report_older_than_last_week_is_late(self):
        last_week = STATE.iso_week(WEDNESDAY - timedelta(days=7))
        two_back = STATE.iso_week(WEDNESDAY - timedelta(days=14))
        self.assertNotIn("R-review-due",
                         self.rules_fired(self.with_weekly(last_week), WEDNESDAY))
        block = STATE.build_next(self.with_weekly(two_back), today=WEDNESDAY)
        self.assertIn("R-review-due", recommended(block))
        self.assertEqual("late", block["position"][3]["state"])

    def test_an_unreadable_report_stamp_is_unknown(self):
        block = STATE.build_next(self.with_weekly("last Tuesday"),
                                 today=WEDNESDAY)
        self.assertIn("history.weeks_since_weekly",
                      {u["fact"] for u in block["unknown"]})

    def test_a_pipeline_over_its_wip_limit_is_recommended_triage(self):
        got = copy.deepcopy(self.payloads["okr_no_phase"])
        got["project"]["config"]["tracks"] = [{
            "track": "flow", "mode": "pipeline", "wip": "review:1",
            "wip_breaches": [{"stage": "review", "count": 2, "limit": 1}]}]
        block = STATE.build_next(got, today=WEDNESDAY)
        self.assertEqual("R-wip-over-limit", block["primary"]["rule"])
        got["project"]["config"]["tracks"][0]["wip"] = "—"
        block = STATE.build_next(got, today=WEDNESDAY)
        self.assertIn("pipeline.wip_breaches",
                      {u["fact"] for u in block["unknown"]})


class TestTheFiveSitesPointAtTheBlock(unittest.TestCase):
    """The example lists are gone; each site points at the command."""

    SITES = {
        "reference/snapshot.md": "perry-state\" --section next",
        "goals/SKILL.md": "--section next --lane goals",
        "work/SKILL.md": "--section next --lane work",
        "decide/SKILL.md": "--section next --lane decide",
    }

    def test_each_standup_calls_the_section_and_cites_the_page(self):
        for rel, call in self.SITES.items():
            text = (ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(page=rel):
                self.assertIn(call, text)
                self.assertIn("reference/next.md", text)
                self.assertNotIn("Suggest 1–3 next actions", text)

    def test_the_router_points_at_the_page_without_growing(self):
        router = ROOT / "SKILL.md"
        text = router.read_text(encoding="utf-8")
        self.assertIn("reference/next.md", text)
        self.assertNotIn("suggest 1–3 next actions", text)
        self.assertLessEqual(router.stat().st_size, ROUTER_BYTES_AT_BASE)


if __name__ == "__main__":
    unittest.main()
