"""`tracks_source`: every value the tools emit is documented, and nothing else. TASK-271.

`tracks_source` says which register a track list was read from, and two of
its values mean the list is a stand-in rather than the project's. It was
emitted by `bin/perry-state` (`project.config.tracks_source`, and
`project.tracks_source` under `--compact`) and by `bin/perry-diagnose`
(`work_modes.tracks_source`), and documented nowhere a reader would look.

**Neither payload has a `schema/*-contract.md` page.** `schema/README.md` says
`perry-state --json` "is not a frozen contract", and `perry-diagnose` has no
page at all. Each value is therefore documented on the page that already
describes its payload: `reference/snapshot.md` step 3b, which is where a reader
of `project.config.tracks[]` is sent, and `reference/diagnose.md § What the
scan reports about work mode`, which tabulates the `work_modes` entries.

**The pattern is `tests/contract_key_parity.py`'s, at one key.** Nothing here
lists the values. The emitted side comes from running the real tools over one
project per store state; the documented side is read from the page's
`tracks_source` table; the two are diffed in both directions and a difference
is named. A value added to the code on a path one of these projects reaches,
or a row added to a page that no tool emits, turns this red.

**The limit, stated rather than hidden.** A value emitted only on a branch no
project below reaches is not observed. The projects are one per state
`bin/perry-state § stored_tracks` distinguishes plus the scan failure
`bin/perry-diagnose § scan_work_modes` catches; a new branch needs a new
project here, which is the same rule `tests/fixtures/witness-project` states
for an empty collection.

Every project is a temporary copy (NN-5).

Run: python3 tests/parallel test_tracks_source_documented
"""

from __future__ import annotations

COVERS = (
    "bin/perry-state",
    "bin/perry-diagnose",
    "viewer/parsers.py",
    "reference/snapshot.md",
    "reference/diagnose.md",
)

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
FIXTURE = ROOT / "tests" / "fixtures" / "sample-project"
STATE = ROOT / "bin" / "perry-state"
DIAGNOSE = ROOT / "bin" / "perry-diagnose"

#: The page that documents each payload's `tracks_source`.
STATE_PAGE = ROOT / "reference" / "snapshot.md"
DIAGNOSE_PAGE = ROOT / "reference" / "diagnose.md"

#: The header cell that marks a page's `tracks_source` table.
TABLE_KEY = "`tracks_source`"


def _track(name: str, mode: str, order: int) -> str:
    return json.dumps({
        "kind": "track", "track": name, "mode": mode, "spine": "phase/",
        "stages": "", "wip": "", "sla": "", "cycle": "",
        "default_rung": "V3", "order": order})


#: The fixture's own store: five settings and no track record.
KEEP = object()

#: One `.perry/config.jsonl` per store state, as text; `None` removes it and
#: `KEEP` leaves the fixture's. Named by what is on disk, never by the value
#: expected — the value is what the tool says.
STORES: dict[str, object] = {
    "one track record": _track("main", "project", 0) + "\n",
    "two track records": (_track("main", "project", 0) + "\n"
                          + _track("intake", "queue", 1) + "\n"),
    "settings only": KEEP,
    "empty": "",
    "no store": None,
    "a truncated line": (_track("main", "project", 0) + "\n"
                         + '{"kind": "track", "track": "hal'),
    "a record that does not validate": json.dumps(
        {"kind": "track", "track": "intake", "mode": [], "order": 9}) + "\n",
}


def _env() -> dict:
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    env.pop("PERRY_HOME", None)
    return env


def documented(page: pathlib.Path) -> set[str]:
    """The first-column values of the one table headed `` `tracks_source` ``.

    Mechanical: a table is consecutive lines starting with `|` (leading
    indentation ignored, since a table can sit inside a list item); its first
    header cell must be exactly the key; every body row's first cell must be
    one backticked value. Anything else fails by name rather than being
    skipped, because a skipped row is a value this test stopped checking."""
    lines = [l.strip() for l in page.read_text(encoding="utf-8").splitlines()]
    tables: list[set[str]] = []
    i = 0
    while i < len(lines):
        cells = [c.strip() for c in lines[i].strip("|").split("|")]
        if lines[i].startswith("|") and cells[0] == TABLE_KEY:
            values: set[str] = set()
            i += 2                                   # header + separator
            while i < len(lines) and lines[i].startswith("|"):
                first = lines[i].strip("|").split("|")[0].strip()
                if not (len(first) > 2 and first[0] == first[-1] == "`"
                        and "`" not in first[1:-1]):
                    raise AssertionError(
                        f"{page.name}: row {lines[i][:60]!r} does not start "
                        f"with one backticked value")
                values.add(first[1:-1])
                i += 1
            tables.append(values)
        i += 1
    if len(tables) != 1:
        raise AssertionError(f"{page.name}: expected exactly one table headed "
                             f"{TABLE_KEY}, found {len(tables)}")
    return tables[0]


def _diagnose_module():
    loader = importlib.machinery.SourceFileLoader(
        "perry_diagnose_t271", str(DIAGNOSE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


#: `(state values by flag, diagnose values)`, measured once per process.
_MEASURED: list = []


def measured() -> tuple[dict[str, set[str]], set[str]]:
    if not _MEASURED:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="perry-t271-"))
        try:
            _MEASURED.append(_measure(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return _MEASURED[0]


def _measure(tmp: pathlib.Path) -> tuple[dict[str, set[str]], set[str]]:
    """Every tool over every store state."""
    by_payload: dict[str, set[str]] = {"--json": set(), "--compact": set()}
    diag: set[str] = set()
    for i, (label, store) in enumerate(STORES.items()):
        d = tmp / f"p{i}"
        shutil.copytree(FIXTURE, d)
        cfg = d / ".perry" / "config.jsonl"
        if store is None:
            cfg.unlink()
        elif store is not KEEP:
            cfg.write_text(store, encoding="utf-8")
        full = _run(STATE, d, "--json")
        by_payload["--json"].add(full["project"]["config"]["tracks_source"])
        compact = _run(STATE, d, "--compact")
        by_payload["--compact"].add(compact["project"]["tracks_source"])
        diag.add(_run(DIAGNOSE, d, "--json")
                 ["work_modes"]["tracks_source"])
    # The one `perry-diagnose` value no store produces: the scan failing.
    # Reached through the tool's own `except`, by making the call it
    # guards raise — not by writing the value in.
    mod = _diagnose_module()

    def _raise(*_a, **_k):
        raise RuntimeError("perry-state could not be loaded")
    mod.load_sibling = _raise
    diag.add(mod.scan_work_modes(tmp / "p0", tmp / "p0")
             ["tracks_source"])
    return by_payload, diag


def _run(tool: pathlib.Path, d: pathlib.Path, flag: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(tool), "--root", str(d), flag],
        capture_output=True, text=True, env=_env(),
        cwd=tempfile.gettempdir())
    if proc.returncode != 0:
        raise AssertionError(f"{tool.name} {flag} exited "
                             f"{proc.returncode}: {proc.stderr[:400]}")
    return json.loads(proc.stdout)


class _Emitted(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.state_values, cls.diagnose_values = measured()

    def assertParity(self, emitted: set[str], page: pathlib.Path):
        doc = documented(page)
        self.assertEqual(
            {"emitted_not_documented": sorted(emitted - doc),
             "documented_not_emitted": sorted(doc - emitted)},
            {"emitted_not_documented": [], "documented_not_emitted": []},
            f"{page.relative_to(ROOT)} and the tool disagree about "
            f"`tracks_source`")


class PerryState(_Emitted):

    def test_json_emits_exactly_what_snapshot_md_documents(self):
        self.assertParity(self.state_values["--json"], STATE_PAGE)

    def test_compact_emits_exactly_what_snapshot_md_documents(self):
        """The page documents both keys in one table, so both must match it."""
        self.assertParity(self.state_values["--compact"], STATE_PAGE)


class PerryDiagnose(_Emitted):

    def test_work_modes_emits_exactly_what_diagnose_md_documents(self):
        self.assertParity(self.diagnose_values, DIAGNOSE_PAGE)

    def test_the_scan_shares_perry_states_values_and_adds_only_its_own(self):
        """The two pages say five values are shared. Measured, not trusted."""
        self.assertEqual(self.diagnose_values - self.state_values["--json"],
                         {"unavailable"})
        self.assertLessEqual(self.state_values["--json"], self.diagnose_values)


class TheInstrument(unittest.TestCase):
    """Not vacuous: the projects reach distinct states, and the reader fails
    loudly on a page it cannot read."""

    def test_a_page_with_no_table_is_named(self):
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-t271-page-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        page = d / "page.md"
        page.write_text("# nothing here\n")
        with self.assertRaises(AssertionError):
            documented(page)

    def test_a_row_that_is_not_one_value_is_named(self):
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-t271-page-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        page = d / "page.md"
        page.write_text("| `tracks_source` | means |\n|---|---|\n"
                        "| store or absent | x |\n")
        with self.assertRaises(AssertionError):
            documented(page)


if __name__ == "__main__":
    unittest.main()
