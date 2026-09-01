"""`OKR.md` and `.perry/config.md` — the stores, and the renderers of them.

ADR-007's second slice (TASK-092). `perry/tasks.jsonl` proved the shape on
`BOARD.md`; these two files are the same move on the two documents that are
mostly *not* table. The whole design is one sentence:

    the STORE holds what is written; every other byte of the file is LAYOUT
    and comes back out of the file untouched.

**`bin/perry_store.py` is the cell model, and it is not copied here.**
`describe_cell`, `row_descriptor`, `slot_descriptor`, `render_line` and
`render_lines` are imported. A second cell model is the defect ADR-007 exists
to remove, and it would show up exactly where it is hardest to see: on a rule
like "a declared blank marker such as `—` is layout, not data", which would
then mean one thing in `BOARD.md` and another in `.perry/config.md`.

Why byte-identity rather than "parses the same". `TASK-037-spec` is marked
manual on DESIGN-005 § 5.5's verdict that "the risk is not one a test catches:
the failure mode is a file that still parses and no longer reads the way its
author wrote it". That is true of a writer that re-renders prose. It is not
true of a renderer held to `cmp`: a file that no longer reads the way its
author wrote it fails a byte comparison by definition. So `cmp` is the
acceptance here, on two real projects, and "close enough" is a refusal.

What each store holds
---------------------

`okr.jsonl`, beside `OKR.md` in the state root

    kind `kr`          one KR — from a template KR table OR from the legacy
                       `- KR1: …` bullet form, because `viewer/parsers.py §
                       _parse_krs` reads both and a store that held only the
                       table would drop every KR of a real project written the
                       other way. (Measured: `~/proj/gimegime-pmo/OKR.md`
                       carries 0 markdown tables and 34 bullet KRs.)
    kind `commitment`  one row of `## Commitments` — the register
                       `bin/perry-goals commit` writes.
    kind `version`     one row of the `## Versioning log` table.

`.perry/config.jsonl`

    kind `setting`     one `- Key: value` line of the preamble.
    kind `track`       one row of `## Tracks`.

Everything else — the mission, the operating principles, the rationale
paragraphs, gimegime-pmo's nine screens of dispatch lessons — is layout. It is
never parsed and never re-rendered.

**"Never at risk" was true of a renderer that always had the file in front of
it, and `scaffold_config` below is the one that does not** (TASK-233).
`perry-config render` with no `.perry/config.md` on disk rebuilds the document
from the store alone, which is the settings, the table, and the fixed lines of
the shape — so layout survives a render and does not survive a deletion.
`reference/config.md § Prose in this file is layout` states that to a user and
points at `.perry/hook.md`, which is where Perry's own `## Why the state root is
not .` went.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "viewer"))
sys.path.insert(0, str(HERE))
import lib  # noqa: E402
import parsers as P  # noqa: E402
import perry_store  # noqa: E402
from tables import render_row, split_row, squash  # noqa: E402

markdown_tables = perry_store.markdown_tables


class Refused(Exception):
    """A refusal is a first-class outcome. Nothing was written."""


# ── resolving a header cell ───────────────────────────────────────────────


_SCHEMA: dict | None = None


def schema() -> dict:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = lib.load_schema(Refused)
    return _SCHEMA


def spellings(canonical: str) -> list[str]:
    """Every squashed spelling of one column name, English first.

    Table-local resolution, for the reason `bin/perry-goals § column_spellings`
    spells out at length: `截止` is both `Deadline` and `By when` in Chinese,
    and asked globally the question has two answers. Asked of one table's
    header it has one.
    """
    i18n = (schema().get("i18n") or {}).get("columns") or {}
    out = [squash(canonical)]
    for per_lang in (i18n.get(canonical) or {}).values():
        out += [squash(s) for s in per_lang]
    return out


def field_map(columns: dict[str, str], extra: dict[str, str] | None = None) -> dict:
    """`{canonical column: store field}` → `{squashed spelling: store field}`.

    `extra` carries spellings the schema does not declare — `KR` is the KR
    table's own header cell while the i18n key for it is `KR text`, and a
    template that writes one and a project that writes the other are the same
    column.
    """
    out: dict[str, str] = {}
    for canonical, field in columns.items():
        for spelling in spellings(canonical):
            out.setdefault(spelling, field)
    for spelling, field in (extra or {}).items():
        out.setdefault(squash(spelling), field)
    return out


# ── the record shapes ─────────────────────────────────────────────────────

def column_field(name: str) -> str:
    """`Default rung` → `default_rung`. The one rule, applied everywhere.

    It is what `bin/perry-state § _TRACK_KEYS` writes out by hand, so a track
    column the schema declares and the key the store files it under cannot come
    apart.
    """
    return name.strip().lower().replace(" ", "_")


def table_columns(file_path: str, under_needle: str) -> dict[str, str]:
    """`{canonical column: store field}` for one schema-declared table.

    **Read, not restated.** `perry-lint` validates against the schema's copy of
    this list, so a second copy here would disagree the day a column is added —
    and it would disagree silently, because the extra column would simply
    render verbatim and the file would still pass `cmp`.
    """
    for spec in schema().get("files", []):
        if spec.get("path") != file_path:
            continue
        for table in spec.get("tables", []):
            if under_needle not in (table.get("under") or ""):
                continue
            names = (list(table.get("columns") or [])
                     + list(table.get("optional_columns") or {}))
            return {n: column_field(n) for n in names}
    raise Refused(f"schema/state-schema.json declares no {file_path} table "
                  f"under {under_needle!r}; this tool cannot invent one")


#: `## Commitments` — six declared columns plus two optional ones, whatever the
#: schema currently says they are.
COMMITMENT_COLUMNS = table_columns("OKR.md", "Commitments")

#: A KR table under `### Objective <N>`. The ONE map written out rather than
#: derived, because `column_field` cannot make legal field names of this
#: table's headers — `Metric / Target` and `Stretch?` — and because the header
#: cell the schema calls `KR` is the one the i18n table calls `KR text`, so an
#: alias is needed either way. `KR_EXTRA` carries the spellings
#: `viewer/parsers.py § _parse_krs` also accepts.
KR_COLUMNS = {"Id": "id", "KR text": "text", "Metric / Target": "metric",
              "Stretch?": "stretch", "Deadline": "deadline",
              "Linked overall KR": "linked"}
KR_EXTRA = {"KR": "text", "Key result": "text", "KR id": "id",
            "Metric": "metric", "Target": "metric", "Stretch": "stretch",
            "Linked": "linked"}

#: `## Versioning log`. Not a schema-declared table — it is authored prose in a
#: grid — so the spellings are local and a header this map does not know
#: degrades to a verbatim cell that the report COUNTS, rather than to silence.
VERSION_COLUMNS = {"Version": "version", "Date": "date",
                   "What changed": "what", "Why": "why"}
VERSION_EXTRA = {"版本": "version", "日期": "date", "变更": "what",
                 "改了什么": "what", "原因": "why", "为什么": "why"}

#: `.perry/config.md § Tracks` — `Track` and `Mode` are required and the rest
#: are per-mode optional; all of them come from the schema, under the same keys
#: `bin/perry-state § _TRACK_KEYS` reads, so a track the register declares and
#: a track the store holds cannot come to be different sets.
TRACK_COLUMNS = table_columns(".perry/config.md", "Tracks")

#: Fields carried per record kind, in a fixed order, so two writes of the same
#: state produce the same bytes. Same rule and same reason as
#: `perry_store.record`: a store whose lines reshuffle turns every write into a
#: whole-file diff.
STORED: dict[str, tuple[str, ...]] = {
    "kr": ("kind", "version", "objective", "id", "text", "metric", "stretch",
           "deadline", "linked", "qualifier", "form", "order"),
    "commitment": ("kind", "id", "track", "promise", "to_whom", "due",
                   "status", "by_when_note", "discharged_by", "order"),
    "version": ("kind", "version", "date", "what", "why", "order"),
    "setting": ("kind", "key", "label", "value", "order"),
    "track": ("kind", "track", "mode", "spine", "stages", "wip", "sla",
              "cycle", "default_rung", "order"),
}


def _assert_every_declared_column_is_stored() -> None:
    """A schema column the store has no field for would be dropped in silence.

    `record` copies `STORED[kind]` and nothing else, so a column added to
    `schema/state-schema.json` would be read into a site's values, never
    written to the store, and then rendered from an empty field — a real value
    replaced by a blank, on the first write after a schema change, with `cmp`
    the only thing that would notice and only if the cell was non-empty. This
    turns that into an import-time refusal naming the column.
    """
    for kind, columns in (("commitment", COMMITMENT_COLUMNS),
                          ("track", TRACK_COLUMNS)):
        missing = sorted(set(columns.values()) - set(STORED[kind]))
        if missing:
            raise Refused(
                f"schema/state-schema.json declares column(s) {missing} that "
                f"`STORED[{kind!r}]` has no field for. Add them there — a "
                f"column read and not stored is a value dropped in silence")


_assert_every_declared_column_is_stored()


def record_key(rec: dict) -> str:
    """The handle a line and a record are matched on.

    A KR id is unique inside one objective of one version and nowhere else —
    Perry's own `OKR.md` carries `KR-O1.1` twice, once under `## v1` and once
    under `## v2`, and both are live. So the key is the path to the row rather
    than the id in it. A hand edit to a heading therefore moves a row out of
    the store's reach, which is reported as drift rather than guessed at.
    """
    kind = rec.get("kind", "")
    if kind == "kr":
        return f"kr\x00{rec.get('version','')}\x00{rec.get('objective','')}" \
               f"\x00{rec.get('id','')}"
    if kind == "commitment":
        return f"commitment\x00{rec.get('id','')}"
    if kind == "version":
        return f"version\x00{rec.get('version','')}"
    if kind == "setting":
        return f"setting\x00{rec.get('key','')}"
    if kind == "track":
        return f"track\x00{rec.get('track','')}"
    return f"{kind}\x00{rec.get('id','')}"


def record(kind: str, values: dict, order: int) -> dict:
    """One scanned site → one store record, in `STORED[kind]` key order."""
    out: dict = {}
    for field in STORED[kind]:
        if field == "kind":
            out[field] = kind
        elif field == "order":
            out[field] = order
        else:
            out[field] = values.get(field, "")
    return out


def validate_records(records: list) -> tuple[list[dict], list[dict]]:
    """Valid records, and structured findings for the malformed ones.

    The same posture as `perry_store.validate_records`: a store that cannot be
    read is reported field by field rather than raising, because the caller's
    next move is to show the user which line is wrong.
    """
    good: list[dict] = []
    findings: list[dict] = []
    seen: set[str] = set()
    for line, rec in enumerate(records, 1):
        if not isinstance(rec, dict):
            findings.append({"line": line,
                             "message": "expected one JSON object per line"})
            continue
        kind = rec.get("kind")
        if kind not in STORED:
            findings.append({"line": line, "message":
                             f"`kind` is {kind!r}, expected one of "
                             f"{'/'.join(sorted(STORED))}"})
            continue
        bad = []
        for field, value in rec.items():
            if field not in STORED[kind]:
                continue
            if field == "order":
                ok = value is None or (isinstance(value, int)
                                       and not isinstance(value, bool))
                expected = "integer or null"
            else:
                ok = value is None or isinstance(value, str)
                expected = "string or null"
            if not ok:
                bad.append(f"`{field}` is {type(value).__name__}, "
                           f"expected {expected}")
        key = record_key(rec)
        if key in seen:
            bad.append(f"`{key.replace(chr(0), '/')}` is not unique")
        if bad:
            findings.append({"line": line, "key": key.replace("\x00", "/"),
                             "message": "; ".join(bad)})
            continue
        seen.add(key)
        good.append(rec)
    return good, findings


def store_text(records: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def load_store(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in
            path.read_text(encoding="utf-8").split("\n") if l.strip()]


# ── scanning a document into sites ────────────────────────────────────────
#
# A SITE is one line of the file that the store claims, together with what that
# line says and how it is rebuilt. One scan answers both questions — "what does
# the store hold" (`derive`) and "which line does each record render into"
# (`plan`) — so the two can never come to disagree about a row. That is the
# same arrangement `bin/perry-tasks § build` reaches by calling
# `perry-task § store_records` rather than keeping its own copy.


def stored_value(raw: str) -> str:
    """One authored cell → the value the store holds for it.

    **A declared blank marker is layout, not data** — `bin/perry_store.py §
    describe_cell`'s fourth case, applied on the way IN so the two halves
    cannot disagree. `- Code repo path: —` means the field is empty and the
    dash is how this file writes "empty"; storing the dash would make the
    marker data, and the renderer would then have no way to tell an authored
    `—` from a value that happens to be one. Normalising here means the marker
    stays while the field is empty and is replaced the moment it is not, which
    is exactly the rule a board cell obeys.

    This is the ONE transformation between the file and the store. Everything
    else is `.strip()`, and the padding it strips is put back by the cell
    descriptor's `lead`/`trail`.
    """
    text = (raw or "").strip()
    return "" if lib.is_blank_cell(text) else text


def _table_sites(lines, tables, kind, columns, extra=None, context=None,
                 accept=None):
    """Every readable row of `tables`, as sites of one record `kind`."""
    fields = field_map(columns, extra)
    out = []
    for tbl in tables:
        keys = tbl["keys"]
        if not any(k in fields for k in keys):
            continue
        for row in tbl["rows"]:
            values = {}
            for n, key in enumerate(keys):
                field = fields.get(key)
                if field and not values.get(field):
                    values[field] = stored_value(
                        row["cells"][n] if n < len(row["cells"]) else "")
            if context:
                values.update(context(tbl))
            if accept and not accept(values):
                continue
            out.append({"line": row["line"], "kind": kind, "values": values,
                        "how": "table", "cells": row["cells"],
                        "header": tbl["header"], "keys": keys,
                        "fields": fields})
    return out


def _heading_context(lines: list[str]) -> list[tuple[str, str]]:
    """Per line: the `##` heading and the `###` heading in force above it."""
    out = []
    h2 = h3 = ""
    for line in lines:
        m2 = re.match(r"^##\s+(.*)$", line)
        m3 = re.match(r"^###\s+(.*)$", line)
        if m3:
            h3 = m3.group(1).strip()
        elif m2:
            h2, h3 = m2.group(1).strip(), ""
        out.append((h2, h3))
    return out


# ── OKR.md ────────────────────────────────────────────────────────────────


def heading_pattern(under: str) -> re.Pattern:
    """A schema `under` / `match` regex, applied AFTER the hashes are stripped.

    The schema anchors every alternative with `^` because `perry-lint` applies
    it to a heading whose `## ` is already gone. Here the heading text is
    already stripped too, but a `^` in the middle of an alternation — `^承诺`
    in `^Commitments\\b|^承诺` — can only ever match at position zero of the
    whole pattern, so the Chinese half would silently never fire. Dropping the
    anchors is the entire translation, and it is the one `bin/perry-goals §
    heading_pattern` already performs for the same string.
    """
    return re.compile(re.sub(r"(?:^|(?<=\|))\^", "", under))


def _okr_spec() -> dict:
    for spec in schema().get("files", []):
        if spec.get("path") == "OKR.md":
            return spec
    raise Refused("schema/state-schema.json declares no OKR.md; this tool "
                  "cannot invent one")


def okr_heading(label: str) -> re.Pattern:
    for h in _okr_spec().get("headings", []):
        if h.get("label", "").startswith(label):
            return heading_pattern(h["match"])
    raise Refused(f"schema/state-schema.json declares no OKR.md heading "
                  f"{label!r}; this tool cannot invent one")


def table_under(file_path: str, needle: str) -> re.Pattern:
    """The heading regex one schema-declared table sits under.

    `^Tracks\\b|^轨道` was written out here once, which made this the second
    copy of the register's own heading — `bin/perry-state § parse_tracks` holds
    the first. Two spellings of "is this the Tracks section" is the shape of
    every silent disagreement this repository has found.
    """
    for spec in schema().get("files", []):
        if spec.get("path") != file_path:
            continue
        for t in spec.get("tables", []):
            if needle in (t.get("under") or ""):
                return heading_pattern(t["under"])
    raise Refused(f"schema/state-schema.json declares no {file_path} table "
                  f"under {needle!r}; this tool cannot invent one")


def okr_table_under(needle: str) -> re.Pattern:
    return table_under("OKR.md", needle)


def config_table_under(needle: str) -> re.Pattern:
    return table_under(".perry/config.md", needle)


def scan_okr(text: str) -> tuple[list[str], list[dict]]:
    """`OKR.md` → its lines, and every line the store claims."""
    lines = text.split("\n")
    ctx = _heading_context(lines)
    tables = markdown_tables(lines, 0, len(lines), squash)
    commitments = okr_table_under("Commitments")
    versioning = okr_heading("## Versioning log")
    objective = okr_table_under("Objective")

    def bucket(tbl):
        h2, h3 = ctx[tbl["header_line"]]
        if commitments.match(h2):
            return "commitment"
        if versioning.match(h2):
            return "version"
        if objective.match(h3):
            return "kr"
        return None

    sites: list[dict] = []
    for tbl in tables:
        which = bucket(tbl)
        if which == "commitment":
            sites += _table_sites(lines, [tbl], "commitment",
                                  COMMITMENT_COLUMNS)
        elif which == "version":
            sites += _table_sites(lines, [tbl], "version", VERSION_COLUMNS,
                                  VERSION_EXTRA)
        elif which == "kr":
            h2, h3 = ctx[tbl["header_line"]]
            sites += _table_sites(
                lines, [tbl], "kr", KR_COLUMNS, KR_EXTRA,
                context=lambda _t, v=h2, o=h3: {"version": v, "objective": o,
                                                "form": "table"},
                # A KR table row whose `Id` is not a KR id is not a KR —
                # `viewer/parsers.py § _parse_krs` skips it and so does this.
                # Without the same guard the store would mint a record for a
                # legend row and then render the legend from it.
                accept=lambda v: bool(
                    P._RE_KR_ID.match((v.get("id") or "").replace("*", "").strip())))

    claimed = {s["line"] for s in sites}
    inside = {r["line"] for t in tables for r in t["rows"]}
    for i, line in enumerate(lines):
        if i in claimed or i in inside:
            continue
        m = P._RE_KR_BULLET.match(line.strip())
        if not m:
            continue
        # Offsets are taken on the RAW line, not the stripped one: a KR bullet
        # indented under a sub-list keeps its indent, and slicing by offsets
        # from `line.strip()` would move it left by exactly that indent on
        # every render.
        shift = len(line) - len(line.lstrip())
        h2, h3 = ctx[i]
        sites.append({
            "line": i, "kind": "kr", "how": "slots",
            "values": {"version": h2, "objective": h3, "form": "bullet",
                       "id": m.group(1), "qualifier": m.group(2).strip(),
                       "text": stored_value(m.group(3))},
            "slots": [(shift + m.start(1), shift + m.end(1), "id"),
                      (shift + m.start(3), shift + m.end(3), "text")],
        })
    sites.sort(key=lambda s: s["line"])
    return lines, sites


# ── .perry/config.md ──────────────────────────────────────────────────────


#: `- Document language: English`. The label is everything before the first
#: colon, the value everything after it. Restricted to the PREAMBLE — the lines
#: above the first `##` — because a real config's prose sections are full of
#: bullets that carry a colon and are not settings: gimegime-pmo's
#: `## Notes` opens with "Cross-reference convention: PMO docs → code via …",
#: which is a sentence, not a key. `bin/perry-state § parse_config` reads a
#: fixed set of labels and never meets the question; a store that holds
#: whatever is written has to answer it, and the preamble is where every
#: documented key is written.
_SETTING = re.compile(r"^(\s*[-*]\s+)([^:：]+?)\s*([:：])(.*)$")


def setting_key(label: str) -> str:
    """`PMO repo path` → `pmo_repo_path`. Decoration off, spaces to `_`."""
    return re.sub(r"[^\w]+", "_", squash(label)).strip("_")


def scan_config(text: str) -> tuple[list[str], list[dict]]:
    """`.perry/config.md` → its lines, and every line the store claims."""
    lines = text.split("\n")
    tables = markdown_tables(lines, 0, len(lines), squash)
    ctx = _heading_context(lines)
    sites: list[dict] = []

    tracks_heading = config_table_under("Tracks")
    for tbl in tables:
        h2, _h3 = ctx[tbl["header_line"]]
        if not tracks_heading.match(h2):
            continue
        sites += _table_sites(lines, [tbl], "track", TRACK_COLUMNS)

    inside = {r["line"] for t in tables for r in t["rows"]}
    for i, line in enumerate(lines):
        if ctx[i][0]:
            break                       # the preamble ended at the first `##`
        if i in inside:
            continue
        m = _SETTING.match(line)
        if not m:
            continue
        label = m.group(2).strip()
        key = setting_key(label)
        if not key:
            continue
        sites.append({
            "line": i, "kind": "setting", "how": "slots",
            "values": {"key": key, "label": label,
                       "value": stored_value(m.group(4))},
            "slots": [(m.end(3), len(line), "value")],
        })
    sites.sort(key=lambda s: s["line"])
    return lines, sites


# ── the two documents, as one interface ───────────────────────────────────


# ── rebuilding a projection that is not there ─────────────────────────────
#
# TASK-233. Everything above renders the store INTO a file that exists: `plan`
# scans the file for the lines the store fills, and every other byte comes back
# untouched. That is the right contract while there is a file, and it is the
# whole of `cmp` being the bar. It also means that until this section existed,
# `perry-config render` on a project whose `.perry/config.md` had been deleted
# printed `no .perry/config.md` and wrote nothing — an in-place cell updater,
# not the projection `BOARD.md` is.
#
# **A scaffold is a stated contract, not a recovery.** What comes back is the
# canonical shape and the stored values, and nothing else: the title, the
# `## Tracks` heading and the table header are fixed parts of the shape
# (`reference/config.md § .perry/config.md shape`), and PROSE IS NOT
# RECOVERABLE — DESIGN-013 § 5.1 puts a schema'd fact in exactly one store and
# § 5.5 rejects moving prose into one, so a store that could rebuild the prose
# would be the design's own rejected alternative. `reference/config.md § Prose
# in this file is layout` is where that is written for a user, and it is the
# reason Perry's own commentary moved to `.perry/hook.md`.

#: The first line of `.perry/config.md`. Layout, and fixed: `SKILL.md § 195`
#: records why the field names stay English in every language — this is the
#: file that declares the language, so it has to be readable before the
#: language is known — and the title is that argument's first line.
CONFIG_TITLE = "# Perry configuration"

#: The heading `scan_config` matches `## Tracks` under. Spelled once so the
#: scaffold and the scanner cannot come to disagree about it.
TRACKS_HEADING = "## Tracks"


def scaffold_config(records: list[dict]) -> str:
    """`.perry/config.jsonl` → a complete `.perry/config.md`, from the store ALONE.

    For the case there is no file to project onto. Settings become the
    preamble in stored order, tracks become the `## Tracks` table in stored
    order, and a store carrying no track record writes no section at all —
    DESIGN-003 reads an absent `## Tracks` as one implicit `main`, so writing
    an empty table would state something the store does not.

    A stored blank comes back as the blank marker, because that is how the file
    writes "empty" and `stored_value` normalised it away on the way in. The
    marker is `lib.blank_marker`'s, not a literal here.

    **The caller must check that this round-trips.** `main` renders the result
    through `plan`/`render` and refuses when the bytes move or when a record
    finds no line — a scaffold that cannot express a record would otherwise
    write a file that silently drops it, which is the failure mode this whole
    file exists to make impossible.
    """
    blank = lib.blank_marker()

    def shown(value) -> str:
        text = value if isinstance(value, str) else (
            "" if value is None else str(value))
        return text or blank

    settings = sorted((r for r in records if r.get("kind") == "setting"),
                      key=lambda r: (r.get("order") if isinstance(
                          r.get("order"), int) else 0))
    tracks = sorted((r for r in records if r.get("kind") == "track"
                     and (r.get("track") or "").strip()),
                    key=lambda r: (r.get("order") if isinstance(
                        r.get("order"), int) else 0))

    out = [CONFIG_TITLE, ""]
    for rec in settings:
        label = (rec.get("label") or "").strip()
        if not label:
            # A record with no label cannot be written as `- Label: value`.
            # Refusing here rather than inventing one from the key: the key is
            # `setting_key`'s lossy squash of the label — `PMO repo path` and
            # `pmo repo path` mint the same key — so reconstructing it would
            # guess at the user's own capitalisation.
            raise Refused(
                f"the store holds a setting with no label "
                f"({rec.get('key')!r}); `.perry/config.md` cannot be rebuilt "
                f"from it, because the label is the line")
        out.append(f"- {label}: {shown(rec.get('value'))}")
    if tracks:
        columns = list(TRACK_COLUMNS)
        out += ["", TRACKS_HEADING, "",
                render_row(columns),
                "|" + "---|" * len(columns)]
        out += [render_row([shown(rec.get(TRACK_COLUMNS[c])) for c in columns])
                for rec in tracks]
    return "\n".join(out) + "\n"


class Doc:
    """One markdown file that has become a projection of a store.

    Two instances, one implementation. `scan` is the only thing that differs
    between `OKR.md` and `.perry/config.md`, which is the point: everything
    below — deriving, planning, rendering, byte-comparing, reporting drift —
    is the same code for both, and both reach `bin/perry_store.py` for the
    cell model rather than carrying one.
    """

    def __init__(self, name, rel_file, rel_store, scan, under_state_root,
                 scaffold=None):
        self.name = name
        self.rel_file = rel_file
        self.rel_store = rel_store
        self.scan = scan
        self.under_state_root = under_state_root
        #: How to rebuild the whole file from the store when there is no file
        #: to project onto, or `None` for a document that has no declared
        #: shape to rebuild into. `OKR.md` is the `None` case and stays one:
        #: its file is mostly mission, principles and per-objective narrative,
        #: and a scaffold there would emit a KR table under headings the store
        #: has no record of — a file that looks like an `OKR.md` and asserts
        #: nothing the project wrote. `perry-okr render` on a project with no
        #: `OKR.md` still refuses, and says why.
        self.scaffold = scaffold

    def base(self, project_root: Path, state_root: Path) -> Path:
        return state_root if self.under_state_root else project_root

    def file_path(self, project_root: Path, state_root: Path) -> Path:
        return self.base(project_root, state_root) / self.rel_file

    def store_path(self, project_root: Path, state_root: Path) -> Path:
        return self.base(project_root, state_root) / self.rel_store


OKR = Doc("okr", "OKR.md", "okr.jsonl", scan_okr, under_state_root=True)
CONFIG = Doc("config", Path(".perry") / "config.md",
             Path(".perry") / "config.jsonl", scan_config,
             under_state_root=False, scaffold=scaffold_config)
DOCS = {"okr": OKR, "config": CONFIG}


def derive(doc: Doc, text: str) -> list[dict]:
    """The store, derived from the file as it is written today.

    The migration direction, and the only one that reads the file for values.
    Everything else reads the store.
    """
    _lines, sites = doc.scan(text)
    counters: dict[str, int] = {}
    out = []
    for site in sites:
        kind = site["kind"]
        n = counters.get(kind, 0)
        counters[kind] = n + 1
        out.append(record(kind, site["values"], n))
    return out


def plan(doc: Doc, text: str, records: list[dict]) -> dict:
    """The file, split into the lines the store fills and the lines it does not.

    Disagreements are reported, never smoothed over. A line the store has no
    record for renders verbatim and lands in `lines_verbatim`; a record with no
    line lands in `records_not_in_the_file`. Either is a hole in the
    projection, and neither shows up in `cmp` — which is the entire reason the
    report exists next to a byte comparison rather than instead of one.
    """
    lines, sites = doc.scan(text)
    by_key = {record_key(r): r for r in records}
    rows: dict[int, dict] = {}
    report = {"lines_from_store": 0, "lines_verbatim": [],
              "records_not_in_the_file": [], "cells_verbatim": {},
              # The same counted escape hatch `perry_store.plan` carries, under
              # the same name. A hand edit that APPENDS to a cell —
              # `3 of 3 modes live, honest` over a stored `3 of 3 modes live` —
              # lands here rather than in the disagreement list, because the
              # stored value is still in the cell and the extra words are kept
              # as a suffix. It renders byte-identically, so this counter is
              # the only place it shows up at all.
              "cells_wearing_decoration": {},
              "cells_the_store_and_the_file_disagree_on": [],
              "records_out_of_stored_order": [], "kinds": {}}
    seen: set[str] = set()

    for site in sites:
        key = record_key({"kind": site["kind"], **site["values"]})
        rec = by_key.get(key)
        if rec is None:
            report["lines_verbatim"].append(
                {"line": site["line"] + 1, "kind": site["kind"],
                 "key": key.replace("\x00", "/"),
                 "why": "the store holds no record for this line"})
            continue
        line = lines[site["line"]]
        if site["how"] == "table":
            desc, findings = perry_store.row_descriptor(
                line, site["cells"], site["header"], site["keys"],
                site["fields"], rec)
        else:
            desc, findings = perry_store.slot_descriptor(
                line, site["slots"], rec)
        if desc is None:
            report["lines_verbatim"].append(
                {"line": site["line"] + 1, "kind": site["kind"],
                 "key": key.replace("\x00", "/"),
                 "why": findings[0]["why"]})
            continue
        desc["key"] = key
        for f in findings:
            if "verbatim" in f:
                col = f["verbatim"]
                report["cells_verbatim"][col] = \
                    report["cells_verbatim"].get(col, 0) + 1
            elif "decorated" in f:
                col = f["decorated"]
                report["cells_wearing_decoration"][col] = \
                    report["cells_wearing_decoration"].get(col, 0) + 1
            else:
                report["cells_the_store_and_the_file_disagree_on"].append(
                    {"key": key.replace("\x00", "/"), "column": f["column"],
                     "file": f["file"], "store": f["store"]})
        rows[site["line"]] = desc
        seen.add(key)
        report["lines_from_store"] += 1
        report["kinds"][site["kind"]] = report["kinds"].get(site["kind"], 0) + 1

    report["records_not_in_the_file"] = sorted(
        k.replace("\x00", "/") for k in by_key if k not in seen)

    # `order` is a claim until something can be shown to disagree with it, and
    # a record written before the field existed is not a disagreement — the
    # same rule `perry_store.plan` applies to a board section, for the same
    # reason. Reordering here would produce the whole-file diff `order` exists
    # to prevent, so the disagreement is reported and the lines stay put.
    in_line_order: dict[str, list[str]] = {}
    for i in sorted(rows):
        rec = by_key[rows[i]["key"]]
        in_line_order.setdefault(rec["kind"], []).append(rows[i]["key"])
    for kind, got in in_line_order.items():
        graded = [k for k in got if by_key[k].get("order") is not None]
        want = sorted(graded, key=lambda k: by_key[k]["order"])
        if graded != want:
            report["records_out_of_stored_order"].append(
                {"kind": kind,
                 "in_the_file": [k.replace("\x00", "/") for k in graded],
                 "in_the_store": [k.replace("\x00", "/") for k in want]})

    return {"lines": lines, "rows": rows, "records": by_key, "report": report}


def render(doc: Doc, text: str, records: list[dict]) -> tuple[str, dict]:
    """The store → the text of the file. Byte-for-byte is the bar."""
    p = plan(doc, text, records)
    return (perry_store.render_lines(p["lines"], p["rows"], p["records"]),
            p["report"])


def touches(line: str, touched) -> bool:
    """Does one `would_discard` line belong to a record the caller just wrote?

    An entry ending in `/` is a whole kind — `commitment/` covers every row of
    the register, which is what a widened table or a `--migrate` really moves.
    Anything else is ONE record, and the match has to stop at its boundary:
    a bare `startswith` would let `commitment/ops/1` swallow a hand edit to
    `commitment/ops/10`, which is a real id on a register with ten rows.
    """
    for key in touched:
        if key.endswith("/"):
            if line.startswith(key):
                return True
        elif line.startswith(key + ".") or line.startswith(key + ":"):
            return True
    return False


def would_discard(on_disk: list[dict], derived: list[dict]) -> list[str]:
    """Stored values the file-derived records do not carry, one line each.

    Compared BY FIELD, for the reason `bin/perry-tasks § _would_discard`
    states: a record-level "differs" prints the same line for a promise that
    gained a comma and for a status only the store knows about, and telling
    those apart is the whole decision the refusal is asking the user to make.
    """
    by_key = {record_key(r): r for r in derived}
    out: list[str] = []
    for rec in on_disk:
        key = record_key(rec)
        pretty = key.replace("\x00", "/")
        new = by_key.get(key)
        if new is None:
            out.append(f"{pretty}: in the store, no line in the file — "
                       f"the whole record would be dropped")
            continue
        for field in sorted(set(rec) | set(new)):
            a, b = rec.get(field), new.get(field)
            if a != b:
                out.append(f"{pretty}.{field}: store={a!r} → file={b!r}")
    return out


# ── the command line ──────────────────────────────────────────────────────
#
# ONE implementation, two executables. `bin/perry-okr` and `bin/perry-config`
# differ by the `Doc` they pass and by nothing else, so a fix to `diff`'s
# reporting cannot reach one file's tool and miss the other's — which is the
# whole reason `bin/perry-tasks` re-binds `bin/perry_store.py`'s names instead
# of reimplementing them.

USAGE = """\
{tool} — `{file}` as a store, and the projection of it.

    {tool} build   [--root <p>]                derive the store; write nothing
    {tool} verify  [--root <p>]                field-compare the store to the file
    {tool} render  [--root <p>] [--write]      the store → {file}
    {tool} write   [--root <p>] --from-file    {file} → the store
    {tool} diff    [--root <p>]                render and byte-compare with the file

The store is `{store}`. **It is canonical and `{file}` is rendered output**, the
same contract ADR-007 decision 2 gives `perry/tasks.jsonl` and `BOARD.md`. So a
hand edit to `{file}` is REPORTED — `diff` names the cell, and `write` refuses
rather than absorbing it — and is neither silently honoured nor overwritten.
`render --write` is the store-to-file recovery; `write --from-file` is the
explicit board-import direction, for a project being migrated onto the store.

Exit codes: 0 read or written · 1 refused, or drifted · 2 bad invocation.
"""

COMMANDS = ("build", "verify", "write", "render", "diff")


def _first_difference(live: str, rendered: str) -> dict:
    a, b = live.split("\n"), rendered.split("\n")
    n = next((i for i in range(max(len(a), len(b)))
              if (a[i:i + 1] or [None]) != (b[i:i + 1] or [None])), 0)
    return {"line": n + 1,
            "file": (a[n] if n < len(a) else "<past end of file>")[:400],
            "rendered": (b[n] if n < len(b) else "<past end of render>")[:400]}


def main(doc: Doc, argv: list[str], _locked: bool = False) -> int:
    tool = f"perry-{doc.name}"
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE.format(tool=tool, file=doc.rel_file, store=doc.rel_store)
              .strip())
        return 0
    cmd = argv[0]
    if cmd not in COMMANDS:
        print(f"{tool}: expected {' / '.join(COMMANDS)}, got {cmd!r}",
              file=sys.stderr)
        return 2

    root = Path.cwd()
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1]).expanduser()
    root = Path(os.environ.get("PERRY_PROJECT") or root).expanduser().resolve()
    state_root = P.resolve_state_root(root)
    path = doc.file_path(root, state_root)
    store = doc.store_path(root, state_root)

    # One lock spans source reads, derivation, comparison and replacement.
    # Taking it only around the rename still lets a concurrent writer make
    # every decision above that point against stale bytes — the finding
    # `bin/perry-tasks § main` records.
    if not _locked:
        try:
            with lib.project_lock(state_root, refused=Refused):
                return main(doc, argv, _locked=True)
        except Refused as exc:
            print(f"{tool}: refused — {exc}", file=sys.stderr)
            return 1

    # **`render` is the one command that does not need the file** (TASK-233).
    # Every other command is about what the file says; `render` is about what
    # the store says, and a projection that can only be produced when a copy of
    # it already exists is an in-place cell updater rather than a projection.
    # `text` stays `None` until the store has been read and validated, and the
    # scaffold is built from the records — never from a file that is not there.
    text: str | None = None
    if path.exists():
        text = path.read_text(encoding="utf-8")
    elif cmd != "render":
        print(f"{tool}: no {doc.rel_file} at {path}", file=sys.stderr)
        return 2

    if cmd == "build":
        records = derive(doc, text)
        kinds: dict[str, int] = {}
        for r in records:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print(json.dumps({"file": str(path), "records": len(records),
                          "kinds": kinds,
                          "sample": records[0] if records else None},
                         ensure_ascii=False, indent=2))
        return 0

    # **Every command below reads the store FROM DISK**, never the one it could
    # have just derived. `bin/perry-tasks § verify` documents why at length and
    # the reason is the same one: a renderer fed a store built from the file it
    # is being compared against proves that the scanner and the renderer are
    # inverses, which nobody doubted, and proves nothing at all about the
    # store. A planted hand edit passes such a check, because both sides see
    # the edited value.
    if cmd in ("render", "diff", "verify") and not store.exists():
        print(json.dumps({
            "store": str(store), "exists": False,
            "note": f"no store on disk yet — run `{tool} write --from-file` "
                    f"to perform the explicit import. Rendering {doc.rel_file} "
                    f"from a store built out of that same file proves nothing.",
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    if cmd in ("render", "diff", "verify"):
        try:
            on_disk = load_store(store)
        except (OSError, ValueError) as exc:
            print(json.dumps({"identical": False, "store_valid": False,
                              "store_findings": [{"message":
                                  f"store is not readable JSONL "
                                  f"({type(exc).__name__}: {exc})"}]},
                             ensure_ascii=False, indent=2), file=sys.stderr)
            return 2
        records, findings = validate_records(on_disk)
        if findings:
            print(json.dumps({"identical": False, "store_valid": False,
                              "store_findings": findings},
                             ensure_ascii=False, indent=2), file=sys.stderr)
            return 2

        if text is None:
            scaffold = getattr(doc, "scaffold", None)
            if scaffold is None:
                print(f"{tool}: no {doc.rel_file} at {path}, and this document "
                      f"has no scaffold — there is no declared shape to rebuild "
                      f"it into from {doc.rel_store} alone.", file=sys.stderr)
                return 2
            try:
                text = scaffold(records)
            except Refused as exc:
                print(f"{tool}: cannot rebuild {doc.rel_file} from "
                      f"{doc.rel_store} — {exc}", file=sys.stderr)
                return 2
            # **The scaffold is checked, not trusted.** It is written
            # independently of `scan_config` and `render_lines`, so passing it
            # back through them is a real round trip: a column written in the
            # wrong order comes back with the cells rewritten, and a record the
            # scaffold cannot express lands in `records_not_in_the_file`.
            # Either way this refuses instead of writing a file that silently
            # says less than the store does.
            rendered, report = render(doc, text, records)
            missing = report["records_not_in_the_file"]
            if rendered != text or missing:
                print(json.dumps({
                    "refused": f"the shape rebuilt from {doc.rel_store} does "
                               f"not round-trip through this tool's own reader; "
                               f"nothing was written",
                    "records_not_in_the_file": missing,
                    "first_difference": _first_difference(text, rendered),
                }, ensure_ascii=False, indent=2), file=sys.stderr)
                return 2
        else:
            rendered, report = render(doc, text, records)
        if cmd == "render":
            if "--write" not in argv:
                sys.stdout.write(rendered)
                return 0
            lib.write_atomic(path, rendered)
            print(f"{tool}: rendered {path} from {len(records)} stored "
                  f"record(s)")
            return 0

        report["identical"] = rendered == text
        if not report["identical"]:
            report["first_difference"] = _first_difference(text, rendered)
        if cmd == "diff":
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["identical"] else 1

        # `verify` — the field comparison, in the store's own vocabulary
        # rather than in bytes, so a drifted cell is named as a cell.
        drifted = report["cells_the_store_and_the_file_disagree_on"]
        print(json.dumps({
            "store": str(store), "records": len(records),
            "lines_from_store": report["lines_from_store"],
            "lines_the_store_does_not_hold": report["lines_verbatim"],
            "records_not_in_the_file": report["records_not_in_the_file"],
            "cells_the_store_and_the_file_disagree_on": drifted[:10],
            "drift_count": len(drifted),
            "cells_wearing_decoration": report["cells_wearing_decoration"],
            "byte_identical": report["identical"],
        }, ensure_ascii=False, indent=2))
        # A decorated cell renders byte-identically and still carries text the
        # store does not hold, so `verify` counts it as a mismatch even when
        # `diff` is clean. That is the difference between the two commands:
        # `diff` answers "are the bytes the same", `verify` answers "does the
        # store hold what the file says".
        return 0 if (report["identical"] and not drifted
                     and not report["cells_wearing_decoration"]
                     and not report["lines_verbatim"]
                     and not report["records_not_in_the_file"]) else 1

    # `write` — the file → the store. The MIGRATION direction, and since the
    # store became canonical it is the backwards one. It exists to mint a store
    # for a project that has none; once one exists, re-deriving it from the
    # file replaces the canonical value with the projection, which is the
    # measured defect `bin/perry-tasks § write` records at length — a remedy
    # that destroyed the thing it was repairing, recommended by Perry's own
    # linter.
    derived = derive(doc, text)
    if "--from-file" not in argv:
        print(f"{tool}: refusing file-to-store import without `--from-file`. "
              f"`{doc.rel_store}` is authoritative; use `{tool} render "
              f"--write` for store-to-file recovery, or explicitly run "
              f"`{tool} write --from-file` to replace the store from "
              f"{doc.rel_file}.", file=sys.stderr)
        return 1
    if store.exists():
        try:
            on_disk = load_store(store)
        except (OSError, ValueError) as exc:
            print(f"{tool}: {store} exists but cannot be read "
                  f"({type(exc).__name__}: {exc}). Refusing to overwrite a "
                  f"store this tool cannot compare against; move it aside and "
                  f"re-run.", file=sys.stderr)
            return 2
        _valid, malformed = validate_records(on_disk)
        if malformed:
            print(json.dumps({"refused": f"{store} is malformed; refusing to "
                              f"overwrite a store that cannot be safely "
                              f"compared", "store_findings": malformed},
                             ensure_ascii=False, indent=2), file=sys.stderr)
            return 2
        losses = would_discard(on_disk, derived)
        if losses:
            print(f"{tool}: refusing to overwrite {store}.\n\n"
                  f"  This command derives the store FROM {doc.rel_file}, and "
                  f"that file is rendered output. {len(losses)} stored "
                  f"value(s) would be replaced by what it happens to say:\n",
                  file=sys.stderr)
            for line in losses[:10]:
                print(f"    {line}", file=sys.stderr)
            if len(losses) > 10:
                print(f"    … and {len(losses) - 10} more", file=sys.stderr)
            print(f"\n  If the STORE is right — the ordinary case — run "
                  f"`{tool} render --write` to bring the file back in line.\n"
                  f"  If the FILE is right — someone edited it and means it — "
                  f"move {doc.rel_store} aside and re-run.", file=sys.stderr)
            return 1
    # **The store this command is about to write must be one it could read
    # back.** Two lines of one file carrying the same key — a config that
    # declares `- State root:` twice, a register with a duplicated `Id` — mint
    # two records the loader would then reject, and writing that is minting an
    # unreadable store and calling it a success. The file is the thing to fix,
    # so the finding names its key rather than the JSONL line.
    _valid, bad = validate_records(derived)
    if bad:
        print(json.dumps({"refused": f"{doc.rel_file} produces a store this "
                          f"tool could not read back; nothing was written",
                          "store_findings": bad}, ensure_ascii=False,
                         indent=2), file=sys.stderr)
        return 1
    lib.write_atomic(store, store_text(derived))
    print(f"{tool}: wrote {store} ({len(derived)} records)")
    return 0


# **The ADR-004 conformance gate stood here and is gone (TASK-261).**
# `render --write` used to consult a stored DECLARATION about the file it was
# about to render and refuse when the shape no longer matched. On this
# repository that ledger held 23 records, all `route: declare`, all Perry's
# own files — zero disagreements, because a disagreement needs a foreign
# project and Perry has never been pointed at one. `tests/gate.py § GATE_OFF`,
# the documented way out of the self-referential case this function's own
# docstring described, goes with it.


__all__ = ["CONFIG", "COMMANDS", "CONFIG_TITLE", "DOCS", "OKR", "Doc",
           "Refused", "STORED", "TRACKS_HEADING", "derive", "field_map",
           "load_store", "main", "plan", "record", "record_key", "render",
           "scaffold_config", "scan_config", "scan_okr", "setting_key",
           "store_text", "stored_value", "touches", "validate_records",
           "would_discard"]
