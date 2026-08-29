"""`perry-lint` reports a linkage edge naming a task the store does not carry.

`phase/<NNN>-linkage.md` hangs task ids off `objectives[].krs[].tasks`, and
four `linkage-*` codes shipped before this one: `linkage-kr-exists` proves the
KR half of an edge, `linkage-task-single-kr` proves a task is not claimed
twice, `linkage-objective-agrees` and `linkage-names-unique` police the Project
registry. **Nothing proved the task half of an edge pointed at anything.**

It is load-bearing: `viewer/parsers.py § kr_for_task` is the reverse index, and
`bin/lib § kr_progress_provenance` folds `krs[].tasks` into a KR's
`linked_task_completion` — an id no row carries lands in `total` and is filed
`unknown`, which is a denominator nothing can ever close.

**Every case here is built in a temp project.** Zero edges dangle in this
repository, so "perry-lint finds nothing on Perry" is green with the guard
deleted and worth nothing — the class `tests/live_state_expectations.py`
exists to catch. The failing case has to be constructed, and it is read back
through the real `--root` seam, one subprocess per case.

Three decisions are pinned here as much as the behaviour:

1. **`warn`, not `error`** — `TestItIsWarnAndNotARefusal`. Same severity as
   `linkage-kr-exists`, which is the same statement one edge over.
2. **No store means the sweep does not run** — `TestNoStoreIsSilent`. A project
   with no `tasks.jsonl` has not been adopted (`viewer/parsers.py §
   load_task_store`: "`None` is not 'no tasks'"), and reading absence as "every
   edge dangles" is TASK-117's inversion, which called 175 of 175 rows drifted
   because the event log was missing. The N-versus-zero assertion is the point.
3. **An old phase's register IS judged against today's store** —
   `TestAnOldPhaseIsJudgedAgainstTodaysStore`. `bin/perry-lint`'s comment about
   a linkage file belonging to its own phase does NOT transfer: a KR id is
   scoped to a phase file, so `001-linkage.md` had to be judged against phase
   001's KRs; a task id is global and there is exactly one store, so there is
   no per-phase comparand to prefer.

Two things the spec for this row got wrong, both followed the code instead:
`perry-goals link` DOES write an edge to an id no row carries
(`TestTheShippedWriterCanProduceThisState`), and `perry-lint` is not the only
tool that notices a dangling id — `perry-diagnose`'s `user_load.dangling`
notices some of them, by a different and wronger route
(`test_a_closed_row_that_has_left_the_board_still_counts_as_present`).

Run: python3 tests/parallel test_linkage_task_exists
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
LINT = ROOT / "bin" / "perry-lint"


def phase_file(number: str, title: str, started: str, status: str) -> str:
    """A phase file complete enough to lint clean.

    Written out in full rather than trimmed to the two lines this suite reads,
    because the assertions below turn on the fixture having **zero** errors:
    `--strict` promoting a warning to a red process is only observable on a
    project that was not already red, and "the finding did not refuse the
    lint" is only observable where something else was not refusing it first.
    """
    return (
        f"# Phase #{number} — {title}\n\n"
        f"> **Started**: {started}\n> **Status**: {status}\n\n"
        f"## Phase Focus\n\nOne KR, so the register has something to name.\n\n"
        f"## Operating Rules\n\n- Agent autonomy: none.\n\n"
        f"## Cost Ceiling (phase #{number})\n\n- Spend cap: ≤ $0.\n\n"
        f"## User Commitments\n\n- None.\n\n"
        f"## User-Unavailable Degradation\n\nNone.\n\n"
        f"## Phase Scope Reduction Rule\n\n- **Phase-day trigger**: none.\n\n"
        f"## Objective 1 — {title}\n\n### Key Results\n\n"
        f"| Id | KR text | Metric / Target | Linked overall KR |\n"
        f"|---|---|---|---|\n| P{number}-O1-KR1 | {title} work | 1 | — |\n\n"
        f"## Definition of Done\n\n### Must-Have (failure = phase missed)\n\n"
        f"- [ ] The KR above is met\n\n"
        f"## Not Doing in this phase\n\n- Anything else.\n\n"
        f"## Process Note\n\nRead, never worked.\n"
    )


BOARD = (
    "# Board — linkage fixture\n\n> Live working memory.\n>\n"
    "> Last updated: 2026-08-20\n\n"
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

CONFIG = (
    "# Perry configuration\n\n"
    "- Document language: English\n"
    "- Repo layout: single\n"
    "- State root: .\n"
)

HOOK = (
    "# Perry hook\n\n## High-stakes operations\n\n"
    "- Anything that writes outside this fixture\n"
)


def register(tasks: list[str], own_phase: str,
             kr: str = "P{phase}-O1-KR1") -> str:
    """A linkage register, authored by hand.

    Written directly rather than through `perry-goals link` for the reason
    TASK-163's fixture writes its `BOARD.md` by hand: the file has to hold a
    state under test, and going through a writer would make the fixture a test
    of the writer. (`link` does in fact append this edge — measured, see
    `TestTheShippedWriterCanProduceThisState` — but a fixture that depended on
    that is a fixture that breaks the day the writer is fixed.)
    """
    ids = ", ".join(f'"{t}"' for t in tasks)
    return (
        f'---\nlinkage: 1\nphase: "{own_phase}"\n'
        f'updated: "2026-08-20T00:00:00Z"\nobjectives:\n  - id: O1\n'
        f'    title: "a"\n    krs:\n      - id: {kr}\n'
        f'        title: "work"\n        metric: "1"\n        target: 1\n'
        f'        current: 1\n        stretch: false\n'
        f'        tasks: [{ids}]\n---\n\n# Linkage\n'
    )


def record(tid: str) -> str:
    return json.dumps({
        "id": tid, "title": "a row", "owner": "Coding Agent",
        "status": "in_progress", "priority": "P1", "track": "main",
        "next_action": "carry on", "evidence": "", "verification": "V2",
        "created": "2026-08-01T09:00:00", "order": None,
    }, ensure_ascii=False)


class Fixture(unittest.TestCase):
    """A two-phase project: 001 scored, 002 active, one register per phase."""

    def project(self, *, current: str = "002-new",
                store: list[str] | None = ("TASK-100", "TASK-101"),
                linkage: dict[str, list[str]] | None = None,
                store_text: str | None = None,
                kr: str = "P{phase}-O1-KR1") -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-linkage-task-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / "phase").mkdir()
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text(CONFIG)
        (d / ".perry" / "hook.md").write_text(HOOK)
        (d / "BOARD.md").write_text(BOARD)
        (d / "phase" / "CURRENT").write_text(current + "\n")
        (d / "phase" / "001-old.md").write_text(
            phase_file("001", "old", "2026-08-01", "scored"))
        (d / "phase" / "002-new.md").write_text(
            phase_file("002", "new", "2026-08-19", "active"))
        for name, tasks in (linkage or {"002": ["TASK-100"]}).items():
            # `{phase}` is filled from the register's OWN phase. One
            # literal used to serve both registers; a phase-KR id now names
            # its phase, so a fixture that shared one across two phases
            # would be writing an edge to the other phase's KR.
            (d / "phase" / f"{name}-linkage.md").write_text(
                register(tasks, {"001": "001-old"}.get(name, "002-new"),
                         kr=kr.format(phase=name)))
        if store_text is not None:
            (d / "tasks.jsonl").write_text(store_text)
        elif store is not None:
            (d / "tasks.jsonl").write_text(
                "".join(record(t) + "\n" for t in store))
        return d

    def lint(self, d: pathlib.Path, *extra) -> tuple[int, dict]:
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(d), "--json", *extra],
            capture_output=True, text=True, cwd=ROOT)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        f"perry-lint printed no payload: "
                        f"{proc.stdout[-300:]}{proc.stderr[-400:]}")
        return proc.returncode, json.loads(proc.stdout)

    def dangling(self, payload: dict) -> list[dict]:
        return [f for f in payload["findings"]
                if f["rule"] == "linkage-task-exists"]

    def rules(self, payload: dict) -> list[str]:
        return [f["rule"] for f in payload["findings"]]


class TestADanglingEdgeIsReported(Fixture):
    def test_one_absent_id_yields_exactly_one_finding(self):
        d = self.project(linkage={"002": ["TASK-100", "TASK-404"]})
        _, payload = self.lint(d)
        rows = self.dangling(payload)
        self.assertEqual(len(rows), 1, rows)
        self.assertIn("TASK-404", rows[0]["message"])
        self.assertIn("P002-O1-KR1", rows[0]["message"],
                      "the finding does not name the KR the edge hangs on")
        self.assertEqual(rows[0]["file"], "phase/002-linkage.md")

    def test_the_id_that_resolves_is_not_reported(self):
        """The other half of the assertion above, stated on its own: a
        register whose every edge resolves is silent, on the same project
        shape that produces the finding one method up."""
        d = self.project(linkage={"002": ["TASK-100", "TASK-101"]})
        _, payload = self.lint(d)
        self.assertEqual(self.dangling(payload), [])

    def test_each_dangling_edge_is_named_once(self):
        d = self.project(linkage={"002": ["TASK-404", "TASK-405"]})
        _, payload = self.lint(d)
        rows = self.dangling(payload)
        self.assertEqual(len(rows), 2, rows)
        self.assertEqual(
            sorted(t for r in rows for t in ("TASK-404", "TASK-405")
                   if t in r["message"]),
            ["TASK-404", "TASK-405"])

    def test_a_closed_row_that_has_left_the_board_still_counts_as_present(self):
        """The comparand is the STORE, and this is the case that decides it.

        Under ADR-007 a closed row leaves `BOARD.md` and stays in
        `tasks.jsonl` — `viewer/parsers.py § _records_by_group` skips a
        terminal status, `bin/lib § task_status_index` is the note that says
        so. A guard that resolved ids against the board's rendered rows would
        therefore report **every finished task any register names** as
        dangling, on every project, forever.

        Not hypothetical: `perry-diagnose`'s `user_load.dangling` asks the
        markdown-mention question rather than the store question, and on this
        exact fixture it answers `['TASK-100']` for a row whose record is
        right there in the store. Measured 2026-08-28. That is a defect of
        that check, reported separately; it is recorded here because it is the
        answer this guard must NOT give, and because it is the reason "some
        other tool already notices dangling ids" is not a reason to skip this
        one.
        """
        d = self.project(store=["TASK-100", "TASK-101"],
                         linkage={"002": ["TASK-100"]})
        (d / "BOARD.md").write_text((d / "BOARD.md").read_text().replace(
            "| TASK-100 | a row | Coding Agent | in_progress | carry on | — |\n",
            ""))
        (d / "tasks.jsonl").write_text(
            record("TASK-100").replace('"in_progress"', '"done"') + "\n"
            + record("TASK-101") + "\n")
        _, payload = self.lint(d)
        self.assertEqual(self.dangling(payload), [])


class TestItIsWarnAndNotARefusal(Fixture):
    """Decision 1 — severity.

    `linkage-kr-exists` is `warn` and this is the same statement about the
    other half of the same edge; making one an `error` would say the KR half
    of an edge matters more than the half `kr_progress_provenance` actually
    counts. And an `error` in this tool is a claim that a FILE is malformed:
    the register is well-formed here, its referent is absent, and a referent
    can be absent for a benign and recoverable reason — an id typed for a row
    that has not been opened yet is a real Monday. `--strict` is the control a
    project uses to make advisory findings red, and it still works.
    """

    def test_the_finding_does_not_refuse_the_lint(self):
        rc, payload = self.lint(self.project(
            linkage={"002": ["TASK-404"]}))
        rows = self.dangling(payload)
        self.assertTrue(rows)
        self.assertTrue(all(r["severity"] == "warn" for r in rows), rows)
        self.assertEqual(rc, 0, "a dangling edge refused the whole lint")

    def test_strict_promotes_it(self):
        d = self.project(linkage={"002": ["TASK-404"]})
        self.assertEqual(self.lint(d, "--strict")[0], 1)

    def test_the_schema_registers_the_code_at_the_same_severity(self):
        """The finding registry and the emitter must agree, or the page that
        tells a reader what a code means describes a tool that does not
        exist."""
        schema = json.loads(
            (ROOT / "schema" / "state-schema.json").read_text())
        entry = next(r for r in schema["cross_file"]
                     if r["id"] == "linkage-task-exists")
        self.assertEqual(entry["severity"], "warn")
        _, payload = self.lint(self.project(linkage={"002": ["TASK-404"]}))
        self.assertEqual(self.dangling(payload)[0]["severity"],
                         entry["severity"])


class TestNoStoreIsSilent(Fixture):
    """Decision 2 — what "the task store" means when there is not one.

    TASK-117's inversion, one check over: `check_store_drift` reported 175 of
    175 rows drifted when the only thing missing was the event log. Absence of
    the thing you compare against is not universal failure; it is a question
    that was never asked. `viewer/parsers.py § load_task_store` already answers
    it — `None` is "not adopted", `[]` is "adopted and empty" — so the guard
    reads that contract instead of inventing a second one.

    The N-versus-zero pair is what makes this test worth having: the same two
    edges that yield two findings with a store yield **zero** without one.
    """

    def test_a_project_with_no_store_reports_nothing(self):
        d = self.project(store=None,
                         linkage={"002": ["TASK-404", "TASK-405"]})
        self.assertFalse((d / "tasks.jsonl").exists())
        _, payload = self.lint(d)
        self.assertEqual(self.dangling(payload), [])

    def test_the_same_edges_do_yield_findings_once_a_store_exists(self):
        """Not-N and N, on one project, so "silent" cannot be silence about
        everything."""
        d = self.project(store=None,
                         linkage={"002": ["TASK-404", "TASK-405"]})
        self.assertEqual(len(self.dangling(self.lint(d)[1])), 0)
        (d / "tasks.jsonl").write_text(record("TASK-100") + "\n")
        self.assertEqual(len(self.dangling(self.lint(d)[1])), 2)

    def test_the_rest_of_the_linkage_sweep_still_runs_without_a_store(self):
        """Silence about this one question, not a linkage sweep that stopped.

        The same file, in the same run, is still judged on its KR half: the
        register names a KR its phase does not carry, and `linkage-kr-exists`
        reports it while `linkage-task-exists` declines. Without this the
        no-store case could be passing because the loop never reached the
        file at all.
        """
        d = self.project(store=None, linkage={"002": ["TASK-404"]},
                         kr="P{phase}-O9-KR9")
        _, payload = self.lint(d)
        self.assertEqual(self.dangling(payload), [])
        self.assertIn("linkage-kr-exists", self.rules(payload))

    def test_an_unreadable_store_is_the_same_answer(self):
        """`load_task_store` returns `None` for a store it cannot parse, and
        that is the right answer here too: `check_store_drift` already reports
        `store-unreadable`, and a second check deriving "and all your edges
        dangle" from that one fact is the noise-that-restates-one-flag failure
        `perry-state § reconcile_drift` names."""
        d = self.project(store_text="{not json\n",
                         linkage={"002": ["TASK-404", "TASK-405"]})
        _, payload = self.lint(d)
        self.assertEqual(self.dangling(payload), [])
        self.assertIn("store-unreadable", self.rules(payload),
                      "nothing told the user why the store was skipped")

    def test_an_empty_store_is_not_the_same_answer(self):
        """The boundary the decision turns on. An empty `tasks.jsonl` is an
        adopted project with an empty board — `[]`, not `None` — and a
        register naming a task there really is pointing at nothing."""
        d = self.project(store_text="", linkage={"002": ["TASK-404"]})
        _, payload = self.lint(d)
        self.assertEqual(len(self.dangling(payload)), 1)


class TestAnOldPhaseIsJudgedAgainstTodaysStore(Fixture):
    """Decision 3 — and the answer is the opposite of `linkage-kr-exists`'s.

    `bin/perry-lint`'s comment (the one `tests/test_cadence.py §
    TestLinkageBelongsToItsOwnPhase` was written for) says a linkage file
    belongs to ITS phase: judging `001-linkage.md` against the CURRENT phase's
    KR set reported correct edges as dangling on this project's first rollover.

    That reasoning does not transfer. A **KR id was phase-scoped without
    saying so** — `P-O1.1` [[old-form]] named a different key result in phase
    001 and phase 002, which is precisely why the comparand had to be
    re-derived per file. TASK-180 put the phase in the id (`P001-O1-KR1` vs
    `P002-O1-KR1`), and the old pair is quoted here rather than migrated
    because migrated it stops being an example of anything. The guard is
    unchanged and still earns its place: a register may name a KR belonging
    to a phase that is not its own, and that is now a visible error rather
    than an invisible coincidence. A **task id is global**:
    one `tasks.jsonl` for the project, ids minted across phases and never
    re-used, and no per-phase task store exists to prefer. So today's store is
    not "the current phase leaking into an old file" — it is the only store
    there has ever been, and an old register's edge to a row TASK-167's removal
    path took out is dangling, correctly.
    """

    def test_a_scored_phases_edge_to_a_live_row_is_not_reported(self):
        d = self.project(current="002-new",
                         linkage={"001": ["TASK-100"], "002": ["TASK-101"]})
        _, payload = self.lint(d)
        self.assertEqual(self.dangling(payload), [])
        self.assertNotIn("linkage-kr-exists", self.rules(payload),
                         "the sibling KR guard regressed")

    def test_a_scored_phases_edge_to_a_removed_row_is_reported(self):
        d = self.project(store=["TASK-101"],
                         linkage={"001": ["TASK-100"], "002": ["TASK-101"]})
        _, payload = self.lint(d)
        rows = self.dangling(payload)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(rows[0]["file"], "phase/001-linkage.md")
        self.assertIn("TASK-100", rows[0]["message"])

    def test_the_rationale_says_why_the_kr_comment_does_not_transfer(self):
        """The comment at the guard is the whole answer to decision 3, and a
        reader who deletes it will re-derive the wrong one — `test_cadence`'s
        precedent is right there and looks like it applies."""
        source = LINT.read_text()
        # The anchor moved with TASK-157: the KR guard used to report "{kr.id}
        # is in the graph but not in the current phase file" and now reports
        # the objective disagreement, because the phase document no longer
        # declares KRs to be absent from. The rationale it guards is unchanged.
        start = source.index('f"{kr.id} names objective {declared_under} and is "')
        rationale = source[start:source.index('"linkage-task-exists"', start)]
        self.assertIn("A task id is global", rationale)
        self.assertIn("does NOT transfer", rationale)


class TestTheShippedWriterCanProduceThisState(Fixture):
    """The case is reachable through `perry-goals link`, not only by hand.

    TASK-156's spec says the opposite — "the case cannot be produced by any
    writer — `perry-goals link` presumably will not write an edge to a row it
    cannot resolve" — and the code disagrees. `link_edge` resolves and
    validates the **KR** half of the pair (`resolve_target`, then a second
    check that the graph carries that KR) and asks nothing at all about the
    task id: `link TASK-999 P002-O1-KR1` on a store holding neither returns
    0,
    appends the edge, bumps `updated`, and signs off with `↪ validate:
    perry-lint --root .` — which, before this row, had nothing to say about it.

    So this is not a hand-authored-only defect and the guard is not only a
    backstop for TASK-167's removal path. The fixture cases above stay
    hand-authored anyway, for TASK-163's reason: a fixture that goes through a
    writer is testing the writer.

    **If this test ever skips**, `perry-goals link` grew the check it does not
    have today; that is a good change, and the right follow-up is to turn this
    into an assertion that the refusal names the id it could not resolve.
    """

    def test_link_writes_the_edge_and_the_lint_then_reports_it(self):
        d = self.project(linkage={"002": ["TASK-100"]})
        (d / ".perry" / "config.md").write_text(
            CONFIG + "- Conformance gate: advisory\n")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-goals"), "link",
             "TASK-999", "P002-O1-KR1", "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)
        if proc.returncode != 0:
            self.skipTest(f"perry-goals link now refuses an unresolvable "
                          f"task id: {proc.stdout.strip()[-200:]}")
        self.assertIn(
            "TASK-999", (d / "phase" / "002-linkage.md").read_text(),
            "link reported success and wrote no edge")
        rows = self.dangling(self.lint(d)[1])
        self.assertEqual(len(rows), 1, rows)
        self.assertIn("TASK-999", rows[0]["message"])


if __name__ == "__main__":
    unittest.main()
