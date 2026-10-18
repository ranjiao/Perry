"""`bin/perry-kernel-migrate` — the one-shot importer (DESIGN-023 § 6 row D,
TASK-489).

The importer reads a project's old stores, writes a synthetic kernel export
under a scratch directory, runs `bin/perry-kernel import` into a temporary
store there, and reads the store back through the kernel to check the row's
criteria 1–5. These tests run it on a small fixture project that holds each
case the spec names:

- the decision-13 mapping, and the fields it does not carry, counted;
- a closed task's `next_action` skipped and an open task's kept (§ Decided
  2026-09-29, option A);
- one create event and at most one move per item, timed by the "Dates" rule;
- a purged task id that only `.perry/events.jsonl` holds, seeding the
  ceiling above every id the store holds;
- the stop conditions: an intake or cadence row, a populated field the
  mapping does not name, an ask whose two answers disagree;
- the safety rules: the project is never written, the store is always the
  named one under `--work`, and no store appears under the fixture's `.git`;
- round 3 (TASK-489 spec § Round 3): the one blank rule, an ask's answer and
  a risk's reason, a kernel refusal while reconciling, the `task` and
  `record.id` keys of the old log, and the importer's own checks for
  criteria 3 and 5 shown failing;
- round 4 (§ Round 4, the user's option B): no split of its own. A
  `depends_on` entry is taken whole, an ask's ids are what
  `perry-task asks --all --json` reads, both key-result forms are listed
  for TASK-492, and that read runs only when there is an ask and must write
  nothing under the project.

Run: python3 -m unittest tests.test_kernel_migrate
"""

from __future__ import annotations

COVERS = ("bin/perry-kernel-migrate", "bin/perry-kernel", "kernel/",
          "templates/process/")

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-kernel-migrate"
KERNEL = ROOT / "bin" / "perry-kernel"
sys.path.insert(0, str(ROOT / "tests"))

import config_store  # noqa: E402
import inproc  # noqa: E402

TASK_KEYS = ("id", "title", "owner", "status", "priority", "track", "stage",
             "stage_since", "arrived", "verification", "evidence",
             "next_action", "depends_on", "commitment", "parent", "group",
             "role", "created", "order", "summary", "design_refs")


def task(item_id, status, **given):
    rec = {k: "" for k in TASK_KEYS}
    rec.update(id=item_id, status=status, title=f"title of {item_id}",
               track="main", depends_on=[], order=None, design_refs=[])
    rec.update(given)
    return rec


def ask(item_id, status, answered, **given):
    rec = {"id": item_id, "needed": f"question {item_id}", "blocks": "—",
           "asked": "", "status": status, "answered": answered, "order": 0}
    rec.update(given)
    return rec


def risk(item_id, status, **given):
    rec = {"id": item_id, "risk": f"concern {item_id}", "opened": "",
           "cleared": "", "status": status, "order": 0}
    rec.update(given)
    return rec


OPEN_NEXT = "an open task's next action — kept as it is"

TASKS = [
    task("TASK-001", "done", created="2026-08-01T10:00:00+00:00",
         next_action="a closed task's next action", group="P1",
         evidence="evidence/TASK-001.md", verification="V3",
         design_refs=["DESIGN-001"]),
    task("TASK-002", "not_started", created="2026-08-02",
         next_action=OPEN_NEXT, depends_on=["TASK-001", "USER-001"],
         priority="P1", owner="Coding Agent", summary="a summary"),
    task("TASK-003", "dropped", created="", next_action="gone",
         stage="triaged"),
    task("TASK-004", "in_progress", created="2026-08-05T00:00:00Z",
         depends_on=["TASK-003", "TASK-004"], verification="V4"),
]
ASKS = [
    ask("USER-001", "answered 2026-08-06: yes", True, asked="2026-08-02",
        blocks="TASK-004, P001-O1-KR1"),
    ask("USER-002", "pending", False, asked="2026-08-03"),
]
RISKS = [
    risk("RX-001", "open", opened="2026-08-01"),
    risk("RX-002", "cleared 2026-08-07 — no longer applies",
         cleared="2026-08-07"),
]
EVENTS = [
    {"ts": "2026-08-01T12:00:00+00:00", "event": "done", "id": "TASK-001",
     "from": "not_started", "to": "done"},
    {"ts": "2026-08-03T09:00:00+00:00", "event": "add", "id": "TASK-003",
     "from": None, "to": "not_started"},
    {"ts": "2026-08-04T09:00:00+00:00", "event": "drop", "id": "TASK-003",
     "from": "not_started", "to": "dropped"},
    {"ts": "2026-08-04T10:00:00+00:00", "event": "add", "id": "TASK-009",
     "from": None, "to": "not_started"},
    {"ts": "2026-08-04T11:00:00+00:00", "event": "purge", "id": "TASK-009"},
    {"ts": "2026-08-06T12:00:00+00:00", "event": "answer", "id": "USER-001",
     "from": "pending", "to": "answered"},
    {"ts": "2026-08-06T13:00:00+00:00", "event": "check", "id": "not-an-id"},
]


def jsonl(rows) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    subprocess.run(["git", *args], cwd=str(cwd), env=env, check=True,
                   capture_output=True, timeout=60)


def make_project(base: Path, *, tasks=TASKS, asks=ASKS, risks=RISKS,
                 events=EVENTS, intake=(), cadence=None) -> Path:
    root = base / "proj"
    root.mkdir(parents=True)
    git(root, "init", "-q")
    config_store.write_config(root, {"Document language": "English",
                                     "State root": "state"})
    state = root / "state"
    state.mkdir()
    (state / "tasks.jsonl").write_text(jsonl(tasks), "utf-8")
    (state / "asks.jsonl").write_text(jsonl(asks), "utf-8")
    (state / "risks.jsonl").write_text(jsonl(risks), "utf-8")
    (state / "intake.jsonl").write_text(jsonl(intake), "utf-8")
    if cadence is not None:
        (state / "cadence.jsonl").write_text(jsonl(cadence), "utf-8")
    (root / ".perry" / "events.jsonl").write_text(jsonl(events), "utf-8")
    return root


def fingerprint(root: Path) -> dict:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            st = os.lstat(p)
            digest = (hashlib.sha256(p.read_bytes()).hexdigest()
                      if p.is_file() and not p.is_symlink() else None)
            out[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns,
                                             digest)
    return out


def migrate(*argv, env=None, cwd=None):
    base = {k: v for k, v in os.environ.items()
            if k not in ("PERRY_PROJECT", "PERRY_STORE",
                         "PERRY_KERNEL_TESTING")}
    base.update(env or {})
    return subprocess.run([str(TOOL), *argv], capture_output=True, text=True,
                          env=base, cwd=str(cwd or ROOT), timeout=600)


def kernel(work: Path, state_root: str, *words, data=None):
    argv = [sys.executable, str(KERNEL), *words, "--store",
            str(work / "store.db"), "--root", str(work / "anchor")]
    if data is not None:
        argv += ["--input", json.dumps(data)]
    env = {k: v for k, v in os.environ.items()
           if k not in ("PERRY_PROJECT", "PERRY_STORE")}
    env["PERRY_KERNEL_TESTING"] = "1"
    proc = subprocess.run(argv, capture_output=True, text=True, env=env,
                          timeout=120)
    return json.loads(proc.stdout)


class Fixture(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kernel-migrate-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"

    def project(self, **kw) -> Path:
        return make_project(self.tmp, **kw)

    def run_ok(self, root) -> dict:
        r = migrate("--root", str(root), "--work", str(self.work), "--json")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:] + r.stdout[-2000:])
        return json.loads(r.stdout)

    def refused(self, root, fragment):
        r = migrate("--root", str(root), "--work", str(self.work))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("refused", r.stderr)
        self.assertIn(fragment, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertFalse(self.work.exists(), "a refusal writes nothing")
        return r

    def item(self, item_id) -> dict:
        return kernel(self.work, "state", "item", "get",
                      data={"id": item_id})["result"]["item"]

    def events_of(self, item_id) -> list:
        got = kernel(self.work, "state", "events",
                     data={"items": [item_id], "limit": 0})
        return got["result"]["events"]


class TestAProjectReconciles(Fixture):

    def test_every_criterion_holds_and_the_project_is_untouched(self):
        root = self.project()
        before = fingerprint(root)
        report = self.run_ok(root)
        self.assertEqual(fingerprint(root), before, "the project was written")
        self.assertFalse((root / ".git" / "perry").exists(),
                         "a store appeared under the project's .git")
        self.assertTrue(report["reconciled"])
        self.assertEqual(set(report["criteria"].values()), {True})
        self.assertEqual(len(report["criteria"]), 5)
        self.assertEqual(report["store"], str(self.work / "store.db"))
        self.assertEqual(report["old"]["by_type_and_state"], {
            "task": {"done": 1, "not_started": 1, "dropped": 1,
                     "in_progress": 1},
            "ask": {"answered": 1, "pending": 1},
            "risk": {"open": 1, "cleared": 1}})
        self.assertEqual(report["kernel"]["by_type_and_state"],
                         report["old"]["by_type_and_state"])
        self.assertEqual(report["kernel"]["second_import"],
                         {"exit": 1, "code": "store_not_empty"})
        self.assertEqual(report["kernel"]["export"]["effect"], "unchanged")
        self.assertEqual(report["import"]["result"]["items"], 8)

    def test_the_text_summary_names_each_criterion(self):
        root = self.project()
        r = migrate("--root", str(root), "--work", str(self.work))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("PASS"), 5, r.stdout)

    def test_the_root_flag_beats_the_environment(self):
        root = self.project()
        other = make_project(self.tmp / "other", tasks=[task("TASK-001",
                                                             "done")])
        r = migrate("--root", str(root), "--work", str(self.work), "--json",
                    env={"PERRY_PROJECT": str(other)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["project"], str(root))

    def test_the_project_is_found_from_the_environment_and_the_walk(self):
        root = self.project()
        r = migrate("--work", str(self.work), "--json",
                    env={"PERRY_PROJECT": str(root)})
        self.assertEqual(json.loads(r.stdout)["project"], str(root), r.stderr)
        shutil.rmtree(self.work)
        r = migrate("--work", str(self.work), "--json", cwd=root / "state")
        self.assertEqual(json.loads(r.stdout)["project"], str(root), r.stderr)


class TestTheMapping(Fixture):

    def setUp(self):
        super().setUp()
        self.report = self.run_ok(self.project())

    def test_task_fields_keep_their_names_and_blanks_are_unset(self):
        got = self.item("TASK-002")["fields"]
        self.assertEqual(got["title"], "title of TASK-002")
        self.assertEqual(got["summary"], "a summary")
        self.assertEqual((got["priority"], got["owner"], got["track"]),
                         ("P1", "Coding Agent", "main"))
        self.assertIsNone(got["verification"], "an empty cell is unset")
        self.assertIsNone(got["evidence"])
        self.assertEqual(self.item("TASK-001")["fields"]["evidence"],
                         "evidence/TASK-001.md")

    def test_a_closed_tasks_next_action_is_not_imported(self):
        self.assertIsNone(self.item("TASK-001")["fields"]["next_action"])
        self.assertIsNone(self.item("TASK-003")["fields"]["next_action"])
        self.assertEqual(self.item("TASK-002")["fields"]["next_action"],
                         OPEN_NEXT)
        self.assertEqual(self.report["mapping"]["skipped_next_action"],
                         {"done": 1, "dropped": 1})

    def test_ask_and_risk_fields(self):
        self.assertEqual(self.item("USER-001")["fields"],
                         {"question": "question USER-001", "answer": "yes"})
        self.assertEqual(self.item("USER-001")["state"], "answered")
        self.assertEqual(self.item("USER-002")["fields"],
                         {"question": "question USER-002", "answer": None})
        self.assertEqual(self.item("RX-002")["fields"],
                         {"concern": "concern RX-002",
                          "reason": "cleared 2026-08-07 — no longer applies"})
        self.assertEqual(self.item("RX-002")["state"], "cleared")
        self.assertEqual(self.item("RX-001")["fields"]["reason"], None)
        mapping = self.report["mapping"]
        self.assertEqual(mapping["answers"], {"parsers.ask_answer": 1})
        self.assertEqual(mapping["reasons"], {"status cell verbatim": 1})
        self.assertEqual(mapping["status_not_carried"],
                         {"asks: the answered <date>: part": 1})

    def test_the_fields_not_carried_are_counted(self):
        self.assertEqual(self.report["mapping"]["dropped"], {
            "tasks.group": 1, "tasks.stage": 1, "asks.order": 2,
            "risks.order": 2})

    def test_dependencies_and_ask_blocks_become_blocks_edges(self):
        rel = lambda i: sorted((r["kind"], r["from"], r["to"])  # noqa: E731
                               for r in self.item(i)["relations"])
        self.assertEqual(rel("TASK-002"), [
            ("blocks", "TASK-001", "TASK-002"),
            ("blocks", "USER-001", "TASK-002")])
        self.assertEqual(rel("TASK-004"), [
            ("blocks", "TASK-003", "TASK-004"),
            ("blocks", "USER-001", "TASK-004")])
        mapping = self.report["mapping"]
        self.assertEqual(mapping["unresolved_references"], [])
        self.assertEqual(mapping["for_task_492"], [
            {"register": "asks", "id": "USER-001", "field": "blocks",
             "ref": "P001-O1-KR1"}])
        self.assertEqual(mapping["self_edges"], [
            {"register": "tasks", "id": "TASK-004", "field": "depends_on"}])
        self.assertEqual(mapping["relations"], 4)

    def test_design_refs_become_attachments(self):
        self.assertEqual(self.item("TASK-001")["attachments"],
                         [{"ref": "DESIGN-001", "hash": None}])


class TestTheDates(Fixture):
    """One create event, timed at the creation date, and at most one move,
    timed at the last old status event, or `cleared` for a risk, or the
    creation date. Nothing else of the old history becomes an event."""

    def setUp(self):
        super().setUp()
        self.report = self.run_ok(self.project())

    def shape(self, item_id):
        own = [e for e in self.events_of(item_id) if e["items"][0] == item_id]
        return [(e["command"], e["at"], e["transition"]) for e in own]

    def test_each_item_has_one_create_and_at_most_one_move(self):
        for item_id in ("TASK-001", "TASK-002", "TASK-003", "TASK-004",
                        "USER-001", "USER-002", "RX-001", "RX-002"):
            with self.subTest(item=item_id):
                commands = [c for c, _a, _t in self.shape(item_id)]
                self.assertEqual(commands[0], "item create")
                self.assertLessEqual(commands.count("item move"), 1)
                self.assertEqual(len(commands),
                                 1 + commands.count("item move"))

    def test_the_creation_date_times_the_create(self):
        self.assertEqual(self.shape("TASK-001"), [
            ("item create", "2026-08-01T10:00:00Z", None),
            ("item move", "2026-08-01T12:00:00Z", "done")])
        self.assertEqual(self.shape("TASK-002"), [
            ("item create", "2026-08-02T00:00:00Z", None)])
        self.assertEqual(self.shape("USER-001"), [
            ("item create", "2026-08-02T00:00:00Z", None),
            ("item move", "2026-08-06T12:00:00Z", "answer")])

    def test_no_creation_date_falls_back_to_the_old_log(self):
        self.assertEqual(self.shape("TASK-003"), [
            ("item create", "2026-08-03T09:00:00Z", None),
            ("item move", "2026-08-04T09:00:00Z", "drop")])

    def test_a_cleared_risk_moves_at_cleared(self):
        self.assertEqual(self.shape("RX-002"), [
            ("item create", "2026-08-01T12:00:00Z", None),
            ("item move", "2026-08-07T00:00:00Z", "clear")])

    def test_an_item_with_no_status_event_moves_at_its_creation(self):
        self.assertEqual(self.shape("TASK-004"), [
            ("item create", "2026-08-05T00:00:00Z", None),
            ("item move", "2026-08-05T00:00:00Z", "start")])


class TestABlankCellIsUnset(Fixture):
    """Decided after round 1: the old store's blank marker `—`, and an empty
    string, mean the field is unset, so neither is imported, whatever the
    field. The report counts them per field and by spelling. A `—` on a
    closed task's `next_action` is counted here, not as a skipped cell."""

    def test_the_marker_and_the_empty_string_are_not_imported(self):
        root = self.project(
            tasks=[task("TASK-001", "not_started", evidence="—",
                        next_action="—", summary="", owner="",
                        priority="—", verification="V3"),
                   task("TASK-002", "done", next_action="—",
                        evidence="evidence/TASK-002.md", summary=" — "),
                   task("TASK-003", "done", next_action="closed prose")],
            asks=[ask("USER-001", "pending", False, needed="—")],
            risks=[risk("RX-001", "open", risk="")])
        report = self.run_ok(root)
        fields = self.item("TASK-001")["fields"]
        for name in ("evidence", "next_action", "summary", "owner",
                     "priority"):
            with self.subTest(field=name):
                self.assertIsNone(fields[name])
        self.assertEqual(fields["verification"], "V3")
        self.assertIsNone(self.item("TASK-002")["fields"]["summary"])
        self.assertEqual(self.item("TASK-002")["fields"]["evidence"],
                         "evidence/TASK-002.md")
        self.assertIsNone(self.item("USER-001")["fields"]["question"])
        self.assertIsNone(self.item("RX-001")["fields"]["concern"])
        unset = report["mapping"]["unset_cells"]
        self.assertEqual(unset["tasks.evidence"], {"—": 1, "empty": 1})
        self.assertEqual(unset["tasks.next_action"], {"—": 2})
        self.assertEqual(unset["tasks.summary"], {"empty": 2, "—": 1})
        self.assertEqual(unset["tasks.priority"], {"—": 1, "empty": 2})
        self.assertEqual(unset["asks.needed"], {"—": 1})
        self.assertEqual(unset["risks.risk"], {"empty": 1})
        self.assertEqual(report["mapping"]["skipped_next_action"],
                         {"done": 1}, "only the closed cell with text")

    def test_every_spelling_of_the_one_rule_is_unset(self):
        """Round 3, item 1: unset means `lib.is_blank_cell`, the project's
        one blank rule, not only `—` and an empty string. Each spelling is
        counted as it was written. A cell that only begins with such a word
        says something, and is imported."""
        root = self.project(
            tasks=[task("TASK-001", "not_started", next_action="TBD",
                        summary="n/a", evidence="none", owner="-",
                        priority="待定", verification="?"),
                   task("TASK-002", "not_started",
                        next_action="TBD: ask the vendor")],
            asks=[], risks=[])
        report = self.run_ok(root)
        fields = self.item("TASK-001")["fields"]
        for name in ("next_action", "summary", "evidence", "owner",
                     "priority", "verification"):
            with self.subTest(field=name):
                self.assertIsNone(fields[name])
        self.assertEqual(self.item("TASK-002")["fields"]["next_action"],
                         "TBD: ask the vendor")
        unset = report["mapping"]["unset_cells"]
        self.assertEqual(unset["tasks.next_action"], {"TBD": 1})
        self.assertEqual(unset["tasks.summary"], {"n/a": 1, "empty": 1})
        self.assertEqual(unset["tasks.evidence"], {"none": 1, "empty": 1})
        self.assertEqual(unset["tasks.owner"], {"-": 1, "empty": 1})
        self.assertEqual(unset["tasks.priority"], {"待定": 1, "empty": 1})
        self.assertEqual(unset["tasks.verification"], {"?": 1, "empty": 1})


class TestAMoveIsNeverBeforeItsCreate(Fixture):
    """Decided after round 1: a move is timed at the later of its rule's
    time and its item's create. An `asked` date is read as 00:00 UTC, and
    an answer recorded before that instant on the same day would otherwise
    move the ask before it exists, as USER-930 did."""

    EVENTS = [
        {"ts": "2026-08-09T20:00:00+00:00", "event": "answer",
         "id": "USER-001", "from": "pending", "to": "answered"},
        {"ts": "2026-08-12T09:00:00+00:00", "event": "answer",
         "id": "USER-002", "from": "pending", "to": "answered"},
    ]

    def setUp(self):
        super().setUp()
        root = self.project(
            tasks=[], risks=[], events=self.EVENTS,
            asks=[ask("USER-001", "answered 2026-08-10: yes", True,
                      asked="2026-08-10"),
                  ask("USER-002", "answered 2026-08-12: no", True,
                      asked="2026-08-10")])
        self.report = self.run_ok(root)

    def own(self, item_id):
        return [e for e in self.events_of(item_id)
                if e["items"][0] == item_id]

    def test_the_move_is_clamped_to_the_create_and_says_so(self):
        create, move = self.own("USER-001")
        self.assertEqual((create["command"], create["at"]),
                         ("item create", "2026-08-10T00:00:00Z"))
        self.assertEqual((move["command"], move["at"]),
                         ("item move", "2026-08-10T00:00:00Z"))
        self.assertIn("(2026-08-09T20:00:00Z), clamped to its create",
                      move["note"])
        self.assertIn("a date, read as 00:00 UTC", create["note"])
        self.assertEqual(self.report["mapping"]["clamped_moves"], [
            {"id": "USER-001", "rule": "last old status event",
             "rule_time": "2026-08-09T20:00:00Z",
             "clamped_to": "2026-08-10T00:00:00Z"}])

    def test_a_move_after_its_create_keeps_its_time(self):
        _create, move = self.own("USER-002")
        self.assertEqual(move["at"], "2026-08-12T09:00:00Z")
        self.assertNotIn("clamped", move["note"])


class TestTheCeilings(Fixture):

    def test_an_id_only_the_log_holds_seeds_the_ceiling(self):
        """TASK-009 was purged: the store's highest task is TASK-004, and
        only `.perry/events.jsonl` still names TASK-009. The next id the
        kernel mints is above it."""
        report = self.run_ok(self.project())
        ceiling = report["ceilings"]["TASK"]
        self.assertEqual((ceiling["stored_max"], ceiling["issued_max"],
                          ceiling["log_only_ids"], ceiling["seed"]),
                         (4, 9, ["TASK-009"], 9))
        self.assertEqual(report["kernel"]["next_ids"]["TASK"]["next_id"],
                         "TASK-010")
        self.assertEqual(report["kernel"]["next_ids"]["USER"]["next_id"],
                         "USER-003")
        seeds = [e for e in kernel(self.work, "state", "events",
                                   data={"limit": 0})["result"]["events"]
                 if e["command"] == "seed ceilings"]
        self.assertEqual([c for e in seeds for c in e["changes"]], [
            {"key": "ceiling:TASK", "before": 4, "after": 9}])

    def test_the_task_and_record_id_keys_seed_the_ceiling(self):
        """Round 3, item 6: the ceiling reads every id-bearing key of the
        old events, `id`, `task` and `record.id`. A `link-edge` event names
        its task under `task`, and a purge keeps the purged record under
        `record`. Each case's id is held by no store and by no `id` key."""
        for key, event, number in (
                ("task", {"ts": "2026-08-05T10:00:00+00:00",
                          "event": "link-edge", "kr": "P001-O1-KR1",
                          "task": "TASK-020"}, 20),
                ("record.id", {"ts": "2026-08-05T11:00:00+00:00",
                               "event": "purge",
                               "record": {"id": "TASK-031",
                                          "status": "dropped"}}, 31)):
            with self.subTest(key=key):
                base = self.tmp / key
                self.work = base / "work"
                report = self.run_ok(make_project(base,
                                                  events=EVENTS + [event]))
                ceiling = report["ceilings"]["TASK"]
                self.assertEqual((ceiling["issued_max"], ceiling["seed"]),
                                 (number, number))
                self.assertEqual(ceiling["log_only_ids"],
                                 ["TASK-009", f"TASK-{number:03d}"])
                self.assertEqual(
                    report["kernel"]["next_ids"]["TASK"]["next_id"],
                    f"TASK-{number + 1:03d}")

    def test_with_nothing_purged_no_ceiling_event_is_written(self):
        events = [e for e in EVENTS if e["id"] != "TASK-009"]
        report = self.run_ok(self.project(events=events))
        self.assertIsNone(report["ceilings"]["TASK"]["seed"])
        self.assertEqual(report["kernel"]["next_ids"]["TASK"]["next_id"],
                         "TASK-005")


class TestItStops(Fixture):
    """Each stop condition refuses before anything is written."""

    def test_an_intake_row(self):
        root = self.project(intake=[{"order": 0, "arrived": "2026-08-01",
                                     "request": "r", "outcome": "",
                                     "discharged": False}])
        self.refused(root, "intake.jsonl holds 1 row(s)")

    def test_a_cadence_row(self):
        root = self.project(cadence=[{
            "id": "CAD-001", "title": "t", "owner": "User", "frequency": "weekly",
            "next_due": "2026-08-01", "last_run": "", "order": 0}])
        self.refused(root, "cadence.jsonl holds 1 row(s)")

    def test_a_populated_field_the_mapping_does_not_name(self):
        """`parent` is never set (decision 13) and the mapping carries it
        nowhere; a key the old record shape does not have is carried
        nowhere either. Both stop the import rather than vanish."""
        for field, value in (("parent", "TASK-002"), ("mood", "x")):
            with self.subTest(field=field):
                base = self.tmp / field
                root = make_project(base, tasks=[
                    task("TASK-001", "done", **{field: value})])
                self.work = base / "work"
                self.refused(root, f"field {field!r} holds a value")

    def test_an_ask_whose_answers_disagree(self):
        root = self.project(asks=[ask("USER-001", "pending", True)])
        self.refused(root, "the two disagree")

    def test_a_risk_status_that_is_neither(self):
        root = self.project(risks=[risk("RX-001", "watching")])
        self.refused(root, "neither open nor cleared")

    def test_a_task_status_the_template_does_not_have(self):
        root = self.project(tasks=[task("TASK-001", "parked")])
        self.refused(root, "is not a state of the task type")

    def test_an_id_the_type_would_not_mint(self):
        root = self.project(tasks=[task("TASK-1", "done")])
        self.refused(root, "which is not an id type task mints")


class TestTheKernelsRefusalIsReported(Fixture):

    def test_a_dependency_cycle(self):
        root = self.project(tasks=[
            task("TASK-001", "not_started", depends_on=["TASK-002"]),
            task("TASK-002", "not_started", depends_on=["TASK-001"])],
            asks=[], risks=[], events=[])
        r = migrate("--root", str(root), "--work", str(self.work), "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        report = json.loads(r.stdout)
        self.assertFalse(report["reconciled"])
        self.assertEqual(report["import"]["error"]["code"], "export_invalid")
        self.assertIn("cycle", report["import"]["error"]["message"])
        self.assertEqual(sorted(report["import"]["event_items"]),
                         ["TASK-001", "TASK-002"])


class TestAnAnswerAndAReason(Fixture):
    """Round 3, items 2 and 3. A closed ask's answer and a cleared risk's
    reason are in the status cell, and they are carried. No new parse cuts
    them out:
    - an answered ask's `answer` is what `parsers.ask_answer` returns, and
      where that is empty, as for `withdrawn …`, the status cell verbatim;
    - a risk is cleared when `parsers.status_is_cleared` says so, and its
      `reason` is the status cell verbatim.
    The field is set by the item's one move, the event that closes it."""

    ASKS = [
        ask("USER-001", "answered 2026-08-06: thirty days", True),
        ask("USER-002", "**answered 2026-08-16: 30 days**", True),
        ask("USER-003", "withdrawn 2026-08-20 — folded into TASK-001", True),
        ask("USER-004", "dropped 2026-08-21", True),
        ask("USER-005", "pending", False),
        ask("USER-006", "waiting on legal", False),
    ]
    RISKS = [
        risk("RX-001", "mitigated 2026-08-07 — the vendor shipped the fix"),
        risk("RX-002", "cleared"),
        risk("RX-003", "**resolved** 2026-08-09"),
        risk("RX-004", "open"),
    ]

    def setUp(self):
        super().setUp()
        self.report = self.run_ok(self.project(
            tasks=[task("TASK-001", "done")], asks=self.ASKS,
            risks=self.RISKS, events=[]))

    def field(self, item_id, name):
        return self.item(item_id)["fields"][name]

    def test_an_answer_is_what_ask_answer_returns(self):
        self.assertEqual(self.field("USER-001", "answer"), "thirty days")
        self.assertEqual(self.field("USER-002", "answer"), "30 days")

    def test_an_answer_ask_answer_cannot_read_is_the_cell_verbatim(self):
        self.assertEqual(self.field("USER-003", "answer"),
                         "withdrawn 2026-08-20 — folded into TASK-001")
        self.assertEqual(self.field("USER-004", "answer"),
                         "dropped 2026-08-21")

    def test_a_pending_ask_has_no_answer(self):
        for item_id in ("USER-005", "USER-006"):
            with self.subTest(item=item_id):
                self.assertEqual(self.item(item_id)["state"], "pending")
                self.assertIsNone(self.field(item_id, "answer"))

    def test_status_is_cleared_decides_and_the_reason_is_verbatim(self):
        for item_id, cell in (("RX-001", self.RISKS[0]["status"]),
                              ("RX-002", "cleared"),
                              ("RX-003", "**resolved** 2026-08-09")):
            with self.subTest(item=item_id):
                self.assertEqual(self.item(item_id)["state"], "cleared")
                self.assertEqual(self.field(item_id, "reason"), cell)
        self.assertEqual(self.item("RX-004")["state"], "open")
        self.assertIsNone(self.field("RX-004", "reason"))

    def test_the_move_sets_the_field(self):
        for item_id, name, value in (
                ("USER-003", "answer", self.ASKS[2]["status"]),
                ("RX-002", "reason", "cleared")):
            with self.subTest(item=item_id):
                create, move = [e for e in self.events_of(item_id)
                                if e["items"][0] == item_id]
                self.assertNotIn(f"field:{name}",
                                 [c["key"] for c in create["changes"]])
                self.assertIn({"key": f"field:{name}", "before": None,
                               "after": value}, move["changes"])

    def test_each_kind_is_counted(self):
        mapping = self.report["mapping"]
        self.assertEqual(mapping["answers"], {"parsers.ask_answer": 2,
                                              "status cell verbatim": 2})
        self.assertEqual(mapping["reasons"], {"status cell verbatim": 3})
        self.assertEqual(mapping["status_not_carried"], {
            "asks: the answered <date>: part": 2,
            "asks: a pending status that says more": 1})


class TestTheReferences(Fixture):
    """Round 4, the user's option B: the importer holds no split of its own.
    A `depends_on` entry is taken whole, as `tasks.jsonl` holds it
    (`perry-task § parse_depends` output). An ask's ids are the
    `blocks_ids` that `perry-task asks --all --json` reads out of its
    `Blocks` cell. A reference that is no imported id makes the run "not
    reconciled", unless it is a key result, which is listed for TASK-492."""

    def references(self, depends, blocks):
        return self.project(
            tasks=[task("TASK-001", "done"), task("TASK-002", "not_started"),
                   task("TASK-003", "not_started", depends_on=depends)],
            asks=[ask("USER-001", "pending", False, blocks=blocks)],
            risks=[], events=[])

    def rel(self, item_id):
        return sorted((r["from"], r["to"])
                      for r in self.item(item_id)["relations"]
                      if r["kind"] == "blocks")

    def perry_task_blocks_ids(self, root):
        """What `perry-task asks --all --json` itself reads, run here."""
        env = {k: v for k, v in os.environ.items()
               if k not in ("PERRY_PROJECT", "PERRY_STORE")}
        proc = subprocess.run([sys.executable, str(ROOT / "bin" / "perry-task"),
                               "asks", "--all", "--json", "--root", str(root)],
                              capture_output=True, text=True, env=env,
                              timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return {a["id"]: a["blocks_ids"]
                for a in json.loads(proc.stdout)["asks"]}

    def test_a_blocks_cell_is_read_as_perry_task_reads_it(self):
        report = self.run_ok(self.references(
            ["TASK-001", "TASK-002"], "TASK-002; TASK-003,TASK-001 —"))
        self.assertEqual(report["mapping"]["unresolved_references"], [])
        self.assertEqual(self.rel("TASK-003"), [
            ("TASK-001", "TASK-003"), ("TASK-002", "TASK-003"),
            ("USER-001", "TASK-003")])
        self.assertEqual(self.rel("USER-001"), [
            ("USER-001", "TASK-001"), ("USER-001", "TASK-002"),
            ("USER-001", "TASK-003")])
        self.assertEqual(report["mapping"]["relations"], 5)

    def test_the_importer_agrees_with_perry_task(self):
        """`TASK-001、TASK-002`, an ideographic comma, is two ids to
        `perry-task § _BLOCKS_ID`. Round 3's own split on `,` `;` and white
        space read it as one token that named nothing, so the run was not
        reconciled. Now the importer's edges are exactly the ids
        `perry-task` publishes, prose around them included."""
        root = self.references([], "TASK-001、TASK-002 (TASK-003 later)")
        ids = self.perry_task_blocks_ids(root)
        self.assertEqual(ids, {"USER-001": ["TASK-001", "TASK-002",
                                            "TASK-003"]})
        report = self.run_ok(root)
        self.assertTrue(report["reconciled"])
        self.assertEqual(self.rel("USER-001"),
                         sorted(("USER-001", t) for t in ids["USER-001"]))

    def test_a_depends_on_entry_is_taken_whole(self):
        """`tasks.jsonl` holds `parse_depends` output, one id per entry. An
        entry that is not one is a reference to nothing, never split."""
        root = self.references(["TASK-001;TASK-002"], "—")
        r = migrate("--root", str(root), "--work", str(self.work), "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        report = json.loads(r.stdout)
        self.assertFalse(report["reconciled"])
        self.assertEqual(report["mapping"]["unresolved_references"], [
            {"register": "tasks", "id": "TASK-003", "field": "depends_on",
             "ref": "TASK-001;TASK-002"}])
        self.assertEqual(report["mapping"]["relations"], 0)

    def test_both_key_result_forms_are_listed_for_task_492(self):
        """`perry-task § _BLOCKS_ID` reads `O1-KR1` and `P003-O2-KR3`. Both
        are key results by the id shape the schema declares for one, so
        both are listed, not refused, from either field."""
        report = self.run_ok(self.references(
            ["TASK-001", "O2-KR1"], "O1-KR1, P003-O2-KR3, TASK-002"))
        self.assertTrue(report["reconciled"])
        self.assertEqual(report["mapping"]["for_task_492"], [
            {"register": "tasks", "id": "TASK-003", "field": "depends_on",
             "ref": "O2-KR1"},
            {"register": "asks", "id": "USER-001", "field": "blocks",
             "ref": "O1-KR1"},
            {"register": "asks", "id": "USER-001", "field": "blocks",
             "ref": "P003-O2-KR3"}])
        self.assertEqual(report["mapping"]["unresolved_references"], [])
        self.assertEqual(self.rel("USER-001"), [("USER-001", "TASK-002")])

    def test_a_reference_to_no_imported_id_is_not_reconciled(self):
        root = self.references(["TASK-088"], "TASK-002; TASK-077")
        r = migrate("--root", str(root), "--work", str(self.work), "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        report = json.loads(r.stdout)
        self.assertFalse(report["reconciled"])
        self.assertEqual(set(report["criteria"].values()), {True})
        self.assertEqual(report["mapping"]["unresolved_references"], [
            {"register": "tasks", "id": "TASK-003", "field": "depends_on",
             "ref": "TASK-088"},
            {"register": "asks", "id": "USER-001", "field": "blocks",
             "ref": "TASK-077"}])
        self.assertEqual(report["not_reconciled_because"],
                         ["2 reference(s) resolve to no imported id"])
        shutil.rmtree(self.work)
        text = migrate("--root", str(root), "--work", str(self.work))
        self.assertEqual(text.returncode, 1, text.stderr)
        self.assertIn("FAIL  2 reference(s) resolve to no imported id: "
                      "TASK-003 depends_on TASK-088, USER-001 blocks "
                      "TASK-077", text.stdout)
        self.assertIn("NOT reconciled", text.stdout)

    def test_a_blocks_cell_that_names_no_id_is_counted(self):
        report = self.run_ok(self.references([], "waiting on the vendor"))
        self.assertTrue(report["reconciled"])
        self.assertEqual(report["mapping"]["blocks_cells_with_no_id"],
                         ["USER-001"])
        self.assertEqual(self.rel("USER-001"), [])


class InProcess(Fixture):
    """The importer's `main`, run in this process, so that a test can make
    one kernel answer or one export line what it needs (`tests/inproc.py`).
    Every other kernel call is the real one, on the store under `--work`."""

    def setUp(self):
        super().setUp()
        self.mod = inproc.load("perry-kernel-migrate")

    def main(self, root, *flags):
        return inproc.run("perry-kernel-migrate",
                          ["--root", str(root), "--work", str(self.work),
                           *flags],
                          env={"PERRY_PROJECT": None, "PERRY_STORE": None})


class TestAKernelRefusalWhileReconciling(InProcess):
    """Round 3, item 5. A kernel call that is refused after the import, or
    that prints no envelope, is reported, the run is "not reconciled", and
    no traceback is printed."""

    REFUSAL = {"ok": False, "surface": "1.0", "effect": None, "events": [],
               "store_seq": None, "warnings": [], "result": None,
               "error": {"code": "store_busy",
                         "message": "the write lock was not acquired within "
                                    "5 s", "details": {}}}

    #: Each reconciliation call that must succeed, and the criterion it
    #: serves. `events` serves none: it only reads the store's tail.
    CALLS = (("query", "count_by", "1_counts_per_type_and_state"),
             ("query", "ids", "2_every_old_id_resolves"),
             ("item create", None, "3_next_id_above_every_issued_id"),
             ("export", None, "5_replay_reproduces_the_items"),
             ("events", None, None))

    def refused(self, command, key, *, envelope=True):
        """`(the --json run, the text run)`, each into its own empty
        `--work`, with `command` refused and every other call real."""
        real = self.mod.kernel

        def refusing(words, data, **kw):
            if " ".join(words) == command and (key is None or key in data):
                if not envelope:
                    raise self.mod.Refused(f"perry-kernel {command} printed "
                                           f"no envelope (exit 3): boom")
                return {**self.REFUSAL, "command": command, "exit": 1}
            return real(words, data, **kw)

        base = self.tmp / f"{command}-{key}".replace(" ", "-")
        root = make_project(base)
        runs = []
        for flags in (["--json"], []):
            self.work = base / f"work{len(runs)}"
            with mock.patch.object(self.mod, "kernel", refusing):
                runs.append(self.main(root, *flags))
        return tuple(runs)

    def test_each_refused_call_is_reported_and_not_reconciled(self):
        for command, key, criterion in self.CALLS:
            with self.subTest(command=command, key=key):
                r, text = self.refused(command, key)
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertNotIn("Traceback", r.stderr + text.stderr)
                report = json.loads(r.stdout)
                self.assertFalse(report["reconciled"])
                errors = report["kernel"]["errors"]
                self.assertTrue(errors, report["kernel"])
                self.assertEqual({(e["command"], e["code"]) for e in errors},
                                 {(command, "store_busy")})
                self.assertIn(f"{len(errors)} kernel call(s) refused during "
                              f"reconciliation",
                              report["not_reconciled_because"])
                failed = {n for n, held in report["criteria"].items()
                          if not held}
                self.assertEqual(failed, {criterion} - {None})
                self.assertEqual(text.returncode, 1, text.stderr)
                self.assertIn(f"FAIL  the kernel refused {command}: "
                              f"store_busy", text.stdout)

    def test_a_call_that_prints_no_envelope_is_reported_alike(self):
        r, text = self.refused("export", None, envelope=False)
        self.assertEqual((r.returncode, text.returncode), (1, 1), r.stderr)
        self.assertNotIn("Traceback", r.stderr + text.stderr)
        report = json.loads(r.stdout)
        self.assertFalse(report["reconciled"])
        self.assertFalse(report["criteria"]["5_replay_reproduces_the_items"])
        self.assertEqual(report["kernel"]["errors"], [
            {"command": "export", "exit": None, "code": None,
             "message": "perry-kernel export printed no envelope (exit 3): "
                        "boom"}])


class TestTheImportersOwnChecks(InProcess):
    """Round 3, item 7. The importer's checks for criteria 3 and 5 fail when
    they should. In round 1, forcing either one true (mutants M8 and M9)
    left every test green."""

    def test_criterion_3_fails_when_the_seed_is_lost(self):
        """TASK-009 was purged, so only the `ceiling:TASK` event lifts the
        mint above it. An export without that event imports cleanly, and
        the kernel then mints TASK-005, which was issued before."""
        real = self.mod.build_export

        def unseeded(plan, state_root):
            items_bytes, events_bytes, built = real(plan, state_root)
            lines = events_bytes.decode("utf-8").splitlines(keepends=True)
            self.assertEqual(json.loads(lines[-1])["command"],
                             "seed ceilings")
            return (items_bytes, "".join(lines[:-1]).encode("utf-8"),
                    {**built, "events": built["events"][:-1]})

        with mock.patch.object(self.mod, "build_export", unseeded):
            r = self.main(self.project(), "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        report = json.loads(r.stdout)
        self.assertTrue(report["import"]["ok"], report["import"])
        self.assertEqual(report["kernel"]["next_ids"]["TASK"], {
            "next_id": "TASK-005", "issued_max": 9, "above": False})
        criteria = report["criteria"]
        self.assertFalse(criteria.pop("3_next_id_above_every_issued_id"))
        self.assertEqual(set(criteria.values()), {True})
        self.assertFalse(report["reconciled"])

    def test_criterion_5_fails_when_the_export_does_not_match(self):
        """The export the import read is changed before the check asks for
        `export`. The kernel's own serialisation then differs from it, so
        `export` writes, and the check must say FAIL."""
        real = self.mod.kernel

        def tampering(words, data, **kw):
            if list(words) == ["export"]:
                path = kw["anchor"] / "state" / "export" / "items.jsonl"
                lines = path.read_bytes().splitlines(keepends=True)
                path.write_bytes(b"".join(lines[:-1]))
            return real(words, data, **kw)

        with mock.patch.object(self.mod, "kernel", tampering):
            r = self.main(self.project(), "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        report = json.loads(r.stdout)
        self.assertEqual(report["kernel"]["export"], {"effect": "written"})
        criteria = report["criteria"]
        self.assertFalse(criteria.pop("5_replay_reproduces_the_items"))
        self.assertEqual(set(criteria.values()), {True})
        self.assertFalse(report["reconciled"])


class TestTheChecksForCriteria124(InProcess):
    """Round 5. The importer's checks for criteria 1, 2 and 4 fail when the
    kernel's answer says they should. In round 2, forcing each one true
    (mutants M18–M20) left every test green. Each test edits one answer of
    the real kernel and shows that one criterion, and only it, failing."""

    def edited(self, words, key, edit):
        real = self.mod.kernel

        def editing(w, data, **kw):
            got = real(w, data, **kw)
            if list(w) == words and (key is None or key in (data or {})):
                edit(got)
            return got

        with mock.patch.object(self.mod, "kernel", editing):
            r = self.main(self.project(), "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return json.loads(r.stdout)

    def only_failed(self, report, name):
        failed = sorted(n for n, held in report["criteria"].items()
                        if not held)
        self.assertEqual(failed, [name])
        self.assertFalse(report["reconciled"])

    def test_criterion_1_fails_when_a_count_differs(self):
        def one_less(got):
            got["result"]["counts"][0]["n"] -= 1

        report = self.edited(["query"], "count_by", one_less)
        self.only_failed(report, "1_counts_per_type_and_state")

    def test_criterion_2_fails_when_an_id_does_not_resolve(self):
        def drop_one(got):
            got["result"]["items"].pop()

        report = self.edited(["query"], "ids", drop_one)
        self.only_failed(report, "2_every_old_id_resolves")
        self.assertEqual(len(report["kernel"]["ids"]["missing_or_wrong_type"]),
                         1)

    def test_criterion_2_fails_when_an_id_has_another_type(self):
        def retype(got):
            item = got["result"]["items"][0]
            item["type"] = "ask" if item["type"] != "ask" else "risk"

        report = self.edited(["query"], "ids", retype)
        self.only_failed(report, "2_every_old_id_resolves")

    def test_criterion_4_fails_when_the_second_import_is_not_refused(self):
        for name, edit in (
                ("accepted", lambda g: g.update(ok=True, exit=0, error=None)),
                ("refused for another reason",
                 lambda g: g["error"].update(code="export_invalid"))):
            with self.subTest(case=name):
                self.work = self.tmp / name.replace(" ", "-")
                real = self.mod.kernel
                calls = {"import": 0}

                def second_import(w, data, edit=edit, real=real,
                                  calls=calls, **kw):
                    got = real(w, data, **kw)
                    if list(w) == ["import"]:
                        calls["import"] += 1
                        if calls["import"] == 2:
                            edit(got)
                    return got

                base = self.tmp / f"{name}-proj".replace(" ", "-")
                with mock.patch.object(self.mod, "kernel", second_import):
                    r = self.main(make_project(base), "--json")
                self.assertEqual(r.returncode, 1, r.stderr)
                report = json.loads(r.stdout)
                self.only_failed(
                    report, "4_import_refuses_a_store_that_is_not_empty")


class TestThePerryTaskRead(InProcess):
    """Round 4. The ask ids come from `perry-task asks --all --json`, run as
    a subprocess. It runs only when the project holds an ask, it must write
    nothing under the project, and its payload must carry `blocks_ids` for
    exactly the store's asks."""

    def test_a_project_with_no_ask_runs_no_perry_task(self):
        def never(_root):
            raise AssertionError("perry-task asks ran for a project with no "
                                 "ask")

        root = self.project(tasks=[task("TASK-001", "done")], asks=[],
                            events=[])
        with mock.patch.object(self.mod, "run_perry_task_asks", never):
            r = self.main(root, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["reconciled"])

    MARKER = ".perry-task-transaction.json"

    def test_a_pending_marker_stops_the_import_asks_or_no_asks(self):
        """Round 6. A pending `perry-task` recovery marker, as
        `parsers.scan_recovery` reports it, stops the import before any
        store is read: on a project with no ask (SkyTonight's shape), where
        no `perry-task` runs, and on one with asks. The marker is left as it
        was, and nothing is written."""
        for name, asks in (("no-ask", []), ("asks", ASKS)):
            with self.subTest(project=name):
                base = self.tmp / name
                self.work = base / "work"
                root = make_project(base, tasks=[task("TASK-001", "done")],
                                    asks=asks, events=[])
                marker = root / "state" / self.MARKER
                body = json.dumps({"version": 1, "entries": []})
                marker.write_text(body, "utf-8")
                for flags in (["--work", str(self.work)], []):
                    r = migrate("--root", str(root), *flags)
                    self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                    self.assertIn(f"state/{self.MARKER} is a pending "
                                  f"perry-task recovery marker", r.stderr)
                    self.assertNotIn("Traceback", r.stderr)
                    self.assertEqual(marker.read_text("utf-8"), body)
                    self.assertFalse(self.work.exists())

    def test_a_late_marker_is_not_recovered_by_the_frozen_reader(self):
        """A marker appearing after the outer gate stays untouched, and
        the read refusal retains its exact path through the importer."""
        root = self.project()
        state = root / "state"
        marker = state / self.MARKER
        real = self.mod.run_perry_task_asks

        def marker_appears(project_root):
            staged = b"staged by a crashed write\n"
            (state / "note.json.tmp").write_bytes(staged)
            marker.write_text(json.dumps({"version": 1, "phase": "commit",
                                          "entries": [{
                "target": "note.json", "tmp": "note.json.tmp",
                "new_sha256": hashlib.sha256(staged).hexdigest()}]}), "utf-8")
            return real(project_root)

        with mock.patch.object(self.mod, "run_perry_task_asks",
                               marker_appears):
            r = self.main(root)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("perry-task asks refused", r.stderr)
        self.assertIn(str(marker), r.stderr)
        self.assertIn("pre-cutover", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertTrue(marker.exists(), "a frozen read recovered the marker")
        self.assertFalse((state / "note.json").exists())
        self.assertEqual((state / "note.json.tmp").read_bytes(),
                         b"staged by a crashed write\n")

    def test_a_concurrent_source_change_still_stops_the_import(self):
        root = self.project()
        real = self.mod.run_perry_task_asks
        def another_writer(project_root):
            result = real(project_root)
            (root / "state" / "concurrent.json").write_text("concurrent change")
            return result
        with mock.patch.object(self.mod, "run_perry_task_asks", another_writer):
            result = self.main(root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("changed 1 file(s) under the state root or .perry/",
                      result.stderr)
        self.assertFalse(self.work.exists())
        self.assertFalse(self.work.exists(), "a refusal writes nothing")

    def edited_payload(self, edit):
        real = self.mod.run_perry_task_asks

        def edited(root):
            payload = real(root)
            edit(payload)
            return payload

        with mock.patch.object(self.mod, "run_perry_task_asks", edited):
            return self.main(self.project())

    def test_a_payload_with_no_blocks_ids_stops_the_import(self):
        def drop(payload):
            for row in payload["asks"]:
                row.pop("blocks_ids")

        r = self.edited_payload(drop)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("carries no `blocks_ids` list", r.stderr)
        self.assertFalse(self.work.exists())

    def test_a_payload_that_disagrees_with_the_store_stops_the_import(self):
        for name, edit in (
                ("an ask missing", lambda p: p["asks"].pop()),
                ("a cell rewritten",
                 lambda p: p["asks"][0].update(blocks="TASK-001"))):
            with self.subTest(case=name):
                self.work = self.tmp / name.replace(" ", "-")
                base = self.tmp / f"{name}-proj".replace(" ", "-")
                real = self.mod.run_perry_task_asks

                def edited(root, edit=edit, real=real):
                    payload = real(root)
                    edit(payload)
                    return payload

                with mock.patch.object(self.mod, "run_perry_task_asks",
                                       edited):
                    r = self.main(make_project(base))
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn("perry-task asks and the ask store disagree",
                              r.stderr)
                self.assertFalse(self.work.exists())


class TestTheInvocation(Fixture):

    def test_help_runs_nothing(self):
        for argv in (["--help"], ["--work", str(self.work), "-h"],
                     ["--root", str(self.tmp), "--help"]):
            with self.subTest(argv=argv):
                r = migrate(*argv)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.startswith("Usage:"), r.stdout[:80])
                self.assertFalse(self.work.exists())

    def test_bad_invocations_are_exit_2(self):
        for argv, fragment in (
                (["--work", str(self.work), "--xyzzy"], "unknown argument"),
                (["--work", str(self.work), "extra"], "takes no argument"),
                (["--work"], "--work takes a value"),
                (["--work", ""], "--work was given an empty value"),
                (["--root", "", "--work", str(self.work)], "empty value")):
            with self.subTest(argv=argv):
                r = migrate(*argv, cwd=self.tmp)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn(fragment, r.stderr)
                self.assertFalse(self.work.exists())

    def test_without_work_it_plans_and_writes_nothing(self):
        """The flag-only default (DESIGN-016 C3): the same plan the import
        would write, reported, with nothing written anywhere."""
        root = self.project()
        before = fingerprint(root)
        r = migrate("--root", str(root), "--json", cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(r.stdout)
        self.assertTrue(plan["planned_only"])
        self.assertIsNone(plan["reconciled"])
        self.assertEqual(plan["old"]["ids"], 8)
        self.assertEqual(plan["ceilings"]["TASK"]["seed"], 9)
        self.assertEqual(plan["mapping"]["skipped_next_action"],
                         {"done": 1, "dropped": 1})
        self.assertEqual(fingerprint(root), before)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["proj"])
        text = migrate("--root", str(root), cwd=self.tmp)
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertIn("plan only", text.stdout)

    def test_the_plan_stops_where_the_import_would(self):
        root = self.project(risks=[risk("RX-001", "watching")])
        r = migrate("--root", str(root), cwd=self.tmp)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("neither open nor cleared", r.stderr)

    def test_a_bare_call_outside_a_project_is_refused(self):
        r = migrate(cwd=self.tmp)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("holds no .perry/", r.stderr)

    def test_the_work_directory_must_be_empty_and_outside(self):
        root = self.project()
        occupied = self.tmp / "occupied"
        occupied.mkdir()
        (occupied / "keep.txt").write_text("mine")
        before = fingerprint(root)
        for work, fragment in (
                (root / "scratch", "is inside the project"),
                (root, "is inside the project"),
                (self.tmp, "holds the project"),
                (occupied, "is not an empty directory"),
                (self.tmp / "elsewhere" / ".git" / "perry",
                 "inside a .git directory")):
            with self.subTest(work=str(work)):
                r = migrate("--root", str(root), "--work", str(work))
                self.assertEqual(r.returncode, 1, r.stderr)
                self.assertIn(fragment, r.stderr)
        self.assertEqual(fingerprint(root), before)
        self.assertEqual((occupied / "keep.txt").read_text(), "mine")
        self.assertFalse((self.tmp / "elsewhere").exists())

    def test_a_directory_that_is_not_a_project(self):
        bare = self.tmp / "bare"
        bare.mkdir()
        r = migrate("--root", str(bare), "--work", str(self.work))
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("holds no .perry/", r.stderr)


if __name__ == "__main__":
    unittest.main()
