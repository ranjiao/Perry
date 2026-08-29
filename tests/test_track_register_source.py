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
CONFIG = ROOT / "bin" / "perry-config"


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

#: The same config with a SECOND declared track. Needed because the divergence
#: this module measures is "the table declares something the store does not",
#: and a one-row table has nothing to lose.
CONFIG_MD_TWO = CONFIG_MD + (
    "| intake | queue | standing | new→done | 6 | 5d | weekly | V3 |\n")

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

    def project(self, store: str | None, *, md_declares: bool = True,
                md_declares_two: bool = False) -> pathlib.Path:
        """The `.perry/config.md` half of the fixture, in three shapes.

        `md_declares=True` (default) writes a `## Tracks` table declaring ONLY
        `main`, while `GOOD_STORE` declares `main` AND `intake` — that
        divergence is the instrument every assertion about "did it read the
        store or the projection" rests on, and it must not be disturbed.

        `md_declares=False` writes no `## Tracks` section at all. That is the
        shape three of this repo's six config files have.

        `md_declares_two=True` writes a table declaring `main` AND `intake`,
        which is the ONLY shape where a `store-default` answer loses something
        — the distinction round 3 failed on. It is opt-in for the same reason
        the default is one track: turning it on globally would make the store
        and the table agree and quietly disarm the other twenty tests.
        """
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-track-source-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text(
            CONFIG_MD_TWO if md_declares_two else
            CONFIG_MD if md_declares else
            CONFIG_MD.split("## Tracks")[0])
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
        self.assertEqual(
            self.detail(self.project(setting + "\n", md_declares=False))[1],
            PS.TRACKS_STORE_DEFAULT)

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
            self.project(setting + "\n", md_declares=False))
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

    def test_every_unusable_source_has_a_sentence_for_a_human(self):
        """One wording, so three callers cannot describe one state three ways."""
        for source in PS.TRACKS_STORE_UNUSABLE:
            self.assertIn(source, PS.TRACKS_STORE_WHY)
            self.assertIn("config.jsonl", PS.TRACKS_STORE_WHY[source])


SETTING_ONLY = json.dumps({"kind": "setting", "key": "language",
                           "value": "English", "order": 0}) + "\n"

#: A `## Tracks` row whose every cell is FILLED, so that a store record which
#: merely EXISTS under the same name still contradicts it. Round 5's FAIL
#: lived in the gap between "a record named `main`" and "a record that says
#: what the table says", and `CONFIG_MD` above cannot express it: its `main`
#: row agrees with `GOOD_STORE`'s `main` record cell for cell.
DECLARING_MAIN = ("""# Perry configuration

- Document language: English
- Repo layout: single
- State root: .
""" + GATE_OFF + """
## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| main | queue | standing | new→triaged→done | 4 | 3d | weekly | V2 |
""")

#: The same table, localized. `perry_md_store` takes the heading AND every
#: column name from `schema/state-schema.json § i18n` — the same place
#: `perry-lint` takes them from — so this is one register read one way, not
#: an English path and a Chinese one.
DECLARING_MAIN_ZH = DECLARING_MAIN.replace(
    "## Tracks", "## 轨道").replace(
    "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |",
    "| 轨道 | 模式 | 主线 | 阶段序列 | 在制上限 | 时限 | 周期 | 默认验证级 |")


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
            self.project(SETTING_ONLY, md_declares=False))
        self.assertEqual(source, PS.TRACKS_STORE_DEFAULT)
        self.assertEqual([t["track"] for t in tracks], ["main"])
        self.assertNotIn(source, PS.TRACKS_STORE_UNUSABLE)

    def test_it_is_not_labelled_store_because_no_record_answered(self):
        """`store` would assert a provenance the answer does not have."""
        self.assertNotEqual(
            self.detail(self.project(SETTING_ONLY, md_declares=False))[1],
            PS.TRACKS_FROM_STORE)

    DEFAULTED = [dict(PS.DEFAULT_TRACK)]

    def contradicts(self, d: pathlib.Path) -> list[str]:
        return PS.tracks_the_register_contradicts(d, self.detail(d)[1])

    def test_a_complete_default_loses_nothing(self):
        """**The trackless case, named.** No `## Tracks` section and a store
        with no track record: nothing is declared, so nothing is contradicted.
        Three of this repo's six `config.md` files are this shape and round 2
        hard-blocked every one of them."""
        d = self.project(SETTING_ONLY, md_declares=False)
        self.assertEqual(self.detail(d)[1], PS.TRACKS_STORE_DEFAULT)
        self.assertEqual(self.contradicts(d), [])
        self.assertEqual(PS.tracks_the_register_cannot_place(
            d, self.DEFAULTED, PS.TRACKS_STORE_DEFAULT), [])

    def test_a_table_that_DECLARES_main_is_not_a_complete_default(self):
        """**Round 4's FAIL.** The predicate filtered on the NAME `main`, so a
        table DECLARING `| main | queue | … | 4 | 3d | … | V2 |` beside a
        trackless store looked identical to no table at all — and every one of
        those settings vanished in silence with an allowed write, while
        `perry-lint` reported `config-store-drift · track/main`.
        """
        self.assertEqual(self.contradicts(
            self.project(SETTING_ONLY, md_declares=True)), ["main"])

    def test_it_names_every_declared_track_the_register_lacks(self):
        self.assertEqual(self.contradicts(
            self.project(SETTING_ONLY, md_declares_two=True)),
            ["intake", "main"])

    def test_the_predicate_is_empty_where_a_register_did_not_answer(self):
        """`absent` is the adoption path — there is nothing to compare — and
        the two unusable sources are already refused on their own terms, so a
        second finding would double-report."""
        d = self.project(SETTING_ONLY, md_declares_two=True)
        for source in (PS.TRACKS_STORE_ABSENT, PS.TRACKS_STORE_UNREADABLE,
                       PS.TRACKS_STORE_INVALID):
            with self.subTest(source):
                self.assertEqual(
                    PS.tracks_the_register_contradicts(d, source), [])

    #: Each retired name with the arity ITS OWN callers used, so the
    #: `TypeError` comes from the body and not from Python counting arguments
    #: — an assertion satisfied by a wrong call is an assertion about nothing.
    RETIRED_CALLS = {
        "defaulted_over_a_declaring_table": lambda fn, d, rows:
            fn(d, PS.TRACKS_STORE_DEFAULT),
        "tracks_missing_from_the_register": lambda fn, d, rows:
            fn(d, rows, PS.TRACKS_STORE_DEFAULT),
    }

    def test_the_retired_names_raise_rather_than_answering_narrowly(self):
        """Both earlier spellings — round 4's and round 5's. A caller reaching
        for one is asking a question that has since been split in two, and a
        silently narrower answer under an old name is the shape this row keeps
        being failed for."""
        self.assertEqual(sorted(PS._RETIRED_TRACK_PREDICATES),
                         sorted(self.RETIRED_CALLS))
        d = self.project(SETTING_ONLY)
        for name, call in sorted(self.RETIRED_CALLS.items()):
            with self.subTest(name):
                with self.assertRaises(TypeError):
                    call(getattr(PS, name), d, self.DEFAULTED)


class TestOneTableTwoStoresOneVerdict(Fixture):
    """**Round 5's FAIL, and the principle the user settled in USER-905.**

    *A declared row the register contradicts is drift* — principle A, one
    principle everywhere, with no second principle for the synthesised `main`.

    Round 5 compared a set of NAMES, so a register record that CONTRADICTED a
    declared row counted as carrying it. One table
    (`main/queue/standing/4/3d/V2`) against two stores differing ONLY in
    whether a `main` record exists got opposite responses — `source=store`,
    no warning, `add` rc 0 with a record; `source=store-default`, one warning,
    `add` rc 1 without one — while `perry-lint` reported the same rule on the
    same row in both.

    The fix is not a better comparison written here. It is not writing one:
    `tracks_the_register_contradicts` hands the file and the store's records
    to `perry_md_store.plan`, which is exactly what `bin/perry-lint §
    check_md_store_drift` does.
    """

    #: The store that CONTRADICTS the declared row: a real `kind: track`
    #: record named `main`, saying `project`/`phase/`/`V3` where the table
    #: says `queue`/`standing`/`V2`.
    CONTRADICTING = SETTING_ONLY + track_record("main", "project", 0) + "\n"

    def declaring(self, store: str, *, zh: bool = False) -> pathlib.Path:
        d = self.project(store)
        (d / ".perry" / "config.md").write_text(
            DECLARING_MAIN_ZH if zh else DECLARING_MAIN)
        return d

    def lint_track_rows(self, d: pathlib.Path) -> list[str]:
        """`perry-lint`'s own verdict — the independent control."""
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-lint"), "--root",
             str(d), "--json"], capture_output=True, text=True, cwd=ROOT)
        payload = json.loads(proc.stdout)
        return sorted({f["message"].split(" — ")[0]
                       for f in payload["findings"]
                       if f["rule"] == "config-store-drift"
                       and f["message"].startswith("track/")})

    def run_task(self, d: pathlib.Path, *argv):
        return subprocess.run(
            [sys.executable, str(TASK), *argv, "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)

    def test_the_two_stores_really_do_differ(self):
        """The control. Without it every assertion below could pass on two
        identical fixtures."""
        self.assertEqual(self.detail(self.declaring(self.CONTRADICTING))[1],
                         PS.TRACKS_FROM_STORE)
        self.assertEqual(self.detail(self.declaring(SETTING_ONLY))[1],
                         PS.TRACKS_STORE_DEFAULT)

    def test_perry_lint_reports_the_same_rule_on_both(self):
        for label, store in (("record", self.CONTRADICTING),
                             ("no record", SETTING_ONLY)):
            with self.subTest(label):
                self.assertEqual(
                    self.lint_track_rows(self.declaring(store)), ["track/main"])

    def test_the_writer_gives_the_same_verdict_on_both(self):
        """Same table, same drift, same answer — and the answer is *write, and
        say so*, because a register holding a row for every declared name can
        place every row it is asked to place (USER-905 decision 2)."""
        for label, store in (("record", self.CONTRADICTING),
                             ("no record", SETTING_ONLY)):
            with self.subTest(label):
                d = self.declaring(store)
                out = self.run_task(d, "add", "--title", "t", "--deliverable",
                                    "d", "--verification", "v")
                self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
                self.assertIn("the track register disagrees", out.stderr)

    def test_the_payload_warns_on_both(self):
        for label, store in (("record", self.CONTRADICTING),
                             ("no record", SETTING_ONLY)):
            with self.subTest(label):
                d = self.declaring(store)
                proc = subprocess.run(
                    [sys.executable, str(STATE), "--root", str(d), "--json"],
                    capture_output=True, text=True, cwd=ROOT)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                hits = [w for w in json.loads(proc.stdout)["warnings"]
                        if "track register" in w]
                self.assertTrue(hits, "the payload said nothing about drift "
                                      "perry-lint reports on this row")
                self.assertIn("main", hits[0])

    def test_the_goals_lane_gives_the_same_verdict_on_both(self):
        """Asserted as an EQUALITY between the two stores, not as a rc of 0.

        `commit` on this fixture is refused either way, for a reason that is
        not this row's: `DECLARING_MAIN` declares `main` as `queue` work, both
        registers answer `project`, and `OKR.md` has no `## Commitments`
        section. That refusal is identical on both sides, which is the point —
        what must not differ is the track-register verdict, and a test pinned
        to `rc == 0` would be measuring the commitments gate instead.
        """
        seen = []
        for label, store in (("record", self.CONTRADICTING),
                             ("no record", SETTING_ONLY)):
            out = subprocess.run(
                [sys.executable, str(GOALS), "commit", "--track", "main",
                 "--promise", "p", "--to", "someone", "--due",
                 "2026-09-30", "--root", str(self.declaring(store))],
                capture_output=True, text=True, cwd=ROOT)
            blob = out.stdout + out.stderr
            with self.subTest(label):
                self.assertIn("the track register disagrees", out.stderr)
                self.assertNotIn("the track register does not carry", blob,
                                 "the lane refused for a track-register "
                                 "reason on one store and not the other — "
                                 "the round 5 FAIL")
            seen.append((out.returncode,
                         "the track register disagrees" in out.stderr))
        self.assertEqual(seen[0], seen[1],
                         "one table, two stores, two different verdicts")

    def test_the_contradicted_declaration_is_named_by_the_predicate(self):
        """**The contradicted-declaration case, named.** The store HAS a
        record for `main` and it says something else — the case round 5's set
        of names could not see at all."""
        d = self.declaring(self.CONTRADICTING)
        self.assertEqual(PS.tracks_the_register_contradicts(
            d, PS.TRACKS_FROM_STORE), ["main"])
        # …and it is NOT a refusal: the register can place a `main` row.
        self.assertEqual(PS.tracks_the_register_cannot_place(
            d, self.detail(d)[0], PS.TRACKS_FROM_STORE), [])

    def test_the_localized_table_behaves_identically(self):
        """`## 轨道` with localized column headers, at both states.
        Round 5 got this right and it must not regress: the aliases come from
        `schema/state-schema.json § i18n`, which is where `perry-lint` gets
        them."""
        for label, store in (("record", self.CONTRADICTING),
                             ("no record", SETTING_ONLY)):
            with self.subTest(label):
                zh = self.declaring(store, zh=True)
                en = self.declaring(store)
                self.assertEqual(self.lint_track_rows(zh),
                                 self.lint_track_rows(en))
                self.assertEqual(
                    PS.tracks_the_register_contradicts(zh, self.detail(zh)[1]),
                    PS.tracks_the_register_contradicts(en, self.detail(en)[1]))
                self.assertEqual(["main"], PS.tracks_the_register_contradicts(
                    zh, self.detail(zh)[1]))


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
        """The round 2 regression at the write path, where it actually bit.

        **`md_declares=False`, and the round 4 review failed this row because
        it was not.** The round 2 regression bit on projects with NO
        `## Tracks` section; this guard was built with the fixture default,
        which WRITES a table declaring `main`, so it asserted an allowed write
        on a project whose table declares a track the register does not carry —
        pinning the very defect that round caused, under a docstring naming a
        different one.
        """
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        out = self.run_task(
            self.project(setting + "\n", md_declares=False),
            "intake", "--title", "a request")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


class TestAWriteAgainstADefaultedRegisterIsRefused(Fixture):
    """State 7 at the write path, which is where round 3 did the damage.

    Round 2 refused here and the reviewer called it *"correctly, loudly"*.
    Round 3 allowed the write against a register provably missing a declared
    track — and then refused `--track intake` with a message pointing at the
    very table that declares it on line 14.

    The refusal now names the STORE as the register that answered.
    """

    def run_task(self, d: pathlib.Path, *argv):
        return subprocess.run(
            [sys.executable, str(TASK), *argv, "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)

    def test_a_write_is_refused_and_nothing_is_written(self):
        d = self.project(SETTING_ONLY, md_declares_two=True)
        out = self.run_task(d, "add", "--title", "t",
                            "--deliverable", "d", "--verification", "v")
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((d / "tasks.jsonl").exists(),
                         "the refusal must mean NOTHING was written")

    def test_the_message_names_the_store_not_the_table(self):
        """Round 3's message told the user a track was "not declared in
        `.perry/config.md § Tracks`" while pointing at a table that declares
        it. The store is the register that answered; say so."""
        d = self.project(SETTING_ONLY, md_declares_two=True)
        out = self.run_task(d, "add", "--title", "t",
                            "--deliverable", "d", "--verification", "v")
        blob = out.stdout + out.stderr
        self.assertIn("the track register does not carry", blob)
        self.assertIn("intake", blob, "the message must name what was lost")
        # Round 3's message read "track 'intake' is not declared in
        # `.perry/config.md § Tracks`" while pointing at a table that declares
        # it on line 14. The register is what does not carry it; the table is
        # the thing that DOES declare it, and the wording must not swap them.
        self.assertNotIn("is not declared in", blob)
        self.assertIn("`.perry/config.md § Tracks` declares", blob)

    def test_a_read_is_still_allowed(self):
        d = self.project(SETTING_ONLY, md_declares_two=True)
        self.assertEqual(self.run_task(d, "list", "--json").returncode, 0)

    def test_a_COMPLETE_default_still_writes(self):
        """The other half. Three of this repo's six config files are this
        shape, and round 2 hard-blocked every one of them."""
        out = self.run_task(
            self.project(SETTING_ONLY, md_declares=False),
            "add", "--title", "t", "--deliverable", "d",
            "--verification", "v")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


class TestTheThreeHandEditWorkflowsStillWrite(Fixture):
    """**USER-905 decision 2, measured as commands.**

    The V4 round 5 review measured three ordinary hand-edit workflows — each
    starting from a store genuinely derived by `perry-config write
    --from-file` — hard-blocked by a refusal widened from `store-default` to
    every drifted row. All three wrote at `45a355d` and at round 4. On W3 the
    block could not even be cleared by the one command either refusal message
    names: `perry-config write --from-file` exits 1 there, so the front door
    was locked from the inside.

    | | the hand edit | round 5 | here |
    |---|---|---|---|
    | W1 | no `## Tracks`, then add a `main` row | refused | writes |
    | W2 | one track, then add a second | refused | writes |
    | W3 | two tracks, then SWAP one row | refused | writes |

    W1 is the one that separates this from round 4: round 4 also wrote here,
    by filtering the projection's names on the string `main`, and that filter
    is what round 4 was failed for. The refusal asks the register what it
    returned instead, which says the same thing about `store-default` without
    saying anything false about state 8.
    """

    NO_TRACKS = CONFIG_MD.split("## Tracks")[0]
    ONE_TRACK = CONFIG_MD
    TWO_TRACKS = CONFIG_MD_TWO
    #: **W3's swap**, and it is the NAME that swaps: the second declared row
    #: is replaced by a row for a track the register has no record of. This
    #: is the shape that reproduces the round 5 reviewer's measurement exactly
    #: — refused at `main`, and `perry-config write --from-file` exits 1 on it
    #: with *"track/intake: in the store, no line in the file — the whole
    #: record would be dropped"*, so the block cannot be cleared by the one
    #: command the refusal names.
    TWO_TRACKS_SWAPPED = CONFIG_MD_TWO.replace(
        "| intake | queue |", "| ops | queue |")

    #: The other reading of "swap one row" — the row keeps its name and
    #: changes what it says. Measured at `main` too: this one already WROTE
    #: there, because round 5 compared names, which is finding 1. It is kept
    #: because it is the shape whose stored cells the remedy would overwrite.
    TWO_TRACKS_RECELLED = CONFIG_MD_TWO.replace(
        "| main | project | phase/ | — | — | — | — | V3 |",
        "| main | queue | standing | new→triaged→done | 4 | 3d | weekly | V2 |")

    def derived(self, config_md: str) -> pathlib.Path:
        """A project whose store `perry-config write --from-file` built."""
        d = self.project(None)
        (d / ".perry" / "config.md").write_text(config_md)
        out = self.tool(CONFIG, d, "write", "--from-file")
        self.assertEqual(out.returncode, 0,
                         "the fixture's own precondition failed: "
                         + out.stdout + out.stderr)
        self.assertTrue((d / ".perry" / "config.jsonl").exists())
        return d

    def tool(self, exe: pathlib.Path, d: pathlib.Path, *argv):
        return subprocess.run(
            [sys.executable, str(exe), *argv, "--root", str(d)],
            capture_output=True, text=True, cwd=ROOT)

    def hand_edit_then_write(self, before: str, after: str):
        d = self.derived(before)
        (d / ".perry" / "config.md").write_text(after)
        out = self.tool(TASK, d, "add", "--title", "t", "--deliverable", "d",
                       "--verification", "v")
        return d, out

    def test_W1_no_section_then_a_main_row_is_added(self):
        d, out = self.hand_edit_then_write(self.NO_TRACKS, self.ONE_TRACK)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertTrue((d / "tasks.jsonl").exists(), "nothing was written")

    def test_W2_one_track_then_a_second_is_added(self):
        d, out = self.hand_edit_then_write(self.ONE_TRACK, self.TWO_TRACKS)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertTrue((d / "tasks.jsonl").exists(), "nothing was written")

    def test_W3_two_tracks_then_one_row_is_swapped(self):
        """The one whose named remedy fails. `perry-config write --from-file`
        exits 1 on this project — a defect of that command, filed separately —
        so a refusal here is a board the user cannot unblock through the front
        door."""
        d, out = self.hand_edit_then_write(self.TWO_TRACKS,
                                           self.TWO_TRACKS_SWAPPED)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertTrue((d / "tasks.jsonl").exists(), "nothing was written")

    def test_W3b_the_other_reading_of_a_swapped_row_also_writes(self):
        """Same name, different cells. Round 5 allowed this one — its
        comparison was on names — and round 6 must not lose it while fixing
        the case round 5 blocked."""
        d, out = self.hand_edit_then_write(self.TWO_TRACKS,
                                           self.TWO_TRACKS_RECELLED)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("the track register disagrees", out.stderr)
        self.assertTrue((d / "tasks.jsonl").exists(), "nothing was written")

    def test_W3_says_so_rather_than_writing_in_silence(self):
        """Allowed is not the same as unreported: the register really does
        disagree with the table, and `perry-lint` says so too."""
        _d, out = self.hand_edit_then_write(self.TWO_TRACKS,
                                            self.TWO_TRACKS_SWAPPED)
        self.assertIn("the track register disagrees", out.stderr)

    def test_the_named_remedy_really_does_fail_on_W3(self):
        """The instrument for the sentence above. If `perry-config write
        --from-file` starts succeeding here, the argument for the narrower
        refusal weakens and this test is where that shows up — rather than in
        a paragraph nobody re-measures."""
        d = self.derived(self.TWO_TRACKS)
        (d / ".perry" / "config.md").write_text(self.TWO_TRACKS_SWAPPED)
        out = self.tool(CONFIG, d, "write", "--from-file")
        self.assertNotEqual(
            out.returncode, 0,
            "`perry-config write --from-file` now recovers W3 — re-open "
            "USER-905 decision 2 rather than deleting this test")


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


class TestWhatTheProjectionDeclares(Fixture):
    """`tracks_the_projection_declares` — names only, and only track rows.

    It feeds the write refusal, so anything that leaks into it becomes a
    refusal naming something that is not a track. Its two filters — *this
    site is a track site* and *the name is not blank* — MASK EACH OTHER under
    single-line mutation: a settings site carries no `track` value, so
    dropping the kind filter leaks a blank that the blank filter catches, and
    the scanner already drops a `## Tracks` row whose first cell is empty, so
    dropping the blank filter leaks nothing the kind filter has not already
    excluded. Each alone is therefore an equivalent mutant. Both together are
    not, and that is what this asserts.
    """

    #: Settings in the preamble, a `## Tracks` row with a BLANK first cell,
    #: and one real row. Nothing but `main` may come out.
    RAGGED = ("""# Perry configuration

- Document language: English
- Repo layout: single
- State root: .
""" + GATE_OFF + """
## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
|  | queue | standing | — | 4 | 3d | — | V2 |
| main | project | phase/ | — | — | — | — | V3 |
""")

    def test_only_named_track_rows_come_out(self):
        d = self.project(SETTING_ONLY)
        (d / ".perry" / "config.md").write_text(self.RAGGED)
        self.assertEqual(PS.tracks_the_projection_declares(d), ["main"])

    def test_nothing_nameless_reaches_the_refusal(self):
        """The consequence, at the writer: a leaked blank would refuse every
        write with an empty name in the message."""
        d = self.project(SETTING_ONLY)
        (d / ".perry" / "config.md").write_text(self.RAGGED)
        lost = PS.tracks_the_register_cannot_place(
            d, [dict(PS.DEFAULT_TRACK)], PS.TRACKS_STORE_DEFAULT)
        self.assertEqual(lost, [], "a nameless or non-track site reached the "
                                   "write refusal")

    def test_no_config_md_declares_nothing(self):
        """The adoption shape. Round 4's review found this branch untested and
        round 5 left it that way."""
        d = self.project(SETTING_ONLY)
        (d / ".perry" / "config.md").unlink()
        self.assertEqual(PS.tracks_the_projection_declares(d), [])

    def test_an_unusable_store_with_no_config_md_beside_it_still_answers(self):
        """A store present and unusable, and no projection to fall back TO.

        `declared_tracks_detail`'s `cfg.exists()` guard is the only thing
        between this state and a `FileNotFoundError` out of the tool that is
        supposed to keep working when everything else has broken. It was
        GREEN across the whole suite at rounds 4 and 5 — the round 4 review
        recorded it and round 5 left it — so it is asserted here rather than
        carried for a third round.
        """
        d = self.project(GOOD_STORE + '{"kind": "track", "track": "hal')
        (d / ".perry" / "config.md").unlink()
        tracks, source = self.detail(d)
        self.assertIn(source, PS.TRACKS_STORE_UNUSABLE)
        self.assertEqual([t["track"] for t in tracks], ["main"])
        self.assertEqual(PS.tracks_the_register_contradicts(d, source), [])


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
        """`md_declares=False` — see the note on the `perry-task` twin."""
        setting = json.dumps({"kind": "setting", "key": "language",
                              "value": "English", "order": 0})
        out = self.run_goals(
            self.project(setting + "\n", md_declares=False),
            *self.REACHES_REGISTER)
        self.assertNotIn("track register", out.stdout + out.stderr)

    def test_goals_refuses_when_a_declared_track_has_no_row_at_all(self):
        """**The assertion this class was missing, and Decision 3 of USER-905.**

        `bin/perry-goals`' refusal was measured again at round 5: `if lost:` →
        `if False:` left the FULL suite at exactly the baseline, because none
        of this class's three tests reached the `lost` branch — all three used
        fixtures where the table declares nothing the register lacks. That is
        the same defect this class's own docstring records against round 2,
        one branch to the side.

        State 7 is the branch: a settings-only store beside a table declaring
        `main` AND `intake`. The register has no row for `intake` at all, so
        `commit --track main` would still write `phase/` and the linkage
        register off a truncated list.
        """
        out = self.run_goals(self.project(SETTING_ONLY, md_declares_two=True),
                             *self.REACHES_REGISTER)
        self.assertNotEqual(out.returncode, 0,
                            "the goals lane wrote against a register that "
                            "carries no row for a declared track")
        blob = out.stdout + out.stderr
        self.assertIn("the track register does not carry", blob)
        self.assertIn("intake", blob, "the message must name what was lost")


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

    def payload(self, d: pathlib.Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(DIAGNOSE), "--root", str(d), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[:400])
        return json.loads(proc.stdout)

    def test_a_label_with_no_drift_signal_was_the_silent_one(self):
        """**V4 amended criterion 9.** Round 5 measured `perry-diagnose` on
        state 7 reporting `store-default` / `['main']` with empty stderr while
        `perry-state` warned and both writers refused. It carried WHICH
        register answered and nothing about that register contradicting the
        table beside it. `MODE-02` is that half."""
        d = self.project(SETTING_ONLY, md_declares_two=True)
        pay = self.payload(d)
        wm = pay["work_modes"]
        self.assertEqual(wm["tracks_source"], PS.TRACKS_STORE_DEFAULT)
        self.assertEqual(wm["tracks_contradicted"], ["intake", "main"])
        self.assertIn("MODE-02", [f["id"] for f in pay["findings"]])

    def test_it_reports_the_contradicted_declaration_too(self):
        """The other half of the one principle: a store record that DISAGREES
        with the declared row, not merely a missing one."""
        d = self.project(SETTING_ONLY + track_record("main", "project", 0)
                         + "\n")
        (d / ".perry" / "config.md").write_text(DECLARING_MAIN)
        pay = self.payload(d)
        self.assertEqual(pay["work_modes"]["tracks_source"],
                         PS.TRACKS_FROM_STORE)
        self.assertEqual(pay["work_modes"]["tracks_contradicted"], ["main"])
        self.assertIn("MODE-02", [f["id"] for f in pay["findings"]])

    def test_an_agreeing_register_gets_no_finding(self):
        """The other direction, or the check is decorative: `GOOD_STORE`'s
        `main` record agrees with `CONFIG_MD`'s `main` row cell for cell, and
        `intake` being in the store and not the table is the register
        declaring MORE — `perry-lint`'s to report, not a contradiction of a
        declared row."""
        pay = self.payload(self.project(GOOD_STORE))
        self.assertEqual(pay["work_modes"]["tracks_contradicted"], [])
        self.assertNotIn("MODE-02", [f["id"] for f in pay["findings"]])


if __name__ == "__main__":
    unittest.main()
