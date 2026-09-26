"""Relations and attachments, and `item create` writing them in the same
transaction (§ 5.6; DESIGN-015 § 5.3: an edge made at create cannot half-land).
"""

from __future__ import annotations

import shutil
import unittest

import test_export_import
from support import ACTOR, Sandbox

edit = test_export_import.TestImport.edit


class RelCase(unittest.TestCase):

    def setUp(self):
        self.sb = Sandbox(self).ready()
        self.a, self.b, self.c = (self.sb.create() for _ in range(3))

    def rel(self, verb, kind, src, dst, **extra):
        return self.sb.run("rel", verb, data={"actor": ACTOR, "kind": kind,
                                              "from": src, "to": dst, **extra})


class TestRel(RelCase):

    def test_add_and_remove_record_the_edge_on_both_ends(self):
        r = self.rel("add", "blocks", self.a, self.b)
        self.assertEqual(r.result, {"relation": {"kind": "blocks",
                                                 "from": self.a,
                                                 "to": self.b}})
        seq = r.env["events"][0]
        event = self.sb.events()[-1]
        self.assertEqual(event["items"], [self.a, self.b])
        self.assertEqual(event["changes"], [
            {"key": f"rel:blocks:{self.a}:{self.b}", "before": False,
             "after": True}])
        for end in (self.a, self.b):
            got = self.sb.get(end)
            self.assertEqual(got["seq"], seq)
            self.assertEqual(got["relations"], [
                {"kind": "blocks", "from": self.a, "to": self.b}])
        self.assertEqual(self.rel("add", "blocks", self.a, self.b)
                         .env["effect"], "unchanged")
        r = self.rel("remove", "blocks", self.a, self.b)
        self.assertEqual(r.env["effect"], "written")
        self.assertEqual(self.sb.events()[-1]["changes"][0]["after"], False)
        self.assertEqual(self.rel("remove", "blocks", self.a, self.b)
                         .env["effect"], "unchanged")
        self.assertEqual(self.sb.get(self.a)["relations"], [])

    def test_refusals(self):
        g = self.sb.create("gauge")
        cases = [
            (("add", "blocks", self.a, self.a), "relation_invalid"),
            (("add", "pairs_with", self.a, g), "relation_invalid"),
            (("add", "pairs_with", g, self.a), "relation_invalid"),
            (("add", "follows", self.a, self.b), "unknown_relation"),
            (("add", "blocks", self.a, "W-404"), "item_not_found"),
            (("remove", "blocks", "W-404", self.a), "item_not_found"),
        ]
        for args, code in cases:
            with self.subTest(args=args):
                r = self.rel(*args)
                self.assertEqual((r.code, r.code_name), (1, code), r)

    def test_one_parent(self):
        self.assertTrue(self.rel("add", "parent", self.a, self.b).ok)
        r = self.rel("add", "parent", self.a, self.c)
        self.assertEqual(r.code_name, "relation_invalid", r)
        self.assertTrue(self.rel("add", "parent", self.c, self.b).ok,
                        "a parent may have many children")

    def test_cycles_in_blocks_and_parent(self):
        for kind in ("blocks", "parent"):
            with self.subTest(kind=kind):
                sb = Sandbox(self).ready()
                a, b, c = (sb.create() for _ in range(3))
                for src, dst in ((a, b), (b, c)):
                    sb.ok("rel", "add", data={"actor": ACTOR, "kind": kind,
                                              "from": src, "to": dst})
                r = sb.run("rel", "add", data={"actor": ACTOR, "kind": kind,
                                               "from": c, "to": a})
                self.assertEqual(r.code_name, "relation_cycle", r)
                self.assertEqual(sb.get(c)["relations"], [
                    {"kind": kind, "from": b, "to": c}])

    def test_a_declared_kind_may_run_both_ways(self):
        self.assertTrue(self.rel("add", "pairs_with", self.a, self.b).ok)
        self.assertTrue(self.rel("add", "pairs_with", self.b, self.a).ok)

    def test_compare_and_set(self):
        seq = self.sb.get(self.b)["seq"]
        self.rel("add", "blocks", self.a, self.b)
        r = self.rel("add", "blocks", self.c, self.b, expect={self.b: seq})
        self.assertEqual(r.code_name, "stale_write", r)


class TestCreateWithRelations(RelCase):

    def create(self, relations, **extra):
        return self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "widget", "fields": {"bench": "north"},
            "relations": relations, **extra})

    def test_edges_land_with_the_item(self):
        r = self.create([{"kind": "blocks", "to": self.a},
                         {"kind": "parent", "to": self.b},
                         {"kind": "pairs_with", "from": self.c}],
                        attachments=[{"ref": "notes/plan.txt"}])
        self.assertTrue(r.ok, r)
        new = r.result["item"]["id"]
        event = self.sb.events()[-1]
        self.assertEqual(event["items"], [new, self.a, self.b, self.c])
        self.assertEqual([c["key"] for c in event["changes"][3:]], [
            f"rel:blocks:{new}:{self.a}", f"rel:pairs_with:{self.c}:{new}",
            f"rel:parent:{new}:{self.b}", "attach:notes/plan.txt"])
        self.assertEqual(self.sb.get(self.a)["blocked_by"], [new])

    def test_a_refusal_lands_nothing(self):
        seq = self.sb.seq()
        cases = [
            ([{"kind": "blocks", "to": self.a}, {"kind": "blocks",
                                                 "to": "W-404"}],
             "item_not_found"),
            ([{"kind": "parent", "to": self.a}, {"kind": "parent",
                                                 "to": self.b}],
             "relation_invalid"),
            ([{"kind": "blocks", "to": self.a}, {"kind": "blocks",
                                                 "to": self.a}],
             "relation_invalid"),
            ([{"kind": "blocks", "to": self.a, "from": self.b}],
             "input_invalid"),
            ([{"kind": "blocks"}], "input_invalid"),
            ([{"kind": "nope", "to": self.a}], "unknown_relation"),
        ]
        for relations, code in cases:
            with self.subTest(code=code, relations=relations):
                r = self.create(relations)
                self.assertEqual(r.code_name, code, r)
        self.assertEqual(self.sb.seq(), seq)
        self.assertEqual(self.sb.get(self.a)["relations"], [])

    def test_a_cycle_through_the_new_item_is_refused(self):
        self.sb.ok("rel", "add", data={"actor": ACTOR, "kind": "blocks",
                                       "from": self.a, "to": self.b})
        r = self.create([{"kind": "blocks", "from": self.b},
                         {"kind": "blocks", "to": self.a}])
        self.assertEqual(r.code_name, "relation_cycle", r)
        self.assertEqual(self.sb.ok("query")["total"], 3)


class TestOneParentOnEveryPath(RelCase):
    """F1: an item has at most one parent, whichever path writes the edge.

    The paths that write a `parent` edge are `rel add`, `item create` with
    `{kind: parent, to}` (the new item is the child), `item create` with
    `{kind: parent, from}` (the new item is the parent of an existing one),
    and `import`'s replay. All four go through `Store._check_edge_shape`."""

    def setUp(self):
        super().setUp()
        self.sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent",
                                       "from": self.a, "to": self.b})
        self.seq = self.sb.seq()

    def assert_nothing_landed(self):
        self.assertEqual(self.sb.seq(), self.seq)
        self.assertEqual(self.sb.get(self.a)["relations"], [
            {"kind": "parent", "from": self.a, "to": self.b}])

    def test_rel_add(self):
        r = self.rel("add", "parent", self.a, self.c)
        self.assertEqual((r.code, r.code_name), (1, "relation_invalid"), r)
        self.assertEqual(r.details["parent"], self.b)
        self.assert_nothing_landed()

    def test_create_with_to(self):
        r = self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "widget", "fields": {"bench": "north"},
            "relations": [{"kind": "parent", "to": self.b},
                          {"kind": "parent", "to": self.c}]})
        self.assertEqual((r.code, r.code_name), (1, "relation_invalid"), r)
        self.assert_nothing_landed()

    def test_create_with_from_an_item_that_has_a_parent(self):
        r = self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "widget", "fields": {"bench": "north"},
            "relations": [{"kind": "parent", "from": self.a}]})
        self.assertEqual((r.code, r.code_name), (1, "relation_invalid"), r)
        self.assertEqual((r.details["from"], r.details["parent"]),
                         (self.a, self.b))
        self.assert_nothing_landed()
        self.assertEqual(self.sb.create(), "W-004", "no id was consumed")

    def test_create_with_from_an_orphan_is_allowed(self):
        new = self.sb.ok("item", "create", data={
            "actor": ACTOR, "type": "widget", "fields": {"bench": "north"},
            "relations": [{"kind": "parent", "from": self.c},
                          {"kind": "parent", "to": self.b}]})["item"]["id"]
        self.assertEqual(self.sb.get(self.c)["relations"], [
            {"kind": "parent", "from": self.c, "to": new}])

    def test_import_replay(self):
        def second_parent(items, events):
            add = edit(events[-1], lambda o: o.update(
                seq=len(events) + 1, command="rel add",
                items=[self.a, self.c], transition=None, note=None,
                warnings=[], changes=[{"key": f"rel:parent:{self.a}:{self.c}",
                                       "before": False, "after": True}]))
            return items, events + [add]
        self.sb.ok("export")
        r = replay(self, self.sb, second_parent)
        self.assertEqual((r.code, r.code_name), (1, "export_invalid"), r)
        self.assertEqual((r.details["seq"], r.details["parent"]),
                         (self.seq + 1, self.b))


class TestEdgeShapeOnImport(unittest.TestCase):
    """The other two shape rules, which `import` used to replay unchecked."""

    def test_re_adding_an_existing_parent_edge_never_reaches_the_shape_check(self):
        """Why `_check_edge_shape` needs no `d != dst` filter (round 4, A3):
        the edge being added never exists when the check runs. Live, `rel
        add` of an existing edge is unchanged; replayed, an event that adds
        it again says `before: false` against a stored true, and the before
        comparison refuses it first."""
        sb = Sandbox(self).ready()
        a, b = sb.create(), sb.create()
        edge = {"actor": ACTOR, "kind": "parent", "from": a, "to": b}
        sb.ok("rel", "add", data=edge)
        again = sb.run("rel", "add", data=edge)
        self.assertEqual(again.env["effect"], "unchanged", again)
        sb.ok("export")

        def readd(items, events):
            return items, events + [edit(events[-1], lambda o: o.update(
                seq=len(events) + 1))]
        r = replay(self, sb, readd)
        self.assertEqual(r.code_name, "export_invalid", r)
        self.assertEqual(r.details["key"], f"rel:parent:{a}:{b}")
        self.assertIn("the event says it was false",
                      r.env["error"]["message"])

    def test_a_self_edge_and_a_cycle_are_export_invalid(self):
        for name, changes in (
                ("self-edge", [{"key": "rel:blocks:W-001:W-001",
                                "before": False, "after": True}]),
                ("cycle", [{"key": "rel:blocks:W-002:W-001",
                            "before": False, "after": True}])):
            with self.subTest(name):
                sb = Sandbox(self).ready()
                a, b = sb.create(), sb.create()
                sb.ok("rel", "add", data={"actor": ACTOR, "kind": "blocks",
                                          "from": a, "to": b})
                sb.ok("export")

                def planted(items, events, changes=changes):
                    return items, events + [edit(events[-1], lambda o: o.update(
                        seq=len(events) + 1, items=[a, b], changes=changes))]
                r = replay(self, sb, planted)
                self.assertEqual(r.code_name, "export_invalid", r)
                self.assertEqual(r.details["seq"], 6)


def replay(testcase, sb, mutate):
    """Copy `sb`'s export into a fresh project, edit it, and import it."""
    other = Sandbox(testcase, state_root=sb.state_root)
    src = sb.root / sb.state_root / "export"
    dst = other.root / other.state_root / "export"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    items = (dst / "items.jsonl").read_text("utf-8").splitlines(True)
    events = (dst / "events.jsonl").read_text("utf-8").splitlines(True)
    items, events = mutate(items, events)
    (dst / "items.jsonl").write_text("".join(items), "utf-8")
    (dst / "events.jsonl").write_text("".join(events), "utf-8")
    r = other.run("import", data={"state_root": other.state_root})
    testcase.assertFalse(other.store.exists() and other.run(
        "events", data={}).ok, "a refused import leaves no initialised store")
    return r


class TestAttachments(RelCase):
    HASH = "sha256:" + "ab" * 32

    def attach(self, verb, ref, **extra):
        return self.sb.run("attach", verb, data={"actor": ACTOR, "id": self.a,
                                                 "ref": ref, **extra})

    def test_add_change_and_remove(self):
        ref = "https://example.invalid/never/opened"
        r = self.attach("add", ref, hash=self.HASH)
        self.assertEqual(r.result, {"attachment": {"item": self.a, "ref": ref,
                                                   "hash": self.HASH}})
        self.assertEqual(self.sb.events()[-1]["changes"], [
            {"key": f"attach:{ref}", "before": None,
             "after": {"hash": self.HASH}}])
        self.assertEqual(self.attach("add", ref, hash=self.HASH)
                         .env["effect"], "unchanged")
        other = "sha256:" + "cd" * 32
        self.assertEqual(self.attach("add", ref, hash=other).env["effect"],
                         "written")
        self.assertEqual(self.sb.get(self.a)["attachments"],
                         [{"ref": ref, "hash": other}])
        r = self.attach("remove", ref)
        self.assertEqual(self.sb.events()[-1]["changes"][0]["after"], None)
        self.assertEqual(r.result["attachment"]["hash"], other)
        self.assertEqual(self.attach("remove", ref).env["effect"], "unchanged")
        self.assertEqual(self.attach("add", "no/hash.txt").result,
                         {"attachment": {"item": self.a, "ref": "no/hash.txt",
                                         "hash": None}})

    def test_refusals(self):
        for ref, digest in (("", None), ("  ", None), ("a\nb", None),
                            ("a\rb", None), ("ok", "md5:abc"),
                            ("ok", "sha256:" + "AB" * 32),
                            ("ok", "sha256:" + "ab" * 31)):
            with self.subTest(ref=ref, digest=digest):
                extra = {"hash": digest} if digest else {}
                r = self.attach("add", ref, **extra)
                self.assertEqual(r.code_name, "attachment_invalid", r)
        r = self.sb.run("attach", "remove", data={
            "actor": ACTOR, "id": self.a, "ref": "x", "hash": self.HASH})
        self.assertEqual(r.code_name, "unknown_key", r)
        r = self.sb.run("item", "create", data={
            "actor": ACTOR, "type": "widget", "fields": {"bench": "north"},
            "attachments": [{"ref": "x"}, {"ref": "x"}]})
        self.assertEqual(r.code_name, "attachment_invalid", r)


if __name__ == "__main__":
    unittest.main()
