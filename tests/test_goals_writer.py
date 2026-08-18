"""TASK-037's gate, and TASK-042's writer.

DESIGN-005 § 5.5 rates the `perry-goals` writer the riskiest of the markdown
three, for a reason no ordinary test catches — `OKR.md` is prose the user
argued with, and a writer that tidies it produces a file that still passes
`perry-lint` and no longer reads the way its author wrote it.

So the first half runs against the **real** files on this machine, not against
a fixture Perry generated. They disagree about almost everything and not one of
them is malformed.

The second half is `commit`, whose specification is
`goals/reference/phases.md § commit <promise>` rule for rule. Every assertion
about a write is made **as a diff** — which lines changed, and that no others
did — because "the file still contains the right value" is exactly the check
that passes on a writer which reformatted everything around it.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))


def _load():
    """`bin/perry-goals` has no `.py` suffix, so import it by path."""
    spec = importlib.util.spec_from_loader(
        "perry_goals",
        importlib.machinery.SourceFileLoader(
            "perry_goals", str(ROOT / "bin" / "perry-goals")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(ROOT / 'viewer'))
import tables as T  # noqa: E402

G = _load()
GOALS = ROOT / "bin" / "perry-goals"

#: In-repo files, always present. `CORPUS` adds the ones that only exist on a
#: machine where those projects are checked out.
IN_REPO = [
    ROOT / "perry" / "OKR.md",
    ROOT / "tests" / "fixtures" / "sample-project" / "OKR.md",
    ROOT / "goals" / "state" / "OKR_TEMPLATE.md",
]
ELSEWHERE = [
    pathlib.Path.home() / "proj" / "gimegime-pmo" / "OKR.md",
    pathlib.Path.home() / "proj" / "aimark" / "perry" / "OKR.md",
]


class TestByteIdentity(unittest.TestCase):
    """Load it, change nothing, write it back."""

    def test_the_in_repo_files_round_trip(self):
        for path in IN_REPO:
            self.assertTrue(path.exists(), f"{path} is gone; fix this list")
            with self.subTest(path=path.name):
                doc = G.Okr(path)
                self.assertEqual(path.read_text(), doc.render())
                self.assertTrue(doc.unchanged())

    def test_the_files_outside_the_repo_round_trip_when_present(self):
        """Skipped rather than failed when those projects are not checked out
        — but never silently: a skip that prints nothing is the same as a
        check that was never written."""
        found = [p for p in ELSEWHERE if p.exists()]
        if not found:
            self.skipTest(
                f"none of {[str(p) for p in ELSEWHERE]} present on this "
                f"machine; the in-repo corpus still ran")
        for path in found:
            with self.subTest(path=str(path)):
                self.assertEqual(path.read_text(), G.Okr(path).render())

    def test_the_corpus_actually_disagrees(self):
        """A round-trip test over three files written by the same template
        proves nothing. This asserts the corpus contains the shapes the gate
        is about, so it cannot quietly become uniform."""
        texts = [p.read_text() for p in IN_REPO + ELSEWHERE if p.exists()]
        joined = "\n".join(texts)
        self.assertRegex(joined, r"(?m)^### Objective \d+[:—-]",
                         "no objective heading in the corpus at all")
        self.assertGreaterEqual(
            len({t.count("\n## v") for t in texts}), 2,
            "every file in the corpus has the same number of versions, so "
            "the multi-version shape is not being exercised")

    def test_a_file_with_no_trailing_newline_round_trips(self):
        """`splitlines()` would silently absorb the difference between a file
        ending in a newline and one that does not, and write back the wrong
        one. This is why `render` uses `split`/`join`."""
        import tempfile
        for text in ("# OKR\n\n## Mission\n\nship it",
                     "# OKR\n\n## Mission\n\nship it\n",
                     "# OKR\n\n## Mission\n\nship it\n\n\n"):
            with tempfile.TemporaryDirectory() as d:
                p = pathlib.Path(d) / "OKR.md"
                p.write_text(text)
                self.assertEqual(text, G.Okr(p).render(), repr(text))


class TestLocating(unittest.TestCase):
    """The section scanner, against the shapes the real files carry."""

    def okr(self, text: str):
        import tempfile
        self._d = tempfile.TemporaryDirectory()
        p = pathlib.Path(self._d.name) / "OKR.md"
        p.write_text(text)
        return G.Okr(p)

    NESTED = """# OKR

## v2: 2026-04-30

### Objective 1: 维持长期稳定收益

text

### Anti-Goals

- not this

## v4: 2026-05-29

### Objective 1: Insurance
"""

    def test_a_version_section_swallows_the_headings_beneath_it(self):
        """gimegime-pmo nests `### Anti-Goals` inside a version. A scanner
        that stopped at any heading would cut that version in half and a
        writer would then append into the middle of it."""
        o = self.okr(self.NESTED)
        lo, hi = o.section(r"v2\b")
        body = "\n".join(o.lines[lo:hi])
        self.assertIn("Anti-Goals", body)
        self.assertNotIn("v4", body)

    def test_a_missing_section_is_refused_not_guessed(self):
        o = self.okr(self.NESTED)
        self.assertFalse(o.has_section(r"Commitments"))
        with self.assertRaises(G.Refused):
            o.section(r"Commitments")

    def test_rows_key_by_header_not_position(self):
        """The defect `schema/README.md` names outright: columns resolve by
        name, never by position."""
        o = self.okr("""# OKR

## Commitments

| Id | Track | Promise | To whom | By when | Status |
|---|---|---|---|---|---|
| ops/1 | ops | Invoices reconciled | Finance | within the track SLA | active |
""")
        lo, hi = o.section(r"Commitments")
        rows = o.rows(lo, hi)
        self.assertEqual(1, len(rows))
        _, cells = rows[0]
        self.assertEqual("ops/1", cells["id"])
        self.assertEqual("Finance", cells["to whom"])
        self.assertEqual("within the track SLA", cells["by when"])

    def test_a_decorated_header_still_resolves(self):
        o = self.okr("""# OKR

## Commitments

| **Id** | **Track** | `Promise` |
|---|---|---|
| ops/1 | ops | Invoices reconciled |
""")
        lo, hi = o.section(r"Commitments")
        self.assertEqual("ops/1", o.rows(lo, hi)[0][1]["id"])


TRACKS = """# Perry configuration

- Document language: English
- Repo layout: single

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| ops | queue | commitments | intake -> doing | — | 5d | weekly | V2 |
| rel | pipeline | commitments | draft -> shipped | 3 | 10d | weekly | V3 |
| bare | queue | commitments | intake -> doing | — |  | weekly | V2 |
| main | project | okr | — | — | — | — | V2 |
"""

BARE_OKR = """# OKR — fixture

## Mission

Ship it.

## Anti-Goals

- not this

## Versioning log

- v1: 2026-08-01 — initial.
"""

#: Deliberately hand-aligned, and deliberately NOT in the schema's column
#: order — a writer that places cells by position rather than by resolved name
#: fills `To whom` with a date here and the test says so.
ALIGNED = """# OKR — fixture

## Mission

Ship it.

## Commitments

> a note the user wrote

| Track | Id      | Promise                | To whom | By when    | Status | Discharged by |
|-------|---------|------------------------|---------|------------|--------|---------------|
| rel   | rel/1   | Release 2.0            | Users   | {past}     | active |               |
| ops   | ops/7   | Invoices reconciled    | Finance | within SLA | active | oldest-first  |

## Anti-Goals

- not this
"""

#: The same table with the headers Perry's own glossary declares for zh. Note
#: `截止`, which the glossary maps from BOTH `Deadline` and `By when`.
CHINESE = """# OKR — 项目

## 使命

做出来。

## 承诺

| 编号 | 轨道 | 承诺内容 | 承诺对象 | 截止 | 状态 |
|---|---|---|---|---|---|
| ops/1 | ops | 对账 | 财务 | within the track SLA | active |

## 反目标

- 不做这个
"""


class Project:
    """A throwaway project root. Never the Perry repo — a previous agent ran a
    writer against it and the test writes landed in Perry's real board."""

    def __init__(self, okr: str = BARE_OKR, tracks: str | None = TRACKS):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="perry-goals-test-"))
        self.okr_path = self.dir / "OKR.md"
        self.okr_path.write_text(okr)
        (self.dir / ".perry").mkdir()
        if tracks is not None:
            (self.dir / ".perry" / "config.md").write_text(tracks)

    def run(self, *argv, expect=None, **env):
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        e.update(env)
        p = subprocess.run(
            [sys.executable, str(GOALS), *argv, "--root", str(self.dir)],
            capture_output=True, text=True, env=e)
        if expect is not None:
            assert p.returncode == expect, (p.returncode, p.stdout, p.stderr)
        return p

    def commit(self, *argv, expect=0):
        return self.run("commit", *argv, expect=expect)

    def text(self) -> str:
        return self.okr_path.read_text()

    def events(self) -> list[dict]:
        p = self.dir / ".perry" / "events.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().split("\n") if l.strip()]

    def changed_lines(self, before: str) -> list[tuple[str, str]]:
        """(old, new) for every line that is not byte-identical.

        Compared positionally after aligning on length, so an insert reports as
        one added line rather than shifting every line after it into the diff.
        """
        import difflib
        out = []
        for line in difflib.ndiff(before.split("\n"), self.text().split("\n")):
            if line.startswith("- "):
                out.append(("-", line[2:]))
            elif line.startswith("+ "):
                out.append(("+", line[2:]))
        return out

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class WriterCase(unittest.TestCase):
    def project(self, *a, **kw) -> Project:
        p = Project(*a, **kw)
        self.addCleanup(p.cleanup)
        return p


class TestCreatingACommitment(WriterCase):

    def test_a_create_appends_exactly_one_line_and_touches_nothing_else(self):
        """V3 in the spec: asserted as a diff, not as a grep. A writer that
        re-rendered the table would still contain the new row."""
        p = self.project(ALIGNED.format(past="2027-01-01"))
        before = p.text()
        p.commit("--track", "ops", "--promise", "Statements filed",
                 "--to", "Auditor", "--by", "within the track SLA")
        diff = p.changed_lines(before)
        self.assertEqual([d[0] for d in diff], ["+"], diff)
        self.assertIn("ops/8", diff[0][1])
        # every pre-existing line survives, in order and byte for byte
        after = p.text().split("\n")
        after.remove(diff[0][1])
        self.assertEqual(before.split("\n"), after)

    def test_cells_land_by_resolved_name_not_by_position(self):
        """`ALIGNED`'s header starts `| Track | Id |`, not `| Id | Track |`.
        Placing by position writes the id into `Track` and every consumer of
        this register then follows a link that points at nothing."""
        p = self.project(ALIGNED.format(past="2027-01-01"))
        p.commit("--track", "ops", "--promise", "Statements filed",
                 "--to", "Auditor", "--by", "within the track SLA")
        row = [l for l in p.text().split("\n") if "ops/8" in l][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual("ops", cells[0])
        self.assertEqual("ops/8", cells[1])
        self.assertEqual("Auditor", cells[3])
        self.assertEqual("active", cells[5])

    def test_the_id_is_minted_per_track(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x",
                 "--by", "5 days")
        p.commit("--track", "rel", "--promise", "b", "--to", "y",
                 "--by", "2027-01-01")
        p.commit("--track", "ops", "--promise", "c", "--to", "z",
                 "--by", "5 days")
        ids = [e["id"] for e in p.events() if e["event"] == "commit"]
        self.assertEqual(["ops/1", "rel/1", "ops/2"], ids)

    def test_an_id_is_never_reused_after_its_row_is_deleted_by_hand(self):
        """`phases.md`: *ids are never reused and never renumbered*. A board
        row's `Commitment` cell points at this string; reusing a number does
        not dangle visibly, it silently re-points work at another promise."""
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        p.okr_path.write_text(
            "\n".join(l for l in p.text().split("\n") if "ops/1" not in l))
        p.commit("--track", "ops", "--promise", "b", "--to", "y", "--by", "5 days")
        self.assertIn("ops/2", p.text())
        self.assertNotIn("ops/1 ", p.text())

    def test_status_is_active_and_discharged_by_is_left_empty(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        row = [l for l in p.text().split("\n") if "ops/1" in l][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual("active", cells[5])
        self.assertEqual("", cells[6])


class TestCreatingTheSection(WriterCase):

    def test_it_is_refused_when_no_track_is_pipeline_or_queue(self):
        """`OKR_TEMPLATE.md` says to omit the section entirely on an
        all-`project` project. Creating it because someone typed `commit`
        would add a spine to a shape that has no use for one."""
        only_project = TRACKS.replace("| ops | queue", "| ops | project") \
                             .replace("| rel | pipeline", "| rel | project") \
                             .replace("| bare | queue", "| bare | project")
        p = self.project(BARE_OKR, only_project)
        before = p.text()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--by", "5 days", expect=1)
        self.assertIn("no track", r.stderr)
        self.assertEqual(before, p.text())

    def test_it_is_created_from_the_template_note_included(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        note = "> Promises to a named party by a date"
        self.assertIn(note, p.text())
        self.assertIn(note, (ROOT / "goals" / "state" / "OKR_TEMPLATE.md").read_text())
        # and not the template's placeholder row
        self.assertNotIn("{{track}}", p.text())

    def test_it_lands_before_anti_goals_and_leaves_every_other_line_alone(self):
        p = self.project()
        before = p.text()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        self.assertLess(p.text().index("## Commitments"),
                        p.text().index("## Anti-Goals"))
        for line in before.split("\n"):
            if line.strip():
                self.assertIn(line, p.text().split("\n"))

    def test_a_file_with_no_anti_goals_gets_the_section_at_the_end(self):
        p = self.project("# OKR\n\n## Mission\n\nShip it.\n")
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        self.assertTrue(p.text().startswith("# OKR\n\n## Mission\n\nShip it.\n"))
        self.assertIn("## Commitments", p.text())


class TestByWhenCarriesTwoFormats(WriterCase):
    """`phases.md § commit` step 4."""

    def test_a_pipeline_track_refuses_prose(self):
        p = self.project()
        r = p.commit("--track", "rel", "--promise", "a", "--to", "x",
                     "--by", "when it is ready", expect=1)
        self.assertIn("must be a date", r.stderr)

    def test_a_pipeline_track_refuses_a_date_that_is_not_one(self):
        p = self.project()
        p.commit("--track", "rel", "--promise", "a", "--to", "x",
                 "--by", "2026-02-30", expect=1)

    def test_a_queue_track_refuses_prose_that_names_no_clock(self):
        """The category, not the three examples. `phases.md` lists `soon`,
        `ASAP` and `when we get to it`; a guard built from that list passes
        every other clockless phrase while claiming to implement the rule."""
        p = self.project()
        for prose in ("soon", "ASAP", "when we get to it", "eventually",
                      "next time we look at it", "尽快", "有空再说",
                      "best effort", "when resourcing allows"):
            with self.subTest(prose=prose):
                r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                             "--by", prose, expect=1)
                self.assertIn("names no clock", r.stderr)

    def test_a_queue_track_accepts_prose_that_does_name_one(self):
        p = self.project()
        for prose in ("within the track SLA", "same business day", "5 days",
                      "2027-01-01", "每周一次", "在时限内"):
            with self.subTest(prose=prose):
                p.commit("--track", "ops", "--promise", "a", "--to", "x",
                         "--by", prose)

    def test_a_queue_track_with_no_sla_in_the_register_is_refused(self):
        """"within the track SLA" pointing at an empty register is a promise
        with no clock at all."""
        p = self.project()
        r = p.commit("--track", "bare", "--promise", "a", "--to", "x",
                     "--by", "within the track SLA", expect=1)
        self.assertIn("no `SLA`", r.stderr)
        self.assertNotIn("bare/1", p.text())

    def test_an_undeclared_track_is_refused(self):
        p = self.project()
        r = p.commit("--track", "ghost", "--promise", "a", "--to", "x",
                     "--by", "5 days", expect=1)
        self.assertIn("not declared", r.stderr)

    def test_a_promise_to_nobody_is_routed_not_filed(self):
        """*A promise with no named party is a KR, and belongs under an
        Objective instead* — the refusal says where it goes."""
        p = self.project()
        r = p.commit("--track", "ops", "--promise", "a", "--by", "5 days",
                     expect=1)
        self.assertIn("Objective", r.stderr)


class TestEndingOne(WriterCase):

    def start(self) -> Project:
        p = self.project(ALIGNED.format(past="2027-01-01"))
        return p

    def test_close_changes_one_cell_of_one_line(self):
        p = self.start()
        before = p.text()
        p.commit("--close", "ops/7")
        diff = p.changed_lines(before)
        self.assertEqual(1, len([d for d in diff if d[0] == "+"]), diff)
        old = [d[1] for d in diff if d[0] == "-"][0]
        new = [d[1] for d in diff if d[0] == "+"][0]
        self.assertEqual(old.replace("| active |", "| closed |"), new,
                         "the edit re-spaced cells it was not asked to change")

    def test_close_with_an_empty_discharged_by_is_refused(self):
        """*A promise closed with no account of how is indistinguishable from
        one abandoned quietly.*"""
        p = self.start()
        before = p.text()
        r = p.commit("--close", "rel/1", expect=1)
        self.assertIn("Discharged by", r.stderr)
        self.assertEqual(before, p.text())

    def test_close_fills_discharged_by_when_given_one(self):
        p = self.start()
        p.commit("--close", "rel/1", "--discharged-by", "shipped on the 30th")
        row = [l for l in p.text().split("\n") if "rel/1" in l][0]
        self.assertIn("shipped on the 30th", row)
        self.assertIn("closed", row)

    def test_miss_needs_a_reason(self):
        p = self.start()
        before = p.text()
        p.commit("--miss", "rel/1", expect=1)
        self.assertEqual(before, p.text())

    def test_miss_appends_to_discharged_by_rather_than_replacing_it(self):
        p = self.start()
        p.commit("--miss", "ops/7", "--reason", "the vendor went quiet")
        row = [l for l in p.text().split("\n") if "ops/7" in l][0]
        self.assertIn("oldest-first", row)
        self.assertIn("the vendor went quiet", row)
        self.assertIn("missed", row)

    def test_ending_a_row_twice_is_refused(self):
        p = self.start()
        p.commit("--close", "ops/7", "--discharged-by", "done")
        r = p.commit("--close", "ops/7", "--discharged-by", "done again",
                     expect=1)
        self.assertIn("already", r.stderr)

    def test_an_unknown_id_is_refused(self):
        p = self.start()
        p.commit("--close", "ops/999", "--discharged-by", "x", expect=1)


class TestAMissedCommitmentIsNeverSilentlyReDated(WriterCase):
    """*Editing `By when` on a promise whose date has passed erases the fact
    that it was missed, and the party it was made to is the one person who
    cannot see the edit.*"""

    def past(self) -> str:
        return f"{date.today() - timedelta(days=3):%Y-%m-%d}"

    def future(self) -> str:
        return f"{date.today() + timedelta(days=30):%Y-%m-%d}"

    def test_re_dating_a_past_due_active_row_is_refused(self):
        p = self.project(ALIGNED.format(past=self.past()))
        before = p.text()
        r = p.commit("--id", "rel/1", "--by", self.future(), expect=1)
        self.assertIn("--miss rel/1", r.stderr)
        self.assertEqual(before, p.text())

    def test_re_dating_a_row_still_in_the_future_is_allowed(self):
        """The refusal is about a promise that was MISSED, not about editing a
        date. A guard keyed on "is this an active row" would block the ordinary
        correction the procedure never forbade."""
        p = self.project(ALIGNED.format(past=self.future()))
        p.commit("--id", "rel/1", "--by",
                 f"{date.today() + timedelta(days=60):%Y-%m-%d}")

    def test_re_dating_a_past_due_row_that_was_already_missed_is_allowed(self):
        p = self.project(ALIGNED.format(past=self.past()))
        p.commit("--miss", "rel/1", "--reason", "slipped")
        p.commit("--id", "rel/1", "--by", self.future())

    def test_the_route_the_refusal_names_actually_works(self):
        p = self.project(ALIGNED.format(past=self.past()))
        p.commit("--miss", "rel/1", "--reason", "the build broke")
        p.commit("--track", "rel", "--promise", "Release 2.0",
                 "--to", "Users", "--by", self.future())
        self.assertIn("rel/2", p.text())
        self.assertEqual(
            2, sum(1 for e in p.events() if e["id"].startswith("rel/")))


class TestAHandEditIsReconciledNotOverwritten(WriterCase):
    """DESIGN-005 § 9: the log became canonical *before* this writer was built,
    and the cost the user accepted was that a hand edit *raises a reconcile
    prompt — never silently overwritten, and never silently authoritative*."""

    def edited(self) -> Project:
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        p.okr_path.write_text(
            p.text().replace("| ops/1 | ops | a | x | 5 days | active |",
                             "| ops/1 | ops | a | x | 5 days | closed |"))
        return p

    def test_a_row_the_log_disagrees_with_refuses(self):
        p = self.edited()
        before = p.text()
        r = p.commit("--miss", "ops/1", "--reason", "did not happen", expect=1)
        self.assertIn("by hand", r.stderr)
        self.assertIn("--accept-hand-edit", r.stderr)
        self.assertEqual(before, p.text())

    def test_accepting_takes_the_FILE_value_never_the_log_value(self):
        p = self.edited()
        p.commit("--miss", "ops/1", "--reason", "did not happen",
                 "--accept-hand-edit")
        last = p.events()[-1]
        self.assertEqual("closed", last["from"],
                         "the log's value was used instead of the file's")
        self.assertEqual("missed", last["to"])

    def test_a_row_the_log_has_never_heard_of_is_not_a_hand_edit(self):
        """Every Commitments table alive today was written by hand. Treating
        those rows as edits makes the first write on every real project a wall
        of reconcile prompts about work done correctly under the old rules."""
        p = self.project(ALIGNED.format(past="2027-01-01"))
        self.assertEqual([], p.events())
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")


class TestTheEventLog(WriterCase):

    def test_every_write_emits_one_event(self):
        p = self.project(ALIGNED.format(past="2027-01-01"))
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        p.commit("--close", "ops/7", "--discharged-by", "done")
        p.commit("--miss", "rel/1", "--reason", "slipped")
        p.commit("--id", "ops/8", "--promise", "a, revised")
        self.assertEqual(["commit", "commit-close", "commit-miss",
                          "commit-update"],
                         [e["event"] for e in p.events()])

    def test_no_event_name_collides_with_the_board_orphan_detector(self):
        """`perry-state § reconcile_drift` keys its orphan check on `add` /
        `route` and its close check on `done` / `drop`. A commitment id
        carrying one of those names would be reported as a task whose row went
        missing — a drift finding about a row that never existed."""
        self.assertFalse(set(G.COMMIT_EVENTS)
                         & {"add", "route", "done", "drop"})

    def test_a_refusal_writes_no_event(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x",
                 "--by", "soon", expect=1)
        self.assertEqual([], p.events())

    def test_the_okr_write_stands_even_when_the_event_cannot_be_appended(self):
        """`perry-task § commit` chose this failure direction and documents it:
        the canonical file never disagrees with itself, and the derived record
        may be missing. Losing an event costs history resolution; losing the
        write costs the truth."""
        p = self.project()
        (p.dir / ".perry" / "events.jsonl").mkdir()  # a directory, not a file
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--by", "5 days")
        self.assertIn("ops/1", p.text())
        self.assertIn("warning", r.stderr)


class TestTheHandOffContract(WriterCase):
    """`SKILL.md § The hand-off contract`: *each lane reads the others' files
    freely; no lane writes outside its own.*"""

    #: The rule is a predicate over the whole filesystem, so this is a
    #: category, not the three files the contract happens to name. A guard
    #: shaped around `BOARD.md` / `journal/` / `DECISIONS.md` would pass a
    #: write to `weekly/` that the same sentence forbids for the same reason.
    FOREIGN = ["BOARD.md", "journal/2026-08/2026-08-17.md", "DECISIONS.md",
               "decisions/ADR-001-x.md", "PROJECT_STATE.md",
               "evidence/2026-08/retro.md", "weekly/2026-W33.md",
               "handoff/session.md", "design/DESIGN-001-x.md"]

    def test_no_file_outside_the_goals_lane_can_be_written(self):
        p = self.project()
        for rel in self.FOREIGN:
            with self.subTest(path=rel):
                with self.assertRaises(G.Refused) as caught:
                    G.write_atomic(p.dir, p.dir / rel, "x")
                self.assertIn("hand-off contract", str(caught.exception))
                self.assertFalse((p.dir / rel).exists())

    def test_the_lane_it_names_is_the_right_one(self):
        p = self.project()
        for rel, lane in (("BOARD.md", "work"), ("journal/x.md", "work"),
                          ("DECISIONS.md", "decide"),
                          ("decisions/ADR-001.md", "decide")):
            with self.subTest(path=rel):
                with self.assertRaises(G.Refused) as caught:
                    G.write_atomic(p.dir, p.dir / rel, "x")
                self.assertIn(f"`{lane}`", str(caught.exception))

    def test_the_files_the_goals_lane_does_own_are_allowed(self):
        p = self.project()
        for rel in ("OKR.md", "phase/002-x.md", "phase/002-linkage.md",
                    "phase/CURRENT", "phase/snapshots/2026-08-17-002-x.md"):
            with self.subTest(path=rel):
                G.write_atomic(p.dir, p.dir / rel, "x")
                self.assertTrue((p.dir / rel).exists())

    def test_a_commit_leaves_every_other_lane_byte_identical(self):
        p = self.project()
        (p.dir / "BOARD.md").write_text("# board\n")
        (p.dir / "DECISIONS.md").write_text("# decisions\n")
        (p.dir / "journal").mkdir()
        (p.dir / "journal" / "2026-08-17.md").write_text("# day\n")
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--by", "5 days")
        self.assertEqual("# board\n", (p.dir / "BOARD.md").read_text())
        self.assertEqual("# decisions\n", (p.dir / "DECISIONS.md").read_text())
        self.assertEqual("# day\n",
                         (p.dir / "journal" / "2026-08-17.md").read_text())

    def test_the_board_side_link_is_printed_as_a_hand_off(self):
        """The `Commitment` cell is the `work` lane's write, and the link runs
        from the board side on purpose. A lane that needs a change in another
        lane's file asks in chat and stops."""
        p = self.project()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--by", "5 days")
        self.assertIn("hand-off", r.stdout)
        self.assertIn("ops/1", r.stdout)
        self.assertIn("does not write BOARD.md", r.stdout)


class TestTheLockAndTheGate(WriterCase):

    def test_a_write_takes_the_same_project_lock_the_other_writers_take(self):
        """DESIGN-005 § 5.4: one lock per project, not one per lane."""
        import fcntl
        import hashlib
        p = self.project()
        key = hashlib.sha1(str(p.dir.resolve()).encode()).hexdigest()[:16]
        lock = pathlib.Path(tempfile.gettempdir()) / f"perry-task-{key}.lock"
        with open(lock, "w") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                         "--by", "5 days", expect=1)
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        self.assertIn("another Perry write is holding", r.stderr)
        self.assertNotIn("Commitments", p.text())

    def test_the_conformance_gate_refuses_a_write_on_an_undeclared_file(self):
        """ADR-004. `perry-task` and `perry-decide` already gate; this one
        gates on `OKR.md`, its own file and no other."""
        p = self.project()
        before = p.text()
        r = p.run("commit", "--track", "ops", "--promise", "a", "--to", "x",
                  "--by", "5 days", expect=1, PERRY_CONFORMANCE="enforce")
        self.assertIn("ADR-004", r.stderr)
        self.assertEqual(before, p.text())

    def test_reading_is_never_gated(self):
        p = self.project()
        p.run("list", "--json", expect=0, PERRY_CONFORMANCE="enforce")

    def test_a_dry_run_writes_nothing(self):
        p = self.project()
        before = p.text()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--by", "5 days", "--dry-run", "--json")
        self.assertEqual(before, p.text())
        self.assertEqual([], p.events())
        self.assertTrue(json.loads(r.stdout)["dry_run"])


class TestALocalizedTable(WriterCase):

    def test_the_by_when_column_resolves_even_though_zh_shares_a_word(self):
        """`schema/state-schema.json § i18n.columns` maps BOTH `Deadline` and
        `By when` onto `截止`. Resolved globally, a Chinese Commitments table
        loses its `By when` column and a writer places the date by position.
        Resolution here is table-local, so the question has one answer."""
        p = self.project(CHINESE)
        p.commit("--track", "ops", "--promise", "报表", "--to", "审计",
                 "--by", "within the track SLA")
        row = [l for l in p.text().split("\n") if "ops/2" in l][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(["ops/2", "ops", "报表", "审计",
                          "within the track SLA", "active"], cells)

    def test_the_chinese_heading_is_found(self):
        p = self.project(CHINESE)
        p.commit("--close", "ops/1", "--discharged-by", "已完成")
        self.assertIn("closed", p.text())

    def test_a_widened_chinese_table_gets_a_chinese_header(self):
        """A table this tool can still read and a human cannot is the same
        failure as reformatting prose — the file stops being the user's."""
        p = self.project(CHINESE)
        p.commit("--close", "ops/1", "--discharged-by", "已完成")
        header = [l for l in p.text().split("\n") if l.startswith("| 编号")][0]
        self.assertTrue(header.endswith("| 由谁完成 |"), header)
        self.assertNotIn("Discharged by", p.text())


class TestWideningIsTheOnlyEditThatTouchesOtherRows(WriterCase):
    """`Discharged by` is optional in the schema, `--close` has nowhere to put
    its account without it, and refusing would strand a real promise on a table
    that is not malformed. So the table is widened — and that is the only edit
    here that reaches lines the caller did not name, which is why it is
    reported and why its exactness is tested."""

    NARROW = (ALIGNED.format(past="2027-01-01")
              .replace(" | Discharged by |", " |")
              .replace("|--------|---------------|", "|--------|")
              .replace("| active |               |", "| active |")
              .replace("| active | oldest-first  |", "| active |"))

    def narrow(self) -> Project:
        p = self.project(self.NARROW)
        self.assertNotIn("Discharged by", p.text())
        return p

    def test_an_untouched_row_gains_a_cell_and_loses_no_byte(self):
        p = self.narrow()
        old = [l for l in p.text().split("\n") if "rel/1" in l][0]
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        new = [l for l in p.text().split("\n") if "rel/1" in l][0]
        self.assertEqual(old + "  |", new,
                         "a row the edit did not name was re-spaced")

    def test_the_header_and_separator_keep_their_own_style(self):
        p = self.narrow()
        head = [l for l in p.text().split("\n") if l.startswith("| Track")][0]
        sep = [l for l in p.text().split("\n") if l.startswith("|-------")][0]
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        lines = p.text().split("\n")
        self.assertEqual(head + " Discharged by |",
                         [l for l in lines if l.startswith("| Track")][0])
        self.assertEqual(sep + "--------|",
                         [l for l in lines if l.startswith("|-------")][0],
                         "the separator was rewritten in another style")

    def test_prose_around_the_table_is_untouched(self):
        p = self.narrow()
        before = p.text().split("\n")
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        for old, new in zip(before, p.text().split("\n")):
            if not old.strip().startswith("|"):
                self.assertEqual(old, new)

    def test_the_widening_is_reported_to_the_user(self):
        p = self.narrow()
        r = p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        self.assertIn("widened", r.stdout)

    def test_a_create_never_widens_a_table_missing_a_required_column(self):
        """Padding every row of a register this tool did not write is not a
        repair a writer gets to make silently."""
        okr = ALIGNED.format(past="2027-01-01").replace(
            "| To whom ", "").replace("|---------|---------|", "|---------|")
        p = self.project(okr.replace("| Users   |", "").replace("| Finance |", ""))
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--by", "5 days", expect=1)
        self.assertIn("To whom", r.stderr)


class TestTheRealFilesOnThisMachine(WriterCase):
    """Rule 3 of this task: against COPIES, never the originals."""

    def copy_of(self, source: pathlib.Path) -> Project | None:
        if not source.exists():
            return None
        p = Project(source.read_text(), tracks=None)
        self.addCleanup(p.cleanup)
        return p

    def test_both_refuse_and_change_nothing(self):
        """Neither project declares a `pipeline` or `queue` track, and neither
        `OKR.md` has a `## Commitments` section. The correct answer is a
        refusal that names the modes the section serves — and a file that is
        byte-identical afterwards."""
        found = 0
        for source in ELSEWHERE:
            p = self.copy_of(source)
            if p is None:
                continue
            found += 1
            with self.subTest(path=str(source)):
                before = p.text()
                r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                             "--by", "5 days", expect=1)
                self.assertIn("pipeline", r.stderr)
                self.assertEqual(before, p.text())
                self.assertEqual(source.read_text(), before,
                                 "the ORIGINAL was touched")
        if not found:
            self.skipTest(f"none of {[str(p) for p in ELSEWHERE]} present")

    def test_a_declared_queue_track_makes_the_section_land_cleanly(self):
        """The other half of the same question: given a track that needs the
        spine, does the section land in a real, unusual file without
        disturbing it? gimegime nests `### Anti-Goals` INSIDE a version, so a
        naive insert-before-Anti-Goals lands in the middle of `## v2`."""
        found = 0
        for source in ELSEWHERE:
            if not source.exists():
                continue
            found += 1
            p = Project(source.read_text(), tracks=TRACKS)
            self.addCleanup(p.cleanup)
            with self.subTest(path=str(source)):
                before = p.text()
                p.commit("--track", "ops", "--promise", "Statements filed",
                         "--to", "Auditor", "--by", "within the track SLA")
                added = [d for d in p.changed_lines(before) if d[0] == "-"]
                self.assertEqual([], added, "an existing line was rewritten")
                lines = p.text().split("\n")
                at = next(i for i, l in enumerate(lines)
                          if l.startswith("## Commitments"))
                # not swallowed by a version block
                prior = [l for l in lines[:at] if l.startswith("## ")]
                self.assertFalse(any(l.startswith("## v") for l in prior),
                                 f"landed inside {prior[-1] if prior else '?'}")
        if not found:
            self.skipTest(f"none of {[str(p) for p in ELSEWHERE]} present")


class TestTheReadContractDidNotMove(unittest.TestCase):
    """`perry-goals/list/2.0` is frozen and published. Shipping a writer is not
    a read-contract change, and this says so where it can fail."""

    def test_the_version_is_unchanged(self):
        self.assertEqual("perry-goals/list/2.0", G.LIST_CONTRACT)

    def test_the_contract_document_agrees(self):
        doc = (ROOT / "schema" / "goals-list-contract.md").read_text()
        self.assertIn(G.LIST_CONTRACT, doc)
        self.assertIn("## Changelog", doc)


class TestTheClockRuleIsEnforcedInBothLanguages(unittest.TestCase):
    """`CLOCK_RE` required a whole word in English and a bare character in
    Chinese.

    `[天日周月年]` matched any stray 日 or 年, so **`日后再说`** ("we'll talk
    about it later"), `改天` and `年后再说` were **accepted and written into
    `OKR.md` as live `By when` values** — while the English `when we get to it`
    and the criteria file's own `有空再说` were correctly refused.

    A rule enforced in one language and not the other is worse than a rule
    enforced in neither: a Chinese project got a commitments register full of
    deadlines that are not deadlines, and passed every check.

    Found by a V4 reviewer. The second half — `3d` and `2w`, the shorthand
    Perry's own `## Tracks` examples use — was **refused** by the same pattern,
    so a legitimate SLA could not be written either.
    """

    CLOCKS = ["2026-09-30", "3d", "5 d", "2w", "2 weeks", "within the SLA",
              "30 days", "hourly", "5个工作日", "两周内", "三天", "24小时",
              "季度末", "月底", "本周内", "时限内"]
    VAGUE = ["日后再说", "改天", "年后再说", "有空再说", "尽快", "有时间了做",
             "when we get to it", "next time we look at it", "best effort",
             "soon", "ASAP", "when resourcing allows"]

    def test_every_real_clock_is_accepted_in_both_languages(self):
        for v in self.CLOCKS:
            with self.subTest(value=v):
                self.assertTrue(G.CLOCK_RE.search(v), f"{v!r} is a clock")

    def test_every_vague_promise_is_refused_in_both_languages(self):
        for v in self.VAGUE:
            with self.subTest(value=v):
                self.assertFalse(G.CLOCK_RE.search(v),
                                 f"{v!r} names no clock and was accepted")

    def test_the_two_languages_are_held_to_the_same_standard(self):
        """The property, not the instances: for each pair meaning the same
        thing, the two must agree. This is what a per-language list of
        phrases cannot assert."""
        pairs = [("日后再说", "when we get to it"),
                 ("尽快", "ASAP"),
                 ("两周内", "within 2 weeks"),
                 ("三天", "3 days")]
        for zh, en in pairs:
            with self.subTest(pair=(zh, en)):
                self.assertEqual(
                    bool(G.CLOCK_RE.search(zh)), bool(G.CLOCK_RE.search(en)),
                    f"{zh!r} and {en!r} mean the same and are judged "
                    f"differently")

    def test_a_bare_unit_with_no_quantity_is_not_a_clock(self):
        """The category. `日` alone is a character, not a deadline — it becomes
        one when something counts or bounds it."""
        for v in ["日", "年", "周", "月"]:
            with self.subTest(value=v):
                self.assertFalse(G.CLOCK_RE.search(v))


class TestCreateAndAmendAgreeAboutWhatACellCanHold(unittest.TestCase):
    """One tool, one value, two answers.

    `commit --promise $'a\\n\\nb'` was **refused** on the create path and
    **silently collapsed** on every amend path — `--miss --reason`,
    `--id --promise` and `--close --discharged-by` — because `splice_cell`
    carried its own `.replace("\\n", " ")` instead of `render_row`'s rule. A
    user writing a two-paragraph promise got a refusal from one subcommand and
    a quietly mangled cell from another.

    The reviewer's finding also included that **none of these three functions
    had any test coverage at all** — `splice_cell`, `append_cell` and
    `UnrenderableCell` appeared nowhere in this file. They now live in
    `viewer/tables.py` beside `split_row`, which is where the builder said they
    belonged and could not put them at the time.
    """

    OKR = ("# OKR\n\n## Mission\n\nx\n\n## Commitments\n\n"
           "| Id | Track | Promise | To whom | By when | Status | Discharged by |\n"
           "|---|---|---|---|---|---|---|\n"
           "| C-1 | ops | keep it up | Finance | 3d | active | — |\n")
    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | OKR.md | new,triaged | — | 3d | — | V2 |\n")

    def project(self):
        return Project(okr=self.OKR, tracks=self.TRACKS)

    MULTILINE = "first paragraph\n\nsecond paragraph"

    def test_the_amend_paths_refuse_what_create_refuses(self):
        for argv in (["--id", "C-1", "--miss", "--reason", self.MULTILINE],
                     ["--id", "C-1", "--promise", self.MULTILINE],
                     ["--id", "C-1", "--close",
                      "--discharged-by", self.MULTILINE]):
            with self.subTest(path=argv[2]):
                p = self.project()
                before = p.okr_path.read_bytes()
                out = p.run("commit", *argv)
                self.assertEqual(out.returncode, 1,
                                 f"accepted silently: {out.stderr}")
                self.assertEqual(p.okr_path.read_bytes(),
                                 before, "a refusal wrote to the file")

    def test_the_refusal_says_what_is_wrong_rather_than_collapsing(self):
        p = self.project()
        out = p.run("commit", "--id", "C-1", "--promise", self.MULTILINE)
        self.assertEqual(out.returncode, 1)
        self.assertIn("line break", (out.stderr + out.stdout).lower())

    def test_a_pipe_is_escaped_rather_than_refused_on_both_paths(self):
        """`|` round-trips, so it is carried; `\\n` cannot, so it is refused.
        The two are not the same and the tool must not treat them alike."""
        p = self.project()
        out = p.run("commit", "--id", "C-1", "--promise", "A | B")
        self.assertEqual(out.returncode, 0, out.stderr)
        text = p.okr_path.read_text(encoding="utf-8")
        self.assertIn("A \\| B", text)
        row = [l for l in text.split("\n") if l.startswith("| C-1")][0]
        self.assertEqual(len(T.split_row(row)), 7, row)

    def test_one_cell_changes_and_the_rest_of_the_row_keeps_its_bytes(self):
        """The reason `splice_cell` exists rather than `render_row` on a parsed
        row: a hand-aligned table stays aligned everywhere the edit did not
        reach."""
        p = self.project()
        before = [l for l in p.okr_path.read_text().split("\n")
                  if l.startswith("| C-1")][0]
        p.run("commit", "--id", "C-1", "--promise", "changed")
        after = [l for l in p.okr_path.read_text().split("\n")
                 if l.startswith("| C-1")][0]
        self.assertNotEqual(before, after)
        self.assertEqual(T.split_row(before)[3:], T.split_row(after)[3:],
                         "cells the edit did not name were rewritten")


if __name__ == "__main__":
    unittest.main()
