"""DESIGN-016 B1 — `perry-state --compact` is a projection, and it carries the vocabulary.

`SKILL.md` step 3 mandated `perry-state --json`. That payload was 186,856
bytes when DESIGN-016 was written and 258,981 five days later, of which
`board.tasks` is 159KB — and the standup reads counts, not rows. The bill this
sits against is 99.1% `cache_read`, so the cost is the payload times every turn
after it.

Two claims, and the second is the one that keeps `--compact` from becoming a
second answer to "what is the state":

- **It carries what the standup and the writers need** — the dashboard's
  numbers, and the project's VOCABULARY: which tracks are declared, what mode
  each is, which stages are legal on it (DESIGN-016 § 1.7). That last read used
  to cost `--section project`, 11,681 bytes, three levels down.
- **Every value in it is the full payload's own.** `perry-state § COMPACT` is
  the projection declared once; `project_compact` walks it and so does this
  module. A field added to the spec is asserted here without editing this file,
  and a field computed rather than projected fails.

Run: python3 tests/parallel -j 4 test_compact_payload
"""

from __future__ import annotations

COVERS = ("bin/perry-state", "SKILL.md", "reference/snapshot.md")

import json
import os
import sys
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(PERRY_HOME / "tests"))
sys.path.insert(0, str(PERRY_HOME / "bin"))

import inproc  # noqa: E402
import lib  # noqa: E402
from task_writer_support import Project  # noqa: E402

STATE = inproc.load("perry-state")


def payloads(root: Path) -> tuple[dict, dict]:
    full = json.loads(inproc.run("perry-state", ["--root", str(root), "--json"]).stdout)
    narrow = json.loads(inproc.run("perry-state", ["--root", str(root), "--compact"]).stdout)
    return full, narrow


class TestItIsAProjectionAndNothingElse(unittest.TestCase):
    """Walk the spec: every value in the narrow payload is the full one's."""

    @classmethod
    def setUpClass(cls):
        cls.p = Project()
        cls.p.run("add", "--title", "a row to count")
        cls.full, cls.narrow = payloads(cls.p.root)

    def _narrow_at(self, key: str):
        cur = self.narrow
        for step in key.split("."):
            self.assertIsInstance(cur, dict, f"{key} is not reachable")
            self.assertIn(step, cur, f"{key} is missing from --compact")
            cur = cur[step]
        return cur

    #: `generated_at` is `datetime.now()` inside each invocation, and this
    #: class makes two — so a run that straddles a second boundary compared two
    #: honest stamps and failed. Measured at about 17 ms apart on an empty
    #: project, which is ~1.7% of runs and worse under eight workers; it fired
    #: once in six suite runs during a V4 review. Excluded here and asserted
    #: for its SHAPE below, which is the claim that can be made about a clock.
    CLOCK = ("generated_at",)

    def test_the_clock_exclusion_holds_exactly_one_name(self):
        """`CLOCK` is the one place this file may skip a declared field, so it
        is bounded here rather than trusted.

        A second name added to it drops that field out of BOTH projection
        walks, silently and with every test still green. A clock is the only
        thing that can honestly be excluded from a value comparison; anything
        else added here is a field going untested, and a round found the
        exclusion mechanism before it found a second name in it.
        """
        self.assertEqual(self.CLOCK, ("generated_at",))

    def test_every_declared_field_matches_the_full_payload(self):
        """The projection is applied to the FULL payload here and compared to
        what the tool emitted.

        **This one cannot see a defect INSIDE `project_value`, and that is on
        purpose now rather than by accident.** It calls the function under
        test to build its own expectation, so it asserts `f(x) == f(x)`: what
        it pins is that the tool RAN the projection over the declared fields,
        not that the projection is right. A V4 reviewer proved the gap by
        adding 1 to every integer `project_value` returns and watching all
        3,440 tests stay green while `--compact` reported a board of 239 lines
        against `--json`'s 238.

        The rule itself is checked by `test_the_six_kinds_are_checked_against_a
        _second_opinion` below, which reimplements the six kinds by hand. The
        split is deliberate: the FIELD LIST stays single-sourced from
        `STATE.COMPACT`, so the two files cannot disagree about which fields
        exist, while the RULE gets an independent second author.
        """
        for key, path, how in STATE.COMPACT:
            if key in self.CLOCK:
                continue
            with self.subTest(field=key):
                self.assertEqual(
                    self._narrow_at(key),
                    STATE.project_value(STATE._at(self.full, path), how))

    @staticmethod
    def _walk(payload, dotted):
        """A dotted-path read this file owns.

        Deliberately not `STATE._at`: the tool walks its source with that, so
        sharing it makes a defect in the walk invisible to every comparison
        built on top of it. Same reasoning as `_second_opinion` one level up.
        """
        cur = payload
        for step in dotted.split("."):
            if not isinstance(cur, dict) or step not in cur:
                return None
            cur = cur[step]
        return None if cur is None else cur

    @staticmethod
    def _second_opinion(value, how):
        """The six projection kinds, written again and deliberately not shared.

        Reimplemented from `DESIGN-016 § 1.7` and the `COMPACT` declaration,
        not from `bin/perry-state § project_value`. If this ever imports that
        function, the test below becomes the tautology it exists to replace.
        """
        if how == "value":
            return value
        if how == "count":
            if isinstance(value, list):
                return len(value)
            if isinstance(value, dict):
                return len(value)
            return None
        kind, arg = how
        if kind == "fields":
            if not isinstance(value, list):
                return None
            out = []
            for item in value:
                if isinstance(item, dict):
                    out.append({name: item.get(name) for name in arg})
            return out
        if kind in ("objectives", "objectives_with_progress"):
            if not isinstance(value, list):
                return None
            out = []
            for o in value:
                if not isinstance(o, dict):
                    continue
                row = {"title": o.get("title")}
                if kind == "objectives_with_progress":
                    row = {"id": o.get("id"), "title": o.get("title")}
                krs = o.get("krs")
                row["krs"] = [{name: kr.get(name) for name in arg}
                              for kr in (krs if krs else [])]
                out.append(row)
            return out
        if kind == "fields_of_dict":
            if not isinstance(value, dict):
                return None
            return {name: value.get(name) for name in arg}
        if kind == "subdict":
            if not isinstance(value, dict):
                return None
            # `_walk`, not `STATE._at`. The tool resolves its source with `_at`
            # and this file used to resolve its EXPECTATION with the same
            # function, so a defect inside it moved both sides together —
            # reversing every list `_at` returns was green on the full suite
            # while `--compact` listed the phase objectives in the opposite
            # order to `--json`. A round found that; this is the second walker.
            return {k: TestItIsAProjectionAndNothingElse._second_opinion(
                TestItIsAProjectionAndNothingElse._walk(value, path), sub)
                for k, path, sub in arg}
        raise ValueError(f"unknown projection {how!r}")

    def test_the_six_kinds_are_checked_against_a_second_opinion(self):
        """Every declared field, projected by a body this file owns.

        The population is `STATE.COMPACT`, and every one of its `how` values
        must be reachable here — an unknown kind raises rather than passing,
        so a seventh projection added to the tool fails this until somebody
        writes it down twice.
        """
        for key, path, how in STATE.COMPACT:
            if key in self.CLOCK:
                continue
            with self.subTest(field=key):
                want = self._second_opinion(STATE._at(self.full, path), how)
                self.assertEqual(self._narrow_at(key), want)

    #: The five fields whose `--compact` key is NOT its source path, written
    #: out here rather than read from the declaration. Everything else in
    #: `COMPACT` is an identity pair, so anchoring on the key is the same
    #: question as anchoring on the path — until someone repoints one.
    RENAMED = {
        "project.tracks": "project.config.tracks",
        "project.tracks_source": "project.config.tracks_source",
        "project.packs": "project.config.packs",
        "project.state_root": "project.config.state_root",
        "project.language": "project.config.language",
    }

    def test_every_field_reads_the_source_its_key_names(self):
        """The third way this criterion was self-checked, and the last one.

        Round 4 found the RULE was verified with the function under test.
        Round 5 found the DATA could not tell a correct projection from one
        that keeps only the first of anything. Round 6 found the (key, path)
        PAIRING: every walk in this file resolved its expectation through the
        very `path` field it was meant to be checking, so the declaration was
        both question and answer.

        **46 of the 53 declared pairs could be repointed at another declared
        path with the full suite still green.** The worst one is the spec's own
        harm sentence: repointing `linkage.objectives` at `phase.objectives`
        makes `--compact` report `current: null, target: null` for all three key
        results of `tests/fixtures/sample-project` while `--json` in the same
        process reports `current: 1.0, target: 3.0`, and
        `reference/snapshot.md` step 4 renders the percentage from exactly that
        list.

        The fix is to anchor BOTH sides on the key — which one field,
        `generated_at`, already did, and which is why it was one of the seven
        that reddened. For the five renames, this file writes the mapping down
        itself, so a sixth rename fails here until someone records it.
        """
        for key, path, how in STATE.COMPACT:
            if key in self.CLOCK:
                continue
            with self.subTest(field=key):
                source = self.RENAMED.get(key, key)
                self.assertEqual(source, path,
                                 f"{key} reads {path}, and this file expects "
                                 f"{source} — one of them is wrong, and a "
                                 f"rename belongs in RENAMED")
                self.assertEqual(
                    self._narrow_at(key),
                    self._second_opinion(STATE._at(self.full, source), how))

    def test_every_subdict_child_reads_the_source_its_key_names(self):
        """The same key-anchoring, one level down, where nothing reached.

        `COMPACT` holds one `subdict` entry — `phase` — whose `arg` carries ten
        more `(key, path, how)` triples. **Every walk in this file iterates
        `STATE.COMPACT`, which is top level only**, and the undeclared-key case
        stops descending the moment a key is declared, which `phase` is. So the
        ten were declared and compared by nothing.

        A round rotated all ten at once — each key reading its neighbour's
        field — and the full suite stayed at its known reds while `--compact`
        reported `phase.number` as the slug, `slug` as the status, `day` as the
        KR total. `reference/snapshot.md:165` renders
        `Current phase #<NNN> <slug> · day <N>` from exactly those three.
        """
        seen = 0
        for key, path, how in STATE.COMPACT:
            if not (isinstance(how, tuple) and how[0] == "subdict"):
                continue
            source = self._walk(self.full, path)
            for inner_key, inner_path, inner_how in how[1]:
                with self.subTest(field=f"{key}.{inner_key}"):
                    self.assertEqual(
                        inner_key, inner_path,
                        f"{key}.{inner_key} reads {inner_path}; a rename here "
                        f"needs recording the way RENAMED does one level up")
                    self.assertEqual(
                        self._walk(self.narrow, f"{key}.{inner_key}"),
                        self._second_opinion(
                            self._walk(source, inner_path), inner_how))
                seen += 1
        self.assertGreaterEqual(seen, 10, "the subdict children went unchecked")

    def test_every_declared_field_name_is_one_the_source_carries(self):
        """The `arg` name tuples, which are a second copy of a source's shape.

        Eleven names can be dropped from those tuples with the full suite
        green — `wip`, `sla`, `cycle`, `default_rung`, `declared` on
        `project.tracks`; `linked` and `stretch` at the two `objectives` sites;
        `checked`, `drift`, `unrecorded` on `board.drift`; and the inner
        `objectives` arg. A dropped name announces itself to whoever reads the
        payload, which is why a round graded it ROW rather than FAIL — but
        nothing pins the list, so it can shrink by accident as easily as on
        purpose.

        This does not assert WHICH names are declared. It asserts that every
        one of them is a key the source actually carries, so a name that stops
        existing fails here instead of quietly narrowing the payload.
        """
        def names_of(how):
            if isinstance(how, tuple) and how[0] in (
                    "fields", "fields_of_dict", "objectives",
                    "objectives_with_progress"):
                return list(how[1])
            return []

        checked = 0
        for key, path, how in STATE.COMPACT:
            source = self._walk(self.full, path)
            if source is None:
                continue
            for name in names_of(how):
                rows = (source if isinstance(source, list) else [source])
                # `objectives` name tuples describe the KRs, not the objective.
                if isinstance(how, tuple) and how[0].startswith("objectives"):
                    rows = [kr for o in rows if isinstance(o, dict)
                            for kr in (o.get("krs") or [])]
                rows = [r for r in rows if isinstance(r, dict)]
                if not rows:
                    continue
                with self.subTest(field=key, name=name):
                    self.assertTrue(
                        any(name in r for r in rows),
                        f"{key} declares {name!r} and no record under {path} "
                        f"carries it")
                checked += 1
        self.assertGreater(checked, 5, "no declared name was reachable")

    #: **What each field IS, stated a second time.** A `COMPACT` entry is a
    #: TRIPLE — `(key, path, how)` — and rounds 4 to 7 pinned the rule, the
    #: data, and the `(key, path)` pairing at both levels. `how` was pinned by
    #: nothing: every expectation in this file applies the same `how` it is
    #: meant to be checking, so rewriting one moved both sides together.
    #:
    #: A round enumerated it rather than sampling: **45 of the 53 top-level
    #: entries accepted a rewritten projection kind with the suite green**, and
    #: the 8 that reddened were each caught by a hand-written case, never by a
    #: walk. The sharpest was `installed`: as a `count` it publishes `null`,
    #: `null` is falsy, and `SKILL.md:132` routes every `/perry` on a real
    #: project into first-time setup on exactly that value.
    #:
    #: So this is the same shape as `RENAMED` and `NAMES` one level over —
    #: a second author saying what the declaration means, so the declaration
    #: stops being both question and answer.
    KINDS = {
        "schema": "value",
        "generated_at": "value",
        "installed": "value",
        "recovery": "value",
        "interrupted": "count",
        "project.root": "value",
        "project.name": "value",
        "project.tracks": "fields",
        "project.tracks_source": "value",
        "project.packs": "value",
        "project.state_root": "value",
        "project.language": "value",
        "okr.present": "value",
        "okr.version": "value",
        "okr.objectives": "objectives",
        "okr.anti_goals": "value",
        "okr.operating_principles": "value",
        "phase": "subdict",
        "linkage.phase": "value",
        "linkage.objectives": "objectives_with_progress",
        "linkage.unlinked": "count",
        "attribution.kr_currents": "value",
        "board.lines": "value",
        "board.cap": "value",
        "board.last_updated": "value",
        "board.p0": "value",
        "board.p1": "value",
        "board.p2": "value",
        "board.cadence": "value",
        "board.blocked": "value",
        "board.open": "value",
        "board.verification": "value",
        "board.drift": "fields_of_dict",
        "board.tasks": "count",
        "intake": "value",
        "user_input_queue": "value",
        "cadence": "value",
        "risks.top": "value",
        "risks.count": "value",
        "risks.cleared": "value",
        "attribution.linked": "value",
        "attribution.unlinked": "count",
        "attribution.declared_unlinked": "count",
        "decisions": "value",
        "design.total": "value",
        "design.locked": "value",
        "design.by_status": "value",
        "design.pending_handoff": "count",
        "history": "value",
        "operations": "value",
        "architecture": "value",
        "roles": "value",
        "warnings": "value",
        # the eleven `phase` children
        "phase.number": "value",
        "phase.slug": "value",
        "phase.status": "value",
        "phase.started": "value",
        "phase.day": "value",
        "phase.kr_total": "value",
        # TASK-264 D3 repair (F1): the withdrawn KRs `kr_total` leaves out.
        "phase.kr_withdrawn": "value",
        "phase.focus_present": "value",
        "phase.cost_ceiling": "value",
        "phase.objectives": "objectives",
        "phase.scope_triggers": "count",
    }

    def test_every_field_is_projected_by_the_kind_this_file_expects(self):
        """The third element of the triple, pinned at both levels."""
        seen = set()
        for key, _path, how in STATE.COMPACT:
            with self.subTest(field=key):
                self.assertIn(key, self.KINDS,
                              f"{key} is declared and this file does not say "
                              f"what it is")
                self.assertEqual(
                    how if isinstance(how, str) else how[0], self.KINDS[key])
            seen.add(key)
            if isinstance(how, tuple) and how[0] == "subdict":
                for ik, _ip, ih in how[1]:
                    name = f"{key}.{ik}"
                    with self.subTest(field=name):
                        self.assertIn(name, self.KINDS, f"{name} is declared "
                                      f"and this file does not say what it is")
                        self.assertEqual(
                            ih if isinstance(ih, str) else ih[0],
                            self.KINDS[name])
                    seen.add(name)
        self.assertEqual(
            sorted(set(self.KINDS) - seen), [],
            "this file names a field the declaration no longer carries")

    def test_the_rename_list_is_exactly_the_pairs_that_differ(self):
        """The bound, both ways.

        An entry here for a field that does not differ would let a repointing
        hide behind the rename list; a field that differs and is absent would
        fail the case above with a message that reads like a defect in the
        tool. Five today.
        """
        differ = {k: p for k, p, _h in STATE.COMPACT if k != p}
        self.assertEqual(differ, self.RENAMED)

    def test_the_clock_field_is_projected_like_everything_else(self):
        """**One invocation, so the clock is deterministic.**

        The first fix for the flake excluded `generated_at` from the walk and
        left a case whose body called `datetime.fromisoformat` and asserted
        NOTHING — a hard-coded `"2020-01-01T00:00:00"` would have passed it,
        and `--compact`'s stamp stopped being compared with `--json`'s at all.
        A V4 review found that. The flake came from making two invocations;
        projecting the full payload in-process makes one.
        """
        from datetime import datetime
        projected = STATE.project_compact(self.full)
        self.assertEqual(projected["generated_at"], self.full["generated_at"],
                         "the projection did not carry the stamp verbatim")
        datetime.fromisoformat(self.narrow["generated_at"])
        self.assertNotEqual(self.narrow["generated_at"], "",
                            "the tool emitted an empty stamp")

    def test_a_scalar_is_carried_verbatim_and_a_list_is_counted(self):
        """The control: the case above passes if `project_value` is the
        identity, so at least one field of each kind is checked by hand."""
        self.assertEqual(self.narrow["project"]["name"],
                         self.full["project"]["name"])
        self.assertEqual(self.narrow["board"]["tasks"],
                         len(self.full["board"]["tasks"]))
        self.assertNotEqual(self.narrow["board"]["tasks"],
                            self.full["board"]["tasks"])

    def test_the_spec_reaches_something_in_a_real_payload(self):
        """The control: a spec of paths that all resolve to `None` would pass
        every case above and say nothing."""
        live = [k for k, path, _ in STATE.COMPACT
                if STATE._at(self.full, path) is not None]
        # **A floor, not a half.** `> len(COMPACT) // 2` let up to 22 of the
        # 53 declared paths start resolving to None — a key renamed in
        # `build()` — with both walks still agreeing, because both fetch the
        # source with `STATE._at(self.full, path)` and both would get None.
        # 48 resolve on this fixture; the 5 that do not are the phase and
        # linkage paths a scratch project has no data for, and they are named
        # so a sixth cannot join them quietly.
        self.assertGreaterEqual(len(live), 48,
                                "declared paths stopped resolving")
        dark = {k for k, path, _h in STATE.COMPACT
                if STATE._at(self.full, path) is None}
        self.assertEqual(
            dark, {"phase", "linkage.phase", "linkage.objectives",
                   "linkage.unlinked", "risks.top"},
            "a declared path resolved to nothing on a fresh project, and this "
            "file's synthetic cases are the only evidence for its kind")

    def test_it_holds_no_key_the_spec_did_not_declare(self):
        """Every path, not just the top-level name.

        This compared `k.split(".")[0]`, so a key emitted under `board.`,
        `project.` or `risks.` that the declaration never names was invisible:
        the parent was declared, and the parent was all it looked at.
        """
        def paths(node, prefix=""):
            if not isinstance(node, dict):
                return {prefix}
            out = set()
            for k, v in node.items():
                out |= paths(v, f"{prefix}.{k}" if prefix else k)
            return out

        declared = {k for k, _p, _h in STATE.COMPACT}
        # A declared key whose value is itself a dict — `subdict`, or a scalar
        # that happens to be an object — owns everything under it; the walk
        # stops there rather than descending into data the spec did not shape.
        emitted = set()
        for key in self.narrow:
            if key in declared:
                emitted.add(key)
                continue
            emitted |= {p for p in paths(self.narrow[key], key)}
        undeclared = {p for p in emitted
                      if p not in declared
                      and not any(p.startswith(d + ".") for d in declared)}
        self.assertEqual(undeclared, set(),
                         "--compact emits a key the declaration does not name")


class TestItCarriesTheVocabulary(unittest.TestCase):
    """What a caller needs before writing a row (DESIGN-016 § 1.7)."""

    def setUp(self):
        import config_store
        self.p = Project(tracks=[
            config_store.track("main", "project"),
            config_store.track("intake", "queue",
                               stages="new→triaged→done", wip="6", sla="5d"),
        ])
        _full, self.narrow = payloads(self.p.root)

    def test_every_declared_track_is_named_with_its_mode(self):
        tracks = {t["track"]: t for t in self.narrow["project"]["tracks"]}
        self.assertEqual(set(tracks), {"main", "intake"})
        self.assertEqual(tracks["intake"]["mode"], "queue")

    def test_the_stages_legal_on_a_track_are_in_it(self):
        tracks = {t["track"]: t for t in self.narrow["project"]["tracks"]}
        self.assertEqual(tracks["intake"]["stage_list"],
                         ["new", "triaged", "done"])
        self.assertTrue(tracks["intake"]["stages_declared"])

    def test_every_cell_equals_the_store_up_to_how_a_blank_is_spelled(self):
        """Criterion 13's own sentence, which nothing pinned.

        "those values equal what `.perry/config.jsonl` holds" is true only up
        to one normalisation, and the normalisation is deliberate:
        `perry_md_store § stored_value` writes a declared blank INTO the store
        as `""` because the marker is layout, and `perry-state §
        track_from_record` puts the marker back on the way out so the payload
        reports the bytes the project wrote. Every other difference is a defect.

        Splitting the two is the whole test. A round that read the criterion
        literally would fail the payload for spelling a blank `—`; a test that
        compared nothing would have missed what actually went wrong, which was
        a CONSUMER treating `—` as a value (`cmd_done`, see
        `TestADeclaredBlankRungIsNotARung` in `test_task_writer_core.py`).
        """
        store = {r["track"]: r for r in
                 (json.loads(line) for line in
                  (self.p.root / ".perry" / "config.jsonl").read_text().splitlines())
                 if r.get("kind") == "track"}
        fields = ("mode", "spine", "stages", "wip", "sla", "cycle", "default_rung")
        blanks_seen = 0
        for shown in self.narrow["project"]["tracks"]:
            record = store[shown["track"]]
            for field in fields:
                if field not in shown:
                    continue
                stored, published = str(record.get(field, "")), str(shown[field])
                if stored == published:
                    continue
                where = f"{shown['track']}.{field}"
                self.assertTrue(
                    lib.is_blank_cell(stored) and lib.is_blank_cell(published),
                    f"{where}: the store holds {stored!r} and --compact "
                    f"publishes {published!r}, and they are not two spellings "
                    f"of nothing")
                blanks_seen += 1
        # Two separate things, because the loop above passes vacuously
        # without both: the fixture has to CONTAIN a declared blank, and the
        # payload has to have spelled it differently. Collapsing them into one
        # count made a payload that stopped putting the marker back fail with
        # "the fixture has no blank", which is not what went wrong.
        declared_blanks = sum(1 for record in store.values() for field in fields
                              if lib.is_blank_cell(str(record.get(field, ""))))
        self.assertTrue(declared_blanks,
                        "this fixture declares no blank track cell, so the "
                        "tolerance above was never exercised")
        self.assertTrue(blanks_seen,
                        f"{declared_blanks} track cells are blank in the store "
                        f"and --compact published every one of them "
                        f"unchanged: `track_from_record` has stopped putting "
                        f"the blank marker back, which moves the payload")

    def test_the_diagnosis_of_a_track_is_not_in_it(self):
        """`stage_counts` and the breach lists belong to `--section project`;
        this payload is the vocabulary, not the verdict."""
        for track in self.narrow["project"]["tracks"]:
            self.assertNotIn("sla_check", track)
            self.assertNotIn("wip_breaches", track)


class TestTheStandupCanActuallyRenderFromIt(unittest.TestCase):
    """Completeness, named by hand — the other direction from the projection
    test above, and the one that was missing.

    Every case in this module walks `COMPACT`, so deleting an entry deletes its
    own assertion: a V4 review dropped `project.packs` from the spec and the
    whole suite stayed green, and that is the structural reason `linkage` — the
    only machine-readable KR progress, which `reference/snapshot.md` step 4
    renders a percentage from — was missing from the first `--compact` and
    nothing said so. This list is written out, so removing a field from the
    spec reddens here.
    """

    @classmethod
    def setUpClass(cls):
        cls.p = Project()
        cls.p.run("add", "--title", "a row for the dashboard to count")
        _full, cls.narrow = payloads(cls.p.root)

    #: `(dotted path, which step of `reference/snapshot.md` reads it)`.
    #: The field names each projection picks out, written here so a shrinking
    #: `arg` tuple fails instead of quietly narrowing the payload. `NEEDED`
    #: below does this for the top-level keys; these are the names one level
    #: in, and a round measured eleven of them droppable with the full suite
    #: green. Dropping one is visible to whoever reads the payload, which is
    #: why it was graded a row and not a defect — but nothing pinned the list,
    #: so it could shrink by accident as easily as on purpose.
    NAMES = {
        "project.tracks": ("track", "mode", "stage_list", "stages_declared",
                           "wip", "sla", "cycle", "default_rung", "declared"),
        "board.drift": ("checked", "drift", "unrecorded"),
        # `status` on all three KR lists: TASK-264 D3 repair (F1) — a
        # withdrawn KR stays listed and the standup must be able to tell.
        "okr.objectives": ("id", "linked", "stretch", "status"),
        "linkage.objectives": ("id", "title", "current", "target", "stretch",
                               "status"),
        # the one `subdict` child that carries names of its own
        "phase.objectives": ("id", "linked", "stretch", "status"),
    }

    def test_each_projection_still_picks_out_the_names_it_is_meant_to(self):
        """All FIVE name-carrying sites, not the two this started with.

        A round measured the gap rather than assuming it closed: dropping
        `linked` from `okr.objectives` and from the inner `phase.objectives`
        was green across seventeen modules, because this list covered
        `project.tracks` and `board.drift` and nothing else.
        """
        by_key = {}
        for key, _p, how in STATE.COMPACT:
            by_key[key] = how
            if isinstance(how, tuple) and how[0] == "subdict":
                for ik, _ip, ih in how[1]:
                    by_key[f"{key}.{ik}"] = ih
        for key, want in self.NAMES.items():
            with self.subTest(field=key):
                how = by_key.get(key)
                self.assertIsNotNone(how, f"{key} left the declaration")
                self.assertEqual(tuple(how[1]), want)
        # Every site that carries names is named here, so a sixth cannot
        # appear unpinned the way two of these five did.
        # `subdict`'s second element is TRIPLES, not names — it is covered by
        # KINDS and by the subdict walks, not here.
        carries = {k for k, h in by_key.items()
                   if isinstance(h, tuple) and h[0] != "subdict"
                   and len(h) > 1 and isinstance(h[1], tuple)}
        self.assertEqual(sorted(carries - set(self.NAMES)), [])

    NEEDED = (
        ("project.name", "step 4, the header"),
        ("project.tracks", "step 3b, one mode file per distinct mode"),
        ("project.packs", "step 3c, the display glossary"),
        ("okr.present", "step 4, the OKR line"),
        ("okr.version", "step 4, the OKR line"),
        ("okr.objectives", "step 4, one line per objective"),
        ("linkage.objectives", "step 4, <%> and <KRs done>/<KRs total>"),
        ("phase", "step 4, the phase line"),
        ("board.p0", "step 4, open tasks"),
        ("board.p1", "step 4, open tasks"),
        ("board.p2", "step 4, open tasks"),
        ("board.blocked", "step 4, open tasks"),
        ("user_input_queue", "step 4, the User Input Q line"),
        ("risks.top", "step 4, the top risk"),
        ("decisions", "step 4, the last decision"),
        ("history", "step 4, last weekly and last handoff"),
        ("installed", "step 3, the first-time-setup branch"),
        ("recovery", "step 2, the recovery hazard"),
        ("interrupted", "step 2, the interrupted-run gate"),
    )

    def _at(self, path: str):
        cur = self.narrow
        for step in path.split("."):
            self.assertIsInstance(cur, dict, f"{path}: {step} is not reachable")
            self.assertIn(step, cur, f"{path} is missing from --compact")
            cur = cur[step]
        return cur

    def test_every_field_the_standup_reads_is_present(self):
        for path, why in self.NEEDED:
            with self.subTest(field=path, read_by=why):
                self._at(path)

    def test_a_kr_carries_a_number_to_render_a_percentage_from(self):
        """`linkage.objectives[].krs[]` must carry `current` and `target`;
        `attribution.kr_currents` is a roll-up over the phase and cannot answer
        per objective."""
        objectives = self.narrow["linkage"]["objectives"]
        # **No skip.** This used to `skipTest` when the fixture had no phase
        # KRs, and its only fixture was a scratch `Project()`, which never has
        # any — so the one case asserting that `current` and `target` reach
        # `--compact` had NEVER EXECUTED. A V4 round found it skipping.
        # `TestTheFullFixtureReachesTheDarkPaths` below runs the same claim
        # against `tests/fixtures/sample-project`, which does declare them.
        self.assertIn(objectives, ([], None),
                      "a scratch project grew phase KRs; this case is now the "
                      "wrong place to assert about them, and the fixture-backed "
                      "class below is the right one")


class TestItIsSmallerByTheOrderOfMagnitudeThatWasThePoint(unittest.TestCase):

    def setUp(self):
        self.p = Project()
        for n in range(12):
            self.p.run("add", "--title", f"a row that makes the board big {n}")
        self.full_text = inproc.run(
            "perry-state", ["--root", str(self.p.root), "--json"]).stdout
        self.narrow_text = inproc.run(
            "perry-state", ["--root", str(self.p.root), "--compact"]).stdout

    def test_it_is_a_small_fraction_of_the_full_payload(self):
        self.assertLess(len(self.narrow_text), len(self.full_text) / 3,
                        f"compact {len(self.narrow_text)} vs full "
                        f"{len(self.full_text)} bytes")

    def test_it_does_not_grow_with_the_board(self):
        """The property that makes it a standup read: task ROWS are counted,
        not carried, so twelve more of them cost one integer."""
        before = len(self.narrow_text)
        for n in range(12):
            self.p.run("add", "--title", f"another row on the same board {n}")
        after = len(inproc.run(
            "perry-state", ["--root", str(self.p.root), "--compact"]).stdout)
        self.assertLess(after - before, 200,
                        f"twelve rows added {after - before} bytes")

    def test_the_row_count_is_still_reported(self):
        """The control for the case above: counted, not dropped."""
        narrow = json.loads(self.narrow_text)
        self.assertEqual(narrow["board"]["tasks"],
                         len(json.loads(self.full_text)["board"]["tasks"]))


class TestTheTwoNarrowingsDoNotCombine(unittest.TestCase):

    def test_compact_with_section_is_refused(self):
        p = Project()
        out = inproc.run("perry-state",
                         ["--root", str(p.root), "--compact", "--section", "board"])
        self.assertEqual(out.returncode, 2, out.stdout)
        self.assertIn("--compact", out.stderr)


class TestAProjectWithNoStateStillAnswers(unittest.TestCase):

    def test_installed_false_survives_the_projection(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = inproc.run("perry-state", ["--root", td, "--compact"])
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertFalse(json.loads(out.stdout)["installed"])


class TestEveryProjectionKindIsFedDataThatDistinguishesIt(unittest.TestCase):
    """The rule itself, on synthetic values, independent of any project.

    **Why this is not redundant with the class above.** That one runs against
    `Project()` — a scratch project with no phase and no linkage — so three of
    the declared kinds (`objectives_with_progress`, `objectives`, `subdict`)
    receive `None` or an empty list and every implementation of them agrees.
    A V4 reviewer made `objectives_with_progress` put each KR's `target` into
    its `current` slot, watched the live project report a key result at 100%
    that is actually at 43%, and watched all 3,440 tests stay green. The
    projection was not untested; it was tested on data that could not tell.

    So each kind is fed a value built to distinguish it: counts get a list
    whose length differs from its contents, field-pickers get an extra key
    that must be dropped, and `current`/`target` are given DIFFERENT numbers,
    which is the exact discrimination the live board happened not to make in
    five of its six key results.
    """

    #: One synthetic input per kind, and what a correct projection returns.
    #: Written from the declaration, not from `project_value`.
    #:
    #: **Every collection here holds MORE THAN ONE element, and that is the
    #: point.** The first version of this dict gave each kind one objective,
    #: one key result and two scalar `subdict` children. A V4 round appended
    #: `[:1]` to the KR comprehension and to the objective comprehension and
    #: the whole suite stayed green — `--compact` reported ONE key result per
    #: phase objective where `--json` reported two on
    #: `tests/fixtures/sample-project` and three on this project, and
    #: `reference/snapshot.md` step 4 renders `<KRs done>/<KRs total>` from
    #: exactly that list. A projection tested at cardinality one cannot tell a
    #: correct implementation from one that keeps only the first of anything,
    #: which is the same defect the class above was written to fix, one level
    #: up: the rule had a second author and the data could not tell.
    CASES = {
        "value": (7, 7),
        "count": ([10, 20, 30], 3),
        ("fields", ("a", "b")): (
            [{"a": 1, "b": 2, "drop": 3}, {"a": 4, "b": 5, "drop": 6}],
            [{"a": 1, "b": 2}, {"a": 4, "b": 5}]),
        ("fields_of_dict", ("a", "b")): (
            {"a": 1, "b": 2, "drop": 3}, {"a": 1, "b": 2}),
        ("objectives", ("id", "current", "target")): (
            [{"title": "T1", "drop": "x",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0, "drop": "x"},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}],
            [{"title": "T1",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}]),
        ("objectives_with_progress", ("id", "current", "target")): (
            [{"id": "O1", "title": "T1", "drop": "x",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0, "drop": "x"},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"id": "O2", "title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}],
            [{"id": "O1", "title": "T1",
              "krs": [{"id": "K1", "current": 1.0, "target": 9.0},
                      {"id": "K2", "current": 2.0, "target": 8.0}]},
             {"id": "O2", "title": "T2",
              "krs": [{"id": "K3", "current": 3.0, "target": 7.0}]}]),
    }

    def test_each_kind_maps_its_input_to_the_declared_output(self):
        for how, (given, want) in self.CASES.items():
            with self.subTest(kind=how if isinstance(how, str) else how[0]):
                self.assertEqual(STATE.project_value(given, how), want)
                self.assertEqual(
                    TestItIsAProjectionAndNothingElse._second_opinion(
                        given, how), want)

    def test_no_collection_in_the_cases_has_one_element(self):
        """The anti-vacuity control for the control.

        Without this, the fix for a cardinality finding is to add a second
        element once and let the next author drop it back. Every list-shaped
        input above must hold at least two, and at least one nested list must
        too, or the cases stop being able to see a projection that keeps only
        the first of anything.
        """
        nested = 0
        for how, (given, _) in self.CASES.items():
            if not isinstance(given, list):
                continue
            with self.subTest(kind=how if isinstance(how, str) else how[0]):
                self.assertGreaterEqual(len(given), 2, "one element cannot tell")
            for item in given:
                if isinstance(item, dict) and len(item.get("krs", ())) >= 2:
                    nested += 1
        self.assertGreaterEqual(
            nested, 2, "no case nests a collection of two, so a projection "
                       "that keeps only the first KR would pass")

    def test_the_nested_kind_carries_its_children(self):
        """`subdict`, with a COMPOSITE child.

        Both children used to be scalar kinds, so a `subdict` that stopped
        projecting its children and carried them verbatim was green: a scalar
        projected is a scalar carried. The `krs` child below is the whole point
        — it must come back narrowed, and it cannot if the recursion is gone.
        """
        how = ("subdict", (("n", "inner.n", "value"),
                           ("c", "inner.items", "count"),
                           ("o", "inner.objs",
                            ("objectives", ("id", "current")))))
        given = {"inner": {"n": 4, "items": ["a", "b"],
                           "objs": [{"title": "T", "drop": "x",
                                     "krs": [{"id": "K1", "current": 1.0,
                                              "drop": "x"},
                                             {"id": "K2", "current": 2.0}]}]}}
        want = {"n": 4, "c": 2,
                "o": [{"title": "T", "krs": [{"id": "K1", "current": 1.0},
                                             {"id": "K2", "current": 2.0}]}]}
        self.assertEqual(STATE.project_value(given, how), want)
        self.assertEqual(
            TestItIsAProjectionAndNothingElse._second_opinion(given, how),
            want)

    def test_every_kind_the_declaration_uses_has_a_case_here(self):
        """The bound. A seventh projection fails this until it is written twice."""
        declared = {h if isinstance(h, str) else h[0] for _, _, h in STATE.COMPACT}
        covered = {h if isinstance(h, str) else h[0] for h in self.CASES}
        covered.add("subdict")
        self.assertEqual(declared - covered, set(),
                         "a projection kind reached the tool and not this file")

    def test_a_wrong_projection_is_visible_here(self):
        """The anti-vacuity control: the cases can tell right from wrong.

        Each assertion above would pass against an identity function if the
        inputs and outputs were equal. They are not, and this says so —
        except for `value`, which IS the identity and is the one kind whose
        input must equal its output.
        """
        for how, (given, want) in self.CASES.items():
            if how == "value":
                self.assertEqual(given, want, "`value` is the identity")
                continue
            with self.subTest(kind=how if isinstance(how, str) else how[0]):
                self.assertNotEqual(given, want)



class TestTheFullFixtureReachesTheDarkPaths(unittest.TestCase):
    """`--compact` against the one fixture that has a phase.

    **Five of the 53 declared paths resolve to `None` on a scratch
    `Project()`** — `phase`, `linkage.phase`, `linkage.objectives`,
    `linkage.unlinked`, `risks.top` — and those five are the only route to
    three of the six projection kinds. `tests/fixtures/sample-project` reaches
    all five, is used by fifteen other modules, and until now **no test ran
    `--compact` against it**. That is why a round could repoint
    `linkage.objectives` at `phase.objectives` and watch the whole suite stay
    green while every key result reported `current: null`.

    Read-only: the fixture is shipped state and this module must not write to
    it. `--json` and `--compact` both only read.
    """

    @classmethod
    def setUpClass(cls):
        cls.root = PERRY_HOME / "tests" / "fixtures" / "sample-project"
        cls.full = json.loads(inproc.run(
            "perry-state", ["--root", str(cls.root), "--json"]).stdout)
        cls.narrow = json.loads(inproc.run(
            "perry-state", ["--root", str(cls.root), "--compact"]).stdout)

    def _at(self, payload, dotted):
        cur = payload
        for step in dotted.split("."):
            self.assertIsInstance(cur, dict, f"{dotted} is not reachable")
            self.assertIn(step, cur, f"{dotted} is missing")
            cur = cur[step]
        return cur

    DARK = ("phase", "linkage.phase", "linkage.objectives",
            "linkage.unlinked", "risks.top")

    def test_the_five_paths_a_scratch_project_cannot_reach_are_populated(self):
        """The control. If the fixture stops declaring a phase, every case
        below passes vacuously and this is what says so."""
        for path in self.DARK:
            with self.subTest(path=path):
                self.assertIsNotNone(self._at(self.full, path),
                                     "the fixture stopped populating this")
        self.assertGreaterEqual(len(self.narrow["linkage"]["objectives"]), 2)

    def test_every_field_reads_the_source_its_key_names_here_too(self):
        """The key-anchored comparison, on the payload that has the data.

        The identical case in `TestItIsAProjectionAndNothingElse` runs on a
        scratch project, where five paths are `None` and any two of them agree.
        """
        renamed = TestItIsAProjectionAndNothingElse.RENAMED
        second = TestItIsAProjectionAndNothingElse._second_opinion
        for key, path, how in STATE.COMPACT:
            if key in TestItIsAProjectionAndNothingElse.CLOCK:
                continue
            with self.subTest(field=key):
                source = renamed.get(key, key)
                self.assertEqual(source, path)
                self.assertEqual(self._at(self.narrow, key),
                                 second(STATE._at(self.full, source), how))

    def test_every_subdict_child_reads_its_own_source_on_real_data(self):
        """The subdict comparison where `phase` is not `None`.

        The identical case in `TestItIsAProjectionAndNothingElse` runs on a
        scratch project, where `phase` resolves to nothing and every
        implementation of a phase agrees. This fixture has one.
        """
        P = TestItIsAProjectionAndNothingElse
        seen = 0
        for key, path, how in STATE.COMPACT:
            if not (isinstance(how, tuple) and how[0] == "subdict"):
                continue
            source = P._walk(self.full, path)
            self.assertIsNotNone(source, f"{key} is empty on this fixture")
            for inner_key, inner_path, inner_how in how[1]:
                with self.subTest(field=f"{key}.{inner_key}"):
                    self.assertEqual(inner_key, inner_path)
                    self.assertEqual(
                        P._walk(self.narrow, f"{key}.{inner_key}"),
                        P._second_opinion(
                            P._walk(source, inner_path), inner_how))
                seen += 1
        self.assertGreaterEqual(seen, 10)

    def test_a_key_result_carries_the_numbers_the_percentage_is_rendered_from(self):
        """`reference/snapshot.md` step 4 renders `<%>` from these.

        The case this replaces skipped on its only fixture and had never run.
        """
        objectives = self.narrow["linkage"]["objectives"]
        seen = 0
        for objective in objectives:
            for kr in objective["krs"]:
                with self.subTest(kr=kr["id"]):
                    self.assertIn("current", kr)
                    self.assertIn("target", kr)
                seen += 1
        self.assertGreaterEqual(seen, 3, "no key result to check")

    def test_the_numbers_are_the_ones_the_full_payload_carries(self):
        """Value equality, per key result, `--compact` against `--json`.

        Repointing `linkage.objectives` at `phase.objectives` — a path of the
        same shape whose KRs carry no numbers — made `--compact` report
        `current: null` for every one of them while `--json` reported `1.0`.
        This is the case that sees it.
        """
        by_id = {}
        for objective in STATE._at(self.full, "linkage.objectives") or []:
            for kr in objective.get("krs") or []:
                by_id[kr.get("id")] = kr
        self.assertTrue(by_id, "the fixture declares no linkage KRs")
        for objective in self.narrow["linkage"]["objectives"]:
            for kr in objective["krs"]:
                with self.subTest(kr=kr["id"]):
                    self.assertIn(kr["id"], by_id)
                    for field in ("current", "target", "title", "stretch"):
                        self.assertEqual(kr[field], by_id[kr["id"]][field])


if __name__ == "__main__":
    unittest.main()
