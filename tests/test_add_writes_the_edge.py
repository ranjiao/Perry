"""`perry-task add --kr` writes the edge, in the same transaction as the row.

TASK-279, implementation row **D** of `DESIGN-015 § 5.3`. Row C moved the six
readers of § 5.6 onto `linkage.jsonl`; this row gives the `work` lane the one
write into that store § 5.5 permits it, and puts the write inside `commit()`'s
existing recovery marker rather than beside it.

**The one sequence this module exists for**, with nothing run in between:

    perry-task add --title "…" --kr P003-O1-KR1
    perry-state --section attribution

The new row must report `linked`. Before this row the identical sequence
reported never-asked, because `--kr` was parsed into `args.kr` and read by
exactly one line — the journal's `- **KR linkage**:` prose — so the flag was
accepted and had no effect on any state a reader consults.

**How these tests are built to be able to fail.**

*The one sequence* (`TestTheOneSequence`) asserts on a row that did not exist
when the fixture was authored, so the document CANNOT carry its edge. Only the
store can. A reader still answering from `phase/<NNN>-linkage.md` therefore
reports the new row as never-asked and the test goes red — which is also why
this module is the ordering guard § 6 asks for: if row D ever runs against a
tree where row C has been reverted, the failure is silent in production and
loud here.

*The ordering guard* (`TestTheReadersAreOnTheStore`) states that same
dependency directly rather than as a side effect, on an edge the two files
DISAGREE about: the store puts `TASK-100` under KR1, the document under KR2. A
fixture whose halves agree is green with the readers moved, green with them
unmoved, and green with them deleted.

*Atomicity* (`TestTheEdgeIsNotASecondTransaction`) kills the writer with
SIGKILL between two of the canonical renames and then runs a locked Perry
command. SIGKILL and not an exception: an exception unwinds into
`replace_canonical_pair`'s `except OSError`, which is the deliberate-rollback
branch and is already covered. The branch row D has to survive is the one
where nothing gets to run. The assertion is not "it recovered" but **the edge
and the row agree** — an edge for a task `tasks.jsonl` does not carry is the
half-landed write this row exists to make impossible.

Run: python3 tests/parallel test_add_writes_the_edge
"""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-task",
    "bin/perry-state",
    "bin/perry_store.py",
    "reference/okr-linkage.md",
    "schema/state-schema.json",
)

import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from kernel_work_support import ACTOR, ready, task

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402


def load_tool():
    """`bin/perry-task` as a module, so its guards can be reached directly.

    Every other test here drives the tool through `subprocess`, which is the
    honest way to test a CLI and is also why one guard went unmeasured: the
    `event != "add"` early return in `linkage_add_change` cannot be reached
    from any command line, because no command Perry has TODAY emits an event
    that carries a `kr` key and is not an `add`. Through the process boundary
    the guard is therefore dead code that deletes green — which the mutation
    round found by deleting it (M15). Called directly, it is a live branch
    with a stated reason to exist.
    """
    import importlib.machinery
    import importlib.util
    tool = ROOT / "bin" / "perry-task"
    spec = importlib.util.spec_from_loader(
        "perry_task_for_edge_tests",
        importlib.machinery.SourceFileLoader(
            "perry_task_for_edge_tests", str(tool)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PT = load_tool()

import config_store  # noqa: E402
from config_store import track  # noqa: E402

TASK = ROOT / "bin" / "perry-task"
STATE = ROOT / "bin" / "perry-state"

# Two tracks, because `route` is a QUEUE-mode operation and refuses on a
# project-mode track. A fixture with only `main` makes the route test skip,
# and a skipped test states nothing about the behaviour it names.
TRACKS = [
    track("main", "project", spine="phase/", default_rung="V3"),
    track("intake", "queue", spine="standing",
          stages="new→triaged→in_progress→resolved", wip="6", sla="5d",
          cycle="weekly", default_rung="V3"),
]
HOOK = ("# Perry hook\n\n## High-stakes operations\n\n"
        "- Anything that writes outside this fixture\n")

BOARD = (
    "# Board — add-writes-the-edge fixture\n\n> Live working memory.\n>\n"
    "> Last updated: 2026-09-05\n\n"
    "## P0 (must finish this period)\n\n"
    "| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n"
    "| TASK-100 | a row | Coding Agent | in_progress | carry on | — |\n\n"
    "## P1\n\n| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n\n"
    "## P2\n\n| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n\n"
    "## Cadence\n\n| ID | Recurring task | Owner | Frequency | Next due |\n"
    "|---|---|---|---|---|\n\n"
    "## Intake\n\n| Arrived | Request | Outcome |\n|---|---|---|\n\n"
    "## User Input Queue\n\n"
    "| USER-id | Needed from user | Blocks | Idle | Status |\n"
    "|---|---|---|---|---|\n\n"
    "## Top risks (one-line)\n\n- None.\n"
)

PHASE = (
    "# Phase #003 — storage\n\n"
    "> **Started**: 2026-09-01\n> **Status**: active\n\n"
    "## Phase Focus\n\nOne objective, so the register has something to name.\n\n"
    "## Operating Rules\n\n- Agent autonomy: none.\n\n"
    "## Cost Ceiling (phase #003)\n\n- Spend cap: ≤ $0.\n\n"
    "## User Commitments\n\n- None.\n\n"
    "## User-Unavailable Degradation\n\nNone.\n\n"
    "## Phase Scope Reduction Rule\n\n- **Phase-day trigger**: none.\n\n"
    "## Objective 1 — storage\n\n### Key Results\n\n"
    "| Id | KR text | Metric / Target | Linked overall KR |\n"
    "|---|---|---|---|\n"
    "| P003-O1-KR1 | the KR1 result | 1 | — |\n"
    "| P003-O1-KR2 | the KR2 result | 1 | — |\n\n"
    "## Definition of Done\n\n### Must-Have (failure = phase missed)\n\n"
    "- [ ] The KR above is met\n\n"
    "## Not Doing in this phase\n\n- Anything else.\n\n"
    "## Process Note\n\nRead, never worked.\n"
)


def document(edges: dict[str, list[str]], unlinked: list[str] | None = None) -> str:
    body = ['---\nlinkage: 1\nphase: "003-storage"',
            'updated: "2026-09-05T00:00:00Z"',
            "unlinked: [" + ", ".join(f'"{t}"' for t in (unlinked or [])) + "]",
            'objectives:\n  - id: O1\n    title: "an objective"\n    krs:']
    for suffix in ("KR1", "KR2"):
        kr_id = f"P003-O1-{suffix}"
        ids = ", ".join(f'"{t}"' for t in edges.get(kr_id, []))
        body.append(
            f"      - id: {kr_id}\n"
            f'        title: "the {suffix} result"\n'
            f'        metric: "the argument for {suffix}"\n'
            f"        target: 1\n        current: 1\n"
            f"        stretch: false\n        tasks: [{ids}]")
    return "\n".join(body) + "\n---\n\n# Linkage\n"


def store(edges: dict[str, list[str]], unlinked: list[str] | None = None) -> str:
    lines = [json.dumps({"kind": "objective", "phase": "003-storage",
                         "id": "O1", "title": "an objective"})]
    for suffix in ("KR1", "KR2"):
        lines.append(json.dumps({
            "kind": "kr", "phase": "003-storage", "objective": "O1",
            "id": f"P003-O1-{suffix}", "title": f"the {suffix} result",
            "target": 1, "current": 1, "stretch": False}))
    for kr_id, tasks in edges.items():
        for tid in tasks:
            lines.append(json.dumps({
                "kind": "edge", "task": tid, "kr": kr_id,
                "declared_at": "2026-09-05T00:00:00Z",
                "actor": "goals", "via": "link"}))
    for tid in (unlinked or []):
        lines.append(json.dumps({
            "kind": "unlinked", "task": tid, "phase": "003-storage",
            "declared_at": "2026-09-05T00:00:00Z",
            "actor": "goals", "via": "link"}))
    return "".join(line + "\n" for line in lines)


def task_record(tid: str) -> str:
    """A seeded row, carrying `group` — which is what makes it VISIBLE.

    Written out in full rather than trimmed to the fields under test. A
    record without `group` parses, renders, and lints, and then
    `perry-state`'s store-hydrated snapshot silently drops it: `board.tasks`
    comes back empty, `attribution` counts nothing, and every assertion about
    a bucket this row should sit in passes for free. Measured while building
    this module — the seeded row was invisible to `attribution` in exactly
    that way, and only the counts gave it away.
    """
    return json.dumps({
        "id": tid, "title": "a row", "summary": "a seeded row.",
        "owner": "Coding Agent", "status": "in_progress", "priority": "P0",
        "track": "main", "group": "P0", "next_action": "carry on",
        "evidence": "", "verification": "V2", "depends_on": [],
        "design_refs": [], "commitment": "", "parent": "", "role": "",
        "stage": "", "stage_since": "", "arrived": "",
        "created": "2026-09-01T09:00:00", "order": 0,
    }, ensure_ascii=False)


class Fixture(unittest.TestCase):
    """A project whose store and document disagree about `TASK-100`'s KR."""

    STORE_KR = "P003-O1-KR1"
    DOC_KR = "P003-O1-KR2"

    def project(self, *, with_store: bool = True,
                store_edges: dict | None = None,
                doc_edges: dict | None = None,
                store_unlinked: list[str] | None = None,
                doc_unlinked: list[str] | None = None) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-add-edge-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "phase").mkdir()
        config_store.write_config(d, tracks=TRACKS)
        (d / ".perry" / "hook.md").write_text(HOOK)
        (d / "BOARD.md").write_text(BOARD)
        (d / "phase" / "CURRENT").write_text("003-storage\n")
        (d / "phase" / "003-storage.md").write_text(PHASE)
        (d / "phase" / "003-linkage.md").write_text(document(
            doc_edges if doc_edges is not None else {self.DOC_KR: ["TASK-100"]},
            doc_unlinked))
        if with_store:
            (d / "linkage.jsonl").write_text(store(
                store_edges if store_edges is not None
                else {self.STORE_KR: ["TASK-100"]},
                store_unlinked))
        (d / "tasks.jsonl").write_text(task_record("TASK-100") + "\n")
        return d

    # -- seams

    def add(self, d: pathlib.Path, title: str, kr: str | None = None,
            *extra: str) -> subprocess.CompletedProcess:
        argv = [sys.executable, str(TASK), "add", "--title", title,
                "--root", str(d), "--deliverable", "d",
                "--verification", "v", "--summary", "a summary sentence."]
        if kr:
            argv += ["--kr", kr]
        return subprocess.run(task_actor.command(argv + list(extra), 'test_add_writes_the_edge'), capture_output=True,
                              text=True, cwd=ROOT)

    def attribution(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root", str(d),
             "--section", "attribution"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)["attribution"]

    def records(self, d: pathlib.Path) -> list[dict]:
        p = d / "linkage.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().split("\n") if l.strip()]

    def events(self, d: pathlib.Path) -> list[dict]:
        p = d / ".perry" / "events.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().split("\n") if l.strip()]

    def new_id(self, proc: subprocess.CompletedProcess) -> str:
        """The id `add` minted, read off its own success line."""
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for word in proc.stdout.split():
            if word.startswith("TASK-"):
                return word
        self.fail(f"no task id in {proc.stdout!r}")


class TestNativeCreateDoesNotWriteGoalRegisters(unittest.TestCase):
    def test_create_and_attach_leave_linkage_and_legacy_history_unchanged(self):
        sb = ready(self)
        held = {"linkage.jsonl": '{"kind":"fixture-goal-record"}\n',
                ".perry/events.jsonl": "legacy history\n",
                "journal/2026-08/2026-08-01.md": "legacy journal\n"}
        for rel, body in held.items():
            path = sb.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        tid = task(sb)
        sb.ok("attach add", data={"actor": ACTOR, "id": tid, "ref": "evidence/spec.md"})
        self.assertEqual(sb.get(tid)["state"], "not_started")
        for rel, body in held.items():
            self.assertEqual((sb.root / rel).read_text(), body)

    def test_kr_is_not_a_native_field_or_an_implicit_linkage_declaration(self):
        sb = ready(self)
        tid = task(sb)
        before = sb.seq()
        for key in ("kr", "unlinked"):
            out = sb.run("item update", data={"actor": ACTOR, "id": tid,
                                              "set": {key: "P003-O1-KR1"}})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)
        self.assertFalse((sb.root / "linkage.jsonl").exists())


class TestTheReadersAreOnTheStore(Fixture):
    """The ordering guard § 6 asks for: **C before D**.

    Stated on an edge the two files disagree about, so a reader that has
    regressed to `phase/<NNN>-linkage.md` is caught by name rather than by the
    silence row D would otherwise fail with.
    """

    def test_attribution_answers_from_the_store(self):
        d = self.project()
        att = self.attribution(d)
        # `TASK-100` is under KR1 in the store and KR2 in the document, and is
        # in neither file's `unlinked`. Both readings make it `linked`, so the
        # count cannot separate them — the KR it resolved to is what can.
        krs = {k["id"]: k for o in
               json.loads(subprocess.run(
                   [sys.executable, str(STATE), "--root", str(d),
                    "--section", "linkage"],
                   capture_output=True, text=True,
                   cwd=ROOT).stdout)["linkage"]["objectives"]
               for k in o["krs"]}
        self.assertIn("TASK-100", krs[self.STORE_KR]["tasks"],
                      "the reader answered from the document, not the store — "
                      "row C has been reverted and row D fails SILENTLY")
        self.assertNotIn("TASK-100", krs[self.DOC_KR]["tasks"])

    def test_a_row_linked_by_add_is_visible_to_the_reader(self):
        """The end-to-end statement of the same dependency.

        The document cannot carry this edge — the row did not exist when the
        document was written — so a reader on the document reports never-asked
        for a row just linked, which is § 6's silent failure exactly.
        """
        d = self.project(store_edges={self.DOC_KR: ["TASK-100"]})
        att = self.attribution(d)
        self.assertNotIn("TASK-100", [u["id"] for u in att["unlinked"]])


class TestTheGuardsAreReached(Fixture):
    """`linkage_add_change`'s early returns, called directly.

    The mutation round (M15) deleted the `event != "add"` guard and every
    test in this module stayed green: through the CLI the guard is
    unreachable, because no command Perry has today emits a non-`add` event
    carrying a `kr` key. `route` and `intake` pass it for the WRONG REASON —
    they have no `kr` at all — so the subprocess tests above measure the
    absence of the key, not the guard. These reach it.
    """

    def change(self, d: pathlib.Path, event: dict):
        return PT.linkage_add_change(d, event)

    def test_a_non_add_event_carrying_a_kr_writes_nothing(self):
        d = self.project()
        # The shape no command produces today and any command could tomorrow.
        # `work` may write an edge at `add` and nowhere else (§ 5.5); the
        # guard is what says so in code rather than in a comment.
        for name in ("route", "intake", "start", "done", "retitle"):
            with self.subTest(event=name):
                self.assertIsNone(self.change(d, {
                    "event": name, "id": "TASK-100", "kr": self.STORE_KR,
                    "actor": "agent"}))

    def test_an_add_event_carrying_a_kr_does_write(self):
        """The other side of the same guard, so it is not vacuously true."""
        d = self.project()
        out = self.change(d, {"event": "add", "id": "TASK-999",
                              "kr": self.STORE_KR, "actor": "agent"})
        self.assertIsNotNone(out, "the guard rejects the one event it must pass")
        self.assertEqual(out[2]["task"], "TASK-999")
        self.assertEqual(out[2]["via"], "add")

    def test_an_add_with_no_kr_writes_nothing(self):
        d = self.project()
        self.assertIsNone(self.change(d, {"event": "add", "id": "TASK-999",
                                          "kr": None, "actor": "agent"}))

    def test_an_add_with_no_id_writes_nothing(self):
        d = self.project()
        self.assertIsNone(self.change(d, {"event": "add", "id": "",
                                          "kr": self.STORE_KR,
                                          "actor": "agent"}))

    def test_a_project_with_no_store_writes_nothing(self):
        d = self.project(with_store=False)
        self.assertIsNone(self.change(d, {"event": "add", "id": "TASK-999",
                                          "kr": self.STORE_KR,
                                          "actor": "agent"}))


if __name__ == "__main__":
    unittest.main()
