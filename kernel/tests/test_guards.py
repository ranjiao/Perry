"""The four guards, with and without `when` (§ 5.4; acceptance criterion 6).

Each guard kind has a test that shows it refusing without `when`, and one that
shows it refusing with `when` and standing aside when `when` does not match.
`limit` has both a warn-mode and a refuse-mode test.
"""

from __future__ import annotations

import unittest

from support import ACTOR, HUMAN, Sandbox

FLAG = {"flag": [True]}


def piece_template(guards_by_transition: dict, create_guards=()) -> dict:
    """One type, `piece`, with a transition from idle to busy per guard set."""
    transitions = {name: {"from": ["idle"], "to": "busy", "guards": guards}
                   for name, guards in guards_by_transition.items()}
    transitions["back"] = {"from": ["busy"], "to": "idle", "guards": []}
    transitions["finish"] = {"from": ["idle", "busy"], "to": "gone",
                             "guards": []}
    return {
        "format": 1, "name": "bench-test", "version": 1,
        "types": {"piece": {
            "prefix": "P", "states": ["idle", "busy", "gone"],
            "initial": "idle", "terminal": ["gone"],
            "fields": {"flag": {"kind": "enum", "values": [False, True]},
                       "holder": {"kind": "text"},
                       "grade": {"kind": "enum", "ordered": True,
                                 "values": ["low", "mid", "high"]},
                       "lane": {"kind": "enum", "values": ["a", "b"]}},
            "create_guards": list(create_guards),
            "transitions": transitions}},
        "relations": {}}


def with_when(guard: dict) -> dict:
    return {**guard, "when": FLAG}


class GuardCase(unittest.TestCase):
    GUARD: dict = {}

    def setUp(self):
        self.sb = Sandbox(self).ready(piece_template({
            "go": [self.GUARD], "go_when": [with_when(self.GUARD)]}))

    def piece(self, **fields) -> str:
        return self.sb.create("piece", fields)

    def attempt(self, item, transition, actor=None, **extra):
        return self.sb.run("item", "move", data={
            "actor": actor or ACTOR, "id": item, "transition": transition,
            **extra})

    def assert_refused(self, r, kind, when=None):
        self.assertEqual((r.code, r.code_name), (1, "guard_refused"), r)
        (failure,) = r.details["guards"]
        self.assertEqual(sorted(failure), ["detail", "index", "kind", "when"])
        self.assertEqual((failure["index"], failure["kind"], failure["when"]),
                         (0, kind, when))
        return failure["detail"]

    def assert_moved(self, r):
        self.assertTrue(r.ok, r)
        self.assertEqual(r.result["to_state"], "busy")


class TestRequired(GuardCase):
    GUARD = {"kind": "required", "fields": ["holder"],
             "at_least": {"grade": "mid"}}

    def test_refuses_without_when(self):
        item = self.piece()
        detail = self.assert_refused(self.attempt(item, "go"), "required")
        self.assertEqual(detail, {"missing": ["holder"], "below": {
            "grade": {"value": None, "at_least": "mid"}}})
        self.assertEqual(self.sb.get(item)["state"], "idle")
        detail = self.assert_refused(
            self.attempt(item, "go", set={"holder": "   ", "grade": "low"}),
            "required")
        self.assertEqual(detail["missing"], ["holder"], "blank text is unset")
        self.assertEqual(detail["below"]["grade"]["value"], "low")
        self.assert_moved(self.attempt(item, "go", set={"holder": "Kim",
                                                        "grade": "high"}))

    def test_refuses_with_when_and_stands_aside_otherwise(self):
        flagged, plain = self.piece(flag=True), self.piece(flag=False)
        self.assert_refused(self.attempt(flagged, "go_when"), "required", FLAG)
        self.assert_moved(self.attempt(plain, "go_when"))
        self.assert_moved(self.attempt(self.piece(), "go_when"))


class TestActor(GuardCase):
    GUARD = {"kind": "actor", "actor_kind": "human", "name": "Pat"}

    def test_refuses_without_when(self):
        item = self.piece()
        detail = self.assert_refused(self.attempt(item, "go"), "actor")
        self.assertEqual(detail, {"actor": ACTOR, "needs": {
            "actor_kind": "human", "name": "Pat"}})
        other_human = {"kind": "human", "name": "Kim"}
        self.assert_refused(self.attempt(item, "go", actor=other_human),
                            "actor")
        self.assert_moved(self.attempt(item, "go", actor=HUMAN))

    def test_refuses_with_when_and_stands_aside_otherwise(self):
        flagged, plain = self.piece(flag=True), self.piece()
        self.assert_refused(self.attempt(flagged, "go_when"), "actor", FLAG)
        self.assert_moved(self.attempt(flagged, "go_when", actor=HUMAN))
        self.assert_moved(self.attempt(plain, "go_when"))


class TestRelationsClosed(GuardCase):
    GUARD = {"kind": "relations_closed", "relation": "blocks",
             "direction": "incoming"}

    def block(self, src, dst):
        self.sb.ok("rel", "add", data={"actor": ACTOR, "kind": "blocks",
                                       "from": src, "to": dst})

    def test_refuses_without_when(self):
        item, blocker = self.piece(), self.piece()
        self.block(blocker, item)
        detail = self.assert_refused(self.attempt(item, "go"),
                                     "relations_closed")
        self.assertEqual(detail, {"not_terminal": [blocker]})
        self.sb.move(blocker, "finish")
        self.assert_moved(self.attempt(item, "go"))

    def test_refuses_with_when_and_stands_aside_otherwise(self):
        flagged, plain, blocker = (self.piece(flag=True), self.piece(),
                                   self.piece())
        self.block(blocker, flagged)
        self.block(blocker, plain)
        self.assert_refused(self.attempt(flagged, "go_when"),
                            "relations_closed", FLAG)
        self.assert_moved(self.attempt(plain, "go_when"))

    def test_outgoing_looks_the_other_way(self):
        sb = Sandbox(self).ready(piece_template({"go": [{
            "kind": "relations_closed", "relation": "parent",
            "direction": "outgoing"}]}))
        child, parent = sb.create("piece", {}), sb.create("piece", {})
        sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent",
                                  "from": child, "to": parent})
        r = sb.run("item", "move", data={"actor": ACTOR, "id": child,
                                         "transition": "go"})
        self.assertEqual(r.details["guards"][0]["detail"],
                         {"not_terminal": [parent]})
        r = sb.run("item", "move", data={"actor": ACTOR, "id": parent,
                                         "transition": "go"})
        self.assertTrue(r.ok, r)


class TestLimitRefuse(GuardCase):
    GUARD = {"kind": "limit", "max": 1, "per": ["lane"], "mode": "refuse"}

    def test_refuses_without_when(self):
        first, second, other_lane = (self.piece(lane="a"), self.piece(lane="a"),
                                     self.piece(lane="b"))
        self.assert_moved(self.attempt(first, "go"))
        detail = self.assert_refused(self.attempt(second, "go"), "limit")
        self.assertEqual(detail, {"count": 2, "max": 1,
                                  "values": {"lane": "a"}})
        self.assert_moved(self.attempt(other_lane, "go"))
        self.assertEqual(self.sb.get(second)["state"], "idle")

    def test_refuses_with_when_and_stands_aside_otherwise(self):
        a1, a2 = self.piece(lane="a", flag=True), self.piece(lane="a",
                                                             flag=True)
        a3 = self.piece(lane="a")
        self.assert_moved(self.attempt(a1, "go_when"))
        self.assert_refused(self.attempt(a2, "go_when"), "limit", FLAG)
        self.assert_moved(self.attempt(a3, "go_when"))

    def test_unset_per_values_count_together(self):
        self.assert_moved(self.attempt(self.piece(), "go"))
        detail = self.assert_refused(self.attempt(self.piece(), "go"), "limit")
        self.assertEqual(detail["values"], {"lane": None})


class TestLimitWarn(GuardCase):
    GUARD = {"kind": "limit", "max": 1, "per": [], "mode": "warn"}

    def test_warns_without_when(self):
        self.assert_moved(self.attempt(self.piece(), "go"))
        r = self.attempt(self.piece(), "go")
        self.assert_moved(r)
        (warning,) = r.env["warnings"]
        self.assertEqual(warning["code"], "limit_exceeded")
        self.assertEqual((warning["index"], warning["kind"], warning["when"],
                          warning["detail"]),
                         (0, "limit", None, {"count": 2, "max": 1,
                                             "values": {}}))
        event = self.sb.events()[-1]
        self.assertEqual(event["warnings"], r.env["warnings"])

    def test_warns_with_when_and_stands_aside_otherwise(self):
        self.assert_moved(self.attempt(self.piece(flag=True), "go_when"))
        r = self.attempt(self.piece(), "go_when")
        self.assert_moved(r)
        self.assertEqual(r.env["warnings"], [])
        r = self.attempt(self.piece(flag=True), "go_when")
        self.assert_moved(r)
        self.assertEqual(r.env["warnings"][0]["when"], FLAG)


class TestGuardsTogether(unittest.TestCase):

    def test_every_failure_is_listed_and_nothing_lands(self):
        sb = Sandbox(self).ready(piece_template({"go": [
            {"kind": "required", "fields": ["holder"]},
            {"kind": "actor", "actor_kind": "human"},
            {"kind": "limit", "max": 1, "per": [], "mode": "warn"},
            {"kind": "limit", "max": 1, "per": [], "mode": "refuse"}]}))
        busy = sb.create("piece", {})
        sb.move(busy, "go", actor=HUMAN, set={"holder": "x"})
        item = sb.create("piece", {})
        seq = sb.seq()
        r = sb.run("item", "move", data={"actor": ACTOR, "id": item,
                                         "transition": "go",
                                         "set": {"grade": "high"}})
        self.assertEqual(r.code_name, "guard_refused", r)
        self.assertEqual([g["index"] for g in r.details["guards"]], [0, 1, 3])
        self.assertEqual([w["index"] for w in r.details["warnings"]], [2])
        self.assertEqual(sb.seq(), seq)
        got = sb.get(item)
        self.assertEqual((got["state"], got["fields"]["grade"]), ("idle", None))

    def test_create_guards_see_what_the_same_command_sets(self):
        sb = Sandbox(self).ready(piece_template({}, create_guards=[
            {"kind": "required", "fields": ["holder"],
             "when": {"lane": ["b"]}},
            {"kind": "relations_closed", "relation": "blocks",
             "direction": "incoming"},
            {"kind": "limit", "max": 1, "per": ["lane"], "mode": "refuse"}]))
        blocker = sb.create("piece", {"lane": "a"})
        r = sb.run("item", "create", data={
            "actor": ACTOR, "type": "piece", "fields": {"lane": "b"},
            "relations": [{"kind": "blocks", "from": blocker}]})
        self.assertEqual(r.code_name, "guard_refused", r)
        self.assertEqual([g["kind"] for g in r.details["guards"]],
                         ["required", "relations_closed"])
        self.assertEqual(sb.ok("query")["total"], 1)
        self.assertEqual(sb.get(blocker)["relations"], [])
        # The id was not consumed, and the edge did not half-land.
        self.assertEqual(sb.create("piece", {"lane": "b", "holder": "x"}),
                         "P-2")
        r = sb.run("item", "create", data={
            "actor": ACTOR, "type": "piece", "fields": {"lane": "a"}})
        self.assertEqual(r.details["guards"][0]["kind"], "limit")


if __name__ == "__main__":
    unittest.main()
