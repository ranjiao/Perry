#!/usr/bin/env python3
"""TASK-325 — the summary census, and the structural predicates behind it.

Run: `python3 perry/evidence/2026-09/TASK-325-census.py [--root .]`

This is the instrument the TASK-325 result quotes. It is committed rather than
pasted into the result document for the reason TASK-299 exists: a number
produced by a command nobody can re-run is an assertion, not a measurement.

**It shares no code with `bin/perry-lint`, deliberately.** The lint check is
the product; this is the independent second count. If the two disagree, that
disagreement is the finding — which is the same posture `perry-tasks verify`
takes against `perry-lint`'s drift census.

The predicates below are the SAME FOUR the lint check pins, restated here so a
reader can see what is and is not being measured without reading the linter:

  missing        the field is absent or whitespace-only
  repeats-title  summary and title are equal after case/punctuation folding,
                 or one is a prefix of the other
  no-sentence    no sentence-terminating mark anywhere in the value
  fragment       fewer than MIN_WORDS whitespace-separated words

And the properties deliberately NOT measured, each with its reason:

  opens-with-an-id   10 of the 49 summaries on this board open with a bare
                     `DESIGN-012 I1` / `USER-908` style citation, and ALL TEN
                     are good summaries. The TASK-325 spec proposed this
                     predicate; the corpus refutes it. A leading citation is
                     this project's house style, not a defect.
  contains ids,      39 of 49 carry an id, a path or a backtick somewhere.
  paths, backticks   That is a feature of a summary that cites its source.
  readability        No wording, vocabulary, hedge-word or reading-level test
                     of any kind. Two guards on this project have already lost
                     to a denylist over English; this one does not try.
  accuracy           Nothing here checks that a summary is TRUE of its row.
                     No structural test can.
  closed rows        Out of scope by the spec. History is not backfilled.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CLOSED = {"done", "dropped"}

#: Fewer words than this and the value cannot be an explanation of anything.
#: The floor is set against the corpus rather than by taste: the SHORTEST
#: genuine summary on this board is 22 words, so 5 leaves better than 4x
#: headroom. It is the one predicate here that is a proxy rather than a
#: structural fact, and it is deliberately set far below the real population
#: so that it can only ever fire on a stub.
MIN_WORDS = 5

_FOLD = re.compile(r"[^0-9a-z]+")
_SENTENCE = re.compile(r"[.!?。！？]")


def fold(s: str) -> str:
    """Case- and punctuation-insensitive comparison key."""
    return _FOLD.sub(" ", s.lower()).strip()


def shape_findings(title: str, summary: str) -> list[str]:
    """Every structural rule the value breaks. Empty means it passes."""
    s = (summary or "").strip()
    if not s:
        return ["missing"]
    out = []
    ft, fs = fold(title or ""), fold(s)
    if ft and fs == ft:
        out.append("repeats-title")
    elif ft and (fs.startswith(ft) or ft.startswith(fs)):
        out.append("repeats-title")
    if not _SENTENCE.search(s):
        out.append("no-sentence")
    if len(s.split()) < MIN_WORDS:
        out.append("fragment")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--list-blank", action="store_true",
                    help="print every open row carrying no summary")
    a = ap.parse_args(argv)

    store = Path(a.root).expanduser().resolve() / "perry" / "tasks.jsonl"
    if not store.exists():
        store = Path(a.root).expanduser().resolve() / "tasks.jsonl"
    if not store.exists():
        print(f"no tasks.jsonl under {a.root}", file=sys.stderr)
        return 2

    rows = [json.loads(l) for l in store.read_text().split("\n") if l.strip()]
    open_rows = [r for r in rows if (r.get("status") or "") not in CLOSED]

    def carried(r):
        return bool((r.get("summary") or "").strip())

    print(f"store          : {store}")
    print(f"rows           : {len(rows)} total · {len(open_rows)} open · "
          f"{len(rows) - len(open_rows)} closed (out of scope)")
    print(f"carrying one   : {sum(1 for r in rows if carried(r))} of {len(rows)} all · "
          f"{sum(1 for r in open_rows if carried(r))} of {len(open_rows)} open")
    print(f"open and blank : {sum(1 for r in open_rows if not carried(r))}")

    tally: dict[str, int] = {}
    shaped: list[tuple[str, list[str]]] = []
    for r in open_rows:
        hits = shape_findings(r.get("title") or "", r.get("summary") or "")
        for h in hits:
            tally[h] = tally.get(h, 0) + 1
        if hits and hits != ["missing"]:
            shaped.append((r["id"], hits))
    print("\nopen rows by rule:")
    for k in ("missing", "repeats-title", "no-sentence", "fragment"):
        print(f"  {k:<14} {tally.get(k, 0)}")
    if shaped:
        print("\nshape failures on rows that DO carry a summary:")
        for tid, hits in shaped:
            print(f"  {tid}: {', '.join(hits)}")
    else:
        print("\nno shape failure on any row that carries a summary "
              "(the blanks are the whole population today)")

    if a.list_blank:
        print("\nopen rows carrying no summary:")
        for r in open_rows:
            if not carried(r):
                print(f"  {r['id']}  {(r.get('title') or '')[:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
