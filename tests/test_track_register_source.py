"""`no store` and `store present but unusable` are different answers. TASK-095.

**Written after the V4 round 1 review failed TASK-095 on exactly this.**

`stored_tracks` returned a bare `None` for four different situations, and
`declared_tracks` read the rendered `.perry/config.md § Tracks` in all four.
One of those four is right; three are wrong:

| situation | store on disk | reading the markdown is |
|---|---|---|
| no store | no | **correct** — the adoption path `P003-O2-KR1` excludes |
| unreadable JSONL | **yes** | the condition the KR counts |
| records do not validate | **yes** | the condition the KR counts |
| no `kind: track` record | **yes** | the condition the KR counts |

The reviewer reproduced it with a store holding valid `main` and `intake`
records plus one truncated trailing line — the shape an interrupted write
leaves. `intake` vanished from all four converted call sites at once:
`perry-task --track intake` refused a track the project really declares,
`perry-goals` reported it undeclared, `perry-diagnose` scanned one track, and
`perry-state --json` carried **no signal at all** — the payload looked like an
ordinary single-track project.

**And every one of those branches was untested.** Three mutations inside the
new code came back GREEN against `test_work_modes`, `test_md_store`,
`test_store_drift` and `test_parsers`: `if findings:` → `if False:`,
`return None` → `raise`, and `return None` → `return []`. No test called
`stored_tracks` or `declared_tracks` directly. That is review finding 6, and it
is why this module asserts the source of the answer and not only the answer.

**The three callers do three different things, deliberately.**
`perry-state` falls back and WARNS — it is the read-everything tool and must
exit 0 on a project with no state at all, so it may not turn a corrupt store
into a crash; what it may not do is stay silent. `perry-task` and `perry-goals`
REFUSE on a write: they stamp `Track`, `Stage` and `Arrived` off this register
and write `phase/`, and a row written against a register missing a track is not
recoverable by re-running the command. `perry-task` still lets READS through,
because refusing `list` would make a corrupt store un-diagnosable with the tool
the user has in their hand.

Run: python3 tests/parallel test_track_register_source
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from gate import GATE_OFF   # tests/gate.py — why this fixture opts out

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

STATE = ROOT / "bin" / "perry-state"
TASK = ROOT / "bin" / "perry-task"
GOALS = ROOT / "bin" / "perry-goals"
DIAGNOSE = ROOT / "bin" / "perry-diagnose"


def _state_module():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("perry_state_mod", str(STATE))
    spec = importlib.util.spec_from_loader("perry_state_mod", loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PS = _state_module()

#: `GATE_OFF` is appended rather than spelled out: `tests/gate.py` exists so
#: that renaming the `Conformance gate` matcher reddens every fixture using it
#: at once, and a fixture that inlines the line opts itself out of that.
CONFIG_MD = ("""# Perry configuration

- Document language: English
- Repo layout: single
- State root: .
""" + GATE_OFF + """
## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| main | project | phase/ | — | — | — | — | V3 |
""")

BOARD = (
    "# Board — track source fixture\n\n> Last updated: 2026-08-29\n\n"
    "## P0 (must finish this period)\n\n"
    "| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n\n"
    "## P1\n\n| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n\n"
    "## P2\n\n| ID | Title | Owner | Status | Next action | Evidence |\n"
    "|---|---|---|---|---|---|\n"
)


def track_record(name: str, mode: str, order: int) -> str:
    return json.dumps({
        "kind": "track", "track": name, "mode": mode, "spine": "phase/",
        "stages": "", "wip": "", "sla": "", "cycle": "",
        "default_rung": "V3", "order": order,
    }, ensure_ascii=False)


#: A store holding BOTH tracks. `.perry/config.md` above declares only `main`,
#: so any test whose answer contains `intake` read the store and any test whose
#: answer does not read the projection. The divergence IS the instrument.
GOOD_STORE = track_record("main", "project", 0) + "\n" \
    + track_record("intake", "queue", 1) + "\n"


class Fixture(unittest.TestCase):

    def project(self, store: str | None) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-track-source-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text(CONFIG_MD)
        (d / "BOARD.md").write_text(BOARD)
        # `perry-goals commit` refuses before it reaches the track register
        # without one, and a refusal for the wrong reason is a test that passes
        # while measuring nothing — the trap this whole module was written
        # after.
        shutil.copy(ROOT / "tests" / "fixtures" / "sample-project" / "OKR.md",
                    d / "OKR.md")
        if store is not None:
            (d / ".perry" / "config.jsonl").write_text(store)
        return d

    def detail(self, d: pathlib.Path):
        return PS.declared_tracks_detail(d)

    def names(self, d: pathlib.Path) -> list[str]:
        return [t["track"] for t in self.detail(d)[0]]


class TestTheInstrumentWorks(Fixture):
    """The control: the store and the projection must actually disagree.

    Without this, every assertion below could pass on two identical answers
    and the module would be measuring nothing.
    """

    def test_the_store_and_the_markdown_declare_different_tracks(self):
        self.assertEqual(self.names(self.project(GOOD_STORE)),
                         ["main", "intake"])
        self.assertEqual(self.names(self.project(None)), ["main"])


class TestTheFourSituationsAreDistinguished(Fixture):
    """One assertion per branch. All three unusable ones were untested."""

    def test_a_healthy_store_reports_store(self):
        self.assertEqual(self.detail(self.project(GOOD_STORE))[1],
                         PS.TRACKS_FROM_STORE)

    def test_no_store_reports_absent_and_is_NOT_unusable(self):
        """The adoption path. Reading the markdown here is correct."""
        source = self.detail(self.project(None))[1]
        self.assertEqual(source, PS.TRACKS_STORE_ABSENT)
        self.assertNotIn(source, PS.TRACKS_STORE_UNUSABLE)

    def test_a_truncated_line_reports_unreadable(self):
        """The reviewer's exact fixture: two valid records, one torn line."""
        d = self.project(GOOD_STORE + '{"kind": "track", "track": "hal')
        tracks, source = self.detail(d)
        self.assertEqual(source, PS.TRACKS_STORE_UNREADABLE)
        self.assertEqual([t["track"] for t in tracks], ["main"],
                         "the fallback answer is the projection's — which is "
                         "the whole hazard this source string exists to flag")

    def test_a_record_that_parses_but_does_not_validate_reports_invalid(self):
        """**A separate branch from `unreadable`, and it needs a separate
        fixture to reach.**

        Written after the first draft of this module left the `if findings:`
        mutation GREEN while the other two went red. A torn line makes
        `load_store` RAISE, so it exits through `unreadable` and never reaches
        the validation branch — a fixture that accepted "unreadable or invalid"
        was therefore testing one branch and reporting two. The store here is
        well-formed JSONL whose `mode` is a list, which validates and fails.
        """
        bad = json.dumps({"kind": "track", "track": "intake",
                          "mode": [], "order": 1})
        d = self.project(track_record("main", "project", 0) + "\n" + bad + "\n")
        tracks, source = self.detail(d)
        self.assertEqual(source, PS.TRACKS_STORE_INVALID)
        self.assertEqual([t["track"] for t in tracks], ["main"])

    def test_an_empty_store_is_unusable_but_a_settings_only_store_is_not(self):
        """The distinction the round 2 review drew, asserted as a pair.

        A file that parsed to ZERO records has answered nothing — an
        interrupted write produces one and `perry-config write --from-file`
        never does. A store carrying settings and no track record HAS answered:
        DESIGN-003 says that means one implicit `main`. Collapsing the two is
        the same class of error as round 1's, one level down.
        """
        self.assertIn(self.detail(self.project(""))[1],
                      PS.TRACKS_STORE_UNUSABLE)
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        self.assertEqual(self.detail(self.project(setting + "\n"))[1],
                         PS.TRACKS_FROM_STORE)

    def test_a_store_with_no_track_record_HAS_ANSWERED(self):
        """**The round 2 regression, asserted in the direction that failed.**

        A store that validates and carries no `kind: track` record is not
        broken. `schema/state-schema.json § work_modes.note` (DESIGN-003,
        locked 2026-08-16) defines the state: *"Absent a Tracks section there
        is one implicit track named `main`, mode `project`"*, and marks the
        section *"OPTIONAL … which is what keeps every pre-DESIGN-003 project
        valid."*

        Round 2 filed it under `TRACKS_STORE_UNUSABLE` and hung a permanent
        write refusal off that bucket. Three of this repo's six `config.md`
        files have no `## Tracks` section, so on each of them
        `perry-config write --from-file` produced a settings-only store and
        every subsequent write was refused — pointing the user at two commands
        that report the store as `drift_count: 0, byte_identical: true`.
        """
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        tracks, source = self.detail(self.project(setting + "\n"))
        self.assertEqual(source, PS.TRACKS_FROM_STORE)
        self.assertNotIn(source, PS.TRACKS_STORE_UNUSABLE)
        self.assertEqual([t["track"] for t in tracks], ["main"],
                         "DESIGN-003 specifies one implicit `main`")

    def test_the_register_is_never_empty(self):
        """`declared_tracks`' documented invariant, which nothing asserted.

        Round 2's review found that returning `[]` with a truthful source label
        was green across 2811 tests, so the docstring's *"Never empty, for the
        reason `parse_tracks` is never empty: the router has no 'no tracks
        declared' branch"* was a claim with no guard under it.
        """
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        for store in (None, "", GOOD_STORE, setting + "\n",
                      GOOD_STORE + '{"kind": "track", "track": "hal'):
            with self.subTest(repr((store or "")[:24])):
                self.assertTrue(self.detail(self.project(store))[0],
                                "the router has no empty-register branch")

    def test_every_unusable_source_has_a_sentence_for_a_human(self):
        """One wording, so three callers cannot describe one state three ways."""
        for source in PS.TRACKS_STORE_UNUSABLE:
            self.assertIn(source, PS.TRACKS_STORE_WHY)
            self.assertIn("config.jsonl", PS.TRACKS_STORE_WHY[source])


class TestThePayloadSaysWhichAnswerItGave(Fixture):
    """`perry-state` falls back — and no longer does it silently."""

    def payload(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return json.loads(proc.stdout)

    def test_a_healthy_store_warns_about_nothing(self):
        pay = self.payload(self.project(GOOD_STORE))
        self.assertEqual(pay["project"]["config"]["tracks_source"], "store")
        self.assertEqual(
            [w for w in pay["warnings"] if "track register" in w], [])

    def test_no_store_warns_about_nothing_either(self):
        """`absent` is legitimate. A warning here would cry wolf on every
        project that has not migrated — which is every foreign project."""
        pay = self.payload(self.project(None))
        self.assertEqual(pay["project"]["config"]["tracks_source"], "absent")
        self.assertEqual(
            [w for w in pay["warnings"] if "track register" in w], [])

    def test_an_unusable_store_puts_a_warning_in_the_payload(self):
        """The signal the review found missing, asserted where it was missing."""
        pay = self.payload(
            self.project(GOOD_STORE + '{"kind": "track", "track": "hal'))
        self.assertIn(pay["project"]["config"]["tracks_source"],
                      PS.TRACKS_STORE_UNUSABLE)
        hits = [w for w in pay["warnings"] if "track register" in w]
        self.assertTrue(hits, "the payload fell back to the projection and "
                              "said nothing — the round 1 FAIL")
        self.assertIn("config.md", hits[0])

    def test_perry_state_still_exits_zero_on_a_corrupt_store(self):
        """It may warn; it may not become the thing that crashes.

        `perry-state` is the read-everything tool and exits 0 on a project with
        no state at all. A corrupt store must not be the one input that makes
        the dashboard unreadable.
        """
        proc = subprocess.run(
            [sys.executable, str(STATE), "--root",
             str(self.project(GOOD_STORE + '{"kind": "trac')), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestAWriterRefusesRatherThanFallingBack(Fixture):
    """The other half of the fix, and the reason it is not one rule for all.

    A read may degrade with a warning. A write may not: `Track`, `Stage` and
    `Arrived` are stamped off this register, and a row written against a
    register missing a track is not fixed by re-running the command.
    """

    def run_task(self, d: pathlib.Path, *argv):
        return subprocess.run(
            [sys.executable, str(TASK), *argv, "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)

    def test_a_write_is_refused_when_the_store_is_present_and_unusable(self):
        d = self.project(GOOD_STORE + '{"kind": "track", "track": "hal')
        out = self.run_task(d, "intake", "--title", "a request")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("track register", (out.stdout + out.stderr))
        self.assertFalse((d / "intake.jsonl").exists(),
                         "the refusal must mean NOTHING was written")

    def test_a_read_is_still_allowed_through(self):
        """Refusing `list` would make a corrupt store un-diagnosable with the
        tool the user already has open."""
        d = self.project(GOOD_STORE + '{"kind": "track", "track": "hal')
        self.assertEqual(self.run_task(d, "list", "--json").returncode, 0)

    def test_a_write_is_fine_with_no_store_at_all(self):
        """`absent` is the adoption path and must not be swept into the
        refusal — every project that has not migrated writes through here."""
        out = self.run_task(self.project(None), "intake", "--title", "a request")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_a_write_is_fine_with_a_healthy_store(self):
        out = self.run_task(self.project(GOOD_STORE), "intake",
                            "--title", "a request")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_a_write_is_fine_with_a_trackless_store(self):
        """The round 2 regression at the write path, where it actually bit."""
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        out = self.run_task(self.project(setting + "\n"), "intake",
                            "--title", "a request")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


class TestTheGoalsLaneRefusesToo(Fixture):
    """**The guard round 2 shipped with no test at all.**

    Its review deleted `bin/perry-goals`' eight-line refusal and the full
    2811-test suite stayed green: the module exercised `perry-state` and
    `perry-task` and never invoked `perry-goals`, while the commit message
    claimed it covered "both callers". That is round 1's finding 6 reproduced
    inside round 2's own fix, which is why this class exists.
    """

    def run_goals(self, d: pathlib.Path, *argv):
        return subprocess.run(
            [sys.executable, str(GOALS), *argv, "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)

    #: `list` does not read the track register; `commit` does (bin/perry-goals
    #: :3120). Using a command that never reaches `tracks_of` would make this
    #: whole class green on a deleted guard, which is the failure it exists for.
    REACHES_REGISTER = ("commit", "--track", "main", "--promise", "p",
                        "--to", "someone", "--due", "2026-09-30")

    def test_goals_refuses_when_the_store_is_present_and_unusable(self):
        d = self.project(GOOD_STORE + '{"kind": "track", "track": "hal')
        out = self.run_goals(d, *self.REACHES_REGISTER)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("track register", out.stdout + out.stderr)

    def test_goals_is_fine_with_no_store(self):
        """`absent` is the adoption path and must never reach the refusal."""
        out = self.run_goals(self.project(None), *self.REACHES_REGISTER)
        self.assertNotIn("track register", out.stdout + out.stderr)

    def test_goals_is_fine_with_a_trackless_store(self):
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        out = self.run_goals(self.project(setting + "\n"),
                             *self.REACHES_REGISTER)
        self.assertNotIn("track register", out.stdout + out.stderr)


class TestDiagnoseSaysWhichRegisterItRead(Fixture):
    """The FOURTH call site, which round 2's own design note never mentioned.

    Its review measured this reporting `tracks: ['main']` on a store declaring
    `main` AND `intake`, with `register_declared: True` and empty stderr —
    round 1's finding 1, unchanged, at the site nobody counted.
    """

    def work_modes(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(DIAGNOSE), "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[:400])
        return json.loads(proc.stdout).get("work_modes", {})

    def test_it_labels_a_healthy_store(self):
        self.assertEqual(self.work_modes(self.project(GOOD_STORE))
                         .get("tracks_source"), "store")

    def test_it_labels_the_projection_fallback(self):
        wm = self.work_modes(
            self.project(GOOD_STORE + '{"kind": "track", "track": "hal'))
        self.assertIn(wm.get("tracks_source"), PS.TRACKS_STORE_UNUSABLE,
                      "diagnose read the projection and did not say so")


if __name__ == "__main__":
    unittest.main()
