"""TASK-167 — `perry-task purge`, the store's only removal path.

**What made this a row rather than a cleanup.** Three rows titled `t`, added
and dropped inside sixty seconds while somebody smoke-tested `perry-task add`
on 2026-08-18, sat in `perry/tasks.jsonl` reading `status: dropped`. They were
invisible on `BOARD.md` — dropped rows are not rendered — and present in every
`list --json` payload a consumer reads. And there was no way to take them out:
`drop` *sets a status*, which is what put them in that state; there was no
`purge`, no `remove`, no `forget`.

So the deliverable is the mechanism. Everything below is proved on a fixture
project this module builds, never on Perry's own state — a refusal asserted
against the store living around the test is a check that stops meaning
anything the week somebody edits that store.

Run: python3 -m unittest discover -s tests -p test_purge.py
"""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

from test_task_writer import PT, Project, PERRY_HOME

TOOL = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"
REASON = "smoke-test row; never work"


class PurgeCase(unittest.TestCase):
    """A fixture project with one closed row, ready to be purged."""

    def closed_row(self, p: Project, title: str = "the probe row") -> str:
        """Add a row and drop it, through the tool. Returns its id."""
        _, a = p.run("add", "--title", title)
        code, out = p.run("drop", a["id"], "--reason", "probe")
        self.assertEqual(code, 0, out)
        return a["id"]

    def store(self, p: Project) -> list[dict]:
        path = p.root / "tasks.jsonl"
        return [json.loads(l) for l in path.read_text().split("\n") if l.strip()]

    def record(self, p: Project, tid: str) -> dict | None:
        return next((r for r in self.store(p) if r["id"] == tid), None)

    def purge(self, p: Project, tid: str, reason: str = REASON):
        return p.run("purge", tid, "--reason", reason)


# ── it removes the record, and only that record ───────────────────────────


class TestItRemovesTheRecord(PurgeCase):

    def test_the_record_leaves_the_store(self):
        p = Project()
        tid = self.closed_row(p)
        self.assertIsNotNone(self.record(p, tid), "fixture never stored the row")
        code, out = self.purge(p, tid)
        self.assertEqual(code, 0, out)
        self.assertIsNone(self.record(p, tid),
                          "`purge` reported success and the record is still there")

    def test_it_leaves_the_list_payload(self):
        """The surface the row was actually visible on. It was `0` of the
        board and `3` of `tasks[]`, and that asymmetry is what made three
        invisible rows worth a mechanism."""
        p = Project()
        tid = self.closed_row(p)
        _, before = p.run("list", "--all")
        self.assertIn(tid, [t["id"] for t in before["tasks"]])
        self.purge(p, tid)
        _, after = p.run("list", "--all")
        self.assertNotIn(tid, [t["id"] for t in after["tasks"]])
        self.assertEqual(len(after["tasks"]), len(before["tasks"]) - 1)

    def test_no_other_record_is_touched(self):
        """Byte-for-field. A removal that renormalized its neighbours would
        turn a one-line deletion into a whole-file diff, which is the objection
        `perry_store § STORED` records against re-deriving `order`."""
        p = Project()
        keep_a = self.closed_row(p, "a closed row that stays")
        _, live = p.run("add", "--title", "an open row that stays")
        tid = self.closed_row(p)
        before = {r["id"]: r for r in self.store(p)}
        self.purge(p, tid)
        after = {r["id"]: r for r in self.store(p)}
        self.assertEqual(set(before) - set(after), {tid})
        for rid in after:
            self.assertEqual(after[rid], before[rid],
                             f"{rid} changed as a side effect of purging {tid}")
        self.assertIn(keep_a, after)
        self.assertIn(live["id"], after)

    def test_order_is_not_renumbered(self):
        """TASK-167 asked what removal does to `order` and the answer is
        nothing — stated here as a test rather than only in a docstring.

        `commit()` already renumbered at CLOSE time: `done` and `drop`
        decrement every peer below the row and set the row's own `order` to
        `null`. So every record `purge` can reach carries `order: null`, there
        is no position to vacate, and decrementing again here would shift the
        peers a second time for one close.
        """
        p = Project()
        _, first = p.run("add", "--title", "first", "--priority", "P1")
        _, second = p.run("add", "--title", "second", "--priority", "P1")
        _, third = p.run("add", "--title", "third", "--priority", "P1")
        p.run("drop", second["id"], "--reason", "probe")
        before = {r["id"]: r.get("order") for r in self.store(p)}
        self.assertIsNone(before[second["id"]],
                          "a dropped row should already carry order: null")
        self.purge(p, second["id"])
        after = {r["id"]: r.get("order") for r in self.store(p)}
        self.assertEqual(after[first["id"]], before[first["id"]])
        self.assertEqual(after[third["id"]], before[third["id"]])

    def test_the_board_is_not_disturbed(self):
        p = Project()
        _, live = p.run("add", "--title", "an open row that stays")
        tid = self.closed_row(p)
        before = p.board()
        self.purge(p, tid)
        self.assertEqual(p.board(), before,
                         "purging an off-board record rewrote the projection")
        self.assertIn(live["id"], p.board())

    def test_a_dry_run_writes_nothing(self):
        p = Project()
        tid = self.closed_row(p)
        before = {f: f.read_bytes() for f in p.root.rglob("*") if f.is_file()}
        code, out = p.run("purge", tid, "--reason", REASON, "--dry-run")
        self.assertEqual(code, 0, out)
        after = {f: f.read_bytes() for f in p.root.rglob("*") if f.is_file()}
        self.assertEqual(before, after)


# ── the removal is reconstructible ────────────────────────────────────────


class TestItIsReconstructible(PurgeCase):
    """TASK-167 decision 4: it is a destructive write to the user's own state,
    so at minimum the event carries the removed record verbatim."""

    def test_the_event_carries_the_record_verbatim(self):
        p = Project()
        tid = self.closed_row(p)
        stored = self.record(p, tid)
        self.purge(p, tid)
        ev = next(e for e in p.events()
                  if e.get("event") == "purge" and e.get("id") == tid)
        self.assertEqual(ev["record"], stored,
                         "the log does not hold the line that left the store")

    def test_the_store_can_be_rebuilt_from_the_log_alone(self):
        """The property `record` exists for, exercised rather than asserted:
        appending `record` back reproduces the store byte-for-byte."""
        p = Project()
        self.closed_row(p, "a row that stays")
        tid = self.closed_row(p)
        before = (p.root / "tasks.jsonl").read_text()
        self.purge(p, tid)
        ev = next(e for e in p.events()
                  if e.get("event") == "purge" and e.get("id") == tid)
        rebuilt = self.store(p) + [ev["record"]]
        self.assertEqual(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rebuilt),
            before)

    def test_the_journal_says_the_record_was_removed(self):
        """The canonical half of the transaction, not only the disposable log.
        DESIGN-004 lets the event fail alone; if the removal were recorded
        there and nowhere else, a lost event would make the row's
        disappearance unexplainable."""
        p = Project()
        tid = self.closed_row(p)
        self.purge(p, tid)
        journal = p.journal()
        self.assertIn(tid, journal)
        self.assertIn("purged from the store", journal)
        self.assertIn(REASON, journal)


# ── what it refuses ───────────────────────────────────────────────────────


class TestRefusals(PurgeCase):

    def refused(self, p: Project, tid: str, *argv) -> str:
        code, out = p.run("purge", tid, *argv)
        self.assertEqual(code, 1, f"expected a refusal, got {out!r}")
        text = out["refused"] if isinstance(out, dict) else str(out)
        self.assertIsNotNone(self.record(p, tid),
                             "a refusal removed the record anyway")
        return text

    def test_a_removal_with_no_reason_is_refused(self):
        p = Project()
        tid = self.closed_row(p)
        self.assertIn("--reason", self.refused(p, tid))

    def test_an_open_row_is_refused_and_the_refusal_names_drop(self):
        """The refusal that keeps `purge` from manufacturing the drift `drop`
        exists to prevent: an open row removed from the store leaves its `add`
        event with no row and no close, which is `reconcile_drift`'s
        `orphaned`."""
        p = Project()
        _, a = p.run("add", "--title", "live work")
        text = self.refused(p, a["id"], "--reason", REASON)
        self.assertIn("not done or dropped", text)
        self.assertIn("perry-task drop", text)

    def test_an_id_the_store_does_not_carry_is_refused(self):
        p = Project()
        code, out = p.run("purge", "TASK-999", "--reason", REASON)
        self.assertEqual(code, 1)
        self.assertIn("TASK-999", str(out))

    def test_a_row_still_on_the_board_is_refused(self):
        """A terminal record whose row is still rendered means `BOARD.md` is
        stale; removing the record under it leaves a line rendering from
        nothing."""
        p = Project()
        tid = self.closed_row(p)
        # Put the row back under `## P1`, immediately after that table's
        # separator, which is where the projection would carry it. Written by
        # hand because no subcommand can produce this state — that is the
        # point: it is what a stale `BOARD.md` looks like.
        lines = p.board().split("\n")
        i = next(n for n, l in enumerate(lines) if l.startswith("## P1"))
        sep = next(n for n in range(i, len(lines)) if lines[n].startswith("|---"))
        lines.insert(sep + 1, f"| {tid} | the probe row | — | dropped | — | — |")
        (p.root / "BOARD.md").write_text("\n".join(lines))
        text = self.refused(p, tid, "--reason", REASON)
        self.assertIn("perry-tasks render --write", text)


class TestItRefusesALiveReference(PurgeCase):
    """TASK-167 decision 2. Each refusal is proved on a constructed case, and
    each says which reference it found."""

    def edit_store(self, p: Project, tid: str, **fields) -> None:
        """Hand-edit one record of the FIXTURE's store.

        The fixture is the test's own scratch project, not a Perry store, and
        these are field values no subcommand writes onto a foreign row —
        `--parent` and `--commitment` are `add`-time flags. Every assertion
        that matters below still runs through the shipped tool.
        """
        path = p.root / "tasks.jsonl"
        rows = [json.loads(l) for l in path.read_text().split("\n") if l.strip()]
        for r in rows:
            if r["id"] == tid:
                r.update(fields)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                for r in rows))

    def test_a_depends_on_edge_is_refused_and_named(self):
        p = Project()
        tid = self.closed_row(p)
        _, waiter = p.run("add", "--title", "waits on it")
        code, _ = p.run("depends", waiter["id"], "--on", tid)
        self.assertEqual(code, 0)
        code, out = self.purge(p, tid)
        self.assertEqual(code, 1)
        self.assertIn(f"{waiter['id']}.depends_on", out["refused"])

    def test_a_parent_pointer_is_refused_and_named(self):
        p = Project()
        tid = self.closed_row(p)
        _, child = p.run("add", "--title", "a child row")
        self.edit_store(p, child["id"], parent=tid)
        code, out = self.purge(p, tid)
        self.assertEqual(code, 1)
        self.assertIn(f"{child['id']}.parent", out["refused"])

    def test_a_commitment_pointer_is_refused_and_named(self):
        p = Project()
        tid = self.closed_row(p)
        _, other = p.run("add", "--title", "a committed row")
        self.edit_store(p, other["id"], commitment=tid)
        code, out = self.purge(p, tid)
        self.assertEqual(code, 1)
        self.assertIn(f"{other['id']}.commitment", out["refused"])

    def test_a_next_action_that_cites_it_is_refused(self):
        """`conformance.next_action_cites_closed` is a documented finding of
        the list contract, so an id in that cell is a reference Perry itself
        resolves — not decoration."""
        p = Project()
        tid = self.closed_row(p)
        _, other = p.run("add", "--title", "a row that cites it")
        code, _ = p.run("next", other["id"], "--next", f"pick up where {tid} left off")
        self.assertEqual(code, 0)
        code, out = self.purge(p, tid)
        self.assertEqual(code, 1)
        self.assertIn(f"{other['id']}.next_action", out["refused"])

    def test_a_linkage_register_that_names_it_is_refused(self):
        p = Project()
        tid = self.closed_row(p)
        phase = p.root / "phase"
        phase.mkdir(exist_ok=True)
        (phase / "001-linkage.md").write_text(
            "---\nlinkage: 1\nobjectives:\n  - id: O1\n    krs:\n"
            "      - id: P-O1.1\n        title: \"a key result\"\n"
            f"        tasks: [\"{tid}\"]\n---\n")
        code, out = self.purge(p, tid)
        self.assertEqual(code, 1)
        self.assertIn("001-linkage.md", out["refused"])
        self.assertIn("krs[].tasks", out["refused"])

    def test_the_goals_store_linked_field_is_refused(self):
        p = Project()
        tid = self.closed_row(p)
        (p.root / "okr.jsonl").write_text(json.dumps(
            {"kind": "kr", "id": "KR-O1.1", "text": "a key result",
             "linked": tid}) + "\n")
        code, out = self.purge(p, tid)
        self.assertEqual(code, 1)
        self.assertIn("okr.jsonl KR-O1.1.linked", out["refused"])

    def test_a_cited_evidence_document_that_names_it_is_refused(self):
        p = Project()
        tid = self.closed_row(p)
        (p.root / "review.md").write_text(
            f"# A review\n\nThe fix was checked against {tid}.\n")
        _, other = p.run("add", "--title", "a reviewed row")
        code, _ = p.run("evidence", other["id"], "--evidence", "`review.md`")
        self.assertEqual(code, 0)
        code, out = self.purge(p, tid)
        self.assertEqual(code, 1)
        self.assertIn("review.md", out["refused"])
        self.assertIn(other["id"], out["refused"])


class TestWhatIsNotALiveReference(PurgeCase):
    """The other half, and the one that decides whether the command can run at
    all.

    Read `bin/perry-task § live_references` for the argument. In short: a
    pointer is resolved by a reader; a record of what happened is history and
    goes on being true. Taken as *any mention anywhere*, the refusal is one
    nothing can ever pass — `perry-task add` writes a journal line naming every
    id it mints, so the deliverable would refuse its own first use.
    """

    def test_the_journal_naming_it_does_not_refuse(self):
        """The decisive case. `add` and `drop` both wrote this id into the
        journal, so if narrative counted, no tool-created row could ever be
        removed."""
        p = Project()
        tid = self.closed_row(p)
        self.assertIn(tid, p.journal(), "the fixture is not exercising the case")
        code, out = self.purge(p, tid)
        self.assertEqual(code, 0, out)

    def test_the_event_log_naming_it_does_not_refuse(self):
        p = Project()
        tid = self.closed_row(p)
        self.assertIn(tid, [e.get("id") for e in p.events()])
        self.assertEqual(self.purge(p, tid)[0], 0)

    def test_a_document_nothing_cites_does_not_refuse(self):
        """Refusing on an uncited file is refusing on the repository: any
        markdown anybody ever wrote about the row would pin it in the store
        forever."""
        p = Project()
        tid = self.closed_row(p)
        (p.root / "notes.md").write_text(f"# Notes\n\nwe once had {tid}.\n")
        code, out = self.purge(p, tid)
        self.assertEqual(code, 0, out)

    def test_a_cited_source_file_naming_it_does_not_refuse(self):
        """Measured on Perry's own project while this was built: `bin/perry-task`
        is cited as evidence by three records, and this function's own comment
        naming a swept id made the first dry run refuse itself. A code comment
        recording why a line exists is history, and `bin/perry-explain §
        walk_md` — Perry's id resolver — reads markdown and nothing else."""
        p = Project()
        tid = self.closed_row(p)
        (p.root / "impl.py").write_text(f"# written for {tid}\nx = 1\n")
        _, other = p.run("add", "--title", "a row citing source")
        p.run("evidence", other["id"], "--evidence", "`impl.py`")
        code, out = self.purge(p, tid)
        self.assertEqual(code, 0, out)

    def test_an_evidence_filename_that_starts_with_the_id_does_not_refuse(self):
        """`TASK-081-review.md` contains `TASK-081` and is not a citation of it
        — it is a filename. Measured on Perry's own store: **109 of 176**
        `Evidence` cells carry a `TASK-nnn` token and essentially all of them
        are paths, so a `\\b`-only boundary makes the command refuse every row
        on the project."""
        p = Project()
        tid = self.closed_row(p)
        doc = p.root / f"{tid}-review.md"
        doc.write_text("# A review\n\nnothing here names the row.\n")
        _, other = p.run("add", "--title", "a reviewed row")
        p.run("evidence", other["id"], "--evidence", f"`{doc.name}`")
        code, out = self.purge(p, tid)
        self.assertEqual(code, 0, out)

    def test_the_purged_rows_own_fields_do_not_refuse(self):
        """A row that declares its own dependency, evidence and next action is
        not a reference to itself."""
        p = Project()
        _, a = p.run("add", "--title", "a row with cells",
                     "--next", "finish it", "--depends", "TASK-900")
        p.run("drop", a["id"], "--reason", "probe")
        code, out = self.purge(p, a["id"])
        self.assertEqual(code, 0, out)

    def test_the_boundary_is_a_hyphen_on_both_sides(self):
        fn = PT.names_id
        self.assertTrue(fn("blocked on TASK-081.", "TASK-081"))
        self.assertTrue(fn("[TASK-081]", "TASK-081"))
        self.assertFalse(fn("evidence/TASK-081-v4-review.md", "TASK-081"))
        self.assertFalse(fn("TASK-0811", "TASK-081"))
        self.assertFalse(fn("XTASK-081", "TASK-081"))


# ── the removal survives the reconstruction ───────────────────────────────


class TestTheDerivationHonoursIt(PurgeCase):
    """The half that makes `purge` a removal rather than a deferred one.

    `perry-tasks write --from-board` rebuilds the store from `BOARD.md` **plus
    the event log**, and it rebuilds closed rows out of the log alone — that is
    exactly how the three smoke-test rows reached `tasks.jsonl` in the first
    place: they were never on the board, they were `add` + `drop` in the log,
    and the migration derived them. A `purge` that only deleted a JSONL line
    would be undone by the next rebuild, silently.
    """

    def test_a_rebuild_from_the_board_does_not_resurrect_it(self):
        p = Project()
        tid = self.closed_row(p)
        self.purge(p, tid)
        r = subprocess.run(
            ["python3", str(TASKS), "write", "--from-board",
             "--root", str(p.root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIsNone(self.record(p, tid),
                          "`write --from-board` rebuilt the purged record out "
                          "of its own `add` and `drop` events")

    def test_a_closed_row_that_was_not_purged_still_survives_a_rebuild(self):
        """The guard on the guard: the deletion must be scoped to the id the
        purge event names, not to closed rows generally."""
        p = Project()
        keep = self.closed_row(p, "a closed row that stays")
        tid = self.closed_row(p)
        self.purge(p, tid)
        subprocess.run(["python3", str(TASKS), "write", "--from-board",
                        "--root", str(p.root)], capture_output=True, text=True)
        self.assertIsNotNone(self.record(p, keep))

    def test_the_id_is_not_reissued(self):
        """`mint_id` reads the log, and the log still carries the `add`. A
        purge that freed the number would let a new row inherit a closed row's
        history in every consumer that joins on `id`."""
        p = Project()
        tid = self.closed_row(p)
        self.purge(p, tid)
        _, fresh = p.run("add", "--title", "the next row")
        self.assertNotEqual(fresh["id"], tid)
        self.assertGreater(fresh["id"], tid)

    def test_it_produces_no_drift(self):
        p = Project()
        tid = self.closed_row(p)
        self.purge(p, tid)
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        drift = json.loads(r.stdout)["board"]["drift"]
        self.assertEqual(drift["drift"], 0, f"a purge produced drift: {drift}")
        self.assertEqual(drift["orphaned"], [])


# ── the payload's shape does not move ─────────────────────────────────────


class TestTheContractShapeIsUnchanged(PurgeCase):
    """TASK-167 verification 3, stated over the fixture rather than over
    Perry's own payload: removal changes what `tasks[]` HOLDS, never what its
    objects look like."""

    def test_every_surviving_task_carries_the_same_keys(self):
        p = Project()
        _, live = p.run("add", "--title", "an open row")
        tid = self.closed_row(p)
        _, before = p.run("list", "--all")
        keys = {t["id"]: sorted(t) for t in before["tasks"]}
        self.purge(p, tid)
        _, after = p.run("list", "--all")
        for t in after["tasks"]:
            self.assertEqual(sorted(t), keys[t["id"]])
        self.assertEqual(sorted(after), sorted(before))
        self.assertEqual(sorted(after["conformance"]),
                         sorted(before["conformance"]))
        self.assertIn(live["id"], [t["id"] for t in after["tasks"]])

    def test_the_contract_version_does_not_move(self):
        """No key is added, removed or retyped, and no value is computed
        differently: `tasks[]` has always been the records the store holds, and
        `purge` changes the store rather than the payload. The page says so in
        prose instead — see `schema/task-list-contract.md § A record can leave
        the store`."""
        p = Project()
        tid = self.closed_row(p)
        self.purge(p, tid)
        _, out = p.run("list", "--all")
        self.assertEqual(out["contract"], PT.LIST_CONTRACT)

    def test_the_page_says_a_record_can_leave_the_store(self):
        """A promise not to bump the version is only honest if the page says
        the thing the version would have announced."""
        page = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        self.assertIn("## A record can leave the store", page)
        self.assertIn("perry-task purge", page)


# ── the registers a new subcommand has to reach ───────────────────────────


class TestItIsDeclaredEverywhereItHasToBe(unittest.TestCase):

    def test_it_is_dispatchable_and_classified_as_a_task_event(self):
        self.assertIn("purge", PT.COMMANDS)
        self.assertIn("purge", PT.TASK_ROW_COMMANDS)
        self.assertIn("purge", PT.TASK_EVENTS)
        self.assertNotIn("purge", PT.SECTION_EVENTS)
        self.assertNotIn("purge", PT.READ_ONLY_COMMANDS)

    def test_the_pair_it_carries_is_declared(self):
        self.assertEqual(PT.EVENT_FIELD["purge"], "status")

    def test_the_usage_banner_advertises_it(self):
        """A subcommand a user cannot discover is one they will hand-edit
        around — and hand-editing the store is the thing this row exists
        against."""
        usage = re.search(r"^Usage:\n(.*?)\n\n", PT.__doc__ or "", re.M | re.S)
        self.assertIn("perry-task purge", usage.group(1))

    def test_the_events_contract_documents_the_kind(self):
        page = (PERRY_HOME / "schema" / "events-list-contract.md").read_text()
        self.assertIn("`purge` · `perry-task purge`", page)

    def test_the_two_names_are_not_confusable(self):
        """TASK-167 decision 1. `drop` records a decision about the WORK and
        leaves the record; `purge` removes the RECORD. Neither name is a
        prefix of the other, so no abbreviation or completion reaches both."""
        self.assertFalse("purge".startswith("drop"))
        self.assertFalse("drop".startswith("purge"))
        self.assertIsNot(PT.COMMANDS["purge"], PT.COMMANDS["drop"])


# ── the blank line in the append-only log ─────────────────────────────────


class TestABlankLineInTheLogIsTolerated(unittest.TestCase):
    """TASK-167's second half, and the whole of it.

    `.perry/events.jsonl` carries a blank line — on Perry's own log, at line 67
    — and the file is APPEND-ONLY, so the row is not "remove the line". It is
    "prove every reader tolerates one, and open a finding if any does not".

    Proved on a log this test writes, so it goes on meaning something after
    somebody rotates or appends to Perry's own. Every reader is exercised
    through its shipped entry point, not by asserting that a `strip()` appears
    in the source.
    """

    def with_blank_lines(self) -> Project:
        p = Project()
        _, a = p.run("add", "--title", "a row before the gap")
        p.run("drop", a["id"], "--reason", "probe")
        _, b = p.run("add", "--title", "a row after the gap")
        log = p.root / ".perry" / "events.jsonl"
        lines = log.read_text().split("\n")
        body = [l for l in lines if l.strip()]
        # A blank line at the head, in the middle, at the tail, and two in a
        # row — every position a hand-edit or a lost write can leave one.
        gapped = ([""] + body[:1] + [""] + body[1:2] + ["", ""] + body[2:]
                  + ["", ""])
        log.write_text("\n".join(gapped))
        self.assertGreater(len([l for l in log.read_text().split("\n")
                                if not l.strip()]), 4)
        self.p, self.live = p, b["id"]
        return p

    def test_the_writers_own_reader_skips_it(self):
        p = self.with_blank_lines()
        events = PT.read_events(p.root)
        self.assertTrue(events)
        self.assertIn(self.live, [e.get("id") for e in events])

    def test_list_still_answers(self):
        p = self.with_blank_lines()
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        self.assertIn(self.live, [t["id"] for t in out["tasks"]])
        self.assertTrue(out["conformance"]["has_event_log"])

    def test_the_events_feed_still_answers(self):
        p = self.with_blank_lines()
        code, out = p.run("events")
        self.assertEqual(code, 0, out)
        self.assertGreater(out["total"], 0)

    def test_drift_reconciliation_still_answers(self):
        """The reader with its own second parse of the file — `perry-state §
        reconcile_drift` re-reads `events.jsonl` line by line rather than
        going through `read_events`, so it is a distinct tolerance claim."""
        p = self.with_blank_lines()
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        drift = json.loads(r.stdout)["board"]["drift"]
        self.assertTrue(drift["checked"])
        self.assertEqual(drift["drift"], 0)

    def test_the_linter_still_answers(self):
        p = self.with_blank_lines()
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-lint"),
             "--root", str(p.root)], capture_output=True, text=True)
        self.assertNotIn("Traceback", r.stderr)

    def test_a_write_still_lands_on_a_gapped_log(self):
        """The tolerance that matters most: the log is append-only, so the
        blank line is permanent and every future write has to cross it."""
        p = self.with_blank_lines()
        code, out = p.run("start", self.live)
        self.assertEqual(code, 0, out)
        self.assertIn("start", [e.get("event") for e in p.events()])

    def test_a_purge_still_lands_on_a_gapped_log(self):
        p = self.with_blank_lines()
        _, c = p.run("add", "--title", "a row to remove")
        p.run("drop", c["id"], "--reason", "probe")
        code, out = p.run("purge", c["id"], "--reason", REASON)
        self.assertEqual(code, 0, out)
        rows = [json.loads(l) for l in
                (p.root / "tasks.jsonl").read_text().split("\n") if l.strip()]
        self.assertNotIn(c["id"], [r["id"] for r in rows])

    def test_the_log_is_never_rewritten_by_any_of_this(self):
        """The constraint, asserted rather than assumed: a purge APPENDS. The
        bytes that were in the file before are still the file's prefix."""
        p = self.with_blank_lines()
        log = p.root / ".perry" / "events.jsonl"
        _, c = p.run("add", "--title", "a row to remove")
        p.run("drop", c["id"], "--reason", "probe")
        before = log.read_bytes()
        p.run("purge", c["id"], "--reason", REASON)
        self.assertTrue(log.read_bytes().startswith(before),
                        "a write rewrote the append-only log instead of "
                        "appending to it")


if __name__ == "__main__":
    unittest.main()
