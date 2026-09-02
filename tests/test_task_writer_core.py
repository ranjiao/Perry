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

class TestFormatIsMechanized(unittest.TestCase):
    """V3: the tool reproduces the format, it does not redefine it."""

    def test_every_hand_written_row_in_perrys_own_board_round_trips(self):
        """The real check. Perry's board was written by hand over a whole
        session; if the tool's renderer disagrees with any of it, adopting the
        tool would silently rewrite rows the moment they were touched.

        Quantified over whatever the board holds, and over nothing else.
        `assertGreater(len(rows), 5)` used to stand at the top of it
        (TASK-151) — a proxy for "the corpus is not empty" that was really a
        census: a board that closed its way below six open rows would have
        reddened a test about ROW FORMATTING. The not-empty guard is a
        property of the reader, not of this project's backlog, so it is proved
        below on a board this module wrote.
        """
        board = PT.Board(PERRY_HOME / "perry" / "BOARD.md")
        for _, raw, _ in board.rows():
            self.assertEqual(
                PT.render_row(PT.split_row(raw)), raw,
                "the tool renders this hand-written row differently:\n"
                f"  hand: {raw}\n  tool: {PT.render_row(PT.split_row(raw))}")

    def test_the_round_trip_above_is_reading_rows_at_all(self):
        """TASK-151's other half: the loop above is vacuous over an empty list.

        `Board.rows()` walking away with nothing — a heading renamed, a
        separator the table reader stopped recognising, a priority it no
        longer maps — would leave that test green while checking no row at
        all. So the reader is held to a board whose roster is written down
        HERE, in the shapes the format actually uses: full cells, blank cells,
        the `—` marker, a pipe-free link, and a row in every section the
        walker is supposed to see.
        """
        board = PT.Board(self.write_board(ROUND_TRIP_BOARD))
        rows = board.rows()
        self.assertEqual([cells["id"] for _, _, cells in rows],
                         list(ROUND_TRIP_ROW_IDS),
                         "the reader did not find the rows this fixture "
                         "wrote — the round-trip above may be looping over "
                         "nothing")
        self.assertEqual([priority for priority, _, _ in rows],
                         list(ROUND_TRIP_ROW_PRIORITIES))
        for _, raw, _ in rows:
            self.assertEqual(
                PT.render_row(PT.split_row(raw)), raw,
                "the tool renders this row differently:\n"
                f"  hand: {raw}\n  tool: {PT.render_row(PT.split_row(raw))}")

    def write_board(self, text: str) -> Path:
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = Path(d.name) / "BOARD.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_the_shipped_template_round_trips_too(self):
        board = PT.Board(PERRY_HOME / "work" / "state" / "BOARD_TEMPLATE.md")
        for _, raw, _ in board.rows():
            self.assertEqual(PT.render_row(PT.split_row(raw)), raw)


class TestAtomicThreeWayWrite(unittest.TestCase):
    """The two canonical files together; the derived event may fail alone.

    The class used to be named for a stronger guarantee — "board, journal and
    event, or none of them" — that four surfaces stated and the code never
    provided, and every test in it exercised a *pre-write validation refusal*.
    An assertion satisfied by the setup cannot fail on the behavior it names:
    `add` with no `--title` never reaches `commit()`, so nothing here touched
    the ordering the claim was about. `test_the_event_may_be_lost_but_never_the_row`
    is the one that goes through `commit()`.
    """

    def test_add_writes_all_three(self):
        p = Project()
        code, out = p.run("add", "--title", "Ship it", "--priority", "P0")
        self.assertEqual(code, 0, out)
        self.assertIn("| TASK-001 | Ship it |", p.board())
        self.assertIn("[TASK-001]", p.journal())
        self.assertEqual(len(p.events()), 1)
        self.assertEqual(p.events()[0]["event"], "add")

    def test_a_refusal_writes_nothing(self):
        p = Project()
        before, ev = p.board(), len(p.events())
        code, out = p.run("add", "--priority", "P0")  # no --title
        self.assertEqual(code, 1)
        self.assertIn("refused", out)
        self.assertEqual(p.board(), before, "a refused call still touched the board")
        self.assertEqual(len(p.events()), ev)
        self.assertEqual(p.journal(), "")

    def test_dry_run_touches_nothing(self):
        p = Project()
        before = p.board()
        code, out = p.run("add", "--title", "X", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.board(), before)
        self.assertEqual(p.events(), [])

    def test_concurrent_writes_do_not_lose_rows(self):
        """`BOARD.md` is read at `Board.__init__` and written at `commit()`.
        Between those, another process can read the same board — and the second
        rename discards the first process's row.

        Measured before the fix, not theorized: five concurrent `add` calls
        left **two** rows, with `TASK-001` and `TASK-002` each issued twice.
        The event log took all five, because it is opened `O_APPEND`: the
        append-only file survived precisely the race the read-modify-write
        document lost.

        `autopilot` dispatches concurrently by design, so this is a live path.

        The lock has to wrap the read too. One around `commit()` alone would
        still let both processes mint the same id from the same stale board —
        which is why this asserts on unique ids and not only on row count.
        """
        p = Project()
        n = 8
        procs = [subprocess.Popen(
            ["python3", str(TOOL), "add", "--title", f"concurrent {i}",
             "--priority", "P0", *Project.ADD_DEFAULTS,
             "--root", str(p.root), "--json"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for i in range(n)]
        for proc in procs:
            proc.wait()

        rows = [l for l in p.board().split("\n") if l.startswith("| TASK-")]
        ids = re.findall(r"TASK-\d+", p.board())
        self.assertEqual(len(rows), n, f"{n - len(rows)} row(s) were lost")
        self.assertEqual(len(set(ids)), n, f"an id was issued twice: {ids}")
        self.assertEqual(len(p.events()), n)

    def test_locking_leaves_nothing_in_the_project(self):
        """The lock is Perry's only piece of pure runtime state, and it must
        not become the user's problem.

        Its first placement was `state_root/.board.lock`, which showed up as
        `?? .board.lock` in a real Perry project the same night it shipped —
        untracked and unignored, because a consumer repo does not inherit
        Perry's own `.gitignore`. A tool that makes every user edit their
        ignore file to stay clean has pushed its bookkeeping onto them.

        It now lives in the temp dir, keyed by a hash of the state root.
        """
        p = Project()
        before = {x.name for x in p.root.iterdir()}
        p.run("add", "--title", "X", "--priority", "P0")
        after = {x.name for x in p.root.iterdir()}
        # `tasks.jsonl` is not bookkeeping — it is what the write writes
        # (ADR-007, TASK-089). `BOARD.md` already existed, so the store is the
        # one new canonical file a first write creates. The lock is still the
        # thing this test is about, and it is still not here.
        self.assertEqual(
            after - before, {"journal"},
            f"a write left files in the project beyond the journal and the "
            f"store: {sorted(after - before - {'journal'})}")
        self.assertFalse(
            list(p.root.rglob("*.lock")),
            "a lock file was written into the project tree")

    def test_the_event_may_be_lost_but_never_the_row(self):
        """Reaches `commit()` and makes the event append fail, which is the
        only path where the ordering matters.

        Before this, an unwritable `.perry/` produced an uncaught
        `PermissionError` — a traceback, exit 1, and board + journal already on
        disk. Exit 1 is documented as "nothing was written", so a caller
        following the docs would retry and raise a second row for work already
        recorded. The canonical pair is recoverable: ordinary failures roll
        back and a crash is completed on the next locked run. The derived event
        is reported when it goes missing.
        """
        p = Project()
        ev_dir = p.root / ".perry"
        (ev_dir / "events.jsonl").write_text("")
        mode = ev_dir.stat().st_mode
        os.chmod(ev_dir / "events.jsonl", 0o444)
        os.chmod(ev_dir, 0o555)
        try:
            code, out = p.run("add", "--title", "atomicity probe", "--priority", "P0")
        finally:
            os.chmod(ev_dir, mode)
            os.chmod(ev_dir / "events.jsonl", 0o644)

        self.assertNotIn("Traceback", str(out),
                         "an unwritable event log crashed instead of reporting")
        self.assertEqual(code, 0,
                         "the canonical write succeeded; exit 1 would tell the "
                         "caller to retry and duplicate the row")
        self.assertIn("atomicity probe", p.board(), "the row was lost")
        self.assertIn("TASK-001", p.journal(), "the journal line was lost")
        self.assertEqual(p.events(), [], "the event should not have been written")

        # And the row is honestly reported as having no creating event.
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout)["board"]["drift"]["unrecorded"], 1)


class TestALocalizedBoard(unittest.TestCase):
    """`perry-task` was the only component in the stack that never read
    `schema § i18n.columns`.

    `perry-state` and `perry-lint` both resolve headers through it;
    the writer keyed rows on hardcoded English. TASK-033 then routed *every*
    board write through the writer — so the migration handed the one component
    that could corrupt a localized board responsibility for all of them.

    The failures were silent and exit 0. `add` wrote a row of empty cells while
    the journal line and the event both asserted the task existed; `start` and
    `status` were board no-ops that still recorded the transition. The tool
    built to eliminate board-vs-history divergence produced it on its first
    write, on any project using the document language Perry advertises.

    No test in the suite had ever run the tool against a localized board, and
    Perry's own board is English — so neither dogfooding nor three review
    rounds could see it.
    """

    def zh(self) -> "Project":
        p = Project(board=ZH_BOARD)
        # Overwrites the config `Project` wrote, so it has to carry `""`
        # forward itself — `ZH_BOARD` is deliberately not Perry's shape.
        (p.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: 中文\n"
            "- Repo layout: single\n- State root: .\n")
        return p

    def row(self, p: "Project") -> list[str]:
        line = next(l for l in p.board().split("\n") if l.startswith("| TASK-001 |"))
        return [c.strip() for c in line.strip().strip("|").split("|")]

    def test_add_populates_the_row_rather_than_emptying_it(self):
        p = self.zh()
        code, out = p.run("add", "--title", "本地化测试", "--priority", "P0")
        self.assertEqual(code, 0, out)
        cells = self.row(p)
        self.assertEqual(cells[0], "TASK-001")
        self.assertEqual(cells[1], "本地化测试", "the title did not reach 标题")
        self.assertEqual(cells[3], "not_started", "the status did not reach 状态")
        self.assertNotEqual(cells, [""] * len(cells))

    def test_a_transition_actually_moves_the_cell(self):
        """`start` rebuilt the row from Chinese-keyed cells, matched no English
        header, and wrote it back byte-identical — while the event recorded
        `to: in_progress`. A board no-op that reports success is worse than a
        refusal: it is the divergence, manufactured by the tool."""
        p = self.zh()
        p.run("add", "--title", "任务", "--priority", "P0")
        code, out = p.run("start", "TASK-001")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.row(p)[3], "in_progress",
                         "the event says in_progress and the board does not")

    def test_a_new_column_joins_in_the_boards_own_language(self):
        """Appending `Stage` beside `阶段序列` would leave a header in two
        languages, which `perry-lint`'s localized match regexes then disagree
        about."""
        p = self.zh()
        (p.root / ".perry" / "config.md").write_text(
            (p.root / ".perry" / "config.md").read_text()
            + "\n## Tracks\n\n"
            "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| blog | pipeline | commitments | brief->draft | — | — | — | V5 |\n")
        code, out = p.run("add", "--title", "文章", "--track", "blog", "--priority", "P0")
        self.assertEqual(code, 0, out)
        header = next(l for l in p.board().split("\n") if l.startswith("| 编号 |"))
        self.assertIn("阶段", header, "the new column was added in English")
        self.assertNotIn("Stage", header)

    def test_an_unreadable_header_is_refused_not_blanked(self):
        """A refusal names the header it could not read. A blank row names
        nothing, and exits 0."""
        p = Project(board=ZH_BOARD.replace("| 编号 | 标题 |", "| 甲 | 乙 |"))
        code, out = p.run("add", "--title", "X", "--priority", "P0")
        self.assertEqual(code, 1, f"an unresolvable header was written to: {out}")
        self.assertIn("i18n.columns", str(out))
        self.assertNotIn("TASK-001", p.board())

    def test_drift_is_clean_on_a_board_the_tool_wrote_in_chinese(self):
        """The end-to-end statement: the localized path produces no false
        signal in the detector either."""
        p = self.zh()
        p.run("add", "--title", "甲任务", "--priority", "P0")
        p.run("add", "--title", "乙任务", "--priority", "P1")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        d = json.loads(r.stdout)["board"]["drift"]
        self.assertEqual((d["drift"], d["unrecorded"]), (0, 0), d)


class TestWhatTheToolComputes(unittest.TestCase):
    """DESIGN-004 §5.2 — every field an agent currently supplies and gets wrong."""

    def test_ids_are_minted_and_never_collide(self):
        p = Project()
        ids = []
        for i in range(3):
            _, out = p.run("add", "--title", f"task {i}")
            ids.append(out["id"])
        self.assertEqual(ids, ["TASK-001", "TASK-002", "TASK-003"])
        self.assertEqual(len(set(ids)), 3)

    def test_a_closed_task_keeps_its_number(self):
        """Reading only the board would hand a live id to a second task and
        silently re-point every reference to the first."""
        p = Project()
        _, a = p.run("add", "--title", "first")
        p.run("done", a["id"], "--evidence", "x.md", "--rung", "V3")
        self.assertNotIn(a["id"], p.board(), "closed row should leave the board")
        _, b = p.run("add", "--title", "second")
        self.assertNotEqual(b["id"], a["id"],
                            "a closed task's id was reused — every reference to "
                            "the first now silently points at the second")

    def test_a_closed_tasks_number_survives_deleting_the_event_log(self):
        """The event log is declared derived and disposable — "delete it and
        what is lost is history resolution and drift detection, not truth."

        That was false for exactly one thing. A closed task is in neither the
        board (its row was removed at close) nor, after a delete, the log — so
        `mint_id`, which read only those two, reissued its number. Every journal
        line, evidence file and commit message naming the old task then
        silently pointed at the new one. **A reused id is truth, not history
        resolution.**

        The journal closes it: canonical, append-only, and carrying a creation
        line for every task ever raised — the one record every procedure here
        forbids editing, including on drop and close.

        Found by demonstrating to the user where task state lives, not by a
        review: closing a task and deleting the log are each ordinary, and only
        doing both in sequence shows it.
        """
        p = Project()
        _, a = p.run("add", "--title", "first")
        p.run("done", a["id"], "--evidence", "x.md", "--rung", "V3")
        (p.root / ".perry" / "events.jsonl").unlink()

        code, b = p.run("add", "--title", "after the log was deleted")
        self.assertEqual(code, 0, b)
        self.assertNotEqual(
            b["id"], a["id"],
            f"{a['id']} was reissued after the disposable log was deleted — "
            f"the journal already carried it")

    def test_timestamps_are_observed_not_asserted(self):
        """**And they carry their offset** (TASK-144). The stamp is local wall
        clock, so the log's text keeps rising across the zoneless lines written
        before this, and it says which offset that wall clock was read at — a
        zoneless stamp is what let `current_staleness` compare the log against
        the register's UTC as though the two were one clock."""
        p = Project()
        p.run("add", "--title", "X")
        ts = p.events()[0]["ts"]
        self.assertRegex(
            ts, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")

    def test_a_bad_rung_is_refused_before_anything_is_written(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        before = p.board()
        code, out = p.run("done", a["id"], "--evidence", "e.md", "--rung", "V9")
        self.assertEqual(code, 1)
        self.assertIn("V9", str(out))
        self.assertEqual(p.board(), before)

    def test_v0_is_refused_by_name(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, out = p.run("done", a["id"], "--evidence", "e.md", "--rung", "V0")
        self.assertEqual(code, 1)
        self.assertIn("asserted", str(out))

    def test_done_without_evidence_is_refused(self):
        """Perry's oldest rule, now enforced at write time rather than reported
        after the fact."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, out = p.run("done", a["id"])
        self.assertEqual(code, 1)
        self.assertIn("evidence", str(out))


class TestLifecycle(unittest.TestCase):
    def test_start_moves_status_and_records_both_ends(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, _ = p.run("start", a["id"])
        self.assertEqual(code, 0)
        self.assertIn("in_progress", p.board())
        ev = p.events()[-1]
        self.assertEqual((ev["from"], ev["to"]), ("not_started", "in_progress"))

    def test_starting_twice_is_refused(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        p.run("start", a["id"])
        code, _ = p.run("start", a["id"])
        self.assertEqual(code, 1)

    def test_done_takes_the_rung_from_the_tracks_default(self):
        p = Project(tracks=BASIC_MODE_TRACKS)
        _, a = p.run("add", "--title", "X", "--track", "blog", "--priority", "P0")
        _, out = p.run("done", a["id"], "--evidence", "e.md")
        self.assertEqual(out["rung"], "V5", "pipeline's declared default rung was ignored")

    def test_the_event_log_is_disposable(self):
        """DESIGN-004 §5.3: delete it and Perry still works. This is the
        constraint that keeps the tool from becoming a database with a markdown
        export."""
        p = Project()
        p.run("add", "--title", "X")
        board_before = p.board()
        (p.root / ".perry" / "events.jsonl").unlink()
        code, out = p.run("list")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.board(), board_before)
        code, _ = p.run("add", "--title", "Y")
        self.assertEqual(code, 0, "the tool could not write without its own log")


class TestJournalAppendsChronologically(unittest.TestCase):
    """A day's journal accumulates one `## Status changes` per entry.

    Appending to the first one buries an 18:33 change inside the block written
    at 09:00. Perry's own journal had seventeen such sections on the day this
    tool shipped, and the tool's first real write landed on line 12 of a
    1026-line file. An append-only record is only chronological if new lines
    land at the end of it.
    """

    MULTI = ("# 2026-08-16\n\n## Status changes\n\n- [TASK-001] a → b · early\n\n"
             "## Notes\n\nprose\n\n---\n\n## Second entry\n\n"
             "## Status changes\n\n- [TASK-002] a → b · later\n\n## Notes\n\nmore prose\n")

    def test_the_line_lands_in_the_last_section(self):
        out = PT.append_status_change(self.MULTI, "- [TASK-003] a → b · newest")
        idx_new = out.index("TASK-003")
        idx_later = out.index("TASK-002")
        self.assertGreater(idx_new, idx_later,
                           "the new line was inserted before an older one")

    def test_earlier_sections_are_untouched(self):
        out = PT.append_status_change(self.MULTI, "- [TASK-003] a → b · newest")
        head = out[:out.index("## Second entry")]
        self.assertNotIn("TASK-003", head)
        self.assertIn("TASK-001", head)

    def test_a_journal_with_no_section_gets_one(self):
        out = PT.append_status_change("# 2026-08-16\n", "- [TASK-001] a → b")
        self.assertIn("## Status changes", out)
        self.assertIn("TASK-001", out)

    def test_an_empty_journal_gets_a_heading_too(self):
        out = PT.append_status_change("", "- [TASK-001] a → b")
        self.assertTrue(out.startswith("# "))
        self.assertIn("TASK-001", out)


class TestEveryStatusHasAToolPath(unittest.TestCase):
    """A gap in coverage becomes a permanent false signal once detection exists.

    `dispatch` moves rows into `review` on every run and the tool could not
    write `review`, so every dispatch manufactured a post-tool edit that drift
    detection would report forever — the same self-inflicted-drift shape that
    an unmigrated `drop-task` produced, found by a review one level out.
    """

    STATUSES = ["not_started", "blocked", "in_progress", "review", "done", "dropped"]

    def test_the_schema_enum_is_what_the_tool_accepts(self):
        """Named for a check it did not perform: it compared the schema to a
        hardcoded list and never invoked anything. Now it asks the tool."""
        schema = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
        self.assertEqual(schema["enums"]["task_status"], self.STATUSES)

        p = Project()
        p.run("add", "--title", "X")
        code, out = p.run("status", "TASK-001", "--status", "nonesuch")
        self.assertEqual(code, 1)
        for want in self.STATUSES:
            self.assertIn(want, str(out),
                          f"the tool's refusal does not offer {want!r}")

    def test_blocked_and_review_have_a_tool_path(self):
        p = Project()
        _, a = p.run("add", "--title", "X")
        for want, extra in (("review", []), ("blocked", ["--reason", "waiting on USER-001"])):
            code, out = p.run("status", a["id"], "--status", want, *extra)
            self.assertEqual(code, 0, f"{want}: {out}")
            self.assertIn(want, p.board())

    def test_blocked_without_a_named_dependency_is_refused(self):
        """A blocked row with no named dependency is a row nobody can unblock."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, out = p.run("status", a["id"], "--status", "blocked")
        self.assertEqual(code, 1)
        self.assertIn("reason", str(out))

    def test_status_refuses_the_closing_transitions(self):
        """`done` needs evidence and `dropped` needs a reason; letting `status`
        write them would route around both gates."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        for want in ("done", "dropped"):
            code, out = p.run("status", a["id"], "--status", want)
            self.assertEqual(code, 1, want)
            self.assertIn("perry-task", str(out))

    def test_every_accepted_command_runs_and_is_advertised(self):
        """The acceptance guard, the dispatch table and the "expected one of"
        message drifted apart twice.

        First `drop` was accepted and undispatched — a bare KeyError. Then
        `drop`, `status` and `resolve-intake` were dispatched and missing from
        the error message. Both were one list of command names written down
        three times, so `COMMANDS` is now the only copy and this test asserts
        the three readers agree.

        Reached through the CLI, not by importing the dict: what matters is
        that a name a user can type is a name that runs, and only invoking the
        process can show that.

        The "expected one of" half is deliberately weak — that message is
        literally `' / '.join(COMMANDS)`, so asserting it lists every command
        is a tautology. The check that carries weight is against the module
        **docstring**, which is a hand-maintained fourth copy that nothing kept
        in step: `--arrived`, `--owner`, `--commitment` and `--actor` had all
        shipped without it noticing.

        **`--root`, and why it is not decoration (TASK-249).** This loop used
        to invoke each name with no root at all. `perry-task` resolves its
        project root from `$PERRY_PROJECT`, else the cwd, and `tests/run` cds
        to the repository root — so all 29 commands ran against the live
        checkout. Twenty-eight refused for want of arguments. `intake-sweep`
        takes none: it discharged a REAL board row and moved four files —
        `.perry/events.jsonl`, `perry/BOARD.md`, `perry/intake.jsonl` and
        `perry/journal/<today>.md` — on every run of the suite, in whatever
        repository the suite ran in. It went unnoticed for months because the
        sweep is idempotent: the second run finds nothing left to discharge,
        so the natural check — run it twice and diff — reports nothing. It
        reached a coding branch's commit once and was caught only because an
        append-only file conflicted at merge.

        The root here is a throwaway `Project()`, which is what every other
        subprocess in this module already uses. `tests/tree_guard.py` is the
        structural half: it fails the suite if the checkout moves at all, for
        any reason, whether or not the write came through a fixture.
        """
        p = Project()
        tool = str(PERRY_HOME / "bin" / "perry-task")
        for name in PT.COMMANDS:
            r = subprocess.run(
                ["python3", tool, name, "--root", str(p.root)],
                capture_output=True, text=True)
            self.assertNotEqual(
                r.returncode, 2,
                f"{name!r} is dispatchable but the guard rejects it")
            self.assertNotIn(
                "Traceback", r.stderr,
                f"{name!r} crashed instead of refusing:\n{r.stderr}")

        r = subprocess.run(
            ["python3", tool, "nonesuch", "--root", str(p.root)],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

        usage = re.search(r"^Usage:\n(.*?)\n\n", PT.__doc__ or "", re.M | re.S)
        self.assertIsNotNone(usage, "the docstring's Usage block moved")
        documented = set(re.findall(r"^\s*perry-task\s+([a-z-]+)",
                                    usage.group(1), re.M))
        self.assertEqual(
            documented, set(PT.COMMANDS),
            f"the docstring and COMMANDS disagree — only in docstring: "
            f"{documented - set(PT.COMMANDS)}; missing from it: "
            f"{set(PT.COMMANDS) - documented}")

    def test_drop_requires_a_reason_and_leaves_no_orphan(self):
        """A hand-removed row leaves its `add` event with no row and no close —
        drift's second condition — so every hand drop manufactured false drift
        forever. `drop` was in the argument guard and missing from the dispatch
        table, crashing with a bare KeyError."""
        p = Project()
        _, a = p.run("add", "--title", "X")
        code, _ = p.run("drop", a["id"])
        self.assertEqual(code, 1, "drop without a reason should refuse")
        code, out = p.run("drop", a["id"], "--reason", "superseded")
        self.assertEqual(code, 0, out)
        self.assertNotIn(a["id"], p.board())
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"], capture_output=True, text=True)
        d = json.loads(r.stdout)["board"]["drift"]
        self.assertEqual(d["drift"], 0, f"a tool-executed drop produced drift: {d}")

    def test_resolve_intake_covers_the_other_two_outcomes(self):
        p = Project(tracks=MODE_TRACKS)
        p.run("intake", "--title", "a request")
        code, out = p.run("resolve-intake", "1", "--outcome", "dropped",
                          "--reason", "covered by the handbook")
        self.assertEqual(code, 0, out)
        row = next(l for l in p.board().split("\n") if "a request" in l)
        self.assertIn("dropped", row)
        self.assertIn("handbook", row)

    def test_a_queue_add_creates_the_intake_section(self):
        """`triage` step 0 gated itself on the section existing, and only
        `intake` created it — so the gate no-opped for every queue track."""
        p = Project(tracks=MODE_TRACKS)
        p.run("add", "--title", "X", "--track", "ops", "--priority", "P0")
        self.assertIn("## Intake", p.board())

    def test_add_honours_arrived_rather_than_silently_ignoring_it(self):
        """The flag was accepted and overwritten with today, writing a wrong
        SLA clock without complaint."""
        p = Project(tracks=MODE_TRACKS)
        p.run("add", "--title", "X", "--track", "ops", "--priority", "P0",
              "--arrived", "2026-08-01")
        row = next(l for l in p.board().split("\n") if l.startswith("| TASK-001 |"))
        self.assertIn("2026-08-01", row)

    def test_dispatch_and_autopilot_carry_the_invariant(self):
        """Both are loaded on their own, so the rule stated in subcommands.md
        never reaches them — it has to be restated where they are read."""
        for name in ("dispatch", "autopilot"):
            text = (PERRY_HOME / "work" / "reference" / f"{name}.md").read_text()
            self.assertIn("perry-task", text,
                          f"{name}.md never names the tool it must use")
            # Naming it once in a header would satisfy the line above while the
            # body instructed hand-edits throughout. Both files move rows, so
            # both must reach the subcommands that move them.
            for sub in ("start", "status"):
                self.assertRegex(
                    text, rf"perry-task[^\n]*\b{sub}\b|`{sub}`",
                    f"{name}.md moves rows but never reaches `perry-task {sub}`")


class TestRetitle(unittest.TestCase):
    """The gap `next` closed, one column over.

    TASK-021 was filed as "Recurrence register + `OKR.md § Commitments`". The
    second half turned out to belong to a different lane and was split into
    its own row, leaving a title describing work this row would never do —
    and no tool could correct it. `status` refuses a no-op, `next` writes a
    different cell, so the row could not close honestly without a hand edit.
    """

    def test_it_rewrites_the_title_and_touches_nothing_else(self):
        p = Project()
        _, a = p.run("add", "--title", "two things at once", "--priority", "P0")
        before = next(l for l in p.board().split("\n")
                      if l.startswith(f"| {a['id']} |"))
        code, out = p.run("retitle", a["id"], "--title", "one thing")
        self.assertEqual(code, 0, out)
        after = next(l for l in p.board().split("\n")
                     if l.startswith(f"| {a['id']} |"))
        self.assertIn("one thing", after)
        self.assertNotIn("two things at once", after)
        self.assertEqual(
            [c for c in PT.split_row(before)[2:]],
            [c for c in PT.split_row(after)[2:]],
            "retitle changed a cell that is not the title")

    def test_the_same_title_is_refused(self):
        """Same reason `status` refuses a no-op: a journal line asserting a
        change that did not happen."""
        p = Project()
        _, a = p.run("add", "--title", "a name", "--priority", "P0")
        code, _ = p.run("retitle", a["id"], "--title", "a name")
        self.assertEqual(code, 1)

    def test_an_empty_title_is_refused(self):
        p = Project()
        _, a = p.run("add", "--title", "a name", "--priority", "P0")
        code, out = p.run("retitle", a["id"])
        self.assertEqual(code, 1)
        self.assertIn("nobody can find", str(out))

    def test_it_is_its_own_event(self):
        """A reader has to be able to tell "what this is called changed" from
        "where this got to"; folding them loses both facts forever."""
        p = Project()
        _, a = p.run("add", "--title", "a name", "--priority", "P0")
        p.run("retitle", a["id"], "--title", "a better name")
        events = [json.loads(l)["event"]
                  for l in (p.root / ".perry" / "events.jsonl").read_text()
                  .strip().split("\n")]
        self.assertEqual(["add", "retitle"], events)

    def test_the_journal_records_what_it_used_to_be_called(self):
        """A title that changes with no record of the old one makes every
        earlier mention of this row unfindable."""
        p = Project()
        _, a = p.run("add", "--title", "old name", "--priority", "P0")
        p.run("retitle", a["id"], "--title", "new name")
        journal = "\n".join(
            f.read_text() for f in sorted((p.root / "journal").rglob("*.md")))
        # The retitle line specifically. Asserting "old name" appears anywhere
        # in the journal passes on `add`'s own line and cannot fail on the bug
        # it names — a mutation run proved exactly that.
        line = next(l for l in journal.split("\n") if "retitled" in l)
        self.assertIn("old name", line, "no record of what it used to be called")
        self.assertIn("new name", line)


class TestOnePriorityValidator(unittest.TestCase):
    """`cmd_add` refused an unknown priority; `cmd_route` did not, and fed it
    straight into `PRIORITY_RE[...]`.

    So `route --priority "P2 (低优先 carry)"` — a real project's full section
    heading, which is what anyone reading that board would type — raised
    `KeyError` instead of refusing. A traceback where a refusal belongs, for
    the third time in this file.

    The shape is the recurring one: one rule, two implementations, and the
    value is a dict key, so validating it in one place and indexing with it in
    another guarantees the mismatch eventually.
    """

    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | commitments | new->triaged->in_progress | — | 5d | monthly | V2 |\n")

    def test_route_refuses_an_unknown_priority_rather_than_crashing(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        code, out = p.run("route", "1", "--track", "ops",
                          "--priority", "P2 (低优先 carry)")
        self.assertEqual(code, 1, out)
        self.assertIn("not one of P0/P1/P2", str(out))

    def test_the_refusal_says_what_to_type_instead(self):
        """A refusal that names no way forward is a wall. The heading IS the
        thing `--group` takes."""
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        _, out = p.run("route", "1", "--track", "ops", "--priority", "nonsense")
        self.assertIn("--group", str(out))

    def test_add_and_route_refuse_identically(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        _, a = p.run("add", "--title", "x", "--priority", "ZZZ")
        _, r = p.run("route", "1", "--track", "ops", "--priority", "ZZZ")
        self.assertEqual(str(a), str(r),
                         "two callers, two different answers to one question")

    def test_a_valid_priority_still_routes(self):
        p = Project(tracks=self.TRACKS)
        p.run("intake", "--title", "a request")
        code, out = p.run("route", "1", "--track", "ops", "--priority", "P2")
        self.assertEqual(code, 0, out)


class TestTheRungIsWritableAndCorrectable(unittest.TestCase):
    """`add --rung V4` parsed, and wrote nothing. The flag existed, the cell
    did not get it, and the caller had no way to notice. `--rung NONSENSE` was
    accepted the same way.

    A flag that is silently ignored is worse than a missing one: a missing
    flag refuses, and this one reported success.

    And there was no writer at all for an open row — `--rung` lived only on
    `done`, which is far too late to argue about it. Third instance of one
    gap: `next` closed it for `Next action`, `retitle` for `Title`.

    `ADR-005` is what makes it load-bearing. The rung is now a claim about who
    is hurt when the work is wrong, and a claim nobody can correct without a
    hand edit is one nobody corrects.
    """

    def cell(self, p, tid):
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)],
                        PT.split_row(row))).get("verification", "")

    def test_add_writes_the_rung_it_was_given(self):
        p = Project()
        code, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
        self.assertEqual(code, 0, a)
        self.assertEqual("V4", self.cell(p, a["id"]))

    def test_an_unknown_rung_is_refused_not_dropped(self):
        p = Project()
        code, out = p.run("add", "--title", "x", "--priority", "P0",
                          "--rung", "NONSENSE")
        self.assertEqual(code, 1)
        self.assertIn("not one of", str(out))

    def test_the_refusal_does_not_offer_a_rung_it_will_refuse(self):
        """V0 is in the enum so a linter can name it. Listing it as a choice
        advertises a value the next check rejects."""
        p = Project()
        _, out = p.run("add", "--title", "x", "--priority", "P0",
                       "--rung", "NONSENSE")
        self.assertNotIn("V0", str(out))

    def test_v0_is_refused_by_name(self):
        p = Project()
        code, out = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V0")
        self.assertEqual(code, 1)
        self.assertIn("asserted", str(out))

    def test_rung_corrects_an_open_row(self):
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
        code, _ = p.run("rung", a["id"], "--rung", "V5")
        self.assertEqual(code, 0)
        self.assertEqual("V5", self.cell(p, a["id"]))

    def test_the_same_rung_is_refused(self):
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
        code, _ = p.run("rung", a["id"], "--rung", "V4")
        self.assertEqual(code, 1)

    def test_it_is_its_own_event(self):
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        p.run("rung", a["id"], "--rung", "V4")
        events = [json.loads(l)["event"]
                  for l in (p.root / ".perry" / "events.jsonl").read_text()
                  .strip().split("\n")]
        self.assertEqual(["add", "rung"], events)

    def test_add_and_done_answer_the_same_way(self):
        """Two validators for one enum is how they drift. `done` had one and
        `add` had none."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        _, add_out = p.run("add", "--title", "y", "--priority", "P0",
                           "--rung", "ZZZ")
        _, done_out = p.run("done", a["id"], "--evidence", "e", "--rung", "ZZZ")
        self.assertEqual(str(add_out), str(done_out))


class TestTheDelimiterIsACharacterPeopleWrite(unittest.TestCase):
    """`render_row` joined on `|` and escaped nothing, so a cell whose value
    contained a pipe silently became several cells and shifted every column
    after it.

    Not hypothetical: filing a task whose `Next action` quoted a markdown
    header — `` | ID | **Risk** | Opened | Status | `` — turned a 7-cell row
    into a 12-cell row on Perry's own board and pushed the word `Risk` into
    the `Verification` column, where the enum check caught it.

    Two things that make this worse than an ordinary escaping bug, and both
    are asserted below:

    - the corruption **survives** later tool writes. A row is read back with
      `dict(zip(header, cells))`, and a shifted row zips without complaint, so
      the wrong values are read as right and written out again.
    - nothing upstream refuses. The value is the user's prose; the delimiter is
      a character prose contains.
    """

    def test_a_pipe_in_a_value_round_trips(self):
        for cells in (["a", "b | c", "d"],
                      ["a", "|leading", "trailing|"],
                      ["a", "b || c", "d"]):
            with self.subTest(cells=cells):
                self.assertEqual(cells, PT.split_row(PT.render_row(cells)))

    def test_a_row_keeps_its_column_count(self):
        line = PT.render_row(["TASK-001", "quoting | ID | Title |", "Coding Agent"])
        self.assertEqual(3, len(PT.split_row(line)),
                         "a value containing the delimiter became extra cells")

    def test_an_already_escaped_pipe_is_not_double_escaped(self):
        """Reading a hand-written row that already uses markdown's `\\|` and
        writing it back must not grow a second backslash each time."""
        once = PT.render_row(PT.split_row(r"| a | b \| c | d |"))
        twice = PT.render_row(PT.split_row(once))
        self.assertEqual(once, twice, "escaping is not idempotent")

    def test_the_cell_survives_the_whole_write_path(self):
        p = Project()
        code, a = p.run("add", "--title", "x", "--priority", "P0",
                        "--next", "see | ID | Title | Owner | in the board")
        self.assertEqual(code, 0, a)
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {a['id']} |"))
        self.assertEqual(len(PT.split_row(header)), len(PT.split_row(row)),
                         "the row and its header stopped agreeing")
        cells = dict(zip([PT.norm(h) for h in PT.split_row(header)],
                         PT.split_row(row)))
        self.assertIn("| ID | Title | Owner |", cells["next action"])
        self.assertEqual("", cells.get("verification", ""),
                         "a value leaked into the column after it")


class TestOneCellWriterNotFour(unittest.TestCase):
    """`next`, `retitle` and `rung` were three copies of one twenty-line
    function, written weeks apart, each a copy of the one before. The fourth
    was about to be written for `Evidence` — a corrupted cell needed repairing
    and `done --evidence` was the only other writer, so the only way to fix a
    cell was to close the row, which is not a correction but a lie about the
    work.

    Three copies of one rule is the defect class five review rounds found in
    this project's prose. This one was in its own code.

    What is *not* shared is the part that is not boilerplate: each writer keeps
    its own event name, its own journal wording and its own refusal. A reader
    has to be able to tell "the plan changed" from "what this is called
    changed" from "where this got to", and one event name loses all three.
    """

    FIELDS = [("next", "--next", "next action"),
              ("retitle", "--title", "title"),
              ("rung", "--rung", "verification"),
              ("evidence", "--evidence", "evidence")]

    def cell(self, p, tid, key):
        board = p.board()
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        row = next(l for l in board.split("\n") if l.startswith(f"| {tid} |"))
        return dict(zip([PT.norm(h) for h in PT.split_row(header)],
                        PT.split_row(row))).get(key, "")

    def value_for(self, sub):
        return "V5" if sub == "rung" else "a new value"

    def test_each_writes_its_own_cell_and_no_other(self):
        for sub, flag, key in self.FIELDS:
            with self.subTest(sub=sub):
                p = Project()
                _, a = p.run("add", "--title", "x", "--priority", "P0",
                             "--rung", "V4")
                before = {k: self.cell(p, a["id"], k)
                          for _, _, k in self.FIELDS}
                code, out = p.run(sub, a["id"], flag, self.value_for(sub))
                self.assertEqual(code, 0, out)
                for _, _, other in self.FIELDS:
                    if other == key:
                        continue
                    self.assertEqual(before[other], self.cell(p, a["id"], other),
                                     f"{sub} also wrote `{other}`")

    def test_each_is_its_own_event(self):
        """Four subcommands, four event names. Folding them is what makes the
        three facts unrecoverable."""
        seen = []
        for sub, flag, _ in self.FIELDS:
            p = Project()
            _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
            p.run(sub, a["id"], flag, self.value_for(sub))
            events = [json.loads(l)["event"]
                      for l in (p.root / ".perry" / "events.jsonl").read_text()
                      .strip().split("\n")]
            seen.append(events[-1])
        self.assertEqual(len(self.FIELDS), len(set(seen)),
                         f"two writers share an event name: {seen}")

    def test_each_refuses_a_no_op(self):
        for sub, flag, _ in self.FIELDS:
            with self.subTest(sub=sub):
                p = Project()
                _, a = p.run("add", "--title", "x", "--priority", "P0", "--rung", "V4")
                p.run(sub, a["id"], flag, self.value_for(sub))
                code, _ = p.run(sub, a["id"], flag, self.value_for(sub))
                self.assertEqual(code, 1, f"{sub} wrote a value already there")

    def test_each_refusal_says_what_that_subcommand_is_for(self):
        """The unification must not cost the wording. `next` explains that
        clearing it leaves the row with no stated next step; `retitle` that a
        row with no title is one nobody can find."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        _, n = p.run("next", a["id"])
        _, r = p.run("retitle", a["id"])
        self.assertIn("no stated next step", str(n))
        self.assertIn("nobody can find", str(r))

    def test_only_next_refuses_a_finished_row(self):
        """A finished row has no next step. It still has a title, a rung and
        an evidence path, and those stay correctable — a board that stages
        finished work in place is the case that matters, since `done` removes
        the row. Perry's own board did that for twenty rows."""
        p = Project(board=BOARD.replace(
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n\n## P1",
            "| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
            "| TASK-900 | finished in place | User | done | — | e.md |\n\n## P1", 1))
        self.assertEqual(1, p.run("next", "TASK-900", "--next", "more")[0],
                         "a finished row was given a live-looking next step")
        self.assertEqual(0, p.run("retitle", "TASK-900", "--title", "clearer")[0],
                         "a finished row's title stopped being correctable")

    def test_evidence_repairs_a_cell_without_closing_the_row(self):
        """The case that showed the other three were a pattern."""
        p = Project()
        _, a = p.run("add", "--title", "x", "--priority", "P0")
        code, _ = p.run("evidence", a["id"], "--evidence", "evidence/2026-08/x.md")
        self.assertEqual(code, 0)
        self.assertEqual("evidence/2026-08/x.md", self.cell(p, a["id"], "evidence"))
        self.assertEqual("not_started", self.cell(p, a["id"], "status"),
                         "repairing a cell closed the row")


if __name__ == "__main__":
    unittest.main()
