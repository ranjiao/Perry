"""Every reader of the O→KR→task graph answers from `linkage.jsonl`.

TASK-278 (DESIGN-015 row **C**) moved six readers off `phase/<NNN>-linkage.md`
and onto the store, and this module was built around the two files
DISAGREEING: the store put an edge under one KR, the document under another,
so restoring any one call site to `parse_linkage(<document>)` turned exactly
the test named for that site red.

**ADR-019 deleted the document, and that fixture with it.** There is one copy
of this graph now, so "which file did this reader read" is no longer a
question anything can be asked. What survives, and what this module now pins:

1. **Each reader still reports what the store says**, and says which KR — a
   reader that reported nothing, or the wrong KR, is red. Weaker than the old
   two-file refutation and honestly so; the two-file refutation cannot exist
   without two files.
2. **The per-phase rule**, which is the part that got harder rather than
   easier. `linkage.jsonl` now holds every phase at once — three of them on
   this project — so a reader that took the store store-wide would print
   phase 001's key results under phase 003's objectives. Four seams decide
   this and the TASK-278 V4 review found the rule applied at one and missing
   at three, with four of five mutations against it green.
3. **The wrong-input branches**, which are where TASK-277's mutation round
   found five guards that could each be deleted with the suite green. A store
   that is not there, one that will not parse, a phase the store does not
   declare, a record whose line the writer cannot read.
4. **The drift class is impossible rather than clean** —
   `TestTheDriftClassCannotOccur`. `linkage-store-drift` reported `1 row(s)
   drifted` on this project the day ADR-019 was written, and the rule is gone
   because its subject is. A census line still printing `0 row(s) drifted`
   would be the strongest possible version of "unchecked read as clean".

Run: python3 tests/parallel test_linkage_store_readers
"""

from __future__ import annotations

import goals_actor
import task_actor

COVERS = (
    "tests/goals_actor.py",
    "bin/perry-goals",
    "bin/perry-lint",
    "bin/perry-state",
    "bin/perry-task",
    "viewer/parsers.py",
)

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402

LINT = ROOT / "bin" / "perry-lint"
STATE = ROOT / "bin" / "perry-state"
GOALS = ROOT / "bin" / "perry-goals"
TASK = ROOT / "bin" / "perry-task"

CONFIG = ("# Perry configuration\n\n- Document language: English\n"
          "- Repo layout: single\n- State root: .\n")
HOOK = ("# Perry hook\n\n## High-stakes operations\n\n"
        "- Anything that writes outside this fixture\n")

BOARD = (
    "# Board — linkage store fixture\n\n> Live working memory.\n>\n"
    "> Last updated: 2026-09-05\n\n"
    "## P0 (must finish this period)\n\n"
    "| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n"
    "| TASK-100 | a row | Coding Agent | in_progress | carry on | — |\n"
    "| TASK-101 | another row | Coding Agent | in_progress | carry on | — |\n\n"
    "## P1\n\n| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n\n"
    "## P2\n\n| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n\n"
    "## Cadence\n\n| ID | Recurring task | Owner | Frequency | Next due |\n"
    "|---|---|---|---|---|\n\n"
    "## User Input Queue\n\n"
    "| USER-id | Needed from user | Blocks | Idle | Status |\n"
    "|---|---|---|---|---|\n\n"
    "## Top risks (one-line)\n\n- None.\n"
)


def phase_file(number: str, title: str, started: str, status: str,
               kr_rows: str) -> str:
    """A phase document complete enough to lint clean.

    `kr_rows` is the KR table. It matters for the FALLBACK: a project whose
    store declares no KR for a phase is still swept from this table, which is
    what an adopted project and every Perry project older than TASK-157 has.
    """
    return (
        f"# Phase #{number} — {title}\n\n"
        f"> **Started**: {started}\n> **Status**: {status}\n\n"
        f"## Phase Focus\n\nOne objective, so the register has something to "
        f"name.\n\n"
        f"## Operating Rules\n\n- Agent autonomy: none.\n\n"
        f"## Cost Ceiling (phase #{number})\n\n- Spend cap: ≤ $0.\n\n"
        f"## User Commitments\n\n- None.\n\n"
        f"## User-Unavailable Degradation\n\nNone.\n\n"
        f"## Phase Scope Reduction Rule\n\n- **Phase-day trigger**: none.\n\n"
        f"## Objective 1 — {title}\n\n### Key Results\n\n"
        f"| Id | KR text | Metric / Target | Linked overall KR |\n"
        f"|---|---|---|---|\n{kr_rows}\n"
        f"## Definition of Done\n\n### Must-Have (failure = phase missed)\n\n"
        f"- [ ] The KR above is met\n\n"
        f"## Not Doing in this phase\n\n- Anything else.\n\n"
        f"## Process Note\n\nRead, never worked.\n"
    )


AT = "2026-09-05T00:00:00Z"


def store(*, phase: str, edges: dict[str, list[str]],
          unlinked: list[str] | None = None,
          krs: tuple[str, ...] = ("KR1", "KR2"),
          serves: str | None = None,
          agents: dict[str, list[str]] | None = None,
          objectives: tuple[str, ...] = ("O1",)) -> str:
    """`linkage.jsonl` — the six declared kinds, one JSON object per line.

    Written by hand rather than through `perry-goals link`, for the reason
    `tests/test_linkage_task_exists.py § register` gives: the file has to hold
    a state under test, and going through the writer would make every fixture
    a test of the writer — which is itself one of the readers being measured.
    """
    number = phase.split("-")[0]
    lines = []
    for oid in objectives:
        lines.append(json.dumps({"kind": "objective", "phase": phase,
                                 "id": oid, "title": "an objective"}))
    for suffix in krs:
        lines.append(json.dumps({
            "kind": "kr", "phase": phase, "objective": "O1",
            "id": f"P{number}-O1-{suffix}",
            "title": f"the {suffix} result",
            "metric": f"the argument for {suffix}",
            "target": 1, "current": 1, "stretch": False,
            "asserted_at": AT}))
    for kr_id, tasks in edges.items():
        for tid in tasks:
            lines.append(json.dumps({
                "kind": "edge", "task": tid, "kr": kr_id,
                "declared_at": AT, "actor": "goals", "via": "link"}))
    for tid in (unlinked or []):
        lines.append(json.dumps({
            "kind": "unlinked", "task": tid, "phase": phase,
            "declared_at": AT, "actor": "goals", "via": "link"}))
    if serves:
        lines.append(json.dumps({
            "kind": "project", "phase": phase, "id": "PRJ-1", "kr": serves,
            "name": "a project", "aliases": [],
            "declared_at": AT, "actor": "goals", "via": "link"}))
    for who, tids in (agents or {}).items():
        for tid in tids:
            lines.append(json.dumps({
                "kind": "agent", "phase": phase, "id": who, "task": tid,
                "declared_at": AT, "actor": "goals", "via": "link"}))
    return "".join(line + "\n" for line in lines)


def task_record(tid: str, status: str = "in_progress") -> str:
    return json.dumps({
        "id": tid, "title": "a row", "owner": "Coding Agent",
        "status": status, "priority": "P0", "track": "main",
        "next_action": "carry on", "evidence": "", "verification": "V2",
        "created": "2026-09-01T09:00:00", "order": None,
    }, ensure_ascii=False)


class Fixture(unittest.TestCase):
    """A project whose store puts `TASK-100` under `KR1` and not under `KR2`.

    `KR2` is declared and empty, deliberately: every assertion below names
    which of the two the reader reported, so a reader that lost the edge, or
    attached it to the wrong KR, is red rather than merely quiet.
    """

    STORE_KR = "P003-O1-KR1"
    OTHER_KR = "P003-O1-KR2"

    def project(self, *, store_text: str | None = "default",
                tasks: tuple[str, ...] = ("TASK-100", "TASK-101"),
                store_unlinked: list[str] | None = None,
                extra_phase: bool = False,
                extra_in_store: bool = True) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-linkage-store-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "phase").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text(CONFIG)
        (d / ".perry" / "hook.md").write_text(HOOK)
        (d / "BOARD.md").write_text(BOARD)
        (d / "phase" / "CURRENT").write_text("003-storage\n")
        (d / "phase" / "003-storage.md").write_text(phase_file(
            "003", "storage", "2026-09-01", "active",
            "| P003-O1-KR1 | the KR1 result | 1 | — |\n"
            "| P003-O1-KR2 | the KR2 result | 1 | — |\n"))
        if store_text == "default":
            store_text = store(phase="003-storage",
                               edges={self.STORE_KR: ["TASK-100"]},
                               unlinked=store_unlinked)
        if extra_phase:
            # A SECOND phase in the same store — the condition the per-phase
            # rule exists for, and the one this project is now permanently in:
            # ADR-019 imported all three of its registers into one file.
            (d / "phase" / "002-zeta.md").write_text(phase_file(
                "002", "zeta", "2026-08-01", "scored",
                "| P002-O1-KR1 | the KR1 result | 1 | — |\n"))
            if extra_in_store and store_text is not None:
                store_text += store(phase="002-zeta",
                                    edges={"P002-O1-KR1": ["TASK-101"]},
                                    krs=("KR1",))
        if store_text is not None:
            (d / "linkage.jsonl").write_text(store_text)
        (d / "tasks.jsonl").write_text(
            "".join(task_record(t) + "\n" for t in tasks))
        return d

    # -- the seams

    def lint(self, d: pathlib.Path, *extra) -> dict:
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(d), "--json", *extra],
            capture_output=True, text=True, cwd=ROOT)
        return json.loads(proc.stdout)

    def state(self, d: pathlib.Path, section: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root", str(d),
             "--section", section],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def goals(self, d: pathlib.Path, *argv) -> tuple[int, dict]:
        proc = subprocess.run(
            # Keep the fixture root visible at the subprocess boundary: the
            # live-state sweep follows --root before considering cwd=ROOT.
            [sys.executable, str(GOALS), *goals_actor.owned(argv),
             "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, json.loads(proc.stdout or "{}")

    def purge(self, d: pathlib.Path, tid: str) -> tuple[int, dict]:
        proc = subprocess.run(
            task_actor.command([sys.executable, str(TASK), "purge", tid, "--reason",
             "a fixture row", "--root", str(d), "--json"], 'test_linkage_store_readers'),
            capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, json.loads(proc.stdout or "{}")

    def drop(self, d: pathlib.Path, tid: str) -> None:
        subprocess.run(
            task_actor.command([sys.executable, str(TASK), "drop", tid, "--reason",
             "done with it", "--root", str(d)], 'test_linkage_store_readers'),
            capture_output=True, text=True, cwd=ROOT)

    def rules(self, payload: dict, rule: str) -> list[dict]:
        return [f for f in payload["findings"] if f["rule"] == rule]

    def records(self, d: pathlib.Path) -> list[dict]:
        return [json.loads(line) for line
                in (d / "linkage.jsonl").read_text().split("\n")
                if line.strip()]


class TestEveryReaderAnswersFromTheStore(Fixture):
    """One test per call site of `DESIGN-015 § 5.6`."""

    def test_site_6_perry_state_attribution_reads_the_store(self):
        """`viewer/parsers.py § load_snapshot` — what `perry-state`'s
        attribution reader is built on."""
        d = self.project()
        payload = self.state(d, "linkage")["linkage"]
        by_id = {k["id"]: k["tasks"]
                 for o in payload["objectives"] for k in o["krs"]}
        self.assertEqual(by_id[self.STORE_KR], ["TASK-100"])
        self.assertEqual(by_id[self.OTHER_KR], [],
                         "KR2 has no edge in the store and must have none "
                         "here")

    def test_site_6_carries_the_metric_the_document_used_to_hold(self):
        """`metric` was `derived_not_stored` and lived in the register
        document — DESIGN-015 decision 2, *an argument about how a number was
        reached is what a document is for*. ADR-019 deleted the document, so
        the choice stopped being "store or document" and became "store or
        lose it". A reader that took the typed half and dropped the argument
        would satisfy the test above and still lose the thing.
        """
        d = self.project()
        payload = self.state(d, "linkage")["linkage"]
        metrics = {k["id"]: k["metric"]
                   for o in payload["objectives"] for k in o["krs"]}
        self.assertEqual(metrics[self.STORE_KR], "the argument for KR1")

    def test_site_6_carries_the_objective_title_too(self):
        """The other field with no home left. Objective titles and their ORDER
        came from the document's `objectives:` block; they are `kind:
        objective` records now, and an objective rendered untitled is a
        heading a reader cannot use."""
        d = self.project()
        payload = self.state(d, "linkage")["linkage"]
        self.assertEqual([o["title"] for o in payload["objectives"]],
                         ["an objective"])

    def test_site_2_perry_goals_krs_reads_the_store(self):
        """`bin/perry-goals § cmd_krs`."""
        d = self.project()
        code, out = self.goals(d, "krs")
        self.assertEqual(code, 0, out)
        by_id = {k["id"]: k["tasks"]
                 for o in out["objectives"] for k in o["krs"]}
        self.assertEqual(by_id[self.STORE_KR], ["TASK-100"])
        self.assertEqual(by_id[self.OTHER_KR], [])
        self.assertEqual(out["register"], "linkage.jsonl")

    def test_site_3_perry_task_names_the_store_and_its_line(self):
        """`bin/perry-task § live_references`, and the regex that is gone.

        The refusal quotes `linkage.jsonl:<line>`. A line number is only
        available because one record is one line — the property that let the
        regex be replaced by `json.loads` rather than by a second regex.
        """
        d = self.project()
        self.drop(d, "TASK-100")
        code, out = self.purge(d, "TASK-100")
        self.assertEqual(code, 1, out)
        self.assertIn("linkage.jsonl:", out["refused"],
                      "the refusal must name the store and the line")
        self.assertIn(self.STORE_KR, out["refused"],
                      "and the KR the edge attaches to, so a reader knows "
                      "what they would be breaking")

    def test_site_3_an_agent_record_is_a_live_reference_and_says_so(self):
        """`agents[].tasks` was a YAML block in the deleted document and the
        store had NO record kind for it. That is exactly why `purge` read the
        documents as well as the store — and why the union comment in
        `live_references` records a live data loss: when the two scans were
        exclusive, the store's mere presence retired 16 such entries in
        `phase/001-linkage.md` and TASK-028, TASK-046 and TASK-087 stopped
        refusing. ADR-019 declared `kind: agent` so those references live in
        the file the guard already reads.
        """
        d = self.project(store_text=store(
            phase="003-storage", edges={self.STORE_KR: ["TASK-100"]},
            agents={"Coding Agent": ["TASK-101"]}))
        self.drop(d, "TASK-101")
        code, out = self.purge(d, "TASK-101")
        self.assertEqual(code, 1, out)
        self.assertIn("linkage.jsonl:", out["refused"])
        self.assertIn("agent", out["refused"],
                      "the refusal must say WHICH kind of reference it is; "
                      "an agent assignment is not a KR edge")
        self.assertIn("Coding Agent", out["refused"])

    def test_site_3_uses_no_regex_over_the_store(self):
        """The deliverable's own words: replaced by `json.loads`, **not by a
        second regex**.

        Asserted against the source, because the behaviour cannot tell the two
        apart — a regex that happened to match would pass the tests above. The
        window is the reader itself, so an unrelated `re` elsewhere in a
        7,900-line file cannot make this green or red by accident.

        **The window is the whole reference scan now.** It used to stop at the
        document half, because the register document was still read by line —
        it was *"markdown with a YAML-shaped block in it, not a YAML
        document"*, and the refusal had to name a line a reader would go and
        edit. There is no document half, so there is nothing in this scan that
        a regex may still be reading.
        """
        text = (ROOT / "bin" / "perry-task").read_text()
        start = text.index("# `linkage.jsonl § kind: edge`")
        end = text.index("# The goals store's own linkage field", start)
        window = text[start:end]
        self.assertIn("json.loads", window)
        self.assertNotIn("re.match", window)
        self.assertNotIn("re.search", window)
        self.assertNotIn("re.findall", window)

    def test_site_4_the_lint_check_grades_the_stores_edges(self):
        d = self.project(store_text=store(
            phase="003-storage",
            edges={self.STORE_KR: ["TASK-100", "TASK-404"]}))
        found = self.rules(self.lint(d), "linkage-task-exists")
        self.assertEqual(len(found), 1, found)
        self.assertIn("TASK-404", found[0]["message"])
        self.assertEqual(found[0]["file"], "linkage.jsonl")

    def test_site_4_a_dangling_unlinked_declaration_comes_from_the_store(self):
        d = self.project(store_unlinked=["TASK-404"])
        found = self.rules(self.lint(d), "linkage-unlinked-exists")
        self.assertEqual(len(found), 1, found)
        self.assertIn("TASK-404", found[0]["message"])
        self.assertEqual(found[0]["file"], "linkage.jsonl")

    def test_a_projects_finding_names_the_store(self):
        """`kind: project` — the Project↔KR registry.

        It had no record kind before ADR-019, so a finding about it named the
        register DOCUMENT and `linkage_from_store` copied `projects` through
        from there purely so the finding could be filed against the file that
        carried the line. Both halves of that are gone: the entry is a record
        and the finding names the store.
        """
        d = self.project(store_text=store(
            phase="003-storage", edges={self.STORE_KR: ["TASK-100"]},
            serves="P003-O1-KR9"))
        found = [f for f in self.rules(self.lint(d), "linkage-kr-exists")
                 if "PRJ-1" in f["message"]]
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["file"], "linkage.jsonl")

    def test_site_1_link_refuses_on_what_the_store_says(self):
        """`bin/perry-goals § link` — this graph's only writer in the goals
        lane. The store says TASK-100 is under KR1; linking it to KR2 must be
        refused NAMING KR1."""
        d = self.project()
        code, out = self.goals(d, "link", "TASK-100", self.OTHER_KR)
        self.assertEqual(code, 1, out)
        self.assertIn(self.STORE_KR, out["refused"])

    def test_site_1_writes_the_edge_into_the_store(self):
        d = self.project()
        code, out = self.goals(d, "link", "TASK-101", self.OTHER_KR)
        self.assertEqual(code, 0, out)
        edges = [r for r in self.records(d)
                 if r["kind"] == "edge" and r["task"] == "TASK-101"]
        self.assertEqual(len(edges), 1, self.records(d))
        self.assertEqual(edges[0]["kr"], self.OTHER_KR)
        self.assertEqual(edges[0]["via"], "link",
                         "`via` is what P003-O3-KR2 counts on; `add` is row D "
                         "and this path is not it")
        self.assertTrue(edges[0]["actor"],
                        "DESIGN-015 § 7's mitigation is that § 5.5's per-kind "
                        "rule be auditable off the records before anything "
                        "enforces it")

    def test_site_1_dates_only_the_record_it_writes(self):
        """**TASK-155, at the writer.**

        Every `perry-goals link` write used to bump the register document's
        one file-level `updated:` stamp, and that stamp was read as every KR's
        assertion date — so appending one edge re-dated every asserted number
        in the phase. There is no file-level stamp to bump: the write dates
        the record it appends and touches no byte of any other line.
        """
        d = self.project()
        before = (d / "linkage.jsonl").read_text().split("\n")
        code, out = self.goals(d, "link", "TASK-101", self.OTHER_KR)
        self.assertEqual(code, 0, out)
        after = (d / "linkage.jsonl").read_text().split("\n")
        self.assertEqual([line for line in before if line.strip()],
                         [line for line in after if line.strip()][:-1],
                         "the write changed a line it was not asked to write")
        appended = json.loads([line for line in after if line.strip()][-1])
        self.assertEqual(appended["task"], "TASK-101")
        self.assertTrue(appended["declared_at"])
        krs = [r for r in self.records(d) if r["kind"] == "kr"]
        self.assertTrue(krs)
        self.assertTrue(all(r.get("asserted_at") == AT for r in krs),
                        "an edge write moved a KR's assertion date")

    def test_site_1_retracts_the_unlinked_record_it_supersedes(self):
        """A row cannot be attributed and declared drifting at once. This is
        the one place this writer removes a record rather than appending
        one."""
        d = self.project(store_unlinked=["TASK-101"])
        code, out = self.goals(d, "link", "TASK-101", self.OTHER_KR)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["store_records_retracted"], ["TASK-101"])
        self.assertEqual(
            [r for r in self.records(d)
             if r["kind"] == "unlinked" and r["task"] == "TASK-101"], [])


class TestThePerPhaseRule(Fixture):
    """One store, every phase — so the slice is what keeps them apart.

    This got HARDER at ADR-019, not easier. Before it, `linkage.jsonl` held
    phase 003 only and the filter had no work to do: TASK-278 round 2's
    mutation made the `edge` clause always true and nothing went red, because
    the input that would have caught it did not exist in any fixture. The
    store now holds all three of this project's phases, so every one of these
    clauses is load-bearing on the real file.
    """

    def test_a_second_phases_krs_do_not_print_under_this_ones_objectives(self):
        d = self.project(extra_phase=True)
        by_id = {k["id"]: k["tasks"] for o in
                 self.state(d, "linkage")["linkage"]["objectives"]
                 for k in o["krs"]}
        self.assertIn(self.STORE_KR, by_id)
        self.assertNotIn("P002-O1-KR1", by_id,
                         "phase 002's KR printed under phase 003 — the store "
                         "was read store-wide")

    def test_reading_the_other_phase_gives_the_other_phases_krs(self):
        """The control. Without it the test above passes for a reader that
        answers nothing at all."""
        d = self.project(extra_phase=True)
        (d / "phase" / "CURRENT").write_text("002-zeta\n")
        by_id = {k["id"]: k["tasks"] for o in
                 self.state(d, "linkage")["linkage"]["objectives"]
                 for k in o["krs"]}
        self.assertEqual(by_id.get("P002-O1-KR1"), ["TASK-101"])
        self.assertNotIn(self.STORE_KR, by_id)

    def test_a_declaration_is_scoped_to_the_phase_it_was_made_against(self):
        """`unlinked.phase`, which ADR-019 added and DESIGN-015 § 5.1 had
        deliberately left out.

        The old argument was sound while it held: "this row serves no KR" is a
        statement about the row, not about a phase, so the record needed no
        phase field. What made it stop holding is that the store now covers
        every phase at once — `linkage_records_for_phase` handed the WHOLE
        unlinked set to whichever phase was asked, so phase 001's 23
        declarations would count against phase 003's board.
        """
        d = self.project(extra_phase=True)
        with (d / "linkage.jsonl").open("a") as fh:
            fh.write(json.dumps({"kind": "unlinked", "task": "TASK-101",
                                 "phase": "002-zeta", "declared_at": AT,
                                 "actor": "goals", "via": "link"}) + "\n")
        self.assertEqual(
            self.state(d, "linkage")["linkage"]["unlinked"], [],
            "a declaration made against phase 002 was counted under 003")
        (d / "phase" / "CURRENT").write_text("002-zeta\n")
        self.assertEqual(
            self.state(d, "linkage")["linkage"]["unlinked"], ["TASK-101"])

    def test_a_declaration_with_no_phase_still_travels_with_every_phase(self):
        """Back-compat, stated rather than left to be discovered.

        A store imported under DESIGN-015 row B has `unlinked` records with no
        `phase` field, and that is what every one of them meant: the whole set
        belonged to whichever phase the store was the authority for. They keep
        that meaning; only records that carry the field are scoped by it.
        """
        d = self.project(extra_phase=True)
        with (d / "linkage.jsonl").open("a") as fh:
            fh.write(json.dumps({"kind": "unlinked", "task": "TASK-101",
                                 "declared_at": AT, "actor": "goals",
                                 "via": "link"}) + "\n")
        self.assertEqual(
            self.state(d, "linkage")["linkage"]["unlinked"], ["TASK-101"])
        (d / "phase" / "CURRENT").write_text("002-zeta\n")
        self.assertEqual(
            self.state(d, "linkage")["linkage"]["unlinked"], ["TASK-101"])

    def test_the_writer_reads_only_its_own_phases_records(self):
        """Site 1 — `linkage_graph`, the seam `link`'s refusals are made from.

        This site was already correct and had NO test: the TASK-278 V4
        review's V10 and V11 both removed its per-phase rule and the suite
        stayed green. `TASK-101` is already under `P002-O1-KR1`, so a
        correctly scoped graph answers "already linked" and writes nothing;
        read store-wide the graph carries phase 003's KRs instead and
        `P002-O1-KR1` becomes a KR it does not carry — a refusal, and a
        different exit code.
        """
        d = self.project(extra_phase=True)
        (d / "phase" / "CURRENT").write_text("002-zeta\n")
        code, out = self.goals(d, "link", "TASK-101", "P002-O1-KR1",
                               "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("already", out,
                      "phase 002's own records already carry this edge; a "
                      "graph that cannot see it was read store-wide")
        self.assertIn("P002-O1-KR1", out["already"])

    def test_an_edge_naming_another_phases_kr_stays_out_of_this_slice(self):
        """**Round 2's green N3, and it is REACHABLE — `add --kr` reaches it.**

        `perry-task add --kr P001-O1-KR1` appends an `edge` record naming
        another phase's KR, and from that moment phase 003's render would
        carry a phase-001 edge.
        """
        d = self.project(store_text=store(
            phase="003-storage", edges={self.STORE_KR: ["TASK-100"]})
            + json.dumps({"kind": "edge", "task": "TASK-101",
                          "kr": "P001-O1-KR1", "declared_at": AT,
                          "actor": "goals", "via": "add"}) + "\n")
        records = P.load_linkage_store(d)
        self.assertTrue(
            any(r.get("kr") == "P001-O1-KR1" for r in records),
            "the fixture must actually carry the cross-phase edge")
        mine = P.linkage_records_for_phase(records, "003")
        self.assertNotIn("P001-O1-KR1", [r.get("kr") for r in mine])
        by_id = {k["id"]: k["tasks"] for o in
                 self.state(d, "linkage")["linkage"]["objectives"]
                 for k in o["krs"]}
        self.assertNotIn("P001-O1-KR1", by_id)

    def test_an_edge_to_an_overall_kr_this_phase_declares_is_kept(self):
        """The other side of the same clause, and not a loosening of it.

        An overall KR carries no phase in its id — by DESIGN-009 it belongs to
        none — so an edge to `O1-KR1` matches no `P<NNN>-` prefix. Filtering
        on the prefix alone would drop it from every phase, silently.
        `tests/fixtures/witness-project` registers exactly that pair.
        """
        d = self.project(store_text=store(
            phase="003-storage", edges={self.STORE_KR: ["TASK-100"]})
            + json.dumps({"kind": "kr", "phase": "003-storage",
                          "objective": "O1", "id": "O1-KR1",
                          "title": "an overall KR"}) + "\n"
            + json.dumps({"kind": "edge", "task": "TASK-101", "kr": "O1-KR1",
                          "declared_at": AT, "actor": "goals",
                          "via": "link"}) + "\n")
        by_id = {k["id"]: k["tasks"] for o in
                 self.state(d, "linkage")["linkage"]["objectives"]
                 for k in o["krs"]}
        self.assertEqual(by_id.get("O1-KR1"), ["TASK-101"])

    def test_no_phase_number_reads_nothing_rather_than_the_whole_store(self):
        """**Round 2's green N1.**

        `linkage_records_for_phase` returns `None` — not the whole store —
        when nothing names the phase. `None` is what keeps another phase's key
        results from being printed under this one's headings.
        """
        records = P.load_linkage_store(self.project())
        self.assertIsNotNone(records)
        self.assertIsNone(P.linkage_records_for_phase(records, ""))
        self.assertIsNotNone(P.linkage_records_for_phase(records, "003"),
                             "and the control: phase 003 IS in this store")
        # **The input that makes deleting the early return observable.**
        # Without it an empty phase number builds `prefix = "-"`, a MATCHABLE
        # prefix rather than one that matches nothing — so a record whose
        # `phase` begins with a dash is silently adopted by a caller that
        # could not name a phase at all.
        self.assertIsNone(
            P.linkage_records_for_phase(
                [{"kind": "kr", "phase": "-weird", "id": "P-X-KR1"}], ""),
            "no phase was named, so nothing may be filtered to it")

    def test_a_phase_the_store_does_not_declare_falls_back_to_its_table(self):
        """The fallback that survives ADR-019, and the only one left.

        A project that has never had a linkage store declares its phase KRs in
        the phase document's own table — that is what adoption reads, and what
        every Perry project older than TASK-157 has. The id-shape check is
        what can be made from a table alone, and it is still made.
        """
        d = self.project(store_text=None, extra_phase=True,
                         extra_in_store=False)
        (d / "phase" / "002-zeta.md").write_text(phase_file(
            "002", "zeta", "2026-08-01", "scored",
            "| P003-O1-KR9 | pasted from another phase | 1 | — |\n"))
        found = [f for f in self.rules(self.lint(d), "linkage-kr-exists")
                 if "P003-O1-KR9" in f["message"]]
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["file"], "phase/002-zeta.md")


class TestTheWrongInputBranchesAreReached(Fixture):
    """The guards that exist for absence and malformation, each reached.

    **TASK-277's finding, applied forward.** Its round found one shape of
    defect five times over: every test in its module asserted an outcome on
    the happy path, so no branch written for wrong input was ever executed,
    and five guards could each be deleted with the suite still green.
    """

    def test_an_absent_store_is_not_an_empty_one(self):
        """`load_linkage_store` answers `None`, and the graph is empty rather
        than half-built. Reading absence as `[]` and an empty slice as an
        empty graph are two different mistakes and both end in a render that
        says "nothing is being done about that"."""
        d = self.project(store_text=None)
        self.assertIsNone(P.load_linkage_store(d))
        self.assertIsNone(self.state(d, "linkage")["linkage"])

    def test_an_empty_store_is_not_an_absent_one(self):
        """`[]` is a real, present, empty store — the distinction
        `load_task_store` draws and this reader has to draw too."""
        d = self.project(store_text="")
        self.assertEqual(P.load_linkage_store(d), [])

    def test_a_malformed_store_does_not_raise_and_does_not_half_parse(self):
        d = self.project(store_text='{"kind": "kr"\nnot json at all\n')
        self.assertIsNone(P.load_linkage_store(d),
                          "a partial parse would hand a caller half a graph")
        payload = self.lint(d)
        self.assertTrue(self.rules(payload, "linkage-store-unreadable")
                        or self.rules(payload, "linkage-store-malformed"),
                        "perry-lint is the tool that says why, and it must")

    def test_a_record_of_the_wrong_shape_is_a_finding(self):
        """The schema is what says so, and it is read rather than restated."""
        d = self.project(store_text=store(
            phase="003-storage", edges={self.STORE_KR: ["TASK-100"]})
            + json.dumps({"kind": "edge", "task": "TASK-101",
                          "kr": "not-a-kr-id", "declared_at": AT,
                          "actor": "goals", "via": "link"}) + "\n")
        found = self.rules(self.lint(d), "linkage-store-malformed")
        self.assertEqual(len(found), 1, found)
        self.assertIn("not-a-kr-id", found[0]["message"])

    def test_a_kr_whose_objective_has_no_record_is_kept(self):
        """Titleless, never dropped.

        A KR that exists in the authority and vanishes from the render is the
        silent loss this store was built to end, and it is the state a phase
        is in between `plan-phase` writing the KR and anyone writing the
        objective's title.
        """
        recs = [json.loads(line) for line in
                store(phase="003-storage", edges={}).strip().split("\n")]
        recs.append({"kind": "kr", "phase": "003-storage", "objective": "O9",
                     "id": "P003-O9-KR1", "title": "an orphan"})
        graph = P.linkage_from_store(recs)
        self.assertIn("O9", [o.id for o in graph.objectives])
        self.assertEqual([o.title for o in graph.objectives if o.id == "O9"],
                         [""])

    def test_krs_reads_a_phase_the_store_does_not_declare_as_a_refusal(self):
        """Not as an empty table. An empty table and a phase nobody planned
        print the same and mean opposite things."""
        d = self.project(store_text=store(phase="002-zeta", edges={},
                                          krs=("KR1",)))
        code, out = self.goals(d, "krs")
        self.assertEqual(code, 1, out)
        self.assertIn("declares no key result", out["refused"])

    def test_link_on_a_store_less_project_is_refused_not_silently_dropped(self):
        """`Register.__init__` refuses, and the refusal names what writes the
        store. Creating a one-record store here would produce a graph
        consisting of one edge and no key results, and every reader treats a
        present store as the authority."""
        d = self.project(store_text=None)
        code, out = self.goals(d, "link", "TASK-101", self.OTHER_KR)
        self.assertEqual(code, 1, out)
        self.assertFalse((d / "linkage.jsonl").exists())
        self.assertIn("plan-phase", out["refused"])

    def test_a_store_with_a_line_the_writer_cannot_read_is_refused(self):
        """**The rule changed direction at ADR-019, and this is the record.**

        Before it, an unreadable line made `load_linkage_store` answer `None`,
        `linkage_graph` fell back to the register DOCUMENT, and the write
        proceeded — appending to the store while judging the request against
        the other file. `linkage_store_text` therefore had a
        `except json.JSONDecodeError: kept.append(line)` branch whose whole
        job was to carry that line through a rewrite, and two tests drove it,
        because deleting the branch lost a record nobody had looked at yet.

        There is no other file to fall back to. A graph this tool cannot fully
        read is a graph it must not append to — the append would be judged
        against records nobody can see — so `Register.__init__` refuses, by
        name, and points at the tool that reports the line. The branch below
        it is unreachable through this path and is kept as defence in depth
        rather than pinned by a test that would be measuring nothing.

        What has to stay true is that the refusal WRITES NOTHING: a refusal
        that had already rewritten the file would be the data loss with an
        error message on top.
        """
        d = self.project()
        with (d / "linkage.jsonl").open("a") as fh:
            fh.write("{ not json\n")
        before = (d / "linkage.jsonl").read_text()
        code, out = self.goals(d, "link", "TASK-101", self.OTHER_KR)
        self.assertEqual(code, 1, out)
        self.assertIn("cannot be read", out["refused"])
        self.assertIn("perry-lint", out["refused"],
                      "the refusal must name the tool that reports the line")
        self.assertEqual((d / "linkage.jsonl").read_text(), before,
                         "the refusal rewrote the file it refused to write")

    def test_the_linter_names_the_unreadable_line_the_writer_refused_on(self):
        """The other half: a refusal that says "run perry-lint" is only a road
        if `perry-lint` actually answers."""
        d = self.project()
        with (d / "linkage.jsonl").open("a") as fh:
            fh.write("{ not json\n")
        payload = self.lint(d)
        self.assertTrue(self.rules(payload, "linkage-store-unreadable")
                        or self.rules(payload, "linkage-store-malformed"))


class TestTheDriftClassCannotOccur(Fixture):
    """**ADR-019's own claim, as a test.**

    `TestTheDriftVerdictIsReal` stood here and had three cases — agreement,
    disagreement, and nothing-to-compare — because `linkage.jsonl` projected
    from `phase/<NNN>-linkage.md` and the two could differ. They did: on the
    day the ADR was written `perry-lint` reported `linkage store: 124
    record(s), 1 row(s) drifted`, and the drifted row was `P003-O3-KR2`, this
    project's own computed KR.

    The ADR's argument is that a check for the disagreement is the ongoing
    cost of the duplication rather than a fix for it. So the document is gone
    and the class is impossible rather than detected. What has to be tested is
    that nothing still REPORTS on it: a census line reading `0 row(s) drifted`
    over a store with one copy would be the strongest possible version of the
    mistake `P003-O1-KR3` exists to prevent — unchecked printed as clean.
    """

    def test_no_finding_carries_the_drift_rule(self):
        d = self.project()
        self.assertEqual(self.rules(self.lint(d), "linkage-store-drift"), [])

    def test_the_payload_reports_records_and_shape_not_drift(self):
        d = self.project()
        payload = self.lint(d)
        self.assertNotIn("linkage_store_drift", payload,
                         "a consumer reading `drifted` off this store would "
                         "be reading a number that cannot be non-zero and "
                         "taking it for a check that passed")
        stats = payload["linkage_store"]
        self.assertTrue(stats["store_present"])
        self.assertEqual(stats["malformed"], 0)
        self.assertEqual(stats["records"], len(self.records(d)))

    def test_an_absent_store_is_unchecked_and_says_so(self):
        """`P003-O1-KR3`'s rule, which survives the drift check that used to
        carry it: an absent store must not print as a clean one."""
        d = self.project(store_text=None)
        payload = self.lint(d)
        self.assertFalse(payload["linkage_store"]["store_present"])
        self.assertEqual(payload["linkage_store"]["records"], 0)

    def test_the_rule_is_named_nowhere_a_reader_would_look_it_up(self):
        """A rule id declared in the schema, or printed by the census, that no
        code can emit is a checked box nobody ticks."""
        schema = (ROOT / "schema" / "state-schema.json").read_text()
        self.assertNotIn("linkage-store-drift", schema)
        lint = (ROOT / "bin" / "perry-lint").read_text()
        emitted = lint.count('"linkage-store-drift"')
        self.assertEqual(emitted, 0,
                         "perry-lint can still emit a finding for a class "
                         "that cannot occur")


if __name__ == "__main__":
    unittest.main(verbosity=2)
