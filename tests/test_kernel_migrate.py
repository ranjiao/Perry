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
  named one under `--work`, and no store appears under the fixture's `.git`.

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

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "perry-kernel-migrate"
KERNEL = ROOT / "bin" / "perry-kernel"
sys.path.insert(0, str(ROOT / "tests"))

import config_store  # noqa: E402

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
                         {"question": "question USER-001", "answer": None})
        self.assertEqual(self.item("USER-001")["state"], "answered")
        self.assertEqual(self.item("RX-002")["fields"],
                         {"concern": "concern RX-002", "reason": None})
        self.assertEqual(self.item("RX-002")["state"], "cleared")
        self.assertEqual(self.report["mapping"]["status_not_carried"],
                         {"asks": 1, "risks": 1})

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
        self.assertEqual(mapping["unresolved_references"], [
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
        root = self.project()
        for argv, fragment in (
                ([], "--work <dir> is required"),
                (["--root", str(root)], "--work <dir> is required"),
                (["--work", str(self.work), "--xyzzy"], "unknown argument"),
                (["--work", str(self.work), "extra"], "takes no argument"),
                (["--work"], "--work takes a value"),
                (["--root", "", "--work", str(self.work)], "empty value")):
            with self.subTest(argv=argv):
                r = migrate(*argv, cwd=self.tmp)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn(fragment, r.stderr)
                self.assertFalse(self.work.exists())

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
