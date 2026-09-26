"""Template format 1: validation, versions and compatibility (§ 5.2)."""

from __future__ import annotations

import copy
import unittest

from support import ACTOR, TEMPLATE, Sandbox, mkdtemp


def variant(mutate) -> dict:
    out = copy.deepcopy(TEMPLATE)
    mutate(out)
    return out


def widget(t):
    return t["types"]["widget"]


class TestValidate(unittest.TestCase):

    def validate(self, tpl):
        sb = Sandbox(self)
        return sb.run("template", "validate", data={"template": tpl},
                      store=False, root=False, cwd=mkdtemp(self))

    def test_the_fixture_template_is_valid_and_no_store_is_opened(self):
        r = self.validate(TEMPLATE)
        self.assertTrue(r.ok, r)
        self.assertEqual(r.result, {"valid": True, "format": 1, "types": 2})
        self.assertIsNone(r.env["store_seq"])

    def test_every_rule_names_its_path(self):
        cases = {
            "template.extra": lambda t: t.update(extra=1),
            "template.format": lambda t: t.update(format=2),
            "template.version": lambda t: t.update(version=0),
            "template.relations": lambda t: t.pop("relations"),
            "template.types.widget.colour": lambda t: widget(t).update(
                colour="red"),
            "template.types.Widget": lambda t: t["types"].update(
                Widget=t["types"].pop("widget")),
            "template.types.widget.fields.state":
                lambda t: widget(t)["fields"].update(state={"kind": "text"}),
            "template.types.widget.fields.label.kind":
                lambda t: widget(t)["fields"]["label"].update(kind="blob"),
            "template.types.widget.fields.label.values":
                lambda t: widget(t)["fields"]["label"].update(values=["a"]),
            "template.types.widget.fields.size.values[1]":
                lambda t: widget(t)["fields"]["size"].update(
                    values=["XS", "XS"]),
            "template.types.widget.fields.colors.of.kind":
                lambda t: widget(t)["fields"]["colors"].update(
                    of={"kind": "list", "of": {"kind": "text"}}),
            "template.types.widget.fields.made_from.to[0]":
                lambda t: widget(t)["fields"]["made_from"].update(to=["nope"]),
            "template.types.widget.prefix":
                lambda t: widget(t).update(prefix="w"),
            "template.types.gauge.prefix":
                lambda t: t["types"]["gauge"].update(prefix="W"),
            "template.types.widget.digits":
                lambda t: widget(t).update(digits=0),
            "template.types.widget.initial":
                lambda t: widget(t).update(initial="nowhere"),
            "template.types.widget.terminal[0]":
                lambda t: widget(t).update(terminal=["gone"]),
            "template.types.widget.transitions.polish.to":
                lambda t: widget(t)["transitions"]["polish"].update(to="x"),
            "template.types.widget.transitions.polish.from[0]":
                lambda t: widget(t)["transitions"]["polish"].update(
                    **{"from": ["x"]}),
            "template.types.widget.transitions.polish.guards":
                lambda t: widget(t)["transitions"]["polish"].pop("guards"),
            "template.types.widget.create_guards[0].fields[0]":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "required", "fields": ["nope"]}]),
            "template.types.widget.create_guards[0].kind":
                lambda t: widget(t).update(create_guards=[{"kind": "script"}]),
            "template.types.widget.create_guards[0]":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "required"}]),
            "template.types.widget.create_guards[0].at_least.bench":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "required", "at_least": {"bench": "north"}}]),
            "template.types.widget.create_guards[0].when.colors":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "required", "fields": ["bench"],
                     "when": {"colors": [None]}}]),
            "template.types.widget.create_guards[0].when":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "required", "fields": ["bench"],
                     "when": {"bench": ["north"], "size": ["S"]}}]),
            "template.types.widget.create_guards[0].when.bench[0]":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "required", "fields": ["bench"],
                     "when": {"bench": ["east"]}}]),
            "template.types.widget.create_guards[0].max":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "limit", "max": 0, "mode": "warn"}]),
            "template.types.widget.create_guards[0].mode":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "limit", "max": 1, "mode": "maybe"}]),
            "template.types.widget.create_guards[0].per[0]":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "limit", "max": 1, "mode": "warn",
                     "per": ["colors"]}]),
            "template.types.widget.create_guards[0].relation":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "relations_closed", "relation": "nope",
                     "direction": "incoming"}]),
            "template.types.widget.create_guards[0].direction":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "relations_closed", "relation": "blocks",
                     "direction": "sideways"}]),
            "template.types.widget.create_guards[0].actor_kind":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "actor", "actor_kind": "robot"}]),
            "template.types.widget.create_guards[0].script":
                lambda t: widget(t).update(create_guards=[
                    {"kind": "actor", "name": "Pat", "script": "x"}]),
            "template.relations.blocks":
                lambda t: t["relations"].update(
                    blocks={"from": ["widget"], "to": ["widget"]}),
            "template.relations.pairs_with.to[0]":
                lambda t: t["relations"]["pairs_with"].update(to=["nope"]),
        }
        for path, mutate in cases.items():
            with self.subTest(path=path):
                r = self.validate(variant(mutate))
                self.assertEqual((r.code, r.code_name), (1, "template_invalid"),
                                 r)
                paths = [p["path"] for p in r.details["problems"]]
                self.assertIn(path, paths)

    def test_there_is_no_expression_language(self):
        """A `when` is one field and a list of values; anything else is
        refused rather than interpreted."""
        for when in ({"bench": "north"}, {"bench": {"not": ["north"]}},
                     "bench == 'north'", {}):
            with self.subTest(when=when):
                r = self.validate(variant(lambda t: widget(t).update(
                    create_guards=[{"kind": "required", "fields": ["bench"],
                                    "when": when}])))
                self.assertEqual(r.code_name, "template_invalid", r)


class TestApply(unittest.TestCase):

    def test_versions_must_rise(self):
        sb = Sandbox(self)
        sb.init()
        first = sb.apply()
        self.assertEqual(first, {"name": "workshop", "version": 1,
                                 "previous_version": None})
        same = sb.run("template", "apply",
                      data={"actor": ACTOR, "template": TEMPLATE})
        self.assertEqual(same.env["effect"], "unchanged")
        changed = variant(lambda t: widget(t)["fields"].update(
            note_text={"kind": "text"}))
        r = sb.run("template", "apply", data={"actor": ACTOR,
                                              "template": changed})
        self.assertEqual(r.code_name, "template_version", r)
        changed["version"] = 2
        self.assertEqual(sb.ok("template", "apply",
                               data={"actor": ACTOR, "template": changed}),
                         {"name": "workshop", "version": 2,
                          "previous_version": 1})
        TEMPLATE_V0 = variant(lambda t: t.update(version=1))
        r = sb.run("template", "apply", data={"actor": ACTOR,
                                              "template": TEMPLATE_V0})
        self.assertEqual(r.code_name, "template_version", r)

    def test_show_returns_the_applied_template_verbatim(self):
        sb = Sandbox(self)
        sb.init()
        self.assertEqual(sb.ok("template", "show"),
                         {"template": None, "version": None,
                          "applied_seq": None, "applied_at": None})
        sb.apply()
        shown = sb.ok("template", "show")
        self.assertEqual(shown["template"], TEMPLATE)
        self.assertNotIn("digits", shown["template"]["types"]["gauge"])
        self.assertEqual((shown["version"], shown["applied_seq"]), (1, 2))
        self.assertTrue(shown["applied_at"].endswith("Z"))

    def test_the_event_carries_the_previous_version_and_the_template(self):
        sb = Sandbox(self).ready()
        event = sb.events(keys=["template"])[0]
        self.assertEqual(event["changes"], [{"key": "template", "before": None,
                                             "after": TEMPLATE}])

    def test_existing_items_are_not_rechecked(self):
        sb = Sandbox(self).ready()
        item = sb.create()
        v2 = variant(lambda t: (t.update(version=2), widget(t).update(
            create_guards=[{"kind": "required", "fields": ["label"]}])))
        sb.ok("template", "apply", data={"actor": ACTOR, "template": v2})
        self.assertEqual(sb.get(item)["fields"]["label"], None)
        r = sb.run("item", "create", data={"actor": ACTOR, "type": "widget",
                                           "fields": {"bench": "north"}})
        self.assertEqual(r.code_name, "guard_refused")

    def test_no_template(self):
        sb = Sandbox(self)
        sb.init()
        for words, data in (
                (("item", "create"), {"actor": ACTOR, "type": "widget"}),
                (("item", "get"), {"id": "W-001"}),
                (("rel", "add"), {"actor": ACTOR, "kind": "blocks",
                                  "from": "W-1", "to": "W-2"}),
                (("attach", "add"), {"actor": ACTOR, "id": "W-1", "ref": "a"}),
                (("query",), {})):
            with self.subTest(command=words):
                r = sb.run(*words, data=data)
                self.assertEqual((r.code, r.code_name), (1, "no_template"), r)


class TestCompatibility(unittest.TestCase):
    """A new version cannot strand stored data; adding is always compatible."""

    def setUp(self):
        self.sb = Sandbox(self).ready()
        sb = self.sb
        self.a = sb.create(fields={"bench": "south", "size": "M",
                                   "label": "x", "colors": ["red"]})
        self.b = sb.create(fields={"bench": "north", "made_from": self.a})
        self.g = sb.create("gauge", {"reading": {"target": 5,
                                                 "direction": "up"}})
        sb.move(self.a, "start")
        sb.ok("rel", "add", data={"actor": ACTOR, "kind": "pairs_with",
                                  "from": self.a, "to": self.b})

    def refused_by(self, mutate, message_part, item):
        v2 = variant(lambda t: (t.update(version=2), mutate(t)))
        r = self.sb.run("template", "apply",
                        data={"actor": ACTOR, "template": v2})
        self.assertEqual(r.code_name, "template_incompatible", r)
        problems = r.details["problems"]
        hit = [p for p in problems if message_part in p["message"]]
        self.assertTrue(hit, problems)
        self.assertIn(item, hit[0]["items"])

    def test_what_strands_data(self):
        self.refused_by(lambda t: t["types"].pop("gauge"),
                        "type gauge is removed", self.g)
        self.refused_by(lambda t: (
            widget(t)["states"].remove("cutting"),
            widget(t)["transitions"].pop("start"),
            widget(t)["transitions"].pop("polish"),
            widget(t)["transitions"]["scrap"].update(
                **{"from": ["queued", "polished"]})),
            "state widget.cutting", self.a)
        self.refused_by(lambda t: widget(t)["fields"].pop("label"),
                        "field widget.label is removed", self.a)
        self.refused_by(lambda t: widget(t)["fields"]["label"].update(
            kind="int"), "changes kind", self.a)
        self.refused_by(lambda t: widget(t)["fields"]["colors"].update(
            of={"kind": "int"}), "changes kind", self.a)
        self.refused_by(lambda t: widget(t)["fields"]["size"].update(
            values=["XS", "S", "L"]), "size would no longer", self.a)
        self.refused_by(lambda t: widget(t)["fields"]["made_from"].update(
            to=["gauge"]), "made_from would no longer", self.b)
        self.refused_by(lambda t: t["relations"].pop("pairs_with"),
                        "relation kind pairs_with is removed", self.a)
        self.refused_by(lambda t: widget(t).update(prefix="V"),
                        "prefix or digits", self.a)
        self.refused_by(lambda t: widget(t).update(digits=4),
                        "prefix or digits", self.a)
        self.assertEqual(self.sb.ok("template", "show")["version"], 1)

    def test_adding_is_compatible(self):
        def grow(t):
            t["version"] = 2
            widget(t)["states"].append("resting")
            widget(t)["fields"]["colour_code"] = {"kind": "int"}
            widget(t)["fields"]["size"]["values"].append("XL")
            widget(t)["transitions"]["rest"] = {
                "from": ["queued"], "to": "resting", "guards": []}
            t["types"]["crate"] = {"prefix": "C", "states": ["open", "sealed"],
                                   "initial": "open", "terminal": ["sealed"],
                                   "fields": {}, "transitions": {}}
            t["relations"]["holds"] = {"from": ["crate"], "to": ["widget"]}
        r = self.sb.run("template", "apply",
                        data={"actor": ACTOR, "template": variant(grow)})
        self.assertTrue(r.ok, r)
        self.assertEqual(self.sb.create("crate", {}), "C-1")


if __name__ == "__main__":
    unittest.main()
