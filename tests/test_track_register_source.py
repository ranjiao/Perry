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

**Everything below that compared the store to `## Tracks` is gone with
ADR-019**, which deleted `.perry/config.md`. This module's instrument was a
fixture whose table declared `main` while its store declared `main` AND
`intake`, so that "which register did you read" had an observable answer. With
one register the question is unaskable, and the three predicates built on it —
`tracks_the_projection_declares`, `tracks_the_register_contradicts`,
`tracks_the_register_cannot_place` — raise rather than answer.

What survives is the half TASK-095 was actually failed for and which has
nothing to do with the projection: **`no store` and `store present but
unusable` are still different answers**, the four sources are still
distinguished, `perry-state` still warns and exits 0, and `perry-task` and
`perry-goals` still refuse a write against a register they could not read. The
consequence of getting that wrong is worse now, not better: the fallback used
to be the table's rows and is now DESIGN-003's implicit `main`, so a store
silently missing `intake` no longer even leaves a second copy to notice.

Run: python3 tests/parallel test_track_register_source
"""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-config",
    "bin/perry-state",
    "bin/perry-diagnose",
    "bin/perry-goals",
    "bin/perry-lint",
    "bin/perry-task",
    "viewer/parsers.py",
    "schema/state-schema.json",
)

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

STATE = ROOT / "bin" / "perry-state"
TASK = ROOT / "bin" / "perry-task"
GOALS = ROOT / "bin" / "perry-goals"
DIAGNOSE = ROOT / "bin" / "perry-diagnose"
CONFIG = ROOT / "bin" / "perry-config"
LINT = ROOT / "bin" / "perry-lint"


def _state_module():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("perry_state_mod", str(STATE))
    spec = importlib.util.spec_from_loader("perry_state_mod", loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PS = _state_module()

#: A pre-ADR-019 `.perry/config.md`, for the one test that asserts a leftover
#: copy is inert. It declares a track no store in this module holds, so a
#: reader that fell back to it would be caught by the NAME and not merely by a
#: count — `fromthemarkdown` can only have come from here.
STRAY_CONFIG_MD = """# Perry configuration

- Document language: English
- Repo layout: single
- State root: .

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| fromthemarkdown | queue | standing | new→done | 6 | 5d | weekly | V3 |
"""

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


#: A store holding BOTH tracks. `intake` in an answer is proof the register
#: was READ; DESIGN-003's implicit `main` is what every non-answer produces, so
#: a test probing `main` alone cannot tell the two apart and every probe here
#: is `intake`.
#: The `conformance_gate` record rides along on every hand-built store here for
#: the reason `tests/gate.py § gate_off_record` states: `gate_mode` reads
#: `.perry/config.jsonl` first (TASK-233), so a store that omits the setting is
#: a project declaring no gate — which would make every write below refuse for
#: an ADR-004 reason that has nothing to do with the track register, the exact
#: trap this module was written after.
GOOD_STORE = track_record("main", "project", 0) + "\n" \
    + track_record("intake", "queue", 1) + "\n" + ""


class Fixture(unittest.TestCase):

    def project(self, store: str | None, *,
                stray_markdown: bool = False) -> pathlib.Path:
        """A project whose register is `store`, or which has none.

        **The `.perry/config.md` half of this fixture is gone** (ADR-019). It
        wrote a `## Tracks` table declaring only `main` while `GOOD_STORE`
        declares `main` AND `intake`, and that divergence was the instrument
        every "did it read the store or the projection" assertion rested on.
        There is one register, so the parameters that shaped the table
        (`md_declares`, `md_declares_two`) are gone with the tests that used
        them rather than left as flags that change nothing.

        `stray_markdown=True` writes one anyway — a pre-ADR-019 config
        declaring a track called `fromthemarkdown`, left in a working tree the
        way a real one would be. Exactly one test uses it, and what it asserts
        is that the file is inert. A leftover copy is the state a user actually
        arrives in after pulling this change, and "nothing reads it" is a claim
        worth one test rather than none.
        """
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-track-source-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        if stray_markdown:
            (d / ".perry" / "config.md").write_text(STRAY_CONFIG_MD)
        (d / "BOARD.md").write_text(BOARD)
        # `perry-goals commit` refuses before it reaches the track register
        # without one, and a refusal for the wrong reason is a test that passes
        # while measuring nothing — the trap this whole module was written
        # after.
        shutil.copy(ROOT / "tests" / "fixtures" / "sample-project" / "OKR.md",
                    d / "OKR.md")
        if store is not None:
            (d / ".perry" / "config.jsonl").write_text(store)
        else:
            # TASK-237 3b′: with no config store, `BOARD.md` and `OKR.md`
            # alone no longer make a project installed, and `perry-state`
            # would answer its no-state payload with no `project.config` to
            # read. An empty risk store is a canonical store that declares no
            # track, so the register stays `absent` — the case under test.
            (d / "risks.jsonl").write_text("")
        return d

    def detail(self, d: pathlib.Path):
        return PS.declared_tracks_detail(d)

    def names(self, d: pathlib.Path) -> list[str]:
        return [t["track"] for t in self.detail(d)[0]]


# `TestTheInstrumentWorks` was the control: it asserted that the store
# and the table really did declare different tracks, so that every
# assertion resting on the divergence was resting on something. There is
# no table to diverge from.


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

    def test_an_empty_store_answers_like_a_settings_only_store(self):
        """**Reversed by TASK-270, on the refusal's own reason.**

        This asserted the pair the other way — empty unusable, settings-only
        usable — on two premises: that an interrupted write produces an empty
        store, and that `perry-config write --from-file` never does. The
        importer is gone (ADR-019); `lib.write_atomic` renames, so a write is
        never torn to zero bytes; and `perry-config unset` of the last setting
        produces one at exit 0. The writers refuse a store that may hide a
        declaration, and an empty store that parsed and validated hides none,
        exactly like a settings-only one. `tests/test_empty_config_store.py`
        holds the rest; the invalid and unreadable branches above are unchanged.
        """
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        for store in ("", setting + "\n"):
            with self.subTest(store=store):
                source = self.detail(self.project(store))[1]
                self.assertEqual(source, PS.TRACKS_STORE_DEFAULT)
                self.assertNotIn(source, PS.TRACKS_STORE_UNUSABLE)

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
        tracks, source = self.detail(
            self.project(setting + "\n"))
        self.assertEqual(source, PS.TRACKS_STORE_DEFAULT,
                         "round 4: the answer came from DEFAULT_TRACK, not "
                         "from a record, and the label must say so")
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

    def test_a_leftover_config_md_is_inert(self):
        """The state a user is in after pulling ADR-019 with a dirty tree.

        `STRAY_CONFIG_MD` declares `fromthemarkdown` and no store here holds
        it, so a reader that fell back would be caught by the name. Asserted
        against BOTH a healthy store and no store at all: the second is where
        the old fallback actually lived, and a test that only covered the first
        would pass on a reader that still read the file when it had nothing
        else to read.
        """
        for label, store in (("a healthy store", GOOD_STORE),
                             ("no store at all", None)):
            with self.subTest(label):
                d = self.project(store, stray_markdown=True)
                self.assertNotIn("fromthemarkdown", self.names(d))

    def test_every_unusable_source_has_a_sentence_for_a_human(self):
        """One wording, so three callers cannot describe one state three ways."""
        for source in PS.TRACKS_STORE_UNUSABLE:
            self.assertIn(source, PS.TRACKS_STORE_WHY)
            self.assertIn("config.jsonl", PS.TRACKS_STORE_WHY[source])


#: A store that validates, carries a setting and declares no track. The
#: `conformance_gate` record rides along for the reason `GOOD_STORE`'s does —
#: without it every write against this fixture refuses on ADR-004 instead of
#: reaching the track register, which is a green `assertNotEqual(rc, 0)`
#: measuring nothing.
SETTING_ONLY = json.dumps({"kind": "setting", "key": "language",
                           "value": "English", "order": 0}) + "\n" \
    + ""

# `DECLARING_MAIN` and `DECLARING_MAIN_ZH` stood here: a `## Tracks` row with
# every cell filled, and the same table localized. The first was the
# instrument for round 5's FAIL — the gap between "a record named `main`" and
# "a record that says what the table says" — and the second proved the
# comparison read one register one way rather than an English path and a
# Chinese one. Both are gone with the table (ADR-019). The localization
# property they stood for is now structural rather than checked: a track's
# fields are ASCII keys, so there is no Chinese path for the register to have.


class TestAStoreThatDeclaresNoTrackIsTwoSituations(Fixture):
    """**Round 3's FAIL, and the third `two situations, one answer` in a row.**

    Round 1 collapsed four `None`s into one. Round 2 collapsed `no-track-record`
    into "unusable" and hard-blocked three of this repo's own fixtures. Round 3
    split that out and then collapsed the two `store-default` situations:

    - the store declares no track and `## Tracks` declares none either — a
      COMPLETE answer, DESIGN-003's implicit `main`, and silence is correct;
    - the store declares no track while `## Tracks` declares `main` AND
      `intake` — **drift**, which `perry-lint` reports as `config-store-drift`.

    Round 3 answered both with `[main]`, `source: "store"`, no warning, and an
    allowed write. On the second it lost a declared track and its 5d SLA from
    the dashboard, from `sla_report`, from `wip_report` and from `--track`
    validation, and then refused `add --track intake` with a message pointing
    at the very table that declares it. That was **worse than `45a355d`**,
    which returned both tracks, **and worse than round 2**, which refused
    loudly.

    `source` is `store-default` now, not `store` — the list comes from a
    constant in `bin/perry-state`, and labelling that `store` asserted a
    provenance the answer did not have. The label was load-bearing: the payload
    warning and both writers' refusals are keyed on it.
    """

    def test_a_complete_default_is_labelled_store_default(self):
        tracks, source = self.detail(
            self.project(SETTING_ONLY))
        self.assertEqual(source, PS.TRACKS_STORE_DEFAULT)
        self.assertEqual([t["track"] for t in tracks], ["main"])
        self.assertNotIn(source, PS.TRACKS_STORE_UNUSABLE)

    def test_it_is_not_labelled_store_because_no_record_answered(self):
        """`store` would assert a provenance the answer does not have."""
        self.assertNotEqual(
            self.detail(self.project(SETTING_ONLY))[1],
            PS.TRACKS_FROM_STORE)

    DEFAULTED = [dict(PS.DEFAULT_TRACK)]

    def test_a_complete_default_loses_nothing(self):
        """**The trackless case, named.** A store with no track record
        declares nothing, so nothing is lost by answering `main`. Three of
        this repo's six configs were this shape and round 2 hard-blocked every
        one of them; the half of this test that asked what a `## Tracks` table
        declared instead is gone with the table."""
        d = self.project(SETTING_ONLY)
        self.assertEqual(self.detail(d)[1], PS.TRACKS_STORE_DEFAULT)
        self.assertEqual(self.detail(d)[0], self.DEFAULTED)

    # `test_a_table_that_DECLARES_main_is_not_a_complete_default` and
    # `test_it_names_every_declared_track_the_register_lacks` stood here.
    # Both asked what a `## Tracks` table declares that the store does not.

    #: Each retired name with the arity ITS OWN callers used, so the
    #: `TypeError` comes from the body and not from Python counting arguments
    #: — an assertion satisfied by a wrong call is an assertion about nothing.
    RETIRED_CALLS = {
        "defaulted_over_a_declaring_table": lambda fn, d, rows:
            fn(d, PS.TRACKS_STORE_DEFAULT),
        "tracks_missing_from_the_register": lambda fn, d, rows:
            fn(d, rows, PS.TRACKS_STORE_DEFAULT),
        # The three ADR-019 retired. They are here rather than merely deleted
        # for the reason the two above are: `bin/perry-task`,
        # `bin/perry-goals`, `bin/perry-diagnose` and `bin/perry-state § build`
        # all called them, and a stale caller must get a sentence explaining
        # that the comparison has no second side rather than an empty list
        # that reads as "no drift".
        "tracks_the_projection_declares": lambda fn, d, rows: fn(d),
        "tracks_the_register_contradicts": lambda fn, d, rows:
            fn(d, PS.TRACKS_STORE_DEFAULT),
        "tracks_the_register_cannot_place": lambda fn, d, rows:
            fn(d, rows, PS.TRACKS_STORE_DEFAULT),
    }

    def test_the_retired_names_raise_rather_than_answering_narrowly(self):
        """Every retired spelling — round 4's, round 5's, and the three
        ADR-019 removed. A caller reaching for one is asking a question that
        was either split in two or has lost its second side entirely, and a
        silently narrower answer under an old name is the shape this row keeps
        being failed for."""
        self.assertEqual(sorted(PS._RETIRED_TRACK_PREDICATES),
                         sorted(self.RETIRED_CALLS))
        d = self.project(SETTING_ONLY)
        for name, call in sorted(self.RETIRED_CALLS.items()):
            with self.subTest(name):
                with self.assertRaises(TypeError):
                    call(getattr(PS, name), d, self.DEFAULTED)


# `TestOneTableTwoStoresOneVerdict` held USER-905's principle A — one
# table over two stores differing only in whether a `main` record exists
# must get ONE verdict from the linter, the writer, the payload and the
# goals lane. All four verdicts were about drift between the table and
# the store, and `perry-lint`'s `config-store-drift` is gone with them.


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
        self.assertTrue(hits, "the payload answered from somewhere and said "
                              "nothing — the round 1 FAIL")
        # It names the register it could not read, and says what the payload
        # carries instead. Before ADR-019 that was the projection's rows; it
        # is DESIGN-003's implicit `main` now, which is a WORSE thing to be
        # silent about — there is no second copy left to notice.
        self.assertIn(".perry/config.jsonl", hits[0])
        self.assertIn("implicit `main`", hits[0])

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
            task_actor.command([sys.executable, str(TASK), *argv, "--root", str(d)], 'test_track_register_source'),
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
        """The round 2 regression at the write path, where it actually bit.

        **A trackless store, and the round 4 review failed this row because
        it was not.** The round 2 regression bit on projects with NO
        `## Tracks` section; this guard was built with the fixture default,
        which WRITES a table declaring `main`, so it asserted an allowed write
        on a project whose table declares a track the register does not carry —
        pinning the very defect that round caused, under a docstring naming a
        different one.
        """
        out = self.run_task(
            self.project(SETTING_ONLY),
            "intake", "--title", "a request")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


# `TestAWriteAgainstADefaultedRegisterIsRefused` pinned USER-905
# decision 2: a write is refused when the store answered by DEFAULT while
# the table declared tracks it has no record for. That is
# `tracks_the_register_cannot_place`, whose other side was the table. A
# store-default answer is now simply the answer.


# `TestTheThreeHandEditWorkflowsStillWrite` measured the three
# hand-edit workflows round 5's wider refusal blocked: add a `## Tracks`
# section, add a row to it, swap a row. All three are edits to a file
# that no longer exists; the equivalent today is `perry-config track`,
# which writes the register directly and cannot leave it disagreeing with
# anything.


class TestABlankTrackNameIsNotSilentlyADefault(Fixture):
    """The gap round 3's reviewer found unguarded.

    `stored_tracks` filters on `(r.get("track") or "").strip()`. A store
    carrying one `kind: track` record whose name is blank validates, survives
    validation, leaves `rows` empty, and lands on the default branch — the
    store HAS a track record and the code reports it as a store with none.

    Not reachable through the importer (a `## Tracks` row with an empty first
    cell is dropped), so it is a hand-edit or partial-write shape. It was
    GREEN: dropping the filter entirely passed all 23 tests.
    """

    BLANK = json.dumps({"kind": "track", "track": "", "mode": "project",
                        "order": 0}) + "\n"

    def test_the_filter_is_load_bearing(self):
        """With the filter, a blank-named record is not a track and the answer
        defaults. Without it, the record would be treated as a real track with
        an empty name, and every consumer keyed on the name would see `''`."""
        tracks, source = self.detail(self.project(self.BLANK))
        self.assertEqual(source, PS.TRACKS_STORE_DEFAULT)
        self.assertEqual([t["track"] for t in tracks], ["main"])
        self.assertNotIn("", [t["track"] for t in tracks],
                         "a blank-named record became a track")


# `TestWhatTheProjectionDeclares` was the unit test for
# `tracks_the_projection_declares` — which names the tracks `## Tracks`
# declares. It has no subject and the function raises.


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
        """A trackless store — see the note on the `perry-task` twin."""
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        out = self.run_goals(
            self.project(setting + "\n"),
            *self.REACHES_REGISTER)
        self.assertNotIn("track register", out.stdout + out.stderr)

    # `test_goals_refuses_when_a_declared_track_has_no_row_at_all` was
    # the goals lane's half of the same refusal, over the same table.

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

    # `test_it_labels_the_projection_fallback`,
    # `test_a_label_with_no_drift_signal_was_the_silent_one` and
    # `test_it_reports_the_contradicted_declaration_too` stood here. The
    # first labelled a fallback that no longer exists; the other two were
    # `MODE-02`, the diagnose finding for a table and a store disagreeing.

    def payload(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(DIAGNOSE), "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[:400])
        return json.loads(proc.stdout)

    # `test_an_agreeing_register_gets_no_finding` stood here: the other
    # direction of `MODE-02`, so the finding was not decorative. Gone with
    # the finding.

def _lint_module():
    """`bin/perry-lint` as a module — same loader, same reason, as `PS`."""
    import importlib.machinery
    import importlib.util
    sys.path.insert(0, str(ROOT / "viewer"))
    loader = importlib.machinery.SourceFileLoader("perry_lint_mod", str(LINT))
    spec = importlib.util.spec_from_loader("perry_lint_mod", loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PL = _lint_module()


class TestLintTypesACellAgainstTheRegister(Fixture):
    """`perry-lint § _track_context` asks the STORE. TASK-283.

    **The fifth site, and the one `P003-O2-KR1`'s baseline never counted.**
    That baseline enumerated four `parse_tracks` call sites and fixed them.
    `_track_context` does not call `parse_tracks` — it carried an inline
    parser of `.perry/config.md § Tracks` all its own — so it never answered
    to the name the count was taken over, and the KR read 0 while a register
    reader sat in `bin/perry-lint`.

    TASK-247 fixed the WALK above it (`P.configured`, so the root of a
    store-only project resolves to that project instead of to an ancestor
    holding some other repository's `.perry/`) and named this read as still
    outstanding rather than folding it in. This class is that read.

    **Why `{}` was never a safe wrong answer.** `_track_context` feeds
    `lib.classify_due`, and `{}` there means mode `project` with no clock —
    the most PERMISSIVE contract there is. So on a store-only project a
    `pipeline` track accepted the duration tokens it exists to reject and a
    `queue` track with no declared clock accepted a populated `Due`. The
    column did not report a wrong answer; it stopped asking the question,
    which is the one failure a linter cannot show you.
    """

    #: The track `GOOD_STORE` declares and `DEFAULT_TRACK` does not, so
    #: resolving it is proof the register was read rather than defaulted. It
    #: used to be proof of something narrower — that the STORE was read and not
    #: the table beside it — and the probe is unchanged because the thing it
    #: has to tell apart is still a real answer from a fallback.
    RESOLVED_FROM_THE_STORE = "intake"

    def setUp(self):
        # Module-level cache, and these fixtures are fresh directories each
        # time. Left dirty, the first test's answer would be served to the
        # rest and a broken read would still look right.
        PL._TRACK_CONTEXTS.clear()

    def store_only(self, store: str = GOOD_STORE) -> pathlib.Path:
        """A project configured by `.perry/config.jsonl` ALONE.

        The shape a clone made before `perry-config render --write` has, and
        the shape `project()` cannot produce — it always writes the
        projection, because the twenty tests above measure divergence between
        the two files and need both.
        """
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-track-storeonly-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        (d / ".perry" / "config.jsonl").write_text(store)
        (d / "BOARD.md").write_text(BOARD)
        self.assertFalse((d / ".perry" / "config.md").exists(),
                         "the fixture is only worth running store-only")
        return d

    def context(self, d: pathlib.Path, name: str) -> dict:
        return PL._track_context(d / "BOARD.md", name)

    # ── the defect ────────────────────────────────────────────────────────

    def test_a_store_only_project_resolves_a_track_it_declares(self):
        """**The before-state, stated as the assertion that catches it.**

        Before TASK-283 every name here came back `{}` — including `main`,
        which every store declares — because the read was of a
        `.perry/config.md` that is not on disk.
        """
        d = self.store_only()
        got = self.context(d, self.RESOLVED_FROM_THE_STORE)
        self.assertTrue(got, "the store declares this track and it resolved "
                             "to `{}` — the register was not read")
        self.assertEqual(got.get("track"), self.RESOLVED_FROM_THE_STORE)
        self.assertEqual(got.get("mode"), "queue",
                         "the MODE is the half `lib.classify_due` types a "
                         "`Due` cell against; a name with no mode is not a "
                         "resolved track")

    # `test_it_reads_the_store_and_not_the_projection_when_BOTH_exist`
    # and `test_no_store_at_all_still_reads_the_projection` stood here: the
    # linter's typed-cell check resolving a track against one register while
    # the other said otherwise. `test_a_store_only_project_resolves_a_track
    # _it_declares` above is what is left, and it is now the ordinary case
    # rather than the interesting one.

    # ── the controls ──────────────────────────────────────────────────────

    def test_a_genuinely_undeclared_track_is_still_permissive(self):
        """A fix that resolves EVERYTHING passes the two above and is wrong.

        `{}` is the documented permissive case and the reason a typo in the
        register does not silently make a column stricter.
        """
        for label, d in (("store only", self.store_only()),
                        ("good store", self.project(GOOD_STORE))):
            with self.subTest(label):
                PL._TRACK_CONTEXTS.clear()
                self.assertEqual(self.context(d, "no-such-track"), {})

    def test_an_unusable_store_does_not_hand_back_the_projections_row(self):
        """**The `TRACKS_STORE_UNUSABLE` half, which is the whole point.**

        `declared_tracks_detail` still ANSWERS when a store is present and
        could not be read — with DESIGN-003's implicit `main` and a `source`
        saying so, and its own docstring forbids treating that as the project's
        register. A caller that takes it silently is the defect the V4 round 1
        review found; this asserts `perry-lint` is not that caller.

        `main` is the probe, not `intake`, and after ADR-019 that matters
        MORE. The fallback used to be the table's rows; it is now the implicit
        `main`, which is a row the answer really does carry — so probing
        `intake`, which no fallback produces, would pass on a reader that took
        the fallback whole.
        """
        d = self.project(GOOD_STORE + '{"kind": "track", "track": "hal')
        self.assertIn(self.detail(d)[1], PS.TRACKS_STORE_UNUSABLE,
                      "the fixture must actually be unusable")
        self.assertTrue([t for t in self.detail(d)[0] if t["track"] == "main"],
                        "the projection must have a `main` row to hand back, "
                        "or this test cannot tell the two readers apart")
        self.assertEqual(self.context(d, "main"), {},
                         "the projection's row was returned as the "
                         "register's answer")

    # ── the cache ─────────────────────────────────────────────────────────

    def test_the_cache_is_keyed_on_the_root_not_on_a_projection_path(self):
        """It was keyed on `str(root / ".perry" / "config.md")` — a path that
        does not exist on any project this row is about.

        Two store-only projects declaring DIFFERENT registers must not collapse
        onto one entry, and the key must name the root rather than a file
        neither of them has.
        """
        one = self.store_only()
        two = self.store_only(track_record("main", "project", 0) + "\n")
        self.assertTrue(self.context(one, "intake"))
        self.assertEqual(self.context(two, "intake"), {},
                         "the second project's register does not declare "
                         "`intake`; a shared cache entry would resolve it")
        for key in PL._TRACK_CONTEXTS:
            self.assertFalse(key.endswith("config.md"),
                             f"cache key {key!r} names the projection")

    def test_the_register_never_hands_back_a_blank_track_name(self):
        """**Why `_track_context`'s own blank filter mutates GREEN.**

        The round planted six mutations and this is the one that survived:
        dropping `if row.get("track")` from the index build changed no test.
        It is not a missing guard on that line — it is that the line is
        DEFENCE over an invariant two readers upstream already hold.
        `stored_tracks` filters `(r.get("track") or "").strip()` and
        `parse_tracks` returns `[r for r in rows if r["track"]]`, so no
        `declared_tracks_detail` answer can carry a nameless row; and
        `_track_context` returns `{}` for an empty cell before any lookup, so
        a blank key would be unreachable even if one existed.

        Pinning it HERE is the honest place: the day a reader upstream starts
        emitting a nameless row, this reddens and that filter starts
        mattering. A fixture in `_track_context` faking a state neither reader
        can produce would assert nothing about the code that actually runs.
        """
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        # **A shape where each reader has something to filter**, or the
        # assertion is over rows that were never at risk. The first draft of
        # this test used only the fixtures above, none of which carries a
        # nameless row — so dropping the filter mutated GREEN through it. One
        # of the two shapes it added was a `## Tracks` table with a nameless
        # row; that reader is gone with ADR-019, and the store side, which is
        # the one that still has a filter to lose, stays.
        nameless_store = self.project(
            track_record("main", "project", 0) + "\n"
            + json.dumps({"kind": "track", "track": "   ", "mode": "queue",
                          "spine": "", "stages": "", "wip": "", "sla": "",
                          "cycle": "", "default_rung": "V3", "order": 1}) + "\n")
        shapes = {
            "healthy store": self.project(GOOD_STORE),
            "no store": self.project(None),
            "trackless store": self.project(setting + "\n"),
            "unreadable store": self.project(
                GOOD_STORE + '{"kind": "track", "track": "hal'),
            "empty store": self.project(""),
            "store carries a nameless record": nameless_store,
        }
        for label, d in shapes.items():
            with self.subTest(label):
                tracks, _source = self.detail(d)
                self.assertTrue(tracks, "the register is never empty")
                for row in tracks:
                    self.assertTrue(
                        (row.get("track") or "").strip(),
                        f"{label}: the register handed back a nameless row "
                        f"{row!r} — `perry-lint § _track_context`'s blank "
                        f"filter is now load-bearing and needs its own test")

    # ── the KR's own condition ────────────────────────────────────────────

    def test_perry_lint_holds_no_reader_of_the_track_register_projection(self):
        """`P003-O2-KR1`, asserted against the file rather than against a count.

        The KR targeted ZERO `bin/` call sites reading the track register
        from `.perry/config.md` while the store exists. **ADR-019 drives it to
        zero by construction** — the file is gone — and this test is kept
        because it never measured the filename: it asserts that `perry-lint`
        holds no inline TABLE PARSER of its own. The four call sites the KR
        enumerated were `parse_tracks` callers; this one was not, which is
        exactly how it went uncounted, and a grep for `parse_tracks` would
        not have found it.

        So what is left is the guard against the shape coming back under
        another register: a header probe and a row parser written inline, in a
        file whose one legitimate reader is `declared_tracks_detail`.
        """
        text = LINT.read_text(encoding="utf-8")
        self.assertNotIn('column_index(cells, "Mode")', text,
                         "the inline `## Tracks` header probe is back")
        self.assertNotIn("canonical_header", text,
                         "the inline track-row parser is back")
        self.assertIn("declared_tracks_detail", text,
                      "the one register reader is not being used")


if __name__ == "__main__":
    unittest.main()
