"""JSON helpers, field-kind validation and the metric formula (§ 5.3, § 5.5).

Nothing here touches the store. A `ref` value is resolved through a lookup
function the caller passes in, so this module stays pure.
"""

from __future__ import annotations

import datetime
import json
import math
import re

FIELD_KINDS = ("text", "int", "number", "date", "enum", "actor", "ref", "list",
               "metric")
ACTOR_KINDS = ("human", "agent")
METRIC_KEYS = ("current", "target", "baseline", "direction")
DIRECTIONS = ("up", "down")
INT_LIMIT = 2 ** 53
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


# ── JSON ────────────────────────────────────────────────────────────────────


def canonical(value) -> str:
    """The one serialisation: sorted keys, compact, UTF-8 (§ 5.8)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def json_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def same(a, b) -> bool:
    """JSON equality: a boolean never equals a number, 1 equals 1.0."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def is_number(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


# ── set / unset (§ 5.3, the last column) ────────────────────────────────────


def is_set(kind: str, value) -> bool:
    if value is None:
        return False
    if kind == "text":
        return isinstance(value, str) and value.strip() != ""
    if kind == "list":
        return isinstance(value, list) and len(value) > 0
    if kind == "metric":
        return isinstance(value, dict) and value.get("current") is not None
    return True


def effective(kind: str, value):
    """The value a `when`, a `per` or a `where` compares: `None` when unset."""
    return value if is_set(kind, value) else None


# ── validation ──────────────────────────────────────────────────────────────


class ValueProblem(Exception):
    """A value that does not fit. `code` is field_invalid, metric_invalid or
    item_not_found; the caller turns it into a KernelError with its path."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def valid_date(text) -> bool:
    if not isinstance(text, str) or not DATE_RE.match(text):
        return False
    try:
        datetime.date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return False
    return True


def normalize_actor(value, *, problem=ValueProblem, code="field_invalid"):
    """`{"kind", "name", "session"}`, session required for an agent."""
    if not isinstance(value, dict):
        raise problem(code, "an actor is an object")
    extra = sorted(set(value) - {"kind", "name", "session"})
    if extra:
        raise problem(code, f"an actor takes kind, name and session, not "
                            f"{', '.join(extra)}")
    kind = value.get("kind")
    if kind not in ACTOR_KINDS:
        raise problem(code, "an actor's kind is human or agent")
    name = value.get("name")
    if not isinstance(name, str) or not name.strip():
        raise problem(code, "an actor's name is a non-empty string")
    session = value.get("session")
    if session is not None and (not isinstance(session, str)
                                or not session.strip()):
        raise problem(code, "an actor's session is a non-empty string")
    if kind == "agent" and session is None:
        raise problem(code, "an agent actor needs a session")
    return {"kind": kind, "name": name, "session": session}


def check_scalar(decl: dict, value, lookup=None):
    """Validate one non-null value against a non-metric declaration and return
    it normalised. `lookup(id)` returns the item's type or None."""
    kind = decl["kind"]
    if kind == "text":
        if not isinstance(value, str):
            raise ValueProblem("field_invalid", "a text value is a string")
        return value
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueProblem("field_invalid", "an int value is a JSON integer")
        if abs(value) > INT_LIMIT:
            raise ValueProblem("field_invalid", "an int value is at most 2^53 "
                                                "in magnitude")
        return value
    if kind == "number":
        if not is_number(value):
            raise ValueProblem("field_invalid", "a number value is a finite "
                                                "JSON number")
        return value
    if kind == "date":
        if not valid_date(value):
            raise ValueProblem("field_invalid", "a date value is a valid "
                                                "calendar date, YYYY-MM-DD")
        return value
    if kind == "enum":
        if not any(same(value, v) for v in decl["values"]):
            raise ValueProblem("field_invalid",
                               f"{canonical(value)} is not one of "
                               f"{canonical(decl['values'])}")
        return value
    if kind == "actor":
        return normalize_actor(value)
    if kind == "ref":
        if not isinstance(value, str):
            raise ValueProblem("field_invalid", "a ref value is an item id")
        found = lookup(value) if lookup else None
        if found is None:
            raise ValueProblem("item_not_found", f"no item {value}")
        if found not in decl["to"]:
            raise ValueProblem("field_invalid",
                               f"{value} is a {found}; this ref takes "
                               f"{', '.join(decl['to'])}")
        return value
    if kind == "list":
        if not isinstance(value, list):
            raise ValueProblem("field_invalid", "a list value is a JSON array")
        out = []
        for n, element in enumerate(value):
            if element is None:
                raise ValueProblem("field_invalid", f"element {n} is null")
            try:
                out.append(check_scalar(decl["of"], element, lookup))
            except ValueProblem as exc:
                raise ValueProblem(exc.code, f"element {n}: {exc.message}")
        return out
    raise ValueProblem("field_invalid", f"no value rule for kind {kind}")


def merge_metric(stored, given):
    """§ 5.3: a metric `set` merges the keys given into the stored value."""
    if not isinstance(given, dict):
        raise ValueProblem("metric_invalid", "a metric value is an object")
    extra = sorted(set(given) - set(METRIC_KEYS))
    if extra:
        raise ValueProblem("metric_invalid",
                           f"a metric takes {', '.join(METRIC_KEYS)}, not "
                           f"{', '.join(extra)}")
    merged = dict(stored or {})
    merged.update(given)
    return check_metric(merged)


def check_metric(value) -> dict:
    if not isinstance(value, dict):
        raise ValueProblem("metric_invalid", "a metric value is an object")
    extra = sorted(set(value) - set(METRIC_KEYS))
    if extra:
        raise ValueProblem("metric_invalid",
                           f"a metric takes {', '.join(METRIC_KEYS)}, not "
                           f"{', '.join(extra)}")
    for key in ("target", "direction"):
        if value.get(key) is None:
            raise ValueProblem("metric_invalid", f"a metric needs {key}")
    target, direction = value["target"], value["direction"]
    current, baseline = value.get("current"), value.get("baseline")
    if not is_number(target):
        raise ValueProblem("metric_invalid", "target is a finite number")
    if direction not in DIRECTIONS:
        raise ValueProblem("metric_invalid", "direction is up or down")
    for key, v in (("current", current), ("baseline", baseline)):
        if v is not None and not is_number(v):
            raise ValueProblem("metric_invalid", f"{key} is a finite number "
                                                 f"or null")
    if baseline is not None:
        beyond = target > baseline if direction == "up" else target < baseline
        if not beyond:
            raise ValueProblem("metric_invalid",
                               f"target must be {'above' if direction == 'up' else 'below'} "
                               f"baseline for direction {direction}")
    return {"current": current, "target": target, "baseline": baseline,
            "direction": direction}


# ── the metric formula (§ 5.5) ──────────────────────────────────────────────


def metric_met(value: dict):
    current = value.get("current")
    if current is None:
        return None
    if value["direction"] == "up":
        return current >= value["target"]
    return current <= value["target"]


def metric_fraction(value: dict):
    current, baseline = value.get("current"), value.get("baseline")
    if current is None or baseline is None:
        return None
    raw = (current - baseline) / (value["target"] - baseline)
    if raw <= 0:
        return 0.0
    if raw >= 1:
        return 1.0
    return min(0.999, max(0.001, round(raw, 3)))


def with_derived(value: dict) -> dict:
    """A stored metric plus `met` and `fraction`, for `item get` and `query`."""
    out = dict(value)
    out["met"] = metric_met(value)
    out["fraction"] = metric_fraction(value)
    return out
