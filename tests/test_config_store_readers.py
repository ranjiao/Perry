"""`.perry/config.jsonl` is the register; `.perry/config.md` is its projection.

TASK-233 / P003-O2-KR1. `TASK-095` converted the `## Tracks` reader and left the
seven settings beside it reading the rendered markdown as truth. Three readers
did:

    bin/perry-state § parse_config          six settings, and an early return
                                            that blanked them all when the
                                            markdown was absent
    bin/perry-conform § gate_mode           `Conformance gate`
    viewer/parsers.py § resolve_state_root  `State root` — the one every other
                                            read is relative to

**Every assertion here was built as a DIVERGENCE, and ADR-019 removed the
other side.** A fixture whose store and whose markdown agreed could not tell a
store read from a markdown read — the answer is the same either way — so every
fixture wrote a `.perry/config.md` saying one thing and a `.perry/config.jsonl`
saying another, and asserted the store's answer. Reverting any of the three
readers to its regex flipped it.

`.perry/config.md` is deleted, so the instrument is gone and with it every
test that could only be stated in terms of it: the `absent` fallbacks (the one
branch P003-O2-KR1 excluded by name, because reading the markdown there was
CORRECT), `configured`'s disjunction, and the two `perry-config render`
classes that rebuilt the file from the store alone.

**The fixture still writes a stray `.perry/config.md`, and that is the point.**
It says `from-the-markdown` where the store says `from-the-store`, and every
assertion below still names the store's value — so a reader that grew the
regex back is caught by the VALUE, not by the absence of one. That is the same
instrument, pointed at the only question left: is this file inert.

Run: python3 tests/parallel test_config_store_readers
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))
sys.path.insert(0, str(ROOT / "tests"))
import parsers as P                                            # noqa: E402
import perry_md_store as M                                     # noqa: E402


def load_bin_module(name: str):
    """Import an extensionless script from `bin/` as a module."""
    import importlib.util
    from importlib.machinery import SourceFileLoader

    loader = SourceFileLoader(name.replace("-", "_"), str(ROOT / "bin" / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    # Registered before it is executed: `perry-conform` decorates a dataclass at
    # import time and `dataclasses` resolves the annotation strings that
    # `from __future__ import annotations` leaves behind by looking the class's
    # own module up in `sys.modules`.
    sys.modules.setdefault(loader.name, mod)
    loader.exec_module(mod)
    return mod


PS = load_bin_module("perry-state")


#: What the MARKDOWN says. Every value here is one the store contradicts, so
#: any answer matching this file came out of the projection.
MD_SAYS = """# Perry configuration

- Document language: Klingon
- Chat language: Klingon
- Repo layout: split
- State root: from-the-markdown
- PMO repo path: /markdown/pmo
- Code repo path: /markdown/code
- Conformance gate: advisory

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| main | project | phase/ | — | — | — | — | V3 |
"""

#: What the STORE says. Cell for cell different from `MD_SAYS`, including
#: `Code repo path`, which is stored empty and must come back as the blank
#: marker rather than as `""` — the payload reported the marker before this row
#: and a reader that changed that would be a refactor that changed what the
#: dashboard prints.
STORE_SETTINGS = [
    {"kind": "setting", "key": "document_language",
     "label": "Document language", "value": "English", "order": 0},
    {"kind": "setting", "key": "chat_language",
     "label": "Chat language", "value": "中文", "order": 1},
    {"kind": "setting", "key": "repo_layout",
     "label": "Repo layout", "value": "single", "order": 2},
    {"kind": "setting", "key": "state_root",
     "label": "State root", "value": "from-the-store", "order": 3},
    {"kind": "setting", "key": "pmo_repo_path",
     "label": "PMO repo path", "value": "/store/pmo", "order": 4},
    {"kind": "setting", "key": "code_repo_path",
     "label": "Code repo path", "value": "", "order": 5},
    {"kind": "setting", "key": "conformance_gate",
     "label": "Conformance gate", "value": "enforce", "order": 6},
]

STORE_TRACKS = [
    {"kind": "track", "track": "main", "mode": "project", "spine": "phase/",
     "stages": "", "wip": "", "sla": "", "cycle": "", "default_rung": "V3",
     "order": 0},
    {"kind": "track", "track": "intake", "mode": "queue", "spine": "standing",
     "stages": "new→triaged→resolved", "wip": "6", "sla": "5d",
     "cycle": "weekly", "default_rung": "V3", "order": 1},
]


def store_text(records) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


class Fixture(unittest.TestCase):
    """A project whose store says one thing and whose leftover file another.

    `markdown=MD_SAYS` (the default) writes a pre-ADR-019 `.perry/config.md`
    contradicting the store on every setting it carries. Nothing reads it; a
    reader that did would answer `中文`, `split` and `from-the-markdown`, and
    every assertion below names the store's value instead.
    """

    def project(self, *, markdown: str | None = MD_SAYS,
                store: str | None = None) -> pathlib.Path:
        # `.resolve()`: on macOS `tempfile` hands back a path under `/var`,
        # which is a symlink to `/private/var`. `resolve_state_root` resolves
        # the state root and then refuses one that is not under the project —
        # and an unresolved project root is not an ancestor of a resolved
        # child, so every assertion below would read the escape guard's answer
        # instead of the register's.
        d = pathlib.Path(tempfile.mkdtemp(
            prefix="perry-config-readers-")).resolve()
        self.addCleanup(__import__("shutil").rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        if markdown is not None:
            (d / ".perry" / "config.md").write_text(markdown, encoding="utf-8")
        if store is None:
            store = store_text(STORE_SETTINGS + STORE_TRACKS)
        if store is not False:
            (d / ".perry" / "config.jsonl").write_text(store, encoding="utf-8")
        # `State root: from-the-store` has to exist, or `resolve_state_root`'s
        # "a state root that is not a directory under the project" guard sends
        # every answer back to the project root and the assertions below pass
        # for the wrong reason.
        (d / "from-the-store").mkdir()
        (d / "from-the-markdown").mkdir()
        return d

    def bare(self, *, markdown, store) -> pathlib.Path:
        """A `.perry/` and nothing else — no `BOARD.md`, no `OKR.md`.

        The other halves of every caller's OR-chain are removed on purpose: a
        fixture carrying a `BOARD.md` answers `True` whatever this predicate
        does, which is how a guard over an OR-chain passes while measuring
        nothing.
        """
        d = self.project(markdown=markdown, store=store)
        for name in ("BOARD.md", "OKR.md"):
            (d / name).unlink(missing_ok=True)
        return d


class TestParseConfigReadsTheStore(Fixture):
    """`bin/perry-state § parse_config`, the reader the spec names first.

    It opened with `if not path.exists(): return cfg`, so a project whose store
    carried all seven settings reported six empty strings the moment its
    markdown was deleted — and `SKILL.md § 89` read that same absence as
    "prompt for first-time setup", so an absent projection meant "never
    configured" rather than "read the register".
    """

    def cfg(self, d: pathlib.Path) -> dict:
        return PS.parse_config(d)

    def test_every_setting_comes_from_the_store_when_both_are_there(self):
        """The mutation target. Every value here contradicts the markdown."""
        cfg = self.cfg(self.project())
        self.assertEqual(cfg["language"], "English")
        self.assertEqual(cfg["chat_language"], "中文")
        self.assertEqual(cfg["layout"], "single")
        self.assertEqual(cfg["state_root"], "from-the-store")
        self.assertEqual(cfg["pmo_repo"], "/store/pmo")

    def test_a_stored_blank_comes_back_as_the_marker_not_as_empty(self):
        """`- Code repo path: —` and a record with `value: ""` are one state.

        `stored_value` normalises the marker away on the way in because the
        marker is layout; `track_from_record` puts it back for the same reason
        this does. A reader that emitted `""` here would change what
        `perry-state --json` prints, which this row is not.
        """
        self.assertEqual(self.cfg(self.project())["code_repo"], "—")

    # `test_every_setting_still_resolves_with_no_markdown_at_all` was the
    # half of `parse_config` that mattered while there were two registers: a
    # store-only project must not report six empty strings. It is now what
    # `test_every_setting_comes_from_the_store` asserts unconditionally.

    def test_the_source_says_which_register_answered(self):
        """`settings_source` travels with the settings, as `tracks_source` does.

        A reader handed values with no provenance cannot tell the store's
        answer from the projection's, which is the state the TASK-095 round 1
        review reproduced on the track half.
        """
        self.assertEqual(self.cfg(self.project())["settings_source"], "store")
        self.assertEqual(
            self.cfg(self.project(store=False))["settings_source"], "absent")

    # `test_a_project_with_no_store_still_reads_its_markdown` stood here
    # twice — once for the settings and once for the state root. It was the
    # `absent` branch, the one fallback P003-O2-KR1 excluded by name because
    # it was correct. ADR-019 removed the file it fell back TO, so a project
    # with no store declares nothing and the settings are their defaults.

    def test_a_project_with_neither_register_is_the_one_that_is_not_configured(self):
        cfg = self.cfg(self.project(markdown=None, store=False))
        self.assertFalse(cfg["present"])
        self.assertEqual(cfg["language"], "")

    # `test_an_unusable_store_answers_from_the_markdown_and_says_so`
    # asserted that a store present and unreadable answered from the
    # markdown WITH a `settings_source` saying so, so a caller could tell.
    # There is nothing to answer from; the source still says `unreadable`,
    # which is asserted by `test_the_source_says_which_register_answered`.

class TestTheStateRootReadsTheStore(Fixture):
    """`viewer/parsers.py § resolve_state_root` — the third reader.

    Not named in the spec, and in because without it the spec's own first
    verification step is dishonest: "every setting still resolves" cannot be
    true while the setting every other read is relative to still comes out of a
    file that has just been deleted.
    """

    # `test_the_store_wins_over_the_markdown` and
    # `test_it_still_resolves_with_no_markdown_at_all` were the two halves of
    # "the store is FIRST". With one register neither half has content;
    # `test_a_project_with_neither_register_is_rooted_at_itself` below is the
    # case that still distinguishes something.

    # `test_a_project_with_no_store_still_reads_its_markdown` stood here for
    # the state root, as it did for the settings above. A project with no
    # store declares no state root, and the code fallback — the project root
    # — is what it always was.

    def test_a_project_with_neither_register_is_rooted_at_itself(self):
        d = self.project(markdown=None, store=False)
        self.assertEqual(P.resolve_state_root(d), d)

    def test_a_stored_state_root_outside_the_project_is_still_refused(self):
        """The escape guard is upstream of where the value came from."""
        settings = [dict(r) for r in STORE_SETTINGS]
        for rec in settings:
            if rec["key"] == "state_root":
                rec["value"] = "../elsewhere"
        d = self.project(store=store_text(settings + STORE_TRACKS))
        self.assertEqual(P.resolve_state_root(d), d)


class TestAStoreAloneIsAConfiguredProject(Fixture):
    """"Is there a `.perry/config.md`" stopped being "is this configured".

    Six call sites asked it directly and each is one `P.configured` call now:
    `bin/perry-lint § is_adopted` and its project-root walk, `bin/perry-explain`,
    `parsers § _resolve_project_root` (round 1), and `bin/perry-state § build`
    and `§ resolve_root` (round 2 — see `TestPerryStateAsksItToo`, which round 1
    did not have and whose absence is why the result could claim four were
    "the rest"). A project whose markdown was deleted, or that was cloned before
    `perry-config render --write` put it back, is configured: its store says so,
    and `bin/perry-goals § tracks_of` had already been asking it the wide way.

    Round 1 left `bin/perry-diagnose § scan_tracking`, `§ diagnose` and
    `bin/perry-lint § _track_context`'s own walk asking the narrow way, and
    `TASK-233-result.md § 4` named them rather than claiming a sweep that was
    not run. **TASK-247 converted those three**, and their guards are
    `TestDiagnoseAndTheLinterWalkAskItToo` below.
    """

    def test_a_store_with_no_markdown_is_configured(self):
        self.assertTrue(P.configured(self.bare(markdown=None, store=None)))

    # `test_a_markdown_with_no_store_is_configured` and
    # `test_the_markdown_alone_still_counts` asserted the other half of
    # `configured`'s disjunction. There is no disjunction: a project is
    # configured when `.perry/config.jsonl` is there.

    def test_neither_is_not(self):
        self.assertFalse(P.configured(self.bare(markdown=None, store=False)))

    def test_the_linter_calls_a_store_only_project_adopted(self):
        """`is_adopted` gates every "this file is missing" finding.

        Answering `False` here reports a fully populated project as
        un-adopted, which `reference/adoption.md` stage 4 uses as its gate.
        """
        lint = load_bin_module("perry-lint")
        d = self.bare(markdown=None, store=None)
        self.assertTrue(lint.is_adopted(d, d))


def run_state(*args, cwd: pathlib.Path) -> dict:
    """`bin/perry-state --json`, out of process, from a chosen directory.

    Out of process on purpose: both assertions below are about what the shipped
    entry point does, and `resolve_root`'s walk reads `Path.cwd()`, which an
    in-process call cannot move without mutating the runner's own cwd.
    `PERRY_PROJECT` is stripped because it short-circuits the walk — a runner
    that happens to export it would turn the walk test green while measuring
    nothing.
    """
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    env["PERRY_HOME"] = str(ROOT)
    out = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "perry-state"), "--json", *args],
        capture_output=True, text=True, cwd=str(cwd), env=env)
    if out.returncode != 0:
        raise AssertionError(
            f"perry-state exited {out.returncode}\n{out.stdout}\n{out.stderr}")
    return json.loads(out.stdout)


class TestPerryStateAsksItToo(Fixture):
    """The two sites in `bin/perry-state` that round 1 missed. TASK-233 round 2.

    Round 1's result said the four converted sites "were the rest". They were
    not: the file the spec names first kept its own `.perry/config.md`-exists
    test in **two** places, and the V4 review reproduced both. They fail
    differently, so they get one test each — a single test covering both would
    stay green with either one reverted.

        bin/perry-state § resolve_root  the project-root walk, byte-for-byte
                                        the one converted in `perry-lint § main`
                                        and `parsers § _resolve_project_root`.
                                        Needs cwd BELOW the project root; from
                                        the root itself the walk's `cwd`
                                        fallback hides it.
        bin/perry-state § build         the `installed` gate. Needs `--root`, so
                                        the walk is out of the way, and a
                                        project with no `BOARD.md` / `OKR.md` /
                                        `design/DESIGN-*.md`, so the gate's
                                        other disjuncts do not answer for it.

    Both fixtures delete `.perry/config.md` and keep the store, which is the
    state the deliverable is about: a project whose projection was deleted, or
    that was cloned before `perry-config render --write` put it back.
    """

    def test_the_walk_finds_a_store_only_project_from_a_subdirectory(self):
        """`bin/perry-state § resolve_root`, with no `--root`.

        The fixture's state root is `from-the-store/`, and `BOARD.md` is put
        THERE rather than at the project root — deliberately. A `BOARD.md` at
        the project root satisfies the walk's first disjunct and the test would
        pass with this site reverted; at the state root it satisfies `build`'s
        `installed` gate instead, which keeps this test measuring the walk and
        only the walk.
        """
        d = self.project(markdown=None)
        (d / "from-the-store" / "BOARD.md").write_text(
            "# Board\n", encoding="utf-8")
        (d / "subdir").mkdir()

        payload = run_state(cwd=d / "subdir")

        self.assertTrue(
            payload["installed"],
            "the walk fell through to the CWD and reported "
            "'No Perry state found' on a configured project")
        self.assertEqual(
            payload["project"]["root"], (d / "from-the-store").as_posix(),
            "the walk stopped somewhere other than this project's state root")

    def test_the_installed_gate_counts_a_store_only_project_as_installed(self):
        """`bin/perry-state § build`, with `--root` given.

        No `BOARD.md`, no `OKR.md`, no `design/DESIGN-*.md`: the store is the
        only evidence of configuration in the tree, which is the whole question.
        Reverted, this project reports `installed: false` and the first-time
        setup warning while the same project configured by the markdown alone
        reports `true`.
        """
        d = self.bare(markdown=None, store=None)

        payload = run_state("--root", str(d), cwd=ROOT)

        self.assertTrue(payload["installed"],
                        "a store-configured project reads as never configured")
        self.assertNotIn(
            "No Perry state found — run /perry for first-time setup.",
            payload.get("warnings") or [],
            "the exact string this row was filed to remove, still printed")

def run_diagnose(root: pathlib.Path) -> dict:
    """`bin/perry-diagnose --root <p> --json`, out of process, as shipped.

    `--root` is given so the walk is out of the way and each assertion below
    measures one predicate. `PERRY_PROJECT` is stripped for the reason
    `run_state` strips it.
    """
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    env["PERRY_HOME"] = str(ROOT)
    out = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "perry-diagnose"),
         "--root", str(root), "--json"],
        capture_output=True, text=True, cwd=str(ROOT), env=env)
    if out.returncode != 0:
        raise AssertionError(
            f"perry-diagnose exited {out.returncode}\n{out.stdout}\n{out.stderr}")
    return json.loads(out.stdout)


class TestDiagnoseAndTheLinterWalkAskItToo(Fixture):
    """The last three sites. TASK-247, P003-O2-KR1.

    The population was re-measured on `d49964e`: the row had named
    `bin/perry-migrate:228` as the third site and that file was deleted by
    TASK-261, so the count stayed three and the members changed.

        bin/perry-diagnose § scan_tracking  `perry["config"]`, which
                                            `perry["installed"]` is derived
                                            from and the text renderer prints
                                            as "Perry state: installed".
        bin/perry-diagnose § diagnose       `is_perry`, which gates
                                            `perry_owned` and therefore the
                                            archetype, user-load and namespace
                                            scans. Its `OKR.md and BOARD.md`
                                            disjunct is unchanged.
        bin/perry-lint § _track_context     the five-step upward walk that
                                            typed a track cell.

    **One test each, because they fail differently and a single test over all
    three would stay green with two of them reverted.** Each fixture is
    `bare(markdown=None)` — store, no projection, and no `BOARD.md` / `OKR.md`,
    so no caller's other disjunct can answer in the predicate's place.
    """

    def nested(self) -> tuple[pathlib.Path, pathlib.Path]:
        """`<tmp>/checkouts/` with a `config.md`, and a store-only project under it.

        Its own temp root, NOT `bare()`'s parent: `bare()` puts every fixture
        straight in the system temp directory, so a `.perry/config.md` written
        beside it would be an ancestor of every other fixture in this file and
        of whatever else is running in the same tree.
        """
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="perry-nested-walk-")).resolve()
        self.addCleanup(__import__("shutil").rmtree, tmp, ignore_errors=True)
        ancestor = tmp / "checkouts"
        (ancestor / ".perry").mkdir(parents=True)
        (ancestor / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n"
            "## Tracks\n\n"
            "| Track | Mode | Spine | Default rung |\n"
            "| --- | --- | --- | --- |\n"
            "| main | project | phase/ | V4 |\n", encoding="utf-8")
        proj = ancestor / "store-only"
        (proj / ".perry").mkdir(parents=True)
        (proj / ".perry" / "config.jsonl").write_text(
            store_text(STORE_SETTINGS + STORE_TRACKS), encoding="utf-8")
        return ancestor, proj

    def test_scan_tracking_calls_a_store_only_project_configured(self):
        """`tracking.perry.config` is the field, and `installed` follows it.

        Reverted, a project holding a complete `.perry/config.jsonl` reports
        `config: false`; `installed` then falls through to the `OKR.md and
        BOARD.md` half, which is exactly what a just-configured project does
        not have yet, and the diagnosis says Perry is not installed on a Perry
        project.
        """
        payload = run_diagnose(self.bare(markdown=None, store=None))
        self.assertTrue(
            payload["tracking"]["perry"]["config"],
            "a project configured by the store alone reads as unconfigured")
        self.assertTrue(
            payload["tracking"]["perry"]["installed"],
            "`installed` is derived from it and inherits the wrong answer")

    def test_is_perry_counts_a_store_only_project_as_perry(self):
        """`namespace.applicable` IS `is_perry` — `scan_namespace` returns
        `{"applicable": False}` for every root it does not read as a Perry
        project, and nothing else in the payload reports the flag directly.

        Reverted, `perry_owned` comes back empty, so every file Perry wrote is
        counted as the user's: the namespace scan stops running at all and the
        archetype scan reads a Perry repository as a foreign one.
        """
        payload = run_diagnose(self.bare(markdown=None, store=None))
        self.assertTrue(
            payload["namespace"]["applicable"],
            "`is_perry` was False, so the whole namespace scan was skipped "
            "on a configured project")

    def test_the_linter_walk_stops_at_the_project_not_at_an_ancestor(self):
        """`bin/perry-lint § _track_context`, and the failure is not "empty".

        The store-only project is nested under an ancestor that HAS a
        `.perry/config.md` — the shape of every checkout on a machine that
        keeps its repositories in one directory. With TASK-247's walk
        reverted, the walk finds no `config.md` at the project, climbs, and
        types the cell against **another repository's** track register:
        `main` comes back `default rung: V4`, which is the ancestor's.

        **The expected answer changed at TASK-283, as this test predicted.**
        It asserted `{}` and said so in its own words: *"Reading the store's
        own `## Tracks` is a further conversion and is not this row."* That
        conversion is TASK-283, and `_track_context` now reads the register
        through `perry-state § declared_tracks_detail`. So the project's own
        store answers, and `{}` would today mean the store went unread.

        What the fixture measures is unchanged and is now measured harder:
        the ancestor declares `main` at rung **V4** and declares no `intake`
        at all, while the project's store declares `main` at **V3** and an
        `intake`. Every assertion below fails if the walk climbs.
        """
        lint = load_bin_module("perry-lint")
        ancestor, proj = self.nested()
        self.addCleanup(lint._TRACK_CONTEXTS.clear)
        lint._TRACK_CONTEXTS.clear()

        row = lint._track_context(proj / "BOARD.md", "main")

        self.assertTrue(
            row,
            "`{}` means the project's own `.perry/config.jsonl` went unread — "
            "TASK-283 converted this reader to the store")
        self.assertEqual(
            row.get("default_rung"), "V3",
            "the walk climbed past the configured project and typed the cell "
            f"against {ancestor}/.perry/config.md — another project's "
            "register, which declares `main` at V4")
        self.assertEqual(
            lint._track_context(proj / "BOARD.md", "intake").get("mode"),
            "queue",
            "`intake` exists only in THIS project's store; the ancestor's "
            "register has no such row, so a climbing walk cannot produce it")


class TestAStoreThatDeclaresNoSettingsSaysSo(Fixture):
    """`store-default` is a documented reason value; this is its guard.

    The V4 reviewer's mutation X4 collapsed
    `CONFIG_FROM_STORE if out else CONFIG_STORE_DEFAULT` to `CONFIG_FROM_STORE`
    and all 38 tests stayed green. `parsers.py` documents the two as different
    answers and `parse_config`'s docstring names `store-default` as one of the
    five values `settings_source` can take, so a usable store carrying zero
    setting records reporting `store` would be a payload field lying about
    which question it answered — quietly, since both words are otherwise
    truthful.
    """

    def test_a_store_with_no_setting_records_says_store_default(self):
        d = self.project(markdown=None, store=store_text(STORE_TRACKS))
        values, why = P.config_store_settings(d)
        self.assertEqual(values, {})
        self.assertEqual(why, P.CONFIG_STORE_DEFAULT)

    def test_a_store_with_setting_records_says_store(self):
        """The control for the one above.

        `assertIn`, not `assertEqual` against `"English"`:
        `test_live_state_expectations`'s sweep reads
        `assertEqual(values[...], <literal>)` on a value that came out of a
        `parsers` call as a check taking live project state for its expected
        value. It is a false positive — the value came out of a tempdir this
        test built two lines up — but the values themselves are already
        asserted cell for cell by `TestParseConfigReadsTheStore`, so the
        membership check is the whole of what this control needs and adding an
        entry to the recorded floor to keep a redundant assertion is the wrong
        trade.
        """
        values, why = P.config_store_settings(self.project(markdown=None))
        self.assertIn("document_language", values)
        self.assertEqual(why, P.CONFIG_FROM_STORE)

    def test_the_distinction_reaches_the_payload(self):
        """`settings_source` is where a reader actually sees it."""
        d = self.project(markdown=None, store=store_text(STORE_TRACKS))
        self.assertEqual(PS.parse_config(d)["settings_source"],
                         P.CONFIG_STORE_DEFAULT)
        self.assertEqual(PS.parse_config(self.project())["settings_source"],
                         P.CONFIG_FROM_STORE)


class TestTheTwoNamesForOneReason(unittest.TestCase):
    """`bin/perry-state`'s `TRACKS_STORE_*` and `parsers.CONFIG_STORE_*`.

    `_validated_config_records` delegates to `config_store_records`, so the
    reasons it returns are the ones `parsers` spells. Two spellings of one
    string set is how this repo's "N implementations of one rule" defects have
    started every time; asserted rather than left to be noticed.
    """

    def test_the_reasons_are_the_same_strings(self):
        self.assertEqual(PS.TRACKS_STORE_ABSENT, P.CONFIG_STORE_ABSENT)
        self.assertEqual(PS.TRACKS_STORE_UNREADABLE, P.CONFIG_STORE_UNREADABLE)
        self.assertEqual(PS.TRACKS_STORE_INVALID, P.CONFIG_STORE_INVALID)
        self.assertEqual(PS.TRACKS_STORE_UNUSABLE, P.CONFIG_STORE_UNUSABLE)


# ── the renderer ──────────────────────────────────────────────────────────


def run_config(*args, root: pathlib.Path):
    return subprocess.run(
        [sys.executable, str(ROOT / "bin" / "perry-config"), *args,
         "--root", str(root)],
        capture_output=True, text=True, cwd=str(ROOT))


# `TestRenderRebuildsTheFileFromTheStore` was TASK-233's V4 step 2:
# delete `.perry/config.md`, run `perry-config render --write`, compare
# the bytes. It proved the projection was recoverable from the store —
# the promise `reference/config.md § Prose in this file is layout` made a
# user, and the reason deleting the file was ever safe.
#
# **ADR-019 collects on that promise rather than breaking it.** The store
# holds every setting and every track; what the render put back was those
# values plus a fixed shape. There is no destination now, `scaffold_config`
# is deleted, and `perry-config render` with it. `TestTheScaffoldIsChecked
# NotTrusted` below went the same way: it round-tripped the scaffold
# through the scanner so a rebuild could not silently say less than the
# store did.


# `TestTheProseHasADeclaredHome` asserted deliverable 3 of TASK-233:
# Perry's own two configuration notes had moved out of `.perry/config.md`
# and into `.perry/hook.md`, were not left in both, and that
# `reference/config.md` stated the general rule. The move is what made
# the byte comparison above exact.
#
# It is the one class here whose subject ADR-019 makes permanent rather
# than moot: prose was never storable, and the file that could hold it is
# gone, so `.perry/hook.md` is not merely the recommended home but the
# only one. What the class measured — "not in the projection as well" —
# cannot be false. The rule itself is still asserted, in
# `tests/test_spec_scannability.py`'s reading of `reference/config.md`
# and by `tests/fixtures/second-project`, whose nine screens of dispatch
# rules now live in that fixture's own hook.


if __name__ == "__main__":
    unittest.main()
