"""A project could declare a second track and then move nothing onto it.

`TASK-135`, out of `perry/evidence/2026-08/TASK-133-track-experiment.md`.

`--track` was accepted by exactly two commands: `add`, at creation, and
`route`, which turns an intake row into a task. There was no
`perry-task track <id>`. So a declared track **started empty and could not be
populated** — measured on Perry's own repository, which declared `intake`
(mode `queue`) on 2026-08-20 and left six rows that genuinely arrived stranded
on `main`. A track with no rows is not a mode running on a live track, which is
why declaring one did not meet O1-KR1.

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

import task_actor

COVERS = ("bin/perry-task", "bin/perry-state", "bin/perry-lint")

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import config_store
import inproc
from config_store import track


PERRY_HOME = Path(__file__).resolve().parent.parent
TASK = PERRY_HOME / "bin" / "perry-task"
STATE = PERRY_HOME / "bin" / "perry-state"
LINT = PERRY_HOME / "bin" / "perry-lint"

TODAY = f"{date.today():%Y-%m-%d}"

#: One `project` track, one `queue`, one `pipeline`, one second `queue`. The
#: fourth is not padding: "an existing `Arrived` is carried, never restamped"
#: is only observable across two tracks that both read one.
TRACKS = [
    track("main", "project", spine="OKR.md", default_rung="V3"),
    track("intake", "queue", spine="standing",
          stages="new→triaged→in_progress→resolved", wip="6", sla="5d",
          cycle="weekly", default_rung="V3"),
    track("press", "pipeline", spine="commitments", sla="2w", cycle="1w",
          default_rung="V5"),
    track("ops", "queue", spine="standing", stages="new→triaged→resolved",
          wip="3", sla="3d", cycle="weekly", default_rung="V2"),
]

SETTINGS = {"State root": "perry"}

HEAD = ("| ID | Title | Owner | Status | Next action | Evidence "
        "| Verification |\n|---|---|---|---|---|---|---|\n")


from kernel_work_support import ACTOR, ready, task
from task_writer_support import Project as LegacyProject


class TestNativeTrackMove(unittest.TestCase):
    def test_move_changes_track_alone_and_preserves_relationships(self):
        sb = ready(self)
        parent, tid = task(sb), task(sb, track="main")
        sb.ok("rel add", data={"actor": ACTOR, "kind": "parent", "from": parent, "to": tid})
        sb.ok("attach add", data={"actor": ACTOR, "id": tid, "ref": "evidence/spec.md"})
        before = sb.get(tid)
        for track in ("intake", "main"):
            sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"track": track},
                                       "expect": {tid: sb.get(tid)["seq"]}})
            got = sb.get(tid)
            self.assertEqual(got["fields"]["track"], track)
            self.assertEqual(got["state"], before["state"])
            self.assertEqual(got["relations"], before["relations"])
            self.assertEqual(got["attachments"], before["attachments"])
            self.assertEqual({k: v for k, v in got["fields"].items() if k != "track"},
                             {k: v for k, v in before["fields"].items() if k != "track"})

    def test_unknown_legacy_tracks_refuse_without_clock_or_event(self):
        sb = ready(self)
        tid = task(sb, track="main")
        before = sb.get(tid)
        for track in ("ops", "press", "typo"):
            out = sb.run("item update", data={"actor": ACTOR, "id": tid, "set": {"track": track}})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.get(tid), before)
        for key in ("arrived", "stage", "stage_since"):
            self.assertNotIn(key, before["fields"])

    def test_closed_item_track_can_be_corrected_without_reopening(self):
        sb = ready(self)
        tid = task(sb, track="main")
        sb.move(tid, "done", set={"evidence": "proof.md"})
        sb.ok("item update", data={"actor": ACTOR, "id": tid, "set": {"track": "intake"}})
        self.assertEqual(sb.get(tid)["state"], "done")
        self.assertEqual(sb.get(tid)["fields"]["track"], "intake")


class TestLegacyTrackRead(unittest.TestCase):
    def test_frozen_track_writer_preserves_legacy_clock_and_group(self):
        p = LegacyProject(tracks=TRACKS)
        p.seed_task("TASK-001", track="ops", stage="triaged", arrived="2026-08-01",
                    stage_since="2026-08-02", group="Support lane")
        before = {str(f.relative_to(p.root)): f.read_bytes() for f in p.root.rglob("*") if f.is_file()}
        for target in ("main", "ops", "typo"):
            code, out = p.run("track", "TASK-001", "--track", target)
            self.assertEqual(code, 1, out)
            self.assertIn("perry-kernel item update", out["refused"])
            self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                              for f in p.root.rglob("*") if f.is_file()}, before)
        code, out = p.run("list", "--all")
        self.assertEqual(code, 0, out)
        row = out["tasks"][0]
        self.assertEqual((row["track"], row["stage"], row["arrived"], row["group"]),
                         ("ops", "triaged", "2026-08-01", "Support lane"))


if __name__ == "__main__":
    unittest.main()
