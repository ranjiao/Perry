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

import json
import tempfile
import unittest
from pathlib import Path

from task_writer_support import PT, Project


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


class TestEverySourceIsRead(unittest.TestCase):
    """An id in exactly one source still moves the next mint."""

    def test_an_empty_project_starts_at_001(self):
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                self.assertEqual(Register().mint(cmd, tail), f"{prefix}-001")

    def test_the_board_is_the_canonical_half(self):
        """The section IS the record — there is no store to read instead.

        Planted on the board and nowhere else, so a minter that read a store,
        or only the append-only records, would hand back `-001`.
        """
        for cmd, tail, prefix, section in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                p.plant_on_board(section, f"{prefix}-050", "planted by hand")
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-051")

    def test_the_event_log_is_read(self):
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                p.plant_in_events(event="ask", id=f"{prefix}-060")
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-061")

    def test_the_journal_is_read(self):
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                p.plant_in_journal(f"- [{prefix}-070] something happened")
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-071")

    def test_state_root_markdown_outside_the_journal_is_not_read(self):
        """`journal/`, not "every `.md` under the state root".

        `evidence/` is prose about the project and names ids it does not own —
        counting it would retire numbers because somebody wrote about them.
        `bin/perry-migrate § id_minter` does scan the whole tree; that is a
        different register (`SRC-`) with a different question.
        """
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                p.plant_outside_the_journal(f"discussion of {prefix}-080")
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-001")

    def test_a_family_does_not_count_another_familys_numbers(self):
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                for other in ("USER", "CAD", "RX", "TASK"):
                    if other != prefix:
                        p.plant_in_events(event="ask", id=f"{other}-090")
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-001")

    def test_cadence_counts_the_long_spelling(self):
        """`CADENCE-007` and `CAD-007` are one sequence, not two.

        Kept from `mint_cadence_id`'s own docstring: a live register numbers
        its rows `CADENCE-NNN`, and a minter blind to that hands out `CAD-001`
        beside `CADENCE-002`.
        """
        p = Register()
        p.plant_on_board("Cadence", "CADENCE-007", "a hand-numbered ritual")
        self.assertEqual(p.mint("cadence-add",
                                ("--title", "r", "--frequency", "weekly")),
                         "CAD-008")


class TestANumberIsRetiredNotFreed(unittest.TestCase):
    """TASK-167's question, asked of the three registers that have no `purge`.

    `purge` is a task-store path and does not reach them. The way one of their
    rows leaves is a human deleting the line — and the number must not come
    back, for the reason `minting_records` exists: `.perry/events.jsonl` is
    append-only, so a new row wearing that number inherits the dead row's
    history.
    """

    def test_deleting_the_row_does_not_free_the_number(self):
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                first = p.mint(cmd, tail)
                p.drop_board_row(first)
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-002")

    def test_it_survives_losing_the_event_log(self):
        """The log is *"derived and disposable"* — this module docstring says
        so — so nothing may be load-bearing on it alone. The journal line
        `commit()` writes names the minted id, and that is the second copy."""
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                first = p.mint(cmd, tail)
                p.drop_board_row(first)
                (p.root / ".perry" / "events.jsonl").unlink()
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-002")

    def test_it_survives_losing_the_journal(self):
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                first = p.mint(cmd, tail)
                p.drop_board_row(first)
                for j in (p.root / "journal").rglob("*.md"):
                    j.unlink()
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-002")

    def test_the_boundary_an_id_the_tool_never_minted(self):
        """The one case that is NOT safe, stated rather than left to be found.

        An id hand-written onto the board and never routed through this tool
        was recorded nowhere else, so deleting that row does free the number.
        Irreducible without a store — it is exactly what `risks.jsonl` would
        fix for `RX-`, and `USER-016` owns that.
        """
        for cmd, tail, prefix, section in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                p.plant_on_board(section, f"{prefix}-050", "typed by hand")
                p.drop_board_row(f"{prefix}-050")
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-001")


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

    def test_a_null_id_in_the_log_is_survivable(self):
        """`read_events` keeps whatever JSON a line held — *"a corrupt line is
        not a reason to refuse a write"* — and the log is append-only, shared
        with `perry-goals` and hand-editable. `re.findall(None)` raises
        `TypeError`, which is not a `Refused` and not a message anyone can act
        on. `minting_records` and `perry-goals § mint_commitment_id` both
        guard this; these three did not.
        """
        for cmd, tail, prefix, _ in FAMILIES:
            with self.subTest(prefix=prefix):
                p = Register()
                p.plant_in_events(event="link-kr", id=None)
                self.assertEqual(p.mint(cmd, tail), f"{prefix}-001")


class TestBothRiskCallSites(unittest.TestCase):
    """`mint_risk_id` has two callers, not one.

    `cmd_risk_add` is the obvious one. `ensure_risk_table` is the other: it
    converts a bullet section to the table and allocates a block of ids from
    the same minter. A retired number must not be handed to the conversion
    either, and the conversion is the path that would hand out several.
    """

    BULLETS = ("# Board — b\n\n## P0 (must finish this period)\n\n"
               "| ID | Title | Owner | Status | Next action | Evidence |\n"
               "|---|---|---|---|---|---|\n\n"
               "## Top risks\n\n- the first risk\n- the second risk\n")

    def test_risk_migrate_allocates_above_a_retired_number(self):
        p = Register(board=self.BULLETS)
        p.plant_in_events(event="risk-add", id="RX-030")
        code, out = p.run("risk-migrate")
        self.assertEqual(code, 0, out)
        self.assertEqual([r["id"] for r in out["migrated"]],
                         ["RX-031", "RX-032"])

    def test_risk_add_continues_from_what_the_migration_allocated(self):
        p = Register(board=self.BULLETS)
        p.plant_in_events(event="risk-add", id="RX-030")
        self.assertEqual(p.run("risk-migrate")[0], 0)
        self.assertEqual(p.mint("risk-add", ("--title", "a third risk")),
                         "RX-033")


def _throwaway_board() -> "PT.Board":
    d = Path(tempfile.mkdtemp())
    (d / "BOARD.md").write_text("# B\n\n## Top risks\n\n- none\n")
    return PT.Board(d / "BOARD.md")


if __name__ == "__main__":
    unittest.main()
