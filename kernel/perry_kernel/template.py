"""The process template, format 1 (§ 5.2): validation and the normalised view.

`KEYS` is the key schema. The validator reads it and `describe` reports it, so
the two cannot say different things.
"""

from __future__ import annotations

import re

from .values import (FIELD_KINDS, ValueProblem, canonical, check_scalar,
                     json_type, same)

FORMAT = 1
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{0,9}$")
RESERVED_FIELDS = ("id", "type", "state")
BUILTIN_RELATIONS = {
    "blocks": "from blocks to",
    "parent": "to is the parent of from",
}
GUARD_KINDS = ("required", "actor", "relations_closed", "limit")
DIRECTIONS = ("incoming", "outgoing")
LIMIT_MODES = ("refuse", "warn")
MAX_DIGITS = 18

#: The legal keys at every level. `required` keys must be present; `optional`
#: keys may be left out (§ 5.2 "Keys").
KEYS = {
    "template": {"required": ["format", "name", "version", "types",
                              "relations"], "optional": []},
    "type": {"required": ["prefix", "states", "initial", "terminal", "fields",
                          "transitions"],
             "optional": ["digits", "create_guards"],
             "defaults": {"digits": 1, "create_guards": []}},
    "field": {"required": ["kind"], "optional": [],
              "by_kind": {"enum": {"required": ["values"],
                                   "optional": ["ordered"],
                                   "defaults": {"ordered": False}},
                          "ref": {"required": ["to"], "optional": []},
                          "list": {"required": ["of"], "optional": []}}},
    "transition": {"required": ["from", "to", "guards"], "optional": []},
    "guard": {"required": ["kind"], "optional": ["when"],
              "by_kind": {"required": {"required": [],
                                       "optional": ["fields", "at_least"]},
                          "actor": {"required": [],
                                    "optional": ["actor_kind", "name"]},
                          "relations_closed": {"required": ["relation",
                                                            "direction"],
                                               "optional": []},
                          "limit": {"required": ["max", "mode"],
                                    "optional": ["per"],
                                    "defaults": {"per": []}}}},
    "relation": {"required": ["from", "to"], "optional": []},
}


class Problems:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, path: str, message: str):
        self.items.append({"path": path, "message": message})

    def __bool__(self):
        return bool(self.items)


def _keys(obj, level: dict, path: str, problems: Problems, kind=None) -> bool:
    """Only the declared keys, and every required one. False if `obj` is not
    an object at all."""
    if not isinstance(obj, dict):
        problems.add(path, f"expected an object, got {json_type(obj)}")
        return False
    required = list(level["required"])
    optional = list(level["optional"])
    if kind is not None and kind in level.get("by_kind", {}):
        required += level["by_kind"][kind]["required"]
        optional += level["by_kind"][kind]["optional"]
    legal = set(required) | set(optional)
    for key in obj:
        if key not in legal:
            problems.add(f"{path}.{key}", f"unknown key; legal: "
                                          f"{', '.join(sorted(legal))}")
    for key in required:
        if key not in obj:
            problems.add(f"{path}.{key}", "required key is missing")
    return True


def _name(value, path: str, problems: Problems) -> bool:
    if not isinstance(value, str) or not NAME_RE.match(value):
        problems.add(path, f"{canonical(value)} does not match "
                           f"{NAME_RE.pattern}")
        return False
    return True


def _name_list(value, path: str, problems: Problems, *, allowed=None,
               empty_ok=False) -> list:
    if not isinstance(value, list) or (not value and not empty_ok):
        problems.add(path, "expected a non-empty array of names"
                     if not empty_ok else "expected an array of names")
        return []
    out = []
    for n, v in enumerate(value):
        if not isinstance(v, str):
            problems.add(f"{path}[{n}]", "expected a name")
            continue
        if allowed is not None and v not in allowed:
            problems.add(f"{path}[{n}]", f"{v} is not one of "
                                         f"{', '.join(sorted(allowed))}")
            continue
        if v in out:
            problems.add(f"{path}[{n}]", f"{v} is listed twice")
            continue
        out.append(v)
    return out


def _field_decl(decl, path: str, problems: Problems, types: set,
                element: bool = False) -> None:
    kind = decl.get("kind") if isinstance(decl, dict) else None
    if not _keys(decl, KEYS["field"], path, problems, kind):
        return
    if kind not in FIELD_KINDS:
        problems.add(f"{path}.kind", f"{canonical(kind)} is not one of "
                                     f"{', '.join(FIELD_KINDS)}")
        return
    if element and kind in ("list", "metric"):
        problems.add(f"{path}.kind", "a list element cannot be a list or a "
                                     "metric")
        return
    if kind == "enum":
        values = decl.get("values")
        if not isinstance(values, list) or not values:
            problems.add(f"{path}.values", "expected a non-empty array")
        else:
            for n, v in enumerate(values):
                if not isinstance(v, (str, bool)):
                    problems.add(f"{path}.values[{n}]",
                                 "an enum value is a string or a boolean")
                elif any(same(v, w) for w in values[:n]):
                    problems.add(f"{path}.values[{n}]", "listed twice")
        if "ordered" in decl and not isinstance(decl["ordered"], bool):
            problems.add(f"{path}.ordered", "expected a boolean")
    elif kind == "ref":
        if "to" in decl:
            _name_list(decl["to"], f"{path}.to", problems, allowed=types)
    elif kind == "list":
        if "of" in decl:
            _field_decl(decl["of"], f"{path}.of", problems, types, element=True)


def _when(when, path: str, problems: Problems, fields: dict) -> None:
    if not isinstance(when, dict) or len(when) != 1:
        problems.add(path, "when names exactly one field")
        return
    (name, values), = when.items()
    decl = fields.get(name)
    if decl is None or not isinstance(decl, dict):
        problems.add(f"{path}.{name}", "not a field of this type")
        return
    if decl.get("kind") in ("list", "metric"):
        problems.add(f"{path}.{name}", "when cannot name a list or a metric "
                                       "field")
        return
    if not isinstance(values, list) or not values:
        problems.add(f"{path}.{name}", "expected a non-empty array of values")
        return
    for n, v in enumerate(values):
        if v is None:
            continue
        if decl.get("kind") == "ref":
            # An id cannot be resolved against a store here; only its shape.
            if not isinstance(v, str) or not v:
                problems.add(f"{path}.{name}[{n}]", "a ref value is an id")
            continue
        try:
            check_scalar(decl, v)
        except ValueProblem as exc:
            problems.add(f"{path}.{name}[{n}]", exc.message)
        except (KeyError, TypeError):
            # The field's own declaration is malformed; that is reported at
            # the field's path.
            pass


def _guard(guard, path: str, problems: Problems, fields: dict,
           relation_kinds: set) -> None:
    kind = guard.get("kind") if isinstance(guard, dict) else None
    if not _keys(guard, KEYS["guard"], path, problems, kind):
        return
    if kind not in GUARD_KINDS:
        problems.add(f"{path}.kind", f"{canonical(kind)} is not one of "
                                     f"{', '.join(GUARD_KINDS)}")
        return
    if "when" in guard:
        _when(guard["when"], f"{path}.when", problems, fields)
    if kind == "required":
        names = guard.get("fields", [])
        at_least = guard.get("at_least", {})
        if not isinstance(names, list):
            problems.add(f"{path}.fields", "expected an array of field names")
            names = []
        if not isinstance(at_least, dict):
            problems.add(f"{path}.at_least", "expected an object")
            at_least = {}
        if not names and not at_least:
            problems.add(path, "required needs a non-empty fields or at_least")
        _name_list(names, f"{path}.fields", problems, allowed=set(fields),
                   empty_ok=True)
        for name, minimum in at_least.items():
            decl = fields.get(name)
            if not isinstance(decl, dict):
                problems.add(f"{path}.at_least.{name}", "not a field of this "
                                                        "type")
            elif decl.get("kind") != "enum" or decl.get("ordered") is not True:
                problems.add(f"{path}.at_least.{name}", "at_least names an "
                                                        "ordered enum")
            elif not any(same(minimum, v) for v in decl.get("values", [])):
                problems.add(f"{path}.at_least.{name}",
                             f"{canonical(minimum)} is not one of its values")
    elif kind == "actor":
        if "actor_kind" not in guard and "name" not in guard:
            problems.add(path, "actor needs actor_kind, name, or both")
        if "actor_kind" in guard and guard["actor_kind"] not in ("human",
                                                                 "agent"):
            problems.add(f"{path}.actor_kind", "human or agent")
        if "name" in guard and (not isinstance(guard["name"], str)
                                or not guard["name"].strip()):
            problems.add(f"{path}.name", "a non-empty string")
    elif kind == "relations_closed":
        if "relation" in guard and guard["relation"] not in relation_kinds:
            problems.add(f"{path}.relation",
                         f"{canonical(guard['relation'])} is not a relation "
                         f"kind")
        if "direction" in guard and guard["direction"] not in DIRECTIONS:
            problems.add(f"{path}.direction", "incoming or outgoing")
    elif kind == "limit":
        mx = guard.get("max")
        if "max" in guard and (isinstance(mx, bool) or not isinstance(mx, int)
                               or mx < 1):
            problems.add(f"{path}.max", "an integer of at least 1")
        if "mode" in guard and guard["mode"] not in LIMIT_MODES:
            problems.add(f"{path}.mode", "refuse or warn")
        per = guard.get("per", [])
        names = _name_list(per, f"{path}.per", problems, allowed=set(fields),
                           empty_ok=True)
        for n, name in enumerate(names):
            if fields[name].get("kind") in ("list", "metric"):
                problems.add(f"{path}.per[{n}]", "per cannot name a list or a "
                                                 "metric field")


def validate(template) -> list[dict]:
    """Every problem with a template, as `{path, message}`. Empty when valid."""
    problems = Problems()
    if not _keys(template, KEYS["template"], "template", problems):
        return problems.items
    fmt = template.get("format")
    if "format" in template and (isinstance(fmt, bool) or fmt != FORMAT):
        problems.add("template.format", f"this kernel reads format {FORMAT}")
    if "name" in template and (not isinstance(template["name"], str)
                               or not template["name"].strip()):
        problems.add("template.name", "a non-empty string")
    ver = template.get("version")
    if "version" in template and (isinstance(ver, bool)
                                  or not isinstance(ver, int) or ver < 1):
        problems.add("template.version", "a positive integer")
    types = template.get("types")
    relations = template.get("relations")
    if "types" in template and (not isinstance(types, dict) or not types):
        problems.add("template.types", "a non-empty object of types")
        types = {}
    if "relations" in template and not isinstance(relations, dict):
        problems.add("template.relations", "an object of relation kinds")
        relations = {}
    types = types if isinstance(types, dict) else {}
    relations = relations if isinstance(relations, dict) else {}
    type_names = {t for t in types if isinstance(t, str) and NAME_RE.match(t)}
    for t in types:
        _name(t, f"template.types.{t}", problems)
    for r in relations:
        path = f"template.relations.{r}"
        if _name(r, path, problems) and r in BUILTIN_RELATIONS:
            problems.add(path, f"{r} is built in and cannot be declared")
        decl = relations[r]
        if _keys(decl, KEYS["relation"], path, problems):
            for end in ("from", "to"):
                if end in decl:
                    _name_list(decl[end], f"{path}.{end}", problems,
                               allowed=type_names)
    relation_kinds = set(BUILTIN_RELATIONS) | {
        r for r in relations if isinstance(r, str)}
    prefixes: dict[str, str] = {}
    for t, decl in types.items():
        path = f"template.types.{t}"
        if not _keys(decl, KEYS["type"], path, problems):
            continue
        prefix = decl.get("prefix")
        if "prefix" in decl:
            if not isinstance(prefix, str) or not PREFIX_RE.match(prefix):
                problems.add(f"{path}.prefix", f"{canonical(prefix)} does not "
                                               f"match {PREFIX_RE.pattern}")
            elif prefix in prefixes:
                problems.add(f"{path}.prefix", f"{prefix} is also "
                                               f"{prefixes[prefix]}'s prefix")
            else:
                prefixes[prefix] = t
        digits = decl.get("digits", 1)
        if isinstance(digits, bool) or not isinstance(digits, int) or not (
                1 <= digits <= MAX_DIGITS):
            problems.add(f"{path}.digits", f"an integer from 1 to {MAX_DIGITS}")
        states = []
        if "states" in decl:
            states = _name_list(decl["states"], f"{path}.states", problems)
            for n, s in enumerate(states):
                _name(s, f"{path}.states[{n}]", problems)
        state_set = set(states)
        if "initial" in decl and decl["initial"] not in state_set:
            problems.add(f"{path}.initial", "not one of the type's states")
        if "terminal" in decl:
            _name_list(decl["terminal"], f"{path}.terminal", problems,
                       allowed=state_set)
        fields = decl.get("fields")
        if "fields" in decl and not isinstance(fields, dict):
            problems.add(f"{path}.fields", "an object of field declarations")
        fields = fields if isinstance(fields, dict) else {}
        for f, fdecl in fields.items():
            fpath = f"{path}.fields.{f}"
            if _name(f, fpath, problems) and f in RESERVED_FIELDS:
                problems.add(fpath, f"{f} cannot be a field name")
            _field_decl(fdecl, fpath, problems, type_names)
        good_fields = {f: d for f, d in fields.items() if isinstance(d, dict)}
        guards = decl.get("create_guards", [])
        if not isinstance(guards, list):
            problems.add(f"{path}.create_guards", "an array of guards")
            guards = []
        for n, g in enumerate(guards):
            _guard(g, f"{path}.create_guards[{n}]", problems, good_fields,
                   relation_kinds)
        transitions = decl.get("transitions")
        if "transitions" in decl and not isinstance(transitions, dict):
            problems.add(f"{path}.transitions", "an object of transitions")
        transitions = transitions if isinstance(transitions, dict) else {}
        for name, tdecl in transitions.items():
            tpath = f"{path}.transitions.{name}"
            _name(name, tpath, problems)
            if not _keys(tdecl, KEYS["transition"], tpath, problems):
                continue
            if "from" in tdecl:
                _name_list(tdecl["from"], f"{tpath}.from", problems,
                           allowed=state_set)
            if "to" in tdecl and tdecl["to"] not in state_set:
                problems.add(f"{tpath}.to", "not one of the type's states")
            tguards = tdecl.get("guards")
            if "guards" in tdecl and not isinstance(tguards, list):
                problems.add(f"{tpath}.guards", "an array of guards")
                tguards = []
            for n, g in enumerate(tguards or []):
                _guard(g, f"{tpath}.guards[{n}]", problems, good_fields,
                       relation_kinds)
    return problems.items


def normalize(template: dict) -> dict:
    """A valid template with every default filled in. Never stored: the store
    keeps what the caller applied, verbatim."""
    out = {"format": template["format"], "name": template["name"],
           "version": template["version"], "types": {},
           "relations": {k: {"from": list(v["from"]), "to": list(v["to"])}
                         for k, v in template["relations"].items()}}
    for t, decl in template["types"].items():
        fields = {}
        for f, fdecl in decl["fields"].items():
            fields[f] = _normalize_field(fdecl)
        out["types"][t] = {
            "prefix": decl["prefix"],
            "digits": decl.get("digits", 1),
            "states": list(decl["states"]),
            "initial": decl["initial"],
            "terminal": list(decl["terminal"]),
            "fields": fields,
            "create_guards": [_normalize_guard(g)
                              for g in decl.get("create_guards", [])],
            "transitions": {
                n: {"from": list(td["from"]), "to": td["to"],
                    "guards": [_normalize_guard(g) for g in td["guards"]]}
                for n, td in decl["transitions"].items()},
        }
    return out


def _normalize_field(decl: dict) -> dict:
    out = dict(decl)
    if decl["kind"] == "enum":
        out.setdefault("ordered", False)
    if decl["kind"] == "list":
        out["of"] = _normalize_field(decl["of"])
    return out


def _normalize_guard(guard: dict) -> dict:
    out = dict(guard)
    out.setdefault("when", None)
    if guard["kind"] == "limit":
        out.setdefault("per", [])
    if guard["kind"] == "required":
        out.setdefault("fields", [])
        out.setdefault("at_least", {})
    return out


def relation_kinds(norm: dict) -> set:
    return set(BUILTIN_RELATIONS) | set(norm["relations"])


def schema() -> dict:
    """The key schema as `describe` reports it."""
    return {level: {k: v for k, v in spec.items()} for level, spec in
            KEYS.items()}
