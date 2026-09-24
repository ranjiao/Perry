"""Export and import (§ 5.8; acceptance criterion 4)."""

from __future__ import annotations

import json
import shutil
import unittest

from support import ACTOR, HUMAN, Sandbox


def populated(testcase) -> Sandbox:
    sb = Sandbox(testcase).ready()
    a = sb.create(fields={"bench": "north", "label": "café ✓ — naïve",
                          "colors": ["red"], "weight_g": 2.50,
                          "size": "M"})
    b = sb.create(relations=[{"kind": "blocks", "from": a}],
                  attachments=[{"ref": "docs/b.txt",
                                "hash": "sha256:" + "0f" * 32}])
    g = sb.create("gauge", {"reading": {"current": 1, "target": 4,
                                        "baseline": 0, "direction": "up"}})
    sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent", "from": g,
                              "to": a})
    sb.move(a, "start")
    sb.move(a, "polish")
    sb.move(g, "retire")
    sb.move(a, "ship", actor=HUMAN, set={"inspector": HUMAN})
    sb.ok("item", "update", data={"actor": ACTOR, "id": b,
                                  "unset": ["bench"], "note": "why not"})
    return sb


def export_dir(sb: Sandbox):
    return sb.root / sb.state_root / "export"


def twin(testcase, sb: Sandbox) -> Sandbox:
    """A second project holding a copy of `sb`'s export and an empty store."""
    other = Sandbox(testcase, state_root=sb.state_root)
    dst = export_dir(other)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(export_dir(sb), dst)
    return other


class TestExport(unittest.TestCase):

    def test_the_bytes_are_deterministic(self):
        sb = populated(self)
        r = sb.ok("export")
        directory = export_dir(sb)
        self.assertEqual(r["dir"], str(directory))
        self.assertEqual(sorted(p.name for p in directory.iterdir()),
                         ["events.jsonl", "items.jsonl"])
        items = (directory / "items.jsonl").read_bytes()
        events = (directory / "events.jsonl").read_bytes()
        self.assertEqual(r["files"]["items.jsonl"]["lines"], 3)
        self.assertEqual(r["files"]["events.jsonl"]["bytes"], len(events))
        self.assertEqual(r["last_export_seq"], sb.seq())
        for blob in (items, events):
            for raw in blob.split(b"\n")[:-1]:
                obj = json.loads(raw)
                self.assertEqual(raw.decode("utf-8"), json.dumps(
                    obj, sort_keys=True, separators=(",", ":"),
                    ensure_ascii=False))
        self.assertIn("café ✓ — naïve".encode("utf-8"), items)
        self.assertIn(b'"weight_g":2.5', items)
        lines = [json.loads(x) for x in items.splitlines()]
        self.assertEqual([x["id"] for x in lines], ["G-1", "W-001", "W-002"])
        self.assertEqual(sorted(lines[1]), ["attachments", "created_at",
                                            "fields", "id", "relations",
                                            "seq", "state", "type",
                                            "updated_at"])
        self.assertEqual(lines[1]["relations"],
                         [{"kind": "blocks", "to": "W-002"}])
        self.assertEqual(lines[0]["relations"],
                         [{"kind": "parent", "to": "W-001"}])
        self.assertNotIn("met", lines[0]["fields"]["reading"])
        self.assertNotIn("rollup", lines[1])
        seqs = [json.loads(x)["seq"] for x in events.splitlines()]
        self.assertEqual(seqs, list(range(1, len(seqs) + 1)))

    def test_an_unchanged_store_exports_the_same_bytes(self):
        sb = populated(self)
        sb.ok("export")
        first = {p.name: p.read_bytes() for p in export_dir(sb).iterdir()}
        again = sb.run("export")
        self.assertEqual(again.env["effect"], "unchanged")
        self.assertEqual({p.name: p.read_bytes()
                          for p in export_dir(sb).iterdir()}, first)

    def test_a_foreign_entry_is_refused_and_kept(self):
        sb = populated(self)
        directory = export_dir(sb)
        directory.mkdir(parents=True)
        (directory / "mine.txt").write_text("keep me")
        r = sb.run("export")
        self.assertEqual((r.code, r.code_name), (1, "export_dir_foreign"), r)
        self.assertEqual(r.details["entries"], ["mine.txt"])
        self.assertEqual(sorted(p.name for p in directory.iterdir()),
                         ["mine.txt"])

    def test_a_leftover_temp_file_is_removed_not_foreign(self):
        """A crash between writing a temp file and renaming it leaves the
        kernel's own file behind; the next export removes it."""
        from perry_kernel.commands import EXPORT_TEMP, export_temp_name
        for name in ("items.jsonl", "events.jsonl"):
            self.assertTrue(EXPORT_TEMP.match(export_temp_name(name)))
        sb = populated(self)
        directory = export_dir(sb)
        directory.mkdir(parents=True)
        stale = [".items.jsonl.4242.tmp", ".events.jsonl.1.tmp"]
        for name in stale:
            (directory / name).write_text("half written")
        dry = sb.run("export", flags=["--dry-run"])
        self.assertEqual(dry.env["effect"], "dry_run", dry)
        self.assertEqual(sorted(p.name for p in directory.iterdir()),
                         sorted(stale))
        r = sb.run("export")
        self.assertEqual(r.env["effect"], "written", r)
        self.assertEqual(sorted(p.name for p in directory.iterdir()),
                         ["events.jsonl", "items.jsonl"])
        (directory / stale[0]).write_text("again")
        r = sb.run("export")
        self.assertEqual(r.env["effect"], "unchanged", r)
        self.assertFalse((directory / stale[0]).exists())

    def test_a_lookalike_is_still_foreign(self):
        sb = populated(self)
        directory = export_dir(sb)
        directory.mkdir(parents=True)
        for name in (".items.jsonl.tmp", "items.jsonl.12.tmp",
                     ".notes.jsonl.12.tmp", ".items.jsonl.12.tmp.bak"):
            with self.subTest(name=name):
                (directory / name).write_text("mine")
                r = sb.run("export")
                self.assertEqual(r.code_name, "export_dir_foreign", r)
                self.assertEqual(r.details["entries"], [name])
                (directory / name).unlink()

    def test_dry_run_writes_nothing(self):
        sb = populated(self)
        r = sb.run("export", flags=["--dry-run"])
        self.assertEqual(r.env["effect"], "dry_run")
        self.assertFalse(export_dir(sb).exists())
        self.assertIsNone(sb.ok("events", data={"limit": 1})
                          ["last_export_seq"])


class TestImport(unittest.TestCase):

    def test_round_trip_is_byte_identical(self):
        sb = populated(self)
        sb.ok("export")
        other = twin(self, sb)
        r = other.ok("import", data={"state_root": other.state_root})
        self.assertEqual((r["items"], r["events"], r["last_seq"],
                          r["verified"]), (3, sb.seq(), sb.seq(), True))
        self.assertEqual(other.seq(), sb.seq())
        again = other.run("export")
        self.assertEqual(again.env["effect"], "unchanged")
        for name in ("items.jsonl", "events.jsonl"):
            self.assertEqual((export_dir(other) / name).read_bytes(),
                             (export_dir(sb) / name).read_bytes())
        for item_id in ("W-001", "W-002", "G-1"):
            self.assertEqual(other.get(item_id), sb.get(item_id))
        self.assertEqual(other.ok("template", "show"),
                         sb.ok("template", "show"))
        self.assertEqual(other.ok("events", data={"limit": 1})["unexported"],
                         0)
        self.assertEqual(other.create(), "W-003", "the ceiling came across")

    def test_a_store_that_is_not_empty_is_refused(self):
        sb = populated(self)
        sb.ok("export")
        seq = sb.seq()
        r = sb.run("import", data={"state_root": sb.state_root})
        self.assertEqual((r.code, r.code_name), (1, "store_not_empty"), r)
        fresh = Sandbox(self, state_root=sb.state_root, tmp=sb.tmp / "fresh")
        fresh.init()
        shutil.copytree(export_dir(sb), export_dir(fresh))
        r = fresh.run("import", data={"state_root": fresh.state_root})
        self.assertEqual(r.code_name, "store_not_empty", r)
        self.assertEqual(sb.seq(), seq)
        self.assertEqual(fresh.seq(), 1)

    def test_import_into_an_empty_file_and_dry_run(self):
        sb = populated(self)
        sb.ok("export")
        other = twin(self, sb)
        r = other.run("import", data={"state_root": other.state_root},
                      flags=["--dry-run"])
        self.assertEqual((r.env["effect"], r.result["verified"]),
                         ("dry_run", True), r)
        self.assertFalse(other.store.exists())
        other.store.write_bytes(b"")
        self.assertTrue(other.run("import",
                                  data={"state_root": other.state_root}).ok)

    def test_export_missing(self):
        sb = Sandbox(self)
        r = sb.run("import", data={"state_root": "state"})
        self.assertEqual((r.code, r.code_name), (1, "export_missing"), r)
        self.assertFalse(sb.store.exists())

    def mutate_and_import(self, mutate, code):
        sb = populated(self)
        sb.ok("export")
        other = twin(self, sb)
        directory = export_dir(other)
        items = (directory / "items.jsonl").read_text("utf-8").splitlines(True)
        events = (directory / "events.jsonl").read_text("utf-8").splitlines(True)
        items, events = mutate(items, events)
        (directory / "items.jsonl").write_text("".join(items), "utf-8")
        (directory / "events.jsonl").write_text("".join(events), "utf-8")
        r = other.run("import", data={"state_root": other.state_root})
        self.assertEqual((r.code, r.code_name), (1, code), r)
        state = other.store.exists() and other.run("events", data={}).code_name
        self.assertIn(state, (False, "store_missing"),
                      "a refused import leaves no initialised store")
        return r

    @staticmethod
    def edit(line: str, fn) -> str:
        obj = json.loads(line)
        fn(obj)
        return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False) + "\n"

    def test_export_invalid(self):
        cases = {
            "a gap": lambda i, e: (i, e[:3] + e[4:]),
            "an unknown event key": lambda i, e: (i, [
                self.edit(e[0], lambda o: o.update(extra=1))] + e[1:]),
            "an unknown item key": lambda i, e: ([
                self.edit(i[0], lambda o: o.update(extra=1))] + i[1:], e),
            "not JSON": lambda i, e: (i, e[:2] + ["{not json\n"] + e[3:]),
            "no final newline": lambda i, e: (i, e[:-1] + [e[-1].rstrip()]),
            "event 1 is another root": lambda i, e: (i, [self.edit(
                e[0], lambda o: o["changes"][0].update(after="other"))]
                + e[1:]),
            "a before that disagrees": lambda i, e: (i, e[:4] + [self.edit(
                e[4], lambda o: o["changes"][0].update(before="shipped"))]
                + e[5:]),
            "an edge to nothing": lambda i, e: (i, e + [self.edit(
                e[-1], lambda o: o.update(
                    seq=len(e) + 1, command="rel add", items=["W-001"],
                    changes=[{"key": "rel:blocks:W-001:W-999",
                              "before": False, "after": True}]))]),
            "an invalid template": lambda i, e: (i, e[:1] + [self.edit(
                e[1], lambda o: o["changes"][0]["after"].update(format=9))]
                + e[2:]),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.mutate_and_import(mutate, "export_invalid")

    def test_a_gap_that_replays_cleanly_is_still_refused(self):
        """F3: the gap check is the only thing that catches this one.

        A relation added and then removed changes nothing a later export
        shows, and both ends are touched again afterwards, so deleting the
        two events leaves a history that replays without a before mismatch
        and reproduces items.jsonl byte for byte. Only the seq run 1…n says
        two events are missing."""
        sb = Sandbox(self).ready()
        a, b = sb.create(), sb.create()
        edge = {"actor": ACTOR, "kind": "blocks", "from": a, "to": b}
        sb.ok("rel", "add", data=edge)
        sb.ok("rel", "remove", data=edge)
        for item in (a, b):
            sb.ok("item", "update", data={"actor": ACTOR, "id": item,
                                          "set": {"label": "later"}})
        sb.ok("export")
        other = twin(self, sb)
        path = export_dir(other) / "events.jsonl"
        lines = path.read_text("utf-8").splitlines(True)
        self.assertEqual([json.loads(x)["command"] for x in lines[4:6]],
                         ["rel add", "rel remove"])
        path.write_text("".join(lines[:4] + lines[6:]), "utf-8")
        r = other.run("import", data={"state_root": other.state_root})
        self.assertEqual((r.code, r.code_name), (1, "export_invalid"), r)
        self.assertEqual(r.details, {"line": 5, "seq": 7})
        self.assertIn("without a gap", r.env["error"]["message"])

    def test_replay_mismatch_names_the_first_differing_item(self):
        def tamper(items, events):
            items = list(items)
            items[1] = self.edit(items[1],
                                 lambda o: o["fields"].update(label="forged"))
            return items, events
        r = self.mutate_and_import(tamper, "replay_mismatch")
        self.assertEqual(r.details["id"], "W-001")

    def test_a_ceiling_event_seeds_ids_above_the_stored_ones(self):
        sb = populated(self)
        sb.ok("export")
        other = twin(self, sb)
        directory = export_dir(other)
        events = (directory / "events.jsonl").read_text("utf-8").splitlines(True)
        seed = self.edit(events[-1], lambda o: o.update(
            seq=len(events) + 1, command="seed ids", items=[], transition=None,
            note="ids issued before the import", warnings=[],
            changes=[{"key": "ceiling:W", "before": 2, "after": 40}]))
        (directory / "events.jsonl").write_text("".join(events) + seed,
                                                "utf-8")
        other.ok("import", data={"state_root": other.state_root})
        self.assertEqual(other.create(), "W-041")
        self.assertEqual(other.create("gauge"), "G-2")


if __name__ == "__main__":
    unittest.main()
