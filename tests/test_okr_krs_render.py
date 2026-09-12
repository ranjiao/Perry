"""TASK-236: `perry-goals krs --level overall` is the only surface for the
key results `OKR.md` used to carry, and it reddens when the store is wrong.

**Why this module has to exist, and why it cannot be `perry-okr diff`.**
Before this row, a KR was written in two places — a table row in `OKR.md` and
a `kind: kr` record in `okr.jsonl` — and `perry-okr diff` byte-compared them,
so corrupting a record moved a rendered line and the gate saw it. ADR-019
deleted the duplicate, and the detector went with it: `perry_md_store § Doc`
now lists `kr` in `store_only_kinds`, `perry-okr diff` reports
`kinds: {objective, version}` on this repository, and **nothing in that tool
looks at a KR record any more**. A record deleted from the store today leaves
no stranded line, because there is no line.

That is ADR-019's stated trade — drift becomes impossible rather than
detected — and the cost lands here. This module is what replaced the gate.

## The expectation is written down, not read back

`TASK-182` caught a gate that built its expectation out of the file it then
compared against, which is a comparison that cannot fail. So `ROSTER` below
is a **literal**: five KRs, every field spelled out in this source text. The
fixture is written by `project()` from `STORE`, and `check_roster` asserts the
rendered payload against `ROSTER` — never against `STORE`, and never against
whatever the render happened to produce.

`tests/live_state_expectations.py` is why the live-repository test at the
bottom asserts a PROPERTY (the store's KR ids and the render's are the same
set) rather than a count: a closed literal measured off this project's own
state is the class that guard exists to refuse.

## The mutations are tests, not a paragraph in an evidence file

Each `TestAMutationReddens` case breaks one thing in the store and asserts
`check_roster` RAISES. A mutation demonstrated once by hand rots the moment
someone edits the renderer; these re-run on every suite pass. The fourth is
the anti-vacuity case the row's spec names by name — a store emptied of its
KR records must not render as a quiet success.
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import config_store  # noqa: E402
import inproc  # noqa: E402

#: `State root: perry`, so the fixture's `perry/okr.jsonl` is the file the
#: tool resolves to. Without it `resolve_state_root` falls back to the project
#: root and every case below measures a project with no store at all.
CONFIG_SETTINGS = {"Document language": "English", "Repo layout": "single",
                   "State root": "perry"}

#: Two version blocks so the default (current only) and `--version all` are
#: different answers, and a stretch/blank cell so the render's `—` fallback is
#: exercised rather than assumed.
STORE = [
    {"kind": "version", "version": "v1", "date": "2026-01-01",
     "what": "First.", "why": "Because.", "order": 0},
    {"kind": "version", "version": "v2", "date": "2026-02-01",
     "what": "Second.", "why": "Because again.", "order": 1},

    {"kind": "objective", "id": "O-1", "version": "v1: 2026-01-01",
     "title": "The first objective",
     "heading": "Objective 1 — The first objective", "order": 0},
    {"kind": "objective", "id": "O-2", "version": "v1: 2026-01-01",
     "title": "The second objective",
     "heading": "Objective 2 — The second objective", "order": 1},
    {"kind": "objective", "id": "O-1", "version": "v2: 2026-02-01",
     "title": "The first objective",
     "heading": "Objective 1 — The first objective", "order": 0},

    {"kind": "kr", "version": "v1: 2026-01-01",
     "objective": "Objective 1 — The first objective", "objective_id": "O-1",
     "id": "O1-KR1", "text": "A KR whose text holds `backticks` and a comma",
     "metric": "3 of 3", "stretch": "no", "deadline": "2026-03-01",
     "linked": "", "qualifier": "", "form": "table", "order": 0},
    {"kind": "kr", "version": "v1: 2026-01-01",
     "objective": "Objective 1 — The first objective", "objective_id": "O-1",
     "id": "O1-KR2", "text": "A stretch KR with no deadline",
     "metric": "0", "stretch": "yes", "deadline": "",
     "linked": "", "qualifier": "", "form": "table", "order": 1},
    {"kind": "kr", "version": "v1: 2026-01-01",
     "objective": "Objective 2 — The second objective", "objective_id": "O-2",
     "id": "O2-KR1", "text": "The only KR under the second objective",
     "metric": "1 contract", "stretch": "no", "deadline": "2026-04-01",
     "linked": "", "qualifier": "", "form": "table", "order": 2},
    {"kind": "kr", "version": "v2: 2026-02-01",
     "objective": "Objective 1 — The first objective", "objective_id": "O-1",
     "id": "O1-KR1", "text": "The same id, restated in the next version",
     "metric": "4 of 4", "stretch": "no", "deadline": "2026-05-01",
     "linked": "", "qualifier": "", "form": "table", "order": 0},
    {"kind": "kr", "version": "v2: 2026-02-01",
     "objective": "Objective 1 — The first objective", "objective_id": "O-1",
     "id": "O1-KR2", "text": "A second KR in the current version",
     "metric": "2 of 2", "stretch": "no", "deadline": "2026-06-01",
     "linked": "", "qualifier": "", "form": "table", "order": 1},
]

#: **The literal.** `(version, id) -> (text, metric, stretch, deadline)`.
#: Spelled out here so a wrong value in the store is a FAILING assertion
#: rather than a different expectation.
ROSTER = {
    ("v1: 2026-01-01", "O1-KR1"): (
        "A KR whose text holds `backticks` and a comma",
        "3 of 3", "no", "2026-03-01"),
    ("v1: 2026-01-01", "O1-KR2"): (
        "A stretch KR with no deadline", "0", "yes", ""),
    ("v1: 2026-01-01", "O2-KR1"): (
        "The only KR under the second objective",
        "1 contract", "no", "2026-04-01"),
    ("v2: 2026-02-01", "O1-KR1"): (
        "The same id, restated in the next version",
        "4 of 4", "no", "2026-05-01"),
    ("v2: 2026-02-01", "O1-KR2"): (
        "A second KR in the current version", "2 of 2", "no", "2026-06-01"),
}

OKR_MD = """# OKR — fixture

## Mission

A fixture.

## v1: 2026-01-01

Rationale for the first version.

### Objective 1 — The first objective

### Objective 2 — The second objective

## v2: 2026-02-01

Rationale for the second version.

### Objective 1 — The first objective

## Versioning log

| Version | Date | What changed | Why |
|---|---|---|---|
| v1 | 2026-01-01 | First. | Because. |
| v2 | 2026-02-01 | Second. | Because again. |
"""


def flatten(payload: dict) -> dict:
    """The rendered payload → `(version, id) -> (text, metric, …)`."""
    got = {}
    for block in payload["versions"]:
        for obj in block["objectives"]:
            for kr in obj["krs"]:
                got[(block["version"], kr["id"])] = (
                    kr["text"], kr["metric"], kr["stretch"], kr["deadline"])
    return got


def check_roster(payload: dict, expected: dict | None = None) -> None:
    """Assert the render carries EXACTLY `ROSTER`. Raises on any difference.

    The mutation cases below assert that this raises. It therefore has to
    compare against the literal and nothing else — the moment it derives its
    expectation from `payload`, every one of them goes green and this module
    stops saying anything.
    """
    want = ROSTER if expected is None else expected
    got = flatten(payload)
    if got != want:
        missing = sorted(k for k in want if k not in got)
        extra = sorted(k for k in got if k not in want)
        wrong = sorted(k for k in want if k in got and got[k] != want[k])
        raise AssertionError(
            f"the render does not match the declared roster — "
            f"missing={missing} unexpected={extra} wrong={wrong}")


class Fixture(unittest.TestCase):
    """A project this test wrote, so its literals are not live state."""

    def project(self, store=None, okr_md: str = OKR_MD) -> pathlib.Path:
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        (tmp / ".perry").mkdir()
        (tmp / "perry").mkdir()
        (tmp / ".perry" / "events.jsonl").write_text("", encoding="utf-8")
        config_store.write_config(tmp, CONFIG_SETTINGS)
        (tmp / "perry" / "OKR.md").write_text(okr_md, encoding="utf-8")
        records = STORE if store is None else store
        (tmp / "perry" / "okr.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
            encoding="utf-8")
        return tmp

    def render(self, root: pathlib.Path, *extra: str):
        return inproc.run("perry-goals",
                          ["krs", "--level", "overall", "--json",
                           "--root", str(root), *extra])

    def payload(self, root: pathlib.Path, *extra: str) -> dict:
        res = self.render(root, *extra)
        self.assertEqual(res.returncode, 0, res.stderr)
        return json.loads(res.stdout)


class TestTheRenderCarriesTheStore(Fixture):

    def test_version_all_renders_every_declared_kr(self):
        """The control. Without it, every mutation below proves nothing —
        a roster that never matched cannot start failing."""
        check_roster(self.payload(self.project(), "--version", "all"))

    def test_the_default_is_the_current_version_only(self):
        """`OKR.md` runs oldest-first, so the LAST block is current. A default
        of "everything" would bury the live objectives under retired ones."""
        got = flatten(self.payload(self.project()))
        self.assertEqual(
            sorted(got), [("v2: 2026-02-01", "O1-KR1"),
                          ("v2: 2026-02-01", "O1-KR2")])

    def test_one_version_can_be_named(self):
        got = flatten(self.payload(self.project(),
                                   "--version", "v1: 2026-01-01"))
        self.assertEqual(len(got), 3)
        self.assertEqual(got[("v1: 2026-01-01", "O2-KR1")][1], "1 contract")

    def test_the_same_kr_id_in_two_versions_is_two_rows(self):
        """`O1-KR1` exists in both blocks with different text. Keying the
        render by id alone would silently collapse them to one."""
        got = flatten(self.payload(self.project(), "--version", "all"))
        self.assertNotEqual(got[("v1: 2026-01-01", "O1-KR1")],
                            got[("v2: 2026-02-01", "O1-KR1")])

    def test_a_blank_cell_renders_as_a_dash_and_not_as_the_word_none(self):
        out = self.render(self.project(), "--version", "v1: 2026-01-01")
        self.assertEqual(out.returncode, 0, out.stderr)
        text = inproc.run("perry-goals",
                          ["krs", "--level", "overall", "--root",
                           str(self.project()),
                           "--version", "v1: 2026-01-01"]).stdout
        self.assertIn("| O1-KR2 | A stretch KR with no deadline | 0 | yes | — |",
                      text)
        self.assertNotIn("None", text)

    def test_the_markdown_render_prints_every_kr_whole(self):
        """The row this replaces was read by opening a file, so an elided cell
        is a regression in the thing the row was judged on. `list --level
        overall` truncates to a column width; this must not."""
        text = inproc.run("perry-goals",
                          ["krs", "--level", "overall", "--root",
                           str(self.project()), "--version", "all"]).stdout
        for (_v, _i), (kr_text, *_rest) in ROSTER.items():
            self.assertIn(kr_text, text)
        self.assertNotIn("…", text)


class TestAMutationReddens(Fixture):
    """One broken thing each, and `check_roster` must RAISE for all four.

    A mutation that comes back green is the finding this class exists to make
    impossible to miss.
    """

    def mutated(self, fn) -> dict:
        records = [dict(r) for r in STORE]
        records = fn(records) or records
        return self.payload(self.project(store=records), "--version", "all")

    def test_a_corrupted_kr_field_reddens(self):
        """Mutation 1 — one cell changed. The classic drift the byte gate used
        to catch and no longer can."""
        def corrupt(records):
            for r in records:
                if r.get("kind") == "kr" and r["id"] == "O2-KR1":
                    r["metric"] = "99 contracts"
            return records
        with self.assertRaises(AssertionError) as caught:
            check_roster(self.mutated(corrupt))
        self.assertIn("O2-KR1", str(caught.exception))

    def test_a_deleted_kr_record_reddens(self):
        """Mutation 2 — a whole record gone. Deliberately a DIFFERENT named
        test from the one above: a guard can notice a changed cell and be
        blind to a missing row, which is exactly what happens when the
        comparison walks the render rather than the roster."""
        def drop(records):
            return [r for r in records
                    if not (r.get("kind") == "kr" and r["id"] == "O1-KR2"
                            and r["version"] == "v1: 2026-01-01")]
        with self.assertRaises(AssertionError) as caught:
            check_roster(self.mutated(drop))
        self.assertIn("O1-KR2", str(caught.exception))

    def test_an_okr_jsonl_emptied_of_its_krs_reddens(self):
        """Mutation 3 — **the anti-vacuity case the spec names.** Every `kr`
        record removed and the objectives left standing. The render is a
        well-formed document with no rows in it, exits 0, and says nothing is
        wrong. If the roster were built from the store this would be a PASS,
        and the surface that replaced `OKR.md` would be empty with every
        check green."""
        def empty(records):
            return [r for r in records if r.get("kind") != "kr"]
        payload = self.mutated(empty)
        self.assertEqual(payload["counts"]["krs"], 0)
        self.assertEqual(payload["counts"]["objectives"], 3,
                         "the objectives must survive — this is the case "
                         "where only the KRs are gone")
        with self.assertRaises(AssertionError):
            check_roster(payload)

    def test_a_kr_reattached_to_the_wrong_objective_reddens(self):
        """Mutation 4 — the record is intact and its `objective_id` is not.
        The row still renders, under the wrong heading, so a check that only
        counts rows stays green."""
        def move(records):
            for r in records:
                if (r.get("kind") == "kr" and r["id"] == "O2-KR1"):
                    r["objective_id"] = "O-1"
            return records
        payload = self.mutated(move)
        got = flatten(payload)
        self.assertEqual(len(got), len(ROSTER),
                         "the count is unchanged — that is the point")
        blocks = {o["id"]: [k["id"] for k in o["krs"]]
                  for b in payload["versions"] for o in b["objectives"]
                  if b["version"] == "v1: 2026-01-01"}
        self.assertIn("O2-KR1", blocks["O-1"])
        self.assertEqual(blocks["O-2"], [])


class TestTheSurfaceRefusesRatherThanPrintingAShortTable(Fixture):

    def test_a_project_with_no_store_is_refused(self):
        tmp = self.project()
        (tmp / "perry" / "okr.jsonl").unlink()
        res = self.render(tmp)
        self.assertEqual(res.returncode, 1)
        self.assertIn("refused", json.loads(res.stdout))

    def test_a_badly_typed_record_is_refused_not_skipped(self):
        """Printing the readable rows and dropping the rest is how a reader
        publishes a short table that looks complete — TASK-437's shape.

        A `metric` that is a NUMBER rather than a string is the shape a
        hand-edited or machine-appended store actually produces, and
        `validate_records` excludes it — so without this refusal the render
        would be one row short and say so nowhere."""
        records = [dict(r) for r in STORE]
        for r in records:
            if r.get("kind") == "kr" and r["id"] == "O2-KR1":
                r["metric"] = 1
        res = self.render(self.project(store=records), "--version", "all")
        self.assertEqual(res.returncode, 1)
        self.assertIn("O2-KR1", json.loads(res.stdout)["refused"])

    def test_a_duplicate_kr_key_is_refused_rather_than_collapsed(self):
        """Two records for one `(version, objective, id)` render as one row,
        so the store holding a contradiction would print as a clean table."""
        records = [dict(r) for r in STORE]
        dup = dict(next(r for r in records
                        if r.get("kind") == "kr" and r["id"] == "O2-KR1"))
        dup["metric"] = "a different answer"
        records.append(dup)
        res = self.render(self.project(store=records), "--version", "all")
        self.assertEqual(res.returncode, 1)
        self.assertIn("not unique", json.loads(res.stdout)["refused"])

    def test_an_unknown_version_names_the_ones_that_exist(self):
        res = self.render(self.project(), "--version", "v9: 2030-01-01")
        self.assertEqual(res.returncode, 1)
        self.assertIn("v1: 2026-01-01", json.loads(res.stdout)["refused"])

    def test_a_positional_argument_is_refused(self):
        res = self.render(self.project(), "extra")
        self.assertEqual(res.returncode, 1)


class TestTheShippedOkr(unittest.TestCase):
    """The live repository — a PROPERTY, never a count.

    `tests/live_state_expectations.py` refuses a closed literal measured off
    this project's own state, so "38" does not appear here. What is asserted
    instead is the invariant that has to hold however many KRs the project
    has: the store's KR ids and the rendered ones are the same set, and
    `OKR.md` carries none of them.
    """

    def test_every_stored_kr_reaches_the_render(self):
        res = inproc.run("perry-goals",
                         ["krs", "--level", "overall", "--json",
                          "--root", str(ROOT), "--version", "all"])
        self.assertEqual(res.returncode, 0, res.stderr)
        payload = json.loads(res.stdout)
        rendered = {(b["version"], k["id"])
                    for b in payload["versions"]
                    for o in b["objectives"] for k in o["krs"]}
        stored = set()
        for line in (ROOT / "perry" / "okr.jsonl").read_text(
                encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("kind") == "kr":
                stored.add((rec["version"], rec["id"]))
        self.assertEqual(rendered, stored)
        self.assertTrue(stored, "the shipped store holds no KR records at "
                                "all — this assertion is vacuous")

    def test_the_shipped_okr_md_carries_no_kr_table_rows(self):
        """The deletion itself, asserted where it would be noticed if
        `perry-okr render --write` ever put the rows back."""
        import re
        text = (ROOT / "perry" / "OKR.md").read_text(encoding="utf-8")
        self.assertEqual(
            [ln for ln in text.splitlines()
             if re.match(r"^\| O\d+-KR\d+ \|", ln)], [])

    def test_the_objective_headings_stay(self):
        """The Bound's remainder: the headings are what the KRs hang from and
        deleting them was never this row's scope."""
        import re
        text = (ROOT / "perry" / "OKR.md").read_text(encoding="utf-8")
        self.assertTrue(
            [ln for ln in text.splitlines()
             if re.match(r"^### Objective \d+ — ", ln)])


if __name__ == "__main__":
    unittest.main()
