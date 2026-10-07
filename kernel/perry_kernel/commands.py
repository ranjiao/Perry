"""What each command does (§ 5.6). One command is one transaction (§ 4).

A write computes its changes against the store it has locked, applies them
through `Store.apply_changes`, runs the guards against the result, and then
appends one event. Any refusal after `BEGIN` leaves by an exception, and the
`with` block rolls the whole transaction back.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import secrets
from pathlib import Path, PurePosixPath

from . import guards as guard_mod
from . import template as tpl
from .errors import KernelError
from .paths import resolve_anchor, resolve_store
from .store import Store, id_order, split_id
from .values import (INT_LIMIT, ValueProblem, canonical, check_metric,
                     check_scalar, effective, input_problem, merge_metric,
                     metric_fraction, metric_met, normalize_actor, same,
                     with_derived)

DEFAULT_LIMIT = 50
EXPORT_DIR = "export"
EXPORT_FILES = ("items.jsonl", "events.jsonl")
#: `export` writes each file under a temporary name and renames it into
#: place. The name carries a token the store records when it is created
#: (`init`, `import`), before any export can write, so a file left by a
#: crashed export is one the kernel can prove it made. Nothing else in the
#: directory is removed: every other entry is foreign (§ 5.8).
EXPORT_TOKEN = "export_token"
#: The token's one shape (`new_export_token`). A stored token of any other
#: shape is damage: it becomes part of a file name, so it is refused as
#: `store_corrupt` before any name is built from it (TASK-489, F6).
TOKEN_RE = re.compile(r"[0-9a-f]{16}")
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
EVENT_KEYS = ("seq", "at", "actor", "command", "items", "transition",
              "changes", "note", "warnings")
ITEM_KEYS = ("id", "type", "state", "fields", "relations", "attachments",
             "created_at", "updated_at", "seq")


class Outcome:
    def __init__(self, effect, result, *, events=(), warnings=()):
        self.effect = effect
        self.result = result
        self.events = list(events)
        self.warnings = list(warnings)


class Ctx:
    """One invocation: its flags, input, environment and working directory."""

    def __init__(self, name, flags, data, actor, environ, cwd):
        self.name = name
        self.flags = flags
        self.input = data
        self.actor = actor
        self.environ = environ
        self.cwd = cwd
        self.dry_run = bool(flags.get("--dry-run"))
        self.store_seq = None
        self._anchor = None

    def anchor(self) -> Path:
        if self._anchor is None:
            self._anchor = resolve_anchor(self.flags.get("--root"),
                                          self.environ, self.cwd)
        return self._anchor

    def store_path(self):
        return resolve_store(self.flags.get("--store"), self.environ,
                             self.cwd, self.anchor)

    def open(self, *, write: bool) -> Store:
        path, _derived = self.store_path()
        store = Store.open(path, write=write)
        try:
            self.store_seq = store.store_seq()
        except BaseException:
            store.__exit__(None, None, None)
            raise
        return store


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


# ── shared pieces ──────────────────────────────────────────────────────────


def require_template(store: Store) -> dict:
    row = store.template_row()
    if row is None:
        raise KernelError("no_template", "no template has been applied; run "
                                         "template apply")
    return tpl.normalize(row["template"])


def require_item(store: Store, item_id: str, what: str = "id") -> dict:
    row = store.item_row(item_id)
    if row is None:
        raise KernelError("item_not_found", f"no item {item_id}",
                          {what: item_id})
    return row


def check_expect(store: Store, expect) -> None:
    stale = []
    for item_id, seq in sorted((expect or {}).items(),
                               key=lambda kv: id_order(kv[0])):
        row = require_item(store, item_id, "expect")
        if row["seq"] != seq:
            stale.append({"id": item_id, "expected": seq, "actual": row["seq"]})
    if stale:
        raise KernelError("stale_write",
                          "an item named in expect has moved since it was read",
                          {"items": stale})


def value_error(exc: ValueProblem, field: str) -> KernelError:
    return KernelError(exc.code, f"{field}: {exc.message}", {"field": field})


def check_fields(store: Store, tdecl: dict, type_name: str, given: dict,
                 stored: dict) -> dict:
    """`{field: new value or None}` for every field named in `given`."""
    out = {}
    for field in sorted(given):
        decl = tdecl["fields"].get(field)
        if decl is None:
            raise KernelError("unknown_field",
                              f"{type_name} declares no field {field}",
                              {"type": type_name, "field": field})
        value = given[field]
        try:
            if value is None:
                out[field] = None
            elif decl["kind"] == "metric":
                out[field] = merge_metric(stored.get(field), value)
            else:
                out[field] = check_scalar(decl, value, lookup=store.item_type)
        except ValueProblem as exc:
            raise value_error(exc, field)
    return out


def check_unset(tdecl: dict, type_name: str, names, given: dict) -> None:
    for field in names:
        if field not in tdecl["fields"]:
            raise KernelError("unknown_field",
                              f"{type_name} declares no field {field}",
                              {"type": type_name, "field": field})
        if field in given:
            raise KernelError("input_invalid",
                              f"{field} is both in set and in unset",
                              {"field": field})


def field_changes(stored: dict, new: dict) -> list[dict]:
    changes = []
    for field in sorted(new):
        before, after = stored.get(field), new[field]
        if not same(before, after):
            changes.append({"key": f"field:{field}", "before": before,
                            "after": after})
    return changes


def check_edge_types(norm: dict, kind: str, src: str, dst: str,
                     src_type: str, dst_type: str) -> None:
    """A declared kind's end types. The shape every edge keeps — no
    self-edge, one parent, no cycle — is `Store._check_edge_shape`'s, on the
    one path that writes an edge."""
    decl = norm["relations"].get(kind)
    if decl is not None:
        if src_type not in decl["from"] or dst_type not in decl["to"]:
            raise KernelError(
                "relation_invalid",
                f"{kind} goes from {', '.join(decl['from'])} to "
                f"{', '.join(decl['to'])}; {src} is a {src_type} and {dst} a "
                f"{dst_type}", {"kind": kind, "from": src, "to": dst})


def require_relation_kind(norm: dict, kind: str) -> None:
    if kind not in tpl.relation_kinds(norm):
        raise KernelError("unknown_relation", f"no relation kind {kind}",
                          {"kind": kind})


def check_attachment(ref, digest) -> None:
    if not isinstance(ref, str) or not ref.strip():
        raise KernelError("attachment_invalid", "an attachment ref is a "
                                                "non-empty string")
    if "\n" in ref or "\r" in ref:
        raise KernelError("attachment_invalid", "an attachment ref holds no "
                                                "line break", {"ref": ref})
    if digest is not None and not HASH_RE.match(digest):
        raise KernelError("attachment_invalid",
                          "a hash is sha256: and 64 lowercase hex digits",
                          {"ref": ref, "hash": digest})


def new_event(store, ctx, items, changes, *, transition=None) -> dict:
    return {"seq": store.store_seq() + 1, "at": now(), "actor": ctx.actor,
            "command": ctx.name, "items": items, "transition": transition,
            "changes": changes, "note": ctx.input.get("note"), "warnings": []}


def finish(store: Store, ctx, event: dict, result_fn) -> Outcome:
    """Append the event, build the result from the store as written, then
    commit or, for `--dry-run`, roll back."""
    store.append_event(event)
    result = result_fn()
    warnings = event["warnings"]
    if ctx.dry_run:
        store.rollback()
        return Outcome("dry_run", result, warnings=warnings)
    store.commit()
    ctx.store_seq = event["seq"]
    return Outcome("written", result, events=[event["seq"]],
                   warnings=warnings)


def unchanged(store: Store, ctx, result) -> Outcome:
    store.rollback()
    return Outcome("dry_run" if ctx.dry_run else "unchanged", result)


def run_guards(store, norm, ctx, event, guards, item_id, target_state):
    refusals, warns = guard_mod.evaluate(
        guards, store=store, norm=norm, item_id=item_id,
        target_state=target_state, actor=ctx.actor)
    if refusals:
        raise KernelError(
            "guard_refused",
            f"{len(refusals)} guard(s) refused "
            f"{'the create' if ctx.name == 'item create' else 'the move'} "
            f"of {item_id}",
            {"guards": refusals, "warnings": warns})
    event["warnings"] = [
        {"code": "limit_exceeded",
         "message": f"limit guard {w['index']}: {w['detail']['count']} items "
                    f"would sit in {target_state}, above {w['detail']['max']}",
         **w} for w in warns]


# ── derived output ─────────────────────────────────────────────────────────


def rollup(store: Store, norm: dict, item_id: str):
    members = []
    for _k, child, _d in store.edges(kind="parent", dst=item_id):
        cdecl = norm["types"][store.item_type(child)]
        stored = store.values(child)
        for field, decl in cdecl["fields"].items():
            if decl["kind"] == "metric":
                members.append(stored.get(field))
    if not members:
        return None
    measured = [m for m in members
                if m is not None and m.get("current") is not None]
    if len(measured) < len(members):
        met = None
    else:
        met = all(metric_met(m) for m in measured)
    fraction = None
    if len(members) == 1 and members[0] is not None:
        fraction = metric_fraction(members[0])
    return {"members": len(members), "measured": len(measured), "met": met,
            "fraction": fraction}


def blocked_by(store: Store, norm: dict, item_id: str) -> list[str]:
    out = []
    for _k, src, _d in store.edges(kind="blocks", dst=item_id):
        row = store.item_row(src)
        if row["state"] not in norm["types"][row["type"]]["terminal"]:
            out.append(src)
    return sorted(set(out), key=id_order)


def render_item(store: Store, norm: dict, item_id: str) -> dict:
    row = store.item_row(item_id)
    tdecl = norm["types"][row["type"]]
    stored = store.values(item_id)
    fields = {}
    for field, decl in tdecl["fields"].items():
        value = stored.get(field)
        if decl["kind"] == "metric" and value is not None:
            value = with_derived(value)
        fields[field] = value
    blockers = blocked_by(store, norm, item_id)
    return {
        "id": row["id"], "type": row["type"], "state": row["state"],
        "fields": fields, "seq": row["seq"], "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "relations": [{"kind": k, "from": s, "to": d}
                      for k, s, d in store.edges_touching(item_id)],
        "attachments": store.attachments(item_id),
        "startable": row["state"] == tdecl["initial"] and not blockers,
        "blocked_by": blockers,
        "rollup": rollup(store, norm, item_id),
    }


# ── init ───────────────────────────────────────────────────────────────────


def normalize_state_root(text) -> str:
    if not isinstance(text, str) or not text.strip():
        raise KernelError("input_invalid", "state_root is a non-empty relative "
                                           "path", {"key": "state_root"})
    if "\\" in text or "\n" in text or "\0" in text:
        raise KernelError("input_invalid", "state_root holds a character a "
                                           "path cannot", {"key": "state_root"})
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts:
        raise KernelError("input_invalid", "state_root is a relative path "
                                           "inside the anchor",
                          {"key": "state_root", "value": text})
    return path.as_posix()


def cmd_init(ctx: Ctx) -> Outcome:
    state_root = normalize_state_root(ctx.input["state_root"])
    anchor = ctx.anchor()
    path, _derived = ctx.store_path()
    result = {"store": str(path), "anchor": str(anchor),
              "state_root": state_root, "journal_mode": "wal"}
    # The probe refuses a foreign file before anything writes to it; whether
    # the store is initialised is decided again under the lock (F6).
    probe = Store.probe(path)
    if probe != "store" and ctx.dry_run:
        ctx.store_seq = 0
        return Outcome("dry_run", result)
    store = ctx.open(write=True) if probe == "store" else Store.create(path)
    with store:
        if store.contents() == "store":
            ctx.store_seq = store.store_seq()
            existing = store.meta("state_root")
            if existing != state_root:
                raise KernelError(
                    "store_initialized",
                    f"{path} was initialised with state root {existing}",
                    {"store": str(path), "state_root": existing,
                     "requested": state_root})
            return unchanged(store, ctx, result)
        store.initialise()
        store.set_meta(EXPORT_TOKEN, new_export_token())
        ctx.store_seq = 0
        event = new_event(store, ctx, [], [
            {"key": "state_root", "before": None, "after": state_root}])
        store.apply_changes(event, mismatch="internal")
        journal = store.q("PRAGMA journal_mode")[0][0]
        result["journal_mode"] = str(journal).lower()
        return finish(store, ctx, event, lambda: result)


# ── template ───────────────────────────────────────────────────────────────


def _template_or_refuse(template) -> None:
    problems = tpl.validate(template)
    if problems:
        raise KernelError("template_invalid",
                          f"the template has {len(problems)} problem(s); the "
                          f"first: {problems[0]['path']}: "
                          f"{problems[0]['message']}",
                          {"problems": problems})


def incompatibilities(store: Store, old: dict, new: dict) -> list[dict]:
    """What a new version would strand (§ 5.2 "Compatibility")."""
    found: dict[str, list[str]] = {}

    def note(message, item_id):
        found.setdefault(message, [])
        if item_id not in found[message]:
            found[message].append(item_id)

    for item_id in store.all_item_ids():
        row = store.item_row(item_id)
        t = row["type"]
        if t not in new["types"]:
            note(f"type {t} is removed and has items", item_id)
            continue
        odecl, ndecl = old["types"][t], new["types"][t]
        if row["state"] not in ndecl["states"]:
            note(f"state {t}.{row['state']} is removed and items occupy it",
                 item_id)
        if (odecl["prefix"], odecl["digits"]) != (ndecl["prefix"],
                                                  ndecl["digits"]):
            note(f"type {t} changes its prefix or digits and has items",
                 item_id)
        for field, value in store.values(item_id).items():
            fdecl = ndecl["fields"].get(field)
            if fdecl is None:
                note(f"field {t}.{field} is removed and holds a value", item_id)
                continue
            ofdecl = odecl["fields"].get(field, {})
            if (ofdecl.get("kind") != fdecl["kind"]
                    or (fdecl["kind"] == "list"
                        and ofdecl.get("of", {}).get("kind")
                        != fdecl["of"]["kind"])):
                note(f"field {t}.{field} changes kind and holds a value",
                     item_id)
                continue
            try:
                if fdecl["kind"] == "metric":
                    check_metric(value)
                else:
                    check_scalar(fdecl, value, lookup=store.item_type)
            except ValueProblem as exc:
                note(f"field {t}.{field} would no longer hold its value: "
                     f"{exc.message}", item_id)
    for kind, src, dst in store.edges():
        if kind in tpl.BUILTIN_RELATIONS:
            continue
        decl = new["relations"].get(kind)
        if decl is None:
            note(f"relation kind {kind} is removed and has edges", src)
            continue
        if (store.item_type(src) not in decl["from"]
                or store.item_type(dst) not in decl["to"]):
            note(f"relation kind {kind} no longer allows an edge it holds",
                 src)
    return [{"message": m, "items": sorted(ids, key=id_order)}
            for m, ids in found.items()]


def cmd_template_apply(ctx: Ctx) -> Outcome:
    template = ctx.input["template"]
    _template_or_refuse(template)
    new = tpl.normalize(template)
    with ctx.open(write=True) as store:
        row = store.template_row()
        previous = row["version"] if row else None
        result = {"name": template["name"], "version": template["version"],
                  "previous_version": previous}
        if row is not None:
            if template["version"] == previous:
                if canonical(template) == canonical(row["template"]):
                    return unchanged(store, ctx, result)
                raise KernelError("template_version",
                                  f"version {previous} is applied with "
                                  f"different content; raise the version",
                                  {"applied": previous})
            if template["version"] < previous:
                raise KernelError("template_version",
                                  f"version {template['version']} is not "
                                  f"above the applied {previous}",
                                  {"applied": previous,
                                   "given": template["version"]})
            stranded = incompatibilities(store, tpl.normalize(row["template"]),
                                         new)
            if stranded:
                raise KernelError("template_incompatible",
                                  f"version {template['version']} would strand "
                                  f"stored data: {stranded[0]['message']}",
                                  {"problems": stranded})
        event = new_event(store, ctx, [], [
            {"key": "template", "before": previous, "after": template}])
        store.apply_changes(event, mismatch="internal")
        return finish(store, ctx, event, lambda: result)


def cmd_template_show(ctx: Ctx) -> Outcome:
    with ctx.open(write=False) as store:
        row = store.template_row()
        if row is None:
            return Outcome("read", {"template": None, "version": None,
                                    "applied_seq": None, "applied_at": None})
        return Outcome("read", {"template": row["template"],
                                "version": row["version"],
                                "applied_seq": row["applied_seq"],
                                "applied_at": row["applied_at"]})


def cmd_template_validate(ctx: Ctx) -> Outcome:
    template = ctx.input["template"]
    _template_or_refuse(template)
    return Outcome("read", {"valid": True, "format": template["format"],
                            "types": len(template["types"])})


# ── items ──────────────────────────────────────────────────────────────────


def cmd_item_create(ctx: Ctx) -> Outcome:
    data = ctx.input
    with ctx.open(write=True) as store:
        norm = require_template(store)
        type_name = data["type"]
        tdecl = norm["types"].get(type_name)
        if tdecl is None:
            raise KernelError("unknown_type", f"no type {type_name}",
                              {"type": type_name})
        check_expect(store, data.get("expect"))
        values = check_fields(store, tdecl, type_name, data.get("fields", {}),
                              {})
        prefix = tdecl["prefix"]
        number = (store.ceiling(prefix) or 0) + 1
        if number > INT_LIMIT:
            # The cap import holds ids and ceilings to (`_export_id`): a
            # store never holds an id its own export could not import.
            raise KernelError("id_exhausted",
                              f"{type_name} ids have reached {INT_LIMIT}, the "
                              f"highest an id may carry",
                              {"type": type_name, "prefix": prefix,
                               "ceiling": number - 1})
        new_id = f"{prefix}-{number:0{tdecl['digits']}d}"

        edges, others = [], []
        for n, rel in enumerate(data.get("relations", [])):
            if ("to" in rel) == ("from" in rel):
                raise KernelError("input_invalid", f"relations[{n}] names "
                                                   f"exactly one of to and "
                                                   f"from", {"index": n})
            kind = rel["kind"]
            require_relation_kind(norm, kind)
            other = rel.get("to", rel.get("from"))
            other_type = require_item(store, other, "relation")["type"]
            if "to" in rel:
                src, dst, src_type, dst_type = new_id, other, type_name, \
                    other_type
            else:
                src, dst, src_type, dst_type = other, new_id, other_type, \
                    type_name
            check_edge_types(norm, kind, src, dst, src_type, dst_type)
            if (kind, src, dst) in edges:
                raise KernelError("relation_invalid",
                                  f"relations[{n}] repeats an edge",
                                  {"index": n})
            edges.append((kind, src, dst))
            others.append(other)

        attachments = {}
        for n, att in enumerate(data.get("attachments", [])):
            check_attachment(att["ref"], att.get("hash"))
            if att["ref"] in attachments:
                raise KernelError("attachment_invalid",
                                  f"attachments[{n}] repeats a ref",
                                  {"ref": att["ref"]})
            attachments[att["ref"]] = att.get("hash")

        changes = [{"key": "type", "before": None, "after": type_name},
                   {"key": "state", "before": None, "after": tdecl["initial"]}]
        changes += [{"key": f"field:{f}", "before": None, "after": v}
                    for f, v in sorted(values.items()) if v is not None]
        changes += [{"key": f"rel:{k}:{s}:{d}", "before": False, "after": True}
                    for k, s, d in sorted(edges, key=lambda e: (
                        e[0], id_order(e[1]), id_order(e[2])))]
        changes += [{"key": f"attach:{r}", "before": None,
                     "after": {"hash": h}}
                    for r, h in sorted(attachments.items())]
        items = [new_id] + sorted(set(others), key=id_order)
        event = new_event(store, ctx, items, changes)
        store.apply_changes(event, mismatch="internal")
        run_guards(store, norm, ctx, event, tdecl["create_guards"], new_id,
                   tdecl["initial"])
        return finish(store, ctx, event,
                      lambda: {"item": render_item(store, norm, new_id)})


def cmd_item_get(ctx: Ctx) -> Outcome:
    with ctx.open(write=False) as store:
        norm = require_template(store)
        require_item(store, ctx.input["id"])
        return Outcome("read", {"item": render_item(store, norm,
                                                    ctx.input["id"])})


def _set_and_unset(store, ctx, norm, row):
    tdecl = norm["types"][row["type"]]
    given = ctx.input.get("set", {})
    check_unset(tdecl, row["type"], ctx.input.get("unset", []), given)
    stored = store.values(row["id"])
    new = check_fields(store, tdecl, row["type"], given, stored)
    for field in ctx.input.get("unset", []):
        new[field] = None
    return tdecl, field_changes(stored, new)


def cmd_item_update(ctx: Ctx) -> Outcome:
    with ctx.open(write=True) as store:
        norm = require_template(store)
        row = require_item(store, ctx.input["id"])
        check_expect(store, ctx.input.get("expect"))
        _tdecl, changes = _set_and_unset(store, ctx, norm, row)
        item_id = row["id"]
        if not changes:
            return unchanged(store, ctx,
                             {"item": render_item(store, norm, item_id)})
        event = new_event(store, ctx, [item_id], changes)
        store.apply_changes(event, mismatch="internal")
        return finish(store, ctx, event,
                      lambda: {"item": render_item(store, norm, item_id)})


def cmd_item_move(ctx: Ctx) -> Outcome:
    with ctx.open(write=True) as store:
        norm = require_template(store)
        row = require_item(store, ctx.input["id"])
        check_expect(store, ctx.input.get("expect"))
        tdecl = norm["types"][row["type"]]
        name = ctx.input["transition"]
        transition = tdecl["transitions"].get(name)
        if transition is None:
            raise KernelError("unknown_transition",
                              f"{row['type']} declares no transition {name}",
                              {"type": row["type"], "transition": name})
        if row["state"] not in transition["from"]:
            raise KernelError("transition_not_allowed",
                              f"{row['id']} is {row['state']}; {name} moves "
                              f"from {', '.join(transition['from'])}",
                              {"id": row["id"], "state": row["state"],
                               "from": transition["from"]})
        _tdecl, changes = _set_and_unset(store, ctx, norm, row)
        if row["state"] != transition["to"]:
            changes.insert(0, {"key": "state", "before": row["state"],
                               "after": transition["to"]})
        item_id = row["id"]
        result = lambda: {"item": render_item(store, norm, item_id),  # noqa
                          "transition": name, "from_state": row["state"],
                          "to_state": transition["to"]}
        if not changes:
            return unchanged(store, ctx, result())
        event = new_event(store, ctx, [item_id], changes, transition=name)
        store.apply_changes(event, mismatch="internal")
        run_guards(store, norm, ctx, event, transition["guards"], item_id,
                   transition["to"])
        return finish(store, ctx, event, result)


# ── relations and attachments ──────────────────────────────────────────────


def cmd_rel(ctx: Ctx) -> Outcome:
    adding = ctx.name == "rel add"
    kind, src, dst = (ctx.input["kind"], ctx.input["from"], ctx.input["to"])
    with ctx.open(write=True) as store:
        norm = require_template(store)
        require_relation_kind(norm, kind)
        src_type = require_item(store, src, "from")["type"]
        dst_type = require_item(store, dst, "to")["type"]
        check_expect(store, ctx.input.get("expect"))
        result = {"relation": {"kind": kind, "from": src, "to": dst}}
        present = store.has_edge(kind, src, dst)
        if present == adding:
            return unchanged(store, ctx, result)
        if adding:
            check_edge_types(norm, kind, src, dst, src_type, dst_type)
        event = new_event(store, ctx, [src, dst], [
            {"key": f"rel:{kind}:{src}:{dst}", "before": present,
             "after": adding}])
        store.apply_changes(event, mismatch="internal")
        return finish(store, ctx, event, lambda: result)


def cmd_attach(ctx: Ctx) -> Outcome:
    adding = ctx.name == "attach add"
    item_id, ref = ctx.input["id"], ctx.input["ref"]
    digest = ctx.input.get("hash") if adding else None
    check_attachment(ref, digest)
    with ctx.open(write=True) as store:
        require_template(store)
        require_item(store, item_id)
        check_expect(store, ctx.input.get("expect"))
        present, stored = store.attachment_hash(item_id, ref)
        before = {"hash": stored} if present else None
        after = {"hash": digest} if adding else None
        result = {"attachment": {"item": item_id, "ref": ref,
                                 "hash": digest if adding else stored}}
        if same(before, after):
            return unchanged(store, ctx, result)
        event = new_event(store, ctx, [item_id], [
            {"key": f"attach:{ref}", "before": before, "after": after}])
        store.apply_changes(event, mismatch="internal")
        return finish(store, ctx, event, lambda: result)


# ── reads ──────────────────────────────────────────────────────────────────


def _limit(data, key="limit") -> int:
    limit = data.get(key, DEFAULT_LIMIT)
    if limit < 0:
        raise KernelError("input_invalid", f"{key} is 0 (everything) or more",
                          {"key": key})
    return limit


def _plain_field(norm, type_name, field, what) -> dict:
    if type_name is None:
        raise KernelError("input_invalid", f"{what} names a field, so it needs "
                                           f"type", {"key": what})
    decl = norm["types"][type_name]["fields"].get(field)
    if decl is None:
        raise KernelError("unknown_field", f"{type_name} declares no field "
                                           f"{field}",
                          {"type": type_name, "field": field})
    if decl["kind"] in ("list", "metric"):
        raise KernelError("input_invalid", f"{what} cannot name the "
                                           f"{decl['kind']} field {field}",
                          {"key": what, "field": field})
    return decl


def cmd_query(ctx: Ctx) -> Outcome:
    data = ctx.input
    limit = _limit(data)
    after = data.get("after")
    if after is not None and split_id(after) is None:
        raise KernelError("input_invalid", f"after is an item id, not {after}",
                          {"key": "after"})
    with ctx.open(write=False) as store:
        norm = require_template(store)
        type_name = data.get("type")
        if type_name is not None and type_name not in norm["types"]:
            raise KernelError("unknown_type", f"no type {type_name}",
                              {"type": type_name})
        where = data.get("where", {})
        wdecl = {f: _plain_field(norm, type_name, f, "where") for f in where}
        count_by = data.get("count_by", [])
        for key in count_by:
            if key not in ("type", "state"):
                _plain_field(norm, type_name, key, "count_by")
        related = data.get("related")
        if related is not None:
            if ("to" in related) == ("from" in related):
                raise KernelError("input_invalid", "related names exactly one "
                                                   "of to and from",
                                  {"key": "related"})
            require_relation_kind(norm, related["kind"])
            require_item(store, related.get("to", related.get("from")),
                         "related")
        ids = data.get("ids")
        if ids is not None:
            for item_id in ids:
                require_item(store, item_id, "ids")
            candidates = sorted(set(ids), key=id_order)
        else:
            candidates = store.all_item_ids()
        states = data.get("state")
        matches = []
        for item_id in candidates:
            row = store.item_row(item_id)
            tdecl = norm["types"][row["type"]]
            if type_name is not None and row["type"] != type_name:
                continue
            if states is not None and row["state"] not in states:
                continue
            if "terminal" in data and (
                    (row["state"] in tdecl["terminal"]) != data["terminal"]):
                continue
            if where:
                stored = store.values(item_id)
                if not all(any(same(effective(wdecl[f]["kind"], stored.get(f)),
                                    v) for v in vals)
                           for f, vals in where.items()):
                    continue
            if related is not None:
                if "to" in related:
                    hit = store.has_edge(related["kind"], item_id,
                                         related["to"])
                else:
                    hit = store.has_edge(related["kind"], related["from"],
                                         item_id)
                if not hit:
                    continue
            if "startable" in data:
                startable = (row["state"] == tdecl["initial"]
                             and not blocked_by(store, norm, item_id))
                if startable != data["startable"]:
                    continue
            matches.append(item_id)
        counts = {}
        for item_id in matches:
            row = store.item_row(item_id)
            stored = store.values(item_id)
            key = {}
            for name in count_by:
                if name in ("type", "state"):
                    key[name] = row[name]
                else:
                    kind = norm["types"][type_name]["fields"][name]["kind"]
                    key[name] = effective(kind, stored.get(name))
            ck = canonical([key[n] for n in count_by])
            counts.setdefault(ck, [key, 0])[1] += 1
        rest = ([m for m in matches if id_order(m) > id_order(after)]
                if after is not None else matches)
        page = rest[:limit] if limit else rest
        truncated = len(page) < len(rest)
        return Outcome("read", {
            "items": [render_item(store, norm, m) for m in page],
            "total": len(matches), "returned": len(page),
            "truncated": truncated,
            "next_after": page[-1] if truncated and page else None,
            "counts": ([{"key": key, "n": n} for _ck, (key, n)
                        in sorted(counts.items())] if count_by else []),
        })


def cmd_events(ctx: Ctx) -> Outcome:
    data = ctx.input
    limit = _limit(data)
    after_seq = data.get("after_seq")
    if after_seq is not None and after_seq < 0:
        raise KernelError("input_invalid", "after_seq is 0 or more",
                          {"key": "after_seq"})
    with ctx.open(write=False) as store:
        events = store.events()
        last_export = store.meta_seq("last_export_seq")
    items = data.get("items")
    prefixes = data.get("keys")
    commands = data.get("commands")
    matches = []
    for event in events:
        if items is not None and not set(items) & set(event["items"]):
            continue
        if prefixes is not None and not any(
                c["key"].startswith(p) for c in event["changes"]
                for p in prefixes):
            continue
        if commands is not None and event["command"] not in commands:
            continue
        matches.append(event)
    rest = ([e for e in matches if e["seq"] > after_seq]
            if after_seq is not None else matches)
    page = rest[:limit] if limit else rest
    truncated = len(page) < len(rest)
    return Outcome("read", {
        "events": page, "total": len(matches), "returned": len(page),
        "truncated": truncated,
        "next_after_seq": page[-1]["seq"] if truncated and page else None,
        "last_export_seq": last_export,
        "unexported": sum(1 for e in events if e["seq"] > (last_export or 0)),
    })


# ── export and import (§ 5.8) ──────────────────────────────────────────────


def line(obj) -> bytes:
    return (canonical(obj) + "\n").encode("utf-8")


def serialise(store: Store) -> tuple[bytes, bytes]:
    row = store.template_row()
    norm = tpl.normalize(row["template"]) if row else {"types": {}}
    items = []
    for item_id in store.all_item_ids():
        r = store.item_row(item_id)
        stored = store.values(item_id)
        declared = norm["types"].get(r["type"], {"fields": {}})["fields"]
        fields = {f: stored.get(f) for f in declared}
        for f in stored:  # never drop a stored value
            fields.setdefault(f, stored[f])
        items.append(line({
            "id": r["id"], "type": r["type"], "state": r["state"],
            "fields": fields,
            "relations": [{"kind": k, "to": d}
                          for k, _s, d in store.edges(src=item_id)],
            "attachments": store.attachments(item_id),
            "created_at": r["created_at"], "updated_at": r["updated_at"],
            "seq": r["seq"]}))
    events = [line(e) for e in store.events()]
    return b"".join(items), b"".join(events)


def _file_info(data: bytes) -> dict:
    return {"lines": data.count(b"\n"), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def new_export_token() -> str:
    return secrets.token_hex(8)


def recorded_token(store: Store):
    """The store's recorded export token, or None when it has none. Text of
    any other shape than `new_export_token` writes is a row that cannot be
    read back, so it is `store_corrupt`, as `Store.meta_seq` treats a damaged
    seq (§ 5.1): read as it is, it became part of a temp file's name and
    surfaced as `io_error`, which blames the file system (F6)."""
    token = store.meta(EXPORT_TOKEN)
    if token is not None and not TOKEN_RE.fullmatch(token):
        raise KernelError("store_corrupt", f"{store.path}: meta {EXPORT_TOKEN} "
                                           f"cannot be read back",
                          {"store": str(store.path),
                           "row": f"meta {EXPORT_TOKEN}"})
    return token


def export_temp_names(token: str) -> dict:
    return {n: f".{n}.{token}.tmp" for n in EXPORT_FILES}


def _export_dir(ctx: Ctx, state_root: str) -> Path:
    return ctx.anchor() / state_root / EXPORT_DIR


def _io(what: str, exc: OSError, fallback) -> KernelError:
    return KernelError("io_error", f"cannot {what}: {exc.strerror}",
                       {"path": str(exc.filename or fallback)})


def cmd_export(ctx: Ctx) -> Outcome:
    with ctx.open(write=True) as store:
        directory = _export_dir(ctx, store.meta("state_root"))
        token = recorded_token(store)
        # A store made before the token existed has no provable temp name:
        # this export records one, and until then nothing is removed.
        provable = set(export_temp_names(token).values()) if token else set()
        if token is None:
            token = new_export_token()
            store.set_meta(EXPORT_TOKEN, token)
        temps = export_temp_names(token)
        leftovers = []
        try:
            if directory.exists() and not directory.is_dir():
                raise KernelError("export_dir_foreign",
                                  f"{directory} is not a directory",
                                  {"dir": str(directory)})
            if directory.is_dir():
                entries = set(os.listdir(directory))
                leftovers = sorted(entries & provable)
                foreign = sorted(entries - set(EXPORT_FILES) - set(leftovers))
                if foreign:
                    raise KernelError(
                        "export_dir_foreign",
                        f"{directory} holds {', '.join(foreign)}; the export "
                        f"writes only {' and '.join(EXPORT_FILES)}",
                        {"dir": str(directory), "entries": foreign})
            blobs = dict(zip(EXPORT_FILES, serialise(store)))
            same_bytes = all((directory / n).is_file()
                             and (directory / n).read_bytes() == b
                             for n, b in blobs.items())
        except OSError as exc:
            raise _io("read the export directory", exc, directory)
        seq = store.store_seq()
        result = {"dir": str(directory),
                  "files": {n: _file_info(b) for n, b in blobs.items()},
                  "last_export_seq": seq}
        if ctx.dry_run:
            store.rollback()
            return Outcome("dry_run", result)
        try:
            # A leftover carries this store's recorded token, so the kernel
            # wrote it, and it is stale: exports of this store are serialised
            # by its write lock, which this command holds.
            for name in leftovers:
                (directory / name).unlink(missing_ok=True)
        except OSError as exc:
            raise _io("remove a leftover export file", exc, directory)
        if not same_bytes:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                for n, b in blobs.items():
                    tmp = directory / temps[n]
                    try:
                        tmp.write_bytes(b)
                        os.replace(tmp, directory / n)
                    finally:
                        if tmp.exists():
                            tmp.unlink()
            except OSError as exc:
                raise _io("write the export", exc, directory)
        store.set_meta("last_export_seq", str(seq))
        store.commit()
        return Outcome("unchanged" if same_bytes else "written", result)


def _parse_lines(path: Path, name: str) -> tuple[bytes, list]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise KernelError("io_error", f"cannot read {path}: {exc.strerror}",
                          {"path": str(path)})
    if data and not data.endswith(b"\n"):
        raise KernelError("export_invalid", f"{name} does not end with a line "
                                            f"break", {"file": name})
    rows = []
    for n, raw in enumerate(data.split(b"\n")[:-1] if data else [], 1):
        try:
            obj = json.loads(raw.decode("utf-8"),
                             object_pairs_hook=_no_duplicates,
                             parse_constant=_no_constants)
        except RecursionError:
            raise KernelError("export_invalid", f"{name} line {n} is nested "
                                                f"too deeply",
                              {"file": name, "line": n})
        except (ValueError, UnicodeDecodeError) as exc:
            raise KernelError("export_invalid", f"{name} line {n} is not "
                                                f"JSON: {exc}",
                              {"file": name, "line": n})
        if not isinstance(obj, dict):
            raise KernelError("export_invalid", f"{name} line {n} is not an "
                                                f"object",
                              {"file": name, "line": n})
        problem = input_problem(obj)
        if problem:
            raise KernelError("export_invalid", f"{name} line {n}: "
                                                f"{problem[0]}: {problem[1]}",
                              {"file": name, "line": n, "key": problem[0]})
        rows.append(obj)
    return data, rows


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def _no_constants(name):
    raise ValueError(f"{name} is not JSON")


def _export_id(item_id) -> bool:
    """An id's shape, numbered no higher than a live mint can reach safely:
    the ceiling it seeds must still have room to grow inside sqlite's
    integers."""
    parts = split_id(item_id)
    return bool(parts) and parts[1] <= INT_LIMIT


def _event_shape(event: dict, n: int) -> None:
    def bad(message):
        raise KernelError("export_invalid", f"events.jsonl line {n}: {message}",
                          {"file": "events.jsonl", "line": n})

    if set(event) != set(EVENT_KEYS):
        bad(f"keys are {', '.join(sorted(event))}; an event has exactly "
            f"{', '.join(EVENT_KEYS)}")
    if not isinstance(event["seq"], int) or isinstance(event["seq"], bool):
        bad("seq is an integer")
    if not isinstance(event["at"], str) or not isinstance(event["command"],
                                                          str):
        bad("at and command are strings")
    actor = event["actor"]
    if actor is not None:
        try:
            if not isinstance(actor, dict) or normalize_actor(actor) != actor:
                bad("actor is null or {kind, name, session}")
        except ValueProblem as exc:
            bad(f"actor: {exc.message}")
    if not isinstance(event["items"], list) or not all(
            _export_id(i) for i in event["items"]):
        bad(f"items is an array of item ids numbered up to {INT_LIMIT}")
    if len(set(event["items"])) != len(event["items"]):
        bad("items names an item twice")
    for key in ("transition", "note"):
        if not (event[key] is None or isinstance(event[key], str)):
            bad(f"{key} is a string or null")
    if not isinstance(event["warnings"], list):
        bad("warnings is an array")
    if not isinstance(event["changes"], list):
        bad("changes is an array")
    for change in event["changes"]:
        if not isinstance(change, dict) or set(change) != {"key", "before",
                                                           "after"}:
            bad("a change has exactly key, before and after")
        key = change["key"]
        if not isinstance(key, str):
            bad("a change key is a string")
        if key in ("type", "state") or key.startswith(("field:", "attach:")):
            if not event["items"]:
                bad(f"{key} needs the item in items[0]")
        if key == "template":
            if not isinstance(change["after"], dict) or tpl.validate(
                    change["after"]):
                bad("a template change carries a valid template")
        elif key.startswith("ceiling:"):
            after = change["after"]
            if isinstance(after, bool) or not isinstance(after, int) or \
                    not 0 <= after <= INT_LIMIT:
                bad(f"a ceiling is an integer from 0 to {INT_LIMIT}")
        elif key.startswith("rel:"):
            parts = key.split(":", 3)
            if (len(parts) != 4 or not isinstance(change["after"], bool)
                    or not all(_export_id(i) for i in parts[2:])):
                bad(f"{key} is rel:<kind>:<from>:<to> with a boolean value")
        elif key.startswith("attach:"):
            after = change["after"]
            if not (after is None or (
                    isinstance(after, dict) and set(after) == {"hash"}
                    and (after["hash"] is None
                         or (isinstance(after["hash"], str)
                             and HASH_RE.match(after["hash"]))))):
                bad(f"{key} is null or {{hash}}, a sha256 hash or null")
        elif key in ("type", "state", "state_root"):
            # The store binds these as text; anything else is a malformed
            # line, not a corrupt store.
            if not isinstance(change["after"], str) or not (
                    change["before"] is None
                    or isinstance(change["before"], str)):
                bad(f"{key} is a string, and its before a string or null")


def replay_check(store: Store):
    """The check `import` runs on each replayed change, against the template
    in force when the change's event was written: the last one the replay has
    applied before it (TASK-489, carried from TASK-487).

    The replay runs no guards, because the history was written under earlier
    templates (§ 5.8, step 2), but a value no template allowed was never
    written by a command. So each change is held to what a live write of it
    would have been held to, and a change that breaks it is `export_invalid`:
    - `template`: its version rises above the one in force, and it strands
      no stored data (`incompatibilities`), as `template apply` requires;
    - `type`: set once, on an item that does not exist yet; the template
      declares the type, and the id is one that type mints, its prefix
      padded to its digits (an id of the wrong prefix, or `W-1` beside a
      three-digit `W-001`, is not);
    - `state`: a state of the item's type;
    - `field:<name>`: a field of the item's type, and a value that fits its
      kind (§ 5.3) in the form the kernel stores it;
    - `rel:<kind>` being added: a kind the template knows, and ends whose
      types a declared kind allows (`check_edge_types`);
    - `attach:<ref>`: a ref `check_attachment` takes, as `attach add` and
      `attach remove` require: not empty or only white space, and no line
      break (TASK-489 round 3).
    Ends and items that do not exist are the store's to refuse
    (`Store.apply_changes`), so this check steps aside for them."""
    cache = {"version": None, "norm": None}

    def in_force():
        version = store.q("SELECT MAX(version) FROM template")[0][0]
        if version != cache["version"]:
            row = store.template_row()
            cache["version"] = version
            cache["norm"] = tpl.normalize(row["template"]) if row else None
        return cache["norm"]

    def check(event, primary, key, after):
        seq = event["seq"]

        def bad(message, **extra):
            raise KernelError("export_invalid",
                              f"event {seq}: {key}: {message}",
                              {"seq": seq, "key": key, **extra})

        if key.startswith("attach:"):
            # The ref check a live `attach add` or `attach remove` runs, so
            # an export cannot hand `import` a ref no command writes. The
            # hash is held to `HASH_RE` already, by `_event_shape`.
            try:
                check_attachment(key[len("attach:"):], None)
            except KernelError as exc:
                bad(exc.message)
            return
        if key.startswith("rel:"):
            if not after:
                return
            _, kind, src, dst = key.split(":", 3)
            norm = in_force()
            if norm is None:
                bad("no template is in force")
            if kind not in tpl.relation_kinds(norm):
                bad(f"the template in force declares no relation kind {kind}")
            src_type, dst_type = store.item_type(src), store.item_type(dst)
            if src_type is None or dst_type is None:
                return
            try:
                check_edge_types(norm, kind, src, dst, src_type, dst_type)
            except KernelError as exc:
                bad(exc.message)
            return
        if key == "template":
            norm = in_force()
            if norm is None:
                return
            applied = cache["version"]
            if after["version"] <= applied:
                bad(f"version {after['version']} is not above {applied}, the "
                    f"version in force")
            stranded = incompatibilities(store, norm, tpl.normalize(after))
            if stranded:
                bad(f"version {after['version']} would strand stored data: "
                    f"{stranded[0]['message']}", problems=stranded)
            return
        if key == "type":
            if store.item_type(primary) is not None:
                bad(f"{primary} exists already; an item's type is set once, "
                    f"at its create")
            norm = in_force()
            if norm is None:
                bad("no template is in force")
            tdecl = norm["types"].get(after)
            if tdecl is None:
                bad(f"the template in force declares no type {after}")
            _prefix, number = split_id(primary)
            minted = f"{tdecl['prefix']}-{number:0{tdecl['digits']}d}"
            if primary != minted:
                bad(f"{primary} is not an id type {after} mints; its "
                    f"number would be {minted}", id=primary)
            return
        if key != "state" and not key.startswith("field:"):
            return
        item_type = store.item_type(primary) if primary else None
        if item_type is None:
            return
        tdecl = (in_force() or {"types": {}})["types"].get(item_type)
        if tdecl is None:
            bad(f"the template in force declares no type {item_type}")
        if key == "state":
            if after not in tdecl["states"]:
                bad(f"{item_type} has no state {canonical(after)} in the "
                    f"template in force")
            return
        field = key[len("field:"):]
        decl = tdecl["fields"].get(field)
        if decl is None:
            bad(f"{item_type} declares no field {field} in the template in "
                f"force")
        if after is None:
            return
        try:
            value = (check_metric(after) if decl["kind"] == "metric"
                     else check_scalar(decl, after, lookup=store.item_type))
        except ValueProblem as exc:
            bad(exc.message)
        if not same(value, after):
            bad(f"the value is not in the form a live write stores "
                f"({decl['kind']})")

    return check


def refuse_if_not_empty(store: Store) -> None:
    count = store.event_count()
    if count:
        raise KernelError("store_not_empty",
                          f"{store.path} holds {count} event(s); import "
                          f"needs an empty store", {"store": str(store.path)})


def cmd_import(ctx: Ctx) -> Outcome:
    state_root = normalize_state_root(ctx.input["state_root"])
    anchor = ctx.anchor()
    path, _derived = ctx.store_path()
    probe = Store.probe(path)
    if probe == "store":
        # A fast refusal, so that a full store is named before a missing
        # export. The decision that counts is taken again under the lock.
        with ctx.open(write=False) as existing:
            refuse_if_not_empty(existing)
    directory = anchor / state_root / EXPORT_DIR
    try:
        missing = [n for n in EXPORT_FILES if not (directory / n).is_file()]
    except OSError as exc:
        raise _io("read the export directory", exc, directory)
    if missing:
        raise KernelError("export_missing",
                          f"{directory} has no {', '.join(missing)}",
                          {"dir": str(directory), "missing": missing})
    items_bytes, item_rows = _parse_lines(directory / "items.jsonl",
                                          "items.jsonl")
    _events_bytes, events = _parse_lines(directory / "events.jsonl",
                                         "events.jsonl")
    for n, event in enumerate(events, 1):
        _event_shape(event, n)
        if event["seq"] != n:
            raise KernelError("export_invalid",
                              f"events.jsonl line {n} is seq {event['seq']}; "
                              f"the seqs run 1…n without a gap",
                              {"line": n, "seq": event["seq"]})
    for n, item in enumerate(item_rows, 1):
        if set(item) != set(ITEM_KEYS):
            raise KernelError("export_invalid",
                              f"items.jsonl line {n}: an item has exactly "
                              f"{', '.join(ITEM_KEYS)}",
                              {"file": "items.jsonl", "line": n})
    first = events[0] if events else None
    if (first is None or first["command"] != "init"
            or not any(c["key"] == "state_root" and c["after"] == state_root
                       for c in first["changes"])):
        raise KernelError("export_invalid",
                          f"event 1 is not the init for state root "
                          f"{state_root}", {"state_root": state_root})

    memory = ctx.dry_run and probe != "store"
    store = (Store.open(path, write=True) if probe == "store"
             else Store.create(path, memory=memory))
    with store:
        # Decided inside the write transaction: another process may have run
        # init or import since the probe above (F6).
        if store.contents() == "store":
            refuse_if_not_empty(store)
        else:
            store.initialise()
        ctx.store_seq = 0
        check = replay_check(store)
        for event in events:
            store.apply_event(event, mismatch="export_invalid", check=check)
        produced, _ = serialise(store)
        if produced != items_bytes:
            want = items_bytes.split(b"\n")
            got = produced.split(b"\n")
            first_id = None
            for a, b in zip(want + [b""] * len(got), got + [b""] * len(want)):
                if a != b:
                    source = a or b
                    try:
                        first_id = json.loads(source.decode("utf-8"))["id"]
                    except (ValueError, KeyError, TypeError):
                        first_id = None
                    break
            raise KernelError("replay_mismatch",
                              f"replaying the events does not reproduce "
                              f"items.jsonl; the first differing item is "
                              f"{first_id}", {"id": first_id})
        last = len(events)
        store.set_meta("last_export_seq", str(last))
        store.set_meta(EXPORT_TOKEN, new_export_token())
        result = {"dir": str(directory), "items": len(item_rows),
                  "events": last, "last_seq": last, "verified": True}
        if ctx.dry_run:
            store.rollback()
            return Outcome("dry_run", result)
        store.commit()
        ctx.store_seq = last
        return Outcome("written", result)


# ── describe ───────────────────────────────────────────────────────────────


def cmd_describe(ctx: Ctx) -> Outcome:
    from .surface import describe
    return Outcome("read", describe())


HANDLERS = {
    "init": cmd_init,
    "template apply": cmd_template_apply,
    "template show": cmd_template_show,
    "template validate": cmd_template_validate,
    "item create": cmd_item_create,
    "item get": cmd_item_get,
    "item update": cmd_item_update,
    "item move": cmd_item_move,
    "rel add": cmd_rel,
    "rel remove": cmd_rel,
    "attach add": cmd_attach,
    "attach remove": cmd_attach,
    "query": cmd_query,
    "events": cmd_events,
    "export": cmd_export,
    "import": cmd_import,
    "describe": cmd_describe,
}
