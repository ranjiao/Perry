"""What `delegate` renders from, and what stays advisory.

DESIGN-006 § 5.2 and § 5.4, phase D. `delegate <task-id> <role>` renders from
the card rather than from a list of agent types written into
`work/reference/delegate.md`. Four blocks, four consumers:

  Context, May touch   → the prompt, VERBATIM. Advisory: they shape behaviour.
  Loads                → § 5.4 subscription injection, by topic.
  Must escalate        → the pre-flight union (`tests/test_escalation_union.py`).
  Accepted by, rung    → the close gate; the stricter of mode and role wins.

The one non-advisory thing in the read path is the **stale flag**. § 5.4 says a
subscribed card that is stale is injected *with its flag visible*, and the three
options are not equivalent: dropping it makes the agent re-derive the claim
badly, injecting it unmarked makes it act on a claim nobody has checked, and
only flagging it lets the agent report back that the card is wrong now.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
STATE = PERRY_HOME / "bin" / "perry-state"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
STALE_DAYS = SCHEMA["thresholds"]["knowledge_stale_days"]["value"]

CONTEXT = ("Prepares the monthly close and ad-hoc reports.\n"
           "Reads exports, never writes to source systems.")
MAY_TOUCH = "- write: reports/, `evidence/`\n- run: read-only queries"

CARD = f"""# Role · finance

- Accepted by: the CFO
- Default rung: V5
- Executors: codex only

## Context

{CONTEXT}

## Loads

- knowledge: reporting, ledger-quirks
- pack: software-ops

## May touch

{MAY_TOUCH}

## Must escalate

- any outbound `invoice`
"""


def card(claim: str, days_ago: int) -> str:
    seen = (date.today() - timedelta(days=days_ago)).isoformat()
    return (f"# reporting/{claim} — a claim\n\n"
            f"- Kind: knowledge\n- Owner role: finance\n"
            f"- Source: TASK-001\n- Last verified: {seen}\n"
            f"- Invalidated by: upstream schema change on the ledger\n\n"
            f"The claim itself.\n")


class Base(unittest.TestCase):
    def project(self, cards: dict[str, str] | None = None,
                knowledge: dict[str, str] | None = None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n", encoding="utf-8")
        (root / "BOARD.md").write_text("# Board — T\n", encoding="utf-8")
        for name, text in (cards or {"finance.md": CARD}).items():
            p = root / ".perry" / "roles" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        for rel, text in (knowledge or {}).items():
            p = root / "knowledge" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return root

    def roster(self, root: Path) -> dict:
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--section", "roles"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["roles"]

    def only(self, root: Path) -> dict:
        got = self.roster(root)
        self.assertEqual(got["declared"], 1)
        return got["cards"][0]


class TestWhatRendersFromTheCard(Base):
    def test_context_and_may_touch_come_through_verbatim(self):
        """Copied, not summarized. They are short by schema precisely so that
        pasting them costs nothing; paraphrasing is how a boundary loses its
        edges one delegation at a time."""
        c = self.only(self.project())
        self.assertEqual(c["context"], CONTEXT)
        self.assertEqual(c["may_touch"], MAY_TOUCH)

    def test_the_close_gate_fields_are_the_cards_own(self):
        """`Accepted by` and `Default rung` feed the close-task gate the way a
        mode's default rung does. Read off the card, never defaulted here."""
        c = self.only(self.project())
        self.assertEqual(c["accepted_by"], "the CFO")
        self.assertEqual(c["default_rung"], "V5")
        self.assertEqual(c["executors"], "codex only")

    def test_loads_is_split_into_topics_and_packs(self):
        c = self.only(self.project())
        self.assertEqual(c["loads"]["knowledge"], ["reporting", "ledger-quirks"])
        self.assertEqual(c["loads"]["pack"], ["software-ops"])

    def test_the_roster_names_the_file_it_came_from(self):
        c = self.only(self.project())
        self.assertEqual(c["name"], "finance")
        self.assertEqual(c["path"], ".perry/roles/finance.md")

    def test_an_unfilled_template_contributes_no_escalation_fragments(self):
        """`role_card_TEMPLATE.md` ships `{{term}}` placeholders. A project that
        copied it and has not edited it yet must not get a scan that refuses
        anything containing the literal word `term`."""
        tpl = (PERRY_HOME / "work" / "state" / "role_card_TEMPLATE.md").read_text()
        c = self.only(self.project(cards={"draft.md": tpl}))
        self.assertEqual(c["must_escalate"]["fragments"], [])


class TestSubscriptionInjection(Base):
    """§ 5.4's read path: the cards in the role's subscribed topics, and
    nothing else. Subscription, not volume."""

    def test_a_subscribed_card_is_injected(self):
        root = self.project(knowledge={"reporting/a.md": card("a", 1)})
        got = self.only(root)["knowledge"]
        self.assertEqual([k["path"] for k in got if k.get("path")],
                         ["knowledge/reporting/a.md"])

    def test_an_unsubscribed_topic_is_not_injected(self):
        """A role that loads `reporting` gets `knowledge/reporting/`, not the
        store. The cap on prompt size is the subscription, not a truncation."""
        root = self.project(knowledge={"reporting/a.md": card("a", 1),
                                       "payroll/b.md": card("b", 1)})
        paths = [k["path"] for k in self.only(root)["knowledge"] if k.get("path")]
        self.assertEqual(paths, ["knowledge/reporting/a.md"])

    def test_a_stale_card_is_injected_WITH_its_flag_not_dropped(self):
        """The point of § 5.4. Dropping it and injecting it unmarked are both
        wrong, in opposite directions."""
        root = self.project(knowledge={"reporting/old.md": card("old", STALE_DAYS + 30)})
        got = [k for k in self.only(root)["knowledge"] if k.get("path")]
        self.assertEqual(len(got), 1, "a stale card was dropped from injection")
        self.assertTrue(got[0]["stale"])
        self.assertEqual(got[0]["age_days"], STALE_DAYS + 30)
        self.assertIn("ledger", got[0]["invalidated_by"])

    def test_a_fresh_card_is_not_flagged(self):
        root = self.project(knowledge={"reporting/new.md": card("new", 1)})
        got = [k for k in self.only(root)["knowledge"] if k.get("path")]
        self.assertFalse(got[0]["stale"])

    def test_the_threshold_is_the_schemas_and_not_the_scripts(self):
        """One day either side of the declared number. A hardcoded 90 in the
        script would pass the pair above and fail here the moment the schema
        moves — which is the only time it matters."""
        just_ok = self.project(knowledge={"reporting/a.md": card("a", STALE_DAYS)})
        just_not = self.project(knowledge={"reporting/a.md": card("a", STALE_DAYS + 1)})
        self.assertFalse([k for k in self.only(just_ok)["knowledge"]][0]["stale"])
        self.assertTrue([k for k in self.only(just_not)["knowledge"]][0]["stale"])

    def test_an_archived_card_is_not_re_injected(self):
        """An invalidated card is archived WITH ITS REASON, never deleted
        (§ 5.3). Injecting it again would undo the archiving."""
        root = self.project(knowledge={"reporting/archive/gone.md": card("gone", 1)})
        self.assertEqual(
            [k for k in self.only(root)["knowledge"] if k.get("path")], [])

    def test_a_digest_in_a_subscribed_topic_is_not_a_card(self):
        """Cards and digests share `knowledge/*/*.md` and are told apart by
        `Kind:` — the schema's discriminator, the same one `--knowledge` and
        `--provenance` read. A digest is a source the project read, not a claim
        it made, and injecting one as a claim is exactly the confusion the
        discriminator exists to stop."""
        digest = "# reporting/d — digest\n\n> Id: SRC-1\n\nsome notes\n"
        root = self.project(knowledge={"reporting/d.md": digest,
                                       "reporting/c.md": card("c", 1)})
        paths = [k["path"] for k in self.only(root)["knowledge"] if k.get("path")]
        self.assertEqual(paths, ["knowledge/reporting/c.md"])

    def test_a_subscription_to_a_topic_that_does_not_exist_is_reported(self):
        """Silently resolving to nothing would make the role look
        better-briefed than it is."""
        root = self.project(knowledge={"reporting/a.md": card("a", 1)})
        got = self.only(root)["knowledge"]
        missing = [k for k in got if k.get("missing_topic")]
        self.assertEqual([k["topic"] for k in missing], ["ledger-quirks"])

    def test_a_role_that_loads_nothing_injects_nothing(self):
        bare = CARD.replace("- knowledge: reporting, ledger-quirks\n", "")
        root = self.project(cards={"finance.md": bare},
                            knowledge={"reporting/a.md": card("a", 1)})
        self.assertEqual(self.only(root)["knowledge"], [])


class TestTheRosterAnswersAimarksAsk(unittest.TestCase):
    """`{id, tasks}` — which roles exist, and what each one holds.

    aiMark asked for this in round 1. It used to parse an `agents:` block out of
    `phase/<NNN>-linkage.md`; that was rescoped into DESIGN-006 rather than
    patched into `perry-goals/list`, on the grounds that a roster is a **view
    over roles**, and shipping the view before the object would freeze the wrong
    shape into an additive contract.

    Phase C shipped the object and phase D shipped half the view — "what is each
    working on" needed phase E's `Role` cell, which did not exist yet. It does
    now, so the edge is a **join over two files Perry already reads**, not a
    third registry storing a fact both of them carry.
    """

    CARD = ("# Role · {name}\n\n"
            "- Accepted by: user\n- Default rung: V3\n- Executors: any\n\n"
            "## Context\n\nDoes {name} work.\n\n"
            "## Loads\n\n- knowledge: build-system\n\n"
            "## May touch\n\n- write: source\n\n"
            "## Must escalate\n\n- any `force-push`\n")
    BOARD = ("# Board\n\n## P1\n\n"
             "| ID | Title | Owner | Status | Next action | Evidence | "
             "Verification | Role |\n|---|---|---|---|---|---|---|---|\n"
             "| T-1 | a | o | in_progress | n | — | V3 | coding |\n"
             "| T-2 | b | o | not_started | n | — | V3 | coding |\n"
             "| T-3 | c | o | done | n | — | V3 | coding |\n"
             "| T-4 | d | o | in_progress | n | — | V4 | review |\n")

    def project(self, roles=("coding", "review")) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry" / "roles").mkdir(parents=True)
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: perry\n", encoding="utf-8")
        for r in roles:
            (root / ".perry" / "roles" / f"{r}.md").write_text(
                self.CARD.format(name=r), encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text(self.BOARD, encoding="utf-8")
        return root

    def roster(self, root: Path) -> dict:
        r = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
             "--section", "roles", "--root", str(root)],
            capture_output=True, text=True)
        return {c["name"]: c for c in json.loads(r.stdout)["roles"]["cards"]}

    def held_by(self, root, role):
        """What a role holds, through the edge that survived.

        `cards[].tasks` was removed at `perry-roles/list/1.0`; `tasks[].role`
        in `perry-task/list` answers the same question under contract. These
        tests are about the JOIN, which is still worth asserting — the case
        rule, and that nothing stores the answer — so they were repointed
        rather than deleted.
        """
        r = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "list",
             "--all", "--root", str(root), "--json"],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [t["id"] for t in json.loads(r.stdout)["tasks"]
                if (t.get("role") or "").strip().lower() == role
                and t["open"]]

    def test_the_reverse_edge_answers_what_a_role_holds(self):
        """**`cards[].tasks` was removed at `perry-roles/list/1.0`.**

        Three tests here asserted it: that it lists a role's open rows, that a
        finished task is not one of them, and that a role holding nothing gets
        an empty list rather than a missing key. All three were about a field
        its only consumer called *"dead weight — unversioned and
        open-rows-only"*.

        The question they asked is still answerable, better: `tasks[].role` in
        `perry-task/list` carries a compatibility promise the roster edge never
        had, and it **survives a close**, since `role` now travels on the
        `done` and `drop` events. So it answers *"what has this role ever
        held"*, which is the track record the old edge structurally could not
        give.

        Two edges over one fact is the defect this repository keeps finding.
        This asserts the surviving one still joins.
        """
        root = self.project()
        r = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "list",
             "--all", "--root", str(root), "--json"],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = json.loads(r.stdout)["tasks"]
        by_role = {}
        for t in rows:
            if (t.get("role") or "").strip():
                by_role.setdefault(t["role"].lower(), []).append(t["id"])
        self.assertIn("coding", by_role)
        self.assertIn("T-1", by_role["coding"])

    def test_the_roster_no_longer_publishes_a_second_edge(self):
        r = self.roster(self.project())
        self.assertNotIn("tasks", r["coding"],
                         "the dead edge is back without a version")

    def test_a_role_cell_written_in_any_case_still_matches_its_card(self):
        """`.perry/roles/coding.md` and a cell reading `Coding` are the same
        role. A case-sensitive join silently drops the row, and this test did
        not exist until a mutation of the `.lower()` came back green — the
        fixture was lowercase on both sides, so the guard was untested."""
        root = self.project()
        board = root / "perry" / "BOARD.md"
        board.write_text(board.read_text().replace("| coding |", "| Coding |"),
                         encoding="utf-8")
        self.assertEqual(self.held_by(root, "coding"), ["T-1", "T-2"])

    def test_the_edge_is_a_join_not_a_stored_registry(self):
        """Nothing writes the roster down. Deleting a row's `Role` cell changes
        the roster on the next read — which is the property that stops it
        becoming a third copy that drifts."""
        root = self.project()
        board = (root / "perry" / "BOARD.md")
        board.write_text(board.read_text().replace("| coding |\n", "| review |\n", 1),
                         encoding="utf-8")
        self.assertNotIn("T-1", self.held_by(root, "coding"))
        self.assertIn("T-1", self.held_by(root, "review"))


if __name__ == "__main__":
    unittest.main()
