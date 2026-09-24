"""The CLI rules: NN-K3, NN-K4, NN-K6 and NN-K8, and the envelope (§ 5.1)."""

from __future__ import annotations

import json
import unittest
from unittest import mock

from support import ACTOR, HUMAN, Sandbox, clean_env, mkdtemp

ENVELOPE_KEYS = ["ok", "surface", "command", "effect", "events", "store_seq",
                 "warnings", "result", "error"]


class TestHelpNeverExecutes(unittest.TestCase):
    """NN-K3: -h or --help in any position prints usage, exits 0, and resolves
    no root, reads no input and opens no store."""

    def test_help_anywhere_touches_nothing(self):
        sb = Sandbox(self)
        store = sb.tmp / "never.db"
        write = ["item", "create", "--input", "not json at all",
                 "--store", str(store), "--root", str(sb.tmp / "nowhere")]
        for where in range(len(write) + 1):
            argv = write[:where] + ["--help"] + write[where:]
            with self.subTest(position=where):
                r = sb.run(*argv, store=False, root=False,
                           env=clean_env(PERRY_STORE=str(store)))
                self.assertEqual(r.code, 0, r)
                self.assertIn("usage", r.out.lower())
                self.assertFalse(store.exists())
                self.assertEqual(r.err, "")

    def test_short_flag_and_command_usage(self):
        sb = Sandbox(self)
        r = sb.run("item", "move", "-h", store=False, root=False)
        self.assertEqual(r.code, 0)
        self.assertIn("usage: perry-kernel item move", r.out)
        self.assertIn("transition", r.out)
        self.assertIn("required", r.out)

    def test_help_for_an_unknown_command_is_the_general_usage(self):
        r = Sandbox(self).run("frobnicate", "--help", store=False, root=False)
        self.assertEqual(r.code, 0)
        self.assertIn("commands:", r.out)

    def test_help_through_the_executable(self):
        sb = Sandbox(self)
        r = sb.cli("init", "--help", data={"actor": ACTOR, "state_root": "x"})
        self.assertEqual(r.code, 0, r)
        self.assertIn("usage: perry-kernel init", r.out)
        self.assertFalse(sb.store.exists())


class TestNothingUndeclaredIsAccepted(unittest.TestCase):
    """NN-K4: exit 2 for every undeclared token, and for a declared flag on a
    command that does not honour it."""

    def setUp(self):
        self.sb = Sandbox(self).ready()

    def usage(self, *argv, **kw):
        r = self.sb.run(*argv, **kw)
        self.assertEqual(r.code, 2, r)
        self.assertEqual(r.code_name, "usage", r)
        self.assertTrue(r.err.startswith("perry-kernel: usage: "), r.err)
        return r

    def test_unknown_command_and_no_command(self):
        self.usage("frobnicate")
        self.usage()
        self.usage("item")
        self.usage("item", "destroy")

    def test_undeclared_flag_on_reads_and_writes(self):
        for words in (("describe",), ("query",), ("template", "show"),
                      ("item", "create")):
            with self.subTest(command=words):
                r = self.usage(*words, flags=["--xyzzy"])
                self.assertIn("--store", r.details["legal_flags"])

    def test_undeclared_positional(self):
        self.usage("item", "get", "W-001")
        self.usage("describe", "extra")

    def test_a_flag_the_command_does_not_honour(self):
        self.usage("query", flags=["--dry-run"])
        self.usage("item", "get", data={"id": "W-001"}, flags=["--dry-run"])
        self.usage("describe", data={}, store=False, root=False)
        self.usage("template", "show", data={})
        self.usage("export", data={})

    def test_missing_argument_repeated_flag_and_value_on_a_switch(self):
        self.usage("query", "--store")
        self.usage("query", flags=["--store", str(self.sb.store)])
        self.usage("query", flags=["--json=yes"])

    def test_json_flag_is_accepted_and_changes_nothing(self):
        plain = self.sb.run("template", "show")
        flagged = self.sb.run("template", "show", flags=["--json"])
        self.assertEqual(plain.out, flagged.out)

    def test_unknown_key_at_every_declared_level(self):
        cases = [
            ("item create", {"actor": ACTOR, "type": "widget", "colour": 1},
             "colour"),
            ("item create", {"actor": {**ACTOR, "role": "x"}, "type": "widget"},
             "actor.role"),
            ("item create", {"actor": ACTOR, "type": "widget",
                             "relations": [{"kind": "blocks", "to": "W-001",
                                            "weight": 2}]},
             "relations[0].weight"),
            ("item create", {"actor": ACTOR, "type": "widget",
                             "attachments": [{"ref": "a", "size": 1}]},
             "attachments[0].size"),
            ("query", {"related": {"kind": "blocks", "to": "W-1", "x": 1}},
             "related.x"),
            ("describe", None, None),
        ]
        for name, data, path in cases:
            if data is None:
                continue
            with self.subTest(path=path):
                r = self.sb.run(*name.split(), data=data)
                self.assertEqual(r.code, 2, r)
                self.assertEqual(r.code_name, "unknown_key", r)
                self.assertEqual(r.details["keys"][0]["path"], path)
                self.assertTrue(r.details["keys"][0]["legal"])

    def test_input_invalid(self):
        cases = [
            "not json", "[1, 2]", '"a string"', '{"limit": NaN}',
            '{"limit": 1, "limit": 2}', '{"limit": "5"}', '{"type": 3}',
            '{"related": {"kind": 3, "to": "W-1"}}', '{"ids": "W-1"}',
            '{"terminal": "yes"}', "{} {}",
        ]
        for text in cases:
            with self.subTest(input=text):
                r = self.sb.run("query", data=text)
                self.assertEqual(r.code, 2, r)
                self.assertEqual(r.code_name, "input_invalid", r)

    def test_a_missing_required_key(self):
        r = self.sb.run("item", "get", data={})
        self.assertEqual((r.code, r.code_name), (2, "input_invalid"), r)

    def test_actor_invalid(self):
        bad = [None, {"kind": "robot", "name": "x"},
               {"kind": "human", "name": "  "},
               {"kind": "agent", "name": "x"},
               {"kind": 3, "name": "x"}, "someone"]
        for actor in bad:
            data = {"type": "widget", "fields": {"bench": "north"}}
            if actor is not None:
                data["actor"] = actor
            with self.subTest(actor=actor):
                r = self.sb.run("item", "create", data=data)
                self.assertEqual(r.code, 2, r)
                self.assertIn(r.code_name, ("actor_invalid", "input_invalid"))
                if not isinstance(actor, str):
                    self.assertEqual(r.code_name, "actor_invalid", r)

    def test_a_human_needs_no_session(self):
        r = self.sb.run("item", "create", data={
            "actor": {"kind": "human", "name": "Pat"}, "type": "widget",
            "fields": {"bench": "north"}})
        self.assertTrue(r.ok, r)
        event = self.sb.events()[-1]
        self.assertEqual(event["actor"],
                         {"kind": "human", "name": "Pat", "session": None})

    def test_input_from_a_file_and_from_stdin(self):
        path = self.sb.tmp / "in.json"
        path.write_text(json.dumps({"id": "W-001"}))
        created = self.sb.create()
        self.assertEqual(created, "W-001")
        self.assertTrue(self.sb.run("item", "get", data=f"@{path}").ok)
        self.assertTrue(self.sb.run("item", "get", data="-",
                                    stdin='{"id": "W-001"}').ok)
        r = self.sb.run("item", "get", data=f"@{self.sb.tmp / 'missing.json'}")
        self.assertEqual((r.code, r.code_name), (1, "io_error"), r)


class TestTheEnvelope(unittest.TestCase):
    """§ 5.1 and NN-K6: one JSON object, every key always present."""

    def test_every_key_on_success_and_on_refusal(self):
        sb = Sandbox(self).ready()
        runs = [sb.run("describe", store=False, root=False),
                sb.run("item", "get", data={"id": "W-404"}),
                sb.run("query", flags=["--xyzzy"]),
                sb.run("template", "show")]
        for r in runs:
            with self.subTest(out=r.out[:80]):
                self.assertEqual(list(r.env), ENVELOPE_KEYS)
                self.assertEqual(r.out.count("\n"), 1)
                self.assertEqual(r.env["surface"], "1.0")
                if r.env["ok"]:
                    self.assertIsNone(r.env["error"])
                    self.assertEqual(r.err, "")
                else:
                    self.assertEqual(list(r.env["error"]),
                                     ["code", "message", "details"])
                    self.assertIsNone(r.env["result"])
                    self.assertEqual(r.env["effect"], "refused")
                    self.assertEqual(
                        r.err, f"perry-kernel: {r.code_name}: "
                               f"{r.env['error']['message']}\n")

    def test_reads_carry_store_seq(self):
        sb = Sandbox(self).ready()
        self.assertEqual(sb.run("template", "show").env["store_seq"], 2)
        refused = sb.run("item", "get", data={"id": "W-404"})
        self.assertEqual(refused.env["store_seq"], 2)
        self.assertEqual(refused.code, 1)

    def test_an_internal_fault_is_an_envelope_and_rolls_back(self):
        sb = Sandbox(self).ready()
        with mock.patch("perry_kernel.commands.run_guards",
                        side_effect=RuntimeError("boom")):
            r = sb.run("item", "create", data={
                "actor": ACTOR, "type": "widget",
                "fields": {"bench": "north"}})
        self.assertEqual(r.code, 3, r)
        self.assertEqual(r.code_name, "internal")
        self.assertNotIn("Traceback", r.out + r.err)
        self.assertEqual(sb.seq(), 2)
        self.assertEqual(sb.ok("query")["total"], 0)
        self.assertEqual(sb.create(), "W-001")


class TestANoOpReadsDifferentlyFromAWrite(unittest.TestCase):
    """NN-K8: written, unchanged and dry_run are three different answers."""

    def test_written_unchanged_and_dry_run(self):
        sb = Sandbox(self).ready()
        item = sb.create()
        write = sb.run("item", "update", data={
            "actor": ACTOR, "id": item, "set": {"label": "a"}})
        self.assertEqual((write.env["effect"], write.env["events"],
                          write.env["store_seq"]), ("written", [4], 4))
        again = sb.run("item", "update", data={
            "actor": ACTOR, "id": item, "set": {"label": "a"}})
        self.assertEqual((again.env["effect"], again.env["events"],
                          again.env["store_seq"]), ("unchanged", [], 4))
        dry = sb.run("item", "update", data={
            "actor": ACTOR, "id": item, "set": {"label": "b"}},
            flags=["--dry-run"])
        self.assertEqual((dry.env["effect"], dry.env["events"]),
                         ("dry_run", []))
        self.assertEqual(dry.result["item"]["fields"]["label"], "b")
        self.assertEqual(sb.get(item)["fields"]["label"], "a")
        self.assertEqual(sb.seq(), 4)

    def test_dry_run_reports_the_id_it_would_mint_unreserved(self):
        sb = Sandbox(self).ready()
        dry = sb.run("item", "create", data={
            "actor": ACTOR, "type": "widget", "fields": {"bench": "north"}},
            flags=["--dry-run"])
        self.assertEqual(dry.result["item"]["id"], "W-001")
        self.assertEqual(sb.create(), "W-001")

    def test_dry_run_init_creates_nothing(self):
        sb = Sandbox(self)
        r = sb.run("init", data={"actor": HUMAN, "state_root": "s"},
                   flags=["--dry-run"])
        self.assertEqual(r.env["effect"], "dry_run", r)
        self.assertFalse(sb.store.exists())

    def test_describe_needs_no_store_and_no_anchor(self):
        tmp = mkdtemp(self)
        sb = Sandbox(self)
        r = sb.run("describe", store=False, root=False, cwd=tmp)
        self.assertTrue(r.ok, r)
        self.assertIsNone(r.env["store_seq"])


if __name__ == "__main__":
    unittest.main()
