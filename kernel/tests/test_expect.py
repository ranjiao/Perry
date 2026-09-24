"""Compare-and-set through `expect`, on every command that takes it (§ 5.6).

Round 3, F2: mutants that deleted the `expect` check from `item create`,
`item move` and `attach add` / `attach remove` survived, because only
`item update` and `rel add` had a stale-write test. The category is every
command whose declaration carries `expect`, read from `describe`, so a
command that gains the key tomorrow is covered the day it is declared.
"""

from __future__ import annotations

import unittest

from support import ACTOR, Sandbox

from perry_kernel import surface

HASH = "sha256:" + "ab" * 32


def with_expect() -> list[str]:
    return [c["name"] for c in surface.COMMANDS
            if c["input"] and "expect" in c["input"]]


class TestEveryExpectIsCompared(unittest.TestCase):

    def setUp(self):
        self.fresh()

    def fresh(self):
        self.sb = Sandbox(self).ready()
        self.a = self.sb.create()
        self.b = self.sb.create()
        self.sb.ok("attach", "add", data={"actor": ACTOR, "id": self.a,
                                          "ref": "old"})
        self.sb.ok("rel", "add", data={"actor": ACTOR, "kind": "pairs_with",
                                       "from": self.b, "to": self.a})

    def request(self, name: str) -> dict:
        """A write of `name` that would succeed, touching `self.a`."""
        return {
            "item create": {"type": "widget", "fields": {"bench": "north"},
                            "relations": [{"kind": "blocks",
                                           "to": self.a}]},
            "item update": {"id": self.a, "set": {"label": "new"}},
            "item move": {"id": self.a, "transition": "start"},
            "rel add": {"kind": "blocks", "from": self.b, "to": self.a},
            "rel remove": {"kind": "pairs_with", "from": self.b,
                           "to": self.a},
            "attach add": {"id": self.a, "ref": "new", "hash": HASH},
            "attach remove": {"id": self.a, "ref": "old"},
        }[name]

    def test_the_category_is_the_declared_one(self):
        self.assertEqual(sorted(with_expect()), [
            "attach add", "attach remove", "item create", "item move",
            "item update", "rel add", "rel remove"])

    def test_a_stale_seq_is_refused_and_nothing_lands(self):
        for name in with_expect():
            with self.subTest(command=name):
                read = self.sb.get(self.a)["seq"]
                # Someone else moves the item after it was read.
                self.sb.ok("item", "update", data={
                    "actor": ACTOR, "id": self.a,
                    "set": {"pieces": read}})
                before = self.sb.seq()
                r = self.sb.run(*name.split(), data={
                    "actor": ACTOR, **self.request(name),
                    "expect": {self.a: read}})
                self.assertEqual((r.code, r.code_name), (1, "stale_write"), r)
                self.assertEqual(r.details["items"], [
                    {"id": self.a, "expected": read, "actual": read + 1}])
                self.assertEqual(self.sb.seq(), before)

    def test_a_fresh_seq_is_accepted(self):
        for name in with_expect():
            with self.subTest(command=name):
                self.fresh()
                r = self.sb.run(*name.split(), data={
                    "actor": ACTOR, **self.request(name),
                    "expect": {self.a: self.sb.get(self.a)["seq"]}})
                self.assertTrue(r.ok, r)
                self.assertEqual(r.env["effect"], "written", r)


if __name__ == "__main__":
    unittest.main()
