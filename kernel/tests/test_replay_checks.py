"""What `import` checks as it replays (§ 5.8 step 2; TASK-489).

The replay runs no guards, because the history was written under earlier
templates. Before TASK-489 it checked no value either: an export could hand
the kernel an item of a type no template declared, a state or a field its
type never had, an enum value outside its list, or an edge whose ends a
declared kind does not allow, and `import` stored them. Each case below
plants one such change in an otherwise good export and shows `import`
refusing it as `export_invalid`, naming the event and the key. Each check has
its own test, so a mutant of one check turns its own test red.

The template in force is the one the replay has applied before the event, not
the last one the export holds: a value that only a later version allows is
refused where it stands and accepted after that version. So a replayed
template change is held to what `template apply` holds a live one to (its
version rises, and it strands nothing), and an item's type is set once.

Also here, carried from TASK-487's round-3 review:
- F1: a relation change that flips nothing is refused for every kind;
- F2: the import id cap, with ids of 17 and 18 digits above 2^53, which the
  18-digit id bound (`store.MAX_ID_DIGITS`) does not shadow.
"""

from __future__ import annotations

import json
import unittest

from support import ACTOR, HUMAN, Sandbox, template

from perry_kernel.values import INT_LIMIT

AT = "2026-09-29T00:00:00Z"


def line(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


class Export:
    """A good export of `sb`, held as objects, that a test edits and imports
    into a fresh project."""

    def __init__(self, testcase, sb: Sandbox):
        self.t, self.sb = testcase, sb
        sb.ok("export")
        directory = sb.root / sb.state_root / "export"
        self.items = [json.loads(x) for x in
                      (directory / "items.jsonl").read_text("utf-8")
                      .splitlines()]
        self.events = [json.loads(x) for x in
                       (directory / "events.jsonl").read_text("utf-8")
                       .splitlines()]

    def item(self, item_id) -> dict:
        return next(i for i in self.items if i["id"] == item_id)

    def plant(self, changes, items, *, command="planted", touch=True):
        """Append one event; when `touch`, the items it names take its seq
        and time in items.jsonl, as a replay of it would leave them."""
        seq = len(self.events) + 1
        self.events.append({"seq": seq, "at": AT, "actor": ACTOR,
                            "command": command, "items": list(items),
                            "transition": None, "changes": changes,
                            "note": None, "warnings": []})
        if touch:
            for item in self.items:
                if item["id"] in items:
                    item["seq"], item["updated_at"] = seq, AT
        return seq

    def run(self):
        other = Sandbox(self.t, state_root=self.sb.state_root)
        directory = other.root / other.state_root / "export"
        directory.mkdir(parents=True)
        ordered = sorted(self.items, key=lambda i: (
            i["id"].split("-")[0], int(i["id"].split("-")[1])))
        (directory / "items.jsonl").write_text(
            "".join(line(i) for i in ordered), "utf-8")
        (directory / "events.jsonl").write_text(
            "".join(line(e) for e in self.events), "utf-8")
        return other, other.run("import",
                                data={"state_root": other.state_root})


def new_item(item_id, type_name, state, fields, seq):
    return {"id": item_id, "type": type_name, "state": state,
            "fields": fields, "relations": [], "attachments": [],
            "created_at": AT, "updated_at": AT, "seq": seq}


WIDGET_FIELDS = ("bench", "colors", "fragile", "inspector", "label",
                 "made_from", "pieces", "ship_by", "size", "weight_g")


def widget_fields(**given):
    out = {f: None for f in WIDGET_FIELDS}
    out.update(given)
    return out


class Case(unittest.TestCase):

    def setUp(self):
        self.sb = Sandbox(self).ready()
        self.a, self.b = self.sb.create(), self.sb.create()   # W-001, W-002
        self.g = self.sb.create("gauge")                      # G-1

    def export(self) -> Export:
        return Export(self, self.sb)

    def assert_refused(self, result, seq, key, fragment):
        self.assertEqual((result.code, result.code_name),
                         (1, "export_invalid"), result)
        self.assertEqual((result.details["seq"], result.details["key"]),
                         (seq, key), result)
        self.assertIn(fragment, result.env["error"]["message"])

    def assert_imported(self, result):
        self.assertTrue(result.ok, result)
        self.assertTrue(result.result["verified"], result)

    def create_event(self, ex, item_id, type_name, state="queued",
                     fields=None):
        changes = [{"key": "type", "before": None, "after": type_name},
                   {"key": "state", "before": None, "after": state}]
        changes += [{"key": f"field:{k}", "before": None, "after": v}
                    for k, v in sorted((fields or {}).items())]
        return ex.plant(changes, [item_id], command="item create",
                        touch=False)


class TestTheControl(Case):

    def test_a_good_export_with_planted_writes_imports(self):
        """The planting itself is sound: a create, a field and an edge that
        the template allows replay and reproduce items.jsonl."""
        ex = self.export()
        seq = self.create_event(ex, "W-003", "widget",
                                fields={"bench": "south"})
        ex.items.append(new_item("W-003", "widget", "queued",
                                 widget_fields(bench="south"), seq))
        seq = ex.plant([{"key": "rel:pairs_with:W-001:W-003",
                         "before": False, "after": True}], ["W-001", "W-003"])
        ex.item("W-001")["relations"] = [{"kind": "pairs_with",
                                          "to": "W-003"}]
        _other, r = ex.run()
        self.assert_imported(r)
        self.assertEqual(r.result["events"], seq)


class TestTheType(Case):

    def test_a_type_the_template_does_not_declare(self):
        ex = self.export()
        seq = self.create_event(ex, "W-003", "gadget")
        _other, r = ex.run()
        self.assert_refused(r, seq, "type", "declares no type gadget")

    def test_an_id_the_type_does_not_mint(self):
        """The id must be the one the live mint would have made: its type's
        prefix, padded to its digits. `W-3` beside `W-001` is a second
        spelling of one number."""
        for item_id, type_name, minted in (("W-3", "widget", "W-003"),
                                           ("G-002", "gauge", "G-2"),
                                           ("G-3", "widget", "W-003")):
            with self.subTest(item_id=item_id, type=type_name):
                ex = self.export()
                seq = self.create_event(
                    ex, item_id, type_name, state=(
                        "queued" if type_name == "widget" else "live"))
                _other, r = ex.run()
                self.assert_refused(r, seq, "type",
                                    f"its number would be {minted}")
                self.assertEqual(r.details["id"], item_id)

    def test_no_template_in_force(self):
        """An item created before any template was applied."""
        ex = self.export()
        ex.events = [ex.events[0]]
        ex.items = [new_item("W-001", "widget", "queued",
                             {"bench": "north"}, 2)]
        seq = self.create_event(ex, "W-001", "widget",
                                fields={"bench": "north"})
        _other, r = ex.run()
        self.assert_refused(r, seq, "type", "no template is in force")


class TestTheState(Case):

    def test_a_state_the_type_does_not_have(self):
        ex = self.export()
        seq = ex.plant([{"key": "state", "before": "queued",
                         "after": "melted"}], [self.a])
        ex.item(self.a)["state"] = "melted"
        _other, r = ex.run()
        self.assert_refused(r, seq, "state", "has no state \"melted\"")

    def test_a_create_into_a_state_of_another_type(self):
        ex = self.export()
        seq = self.create_event(ex, "W-003", "widget", state="live")
        _other, r = ex.run()
        self.assert_refused(r, seq, "state", "widget has no state \"live\"")


class TestTheFields(Case):

    def set_field(self, field, value, before=None):
        ex = self.export()
        seq = ex.plant([{"key": f"field:{field}", "before": before,
                         "after": value}], [self.a])
        ex.item(self.a)["fields"][field] = value
        _other, r = ex.run()
        return seq, r

    def test_a_field_the_type_does_not_declare(self):
        seq, r = self.set_field("colour", "red")
        self.assert_refused(r, seq, "field:colour",
                            "widget declares no field colour")

    def test_a_value_that_does_not_fit_its_kind(self):
        cases = (
            ("bench", "west", "\"west\" is not one of"),
            ("label", 7, "a text value is a string"),
            ("pieces", 2.5, "an int value is a JSON integer"),
            ("ship_by", "2026-02-30", "a valid calendar date"),
            ("colors", ["red", 3], "element 1: a text value is a string"),
            ("made_from", "W-404", "no item W-404"),
            ("made_from", "G-1", "G-1 is a gauge; this ref takes widget"),
        )
        for field, value, fragment in cases:
            with self.subTest(field=field, value=value):
                before = "north" if field == "bench" else None
                seq, r = self.set_field(field, value, before=before)
                self.assert_refused(r, seq, f"field:{field}", fragment)

    def test_a_metric_that_breaks_the_formula(self):
        ex = self.export()
        bad = {"current": 1, "target": 0, "baseline": 4, "direction": "up"}
        seq = ex.plant([{"key": "field:reading", "before": None,
                         "after": bad}], [self.g])
        ex.item(self.g)["fields"]["reading"] = bad
        _other, r = ex.run()
        self.assert_refused(r, seq, "field:reading",
                            "target must be above baseline")

    def test_a_value_not_in_the_form_the_kernel_stores(self):
        """An actor with no `session` key fits the kind, and a live write
        would have stored it with `session: null`. The replay must not store
        a form no command writes."""
        seq, r = self.set_field("inspector", {"kind": "human", "name": "Pat"})
        self.assert_refused(r, seq, "field:inspector",
                            "not in the form a live write stores (actor)")

    def test_the_stored_form_is_accepted(self):
        """The control for the case above and for the kind checks: the same
        field in the form a live write stores imports."""
        value = dict(HUMAN)
        _seq, r = self.set_field("inspector", value)
        self.assert_imported(r)


class TestTheTemplateInForce(Case):
    """The check reads the template the replay has applied so far."""

    def setUp(self):
        super().setUp()
        wider = template(version=2)
        wider["types"]["widget"]["fields"]["bench"]["values"] = [
            "north", "south", "east"]
        self.sb.apply(wider)
        self.sb.ok("item", "update", data={"actor": ACTOR, "id": self.a,
                                           "set": {"bench": "east"}})

    def test_after_the_version_that_allows_it_the_value_imports(self):
        _other, r = self.export().run()
        self.assert_imported(r)

    def test_before_that_version_the_same_value_is_refused(self):
        ex = self.export()
        template_event, update = ex.events[-2], ex.events[-1]
        self.assertEqual([c["key"] for c in template_event["changes"]],
                         ["template"])
        # Swap them: the update now comes first, under version 1.
        update["seq"], template_event["seq"] = template_event["seq"], \
            update["seq"]
        ex.events[-2:] = [update, template_event]
        ex.item(self.a)["seq"] = update["seq"]
        _other, r = ex.run()
        self.assert_refused(r, update["seq"], "field:bench",
                            "\"east\" is not one of")


class TestTheRelations(Case):

    def add_edge(self, kind, src, dst):
        ex = self.export()
        seq = ex.plant([{"key": f"rel:{kind}:{src}:{dst}", "before": False,
                         "after": True}], [src, dst])
        ex.item(src)["relations"].append({"kind": kind, "to": dst})
        _other, r = ex.run()
        return seq, r

    def test_a_kind_the_template_does_not_declare(self):
        seq, r = self.add_edge("follows", self.a, self.b)
        self.assert_refused(r, seq, f"rel:follows:{self.a}:{self.b}",
                            "declares no relation kind follows")

    def test_ends_the_declared_kind_does_not_allow(self):
        seq, r = self.add_edge("pairs_with", self.a, self.g)
        self.assert_refused(r, seq, f"rel:pairs_with:{self.a}:{self.g}",
                            "pairs_with goes from widget to widget")

    def test_a_built_in_kind_connects_any_types(self):
        _seq, r = self.add_edge("blocks", self.g, self.a)
        self.assert_imported(r)


class TestTheTemplateChange(Case):
    """A replayed `template` change is held to what `template apply` holds a
    live one to: its version rises above the one in force, and it strands no
    stored data (§ 5.2 "Apply" and "Compatibility"). Before, a version that
    did not rise was a sqlite UNIQUE failure reported as `store_corrupt`, and
    a lower one was stored and silently never in force."""

    def plant_template(self, tpl, before):
        ex = self.export()
        seq = ex.plant([{"key": "template", "before": before, "after": tpl}],
                       [], command="template apply", touch=False)
        _other, r = ex.run()
        return seq, r

    def test_a_version_that_does_not_rise(self):
        self.sb.apply(template(version=2))
        for version in (2, 1):
            with self.subTest(version=version):
                changed = template(version=version, name="another")
                seq, r = self.plant_template(changed, 2)
                self.assert_refused(r, seq, "template",
                                    f"version {version} is not above 2")

    def test_a_version_that_strands_stored_data(self):
        narrower = template(version=2)
        narrower["types"]["widget"]["fields"]["bench"]["values"] = ["south"]
        seq, r = self.plant_template(narrower, 1)
        self.assert_refused(r, seq, "template", "would strand stored data")
        self.assertEqual(r.details["problems"][0]["items"],
                         [self.a, self.b])

    def test_a_version_that_adds_imports(self):
        wider = template(version=2)
        wider["types"]["widget"]["fields"]["bench"]["values"] = [
            "north", "south", "east"]
        _seq, r = self.plant_template(wider, 1)
        self.assert_imported(r)


class TestATypeIsSetOnce(Case):

    def test_a_second_create_of_an_existing_id(self):
        """A `type` change for an item that exists. Before, the before
        comparison passed (`before: widget`) and the insert failed as a
        UNIQUE constraint, reported as `store_corrupt`."""
        ex = self.export()
        seq = ex.plant([{"key": "type", "before": "widget",
                         "after": "widget"}], [self.a], command="item create")
        _other, r = ex.run()
        self.assert_refused(r, seq, "type", f"{self.a} exists already")


class TestANoOpRelationChange(Case):
    """F1 (TASK-487 round 3), decided here: a relation change whose edge is
    already what the change says it becomes is refused, whatever the kind.
    No command writes one: `rel add` of an existing edge and `rel remove` of
    a missing one are `unchanged` and append no event (NN-K8). Before, a
    no-op `blocks` change replayed and a no-op `parent` change was refused
    as a second parent of its own."""

    def noop(self, kind, present):
        if present:
            self.sb.ok("rel", "add", data={"actor": ACTOR, "kind": kind,
                                           "from": self.a, "to": self.b})
        ex = self.export()
        key = f"rel:{kind}:{self.a}:{self.b}"
        seq = ex.plant([{"key": key, "before": present, "after": present}],
                       [self.a, self.b])
        _other, r = ex.run()
        return seq, key, r

    def test_a_no_op_parent_change_is_refused(self):
        seq, key, r = self.noop("parent", True)
        self.assert_refused(r, seq, key, "changes nothing")
        self.assertEqual(r.details, {"seq": seq, "key": key})

    def test_a_no_op_blocks_change_is_refused_alike(self):
        seq, key, r = self.noop("blocks", True)
        self.assert_refused(r, seq, key, "changes nothing")
        self.assertEqual(r.details, {"seq": seq, "key": key})

    def test_removing_an_absent_edge_is_refused_alike(self):
        seq, key, r = self.noop("blocks", False)
        self.assert_refused(r, seq, key, "the edge is already absent")

    def test_the_same_edge_flipped_imports(self):
        """The control: the planted event with `before` and `after` apart
        is a real removal, and replays."""
        self.sb.ok("rel", "add", data={"actor": ACTOR, "kind": "parent",
                                       "from": self.a, "to": self.b})
        ex = self.export()
        ex.plant([{"key": f"rel:parent:{self.a}:{self.b}", "before": True,
                   "after": False}], [self.a, self.b])
        ex.item(self.a)["relations"] = []
        _other, r = ex.run()
        self.assert_imported(r)


class TestAnAttachRef(Case):
    """TASK-489 round 3, item 8: a replayed `attach:` change is held to the
    ref check a live `attach add` or `attach remove` runs
    (`check_attachment`). A live write refuses a ref that is empty or only
    white space, or that holds a line break, as `attachment_invalid`. Before
    this check the replay took such a ref from an export and stored it, so
    `import` could hold an attachment no command can write."""

    def plant_attach(self, ref):
        ex = self.export()
        key = f"attach:{ref}"
        seq = ex.plant([{"key": key, "before": None,
                         "after": {"hash": None}}], [self.a])
        ex.item(self.a)["attachments"] = [{"ref": ref, "hash": None}]
        _other, r = ex.run()
        return seq, key, r

    def test_a_ref_a_live_write_refuses_is_refused(self):
        for ref, fragment in (("", "non-empty string"),
                              ("   ", "non-empty string"),
                              ("spec\nnotes.md", "line break"),
                              ("spec\rnotes.md", "line break")):
            with self.subTest(ref=ref):
                seq, key, r = self.plant_attach(ref)
                self.assert_refused(r, seq, key, fragment)

    def test_a_ref_a_live_write_takes_imports(self):
        """The control: the same planting with a ref `attach add` takes."""
        _seq, _key, r = self.plant_attach("docs/a spec.md")
        self.assert_imported(r)


class TestTheOrderInsideAnEvent(Case):
    """TASK-489 round 5 (the second V4 review's FAIL 1). A change replayed
    before its item's `type` change, in the same event, is checked as it
    would be after it. Before, the check stepped aside for an item with no
    type yet, the store wrote the value row anyway, and the later `type`
    change created the item: an enum value outside its list, an undeclared
    field or a wrong-kind value imported. Each kind of change is planted in
    a new item's create, once before `type` and once after."""

    NEW = "W-003"

    def plant(self, change, before_type):
        ex = self.export()
        typed = [{"key": "type", "before": None, "after": "widget"}]
        rest = [{"key": "state", "before": None, "after": "queued"}]
        if change["key"] == "state":
            rest = []
        changes = ([change] + typed + rest if before_type
                   else typed + rest + [change])
        seq = ex.plant(changes, [self.NEW] + (
            [self.g] if change["key"].startswith("rel:") else []),
            command="item create", touch=False)
        ex.items.append(new_item(self.NEW, "widget", "queued",
                                 widget_fields(), seq))
        _other, r = ex.run()
        return seq, r

    CASES = (
        ({"key": "field:bench", "before": None, "after": "west"},
         "\"west\" is not one of"),
        ({"key": "field:colour", "before": None, "after": "red"},
         "widget declares no field colour"),
        ({"key": "field:label", "before": None, "after": 7},
         "a text value is a string"),
        ({"key": "state", "before": None, "after": "lost"},
         "widget has no state \"lost\""),
        ({"key": f"rel:pairs_with:{NEW}:G-1", "before": False, "after": True},
         "pairs_with goes from widget to widget"),
        ({"key": "attach:", "before": None, "after": {"hash": None}},
         "non-empty string"),
    )

    def test_each_kind_of_change_is_checked_in_either_order(self):
        for change, fragment in self.CASES:
            for before_type in (True, False):
                with self.subTest(key=change["key"], before_type=before_type):
                    seq, r = self.plant(dict(change), before_type)
                    self.assert_refused(r, seq, change["key"], fragment)

    def test_a_value_the_template_allows_imports_before_type(self):
        """The control: the check does not refuse a change for its place.
        A declared field with a declared value, before `type`, imports."""
        ex = self.export()
        seq = ex.plant([{"key": "field:bench", "before": None,
                         "after": "south"},
                        {"key": "type", "before": None, "after": "widget"},
                        {"key": "state", "before": None, "after": "queued"}],
                       [self.NEW], command="item create", touch=False)
        ex.items.append(new_item(self.NEW, "widget", "queued",
                                 widget_fields(bench="south"), seq))
        _other, r = ex.run()
        self.assert_imported(r)


class TestATemplateChangeStandsAlone(Case):
    """TASK-489 round 6 (V4 round 3's FAIL). An event never mixes a template
    change with item changes: `template apply` writes it alone, and no other
    command writes one. The crafted input was one event holding a field
    change, then a template change that forbids the value, then the item's
    `type`; the field was checked under the old template and the strand
    check could not see the untyped item. Every order of such an event is
    now refused as a line that breaks § 5.8."""

    NEW = "W-003"

    def mixed(self, order):
        narrower = template(version=2)
        narrower["types"]["widget"]["fields"]["bench"]["values"] = ["north"]
        parts = {
            "field": {"key": "field:bench", "before": None, "after": "south"},
            "template": {"key": "template", "before": None,
                         "after": narrower},
            "type": {"key": "type", "before": None, "after": "widget"},
        }
        ex = self.export()
        changes = [parts[p] for p in order] + [
            {"key": "state", "before": None, "after": "queued"}]
        seq = ex.plant(changes, [self.NEW], command="item create",
                       touch=False)
        ex.items.append(new_item(self.NEW, "widget", "queued",
                                 widget_fields(bench="south"), seq))
        _other, r = ex.run()
        return seq, r

    def test_the_reviewers_order_is_refused(self):
        seq, r = self.mixed(("field", "template", "type"))
        self.assertEqual((r.code, r.code_name), (1, "export_invalid"), r)
        self.assertEqual(r.details["line"], seq)
        self.assertIn("a template change shares its event with item changes",
                      r.env["error"]["message"])

    def test_every_order_is_refused_alike(self):
        import itertools
        for order in itertools.permutations(("field", "template", "type")):
            with self.subTest(order=order):
                _seq, r = self.mixed(order)
                self.assertEqual(r.code_name, "export_invalid", r)
                self.assertIn("shares its event with item changes",
                              r.env["error"]["message"])

    def test_each_item_change_kind_independently_rejects_a_template_mix(self):
        # Each key independently matters. A field+type+state fixture masks
        # a missing branch in _event_shape's mixed-event predicate.
        changes = [
            {"key": "type", "before": None, "after": "widget"},
            {"key": "state", "before": "queued", "after": "cutting"},
            {"key": "field:bench", "before": "north", "after": "south"},
            {"key": "rel:pairs_with:W-001:W-002", "before": False, "after": True},
            {"key": "attach:evidence/review.md", "before": None,
             "after": {"hash": None}},
        ]
        for change in changes:
            for template_first in (False, True):
                with self.subTest(key=change["key"], template_first=template_first):
                    ex = self.export()
                    template_change = {"key": "template", "before": None,
                                       "after": template(version=2)}
                    mixed = ([template_change, change] if template_first
                             else [change, template_change])
                    seq = ex.plant(mixed, [self.a], touch=False)
                    _other, result = ex.run()
                    self.assertEqual(result.code_name, "export_invalid", result)
                    self.assertEqual(result.details["line"], seq)
                    self.assertIn("shares its event with item changes",
                                  result.env["error"]["message"])

    def test_a_template_change_alone_still_imports(self):
        """The control: `template apply`'s own event, alone, replays."""
        self.sb.apply(template(version=2))
        _other, r = self.export().run()
        self.assert_imported(r)


class TestTheImportIdCap(Case):
    """F2: `import` takes no id numbered above 2^53 (`commands._export_id`),
    so a store never holds an id its own mint could not follow. Its only
    test used a 30-digit id, which the 18-digit bound on an id's number
    (`store.MAX_ID_DIGITS`, D2) now refuses first. Ids of 17 and 18 digits
    above 2^53 pass that bound and reach this cap alone."""

    def create_big(self, number):
        ex = self.export()
        item_id = f"W-{number}"
        seq = self.create_event(ex, item_id, "widget",
                                fields={"bench": "north"})
        ex.items.append(new_item(item_id, "widget", "queued",
                                 widget_fields(bench="north"), seq))
        _other, r = ex.run()
        return item_id, seq, r

    def test_ids_of_17_and_18_digits_above_the_cap_are_refused(self):
        for number in (10 ** 16, 10 ** 17, 999_999_999_999_999_999):
            with self.subTest(digits=len(str(number))):
                self.assertGreater(number, INT_LIMIT)
                self.assertIn(len(str(number)), (17, 18))
                _item_id, seq, r = self.create_big(number)
                self.assertEqual((r.code, r.code_name),
                                 (1, "export_invalid"), r)
                self.assertIn(f"numbered up to {INT_LIMIT}",
                              r.env["error"]["message"])
                self.assertEqual(r.details["line"], seq)

    def test_the_cap_itself_imports(self):
        """The control, at the edge: 2^53 is the highest number an id may
        carry, and an export holding it imports."""
        item_id, _seq, r = self.create_big(INT_LIMIT)
        self.assert_imported(r)
        self.assertEqual(r.result["items"], 4)
        self.assertEqual(item_id, f"W-{INT_LIMIT}")


if __name__ == "__main__":
    unittest.main()
