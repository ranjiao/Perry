"""`query` and `events`: filters, counts and the default bound (§ 5.6, NN-K7)."""

from __future__ import annotations

import unittest

from support import ACTOR, Sandbox


class TestQuery(unittest.TestCase):

    def setUp(self):
        sb = self.sb = Sandbox(self).ready()
        self.n1 = sb.create(fields={"bench": "north", "size": "S"})
        self.n2 = sb.create(fields={"bench": "north"})
        self.s1 = sb.create(fields={"bench": "south", "size": "S"})
        self.g = sb.create("gauge")
        sb.ok("rel", "add", data={"actor": ACTOR, "kind": "blocks",
                                  "from": self.n1, "to": self.n2})
        sb.move(self.s1, "scrap")

    def ids(self, **data):
        return [i["id"] for i in self.sb.ok("query", data=data)["items"]]

    def test_filters_are_anded_and_values_ored(self):
        self.assertEqual(self.ids(), [self.g, self.n1, self.n2, self.s1])
        self.assertEqual(self.ids(type="widget", state=["queued"]),
                         [self.n1, self.n2])
        self.assertEqual(self.ids(terminal=True), [self.s1])
        self.assertEqual(self.ids(terminal=False),
                         [self.g, self.n1, self.n2])
        self.assertEqual(self.ids(type="widget", where={"bench": ["south"]}),
                         [self.s1])
        self.assertEqual(self.ids(type="widget",
                                  where={"size": ["S"], "bench": ["north"]}),
                         [self.n1])
        self.assertEqual(self.ids(type="widget", where={"size": [None]}),
                         [self.n2])
        self.assertEqual(self.ids(type="widget",
                                  where={"size": [None, "S"]}),
                         [self.n1, self.n2, self.s1])
        self.assertEqual(self.ids(related={"kind": "blocks", "to": self.n2}),
                         [self.n1])
        self.assertEqual(self.ids(related={"kind": "blocks",
                                           "from": self.n1}), [self.n2])
        self.assertEqual(self.ids(startable=True), [self.g, self.n1])
        self.assertEqual(self.ids(startable=False), [self.n2, self.s1])
        self.assertEqual(self.ids(ids=[self.n2, self.g]), [self.g, self.n2])

    def test_items_carry_derived_fields(self):
        (item,) = self.sb.ok("query", data={"ids": [self.n2]})["items"]
        self.assertEqual(item["blocked_by"], [self.n1])
        self.assertFalse(item["startable"])

    def test_counts_cover_every_match_before_the_bound(self):
        r = self.sb.ok("query", data={"type": "widget",
                                      "count_by": ["state", "bench"],
                                      "limit": 1})
        self.assertEqual((r["total"], r["returned"], r["truncated"]),
                         (3, 1, True))
        self.assertEqual(r["counts"], [
            {"key": {"state": "queued", "bench": "north"}, "n": 2},
            {"key": {"state": "scrapped", "bench": "south"}, "n": 1}])
        r = self.sb.ok("query", data={"count_by": ["type"]})
        self.assertEqual(r["counts"], [{"key": {"type": "gauge"}, "n": 1},
                                       {"key": {"type": "widget"}, "n": 3}])

    def test_refusals(self):
        cases = [
            ({"type": "gizmo"}, "unknown_type"),
            ({"where": {"bench": ["north"]}}, "input_invalid"),
            ({"type": "widget", "where": {"nope": [1]}}, "unknown_field"),
            ({"type": "widget", "where": {"colors": [None]}},
             "input_invalid"),
            ({"count_by": ["bench"]}, "input_invalid"),
            ({"type": "gauge", "count_by": ["reading"]}, "input_invalid"),
            ({"related": {"kind": "nope", "to": self.n1}},
             "unknown_relation"),
            ({"related": {"kind": "blocks", "to": "W-404"}},
             "item_not_found"),
            ({"related": {"kind": "blocks"}}, "input_invalid"),
            ({"ids": ["W-404"]}, "item_not_found"),
            ({"limit": -1}, "input_invalid"),
            ({"after": "not an id"}, "input_invalid"),
        ]
        for data, code in cases:
            with self.subTest(data=data):
                r = self.sb.run("query", data=data)
                self.assertEqual(r.code_name, code, r)

    def test_bounded_by_default_and_paged_by_after(self):
        sb = Sandbox(self).ready()
        made = [sb.create("gauge") for _ in range(55)]
        first = sb.ok("query")
        self.assertEqual((first["total"], first["returned"],
                          first["truncated"], first["next_after"]),
                         (55, 50, True, "G-50"))
        rest = sb.ok("query", data={"after": first["next_after"]})
        self.assertEqual([i["id"] for i in rest["items"]], made[50:])
        self.assertEqual((rest["truncated"], rest["next_after"],
                          rest["total"]), (False, None, 55))
        everything = sb.ok("query", data={"limit": 0})
        self.assertEqual(everything["returned"], 55)
        self.assertFalse(everything["truncated"])


class TestEvents(unittest.TestCase):

    def test_filters_bound_and_unexported(self):
        sb = Sandbox(self).ready()
        a = sb.create()
        b = sb.create()
        sb.move(a, "start")
        sb.ok("item", "update", data={"actor": ACTOR, "id": b,
                                      "set": {"label": "x"}})
        everything = sb.ok("events", data={})
        self.assertEqual((everything["total"], everything["returned"],
                          everything["truncated"]), (6, 6, False))
        self.assertEqual([e["seq"] for e in everything["events"]],
                         [1, 2, 3, 4, 5, 6])
        self.assertEqual((everything["last_export_seq"],
                          everything["unexported"]), (None, 6))
        self.assertEqual([e["seq"] for e in sb.events(items=[a])], [3, 5])
        # A key filter is a prefix: `state` also matches `state_root`.
        self.assertEqual([e["seq"] for e in sb.events(keys=["state"])],
                         [1, 3, 4, 5])
        self.assertEqual([e["seq"] for e in sb.events(keys=["field:la"])], [6])
        self.assertEqual([e["seq"] for e in sb.events(
            commands=["item move", "init"])], [1, 5])
        page = sb.ok("events", data={"limit": 2, "after_seq": 2})
        self.assertEqual(([e["seq"] for e in page["events"]], page["truncated"],
                          page["next_after_seq"]), ([3, 4], True, 4))
        sb.ok("export")
        after = sb.ok("events", data={"limit": 1})
        self.assertEqual((after["last_export_seq"], after["unexported"]),
                         (6, 0))
        sb.create()
        self.assertEqual(sb.ok("events", data={"limit": 1})["unexported"], 1)

    def test_default_bound_is_fifty(self):
        sb = Sandbox(self).ready()
        for _ in range(50):
            sb.create("gauge")
        page = sb.ok("events", data={})
        self.assertEqual((page["total"], page["returned"], page["truncated"],
                          page["next_after_seq"]), (52, 50, True, 50))
        self.assertEqual(sb.run("events", data={"after_seq": -1}).code_name,
                         "input_invalid")


if __name__ == "__main__":
    unittest.main()
