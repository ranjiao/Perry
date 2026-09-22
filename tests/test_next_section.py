"""`perry-state --section next` tells the next step from a declared rule file.

TASK-442, `DESIGN-020 § 5.2–5.4` and § 6 phase A. Perry's "suggest next
actions" lived at five sites as example sentences with no state behind them,
so two agents reading one project recommended different things. The judgement
now lives in `bin/perry-state § build_next`: typed facts from the payload,
rules from `reference/next-rules.json`, the same answer for the same state.

What this module holds, and the mutation each part answers:

- **Eight fixture projects, each with its primary rule written here** — installed
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

COVERS = (
    "bin/perry-state",
    "reference/next-rules.json",
    "reference/next.md",
    "reference/snapshot.md",
    "schema/state-schema.json",
    "SKILL.md",
    "goals/SKILL.md",
    "work/SKILL.md",
    "decide/SKILL.md",
)

import copy
import json
import pathlib
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import config_store  # noqa: E402
import inproc  # noqa: E402
from test_kr_checks import check, measurement  # noqa: E402

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
    """One of the fixture projects, written under a temporary root."""
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
    # TASK-479: a KR with no edge is unstaffed and one with no check is
    # undeclared, so each fixture names its edges and checks. Closable KRs
    # are measured and met with no task: the UD 14 exemption.
    staffed, declared = ["P001-O1-KR1"], ["P001-O1-KR1"]
    if name in ("active_phase_week_unknown", "checks_undeclared") or name in WRITES:
        krs = [kr("P001-O1-KR1", target=3)]
        declared = [] if name == "checks_undeclared" else declared
    elif name == "kr_unstaffed":
        krs = [kr("P001-O1-KR1", target=3, current=3), kr("P001-O1-KR2", target=3)]
        staffed, declared = [], ["P001-O1-KR2"]
    else:   # closable_phase, phase_scorable
        krs = [kr("P001-O1-KR1", target=3, current=3),
               kr("P001-O1-KR2", target=0, current=0),
               kr("P001-O1-KR3", target=5, stretch=True)]
        staffed = []
    checks = [row for k in krs if "current" in k for row in
              (check(kr=k["id"], direction="at_least", target=k["target"]),
               measurement(k["current"], kr=k["id"]))]
    checks += [check(kr=k["id"], direction="at_least", target=k["target"])
               for k in krs if "current" not in k and k["id"] in declared]
    edges = [{"kind": "edge", "task": "TASK-001", "kr": k, "actor": "goals",
              "declared_at": "2026-09-02T00:00:00Z", "via": "link"} for k in staffed]
    (root / "linkage.jsonl").write_text(jsonl([objective, *krs, *checks, *edges]),
                                        encoding="utf-8")
    if name == "phase_scorable":
        retro(root, PHASE_SLUG)
    for write in WRITES.get(name, ()):
        write(root)
    return root


def rows(*records: dict):
    """TASK-483: task records for the execution-loop fixtures."""
    def write(root):
        with (root / "tasks.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(jsonl(list(records)))
    return write


def row(tid: str, status: str, *, rung="V4", priority="P1", depends=()) -> dict:
    return {**task(tid, track="main", arrived=""), "status": status,
            "verification": rung, "priority": priority, "group": priority,
            "depends_on": list(depends)}


def verdict(tid: str, result: str, name: str = "", rung: str = "V4"):
    """A block in `work/reference/review.md § 3`'s shape, appended to `name`."""
    def write(root):
        path = root / "evidence" / "2026-09" / (name or f"{tid}-v4-review.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n=== VERDICT ===\ntask: {tid}\nrung: {rung}\nresult: {result}\n"
                     f"criteria: evidence/2026-09/{tid}-spec.md\nchecked: all\n"
                     f"not-checked: none\n=== END VERDICT ===\n")
    return write


def spec(tid: str, mode: str, month="2026-09", body=None):
    return text(f"evidence/{month}/{tid}-spec.md", body or (
        f"# {tid} — a row\n\nDate: 2026-09-16.\n> Dispatch mode: {mode} · "
        f"Executor: claude-subagent\n\n## Bound\n\nOne row.\n"))


def text(rel: str, body: str):
    def write(root):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body, encoding="utf-8")
    return write


OWED = rows(row("TASK-011", "review"))
PASSED = (rows(row("TASK-012", "review")), verdict("TASK-012", "PASS"))
READY = (rows(row("TASK-013", "not_started")), spec("TASK-013", "auto"))
#: Each execution-loop fixture: an active phase, then these writes (TASK-483).
LOOP = {"review_owed": (OWED,), "closable_row": PASSED, "dispatchable": READY,
        "blocked_stale": (rows(row("TASK-020", "done"),
                               row("TASK-021", "blocked", depends=["TASK-020"])),),
        "busy_board": (OWED, *PASSED, *READY)}


def cadence_rows(*records: dict):
    """TASK-484: records, not `perry-task cadence-done` — which also writes
    today's journal line and would fire `R-handoff-stale` in every fixture."""
    def write(root):
        with (root / "cadence.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(jsonl(list(records)))
    return write


def cadence(rid: str, title: str, *, next_due: str, last_run="", order=0) -> dict:
    return {"id": rid, "title": title, "owner": "PMO Agent", "order": order,
            "frequency": "weekly", "next_due": next_due, "last_run": last_run,
            "last_evidence": ""}


def day(offset: int) -> str:
    """Relative to the REAL today, which `cadence_report` and `days_since` read."""
    return (date.today() + timedelta(days=offset)).isoformat()


ARCHITECTURE_MD = ("# Architecture — fixture\n\n> Version: v1\n"
                   "> Last reviewed: {reviewed}\n\n## §1. Mission & scope\n\n"
                   "Hold still.\n")

#: Batch 3's rules all sit below `R-review-due` and `R-midweek`, so a fixture
#: showing one of them firing must first be quiet on those two: this week's
#: weekly report, and its recorded mid-week check. Neither is a fact any
#: batch-3 rule reads, so silencing them proves nothing away.
QUIET = (text(f"weekly/{STATE.iso_week(WEDNESDAY)}.md", "# Weekly\n"),
         cadence_rows(cadence("CAD-000", "midweek-check",
                              next_due=day(30), last_run="2026-09-14")))

#: DESIGN-020 § 5.10 batch 3 (TASK-484), each over the quiet active phase.
OPERATIONS = {
    "inputs_waiting": (*QUIET, text("inputs/a-brief.md", "# A brief\n")),
    "cadence_overdue": (*QUIET, cadence_rows(cadence(
        "CAD-001", "weekly close", next_due=day(-9), order=1))),
    "risk_raised": (*QUIET, text("risks.jsonl", json.dumps({
        "kind": "risk", "id": "RX-001", "opened": "2026-09-01",
        "risk": "H · the notarization certificate expires this month",
        "status": "open", "order": 0}) + "\n")),
    "architecture_stale": (*QUIET, text("ARCHITECTURE.md", ARCHITECTURE_MD.format(
        reviewed=day(-400)))),
}

#: Every fixture's writes, after `build` has laid down its phase and KRs.
WRITES = {**LOOP, **OPERATIONS}


def retro(root: pathlib.Path, slug: str) -> None:
    """`end-phase-retro`'s file, its header taken from that procedure's own
    template, so the procedure and `parsers.retro_phases` cannot drift apart."""
    page = (ROOT / "work/reference/subcommands.md").read_text(encoding="utf-8")
    section = page.split("### `end-phase-retro`", 1)[1].split("\n### ", 1)[0]
    header = re.search(r"`(> Phase: [^`]+)`", section).group(1)
    (root / "evidence" / "2026-09").mkdir(parents=True, exist_ok=True)
    (root / "evidence" / "2026-09" / "retro.md").write_text("# Retro\n\n" + header.replace(
        "<NNN>-<slug>", slug).replace("<start-date>", "2026-09-01") + "\n", encoding="utf-8")


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
    "phase_scorable": "R-phase-scorable",
    "kr_unstaffed": "R-kr-unstaffed",
    "checks_undeclared": "R-checks-undeclared",
    "review_owed": "R-review-owed",
    "closable_row": "R-closable-row",
    "dispatchable": "R-dispatchable",
    "blocked_stale": "R-blocked-stale",
    "busy_board": "R-review-owed",
    "inputs_waiting": "R-inputs-waiting",
    "cadence_overdue": "R-cadence-overdue",
    "risk_raised": "R-risk-raised",
    "architecture_stale": "R-architecture-stale",
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


#: The command each fixture's primary must OFFER, written out beside its rule.
#: The PMO found the rule id alone was not enough: `R-no-okr` pointed at
#: `/perry work triage` on a copy and every test here stayed green, because a
#: rule that fires with the wrong command still fires. What a user types is
#: the command, so that is what is pinned.
EXPECTED_COMMAND = {
    "installed_no_okr": "/perry goals init",
    "okr_no_phase": "/perry goals plan-phase <slug>",
    "active_phase_week_unknown": "/perry work friday-review",
    "closable_phase": "/perry work end-phase-retro",
    "queue_track": "/perry work triage",
    "phase_scorable": "/perry goals score-phase",
    "kr_unstaffed": "/perry goals plan-week",
    "checks_undeclared": "/perry goals check P001-O1-KR1",
    "review_owed": "/perry work review TASK-011",
    "closable_row": "/perry work close-task TASK-012",
    "dispatchable": "/perry work dispatch TASK-013",
    "blocked_stale": "/perry work triage",
    "busy_board": "/perry work review TASK-011",
    "inputs_waiting": "/perry work digest a-brief.md",
    "cadence_overdue": "/perry work triage",
    "risk_raised": "/perry work risk",
    "architecture_stale": "/perry work architecture-audit",
}


class TestEachFixtureOffersItsCommand(Fixtures):

    def test_the_primary_offers_the_command_written_for_each_fixture(self):
        self.assertEqual(set(EXPECTED), set(EXPECTED_COMMAND))
        for name, command in EXPECTED_COMMAND.items():
            with self.subTest(fixture=name):
                block = self.next_of(name)
                self.assertIsNotNone(block["primary"], f"{name}: nothing fired")
                self.assertEqual(EXPECTED[name], block["primary"]["rule"])
                self.assertEqual(command, block["primary"]["command"])

    def test_the_command_reaches_the_published_payload_unchanged(self):
        """`--section next` is what a lane runs, so the pin holds there too.
        Not for batch 3's four: their rules sit below `R-review-due` and
        `R-midweek`, which fire on the REAL weekday this subprocess reads, so a
        written pin here would go red on a calendar. `TestTheShape` holds the
        published block to the payload's own for all of them."""
        for name, command in EXPECTED_COMMAND.items():
            if name in OPERATIONS:
                continue
            proc = inproc.run("perry-state", ["--section", "next", "--root",
                                              str(self.roots[name])], cwd=ROOT)
            with self.subTest(fixture=name):
                self.assertEqual(0, proc.returncode, proc.stderr)
                primary = json.loads(proc.stdout)["next"]["primary"]
                self.assertEqual(command, primary["command"])


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
                          "phase.kr_progress.met_ratio=1",
                          "phase.retro_recorded=false"],
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
                {"fact": "phase.days_since_snapshot", "op": "gt", "value": 0}]}},
            {"id": "R-any-true", "when": {"any": [
                {"fact": "week.planned", "op": "eq", "value": False},
                {"fact": "installed", "op": "eq", "value": True}]}},
        ])
        block = self.next_of("okr_no_phase", rules_path=path)
        self.assertEqual("R-any-true", block["primary"]["rule"])
        self.assertEqual(["installed=true"], block["primary"]["facts"])
        self.assertEqual({"phase.days_since_snapshot": ["R-all-unknown"]},
                         {u["fact"]: u["rules"] for u in block["unknown"]})

    def test_the_phase_heartbeat_is_declared_and_its_fact_is_unknown(self):
        """Round 3. `goals/SKILL.md`'s heartbeat prompt is `R-phase-heartbeat`.
        Nothing dates the last snapshot, so it never fires and says why; with
        the fact known and past the threshold, the same rule does fire."""
        block = self.next_of("active_phase_week_unknown")
        unknown = {u["fact"]: u for u in block["unknown"]}
        self.assertEqual(["R-phase-heartbeat"],
                         unknown["phase.days_since_snapshot"]["rules"])
        self.assertNotIn("R-phase-heartbeat", recommended(block))
        self.assertNotIn("phase.days_since_snapshot", {
            u["fact"] for u in self.next_of("okr_no_phase")["unknown"]})

        original = STATE.next_facts

        def known(payload, today, days):
            facts, cannot = original(payload, today)
            cannot.pop("phase.days_since_snapshot")
            facts["phase.days_since_snapshot"] = days
            return facts, cannot

        for days, fires in ((13, False), (14, True)):
            with self.subTest(days=days), mock.patch.object(
                    STATE, "next_facts",
                    lambda p, t, d=days: known(p, t, d)):
                got = self.next_of("active_phase_week_unknown")
            offered = {a["rule"]: a["command"] for a in
                       [got["primary"], *got["alternates"]] if a}
            with self.subTest(days=days):
                self.assertEqual(fires, "R-phase-heartbeat" in offered)
                if fires:
                    self.assertEqual("/perry goals snapshot",
                                     offered["R-phase-heartbeat"])

    def test_met_ratio_is_unknown_while_a_commit_key_result_is_unmeasured(self):
        block = self.next_of("active_phase_week_unknown")
        unknown = {u["fact"]: u for u in block["unknown"]}
        self.assertIn("phase.kr_progress.met_ratio", unknown)
        self.assertIn("1 of 1 commit key results",
                      unknown["phase.kr_progress.met_ratio"]["reason"])
        self.assertNotIn("R-phase-closable", recommended(block))


class TestTheLifecycleRules(Fixtures):
    """TASK-479, DESIGN-020 § 5.10 batch 1: acceptance criteria 1-5."""

    def test_an_unstaffed_kr_is_named_with_its_title_and_edges_silence_it(self):
        block = self.next_of("kr_unstaffed")
        self.assertIn("1 commit key result(s) in phase 001 have no task, starting "
                      "with P001-O1-KR2 (key result P001-O1-KR2)",
                      block["primary"]["reason"])
        staffed = copy.deepcopy(self.payloads["kr_unstaffed"])
        for k in staffed["linkage"]["objectives"][0]["krs"]:
            k["tasks"] = ["TASK-001"]
        got = STATE.build_next(staffed, today=WEDNESDAY)
        self.assertNotIn("R-kr-unstaffed", recommended(got))
        self.assertIsNotNone(got["primary"])

    def test_a_measured_and_met_kr_with_no_task_is_not_unstaffed(self):
        """UD 14. KR1 of `kr_unstaffed` and every closable KR have no task."""
        for name, count in (("closable_phase", 0), ("kr_unstaffed", 1)):
            facts, _u = STATE.next_facts(self.payloads[name], WEDNESDAY)
            with self.subTest(fixture=name):
                self.assertEqual(count, facts["phase.krs_unstaffed"])
        self.assertEqual("P001-O1-KR2", STATE.next_facts(
            self.payloads["kr_unstaffed"], WEDNESDAY)[0]["phase.first_unstaffed_kr"])

    def test_an_undeclared_check_is_named_with_its_title(self):
        block = self.next_of("checks_undeclared")
        self.assertIn("starting with P001-O1-KR1 (key result P001-O1-KR1)",
                      block["primary"]["reason"])

    def test_only_a_retro_naming_this_phase_makes_it_scorable(self):
        root = build(self, "closable_phase")
        retro(root, "000-another")
        self.assertEqual("R-phase-closable", STATE.build_next(
            payload_of(root), today=WEDNESDAY)["primary"]["rule"])
        retro(root, PHASE_SLUG)
        self.assertEqual("R-phase-scorable", STATE.build_next(
            payload_of(root), today=WEDNESDAY)["primary"]["rule"])

    def midweek_run(self, root, *on: str) -> dict:
        """TASK-482: `midweek-check`'s documented write, its commands read from
        the procedure so the two cannot drift; the payload after it."""
        page = (ROOT / "work/reference/subcommands.md").read_text(encoding="utf-8")
        section = page.split("### `midweek-check`", 1)[1].split("\n### ", 1)[0]
        self.assertIn("`perry-task cadence-done <id> --evidence ", section)
        add = re.search(r"`perry-task (cadence-add [^`]+) --actor <actor>`", section).group(1).split()
        def row(payload):
            return next((c["id"] for c in payload["cadence"]["items"]
                         if c["title"] == add[2]), None)
        def task(argv):
            proc = inproc.run("perry-task", argv + ["--root", str(root), "--actor", "t"])
            self.assertEqual(0, proc.returncode, proc.stderr)
        if row(payload_of(root)) is None:
            task(add)
        task(["cadence-done", row(payload_of(root)), "--evidence", "journal/x.md", *on])
        return payload_of(root)

    def test_midweek_fires_until_this_weeks_check_is_recorded(self):
        """A Wednesday with no record, or only last week's, recommends
        `R-midweek` as the second alternate; this week's record silences it,
        and deleting the rule from a copy removes it where it fired."""
        root = build(self, "closable_phase")
        without = [r for r in rules_doc()["rules"] if r["id"] != "R-midweek"]
        for payload, fires in ((payload_of(root), True),
                               (self.midweek_run(root, "--on", "2026-09-09"), True),
                               (self.midweek_run(root, "--on", "2026-09-14"), False)):
            block = STATE.build_next(payload, today=WEDNESDAY)
            # `cadence-done` stamps the next due a week out, so the row this
            # procedure writes is itself overdue once that week has passed —
            # TASK-484 gave that its own rule. Read, not pinned to a date.
            instead = ("R-cadence-overdue" if payload["cadence"]["overdue"]
                       else "R-handoff-stale")
            with self.subTest(fires=fires):
                self.assertEqual(["R-phase-closable", "R-review-due", "R-midweek"
                                  if fires else instead], recommended(block))
                self.assertNotIn("week.midweek_checked",
                                 [u["fact"] for u in block["unknown"]])
                self.assertNotIn("R-midweek", recommended(STATE.build_next(
                    payload, today=WEDNESDAY, rules_path=write_rules(
                        self, {**rules_doc(), "rules": without}))))

    def test_the_documented_write_alone_makes_the_fact_true(self):
        """No `--on`: the run is today, so it counts for this ISO week and
        not for the next one."""
        payload = self.midweek_run(build(self, "installed_no_okr"))
        self.assertTrue(STATE.next_facts(payload, date.today())[0]["week.midweek_checked"])
        self.assertFalse(STATE.next_facts(payload, date.today() + timedelta(days=7))[0][
            "week.midweek_checked"])

    def test_an_unreadable_cadence_store_leaves_the_fact_unknown(self):
        root = build(self, "closable_phase")
        (root / "cadence.jsonl").write_text("{not json\n", encoding="utf-8")
        block = STATE.build_next(payload_of(root), today=WEDNESDAY)
        unknown = {u["fact"]: u["rules"] for u in block["unknown"]}
        self.assertEqual(["R-midweek"], unknown.get("week.midweek_checked"))
        self.assertNotIn("R-midweek", recommended(block))


class TestTheExecutionLoop(Fixtures):
    """TASK-483, DESIGN-020 § 5.10 batch 2: acceptance criteria 1-4."""

    def facts(self, *writes) -> dict:
        root = build(self, "active_phase_week_unknown")
        for write in writes:
            write(root)
        return STATE.next_facts(payload_of(root), WEDNESDAY)[0]

    def counts(self, facts: dict) -> tuple:
        return tuple(facts[f"board.{k}"] for k in (
            "review_owed", "closable", "dispatchable", "blocked_stale"))

    def test_each_fixture_counts_its_one_row_and_names_it_with_its_title(self):
        for name, first in (("review_owed", "TASK-011"), ("closable_row", "TASK-012"),
                            ("dispatchable", "TASK-013"), ("blocked_stale", "TASK-021")):
            block = self.next_of(name)
            with self.subTest(fixture=name):
                self.assertIn(f"{first} (row {first})", block["primary"]["reason"])
        self.assertEqual((1, 1, 1, 0), self.counts(STATE.next_facts(
            self.payloads["busy_board"], WEDNESDAY)[0]))

    def test_a_fail_is_neither_owed_nor_closable_and_the_latest_block_decides(self):
        """The latest block is the highest review round (`verdict_order`); an
        unnumbered file is round 1, as this repository names them."""
        r2, rr2 = "TASK-011-round2-v4-review.md", "TASK-011-v4-review-r2.md"
        hidden = text("evidence/2026-09/c.md", "<!--\n=== VERDICT ===\ntask: TASK-011"
                      "\nrung: V4\nresult: PASS\n=== END VERDICT ===\n-->\n")
        for writes, owed, closable in (
                ((verdict("TASK-011", "FAIL"),), 0, 0),
                ((verdict("TASK-011", "FAIL", "r/round9-v4.md"),
                  verdict("TASK-011", "PASS", "r/round10-v4.md")), 0, 1),
                ((verdict("TASK-011", "PASS", rung="V3"),), 0, 0),
                ((verdict("TASK-011", "FAIL"), verdict("TASK-011", "PASS", r2)), 0, 1),
                ((verdict("TASK-011", "PASS"), verdict("TASK-011", "FAIL", r2)), 0, 0),
                ((verdict("TASK-011", "PASS"), verdict("TASK-011", "FAIL", rr2)), 0, 0),
                ((hidden,), 1, 0)):
            with self.subTest(owed=owed, closable=closable, files=len(writes)):
                self.assertEqual((owed, closable, 0, 0), self.counts(self.facts(OWED, *writes)))
        below = rows(row("TASK-014", "review", rung="V3"))
        for writes in ((below,), (below, verdict("TASK-014", "PASS"))):
            self.assertEqual((0, 0, 0, 0), self.counts(self.facts(*writes)))

    def test_only_an_auto_spec_on_a_startable_p0_or_p1_row_is_dispatchable(self):
        """Criterion 2. The latest month's spec; the whole value; the header block only; two
        different values read `ambiguous`, never `auto` (fails closed: dispatch
        wants an explicit opt-in, `dispatch-preflight.md` step 2); a pending
        ask edge blocks the row and an answered one does not."""
        plain, waits = READY[0], rows(row("TASK-013", "not_started", depends=["USER-001"]))
        def ask(answered):
            return text("asks.jsonl", json.dumps({
                "id": "USER-001", "needed": "q", "blocks": "TASK-013", "asked": "2026-09-10",
                "status": "answered 2026-09-12" if answered else "pending",
                "answered": answered, "order": 1}) + "\n")
        two = "# T\n\n> Dispatch mode: {}\n> Dispatch mode: {}\n\n## Bound\n"
        auto = spec("TASK-013", "auto")
        for writes, count, mode in (
                ((rows(row("TASK-013", "not_started", priority="P0")), auto), 1, "auto"),
                ((rows(row("TASK-013", "not_started", priority="P2")), auto), 0, "auto"),
                ((plain,), 0, ""),
                ((rows(row("TASK-012", "in_progress"), row("TASK-013", "not_started",
                  depends=["TASK-012"])), auto), 0, "auto"),
                ((plain, spec("TASK-013", "auto", "2026-08"), spec("TASK-013", "manual")), 0, "manual"),
                ((plain, spec("TASK-013", "manual", "2026-08"), auto), 1, "auto"),
                ((plain, spec("TASK-013", "auto-review-only")), 0, "auto-review-only"),
                ((plain, spec("TASK-013", "", body=two.format("auto", "manual"))), 0, "ambiguous"),
                ((plain, spec("TASK-013", "", body=two.format("auto", "auto"))), 1, "auto"),
                ((plain, spec("TASK-013", "", body="# T\n\nWhy it matters.\n\n"
                                                   "Dispatch mode: auto\n")), 0, ""),
                ((waits, ask(False), auto), 0, "auto"),
                ((waits, ask(True), auto), 1, "auto")):
            root = build(self, "active_phase_week_unknown")
            for write in writes:
                write(root)
            payload = payload_of(root)
            with self.subTest(count=count, mode=mode):
                self.assertEqual(mode, next(r for r in payload["board"]["execution"]
                                            if r["id"] == "TASK-013")["dispatch_mode"])
                self.assertEqual(count, STATE.next_facts(payload, WEDNESDAY)[0][
                    "board.dispatchable"])

    def test_a_busy_board_finishes_before_it_starts(self):
        """Criterion 4. The control: with `R-dispatchable` moved above the two
        finishing rules, the same payload recommends the dispatch."""
        block = self.next_of("busy_board")
        self.assertIn(block["primary"]["rule"], ("R-review-owed", "R-closable-row"))
        self.assertEqual(["R-review-owed", "R-closable-row", "R-dispatchable"],
                         recommended(block))
        doc = rules_doc()
        moved = [r for r in doc["rules"] if r["id"] == "R-dispatchable"]
        rest = [r for r in doc["rules"] if r["id"] != "R-dispatchable"]
        at = [r["id"] for r in rest].index("R-review-owed")
        got = self.next_of("busy_board", rules_path=write_rules(
            self, {**doc, "rules": rest[:at] + moved + rest[at:]}))
        self.assertEqual("R-dispatchable", got["primary"]["rule"])


class TestCadenceAndOperations(Fixtures):
    """TASK-484, DESIGN-020 § 5.10 batch 3: acceptance criteria 1-4. Each is a
    PAIR — the state that fires the rule, and the nearest state that must not.
    `EXPECTED` pins each fixture's primary and command and
    `TestDeletingARuleReddensItsFixture` removes each new rule from a copy; the
    negative half is here, where no pin can supply it."""

    def over(self, *writes, settings=None) -> tuple[dict, dict, dict]:
        """`(facts, unknown, block)` over the quiet active phase plus `writes`."""
        root = build(self, "active_phase_week_unknown")
        if settings:
            config_store.write_config(root, settings=settings)
        for write in writes:
            write(root)
        got = payload_of(root)
        return (*STATE.next_facts(got, WEDNESDAY),
                STATE.build_next(got, today=WEDNESDAY))

    def pair(self, name: str, *facts: str) -> tuple:
        return tuple(STATE.next_facts(self.payloads[name], WEDNESDAY)[0][f]
                     for f in facts)

    def test_a_waiting_input_and_a_late_cadence_row_each_name_the_first_one(self):
        """Criteria 1 and 2, one shape: a count and the first item it names.
        `EXPECTED_COMMAND` pins `/perry work digest a-brief.md`, so what is here
        is the negative — an empty `inputs/`, a row still inside its period."""
        for name, rule, counted, first, want, quiet in (
                ("inputs_waiting", "R-inputs-waiting", "operations.inputs",
                 "operations.first_input", (1, "a-brief.md"),
                 (lambda root: (root / "inputs").mkdir(),)),
                ("cadence_overdue", "R-cadence-overdue", "cadence.overdue_count",
                 "cadence.first_overdue", (1, "CAD-001"),
                 (cadence_rows(cadence("CAD-001", "weekly close",
                                       next_due=day(9), order=1)),))):
            facts, _u, block = self.over(*QUIET, *quiet)
            with self.subTest(fixture=name):
                self.assertIn(want[1], self.next_of(name)["primary"]["reason"])
                self.assertEqual(want, self.pair(name, counted, first))
                self.assertEqual((0, None), (facts[counted], facts[first]))
                self.assertNotIn(rule, recommended(block))

    def test_only_a_declared_marker_ranks_a_risk_and_no_marker_is_not_unknown(self):
        """Criterion 3. One statement, six front tokens. `""` is an ANSWER: the
        rank comes from a DECLARED marker, never from the sentence (NN-4)."""
        self.assertIn("high", self.next_of("risk_raised")["primary"]["reason"])
        def register(prefix):
            return text("risks.jsonl", json.dumps({
                "kind": "risk", "id": "RX-001", "opened": "2026-09-01",
                "risk": prefix + "the notarization certificate expires this month",
                "status": "open", "order": 0}) + "\n")
        for prefix, rank, fires in (("H · ", "high", True), ("🔴 ", "high", True),
                                    ("M · ", "medium", False), ("L · ", "low", False),
                                    ("URGENT: ", "", False), ("", "", False)):
            facts, unknown, block = self.over(*QUIET, register(prefix))
            with self.subTest(prefix=prefix or "(none)"):
                self.assertEqual(rank, facts["risks.top_rank"])
                self.assertNotIn("risks.top_rank", unknown)
                self.assertEqual(fires, "R-risk-raised" in recommended(block))
        facts, unknown, _b = self.over(*QUIET)      # and with no risk at all
        self.assertEqual("", facts["risks.top_rank"])
        self.assertNotIn("risks.top_rank", unknown)

    def test_a_stale_architecture_needs_the_age_the_document_and_the_pack(self):
        """Criterion 4. Three silences: a fresh review, no `ARCHITECTURE.md`
        (unknown — never a guessed age), and a project without the pack."""
        days = rules_doc()["thresholds"]["architecture_review_days"]["value"]
        self.assertEqual((180, 400, ["software-ops"]), (days, *self.pair(
            "architecture_stale", "architecture.days_since_review", "project.packs")))
        def document(reviewed):
            return text("ARCHITECTURE.md", ARCHITECTURE_MD.format(reviewed=reviewed))
        # The warning and the rule cross on the SAME day. The warning used to
        # wait one longer (`> 180` against `ge 180`), so at exactly the
        # threshold the audit was recommended by a standup silent about it.
        for age, both in ((days - 1, False), (days, True)):
            root = build(self, "active_phase_week_unknown")
            for write in (*QUIET, document(day(-age))):
                write(root)
            got = payload_of(root)
            with self.subTest(age=age):
                self.assertEqual((both, both), (
                    "ARCHITECTURE.md last reviewed" in " ".join(got["warnings"]),
                    "R-architecture-stale" in recommended(
                        STATE.build_next(got, today=WEDNESDAY))))
        for writes, says in (((), "ARCHITECTURE.md"), ((document("soon"),), "soon")):
            facts, unknown, block = self.over(*QUIET, *writes)
            with self.subTest(says=says):
                self.assertNotIn("architecture.days_since_review", facts)
                self.assertIn(says, unknown["architecture.days_since_review"])
                self.assertEqual(["R-architecture-stale"], {
                    u["fact"]: u["rules"] for u in block["unknown"]}[
                        "architecture.days_since_review"])
                self.assertNotIn("R-architecture-stale", recommended(block))
        facts, _u, block = self.over(*QUIET, document(day(-400)), settings={
            **config_store.DEFAULT_SETTINGS, "Packs": "other-pack"})
        self.assertEqual((["other-pack"], 400), (
            facts["project.packs"], facts["architecture.days_since_review"]))
        self.assertNotIn("R-architecture-stale", recommended(block))

    def test_an_unreadable_cadence_store_leaves_both_facts_unknown(self):
        """The register's own failure mode, which `R-midweek` already has: a
        store nothing can parse is reported, never counted as zero overdue."""
        facts, unknown, block = self.over(text("cadence.jsonl", "{not json\n"))
        for fact in ("cadence.overdue_count", "cadence.first_overdue"):
            self.assertNotIn(fact, facts)
            self.assertIn("cadence.jsonl", unknown[fact])
        self.assertEqual(["R-cadence-overdue"], {
            u["fact"]: u["rules"] for u in block["unknown"]}["cadence.overdue_count"])
        self.assertNotIn("R-cadence-overdue", recommended(block))


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
                self.assertEqual("perry-next/1.4", block["contract"])
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
    #: Rules DESIGN-020 does not name, each with its spine and the rule it
    #: follows. The heartbeat carries `goals/SKILL.md`'s old prompt (round 3).
    #: TASK-479 adds DESIGN-020 § 5.10 batch 1 in its declared place.
    #: TASK-484 adds batch 3 and moves nothing: the three event rules land
    #: between R-midweek and R-phase-heartbeat, and R-architecture-stale is
    #: last, both as § 5.10's order has them.
    ADDITIONS = {"R-phase-heartbeat": ("project", "R-risk-raised"),
                 "R-phase-scorable": ("project", "R-phase-closable"),
                 "R-kr-unstaffed": ("project", "R-phase-scorable"),
                 "R-checks-undeclared": ("project", "R-kr-unstaffed"),
                 "R-midweek": ("any", "R-review-due"),
                 "R-review-owed": ("any", "R-week-unplanned"),
                 "R-closable-row": ("any", "R-review-owed"),
                 "R-blocked-stale": ("any", "R-asks-waiting"),
                 "R-dispatchable": ("any", "R-blocked-stale"),
                 "R-inputs-waiting": ("any", "R-midweek"),
                 "R-cadence-overdue": ("any", "R-inputs-waiting"),
                 "R-risk-raised": ("any", "R-cadence-overdue"),
                 "R-architecture-stale": ("any", "R-board-over-cap")}

    def setUp(self):
        self.doc = rules_doc()
        self.ids = [r["id"] for r in self.doc["overlays"] + self.doc["rules"]]

    def test_the_bound_three_overlays_ten_rules_and_the_replacements(self):
        self.assertEqual(["R-recovery", "R-interrupted", "R-draft-waiting"],
                         [r["id"] for r in self.doc["overlays"]])
        sequence = [r["id"] for r in self.doc["rules"]]
        self.assertEqual(list(self.DESIGN_TABLE),
                         [i for i in sequence if i in self.DESIGN_TABLE])
        self.assertEqual(set(self.DESIGN_TABLE) | set(self.REPLACEMENTS)
                         | set(self.ADDITIONS), set(sequence))
        for rid, (spine, follows) in self.ADDITIONS.items():
            self.assertEqual(sequence.index(follows) + 1, sequence.index(rid))
            self.assertEqual(spine, {r["id"]: r["spine"]
                                     for r in self.doc["rules"]}[rid])
        self.assertEqual("R-architecture-stale", sequence[-1])
        self.assertEqual("R-board-over-cap", sequence[-2])
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

    def test_the_architecture_age_is_one_number_and_one_boundary(self):
        """TASK-484 correction. The stale-review warning is raised before any
        rule is evaluated, so the number lives twice; the rule file's note
        claimed a test kept the two equal and none did — changing either
        spelling reddened nothing."""
        rule = next(r for r in self.doc["rules"] if r["id"] == "R-architecture-stale")
        clause = next(c for c in rule["when"]["all"]
                      if c.get("fact") == "architecture.days_since_review")
        self.assertEqual(({"threshold": "architecture_review_days"}, "ge"),
                         (clause["value"], clause["op"]))   # at or over, both sides
        self.assertEqual(STATE.ARCHITECTURE_REVIEW_DAYS,
                         self.doc["thresholds"]["architecture_review_days"]["value"])

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
        # `contains` (TASK-484) is the mirror of `in`: a list fact and a scalar.
        for have, truth in ((["a", "b"], True), (["a"], False), ([], False)):
            self.assertEqual(truth, STATE._compare("contains", have, "b"))
        with self.assertRaises(STATE._RuleError):
            STATE._compare("contains", "ab", "b")
        truth, _f, _u = STATE.next_evaluate(
            {"fact": "installed", "op": "eq", "value": 1},
            {"installed": True}, {}, {})
        self.assertFalse(truth)


class TestKrProgress(unittest.TestCase):
    def test_typed_positions_drive_counts_and_closure(self):
        root = build(self, "closable_phase")
        original = [json.loads(row) for row in
                    (root / "linkage.jsonl").read_text().splitlines()]
        original[1].update(target=400, current=1702)  # Legacy ceiling false positive.
        k1, k2 = "P001-O1-KR1", "P001-O1-KR2"
        for direction, target in (("decrease", 400), ("at_most", 400),
                                  ("at_most", 0), ("increase", 400),
                                  ("at_least", 400), ("done", 1)):
            for values, measured, met in (([], 0, 0), ([target], 1, 1),
                                         ([target, target], 2, 2),
                                         ([1702, target], 2,
                                          1 if direction in ("decrease", "at_most", "done") else 2),
                                         ([0, target], 2,
                                          2 if direction in ("decrease", "at_most") else 1)):
                with self.subTest(direction=direction, values=values):
                    rows = [r for r in original if r["kind"] in ("objective", "kr")]
                    rows += [check(kr=k, direction=direction, target=target)
                             for k in (k1, k2)]
                    rows += [measurement(v, kr=k, asserted_at=(date.today().isoformat()
                             if k == k1 else "2020-01-01") + "T00:00:00Z")
                             for k, v in zip((k1, k2), values)]
                    (root / "linkage.jsonl").write_text(jsonl(rows))
                    payload = payload_of(root)
                    self.assertEqual(["measured", "due"][:len(values)],
                                     [k["state"] for k in payload["linkage"]["objectives"][0]["krs"][:len(values)]])
                    counts, why = STATE.next_kr_progress(payload)
                    self.assertEqual((dict(commit_total=2, measured=measured,
                                           met=met, unmeasured=2-measured), ""), (counts, why))
                    self.assertEqual(met == 2, "R-phase-closable" in
                                     recommended(payload["next"]))
        for extra, measured, met in (([], 0, None), ([check(kr=k1)], 0, None),
                ([check(kr=k1), measurement(400, kr=k1), check("other", kr=k1)], 0, None),
                ([check(kr=k1), measurement(400, kr=k1), check("other", kr=k1),
                  measurement(1702, kr=k1, cid="other")], 1, False),
                ([check(kr=k1), measurement(400, kr=k1), check("other", kr=k1),
                  measurement(400, kr=k1, cid="other")], 1, True)):
            rows = [r for r in original if r["kind"] in ("objective", "kr")]
            (root / "linkage.jsonl").write_text(jsonl(rows + extra))
            payload = payload_of(root)
            self.assertEqual(measured, STATE.next_kr_progress(payload)[0]["measured"])
            self.assertIs(met, payload["linkage"]["objectives"][0]["krs"][0]["met"])
            self.assertNotIn("R-phase-closable", recommended(payload["next"]))

    def test_absent_or_mismatched_linkage_fails_closed(self):
        for phase, linkage in ((None, None), ({"slug": "002-y"}, None),
                               ({"slug": "002-y"}, {"phase": "001-x"})):
            counts, why = STATE.next_kr_progress({"phase": phase, "linkage": linkage})
            self.assertEqual({}, counts)
            self.assertEqual(bool(phase), bool(why))


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
