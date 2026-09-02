"""Task-writer contract tests, split for module-level parallelism."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from task_writer_support import (
    BASIC_MODE_TRACKS, BOARD, MODE_TRACKS, PERRY_HOME, PT, Project,
    ROUND_TRIP_BOARD, ROUND_TRIP_ROW_IDS, ROUND_TRIP_ROW_PRIORITIES, TASKS,
    TOOL, ZH_BOARD, mode_cells,
)

class TestFullTaskSet(unittest.TestCase):
    """`list --all` — the question a front-end must answer and BOARD.md cannot.

    The board holds open work only; closed rows leave it. Until this, the full
    set existed solely as a reconstruction from date-sharded journal prose — a
    reader would have to parse every file in every month and rebuild each task's
    timeline. One call replaces that, which is what lets a consumer stay
    ignorant of Perry's file formats.
    """

    def test_closed_tasks_are_reconstructed_from_events(self):
        p = Project()
        _, a = p.run("add", "--title", "will close")
        _, b = p.run("add", "--title", "stays open")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        _, out = p.run("list", "--all")
        ids = {t["id"]: t for t in out["tasks"]}
        self.assertIn(a["id"], ids, "a closed task vanished from the full set")
        self.assertFalse(ids[a["id"]]["open"])
        self.assertTrue(ids[b["id"]]["open"])
        self.assertEqual(out["open"], 1)
        self.assertEqual(out["closed"], 1)

    def test_a_closed_task_keeps_its_title_and_evidence(self):
        """A bare id is what `reference/user-load.md` forbids handing a reader.
        The event log has to carry enough to name what it is talking about."""
        p = Project()
        _, a = p.run("add", "--title", "the flake detector")
        p.run("done", a["id"], "--evidence", "evidence/x.md", "--rung", "V3")
        _, out = p.run("list", "--all")
        t = next(x for x in out["tasks"] if x["id"] == a["id"])
        self.assertEqual(t["title"], "the flake detector")
        self.assertEqual(t["evidence"], "evidence/x.md")
        self.assertEqual(t["verification"], "V3")

    def test_without_all_only_open_tasks_are_returned(self):
        p = Project()
        _, a = p.run("add", "--title", "closes")
        p.run("done", a["id"], "--evidence", "e.md")
        _, out = p.run("list")
        self.assertEqual([t["id"] for t in out["tasks"] if not t["open"]], [])

    def test_every_task_carries_its_timeline(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        p.run("start", a["id"])
        p.run("done", a["id"], "--evidence", "e.md")
        _, out = p.run("list", "--all")
        t = next(x for x in out["tasks"] if x["id"] == a["id"])
        self.assertEqual([e["event"] for e in t["timeline"]],
                         ["add", "start", "done"])

    def test_an_event_without_a_store_record_is_not_a_task(self):
        """The event stream supplies history, never current task identity."""
        p = Project()
        (p.root / ".perry" / "events.jsonl").write_text(
            json.dumps({"ts": "2026-01-01T00:00:00", "event": "done",
                        "id": "TASK-900", "to": "done"}) + "\n")
        _, out = p.run("list", "--all")
        self.assertNotIn("TASK-900", out["untitled"])
        self.assertNotIn("TASK-900", {task["id"] for task in out["tasks"]})

    def test_the_live_board_wins_over_the_event_stream(self):
        """A row still on the board is the truth; events are derived. If they
        disagree, the markdown is canonical — §5.3."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        p.run("start", a["id"])
        _, out = p.run("list", "--all")
        t = next(x for x in out["tasks"] if x["id"] == a["id"])
        self.assertTrue(t["open"])
        self.assertEqual(t["status"], "in_progress")


class TestPerryStateReadsTheLog(unittest.TestCase):
    def _state(self, root: Path) -> dict:
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(root), "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)

    def test_the_events_block_reports_the_log(self):
        p = Project()
        p.run("add", "--title", "X")
        ev = self._state(p.root)["board"]["events"]
        self.assertTrue(ev["present"])
        self.assertEqual(ev["total"], 1)
        self.assertEqual(ev["by_event"], {"add": 1})

    def test_no_log_is_zeroes_not_an_error(self):
        """A pre-DESIGN-004 project has no log and must not be reported as
        broken for it."""
        p = Project()
        ev = self._state(p.root)["board"]["events"]
        self.assertFalse(ev["present"])
        self.assertEqual(ev["total"], 0)

    def test_a_corrupt_line_does_not_lose_the_rest(self):
        p = Project()
        p.run("add", "--title", "X")
        log = p.root / ".perry" / "events.jsonl"
        log.write_text(log.read_text() + "{ not json\n" +
                       json.dumps({"ts": "2026-01-01T00:00:00", "event": "start",
                                   "id": "TASK-001"}) + "\n")
        ev = self._state(p.root)["board"]["events"]
        self.assertEqual(ev["total"], 2, "a corrupt line took a valid one with it")


class TestDriftReconciliation(unittest.TestCase):
    """DESIGN-004 §5.4 — the check that makes the tool worth building.

    Without it, `perry-task` is a convenience and the discipline problem is
    untouched: §3 says so outright. This is where that claim is made good or
    exposed as another unbacked assertion.

    The implementation corrects the spec's wording in one place. A board row
    with no creating event is NOT drift — it could be a hand-edit, or it could
    simply predate the tool, and nothing on a row distinguishes them. Perry's
    own board had 29 such rows the day `perry-task` shipped. Reporting those as
    drift would make the first standup after every upgrade a wall of noise about
    work done correctly under the old rules, and a check people learn to ignore
    is worse than no check. So `unrecorded` is context and `drift` counts only
    the two unambiguous conditions.
    """

    def _drift(self, p: "Project") -> dict:
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)["board"]["drift"]

    def test_a_board_the_tool_wrote_entirely_has_no_drift(self):
        p = Project()
        p.run("add", "--title", "A", "--priority", "P0")
        p.run("add", "--title", "B", "--priority", "P0")
        d = self._drift(p)
        self.assertEqual(d["drift"], 0)
        self.assertEqual(d["unrecorded"], 0)

    def test_an_event_whose_row_was_deleted_by_hand_is_reported(self):
        """The mutation did not land in the markdown — or someone removed it
        without closing it. Either way the two records disagree."""
        p = Project()
        p.run("add", "--title", "A", "--priority", "P0")
        _, b = p.run("add", "--title", "B", "--priority", "P0")
        board = p.root / "BOARD.md"
        board.write_text("\n".join(
            l for l in board.read_text().split("\n")
            if not l.startswith(f"| {b['id']} |")))
        d = self._drift(p)
        self.assertEqual(d["drift"], 1)
        self.assertIn(b["id"], d["orphaned"])

    def test_a_closed_task_is_not_reported_as_orphaned(self):
        """`done` removes the row on purpose. Reporting that as a lost mutation
        would make every correct close look like a defect."""
        p = Project()
        _, a = p.run("add", "--title", "A", "--priority", "P0")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        d = self._drift(p)
        self.assertEqual(d["drift"], 0, f"a correct close was reported: {d}")

    def test_a_project_with_no_log_is_not_reported_as_broken(self):
        """Every project predates the tool at the moment it upgrades. The first
        standup after an upgrade must not be a wall of findings.

        **Not broken is not the same as clean (TASK-117).** This asserted
        `drift == 0` and `unrecorded == 0` beside `checked is False` — the two
        numbers that made a consumer reading counts instead of the flag report
        a clean board on a tree nothing had looked at. Silence about a question
        nobody asked is the point; a zero is an answer.
        """
        p = Project()
        d = self._drift(p)
        self.assertFalse(d["checked"])
        self.assertIsNone(d["drift"])
        self.assertIsNone(d["unrecorded"])

    def test_rows_predating_the_log_are_context_not_drift(self):
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | written by hand | Coding Agent | not_started | — | — |\n\n## P1", 1))
        p.run("add", "--title", "tool-written", "--priority", "P0")
        d = self._drift(p)
        self.assertEqual(d["drift"], 0, "a pre-tool row was counted as drift")
        self.assertEqual(d["unrecorded"], 1)
        self.assertIn("TASK-900", d["unrecorded_sample"])
        self.assertTrue(d["baseline"], "no baseline to judge unrecorded rows against")

    def test_a_routed_row_is_not_reported_as_un_tool_written(self):
        """Round-5 finding 5, and the first time the recurring defect reached
        code rather than prose.

        `reconcile_drift` recognized only `add` as a creating event. `route`
        emits `route`, so every row the tool itself created by promoting an
        intake request was counted `unrecorded` — forever, and it could never
        be detected as `orphaned` either, because the same tuple gates both
        loops. The detector generated the exact false drift it was built to
        catch, and `work/SKILL.md` then instructed the agent to narrate that
        signal as "written by hand since the tool landed."

        The route path is exercised end to end rather than by asserting on the
        tuple: the bug was that two readers disagreed about what creates a row,
        and only a written row can show that.
        """
        p = Project(tracks=MODE_TRACKS)
        p.run("intake", "--title", "vendor spend reconciliation")
        code, r = p.run("route", "1", "--track", "ops")
        self.assertEqual(code, 0)
        d = self._drift(p)
        self.assertEqual(
            d["unrecorded"], 0,
            f"a row the tool created via `route` was reported as having no "
            f"creating event: {d}")
        self.assertEqual(d["drift"], 0)

        # And the other half of the same tuple: deleting a routed row by hand
        # must still be caught. A fix that made `route` invisible to both loops
        # would pass the assertion above and lose the detection.
        board = p.root / "BOARD.md"
        board.write_text("\n".join(
            l for l in board.read_text().split("\n")
            if not l.startswith(f"| {r['id']} |")))
        d = self._drift(p)
        self.assertIn(r["id"], d["orphaned"],
                      "a routed row deleted by hand went undetected")

    def test_cadence_rows_are_not_counted_as_predating_the_log(self):
        """Round-3 finding B2 — the row set left one round behind the tuple.

        `board.all_tasks` includes `## Cadence`, and `perry-task` has no
        cadence subcommand: `Board.find()` iterates P0/P1/P2 and cannot even
        locate one. So a cadence row was counted `unrecorded` on a board the
        tool wrote entirely — a number no project could ever drive to zero,
        firing at every standup of every board that uses the section the
        template, the schema headings and `work/SKILL.md` all prescribe.

        Unlike the `route` case, this one is unfixable from the user's side,
        which makes it precisely the "a check people learn to ignore is worse
        than no check" failure `reconcile_drift`'s docstring names as its own
        reason for existing.

        Perry's own board ships an EMPTY cadence placeholder, which the
        `if t.id` filter drops — so dogfooding could not surface it. The row
        here is populated on purpose.
        """
        p = Project(board=BOARD + (
            "\n## Cadence\n"
            "| ID | Recurring task | Frequency | Next due | Owner | Last evidence |\n"
            "|---|---|---|---|---|---|\n"
            "| CAD-01 | weekly review | weekly | 2026-08-20 | User | — |\n"))
        p.run("add", "--title", "tool written", "--priority", "P0")
        d = self._drift(p)
        self.assertEqual(
            d["unrecorded"], 0,
            f"a cadence row was reported as predating the log on a board the "
            f"tool wrote entirely, and no user action could ever clear it: {d}")

    def test_drift_is_reported_and_a_write_repairs_from_the_store(self):
        """Projection drift cannot discard store truth after TASK-090."""
        p = Project()
        _, a = p.run("add", "--title", "A", "--priority", "P0")
        board = p.root / "BOARD.md"
        board.write_text("\n".join(
            l for l in board.read_text().split("\n")
            if not l.startswith(f"| {a['id']} |")))
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        code, out = p.run("add", "--title", "must not discard the store")
        self.assertEqual(code, 0, out)
        stored_ids = {json.loads(line)["id"] for line in
                      (p.root / "tasks.jsonl").read_text().splitlines()
                      if line.strip()}
        self.assertIn(a["id"], stored_ids)
        self.assertIn(a["id"], out["projection"]["rows_not_on_board"])


class TestLaneProceduresCallTheTool(unittest.TestCase):
    """TASK-033 — the riskiest migration in DESIGN-004's plan.

    Its failure mode is not a crash. It is a lane that still tells the agent to
    hand-write a row while the tool exists — two written paths to one piece of
    state, with drift reported against a procedure that *instructed* the agent
    to create it. The drift number would then report a documentation defect as
    if it were an agent's indiscipline, which is worse than no signal.

    §5.7 made this hard-blocked on TASK-031 for that reason: detection has to be
    watching before the procedures change, or a migration and a regression look
    identical.
    """

    @classmethod
    def setUpClass(cls):
        cls.proc = (PERRY_HOME / "work" / "reference" / "subcommands.md").read_text()

    def section(self, name: str) -> str:
        i = self.proc.index(f"### `{name}")
        j = self.proc.find("\n### ", i + 1)
        return self.proc[i:j if j > 0 else len(self.proc)]

    def test_add_task_calls_the_tool(self):
        s = self.section("add-task")
        self.assertIn("perry-task", s)
        self.assertIn("add --title", s)

    def test_close_task_calls_the_tool(self):
        s = self.section("close-task")
        self.assertIn("perry-task", s)
        self.assertIn("done", s)

    def test_no_migrated_procedure_still_describes_the_hand_edit(self):
        """The exact failure this task creates: a procedure that says both."""
        for name, banned in (
            ("add-task", "Add a row to `BOARD.md`** — terse"),
            ("close-task", "**Remove the row from `BOARD.md`**."),
        ):
            self.assertNotIn(
                banned, self.section(name),
                f"`{name}` still instructs a hand-edit for state the tool "
                f"now writes — two written paths to one piece of state")

    def test_routing_goes_through_the_tool(self):
        step0 = self.proc[self.proc.index("Step 0"):self.proc.index("Then walk")]
        self.assertIn("perry-task", step0)
        self.assertIn("route", step0)

    def test_the_stage_invariant_names_the_tool(self):
        i = self.proc.index("Every stage move")
        self.assertIn("perry-task", self.proc[i:i + 400])

    def test_the_procedures_say_what_a_refusal_means(self):
        """A tool that exits 1 without the procedure saying so invites the
        agent to treat a refusal as a failure and fall back to editing."""
        # Whitespace-collapsed: these assertions are about prose, and prose
        # reflows. An earlier version matched raw text, so adding one refusal
        # to the sentence re-wrapped the line and broke a test that had no
        # opinion about the change.
        s = re.sub(r"\s+", " ", self.section("add-task"))
        self.assertIn("Refusals are outcomes", s)
        self.assertIn("do not fall back to editing", s)

    def test_every_command_the_procedures_quote_actually_runs(self):
        """A migrated procedure naming a subcommand the tool does not have
        would be the same unbacked-index defect five reviews kept finding."""
        quoted = set(re.findall(r'perry-task"?\s+(\w+)', self.proc))
        r = subprocess.run(["python3", str(TOOL), "--help"],
                           capture_output=True, text=True)
        for cmd in quoted:
            self.assertIn(f"perry-task {cmd}", r.stdout,
                          f"the procedures call `perry-task {cmd}`, which the "
                          f"tool's own usage does not list")


class TestListContract(unittest.TestCase):
    """`perry-task list --json` is published to a program Perry does not own.

    aimark codes against this payload. The point of freezing it is that it does
    NOT move when Perry's storage does — `BOARD.md`'s role is an open question
    (DESIGN-005) and this contract is deliberately not part of it.

    These tests are the thing that makes the promise real: a change to the
    payload breaks CI here rather than breaking a front-end silently, at
    runtime, in another repo.

    Spec: `schema/task-list-contract.md`.
    """

    TASK_KEYS = {
        "role",
        "id", "title", "summary", "owner", "priority", "status", "track", "mode",
        "stage", "stage_since", "arrived", "parent", "commitment",
        "next_action", "evidence", "evidence_paths", "verification", "open",
        "group", "status_text", "created", "updated", "timeline",
        # 1.6 — the dependency edge, and the one question a dashboard asks.
        "depends_on", "blocked_by", "blocks", "startable",
        # 1.12 — the board says blocked and the graph says nothing is.
        "blocked_stale",
        # 1.15 — what each `depends_on` id IS, beside the ids themselves. An
        # ANSWERED ask is in no register a consumer can query — not `tasks[]`,
        # not `asks.items`, not `depends_on_unknown` — and deducing its kind
        # from three arrays it is missing from is set arithmetic, not a
        # contract. A parallel array, because retyping `depends_on` would be a
        # major on the key every consumer of this payload reads.
        "depends_on_resolved",
        # 1.17 — the `Evidence` cell said in a shape a consumer can branch on.
        # `evidence_paths` kept the file half of a column that carries four
        # things at once; the prose, the counts and the elided test ids reached
        # no array at all. Additive, and `evidence_paths` is unchanged.
        "evidence_relations",
    }
    TOP_KEYS = {"contract", "semantics", "project_root", "state_root",
                "conformance",
                "intake", "tasks", "open", "closed", "events", "untitled",
                # 1.6 — the three blocks that were readable only through
                # `perry-state --json`, the payload with no version.
                "risks", "asks", "drift"}
    RISKS_KEYS = {"items", "open", "cleared", "source"}
    RISK_KEYS = {"id", "title", "severity", "severity_text", "severity_rank",
                 "source", "opened", "age_days", "status", "cleared_on", "meta"}
    ASKS_KEYS = {"items", "open"}
    ASK_KEYS = {"id", "needed", "blocks", "asked", "idle", "idle_days",
                "status", "priority"}
    DRIFT_KEYS = {"checked", "baseline", "drift", "unrecorded",
                  "unrecorded_sample", "orphaned", "stale_done"}
    INTAKE_KEYS = {"rows", "undischarged", "oldest_undischarged"}
    INTAKE_ROW_KEYS = {"n", "arrived", "request", "outcome", "discharged",
                       "age_days"}
    # 1.13 — the two `conformance` entry shapes that carry a `means` sentence
    # beside the pattern they matched (TASK-142). A bare `{id, cites, status}`
    # triple reads as a wording complaint, and on 2026-08-20 it was read as one
    # on the only two stranded rows on Perry's own board.
    CITATION_KEYS = {"id", "cites", "status", "row_status", "blocked_stale",
                     "readings", "means"}
    # ONE shape for both idle checks: `status` says which produced the entry
    # and the clock is in hours on both, so a consumer needs one code path.
    IDLE_ROW_KEYS = {"id", "status", "last_event", "idle_hours",
                     "threshold_hours", "means"}
    #: `conformance.depends_on_unknown[]`. Tabulated 2026-08-21, when a row on
    #: Perry's own board was blocked on a `USER-` ask and the collection became
    #: non-empty for the first time — until then `tests/contract_key_parity.py`
    #: could not compare it and its two keys sat undocumented, unseen.
    UNKNOWN_DEP_KEYS = {"id", "unknown"}
    #: `semantics[]`. Shipped at 1.7 and described only in prose until
    #: 2026-08-21 (TASK-131) — rule 3 of the contract hands a consumer a loop
    #: over `version`/`fields`/`note` and no row said what any of the three
    #: holds, so the payload's own compatibility signal was the least
    #: documented thing in it.
    SEMANTICS_KEYS = {"version", "fields", "note"}
    #: `tasks[].depends_on_resolved[]` (1.15). `satisfied` is
    #: `dependency_satisfied`'s own answer rather than a second spelling of
    #: it, so this array and `blocked_by` cannot disagree about an edge;
    #: `kind` is `task` | `ask` | `unknown`, and `title` is `""` on the last
    #: of those because inventing one out of a handle is what `risks[].id`
    #: was corrected for at 1.6.
    RESOLVED_EDGE_KEYS = {"id", "kind", "satisfied", "title", "status"}
    #: `tasks[].evidence_relations[]` (1.17). `text` is the span verbatim,
    #: `path` is the same value `evidence_paths` carries for it, and `kind`
    #: says what the STRING is — `file`/`dir`/`unresolved`/`note` — never what
    #: it is FOR. "The document that justifies the close" and "the code that
    #: was changed" are roles the string does not carry, and deriving one from
    #: a path prefix is the invention `risks[].id` was corrected for at 1.6.
    EVIDENCE_RELATION_KEYS = {"text", "path", "kind"}
    #: `conformance.sections_read[]`. Its shape was stated inside the
    #: `conformance` table's Meaning cell, which is prose to both checkers.
    SECTIONS_READ_KEYS = {"heading", "priority", "rows"}
    #: `conformance.evidence_not_found[]`. Same: `{id, paths}` in a Meaning
    #: cell documented the pair to a human and to neither check.
    EVIDENCE_NOT_FOUND_KEYS = {"id", "paths"}
    CONFORMANCE_KEYS = {"sections_read", "sections_skipped",
                        "rows_with_unrecognized_id", "off_enum_status",
                        "rows_with_no_status", "evidence_not_found",
                        "rows_with_no_computable_age",
                        "next_action_cites_closed",
                        "depends_on_unknown", "dependency_cycles",
                        "blocked_without_dependency",
                        # TASK-142. The stranded-row family: a `blocked` row
                        # every one of whose declared dependencies has closed,
                        # an `in_progress` row with no dispatch slot and a
                        # stopped clock, and a `review` row nobody is coming
                        # back to. All three added at 1.13.
                        "blocked_by_closed_rows",
                        "in_progress_with_no_live_run", "review_idle",
                        "has_event_log",
                        "missing_projection"}
    # `field` (1.7) says what `from`/`to` refer to on this event, so a
    # consumer needs no hardcoded set of events that overload the pair.
    EVENT_KEYS = {"ts", "event", "from", "to", "field", "actor"}

    TRACKS = MODE_TRACKS

    def populated(self) -> "Project":
        p = Project(tracks=self.TRACKS)
        p.run("add", "--title", "plain project row", "--priority", "P0")
        p.run("add", "--title", "pipeline row", "--track", "blog",
              "--priority", "P1", "--commitment", "blog/1")
        _, c = p.run("add", "--title", "closed row", "--priority", "P2")
        p.run("done", c["id"], "--evidence", "e.md", "--rung", "V3")
        return p

    def payload(self, p: "Project", *extra) -> dict:
        _, out = p.run("list", "--all", *extra)
        return out

    def test_the_version_handle_is_present_and_major_1(self):
        d = self.payload(self.populated())
        self.assertEqual(d["contract"], PT.LIST_CONTRACT)
        self.assertTrue(d["contract"].startswith("perry-task/list/1."),
                        f"major bumped to {d['contract']} — every consumer "
                        f"checking major == 1 now refuses; that is intended "
                        f"only for a removed or retyped key")

    def test_every_declared_key_is_present_on_every_task(self):
        """Rule 1 of the contract: an unknown value is "", null or [] — never a
        missing key. It is what lets a consumer skip a defensive branch per
        field, so it has to hold for closed rows and event-only rows too."""
        d = self.payload(self.populated())
        self.assertTrue(d["tasks"])
        for t in d["tasks"]:
            self.assertEqual(set(t), self.TASK_KEYS,
                             f"{t.get('id')}: missing "
                             f"{self.TASK_KEYS - set(t)}, extra "
                             f"{set(t) - self.TASK_KEYS}")
            for e in t["timeline"]:
                self.assertEqual(set(e), self.EVENT_KEYS)

    def test_the_top_level_shape_is_exact(self):
        d = self.payload(self.populated())
        self.assertEqual(set(d), self.TOP_KEYS,
                         f"missing {self.TOP_KEYS - set(d)}, "
                         f"extra {set(d) - self.TOP_KEYS}")
        self.assertEqual(set(d["conformance"]), self.CONFORMANCE_KEYS)
        self.assertEqual(set(d["intake"]), self.INTAKE_KEYS)
        self.assertEqual(set(d["risks"]), self.RISKS_KEYS)
        self.assertEqual(set(d["asks"]), self.ASKS_KEYS)
        self.assertEqual(set(d["drift"]), self.DRIFT_KEYS)

    def test_open_means_still_on_the_board_not_a_status_value(self):
        """The contract says `open` is the live/closed test, not `status` —
        a consumer that filtered on `status != "done"` would keep showing a
        dropped row forever."""
        p = self.populated()
        d = self.payload(p)
        closed = [t for t in d["tasks"] if not t["open"]]
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]["status"], "done")
        self.assertNotIn(closed[0]["id"], p.board())
        self.assertTrue(all(t["id"] in p.board() for t in d["tasks"] if t["open"]))

    def test_without_all_the_closed_row_is_absent(self):
        p = self.populated()
        ids = {t["id"] for t in self.payload(p)["tasks"]}
        _, open_only = p.run("list")
        self.assertEqual(len(open_only["tasks"]), len(ids) - 1)
        self.assertTrue(all(t["open"] for t in open_only["tasks"]))

    def test_mode_columns_reach_the_payload(self):
        """`commitment` and `stage_since` exist as board columns; a payload
        that dropped them would send a front-end back to the markdown."""
        d = self.payload(self.populated())
        blog = next(t for t in d["tasks"] if t["track"] == "blog")
        self.assertEqual(blog["commitment"], "blog/1")
        self.assertEqual(blog["stage"], "brief")
        self.assertTrue(blog["stage_since"], "the dwell clock is not exposed")
        self.assertTrue(blog["owner"], "owner is missing from the payload")

    def test_created_and_updated_are_timestamps_or_null(self):
        d = self.payload(self.populated())
        for t in d["tasks"]:
            for k in ("created", "updated"):
                self.assertTrue(t[k] is None or isinstance(t[k], str), (t["id"], k))
            if t["timeline"]:
                self.assertEqual(t["updated"], t["timeline"][-1]["ts"])

    def test_a_row_predating_the_event_log_still_carries_every_key(self):
        """The hardest case for rule 1: a board row with no event at all."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | predates everything | User | in_progress | — | — |\n\n## P1", 1))
        t = next(x for x in self.payload(p)["tasks"] if x["id"] == "TASK-900")
        self.assertEqual(set(t), self.TASK_KEYS)
        self.assertIsNone(t["created"])
        self.assertEqual(t["timeline"], [])
        self.assertTrue(t["open"])

    # Reduced from a real Perry project, kept close to the original on purpose:
    # sections named by workstream instead of P0/P1/P2, a 4-column table, an id
    # in strikethrough, a status in the document language, a first cell that is
    # prose rather than a handle, and a reference table that is not work at all.
    MESSY = """# BOARD

## ID prefixes (canonical)

| Prefix | Means |
|---|---|
| DATA-n | data layer |

## Open — 投资线

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| IPS-004 | 政策起草 | User | 起草中 | 起草 v2 |

## Open — 工程线 · phase #004

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| TECH-conftest | `tests/conftest.py` 无隔离 | Coding Agent | not_started | — |

## P2 (低优先 carry)

| ID | Title | Owner | Status |
|---|---|---|---|
| 2 待核项 | GAVI 金额 | User | 半解 |
| ~~DATA-007~~ | 每仓核验时效 | Coding Agent | done |

## Cadence

| ID | Recurring task | Frequency | Next due | Owner | Last evidence |
|---|---|---|---|---|---|
| CAD-01 | weekly review | weekly | 2026-08-20 | User | — |

## Top risks

- something
"""

    def test_a_real_projects_board_is_read_rather_than_mostly_skipped(self):
        """The compatibility case, taken from a live Perry project.

        Reading only `## P0` / `## P1` / `## P2` found the one section whose
        name happened to match, reported three tasks for a project with dozens,
        and pulled rows out of a `## ID prefixes` reference table as though
        they were work. A front-end handed that payload shows the user
        confident nonsense — which is worse than showing nothing.
        """
        d = self.payload(Project(board=self.MESSY))
        ids = {t["id"] for t in d["tasks"]}
        self.assertEqual(ids, {"IPS-004", "TECH-conftest", "DATA-007"},
                         f"workstream sections were not read: {sorted(ids)}")

        by_id = {t["id"]: t for t in d["tasks"]}
        self.assertEqual(by_id["IPS-004"]["group"], "Open — 投资线")
        self.assertEqual(by_id["IPS-004"]["priority"], "",
                         "a section that is not P0/P1/P2 must not be assigned "
                         "a priority the project never stated")
        self.assertEqual(by_id["DATA-007"]["priority"], "P2")
        self.assertEqual(by_id["TECH-conftest"]["next_action"], "—")

    def test_projection_only_rows_do_not_enter_task_conformance(self):
        c = self.payload(Project(board=self.MESSY))["conformance"]
        self.assertEqual(c["sections_skipped"], [])
        self.assertEqual(c["rows_with_unrecognized_id"], [])
        self.assertEqual(c["off_enum_status"], [])
        self.assertFalse(c["has_event_log"])
        self.assertEqual(
            {s["heading"] for s in c["sections_read"]},
            {"Open — 投资线", "Open — 工程线 · phase #004", "P2 (低优先 carry)"})

    def test_cadence_and_risks_are_not_reported_as_tasks(self):
        """They are board sections and they are not work. Counting them is how
        `perry-state`'s drift row got a number no project could drive to zero."""
        d = self.payload(Project(board=self.MESSY))
        self.assertNotIn("CAD-01", {t["id"] for t in d["tasks"]})
        headings = {s["heading"] for s in d["conformance"]["sections_read"]}
        self.assertNotIn("Cadence", headings)

    def test_the_contract_document_lists_exactly_these_keys(self):
        """The spec and the payload are two statements of one thing, which is
        the arrangement that has drifted in every review round of this project.
        Read the document's own tables rather than trusting them."""
        doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        self.assertIn(PT.LIST_CONTRACT, doc, "the doc names a different version")
        documented = set(re.findall(r"^\| `(\w+)` \|", doc, re.M))
        known = (self.TASK_KEYS | self.EVENT_KEYS | self.CONFORMANCE_KEYS
                 | self.INTAKE_KEYS | self.INTAKE_ROW_KEYS
                 | self.RISKS_KEYS | self.RISK_KEYS
                 | self.ASKS_KEYS | self.ASK_KEYS | self.DRIFT_KEYS
                 | self.CITATION_KEYS | self.IDLE_ROW_KEYS
                 | self.UNKNOWN_DEP_KEYS | self.SEMANTICS_KEYS
                 | self.RESOLVED_EDGE_KEYS | self.EVIDENCE_RELATION_KEYS
                 | self.SECTIONS_READ_KEYS | self.EVIDENCE_NOT_FOUND_KEYS)
        undocumented = known - documented
        self.assertFalse(undocumented,
                         f"payload keys with no row in the contract doc: "
                         f"{sorted(undocumented)}")
        phantom = documented - known
        self.assertFalse(phantom,
                         f"the contract doc documents keys the payload does "
                         f"not emit: {sorted(phantom)}")


class TestFromAimarksProductionReport(unittest.TestCase):
    """Every case here was measured by a consumer against a real project, not
    read out of the spec. Reported 2026-08-17 after aiMark shipped against
    `perry-task/list/1.1`.

    None of it was blocking for them, which is the reason to fix it: they had
    absorbed all of it, and absorbing means guessing at Perry's intent in the
    consumer — which is how the last divergence started.
    """

    BOARD_WITH_EMPHASIS = """# BOARD

## P0
| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-001 | Bold done | User | **done** | — | — |
| TASK-002 | Bold not started | User | **not_started** | — | — |
| TASK-003 | Two states at once | User | **迁移 done，占比目标 not_started** | — | — |
| TASK-004 | Plain | User | in_progress | — | — |

## P1
| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2
| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Done this period (leaves the board at next triage)

| ID | Title | Evidence |
|---|---|---|
| TASK-010 | Finished, and the table has no Status column | `BOARD.md` |
"""

    def payload(self, board: str):
        p = Project(board=board)
        _, out = p.run("list", "--all")
        return p, out

    def test_emphasis_is_stripped_so_the_enum_claim_is_true(self):
        """`**done**` is `done` wearing bold. Formatting is not meaning, and
        17 of 41 rows on one real board carried it — every finished task
        rendered as an unrecognized state by a consumer trusting the enum."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        by = {t["id"]: t for t in d["tasks"]}
        self.assertEqual(by["TASK-001"]["status"], "done")
        self.assertEqual(by["TASK-002"]["status"], "not_started")
        self.assertEqual(by["TASK-001"]["status_text"], "done")

    def test_a_composite_cell_is_not_rounded_to_one_state(self):
        """`迁移 done，占比目标 not_started` is two states. Picking either is a
        lie about the work; `status` goes empty and `status_text` keeps it."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        t = next(x for x in d["tasks"] if x["id"] == "TASK-003")
        self.assertEqual(t["status"], "")
        self.assertEqual(t["status_text"], "")
        self.assertIn(
            "TASK-003",
            [row["id"] for row in d["conformance"]["rows_with_no_status"]])

    def test_open_is_false_for_a_row_whose_status_is_terminal(self):
        """`open` meant "still on the board", which was true when closing
        removed the row. Once the reader saw every section, a project staging
        finished work under its own heading reported those rows as open — 20 of
        them on Perry's own board."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        by = {t["id"]: t for t in d["tasks"]}
        self.assertFalse(by["TASK-001"]["open"], "a `**done**` row read as open")
        self.assertTrue(by["TASK-004"]["open"])

    def test_a_statusless_row_is_open_and_that_assumption_is_declared(self):
        """The honest limit. A table with no `Status` column says nothing, and
        Perry cannot know better — so it must say which rows those are rather
        than let a consumer trust the flag silently."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        t = next(x for x in d["tasks"] if x["id"] == "TASK-010")
        self.assertEqual(t["status"], "")
        self.assertTrue(t["open"])
        self.assertIn(
            "TASK-010",
            [r["id"] for r in d["conformance"]["rows_with_no_status"]],
            "a row Perry cannot classify was not declared as such")

    def test_a_row_list_printed_can_also_be_closed(self):
        """The read path and the write path must agree about what a row is.

        `1.1` taught the reader to see every `## ` section; `find()` was left
        on `P0`/`P1`/`P2`. So on Perry's own board, 20 rows under
        `## Done this period (leaves the board at next triage)` were listed by
        `list` and refused by `done` with "is not an open row on the board" —
        a false statement, about rows the same tool had just printed, that made
        every archived row permanently unclosable.

        Needing a priority is a rule about `add`: a new row has to be filed
        somewhere. It was wrongly applied to the whole write path. Both now go
        through `Board._task_sections()`, because they drifted the moment they
        did not.
        """
        p = Project(board=self.BOARD_WITH_EMPHASIS)
        _, listed = p.run("list", "--all")
        self.assertIn("TASK-010", [t["id"] for t in listed["tasks"]],
                      "the archived row is not even listed")

        code, out = p.run("done", "TASK-010", "--evidence", "BOARD.md")
        self.assertEqual(
            code, 0,
            f"a row `list` printed could not be closed: {out}")
        self.assertNotIn("TASK-010", p.board())

    def test_a_struck_through_id_is_still_findable(self):
        """`~~DATA-007~~` is how a real board retires a row. The reader already
        strips the emphasis; the writer has to match it."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| ~~TASK-900~~ | Retired | User | done | — | — |\n\n## P1", 1))
        code, out = p.run("drop", "TASK-900", "--reason", "superseded")
        self.assertEqual(code, 0, f"a struck-through id was unreachable: {out}")

    def test_evidence_is_split_and_resolved_rather_than_handed_over_raw(self):
        """One real cell: three comma-separated backticked paths, relative to
        the PROJECT root while the contract declared `state_root` — and the
        same column on the same board also used state-relative paths. Nothing
        in the string distinguishes them, so Perry resolves rather than
        shipping the ambiguity downstream."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | Multi | User | done | — | `BOARD.md`, `.perry/config.md`, `nope.md` |\n\n## P1", 1))
        _, d = p.run("list", "--all")
        t = next(x for x in d["tasks"] if x["id"] == "TASK-900")
        self.assertEqual(t["evidence_paths"], ["BOARD.md", ".perry/config.md"])
        self.assertIn({"id": "TASK-900", "paths": ["nope.md"]},
                      d["conformance"]["evidence_not_found"])
        self.assertIn("`BOARD.md`", t["evidence"], "the raw cell was lost")

    def test_a_dash_means_absent_not_a_file_named_dash(self):
        """aiMark briefly rendered an openable document named `perry/—`."""
        _, d = self.payload(self.BOARD_WITH_EMPHASIS)
        for t in d["tasks"]:
            if t["evidence"] == "—":
                self.assertEqual(t["evidence_paths"], [])

    def test_the_changelog_names_every_shipped_version(self):
        """aiMark saw 1.0 become 1.1 mid-session and could not tell what had
        been added. "1.x may only add keys" is a strong guarantee; it is more
        useful when a consumer can see what the new keys are."""
        import re
        doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        self.assertIn("## Changelog", doc)
        major_minor = PT.LIST_CONTRACT.rsplit("/", 1)[1]
        # **A whole-heading match, not a substring.** `assertIn("### 1.9", doc)`
        # passes against `### 1.9-removed`, which a mutation demonstrated —
        # the guard would have let the entry be renamed away.
        # The version must end at a word boundary of whitespace or end-of-line,
        # so `### 1.6 — 2026-08-18` matches and `### 1.9-removed` does not.
        headings = set(re.findall(r"^###\s+(\d+\.\d+)(?:\s|$)", doc, re.M))
        self.assertIn(major_minor, headings,
                      f"the current version {major_minor} has no changelog "
                      f"entry of its own; found {sorted(headings)}")
        # **Every shipped minor, not only the current one.** A consumer jumping
        # 1.4 → 1.9 reads the entries between, and one skipped is one it cannot
        # learn about.
        major, minor = (int(x) for x in major_minor.split("."))
        for m in range(minor + 1):
            v = f"{major}.{m}"
            self.assertIn(v, headings, f"no changelog entry for {v}")

    def test_the_semantics_list_is_ordered_oldest_first(self):
        """Its whole use is "everything newer than the minor I tested against",
        which a consumer reads by walking the list. It shipped once as
        1.5, 1.9, 1.7 because an entry was written where it read well rather
        than where it belonged."""
        versions = [e["version"] for e in PT.LIST_SEMANTICS]
        keyed = [tuple(int(x) for x in v.split(".")) for v in versions]
        self.assertEqual(keyed, sorted(keyed), versions)

    def test_every_semantics_entry_names_fields_and_a_reason(self):
        """An entry saying "something changed" is the thing this array exists
        to replace."""
        for e in PT.LIST_SEMANTICS:
            self.assertTrue(e["fields"], e)
            self.assertGreater(len(e["note"]), 80, e)


class TestANewIdJoinsTheFamilyTheBoardAlreadyUses(unittest.TestCase):
    """TASK-060, from aiMark §4. On a board whose 17 rows are `AIM-001`…
    `AIM-017`, `add` minted `TASK-001`.

    Legitimate under the contract — ids are opaque and a board may carry
    several project-declared prefixes — but a user creating a task from a
    front-end watched their board sprout a second id family, and there was no
    flag with which to ask for the first. aiMark passes no id and *cannot*:
    nothing in the surface would let it.

    **The decision, and the failure mode it is avoiding.** Both halves shipped:
    `--prefix` names the family outright, and Perry adopts the board's own
    prefix *only when the board has exactly one*. It deliberately does NOT pick
    the most common one. `~/proj/gimegime-pmo` carries **36** families in its
    task tables, declared in its own `## ID prefixes (canonical)` section, and
    they are not stylistic — `IPS-*`/`ALLOC-*`/`DUE-*` mean 投资线 and
    `TECH-*`/`DATA-*` mean 工程线, filed in separate sections for a reason the
    board states. A plurality winner there mints an id that ASSERTS a
    workstream nobody chose, and an id is permanent. A foreign-looking
    `TASK-001` is visibly Perry's and claims nothing; a wrong-family `IPS-014`
    claims something false.

    So the guard for the category is not "adoption happens" — it is
    `test_a_board_with_several_families_is_not_guessed_at`, which is the case
    adoption must decline.
    """

    HDR = ("| ID | Title | Owner | Status | Next action | Evidence |\n"
           "|---|---|---|---|---|---|\n")

    def board(self, *ids: str) -> str:
        rows = "".join(f"| {i} | row | Coding Agent | not_started | — | — |\n"
                       for i in ids)
        return (f"# BOARD\n\n## P0 (must finish this period)\n\n{self.HDR}{rows}"
                f"\n## P1\n\n{self.HDR}\n## P2\n\n{self.HDR}")

    AIMARK = None  # set in setUp; the shape aiMark reported

    def setUp(self):
        self.AIMARK = self.board(*(f"AIM-{i:03d}" for i in range(1, 18)))

    def test_a_single_family_board_mints_into_its_own_family(self):
        p = Project(board=self.AIMARK)
        code, a = p.run("add", "--title", "from the front-end")
        self.assertEqual(code, 0, a)
        self.assertEqual(a["id"], "AIM-018")

    def test_the_number_continues_the_family_rather_than_restarting_it(self):
        """`mint_id` counted `TASK-` specifically. Adopting `AIM` without
        moving the counter with it would have minted `AIM-001` onto a board
        already holding `AIM-017` — the id reuse the function exists to make
        impossible, arrived by a new route."""
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "X")
        self.assertNotIn(f"| {a['id']} |", self.AIMARK,
                         f"{a['id']} was already a row on this board")
        self.assertEqual(a["id"], "AIM-018")
        _, b = p.run("add", "--title", "Y")
        self.assertEqual(b["id"], "AIM-019")

    def test_an_adopted_id_is_never_reissued_either(self):
        """The uniqueness guarantee is per family, and the journal is what
        makes it survive the disposable log — under `AIM` as under `TASK`."""
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "first")
        p.run("done", a["id"], "--evidence", "e.md", "--rung", "V3")
        (p.root / ".perry" / "events.jsonl").unlink()
        _, b = p.run("add", "--title", "second")
        self.assertNotEqual(b["id"], a["id"],
                            f"{a['id']} was reissued after the derived log went")

    def test_a_board_with_several_families_is_not_guessed_at(self):
        """**The load-bearing one.** Three `IPS-` rows and one `TECH-` row: the
        most common family is `IPS`, and Perry must not take it. The families
        on a real board mean different workstreams, and an id that names the
        wrong one is a false claim that can never be withdrawn."""
        p = Project(board=self.board("IPS-001", "IPS-002", "IPS-003", "TECH-001"))
        code, a = p.run("add", "--title", "X")
        self.assertEqual(code, 0, a)
        self.assertEqual(a["prefix"], "TASK")
        self.assertTrue(a["id"].startswith("TASK-"),
                        f"Perry guessed a workstream from a plurality: {a['id']}")

    def test_a_family_with_no_numbers_is_not_given_one(self):
        """`RW-alpha` and `RW-beta` are one family and there is nothing to
        count from. Minting `RW-001` beside them would invent a numbering the
        project did not choose."""
        p = Project(board=self.board("RW-alpha", "RW-beta"))
        _, a = p.run("add", "--title", "X")
        self.assertEqual(a["prefix"], "TASK")

    def test_a_task_board_still_mints_task(self):
        """The bound. Every project that has never said otherwise is
        untouched — including Perry's own board, whose single family is
        `TASK`."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        self.assertEqual(a["id"], "TASK-001")
        self.assertEqual(a["prefix"], "TASK")

    def test_prefix_names_the_family_outright(self):
        """The half the finding actually asked for: a front-end that cannot
        pass an id must be able to ask for a family."""
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "X", "--prefix", "DOC")
        self.assertEqual(a["id"], "DOC-001")

    def test_prefix_beats_what_the_board_would_have_adopted(self):
        p = Project(board=self.AIMARK)
        _, a = p.run("add", "--title", "X", "--prefix", "DOC")
        self.assertEqual(a["prefix"], "DOC")

    def test_prefix_refuses_a_family_the_tool_mints_for_another_register(self):
        """`RX-005` as a task would collide with the risk register's own
        numbering on the same board, and both writers would then be right
        about their own file and wrong about the project."""
        for reserved in ("RX", "USER", "CAD"):
            p = Project(board=self.AIMARK)
            code, out = p.run("add", "--title", "X", "--prefix", reserved)
            self.assertEqual(code, 1, f"--prefix {reserved} was accepted: {out}")
            self.assertNotIn(f"{reserved}-001", p.board())

    def test_prefix_refuses_a_whole_id(self):
        """`--prefix AIM-018` is the obvious mistake, and it has to refuse
        rather than mint `AIM-018-001`."""
        p = Project(board=self.AIMARK)
        code, out = p.run("add", "--title", "X", "--prefix", "AIM-018")
        self.assertEqual(code, 1, out)
        self.assertIn("--prefix", str(out))

    def test_a_multi_segment_prefix_is_allowed(self):
        """`ARCH-V2-*` is a real family on a real board. Each segment starts
        with a letter, which is the rule that separates it from an id."""
        p = Project(board=self.AIMARK)
        code, a = p.run("add", "--title", "X", "--prefix", "ARCH-V2")
        self.assertEqual(code, 0, a)
        self.assertEqual(a["id"], "ARCH-V2-001")

    def test_route_mints_from_the_same_rule_add_does(self):
        """Both verbs mint. A family adopted by one and not the other is the
        same divergence `--group` had, in the id column."""
        p = Project(tracks=MODE_TRACKS, board=self.AIMARK)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "blog")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "AIM-018")

    def test_route_takes_prefix_too(self):
        p = Project(tracks=MODE_TRACKS, board=self.AIMARK)
        p.run("intake", "--title", "a request", "--arrived", "2026-08-05")
        code, out = p.run("route", "1", "--track", "blog", "--prefix", "DOC")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["id"], "DOC-001")

    def test_ids_in_the_non_task_registers_are_not_a_family(self):
        """`## Top risks`, `## Cadence` and `## User Input Queue` carry their
        own prefixes and are not work. Counting them would make every board
        multi-family and adoption would never fire — or worse, a board with one
        `USER-001` and no tasks would adopt `USER`."""
        p = Project(board=self.AIMARK)
        p.run("ask", "--needed", "which staging default?")
        p.run("risk-add", "--title", "a risk")
        _, a = p.run("add", "--title", "X")
        self.assertEqual(a["prefix"], "AIM")


class TestTheSectionsAWorkSurfaceShows(unittest.TestCase):
    """TASK-058. `risks`, `asks` and `drift` — written by `perry-task`, and
    readable until 1.6 only through `perry-state --json`, the one payload that
    carries no version at all. `## User Input Queue` is the *needs-you* list.
    """

    def payload(self, p) -> dict:
        _, out = p.run("list", "--all")
        return out

    def test_an_ask_carries_an_integer_age_beside_the_rendered_string(self):
        """`idle` was `"9d"` — displayable, unsortable. The needs-you list is
        what a dashboard sorts on."""
        p = Project()
        _, u = p.run("ask", "--needed", "the signing certificate",
                     "--arrived", "2020-01-01")
        item = next(a for a in self.payload(p)["asks"]["items"] if a["id"] == u["id"])
        self.assertIsInstance(item["idle_days"], int)
        self.assertGreater(item["idle_days"], 1000)

    def test_an_answered_ask_is_not_in_the_needs_you_list(self):
        """One shared predicate decides this. Counting answered rows is how a
        dashboard came to say "2 items waiting on you" about two questions
        answered the same day."""
        p = Project()
        _, u = p.run("ask", "--needed", "a decision")
        self.assertEqual(1, self.payload(p)["asks"]["open"])
        p.run("answer", u["id"], "--answer", "yes")
        self.assertEqual(0, self.payload(p)["asks"]["open"])

    def test_a_bullet_risk_does_not_report_its_severity_letter_as_an_id(self):
        """Measured: `- H · Apple developer agreement expired` arrived as
        `{"id": "H", "title": "· Apple …", "severity": "watch"}`. Three defects,
        one cause — nothing told the parser the first token was a marker."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- H · Apple developer agreement expired")
        (p.root / "BOARD.md").write_text(board)
        r = self.payload(p)["risks"]["items"][0]
        self.assertEqual("", r["id"], "the severity letter was published as an id")
        self.assertEqual("Apple developer agreement expired", r["title"])
        self.assertEqual("H", r["severity_text"])
        self.assertEqual("high", r["severity_rank"])

    def test_two_risks_a_human_ranked_differently_are_ranked_differently(self):
        """`severity` is the STANCE and is `watch` for both. The magnitude the
        project wrote is a second axis, and folding them into one is what made
        an H and an M display identically."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- H · certificate expired\n- L · docs are thin")
        (p.root / "BOARD.md").write_text(board)
        ranks = [r["severity_rank"] for r in self.payload(p)["risks"]["items"]]
        self.assertEqual(["high", "low"], ranks)

    def test_a_risk_line_with_no_marker_keeps_its_first_word(self):
        """The narrowing check. A guard written around `H` alone would let a
        parser eat the first word of every unmarked sentence — which is what it
        used to do: `- Perry is half-adopted` reported `id: "Perry"`."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- Hostname resolution is flaky in CI")
        (p.root / "BOARD.md").write_text(board)
        r = self.payload(p)["risks"]["items"][0]
        self.assertEqual("Hostname resolution is flaky in CI", r["title"])
        self.assertEqual("", r["severity_text"])

    def test_two_risks_with_no_id_both_survive_the_merge(self):
        """The dedup key was the id, so a risk with a falsy one was silently
        discarded — unreachable only while the parser was inventing ids out of
        first words. Removing the invention would have taken every bullet risk
        on every unmigrated project to zero."""
        p = Project()
        board = p.board().replace(
            "## Top risks\n\n- none",
            "## Top risks\n\n- H · certificate expired\n- M · vendor is late")
        (p.root / "BOARD.md").write_text(board)
        self.assertEqual(2, self.payload(p)["risks"]["open"])

    def test_drift_reports_a_row_the_tool_never_wrote(self):
        p = Project()
        p.run("add", "--title", "written by the tool", "--priority", "P0")
        board = p.board().replace(
            "## P1", "| HAND-001 | typed in by hand | User | not_started | — | — |\n\n## P1", 1)
        (p.root / "BOARD.md").write_text(board)
        d = self.payload(p)["drift"]
        self.assertTrue(d["checked"])
        self.assertEqual(1, d["unrecorded"])
        self.assertIn("HAND-001", d["unrecorded_sample"])

    def test_a_project_with_no_event_log_reports_drift_unchecked_not_broken(self):
        """**The name was true and the assertion was not (TASK-117).**

        `unchecked` was pinned by `checked is False` and then contradicted one
        line down by `drift == 0`, which is a finding. Every field that would
        otherwise report an absence is `null` here — rule 1 of this contract
        names `null` as the unknown value, and a consumer that skipped the flag
        now fails on it instead of rendering a clean board.
        """
        p = Project()
        d = self.payload(p)["drift"]
        self.assertFalse(d["checked"])
        for key in ("drift", "unrecorded", "unrecorded_sample",
                    "orphaned", "stale_done"):
            self.assertIsNone(d[key], f"`{key}` answers a question nobody asked")

    def test_the_three_blocks_are_present_on_a_board_that_has_none_of_them(self):
        """Rule 1 of the contract: an unknown value is `""`, `null` or `[]`,
        never a missing key."""
        p = Project(board=BOARD.split("## Cadence")[0])
        d = self.payload(p)
        self.assertEqual([], d["risks"]["items"])
        self.assertEqual([], d["asks"]["items"])
        self.assertEqual(0, d["asks"]["open"])


if __name__ == "__main__":
    unittest.main()
