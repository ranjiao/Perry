"""Relations and attachments, and `item create` writing them in the same
transaction (§ 5.6; DESIGN-015 § 5.3: an edge made at create cannot half-land).
"""

from __future__ import annotations

import unittest

from support import ACTOR, Sandbox


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
