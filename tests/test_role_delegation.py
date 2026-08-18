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


if __name__ == "__main__":
    unittest.main()
