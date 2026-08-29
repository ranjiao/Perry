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

**Every assertion here is built as a DIVERGENCE, and that is deliberate.** A
fixture whose store and whose markdown agree cannot tell a store read from a
markdown read: the answer is the same either way, and a test written on one
passes against a reader that does neither of the things it claims. So every
fixture below writes a `.perry/config.md` that says one thing and a
`.perry/config.jsonl` that says another, and asserts the store's answer. Revert
any of the three readers to its regex and the divergence flips the assertion.

The other half of the row is `perry-config render`, which could not rebuild
`.perry/config.md` at all with the file absent — it printed `no
.perry/config.md` and wrote nothing. `TestRenderRebuildsTheFileFromTheStore`
is the guard on that, and `TestTheScaffoldIsCheckedNotTrusted` is the guard on
the check that stops it writing a file that says less than the store does.

Run: python3 tests/parallel test_config_store_readers
"""

from __future__ import annotations

import json
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
PC = load_bin_module("perry-conform")


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
    """A project whose two registers disagree about everything they both hold."""

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

    def test_every_setting_still_resolves_with_no_markdown_at_all(self):
        """V4 step 1. This is the sentence the row was filed on."""
        cfg = self.cfg(self.project(markdown=None))
        self.assertTrue(cfg["present"],
                        "an absent markdown still reads as 'never configured'")
        self.assertEqual(
            [cfg["language"], cfg["chat_language"], cfg["layout"],
             cfg["state_root"], cfg["pmo_repo"], cfg["code_repo"]],
            ["English", "中文", "single", "from-the-store", "/store/pmo", "—"])

    def test_the_source_says_which_register_answered(self):
        """`settings_source` travels with the settings, as `tracks_source` does.

        A reader handed values with no provenance cannot tell the store's
        answer from the projection's, which is the state the TASK-095 round 1
        review reproduced on the track half.
        """
        self.assertEqual(self.cfg(self.project())["settings_source"], "store")
        self.assertEqual(
            self.cfg(self.project(store=False))["settings_source"], "absent")

    def test_a_project_with_no_store_still_reads_its_markdown(self):
        """The adoption path, which `P003-O2-KR1` excludes by name.

        There is no store, so the markdown IS the register and reading it is
        correct. A conversion that broke this would break every project that
        has never run `perry-config write --from-file`.
        """
        cfg = self.cfg(self.project(store=False))
        self.assertEqual(cfg["language"], "Klingon")
        self.assertEqual(cfg["state_root"], "from-the-markdown")
        self.assertTrue(cfg["present"])

    def test_a_project_with_neither_register_is_the_one_that_is_not_configured(self):
        cfg = self.cfg(self.project(markdown=None, store=False))
        self.assertFalse(cfg["present"])
        self.assertEqual(cfg["language"], "")

    def test_an_unusable_store_answers_from_the_markdown_and_says_so(self):
        """A store present on disk and broken is not the adoption path.

        The values come back from the projection because there is nothing else
        to read, and `settings_source` is what stops a caller treating them as
        the register's. The truncated trailing line is the shape an interrupted
        write leaves.
        """
        broken = store_text(STORE_SETTINGS) + '{"kind": "setting", "key": "sta'
        cfg = self.cfg(self.project(store=broken))
        self.assertIn(cfg["settings_source"], P.CONFIG_STORE_UNUSABLE)
        self.assertEqual(cfg["language"], "Klingon")


class TestTheGateReadsTheStore(Fixture):
    """`bin/perry-conform § gate_mode`, the second reader the spec names.

    The markdown in every fixture here says `advisory` and the store says
    `enforce`, so `enforce` can only have come from the store. That direction
    is on purpose: a fixture where the store said `advisory` would pass against
    a reader that lost the setting entirely, because `advisory` is also what a
    reader answering nothing at all would eventually... not produce — the
    shipped default is `enforce`. Either direction alone is ambiguous with one
    of the two failure modes, so `TestTheGateReadsTheStore` asserts BOTH.
    """

    def test_the_store_wins_over_the_markdown(self):
        self.assertEqual(PC.gate_mode(self.project()), "enforce")

    def test_the_store_wins_in_the_other_direction_too(self):
        """`advisory` out of the store, over an `enforce` markdown.

        Without this case the class above is satisfied by a reader that dropped
        the setting on the floor, since the shipped default is `enforce`.
        """
        settings = [dict(r) for r in STORE_SETTINGS]
        for rec in settings:
            if rec["key"] == "conformance_gate":
                rec["value"] = "advisory"
        d = self.project(
            markdown=MD_SAYS.replace("- Conformance gate: advisory",
                                     "- Conformance gate: enforce"),
            store=store_text(settings + STORE_TRACKS))
        self.assertEqual(PC.gate_mode(d), "advisory")

    def test_the_declared_gate_survives_the_markdown_being_deleted(self):
        """V4 step 1: *"`perry-conform` still reports the declared gate rather
        than the default"*."""
        settings = [dict(r) for r in STORE_SETTINGS]
        for rec in settings:
            if rec["key"] == "conformance_gate":
                rec["value"] = "advisory"
        d = self.project(markdown=None,
                         store=store_text(settings + STORE_TRACKS))
        self.assertEqual(PC.gate_mode(d), "advisory")
        self.assertNotEqual(PC.gate_mode(d), PC.DEFAULT_MODE,
                            "the fixture no longer distinguishes the declared "
                            "gate from the shipped default")

    def test_a_project_with_no_store_still_reads_its_markdown(self):
        self.assertEqual(PC.gate_mode(self.project(store=False)), "advisory")

    def test_a_usable_store_with_no_gate_record_declares_nothing(self):
        """Not a fallback to the markdown — an answer.

        The store is derived from the preamble, so a key it does not carry is a
        line the file does not have. Falling through here would reintroduce the
        two-registers problem on the one setting that decides whether every
        other write is allowed.
        """
        settings = [r for r in STORE_SETTINGS
                    if r["key"] != "conformance_gate"]
        d = self.project(store=store_text(settings + STORE_TRACKS))
        self.assertEqual(PC.gate_mode(d), PC.DEFAULT_MODE)

    def test_the_environment_still_beats_both(self):
        """Most specific wins, and the env var is still the most specific."""
        import os
        d = self.project()
        old = os.environ.get("PERRY_CONFORMANCE")
        os.environ["PERRY_CONFORMANCE"] = "advisory"
        try:
            self.assertEqual(PC.gate_mode(d), "advisory")
        finally:
            if old is None:
                os.environ.pop("PERRY_CONFORMANCE", None)
            else:
                os.environ["PERRY_CONFORMANCE"] = old


class TestTheStateRootReadsTheStore(Fixture):
    """`viewer/parsers.py § resolve_state_root` — the third reader.

    Not named in the spec, and in because without it the spec's own first
    verification step is dishonest: "every setting still resolves" cannot be
    true while the setting every other read is relative to still comes out of a
    file that has just been deleted.
    """

    def test_the_store_wins_over_the_markdown(self):
        d = self.project()
        self.assertEqual(P.resolve_state_root(d), d / "from-the-store")

    def test_it_still_resolves_with_no_markdown_at_all(self):
        d = self.project(markdown=None)
        self.assertEqual(P.resolve_state_root(d), d / "from-the-store")

    def test_a_project_with_no_store_still_reads_its_markdown(self):
        d = self.project(store=False)
        self.assertEqual(P.resolve_state_root(d), d / "from-the-markdown")

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


class TestRenderRebuildsTheFileFromTheStore(unittest.TestCase):
    """V4 step 2: delete the file, rebuild it, compare the bytes.

    Run on a COPY of Perry's own `.perry/` rather than on a synthetic fixture,
    because the file this row is about is that one, and a fixture written to
    match the scaffold would be comparing the scaffold with itself.
    """

    def project(self) -> tuple[pathlib.Path, str]:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-config-render-"))
        self.addCleanup(__import__("shutil").rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        original = (ROOT / ".perry" / "config.md").read_text(encoding="utf-8")
        (d / ".perry" / "config.md").write_text(original, encoding="utf-8")
        (d / ".perry" / "config.jsonl").write_text(
            (ROOT / ".perry" / "config.jsonl").read_text(encoding="utf-8"),
            encoding="utf-8")
        # `State root: perry` — the lock and every path resolve through it.
        (d / "perry").mkdir()
        return d, original

    def test_the_rebuilt_file_is_byte_identical_to_the_deleted_one(self):
        d, original = self.project()
        (d / ".perry" / "config.md").unlink()
        out = run_config("render", "--write", root=d)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual((d / ".perry" / "config.md").read_text(
            encoding="utf-8"), original)

    def test_it_is_the_store_that_is_being_read_and_not_a_leftover_file(self):
        """Anti-vacuity. Move one stored value and the rebuild moves with it.

        Without this, the test above passes against a renderer that recovered
        the file from a backup, a temp copy, or anything else that is not the
        store.
        """
        d, original = self.project()
        store = d / ".perry" / "config.jsonl"
        store.write_text(store.read_text(encoding="utf-8").replace(
            '"value": "single"', '"value": "split"'), encoding="utf-8")
        (d / ".perry" / "config.md").unlink()
        self.assertEqual(run_config("render", "--write", root=d).returncode, 0)
        rebuilt = (d / ".perry" / "config.md").read_text(encoding="utf-8")
        self.assertIn("- Repo layout: split", rebuilt)
        self.assertNotEqual(rebuilt, original)

    def test_render_to_stdout_needs_no_file_either(self):
        d, original = self.project()
        (d / ".perry" / "config.md").unlink()
        out = run_config("render", root=d)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout, original)
        self.assertFalse((d / ".perry" / "config.md").exists(),
                         "`render` without `--write` wrote a file")

    def test_it_returns_non_zero_when_there_is_no_store_to_rebuild_from(self):
        """*"returns non-zero when it cannot"*, on the case that matters most.

        Rendering a file from a store built out of that same file proves
        nothing, and with neither on disk there is nothing to render at all.
        """
        d, _original = self.project()
        (d / ".perry" / "config.md").unlink()
        (d / ".perry" / "config.jsonl").unlink()
        out = run_config("render", "--write", root=d)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((d / ".perry" / "config.md").exists())

    def test_it_returns_non_zero_on_a_store_it_cannot_read(self):
        d, _original = self.project()
        store = d / ".perry" / "config.jsonl"
        store.write_text(store.read_text(encoding="utf-8")
                         + '{"kind": "setting", "key": "sta',
                         encoding="utf-8")
        (d / ".perry" / "config.md").unlink()
        out = run_config("render", "--write", root=d)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((d / ".perry" / "config.md").exists())

    def test_okr_has_no_scaffold_and_still_refuses(self):
        """`OKR.md` is mostly mission, principles and narrative.

        A scaffold there would emit a KR table under headings the store has no
        record of — a file that looks like an `OKR.md` and asserts nothing the
        project wrote. `perry-okr render` with no file refuses and says so.
        """
        self.assertIsNone(M.OKR.scaffold)
        d, _original = self.project()
        (d / "perry" / "okr.jsonl").write_text(
            json.dumps({"kind": "kr", "version": "v1", "objective": "O1",
                        "id": "KR1", "text": "t", "metric": "m",
                        "stretch": "", "deadline": "", "linked": "",
                        "qualifier": "", "form": "table", "order": 0},
                       ensure_ascii=False) + "\n", encoding="utf-8")
        out = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-okr"), "render",
             "--write", "--root", str(d)],
            capture_output=True, text=True, cwd=str(ROOT))
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((d / "perry" / "OKR.md").exists())


class TestTheScaffoldIsCheckedNotTrusted(unittest.TestCase):
    """The round trip that makes the rebuild a guard rather than a second
    renderer.

    `scaffold_config` is written independently of `scan_config` and
    `render_lines`. `main` renders its output back through those and refuses
    unless the bytes are unchanged and every record found a line — so a
    scaffold that emitted the table's columns in the wrong order, or that could
    not express a record, refuses instead of writing a file that silently says
    less than the store does.
    """

    def project(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-config-scaffold-"))
        self.addCleanup(__import__("shutil").rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        (d / ".perry" / "config.jsonl").write_text(
            store_text(STORE_SETTINGS + STORE_TRACKS), encoding="utf-8")
        (d / "from-the-store").mkdir()
        return d

    def broken(self, doc_scaffold):
        return M.Doc("config", pathlib.Path(".perry") / "config.md",
                     pathlib.Path(".perry") / "config.jsonl", M.scan_config,
                     under_state_root=False, scaffold=doc_scaffold)

    def test_a_scaffold_that_drops_a_record_refuses(self):
        d = self.project()
        doc = self.broken(lambda records: M.scaffold_config(
            [r for r in records if r.get("track") != "intake"]))
        rc = M.main(doc, ["render", "--write", "--root", str(d)])
        self.assertEqual(rc, 2)
        self.assertFalse((d / ".perry" / "config.md").exists())

    def test_a_scaffold_whose_bytes_do_not_round_trip_refuses(self):
        """A table written with its columns swapped.

        The scanner maps cells by header name, so the renderer puts each stored
        value back under its own column and the bytes move. Nothing else in the
        tool notices; this check does.
        """
        d = self.project()

        def swapped(records):
            text = M.scaffold_config(records)
            return text.replace("| Track | Mode |", "| Mode | Track |")

        rc = M.main(self.broken(swapped), ["render", "--write", "--root",
                                           str(d)])
        self.assertEqual(rc, 2)
        self.assertFalse((d / ".perry" / "config.md").exists())

    def test_a_setting_record_with_no_label_refuses(self):
        """The label IS the line, and `setting_key` is a lossy squash of it.

        `PMO repo path` and `pmo repo path` mint the same key, so rebuilding a
        label from a key would guess at the user's own capitalisation.
        """
        d = self.project()
        store = d / ".perry" / "config.jsonl"
        store.write_text(store.read_text(encoding="utf-8").replace(
            '"label": "Repo layout"', '"label": ""'), encoding="utf-8")
        out = run_config("render", "--write", root=d)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse((d / ".perry" / "config.md").exists())

    def test_a_store_with_no_track_record_writes_no_tracks_section(self):
        """DESIGN-003 reads an absent `## Tracks` as one implicit `main`.

        An empty table would state something the store does not.
        """
        text = M.scaffold_config(STORE_SETTINGS)
        self.assertNotIn("## Tracks", text)
        self.assertIn("- Repo layout: single", text)


class TestTheProseHasADeclaredHome(unittest.TestCase):
    """Deliverable 3, and the reason the byte comparison above can be exact.

    `.perry/config.md` carried 29 lines the store has no field for. They are in
    `.perry/hook.md § Configuration notes` now — tier 1, read at every standup,
    and rendered from nothing, so a render cannot destroy them and a deletion
    cannot lose them. `reference/config.md` states the general rule.
    """

    #: One sentence from each of the two relocated sections. Long enough to be
    #: unambiguous, short enough to survive a reflow.
    MOVED = ("carries the work that ARRIVES",
             "would make Perry claim")

    def test_the_relocated_prose_is_in_the_hook(self):
        hook = (ROOT / ".perry" / "hook.md").read_text(encoding="utf-8")
        for sentence in self.MOVED:
            self.assertIn(sentence, hook)

    def test_it_is_not_still_in_the_projection_as_well(self):
        """One place per fact (DESIGN-013 § 5.1), applied to the prose too.

        Left in both, the copy in `.perry/config.md` is the one a render
        deletes, and a reader would then have two versions of the same
        explanation with no way to tell which was current.
        """
        cfg = (ROOT / ".perry" / "config.md").read_text(encoding="utf-8")
        for sentence in self.MOVED:
            self.assertNotIn(sentence, cfg)

    def test_the_general_rule_names_the_home(self):
        ref = (ROOT / "reference" / "config.md").read_text(encoding="utf-8")
        self.assertIn("Prose in this file is layout", ref)
        self.assertIn(".perry/hook.md", ref)

    def test_perrys_own_config_round_trips(self):
        """The consequence, asserted on this repo's real file.

        With the prose moved out, `.perry/config.md` is exactly what the store
        renders — so a deletion of it is recoverable in full rather than in
        part. This is the assertion that goes red if prose comes back into the
        file, which is the moment the recovery stops being complete.
        """
        text = (ROOT / ".perry" / "config.md").read_text(encoding="utf-8")
        records, findings = M.validate_records(
            M.load_store(ROOT / ".perry" / "config.jsonl"))
        self.assertEqual(findings, [])
        self.assertEqual(M.scaffold_config(records), text)


if __name__ == "__main__":
    unittest.main()
