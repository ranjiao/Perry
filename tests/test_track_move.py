"""A project could declare a second track and then move nothing onto it.

`TASK-135`, out of `perry/evidence/2026-08/TASK-133-track-experiment.md`.

`--track` was accepted by exactly two commands: `add`, at creation, and
`route`, which turns an intake row into a task. There was no
`perry-task track <id>`. So a declared track **started empty and could not be
populated** — measured on Perry's own repository, which declared `intake`
(mode `queue`) on 2026-08-20 and left six rows that genuinely arrived stranded
on `main`. A track with no rows is not a mode running on a live track, which is
why declaring one did not meet KR-O1.1.

The two behaviours these tests exist for, because `route` already has them and
a second entrance that did not would make `Arrived` mean one thing per
entrance:

1. Onto a **queue** track the move stamps `Arrived` and the track's first
   post-intake `Stage`. `today − Arrived` is the number every SLA check
   measures, so a move that omitted it would silently exempt the row from the
   only clock governing it.
2. Off a track, `Stage` / `Stage since` / `Arrived` are **cleared, and what
   they held is recorded** in the journal line and the event. A clock left on a
   row no queue governs is a live-looking number, and a non-empty `arrived`
   additionally hides the row from `rows_with_no_computable_age` — the finding
   that says "this row has no clock at all".

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


PERRY_HOME = Path(__file__).resolve().parent.parent
TASK = PERRY_HOME / "bin" / "perry-task"
STATE = PERRY_HOME / "bin" / "perry-state"
LINT = PERRY_HOME / "bin" / "perry-lint"

TODAY = f"{date.today():%Y-%m-%d}"

#: One `project` track, one `queue`, one `pipeline`, one second `queue`. The
#: fourth is not padding: "an existing `Arrived` is carried, never restamped"
#: is only observable across two tracks that both read one.
TRACKS = (
    "| main | project | OKR.md | — | — | — | — | V3 |\n"
    "| intake | queue | standing | new→triaged→in_progress→resolved "
    "| 6 | 5d | weekly | V3 |\n"
    "| press | pipeline | commitments | — | — | 2w | 1w | V5 |\n"
    "| ops | queue | standing | new→triaged→resolved | 3 | 3d | weekly | V2 |\n"
)

CONFIG = ("# Perry configuration\n\n- State root: perry\n"
          + "\n## Tracks\n\n"
          "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
          "|---|---|---|---|---|---|---|---|\n" + TRACKS)

HEAD = ("| ID | Title | Owner | Status | Next action | Evidence "
        "| Verification |\n|---|---|---|---|---|---|---|\n")


class Base(unittest.TestCase):
    def project(self, rows: int = 1, heading: str = "P1") -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(CONFIG, encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text(
            f"# Board\n\n## {heading}\n\n" + HEAD, encoding="utf-8")
        for n in range(rows):
            self.ok(root, "add", "--title", f"row {n + 1}",
                    "--deliverable", "an artifact with a test",
                    "--verification", "perry-lint clean", "--next", "n",
                    *(["--group", heading]
                      if heading not in ("P0", "P1", "P2") else []))
        return root

    def cli(self, root: Path, *args: str):
        r = subprocess.run([sys.executable, str(TASK), *args,
                            "--root", str(root), "--json"],
                           capture_output=True, text=True)
        return r

    def ok(self, root: Path, *args: str) -> dict:
        r = self.cli(root, *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def tasks(self, root: Path) -> dict:
        out = self.ok(root, "list", "--all")
        return {t["id"]: t for t in out["tasks"]}

    def store(self, root: Path) -> dict:
        lines = (root / "perry" / "tasks.jsonl").read_text(
            encoding="utf-8").splitlines()
        return {r["id"]: r for r in (json.loads(l) for l in lines if l.strip())}

    def events(self, root: Path) -> list[dict]:
        path = root / ".perry" / "events.jsonl"
        if not path.exists():
            return []
        return [json.loads(l) for l in
                path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def board(self, root: Path) -> str:
        return (root / "perry" / "BOARD.md").read_text(encoding="utf-8")

    def state(self, root: Path) -> dict:
        r = subprocess.run([sys.executable, str(STATE), "--json",
                            "--root", str(root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)


class TestSixRowsMove(Base):
    """V3 item 1. The measured defect was that a declared track stays empty."""

    def test_six_existing_rows_reach_the_declared_queue_track(self):
        root = self.project(rows=6)
        ids = sorted(self.tasks(root))
        self.assertEqual(len(ids), 6)
        for tid in ids:
            self.ok(root, "track", tid, "--track", "intake")
        moved = self.tasks(root)
        self.assertEqual(sorted(t["id"] for t in moved.values()
                                if t["track"] == "intake"), ids)

    def test_the_board_renders_arrived_and_stage_for_every_moved_row(self):
        """The board is the projection. A move the store knows and the
        rendered file does not is a half-landed write."""
        root = self.project(rows=6)
        for tid in sorted(self.tasks(root)):
            self.ok(root, "track", tid, "--track", "intake")
        for t in self.tasks(root).values():
            self.assertEqual(t["stage"], "triaged", t["id"])
            self.assertEqual(t["arrived"], TODAY, t["id"])
            self.assertEqual(t["stage_since"], TODAY, t["id"])
        board = self.board(root)
        self.assertIn("| Track | Stage | Stage since | Arrived |", board)
        self.assertEqual(board.count(f"| intake | triaged | {TODAY} | {TODAY} |"), 6)

    def test_perry_state_reports_them_under_the_tracks_stage_counts(self):
        """The reader the mode's own triage step runs off. It counted nothing
        for `intake` because nothing could get there."""
        root = self.project(rows=6)
        before = {t["track"]: t["stage_counts"] for t in
                  self.state(root)["project"]["config"]["tracks"]}
        self.assertEqual(before["intake"], {})
        for tid in sorted(self.tasks(root)):
            self.ok(root, "track", tid, "--track", "intake")
        after = {t["track"]: t["stage_counts"] for t in
                 self.state(root)["project"]["config"]["tracks"]}
        self.assertEqual(after["intake"], {"triaged": 6})

    def test_the_stage_is_the_one_the_other_two_entrances_use(self):
        """`add`, `route` and this all call `entry_stage`, so a queue row is
        born past the stage that means "sitting in intake" whichever door it
        came through. Three entrances that each picked their own would put one
        track's rows in two vocabularies."""
        root = self.project(rows=1)
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        born = self.ok(root, "add", "--title", "born on the track",
                           "--deliverable", "an artifact with a test",
                           "--verification", "v", "--next", "n",
                           "--track", "intake")["id"]
        rows = self.tasks(root)
        self.assertEqual(rows[tid]["stage"], rows[born]["stage"])

    def test_nothing_else_about_the_row_moves(self):
        """It keeps its id, its section and every other cell — the property
        that makes this a move rather than a re-file."""
        root = self.project(rows=1)
        tid, = self.tasks(root)
        before = self.tasks(root)[tid]
        self.ok(root, "track", tid, "--track", "intake")
        after = self.tasks(root)[tid]
        for key in ("id", "title", "owner", "status", "priority", "group",
                    "next_action", "evidence", "verification", "created"):
            self.assertEqual(before[key], after[key], key)


class TestTheRefusalIsByName(Base):
    """V3 item 2, in `delegate`'s shape for an undeclared role card."""

    def refusal(self, root: Path):
        r = self.cli(root, "track", next(iter(self.tasks(root))),
                     "--track", "nosuch")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr + r.stdout)
        return json.loads(r.stdout)["refused"]

    def test_it_names_the_track_and_lists_the_declared_ones(self):
        msg = self.refusal(self.project())
        self.assertIn("'nosuch'", msg)
        for declared in ("main", "intake", "press", "ops"):
            self.assertIn(declared, msg)

    def test_it_names_the_file_the_declaration_lives_in(self):
        """A user who must name a declared track needs the set AND the way to
        add the missing one. Printing the set alone — which is what a bare
        Python list repr did — names the problem and not the fix."""
        msg = self.refusal(self.project())
        self.assertIn(".perry/config.md", msg)
        self.assertIn("Nothing was written", msg)

    def test_it_creates_nothing(self):
        root = self.project()
        config_before = (root / ".perry" / "config.md").read_bytes()
        board_before = self.board(root)
        self.refusal(root)
        self.assertEqual((root / ".perry" / "config.md").read_bytes(),
                         config_before)
        self.assertEqual(self.board(root), board_before)
        self.assertEqual([e for e in self.events(root)
                          if e.get("event") == "track"], [])
        tracks = {t["track"] for t in
                  self.state(root)["project"]["config"]["tracks"]}
        self.assertNotIn("nosuch", tracks)

    def test_a_move_to_the_track_the_row_is_already_on_is_refused(self):
        """A no-op that still emitted an event would put a move in the
        timeline that did not happen, and the timeline is what `list` reports
        as history."""
        root = self.project()
        tid, = self.tasks(root)
        r = self.cli(root, "track", tid, "--track", "main")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already on track", json.loads(r.stdout)["refused"])

    def test_a_stage_outside_the_destinations_vocabulary_is_refused(self):
        root = self.project()
        tid, = self.tasks(root)
        r = self.cli(root, "track", tid, "--track", "intake",
                     "--stage", "bogus")
        self.assertEqual(r.returncode, 1)
        self.assertIn("vocabulary", json.loads(r.stdout)["refused"])

    def test_track_without_a_track_is_refused_rather_than_a_no_op(self):
        root = self.project()
        tid, = self.tasks(root)
        r = self.cli(root, "track", tid)
        self.assertEqual(r.returncode, 1)
        self.assertIn("--track is required", json.loads(r.stdout)["refused"])


class TestBothDirectionsOfTheFieldQuestion(Base):
    """V3 item 3. The decision deliverable 2 asks for, asserted in a fixture
    rather than argued in a docstring."""

    def test_onto_a_queue_track_the_clock_starts(self):
        root = self.project()
        tid, = self.tasks(root)
        out = self.ok(root, "track", tid, "--track", "intake")
        self.assertEqual((out["stage"], out["arrived"]), ("triaged", TODAY))
        rec = self.store(root)[tid]
        self.assertEqual(rec["track"], "intake")
        self.assertEqual(rec["stage"], "triaged")
        self.assertEqual(rec["arrived"], TODAY)
        self.assertEqual(rec["stage_since"], TODAY)

    def test_off_a_queue_track_the_clock_is_cleared(self):
        """Not kept: `Arrived` is a queue's clock, not provenance, and one
        left on a row no queue governs is a live-looking number the next SLA
        reader picks up. `cmd_route` already had to stop writing `Arrived` onto
        non-queue rows for the mirror-image reason — a non-empty `arrived`
        hides the row from `rows_with_no_computable_age`."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake",
                    "--arrived", "2026-08-01")
        self.ok(root, "track", tid, "--track", "main")
        rec = self.store(root)[tid]
        self.assertEqual(rec["track"], "main")
        self.assertEqual(rec["arrived"], "")
        self.assertEqual(rec["stage"], "")
        self.assertEqual(rec["stage_since"], "")

    def test_what_was_cleared_is_recorded_on_both_surviving_surfaces(self):
        """Dropping the CELL is not dropping the FACT — `drop`'s precedent,
        applied one field down. The journal is append-only and the event
        carries the pair, which is where every other post-removal question is
        already answered from."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake",
                    "--arrived", "2026-08-01")
        self.ok(root, "track", tid, "--track", "main")
        journal = (root / "perry" / "journal" / f"{date.today():%Y-%m}"
                   / f"{TODAY}.md").read_text(encoding="utf-8")
        self.assertIn(f"[{tid}] track intake → main", journal)
        self.assertIn("stage triaged → —", journal)
        self.assertIn("arrived 2026-08-01 → —", journal)
        off = [e for e in self.events(root) if e.get("event") == "track"][-1]
        self.assertEqual(off["stage_from"], "triaged")
        self.assertEqual(off["arrived_from"], "2026-08-01")
        self.assertEqual((off["stage"], off["arrived"]), ("", ""))

    def test_an_existing_arrived_is_carried_never_restamped(self):
        """The case the spec names. A queue → queue move that reset the clock
        to today would erase an in-flight breach — the same exemption a missing
        stamp buys, arriving through the other door."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake",
                    "--arrived", "2026-08-01")
        out = self.ok(root, "track", tid, "--track", "ops")
        self.assertEqual(out["arrived"], "2026-08-01")
        self.assertEqual(self.store(root)[tid]["arrived"], "2026-08-01")

    def test_the_stage_is_restamped_on_a_queue_to_queue_move(self):
        """The vocabularies differ per track, so the stage cannot be carried
        even when the clock is: `intake` has `in_progress` and `ops` does
        not."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        self.ok(root, "stage", tid, "--stage", "in_progress")
        self.ok(root, "track", tid, "--track", "ops")
        rec = self.store(root)[tid]
        self.assertEqual(rec["stage"], "triaged")
        self.assertEqual(rec["stage_since"], TODAY)

    def test_a_staged_non_queue_destination_gets_stage_since_and_no_arrived(self):
        """`entry_stage` puts a pipeline row at `brief`, not past it — the
        skip is a queue rule, because only a queue's first stage means
        "sitting in intake"."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        self.ok(root, "track", tid, "--track", "press")
        rec = self.store(root)[tid]
        self.assertEqual(rec["stage"], "brief")
        self.assertEqual(rec["stage_since"], TODAY)
        self.assertEqual(rec["arrived"], "")

    def test_arrived_on_a_destination_that_cannot_read_it_is_refused(self):
        """Accepting the flag and dropping the value is how `--rung` and
        `--commitment` were each lost for a release. A refusal says the
        destination has no clock for it."""
        root = self.project()
        tid, = self.tasks(root)
        r = self.cli(root, "track", tid, "--track", "press",
                     "--arrived", "2026-08-01")
        self.assertEqual(r.returncode, 1)
        self.assertIn("--arrived", json.loads(r.stdout)["refused"])

    def test_the_move_survives_a_re_render(self):
        """The board is rendered FROM the store. A `changed` map that listed
        only `track` would leave yesterday's `Stage` and `Arrived` in the
        record beside the new track, and the move would half-revert here."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        before = self.board(root)
        r = subprocess.run([sys.executable, str(PERRY_HOME / "bin" / "perry-tasks"),
                            "render", "--write", "--root", str(root)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.board(root), before)


class TestAnEventPerMove(Base):
    """V3 item 4. A track change nothing recorded is TASK-139's shape."""

    def test_every_move_appends_exactly_one_track_event(self):
        root = self.project(rows=3)
        ids = sorted(self.tasks(root))
        for tid in ids:
            self.ok(root, "track", tid, "--track", "intake")
        moves = [e for e in self.events(root) if e.get("event") == "track"]
        self.assertEqual([e["id"] for e in moves], ids)

    def test_the_event_says_where_from_and_where_to(self):
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake", "--reason", "it arrived")
        e, = [e for e in self.events(root) if e.get("event") == "track"]
        self.assertEqual((e["from"], e["to"]), ("main", "intake"))
        self.assertEqual(e["field"], "track")
        self.assertEqual(e["track"], "intake")
        self.assertEqual(e["mode"], "queue")
        self.assertEqual(e["reason"], "it arrived")
        self.assertEqual(e["title"], "row 1")

    def test_the_pair_reaches_the_timeline_labelled_track(self):
        """`timeline[].field` exists so a consumer needs no hardcoded set of
        special cases. Labelling this pair `status` — or `stage` — would put a
        track name in a field a reader resolves against a status enum or a
        stage vocabulary."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        entry, = [t for t in self.tasks(root)[tid]["timeline"]
                  if t["event"] == "track"]
        self.assertEqual(entry["field"], "track")
        self.assertEqual((entry["from"], entry["to"]), ("main", "intake"))

    def test_the_events_feed_carries_it(self):
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        feed = self.ok(root, "events")["events"]
        move, = [e for e in feed if e["event"] == "track"]
        self.assertEqual(move["field"], "track")
        self.assertEqual(move["track"], "intake")

    def test_a_dry_run_writes_nothing(self):
        root = self.project()
        tid, = self.tasks(root)
        before = (self.board(root), self.store(root), self.events(root))
        self.ok(root, "track", tid, "--track", "intake", "--dry-run")
        self.assertEqual((self.board(root), self.store(root),
                          self.events(root)), before)


class TestTheProjectionAgreesAfterAMove(Base):
    """V3 item 5. The board is a projection; a move that leaves the rendered
    file disagreeing with the store has not finished."""

    def lint(self, root: Path) -> list[dict]:
        r = subprocess.run([sys.executable, str(LINT), "--json",
                            "--root", str(root)], capture_output=True, text=True)
        return json.loads(r.stdout)["findings"]

    def test_perry_lint_reports_no_store_drift_after_a_move(self):
        root = self.project(rows=6)
        for tid in sorted(self.tasks(root)):
            self.ok(root, "track", tid, "--track", "intake")
        drift = [f for f in self.lint(root)
                 if str(f.get("code", "")).startswith("store-drift")]
        self.assertEqual(drift, [], "the board disagrees with the store")

    def test_and_none_after_a_move_that_clears_the_clock(self):
        """The clearing direction is the one a projection loses: a cell whose
        value goes to `""` is exactly the write a renderer can silently skip."""
        root = self.project()
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        self.ok(root, "track", tid, "--track", "main")
        drift = [f for f in self.lint(root)
                 if str(f.get("code", "")).startswith("store-drift")]
        self.assertEqual(drift, [])


class TestABoardWithItsOwnHeadings(Base):
    """`Board.find` returns `P0`/`P1`/`P2` **or a project's own heading**, and
    the two widenings live on different methods. `cmd_stage` widens only in the
    first case, so on the board shape `--group` exists for — the only real
    adopted project available — a stamp is dropped silently at exit 0. A track
    move writes four such cells, so it asks the question for both shapes."""

    def test_the_cells_land_under_a_projects_own_heading(self):
        root = self.project(rows=1, heading="Open — 工程线")
        tid, = self.tasks(root)
        self.ok(root, "track", tid, "--track", "intake")
        rec = self.store(root)[tid]
        self.assertEqual(rec["track"], "intake")
        self.assertEqual(rec["stage"], "triaged")
        self.assertEqual(rec["arrived"], TODAY)
        self.assertIn("| intake | triaged |", self.board(root))


class TestTheSubcommandIsWiredEverywhereItHasToBe(unittest.TestCase):
    """The four tables a subcommand has to appear in, each of which fails
    silently on its own: absent from `COMMANDS` it is unreachable, absent from
    the partition it drops out of the front-end contract, absent from
    `EVENT_FIELD` it ships `""` for the pair's meaning, and absent from
    `commit`'s `changed` map it lands in the store as a track with yesterday's
    clock beside it."""

    @classmethod
    def setUpClass(cls):
        import importlib.machinery
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "perry_task_track",
            importlib.machinery.SourceFileLoader("perry_task_track", str(TASK)))
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_it_is_dispatchable_and_classified_as_a_task_event(self):
        self.assertIn("track", self.mod.COMMANDS)
        self.assertIn("track", self.mod.TASK_EVENTS)
        self.assertNotIn("track", self.mod.SECTION_EVENTS)
        self.assertIn("track", self.mod.TASK_ROW_COMMANDS)

    def test_the_pair_declares_what_it_refers_to(self):
        self.assertEqual(self.mod.EVENT_FIELD["track"], "track")

    def test_the_write_carries_the_clock_fields_with_the_track(self):
        source = TASK.read_text(encoding="utf-8")
        self.assertIn(
            '"track": ("track", "stage", "stage_since", "arrived"),', source,
            "commit's `changed` map must carry the cells the move re-stamps, "
            "or the store keeps yesterday's clock beside the new track")
