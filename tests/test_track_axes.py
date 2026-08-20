"""The mode-contract slot table — DESIGN-008 § 5.2, written by TASK-140.

The claim under test: **every slot in every mode contract table has exactly one
axis, and the four mode names are presets that expand to a (spine, flow) pair
which reproduces that mode file's own table value by value.**

Three things make this file worth having rather than a restatement of the
design.

**1. Coverage is mechanical, not eyeballed.** The slot names are extracted from
`modes/*.md` at run time and compared against § 5.2 in both directions, so a
slot added to a mode file with no axis reddens, and a slot deleted from a mode
file leaves a row in § 5.2 that names a file no longer carrying it — which
reddens too, via the `In` column. That column exists for this reason: without
it, deleting `Spine` from one of the four files would be invisible, because
three files would still carry the name.

**2. The round-trip is value by value.** Each preset expands to a pair, the
per-axis value maps are built from the mode files keyed by *leg value* rather
than by mode name, and each preset's table is then recomposed and compared cell
for cell, in order. The teeth are in the keying: two presets that are assigned
the same leg value must agree on every slot of that axis. That is what forced
`pipeline` and `queue` apart into two spine values — both spine cells cite
`OKR.md § Commitments`, and the sketch grouped them, but their `Spine`,
`Ends when`, `Horizon` and `Unit` cells all differ, so one value cannot hold
both.

**3. The spine → unit map is load-bearing, not documentation.** Decision #2
deleted the declarable "unit" field on the ground that each spine implies
exactly one unit, so a spine with no unit is unrepresentable rather than
awkward (§ 7). The map is checked complete and one-to-one, and each mode file's
own `Unit that gets an ID` cell is checked to name its spine's unit *first* —
which is not vacuous, since pipeline's cell reads "the deliverable, not the
task" and contains two unit words.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
DESIGN = PERRY_HOME / "perry" / "design" / "DESIGN-008-track-axes.md"

MODES = ["project", "pipeline", "queue", "inquiry"]
AXES = {"spine", "flow", "derived", "field"}

# Counted, not estimated. §§ 1.1 and 2 of the design say "~28 distinct"; that
# figure predates anyone counting and § 5.2 records the measured one.
SLOTS_PER_MODE = {"project": 10, "pipeline": 14, "queue": 12, "inquiry": 14}
DISTINCT_SLOTS = 21


# --------------------------------------------------------------------------
# markdown table reading — stdlib only, like everything else here
# --------------------------------------------------------------------------

_SEPARATOR = re.compile(r"\|[\s\-:|]+\|")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def plain(cell: str) -> str:
    """A cell with its markdown emphasis and code ticks removed."""
    return cell.replace("**", "").replace("`", "").replace("*", "").strip()


def tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    out: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i < len(lines):
        head = lines[i].strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if head.startswith("|") and _SEPARATOR.fullmatch(nxt):
            header = cells(head)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            out.append((header, rows))
        else:
            i += 1
    return out


def section(text: str, heading: str) -> str:
    """The body of one `### N.M` section, up to the next heading of any level."""
    keep: list[str] = []
    on = False
    for line in text.splitlines():
        if line.startswith(heading):
            on = True
            continue
        if on and re.match(r"^#{1,3} ", line):
            break
        if on:
            keep.append(line)
    if not on:
        raise AssertionError(f"{heading!r} not found")
    return "\n".join(keep)


def table_with_header(text: str, first: str, width: int):
    for header, rows in tables(text):
        if plain(header[0]) == first and len(header) == width:
            return header, rows
    raise AssertionError(
        f"no table under this section whose first column is {first!r} "
        f"and which has {width} columns")


# --------------------------------------------------------------------------
# the two sides being compared
# --------------------------------------------------------------------------

DESIGN_TEXT = DESIGN.read_text()
S52 = section(DESIGN_TEXT, "### 5.2")


def mode_contract(mode: str) -> list[tuple[str, str, str]]:
    """(slot, value, where-it-is-written) for one mode file, in file order."""
    text = (PERRY_HOME / "modes" / f"{mode}.md").read_text()
    _, rows = table_with_header(text, "Slot", 3)
    return [(plain(r[0]), r[1].strip(), r[2].strip()) for r in rows]


CONTRACTS = {m: mode_contract(m) for m in MODES}


def slot_table() -> list[tuple[str, list[str], str, str]]:
    """(slot, modes-it-is-in, axis, why) from § 5.2, in table order."""
    _, rows = table_with_header(S52, "Slot", 4)
    out = []
    for r in rows:
        modes = [plain(m) for m in r[1].split("·")]
        out.append((plain(r[0]), modes, plain(r[2]), r[3].strip()))
    return out


def unit_map() -> dict[str, str]:
    _, rows = table_with_header(S52, "Spine", 3)
    return {plain(r[0]): plain(r[2]) for r in rows}


def presets() -> dict[str, tuple[str, str]]:
    _, rows = table_with_header(S52, "Mode", 3)
    return {plain(r[0]): (plain(r[1]), plain(r[2])) for r in rows}


SLOTS = slot_table()
AXIS_OF = {s: a for s, _, a, _ in SLOTS}
IN_OF = {s: m for s, m, _, _ in SLOTS}
UNITS = unit_map()
PRESETS = presets()


# --------------------------------------------------------------------------


class TestTheTableIsWellFormed(unittest.TestCase):
    def test_every_row_names_one_of_the_four_axes(self):
        for slot, _, axis, _ in SLOTS:
            self.assertIn(axis, AXES, f"{slot!r} has axis {axis!r}")

    def test_no_slot_is_listed_twice(self):
        names = [s for s, _, _, _ in SLOTS]
        self.assertEqual(len(names), len(set(names)),
                         "a slot with two rows has two axes")

    def test_only_the_obvious_rows_go_without_a_reason(self):
        """A table where every row carries prose is one nobody reads, so this
        checks the inverse of the usual rule: the *contested* assignments must
        be argued. These four are the ones the design's own § 4 and § 5.2 call
        out as not self-evident."""
        for slot in ["Unit that gets an ID", "Calendar", "Default rung",
                     "Question clock"]:
            why = dict((s, w) for s, _, _, w in SLOTS)[slot]
            self.assertTrue(why.strip(), f"{slot!r} is assigned with no reason")


class TestCoverageAgainstTheModeFiles(unittest.TestCase):
    """V3 item 1. Both directions, because either alone is half a check."""

    def test_the_counts_are_what_the_section_claims(self):
        for mode, n in SLOTS_PER_MODE.items():
            self.assertEqual(len(CONTRACTS[mode]), n,
                             f"modes/{mode}.md contract table")
        distinct = {s for m in MODES for s, _, _ in CONTRACTS[m]}
        self.assertEqual(len(distinct), DISTINCT_SLOTS)
        self.assertEqual(len(SLOTS), DISTINCT_SLOTS)

    def test_every_slot_in_a_mode_file_is_assigned(self):
        """Add a slot to a mode file and this reddens."""
        for mode in MODES:
            for slot, _, _ in CONTRACTS[mode]:
                self.assertIn(
                    slot, AXIS_OF,
                    f"modes/{mode}.md has slot {slot!r} with no row in § 5.2")

    def test_every_assigned_slot_is_in_a_mode_file(self):
        """Delete a slot from every mode file and this reddens."""
        live = {s for m in MODES for s, _, _ in CONTRACTS[m]}
        for slot in AXIS_OF:
            self.assertIn(slot, live,
                          f"§ 5.2 assigns {slot!r}, which no mode file carries")

    def test_the_in_column_matches_the_files(self):
        """Delete a slot from *one* mode file and this reddens — which the two
        checks above cannot do for a slot four files share."""
        for slot, listed, _, _ in SLOTS:
            actual = [m for m in MODES if slot in dict(
                (s, v) for s, v, _ in CONTRACTS[m])]
            self.assertEqual(listed, actual, f"§ 5.2 `In` column for {slot!r}")


class TestTheSpineToUnitMap(unittest.TestCase):
    """V3 item 3."""

    def test_every_spine_a_preset_uses_has_a_unit(self):
        for mode, (spine, _) in PRESETS.items():
            self.assertIn(spine, UNITS,
                          f"preset {mode!r} has spine {spine!r} with no unit")
            self.assertTrue(UNITS[spine].strip(),
                            f"spine {spine!r} has an empty unit cell")

    def test_no_unit_appears_under_two_spines(self):
        units = list(UNITS.values())
        self.assertEqual(len(units), len(set(units)),
                         f"the map is not one-to-one: {units}")

    def test_the_map_covers_the_spine_vocabulary_exactly(self):
        self.assertEqual(set(UNITS), {s for s, _ in PRESETS.values()})

    def test_each_mode_files_unit_cell_names_its_spines_unit(self):
        """Not vacuous: pipeline's cell reads "the deliverable, not the task"
        and contains two unit words, so the mapped one must come first."""
        vocabulary = set(UNITS.values())
        for mode in MODES:
            cell = dict((s, v) for s, v, _ in CONTRACTS[mode])[
                "Unit that gets an ID"].lower()
            hits = sorted((cell.index(u), u) for u in vocabulary if u in cell)
            self.assertTrue(hits, f"modes/{mode}.md names no known unit")
            self.assertEqual(hits[0][1], UNITS[PRESETS[mode][0]],
                             f"modes/{mode}.md's unit cell: {cell!r}")

    def test_queues_unit_is_the_one_the_schema_already_records(self):
        """The choice between "the request" and "the incident" was not free."""
        import json
        schema = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text())
        for mode in MODES:
            spine = PRESETS[mode][0]
            self.assertIn(spine, UNITS, f"spine {spine!r} has no unit row")
            self.assertEqual(
                schema["work_modes"]["modes"][mode]["unit"], UNITS[spine],
                f"§ 5.2's map and the schema disagree about {mode}'s unit")


class TestThePresetsRoundTrip(unittest.TestCase):
    """V3 item 2 — value by value, not "a pair exists"."""

    @classmethod
    def setUpClass(cls):
        cls.spine_map, cls.flow_map = {}, {}
        cls.field_map, cls.derived_map = {}, {}
        cls.conflicts = []
        for mode in MODES:
            spine, flow = PRESETS[mode]
            for slot, value, _ in CONTRACTS[mode]:
                # An unassigned slot is `test_every_slot_in_a_mode_file_is_
                # assigned`'s red, not a KeyError that takes six unrelated
                # tests down with it.
                axis = AXIS_OF.get(slot)
                if axis is None:
                    continue
                if axis == "spine":
                    bucket, key = cls.spine_map, spine
                elif axis == "flow":
                    bucket, key = cls.flow_map, flow
                elif axis == "field":
                    bucket, key = cls.field_map, mode
                else:
                    bucket, key = cls.derived_map, (spine, flow)
                prior = bucket.setdefault(key, {}).get(slot)
                if prior is not None and prior != value:
                    cls.conflicts.append((axis, key, slot, prior, value))
                bucket[key][slot] = value

    def test_no_two_presets_sharing_a_leg_disagree_about_that_legs_slots(self):
        """The check with the teeth. Give `pipeline` and `queue` one spine
        value — which is what § 5.2's sketch implied by grouping both under
        "commitments" — and `Spine`, `Ends when`, `Horizon` and `Unit` land
        here at once."""
        self.assertEqual(self.conflicts, [])

    def test_each_preset_reproduces_its_own_contract_table(self):
        for mode in MODES:
            spine, flow = PRESETS[mode]
            rebuilt = []
            for slot, _, _ in CONTRACTS[mode]:
                axis = AXIS_OF.get(slot)
                self.assertIsNotNone(axis, f"{mode}: {slot!r} has no axis")
                source = {
                    "spine": self.spine_map.get(spine, {}),
                    "flow": self.flow_map.get(flow, {}),
                    "field": self.field_map.get(mode, {}),
                    "derived": self.derived_map.get((spine, flow), {}),
                }[axis]
                self.assertIn(slot, source,
                              f"{mode}: {slot!r} is on axis {axis!r} but that "
                              f"leg supplies no value for it")
                rebuilt.append((slot, source[slot]))
            self.assertEqual(rebuilt, [(s, v) for s, v, _ in CONTRACTS[mode]],
                             f"{mode} does not round-trip")

    def test_a_preset_is_the_diagonal_pair(self):
        self.assertEqual(set(PRESETS), set(MODES))
        for mode, (spine, flow) in PRESETS.items():
            self.assertEqual((spine, flow), (mode, mode))


class TestMixedTracks(unittest.TestCase):
    """The pairs the presets do not cover — what this table is for."""

    def _compose(self, spine: str, flow: str) -> dict[str, str]:
        rt = TestThePresetsRoundTrip
        out = {}
        for slot, axis in AXIS_OF.items():
            leg = (rt.spine_map.get(spine, {}) if axis == "spine"
                   else rt.flow_map.get(flow, {}) if axis == "flow"
                   else {})
            if slot in leg:
                out[slot] = leg[slot]
        return out

    @classmethod
    def setUpClass(cls):
        TestThePresetsRoundTrip.setUpClass()

    def test_the_two_axes_compose_for_all_sixteen_pairs(self):
        """Every pair renders every spine slot of its spine and every flow slot
        of its flow. A slot filed on the wrong axis strands itself here."""
        rt = TestThePresetsRoundTrip
        for leg, m in (("spine", rt.spine_map), ("flow", rt.flow_map)):
            self.assertEqual(set(m), set(MODES),
                             f"the {leg} vocabulary is not the four presets")
        for spine in MODES:
            for flow in MODES:
                got = self._compose(spine, flow)
                want = set(rt.spine_map[spine]) | set(rt.flow_map[flow])
                self.assertEqual(set(got), want, f"({spine}, {flow})")

    def test_the_motivating_case_renders(self):
        """§ 1.3 and § 5.1 row 2: this repository. Goals decompose through
        `project`; the work that arrives is advanced as a `queue`."""
        got = self._compose("project", "queue")
        self.assertIn("Arrival", got, "queue's flow must bring the arrival date")
        self.assertIn("SLA", got, "queue's flow must bring the SLA clock")
        self.assertEqual(got["Horizon"],
                         dict((s, v) for s, v, _ in CONTRACTS["project"])["Horizon"],
                         "the phase is still the horizon")
        self.assertNotIn("Commitment link", got,
                         "an objectives spine has no commitment to link")

    def test_the_unit_is_total_over_every_pair(self):
        """#2's worked example, checked rather than asserted: changing how work
        is advanced must not change what a row is. `Unit` is the one `derived`
        slot that reads the spine alone, so unlike the other three it renders
        for all sixteen pairs and not only the four diagonals."""
        for spine in MODES:
            self.assertIn(spine, UNITS,
                          f"spine {spine!r} renders no unit, so a track on it "
                          f"has rows that are not anything (§ 7)")
        self.assertEqual(UNITS["project"], "task",
                         "project spine + queue flow still works tasks, not "
                         "requests — § 4's note on decision #2")

    def test_the_other_derived_slots_stop_at_the_diagonals(self):
        """Named so the boundary is visible rather than assumed: rendering
        these off the diagonal is § 6 step 4's job, which is why step 4 depends
        on this table."""
        rt = TestThePresetsRoundTrip
        deferred = {s for s, a in AXIS_OF.items()
                    if a == "derived" and s != "Unit that gets an ID"}
        self.assertEqual(deferred,
                         {"Calendar", "Triage asks", "Signature failure"})
        self.assertEqual(set(rt.derived_map), {(m, m) for m in MODES},
                         "an off-diagonal pair gained a rendering here; that "
                         "belongs to step 4, not to this row")


class TestWhatEachAxisMeans(unittest.TestCase):
    """The four axis words have operational definitions in § 5.2, and a table
    that used them loosely would still pass everything above."""

    def _where(self, slot: str) -> list[str]:
        return [w for m in MODES
                for s, _, w in CONTRACTS[m] if s == slot]

    def test_a_derived_slot_names_no_column_anywhere(self):
        """`derived` means "written nowhere and rendered at read time" (#2).
        A slot with a column is declared, and a declared field can hold a wrong
        value — which is the whole of #2's argument."""
        for slot, axis in AXIS_OF.items():
            if axis != "derived":
                continue
            for where in self._where(slot):
                self.assertNotIn(
                    "→", where,
                    f"{slot!r} is `derived` but points at a column: {where!r}")

    def test_the_field_is_a_register_column(self):
        """`field` means declared per track in `## Tracks` (#1). If no mode
        file says so, it is not a field."""
        for slot, axis in AXIS_OF.items():
            if axis != "field":
                continue
            joined = " ".join(
                v for m in MODES for s, v, _ in CONTRACTS[m] if s == slot)
            self.assertIn("Tracks", joined,
                          f"{slot!r} is a `field` that no register column holds")

    def test_the_axes_partition_the_slots(self):
        counts = {a: sum(1 for x in AXIS_OF.values() if x == a) for a in AXES}
        self.assertEqual(sum(counts.values()), DISTINCT_SLOTS)
        # § 5.2's own summary line: "Eight spine, eight flow, four derived, one
        # field." A mode file that gains or loses a slot should have to move
        # this number rather than slide under it.
        self.assertEqual(counts, {"spine": 8, "flow": 8, "derived": 4,
                                  "field": 1})


if __name__ == "__main__":
    unittest.main()
