"""The command surface, declared once (§ 5.6).

The parser, the input checker, the generated usage and `describe` all read
`COMMANDS`, so none of them can accept or promise what another does not.
Nothing here reads a store, a path or a clock: `describe` is byte-identical in
every project.
"""

from __future__ import annotations

from . import template as tpl
from .errors import ERRORS, EXIT_CODES, SET_A, SET_S, SET_W, WARNINGS
from .values import FIELD_KINDS

SURFACE = "1.1"

#: The eight concepts (Goal 6). A ninth is a revision of DESIGN-023.
CONCEPTS = ("template", "item", "field", "transition", "guard", "relation",
            "event", "attachment")

#: The declared budget. The kernel suite holds these to its own literals.
BUDGET = {"concepts": 8, "command_groups": 12}


# ── input key declarations ─────────────────────────────────────────────────


def k(json_type: str, required: bool = False, **extra) -> dict:
    spec = {"type": json_type, "required": required}
    spec.update(extra)
    return spec


def obj(keys: dict, required: bool = False, **extra) -> dict:
    return k("object", required, keys=keys, **extra)


def arr(items: dict, required: bool = False) -> dict:
    return k("array", required, items=items)


ACTOR = obj({"kind": k("string", True), "name": k("string", True),
             "session": k("string")}, True, actor=True)
NOTE = k("string")
EXPECT = k("object", values=k("integer"))
OPEN = k("object", open=True)
NAMES = arr(k("string"))
EDGE = obj({"kind": k("string", True), "to": k("string"),
            "from": k("string")})

WRITE_FLAGS = ("--input", "--dry-run")


def command(name, kind, input_keys, result, errors, *, has_input=True,
            summary=""):
    return {"name": name, "kind": kind, "purpose": summary,
            "input": input_keys if has_input else None,
            "result": list(result), "errors": list(dict.fromkeys(errors))}


COMMANDS = [
    command("init", "write",
            {"actor": ACTOR, "state_root": k("string", True), "note": NOTE},
            ("store", "anchor", "state_root", "journal_mode"),
            SET_A + ("anchor_not_found", "store_foreign", "store_version",
                     "store_busy", "store_corrupt", "store_live_under_test",
                     "io_error", "actor_invalid", "store_initialized"),
            summary="create the store and record the state root"),
    command("template apply", "write",
            {"actor": ACTOR, "template": k("object", True, open=True),
             "ceilings": k("object", values=k("integer")), "note": NOTE},
            ("name", "version", "previous_version"),
            SET_W + ("template_invalid", "template_version",
                     "template_incompatible"),
            summary="apply a new version of the process template"),
    command("template show", "read", None,
            ("template", "version", "applied_seq", "applied_at"), SET_S,
            has_input=False, summary="the applied template, verbatim"),
    command("template validate", "read",
            {"template": k("object", True, open=True)},
            ("valid", "format", "types"),
            SET_A + ("io_error", "template_invalid"),
            summary="validate a template's format; opens no store"),
    command("item create", "write",
            {"actor": ACTOR, "type": k("string", True), "fields": OPEN,
             "relations": arr(EDGE),
             "attachments": arr(obj({"ref": k("string", True),
                                     "hash": k("string")})),
             "note": NOTE, "expect": EXPECT},
            ("item",),
            SET_W + ("stale_write", "no_template", "unknown_type",
                     "unknown_field", "field_invalid", "metric_invalid",
                     "item_not_found", "unknown_relation", "relation_invalid",
                     "relation_cycle", "attachment_invalid", "guard_refused",
                     "id_exhausted"),
            summary="create an item with its relations and attachments"),
    command("item get", "read", {"id": k("string", True)}, ("item",),
            SET_S + ("no_template", "item_not_found"),
            summary="one item with its derived fields"),
    command("item update", "write",
            {"actor": ACTOR, "id": k("string", True), "set": OPEN,
             "unset": NAMES, "note": NOTE, "expect": EXPECT},
            ("item",),
            SET_W + ("stale_write", "no_template", "item_not_found",
                     "unknown_field", "field_invalid", "metric_invalid"),
            summary="set or unset fields; no guards run"),
    command("item move", "write",
            {"actor": ACTOR, "id": k("string", True),
             "transition": k("string", True), "set": OPEN, "unset": NAMES,
             "note": NOTE, "expect": EXPECT},
            ("item", "transition", "from_state", "to_state"),
            SET_W + ("stale_write", "no_template", "item_not_found",
                     "unknown_transition", "transition_not_allowed",
                     "unknown_field", "field_invalid", "metric_invalid",
                     "guard_refused"),
            summary="run a transition and its guards"),
]

for _verb in ("add", "remove"):
    COMMANDS.append(command(
        f"rel {_verb}", "write",
        {"actor": ACTOR, "kind": k("string", True), "from": k("string", True),
         "to": k("string", True), "note": NOTE, "expect": EXPECT},
        ("relation",),
        SET_W + ("stale_write", "no_template", "item_not_found",
                 "unknown_relation", "relation_invalid")
        + (("relation_cycle",) if _verb == "add" else ()),
        summary=f"{_verb} one edge; an existing edge added, or a missing one "
                f"removed, is unchanged"))
for _verb in ("add", "remove"):
    _keys = {"actor": ACTOR, "id": k("string", True), "ref": k("string", True)}
    if _verb == "add":
        _keys["hash"] = k("string")
    _keys.update({"note": NOTE, "expect": EXPECT})
    COMMANDS.append(command(
        f"attach {_verb}", "write", _keys, ("attachment",),
        SET_W + ("stale_write", "no_template", "item_not_found",
                 "attachment_invalid"),
        summary=f"{_verb} one attachment; the kernel never opens the target"))

COMMANDS += [
    command("query", "read",
            {"type": k("string"), "ids": NAMES, "state": NAMES,
             "terminal": k("boolean"), "where": k("object", values=k("array")),
             "related": EDGE, "startable": k("boolean"), "count_by": NAMES,
             "after": k("string"), "limit": k("integer")},
            ("items", "total", "returned", "truncated", "next_after",
             "counts"),
            SET_S + ("no_template", "unknown_type", "unknown_field",
                     "unknown_relation", "item_not_found"),
            summary="items by filter, with derived fields; 50 rows unless "
                    "limit says otherwise"),
    command("events", "read",
            {"items": NAMES, "keys": NAMES, "commands": NAMES,
             "after_seq": k("integer"), "limit": k("integer")},
            ("events", "total", "returned", "truncated", "next_after_seq",
             "last_export_seq", "unexported"),
            SET_S, summary="the history; 50 rows unless limit says otherwise"),
    command("export", "write", None, ("dir", "files", "last_export_seq"),
            SET_S + ("export_dir_foreign",), has_input=False,
            summary="write <state root>/export/items.jsonl and events.jsonl"),
    command("import", "write", {"state_root": k("string", True)},
            ("dir", "items", "events", "last_seq", "verified"),
            SET_A + ("anchor_not_found", "store_foreign", "store_version",
                     "store_busy", "store_corrupt", "store_live_under_test",
                     "io_error", "store_not_empty", "export_missing",
                     "export_invalid", "replay_mismatch"),
            summary="restore an empty store from the export, verified"),
    command("describe", "read", None,
            ("surface", "concepts", "budget", "commands", "flags", "env",
             "exit_codes", "errors", "template_format"),
            SET_A, has_input=False,
            summary="this surface as JSON; reads no store, path or clock"),
]

BY_NAME = {c["name"]: c for c in COMMANDS}

#: Commands that open no store at all.
STORELESS = ("template validate", "describe")

#: Flags every command takes, and the two that only some do.
GLOBAL_FLAGS = {
    "--store": {"takes": "PATH", "applies": "every command",
                "help": "the store file; beats PERRY_STORE and the derived "
                        "path"},
    "--root": {"takes": "PATH", "applies": "every command",
               "help": "the project anchor (a directory holding .perry/); "
                       "beats PERRY_PROJECT and the walk up"},
    "--json": {"takes": None, "applies": "every command",
               "help": "accepted and changes nothing: output is always JSON"},
    "-h": {"takes": None, "applies": "every command",
           "help": "print usage and exit 0, in any position; nothing runs"},
    "--help": {"takes": None, "applies": "every command",
               "help": "the same as -h"},
}
COMMAND_FLAGS = {
    "--input": {"takes": "JSON|@FILE|-", "applies": "commands with input",
                "help": "exactly one JSON object: inline, from a file, or "
                        "from stdin"},
    "--dry-run": {"takes": None, "applies": "writes",
                  "help": "run the transaction and roll it back"},
}
VALUE_FLAGS = {name for name, spec in {**GLOBAL_FLAGS, **COMMAND_FLAGS}.items()
               if spec["takes"]}
HELP_FLAGS = ("-h", "--help")

ENV = {
    "PERRY_STORE": "the store file, when --store is not given",
    "PERRY_PROJECT": "the project anchor, when --root is not given",
    "PERRY_KERNEL_TESTING": "when set, a derived store path is refused "
                            "(store_live_under_test)",
}


def flags_of(cmd: dict) -> list[str]:
    out = ["--store", "--root", "--json", "-h", "--help"]
    if cmd["input"] is not None:
        out.append("--input")
    if cmd["kind"] == "write":
        out.append("--dry-run")
    return out


def describe() -> dict:
    """The whole surface. Deterministic: no store, no path, no clock."""
    return {
        "surface": SURFACE,
        "concepts": list(CONCEPTS),
        "budget": dict(BUDGET),
        "commands": [{"name": c["name"], "kind": c["kind"],
                      "purpose": c["purpose"], "flags": flags_of(c),
                      "input": c["input"], "result": c["result"],
                      "errors": c["errors"]} for c in COMMANDS],
        "flags": {**GLOBAL_FLAGS, **COMMAND_FLAGS},
        "env": dict(ENV),
        "exit_codes": dict(EXIT_CODES),
        "errors": {code: {"exit": ex, "when": when}
                   for code, (ex, when) in ERRORS.items()},
        "template_format": {
            "format": tpl.FORMAT,
            "field_kinds": list(FIELD_KINDS),
            "guard_kinds": list(tpl.GUARD_KINDS),
            "relations": dict(tpl.BUILTIN_RELATIONS),
            "names": tpl.NAME_RE.pattern,
            "prefixes": tpl.PREFIX_RE.pattern,
            "keys": tpl.schema(),
            "warnings": dict(WARNINGS),
        },
    }


# ── generated usage (NN-K3) ────────────────────────────────────────────────


def _spec_line(name: str, spec: dict, indent: str) -> list[str]:
    mark = "required" if spec.get("required") else "optional"
    kind = spec["type"]
    if spec.get("items"):
        kind = f"array of {spec['items']['type']}"
    lines = [f"{indent}{name:<14} {kind}, {mark}"]
    for sub, subspec in (spec.get("keys") or {}).items():
        lines += _spec_line(sub, subspec, indent + "  ")
    if spec.get("items") and spec["items"].get("keys"):
        for sub, subspec in spec["items"]["keys"].items():
            lines += _spec_line(sub, subspec, indent + "  ")
    return lines


def usage(prog: str, name: str | None = None) -> str:
    if name in BY_NAME:
        c = BY_NAME[name]
        parts = []
        for f in flags_of(c):
            if f in HELP_FLAGS:
                continue
            takes = (GLOBAL_FLAGS.get(f) or COMMAND_FLAGS[f])["takes"]
            parts.append(f"[{f} {takes}]" if takes else f"[{f}]")
        flags = " ".join(parts)
        lines = [f"usage: {prog} {c['name']} {flags}", "",
                 f"{c['name']} ({c['kind']}): {c['purpose']}.", ""]
        if c["input"] is None:
            lines.append("input: none (--input is refused)")
        else:
            lines.append("input keys (one JSON object via --input):")
            for key, spec in c["input"].items():
                lines += _spec_line(key, spec, "  ")
        lines += ["", "result keys: " + ", ".join(c["result"]),
                  "errors: " + ", ".join(c["errors"]), "",
                  "Every outcome is one JSON envelope on stdout. Exit codes: "
                  "0 success, 1 refused, 2 bad invocation, 3 internal fault.",
                  f"The whole surface as JSON: {prog} describe"]
        return "\n".join(lines) + "\n"
    synopsis = " ".join(
        f"[{f} {spec['takes']}]" if spec["takes"] else f"[{f}]"
        for f, spec in (("--input", COMMAND_FLAGS["--input"]),
                        ("--store", GLOBAL_FLAGS["--store"]),
                        ("--root", GLOBAL_FLAGS["--root"]),
                        ("--dry-run", COMMAND_FLAGS["--dry-run"]),
                        ("--json", GLOBAL_FLAGS["--json"])))
    lines = [f"usage: {prog} <command> {synopsis}", "",
             "The kernel: one store per project, JSON in and JSON out. It "
             "knows eight concepts",
             "and no method; every type, state, field and guard comes from the "
             "applied template.", "", "commands:"]
    for c in COMMANDS:
        lines.append(f"  {c['name']:<18} {c['kind']:<5}  {c['purpose']}")
    lines += ["", "flags:"]
    for f, spec in {**GLOBAL_FLAGS, **COMMAND_FLAGS}.items():
        takes = f" {spec['takes']}" if spec["takes"] else ""
        lines.append(f"  {f + takes:<22} {spec['help']}")
    lines += ["", "environment:"]
    for var, text in ENV.items():
        lines.append(f"  {var:<22} {text}")
    lines += ["", f"{prog} <command> --help shows a command's input keys; "
                  f"{prog} describe prints the whole surface as JSON.",
              "Exit codes: 0 success, 1 refused, 2 bad invocation, "
              "3 internal fault (rolled back)."]
    return "\n".join(lines) + "\n"
