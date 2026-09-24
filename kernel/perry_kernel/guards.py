"""The four guards and `when` (§ 5.4). There are four kinds and no others.

A guard is evaluated against the store as the command would leave it: the
command's changes are applied inside the open transaction first, so a guard
sees the fields and relations the same command sets. A refusal rolls all of it
back.
"""

from __future__ import annotations

from .store import id_order
from .values import effective, is_set, same


def item_view(store, norm: dict, item_id: str) -> dict:
    """The item's type, state and effective field values."""
    row = store.item_row(item_id)
    tdecl = norm["types"][row["type"]]
    stored = store.values(item_id)
    fields = {f: stored.get(f) for f in tdecl["fields"]}
    return {"id": item_id, "type": row["type"], "state": row["state"],
            "fields": fields, "decl": tdecl}


def _effective(view: dict, field: str):
    return effective(view["decl"]["fields"][field]["kind"],
                     view["fields"].get(field))


def applies(guard: dict, view: dict) -> bool:
    when = guard.get("when")
    if not when:
        return True
    (field, values), = when.items()
    value = _effective(view, field)
    return any(same(value, v) for v in values)


def _required(guard, view):
    missing, below = [], {}
    for field in guard["fields"]:
        kind = view["decl"]["fields"][field]["kind"]
        if not is_set(kind, view["fields"].get(field)):
            missing.append(field)
    for field, minimum in guard["at_least"].items():
        values = view["decl"]["fields"][field]["values"]
        value = _effective(view, field)
        rank = next((n for n, v in enumerate(values) if same(v, value)), None)
        floor = next(n for n, v in enumerate(values) if same(v, minimum))
        if value is None or rank is None or rank < floor:
            below[field] = {"value": value, "at_least": minimum}
    if missing or below:
        return {"missing": missing, "below": below}
    return None


def _actor(guard, actor):
    needs = {}
    ok = True
    if "actor_kind" in guard:
        needs["actor_kind"] = guard["actor_kind"]
        ok = ok and actor.get("kind") == guard["actor_kind"]
    if "name" in guard:
        needs["name"] = guard["name"]
        ok = ok and actor.get("name") == guard["name"]
    return None if ok else {"actor": actor, "needs": needs}


def _relations_closed(guard, view, store, norm):
    kind, direction = guard["relation"], guard["direction"]
    if direction == "incoming":
        others = [src for _k, src, _d in store.edges(kind=kind,
                                                     dst=view["id"])]
    else:
        others = [dst for _k, _s, dst in store.edges(kind=kind,
                                                     src=view["id"])]
    open_ends = []
    for other in others:
        row = store.item_row(other)
        terminal = norm["types"][row["type"]]["terminal"]
        if row["state"] not in terminal:
            open_ends.append(other)
    if open_ends:
        return {"not_terminal": sorted(set(open_ends), key=id_order)}
    return None


def _limit(guard, view, store, norm, target_state):
    """Guards run after the command's changes are applied, so this item
    already sits in `target_state` and `items_in` returns it: it counts
    itself once, in the loop."""
    per = guard["per"]
    mine = {f: _effective(view, f) for f in per}
    count = 0
    for other in store.items_in(view["type"], target_state):
        if other == view["id"]:
            count += 1
            continue
        other_view = item_view(store, norm, other)
        if all(same(_effective(other_view, f), mine[f]) for f in per):
            count += 1
    if count > guard["max"]:
        return {"count": count, "max": guard["max"], "values": mine}
    return None


def evaluate(guards: list, *, store, norm: dict, item_id: str,
             target_state: str, actor: dict):
    """Every guard that applies, evaluated. Returns `(refusals, warnings)`,
    each a list of `{index, kind, when, detail}`."""
    view = item_view(store, norm, item_id)
    refusals, warnings = [], []
    for index, guard in enumerate(guards):
        if not applies(guard, view):
            continue
        kind = guard["kind"]
        if kind == "required":
            detail = _required(guard, view)
        elif kind == "actor":
            detail = _actor(guard, actor)
        elif kind == "relations_closed":
            detail = _relations_closed(guard, view, store, norm)
        elif kind == "limit":
            detail = _limit(guard, view, store, norm, target_state)
        else:  # pragma: no cover — the template validator admits four kinds
            raise ValueError(kind)
        if detail is None:
            continue
        failure = {"index": index, "kind": kind, "when": guard.get("when"),
                   "detail": detail}
        if kind == "limit" and guard["mode"] == "warn":
            warnings.append(failure)
        else:
            refusals.append(failure)
    return refusals, warnings
