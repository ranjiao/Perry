"""`perry-task prioritize` — the writer triage's central act did not have.

`perry-task` shipped 22 subcommands and none of them could change a row's
priority. `add` sets it once; `route` — the only other thing that writes a
priority cell — takes an *intake row number*, mints a *new* id, and refuses on
any track in `project` mode. So re-prioritising, which is what `triage`,
`monday-plan`, `friday-review` and `mid-phase-review` all end in, could only be
done by hand-editing `BOARD.md`.

A hand edit lands with **no event**, so `perry-state § reconcile_drift` reports
it as unrecorded drift — the exact failure `DESIGN-004` was written against —
and `priority` is a published field of `perry-task/list` that aiMark's Projects
view sorts on. A front-end could display a priority no caller could change.

Found by trying to execute a triage verdict rather than by reading the code.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import task_actor

COVERS = ("bin/perry-task", "perry/tasks.jsonl")

import re

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from kernel_work_support import ACTOR, ready, task
from task_writer_support import Project as LegacyProject
from pathlib import Path


PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import tables as T  # noqa: E402

import config_store  # noqa: E402

TOOL = PERRY_HOME / "bin" / "perry-task"
HEADER = ["ID", "Title", "Owner", "Status", "Next action", "Evidence",
          "Verification"]
SEP = "|" + "---|" * len(HEADER)


def row(tid, title="t", owner="o", status="not_started", nxt="do it",
        ev="—", ver="V2"):
    return T.render_row([tid, title, owner, status, nxt, ev, ver])


def board(p0=(), p1=(), p2=(), extra_sections=""):
    return "\n".join([
        "# Board", "",
        "## P0", "", T.render_row(HEADER), SEP, *p0, "",
        "## P1", "", T.render_row(HEADER), SEP, *p1, "",
        "## P2", "", T.render_row(HEADER), SEP, *p2, "",
        extra_sections,
        "## Cadence", "",
        "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
        "|---|---|---|---|---|---|", "",
        "## User Input Queue", "",
        "| ID | Needed from user | Blocks | Asked | Status |",
        "|---|---|---|---|---|", "",
        "## Top risks", "",
        "| ID | Risk | Opened | Severity | Cleared |",
        "|---|---|---|---|---|", "",
    ])


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "perry").mkdir()
        (self.root / ".perry").mkdir()
        config_store.write_config(self.root, {"State root": "perry/"})
        self.addCleanup(self.tmp.cleanup)

    def write(self, text):
        (self.root / "perry" / "BOARD.md").write_text(text, encoding="utf-8")
        seeded = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-tasks"), "write",
             "--from-board", "--root", str(self.root)],
            capture_output=True, text=True)
        if seeded.returncode:
            raise AssertionError(seeded.stdout + seeded.stderr)

    def read(self):
        """The board `perry-tasks board` prints (TASK-262 round 4a). The held
        `BOARD.md` `write()` puts down is the import input and no write
        re-renders it any more."""
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        out = subprocess.run([sys.executable, str(PERRY_HOME / "bin" / "perry-tasks"),
                              "board", "--root", str(self.root)],
                             capture_output=True, text=True, env=env)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return out.stdout

    def run_tool(self, *argv):
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        return subprocess.run(task_actor.command([sys.executable, str(TOOL), *argv,
                               "--root", str(self.root)], 'test_prioritize'),
                              capture_output=True, text=True, env=env)

    def payload(self):
        out = self.run_tool("list", "--all", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def task(self, tid):
        return [t for t in self.payload()["tasks"] if t["id"] == tid][0]

    def section_of(self, tid):
        """Which `## …` heading the row currently sits under."""
        head = None
        for line in self.read().split("\n"):
            if line.startswith("## "):
                head = line[3:].strip()
            elif line.strip().startswith("|") and T.split_row(line)[0] == tid:
                return head
        return None


class TestTheEventIsPartOfTheDeclaredSet(unittest.TestCase):
    def test_prioritize_is_a_task_event_not_a_section_event(self):
        """`TASK_EVENTS` and `SECTION_EVENTS` are asserted to be a partition of
        `COMMANDS`. A new subcommand that lands in neither drops out of the
        payload silently; one that lands in both leaks into it."""
        spec = importlib.util.spec_from_loader(
            "perry_task",
            importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertIn("prioritize", mod.COMMANDS)
        self.assertIn("prioritize", mod.TASK_EVENTS)
        self.assertNotIn("prioritize", mod.SECTION_EVENTS)

    def test_it_is_documented_in_the_usage_banner(self):
        """A subcommand a user cannot discover is one they will hand-edit
        around, which is the failure this whole module is about."""
        # Generated from `PT.SURFACE` since DESIGN-016 C2: declared is
        # discoverable, and the usage block is where that shows.
        import inproc
        self.assertIn("prioritize",
                      {s["name"] for s
                       in inproc.load("perry-task").SURFACE["subcommands"]})


class TestEveryEventSaysWhatItsPairMeans(unittest.TestCase):
    """`field` on a timeline entry, so a consumer needs no hardcoded set.

    aiMark had to write `SECTION_MOVE_EVENTS = new Set(["prioritize"])` to keep
    `prioritize` from rendering `P1 → P0` with the status palette. That set is
    wrong the day Perry adds a second event overloading `from`/`to`, and
    **nothing in the payload would say so** — one side knowing and the other
    guessing, which is the defect these contracts exist against.

    The ask was `"status"` on every existing event and `"section"` on
    `prioritize`. That default is false — `retitle`'s pair is a title, `next`'s
    is a next action — and shipping a wrong word in the field whose job is to
    stop a consumer guessing would be the same defect inside its own fix. So it
    is a full map, and this test is what keeps it full.
    """

    def setUp(self):
        spec = importlib.util.spec_from_loader(
            "perry_task",
            importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_the_map_covers_exactly_the_declared_task_events(self):
        """Not "covers them" — **exactly**. A missing key ships `""` to a
        consumer; a stale key promises something that cannot happen. `depends`
        was already missing when this was written, found by running the payload
        rather than by reading the map."""
        self.assertEqual(set(self.mod.EVENT_FIELD), set(self.mod.TASK_EVENTS))

    def test_no_event_claims_a_pair_it_does_not_carry(self):
        """The values are cell names a reader can act on, not a vocabulary of
        their own. Each must be a key of the task payload, or `status`/`section`
        which name a concept rather than a cell."""
        payload_keys = set(self.mod.LIST_TASK_KEYS) if hasattr(
            self.mod, "LIST_TASK_KEYS") else None
        allowed = {"status", "section", "stage", "track", "title", "summary",
                   "next_action", "verification", "evidence", "depends_on",
                   # TASK-139. A STORE field rather than a board cell — there
                   # is no `Design` column and there must not be one, because
                   # the close path clears cells and the whole point of the
                   # edge is that closing must not destroy it.
                   "design_refs"}
        self.assertLessEqual(set(self.mod.EVENT_FIELD.values()), allowed)

    def test_a_section_move_is_not_reported_as_a_status_move(self):
        self.assertEqual(self.mod.EVENT_FIELD["prioritize"], "section")
        self.assertEqual(self.mod.EVENT_FIELD["status"], "status")

    #: The task store the two prose tests below resolve against. It used to be
    #: `load_task_records(PERRY_HOME / "perry")` — this repository's live store
    #: (TASK-152) — which made a test about PROSE PARSING depend on which id
    #: families Perry's own board happens to carry. `OPS-007` is here so the
    #: record half of `known` is exercised by something the hard-coded
    #: citation set does not already cover.
    FIXTURE_TASKS = (
        {"id": "TASK-001", "title": "a row this store carries",
         "status": "open"},
        {"id": "OPS-007", "title": "a second id family, declared here",
         "status": "open"},
    )

    def prose_ctx(self) -> dict:
        """`ctx` for the prose warning, over a store this test wrote.

        Loaded through the real `load_task_records`, so the reader under test
        is the shipped one; only the records are the test's own.

        `project_root` is the same throwaway directory and carries no document
        at all, which is the case that matters here: a project that declares no
        id family of its own must behave exactly as it did before
        `declared_id_families` existed (TASK-158). A project that DOES declare
        one is `tests/test_id_families.py`.
        """
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        (root / "tasks.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in self.FIXTURE_TASKS),
            encoding="utf-8")
        return {"task_records": self.mod.load_task_records(root),
                "project_root": root}

    def test_an_id_shaped_word_in_prose_is_warned_about(self):
        """`ROUND-2` is English with a hyphen and an identifier to every id
        reader here.

        **Caused three times in one session**, each time fixed in the prose and
        each time recurring: `THE ROUND-2 DEFECT`, then `ALL FIVE ROUND-3
        FINDINGS`. `perry-diagnose` reports it as `LOAD-02` dangling and the
        repo's own gate goes red on a board the tool itself wrote.

        The guard is at the WRITE site because that is where the person who
        knows what they meant still is.

        The half that must not be lost is in its neighbour below: the warning
        is **advisory**, and a legitimate citation must come back clean.
        """
        fn = self.mod.idish_tokens_that_resolve_nowhere
        ctx = self.prose_ctx()
        self.assertEqual(fn("the ROUND-2 defect", ctx), ["ROUND-2"],
                         "an id-shaped word naming no declared family stopped "
                         "being warned about")
        self.assertEqual(fn("ALL FIVE ROUND-3 FINDINGS", ctx), ["ROUND-3"])
        self.assertEqual(fn("round 2, plainly", ctx), [],
                         "English without an id shape is not a citation")

    def test_a_citation_of_a_family_that_resolves_is_not_warned_about(self):
        """The other half, and the fragile one — a *silent* expectation.

        `[]` pins nothing about the project, which is why the sweep in
        `tests/live_state_expectations.py` never flagged this line while it
        sat inside the test above reading the live store: it was one id family
        leaving Perry's board away from failing, and nothing said so.
        Advisory, never a refusal — `ADR-006` and `USER-014` are legitimate
        citations of ids this board does not carry, and refusing them would
        make the tool unable to cite a decision.

        Both routes into `known` are exercised: the citation families
        `perry-task` declares in its own source, and the prefixes read out of
        whatever task store it was handed — here, the one above.
        """
        fn = self.mod.idish_tokens_that_resolve_nowhere
        ctx = self.prose_ctx()
        self.assertEqual(fn("see ADR-006 and USER-014", ctx), [],
                         "a declared citation family was warned about — the "
                         "advisory has started refusing legitimate prose")
        self.assertEqual(fn("blocked on OPS-3, per TASK-001", ctx), [],
                         "a prefix the handed-in store carries was warned "
                         "about")


class TestNativePriorityChange(unittest.TestCase):
    def test_priority_changes_alone_without_moving_state_relations_or_attachments(self):
        sb = ready(self)
        parent, tid = task(sb), task(sb, priority="P2")
        sb.ok("rel add", data={"actor": ACTOR, "kind": "parent", "from": parent, "to": tid})
        sb.ok("attach add", data={"actor": ACTOR, "id": tid, "ref": "evidence/spec.md"})
        before = sb.get(tid)
        sb.ok("item update", data={"actor": ACTOR, "id": tid,
            "set": {"priority": "P0"}, "expect": {tid: before["seq"]}})
        after = sb.get(tid)
        self.assertEqual(after["fields"]["priority"], "P0")
        self.assertEqual(after["state"], before["state"])
        self.assertEqual(after["relations"], before["relations"])
        self.assertEqual(after["attachments"], before["attachments"])
        self.assertEqual({k: v for k, v in after["fields"].items() if k != "priority"},
                         {k: v for k, v in before["fields"].items() if k != "priority"})
        self.assertEqual(sb.events()[-1]["changes"],
                         [{"key": "field:priority", "before": "P2", "after": "P0"}])

    def test_invalid_priority_and_stale_write_do_not_change_priority(self):
        sb = ready(self)
        tid = task(sb)
        seq = sb.get(tid)["seq"]
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"title": "changed"}})
        before = sb.seq()
        for fields, expect in (({"priority": "P3"}, {}), ({"priority": "P0"}, {tid: seq})):
            out = sb.run("item update", data={"actor": ACTOR, "id": tid, "set": fields, "expect": expect})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)
            self.assertEqual(sb.get(tid)["fields"]["priority"], "P1")

    def test_terminal_priority_is_correctable_without_reopening(self):
        sb = ready(self)
        tid = task(sb)
        sb.move(tid, "done", set={"evidence": "proof.md"})
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"priority": "P2"}})
        self.assertEqual(sb.get(tid)["fields"]["priority"], "P2")
        self.assertEqual(sb.get(tid)["state"], "done")


class TestLegacyPriorityRead(unittest.TestCase):
    def test_store_priority_and_historical_event_field_still_agree(self):
        p = LegacyProject()
        p.seed_task("TASK-001", priority="P0")
        (p.root / ".perry/events.jsonl").write_text(json.dumps({"event": "prioritize",
            "id": "TASK-001", "from": "P1", "to": "P0", "ts": "2026-09-01T00:00:00Z"}) + "\n")
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["tasks"][0]["priority"], "P0")
        code, out = p.run("events", "--limit", "10")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["events"][0]["field"], "section")
        self.assertEqual((out["events"][0]["from"], out["events"][0]["to"]), ("P1", "P0"))

    def test_retired_prioritize_keeps_the_store_and_journal_unchanged(self):
        p = LegacyProject()
        p.seed_task("TASK-001", priority="P1")
        before = {str(f.relative_to(p.root)): f.read_bytes() for f in p.root.rglob("*") if f.is_file()}
        code, out = p.run("prioritize", "TASK-001", "--priority", "P0")
        self.assertEqual(code, 1, out)
        self.assertIn("perry-kernel item update", out["refused"])
        self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                          for f in p.root.rglob("*") if f.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
