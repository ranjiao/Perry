"""A whole lifecycle through the executable alone (Goal 3; acceptance 3).

Every step is a separate `bin/perry` process: no in-process call, no
agent, no markdown. It inits, applies the template, creates items of each
type, moves them through every transition, relates, attaches, queries, and
then exports, imports into an empty store and exports again. The two exports
must be byte-identical.
"""

from __future__ import annotations

import json
import shutil
import unittest

from support import ACTOR, HUMAN, TEMPLATE, Sandbox


class TestTheLifecycleThroughTheCli(unittest.TestCase):

    def call(self, sb, *words, data=None, **kw):
        r = sb.cli(*words, data=data, **kw)
        self.assertEqual(r.code, 0, r)
        self.assertTrue(r.ok, r)
        self.assertEqual(r.err, "")
        return r.env

    def test_init_to_reexport(self):
        sb = Sandbox(self)
        self.assertEqual(self.call(sb, "init", data={
            "actor": ACTOR, "state_root": sb.state_root})["events"], [1])

        # The template from a file, as a skill would pass it.
        tpl_file = sb.tmp / "template.json"
        tpl_file.write_text(json.dumps({"actor": ACTOR,
                                        "template": TEMPLATE}))
        self.call(sb, "template", "apply", data=f"@{tpl_file}")
        shown = self.call(sb, "template", "show")["result"]
        self.assertEqual(shown["template"], TEMPLATE)
        described = self.call(sb, "describe", store=False, root=False)
        self.assertEqual(described["result"]["budget"],
                         {"concepts": 8, "command_groups": 12})

        def create(type_name, fields, **extra):
            env = self.call(sb, "item", "create", data={
                "actor": ACTOR, "type": type_name, "fields": fields, **extra})
            return env["result"]["item"]["id"]

        def move(item, transition, actor=ACTOR, **extra):
            env = self.call(sb, "item", "move", data={
                "actor": actor, "id": item, "transition": transition,
                **extra})
            return env["result"]["to_state"]

        shipped = create("widget", {"bench": "north", "size": "M"})
        early = create("widget", {"bench": "south"})
        mid = create("widget", {"bench": "north"})
        late = create("widget", {"bench": "south", "fragile": True,
                                 "size": "L"})
        gauge = create("gauge", {"reading": {"target": 3, "baseline": 0,
                                             "direction": "up"}})
        blocked = create("widget", {"bench": "north"},
                         relations=[{"kind": "blocks", "from": shipped},
                                    {"kind": "parent", "to": late}],
                         attachments=[{"ref": "notes/blocked.txt"}])

        # Every transition of every type, and every `from` state of scrap.
        self.assertEqual([move(shipped, t) for t in ("start", "polish")],
                         ["cutting", "polished"])
        self.assertEqual(move(shipped, "ship", set={"inspector": HUMAN}),
                         "shipped")
        self.assertEqual(move(early, "scrap"), "scrapped")
        self.assertEqual([move(mid, t) for t in ("start", "scrap")],
                         ["cutting", "scrapped"])
        self.assertEqual([move(late, t) for t in ("start", "polish")],
                         ["cutting", "polished"])
        refused = sb.cli("item", "move", data={
            "actor": ACTOR, "id": late, "transition": "ship",
            "set": {"inspector": HUMAN}})
        self.assertEqual((refused.code, refused.code_name),
                         (1, "guard_refused"), refused)
        self.assertTrue(refused.err.startswith("perry: guard_refused"))
        self.assertEqual(move(blocked, "start"), "cutting")
        self.assertEqual(move(blocked, "scrap"), "scrapped")
        self.assertEqual(move(late, "ship", actor=HUMAN,
                              set={"inspector": HUMAN}), "shipped")
        self.call(sb, "item", "update", data={
            "actor": ACTOR, "id": gauge, "set": {"reading": {"current": 3}},
            "note": "measured"}, stdin=None)
        self.assertEqual(move(gauge, "retire"), "retired")

        # Relate and attach, including a removal of each.
        self.call(sb, "rel", "add", data={"actor": ACTOR, "kind": "pairs_with",
                                          "from": early, "to": mid})
        self.call(sb, "rel", "add", data={"actor": ACTOR, "kind": "pairs_with",
                                          "from": mid, "to": early})
        self.call(sb, "rel", "remove", data={"actor": ACTOR,
                                             "kind": "pairs_with",
                                             "from": mid, "to": early})
        self.call(sb, "attach", "add", data={
            "actor": ACTOR, "id": shipped, "ref": "reports/final.pdf",
            "hash": "sha256:" + "1a" * 32})
        self.call(sb, "attach", "remove", data={
            "actor": ACTOR, "id": blocked, "ref": "notes/blocked.txt"})

        # Query, from stdin.
        q = self.call(sb, "query", data="-", stdin=json.dumps({
            "type": "widget", "count_by": ["state"]}))["result"]
        self.assertEqual(q["counts"], [{"key": {"state": "scrapped"}, "n": 3},
                                       {"key": {"state": "shipped"}, "n": 2}])
        got = self.call(sb, "item", "get",
                        data={"id": late})["result"]["item"]
        self.assertIsNone(got["rollup"])
        self.assertEqual(got["relations"], [
            {"kind": "parent", "from": blocked, "to": late}])

        # Export, import into an empty store, export again.
        first = self.call(sb, "export")
        self.assertEqual(first["effect"], "written")
        exported = sb.root / sb.state_root / "export"
        before = {n: (exported / n).read_bytes()
                  for n in ("items.jsonl", "events.jsonl")}

        other = Sandbox(self, state_root=sb.state_root)
        shutil.copytree(exported, other.root / other.state_root / "export")
        imported = self.call(other, "import",
                             data={"state_root": other.state_root})
        self.assertEqual(imported["result"]["verified"], True)
        self.assertEqual(imported["store_seq"], first["store_seq"])
        second = self.call(other, "export")
        self.assertEqual(second["effect"], "unchanged")
        after = {n: (other.root / other.state_root / "export" / n).read_bytes()
                 for n in ("items.jsonl", "events.jsonl")}
        self.assertEqual(after, before)
        self.assertEqual(second["result"]["files"], first["result"]["files"])

        # And the round trip refuses to run twice.
        again = other.cli("import", data={"state_root": other.state_root})
        self.assertEqual((again.code, again.code_name), (1, "store_not_empty"))


if __name__ == "__main__":
    unittest.main()
