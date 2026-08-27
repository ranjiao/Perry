"""Two-way key diff: what each contract DOCUMENT declares vs what the tool EMITS.

**The number KR-O2.4 asks for and nothing computed.** The KR's metric is a
count of *contract-payload keys documented but not emitted, or emitted but not
documented*. `tests/test_contract_invariance.py` is the nearest thing and it
answers a different question: it records the payload's SHAPE and compares it to
a recorded baseline, so a key that is emitted and undocumented passes cleanly,
and a key documented and never emitted was never in the baseline to begin with.
The seven other modules that read a contract file each assert that **one named
field** appears in the prose. Seven spot checks are not a count.

**Discovery is a glob, on purpose.** `schema/*-contract.md`. A hand-written
list of contracts is the failure this check exists to prevent — the KR text
says "all three contracts" and there are **five**. The run prints how many
files it found, so a sixth cannot be silently skipped.

## How a document is read

Every contract page states its own invocation in its `# ` heading, inside
backticks: ``perry-task list --json``, ``perry-state --json § roles``. That is
the command this check runs, and the `§ <key>` suffix selects the subtree the
page is about. Nothing here holds a table of tools.

Declared paths come from two places, both mechanical:

1. **The `jsonc` payload sketch.** Comments and `/* below */` placeholders are
   stripped and the rest is parsed as JSON, so nesting survives — these are
   real paths, not a bag of names.
2. **The key tables.** A row whose first cell is nothing but backticked
   identifiers (``| `id` | string | … |``, ``| `from`, `to` | string | … |``)
   declares those keys. A first cell carrying prose is not a key table, which
   is how the changelog and `decide § Reading is tolerant` tables stay out.

A table usually says nothing about *where* its keys hang. That is resolved by
matching the table's key set against the emitted containers and taking the best
fit — with a floor, so a single coincidental overlap cannot claim a table. **A
table that finds no container is reported by name as unassigned rather than
dropped**: a collection this project's own state leaves empty (`intake.rows`,
`asks.items`, `roles.cards`) offers no children to match against, and a
silently narrowed denominator is worse than a smaller one that is stated.

**Unless the heading says where.** A heading may name the collections its table
describes, as backticked `name[]` references:

    #### The idle entry — `in_progress_with_no_live_run[]` and `review_idle[]`

and then the table is placed on **every** collection named and inference is not
consulted at all. This is the one thing best-fit matching structurally cannot
do: two collections with the same entry shape are the same key set, so scoring
either splits the table onto one of them or — because neither wins — refuses it
outright. Six documented keys sat in `unassigned` for three contract versions
for exactly that reason, and `cleared_items[]` beside `items[]` could not be
documented at all without copying its key table.

The syntax is narrow on purpose, because the value of this check is that it
refuses to guess:

- the reference must carry `[]`. A bare backticked `` `asks` `` in a heading is
  the section's topic, not a statement about the table below it — and reading
  it as one would hang `asks[].id` off an object whose keys are `items` and
  `open`, inventing findings.
- the name must resolve to exactly one emitted collection, by its own last
  segment (`` `semantics[]` `` → `semantics[]`, `` `depends_on_resolved[]` ``
  → `tasks[].depends_on_resolved[]`). A full path may be written instead.
- a name that resolves to **nothing**, or to more than one collection, is a
  **failure reported by name** (`named_no_such_collection`) and the whole table
  stays `unassigned`. An author who stated where a table hangs and got it wrong
  is told so; a page that names nothing keeps the old inference and its floors.

## What the two numbers mean

- `documented_not_emitted` — the page promises a key the payload does not carry.
- `emitted_not_documented` — the payload carries a key the page never declares.

Neither is asserted to be zero. This check measures the gap; closing it is
whatever rows the measurement produces. The baseline in
`tests/fixtures/contract-key-parity.json` is what makes the number comparable
across runs by someone who was not here.

Run:

    python3 tests/contract_key_parity.py             # per-contract counts
    python3 tests/contract_key_parity.py --json      # the same, machine-readable
    python3 tests/contract_key_parity.py --record    # rewrite the baseline
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
GLOB = "schema/*-contract.md"
BASELINE = ROOT / "tests" / "fixtures" / "contract-key-parity.json"

#: A key, or a dotted path of keys. Lower-case with underscores, which is every
#: key in every one of these payloads and is not any of the prose, versions
#: (`1.11`) or ids (`ADR-002`) that also appear in a first table cell.
IDENT = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")

#: The invocation, out of the page's own `# ` heading. `§ roles` selects the
#: subtree of a larger payload that the page is the contract for.
SUBTREE = re.compile(r"§\s*([A-Za-z_][A-Za-z0-9_]*)")

#: `perry-task/list/1.11`. The page states it either in the heading or in the
#: `> Contract:` line; the first occurrence is the page's own.
CONTRACT_ID = re.compile(r"`(perry-[a-z]+/[a-z]+/\d+\.\d+)`")

#: A table row's first cell must be backticked names and nothing else. What is
#: allowed BETWEEN them: commas, slashes and whitespace.
SEPARATORS = re.compile(r"[\s,/]+")

#: A collection a HEADING names for the table beneath it: a backticked
#: ``name[]`` or ``parent.name[]``. The `[]` is the whole syntax — it is what
#: separates *these are the entries of that collection* from a mention of a
#: section by name, and the difference is not cosmetic: ``| `asks` — `##
#: User Input Queue` |`` names the section an entry table belongs to, while the
#: entries themselves hang under `asks.items[]`.
NAMED_COLLECTION = re.compile(r"`([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*)\[\]`")


# ---------------------------------------------------------------- the payload

def paths(value, prefix: str = "") -> dict[str, str]:
    """Every field path in a payload, with the type at it.

    Lists collapse to their first element, exactly as
    `test_contract_invariance.shape` does: a contract promises what an entry
    looks like, not how many there are.
    """
    out: dict[str, str] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{prefix}.{key}" if prefix else key
            out[here] = type(child).__name__
            out.update(paths(child, here))
    elif isinstance(value, list) and value:
        out.update(paths(value[0], f"{prefix}[]"))
    return out


def empty_lists(value, prefix: str = "") -> set[str]:
    """List paths with no item to inspect. Their entry shape is unobservable in
    this run — which is a different fact from a key being absent, and the two
    must not be reported as one."""
    out: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            out.update(empty_lists(child, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list):
        if not value:
            out.add(prefix)
        else:
            out.update(empty_lists(value[0], f"{prefix}[]"))
    return out


def under_empty(path: str, empties: set[str]) -> str:
    """The empty list `path` sits inside, or `""`."""
    for parent in empties:
        if path.startswith(f"{parent}[]."):
            return parent
    return ""


# --------------------------------------------------------------- the document

def strip_comments(block: str) -> str:
    """`// …` to end of line and `/* … */` inline, so the sketch parses.

    Both are outside strings in every one of these blocks — the sketches carry
    no URL and no path with a `//` in it — and this is asserted by the parse
    succeeding, not assumed: a block that does not parse is reported, never
    skipped.
    """
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    return re.sub(r"//[^\n]*", "", block)


def sketch_paths(text: str) -> tuple[dict[str, str], list[str]]:
    """Paths from the page's ```jsonc``` payload sketch, and any block that
    would not parse."""
    found: dict[str, str] = {}
    unparsed: list[str] = []
    for tag, block in re.findall(r"^```(json[c]?)\n(.*?)^```", text,
                                 flags=re.S | re.M):
        body = strip_comments(block).strip().rstrip(",")
        if not body.startswith("{"):
            # `schema/roles-list-contract.md` sketches its own subtree as a
            # bare `"roles": { … }` member rather than a whole object.
            body = "{" + body + "}"
        try:
            found.update(paths(json.loads(body)))
        except json.JSONDecodeError as exc:
            unparsed.append(f"{tag} block: {exc}")
    return found, unparsed


def key_tables(text: str) -> list[tuple[str, list[str]]]:
    """`(heading, keys)` for every table whose first column is keys.

    The heading is the nearest one above the table, and is only ever used to
    NAME an unassigned table in the report — never to place it. Placing by
    heading would mean inventing a mapping from English to payload structure,
    which is the hand-written list this check refuses to carry.
    """
    tables: list[tuple[str, list[str]]] = []
    heading, current, fenced = "", [], False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            names = re.findall(r"`([^`]+)`", cells[0])
            residue = SEPARATORS.sub("", re.sub(r"`[^`]+`", "", cells[0]))
            if names and not residue and all(IDENT.match(n) for n in names):
                current.extend(names)
        elif current:
            tables.append((heading, current))
            current = []
    if current:
        tables.append((heading, current))
    return tables


def containers(emitted: dict[str, str], empties: set[str]) -> dict[str, set[str]]:
    """Every path a key could hang under, with the child keys seen there.

    The root is `""`. An empty list contributes a container with no children —
    it exists, and that is why a table matching nothing can be reported as
    *unobservable here* rather than as an error.
    """
    out: dict[str, set[str]] = {"": set()}
    for path in emitted:
        parent, _, leaf = path.rpartition(".")
        out.setdefault(parent, set()).add(leaf)
    for parent in empties:
        out.setdefault(f"{parent}[]", set())
    return out


class Placement(NamedTuple):
    """Where a key table's keys hang.

    `boxes` empty means unplaced — the caller reports the table by name rather
    than dropping it. `named` says the heading stated the containers, so the
    reader of a report can tell a declaration from an inference. `problems`
    are collections the heading named and the payload does not carry; they are
    a failure to report, never a reason to fall back to guessing.
    """

    boxes: list[str]
    named: bool
    problems: list[str]


def named_boxes(heading: str, boxes: dict[str, set[str]]) -> Placement:
    """The collections a heading names, resolved against the payload.

    A name resolves by its **last segment**, so a page may write the short
    ``` `depends_on_resolved[]` ``` for `tasks[].depends_on_resolved[]` the way
    its prose already does — or the whole path, if that is what disambiguates.
    Anything that resolves to no collection, or to several, is a problem
    reported by name: the author said where the table hangs, and a statement
    that does not check out is worth more as an error than as a silent guess.
    """
    found: list[str] = []
    problems: list[str] = []
    for name in NAMED_COLLECTION.findall(heading):
        target = f"{name}[]"
        hits = sorted(b for b in boxes
                      if b == target or b.endswith(f".{target}"))
        if len(hits) == 1:
            found.append(hits[0])
        elif not hits:
            problems.append(f"`{target}` is named by the heading and the "
                            f"payload carries no such collection")
        else:
            problems.append(f"`{target}` is named by the heading and matches "
                            f"{len(hits)} collections: " + ", ".join(hits))
    return Placement([] if problems else found,
                     bool(found or problems), problems)


def place(keys: list[str], boxes: dict[str, set[str]],
          heading: str = "") -> Placement:
    """The containers a key table describes.

    **A heading that names them wins outright.** ``#### The idle entry —
    `in_progress_with_no_live_run[]` and `review_idle[]` `` places its six rows
    on both arrays, and no amount of scoring could have: the two have the same
    entry shape by design — "one shape for both, so a consumer needs one code
    path" — which makes them indistinguishable to a matcher and, being tied,
    refused. Inference is not consulted when the heading has spoken, and a
    heading that names a collection the payload lacks is a reported failure
    rather than a fall-through, or the syntax would be a way to *soften* the
    check instead of a way to state a fact.

    With no name to go on, the old inference stands. Scored on **coverage** —
    how much of the table the container accounts for — and broken on
    **precision**, how much of the container the table accounts for. Both are
    needed and neither alone is enough:

    - Coverage alone put `asks`'s eight fields on `tasks[]`, which shares
      `id`, `blocks`, `status` and `priority` with them, and filed four
      phantom findings against the wrong object.
    - Coverage alone cannot separate `asks` from `risks`: both carry `items`
      and `open`, so a table of exactly those two covers each of them
      completely, and precision is what breaks the tie.

    A table that clears neither floor is left unplaced and reported by name.
    """
    stated = named_boxes(heading, boxes)
    if stated.named:
        return stated
    heads = {k.split(".")[0] for k in keys}
    scored = sorted(
        ((len(heads & children) / len(heads),
          len(heads & children) / len(children) if children else 0.0,
          len(heads & children), path)
         for path, children in boxes.items()),
        key=lambda s: (-s[0], -s[1], s[3]))
    best = scored[0]
    runner = scored[1] if len(scored) > 1 else (0.0, 0.0, 0, "")
    if best[0] < 0.6 or best[2] < 2:
        return Placement([], False, [])
    if (best[0], best[1]) == (runner[0], runner[1]):
        return Placement([], False, [])
    return Placement([best[3]], False, [])


# ------------------------------------------------------------------ the check

def discover(schema_home: pathlib.Path | None = None) -> list[pathlib.Path]:
    """Every contract page, by glob.

    `schema_home` exists so a test can point the glob at a directory it built
    — which is how "a sixth contract is picked up without editing this file"
    is proved rather than asserted.
    """
    if schema_home is not None:
        return sorted(schema_home.glob("*-contract.md"))
    return sorted(ROOT.glob(GLOB))


def invoke(text: str) -> tuple[list[str], str]:
    """The argv and subtree key the page's own heading states."""
    heading = text.splitlines()[0]
    quoted = re.search(r"`([^`]+)`", heading)
    if not quoted:
        raise ValueError("the `# ` heading names no command in backticks")
    command = quoted.group(1)
    subtree = SUBTREE.search(command)
    if subtree:
        command = command[:subtree.start()]
    return command.split(), (subtree.group(1) if subtree else "")


def compare(path: pathlib.Path, root: str = "",
            payload: dict | None = None) -> dict:
    """`root` is the PROJECT the tools read. It defaults to Perry's own
    repository, which is the representative fixture — the same choice
    `test_contract_invariance` makes, and for the same reason: it is the only
    checked-in project carrying a real board, a real OKR and a real event log.
    Its own state is what decides which collections are observable, and the
    ones it leaves empty are named in the report rather than dropped.

    `payload` stands in for running the tool, and exists for one case: a
    fixture page describing a payload **no tool on disk emits**. The
    `items[]`-beside-`cleared_items[]` shape is the case a heading naming its
    collections exists to make documentable, and it cannot be built out of a
    real command without adding that array to a real payload — which is
    TASK-040's row, not this one. No page in `schema/` is read this way; the
    glob path always runs the command the page's own heading states.
    """
    text = path.read_text()
    argv, subtree = invoke(text)
    if payload is None:
        proc = subprocess.run(
            [sys.executable, f"bin/{argv[0]}", *argv[1:]]
            + (["--root", root] if root else []),
            capture_output=True, text=True, cwd=ROOT)
        if proc.returncode != 0:
            raise RuntimeError(f"{path.name}: `{' '.join(argv)}` exited "
                               f"{proc.returncode}: {proc.stderr[-300:]}")
        payload = json.loads(proc.stdout)
    if subtree:
        payload = {subtree: payload[subtree]}

    emitted = paths(payload)
    empties = empty_lists(payload)
    boxes = containers(emitted, empties)

    documented, unparsed = sketch_paths(text)
    unassigned: list[str] = []
    misnamed: list[str] = []
    for heading, keys in key_tables(text):
        spot = place(keys, boxes, heading)
        misnamed.extend(f"{heading} § {p}" for p in spot.problems)
        if not spot.boxes:
            unassigned.extend(f"{heading} § {k}" for k in keys)
            continue
        for box in spot.boxes:
            for key in keys:
                documented[f"{box}.{key}" if box else key] = "documented"

    not_observable = {p: under_empty(p, empties) for p in documented
                      if under_empty(p, empties)}
    gone = sorted(p for p in documented
                  if p not in emitted and p not in not_observable)
    extra = sorted(p for p in emitted if p not in documented)
    identifier = CONTRACT_ID.search(text)
    return {
        "contract": identifier.group(1) if identifier else "",
        "file": (path.relative_to(ROOT).as_posix()
                 if path.is_relative_to(ROOT) else str(path)),
        "command": " ".join(argv) + (f" § {subtree}" if subtree else ""),
        "documented": len(documented),
        "emitted": len(emitted),
        "documented_not_emitted": gone,
        "emitted_not_documented": extra,
        "not_observable": {p: f"inside `{v}`, which is empty in this run"
                           for p, v in sorted(not_observable.items())},
        "unassigned": sorted(unassigned),
        "named_no_such_collection": sorted(misnamed),
        "unparsed_sketches": unparsed,
    }


def measure(root: str = "") -> dict:
    files = discover()
    return {
        "glob": GLOB,
        "root": root or ".",
        "contract_files_discovered": len(files),
        "contracts": {c["contract"] or c["file"]: c
                      for c in (compare(f, root) for f in files)},
    }


def report(result: dict) -> str:
    lines = [f"contract files discovered: "
             f"{result['contract_files_discovered']}   ({result['glob']})",
             f"project read: {result['root']}", ""]
    gone = extra = 0
    for name, c in sorted(result["contracts"].items()):
        gone += len(c["documented_not_emitted"])
        extra += len(c["emitted_not_documented"])
        lines.append(f"{name}   {c['file']}")
        lines.append(f"    `{c['command']}`   "
                     f"{c['documented']} documented / {c['emitted']} emitted")
        for label, key in (("documented_not_emitted", "documented_not_emitted"),
                           ("emitted_not_documented", "emitted_not_documented")):
            lines.append(f"    {label}: {len(c[key])}")
            lines.extend(f"        {p}" for p in c[key])
        if c["not_observable"]:
            lines.append(f"    not observable here: {len(c['not_observable'])}")
            for p, why in c["not_observable"].items():
                lines.append(f"        {p} — {why}")
        if c["unassigned"]:
            lines.append(f"    table matched no emitted collection: "
                         f"{len(c['unassigned'])}")
            lines.extend(f"        {p}" for p in c["unassigned"])
        for problem in c.get("named_no_such_collection", []):
            lines.append(f"    HEADING NAMES NO SUCH COLLECTION: {problem}")
        for problem in c["unparsed_sketches"]:
            lines.append(f"    SKETCH DID NOT PARSE: {problem}")
        lines.append("")
    lines.append(f"TOTAL   documented_not_emitted: {gone}   "
                 f"emitted_not_documented: {extra}   "
                 f"(KR-O2.4 metric: {gone + extra})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="machine-readable")
    ap.add_argument("--record", action="store_true",
                    help=f"rewrite {BASELINE.relative_to(ROOT)}")
    ap.add_argument("--root", default="",
                    help="the project to read (default: Perry's own repo)")
    args = ap.parse_args(argv)
    result = measure(args.root)
    if args.record:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(f"recorded {BASELINE.relative_to(ROOT)}")
        return 0
    print(json.dumps(result, indent=2, sort_keys=True) if args.json
          else report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
