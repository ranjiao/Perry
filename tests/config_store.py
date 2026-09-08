"""Build a `.perry/config.jsonl` for a fixture. One writer, for all of them.

Before ADR-019 a fixture declared its settings and tracks by writing a
`.perry/config.md` — a preamble of `- Key: value` bullets and a `## Tracks`
table — and the tools read it. The file is gone, so every one of those fixtures
was declaring nothing: `perry-task add --track ops` came back "track 'ops' is
not declared", and a test that did not write a track at all looked exactly the
same as one whose register the tools had stopped reading.

That is the reason this module exists rather than each fixture growing its own
`json.dumps` loop. The record shape is `bin/perry_md_store § STORED`, the field
list is the schema's, and a fixture that declares a field neither of them knows
about should fail here rather than produce a store the tool under test quietly
discards.

`markdown_that_declares_nothing` is the other half: a fixture may still want to
write a `.perry/config.md`, to assert that a leftover copy in a working tree
changes nothing. Nothing reads it, and that is the assertion.
"""

from __future__ import annotations

import json
import pathlib
import sys

_BIN = pathlib.Path(__file__).resolve().parent.parent / "bin"
if str(_BIN) not in sys.path:
    sys.path.insert(0, str(_BIN))
import perry_md_store as _M                                     # noqa: E402

#: The settings Perry's own store carries, minus the two repo paths (which are
#: machine-specific) and `State root` (see below). What a fixture gets when it
#: asks for no settings of its own — a project configured in the ordinary way.
#:
#: **`State root` is deliberately absent rather than `.`.** `perry_md_store §
#: stored_value` normalises a declared blank on the way in, and `lib.
#: is_blank_cell(".")` is true, so `State root: .` and no `State root` at all
#: store the identical record. A fixture wanting the state root under a
#: subdirectory passes it; one wanting the project root gets it either way, and
#: writing `.` here would suggest a distinction the store does not carry.
DEFAULT_SETTINGS = {
    "Document language": "English",
    "Repo layout": "single",
}


def track(name: str, mode: str = "project", **fields: str) -> dict:
    """One `kind: track` record. Unnamed fields are the declared blank.

    `**fields` are store field names — `default_rung`, not `Default rung` —
    because that is what the record carries and what a reader asks for. A name
    the schema does not declare raises here rather than being written into a
    record every reader then ignores.
    """
    unknown = sorted(set(fields) - set(_M.TRACK_FIELDS))
    if unknown:
        raise AssertionError(
            f"{unknown} are not track fields. Declared: "
            f"{sorted(_M.TRACK_FIELDS)} — see schema/state-schema.json § "
            f'stores.declared[".perry/config.jsonl"].records.track')
    values = {f: "" for f in _M.TRACK_FIELDS}
    values.update(fields)
    values["track"] = name
    values["mode"] = mode
    return values


def config_jsonl(settings: dict[str, str] | None = None,
                 tracks: list[dict] | None = None) -> str:
    """`(settings, tracks)` → the bytes of a `.perry/config.jsonl`.

    `settings` is keyed by LABEL — the words a human writes — and the store key
    is minted from it by `perry_md_store § setting_key`, which is the same rule
    `bin/perry-config set` applies. Keying the fixture by the minted key
    instead would let a fixture and the tool disagree about what
    `PMO repo path` mints to without either one noticing.
    """
    settings = DEFAULT_SETTINGS if settings is None else settings
    out = []
    for n, (label, value) in enumerate(settings.items()):
        out.append(_M.record("setting", {"key": _M.setting_key(label),
                                         "label": label,
                                         "value": _M.stored_value(value)}, n))
    for n, values in enumerate(tracks or []):
        out.append(_M.record("track", values, n))
    return _M.store_text(out)


def write_config(root, settings: dict[str, str] | None = None,
                 tracks: list[dict] | None = None) -> pathlib.Path:
    """Write `<root>/.perry/config.jsonl`, creating `.perry/` if it is absent."""
    path = pathlib.Path(root) / ".perry" / "config.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config_jsonl(settings, tracks), encoding="utf-8")
    return path


def markdown_that_declares_nothing(tracks: str = "") -> str:
    """A `.perry/config.md` for a fixture that wants to prove it is inert.

    The bytes are a real pre-ADR-019 config — settings that contradict the
    defaults above, so a reader that fell back to it would be caught by the
    VALUE and not merely by the absence of one.
    """
    return ("# Perry configuration\n\n"
            "- Document language: 中文\n"
            "- Repo layout: split\n"
            "- State root: from-the-markdown\n" + tracks)


def tracks_table(rows: list[dict]) -> str:
    """The `## Tracks` table those records used to render as.

    For fixtures asserting the markdown is inert: the table has to DECLARE
    something, or "nothing was read" and "nothing was there" are the same
    observation.
    """
    cols = ["Track", "Mode", "Spine", "Stages", "WIP", "SLA", "Cycle",
            "Default rung"]
    out = ["", "## Tracks", "",
           "| " + " | ".join(cols) + " |",
           "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(
            str(r.get(_M.column_field(c)) or "—") for c in cols) + " |")
    return "\n".join(out) + "\n"


__all__ = ["DEFAULT_SETTINGS", "config_jsonl", "markdown_that_declares_nothing",
           "track", "tracks_table", "write_config"]
