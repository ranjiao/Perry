"""Contract tests for work modes and the verification ladder — DESIGN-003.

The claim under test: **a project's shape is a declaration, and declaring
nothing must cost nothing.**

DESIGN-003 generalizes Perry past the software project by making shape a
property of a *track* rather than of the whole project. The risk that comes with
that is not subtle — every existing Perry project was written before tracks
existed, and a schema that requires the new structure would invalidate all of
them at once. So the design's goal 7 is explicit: absent a declaration,
everything is a single `project`-mode track and today's behavior is
bit-identical.

That property is what most of this file tests, and the mechanism that delivers
it is worth naming because it is easy to break later: **the new structure is
declared through `tables[]`, not through `headings[]`.** `bin/perry-lint`
treats every entry in `headings[]` as required, but skips a `tables[]` spec
whose section is absent (`if not bodies: continue`). So `## Tracks` in
`.perry/config.md` and `## Intake` in `BOARD.md` validate strictly when present
and cost nothing when absent. Moving either into `headings[]` would silently
turn an opt-in into a migration.

The second half tests that opting in is actually checked — a schema that
accepts `mode: kanban` or `rung: V9` is documentation, not a contract.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import config_store  # noqa: E402
from held_board import import_board  # noqa: E402


PERRY_HOME = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
LINT = PERRY_HOME / "bin" / "perry-lint"

MODES = ["project", "pipeline", "queue", "inquiry"]
RUNGS = ["V0", "V1", "V2", "V3", "V4", "V5", "V6"]


def file_spec(file_id: str) -> dict:
    for f in SCHEMA["files"]:
        if f["id"] == file_id:
            return f
    raise AssertionError(f"no files[] entry with id {file_id!r}")


#: `stores.declared[".perry/config.jsonl"]` — where the track register's shape
#: went when ADR-019 deleted the document its table was in.
STORE_SPEC = SCHEMA["stores"]["declared"][".perry/config.jsonl"]

#: `work_modes.modes.<mode>.default_stages`, by mode. Read rather than typed:
#: a mode that changes its vocabulary changes this test and nothing else.
DEFAULT_STAGES = {m: list((c or {}).get("default_stages") or [])
                  for m, c in SCHEMA["work_modes"]["modes"].items()}


def table_spec(file_id: str, under_fragment: str) -> dict | None:
    for t in file_spec(file_id).get("tables", []):
        if under_fragment in t["under"]:
            return t
    return None


def lint(root: Path) -> str:
    r = subprocess.run(
        ["python3", str(LINT), "--root", str(root)],
        capture_output=True, text=True,
    )
    return r.stdout + r.stderr


class TestEnums(unittest.TestCase):
    def test_mode_enum_is_exactly_the_four_shapes(self):
        """Decision 1 chose four over two or three. A fifth is a design
        revision, not a schema edit — mode determines spine, triage and default
        rung, so adding one silently would leave three of those undefined."""
        self.assertEqual(SCHEMA["enums"]["mode"], MODES)

    def test_verification_rungs_are_ordered_v0_to_v6(self):
        self.assertEqual(SCHEMA["enums"]["verification_rung"], RUNGS)

    def test_every_mode_declares_its_semantics(self):
        """A mode with no declared spine/closure/default rung is a label."""
        declared = SCHEMA["work_modes"]["modes"]
        self.assertEqual(sorted(declared), sorted(MODES))
        for name, m in declared.items():
            for field in ("ends_when", "unit", "spine", "calendar", "default_rung"):
                self.assertTrue(m.get(field), f"{name} is missing {field}")
            self.assertIn(m["default_rung"], RUNGS, f"{name} default_rung")

    def test_every_rung_is_documented(self):
        self.assertEqual(sorted(SCHEMA["verification"]["rungs"]), sorted(RUNGS))

    def test_calendar_is_binding_exactly_where_the_design_says(self):
        """`goals/SKILL.md § Why phases, not months` is right for project mode
        and wrong for the 33.4% — month-end close and a filing deadline ARE
        the calendar. DESIGN-003 §1.4 B1."""
        cal = {n: m["calendar"] for n, m in SCHEMA["work_modes"]["modes"].items()}
        self.assertEqual(cal["pipeline"], "binding")
        self.assertEqual(cal["queue"], "binding")
        self.assertEqual(cal["project"], "advisory")
        self.assertEqual(cal["inquiry"], "advisory")

    def test_default_track_is_project_mode(self):
        """Goal 7: declaring nothing reproduces today's Perry exactly."""
        self.assertEqual(SCHEMA["work_modes"]["default_mode"], "project")
        self.assertEqual(SCHEMA["work_modes"]["default_track"], "main")


class TestOptInIsFree(unittest.TestCase):
    """The new structure must be invisible to a project that never opts in."""

    def test_a_track_record_is_optional_not_a_required_file(self):
        """`## Tracks` was a `tables[]` spec and deliberately NOT a
        `headings[]` entry, because a required heading would have invalidated
        every pre-DESIGN-003 project. ADR-019 deleted the file, and the
        property is stronger rather than weaker: there is no `files[]` entry
        for a project to fail to match, and `stores.declared` says in as many
        words that a project declaring no track has one implicit `main`."""
        self.assertIsNone(
            next((f for f in SCHEMA["files"] if f["id"] == "config"), None),
            "ADR-019 removed the .perry/config.md files[] entry")
        rec = STORE_SPEC["records"]["track"]
        self.assertIn("OPTIONAL", rec["note"])
        self.assertIn("main", rec["note"])

    def test_intake_is_a_table_spec_not_a_required_heading(self):
        spec = file_spec("board")
        self.assertNotIn("Intake", json.dumps(spec.get("headings", [])))
        self.assertIsNotNone(table_spec("board", "Intake"))

    def test_track_and_verification_are_not_required_board_columns(self):
        """`bin/perry-lint` errors on any column in `columns[]` that a table
        lacks. Track and Verification are validated via enum_columns /
        optional_columns instead, which are skipped when the column is absent."""
        t = table_spec("board", "P[012]")
        self.assertNotIn("Track", t["columns"])
        self.assertNotIn("Verification", t["columns"])
        self.assertIn("Verification", t["enum_columns"])
        self.assertEqual(t["enum_columns"]["Verification"], "verification_rung")

    def test_design_003_adds_no_new_claimed_path(self):
        """Goal 5, tightened during `decide` from 'at most one' to zero.
        Intake lives inside BOARD.md, which claims[] already covers; tracks
        live inside .perry/, likewise. DESIGN-002's rule under pressure."""
        claimed = {c["path"] for c in SCHEMA["claims"]}
        self.assertIn("BOARD.md", claimed)
        self.assertIn(".perry/", claimed)
        for path in ("INTAKE.md", "TRACKS.md", "packs/", "modes/", "sources/"):
            self.assertNotIn(
                path, claimed,
                f"{path} would be a new claim on a namespace Perry was not given",
            )

    def test_shipped_fixtures_declare_no_tracks(self):
        """If a fixture opted in, the no-op guarantee would stop being tested
        by the rest of the suite."""
        for name in ("sample-project", "sample-project-zh"):
            cfg = (PERRY_HOME / "tests" / "fixtures" / name / ".perry"
                   / "config.jsonl")
            if cfg.exists():
                self.assertNotIn('"kind": "track"',
                                 cfg.read_text(encoding="utf-8"))


class TestOptInIsChecked(unittest.TestCase):
    """Declaring a track must be validated, or the enum is decoration."""

    def _project(self, tracks: list[dict]) -> str:
        """**The enum check moved with the register** (ADR-019).

        These were `## Tracks` rows and the check was
        `files[id=config].tables[Tracks].enum_columns`, driven by
        `perry-lint`'s generic table walk. The table is gone; the same two
        enums are now read off a `kind: track` RECORD in
        `perry-lint § check_config_store`, from the same `schema § enums`.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_store.write_config(root, tracks=tracks)
            return lint(root)

    def test_valid_tracks_lint_clean(self):
        out = self._project([
            config_store.track("core", "project", spine="phase/",
                               default_rung="V3"),
            config_store.track("docs", "pipeline", spine="commitments",
                               stages="draft→review→published",
                               default_rung="V5"),
            config_store.track("issues", "queue", spine="standing", sla="5d",
                               cycle="weekly", default_rung="V2"),
            config_store.track("why", "inquiry", spine="questions",
                               default_rung="V4"),
        ])
        self.assertNotIn("bad-enum", out)

    def test_unknown_mode_is_rejected(self):
        out = self._project([
            config_store.track("issues", "kanban", spine="standing",
                               default_rung="V2")])
        self.assertIn("bad-enum", out)
        self.assertIn("kanban", out)

    def test_unknown_rung_is_rejected(self):
        out = self._project([
            config_store.track("core", "project", spine="phase/",
                               default_rung="V9")])
        self.assertIn("bad-enum", out)
        self.assertIn("V9", out)

    def test_a_track_record_with_no_mode_is_DETERMINED_not_rejected(self):
        """`table-columns` was the finding while `Mode` was a required COLUMN
        of a table that could omit it. A record cannot omit a field, and an
        EMPTY `mode` is a state DESIGN-003 already answers: `project`.

        So this is not the same check moved — it is a check whose subject the
        format removed, and the honest replacement is the assertion that the
        state is determined rather than reported. It is asserted here rather
        than left silent, because "the linter says nothing" and "the reader
        answers `project`" are different facts and only one of them is true.
        """
        out = self._project([dict(
            config_store.track("core", "project", spine="phase/"),
            mode="")])
        self.assertNotIn("bad-enum", out)
        state = load_bin_module("perry-state")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_store.write_config(root, tracks=[dict(
                config_store.track("core", "project", spine="phase/"),
                mode="")])
            self.assertEqual(
                [t["mode"] for t in state.declared_tracks(root)], ["project"])




# `TestTrackParsing` stood here: six unit tests over `bin/perry-state §
# parse_tracks`, the `## Tracks` reader. Its subject was that the router has no
# "no tracks declared" branch, so an empty list from that reader would become a
# silent no-mode-loaded session rather than a visible error.
#
# ADR-019 deleted the table and the reader. **The invariant did not go with
# them** — it moved one function up, to `declared_tracks_detail`, which returns
# `[dict(DEFAULT_TRACK)]` for every source that is not `store`, and it is
# asserted by `TestTheTrackRegisterIsReadFromTheStore` below over a project
# with no store at all. What is gone is the table-shaped half: a heading
# spelled `## 轨道`, a header row that must be recognised before a row can be
# read, and a later `## …` section bleeding into the register. A record has
# none of those failure modes, which is most of why ADR-019 was taken.


def load_bin_module(name: str):
    """Import an extensionless script from `bin/` as a module."""
    import importlib.util
    loader = importlib.machinery.SourceFileLoader(
        name.replace("-", "_"), str(PERRY_HOME / "bin" / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


#: The store the fixture below declares, and the table it declares. They
#: DISAGREE on purpose: the store carries a second track, `intake`, in queue
#: mode with a 5d SLA, and the rendered table carries only `main`. Every
#: assertion in the class is "which of the two did this tool believe".
_STORE_TRACKS = (
    '{"kind": "track", "track": "main", "mode": "project", "spine": "phase/",'
    ' "stages": "", "wip": "", "sla": "", "cycle": "", "default_rung": "V3",'
    ' "order": 0}\n'
    '{"kind": "track", "track": "intake", "mode": "queue", "spine": "standing",'
    ' "stages": "new→triaged→resolved", "wip": "4", "sla": "5d",'
    ' "cycle": "weekly", "default_rung": "V2", "order": 1}\n'
)
class TestTheTrackRegisterIsReadFromTheStore(unittest.TestCase):
    """`.perry/config.jsonl` is the register, and since ADR-019 the only one.

    ADR-007 made `.perry/config.md` a rendered projection of
    `.perry/config.jsonl`, and four call sites went on reading the rendering as
    truth: `bin/perry-state § parse_config`, `bin/perry-goals § tracks_of`,
    `bin/perry-diagnose § scan_work_modes` and `bin/perry-task § main`
    (P003-O2-KR1). This class was built to catch that: the fixture wrote a
    `## Tracks` table that CONTRADICTED the store, because on every real
    project the two agree and "which one did you read" has no observable
    answer unless they differ.

    **That question is now unaskable, and the tests below are what is left of
    it.** ADR-019 deleted the file, so the four readers cannot disagree with
    each other about which register answered — they can only disagree about
    what the one register SAYS, and that is what each test asserts: `main` is
    `project` and `intake` is `queue` with a 5d SLA, in all four, out of one
    store. A reader that started inventing its own default rather than reading
    the record still goes red here.

    The last two tests pin what makes the register usable rather than merely
    present: a project with NO store falls back to DESIGN-003's implicit
    `main` rather than to nothing, and a blank field still reports the blank
    marker, so the payload `perry-state --json` hands the dashboard did not
    move when the table it used to be rendered from went away.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="perry-track-store-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = Path(self.tmp) / "project"
        shutil.copytree(PERRY_HOME / "tests" / "fixtures" / "sample-project",
                        self.root)
        # The fixture project's own settings, plus this class's two tracks.
        # Appended to the store rather than replacing it: `State root` and the
        # document language are what make it a project the readers below can
        # resolve at all.
        cfg = self.root / ".perry" / "config.jsonl"
        cfg.write_text(cfg.read_text(encoding="utf-8") + _STORE_TRACKS,
                       encoding="utf-8")

    def declared(self, tracks) -> list[tuple[str, str]]:
        return [(t["track"], t["mode"]) for t in tracks]

    def test_perry_state_reports_the_register_the_store_holds(self):
        state = load_bin_module("perry-state")
        got = state.parse_config(self.root)["tracks"]
        self.assertEqual(self.declared(got),
                         [("main", "project"), ("intake", "queue")])
        self.assertEqual(got[1]["sla"], "5d")

    def test_perry_goals_reports_the_register_the_store_holds(self):
        goals = load_bin_module("perry-goals")
        self.assertEqual(self.declared(goals.tracks_of(self.root)),
                         [("main", "project"), ("intake", "queue")])

    def test_perry_diagnose_reports_the_register_the_store_holds(self):
        diagnose = load_bin_module("perry-diagnose")
        scan = diagnose.scan_work_modes(self.root, self.root)
        self.assertTrue(scan["available"])
        self.assertEqual([(t["track"], t["declared_mode"])
                          for t in scan["tracks"]],
                         [("main", "project"), ("intake", "queue")])

    def test_perry_task_accepts_a_track_only_the_store_declares(self):
        """A refusal here is the projection winning over the register.

        `--dry-run`, so the assertion is about which register the writer
        resolved `--track` against and nothing is written. The stage the row
        would be born into comes from the same record, which is why it is
        asserted too: reading the table would give `intake` no mode at all.
        """
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-task"), "add",
             "--root", str(self.root), "--title", "probe",
             "--summary", "A fixture row that exists so the writer has something to write. It carries no meaning beyond that.",
             "--deliverable", "d", "--verification", "v",
             # `--unlinked` since TASK-439: `add` refuses a row answering the
             # KR question neither way, and the refusal fires before the track
             # is resolved — so without it this test would read a refusal about
             # linkage and report it as the projection beating the register.
             # Honest for a throwaway probe row, which serves no key result.
             "--track", "intake", "--unlinked", "--dry-run", "--json"],
            capture_output=True, text=True)
        payload = json.loads(r.stdout)
        self.assertNotIn("refused", payload,
                         f"perry-task refused a track the store declares: "
                         f"{payload.get('refused')}")
        # Read under the declared header (TASK-262 round 4a): the row a write
        # lays out is the declared board's, whose `Verification` column sits
        # between `Track` and `Stage`.
        board = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-tasks"), "board",
             "--root", str(self.root)], capture_output=True, text=True).stdout
        header = next(l for l in board.split("\n") if l.startswith("| ID |"))
        split = lambda line: [c.strip() for c in line.strip().strip("|").split("|")]  # noqa: E731
        cells = dict(zip([h.lower() for h in split(header)], split(payload["row"])))
        self.assertEqual((cells["track"], cells["stage"]), ("intake", "triaged"))

    def test_a_project_with_no_store_reads_the_implicit_main_track(self):
        """The invariant `TestTrackParsing` used to hold one function lower.

        This was `test_a_project_with_no_store_still_reads_its_table` — the
        adoption/migration path, where `parse_tracks` answered from
        `.perry/config.md`. There is no table to fall back to, and the answer
        is unchanged, because DESIGN-003 specifies it: one implicit track named
        `main`, mode `project`. The router has no "no tracks declared" branch,
        so `[]` here would be a silent no-mode-loaded session."""
        (self.root / ".perry" / "config.jsonl").unlink()
        state = load_bin_module("perry-state")
        self.assertEqual(self.declared(state.parse_config(self.root)["tracks"]),
                         [("main", "project")])

    def test_a_blank_stored_cell_still_reports_the_blank_marker(self):
        """The store holds `""` where the table wrote `—`, and they are one
        value — every consumer of these cells routes it through
        `lib.is_blank_cell`. The payload keeps the marker, so neither
        converting the reader (TASK-233) nor deleting the table (ADR-019)
        changed what the dashboard prints."""
        state = load_bin_module("perry-state")
        main = state.parse_config(self.root)["tracks"][0]
        self.assertEqual(
            [main["stages"], main["wip"], main["sla"], main["cycle"]],
            ["—", "—", "—", "—"])
        self.assertEqual(main["stage_list"], [])
        self.assertFalse(main["stages_declared"])


class TestVerificationLint(unittest.TestCase):
    """`perry-lint --verification` — advisory, but it must actually fire.

    Advisory does not mean toothless. The failure this guards against is a pass
    that reports nothing because it scanned nothing, which is why the empty-scan
    case is tested explicitly alongside the positive ones.
    """

    BOARD_HEAD = (
        "# Board — T\n\n## P0 (must finish this period)\n\n"
        "| ID | Title | Owner | Status | Next action | Evidence | Verification |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    TAIL = (
        "\n## P1\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
        "\n## P2\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
        "\n## Cadence\n\n| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n|---|---|---|---|---|---|\n"
        "\n## User Input Queue\n\n| USER-id | Needed from user | Blocks | Idle | Status |\n|---|---|---|---|---|\n"
        "\n## Top risks\n\n- none\n"
    )

    def _run(self, rows: str, hook: str | None = None) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry").mkdir()
            # **Installed, and the rows imported** (TASK-262 round 4b). The
            # pass read the `done` rows of a held `BOARD.md` under a
            # `.perry/config.md` nothing reads since ADR-019. That file is
            # retired and the pass judges `tasks.jsonl`'s `done` records that
            # no `done` event closed (F14) — exactly what these rows become
            # through `perry-tasks write --from-board`, which appends no event.
            config_store.write_config(root, {"State root": "."})
            if hook:
                (root / ".perry" / "hook.md").write_text(
                    "# hook\n\n## High-stakes operations\n\n" + hook + "\n")
            (root / "BOARD.md").write_text(self.BOARD_HEAD + rows + self.TAIL)
            import_board(root, "write")
            r = subprocess.run(
                ["python3", str(LINT), "--verification", "--root", str(root), "--json"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, "advisory mode must always exit 0")
            return json.loads(r.stdout)

    def rules(self, out: dict) -> list[str]:
        return [f["rule"] for f in out["findings"]]

    def test_a_satisfiable_rung_is_silent(self):
        out = self._run(
            "| T-1 | Ship | Coding Agent | done | — | `pytest tests/ -q` green | V3 |\n")
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["done_rows_scanned"], 1)

    def test_done_with_no_rung_is_reported(self):
        out = self._run("| T-1 | Ship | Coding Agent | done | — | some/file.md | |\n")
        self.assertIn("no-verification-rung", self.rules(out))

    def test_v0_is_never_a_valid_rung(self):
        out = self._run("| T-1 | Ship | Coding Agent | done | — | looks fine | V0 |\n")
        self.assertIn("rung-not-satisfied", self.rules(out))

    def test_v3_without_anything_rerunnable_is_reported(self):
        out = self._run("| T-1 | Ship | Coding Agent | done | — | it works now | V3 |\n")
        self.assertIn("rung-not-satisfied", self.rules(out))

    def test_v4_without_a_rubric_is_reported(self):
        """A V4 claim citing no acceptance criteria is V1 in a costume."""
        out = self._run("| T-1 | Ship | Coding Agent | done | — | reviewer said ok | V4 |\n")
        self.assertIn("rung-not-satisfied", self.rules(out))

    def test_v5_without_a_date_is_reported(self):
        out = self._run("| T-1 | Ship | Coding Agent | done | — | signed off | V5 |\n")
        self.assertIn("rung-not-satisfied", self.rules(out))

    def test_v5_with_a_date_passes(self):
        out = self._run(
            "| T-1 | Ship | Coding Agent | done | — | Ran J. checked the diff 2026-08-16 | V5 |\n")
        self.assertEqual(out["findings"], [])

    def test_high_stakes_row_below_v5_is_reported(self):
        """The consequence rule has no field of its own — it reads the
        project's own hook, so a project that armed one gets the check for
        free and a project that didn't gets no false positives."""
        out = self._run(
            "| T-1 | Push the release | Coding Agent | done | — | `make release` ok | V3 |\n",
            hook="- Publishing — `git push`, `release`\n",
        )
        self.assertIn("consequence-needs-signoff", self.rules(out))

    def test_no_hook_means_no_consequence_findings(self):
        out = self._run(
            "| T-1 | Push the release | Coding Agent | done | — | `make release` ok | V3 |\n")
        self.assertNotIn("consequence-needs-signoff", self.rules(out))

    def test_board_with_no_rung_column_at_all_is_reported_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry").mkdir()
            # Installed and imported, for `_run`'s reason (TASK-262 round 4b):
            # two `done` records with no rung and no `done` event.
            config_store.write_config(root, {"State root": "."})
            (root / "BOARD.md").write_text(
                "# Board\n\n## P0\n\n"
                "| ID | Title | Owner | Status | Next action | Evidence |\n"
                "|---|---|---|---|---|---|\n"
                "| T-1 | a | Coding Agent | done | — | x.md |\n"
                "| T-2 | b | Coding Agent | done | — | y.md |\n" + self.TAIL)
            import_board(root, "write")
            r = subprocess.run(
                ["python3", str(LINT), "--verification", "--root", str(root), "--json"],
                capture_output=True, text=True)
            out = json.loads(r.stdout)
        self.assertIn("board-declares-no-rungs", [f["rule"] for f in out["findings"]])
        self.assertEqual(out["done_rows_scanned"], 2)

    def test_an_empty_scan_is_not_a_pass(self):
        """Zero done rows must be distinguishable from zero findings, or the
        mode reports a checkmark for having checked nothing."""
        out = self._run("| T-1 | Ship | Coding Agent | in_progress | — | — | |\n")
        self.assertEqual(out["done_rows_scanned"], 0)
        self.assertEqual(out["findings"], [])


class TestRungDistribution(unittest.TestCase):
    """`perry-state` must report HOW closures were verified, not just how many.

    `unrated` is deliberately not folded into V1: "nobody said" and "someone
    said an artifact exists" are different claims, and collapsing them would
    flatter the board during exactly the release where the number is supposed
    to be watched.
    """

    def _state(self, rows: str, header: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry").mkdir()
            # TASK-237 3b′: `.perry/config.md` was deleted by ADR-019 and a
            # `BOARD.md` alone no longer makes a project installed; the config
            # store declares it, and changes nothing this test reads.
            (root / ".perry" / "config.jsonl").write_text(
                '{"kind": "setting", "key": "state_root", "label": '
                '"State root", "value": ".", "order": 0}\n')
            (root / "BOARD.md").write_text(
                "# Board\n\n## P0\n\n" + header + rows
                + "\n## P1\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
                + "\n## P2\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
                + "\n## Cadence\n\n| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n|---|---|---|---|---|---|\n"
                + "\n## User Input Queue\n\n| USER-id | Needed from user | Blocks | Idle | Status |\n|---|---|---|---|---|\n"
                + "\n## Top risks\n\n- none\n")
            # The closures reach `perry-state` as `done` records no `done`
            # event closed (TASK-262 round 4b): a held board's rows are not
            # read, and the header-name resolution this module asserts is the
            # import's, `perry-tasks write --from-board`.
            import_board(root, "write")
            r = subprocess.run(
                ["python3", str(PERRY_HOME / "bin" / "perry-state"),
                 "--root", str(root), "--json"],
                capture_output=True, text=True)
            return json.loads(r.stdout)["board"]["verification"]

    WITH = ("| ID | Title | Owner | Status | Next action | Evidence | Verification |\n"
            "|---|---|---|---|---|---|---|\n")
    WITHOUT = ("| ID | Title | Owner | Status | Next action | Evidence |\n"
               "|---|---|---|---|---|---|\n")

    def test_rungs_are_counted_and_unrated_kept_separate(self):
        v = self._state(
            "| T-1 | a | Coding Agent | done | — | `pytest -q` | V3 |\n"
            "| T-2 | b | Coding Agent | done | — | Ran J. 2026-08-16 | V5 |\n"
            "| T-3 | c | Coding Agent | done | — | f.md | |\n"
            "| T-4 | d | Coding Agent | in_progress | — | — | |\n", self.WITH)
        self.assertEqual(v["closed"], 3)
        self.assertEqual(v["by_rung"], {"V3": 1, "V5": 1})
        self.assertEqual(v["unrated"], 1)

    def test_a_board_with_no_rung_column_reports_all_closures_unrated(self):
        v = self._state(
            "| T-1 | a | Coding Agent | done | — | f.md |\n"
            "| T-2 | b | Coding Agent | done | — | g.md |\n", self.WITHOUT)
        self.assertEqual(v["closed"], 2)
        self.assertEqual(v["by_rung"], {})
        self.assertEqual(v["unrated"], 2)

    def test_nothing_closed_reports_zero_not_absent(self):
        v = self._state(
            "| T-1 | a | Coding Agent | in_progress | — | — |\n", self.WITHOUT)
        self.assertEqual(v, {"closed": 0, "by_rung": {}, "unrated": 0})

    def test_rung_is_resolved_by_header_name_not_position(self):
        """A board that puts Verification somewhere other than last must still
        rate the right cell — reading it positionally would rate whatever
        happened to be in column 7."""
        v = self._state(
            "| T-1 | a | Coding Agent | done | — | `pytest -q` | V3 | extra |\n",
            "| ID | Title | Owner | Status | Next action | Evidence | Verification | Notes |\n"
            "|---|---|---|---|---|---|---|---|\n")
        self.assertEqual(v["by_rung"], {"V3": 1})

    def test_a_junk_rung_counts_as_unrated_not_as_a_rung(self):
        v = self._state(
            "| T-1 | a | Coding Agent | done | — | f.md | probably fine |\n", self.WITH)
        self.assertEqual(v["by_rung"], {})
        self.assertEqual(v["unrated"], 1)


class TestV4Corrections(unittest.TestCase):
    """Regressions for the four blocking findings of the TASK-019/020 V4 review.

    Each of these is a control that a mode file *described* while its data had
    nowhere to live. That class of defect is invisible to the author and cheap
    to reintroduce, so each finding gets a test rather than a paragraph.
    Evidence: `perry/evidence/2026-08/TASK-019-020-v4-review.md`.
    """

    def board_table(self, fid: str, under: str) -> dict:
        return table_spec(fid, under)

    # B1 — stages had no recording location
    def test_stage_is_a_board_column_and_is_not_the_status_enum(self):
        t = self.board_table("board", "P[012]")
        self.assertIn("Stage", t["optional_columns"])
        self.assertNotIn("Stage", t["columns"])
        self.assertNotIn(
            "Stage", t["enum_columns"],
            "Stage must NOT be enum-checked — the vocabulary is per-track, "
            "declared in .perry/config.md, not global",
        )
        self.assertEqual(t["enum_columns"]["Status"], "task_status",
                         "Status keeps its global lifecycle enum in every mode")

    # B2 — the arrival date was destroyed on routing
    def test_arrived_is_declared_on_both_sides_of_the_route(self):
        """**Schema only.** This asserts the column is declared in both
        tables; it routes nothing and cannot fail on a router that drops the
        value. It was the only guard on B-2 for a release, which is how B-2
        survived a review — `test_task_writer.py`
        `TestModeColumnsOnBoardsPerryDidNotBuild` is the one that can fail.
        Kept because a declaration and a behaviour are different claims.
        """
        board = self.board_table("board", "P[012]")
        intake = self.board_table("board", "Intake")
        self.assertIn("Arrived", intake["columns"])
        self.assertIn("Arrived", board["optional_columns"],
                      "queue triage measures today − Arrived; a routed row "
                      "without it is exempt from the only clock governing it")

    def test_intake_can_record_a_drop_reason_or_defer_condition(self):
        intake = self.board_table("board", "Intake")
        self.assertIn("Outcome", intake["columns"] + list(
            (intake.get("optional_columns") or {}).keys()),
            "triage mandates dropped-with-a-reason and deferred-with-a-"
            "condition; the table must have somewhere to put them")

    # B3 — the WIP limit had no home and no default
    def test_track_register_declares_wip_sla_and_cycle(self):
        """B3's finding was that a WIP limit had no home. The home moved from
        `optional_columns` on a table spec to `fields` on a store record
        (ADR-019); `required` is the same two, for the same reason a partial
        register must not become a lint error."""
        rec = STORE_SPEC["records"]["track"]
        for field in ("stages", "wip", "sla", "cycle"):
            self.assertIn(field, rec["fields"],
                          f"{field} has no declaration site")
        self.assertEqual(rec["required"], ["kind", "track", "mode"],
                         "only track and mode may be required, or every "
                         "partial register becomes a lint error")

    # B4 — Commitments had no track key, no item link, no owner
    def test_commitments_table_is_track_keyed_and_owned_by_the_goals_lane(self):
        okr = file_spec("okr")
        t = next(x for x in okr["tables"] if "Commitments" in x["under"])
        self.assertEqual(okr["owner"], "goals",
                         "OKR.md has one writer; Commitments is a section of it")
        self.assertIn("Track", t["columns"],
                      "two tracks in one table need a key or the promises merge")
        self.assertIn("Promise", t["columns"])
        self.assertIn("Due", t["columns"],
                      "the typed half of the clock is required (TASK-091)")
        self.assertNotIn("By when", t["columns"],
                         "the column that carried two value spaces is gone")
        self.assertIn("By when note", t["optional_columns"],
                      "the prose half has to have somewhere to go, or the "
                      "split loses what the old column also held")

    def test_commitments_is_optional_so_no_existing_okr_breaks(self):
        okr = file_spec("okr")
        self.assertNotIn("Commitments", json.dumps(okr.get("headings", [])))


class TestATrackRecordIsReadByFieldNotByPosition(unittest.TestCase):
    """The register is read by NAME, never by position.

    This was `TestTrackColumnsResolveByName`, over `## Tracks` header cells:
    only `Track` and `Mode` were required, so any other column could be absent
    and a positional read would attribute one column's value to another the
    moment a project omitted one — the same defect the V4 review caught in the
    board-row parser.

    **ADR-019 makes the shifting failure impossible rather than checked.** A
    record is keyed, so an absent field cannot slide another field's value into
    its place; the column-order and missing-header cases below have no
    counterpart at all. What survives is the property those cases existed to
    protect — every declared field reaches the payload under its own name, and
    a field the project did not declare reads as blank rather than as its
    neighbour — asserted on the reader that is left.
    """

    def setUp(self):
        self.ps = load_bin_module("perry-state")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def tracks(self, records):
        config_store.write_config(self.root, tracks=records)
        return self.ps.declared_tracks(self.root)

    def test_a_full_record_maps_every_field(self):
        got = self.tracks([config_store.track(
            "blog", "pipeline", spine="commitments", stages="a→b→c",
            wip="b:2", sla="5d", cycle="2026-W34", default_rung="V5")])[0]
        self.assertEqual(got["stages"], "a→b→c")
        self.assertEqual(got["wip"], "b:2")
        self.assertEqual(got["sla"], "5d")
        self.assertEqual(got["cycle"], "2026-W34")
        self.assertEqual(got["default_rung"], "V5")

    def test_undeclared_fields_do_not_take_a_neighbours_value(self):
        """The whole point: a minimal register must not read `V3` as a stage.

        The marker rather than `""` on the way out is `track_from_record`'s
        rule — a declared blank is spelled the way this project's files spell
        it, so the payload did not move when the reader converted.
        """
        got = self.tracks([config_store.track(
            "core", "project", default_rung="V3")])[0]
        self.assertEqual(got["default_rung"], "V3")
        for field in ("stages", "wip", "sla"):
            self.assertEqual(got[field], "—", field)
        self.assertEqual(got["stage_list"],
                         DEFAULT_STAGES["project"])
        self.assertFalse(got["stages_declared"])

    def test_a_record_whose_fields_arrive_in_any_order_still_resolves(self):
        """`json.dumps` writes a dict in insertion order, so a store written by
        hand can carry the fields in any order at all. `record` re-keys them;
        nothing downstream reads a position."""
        rec = config_store.track("ops", "queue", sla="3d", default_rung="V2")
        shuffled = {k: rec[k] for k in reversed(list(rec))}
        got = self.tracks([shuffled])[0]
        self.assertEqual(got["track"], "ops")
        self.assertEqual(got["mode"], "queue")
        self.assertEqual(got["default_rung"], "V2")
        self.assertEqual(got["sla"], "3d")

    def test_a_store_that_declares_no_track_is_the_implicit_main(self):
        """`test_a_table_with_no_recognizable_header_is_refused_not_guessed`
        was here: a `## Tracks` table whose header nothing recognised had to
        yield the implicit `main` rather than a guess. A record has no header
        to be unrecognisable; the state that is left is a store carrying no
        track record at all, and it answers the same way."""
        got = self.tracks([])
        self.assertEqual(got[0]["track"], "main")
        self.assertFalse(got[0]["declared"])


class TestI18n(unittest.TestCase):
    def test_new_columns_have_a_chinese_alias(self):
        """A column with no glossary entry silently zeroes its dashboard row in
        a Chinese project — `reference/i18n.md`."""
        cols = SCHEMA["i18n"]["columns"]
        for name in ("Track", "Mode", "Verification", "Default rung",
                     "Arrived", "Request"):
            self.assertIn(name, cols, f"{name} missing from i18n.columns")
            self.assertTrue(cols[name].get("zh"))

    def test_track_section_headers_accept_chinese(self):
        """`## 轨道` was the localized spelling of the track section. There is
        no section: a track is a record and its fields are ASCII keys in every
        language, which is the same rule `schema § i18n.invariant` already
        applied to this register's field NAMES. `## 收件` is unaffected —
        `BOARD.md` is still a document."""
        self.assertIn("收件", table_spec("board", "Intake")["under"])



class TestInquiryHasDataForEveryControl(unittest.TestCase):
    """The defect that failed two prior reviews: a control described in prose
    whose data has nowhere to live. `modes/inquiry.md` was written after the
    schema fields existed rather than before, and this pins that order."""

    def test_the_question_tree_edge_is_a_real_column(self):
        t = table_spec("board", "P[012]")
        self.assertIn("Parent", t["optional_columns"],
                      "a question tree needs an edge; BOARD.md has no nesting")
        self.assertNotIn("Parent", t["columns"],
                         "Parent must stay optional or every non-inquiry board "
                         "becomes a lint error")

    def test_the_source_of_truth_for_citations_is_validated(self):
        """`knowledge/` was claimed but had no files[] entry, so digest headers
        were never checked — provenance is unenforceable without one."""
        k = file_spec("knowledge")
        fields = {f["name"] for f in k["header_fields"]}
        self.assertEqual(k["owner"], "work")
        for required in ("Id", "Source", "Received"):
            self.assertIn(required, fields,
                          f"a digest with no {required} cannot back a citation")
        idf = next(f for f in k["header_fields"] if f["name"] == "Id")
        self.assertEqual(idf["pattern"], r"SRC-\d+")

    def test_every_mode_starts_at_the_floor(self):
        """**Changed 2026-09-11 with the rung rule, and the old name is the
        point.** This asserted `inquiry` starts at V4, and three sibling modes
        started at V3, V5 and V2 by the same table — `ADR-005`'s, where the
        mode was a proxy for how much a defect in it could cost.

        `ADR-020` replaced that proxy with a question a mode cannot answer:
        did the row touch a write path or `schema/state-schema.json`? A mode
        default is chosen before any row exists, so it can only be the floor,
        and `review.md § 0` raises it per row. All four now start at V2.

        Asserted over every declared mode rather than one, because four
        separate assertions of four different values are how the old table
        outlived the decision that set it — only `inquiry`'s was ever pinned,
        so changing `project` from V3 broke nothing and said nothing.
        """
        modes = SCHEMA["work_modes"]["modes"]
        self.assertTrue(modes, "no modes declared")
        for name, spec in modes.items():
            with self.subTest(mode=name):
                self.assertEqual(spec["default_rung"], "V2", name)

    def test_inquiry_calendar_stays_advisory(self):
        """A deadline on a question produces a confident answer, not a correct
        one — the one place besides project mode where advisory is right."""
        self.assertEqual(SCHEMA["work_modes"]["modes"]["inquiry"]["calendar"],
                         "advisory")

    def test_every_field_the_mode_file_names_exists_somewhere(self):
        text = (PERRY_HOME / "modes" / "inquiry.md").read_text()
        board = table_spec("board", "P[012]")
        cols = set(board["columns"]) | set(board["optional_columns"])
        for named in ("Parent", "Stage", "Stage since", "Verification"):
            self.assertIn(f"`{named}`", text,
                          f"inquiry.md never names the {named} column it relies on")
            self.assertIn(named, cols,
                          f"inquiry.md relies on {named}, which the schema lacks")
        self.assertIn("WIP", (PERRY_HOME / "modes" / "inquiry.md").read_text())
        self.assertIn("wip", STORE_SPEC["records"]["track"]["fields"])


class TestProvenanceLint(unittest.TestCase):
    """`--provenance` must fire on all four failure modes, and must not report
    a pass over an empty scan."""

    def _run(self, digests: dict, citing: str = "") -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry").mkdir()
            # TASK-237 3b′: `.perry/config.md` was deleted by ADR-019 and a
            # `BOARD.md` alone no longer makes a project installed; the config
            # store declares it, and changes nothing this test reads.
            (root / ".perry" / "config.jsonl").write_text(
                '{"kind": "setting", "key": "state_root", "label": '
                '"State root", "value": ".", "order": 0}\n')
            kd = root / "knowledge" / "topic"
            kd.mkdir(parents=True)
            for name, body in digests.items():
                (kd / name).write_text(body)
            if citing:
                ev = root / "evidence" / "2026-08"
                ev.mkdir(parents=True)
                (ev / "Q-1-answer.md").write_text(citing)
            r = subprocess.run(
                ["python3", str(LINT), "--provenance", "--root", str(root), "--json"],
                capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, "advisory mode must always exit 0")
            return json.loads(r.stdout)

    GOOD = ("# d\n\n> Id: SRC-1\n> Source: knowledge/topic/p.pdf\n"
            "> Received: 2026-08-10 by file drop\n> Status: active\n")

    def rules(self, out):
        return [f["rule"] for f in out["findings"]]

    def test_a_resolvable_citation_is_silent(self):
        out = self._run({"a.md": self.GOOD}, "The claim holds [SRC-1].")
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["sources_defined"], 1)
        self.assertEqual(out["ids_cited"], 1)

    def test_a_dangling_citation_is_reported(self):
        out = self._run({"a.md": self.GOOD}, "Unverified [SRC-9].")
        self.assertIn("citation-dangling", self.rules(out))

    def test_a_digest_with_no_id_cannot_be_cited_and_is_reported(self):
        out = self._run({"a.md": "# d\n\n> Source: x\n> Received: 2026-08-10\n"})
        self.assertIn("source-has-no-id", self.rules(out))

    def test_a_digest_missing_its_fetch_date_is_reported(self):
        out = self._run({"a.md": "# d\n\n> Id: SRC-1\n> Source: x\n> Status: active\n"})
        self.assertIn("source-missing-field", self.rules(out))

    def test_a_reused_id_is_reported(self):
        """Ids are minted once. A recycled id does not dangle — it silently
        re-points an old citation, which is worse than a broken link."""
        dup = self.GOOD.replace("p.pdf", "other.pdf")
        out = self._run({"a.md": self.GOOD, "b.md": dup})
        self.assertIn("source-id-reused", self.rules(out))

    def test_an_empty_scan_is_not_reported_as_a_pass(self):
        out = self._run({})
        self.assertEqual(out["sources_defined"], 0)
        self.assertEqual(out["ids_cited"], 0)
        self.assertEqual(out["findings"], [])


class TestPackGlossary(unittest.TestCase):
    """DESIGN-003 §5.7 — the vocabulary layer, and the line it must not cross.

    "OKR" and "PMO" are the first two nouns a non-product user meets, and both
    say *this tool is not for you* (§1.4 B7). The glossary answers that at
    near-zero structural cost — but only because it renames PROSE. A glossary
    that could rename a column key or an enum value would break every parser,
    so the loader must not even look at them.
    """

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "perry_state",
            importlib.machinery.SourceFileLoader(
                "perry_state", str(PERRY_HOME / "bin" / "perry-state")))
        self.ps = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ps)

    def test_absent_packs_field_defaults_to_software_ops(self):
        """Every pre-DESIGN-003 project effectively ran that pack."""
        packs = self.ps.load_packs(["software-ops"])
        self.assertEqual(packs[0]["name"], "software-ops")
        self.assertTrue(packs[0]["present"])

    def test_a_missing_pack_is_reported_not_crashed_on(self):
        packs = self.ps.load_packs(["no-such-pack"])
        self.assertFalse(packs[0]["present"])
        self.assertEqual(packs[0]["glossary"], {})

    def test_the_glossary_parses_into_term_to_shown_as(self):
        g = self.ps.load_packs(["software-ops"])[0]["glossary"]
        self.assertIn("Commitment", g)
        self.assertEqual(g["Commitment"], "Key result")

    def test_packs_claim_nothing_in_the_users_project(self):
        """packs/ lives in $PERRY_HOME. A pack that claimed a project path
        would reopen DESIGN-002's collision surface for every install."""
        claimed = {c["path"] for c in SCHEMA["claims"]}
        self.assertNotIn("packs/", claimed)

    def test_the_schema_forbids_a_glossary_renaming_the_machine_contract(self):
        inv = SCHEMA["packs"]["invariant"]
        for protected in ("column", "enum", "path"):
            self.assertIn(protected, inv,
                          f"the packs contract does not protect {protected} names")

    def test_packs_is_optional_in_the_config_store(self):
        """`Packs` was a `header_fields` entry with `required: false`, on the
        `files[]` spec ADR-019 removed. A `setting` record carries whatever the
        project declared and nothing else, so optionality is structural: a
        project that declares no pack has no record, and
        `bin/perry-state § parse_config` reads that as `software-ops`."""
        self.assertEqual(STORE_SPEC["records"]["setting"]["required"],
                         ["kind", "key", "value"])
        self.assertNotIn("packs",
                         STORE_SPEC["records"]["setting"]["required"])
        state = load_bin_module("perry-state")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_store.write_config(root)
            self.assertEqual(
                [p["name"] for p in state.parse_config(root)["packs"]],
                ["software-ops"])


class TestEveryModeColumnHasAWriter(unittest.TestCase):
    """A column is not a control until something writes it.

    This is the defect that survived three review rounds in three disguises. The
    schema kept gaining honest homes for data — `Stage`, `Stage since`,
    `Arrived`, `Commitment`, `Parent` — while no procedure ever set them, so
    triage steps that read those cells were uncomputable in practice no matter
    how correct the mode files sounded. The reviewer's phrasing is the test
    name.

    The write path lives in `work/reference/subcommands.md`, because `work` is
    the only lane that may write `BOARD.md`. Checking the prose is crude, but
    the alternative — asserting only that the schema declares the column — is
    exactly the check that passed three times while the bug survived.
    """

    @classmethod
    def setUpClass(cls):
        cls.proc = (PERRY_HOME / "work" / "reference" / "subcommands.md").read_text()

    def test_the_procedure_tells_the_agent_to_set_the_mode_columns(self):
        """**Prose only.** It greps the triage procedure for column names and
        passes whether or not any write sets them — named for what it checks,
        after the V4 review found it standing in for a behavioural test.
        `TestModeColumnsOnBoardsPerryDidNotBuild` is that test.
        """
        self.assertIn("Stage since", self.proc,
                      "nothing in the writing lane ever sets the stage clock")
        self.assertIn("Arrived", self.proc)
        self.assertIn("Parent", self.proc)

    def test_a_stage_move_stamps_the_clock_in_the_same_edit(self):
        """Status and Stage are orthogonal by design, so a draft→review move
        produces no status change and would otherwise leave no trace at all."""
        self.assertRegex(
            self.proc, r"stage move stamps the clock|sets `Stage since` to today",
            "no rule requires a stage change to update its timestamp",
        )

    def test_routing_out_of_intake_carries_the_arrival_date(self):
        """queue.md calls this not-optional; the procedure that actually does
        the routing is what has to agree."""
        step0 = self.proc[self.proc.index("Step 0"):self.proc.index("Then walk")]
        self.assertIn("Arrived", step0,
                      "triage Step 0 routes a row without carrying `Arrived`, "
                      "which is the only clock a queue row is governed by")
        self.assertIn("Stage", step0)

    def test_intake_staleness_is_measured_in_days_not_triages(self):
        """`Arrived` is recorded and nothing counts triages, so elapsed time is
        computable and a triage count is not.

        Asserted positively — that a day-based threshold exists — rather than by
        forbidding the string. The procedure names the rejected formulation in
        order to reject it, and a checker that cannot tell a rule from its
        counter-example is the same defect this suite hit with example IDs."""
        step0 = self.proc[self.proc.index("Step 0"):self.proc.index("Then walk")]
        self.assertRegex(step0, r"more than \d+ days",
                         "intake staleness has no elapsed-time threshold")

    def test_the_work_lane_no_longer_writes_decisions(self):
        """The signed hand-off contract moved the decision record to
        `decide`. The procedure file is where a violation would actually live.

        The check was `assertNotRegex(self.proc, r"^### \\`decide <topic>\\`")`
        **without `re.M`**, so `^` anchored at byte 0 of a 350-line file and
        matched nothing anywhere. A round-4 reviewer proved it by pasting the
        whole ADR procedure back into the middle of the file: the test stayed
        green. A guard anchored to the wrong line is the second of the two
        defect shapes this project keeps finding.
        """
        self.assertNotIn(
            "### `decide <topic>`", self.proc,
            "the ADR procedure is still in the work lane, contradicting the "
            "signed contract")
        self.assertNotIn(
            "`decisions/ADR-NNN-<slug>.md`", self.proc.split("no longer writes")[0],
            "the work lane's procedures still name the ADR file as one they write")
        self.assertIn("moved to the `decide` lane", self.proc)


class TestRouterNamesOnlyRealThings(unittest.TestCase):
    """Every directory and command the router prints must exist.

    Step −2 of the mandatory ritual verifies the install root by listing what
    `$PERRY_HOME` contains. It named three directories that the rename had
    moved — in the one step whose entire job is to confirm the install is sane.
    """

    def test_every_directory_the_router_lists_exists(self):
        m = re.search(r"it also contains ([^)]+)\)", ROUTER := (PERRY_HOME / "SKILL.md").read_text())
        self.assertTrue(m, "step −2 no longer lists what $PERRY_HOME contains")
        for name in re.findall(r"`(\w[\w-]*)/`", m.group(1)):
            self.assertTrue((PERRY_HOME / name).is_dir(),
                            f"router says $PERRY_HOME contains {name}/, which does not exist")

    # A withdrawn command, in every shape the router actually writes one.
    #
    # The first version of this guard matched three literals — "`/okr ",
    # "`/pmo ", "`/design " — backtick, slash, name, trailing space. A round-4
    # reviewer pasted four withdrawn forms into SKILL.md and every one passed:
    # a form with no trailing space (`` `/okr` ``), a form with no leading
    # slash (`` `pmo triage` ``), and any line at all that began with `>` or
    # merely contained the word "shorthand". The no-leading-slash shape was not
    # hypothetical — SKILL.md:677/679/686 already carried `okr score`,
    # `pmo triage`, `design decide` and `pmo dispatch`.
    WITHDRAWN = re.compile(
        # /okr, /pmo, /design in any position — `/perry work` is untouched
        # because the lookbehind rejects a name-char before the slash.
        r"(?<!\w)/(?:okr|pmo|design)\b"
        # `okr score`, `pmo triage`, `design decide` — backticked, no slash.
        r"|`(?:okr|pmo|design)\s+[a-z]"
    )

    # The two lines whose subject IS the withdrawn vocabulary. Named
    # individually rather than by shape: the old guard exempted every
    # blockquote and every line containing the word "shorthand", which is how
    # `> Tip: run `/pmo triage`` would have sailed through.
    CARVE_OUTS = (
        "are written in shorthand",          # SKILL.md § Reading the lane docs
        "Earlier versions symlinked them",   # SKILL.md, why the siblings went
    )

    def test_the_router_does_not_tell_users_to_run_withdrawn_commands(self):
        """`/okr` and `/design` resolve to other people's skills on a host with
        lark-okr or the design: plugin family installed — which is the reason
        the siblings were withdrawn in the first place.

        `SKILL.md:41` scopes the shorthand carve-out to lane SKILL.md files and
        `*/reference/`. It does not exempt the router itself, so this file is
        held to the user-facing vocabulary throughout.
        """
        router = (PERRY_HOME / "SKILL.md").read_text()
        offenders = []
        for n, line in enumerate(router.split("\n"), 1):
            if any(c in line for c in self.CARVE_OUTS):
                continue
            for hit in self.WITHDRAWN.findall(line):
                offenders.append(f"SKILL.md:{n} → {line.strip()[:90]}")
                break
        self.assertEqual(
            offenders, [],
            "the router quotes a withdrawn command back to the user:\n    "
            + "\n    ".join(offenders))


class TestTheHookTemplateIsNotBlind(unittest.TestCase):
    """The shipped safety gate must match the things it says it covers.

    `high_stakes_fragments` extracts only backticked spans. The shipped default
    hook once had two lines — money, and anything sent on the user's behalf —
    written entirely in prose, contributing zero fragments each. A fifth review
    put three deliberately outward-facing closures on a board (a published post,
    an invoice email, a cost-ceiling raise) and `consequence-needs-signoff`
    fired zero times: the gate reported them clean.

    That is the worst failure shape a safety check has, because it is
    indistinguishable from safety. The test is empirical for the same reason —
    asserting that the template *mentions* money would have passed while the
    gate was blind.
    """

    OUTWARD = [
        ("T-1", "Publish launch post"),
        ("T-2", "Email Q3 invoice summary to vendors"),
        ("T-3", "Raise the paid API cost ceiling"),
    ]

    def test_every_high_stakes_line_contributes_at_least_one_fragment(self):
        text = (PERRY_HOME / "work" / "state" / "hook_TEMPLATE.md").read_text()
        body = re.search(r"## High-stakes operations(.*?)^## ", text, re.M | re.S)
        self.assertTrue(body, "the template has no high-stakes section")
        for line in body.group(1).split("\n"):
            if not line.strip().startswith("-") or "{{" in line:
                continue
            self.assertTrue(
                re.findall(r"`([^`]+)`", line),
                f"this line contributes no fragments and the gate is silently "
                f"blind to it: {line.strip()[:70]}",
            )

    def test_the_shipped_hook_actually_catches_outward_facing_closures(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry").mkdir()
            # TASK-237 3b′: `.perry/config.md` was deleted by ADR-019 and a
            # `BOARD.md` alone no longer makes a project installed; the config
            # store declares it, and changes nothing this test reads.
            (root / ".perry" / "config.jsonl").write_text(
                '{"kind": "setting", "key": "state_root", "label": '
                '"State root", "value": ".", "order": 0}\n')
            (root / ".perry" / "hook.md").write_text(
                (PERRY_HOME / "work" / "state" / "hook_TEMPLATE.md").read_text())
            rows = "".join(
                f"| {tid} | {title} | User + Agent | done | — | done 2026-08-16 | V2 |\n"
                for tid, title in self.OUTWARD)
            (root / "BOARD.md").write_text(
                "# Board\n\n## P0\n\n"
                "| ID | Title | Owner | Status | Next action | Evidence | Verification |\n"
                "|---|---|---|---|---|---|---|\n" + rows +
                "\n## P1\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
                "\n## P2\n\n| ID | Title | Owner | Status | Next action | Evidence |\n|---|---|---|---|---|---|\n"
                "\n## Cadence\n\n| ID | Recurring task | Owner | Frequency | Next due | Last evidence |\n|---|---|---|---|---|---|\n"
                "\n## User Input Queue\n\n| USER-id | Needed from user | Blocks | Idle | Status |\n|---|---|---|---|---|\n"
                "\n## Top risks\n\n- none\n")
            import_board(root, "write")       # TASK-262 round 4b, F14
            r = subprocess.run(
                ["python3", str(LINT), "--verification", "--root", str(root), "--json"],
                capture_output=True, text=True)
            out = json.loads(r.stdout)
        hits = " ".join(f["message"] for f in out["findings"]
                        if f["rule"] == "consequence-needs-signoff")
        for tid, title in self.OUTWARD:
            self.assertIn(tid, hits,
                          f"{title!r} closed at V2 and the gate said nothing")


class TestVerificationSeesToolClosedWork(unittest.TestCase):
    """V4 review M-4. The verification ladder was grading an empty set.

    `perry-task done` REMOVES the row it closes, and both readers — the linter
    and `perry-state` — looked only at board rows. On Perry itself: 29 close
    events carrying rungs (28 V3, one V4), and both reported zero. So the whole
    of DESIGN-003 § 5.3, including the rule that anything outward-facing or
    carrying money needs V5 regardless of mode, could never fire on a task the
    tool had closed — which by then was all of them.
    """

    def project(self, rung: str, title: str, hook: str = ""):
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        # Installed the way a start installs a project (TASK-237 round 2).
        config_store.write_config(root)
        if hook:
            (root / ".perry" / "hook.md").write_text(
                f"# hook\n\n## High-stakes operations\n\n- {hook}\n")
        (root / "BOARD.md").write_text(
            "# BOARD\n\n## P0\n| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n\n## P1\n| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n\n## P2\n| ID | Title | Owner | Status | Next action | Evidence |\n"
            "|---|---|---|---|---|---|\n")
        tool = str(PERRY_HOME / "bin" / "perry-task")
        subprocess.run(["python3", tool, "add", "--title", title,
                        "--summary", "A fixture row that exists so the writer has something to write. It carries no meaning beyond that.",
                        "--deliverable", "d", "--verification", "v",
                        "--priority", "P0", "--root", str(root)],
                       capture_output=True, text=True)
        subprocess.run(["python3", tool, "done", "TASK-001",
                        "--evidence", "e.md", "--rung", rung,
                        "--root", str(root)], capture_output=True, text=True)
        return root

    def lint(self, root: Path) -> str:
        return subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-lint"),
             "--verification", "--root", str(root)],
            capture_output=True, text=True).stdout

    def test_a_closed_row_is_counted_after_it_leaves_the_board(self):
        root = self.project("V3", "ordinary work")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(root), "--json"], capture_output=True, text=True)
        v = json.loads(r.stdout)["board"]["verification"]
        self.assertEqual(v["closed"], 1, "a tool-closed task was not counted")
        self.assertEqual(v["by_rung"], {"V3": 1})

    def test_the_consequence_rule_fires_on_tool_closed_work(self):
        """The rule that overrides the mode default in every mode, and which
        could not reach a single tool-closed task."""
        root = self.project("V3", "send the wire transfer", hook="`wire transfer`")
        self.assertIn("consequence-needs-signoff", self.lint(root))

    def test_v5_satisfies_it(self):
        root = self.project("V5", "send the wire transfer", hook="`wire transfer`")
        self.assertNotIn("consequence-needs-signoff", self.lint(root))

    def test_an_evidence_path_is_not_a_consequence(self):
        """The haystack used to include the evidence path, so a hook listing
        `evidence/` under "destructive filesystem operations" matched every
        task that had evidence — all 29 on Perry's own board, the moment this
        check started working. A latent bug that could not fire while the check
        rated nothing."""
        root = self.project("V3", "ordinary work", hook="`evidence/`")
        self.assertNotIn("consequence-needs-signoff", self.lint(root))


if __name__ == "__main__":
    unittest.main()
