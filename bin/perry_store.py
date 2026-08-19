"""`perry/tasks.jsonl` — the store, its record shape, and the renderer.

ADR-007's first slice. `bin/perry-tasks` derives and inspects the store;
`bin/perry-task` writes it. **Both reach the same code here**, because the one
defect this repository keeps re-finding is two implementations of one question
drifting apart — `viewer/parsers.py` and `bin/perry-task` were two parsers of
one file and disagreed silently, and a renderer copied into the writer would be
the same bug with the arrow reversed.

Nothing here imports `bin/perry-task`. What it needs from that file — a `Board`,
and the module itself as `ops`, for `ops.norm` and `ops.strip_handle` — is
passed in, so the dependency runs one way and the two load in either order.
`ops.norm` rather than a local copy is the same route `bin/perry-migrate` takes
to the one header rule (`tests/test_one_header_rule.py`): a header cell is
resolved by `squash` and its glossary aliases, here as everywhere.

Two things go into a rendered board and they are different things:

  the STORE      the typed values — the nineteen fields of `STORED`. Every one
                 of them is read out of `perry/tasks.jsonl` and out of nothing
                 else.
  the LAYOUT     the projection's shape — the preamble, the section order and
                 headings, the separator rows, which column sits where, and the
                 padding and decoration each cell wears. Derived from the board
                 in this slice; TASK-090 is where the board reader goes.

The line between them is the whole proof, so the report counts every cell the
layout had to keep VERBATIM rather than fill from the store.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "viewer"))
from tables import cell_spans, split_row  # noqa: E402

#: Written to the store. Everything else in `perry-task/list` is computed.
#:
#: `order` is the nineteenth and it is the answer to TASK-088's third finding.
#: **Authored row order is recorded, not re-derived.** `perry-task/list` sorts
#: by id and Perry's own `## P1` runs `TASK-047` before `TASK-038`, so a store
#: that did not carry order would move two rows of the first board it rendered
#: — a whole-file diff on somebody's project, on the first write, which is
#: exactly what `viewer/tables.py § render_row` already refuses to do one row
#: down ("turning a one-cell edit into a whole-table diff and burying the
#: change nobody can then review") and what ADR-004 means by a migration being
#: reviewable. It is not a derived value: nothing else in the record determines
#: where triage decided a row should sit.
STORED = ("id", "title", "owner", "status", "priority", "track", "stage",
          "stage_since", "arrived", "verification", "evidence", "next_action",
          "depends_on", "commitment", "parent", "group", "role", "created",
          "order")

#: `norm(header cell)` → the store field that column is rendered from. The keys
#: are exactly what `bin/perry-task § cmd_list` zips its cells under, so a
#: localized header resolves here for the same reason it resolves there, and
#: this table cannot drift from the reader without the round trip going red.
FIELD_BY_COLUMN = {
    "id": "id", "title": "title", "owner": "owner", "status": "status",
    "track": "track", "stage": "stage", "stage since": "stage_since",
    "arrived": "arrived", "parent": "parent", "commitment": "commitment",
    "next action": "next_action", "evidence": "evidence",
    "verification": "verification", "role": "role", "depends on": "depends_on",
}


# ── markdown tables ───────────────────────────────────────────────────────


_SEPARATOR = re.compile(r"^\|\s*:?-{2,}")


def markdown_tables(lines: list[str], start: int, end: int, norm) -> list[dict]:
    """Every markdown table block in ``lines[start:end]``.

    A table starts only at a header immediately followed by a separator. Its
    rows remain contiguous apart from blank lines, subheadings, and notes; prose
    ends that table, but scanning continues so a later table is still found.
    This one rule is shared by lookup, section walkers, store derivation, and
    rendering. In particular, a repeated header starts another table and can
    never become a record whose id is the literal ``ID``.
    """
    starts: list[tuple[int, int, list[str]]] = []
    for sep in range(start + 1, end):
        if not _SEPARATOR.match(lines[sep].strip()):
            continue
        if not lines[sep - 1].strip().startswith("|"):
            continue
        header = split_row(lines[sep - 1])
        if header:
            starts.append((sep - 1, sep, header))

    out: list[dict] = []
    for n, (header_i, sep, header) in enumerate(starts):
        limit = starts[n + 1][0] if n + 1 < len(starts) else end
        keys = [norm(h) for h in header]
        rows = []
        active = True
        for i in range(sep + 1, limit):
            s = lines[i].strip()
            if not s.startswith("|"):
                if s and not s.startswith(("#", ">")):
                    active = False
                continue
            if not active or _SEPARATOR.match(s):
                continue
            cells = split_row(lines[i])
            if not cells or not cells[0]:
                continue
            rows.append({"line": i, "cells": cells,
                         "values": dict(zip(keys, cells))})
        out.append({"header_line": header_i, "separator": sep,
                    "header": header, "keys": keys, "rows": rows,
                    "end": limit})
    return out


# ── the record ────────────────────────────────────────────────────────────


def record(task: dict, order: int | None) -> dict:
    """One `perry-task/list` task → one store record, in `STORED` key order.

    The key order is fixed rather than incidental so two writes of the same
    state produce the same bytes; a store whose lines reshuffle turns every
    write into a whole-file diff, which is the same objection `order` exists
    to answer.
    """
    out: dict = {}
    for k in STORED:
        if k == "order":
            out[k] = order
        elif k == "depends_on":
            out[k] = list(task.get("depends_on") or [])
        else:
            out[k] = task.get(k, "")
    return out


def board_order(board, ops) -> dict[str, int]:
    """id → its position among the rows of its section, 0-based.

    **Position among the rows the STORE holds**, not among the lines. One real
    board carries `| 2 待核项 |` — a first cell that is prose rather than a
    handle — and the store has no record of it, so it cannot be a record's
    neighbour. Rows the store does not hold are the layout's business and are
    counted in `rows_verbatim` instead.
    """
    out: dict[str, int] = {}
    positions: dict[str, int] = {}
    for tbl in board.task_tables():
        if not tbl["readable"]:
            continue
        n = positions.get(tbl["heading"], 0)
        for c in tbl["rows"]:
            tid = ops.strip_handle(c.get("id", ""))
            if not tid or tid in out:
                continue
            out[tid] = n
            n += 1
        positions[tbl["heading"]] = n
    return out


def store_path(state_root: Path) -> Path:
    return Path(state_root) / "tasks.jsonl"


def store_text(records: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def load_store(state_root: Path) -> list[dict]:
    p = store_path(state_root)
    if not p.exists():
        return []
    return [json.loads(l) for l in
            p.read_text(encoding="utf-8").split("\n") if l.strip()]


def validate_records(records: list) -> tuple[list[dict], list[dict]]:
    """Return valid records and structured findings for malformed ones.

    ``bool`` is intentionally not an integer here even though Python subclasses
    it from ``int``. JSON ``true`` is not a meaningful row position.
    """
    good: list[dict] = []
    findings: list[dict] = []
    seen: set[str] = set()
    for line, rec in enumerate(records, 1):
        if not isinstance(rec, dict):
            findings.append({"line": line, "field": None,
                             "message": "expected one JSON object per line"})
            continue
        bad = []
        for field, value in rec.items():
            if field not in STORED:
                continue
            if field == "order":
                ok = value is None or (isinstance(value, int)
                                       and not isinstance(value, bool))
                expected = "integer or null"
            elif field == "depends_on":
                ok = value is None or (
                    isinstance(value, list)
                    and all(isinstance(item, str) for item in value)
                )
                expected = "list of strings or null"
            else:
                ok = value is None or isinstance(value, str)
                expected = "string or null"
            if not ok:
                bad.append({"field": field, "actual": type(value).__name__,
                            "expected": expected})
        tid = rec.get("id")
        if not isinstance(tid, str) or not tid.strip():
            bad.append({"field": "id", "actual": type(tid).__name__,
                        "expected": "non-empty string"})
        elif tid in seen:
            bad.append({"field": "id", "actual": tid,
                        "expected": "unique task id"})
        if bad:
            findings.append({"line": line, "id": tid if isinstance(tid, str) else None,
                             "fields": bad,
                             "message": "; ".join(
                                 f"`{b['field']}` is {b['actual']}, expected {b['expected']}"
                                 for b in bad)})
            continue
        seen.add(tid)
        good.append(rec)
    return good, findings


# ── the renderer ──────────────────────────────────────────────────────────
#
# **A store that cannot reproduce the document it replaces has already lost
# data**, and "reproduce" has to mean the bytes. So the acceptance is `cmp`,
# not "equivalent".


def cell_text(field: str, rec: dict) -> str:
    """One stored field → the text of its cell, escaped the way a row carries it.

    `depends_on` is a list in the store and a cell on the board, so the join is
    here and the split is `bin/perry-task § parse_depends`. The separator that
    round-trips is the one `add --depends` writes; a board that spells its list
    with `、` renders as a verbatim cell and is counted as one, rather than
    being quietly rewritten into English punctuation.
    """
    v = rec.get(field, "")
    if field == "depends_on":
        v = ", ".join(v or [])
    return str("" if v is None else v).strip().replace("|", "\\|")


def describe_cell(raw: str, field: str, rec: dict) -> dict:
    """How one raw cell is rebuilt from one stored value — or that it cannot be.

    Four cases, and **the third is the one the first version of this got
    wrong**:

      the cell IS the value    `{"f": …}` — padding aside, they are the same
                               text.
      the value, decorated     `{"f": …, "p"/"s": …}` — `~~**ALLOC-01**~~` is a
                               real id cell from a real board and
                               `strip_handle` drops the `~~**` before the store
                               ever sees it. The decoration is presentation and
                               is kept here; the id is data and is kept there.
      they DISAGREE            `{"f": …}` again — the store's value is
                               rendered, the board's text is not, and the byte
                               difference is the report. The first version
                               fell back to verbatim here, which meant the
                               layout was derived against the store it was
                               meant to be testing. **A renderer that cannot be
                               made to print a wrong value cannot be shown to
                               print a right one.**
      the store is EMPTY       `{"lit": …}` — `""` is the contract's word for
                               "not known" (`schema/task-list-contract.md`).
                               Kept verbatim AND COUNTED, because a fallback
                               nobody counts is how a renderer passes `cmp`
                               while reproducing nothing.

    An off-enum `Status` cell used to be the fourth case's headline example.
    It is not one any more: `bin/perry-task § refuse_unstorable_status` refuses
    the write rather than letting the store carry a column it cannot hold —
    see that function for why. This branch still exists because a board may
    carry a column the store has no field for at all (`By when`, `Notes`), and
    that is layout, not a lost value.
    """
    want = cell_text(field, rec)
    body = raw.strip()
    lead = raw[:len(raw) - len(raw.lstrip())]
    trail = raw[len(raw.rstrip()):]
    if not body:
        # A blank cell is ALL padding, and splitting it into a leading half and
        # a trailing half counts it twice — `|  |` came back `|    |` on every
        # empty `Depends on` cell of Perry's own board. The padding it had is
        # kept as one piece for as long as the value is empty; the day the
        # store fills that field the cell gets ordinary `| x |` spacing,
        # because there is no hand alignment in a cell that held nothing.
        c = {"f": field, "lead": " ", "trail": " ", "blank": raw}
        if want:
            c["disagrees"] = body
        return c
    if body == want:
        return {"f": field, "lead": lead, "trail": trail}
    if not want:
        return {"lit": raw}
    if want in body:
        at = body.index(want)
        return {"f": field, "lead": lead, "trail": trail,
                "p": body[:at], "s": body[at + len(want):]}
    return {"f": field, "lead": lead or " ", "trail": trail or " ",
            "disagrees": body}


def render_line(desc: dict, rec: dict) -> str:
    """One row descriptor + one store record → the row's line.

    The separators are `|` because `cell_spans` splits on exactly that and
    leaves the escaped ones inside the span, so a cell whose value contains a
    pipe rebuilds through `cell_text` and lands back where it started.
    """
    out = []
    for c in desc["cells"]:
        if "lit" in c:
            out.append(c["lit"])
            continue
        v = cell_text(c["f"], rec)
        if not v and "blank" in c:
            out.append(c["blank"])
            continue
        out.append(c["lead"] + c.get("p", "") + v + c.get("s", "") + c["trail"])
    return desc["pre"] + "|".join(out) + desc["post"]


def plan(board, records: list[dict], ops) -> dict:
    """A board, split into the lines the store fills and the lines it does not.

    A row line is filled from the record whose `id` it carries and whose
    `group` is the section it sits in; everything else about the line — what
    its cells are padded with, what decoration they wear — is layout.

    **Where a row SITS is the store's business now.** TASK-088 measured that it
    was not: ordering out of the store would have moved two rows of Perry's own
    `## P1`. `STORED` carries `order` for that reason, and this function reports
    every section whose lines disagree with it (`sections_out_of_stored_order`)
    rather than reordering them — reordering here would produce the whole-file
    diff the field exists to prevent, and the disagreement is a finding either
    way. TASK-090 is where `order` stops being checked and starts being obeyed,
    because that is where the board stops being read.

    Disagreements are reported rather than smoothed over: a row on the board
    that the store does not hold renders verbatim and lands in
    `rows_verbatim`, and a row the store holds for a section that has no line
    for it lands in `rows_not_on_board`. Either one is a hole in the
    projection, and neither shows up in `cmp`.
    """
    lines = board.lines
    by_id = {r["id"]: r for r in records}
    by_group: dict[str, list[dict]] = {}
    for r in records:
        if r.get("group"):
            by_group.setdefault(r["group"], []).append(r)

    rows: dict[int, dict] = {}
    report = {"rows_from_store": 0, "rows_verbatim": [],
              "rows_not_on_board": [], "cells_verbatim": {},
              "cells_the_store_and_board_disagree_on": [],
              "sections_out_of_stored_order": [], "sections": []}

    for table in board.task_tables():
        heading = table["heading"]
        header = table["header"]
        keys = [ops.norm(h) for h in header]
        if not table["readable"]:
            # Not a task table — a reference table, a legend. `task_tables()`
            # reports it and reads nothing from it; so does this.
            continue
        wanted = {r["id"] for r in by_group.get(heading, [])}
        seen: set = set()
        in_line_order: list[str] = []
        for item in table["row_items"]:
            i, cells = item["line"], item["cells"]
            tid = ops.strip_handle(cells[0])
            rec = by_id.get(tid)
            if rec is None or rec.get("group") != heading:
                report["rows_verbatim"].append(
                    {"section": heading, "cell": cells[0][:60]})
                continue
            seen.add(tid)
            in_line_order.append(tid)
            spans = cell_spans(lines[i])
            if len(spans) != len(cells):
                # The two scans disagree about this line, which means one of
                # them is wrong about it. Rendering from the one that is wrong
                # would move a cell; leaving the line alone does not.
                report["rows_verbatim"].append(
                    {"section": heading, "cell": cells[0][:60],
                     "why": "cell spans and split disagree"})
                in_line_order.pop()
                seen.discard(tid)
                continue
            desc = {"id": tid, "pre": lines[i][:spans[0][0]],
                    "post": lines[i][spans[-1][1]:], "cells": []}
            for n, (a, b) in enumerate(spans):
                col = header[n] if n < len(header) else f"#{n}"
                field = FIELD_BY_COLUMN.get(keys[n]) if n < len(keys) else None
                c = ({"lit": lines[i][a:b]} if field is None
                     else describe_cell(lines[i][a:b], field, rec))
                if "lit" in c:
                    report["cells_verbatim"][col] = \
                        report["cells_verbatim"].get(col, 0) + 1
                elif "disagrees" in c:
                    report["cells_the_store_and_board_disagree_on"].append(
                        {"id": tid, "column": col,
                         "board": c["disagrees"][:120],
                         "store": cell_text(field, rec)[:120]})
                desc["cells"].append(c)
            rows[i] = desc
            report["rows_from_store"] += 1
        # A section may contain several task tables. Missing rows can only be
        # decided after its last table, otherwise the first table reports every
        # record carried by the second as absent.
        later_same_section = any(
            t["heading"] == heading and t["table_index"] > table["table_index"]
            and t["readable"] for t in board.task_tables())
        if not later_same_section:
            section_seen = {ops.strip_handle(r["values"].get("id", ""))
                            for t in board.task_tables()
                            if t["heading"] == heading and t["readable"]
                            for r in t["row_items"]}
            report["rows_not_on_board"].extend(sorted(wanted - section_seen))
        # `order` is only a claim until something can be shown to disagree with
        # it. A record with no `order` at all — a store written before the
        # field existed — is not a disagreement, so it is skipped rather than
        # sorted to the front.
        graded = [t for t in in_line_order if by_id[t].get("order") is not None]
        if graded != sorted(graded, key=lambda t: by_id[t]["order"]):
            report["sections_out_of_stored_order"].append(
                {"heading": heading, "on_the_board": graded,
                 "in_the_store": sorted(graded,
                                        key=lambda t: by_id[t]["order"])})
        report["sections"].append({"heading": heading, "rows": len(seen)})
    return {"lines": lines, "rows": rows, "report": report,
            "records": {r["id"]: r for r in records}}


def render(board, records: list[dict], ops) -> tuple[str, dict]:
    """`perry/tasks.jsonl` → the text of `BOARD.md`. Byte-for-byte is the bar."""
    p = plan(board, records, ops)
    out = list(p["lines"])
    for i, desc in p["rows"].items():
        out[i] = render_line(desc, p["records"][desc["id"]])
    return "\n".join(out), p["report"]


__all__ = ["STORED", "FIELD_BY_COLUMN", "board_order", "cell_text",
           "describe_cell", "load_store", "plan", "record", "render",
           "render_line", "store_path", "store_text", "markdown_tables",
           "validate_records"]
