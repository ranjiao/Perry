"""The work lane's method as data: `templates/process/perry.json` (TASK-488).

DESIGN-023 § 6 row C, round 2. The file holds exactly DESIGN-023 decision
13's pruned method — the types `task`, `ask` and `risk` with their fields,
states and guards — and decision 14's `track` enum. The spec's acceptance
criteria this module holds:

- 1: the kernel's `template validate` accepts the file, in process and
  through the executable;
- 7: the file's types, fields, states, transitions, relations and guards are
  exactly decision 13's list (`TestTheTemplateIsDecisionThirteen`). The list is
  written out below as literals, so the comparison reads the decision, not
  the file;
- 2: every type is driven through every transition from every state the
  transition names. The set driven is derived from the file, so a new
  transition is covered the day it lands;
- 2 and 8: each decision-13 guard is shown refusing where the method refuses
  and standing aside where it does not. A mutant of any of those guards in
  the file turns the refusing test red.

Criterion 3, the Goal 1 grep, is `test_vocabulary.py`.

The names here are the template's, which is why this is a test and not kernel
source: `test_vocabulary` scans `perry_kernel/` and the wrapper, never tests.
"""

from __future__ import annotations

import json
import unittest
from collections import deque

from support import ACTOR, HUMAN, REPO, Sandbox

SHIPPED = REPO / "templates" / "process" / "perry.json"
REVIEWER = {"kind": "agent", "name": "fresh-reviewer", "session": "fresh-ctx-1"}
RUNGS = ["V1", "V2", "V3", "V4", "V5", "V6"]
EVIDENCE = "perry/evidence/2026-09/TASK-001-close.md"

# ── decision 13, written out ───────────────────────────────────────────────

TEXT = {"kind": "text"}
TASK_STATES = ["not_started", "blocked", "in_progress", "review", "done",
               "dropped"]
OPEN_TASK = ["not_started", "blocked", "in_progress", "review"]
REQUIRE_REASON = [{"kind": "required", "fields": ["reason"]}]

DECISION_13 = {
    "task": {
        "prefix": "TASK", "digits": 3,
        "states": TASK_STATES, "initial": "not_started",
        "terminal": ["done", "dropped"],
        "fields": {
            "title": TEXT,
            "summary": TEXT,
            "priority": {"kind": "enum", "values": ["P0", "P1", "P2"]},
            "owner": {"kind": "enum", "values": [
                "User", "PMO Agent", "Coding Agent", "Research Agent",
                "Review Agent", "User + Agent"]},
            "track": {"kind": "enum", "values": ["main", "intake"]},
            "verification": {"kind": "enum", "values": RUNGS,
                             "ordered": True},
            "next_action": TEXT,
            "evidence": TEXT,
            "reason": TEXT,
            "verified_by": {"kind": "actor"},
        },
        "create_guards": [{"kind": "required", "fields": [
            "title", "summary", "priority", "verification"]}],
        "transitions": {
            "start": {"from": ["not_started", "blocked", "review"],
                      "to": "in_progress", "guards": []},
            "block": {"from": ["not_started", "in_progress", "review"],
                      "to": "blocked", "guards": REQUIRE_REASON},
            "submit": {"from": ["not_started", "blocked", "in_progress"],
                       "to": "review", "guards": []},
            "reset": {"from": ["blocked", "in_progress", "review"],
                      "to": "not_started", "guards": []},
            "done": {"from": OPEN_TASK, "to": "done", "guards": [
                {"kind": "required", "fields": ["evidence"]},
                {"kind": "required", "fields": ["verified_by"],
                 "when": {"verification": ["V4"]}},
                {"kind": "actor", "actor_kind": "human",
                 "when": {"verification": ["V5"]}}]},
            "drop": {"from": OPEN_TASK, "to": "dropped",
                     "guards": REQUIRE_REASON},
        },
    },
    "ask": {
        "prefix": "USER", "digits": 3,
        "states": ["pending", "answered"], "initial": "pending",
        "terminal": ["answered"],
        "fields": {"question": TEXT, "answer": TEXT},
        "create_guards": [{"kind": "required", "fields": ["question"]}],
        "transitions": {
            "answer": {"from": ["pending"], "to": "answered", "guards": [
                {"kind": "required", "fields": ["answer"]}]},
        },
    },
    "risk": {
        "prefix": "RX", "digits": 3,
        "states": ["open", "cleared"], "initial": "open",
        "terminal": ["cleared"],
        "fields": {"concern": TEXT, "reason": TEXT},
        "create_guards": [],
        "transitions": {
            "clear": {"from": ["open"], "to": "cleared",
                      "guards": REQUIRE_REASON},
        },
    },
}

#: What each type needs at `item create` to pass its create guards.
CREATE = {
    "task": {"title": "Parser resolves columns by name",
             "summary": "viewer/parsers.py reads the header by name; the "
                        "round-trip test passes on both boards.",
             "priority": "P1", "verification": "V3"},
    "ask": {"question": "Which staleness threshold?"},
    "risk": {},
}

#: What each transition needs in `set` to pass its guards, at the rung
#: `CREATE` gives a task (V3, where no rung rule applies).
PASS = {
    ("task", "start"): {},
    ("task", "block"): {"reason": "waiting on USER-001"},
    ("task", "submit"): {},
    ("task", "reset"): {},
    ("task", "done"): {"evidence": EVIDENCE},
    ("task", "drop"): {"reason": "superseded by TASK-002"},
    ("ask", "answer"): {"answer": "30 days"},
    ("risk", "clear"): {"reason": "the export is committed"},
}


def shipped() -> dict:
    return json.loads(SHIPPED.read_text(encoding="utf-8"))


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


def attempt(sb, item, transition, *, actor=None, **extra):
    return sb.run("item", "move", data={"actor": actor or ACTOR, "id": item,
                                        "transition": transition, **extra})


def missing(r) -> list[str]:
    return sorted({f for g in r.details["guards"] if g["kind"] == "required"
                   for f in g["detail"]["missing"]})


class WorkCase(unittest.TestCase):
    """A sandbox with the shipped template applied."""

    def setUp(self):
        self.tpl = shipped()
        self.sb = Sandbox(self).ready(self.tpl)

    def new(self, type_name: str, state: str | None = None, **fields) -> str:
        fields = {k: v for k, v in {**CREATE[type_name], **fields}.items()
                  if v is not None}
        item = self.sb.create(type_name, fields)
        if state is not None:
            for name in path_to(self.tpl, type_name,
                                self.sb.get(item)["state"], state):
                self.sb.move(item, name, set=dict(PASS[(type_name, name)]))
        return item

    def create(self, type_name: str, fields: dict):
        return self.sb.run("item", "create", data={
            "actor": ACTOR, "type": type_name, "fields": fields})

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
        self.assertEqual(r, {"valid": True, "format": 1, "types": 3})

    def test_through_the_executable_as_the_skill_calls_it(self):
        sb = Sandbox(self)
        wrapped = sb.tmp / "input.json"
        wrapped.write_text(json.dumps({"template": shipped()}))
        r = sb.cli("template", "validate", data=f"@{wrapped}", root=False)
        self.assertEqual((r.code, r.result),
                         (0, {"valid": True, "format": 1, "types": 3}), r)

    def test_apply_writes_it_and_show_returns_it_verbatim(self):
        sb = Sandbox(self).ready(shipped())
        shown = sb.ok("template show")
        self.assertEqual((shown["template"], shown["version"]),
                         (shipped(), 1))


# ── criterion 7: exactly decision 13 ───────────────────────────────────────


class TestTheTemplateIsDecisionThirteen(unittest.TestCase):
    """Each part of the file against DESIGN-023 decision 13's list. A part
    the decision does not name — an intake or cadence type, a stage, WIP,
    `high_stakes`, a review or sign-off field, a `restage_*` move, V0 — fails
    the comparison it lands in."""

    def setUp(self):
        self.tpl = shipped()

    def test_the_header(self):
        self.assertEqual({k: v for k, v in self.tpl.items() if k != "types"},
                         {"format": 1, "name": "perry", "version": 1,
                          "relations": {}})

    def test_the_types(self):
        self.assertEqual(list(self.tpl["types"]), ["task", "ask", "risk"])

    def test_each_types_ids_states_and_ends(self):
        for type_name, want in DECISION_13.items():
            with self.subTest(type=type_name):
                got = self.tpl["types"][type_name]
                self.assertEqual(
                    {k: got[k] for k in ("prefix", "digits", "states",
                                         "initial", "terminal")},
                    {k: want[k] for k in ("prefix", "digits", "states",
                                          "initial", "terminal")})
                self.assertEqual(
                    set(got), {"prefix", "digits", "states", "initial",
                               "terminal", "fields", "create_guards",
                               "transitions"})

    def test_each_types_fields(self):
        for type_name, want in DECISION_13.items():
            with self.subTest(type=type_name):
                self.assertEqual(self.tpl["types"][type_name]["fields"],
                                 want["fields"])

    def test_rungs_are_v1_to_v6_ordered_with_no_v0(self):
        rung = self.tpl["types"]["task"]["fields"]["verification"]
        self.assertEqual(rung, {"kind": "enum", "values": RUNGS,
                                "ordered": True})
        self.assertNotIn("V0", rung["values"])

    def test_track_is_an_enum_of_main_and_intake(self):
        """Decision 14: a label for filtering, with no per-track guard."""
        self.assertEqual(self.tpl["types"]["task"]["fields"]["track"],
                         {"kind": "enum", "values": ["main", "intake"]})

    def test_each_types_moves(self):
        for type_name, want in DECISION_13.items():
            with self.subTest(type=type_name):
                got = self.tpl["types"][type_name]["transitions"]
                self.assertEqual(
                    {n: (t["from"], t["to"]) for n, t in got.items()},
                    {n: (t["from"], t["to"])
                     for n, t in want["transitions"].items()})

    def test_each_guard(self):
        for type_name, want in DECISION_13.items():
            got = self.tpl["types"][type_name]
            with self.subTest(type=type_name, on="create"):
                self.assertEqual(got["create_guards"], want["create_guards"])
            for name, t in want["transitions"].items():
                with self.subTest(type=type_name, on=name):
                    self.assertEqual(got["transitions"][name]["guards"],
                                     t["guards"])

    def test_no_guard_reads_the_track(self):
        for decl in self.tpl["types"].values():
            guards = list(decl["create_guards"])
            for t in decl["transitions"].values():
                guards += t["guards"]
            for g in guards:
                self.assertNotIn("track", g.get("when") or {}, g)
                self.assertNotIn("track", g.get("per") or [], g)


# ── criterion 2: every transition ─────────────────────────────────────────


class TestEveryTransitionIsDriven(WorkCase):

    def test_every_transition_has_its_passing_input(self):
        declared = {(type_name, name)
                    for type_name, decl in self.tpl["types"].items()
                    for name in decl["transitions"]}
        self.assertEqual(declared, set(PASS))

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
                        r = self.sb.move(item, name,
                                         set=dict(PASS[(type_name, name)]))
                        self.assertEqual((r["from_state"], r["to_state"]),
                                         (origin, t["to"]))
                        self.assertEqual(self.sb.get(item)["state"], t["to"])
                        driven.add((type_name, name, origin))
        self.assertEqual(driven, declared)
        self.assertEqual(len(declared), 22)

    def test_a_closed_item_moves_no_further(self):
        for type_name, decl in self.tpl["types"].items():
            for terminal in decl["terminal"]:
                with self.subTest(type=type_name, state=terminal):
                    item = self.new(type_name, terminal)
                    for name in decl["transitions"]:
                        r = attempt(self.sb, item, name,
                                    set=dict(PASS[(type_name, name)]))
                        self.assertEqual(r.code_name,
                                         "transition_not_allowed", r)

    def test_the_moves_without_a_guard_need_nothing(self):
        """`start`, `submit` and `reset` carry no guard (decision 13)."""
        for name in ("start", "submit", "reset"):
            t = self.tpl["types"]["task"]["transitions"][name]
            for origin in t["from"]:
                with self.subTest(transition=name, origin=origin):
                    item = self.new("task", origin)
                    self.written(attempt(self.sb, item, name))


# ── criteria 2 and 8: each guard of decision 13 refuses ───────────────────


class TestTaskCreate(WorkCase):

    def test_a_task_is_born_with_title_summary_priority_and_rung(self):
        for field in ("title", "summary", "priority", "verification"):
            with self.subTest(field=field):
                fields = {k: v for k, v in CREATE["task"].items()
                          if k != field}
                r = self.refused(self.create("task", fields))
                self.assertEqual(missing(r), [field])
        r = self.refused(self.create("task", {}))
        self.assertEqual(missing(r), ["priority", "summary", "title",
                                      "verification"])
        item = self.written(self.create("task", CREATE["task"]))
        self.assertEqual(item.result["item"]["state"], "not_started")

    def test_nothing_else_is_required_at_create(self):
        item = self.sb.get(self.new("task"))
        self.assertEqual({k for k, v in item["fields"].items()
                          if v is not None}, set(CREATE["task"]))


class TestRungs(WorkCase):
    """V1–V6. V0 is not a value, so no write can store it."""

    def test_every_rung_from_v1_to_v6_is_stored(self):
        for rung in RUNGS:
            with self.subTest(rung=rung):
                item = self.new("task", verification=rung)
                self.assertEqual(
                    self.sb.get(item)["fields"]["verification"], rung)

    def test_no_write_stores_v0(self):
        r = self.create("task", {**CREATE["task"], "verification": "V0"})
        self.assertEqual(r.code_name, "field_invalid", r)
        item = self.new("task", "in_progress")
        r = self.sb.run("item", "update", data={
            "actor": ACTOR, "id": item, "set": {"verification": "V0"}})
        self.assertEqual(r.code_name, "field_invalid", r)
        r = attempt(self.sb, item, "done",
                    set={"evidence": EVIDENCE, "verification": "V0"})
        self.assertEqual(r.code_name, "field_invalid", r)
        self.assertEqual(self.sb.get(item)["fields"]["verification"], "V3")


class TestTrack(WorkCase):
    """Decision 14: `track` is `main` or `intake`, a label and nothing more."""

    def test_the_two_tracks_are_values_and_no_other_is(self):
        for track in ("main", "intake"):
            with self.subTest(track=track):
                self.assertEqual(self.sb.get(self.new("task", track=track))
                                 ["fields"]["track"], track)
        r = self.create("task", {**CREATE["task"], "track": "ops"})
        self.assertEqual(r.code_name, "field_invalid", r)

    def test_a_track_changes_no_rule(self):
        for track in ("main", "intake", None):
            with self.subTest(track=track):
                item = self.new("task", "in_progress", track=track,
                                verification="V1")
                self.written(attempt(self.sb, item, "done",
                                     set={"evidence": EVIDENCE}))


class TestBlockAndDrop(WorkCase):
    """`block` and `drop` need a `reason`. Decision 13 gives a task one
    `reason` field, and `required` asks only that it is set when the move
    lands (§ 5.4), so a move that leaves it unset is refused from every
    state it starts in."""

    def test_block_needs_a_reason(self):
        for origin in self.tpl["types"]["task"]["transitions"]["block"]["from"]:
            with self.subTest(origin=origin):
                item = self.new("task", origin)
                r = self.refused(attempt(self.sb, item, "block"))
                self.assertEqual(missing(r), ["reason"])
                self.written(attempt(self.sb, item, "block",
                                     set={"reason": "waiting on USER-001"}))

    def test_drop_needs_a_reason(self):
        for origin in self.tpl["types"]["task"]["transitions"]["drop"]["from"]:
            with self.subTest(origin=origin):
                item = self.new("task", origin)
                r = self.refused(attempt(self.sb, item, "drop",
                                         unset=["reason"]))
                self.assertEqual(missing(r), ["reason"])
                self.written(attempt(self.sb, item, "drop",
                                     set={"reason": "superseded"}))

    def test_a_blocked_tasks_reason_satisfies_drop(self):
        """One field serves both moves: a blocked task holds the reason it
        was blocked for, and `drop` from `blocked` passes on it. The kernel
        cannot ask for a reason written by this move, so the skill writes
        the drop's own reason in the same `item move`."""
        item = self.new("task", "blocked")
        self.written(attempt(self.sb, item, "drop"))
        self.assertEqual(self.sb.get(item)["fields"]["reason"],
                         PASS[("task", "block")]["reason"])


class TestDone(WorkCase):
    """The close gate: evidence always, a reviewer at V4, a human at V5."""

    def close(self, item, actor=None, **fields):
        return attempt(self.sb, item, "done", actor=actor,
                       set={"evidence": EVIDENCE, **fields})

    def test_done_needs_evidence(self):
        for origin in self.tpl["types"]["task"]["transitions"]["done"]["from"]:
            with self.subTest(origin=origin):
                item = self.new("task", origin)
                r = self.refused(attempt(self.sb, item, "done"))
                self.assertEqual(missing(r), ["evidence"])
                self.written(self.close(item))

    def test_v4_needs_the_reviewer(self):
        """TASK-291, carried: the V4 verdict is `verified_by` on the item, a
        typed record; the review document is an attachment."""
        item = self.new("task", "review", verification="V4")
        r = self.refused(self.close(item))
        self.assertEqual(missing(r), ["verified_by"])
        (failure,) = r.details["guards"]
        self.assertEqual(failure["when"], {"verification": ["V4"]})
        self.sb.ok("attach add", data={
            "actor": ACTOR, "id": item,
            "ref": "perry/evidence/2026-09/TASK-001-review.md"})
        self.written(self.close(item, verified_by=REVIEWER))
        self.assertEqual(self.sb.get(item)["fields"]["verified_by"], REVIEWER)

    def test_the_reviewer_is_a_typed_record_never_prose(self):
        item = self.new("task", "review", verification="V4")
        for bad in ("fresh-reviewer", "PASS",
                    {"kind": "agent", "name": "fresh-reviewer"}):
            with self.subTest(value=bad):
                r = self.close(item, verified_by=bad)
                self.assertEqual(r.code_name, "field_invalid", r)
        self.assertEqual(self.sb.get(item)["state"], "review")

    def test_the_reviewer_rule_is_v4s_alone(self):
        for rung in ("V1", "V2", "V3", "V5", "V6"):
            with self.subTest(rung=rung):
                item = self.new("task", "review", verification=rung)
                self.written(self.close(item, HUMAN))

    def test_v5_is_closed_by_a_human(self):
        """DESIGN-023 § 5.2: the guard makes a V5 close name a human; it does
        not authenticate one. What the signer checked is an attached
        document, and the date is the event's time."""
        item = self.new("task", "review", verification="V5")
        r = self.refused(self.close(item, ACTOR))
        (failure,) = r.details["guards"]
        self.assertEqual((failure["kind"], failure["when"],
                          failure["detail"]["needs"]),
                         ("actor", {"verification": ["V5"]},
                          {"actor_kind": "human"}))
        r = self.written(self.close(item, HUMAN))
        (event,) = [e for e in self.sb.events(items=[item])
                    if e["transition"] == "done"]
        self.assertEqual((event["transition"], event["actor"]["kind"],
                          event["actor"]["name"], event["seq"]),
                         ("done", "human", HUMAN["name"], r.env["events"][0]))
        self.assertTrue(event["at"])

    def test_the_human_rule_is_v5s_alone(self):
        for rung in ("V1", "V2", "V3", "V6"):
            with self.subTest(rung=rung):
                item = self.new("task", "review", verification=rung)
                self.written(self.close(item, ACTOR))
        item = self.new("task", "review", verification="V4")
        self.written(self.close(item, ACTOR, verified_by=REVIEWER))


class TestAsk(WorkCase):

    def test_an_ask_is_born_with_its_question(self):
        r = self.refused(self.create("ask", {}))
        self.assertEqual(missing(r), ["question"])
        self.assertEqual(self.sb.get(self.new("ask"))["state"], "pending")

    def test_answering_needs_the_answer_and_happens_once(self):
        ask = self.new("ask")
        r = self.refused(attempt(self.sb, ask, "answer"))
        self.assertEqual(missing(r), ["answer"])
        self.written(attempt(self.sb, ask, "answer", set={"answer": "30 days"}))
        r = attempt(self.sb, ask, "answer", set={"answer": "60 days"})
        self.assertEqual(r.code_name, "transition_not_allowed", r)

    def test_an_ask_blocks_the_task_until_it_is_answered(self):
        """Decision 13: an ask holds a task up through a `blocks` relation,
        which the kernel builds in; the template declares no relation."""
        ask = self.new("ask")
        task = self.sb.create("task", CREATE["task"],
                              relations=[{"kind": "blocks", "from": ask}])
        got = self.sb.get(task)
        self.assertEqual((got["blocked_by"], got["startable"]), ([ask], False))
        self.sb.move(ask, "answer", set={"answer": "yes"})
        got = self.sb.get(task)
        self.assertEqual((got["blocked_by"], got["startable"]), ([], True))


class TestRisk(WorkCase):

    def test_a_risk_needs_nothing_at_create(self):
        """Decision 13 names no create guard for a risk."""
        risk = self.written(self.create("risk", {}))
        self.assertEqual(risk.result["item"]["state"], "open")
        self.written(self.create("risk", {"concern": "the store is unseen"}))

    def test_a_risk_is_cleared_once_and_with_its_reason(self):
        risk = self.new("risk", concern="The store sits where no one sees it.")
        r = self.refused(attempt(self.sb, risk, "clear"))
        self.assertEqual(missing(r), ["reason"])
        self.written(attempt(self.sb, risk, "clear",
                             set={"reason": "the export is committed"}))
        r = attempt(self.sb, risk, "clear", set={"reason": "again"})
        self.assertEqual(r.code_name, "transition_not_allowed", r)


class TestTheTaskTree(WorkCase):
    """Dependencies are `blocks`, the tree is `parent`: both built in."""

    def test_a_task_depends_on_a_task_and_has_a_parent(self):
        parent, blocker = self.new("task"), self.new("task")
        child = self.sb.create("task", CREATE["task"], relations=[
            {"kind": "parent", "to": parent},
            {"kind": "blocks", "from": blocker}])
        got = self.sb.get(child)
        self.assertEqual(got["blocked_by"], [blocker])
        self.assertIn({"kind": "parent", "from": child, "to": parent},
                      got["relations"])
        self.sb.move(blocker, "drop", set={"reason": "not needed"})
        self.assertTrue(self.sb.get(child)["startable"])


if __name__ == "__main__":
    unittest.main()
