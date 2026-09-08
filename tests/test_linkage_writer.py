"""TASK-119 — `perry-goals link`, the writer this graph was documented as
having and did not have; ADR-019 — the graph it writes is `linkage.jsonl`.

`goals/SKILL.md § State files` called the register "machine-written" since the
lane shipped, and until TASK-119 there was no `link`: this repository's own
`perry/phase/002-linkage.md` was typed by hand on 2026-08-20, every edge and
every number.

**What ADR-019 took out of this module, and what it left.** The writer's
target was markdown, so the acceptance was a BYTE GATE over YAML: an append
had to change two lines of a file a human might have reformatted, preserve the
register's own quoting style, append to a block list as a block list, refuse
CRLF, and refuse a value the YAML reader could not read back. All of that was
machinery for editing a document in place, and all of it is gone with the
document. Six tests went with it and are named in the commit rather than
quietly dropped.

What survives is everything the writer was FOR, and it survives sharper:

1. **A write appends one record and touches no other byte.** Still a byte
   compare, and it is now the stronger claim — the old writer had to change a
   second line, `updated`, on every write, and that second line is TASK-155.
2. **The writer cannot create the state `perry-lint` rejects.** A task under
   two KRs is `linkage-task-single-kr`; a refusal that leaves the file
   untouched is the only acceptable answer, asserted by re-running the
   linter's own check on the file afterwards rather than by trusting an exit
   code.
3. **No invented `current`.** An unasserted `current` is absent, never `0`,
   because most KRs here drive a count DOWN and a zero reads as met on the day
   the register is written. And after ADR-019: **no invented `asserted_at`**,
   for the same reason one field over.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOALS = ROOT / "bin" / "perry-goals"
STATE = ROOT / "bin" / "perry-state"

sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402


def _load(name: str, as_name: str):
    spec = importlib.util.spec_from_loader(
        as_name, importlib.machinery.SourceFileLoader(as_name, str(ROOT / "bin" / name)))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[as_name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("perry-goals", "perry_goals_for_linkage")
LINT = _load("perry-lint", "perry_lint_for_linkage")
SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text())
LINT.load_glossary(SCHEMA)
DECLARED = SCHEMA["stores"]["declared"]["linkage.jsonl"]

#: The corpus: real stores, in the repository, on every machine.
#: `tests/live_state_expectations.py` is the standing guard about what a test
#: may say about one — a literal enumerating what this project happens to hold
#: today goes red when the project moves, for no reason anyone can act on. So
#: the corpus tests assert PROPERTIES of the write and take every id they need
#: from the file itself; the behavioural assertions run against `SYNTHETIC`.
CORPUS = [
    ROOT / "perry" / "linkage.jsonl",
    ROOT / "tests" / "fixtures" / "sample-project" / "linkage.jsonl",
]

AT = "2026-08-20T09:00:00Z"


def records(text: str) -> list[dict]:
    return [json.loads(line) for line in text.split("\n") if line.strip()]


def dump(rows: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def first_kr(model) -> str:
    return [k.id for o in model.objectives for k in o.krs][0]


def a_linked_task(model) -> tuple[str, str]:
    """(task id, the KR that already claims it), out of the graph."""
    for o in model.objectives:
        for k in o.krs:
            if k.tasks:
                return k.tasks[0], k.id
    raise AssertionError("the corpus store declares no edge")


def another_kr(model, not_this: str) -> str:
    return [k.id for o in model.objectives for k in o.krs if k.id != not_this][0]


def lint_findings(path: pathlib.Path) -> list[str]:
    """`perry-lint`'s own graph rules for this store, run in process.

    The linter's check, not a re-implementation of it — "the writer cannot
    create a task under two KRs" has to be asserted with the same predicate
    that would reject the file, or the two can drift apart in exactly the way
    this project keeps finding.
    """
    good, _bad = LINT._linkage_record_findings(records(path.read_text()),
                                               DECLARED, SCHEMA["enums"])
    out = []
    for slug in sorted({str(r.get("phase") or "") for r in good
                        if r.get("kind") in ("objective", "kr")}):
        number = P.linkage_phase_number(slug)
        mine = P.linkage_records_for_phase(good, number) if number else None
        if mine:
            out += [f.rule for f in LINT._linkage_graph_findings(mine, "s")]
    return out


class Project:
    """A throwaway project with one linkage store. Never the Perry repo."""

    def __init__(self, store: str, slug: str = "002-fields-are-typed"):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="perry-link-test-"))
        (self.dir / "phase").mkdir()
        (self.dir / ".perry").mkdir()
        (self.dir / "phase" / "CURRENT").write_text(slug)
        self.path = self.dir / "linkage.jsonl"
        self.path.write_text(store)

    @classmethod
    def of(cls, source: pathlib.Path) -> "Project":
        """A copy of a real store, pointed at one of the phases it declares.

        The corpus holds every phase in one file now, so the slug is READ from
        the records rather than derived from a filename — there is no filename
        to derive it from, and picking the wrong one would test a slice the
        writer is not writing.
        """
        rows = records(source.read_text())
        slug = next(str(r["phase"]) for r in rows
                    if r.get("kind") == "kr" and r.get("phase"))
        return cls(source.read_text(), slug)

    def run(self, *argv, expect=None, **env):
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        e.update(env)
        p = subprocess.run([sys.executable, str(GOALS), *argv, "--root", str(self.dir)],
                           capture_output=True, text=True, env=e)
        if expect is not None:
            assert p.returncode == expect, (p.returncode, p.stdout, p.stderr)
        return p

    def link(self, *argv, expect=0, **env):
        return self.run("link", *argv, expect=expect, **env)

    def text(self) -> str:
        return self.path.read_text()

    def model(self):
        return P.load_linkage(self.dir,
                              (self.dir / "phase" / "CURRENT").read_text())

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def sample_project(case: unittest.TestCase) -> pathlib.Path:
    """A copy of the shipped fixture — a whole project, not just a store.

    `perry-state` reports the sections a project HAS, so a temp directory
    holding one file has no `linkage` section to read and a test asserting
    about it would pass on an empty payload."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="perry-link-fixture-"))
    case.addCleanup(shutil.rmtree, d, ignore_errors=True)
    shutil.copytree(ROOT / "tests" / "fixtures" / "sample-project", d / "p")
    (d / "p" / ".perry").mkdir(exist_ok=True)
    return d / "p"


class Case(unittest.TestCase):
    def project(self, *a, **kw) -> Project:
        p = Project(*a, **kw)
        self.addCleanup(p.cleanup)
        return p

    def corpus(self, source: pathlib.Path) -> Project:
        p = Project.of(source)
        self.addCleanup(p.cleanup)
        return p


# ── 1. the byte gate ──────────────────────────────────────────────────────


class TestAWriteAppendsOneLine(Case):
    """Verification 1: proved with a byte compare, not with a parse.

    **The claim got stronger at ADR-019 and the test says so.** It was "a
    write touches TWO lines" — the `tasks:` list and the file-level `updated:`
    stamp — and the second was mandatory: `goals/reference/linkage.md` said
    every write bumps it. That stamp was also read as every KR's assertion
    date, so the second line this writer was obliged to move re-dated every
    asserted number in the phase (TASK-155). There is no second line.
    """

    def test_an_edge_appends_one_record_and_changes_no_other_byte(self):
        for source in CORPUS:
            with self.subTest(store=source.name, phase=source.parent.name):
                p = self.corpus(source)
                before = p.text()
                p.link("ZZZ-001", first_kr(p.model()))
                after = p.text()
                self.assertTrue(after.startswith(before),
                                "the write changed a byte it did not append")
                added = records(after[len(before):])
                self.assertEqual(len(added), 1, added)
                self.assertEqual(added[0]["kind"], "edge")
                self.assertEqual(added[0]["task"], "ZZZ-001")

    def test_no_kr_records_assertion_date_moves(self):
        """TASK-155, as bytes rather than as a warning.

        The old writer printed a warning naming every KR whose `current` its
        own write was about to re-date. There is nothing to warn about: the
        assertion date is on the `kr` record and an edge write does not touch
        one.
        """
        p = self.corpus(ROOT / "perry" / "linkage.jsonl")
        before = {r["id"]: r.get("asserted_at", "")
                  for r in records(p.text()) if r.get("kind") == "kr"}
        r = p.link("ZZZ-001", first_kr(p.model()))
        after = {r2["id"]: r2.get("asserted_at", "")
                 for r2 in records(p.text()) if r2.get("kind") == "kr"}
        self.assertEqual(before, after)
        self.assertNotIn("staleness signal", r.stderr,
                         "the writer still warns about a defect it cannot "
                         "commit")

    def test_every_refusal_leaves_the_file_byte_identical(self):
        """Seven refusals over the real store, each asserted as bytes.

        The ids come out of the file (`a_linked_task`), so this stays a
        statement about the writer when the project's own edges change."""
        source = ROOT / "perry" / "linkage.jsonl"
        model = Project.of(source).model()
        linked, holder = a_linked_task(model)
        for argv in (["ZZZ-001", "P002-O9-KR9"],
                     [linked, another_kr(model, holder)],
                     ["--unlinked", linked],
                     ["--alias", "NOPE-001", "a name"],
                     ["--project", "NEW-001", "P002-O9-KR9", "a name"],
                     ["ZZZ-001"],
                     ["ZZZ-001", first_kr(model), "extra"]):
            with self.subTest(argv=argv):
                p = self.corpus(source)
                before = p.text()
                r = p.link(*argv, expect=1)
                self.assertEqual(p.text(), before)
                self.assertIn("Nothing was written", r.stderr)

    def test_a_second_identical_edge_writes_nothing_at_all(self):
        """A no-op that re-stamped anything would report the graph as freshly
        asserted on a run that changed nothing — the same lie `current: 0`
        tells one field over."""
        p = self.corpus(ROOT / "perry" / "linkage.jsonl")
        kr = first_kr(p.model())
        p.link("ZZZ-001", kr)
        once = p.text()
        r = p.link("ZZZ-001", kr, expect=0)
        self.assertEqual(p.text(), once)
        self.assertIn("nothing to write", r.stdout)

    def test_a_dry_run_writes_nothing_and_prints_the_record(self):
        p = self.corpus(ROOT / "perry" / "linkage.jsonl")
        before = p.text()
        r = p.link("ZZZ-001", first_kr(p.model()), "--dry-run", "--json",
                   expect=0)
        self.assertEqual(p.text(), before)
        out = json.loads(r.stdout)
        self.assertTrue(out["dry_run"])
        self.assertFalse(out["written"])
        self.assertTrue(any("ZZZ-001" in line for line in out["diff"]))


# ── 2. the refusals ───────────────────────────────────────────────────────


class TestTheRefusalFires(Case):
    """Verification 2. Each one names what it could not decide, and writes
    nothing — `perry-lint` already rejects a task under two KRs, and the writer
    must not be able to produce that file in the first place."""

    def test_an_unresolvable_name_lists_the_phases_kr_ids(self):
        p = self.project(SYNTHETIC)
        r = p.link("ZZZ-001", "the store thing", expect=1)
        self.assertIn("is not a KR id, a Project id or a registered alias",
                      r.stderr)
        for kr in ("P002-O1-KR1", "P002-O1-KR2", "P002-O2-KR1"):
            self.assertIn(kr, r.stderr)
        self.assertIn("near-match is not a match", r.stderr)

    def test_a_kr_id_that_disagrees_with_its_nesting_is_refused(self):
        """`P002-O2-KR1` filed under `O1`, and the writer will not pick a side.

        This exists because the mutation matrix for TASK-180 found nothing
        holding the anchored `^P\\d{3}-(O\\d+)-KR\\d+$` in `link_project`:
        reverting it to the pre-migration `^P-(O\\d+)\\.` left every module
        green, because `objective` silently falls back to the nesting and this
        refusal is the only reader that can tell the two apart. An id form the
        writer cannot parse is an id form whose disagreements it cannot see.
        """
        p = self.project(MISNESTED)
        before = p.text()
        r = p.link("--project", "NEW-001", "P002-O2-KR1", "a name", expect=1)
        self.assertEqual(p.text(), before, "a refusal wrote to the store")
        self.assertIn("encodes objective O2", r.stderr)
        self.assertIn("sits under O1", r.stderr)

    def test_an_ambiguous_name_names_its_candidates_and_writes_nothing(self):
        """Two Projects answering to one label, on two different KRs.

        The graph `perry-lint` rejects — and a file the writer refuses to
        create can still be handed to it, which is the case that matters: the
        answer is the candidates, never the nearest one."""
        p = self.project(AMBIGUOUS)
        before = p.text()
        r = p.link("ZZZ-001", "shared name", expect=1)
        self.assertEqual(p.text(), before)
        self.assertIn("does not resolve to exactly one KR", r.stderr)
        self.assertIn("PROJ-A", r.stderr)
        self.assertIn("PROJ-B", r.stderr)
        self.assertIn("P002-O1-KR1", r.stderr)
        self.assertIn("P002-O1-KR2", r.stderr)
        self.assertIn("never by resemblance", r.stderr)

    def test_the_writer_cannot_put_one_task_under_two_krs(self):
        p = self.project(SYNTHETIC)
        self.assertNotIn("linkage-task-single-kr", lint_findings(p.path))
        p.link("ZZZ-001", "P002-O1-KR1")
        r = p.link("ZZZ-001", "P002-O2-KR1", expect=1)
        self.assertIn("already listed under P002-O1-KR1", r.stderr)
        self.assertIn("Move it, don't duplicate it", r.stderr)
        self.assertNotIn("linkage-task-single-kr", lint_findings(p.path))
        self.assertEqual(
            [k.id for o in p.model().objectives for k in o.krs
             if "ZZZ-001" in k.tasks], ["P002-O1-KR1"])

    def test_declaring_a_linked_task_unlinked_is_refused(self):
        p = self.project(SYNTHETIC)
        r = p.link("--unlinked", "AAA-001", expect=1)
        self.assertIn("attributed and drifting", r.stderr)

    def test_linking_a_declared_unlinked_task_undeclares_it(self):
        """One write, not two: otherwise it renders as both at once."""
        p = self.project(SYNTHETIC)
        self.assertIn("BBB-002", p.model().unlinked)
        p.link("BBB-002", "P002-O1-KR2")
        model = p.model()
        self.assertNotIn("BBB-002", model.unlinked)
        self.assertEqual(model.kr_for_task("BBB-002"), "P002-O1-KR2")
        self.assertNotIn("linkage-task-single-kr", lint_findings(p.path))

    def test_an_alias_another_project_claims_is_refused(self):
        p = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "linkage.jsonl")
        before = p.text()
        r = p.link("--alias", "REL-002", "Deploy script hardening", expect=1)
        self.assertEqual(p.text(), before)
        self.assertIn("already claimed by REL-001", r.stderr)
        self.assertIn("linkage-names-unique", r.stderr)

    def test_a_registered_alias_resolves_the_next_report_under_the_old_name(self):
        """What the registry is FOR: a name that drifted resolves to the same
        KR through a recorded alias, instead of through a resemblance."""
        p = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "linkage.jsonl")
        p.link("ZZZ-001", "deploy-hardening")
        self.assertEqual(p.model().kr_for_task("ZZZ-001"), "P002-O1-KR1")

    def test_an_alias_is_appended_as_a_record_and_the_old_one_survives(self):
        """The store is append-only apart from one retraction, so an alias is
        a SECOND `project` record for the same id carrying the full list.
        Rewriting the earlier line would be this writer editing a record it
        did not write."""
        p = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "linkage.jsonl")
        before = p.text()
        p.link("--alias", "REL-002", "flake-detector")
        self.assertTrue(p.text().startswith(before))
        entry = [x for x in p.model().projects
                 if x.project_id == "REL-002"][-1]
        self.assertIn("flake-detector", entry.aliases)
        self.assertEqual(p.model().kr_for_task("ZZZ-001"), "")
        p.link("ZZZ-001", "flake-detector")
        self.assertEqual(p.model().kr_for_task("ZZZ-001"), "P002-O2-KR1")

    def test_a_retired_project_is_named_rather_than_used(self):
        p = self.project(DROPPED)
        r = p.link("ZZZ-001", "PROJ-OLD", expect=1)
        self.assertIn("retired Project", r.stderr)
        self.assertIn("history, not an attribution", r.stderr)

    def test_a_new_project_derives_its_objective_and_keeps_the_linter_quiet(self):
        p = self.project(SYNTHETIC)
        p.link("--project", "PROJ-009", "P002-O2-KR1", "the reader cutover")
        entry = [x for x in p.model().projects
                 if x.project_id == "PROJ-009"][0]
        self.assertEqual((entry.serves_kr, entry.objective, entry.status),
                         ("P002-O2-KR1", "O2", "active"))
        self.assertEqual(lint_findings(p.path), [])

    def test_a_project_id_already_in_the_graph_is_refused(self):
        p = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "linkage.jsonl")
        r = p.link("--project", "REL-001", "P002-O1-KR1", "another name",
                   expect=1)
        self.assertIn("already in this phase's graph", r.stderr)


# ── 3. no invented number, and no invented date ───────────────────────────


class TestNoInventedCurrent(Case):
    """Verification 3, and TASK-120's hand-over.

    `goals/state/linkage_TEMPLATE.md` wrote `current: 0` into every register a
    project ever created. Six of eight phase KRs on THIS project carry
    `target: 0` — they drive a count down — so that default made every one of
    them read as met on the day the register was written.

    The template is deleted (ADR-019 deleted the document it templated), so
    the "shipped template asserts no current" test is gone with it. What
    replaces it is the same guarantee stated where it can still be violated:
    **no write path invents either field**, and a KR with no `current` is
    published `unasserted` rather than `0`.
    """

    def test_perry_reports_an_absent_current_as_unasserted_and_not_as_zero(self):
        """`0` and "nobody has said" are different facts, and only one of them
        can be `target: 0` met."""
        root = sample_project(self)
        (root / "linkage.jsonl").write_text(dump([
            {"kind": "objective", "phase": "002-release-pipeline", "id": "O1",
             "title": "an objective"},
            {"kind": "kr", "phase": "002-release-pipeline", "objective": "O1",
             "id": "P002-O1-KR1", "title": "a KR", "metric": "m",
             "target": 0},
        ]))
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        run = subprocess.run(
            [sys.executable, str(GOALS), "link", "ZZZ-001", "P002-O1-KR1",
             "--root", str(root)], capture_output=True, text=True, env=e)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(subprocess.run(
            [sys.executable, str(STATE), "--json", "--section", "linkage",
             "--root", str(root)], capture_output=True, text=True,
            env=e).stdout)["linkage"]
        kr = [k for o in out["objectives"] for k in o["krs"]
              if k["id"] == "P002-O1-KR1"][0]
        self.assertIsNone(kr["current"])
        self.assertEqual(kr["current_provenance"]["state"], "unasserted")
        self.assertEqual(kr["current_provenance"]["asserted_at"], "")
        self.assertFalse(kr["current_staleness"]["stale"])

    def test_the_writer_never_writes_target_current_or_asserted_at(self):
        """Asserted over every write path, as the records it appends.

        `asserted_at` joins the other two at ADR-019 and for the same reason:
        the only date a writer that did not measure the number can supply is
        `now`, and a number stamped `now` by a command that appended an edge
        is TASK-155 with a different spelling.
        """
        p = self.project(SYNTHETIC)
        for argv in (["ZZZ-001", "P002-O1-KR1"],
                     ["--unlinked", "ZZZ-002"],
                     ["--project", "PROJ-009", "P002-O2-KR1", "a project"],
                     ["--alias", "PROJ-009", "another name"]):
            with self.subTest(argv=argv):
                before = p.text()
                p.link(*argv, expect=0)
                added = records(p.text()[len(before):])
                self.assertTrue(added)
                for rec in added:
                    for field in ("target", "current", "asserted_at"):
                        self.assertNotIn(field, rec, rec)

    def test_no_write_path_touches_a_kr_record_at_all(self):
        """The stronger form, and the one a field added later cannot slip
        past: `link` writes `edge`, `unlinked` and `project` records, and
        every `kr` record in the file is byte-identical afterwards."""
        p = self.project(SYNTHETIC)
        before = [r for r in records(p.text()) if r["kind"] == "kr"]
        for argv in (["ZZZ-001", "P002-O1-KR1"],
                     ["--unlinked", "ZZZ-002"],
                     ["--project", "PROJ-009", "P002-O2-KR1", "a project"]):
            p.link(*argv, expect=0)
        after = [r for r in records(p.text()) if r["kind"] == "kr"]
        self.assertEqual(before, after)


# ── 4. what Perry reads back ──────────────────────────────────────────────


class TestPerryReadsWhatTheWriterWrote(Case):
    """Verification 4: through `perry-state --section linkage`, with TASK-120's
    provenance keys resolving."""

    def setUp(self):
        self.root = sample_project(self)

    def tool(self, tool: pathlib.Path, *argv):
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        return subprocess.run([sys.executable, str(tool), *argv,
                               "--root", str(self.root)],
                              capture_output=True, text=True, env=e)

    def test_the_edge_the_writer_wrote_is_the_edge_perry_reports(self):
        w = self.tool(GOALS, "link", "ZZZ-001", "P002-O1-KR2")
        self.assertEqual(w.returncode, 0, w.stderr)
        out = json.loads(self.tool(
            STATE, "--json", "--section", "linkage").stdout)["linkage"]
        kr = [k for o in out["objectives"] for k in o["krs"]
              if k["id"] == "P002-O1-KR2"][0]
        self.assertIn("ZZZ-001", kr["tasks"])
        self.assertEqual(kr["current_provenance"]["source"], "linkage-store")
        self.assertEqual(kr["current_provenance"]["asserted_scope"], "kr",
                         "the fixture's KR carries an `asserted_at`, so the "
                         "scope must be the KR and never a file")
        self.assertIn("evaluated", kr["current_staleness"])

    def test_a_declared_unlinked_task_stops_being_drift_when_it_is_linked(self):
        """The read side of the same edge: linking a declared row moves it.

        A declared row is reported in `declared_unlinked` and nowhere else,
        before the edge as well as after (TASK-228); writing the edge moves it
        into `linked` and empties both other buckets.
        """
        def attribution():
            return json.loads(self.tool(STATE, "--json", "--section",
                                        "attribution").stdout)["attribution"]
        before = attribution()
        self.assertEqual([t["id"] for t in before["unlinked"]], [])
        self.assertEqual(before["declared_unlinked"], ["REL-009"])
        w = self.tool(GOALS, "link", "REL-009", "P002-O2-KR1")
        self.assertEqual(w.returncode, 0, w.stderr)
        after = attribution()
        self.assertEqual(after["linked"], before["linked"] + 1)
        self.assertEqual(after["unlinked"], [])
        self.assertEqual(after["declared_unlinked"], [])


# ── 5. the record's own date ──────────────────────────────────────────────


class TestDeclaredAt(Case):
    """`declared_at` is per record, and it is the moment of the write.

    **This class replaces `TestUpdated`, which had three tests about the
    file-level stamp.** One of them —
    `test_re_dating_someone_elses_assertion_is_reported_not_absorbed` — pinned
    the WARNING the old writer printed on every run, naming every KR whose
    assertion date its own write was about to move. The warning is gone
    because the defect is: an edge write cannot reach a KR record.
    """

    def test_the_appended_record_carries_a_full_utc_datetime(self):
        p = self.corpus(ROOT / "perry" / "linkage.jsonl")
        before = p.text()
        p.link("ZZZ-001", first_kr(p.model()))
        rec = records(p.text()[len(before):])[0]
        self.assertRegex(rec["declared_at"],
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_a_second_write_dates_only_its_own_record(self):
        """The property the file-level stamp could not have. Two writes, and
        the first record's date is the same byte afterwards."""
        p = self.project(SYNTHETIC)
        p.link("ZZZ-001", "P002-O1-KR1")
        first = [r for r in records(p.text())
                 if r.get("task") == "ZZZ-001"][0]["declared_at"]
        p.link("ZZZ-002", "P002-O1-KR2")
        again = [r for r in records(p.text())
                 if r.get("task") == "ZZZ-001"][0]["declared_at"]
        self.assertEqual(first, again)

    def test_a_declaration_carries_the_phase_it_was_made_against(self):
        """ADR-019's `unlinked.phase`. The store holds every phase, so a
        declaration with no phase would count against all of them."""
        p = self.project(SYNTHETIC)
        p.link("--unlinked", "ZZZ-003")
        rec = [r for r in records(p.text())
               if r.get("kind") == "unlinked" and r["task"] == "ZZZ-003"][0]
        self.assertEqual(rec["phase"], "002-synthetic")


# ── 5b. a refusal says which of the values it means ───────────────────────


class TestARefusedValueIsLocated(Case):
    """TASK-037's rule, on the one `perry-goals` command with no flags.

    `bin/perry-goals § check_due` states it — *"the refusal says so and names
    the flag, so a user is never guessing where their words go"* — and every
    flag-carried value in `commit` now obeys it. `link` takes its values
    positionally (`goals/reference/linkage.md` writes the grammar that way),
    so there is no flag to name and `argument 1` was the whole of the answer:
    on `--project <PROJECT-ID> <KR-ID> "<name>"` that is a position to count
    out against a grammar the user has to go and find. The SLOT is named
    instead, read out of the same `usage` line the arity refusal prints.
    """

    def test_the_refusal_names_the_slot_not_just_a_position(self):
        p = self.project(SYNTHETIC)
        r = p.link("AAA-001\nsecond line", "P002-O1-KR1", expect=1)
        self.assertIn("<TASK-ID> (argument 1) contains a line break",
                      r.stderr)
        self.assertNotIn("second line", p.text())

    def test_each_shape_names_its_own_slots(self):
        """One list, four grammars. The slot names come from `usage`, so a
        grammar that changes cannot leave the refusal quoting the old one."""
        for argv, bad_at, slot in (
                (("{v}", "P002-O1-KR1"), 0, "<TASK-ID>"),
                (("AAA-009", "{v}"), 1, "<KR-ID>"),
                (("--unlinked", "{v}"), 1, "<TASK-ID>"),
                (("--alias", "PROJ-001", "{v}"), 2, "<the other name>"),
                (("--project", "{v}", "P002-O1-KR1", "n"), 1, "<PROJECT-ID>"),
                (("--project", "PROJ-009", "P002-O1-KR1", "{v}"), 3, "<name>")):
            with self.subTest(argv=argv):
                p = self.project(SYNTHETIC)
                r = p.link(*[a.format(v="a\nb") for a in argv], expect=1)
                position = bad_at - sum(1 for a in argv[:bad_at]
                                        if a.startswith("--"))
                self.assertIn(f"{slot} (argument {position + 1}) contains a "
                              f"line break", r.stderr)

    def test_an_empty_value_is_located_the_same_way(self):
        """**The quote case is gone, and it was a YAML fact rather than a
        register fact.** `parse_yaml_subset` stripped matching outer quotes and
        did no escape processing, so a name carrying a quote could not be read
        back as itself and the writer refused it. JSON escapes; the value
        round-trips; refusing it would be this writer inventing a rule its own
        format does not have. What is left of `check_writable` is the shape of
        a record VALUE — one line, non-empty — and both refusals carry the
        slot."""
        p = self.project(SYNTHETIC)
        self.assertIn("<KR-ID> (argument 2) is empty",
                      p.link("AAA-009", "   ", expect=1).stderr)
        p.link("--project", "PROJ-009", "P002-O2-KR1", 'the "real" name',
               expect=0)
        entry = [x for x in p.model().projects
                 if x.project_id == "PROJ-009"][0]
        self.assertEqual(entry.name, 'the "real" name',
                         "a quoted name did not survive the round trip")


# ── 6. what it refuses to write at all ────────────────────────────────────


class TestItRefusesWhatItCannotWriteSafely(Case):

    def test_an_unreadable_store(self):
        p = self.project('{"kind": "kr"\nnot json at all\n')
        r = p.link("ZZZ-001", "P002-O1-KR1", expect=1)
        self.assertIn("cannot be read", r.stderr)

    def test_a_store_that_declares_no_kr_for_this_phase(self):
        """**This replaces `test_an_unfilled_template`.** That one fed the
        writer a register full of `{{...}}` placeholders and asserted it
        refused. The template is deleted; the equivalent state is a store that
        exists and declares nothing for the phase being written, and the
        refusal has to name what writes those records."""
        p = self.project("")
        r = p.link("ZZZ-001", "P002-O1-KR1", expect=1)
        self.assertIn("declares no key result", r.stderr)
        self.assertIn("plan-phase", r.stderr)

    def test_no_store_at_all(self):
        p = self.project(SYNTHETIC)
        p.path.unlink()
        r = p.link("ZZZ-001", "P002-O1-KR1", expect=1)
        self.assertIn("no linkage store", r.stderr)
        self.assertFalse(p.path.exists(),
                         "a refusal created the store it refused to write")

    def test_no_current_phase(self):
        p = self.corpus(ROOT / "perry" / "linkage.jsonl")
        (p.dir / "phase" / "CURRENT").write_text("")
        r = p.link("ZZZ-001", "P002-O1-KR1", expect=1)
        self.assertIn("no current phase", r.stderr)

    def test_it_still_refuses_another_lanes_file(self):
        """`SKILL.md § The hand-off contract`, unchanged by this row: the
        store is this lane's, `BOARD.md` is not."""
        self.assertTrue(G.owned_by_goals("linkage.jsonl"))
        self.assertFalse(G.owned_by_goals("BOARD.md"))


# ── fixtures ──────────────────────────────────────────────────────────────


def _graph(phase: str, krs, *, unlinked=(), projects=()) -> str:
    """One phase's records. `krs` is `(suffix, objective, extra fields)`."""
    rows: list[dict] = []
    for oid in sorted({o for _s, o, _e in krs}):
        rows.append({"kind": "objective", "phase": phase, "id": oid,
                     "title": f"objective {oid}"})
    for suffix, oid, extra in krs:
        rows.append({"kind": "kr", "phase": phase, "objective": oid,
                     "id": f"P002-{suffix}", "title": f"the {suffix} result",
                     "metric": "m", **extra})
    for task, kr in unlinked:
        rows.append({"kind": "unlinked", "task": task, "phase": phase,
                     "declared_at": AT, "actor": "goals", "via": "link"}
                    if kr is None else
                    {"kind": "edge", "task": task, "kr": kr,
                     "declared_at": AT, "actor": "goals", "via": "link"})
    for pid, kr, name, status in projects:
        rec = {"kind": "project", "phase": phase, "id": pid, "kr": kr,
               "name": name, "aliases": []}
        if status != "active":
            rec["status"] = status
        rec.update({"declared_at": AT, "actor": "goals", "via": "link"})
        rows.append(rec)
    return dump(rows)


#: The graph the behavioural assertions run against: every id they name is
#: written here, so nothing this module claims can be falsified by this
#: project's own graph moving on. It carries the shapes those assertions need
#: and the real store happens to have today — a declared `unlinked` record and
#: an asserted `current` — stated rather than borrowed.
SYNTHETIC = _graph(
    "002-synthetic",
    [("O1-KR1", "O1", {"target": 1}),
     ("O1-KR2", "O1", {"target": 0, "current": 5, "asserted_at": AT}),
     ("O2-KR1", "O2", {})],
    unlinked=[("AAA-001", "P002-O1-KR1"), ("BBB-002", None)],
    projects=[("PROJ-001", "P002-O1-KR1", "the first project", "active")])

#: A graph whose objective records contradict its KR ids: `P002-O2-KR1` is
#: filed under `O1`. `perry-lint § linkage-objective-agrees` reports it; the
#: writer refuses to add to it rather than picking a side.
MISNESTED = _graph(
    "002-misnested",
    [("O1-KR1", "O1", {"target": 1}), ("O2-KR1", "O1", {"target": 1})])

AMBIGUOUS = _graph(
    "002-ambiguous",
    [("O1-KR1", "O1", {}), ("O1-KR2", "O1", {})],
    projects=[("PROJ-A", "P002-O1-KR1", "shared name", "active"),
              ("PROJ-B", "P002-O1-KR2", "shared name", "active")])

DROPPED = _graph(
    "002-dropped",
    [("O1-KR1", "O1", {"target": 1})],
    projects=[("PROJ-OLD", "P002-O1-KR1", "an old project", "dropped")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
