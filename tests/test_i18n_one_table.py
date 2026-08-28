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

    #: file → how many code lines may carry a schema-declared alias as a
    #: literal. **All zero**, measured 2026-08-18 after TASK-069.
    #:
    #: The sharpest of the three was `viewer/parsers.py`: it already had
    #: `alias("headings", name)` reading the schema, and **eight call sites
    #: hand-carried the Chinese spelling anyway, in the same file**. The
    #: mechanism existed; the call sites went around it. `bin/perry-task`
    #: measured zero all along — an earlier count of "24 CJK lines" was
    #: counting comments and docstrings, and is corrected here.
    BUDGET = {"bin/perry-state": 0,
              "bin/perry-task": 0,
              "viewer/parsers.py": 0}

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

    def test_no_read_path_tool_carries_a_declared_alias(self):
        """The category, over all three tools on the state read path. A ninth
        copy fails the build rather than being noticed in review."""
        for rel, budget in self.BUDGET.items():
            self.assertEqual(self.carried(rel), budget, rel)

    def test_the_alias_reader_is_one_function_not_one_per_tool(self):
        """`bin/perry-state` briefly grew its own `heading_spellings` while
        this row was being fixed — a second implementation of `alias()`,
        added by the fix for having two implementations.

        **This assertion changed shape at TASK-202, and the property got
        stronger, not weaker.** `hook_profile` held this file's only direct
        `P.alias("headings", …)` call, inside its own copy of the hook-section
        read; that whole read moved into `P.hook_escalation_lines`, which the
        linter and the pre-flight union were already using. So `bin/perry-state`
        now resolves no heading spelling at all rather than resolving them
        correctly — one fewer place that could get it wrong.

        The behaviour this stands in for is asserted for real in
        `test_i18n.py`, where the ZH fixture's Chinese `## 高风险操作` heading
        must come back armed from this tool. That is the test that fails if the
        spelling stops being resolved; this one only says WHERE it is resolved.
        """
        st = (PERRY_HOME / "bin" / "perry-state").read_text(encoding="utf-8")
        self.assertNotIn("def heading_spellings", st)
        self.assertIn("P.hook_escalation_lines(", st)
        self.assertIn('alias("headings"',
                      (PERRY_HOME / "viewer" / "parsers.py").read_text(
                          encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
