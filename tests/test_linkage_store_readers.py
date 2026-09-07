"""The six readers of `DESIGN-015 § 5.6` answer from `linkage.jsonl`.

TASK-278, implementation row **C**. Rows A and B declared the store and filled
it while every reader still answered from `phase/<NNN>-linkage.md`; this row
moves the readers, and § 6 states the one hard ordering constraint it is here
to protect: **C before D**, because a writer pointing at a store the readers
have not moved to fails *silently* — the edge lands, every reader still
answers from the document, and `attribution` reports never-asked for a row
that was just linked.

**How every test here is built to be able to fail.** The store and the
document are seeded to DISAGREE: the store carries the edge under one KR, the
document under another. A reader that has been moved reports the store's
answer; a reader that has not reports the document's. So restoring any one of
the six call sites to `P.parse_linkage(<document>)` turns exactly the test
named for that site red, which is this row's acceptance — *"restore one moved
call site to the document and a named test fails"*. Two of them were run that
way before this file was committed, and `evidence/2026-09/TASK-278-result.md`
records what each printed.

A fixture whose two halves AGREE cannot do that. It is green with every reader
still on the document, green with every reader moved, and green with the
readers deleted — the shape `tests/live_state_expectations.py` exists to catch,
and the reason no assertion here is made against this repository's own state.

**The second class is the trap TASK-277 fell into and fixed.** Its mutation
round found that every test in its module checked an outcome on the happy
path, so no branch that exists for wrong input was ever reached: five separate
guards could each be deleted with the suite still green. The guards this row
adds are mostly about *absence and malformation* — a store that is not there,
a store that will not parse, a phase the store does not cover, a record whose
line this writer cannot read — and every one of them is reached by name in
`TestTheWrongInputBranchesAreReached`, which is where the deletions were tried.

Run: python3 tests/parallel test_linkage_store_readers
"""

from __future__ import annotations

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

    `kr_rows` is the KR table. It matters for site 5: the exclusion's whole
    purpose is to let a phase whose REGISTER declares nothing fall back to
    this table, and never to the register itself.
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


def document(*, phase: str, edges: dict[str, list[str]],
             unlinked: list[str] | None = None,
             krs: tuple[str, ...] = ("KR1", "KR2"),
             serves: str | None = None,
             agents: dict[str, list[str]] | None = None) -> str:
    """The register document, authored by hand.

    By hand and not through `perry-goals link` for the reason
    `tests/test_linkage_task_exists.py § register` gives: the file has to hold
    a state under test, and going through the writer would make the fixture a
    test of the writer. Here it matters twice over — the writer is site 1, one
    of the six things being measured.
    """
    number = phase.split("-")[0]
    body = [f'---\nlinkage: 1\nphase: "{phase}"',
            'updated: "2026-09-05T00:00:00Z"']
    body.append("unlinked: [" + ", ".join(
        f'"{t}"' for t in (unlinked or [])) + "]")
    if agents:
        # `agents[].tasks` — a register half the store has NO record kind for
        # (`schema/state-schema.json` declares three kinds and `agent` is not
        # one). It is therefore only ever a document reference, and a `purge`
        # that reads the store instead of the document stops seeing it for
        # every phase, not just the uncovered ones.
        body.append("agents:")
        for who, tids in agents.items():
            ids = ", ".join(f'"{t}"' for t in tids)
            body.append(f'  - id: "{who}"\n    tasks: [{ids}]')
    if serves:
        # The Project↔KR registry. It has no record kind in the store — there
        # are three and this is not one — so it stays in the document, and a
        # finding about it must name the document.
        body.append(f'projects:\n  - id: PRJ-1\n    serves: {serves}\n'
                    f'    objective: O1\n    name: "a project"')
    body.append("objectives:\n  - id: O1\n    title: \"an objective\"\n    krs:")
    for suffix in krs:
        kr_id = f"P{number}-O1-{suffix}"
        ids = ", ".join(f'"{t}"' for t in edges.get(kr_id, []))
        body.append(
            f"      - id: {kr_id}\n"
            f'        title: "the {suffix} result"\n'
            f'        metric: "the argument for {suffix}"\n'
            f"        target: 1\n        current: 1\n"
            f"        stretch: false\n        tasks: [{ids}]")
    return "\n".join(body) + "\n---\n\n# Linkage\n"


def store(*, phase: str, edges: dict[str, list[str]],
          unlinked: list[str] | None = None,
          krs: tuple[str, ...] = ("KR1", "KR2")) -> str:
    """`linkage.jsonl` — the three declared kinds, one JSON object per line."""
    number = phase.split("-")[0]
    lines = []
    for suffix in krs:
        lines.append(json.dumps({
            "kind": "kr", "phase": phase, "objective": "O1",
            "id": f"P{number}-O1-{suffix}",
            "title": f"the {suffix} result",
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


def task_record(tid: str, status: str = "in_progress") -> str:
    return json.dumps({
        "id": tid, "title": "a row", "owner": "Coding Agent",
        "status": status, "priority": "P0", "track": "main",
        "next_action": "carry on", "evidence": "", "verification": "V2",
        "created": "2026-09-01T09:00:00", "order": None,
    }, ensure_ascii=False)


class Fixture(unittest.TestCase):
    """A project whose store and document DISAGREE about one edge.

    The store puts `TASK-100` under `KR1`; the document puts it under `KR2`.
    Every assertion below names which of those two a reader reported, so the
    test says which file the reader read and not merely that it produced
    something.
    """

    STORE_KR = "P003-O1-KR1"
    DOC_KR = "P003-O1-KR2"

    def project(self, *, store_text: str | None = "default",
                doc_text: str | None = "default",
                tasks: tuple[str, ...] = ("TASK-100", "TASK-101"),
                store_unlinked: list[str] | None = None,
                doc_unlinked: list[str] | None = None,
                extra_phase: bool = False) -> pathlib.Path:
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
        if doc_text == "default":
            doc_text = document(phase="003-storage",
                                edges={self.DOC_KR: ["TASK-100"]},
                                unlinked=doc_unlinked)
        if doc_text is not None:
            (d / "phase" / "003-linkage.md").write_text(doc_text)
        if store_text == "default":
            store_text = store(phase="003-storage",
                               edges={self.STORE_KR: ["TASK-100"]},
                               unlinked=store_unlinked)
        if store_text is not None:
            (d / "linkage.jsonl").write_text(store_text)
        if extra_phase:
            # A phase the store does NOT declare a `kr` record for — the
            # condition `_linkage_records_for_phase` answers `None` to, and
            # the reason the sweep is per phase rather than store-wide.
            #
            # **The slug sorts AFTER `linkage`, and that is load-bearing.**
            # The exclusion under test filters `sorted(glob("002-*.md"))` and
            # the fallback takes `mine[0]`. With a slug like `earlier`, the
            # phase document sorts first and `mine[0]` is right whether the
            # exclusion runs or not — the mutation round caught exactly that:
            # deleting the exclusion left this suite green. `zeta` puts
            # `002-linkage.md` first, so removing the filter makes the
            # register its own comparand and the test can see it.
            (d / "phase" / "002-zeta.md").write_text(phase_file(
                "002", "zeta", "2026-08-01", "scored",
                "| P002-O1-KR1 | the KR1 result | 1 | — |\n"))
            (d / "phase" / "002-linkage.md").write_text(document(
                phase="002-zeta", edges={"P002-O1-KR1": ["TASK-101"]},
                krs=("KR1",)))
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
            [sys.executable, str(GOALS), *argv, "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, json.loads(proc.stdout or "{}")

    def purge(self, d: pathlib.Path, tid: str) -> tuple[int, dict]:
        proc = subprocess.run(
            [sys.executable, str(TASK), "purge", tid, "--reason",
             "a fixture row", "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, json.loads(proc.stdout or "{}")

    def rules(self, payload: dict, rule: str) -> list[dict]:
        return [f for f in payload["findings"] if f["rule"] == rule]


class TestTheSixReadersAnswerFromTheStore(Fixture):
    """One test per call site of `DESIGN-015 § 5.6`. **This is the gate.**

    Each asserts the STORE's answer and refutes the DOCUMENT's, so restoring
    that one call site to `parse_linkage(<document>)` turns this one test red
    and leaves the others alone. That is what makes a pass here evidence
    rather than a coincidence.
    """

    def test_site_6_perry_state_attribution_reads_the_store(self):
        """`viewer/parsers.py § load_snapshot` — what `perry-state`'s
        attribution reader is built on."""
        d = self.project()
        payload = self.state(d, "linkage")["linkage"]
        by_id = {k["id"]: k["tasks"]
                 for o in payload["objectives"] for k in o["krs"]}
        self.assertEqual(by_id[self.STORE_KR], ["TASK-100"],
                         "the store puts TASK-100 under KR1 and perry-state "
                         "did not report it there — this reader is still on "
                         "the document")
        self.assertEqual(by_id[self.DOC_KR], [],
                         "KR2 is where the DOCUMENT puts TASK-100; reporting "
                         "it there means the document was read")

    def test_site_6_keeps_the_documents_metric(self):
        """The other half of the split, and it is not decoration.

        `metric` is `derived_not_stored` in the schema — Decision 2 — so a
        reader that answered the typed half from the store and dropped the
        argument with it would satisfy the test above and still lose the one
        thing the document exists to hold.
        """
        d = self.project()
        payload = self.state(d, "linkage")["linkage"]
        metrics = {k["id"]: k["metric"]
                   for o in payload["objectives"] for k in o["krs"]}
        self.assertEqual(metrics[self.STORE_KR], "the argument for KR1")

    def test_site_2_perry_goals_krs_reads_the_store(self):
        """`bin/perry-goals § cmd_krs`."""
        d = self.project()
        code, out = self.goals(d, "krs")
        self.assertEqual(code, 0, out)
        by_id = {k["id"]: k["tasks"]
                 for o in out["objectives"] for k in o["krs"]}
        self.assertEqual(by_id[self.STORE_KR], ["TASK-100"])
        self.assertEqual(by_id[self.DOC_KR], [])

    def test_site_3_perry_task_names_the_store_and_its_line(self):
        """`bin/perry-task § live_references`, and the regex that is gone.

        The refusal quotes `linkage.jsonl:<line>`. A line number is only
        available because one record is one line — the property that let the
        regex be replaced by `json.loads` rather than by a second regex.

        **This test used to assert `003-linkage.md` was NOT named, and that
        assertion was the defect written down.** `live_references` is not a
        renderer choosing an authority — it is the refusal that stands between
        `perry-task purge` and a permanent deletion, and `purge` never
        re-issues the id. Requiring it to report the store *instead of* the
        document is what let a store covering phase 003 retire
        `phase/001-linkage.md`'s 18 edges as live references, so TASK-028,
        TASK-046 and TASK-087 stopped refusing (TASK-278 V4 review, FAIL 2).
        The guard now reads both and reports both.

        What that assertion was really protecting — that site 3 has MOVED to
        the store — is still measured, and by the same fixture: the store puts
        TASK-100 under `KR1` and the document puts it under `KR2`, so a reader
        still on the document names neither `linkage.jsonl:` nor `KR1`. The
        refutation is the KR id, which is stronger than the filename was.
        `test_site_3_a_register_the_store_does_not_cover_still_protects_a_row`
        is the other direction.
        """
        d = self.project(tasks=("TASK-100", "TASK-101"))
        subprocess.run(
            [sys.executable, str(TASK), "drop", "TASK-100", "--reason",
             "done with it", "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)
        code, out = self.purge(d, "TASK-100")
        self.assertEqual(code, 1, out)
        self.assertIn("linkage.jsonl:", out["refused"],
                      "the refusal must name the store and the line")
        self.assertIn(self.STORE_KR, out["refused"],
                      "the store puts TASK-100 under KR1; a refusal naming "
                      "only KR2 means this reader is still on the document")
        self.assertIn("003-linkage.md:", out["refused"],
                      "the document names TASK-100 too, and purging would "
                      "leave that reference dangling — a reference guard "
                      "reads BOTH authorities or it deletes live rows")

    def test_site_3_uses_no_regex_over_the_store(self):
        """The deliverable's own words: replaced by `json.loads`, **not by a
        second regex**.

        Asserted against the source, because the behaviour above cannot tell
        the two apart — a regex that happened to match would pass it. The
        window is the reader itself, so an unrelated `re` elsewhere in a
        7,900-line file cannot make this green or red by accident.

        **The window ends at the store scan, not at the end of the function,
        and the narrowing is the point of the rule rather than a relaxation
        of it.** DESIGN-015's claim is about `linkage.jsonl`: one JSON object
        per line is `json.loads`, so the regex that used to read the store is
        gone and was not replaced by a second regex. The register DOCUMENT did
        not become JSONL. It is still what the original comment called it —
        *"markdown with a YAML-shaped block in it, not a YAML document"* — and
        it is still read by line, because the refusal has to name the line a
        reader would go and edit. Ending the window at the whole function
        would forbid reading the document at all, which is FAIL 2.
        """
        text = (ROOT / "bin" / "perry-task").read_text()
        start = text.index("# `linkage.jsonl § kind: edge`")
        end = text.index("# **UNION, not an alternative", start)
        window = text[start:end]
        self.assertIn("json.loads", window)
        self.assertNotIn("re.match", window)
        self.assertNotIn("re.search", window)
        self.assertNotIn("re.findall", window)

    # -- the per-phase rule, at every seam that decides it (TASK-278 round 2)
    #
    # `linkage.jsonl` covers phase 003 ONLY — row B imported one phase — while
    # `phase/001-linkage.md` and `phase/002-linkage.md` still hold 16 KRs and
    # 31 edges between them. A reader that takes the store as authority
    # STORE-WIDE answers for phases the store says nothing about. The V4
    # review found that rule applied at one seam and missing at three, and
    # measured five mutations against it of which FOUR were green — including
    # applying the fix itself. These four tests are what those mutations had
    # nothing to hit. Each uses `extra_phase=True`: phase 002 has a register
    # document and NO `kr` record in the store, so the store is not the
    # authority for it and its own document is.

    def test_site_3_a_register_the_store_does_not_cover_still_protects_a_row(self):
        """**FAIL 2, and it was live irreversible data loss.**

        The document scan was an `else:` on "does the store exist", so the
        moment `linkage.jsonl` appeared, every register for a phase the store
        does not cover stopped counting as a live reference. `purge` deletes
        permanently and `mint_id` never re-issues the number: on this project
        TASK-028, TASK-046 and TASK-087 went from refused — each naming its
        exact register line — to deletable.

        TASK-101 here is named ONLY by `002-linkage.md`, a phase the store
        holds no record for. Restoring the `else:` makes this red.
        """
        d = self.project(extra_phase=True)
        subprocess.run(
            [sys.executable, str(TASK), "drop", "TASK-101", "--reason",
             "done with it", "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)
        code, out = self.purge(d, "TASK-101")
        self.assertEqual(code, 1,
                         "TASK-101 is named by 002-linkage.md, a phase the "
                         "store does not cover; purging it would leave that "
                         "register pointing at an id nothing resolves")
        self.assertIn("002-linkage.md:", out["refused"],
                      "the refusal must name the register FILE AND LINE a "
                      "reader would go and edit")
        self.assertIn("krs[].tasks", out["refused"])

    def test_the_filename_names_the_phase_when_the_document_does_not(self):
        """`linkage_document_phase`'s FIRST branch, on its own.

        The function asks the filename before the document's `phase:` field,
        and on every register this project has the two agree — so nulling the
        filename branch alone changed no answer anywhere and the mutation
        removing it came back GREEN. That is a hole, not an equivalence: the
        filename is the source that survives a register which does not declare
        `phase:` at all, and it is what `perry-goals` and `perry-state` build
        the path from in the first place.

        Here the document carries no `phase:` field. Scoped from the filename,
        phase 003 is in the store and the store answers (TASK-100 under
        `KR1`). With only the document's own field to go on there is no phase,
        nothing can be filtered to it, and the reader falls back to the
        document — which puts TASK-100 under `KR2`.
        """
        doc = document(phase="003-storage",
                       edges={self.DOC_KR: ["TASK-100"]})
        stripped = "\n".join(line for line in doc.split("\n")
                             if not line.startswith("phase:"))
        self.assertNotIn("\nphase:", stripped)
        d = self.project(doc_text=stripped)
        payload = self.state(d, "linkage")["linkage"]
        by_id = {k["id"]: k["tasks"]
                 for o in payload["objectives"] for k in o["krs"]}
        self.assertEqual(by_id.get(self.STORE_KR), ["TASK-100"],
                         "the filename says phase 003 and the store covers "
                         "it, so the store is the authority here")
        self.assertEqual(by_id.get(self.DOC_KR), [])

    def test_site_3_an_agents_tasks_entry_is_a_live_reference_and_says_so(self):
        """`agents[].tasks`, which the store has no record kind for at all.

        `schema/state-schema.json` declares three kinds — `kr`, `edge`,
        `unlinked` — and `agent` is not one. So this half of the register can
        only ever be a document reference, and reading the store INSTEAD of
        the document retired it for every phase, the covered one included:
        `phase/001-linkage.md` carries 16 such entries today and none of them
        was protecting a row any more.

        The label is asserted, not just the refusal, because reporting an
        agent assignment as `krs[].tasks` sends the reader to look for a key
        result that does not name the row.
        """
        d = self.project(doc_text=document(
            phase="003-storage",
            edges={self.DOC_KR: []},
            agents={"Coding Agent": ["TASK-101"]}))
        subprocess.run(
            [sys.executable, str(TASK), "drop", "TASK-101", "--reason",
             "done with it", "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)
        code, out = self.purge(d, "TASK-101")
        self.assertEqual(code, 1,
                         "an agent still has this row assigned; the store has "
                         "no record kind that could carry that fact")
        self.assertIn("agents[].tasks", out["refused"],
                      "reported as krs[].tasks, this sends the reader to a "
                      "key result that never named the row")
        self.assertIn("003-linkage.md:", out["refused"])

    def test_site_2_a_phase_the_store_does_not_cover_reads_its_own_document(self):
        """**FAIL 1 at site 2** — `perry-goals krs --phase <not the store's>`.

        `load_linkage` handed the WHOLE store to `linkage_from_store` with no
        filter for the phase `document_path` names, so on this project
        `krs --phase 001` printed phase 003's six KRs under phase 001's
        objective headings, above a line saying they were declared in
        `001-linkage.md`, and dropped all eight of 001's own KRs.

        Here phase 002's document declares `P002-O1-KR1` with TASK-101 and the
        store declares no phase 002 KR at all. Removing the phase filter makes
        this print `P003-O1-KR1` instead, and this test red.
        """
        d = self.project(extra_phase=True)
        code, out = self.goals(d, "krs", "--phase", "002")
        self.assertEqual(code, 0, out)
        by_id = {k["id"]: k["tasks"]
                 for o in out["objectives"] for k in o["krs"]}
        self.assertEqual(by_id.get("P002-O1-KR1"), ["TASK-101"],
                         "phase 002's own register declares this edge and the "
                         "store says nothing about phase 002")
        self.assertNotIn(self.STORE_KR, by_id,
                         "P003-O1-KR1 belongs to phase 003; printing it under "
                         "phase 002's objective headings is the store being "
                         "read store-wide instead of per phase")

    def test_site_6_a_phase_the_store_does_not_cover_reads_its_own_document(self):
        """**FAIL 1 at site 6** — the same root cause through `load_snapshot`.

        It hides today only because `phase/CURRENT` happens to name the one
        phase the store covers. It stops hiding the moment the next phase
        opens, which is why `CURRENT` is moved here rather than waited for.
        """
        d = self.project(extra_phase=True)
        (d / "phase" / "CURRENT").write_text("002-zeta\n")
        payload = self.state(d, "linkage")["linkage"]
        by_id = {k["id"]: k["tasks"]
                 for o in payload["objectives"] for k in o["krs"]}
        self.assertEqual(by_id.get("P002-O1-KR1"), ["TASK-101"])
        self.assertNotIn(self.STORE_KR, by_id,
                         "perry-state rendered phase 003's KRs under phase "
                         "002's document")

    def test_site_1_the_writer_reads_only_its_own_phases_records(self):
        """Site 1 — `linkage_graph`, the seam `link`'s refusals are made from.

        This site was already correct and had NO test: the V4 review's V10 and
        V11 both removed its per-phase rule and the suite stayed green. It now
        shares one spelling of the rule with `load_linkage`
        (`parsers.linkage_records_for_phase`), so this pins the shared helper
        from the writer's side too.

        `link`ing a row to a phase-002 KR must be judged against phase 002's
        register. Read store-wide, `P002-O1-KR1` is a KR the graph has never
        heard of and the refusal changes.

        **Driven through `perry-goals link`, not by calling the helper.** The
        first version of this test called `linkage_records_for_phase` directly
        and a mutation taking the whole store inside `linkage_graph` stayed
        GREEN — the helper was right and its one caller was not asked. `link`
        writes the CURRENT phase's register, so pointing `CURRENT` at phase
        002 is what puts `linkage_graph` on the phase the store does not
        cover.

        `TASK-101` is already under `P002-O1-KR1` in that document, so a
        correctly scoped graph answers "already linked" and writes nothing.
        Read store-wide, the graph carries phase 003's KRs instead, and
        `P002-O1-KR1` becomes a KR it "does not carry" — a refusal, and a
        different exit code.
        """
        d = self.project(extra_phase=True)
        (d / "phase" / "CURRENT").write_text("002-zeta\n")
        code, out = self.goals(d, "link", "TASK-101", "P002-O1-KR1",
                               "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("already", out,
                      "phase 002's own register already carries this edge; a "
                      "graph that cannot see it was read store-wide")
        self.assertIn("P002-O1-KR1", out["already"])

    def test_site_4_the_lint_check_grades_the_stores_edges(self):
        """`bin/perry-lint` — the linkage lint check, rewritten not deleted.

        The dangling edge is in the STORE only. A check still reading the
        document sees a graph whose every edge resolves and reports nothing.
        """
        d = self.project(store_text=store(
            phase="003-storage",
            edges={self.STORE_KR: ["TASK-100", "TASK-404"]}))
        found = self.rules(self.lint(d), "linkage-task-exists")
        self.assertEqual(len(found), 1, found)
        self.assertIn("TASK-404", found[0]["message"])
        self.assertEqual(found[0]["file"], "linkage.jsonl")

    def test_site_4_a_dangling_edge_in_the_document_alone_is_not_reported(self):
        """The refutation the test above needs to mean anything.

        The document names a task no row carries and the store does not. The
        store is the authority, so there is nothing to report — and a check
        still reading the document would report it. Without this case the
        test above passes with BOTH files being read.
        """
        d = self.project(doc_text=document(
            phase="003-storage",
            edges={self.DOC_KR: ["TASK-100", "TASK-404"]}))
        self.assertEqual(self.rules(self.lint(d), "linkage-task-exists"), [])

    def test_site_4_a_dangling_unlinked_declaration_comes_from_the_store(self):
        d = self.project(store_unlinked=["TASK-404"],
                         doc_unlinked=["TASK-101"])
        found = self.rules(self.lint(d), "linkage-unlinked-exists")
        self.assertEqual(len(found), 1, found)
        self.assertIn("TASK-404", found[0]["message"])
        self.assertEqual(found[0]["file"], "linkage.jsonl")

    def test_site_5_the_register_is_never_its_own_comparand(self):
        """`bin/perry-lint § _is_linkage_register` — the exclusion.

        A phase whose register declares no KR falls back to the phase
        DOCUMENT's table. Delete the exclusion and the glob's first match is
        `002-linkage.md` — the register grading itself, which proves only that
        a file agrees with itself. The register below names `P002-O1-KR9` in
        its own `projects[]`, so scraping it for KR ids makes that id look
        declared and the finding disappears.
        """
        d = self.project(extra_phase=True)
        # A register with no `krs[]` at all, and a Project serving a KR that
        # the phase document does NOT declare.
        (d / "phase" / "002-linkage.md").write_text(
            '---\nlinkage: 1\nphase: "002-zeta"\n'
            'updated: "2026-09-05T00:00:00Z"\n'
            "objectives: []\nprojects:\n  - id: PRJ-1\n"
            '    serves: P002-O1-KR9\n    objective: O1\n'
            '    name: "a project"\n---\n\n# Linkage\n')
        found = [f for f in self.rules(self.lint(d), "linkage-kr-exists")
                 if "PRJ-1" in f["message"]]
        self.assertEqual(len(found), 1, found)

    def test_a_projects_finding_names_the_document_and_not_the_store(self):
        """The other half of site 5, on a phase the store DOES cover.

        Split out because on a store-less phase `rel` and `doc_rel` are the
        same string, so filing the finding under the wrong one is invisible —
        the mutation round found exactly that, and this is the case that can
        see it. Phase 003 is graded from `linkage.jsonl`, but a `projects[]`
        entry has no record kind there, so a reader sent to the store would be
        sent to a file the entry is not in.
        """
        d = self.project(doc_text=document(
            phase="003-storage", edges={self.DOC_KR: ["TASK-100"]},
            serves="P003-O1-KR9"))
        found = [f for f in self.rules(self.lint(d), "linkage-kr-exists")
                 if "PRJ-1" in f["message"]]
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["file"], "phase/003-linkage.md",
                         "a projects[] finding must name the document that "
                         "carries the line, never the store")

    def test_site_1_link_refuses_on_what_the_store_says(self):
        """`bin/perry-goals § link` — the only writer today.

        The store says TASK-100 is under KR1. Linking it to KR2 must be
        refused NAMING KR1. A writer still judging from the document would
        see TASK-100 under KR2, call the request a no-op, and report
        `already` — an accepted write that contradicts every reader, which is
        the silent failure `DESIGN-015 § 6` orders C before D to prevent.
        """
        d = self.project()
        code, out = self.goals(d, "link", "TASK-100", self.DOC_KR)
        self.assertEqual(code, 1, out)
        self.assertIn(self.STORE_KR, out["refused"])

    def test_site_1_writes_the_edge_into_the_store(self):
        d = self.project()
        code, out = self.goals(d, "link", "TASK-101", self.DOC_KR)
        self.assertEqual(code, 0, out)
        records = [json.loads(line) for line
                   in (d / "linkage.jsonl").read_text().split("\n")
                   if line.strip()]
        edges = [r for r in records
                 if r["kind"] == "edge" and r["task"] == "TASK-101"]
        self.assertEqual(len(edges), 1, records)
        self.assertEqual(edges[0]["kr"], self.DOC_KR)
        self.assertEqual(edges[0]["via"], "link",
                         "`via` is what P003-O3-KR2 counts on; `add` is row D "
                         "and this path is not it")
        self.assertTrue(edges[0]["actor"],
                        "DESIGN-015 § 7's mitigation is that § 5.5's per-kind "
                        "rule be auditable off the records before anything "
                        "enforces it")

    def test_site_1_retracts_the_unlinked_record_it_supersedes(self):
        """A row cannot be attributed and declared drifting at once.

        The document write has applied this rule since TASK-227. The store
        half is new here, and it is the one place this writer removes a
        record rather than appending one.
        """
        d = self.project(store_unlinked=["TASK-101"],
                         doc_unlinked=["TASK-101"])
        code, out = self.goals(d, "link", "TASK-101", self.DOC_KR)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["store_records_retracted"], ["TASK-101"])
        records = [json.loads(line) for line
                   in (d / "linkage.jsonl").read_text().split("\n")
                   if line.strip()]
        self.assertEqual(
            [r for r in records
             if r["kind"] == "unlinked" and r["task"] == "TASK-101"], [])


class TestTheWrongInputBranchesAreReached(Fixture):
    """The guards that exist for absence and malformation, each reached.

    **TASK-277's finding, applied forward.** Its round found one shape of
    defect five times over: every test in its module asserted an outcome on
    the happy path, so no branch written for wrong input was ever executed,
    and five guards could each be deleted with the suite still green. The
    branches this row adds are almost all of that kind, so they get a class of
    their own rather than a happy-path assertion each.
    """

    def test_an_absent_store_is_not_an_empty_one(self):
        """`load_linkage_store` answers `None`, and the document stays the
        authority. Reading absence as `[]` would report "no edges anywhere"
        for every Perry project older than DESIGN-015."""
        d = self.project(store_text=None)
        self.assertIsNone(P.load_linkage_store(d))
        by_id = {k["id"]: k["tasks"] for o in
                 self.state(d, "linkage")["linkage"]["objectives"]
                 for k in o["krs"]}
        self.assertEqual(by_id[self.DOC_KR], ["TASK-100"],
                         "with no store the document is the authority")

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
                          "kr": "not-a-kr-id",
                          "declared_at": "2026-09-05T00:00:00Z",
                          "actor": "goals", "via": "link"}) + "\n")
        found = self.rules(self.lint(d), "linkage-store-malformed")
        self.assertEqual(len(found), 1, found)
        self.assertIn("not-a-kr-id", found[0]["message"])

    def test_a_phase_the_store_does_not_declare_keeps_its_document(self):
        """`_linkage_records_for_phase` answers `None`, not `[]`.

        Measured on this project and the reason the sweep is per phase: row B
        imported phase 003 only, and phases 001 and 002 still carry 16 KRs
        and 12 edge lists. A store-wide sweep would stop checking them and
        report nothing, which is not a clean sweep but an unrun one.
        """
        d = self.project(extra_phase=True)
        (d / "phase" / "002-linkage.md").write_text(document(
            phase="002-earlier", edges={"P002-O1-KR1": ["TASK-404"]},
            krs=("KR1",)))
        found = self.rules(self.lint(d), "linkage-task-exists")
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["file"], "phase/002-linkage.md",
                         "phase 002 is not in the store, so its own document "
                         "is still graded and still named")

    def test_a_document_that_will_not_parse_is_still_a_failure(self):
        """Even with a sound store. `metric`, `due` and the objective titles
        come from the document, so a graph composed over an unreadable one
        renders KR rows whose argument column is silently blank."""
        d = self.project(doc_text="---\nlinkage: 9\n---\n\n# Linkage\n")
        code, out = self.goals(d, "krs")
        self.assertEqual(code, 1, out)
        self.assertIn("refused", out)

    def test_a_kr_the_document_has_no_objective_for_is_kept(self):
        """Titleless, never dropped.

        A KR that exists in the authority and vanishes from the render is the
        silent loss this store was built to end, and it is the state a phase
        is in between `plan-phase` writing the store and anyone writing the
        objective's title.
        """
        doc = P.parse_linkage(document(phase="003-storage", edges={}))
        recs = json.loads('[' + ','.join(
            store(phase="003-storage", edges={}).strip().split("\n")) + ']')
        recs.append({"kind": "kr", "phase": "003-storage", "objective": "O9",
                     "id": "P003-O9-KR1", "title": "an orphan"})
        graph = P.linkage_from_store(recs, doc)
        self.assertIn("O9", [o.id for o in graph.objectives])
        self.assertEqual([o.title for o in graph.objectives if o.id == "O9"],
                         [""])

    def test_link_on_a_store_less_project_creates_no_store(self):
        """`linkage_store_text` answers `None`, and `None` is not `""`.

        Writing an empty store here would create `linkage.jsonl` on a project
        that has never had one — and every reader moved in this row treats a
        present store as the authority, so the next command would answer "no
        edges, anywhere" for a project whose register is full.
        """
        d = self.project(store_text=None)
        code, out = self.goals(d, "link", "TASK-101", self.DOC_KR)
        self.assertEqual(code, 0, out)
        self.assertFalse((d / "linkage.jsonl").exists())
        self.assertNotIn("store_records_written", out)

    def test_a_line_the_writer_cannot_read_survives_the_write(self):
        """Kept, never dropped.

        `perry-lint` reports an unreadable line by number; discarding it here
        would make this writer the thing that lost a record nobody had looked
        at yet.

        **This test asserted the retraction path and never reached it.** The
        mutation round found it: dropping the line in `linkage_store_text`'s
        `except json.JSONDecodeError` branch left the suite green, because a
        store with one unparseable line makes `load_linkage_store` answer
        `None` for the WHOLE store, so `reg.graph` falls back to the document,
        no retraction is ever requested, and the branch is not entered. What
        is reachable — and what this now asserts — is the append: the write
        still lands, and the line this writer could not read is still in the
        file afterwards.
        """
        d = self.project()
        with (d / "linkage.jsonl").open("a") as fh:
            fh.write("{ not json\n")
        code, out = self.goals(d, "link", "TASK-101", self.DOC_KR)
        self.assertEqual(code, 0, out)
        after = (d / "linkage.jsonl").read_text().split("\n")
        self.assertIn("{ not json", after)
        self.assertTrue(
            any('"TASK-101"' in line for line in after),
            "the fixture is not exercising the case: the store was never "
            "rewritten, so keeping the line proves nothing")


class TestTheDriftVerdictIsReal(Fixture):
    """`perry-lint`'s seventh census line stops saying "comparison incomplete".

    Before this row it read *"121 valid record(s), comparison incomplete —
    drift is unchecked, not clean"*, because the readers still answered from
    the document and a store nothing reads has no second opinion to check. The
    three states below are the three answers that line can now give, and the
    third is why `comparison_performed` is driven by the count of registers
    actually compared rather than by "the store parsed".
    """

    def stats(self, d: pathlib.Path) -> dict:
        return self.lint(d)["linkage_store_drift"]

    def test_agreement_is_a_verdict_and_not_a_deferral(self):
        edges = {self.STORE_KR: ["TASK-100"]}
        d = self.project(store_text=store(phase="003-storage", edges=edges),
                         doc_text=document(phase="003-storage", edges=edges))
        got = self.stats(d)
        self.assertTrue(got["comparison_performed"])
        self.assertEqual(got["drifted"], 0)
        self.assertEqual(self.rules(self.lint(d), "linkage-store-drift"), [])

    def test_a_disagreement_is_counted_and_named(self):
        d = self.project()          # store KR1, document KR2
        got = self.stats(d)
        self.assertTrue(got["comparison_performed"])
        self.assertEqual(got["drifted"], 2,
                         "both KRs disagree: one gained the edge, one lost it")
        found = self.rules(self.lint(d), "linkage-store-drift")
        self.assertTrue(found)
        self.assertTrue(all(f["file"] == "linkage.jsonl" for f in found))

    def test_nothing_to_compare_against_stays_unchecked_not_clean(self):
        """`P003-O1-KR3`'s rule, reaching the seventh store.

        A store whose phases have no register document beside them has nothing
        to compare. `0 drifted` would then mean "I did not look", which is the
        green gate on a false premise that rule exists to refuse.
        """
        d = self.project(doc_text=None)
        got = self.stats(d)
        self.assertTrue(got["store_present"])
        self.assertFalse(got["comparison_performed"])
        self.assertEqual(got["drifted"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
