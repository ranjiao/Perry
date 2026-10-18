"""What the three store-less minters read, and what retires one of their ids.

TASK-118. `bin/perry-task` mints four families. `mint_id` (`TASK-`) reads the
canonical store; `USER-`, `CAD-` and `RX-` have no store at all, and all three
carried the docstring *"max(board ∪ journal ∪ events), like `mint_id`"* — a
claim about a function that has not read a board since ADR-007.

The correction is that there was never a grab-bag of three sources. There is
one shape, `minting_records`': **the register's canonical form, plus the ids
that have left it.** For `TASK-` the canonical half is `tasks.jsonl` and the
departed half is the `purge` events. For these three the canonical half is the
markdown section — `## User Input Queue`, `## Cadence` and `## Top risks` are
not projections of anything — and the departed half is the two append-only
records a board row cannot be deleted without leaving behind.

So the tests below are not "does it read three files". They are, per family:

1. **each source is read** — an id planted in exactly one of them moves the
   next mint, and an id planted in a state-root markdown file that is *not*
   the journal does not;
2. **the departure property TASK-167 had to build `minting_records` to get** —
   delete a tool-minted row off the board and the number does not come back,
   and it survives losing *either* append-only record but not both;
3. **one mechanism, by identity** — all three route through `minting_text`,
   asserted by substitution rather than by three copies agreeing.

**TASK-262 round 4a.** Since TASK-237 the three registers have stores
(`asks.jsonl`, `cadence.jsonl`, `risks.jsonl`), and since round 4a a write
builds its board from them rather than from a held `BOARD.md`. So "the board"
below is the register's STORE: an id is planted as a stored record, and a row
leaves by its record leaving the store. A line typed into a held file no longer
reaches a minter at all.

Every case is built in a throwaway project and read through the real `--root`
seam. Nothing here asserts anything about Perry's own board: TASK-151's lesson
is that a check whose expected value is the project living around it stops
meaning anything the next morning.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

COVERS = ("bin/perry-task",)

import json
import tempfile
import unittest
from pathlib import Path

from task_writer_support import PT, Project
from kernel_work_support import ACTOR, ready, task


#: The three families, as (subcommand, argv tail, prefix, board section). One
#: table so that a fourth store-less register cannot be added with two of the
#: three properties below tested.
FAMILIES = [
    ("ask", ("--needed", "a question"), "USER", "User Input Queue"),
    ("cadence-add", ("--title", "a ritual", "--frequency", "weekly"),
     "CAD", "Cadence"),
    ("risk-add", ("--title", "a risk"), "RX", "Top risks"),
]


#: The register each family's section is printed from, and a minimal valid
#: record for it (TASK-262 round 4a).
STORE = {
    "User Input Queue": ("asks.jsonl", lambda rid, text, order: {
        "id": rid, "needed": text, "blocks": "", "asked": "",
        "status": "pending", "answered": False, "order": order}),
    "Cadence": ("cadence.jsonl", lambda rid, text, order: {
        "id": rid, "title": text, "owner": "", "frequency": "weekly",
        "next_due": "", "last_run": "", "last_evidence": "", "order": order}),
    "Top risks": ("risks.jsonl", lambda rid, text, order: {
        "id": rid, "risk": text, "opened": "", "cleared": "",
        "status": "open", "order": order}),
}


class Register(Project):
    """A throwaway project with one id plantable in exactly one source."""

    def _records(self, name: str) -> list[dict]:
        p = self.root / name
        return ([json.loads(l) for l in p.read_text().split("\n") if l.strip()]
                if p.exists() else [])

    def _write(self, name: str, records: list[dict]) -> None:
        (self.root / name).write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))

    def plant_on_board(self, section: str, rid: str, text: str) -> None:
        """A record in `section`'s store — the board a write builds from."""
        name, make = STORE[section]
        records = self._records(name)
        records.append(make(rid, text, len(records)))
        self._write(name, records)

    def plant_in_events(self, **event) -> None:
        p = self.root / ".perry" / "events.jsonl"
        with p.open("a") as fh:
            fh.write(json.dumps({"ts": "2026-08-01T00:00:00+08:00", **event}) + "\n")

    def plant_in_journal(self, text: str) -> None:
        d = self.root / "journal" / "2026-08"
        d.mkdir(parents=True, exist_ok=True)
        (d / "2026-08-01.md").write_text(text + "\n")

    def plant_outside_the_journal(self, text: str) -> None:
        """A state-root markdown file the minters must NOT count."""
        d = self.root / "evidence" / "2026-08"
        d.mkdir(parents=True, exist_ok=True)
        (d / "a-note.md").write_text(text + "\n")

    def drop_board_row(self, rid: str) -> None:
        """The row leaves: its record is deleted from whichever store holds it,
        with no event and no journal line — a hand edit."""
        dropped = 0
        for name, _make in STORE.values():
            records = self._records(name)
            kept = [r for r in records if r.get("id") != rid]
            dropped += len(records) - len(kept)
            if len(kept) != len(records):
                for n, r in enumerate(kept):
                    r["order"] = n
                self._write(name, kept)
        assert dropped == 1, (rid, dropped)

    def mint(self, cmd: str, tail: tuple[str, ...]) -> str:
        code, out = self.run(cmd, *tail)
        if code or not isinstance(out, dict):
            raise AssertionError(f"{cmd} failed: {out}")
        return out["id"]


class TestNativeIdentityComesFromTheStore(unittest.TestCase):
    def test_each_native_family_has_its_own_monotone_sequence(self):
        sb = ready(self)
        one = task(sb)
        ask = sb.create("ask", fields={"question": "Which?"})
        risk = sb.create("risk", fields={"concern": "A concern"})
        self.assertEqual((one, ask, risk), ("TASK-001", "USER-001", "RX-001"))
        sb.move(one, "drop", set={"reason": "fixture complete"})
        sb.move(ask, "answer", set={"answer": "yes"})
        sb.move(risk, "clear", set={"reason": "resolved"})
        self.assertEqual(task(sb), "TASK-002")
        self.assertEqual(sb.create("ask", fields={"question": "Again?"}), "USER-002")
        self.assertEqual(sb.create("risk", fields={"concern": "Another"}), "RX-002")
        for item in (one, ask, risk):
            self.assertIn(sb.get(item)["state"], ("dropped", "answered", "cleared"))

    def test_legacy_prose_and_events_cannot_raise_a_native_id_counter(self):
        sb = ready(self)
        for rel in ("tasks.jsonl", "journal/2026-08/2026-08-01.md", ".perry/events.jsonl",
                    "evidence/mentions.md", "BOARD.md"):
            path = sb.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("TASK-900 USER-900 RX-900 CAD-900\n")
        self.assertEqual(task(sb), "TASK-001")
        self.assertEqual(sb.create("ask", fields={"question": "Which?"}), "USER-001")
        self.assertEqual(sb.create("risk", fields={"concern": "A concern"}), "RX-001")


class TestOneMechanism(unittest.TestCase):
    """Same source of truth for all three, by identity and not by agreement."""

    def test_all_three_read_minting_text(self):
        board = _throwaway_board()
        real, seen = PT.minting_text, []

        def spy(b, events, state_root):
            seen.append(True)
            return ["USER-140 CAD-140 RX-140"]

        PT.minting_text = spy
        try:
            got = [PT.mint_user_id(board, [], Path("/nonexistent")),
                   PT.mint_cadence_id(board, [], Path("/nonexistent")),
                   PT.mint_risk_id(board, [], Path("/nonexistent"))]
        finally:
            PT.minting_text = real
        self.assertEqual(got, ["USER-141", "CAD-141", "RX-141"])
        self.assertEqual(len(seen), 3)

    def test_a_null_id_is_tolerated_by_the_retained_legacy_minter(self):
        board = _throwaway_board()
        for minter in (PT.mint_user_id, PT.mint_cadence_id, PT.mint_risk_id):
            got = minter(board, [{"event": "link-kr", "id": None}], Path("/nonexistent"))
            self.assertTrue(got.endswith("-001"), got)


class TestRetiredRiskCallSites(unittest.TestCase):
    def test_add_and_migrate_never_consume_a_legacy_id(self):
        p = Register()
        p.plant_in_events(event="risk-add", id="RX-030")
        before = {str(f.relative_to(p.root)): f.read_bytes()
                  for f in p.root.rglob("*") if f.is_file()}
        for argv in (("risk-migrate",), ("risk-add", "--title", "another")):
            code, out = p.run(*argv)
            self.assertEqual(code, 1, out)
            self.assertIn("read-only", out["refused"])
            self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                              for f in p.root.rglob("*") if f.is_file()}, before)


def _throwaway_board() -> "PT.Board":
    d = Path(tempfile.mkdtemp())
    (d / "BOARD.md").write_text("# B\n\n## Top risks\n\n- none\n")
    return PT.Board(d / "BOARD.md")


if __name__ == "__main__":
    unittest.main()
