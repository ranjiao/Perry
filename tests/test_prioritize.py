"""`perry-task prioritize` — the writer triage's central act did not have.

`perry-task` shipped 22 subcommands and none of them could change a row's
priority. `add` sets it once; `route` — the only other thing that writes a
priority cell — takes an *intake row number*, mints a *new* id, and refuses on
any track in `project` mode. So re-prioritising, which is what `triage`,
`monday-plan`, `friday-review` and `mid-phase-review` all end in, could only be
done by hand-editing `BOARD.md`.

A hand edit lands with **no event**, so `perry-state § reconcile_drift` reports
it as unrecorded drift — the exact failure `DESIGN-004` was written against —
and `priority` is a published field of `perry-task/list` that aiMark's Projects
view sorts on. A front-end could display a priority no caller could change.

Found by trying to execute a triage verdict rather than by reading the code.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import re

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import tables as T  # noqa: E402

TOOL = PERRY_HOME / "bin" / "perry-task"
HEADER = ["ID", "Title", "Owner", "Status", "Next action", "Evidence",
          "Verification"]
SEP = "|" + "---|" * len(HEADER)


def row(tid, title="t", owner="o", status="not_started", nxt="do it",
        ev="—", ver="V2"):
    return T.render_row([tid, title, owner, status, nxt, ev, ver])


def board(p0=(), p1=(), p2=(), extra_sections=""):
    return "\n".join([
        "# Board", "",
        "## P0", "", T.render_row(HEADER), SEP, *p0, "",
        "## P1", "", T.render_row(HEADER), SEP, *p1, "",
        "## P2", "", T.render_row(HEADER), SEP, *p2, "",
        extra_sections,
        "## Cadence", "",
        "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
        "|---|---|---|---|---|---|", "",
        "## User Input Queue", "",
        "| ID | Needed from user | Blocks | Asked | Status |",
        "|---|---|---|---|---|", "",
        "## Top risks", "",
        "| ID | Risk | Opened | Severity | Cleared |",
        "|---|---|---|---|---|", "",
    ])


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "perry").mkdir()
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Config\n\nState root: perry/\n", encoding="utf-8")
        self.addCleanup(self.tmp.cleanup)

    def write(self, text):
        (self.root / "perry" / "BOARD.md").write_text(text, encoding="utf-8")
        seeded = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-tasks"), "write",
             "--from-board", "--root", str(self.root)],
            capture_output=True, text=True)
        if seeded.returncode:
            raise AssertionError(seeded.stdout + seeded.stderr)

    def read(self):
        return (self.root / "perry" / "BOARD.md").read_text(encoding="utf-8")

    def run_tool(self, *argv):
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        return subprocess.run([sys.executable, str(TOOL), *argv,
                               "--root", str(self.root)],
                              capture_output=True, text=True, env=env)

    def payload(self):
        out = self.run_tool("list", "--all", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def task(self, tid):
        return [t for t in self.payload()["tasks"] if t["id"] == tid][0]

    def section_of(self, tid):
        """Which `## …` heading the row currently sits under."""
        head = None
        for line in self.read().split("\n"):
            if line.startswith("## "):
                head = line[3:].strip()
            elif line.strip().startswith("|") and T.split_row(line)[0] == tid:
                return head
        return None


class TestItMoves(Base):
    def setUp(self):
        super().setUp()
        self.write(board(p2=[row("TASK-001", nxt="a long next action",
                                 ev="evidence/x.md", ver="V4")]))

    def test_the_row_moves_and_keeps_its_id(self):
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.section_of("TASK-001"), "P1")
        self.assertEqual(self.task("TASK-001")["priority"], "P1")

    def test_every_other_cell_survives_the_move(self):
        """A move, not a re-file. Re-adding under a new priority would mint a
        second id — and an id is permanent and never reissued — so the row has
        to carry its own cells across."""
        self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        t = self.task("TASK-001")
        self.assertEqual(t["next_action"], "a long next action")
        self.assertEqual(t["evidence"], "evidence/x.md")
        self.assertEqual(t["verification"], "V4")
        self.assertEqual(t["title"], "t")

    def test_the_move_is_one_row_leaving_and_one_arriving(self):
        before = self.read().count("TASK-001")
        self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        self.assertEqual(before, 1)
        self.assertEqual(self.read().count("TASK-001"), 1,
                         "the row was copied rather than moved")

    def test_it_emits_an_event_so_the_move_is_not_drift(self):
        """The whole reason this subcommand exists. A hand edit lands with no
        event and `perry-state § reconcile_drift` reports it as unrecorded."""
        self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        tl = self.task("TASK-001")["timeline"]
        self.assertTrue(tl, "no timeline")
        last = tl[-1]
        self.assertEqual(last["event"], "prioritize")
        self.assertEqual((last["from"], last["to"]), ("P2", "P1"))

    def test_from_and_to_are_the_section_and_the_event_says_so(self):
        """Most events use `from`/`to` for the STATUS. A consumer that assumed
        so would read a move as a status change, so the event carries
        `field: section` to disambiguate without a per-event special case.

        It said `priority` for one commit, while the payload's own `field` said
        `section` — two names for one thing, which is how a reader and a writer
        drift apart. This test failed on that change and is why it was caught.
        """
        self.run_tool("prioritize", "TASK-001", "--priority", "P1")
        events = [json.loads(l) for l in
                  (self.root / ".perry" / "events.jsonl").read_text().splitlines() if l.strip()]
        ev = [e for e in events if e["event"] == "prioritize"][-1]
        self.assertEqual(ev["field"], "section")
        self.assertEqual(self.task("TASK-001")["status"], "not_started",
                         "the status must not have moved")

    def test_a_dry_run_writes_nothing(self):
        before = (self.root / "perry" / "BOARD.md").read_bytes()
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P1",
                            "--dry-run")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual((self.root / "perry" / "BOARD.md").read_bytes(), before)


class TestItRefuses(Base):
    def setUp(self):
        super().setUp()
        self.write(board(p2=[row("TASK-001")]))

    def test_a_move_to_where_it_already_is_is_refused(self):
        """A no-op that still emitted an event would put a move in the timeline
        that did not happen, and the timeline is what `list` reports as
        history."""
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P2")
        self.assertEqual(out.returncode, 1)
        self.assertIn("already under", out.stderr)

    def test_naming_no_destination_is_refused(self):
        out = self.run_tool("prioritize", "TASK-001")
        self.assertEqual(out.returncode, 1)
        self.assertIn("--priority", out.stderr)

    def test_an_unknown_priority_is_refused(self):
        out = self.run_tool("prioritize", "TASK-001", "--priority", "URGENT")
        self.assertEqual(out.returncode, 1)

    def test_a_row_that_is_not_on_the_board_is_refused(self):
        out = self.run_tool("prioritize", "TASK-999", "--priority", "P1")
        self.assertEqual(out.returncode, 1)
        self.assertIn("TASK-999", out.stderr)

    def test_a_refusal_writes_nothing(self):
        before = (self.root / "perry" / "BOARD.md").read_bytes()
        self.run_tool("prioritize", "TASK-001", "--priority", "P2")
        self.run_tool("prioritize", "TASK-999", "--priority", "P1")
        self.assertEqual((self.root / "perry" / "BOARD.md").read_bytes(), before)


class TestBoardsThatAreNotShapedLikePerrys(Base):
    """The case `route` could not reach, and the reason `--group` exists.

    `~/proj/gimegime-pmo` — the only year-old real project available — files
    work under its own headings and has no `## P0`/`## P1`/`## P2` at all.
    A subcommand that only worked on Perry-shaped boards would be unusable on
    exactly the projects migration is aimed at.
    """

    def setUp(self):
        super().setUp()
        self.write("\n".join([
            "# Board", "",
            "## Open — 工程线", "", T.render_row(HEADER), SEP,
            row("ENG-001", nxt="keep me"), "",
            "## Open — 投资线", "", T.render_row(HEADER), SEP, "",
            "## Cadence", "",
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
            "|---|---|---|---|---|---|", "",
            "## User Input Queue", "",
            "| ID | Needed from user | Blocks | Asked | Status |",
            "|---|---|---|---|---|", "",
            "## Top risks", "",
            "| ID | Risk | Opened | Severity | Cleared |",
            "|---|---|---|---|---|", "",
        ]))

    def test_a_row_moves_between_the_projects_own_headings(self):
        out = self.run_tool("prioritize", "ENG-001", "--group", "Open — 投资线")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.section_of("ENG-001"), "Open — 投资线")
        self.assertEqual(self.task("ENG-001")["next_action"], "keep me")

    def test_no_priority_section_is_created_on_a_board_that_has_none(self):
        """"No automatic rewrite of a project's existing structure" is an
        Anti-Goal. The refusal must name the headings the project does use."""
        out = self.run_tool("prioritize", "ENG-001", "--priority", "P1")
        self.assertEqual(out.returncode, 1)
        self.assertIn("Open — 工程线", out.stderr)
        self.assertNotIn("## P1", self.read())


class TestTheIndexIsCheckedBeforeAnythingIsDeleted(Base):
    """`remove_row` pops by index without looking at what it pops.

    The index is computed before the destination is widened, so its validity
    is an assumption about two other functions — `ensure_columns` and
    `ensure_section_columns` — held across a call, guarding the one operation
    on this board that deletes a line. Today they rewrite in place and never
    insert, so it holds. A widener that ever grew to insert a row would
    silently delete somebody else's task and append this one, and **both
    boards would still parse**.

    This class exists because the mutation written to prove the *ordering*
    came back green: the ordering genuinely does not matter, because `values`
    is extracted before either call. The invariant that does matter is this
    one, and it was invisible until the mutation failed to find anything.
    """

    def test_a_widener_that_inserts_is_refused_and_deletes_nothing(self):
        """Simulated by inserting a line above the row between locate and
        remove — which is exactly what a future `ensure_columns` that grew an
        insert would do."""
        self.write(board(p2=[row("TASK-001"), row("TASK-002")]))
        text = self.read()
        # The guard reads `board.lines[idx]`; shift the board by one line under
        # it by making the widener's own section grow. `--group` on a heading
        # that does not exist is refused earlier, so drive it through the code
        # rather than the CLI.
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        probe = (
            "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r)\n"
            "import importlib.machinery as m\n"
            "t = m.SourceFileLoader('t', %r).load_module()\n"
            "orig = t.widen_target_section\n"
            "def sneaky(board, priority, group, values):\n"
            "    orig(board, priority, group, values)\n"
            "    board.lines.insert(0, '')   # a widener that inserts\n"
            "t.widen_target_section = sneaky\n"
            "sys.exit(t.main(['prioritize','TASK-002','--priority','P1',"
            "'--root', %r]))\n"
        ) % (str(PERRY_HOME / "viewer"), str(PERRY_HOME / "bin"), str(TOOL),
             str(self.root))
        out = subprocess.run([sys.executable, "-c", probe],
                             capture_output=True, text=True, env=env)
        self.assertIn("shifted under the write", out.stdout + out.stderr)
        self.assertEqual(self.read(), text, "a refusal wrote to the board")


class TestWideningReachesTheDestination(Base):
    """A narrow destination gains the columns the row needs.

    Not about ordering — see the class above for why that turned out not to be
    the invariant. This is about the widening happening at all: without it the
    row is appended against a header that never gained the column, and
    whichever cell only the source carried is dropped with no error anywhere.
    """

    def setUp(self):
        super().setUp()
        narrow = ["ID", "Title", "Owner", "Status"]
        self.write("\n".join([
            "# Board", "",
            "## P0", "", T.render_row(narrow), "|" + "---|" * len(narrow), "",
            "## P2", "", T.render_row(HEADER), SEP,
            row("TASK-001", nxt="must survive", ev="evidence/y.md", ver="V3"), "",
            "## Cadence", "",
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
            "|---|---|---|---|---|---|", "",
            "## User Input Queue", "",
            "| ID | Needed from user | Blocks | Asked | Status |",
            "|---|---|---|---|---|", "",
            "## Top risks", "",
            "| ID | Risk | Opened | Severity | Cleared |",
            "|---|---|---|---|---|", "",
        ]))

    def test_the_narrow_destination_gains_the_columns_and_no_cell_is_lost(self):
        out = self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        self.assertEqual(out.returncode, 0, out.stderr)
        t = self.task("TASK-001")
        self.assertEqual(t["next_action"], "must survive")
        self.assertEqual(t["evidence"], "evidence/y.md")
        self.assertEqual(t["verification"], "V3")


class TestTheEventIsPartOfTheDeclaredSet(unittest.TestCase):
    def test_prioritize_is_a_task_event_not_a_section_event(self):
        """`TASK_EVENTS` and `SECTION_EVENTS` are asserted to be a partition of
        `COMMANDS`. A new subcommand that lands in neither drops out of the
        payload silently; one that lands in both leaks into it."""
        spec = importlib.util.spec_from_loader(
            "perry_task",
            importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertIn("prioritize", mod.COMMANDS)
        self.assertIn("prioritize", mod.TASK_EVENTS)
        self.assertNotIn("prioritize", mod.SECTION_EVENTS)

    def test_it_is_documented_in_the_usage_banner(self):
        """A subcommand a user cannot discover is one they will hand-edit
        around, which is the failure this whole module is about."""
        doc = TOOL.read_text(encoding="utf-8").split('"""')[1]
        self.assertIn("perry-task prioritize", doc)




class TestAClosedRowKeepsThePriorityItWasMovedTo(Base):
    """A row that has left the board is folded back together from events.

    `cmd_list` rebuilds a closed row with
    `t["priority"] = e.get("priority") or t["priority"]` — there are no cells
    left to read. The `prioritize` event therefore has to carry `priority` and
    `group` the way `add` and `route` do, or the fold silently keeps the `add`
    event's value and the payload reports a priority the row's **own timeline**,
    two lines above, says it moved away from.

    Found by running the lifecycle end to end rather than by reading the code.
    """

    def setUp(self):
        super().setUp()
        self.write(board(p1=[row("TASK-001")]))

    def test_the_closed_row_reports_where_it_was_moved_to(self):
        self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        (self.root / "perry" / "evidence").mkdir(parents=True, exist_ok=True)
        (self.root / "perry" / "evidence" / "e.md").write_text("x", encoding="utf-8")
        out = self.run_tool("done", "TASK-001", "--evidence", "evidence/e.md",
                            "--rung", "V3")
        self.assertEqual(out.returncode, 0, out.stderr)
        t = self.task("TASK-001")
        self.assertFalse(t["open"], "the row should have left the board")
        self.assertEqual(t["priority"], "P0")

    def test_the_field_never_disagrees_with_its_own_timeline(self):
        """The check that would have caught it without knowing the mechanism."""
        self.run_tool("prioritize", "TASK-001", "--priority", "P0")
        (self.root / "perry" / "evidence").mkdir(parents=True, exist_ok=True)
        (self.root / "perry" / "evidence" / "e.md").write_text("x", encoding="utf-8")
        self.run_tool("done", "TASK-001", "--evidence", "evidence/e.md",
                      "--rung", "V3")
        t = self.task("TASK-001")
        moves = [e for e in t["timeline"] if e["event"] == "prioritize"]
        self.assertTrue(moves)
        self.assertEqual(t["priority"], moves[-1]["to"],
                         "the payload disagrees with its own timeline")


class TestARungPassedAsTheCheckIsRefused(Base):
    """`--verification` and `--rung` share a word and mean different things.

    `--verification` is the falsifiable **check** a rung is graded against;
    `--rung` is the rung, and the cell the board shows. Passing the rung to the
    first was accepted silently, filing `"V4"` as though it were a check — the
    mistake was made while opening six rows on Perry's own board the night this
    guard was written.

    The guard is the **category** — any value that is nothing but a rung token —
    not the one spelling that happened to bite.
    """

    def setUp(self):
        super().setUp()
        self.write(board())

    def test_every_rung_token_is_refused_as_a_check(self):
        for rung in ("V0", "V1", "V2", "V3", "V4", "V5", "V6", "  V4  "):
            out = self.run_tool("add", "--title", "t", "--deliverable", "d",
                                "--verification", rung, "--priority", "P1")
            self.assertEqual(out.returncode, 1, f"{rung!r} was accepted")
            self.assertIn("is a rung, not a check", out.stderr)

    def test_the_refusal_names_the_flag_that_would_have_worked(self):
        out = self.run_tool("add", "--title", "t", "--deliverable", "d",
                            "--verification", "V4", "--priority", "P1")
        self.assertIn("--rung V4", out.stderr)

    def test_a_real_check_that_merely_mentions_a_rung_is_accepted(self):
        """Prose is not a rung token. A guard that matched a substring would
        refuse the most natural check anyone would write."""
        out = self.run_tool("add", "--title", "t", "--deliverable", "d",
                            "--verification", "V4 review by a fresh reviewer",
                            "--rung", "V4", "--priority", "P1")
        self.assertEqual(out.returncode, 0, out.stderr)


class TestEveryEventSaysWhatItsPairMeans(unittest.TestCase):
    """`field` on a timeline entry, so a consumer needs no hardcoded set.

    aiMark had to write `SECTION_MOVE_EVENTS = new Set(["prioritize"])` to keep
    `prioritize` from rendering `P1 → P0` with the status palette. That set is
    wrong the day Perry adds a second event overloading `from`/`to`, and
    **nothing in the payload would say so** — one side knowing and the other
    guessing, which is the defect these contracts exist against.

    The ask was `"status"` on every existing event and `"section"` on
    `prioritize`. That default is false — `retitle`'s pair is a title, `next`'s
    is a next action — and shipping a wrong word in the field whose job is to
    stop a consumer guessing would be the same defect inside its own fix. So it
    is a full map, and this test is what keeps it full.
    """

    def setUp(self):
        spec = importlib.util.spec_from_loader(
            "perry_task",
            importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_the_map_covers_exactly_the_declared_task_events(self):
        """Not "covers them" — **exactly**. A missing key ships `""` to a
        consumer; a stale key promises something that cannot happen. `depends`
        was already missing when this was written, found by running the payload
        rather than by reading the map."""
        self.assertEqual(set(self.mod.EVENT_FIELD), set(self.mod.TASK_EVENTS))

    def test_no_event_claims_a_pair_it_does_not_carry(self):
        """The values are cell names a reader can act on, not a vocabulary of
        their own. Each must be a key of the task payload, or `status`/`section`
        which name a concept rather than a cell."""
        payload_keys = set(self.mod.LIST_TASK_KEYS) if hasattr(
            self.mod, "LIST_TASK_KEYS") else None
        allowed = {"status", "section", "stage", "title", "next_action",
                   "verification", "evidence", "depends_on"}
        self.assertLessEqual(set(self.mod.EVENT_FIELD.values()), allowed)

    def test_a_section_move_is_not_reported_as_a_status_move(self):
        self.assertEqual(self.mod.EVENT_FIELD["prioritize"], "section")
        self.assertEqual(self.mod.EVENT_FIELD["status"], "status")

    def test_an_id_shaped_word_in_prose_is_warned_about(self):
        """`ROUND-2` is English with a hyphen and an identifier to every id
        reader here.

        **Caused three times in one session**, each time fixed in the prose and
        each time recurring: `THE ROUND-2 DEFECT`, then `ALL FIVE ROUND-3
        FINDINGS`. `perry-diagnose` reports it as `LOAD-02` dangling and the
        repo's own gate goes red on a board the tool itself wrote.

        The guard is at the WRITE site because that is where the person who
        knows what they meant still is. Advisory, never a refusal — `USER-014`
        and `ADR-006` are legitimate citations of ids this board does not
        carry, and refusing them would make the tool unable to cite a
        decision.
        """
        fn = self.mod.idish_tokens_that_resolve_nowhere
        state_root = TOOL.parent.parent / "perry"
        ctx = {"task_records": self.mod.load_task_records(state_root)}
        self.assertEqual(fn("the ROUND-2 defect", ctx), ["ROUND-2"])
        self.assertEqual(fn("see ADR-006 and USER-014", ctx), [])
        self.assertEqual(fn("round 2, plainly", ctx), [])

    def test_the_docs_rebuttal_counts_what_the_map_holds(self):
        """The contract doc states a COUNT, and nothing checked it.

        aiMark's round-2 report proposed `field: "status"` on every event
        except `prioritize`. Two paragraphs of `schema/task-list-contract.md`
        rebut that, and both said it would be false for three events —
        `retitle`, `next`, `rung`. It is false for **six**: those three plus
        `stage`, `evidence` and `depends`.

        The `1.7` paragraph enumerates all seven non-`status` fields two
        sentences before claiming three would be wrong, so the doc contradicted
        itself inside one paragraph. The test above covers the map's KEYS
        against the writer's event set, and a prose number is not a key — which
        is why an assertion sitting six lines away did not catch it.

        A number in prose that restates a data structure is the same defect as
        a rule in prose that nothing implements. This binds them, in both
        copies, by name and not only by count.
        """
        mislabelled = sorted(e for e, f in self.mod.EVENT_FIELD.items()
                             if f != "status" and e != "prioritize")
        doc = (TOOL.parent.parent / "schema"
               / "task-list-contract.md").read_text(encoding="utf-8")
        claims = re.findall(
            r"proposed `status` for everything except `prioritize`;.*?"
            r"\*\*(\w+)\*\* of the thirteen — (.*?) — and a wrong word",
            doc, re.S)
        self.assertEqual(len(claims), 2,
                         "the rebuttal is stated twice; both must be checked")
        words = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
        for word, listed in claims:
            self.assertEqual(
                words.get(word), len(mislabelled),
                f"doc says {word!r}, EVENT_FIELD says {len(mislabelled)}: "
                f"{mislabelled}")
            self.assertEqual(sorted(re.findall(r"`([a-z_]+)`", listed)),
                             mislabelled,
                             "the doc names different events than the map")

    def test_the_stored_event_says_the_same_word_the_payload_does(self):
        """`cmd_prioritize` writes `field` into the event too. Two names for one
        thing is how the reader and the writer drift apart — it said `priority`
        while the payload said `section` for one commit."""
        src = TOOL.read_text(encoding="utf-8")
        self.assertIn('"field": "section"', src)
        self.assertNotIn('"field": "priority"', src)


class TestClosingWithoutStartingIsVisible(Base):
    """`DESIGN-004 § 1.3`'s second question is "what is being worked on right
    now", and the event log exists to answer it.

    Measured on Perry's own log while this was written: **56 rows closed, 54
    of them with no `start` event.** For an entire working session the board
    could not answer that question about any row — reproducing, by the tool's
    own author, the failure the design doc describes: *"the board said
    `in_progress` when an agent remembered to write it."*

    A **warning, not a refusal**: work genuinely done in one sitting is
    honestly `add → done`, and refusing that would teach people to write a
    `start` they do not mean. What it buys is that the omission is visible at
    the moment it is made rather than discoverable by counting events later.
    """

    def setUp(self):
        super().setUp()
        self.write(board(p1=[row("TASK-001")]))

    def test_closing_an_unstarted_row_says_so(self):
        out = self.run_tool("done", "TASK-001", "--evidence", "e.md",
                            "--rung", "V2")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("without ever being", out.stderr)
        self.assertIn("start", out.stderr)

    def test_closing_a_started_row_says_nothing(self):
        self.run_tool("start", "TASK-001")
        out = self.run_tool("done", "TASK-001", "--evidence", "e.md",
                            "--rung", "V2")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("without ever being", out.stderr)

    def test_it_warns_and_does_not_refuse(self):
        """The row must still close. A guard that blocked the close would be
        worse than the gap it reports."""
        out = self.run_tool("done", "TASK-001", "--evidence", "e.md",
                            "--rung", "V2")
        self.assertEqual(out.returncode, 0)
        self.assertNotIn("TASK-001", self.read())

    def test_the_payload_carries_it_so_a_front_end_can_show_it(self):
        out = self.run_tool("done", "TASK-001", "--evidence", "e.md",
                            "--rung", "V2", "--json")
        self.assertFalse(json.loads(out.stdout)["was_started"])
        self.assertNotIn("without ever being", out.stderr,
                         "--json must keep stderr quiet")


if __name__ == "__main__":
    unittest.main()
