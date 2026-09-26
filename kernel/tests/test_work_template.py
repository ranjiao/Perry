"""The work lane's method as data: `templates/process/perry.json` (TASK-488).

DESIGN-023 § 6 row C. The five work-lane types — task, ask, risk, intake and
cadence — reproduce what `bin/perry-task` runs today (DESIGN-023 § 3), with
the two carried requirements the spec names. This module holds the file to
the spec's acceptance criteria 1, 2 and 4:

- the kernel's `template validate` accepts the file, in process and through
  the executable;
- every type is driven through every transition, from every state a
  transition names, and the set driven is derived from the file, so a new
  transition is covered the day it lands;
- every guard in the file is shown refusing (or, for a warn-mode `limit`,
  warning) where the method refuses, and standing aside where it does not;
- the file declares no tracks and no project settings until the user decides
  where they live (spec criterion 4), and a track-dependent rule is shown
  expressible once tracks are data (`TestTrackRulesOnceTracksAreData`).

Criterion 3, the Goal 1 grep, is `test_vocabulary.py`.

The names here are the template's, which is why this is a test and not kernel
source: `test_vocabulary` scans `perry_kernel/` and the wrapper, never tests.
"""

from __future__ import annotations

import copy
import json
import unittest
from collections import deque

from support import ACTOR, HUMAN, REPO, Sandbox

SHIPPED = REPO / "templates" / "process" / "perry.json"
DAY = "2026-09-26"
REVIEWER = {"kind": "agent", "name": "fresh-reviewer", "session": "fresh-ctx-1"}
SIGNER = {"kind": "human", "name": "Pat"}

#: What each type needs at `item create` to pass its create guards.
CREATE = {
    "task": {"title": "Parser resolves columns by name",
             "gist": "Two parsers disagreed; one reads the header by name.",
             "deliverable": "viewer/parsers.py resolves by name, with a test",
             "verification_check": "the round-trip test passes on both boards"},
    "ask": {"question": "Which staleness threshold?", "asked_on": DAY},
    "risk": {"concern": "The store sits where no one sees it.",
             "opened": DAY},
    "intake": {"request": "Export the board as CSV", "arrived": DAY},
    "cadence": {"title": "Friday review", "frequency": "weekly",
                "next_due": "2026-10-02"},
}

#: What each transition needs in `set` to pass its guards. A callable is
#: given the sandbox, for a value that is another item's id.
PASS = {
    ("task", "start"): {},
    ("task", "block"): {"block_reason": "waiting on USER-001"},
    ("task", "submit"): {},
    ("task", "reset"): {},
    ("task", "restage_not_started"): {"stage": "draft", "stage_since": DAY},
    ("task", "restage_blocked"): {"stage": "draft", "stage_since": DAY},
    ("task", "restage_in_progress"): {"stage": "draft", "stage_since": DAY},
    ("task", "restage_review"): {"stage": "draft", "stage_since": DAY},
    ("task", "done"): {"evidence": "perry/evidence/2026-09/TASK-1-close.md",
                       "verification": "V3"},
    ("task", "drop"): {"drop_reason": "superseded by TASK-2"},
    ("ask", "answer"): {"answer": "30 days"},
    ("risk", "clear"): {"clear_reason": "the export is committed"},
    ("intake", "route"): lambda sb: {"routed_to": sb.create("task",
                                                             CREATE["task"])},
    ("intake", "drop"): {"resolve_reason": "out of scope"},
    ("intake", "postpone"): {"resolve_reason": "after the release"},
    ("cadence", "record_run"): {"last_run": DAY,
                                "last_evidence": "journal/2026-09/26.md",
                                "next_due": "2026-10-09"},
}

V0_GUARD = {"kind": "required", "at_least": {"verification": "V1"},
            "when": {"verification": ["V0"]}}
RESTAGES = ("restage_not_started", "restage_blocked", "restage_in_progress",
            "restage_review")


def shipped() -> dict:
    return json.loads(SHIPPED.read_text(encoding="utf-8"))


def pass_data(sb, type_name: str, transition: str) -> dict:
    data = PASS[(type_name, transition)]
    return data(sb) if callable(data) else dict(data)


def path_to(tpl: dict, type_name: str, start: str, goal: str) -> list[str]:
    """The shortest run of transitions from `start` to `goal`."""
    decl = tpl["types"][type_name]
    seen, queue = {start}, deque([(start, [])])
    while queue:
        state, path = queue.popleft()
        if state == goal:
            return path
        for name, t in sorted(decl["transitions"].items()):
            if state in t["from"] and t["to"] not in seen:
                seen.add(t["to"])
                queue.append((t["to"], path + [name]))
    raise AssertionError(f"{type_name}: no path from {start} to {goal}")


def reach(sb, tpl, type_name: str, item: str, goal: str) -> None:
    state = sb.get(item)["state"]
    for name in path_to(tpl, type_name, state, goal):
        sb.move(item, name, set=pass_data(sb, type_name, name))


def attempt(sb, item, transition, *, actor=None, **extra):
    return sb.run("item", "move", data={"actor": actor or ACTOR, "id": item,
                                        "transition": transition, **extra})


def missing(r) -> list[str]:
    return sorted({f for g in r.details["guards"] if g["kind"] == "required"
                   for f in g["detail"]["missing"]})


def below(r) -> list[tuple]:
    return sorted((f, v["value"], v["at_least"])
                  for g in r.details["guards"] if g["kind"] == "required"
                  for f, v in g["detail"]["below"].items())


class WorkCase(unittest.TestCase):
    """A sandbox with the shipped template applied."""

    def setUp(self):
        self.tpl = shipped()
        self.sb = Sandbox(self).ready(self.tpl)

    def new(self, type_name: str, state: str | None = None, **fields) -> str:
        item = self.sb.create(type_name, {**CREATE[type_name], **fields})
        if state is not None:
            reach(self.sb, self.tpl, type_name, item, state)
        return item

    def refused(self, r):
        self.assertEqual((r.code, r.code_name), (1, "guard_refused"), r)
        return r

    def written(self, r):
        self.assertTrue(r.ok, r)
        self.assertEqual(r.env["effect"], "written", r)
        return r


# ── criterion 1 ────────────────────────────────────────────────────────────


class TestTheKernelAcceptsTheTemplate(unittest.TestCase):

    def test_template_validate_accepts_the_file(self):
        sb = Sandbox(self)
        r = sb.ok("template validate", data={"template": shipped()},
                  root=False)
        self.assertEqual(r, {"valid": True, "format": 1, "types": 5})

    def test_through_the_executable_as_the_skill_calls_it(self):
        sb = Sandbox(self)
        wrapped = sb.tmp / "input.json"
        wrapped.write_text(json.dumps({"template": shipped()}))
        r = sb.cli("template", "validate", data=f"@{wrapped}", root=False)
        self.assertEqual((r.code, r.result),
                         (0, {"valid": True, "format": 1, "types": 5}), r)

    def test_apply_writes_it_and_show_returns_it_verbatim(self):
        sb = Sandbox(self).ready(shipped())
        shown = sb.ok("template show")
        self.assertEqual((shown["template"], shown["version"]),
                         (shipped(), 1))


class TestTheTemplateIsTheWorkLane(unittest.TestCase):
    """What the file declares, read from the file (spec § Deliverable)."""

    def setUp(self):
        self.tpl = shipped()
        self.task = self.tpl["types"]["task"]

    def test_the_five_work_lane_types_and_no_other(self):
        self.assertEqual(set(self.tpl["types"]),
                         {"task", "ask", "risk", "intake", "cadence"})
        self.assertEqual({t: d["prefix"] for t, d in self.tpl["types"].items()},
                         {"task": "TASK", "ask": "USER", "risk": "RX",
                          "intake": "IN", "cadence": "CAD"})

    def schema_enum(self, name: str) -> list:
        """The method is reproduced, not changed (DESIGN-023 § 3), so these
        lists are compared with the declaration `bin/` enforces today rather
        than copied. `schema/state-schema.json` is deleted at DESIGN-023 § 6
        row H; the row that deletes it turns these into literals."""
        schema = json.loads((REPO / "schema" / "state-schema.json")
                            .read_text(encoding="utf-8"))
        return schema["enums"][name]

    def test_task_states_are_the_status_enum(self):
        self.assertEqual(self.task["states"], self.schema_enum("task_status"))
        self.assertEqual(self.task["terminal"], ["done", "dropped"])
        self.assertEqual(self.task["fields"]["priority"]["values"],
                         self.schema_enum("priority"))
        self.assertEqual(self.task["fields"]["owner"]["values"],
                         self.schema_enum("owner"))

    def test_rungs_are_an_ordered_enum_v0_to_v6(self):
        rung = self.task["fields"]["verification"]
        self.assertEqual(rung, {"kind": "enum", "ordered": True,
                                "values": self.schema_enum(
                                    "verification_rung")})
        self.assertEqual(rung["values"][0], "V0")

    def test_no_tracks_and_no_settings_are_declared(self):
        """Spec criterion 4: until the user decides where tracks and settings
        live, the template names none. `track` and `stage` are free text, no
        guard is conditioned on a track, and no relation kind is declared."""
        self.assertEqual(self.task["fields"]["track"], {"kind": "text"})
        self.assertEqual(self.task["fields"]["stage"], {"kind": "text"})
        self.assertEqual(self.tpl["relations"], {})
        for type_name, decl in self.tpl["types"].items():
            guards = list(decl.get("create_guards", []))
            for t in decl["transitions"].values():
                guards += t["guards"]
            for g in guards:
                self.assertNotIn("track", g.get("when") or {}, (type_name, g))


# ── criterion 2: every transition ─────────────────────────────────────────


class TestEveryTransitionIsDriven(WorkCase):

    def test_every_type_through_every_transition_from_every_state(self):
        declared, driven = set(), set()
        for type_name, decl in self.tpl["types"].items():
            for name, t in decl["transitions"].items():
                for origin in t["from"]:
                    declared.add((type_name, name, origin))
                    with self.subTest(type=type_name, transition=name,
                                      origin=origin):
                        item = self.new(type_name, origin)
                        self.assertEqual(self.sb.get(item)["state"], origin)
                        r = self.sb.move(item, name, set=pass_data(
                            self.sb, type_name, name))
                        self.assertEqual((r["from_state"], r["to_state"]),
                                         (origin, t["to"]))
                        self.assertEqual(self.sb.get(item)["state"], t["to"])
                        driven.add((type_name, name, origin))
        self.assertEqual(driven, declared)
        self.assertGreaterEqual(len(declared), 30)

    def test_a_closed_item_moves_no_further(self):
        for type_name, decl in self.tpl["types"].items():
            for terminal in decl["terminal"]:
                if not any(t["to"] == terminal
                           for t in decl["transitions"].values()):
                    continue  # the cadence's end state, which no step reaches
                with self.subTest(type=type_name, state=terminal):
                    item = self.new(type_name, terminal)
                    for name in decl["transitions"]:
                        r = attempt(self.sb, item, name,
                                    set=pass_data(self.sb, type_name, name))
                        self.assertEqual(r.code_name,
                                         "transition_not_allowed", r)


# ── criterion 2: every guard ──────────────────────────────────────────────


class TestTaskCreate(WorkCase):

    def test_a_task_is_born_with_its_definition(self):
        """`perry-task add` refuses a row without a title, a deliverable, a
        falsifiable check or a summary."""
        for field in CREATE["task"]:
            with self.subTest(field=field):
                fields = {k: v for k, v in CREATE["task"].items()
                          if k != field}
                r = self.refused(self.sb.run("item", "create", data={
                    "actor": ACTOR, "type": "task", "fields": fields}))
                self.assertEqual(missing(r), [field])
        self.assertEqual(self.sb.get(self.new("task"))["state"], "not_started")

    def test_v0_is_refused_at_create_and_no_rung_is_not(self):
        r = self.refused(self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "task",
            "fields": {**CREATE["task"], "verification": "V0"}}))
        self.assertEqual(below(r), [("verification", "V0", "V1")])
        for rung in (None, "V1", "V6"):
            with self.subTest(rung=rung):
                self.new("task", verification=rung)


class TestV0IsAlwaysRefused(WorkCase):
    """`check_rung`: "V0 is refused by name wherever a rung is written"."""

    def test_every_transition_refuses_an_item_at_v0(self):
        """`item update` runs no guards (§ 5.6), so V0 can be written there —
        the one place the kernel cannot refuse it. Every transition then
        refuses, so an item at V0 cannot move until its rung changes."""
        for name, t in self.tpl["types"]["task"]["transitions"].items():
            with self.subTest(transition=name):
                item = self.new("task", t["from"][0])
                self.assertTrue(self.sb.run("item", "update", data={
                    "actor": ACTOR, "id": item,
                    "set": {"verification": "V0"}}).ok)
                data = pass_data(self.sb, "task", name)
                data.pop("verification", None)
                r = self.refused(attempt(self.sb, item, name, set=data))
                self.assertIn(("verification", "V0", "V1"), below(r))
                r = attempt(self.sb, item, name,
                            set={**data, "verification": "V2"})
                self.assertTrue(r.ok, r)


class TestTaskMoves(WorkCase):

    def test_blocked_needs_what_it_waits_on(self):
        for origin in self.tpl["types"]["task"]["transitions"]["block"]["from"]:
            with self.subTest(origin=origin):
                item = self.new("task", origin)
                r = self.refused(attempt(self.sb, item, "block"))
                self.assertEqual(missing(r), ["block_reason"])

    def test_a_stage_move_restamps_its_clock_in_the_same_write(self):
        for name in RESTAGES:
            origin = self.tpl["types"]["task"]["transitions"][name]["from"][0]
            with self.subTest(transition=name):
                item = self.new("task", origin)
                r = self.refused(attempt(self.sb, item, name,
                                         set={"stage": "draft"}))
                self.assertEqual(missing(r), ["stage_since"])
                r = self.refused(attempt(self.sb, item, name,
                                         set={"stage_since": DAY}))
                self.assertEqual(missing(r), ["stage"])
                self.written(attempt(self.sb, item, name,
                                     set={"stage": "draft",
                                          "stage_since": DAY}))
                self.assertEqual(self.sb.get(item)["state"], origin)

    def test_drop_needs_its_reason(self):
        item = self.new("task", "in_progress")
        r = self.refused(attempt(self.sb, item, "drop"))
        self.assertEqual(missing(r), ["drop_reason"])


class TestDone(WorkCase):
    """The close gate: evidence, a rung, and the three conditional rules."""

    def close(self, item, actor=None, **fields):
        return attempt(self.sb, item, "done", actor=actor,
                       set={"evidence": "perry/evidence/x.md", **fields})

    def test_done_needs_evidence_and_a_rung(self):
        item = self.new("task", "in_progress")
        r = self.refused(attempt(self.sb, item, "done",
                                 set={"verification": "V3"}))
        self.assertEqual(missing(r), ["evidence"])
        r = self.refused(self.close(item))
        self.assertEqual(below(r), [("verification", None, "V1")])
        r = self.refused(self.close(item, verification="V0"))
        self.assertEqual(below(r), [("verification", "V0", "V1")])
        self.written(self.close(item, verification="V1"))

    def test_high_stakes_work_needs_v5(self):
        """DESIGN-003 § 5.3 rule 1: consequence beats the mode default."""
        verdict = {"review_result": "PASS", "review_criteria": "spec.md",
                   "reviewer": REVIEWER}
        for rung in ("V1", "V3", "V4"):
            with self.subTest(rung=rung):
                item = self.new("task", "review", high_stakes=True, **verdict)
                r = self.refused(self.close(item, verification=rung))
                self.assertEqual(below(r), [("verification", rung, "V5")])
        signed = {"signer": SIGNER, "signed_on": DAY,
                  "signoff_checked": ["the diff touches no claim"]}
        item = self.new("task", "review", high_stakes=True)
        self.written(self.close(item, HUMAN, verification="V5", **signed))
        item = self.new("task", "review", high_stakes=True)
        self.written(self.close(item, verification="V6"))
        for flag in (False, None):
            with self.subTest(high_stakes=flag):
                item = self.new("task", "review", high_stakes=flag)
                self.written(self.close(item, verification="V3"))

    def test_v4_needs_a_passing_verdict_record(self):
        """TASK-291, carried: a V4 close reads a typed verdict on the item."""
        item = self.new("task", "review")
        r = self.refused(self.close(item, verification="V4"))
        self.assertEqual(missing(r), ["review_criteria", "reviewer"])
        self.assertEqual(below(r), [("review_result", None, "PASS")])
        r = self.refused(self.close(
            item, verification="V4", review_result="FAIL",
            review_criteria="perry/evidence/2026-09/TASK-1-spec.md",
            reviewer=REVIEWER, review_proof="bin/x:12 is unguarded"))
        self.assertEqual(below(r), [("review_result", "FAIL", "PASS")])
        self.written(self.close(
            item, verification="V4", review_result="PASS",
            review_criteria="perry/evidence/2026-09/TASK-1-spec.md",
            reviewer=REVIEWER))
        for rung in ("V3", "V5", "V6"):  # the rule is V4's alone
            with self.subTest(rung=rung):
                other = self.new("task", "review")
                extra = ({"signer": SIGNER, "signed_on": DAY,
                          "signoff_checked": ["x"]} if rung == "V5" else {})
                self.written(self.close(other, HUMAN, verification=rung,
                                        **extra))

    def test_the_verdict_is_typed_and_never_parsed_from_prose(self):
        item = self.new("task", "review")
        block = ("=== VERDICT ===\ntask: TASK-001\nrung: V4\nresult: PASS\n"
                 "criteria: spec.md\n=== END VERDICT ===")
        r = self.refused(self.close(item, verification="V4",
                                    evidence=block, review_proof=block))
        self.assertIn(("review_result", None, "PASS"), below(r))
        for bad in ("pass", "PASS ", "**PASS**", True):
            with self.subTest(value=bad):
                r = self.sb.run("item", "update", data={
                    "actor": ACTOR, "id": item,
                    "set": {"review_result": bad}})
                self.assertEqual(r.code_name, "field_invalid", r)
        r = self.sb.run("item", "update", data={
            "actor": ACTOR, "id": item,
            "set": {"reviewer": "fresh-reviewer"}})
        self.assertEqual(r.code_name, "field_invalid", r)

    def test_v5_needs_the_signature_on_the_item(self):
        """DESIGN-023 § 5.4: signer, date and what they checked are fields,
        written in the same transaction as the close."""
        signed = {"signer": SIGNER, "signed_on": DAY,
                  "signoff_checked": ["claims[] has zero lines in the diff"]}
        for field in signed:
            with self.subTest(field=field):
                item = self.new("task", "review")
                partial = {k: v for k, v in signed.items() if k != field}
                r = self.refused(self.close(item, HUMAN, verification="V5",
                                            **partial))
                self.assertEqual(missing(r), [field])
        item = self.new("task", "review")
        self.written(self.close(item, HUMAN, verification="V5", **signed))
        self.assertEqual(self.sb.get(item)["fields"]["signer"],
                         {**SIGNER, "session": None})

    def test_v5_is_closed_by_a_human(self):
        """DESIGN-023 § 5.2: the guard makes a V5 close name a human; it does
        not authenticate one."""
        signed = {"signer": SIGNER, "signed_on": DAY,
                  "signoff_checked": ["x"]}
        item = self.new("task", "review")
        r = self.refused(self.close(item, ACTOR, verification="V5", **signed))
        (failure,) = r.details["guards"]
        self.assertEqual((failure["kind"], failure["detail"]["needs"]),
                         ("actor", {"actor_kind": "human"}))
        self.written(self.close(item, HUMAN, verification="V5", **signed))


class TestWip(WorkCase):
    """WIP as a grouped `limit` in `warn` mode (DESIGN-023 decision 9). The
    limits are the schema's mode defaults, `review:3` (pipeline) and `open:5`
    (inquiry), counted per track and stage. Warn never refuses."""

    LIMITS = (("review", 3), ("open", 5))

    def assert_warned(self, r, stage, count, limit, track):
        self.written(r)
        (warning,) = r.env["warnings"]
        self.assertEqual((warning["code"], warning["kind"], warning["when"],
                          warning["detail"]),
                         ("limit_exceeded", "limit", {"stage": [stage]},
                          {"count": count, "max": limit,
                           "values": {"track": track, "stage": stage}}))

    def test_a_stage_move_past_the_limit_warns_and_proceeds(self):
        for name in RESTAGES:
            origin = self.tpl["types"]["task"]["transitions"][name]["from"][0]
            for stage, limit in self.LIMITS:
                with self.subTest(transition=name, stage=stage):
                    track = f"t-{name}-{stage}"
                    items = [self.new("task", origin, track=track,
                                      stage="draft")
                             for _ in range(limit + 1)]
                    move = {"stage": stage, "stage_since": DAY}
                    for item in items[:limit]:
                        r = self.written(attempt(self.sb, item, name,
                                                 set=move))
                        self.assertEqual(r.env["warnings"], [])
                    self.assert_warned(attempt(self.sb, items[-1], name,
                                               set=move),
                                       stage, limit + 1, limit, track)

    def test_a_row_born_past_the_limit_warns(self):
        for stage, limit in self.LIMITS:
            with self.subTest(stage=stage):
                track = f"born-{stage}"
                fields = {**CREATE["task"], "track": track, "stage": stage}
                for _ in range(limit):
                    r = self.sb.run("item", "create", data={
                        "actor": ACTOR, "type": "task", "fields": fields})
                    self.assertEqual(r.env["warnings"], [], r)
                r = self.sb.run("item", "create", data={
                    "actor": ACTOR, "type": "task", "fields": fields})
                self.assert_warned(r, stage, limit + 1, limit, track)

    def test_the_count_is_per_track_and_stage(self):
        for n in range(3):
            self.new("task", track="pub", stage="review")
        r = self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "task",
            "fields": {**CREATE["task"], "track": "ops", "stage": "review"}})
        self.assertEqual(r.env["warnings"], [], r)
        r = self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "task",
            "fields": {**CREATE["task"], "track": "pub", "stage": "draft"}})
        self.assertEqual(r.env["warnings"], [], r)


class TestRegisters(WorkCase):
    """The ask, risk, intake and cadence registers."""

    def create_refused(self, type_name, field):
        fields = {k: v for k, v in CREATE[type_name].items() if k != field}
        return self.refused(self.sb.run("item", "create", data={
            "actor": ACTOR, "type": type_name, "fields": fields}))

    def test_each_register_row_is_born_with_what_its_writer_requires(self):
        for type_name in ("ask", "risk", "intake", "cadence"):
            for field in CREATE[type_name]:
                with self.subTest(type=type_name, field=field):
                    self.assertEqual(
                        missing(self.create_refused(type_name, field)), [field])

    def test_an_answer_is_recorded_once(self):
        ask = self.new("ask")
        r = self.refused(attempt(self.sb, ask, "answer"))
        self.assertEqual(missing(r), ["answer"])
        self.sb.move(ask, "answer", set={"answer": "30 days"})
        r = attempt(self.sb, ask, "answer", set={"answer": "60 days"})
        self.assertEqual(r.code_name, "transition_not_allowed", r)

    def test_an_ask_blocks_the_task_until_it_is_answered(self):
        ask = self.new("ask")
        task = self.sb.create("task", CREATE["task"],
                              relations=[{"kind": "blocks", "from": ask}])
        self.assertEqual(self.sb.get(task)["blocked_by"], [ask])
        self.sb.move(ask, "answer", set={"answer": "yes"})
        self.assertTrue(self.sb.get(task)["startable"])

    def test_a_risk_is_cleared_once_and_with_its_reason(self):
        risk = self.new("risk")
        r = self.refused(attempt(self.sb, risk, "clear"))
        self.assertEqual(missing(r), ["clear_reason"])
        self.sb.move(risk, "clear", set={"clear_reason": "mitigated"})
        r = attempt(self.sb, risk, "clear", set={"clear_reason": "again"})
        self.assertEqual(r.code_name, "transition_not_allowed", r)

    def test_an_intake_row_takes_exactly_one_outcome(self):
        cases = {"route": "routed_to", "drop": "resolve_reason",
                 "postpone": "resolve_reason"}
        for name, field in cases.items():
            with self.subTest(transition=name):
                row = self.new("intake")
                r = self.refused(attempt(self.sb, row, name))
                self.assertEqual(missing(r), [field])
                self.sb.move(row, name, set=pass_data(self.sb, "intake", name))
                for other in cases:
                    r = attempt(self.sb, row, other,
                                set=pass_data(self.sb, "intake", other))
                    self.assertEqual(r.code_name, "transition_not_allowed", r)

    def test_an_intake_row_routes_to_a_task_only(self):
        row, ask = self.new("intake"), self.new("ask")
        r = attempt(self.sb, row, "route", set={"routed_to": ask})
        self.assertFalse(r.ok, r)
        self.assertEqual(r.code_name, "field_invalid", r)

    def test_a_cadence_run_records_its_date_and_evidence(self):
        """`cadence-done` refuses a run without evidence and restamps the
        run date and the next due date in the same write. The kernel does
        not compute `next_due`: the caller does, and the guard sees it set."""
        cad = self.new("cadence")
        run = PASS[("cadence", "record_run")]
        for field in ("last_run", "last_evidence"):
            with self.subTest(field=field):
                partial = {k: v for k, v in run.items() if k != field}
                r = self.refused(attempt(self.sb, cad, "record_run",
                                         set=partial))
                self.assertEqual(missing(r), [field])
        partial = {k: v for k, v in run.items() if k != "next_due"}
        r = self.refused(attempt(self.sb, cad, "record_run", set=partial,
                                 unset=["next_due"]))
        self.assertEqual(missing(r), ["next_due"])
        self.written(attempt(self.sb, cad, "record_run", set=run))
        self.assertEqual(self.sb.get(cad)["state"], "active")


# ── spec criterion 4: expressible once tracks are data ─────────────────────


def with_tracks(tpl: dict) -> dict:
    """The shipped template as it would read if tracks were template data:
    `track` an enum of declared names, and each track's default rung a `when`
    guard on `done`. Built here, in memory, to show the rule is expressible;
    the shipped file declares no track (criterion 4)."""
    out = copy.deepcopy(tpl)
    task = out["types"]["task"]
    task["fields"]["track"] = {"kind": "enum", "values": ["main", "ops"]}
    task["transitions"]["done"]["guards"] += [
        {"kind": "required", "at_least": {"verification": "V2"},
         "when": {"track": ["main"]}},
        {"kind": "required", "at_least": {"verification": "V3"},
         "when": {"track": ["ops"]}}]
    out["version"] = tpl["version"] + 1
    return out


class TestTrackRulesOnceTracksAreData(unittest.TestCase):

    def test_each_tracks_default_rung_is_a_when_guard(self):
        tpl = with_tracks(shipped())
        sb = Sandbox(self)
        self.assertTrue(sb.ok("template validate", data={"template": tpl},
                              root=False)["valid"])
        sb.ready(tpl)

        def close(track, rung):
            item = sb.create("task", {**CREATE["task"], "track": track})
            return attempt(sb, item, "done", set={
                "evidence": "e.md", "verification": rung})

        r = close("ops", "V2")
        self.assertEqual(below(r), [("verification", "V2", "V3")])
        self.assertTrue(close("ops", "V3").ok)
        self.assertTrue(close("main", "V2").ok)
        self.assertEqual(below(close("main", "V1")),
                         [("verification", "V1", "V2")])

    def test_making_track_an_enum_is_refused_once_a_value_is_stored(self):
        """`text` → `enum` is a kind change, and a kind change on a field
        that holds a value is `template_incompatible` (§ 5.2). So the tracks
        decision must land before an import writes any `track` value."""
        sb = Sandbox(self).ready(shipped())
        sb.create("task", {**CREATE["task"], "track": "main"})
        r = sb.run("template", "apply", data={
            "actor": ACTOR, "template": with_tracks(shipped())})
        self.assertEqual(r.code_name, "template_incompatible", r)


if __name__ == "__main__":
    unittest.main()
