"""TASK-237 deliverable 3a — nothing needs `BOARD.md`; the file stays on disk.

`TASK-237-spec.md § Amendment 2026-09-14 (3) § Deliverable 3a`:

1. **Every read surface answers from its store.** With `BOARD.md` deleted,
   `perry-task list` / `asks`, `perry-state --json` carry the same asks, risks
   and intake rows they carry with it. Measured on `d358a2cf` before this
   change: `asks --all` 0 of 33, `list` risks 0, `drift.drift` 97,
   `perry-state` risks 0 / `none`. This is also TASK-268 (`top_risks` built
   from `BOARD.md`).
2. **Every `perry-task` write succeeds without `BOARD.md`**: the store record,
   the journal line and the event land, and no file is created. While the
   file exists it is still re-rendered.

**No expectation here comes from a `BOARD.md`.** Expectations are the store
records this module writes (or, for the live case, reads as JSONL) and the
values a command was given. The file appears in two roles only: ABSENT, and
FORGED — a `BOARD.md` whose registers carry rows no store holds. A read path
that consults the file shows a forged row or loses a stored one, and a test
below goes red.

Run: python3 tests/parallel test_board_less_reads_and_writes
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

import inproc

ROOT = Path(__file__).resolve().parent.parent
STATE_TOOL = ROOT / "bin" / "perry-state"
LINT_TOOL = ROOT / "bin" / "perry-lint"

# ── the fixture ────────────────────────────────────────────────────────────


def task(tid, order, group="P1", status="not_started", priority="P1", **kw):
    rec = {"id": tid, "title": f"title of {tid}", "summary": "",
           "owner": "Coding Agent", "status": status, "priority": priority,
           "track": "main", "stage": "", "stage_since": "", "arrived": "",
           "verification": "V3", "evidence": "", "next_action": f"next for {tid}",
           "depends_on": [], "design_refs": [], "commitment": "", "parent": "",
           "group": group, "role": "", "created": "2026-09-01", "order": order}
    rec.update(kw)
    return rec


TASKS = [
    # Waits on an ANSWERED ask, so it is startable only if the ask register
    # is read.
    task("TASK-001", 0, group="P0 (must finish this period)", priority="P0",
         depends_on=["USER-002"]),
    task("TASK-002", 0, status="in_progress"),
    # Waits on an OPEN ask.
    task("TASK-003", 1, status="blocked", depends_on=["USER-001"]),
    task("TASK-004", None, group="P2", priority="P2", status="done"),
    # The subject of the write cases: open, not started, nothing waits on it.
    task("TASK-005", 2),
]
ASKS = [
    {"id": "USER-001", "needed": "which threshold?", "blocks": "TASK-001",
     "asked": "2026-09-01", "status": "open", "answered": False, "order": 0},
    {"id": "USER-002", "needed": "keep the file?", "blocks": "TASK-001",
     "asked": "2026-08-20", "status": "answered 2026-08-21: no",
     "answered": True, "order": 1},
]
RISKS = [
    {"id": "RX-001", "risk": "the store is wrong on a row", "opened": "2026-09-01",
     "cleared": "", "status": "open", "order": 0},
    # The `Status` cell names no date, so `cleared_on` can only come from the
    # record's `cleared` field — the source the contract names.
    {"id": "RX-002", "risk": "a reader parses the file", "opened": "2026-08-01",
     "cleared": "2026-09-10", "status": "cleared — read the store",
     "order": 1},
]
INTAKE = [
    {"order": 0, "arrived": "2026-09-10", "request": "print the board",
     "outcome": "", "discharged": False},
    {"order": 1, "arrived": "2026-09-09", "request": "drop the file",
     "outcome": "dropped 2026-09-11 — out of scope", "discharged": True},
]
CONFIG = [
    {"kind": "setting", "key": "state_root", "label": "State root",
     "value": "perry", "order": 0},
    {"kind": "track", "track": "main", "mode": "project", "spine": "phase/",
     "stages": "", "wip": "", "sla": "", "cycle": "", "default_rung": "V3",
     "order": 0},
    {"kind": "track", "track": "intake", "mode": "queue", "spine": "standing",
     "stages": "new→triaged→in_progress→resolved", "wip": "6", "sla": "5d",
     "cycle": "weekly", "default_rung": "V3", "order": 1},
]

#: A `BOARD.md` whose three registers hold rows NO store holds, and none of the
#: rows the stores do. Any read path that consults it shows `USER-777`,
#: `RX-777` or `forged request`, or loses a stored row.
FORGED_BOARD = """# Board — forged

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-777 | forged task | nobody | in_progress | forged | — |

## Intake

| Arrived | Request | Outcome |
|---|---|---|
| 2026-01-01 | forged request | |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|
| USER-777 | forged question | TASK-001 | 3d | open |

## Top risks

| ID | Risk | Opened | Status |
|---|---|---|---|
| RX-777 | forged risk | 2026-01-01 | open |
"""


def jsonl(records) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").split("\n")
            if l.strip()]


class Project:
    """A configured project holding the four stores and an event log."""

    def __init__(self, board: str | None = None):
        self.tmp = tempfile.mkdtemp(prefix="t237d3a-")
        self.root = Path(self.tmp)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.jsonl").write_text(jsonl(CONFIG),
                                                          encoding="utf-8")
        events = [{"ts": "2026-09-01T10:00:00+08:00", "event": "add",
                   "id": t["id"], "title": t["title"], "track": "main",
                   "actor": "agent", "from": None, "to": "not_started"}
                  for t in TASKS]
        (self.root / ".perry" / "events.jsonl").write_text(jsonl(events),
                                                          encoding="utf-8")
        self.state = self.root / "perry"
        (self.state / "evidence").mkdir(parents=True)
        (self.state / "evidence" / "proof.md").write_text("# proof\n",
                                                          encoding="utf-8")
        (self.state / "design").mkdir()
        (self.state / "design" / "DESIGN-001-probe.md").write_text(
            "# DESIGN-001 — probe\n\n> Status: locked\n", encoding="utf-8")
        for name, recs in (("tasks", TASKS), ("asks", ASKS), ("risks", RISKS),
                           ("intake", INTAKE)):
            (self.state / f"{name}.jsonl").write_text(jsonl(recs),
                                                      encoding="utf-8")
        if board is not None:
            (self.state / "BOARD.md").write_text(board, encoding="utf-8")

    @property
    def board(self) -> Path:
        return self.state / "BOARD.md"

    def task(self, argv: list[str]):
        return inproc.run("perry-task", argv + ["--root", str(self.root)])

    def task_json(self, argv: list[str]) -> dict:
        out = self.task(argv + ["--json"])
        if out.returncode != 0:
            raise AssertionError(f"perry-task {argv} exited {out.returncode}: "
                                 f"{out.stdout[-400:]}{out.stderr[-400:]}")
        return json.loads(out.stdout)

    def state_json(self) -> dict:
        out = subprocess.run([str(STATE_TOOL), "--json", "--root", str(self.root)],
                             capture_output=True, text=True, cwd=self.tmp)
        if out.returncode != 0:
            raise AssertionError(out.stderr[-600:])
        return json.loads(out.stdout)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ── item 1: reads ──────────────────────────────────────────────────────────


class RegistersFromTheStores:
    """The register-shaped half of every read payload, asserted from the stores.

    Mixed into two cases: `BOARD.md` absent, and `BOARD.md` forged. Both must
    give the same answers, because neither may be read.
    """

    board_text: str | None = None

    def setUp(self):
        self.p = Project(board=self.board_text)
        self.addCleanup(self.p.close)

    def test_asks_all_is_every_stored_ask(self):
        got = self.p.task_json(["asks", "--all"])
        self.assertEqual([a["id"] for a in got["asks"]], [a["id"] for a in ASKS])
        self.assertEqual(got["count"], len(ASKS))
        self.assertEqual({a["id"]: a["answered"] for a in got["asks"]},
                         {a["id"]: a["answered"] for a in ASKS})
        for a, want in zip(got["asks"], ASKS):
            with self.subTest(ask=want["id"]):
                self.assertEqual((a["needed"], a["blocks"], a["asked"], a["status"]),
                                 (want["needed"], want["blocks"], want["asked"],
                                  want["status"]))

    def test_asks_default_is_the_open_stored_asks(self):
        got = self.p.task_json(["asks"])
        self.assertEqual([a["id"] for a in got["asks"]],
                         [a["id"] for a in ASKS if not a["answered"]])
        self.assertEqual(got["answered"], sum(1 for a in ASKS if a["answered"]))

    def test_list_carries_the_stored_risks_asks_and_intake(self):
        got = self.p.task_json(["list"])
        open_risks = [r["id"] for r in RISKS if not r["cleared"]]
        self.assertEqual([r["id"] for r in got["risks"]["items"]], open_risks)
        self.assertEqual(got["risks"]["open"], len(open_risks))
        self.assertEqual(got["risks"]["cleared"], len(RISKS) - len(open_risks))
        self.assertEqual(got["risks"]["source"], "table")
        cleared = next(r for r in RISKS if r["cleared"])
        self.assertNotIn(cleared["id"], [r["id"] for r in got["risks"]["items"]])
        self.assertEqual([a["id"] for a in got["asks"]["items"]],
                         [a["id"] for a in ASKS if not a["answered"]])
        self.assertEqual([(r["n"], r["request"], r["outcome"], r["discharged"])
                          for r in got["intake"]["rows"]],
                         [(i + 1, r["request"], r["outcome"], r["discharged"])
                          for i, r in enumerate(INTAKE)])
        self.assertEqual(got["intake"]["undischarged"],
                         sum(1 for r in INTAKE if not r["discharged"]))

    def test_an_answered_stored_ask_satisfies_its_edge(self):
        got = self.p.task_json(["list"])
        tasks = {t["id"]: t for t in got["tasks"]}
        answered = next(a for a in ASKS if a["answered"])
        waiting = next(a for a in ASKS if not a["answered"])
        edge = tasks["TASK-001"]["depends_on_resolved"][0]
        self.assertEqual((edge["id"], edge["kind"], edge["satisfied"]),
                         (answered["id"], "ask", True))
        self.assertEqual(edge["title"], answered["needed"])
        self.assertTrue(tasks["TASK-001"]["startable"])
        self.assertEqual(tasks["TASK-003"]["blocked_by"], [waiting["id"]])
        unknown = {d for row in got["conformance"]["depends_on_unknown"]
                   for d in row["unknown"]}
        self.assertFalse(unknown & {a["id"] for a in ASKS})

    def test_perry_state_carries_the_stored_registers(self):
        got = self.p.state_json()
        open_risks = [r["id"] for r in RISKS if not r["cleared"]]
        self.assertEqual(got["risks"]["count"], len(open_risks))
        self.assertEqual(got["risks"]["source"], "table")
        self.assertEqual([r["id"] for r in got["risks"]["items"]], open_risks)
        self.assertEqual([r["id"] for r in got["risks"]["cleared_items"]],
                         [r["id"] for r in RISKS if r["cleared"]])
        self.assertEqual(got["risks"]["cleared_items"][0]["cleared_on"],
                         next(r["cleared"] for r in RISKS if r["cleared"]))
        self.assertEqual(got["user_input_queue"]["count"],
                         sum(1 for a in ASKS if not a["answered"]))
        self.assertEqual(got["intake"]["rows"], len(INTAKE))
        self.assertEqual(got["intake"]["undischarged"],
                         sum(1 for r in INTAKE if not r["discharged"]))


class TestTheRegistersWithNoBoard(RegistersFromTheStores, unittest.TestCase):
    board_text = None

    # Drift is asserted only here. With a file on disk it is DOCUMENTED to be
    # about that file (`schema/task-list-contract.md § drift`), so a forged
    # board is supposed to show drift; with no file there is nothing to drift.
    def test_drift_names_no_stored_open_row(self):
        open_ids = {t["id"] for t in TASKS if t["status"] not in ("done", "dropped")}
        got = self.p.task_json(["list"])
        self.assertTrue(got["drift"]["checked"])
        self.assertFalse(set(got["drift"]["orphaned"] or []) & open_ids,
                         got["drift"])
        state = self.p.state_json()
        self.assertFalse(set(state["board"]["drift"]["orphaned"] or []) & open_ids,
                         state["board"]["drift"])

    def test_the_fixture_carries_every_shape(self):
        """Anti-vacuity: each read case above needs one of these shapes."""
        self.assertFalse(self.p.board.exists())
        self.assertTrue(any(a["answered"] for a in ASKS))
        self.assertTrue(any(not a["answered"] for a in ASKS))
        self.assertTrue(any(r["cleared"] for r in RISKS))
        self.assertTrue(any(not r["cleared"] for r in RISKS))
        self.assertTrue(any(r["discharged"] for r in INTAKE))
        self.assertTrue(any(not r["discharged"] for r in INTAKE))
        answered = {a["id"] for a in ASKS if a["answered"]}
        self.assertTrue(any(set(t["depends_on"]) & answered for t in TASKS))


class TestTheRegistersWithAForgedBoard(RegistersFromTheStores, unittest.TestCase):
    board_text = FORGED_BOARD

    def test_no_forged_row_reaches_a_payload(self):
        self.assertTrue(self.p.board.exists())
        on_disk = self.p.board.read_text(encoding="utf-8")
        for forged in ("USER-777", "RX-777", "forged request"):
            self.assertIn(forged, on_disk, "the forged board lost a forged row")
        blobs = [json.dumps(self.p.task_json(["asks", "--all"])),
                 json.dumps({k: v for k, v in self.p.task_json(["list"]).items()
                             if k in ("risks", "asks", "intake")}),
                 json.dumps({k: v for k, v in self.p.state_json().items()
                             if k in ("risks", "user_input_queue")})]
        for blob in blobs:
            for forged in ("USER-777", "RX-777", "forged request"):
                self.assertNotIn(forged, blob)


class TestThisProjectsStoresWithNoBoard(unittest.TestCase):
    """This checkout's stores, config and event log, with no `BOARD.md`."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="t237d3a-live-")
        root = Path(cls.tmp)
        (root / ".perry").mkdir()
        for name in ("config.jsonl", "events.jsonl"):
            shutil.copy2(ROOT / ".perry" / name, root / ".perry" / name)
        state_root = next((r["value"] for r in read_jsonl(ROOT / ".perry" / "config.jsonl")
                           if r.get("key") == "state_root"), "")
        cls.state = root / state_root
        cls.state.mkdir(parents=True, exist_ok=True)
        for name in ("tasks", "asks", "risks", "intake", "linkage", "okr"):
            src = ROOT / state_root / f"{name}.jsonl"
            if src.exists():
                shutil.copy2(src, cls.state / f"{name}.jsonl")
        cls.root = root
        run = lambda argv: json.loads(inproc.run(  # noqa: E731
            "perry-task", argv + ["--root", str(root), "--json"]).stdout)
        cls.asks = run(["asks", "--all"])
        cls.listed = run(["list", "--limit", "0"])
        cls.stored_asks = read_jsonl(cls.state / "asks.jsonl")
        cls.stored_risks = read_jsonl(cls.state / "risks.jsonl")
        cls.stored_tasks = read_jsonl(cls.state / "tasks.jsonl")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_every_stored_ask_is_listed(self):
        self.assertFalse((self.state / "BOARD.md").exists())
        self.assertGreaterEqual(len(self.stored_asks), 1, "no ask store to check")
        self.assertEqual([a["id"] for a in self.asks["asks"]],
                         [a["id"] for a in sorted(self.stored_asks,
                                                  key=lambda a: a["order"])])

    def test_every_open_stored_risk_is_listed(self):
        open_ids = [r["id"] for r in sorted(self.stored_risks,
                                             key=lambda r: r["order"])
                    if not r.get("cleared")]
        self.assertGreaterEqual(len(self.stored_risks), 1, "no risk store to check")
        self.assertEqual([r["id"] for r in self.listed["risks"]["items"]], open_ids)
        self.assertEqual(self.listed["risks"]["cleared"],
                         len(self.stored_risks) - len(open_ids))

    def test_no_stored_open_row_is_drift(self):
        open_ids = {t["id"] for t in self.stored_tasks
                    if t.get("status") not in ("done", "dropped")}
        self.assertGreaterEqual(len(open_ids), 1)
        self.assertFalse(set(self.listed["drift"]["orphaned"] or []) & open_ids)

    def test_every_edge_to_a_stored_ask_resolves_as_an_ask(self):
        ask_ids = {a["id"] for a in self.stored_asks}
        edges = [e for t in self.listed["tasks"] for e in t["depends_on_resolved"]
                 if e["id"] in ask_ids]
        self.assertGreaterEqual(len(edges), 1, "no task waits on a stored ask")
        self.assertEqual({e["kind"] for e in edges}, {"ask"})


# ── item 2: writes ─────────────────────────────────────────────────────────

PROOF = "perry/evidence/proof.md"

#: `(name, prerequisites, argv, store the write lands in, check)`. `check`
#: reads the store AFTER the write and returns what must be true of it, built
#: from the values the command was given — never from a board.
WRITES = [
    ("add", [], ["add", "--title", "probe row", "--priority", "P2",
                 "--deliverable", "a probe", "--verification", "the test",
                 "--rung", "V2", "--summary",
                 "Proves a write lands in tasks.jsonl when no board file exists "
                 "on disk.", "--next", "nothing"],
     "tasks", lambda s: any(t["title"] == "probe row" for t in s)),
    ("start", [], ["start", "TASK-005", "--next", "go"], "tasks",
     lambda s: _t(s, "TASK-005")["status"] == "in_progress"),
    ("track", [], ["track", "TASK-005", "--track", "intake", "--stage", "new",
                   "--reason", "probe"], "tasks",
     lambda s: _t(s, "TASK-005")["track"] == "intake"),
    ("stage", [["track", "TASK-005", "--track", "intake", "--stage", "new",
                "--reason", "probe"]],
     ["stage", "TASK-005", "--stage", "triaged"], "tasks",
     lambda s: _t(s, "TASK-005")["stage"] == "triaged"),
    ("ask", [], ["ask", "--needed", "probe question?", "--blocks", "TASK-005"],
     "asks", lambda s: any(a["needed"] == "probe question?" for a in s)),
    ("answer", [], ["answer", "USER-001", "--answer", "seven"], "asks",
     lambda s: "seven" in _t(s, "USER-001")["status"]),
    ("next", [], ["next", "TASK-005", "--next", "probe next"], "tasks",
     lambda s: _t(s, "TASK-005")["next_action"] == "probe next"),
    ("risk-add", [], ["risk-add", "--title", "probe risk"], "risks",
     lambda s: any(r["risk"] == "probe risk" for r in s)),
    ("risk-clear", [], ["risk-clear", "RX-001", "--reason", "probe"], "risks",
     lambda s: _t(s, "RX-001")["cleared"] != ""),
    ("done", [], ["done", "TASK-002", "--evidence", PROOF, "--rung", "V3"],
     "tasks", lambda s: _t(s, "TASK-002")["status"] == "done"),
    ("drop", [], ["drop", "TASK-005", "--reason", "probe"], "tasks",
     lambda s: _t(s, "TASK-005")["status"] == "dropped"),
    ("purge", [], ["purge", "TASK-004", "--reason", "probe"], "tasks",
     lambda s: not any(t["id"] == "TASK-004" for t in s)),
    ("intake", [], ["intake", "--title", "probe request"], "intake",
     lambda s: any(r["request"] == "probe request" for r in s)),
    ("route", [], ["route", "1", "--track", "intake", "--stage", "new"],
     "tasks", lambda s: any(t["title"] == "print the board" for t in s)),
    ("resolve-intake", [], ["resolve-intake", "1", "--outcome", "dropped",
                            "--reason", "probe"], "intake",
     lambda s: s[0]["outcome"].startswith("dropped")),
    ("intake-sweep", [], ["intake-sweep"], "intake",
     lambda s: [r["request"] for r in s] == ["print the board"]),
    ("retitle", [], ["retitle", "TASK-005", "--title", "probe title"], "tasks",
     lambda s: _t(s, "TASK-005")["title"] == "probe title"),
    ("summary", [], ["summary", "TASK-005", "--summary", "probe summary"],
     "tasks", lambda s: _t(s, "TASK-005")["summary"] == "probe summary"),
    ("rung", [], ["rung", "TASK-005", "--rung", "V2"], "tasks",
     lambda s: _t(s, "TASK-005")["verification"].startswith("V2")),
    ("evidence", [], ["evidence", "TASK-005", "--evidence", PROOF], "tasks",
     lambda s: PROOF in _t(s, "TASK-005")["evidence"]),
    ("prioritize", [], ["prioritize", "TASK-005", "--priority", "P2",
                        "--reason", "probe"], "tasks",
     lambda s: _t(s, "TASK-005")["priority"] == "P2"),
    ("status", [], ["status", "TASK-005", "--status", "blocked", "--on",
                    "TASK-002", "--reason", "probe", "--next", "wait"], "tasks",
     lambda s: _t(s, "TASK-005")["status"] == "blocked"),
    ("depends", [], ["depends", "TASK-005", "--on", "TASK-002"], "tasks",
     lambda s: _t(s, "TASK-005")["depends_on"] == ["TASK-002"]),
    ("design-link", [], ["design-link", "TASK-005", "--design", "DESIGN-001"],
     "tasks", lambda s: _t(s, "TASK-005")["design_refs"] == ["DESIGN-001"]),
]

#: Every `perry-task` write `--describe` declares, and what covers it here.
#: `risk-migrate` converts BULLETS in the file into the table; a project with a
#: risks store has no bullets to convert, and it refuses in both states.
NOT_IN_WRITES = {"cadence-add": "refused without the file — see below",
                 "cadence-done": "refused without the file — see below",
                 "risk-migrate": "nothing to migrate on a store-backed register"}

TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?")


def _t(records, rid):
    return next(r for r in records if r.get("id") == rid)


def journal(p: Project) -> Path:
    return p.state / "journal" / f"{date.today():%Y-%m}" / f"{date.today():%Y-%m-%d}.md"


def outcome(p: Project, prereqs, argv, store):
    """Run a write; return what landed, with clocks and the root taken out."""
    for pre in prereqs:
        out = p.task(pre)
        if out.returncode != 0:
            raise AssertionError(f"prerequisite {pre} exited {out.returncode}: "
                                 f"{out.stderr[-400:]}")
    events_before = (p.root / ".perry" / "events.jsonl").read_text(encoding="utf-8")
    journal_before = journal(p).read_text(encoding="utf-8") if journal(p).exists() else ""
    out = p.task(argv)
    norm = lambda s: TS.sub("<TS>", s.replace(str(p.root), "<ROOT>"))  # noqa: E731
    return {
        "exit": out.returncode, "stderr": out.stderr, "stdout": out.stdout,
        "store": read_jsonl(p.state / f"{store}.jsonl"),
        "stores": {n: norm((p.state / f"{n}.jsonl").read_text(encoding="utf-8"))
                   if (p.state / f"{n}.jsonl").exists() else None
                   for n in ("tasks", "asks", "risks", "intake", "linkage")},
        "events": norm((p.root / ".perry" / "events.jsonl")
                       .read_text(encoding="utf-8")[len(events_before):]),
        "journal": norm((journal(p).read_text(encoding="utf-8")
                         if journal(p).exists() else "")[len(journal_before):]),
    }


class TestEveryWriteLandsWithNoBoard(unittest.TestCase):

    def test_the_write_table_covers_every_declared_write(self):
        described = json.loads(inproc.run("perry-task", ["--describe", "--json"]).stdout)
        writes = {s["name"] for s in described["subcommands"] if s.get("writes")}
        covered = {w[0] for w in WRITES} | set(NOT_IN_WRITES)
        self.assertEqual(writes, covered)

    def test_each_write_lands_its_record_event_and_journal_line(self):
        for name, prereqs, argv, store, check in WRITES:
            with self.subTest(write=name):
                p = Project(board=None)
                self.addCleanup(p.close)
                got = outcome(p, prereqs, argv, store)
                self.assertEqual(got["exit"], 0, got["stderr"][-600:])
                self.assertTrue(check(got["store"]), f"{store}.jsonl after {name}")
                self.assertIn(f'"event": "{name}"', got["events"])
                self.assertTrue(got["journal"].strip(), "no journal line")
                self.assertFalse(p.board.exists(), "a write created BOARD.md")
                self.assertNotIn("BOARD.md", got["stdout"])

    def test_a_write_is_the_same_with_and_without_the_file(self):
        """Same store, event and journal line in both states; the file is re-rendered."""
        for name, prereqs, argv, store, _check in WRITES:
            with self.subTest(write=name):
                absent, present = Project(board=None), Project(board=None)
                self.addCleanup(absent.close)
                self.addCleanup(present.close)
                # The present state's file is the board the stores render to —
                # not a copy of any `BOARD.md` — so the two states start equal.
                render = inproc.run("perry-tasks", ["board", "--root", str(present.root)])
                self.assertEqual(render.returncode, 0, render.stderr)
                present.board.write_text(render.stdout, encoding="utf-8")
                before = present.board.read_text(encoding="utf-8")
                a = outcome(absent, prereqs, argv, store)
                b = outcome(present, prereqs, argv, store)
                self.assertEqual((a["exit"], b["exit"]), (0, 0),
                                 a["stderr"][-300:] + b["stderr"][-300:])
                self.assertEqual(a["stores"], b["stores"])
                self.assertEqual(a["events"], b["events"])
                self.assertEqual(a["journal"], b["journal"])
                self.assertIn("BOARD.md", b["stdout"])
                if name not in ("summary", "design-link"):
                    # The two writes to a field the board has no column for.
                    self.assertNotEqual(present.board.read_text(encoding="utf-8"),
                                        before, "the file was not re-rendered")

    def test_a_cadence_write_refuses_and_writes_nothing(self):
        for argv in (["cadence-add", "--title", "weekly close", "--frequency", "weekly"],
                     ["cadence-done", "CAD-001", "--evidence", PROOF]):
            with self.subTest(write=argv[0]):
                p = Project(board=None)
                self.addCleanup(p.close)
                events = (p.root / ".perry" / "events.jsonl").read_bytes()
                out = p.task(argv)
                self.assertEqual(out.returncode, 1)
                self.assertIn("`## Cadence` has no store", out.stderr)
                self.assertEqual((p.root / ".perry" / "events.jsonl").read_bytes(),
                                 events)
                self.assertFalse(journal(p).exists())
                self.assertFalse(p.board.exists())


class TestLintOnABoardlessProject(unittest.TestCase):

    @staticmethod
    def lint(p: Project) -> dict:
        out = subprocess.run([str(LINT_TOOL), "--json", "--root", str(p.root)],
                             capture_output=True, text=True, cwd=p.tmp)
        return json.loads(out.stdout)

    def test_the_errors_are_the_present_errors_plus_the_missing_file(self):
        """Item 3: the same errors as with the file, except `[missing-file]`."""
        absent, present = Project(board=None), Project(board=None)
        self.addCleanup(absent.close)
        self.addCleanup(present.close)
        render = inproc.run("perry-tasks", ["board", "--root", str(present.root)])
        self.assertEqual(render.returncode, 0, render.stderr)
        present.board.write_text(render.stdout, encoding="utf-8")
        errors = lambda got: sorted(  # noqa: E731
            (f["rule"], f["file"], f["message"]) for f in got["findings"]
            if f.get("severity") == "error")
        without, with_file = errors(self.lint(absent)), errors(self.lint(present))
        missing = ("missing-file", "BOARD.md", "required state file not found")
        self.assertNotIn(missing, with_file)
        self.assertIn(missing, without)
        self.assertEqual([e for e in without if e != missing], with_file)

    def test_the_store_counts_are_the_stores_with_no_file(self):
        p = Project(board=None)
        self.addCleanup(p.close)
        got = self.lint(p)
        self.assertEqual(got["ask_store_drift"]["records"], len(ASKS))
        self.assertEqual(got["risk_store_drift"]["records"], len(RISKS))
        self.assertEqual(got["intake_store_drift"]["records"], len(INTAKE))


if __name__ == "__main__":
    unittest.main()
