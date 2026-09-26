"""Items, fields, transitions, events and derived fields (§ 5.3, § 5.5, § 5.6)."""

from __future__ import annotations

import unittest

from support import ACTOR, HUMAN, Sandbox

from perry_kernel.values import metric_fraction, metric_met


class TestCreate(unittest.TestCase):

    def test_every_declared_field_is_present_and_null_when_unset(self):
        sb = Sandbox(self).ready()
        item = sb.get(sb.create())
        self.assertEqual(item["id"], "W-001")
        self.assertEqual(item["state"], "queued")
        self.assertEqual(set(item["fields"]), set(
            ["size", "bench", "fragile", "inspector", "ship_by", "made_from",
             "colors", "weight_g", "pieces", "label"]))
        self.assertEqual(item["fields"]["bench"], "north")
        self.assertIsNone(item["fields"]["label"])
        self.assertEqual(item["seq"], 3)
        self.assertEqual(list(item), [
            "id", "type", "state", "fields", "seq", "created_at", "updated_at",
            "relations", "attachments", "startable", "blocked_by", "rollup"])

    def test_unknown_type_and_field(self):
        sb = Sandbox(self).ready()
        sb.refused("unknown_type", "item", "create",
                   data={"actor": ACTOR, "type": "gizmo"})
        r = sb.refused("unknown_field", "item", "create", data={
            "actor": ACTOR, "type": "widget",
            "fields": {"bench": "north", "colour": "red"}})
        self.assertEqual(r.details["field"], "colour")

    def test_the_create_event_records_before_and_after(self):
        sb = Sandbox(self).ready()
        item = sb.create(fields={"bench": "north", "label": "first"},
                         note="made by hand")
        event = sb.events(items=[item])[0]
        self.assertEqual(event["command"], "item create")
        self.assertEqual(event["items"], [item])
        self.assertEqual(event["actor"], ACTOR)
        self.assertEqual(event["note"], "made by hand")
        self.assertEqual(event["changes"], [
            {"key": "type", "before": None, "after": "widget"},
            {"key": "state", "before": None, "after": "queued"},
            {"key": "field:bench", "before": None, "after": "north"},
            {"key": "field:label", "before": None, "after": "first"}])


class TestFieldKinds(unittest.TestCase):
    """§ 5.3: every kind, a value that fits and one that does not."""

    def setUp(self):
        self.sb = Sandbox(self).ready()
        self.other = self.sb.create()
        self.gauge = self.sb.create("gauge")

    def attempt(self, field, value):
        return self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "widget",
            "fields": {"bench": "north", field: value}})

    def test_values_that_fit(self):
        fits = {"label": "a label", "pieces": -(2 ** 53), "weight_g": 12.5,
                "ship_by": "2028-02-29", "size": "M", "fragile": False,
                "inspector": {"kind": "agent", "name": "x", "session": "s"},
                "made_from": self.other, "colors": ["red", "blue"]}
        for field, value in fits.items():
            with self.subTest(field=field):
                r = self.attempt(field, value)
                self.assertTrue(r.ok, r)
                self.assertEqual(r.result["item"]["fields"][field], value)

    def test_values_that_do_not(self):
        misfits = [
            ("label", 5, "field_invalid"),
            ("pieces", 1.5, "field_invalid"),
            ("pieces", True, "field_invalid"),
            ("pieces", 2 ** 53 + 1, "field_invalid"),
            ("weight_g", "12", "field_invalid"),
            ("weight_g", False, "field_invalid"),
            ("ship_by", "2027-02-29", "field_invalid"),
            ("ship_by", "20270101", "field_invalid"),
            ("size", "XXL", "field_invalid"),
            ("fragile", "true", "field_invalid"),
            ("fragile", 1, "field_invalid"),
            ("inspector", {"kind": "agent", "name": "x"}, "field_invalid"),
            ("inspector", {"kind": "human", "name": "x", "role": "y"},
             "field_invalid"),
            ("made_from", "W-404", "item_not_found"),
            ("made_from", self.gauge, "field_invalid"),
            ("colors", ["red", 3], "field_invalid"),
            ("colors", ["red", None], "field_invalid"),
            ("colors", "red", "field_invalid"),
        ]
        for field, value, code in misfits:
            with self.subTest(field=field, value=value):
                r = self.attempt(field, value)
                self.assertEqual((r.code, r.code_name), (1, code), r)
        self.assertEqual(self.sb.ok("query", data={"type": "widget"})["total"],
                         1)

    def test_null_means_unset(self):
        r = self.attempt("label", None)
        self.assertTrue(r.ok, r)
        self.assertIsNone(r.result["item"]["fields"]["label"])


class TestMetrics(unittest.TestCase):
    """§ 5.5: the fixed formula, the merge and the refusals."""

    def test_the_formula(self):
        cases = [
            ({"current": None, "target": 10, "baseline": 0,
              "direction": "up"}, None, None),
            ({"current": 5, "target": 10, "baseline": 0, "direction": "up"},
             False, 0.5),
            ({"current": 10, "target": 10, "baseline": 0, "direction": "up"},
             True, 1.0),
            ({"current": -3, "target": 10, "baseline": 0, "direction": "up"},
             False, 0.0),
            ({"current": 0.00001, "target": 10, "baseline": 0,
              "direction": "up"}, False, 0.001),
            ({"current": 9.99999, "target": 10, "baseline": 0,
              "direction": "up"}, False, 0.999),
            ({"current": 2, "target": 3, "baseline": 0, "direction": "up"},
             False, 0.667),
            ({"current": 8, "target": 5, "baseline": 10, "direction": "down"},
             False, 0.4),
            ({"current": 4, "target": 5, "baseline": 10, "direction": "down"},
             True, 1.0),
            ({"current": 4, "target": 5, "baseline": None,
              "direction": "down"}, True, None),
            ({"current": 0, "target": 1, "baseline": None,
              "direction": "up"}, False, None),
        ]
        for value, met, fraction in cases:
            with self.subTest(value=value):
                self.assertEqual(metric_met(value), met)
                self.assertEqual(metric_fraction(value), fraction)

    def test_set_merges_and_the_first_set_needs_target_and_direction(self):
        sb = Sandbox(self).ready()
        sb.refused("metric_invalid", "item", "create", data={
            "actor": ACTOR, "type": "gauge", "fields": {"reading": {
                "current": 3}}})
        gauge = sb.create("gauge", {"reading": {"target": 10, "baseline": 0,
                                                "direction": "up"}})
        self.assertEqual(sb.get(gauge)["fields"]["reading"], {
            "current": None, "target": 10, "baseline": 0, "direction": "up",
            "met": None, "fraction": None})
        sb.ok("item", "update", data={"actor": ACTOR, "id": gauge,
                                      "set": {"reading": {"current": 8}},
                                      "note": "measured by `count-things`"})
        self.assertEqual(sb.get(gauge)["fields"]["reading"], {
            "current": 8, "target": 10, "baseline": 0, "direction": "up",
            "met": False, "fraction": 0.8})
        event = sb.events(keys=["field:reading"])[-1]
        self.assertEqual(event["note"], "measured by `count-things`")
        self.assertEqual(event["changes"][0]["before"]["current"], None)
        self.assertEqual(event["changes"][0]["after"]["current"], 8)
        self.assertNotIn("met", event["changes"][0]["after"])

    def test_metric_refusals(self):
        sb = Sandbox(self).ready()
        bad = [{"target": 10}, {"direction": "up"},
               {"target": 10, "direction": "sideways"},
               {"target": 10, "direction": "up", "unit": "kg"},
               {"target": 10, "direction": "up", "baseline": 10},
               {"target": 10, "direction": "down", "baseline": 5},
               {"target": "10", "direction": "up"},
               {"target": 10, "direction": "up", "current": True}, 7]
        for value in bad:
            with self.subTest(value=value):
                sb.refused("metric_invalid", "item", "create", data={
                    "actor": ACTOR, "type": "gauge",
                    "fields": {"reading": value}})


class TestUpdate(unittest.TestCase):

    def setUp(self):
        self.sb = Sandbox(self).ready()
        self.item = self.sb.create(fields={"bench": "north", "label": "a"})

    def update(self, **data):
        return self.sb.run("item", "update",
                           data={"actor": ACTOR, "id": self.item, **data})

    def test_set_and_unset_record_before_and_after(self):
        r = self.update(set={"label": "b", "pieces": 3}, unset=["bench"])
        self.assertTrue(r.ok, r)
        event = self.sb.events()[-1]
        self.assertEqual(event["changes"], [
            {"key": "field:bench", "before": "north", "after": None},
            {"key": "field:label", "before": "a", "after": "b"},
            {"key": "field:pieces", "before": None, "after": 3}])
        self.assertEqual(event["items"], [self.item])

    def test_no_guards_run_on_update(self):
        r = self.update(unset=["bench"])  # bench is a create guard's field
        self.assertTrue(r.ok, r)

    def test_refusals(self):
        self.assertEqual(self.update(set={"nope": 1}).code_name,
                         "unknown_field")
        self.assertEqual(self.update(unset=["nope"]).code_name,
                         "unknown_field")
        self.assertEqual(self.update(set={"label": "x"},
                                     unset=["label"]).code_name,
                         "input_invalid")
        self.assertEqual(self.update(set={"pieces": "x"}).code_name,
                         "field_invalid")
        r = self.sb.run("item", "update", data={"actor": ACTOR, "id": "W-404",
                                                "set": {"label": "x"}})
        self.assertEqual(r.code_name, "item_not_found")

    def test_compare_and_set(self):
        seq = self.sb.get(self.item)["seq"]
        self.assertTrue(self.update(set={"label": "b"},
                                    expect={self.item: seq}).ok)
        r = self.update(set={"label": "c"}, expect={self.item: seq})
        self.assertEqual((r.code, r.code_name), (1, "stale_write"), r)
        self.assertEqual(r.details["items"], [
            {"id": self.item, "expected": seq, "actual": seq + 1}])
        self.assertEqual(self.sb.get(self.item)["fields"]["label"], "b")
        r = self.update(set={"label": "c"}, expect={"W-404": 1})
        self.assertEqual(r.code_name, "item_not_found")


class TestMove(unittest.TestCase):

    def test_every_transition_and_its_event(self):
        sb = Sandbox(self).ready()
        item = sb.create(fields={"bench": "north", "size": "M"})
        r = sb.move(item, "start")
        self.assertEqual((r["transition"], r["from_state"], r["to_state"]),
                         ("start", "queued", "cutting"))
        sb.move(item, "polish")
        sb.move(item, "ship", set={"inspector": HUMAN})
        self.assertEqual(sb.get(item)["state"], "shipped")
        event = sb.events()[-1]
        self.assertEqual(event["transition"], "ship")
        self.assertEqual(event["changes"][0], {"key": "state",
                                               "before": "polished",
                                               "after": "shipped"})
        self.assertEqual(event["changes"][1]["key"], "field:inspector")

    def test_refusals(self):
        sb = Sandbox(self).ready()
        item = sb.create()
        r = sb.run("item", "move", data={"actor": ACTOR, "id": item,
                                         "transition": "fly"})
        self.assertEqual(r.code_name, "unknown_transition")
        r = sb.run("item", "move", data={"actor": ACTOR, "id": item,
                                         "transition": "polish"})
        self.assertEqual(r.code_name, "transition_not_allowed")
        self.assertEqual(r.details["state"], "queued")
        sb.move(item, "scrap")
        r = sb.run("item", "move", data={"actor": ACTOR, "id": item,
                                         "transition": "scrap"})
        self.assertEqual(r.code_name, "transition_not_allowed")


class TestDerivedFields(unittest.TestCase):

    def test_startable_and_blocked_by(self):
        sb = Sandbox(self).ready()
        blocker, other, item = sb.create(), sb.create(), sb.create()
        for src in (blocker, other):
            sb.ok("rel", "add", data={"actor": ACTOR, "kind": "blocks",
                                      "from": src, "to": item})
        got = sb.get(item)
        self.assertEqual(got["blocked_by"], [blocker, other])
        self.assertFalse(got["startable"])
        sb.move(blocker, "scrap")
        self.assertEqual(sb.get(item)["blocked_by"], [other])
        sb.move(other, "scrap")
        got = sb.get(item)
        self.assertEqual((got["blocked_by"], got["startable"]), ([], True))
        sb.move(item, "start")
        self.assertFalse(sb.get(item)["startable"])

    def test_rollup_over_parent_children(self):
        sb = Sandbox(self).ready()
        top = sb.create()
        self.assertIsNone(sb.get(top)["rollup"])
        plain = sb.create()
        sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent",
                                  "from": plain, "to": top})
        self.assertIsNone(sb.get(top)["rollup"], "no child declares a metric")
        g1 = sb.create("gauge")
        sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent",
                                  "from": g1, "to": top})
        self.assertEqual(sb.get(top)["rollup"], {
            "members": 1, "measured": 0, "met": None, "fraction": None})
        sb.ok("item", "update", data={"actor": ACTOR, "id": g1, "set": {
            "reading": {"current": 5, "target": 10, "baseline": 0,
                        "direction": "up"}}})
        self.assertEqual(sb.get(top)["rollup"], {
            "members": 1, "measured": 1, "met": False, "fraction": 0.5})
        g2 = sb.create("gauge", {"reading": {"current": 3, "target": 2,
                                             "direction": "up"}})
        sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent",
                                  "from": g2, "to": top})
        self.assertEqual(sb.get(top)["rollup"], {
            "members": 2, "measured": 2, "met": False, "fraction": None})
        sb.ok("item", "update", data={"actor": ACTOR, "id": g1, "set": {
            "reading": {"current": 10}}})
        self.assertEqual(sb.get(top)["rollup"]["met"], True)
        # Whatever their state, one level down, and not the item's own.
        sb.move(g1, "retire")
        self.assertEqual(sb.get(top)["rollup"]["members"], 2)
        grand = sb.create("gauge", {"reading": {"target": 1,
                                                "direction": "up"}})
        sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent",
                                  "from": grand, "to": g1})
        self.assertEqual(sb.get(top)["rollup"]["members"], 2)
        self.assertEqual(sb.get(g1)["rollup"]["members"], 1)


if __name__ == "__main__":
    unittest.main()
