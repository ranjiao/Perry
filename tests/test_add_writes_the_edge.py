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

import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

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

TASK = ROOT / "bin" / "perry-task"
STATE = ROOT / "bin" / "perry-state"

# Two tracks, because `route` is a QUEUE-mode operation and refuses on a
# project-mode track. A fixture with only `main` makes the route test skip,
# and a skipped test states nothing about the behaviour it names.
CONFIG = ("# Perry configuration\n\n- Document language: English\n"
          "- Repo layout: single\n- State root: .\n\n"
          "## Tracks\n\n"
          "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
          "|---|---|---|---|---|---|---|---|\n"
          "| main | project | phase/ | — | — | — | — | V3 |\n"
          "| intake | queue | standing | "
          "new→triaged→in_progress→resolved | 6 | 5d | weekly | V3 |\n")
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
    lines = []
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
            "kind": "unlinked", "task": tid,
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
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text(CONFIG)
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
        return subprocess.run(argv + list(extra), capture_output=True,
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


class TestTheOneSequence(Fixture):
    """`add --kr` then `attribution`, with nothing run in between."""

    def test_the_new_row_reports_linked(self):
        d = self.project()
        before = self.attribution(d)
        proc = self.add(d, "a linked row", self.STORE_KR)
        tid = self.new_id(proc)
        after = self.attribution(d)

        never_asked = [u["id"] for u in after["unlinked"]]
        self.assertNotIn(tid, never_asked,
                         "the row `add --kr` just linked is reported "
                         "never-asked — the edge did not reach the readers")
        self.assertNotIn(tid, after.get("declared_unlinked") or [],
                         "a row given a KR must not be declared unlinked")
        self.assertEqual(after["linked"], before["linked"] + 1,
                         "`linked` did not rise by exactly the one row added")

    def test_the_edge_record_is_written_once_and_says_via_add(self):
        d = self.project()
        before = len(self.records(d))
        tid = self.new_id(self.add(d, "a linked row", self.STORE_KR))
        recs = self.records(d)
        self.assertEqual(len(recs), before + 1, "exactly one record appended")
        edge = recs[-1]
        self.assertEqual(edge["kind"], "edge")
        self.assertEqual(edge["task"], tid)
        self.assertEqual(edge["kr"], self.STORE_KR)
        # `via` is what makes `P003-O3-KR2` computable at all: "attributed in
        # the same action that created the row" is not recoverable from an
        # edge that only says which KR it points at.
        self.assertEqual(edge["via"], "add")
        self.assertTrue(edge["declared_at"].endswith("Z"),
                        "`declared_at` must be the UTC form `perry-goals "
                        "link` writes, or the two writers sort differently")
        self.assertTrue(edge["actor"])

    def test_the_add_event_carries_the_kr(self):
        d = self.project()
        tid = self.new_id(self.add(d, "a linked row", self.STORE_KR))
        add = [e for e in self.events(d)
               if e.get("event") == "add" and e.get("id") == tid]
        self.assertEqual(len(add), 1)
        self.assertEqual(add[0]["kr"], self.STORE_KR)

    def test_the_success_line_names_the_store_it_wrote(self):
        d = self.project()
        proc = self.add(d, "a linked row", self.STORE_KR)
        self.assertIn("linkage.jsonl", proc.stdout,
                      "the line names every file the write touched")


class TestWithoutAKr(Fixture):
    """§ 5.2: the row is still created, `kr` is null, and it warns."""

    def test_the_row_is_created_and_not_refused(self):
        d = self.project()
        proc = self.add(d, "an unattributed row")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        tid = self.new_id(proc)
        rows = [json.loads(l) for l
                in (d / "tasks.jsonl").read_text().split("\n") if l.strip()]
        self.assertIn(tid, [r["id"] for r in rows])

    def test_the_event_carries_kr_null_not_a_missing_key(self):
        d = self.project()
        tid = self.new_id(self.add(d, "an unattributed row"))
        add = [e for e in self.events(d)
               if e.get("event") == "add" and e.get("id") == tid][0]
        # Present-and-null and absent are different facts: `null` says the
        # question was reached and left unanswered, which is what makes
        # never-asked auditable from the log. A missing key is every `add`
        # event written before row D.
        self.assertIn("kr", add)
        self.assertIsNone(add["kr"])

    def test_it_warns_on_stderr(self):
        d = self.project()
        proc = self.add(d, "an unattributed row")
        self.assertIn("without `--kr`", proc.stderr)
        # The warning must not tell the reader the row was DECLARED unlinked:
        # never-asked and declared-unlinked are the two states § 5.2 keeps
        # apart, and the whole bucket was double-counted for a week when a
        # surface conflated them (TASK-228).
        self.assertIn("never-asked", proc.stderr)

    def test_no_record_of_any_kind_is_written(self):
        d = self.project()
        before = self.records(d)
        tid = self.new_id(self.add(d, "an unattributed row"))
        after = self.records(d)
        self.assertEqual(len(after), len(before),
                         "never-asked is DERIVED FROM ABSENCE (§ 5.2) — no "
                         "record, of any kind, may be written for it")
        self.assertEqual([r for r in after if r.get("task") == tid], [])

    def test_there_is_no_fourth_kind(self):
        d = self.project()
        self.add(d, "an unattributed row")
        kinds = {r.get("kind") for r in self.records(d)}
        self.assertTrue(kinds <= {"kr", "edge", "unlinked"},
                        f"a kind the schema does not declare: {kinds}")
        self.assertNotIn("never_asked", kinds)

    def test_the_row_reports_never_asked_and_not_declared_unlinked(self):
        d = self.project()
        tid = self.new_id(self.add(d, "an unattributed row"))
        att = self.attribution(d)
        self.assertIn(tid, [u["id"] for u in att["unlinked"]])
        self.assertNotIn(tid, att.get("declared_unlinked") or [])


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
        d = self.project()
        tid = self.new_id(self.add(d, "a linked row", self.DOC_KR))
        att = self.attribution(d)
        self.assertNotIn(tid, [u["id"] for u in att["unlinked"]])


class TestAProjectWithNoStore(Fixture):
    """A pre-DESIGN-015 project keeps its document, and keeps ALL of it."""

    def test_add_kr_does_not_create_the_store(self):
        d = self.project(with_store=False)
        proc = self.add(d, "a linked row", self.DOC_KR)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # `parsers.load_linkage` is store-FIRST: a one-record store on a
        # project whose register lives in the document would not add an edge,
        # it would replace the whole graph with a single edge and every KR
        # that project has would vanish from every render.
        self.assertFalse((d / "linkage.jsonl").exists(),
                         "a store was created on a project that had none — "
                         "every KR in its document is now unreachable")

    def test_the_document_graph_survives_the_write(self):
        d = self.project(with_store=False)
        self.add(d, "a linked row", self.DOC_KR)
        att = self.attribution(d)
        self.assertGreaterEqual(att["linked"], 1,
                                "the document's own edges stopped resolving")

    def test_the_event_still_records_the_answer(self):
        d = self.project(with_store=False)
        proc = self.add(d, "a linked row", self.DOC_KR)
        tid = self.new_id(proc)
        add = [e for e in self.events(d)
               if e.get("event") == "add" and e.get("id") == tid][0]
        self.assertEqual(add["kr"], self.DOC_KR,
                         "the store may be absent; the answer was still given "
                         "and the log is where it is recorded")


class TestRouteAndIntakeInheritNeverAsked(Fixture):
    """Neither fabricates an `unlinked` declaration for a row with no KR."""

    def test_intake_then_route_writes_no_linkage_record(self):
        d = self.project()
        before = self.records(d)
        intake = subprocess.run(
            [sys.executable, str(TASK), "intake", "--root", str(d),
             "--arrived", "2026-09-05", "--title", "a request arrived"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(intake.returncode, 0, intake.stderr)
        self.assertEqual(len(self.records(d)), len(before),
                         "`intake` wrote a linkage record")

    def test_route_leaves_the_row_never_asked(self):
        d = self.project()
        before = self.records(d)
        subprocess.run(
            [sys.executable, str(TASK), "intake", "--root", str(d),
             "--arrived", "2026-09-05", "--title", "a request arrived"],
            capture_output=True, text=True, cwd=ROOT)
        proc = subprocess.run(
            [sys.executable, str(TASK), "route", "1", "--root", str(d),
             "--title", "a routed row", "--owner", "Coding Agent",
             "--priority", "P1", "--track", "intake",
             "--summary", "Promotes the intake request into a tracked row."],
            capture_output=True, text=True, cwd=ROOT)
        # Not skipped on refusal. A skip here would let the fixture drift out
        # of `route`'s preconditions and report nothing about the behaviour
        # this test names.
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(self.records(d)), len(before),
                         "`route` wrote a linkage record — a row that was "
                         "never asked must inherit absence, not a declaration")


class TestTheEdgeIsNotASecondTransaction(Fixture):
    """SIGKILL between two canonical renames; the edge must not survive alone.

    The child patches `os.replace` to count only renames whose DESTINATION is
    a canonical target and to die before the Nth. The durable marker is
    written through `lib.write_atomic`, which renames too, so counting that
    would make N mean a different crash point on different runs.
    """

    CHILD = r'''
import importlib.machinery, importlib.util, os, signal, sys
TOOL, ROOT, N, TITLE, KR = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
spec = importlib.util.spec_from_loader(
    "perry_task", importlib.machinery.SourceFileLoader("perry_task", TOOL))
mod = importlib.util.module_from_spec(spec)
sys.modules["perry_task"] = mod
spec.loader.exec_module(mod)
seen = [0]
real = os.replace
def counting(src, dst, *a, **kw):
    name = os.path.basename(str(dst))
    canonical = (name in ("tasks.jsonl", "intake.jsonl", "linkage.jsonl")
                 or (name.endswith(".md") and name[:1].isdigit()))
    if not canonical:
        return real(src, dst, *a, **kw)
    if seen[0] >= N:
        os.kill(os.getpid(), signal.SIGKILL)
    seen[0] += 1
    return real(src, dst, *a, **kw)
os.replace = counting
argv = ["add", "--title", TITLE, "--root", ROOT, "--deliverable", "d",
        "--verification", "v", "--summary",
        "Files a throwaway row so the writer reaches its canonical renames."]
if KR:
    argv += ["--kr", KR]
sys.exit(mod.main(argv))
'''

    def crash_at(self, d: pathlib.Path, n: int, kr: str) -> subprocess.CompletedProcess:
        child = d / "_crash_child.py"
        child.write_text(self.CHILD)
        return subprocess.run(
            [sys.executable, str(child), str(TASK), str(d), str(n),
             "an atomicity probe", kr],
            capture_output=True, text=True, cwd=ROOT)

    def consistency(self, d: pathlib.Path, tid: str) -> tuple[bool, bool]:
        rows = [json.loads(l) for l
                in (d / "tasks.jsonl").read_text().split("\n") if l.strip()]
        return (any(r.get("id") == tid for r in rows),
                any(r.get("kind") == "edge" and r.get("task") == tid
                    for r in self.records(d)))

    def next_id(self, d: pathlib.Path) -> str:
        """The id the crashing run will mint, taken from a `--dry-run`.

        Derived rather than assumed: an assertion about the wrong id passes
        for free, which is the shape that makes a crash test decorative.
        """
        proc = subprocess.run(
            [sys.executable, str(TASK), "add", "--title", "probe",
             "--root", str(d), "--deliverable", "d", "--verification", "v",
             "--summary", "Reads back the id the next add will mint.",
             "--dry-run", "--json"],
            capture_output=True, text=True, cwd=ROOT)
        return json.loads(proc.stdout)["id"]

    def test_the_edge_never_survives_without_its_row(self):
        for n in range(0, 4):
            with self.subTest(renames_before_crash=n):
                d = self.project()
                tid = self.next_id(d)
                proc = self.crash_at(d, n, self.STORE_KR)
                self.assertEqual(
                    proc.returncode, -signal.SIGKILL,
                    f"the child exited {proc.returncode} instead of dying — "
                    f"the crash point was never reached, so this subtest "
                    f"proves nothing. stderr={proc.stderr[:300]}")

                row, edge = self.consistency(d, tid)
                self.assertFalse(
                    edge and not row,
                    "mid-crash the store held an edge for a task "
                    "`tasks.jsonl` does not carry")

                # "The next locked Perry run." Read-only on purpose: recovery
                # must not need a second WRITE, or a crashed tree stays broken
                # until somebody happens to file another row.
                rec = subprocess.run(
                    [sys.executable, str(TASK), "list", "--root", str(d)],
                    capture_output=True, text=True, cwd=ROOT)
                self.assertEqual(rec.returncode, 0, rec.stderr)

                row, edge = self.consistency(d, tid)
                self.assertEqual(
                    row, edge,
                    f"after recovery the row and its edge disagree "
                    f"(row={row}, edge={edge}) — the edge is a second "
                    f"transaction that half-landed")

    def test_the_marker_does_not_outlive_recovery(self):
        d = self.project()
        self.crash_at(d, 2, self.STORE_KR)
        self.assertTrue((d / ".perry-task-transaction.json").exists(),
                        "no marker after the crash — the transaction was "
                        "never staged and the probe measured nothing")
        subprocess.run([sys.executable, str(TASK), "list", "--root", str(d)],
                       capture_output=True, text=True, cwd=ROOT)
        self.assertFalse((d / ".perry-task-transaction.json").exists(),
                         "the marker survived a locked run")

    def test_a_crash_before_any_rename_writes_no_edge(self):
        d = self.project()
        before = len(self.records(d))
        tid = self.next_id(d)
        self.crash_at(d, 0, self.STORE_KR)
        row, edge = self.consistency(d, tid)
        self.assertFalse(edge)
        self.assertFalse(row)
        self.assertEqual(len(self.records(d)), before)


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
