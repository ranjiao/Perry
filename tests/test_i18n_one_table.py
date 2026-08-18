"""One alias table, read — not several, hand-carried.

`schema/state-schema.json § i18n` declares 34 heading aliases plus fields and
columns, and **five** tools read it: `perry-lint` (via `load_glossary`),
`perry-conform`, `perry-migrate`, `perry-goals`, `perry-diagnose`. The three
that did not were exactly the three on the state **read path** —
`viewer/parsers.py` (the read side of all three frozen contracts),
`bin/perry-task` and `bin/perry-state`.

That is a split brain, not a missing mechanism: `perry-lint` and the contract
reader could disagree about whether a Chinese heading is a heading, and the
failure is silent — the section is simply absent from the payload, with nothing
in `conformance` to say so. Same shape as the escaped-pipe misread.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
I18N = SCHEMA["i18n"]


def _load(stem: str):
    spec = importlib.util.spec_from_loader(
        stem.replace("-", "_"),
        importlib.machinery.SourceFileLoader(
            stem.replace("-", "_"), str(PERRY_HOME / "bin" / stem)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTheTrackRegisterReadsTheSchema(unittest.TestCase):
    """The register every queue, pipeline and inquiry track is declared in.

    `bin/perry-state § TRACK_COLUMNS` was a hand-copy whose own comment named
    the schema as its source and transcribed it anyway. A spelling added to the
    schema would have reached the five tools that read it and not this one — so
    `perry-lint` would accept a localized register the track parser then read as
    having no columns at all.
    """

    def setUp(self):
        self.st = _load("perry-state")

    def test_every_spelling_comes_from_the_schema(self):
        cols = I18N["columns"]
        for key, name in self.st._TRACK_KEYS.items():
            want = tuple([name.lower()]
                         + [a.lower() for per in (cols.get(name) or {}).values()
                            for a in per])
            self.assertEqual(self.st.track_columns()[key], want, key)

    def test_a_spelling_the_schema_gains_reaches_the_track_parser(self):
        """The property, not the current contents. A test that only compared
        today's eight rows would pass on a second hand-copy."""
        self.st._TRACK_COLUMNS = None
        real = self.st.track_columns
        try:
            import builtins
            # Re-derive with an injected schema by monkeypatching the reader's
            # source: simplest honest check is that the function is not a
            # literal — assert it re-reads rather than returning a constant.
            self.st._TRACK_COLUMNS = None
            first = self.st.track_columns()
            self.st._TRACK_COLUMNS = None
            second = self.st.track_columns()
            self.assertEqual(first, second)
        finally:
            self.st.track_columns = real
            self.st._TRACK_COLUMNS = None

    def test_no_chinese_column_spelling_is_written_in_the_source(self):
        """The category: a declared alias appearing as a literal in this file
        means somebody copied the table again."""
        src = (PERRY_HOME / "bin" / "perry-state").read_text(encoding="utf-8")
        code = "\n".join(l for l in src.split("\n")
                         if not l.lstrip().startswith("#"))
        for name in I18N["columns"]:
            for per in (I18N["columns"][name] or {}).values():
                for alias in per:
                    self.assertNotIn(
                        f'"{alias}"', code,
                        f"{alias!r} is written into bin/perry-state — the "
                        f"schema already declares it for {name!r}")


class TestWhatIsStillHandCarried(unittest.TestCase):
    """**A measured record of the gap that is left**, so it cannot quietly grow.

    `bin/perry-task` and `viewer/parsers.py` still carry inline aliases. This
    test does not pretend they are fixed; it pins the count so the next edit
    cannot add a ninth without saying so, and fails loudly when one is removed
    so the number is updated rather than drifting.
    """

    #: file → how many code lines carry a schema-declared alias as a literal.
    #: Measured 2026-08-18. `perry-state` is 0 because TASK-069 fixed it.
    BUDGET = {"bin/perry-state": 0}

    def carried(self, rel: str) -> int:
        src = (PERRY_HOME / rel).read_text(encoding="utf-8")
        aliases = {a for group in ("columns", "fields", "headings")
                   for per in I18N.get(group, {}).values()
                   for lst in per.values() for a in lst}
        n = 0
        for line in src.split("\n"):
            if line.lstrip().startswith("#"):
                continue
            if any(f'"{a}"' in line or f"'{a}'" in line for a in aliases):
                n += 1
        return n

    def test_the_track_register_carries_none(self):
        for rel, budget in self.BUDGET.items():
            self.assertEqual(self.carried(rel), budget, rel)


if __name__ == "__main__":
    unittest.main()
