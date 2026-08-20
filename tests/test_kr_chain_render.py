"""TASK-146 — the viewer shows a KR's `current` with its provenance, or not at all.

TASK-120 made a KR's `current` honest in both payloads: asserted vs measured,
a staleness signal, and a linked-task tally, all from one derivation in
`bin/lib`. The viewer was not a consumer of any of it. Measured at `8645f12`,
before this row: **`P-O1.1` appears on no page of the viewer at all** — the
register is parsed into `PMOSnapshot.linkage` and no template reads it — so
the first thing the viewer would ever have said about a KR number would have
been the bare number.

The two readings that made this a row, both wrong on this repository's own
register, in opposite directions:

| KR | target | current | reads as | actually |
|---|---|---|---|---|
| `P-O1.1` | 1 | 0 | 0% | all four linked tasks closed |
| `P-O2.2` | 0 | 0 | **met** | 0 of 2 linked tasks closed |

**Every test here goes through the render.** `serve.py § phase` is called and
its template output is asserted on — not `kr_chain`'s return value, not a
helper. A viewer change proved by a unit test on a function nobody renders
through is not proved, so the two stand-ins below exist to make the real route
runnable in a suite that must not require the viewer's opt-in dependencies:
Flask and `markdown` are replaced with the smallest objects `serve.py`'s
module body needs, and `render_template` is wired to a real Jinja environment
loading the real `viewer/templates/`. Everything between the route function
and the HTML is the shipped code.

Run: python3 tests/parallel test_kr_chain_render
"""

from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import types
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
TEMPLATES = PERRY_HOME / "viewer" / "templates"

sys.path.insert(0, str(PERRY_HOME / "tests"))
sys.path.insert(0, str(PERRY_HOME / "viewer"))

#: The register this row's assertions need is TASK-120's, imported rather than
#: retyped: it already carries all three shapes in one project — a `current: 0`
#: whose linked tasks are all closed (`P-O1.1`), a `target: 0` / `current: 0`
#: whose linked task is open (`P-O1.2`), and a KR the register never gave a
#: number (`P-O1.3`) — plus an event log with a non-state event dated after the
#: assertion. A second copy of it would be a second thing to keep true.
from test_kr_progress_provenance import (  # noqa: E402
    UPDATED, append_event, build_project, close_task)


# ── making the shipped route runnable ─────────────────────────────────────


def _stub_flask(filters: dict):
    """The smallest `flask` `serve.py`'s module body imports.

    The viewer is opt-in and its venv lives outside the repo, so the suite
    cannot import the real Flask. What it CAN do is let `serve.py` execute
    unmodified and keep every decorator's registration: the template filters
    `serve.py` declares are collected here and handed to the Jinja
    environment, because a stand-in that dropped them would render a page the
    shipped viewer never serves.
    """
    mod = types.ModuleType("flask")

    class _App:
        def __init__(self, *a, **k):
            self.config = {}

        def route(self, *a, **k):
            return lambda fn: fn

        def template_filter(self, name):
            def deco(fn):
                filters[name] = fn
                return fn
            return deco

        def run(self, *a, **k):  # pragma: no cover - never called from a test
            raise AssertionError("the test render must not start a server")

    mod.Flask = _App
    mod.abort = mod.redirect = lambda *a, **k: None
    mod.url_for = lambda endpoint, **k: "/" + "/".join(str(v) for v in k.values())
    mod.request = types.SimpleNamespace(args={})
    mod.render_template = None      # replaced below, once the filters are known
    return mod


def _stub_markdown():
    mod = types.ModuleType("markdown")

    class _Md:
        toc_tokens: list = []

        def __init__(self, *a, **k):
            pass

        def convert(self, text):
            return text

    mod.Markdown = _Md
    return mod


def _env(filters: dict | None = None):
    """A Jinja environment over the SHIPPED templates.

    The filters `serve.py` registers are read out of `serve.py` rather than
    listed here — a hardcoded list goes stale the moment someone adds one, and
    then this reports a working template as broken. `viewer/templates/
    _macros.html` compiles `task_id`, which uses `evidence_path`, whether or
    not this page renders it, so an environment missing them cannot even load
    the file.
    """
    import jinja2
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATES)),
                             autoescape=True)
    env.globals["url_for"] = lambda endpoint, **k: "/" + "/".join(
        str(v) for v in k.values())
    declared = re.findall(r'@app\.template_filter\(\s*["\'](\w+)["\']',
                          (PERRY_HOME / "viewer" / "serve.py").read_text())
    assert declared, "no template filters found in serve.py — the pattern changed"
    for name in declared:
        env.filters.setdefault(name, lambda v, *a, **k: v)
    env.filters.update(filters or {})
    return env


def render_phase(root: Path) -> str:
    """`GET /phase`, rendered by the shipped route and the shipped templates.

    `root` is what `bin/perry-viewer` exports as `PERRY_PROJECT`, so both the
    snapshot and `kr_chain`'s `perry-state` call see the same project.
    """
    filters: dict = {}
    sys.modules["flask"] = _stub_flask(filters)
    sys.modules["markdown"] = _stub_markdown()

    os.environ["PERRY_PROJECT"] = str(root)
    import parsers
    importlib.reload(parsers)      # `load_snapshot`'s default root is frozen at
    import serve                   # import, and each test renders another project
    importlib.reload(serve)

    env = _env(filters)
    serve.render_template = lambda name, **ctx: env.get_template(name).render(**ctx)
    return serve.phase()


TAG = re.compile(r"<[^>]+>")

#: The card's last line. Everything a KR row says sits above it, so it is also
#: what bounds the final row — without it the last KR's block would run on
#: into the rest of the page and swallow another card's words.
CARD_END = "every number above read from"


def text_of(html: str) -> str:
    """The page as a reader sees it: tags out, whitespace squashed, one line.

    Assertions run against this rather than against the markup so they survive
    a styling change and fail on a wording change, which is the direction that
    matters for a view whose whole job is what it SAYS about a number.
    """
    return re.sub(r"\s+", " ", TAG.sub(" ", html))


def chain_html(html: str) -> str:
    """The chain card's markup alone — the page around it must not answer for it."""
    start = html.find("Phase KR chain")
    assert start >= 0, "the phase page rendered no KR chain card"
    end = html.find(CARD_END, start)
    assert end >= 0, "the chain card did not render its provenance footer"
    return html[start:end]


def chain_card(html: str) -> str:
    """The chain card as a reader sees it."""
    return text_of(chain_html(html))


def kr_block(html: str, kr_id: str) -> str:
    """Just the one KR's row, so an assertion cannot pass on a neighbour.

    Cut on the row element's `data-kr`, and stop at the next `data-kr` OR the
    next `data-objective`. Bounding a row by "up to the next `P-O…`" in the
    text let the last KR of each objective swallow the heading below it, and a
    block that reaches into its neighbour is a block an assertion can pass on
    by accident.
    """
    parts = re.split(r'<div data-(?:kr|objective)="', chain_html(html))
    hit = [p for p in parts[1:] if p.startswith(kr_id + '"')]
    assert len(hit) == 1, f"{kr_id}: {len(hit)} rows in the rendered chain"
    return text_of(hit[0].split(">", 1)[1])


class Rendered(unittest.TestCase):
    """One fixture, rendered once per test so a mutation cannot leak sideways."""

    def setUp(self):
        self.root = build_project()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def page(self) -> str:
        return render_phase(self.root)


# ── V3 item 1 — the two readings that made this a row ─────────────────────


class TestTheTwoWrongReadingsCannotBeTakenFromTheRender(Rendered):

    def test_a_zero_against_a_target_does_not_read_as_zero_percent(self):
        """`P-O1.1`'s shape: `current 0` / `target 1`, both linked tasks closed.

        The number still renders — hiding it would be a different lie — but it
        cannot be read as progress, because the render carries no percentage
        and states the tally that contradicts it.
        """
        block = kr_block(self.page(), "P-O1.1")
        self.assertIn("current 0", block)
        self.assertIn("asserted by the author, not measured", block)
        self.assertIn("linked tasks 2 · closed 2 · open 0", block)
        self.assertNotIn("%", block)

    def test_a_drive_to_zero_kr_does_not_read_as_met(self):
        """`P-O2.2`'s shape: `target 0` / `current 0`, its linked task OPEN.

        Nothing on the page says met, achieved or complete about any KR, and
        the one line that could be mistaken for a verdict — the tally — is in
        tasks, not in the metric's unit.
        """
        block = kr_block(self.page(), "P-O1.2")
        self.assertIn("current 0", block)
        self.assertIn("target 0", block)
        self.assertIn("linked tasks 1 · closed 0 · open 1", block)

    def test_the_chain_never_draws_a_verdict_or_a_proportion(self):
        card = chain_card(self.page()).lower()
        for banned in ("%", "achieved", "on track", "complete"):
            self.assertNotIn(banned, card,
                             f"the chain rendered {banned!r} about a number "
                             "nothing re-measured")
        # `met` only as a whole word — `metric` is expected and legitimate.
        self.assertIsNone(re.search(r"\bmet\b", card),
                          "a KR was rendered as met")


# ── V3 item 2 — staleness, both directions, one fixture ───────────────────


class TestStalenessIsVisibleAndOnlyWhereItIsTrue(Rendered):

    def moved(self) -> str:
        """One linked task of `P-O1.2` moves AFTER the register's `updated`."""
        append_event(self.root, {"ts": "2026-08-19T09:00:00", "event": "done",
                                 "id": "TASK-003", "from": "in_progress",
                                 "to": "done"})
        close_task(self.root, "TASK-003")
        return self.page()

    def test_an_assertion_that_has_not_aged_is_not_marked(self):
        page = self.page()
        self.assertNotIn("stale assertion", chain_card(page))
        self.assertIn(f"no linked task has changed state since "
                      f"{UPDATED.rstrip('Z')}", kr_block(page, "P-O1.1"))

    def test_the_kr_whose_task_moved_is_marked_stale_and_says_which(self):
        block = kr_block(self.moved(), "P-O1.2")
        self.assertIn("stale assertion", block)
        self.assertIn("TASK-003 (in_progress → done)", block)

    def test_only_that_kr_goes_stale(self):
        page = self.moved()
        self.assertNotIn("stale assertion", kr_block(page, "P-O1.1"))
        self.assertNotIn("stale assertion", kr_block(page, "P-O1.3"))


# ── V3 item 3 — an absent `current` renders as absent ─────────────────────


class TestNothingIsInvented(Rendered):
    """The default TASK-120 measured was `0`, and it read as met before the
    work started on six of this register's eight KRs. Re-introducing it in the
    render would undo the row this one completes, so `P-O1.3` — a KR the
    register never gave a number — is asserted here in the negative as well as
    the positive."""

    def block(self) -> str:
        return kr_block(self.page(), "P-O1.3")

    def test_it_says_the_number_was_never_asserted(self):
        self.assertIn("current not asserted", self.block())
        self.assertIn("the register gives this KR no current", self.block())

    def test_it_is_not_rendered_as_zero(self):
        block = self.block()
        self.assertIsNone(
            re.search(r"current\s+(-?\d)", block),
            "an absent `current` was rendered as a number")

    def test_it_is_not_rendered_as_an_em_dash_percentage(self):
        self.assertNotIn("—%", self.block())
        self.assertNotIn("%", self.block())

    def test_its_staleness_is_not_asserted_either(self):
        self.assertIn("never asserted, so there is nothing to go stale",
                      self.block())


# ── V3 item 4 — reverting reddens THE RENDER ──────────────────────────────


class TestTheRenderIsWhatCarriesTheProvenance(Rendered):
    """Each of these fails if the view goes back to reading the register
    directly — which is the state this row found — and each fails through the
    rendered page, not through a helper."""

    def test_the_page_never_shows_a_current_without_its_provenance(self):
        """The invariant, stated over every KR the register carries rather
        than over the three this fixture happens to name."""
        page = self.page()
        ids = sorted(set(re.findall(r"P-O\d+\.\d+", chain_card(page))))
        self.assertTrue(ids, "the chain rendered no KR at all")
        for kr_id in ids:
            block = kr_block(page, kr_id)
            self.assertIn("current", block)
            self.assertTrue(
                "not measured" in block or "not asserted" in block,
                f"{kr_id}: a `current` reached the page with no provenance")
            self.assertIn("linked tasks", block,
                          f"{kr_id}: no linked-task tally beside the number")

    def test_a_payload_that_did_not_arrive_shows_no_numbers_at_all(self):
        """The other half of item 3. If the derivation cannot be read, the
        view says so — it does not fall back to the register's bare number,
        which is the very thing it stopped rendering."""
        out = _env().from_string(
            "{% from '_macros.html' import kr_chain %}{{ kr_chain(chain) }}"
        ).render(chain={"ok": False, "reason": "perry-state could not be run"})
        body = text_of(out)
        self.assertIn("perry-state could not be run", body)
        self.assertIsNone(re.search(r"P-O\d", body))
        self.assertNotIn("current", body)

    def test_the_numbers_are_the_payload_s_and_not_a_second_derivation(self):
        """Every number the chain prints for a KR is present in
        `perry-state --json`, under the keys TASK-120 defined.

        This is what stops the next edit from computing a friendlier-looking
        figure in the template: the view may only show what the derivation
        said.
        """
        payload = json.loads(subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(self.root), "--json"],
            capture_output=True, text=True, check=True).stdout)
        krs = {k["id"]: k for o in payload["linkage"]["objectives"]
               for k in o["krs"]}
        page = self.page()
        for kr_id, k in krs.items():
            block = kr_block(page, kr_id)
            tally = k["linked_task_completion"]
            self.assertIn(
                f"linked tasks {tally['total']} · "
                f"closed {tally['done'] + tally['dropped']} · "
                f"open {tally['open']}", block)
            if k["current_provenance"]["state"] == "asserted":
                self.assertIn(f"current {k['current']}", block)
            self.assertIn(k["current_staleness"]["reason"], block)


# ── the register that made this a row, on this repository ─────────────────


class TestOnPerrysOwnRegister(unittest.TestCase):
    """`perry/phase/002-linkage.md` belongs to the `goals` lane and this row
    does not write it, so nothing here asserts a hand-typed number. What is
    asserted is that the two readings the row names can no longer be taken
    from the page."""

    def page(self) -> str:
        return render_phase(PERRY_HOME)

    def test_p_o1_1_reads_as_an_assertion_and_carries_its_tally(self):
        block = kr_block(self.page(), "P-O1.1")
        self.assertIn("asserted by the author, not measured", block)
        self.assertRegex(block,
                         r"linked tasks \d+ · closed \d+ · open \d+")
        self.assertNotIn("%", block)

    def test_p_o2_2_does_not_read_as_met(self):
        block = kr_block(self.page(), "P-O2.2")
        self.assertIn("asserted by the author, not measured", block)
        self.assertIsNone(re.search(r"\bmet\b", block.lower()))
        self.assertRegex(block,
                         r"linked tasks \d+ · closed \d+ · open \d+")

    def test_the_register_s_own_timestamp_is_not_passed_off_as_the_kr_s(self):
        """TASK-120 reused the register's top-level `updated` rather than add
        an authored per-KR field, and emitted `asserted_scope` so a reader
        could not mistake one for the other. The render has to carry that
        distinction or the choice was undone here."""
        self.assertIn("the register's own timestamp, not this KR's",
                      kr_block(self.page(), "P-O1.1"))


if __name__ == "__main__":
    unittest.main()
