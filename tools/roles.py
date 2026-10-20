#!/usr/bin/env python3
"""Read role cards and the additive escalation union; no writes or task state.

Usage: python3 tools/roles.py --root /absolute/project
See helper-contracts.md for the versioned output and interpretation limits.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import safety_policy

from host_common import bullets, explicit_directory, field, section, strip_comments, owned_markdown


def line_fragments(line: str) -> list[str]:
    if "{{" in line:
        return []
    return list(dict.fromkeys(f.strip().lower() for f in re.findall(r"`([^`]+)`", line)
                             if len(f.strip()) > (2 if f.strip().isascii() else 1)))


def escalation(lines: list[str]) -> dict:
    return {"lines": lines,
            "fragments": list(dict.fromkeys(f for line in lines for f in line_fragments(line))),
            "unextractable": [line for line in lines if not line_fragments(line)]}


def parse_card(path: Path, root: Path) -> dict:
    text = strip_comments(path.read_text(encoding="utf-8"))
    headings = re.findall(r"^##\s+(.+?)\s*$", text, re.M)
    for required in ('May touch', 'Must escalate'):
        if headings.count(required) != 1 or not section(text, required).strip():
            raise ValueError('one nonempty role safety section required: ' + required)
    heading = re.search(r"^#\s+(.+)$", text, re.M)
    name = heading.group(1).strip() if heading else path.stem
    name = re.sub(r"^Role\s*[·:：-]\s*", "", name)
    loads = section(text, "Loads")
    topics = {}
    for label in ("knowledge", "pack"):
        topics[label] = [t.strip().strip("*`") for line in bullets(loads)
                         if re.match(rf"{label}\s*[:：]", line, re.I)
                         for t in re.split(r"[,，;；]", re.split(r"[:：]", line, 1)[1])
                         if t.strip() and "{{" not in t]
    return {"name": name, "path": path.relative_to(root).as_posix(),
            "accepted_by": field(text, "Accepted by"), "default_rung": field(text, "Default rung"),
            "executors": field(text, "Executors"), "context": section(text, "Context"),
            "may_touch": section(text, "May touch"), "loads": topics,
            "must_escalate": escalation(bullets(section(text, "Must escalate")))}


def report(root: Path) -> dict:
    root = root.resolve()
    paths, errors = owned_markdown(root, root/'.perry/roles')
    cards = []
    for path in paths:
        try:
            cards.append(parse_card(path, root))
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append({'path':str(path),'code':'role_unreadable','error':str(exc)})
    try:
        policy = safety_policy.read(root)
        policy_source = {'path':policy['path'],'sha256':policy['sha256']}
        policy_fragments = policy['patterns']
    except (OSError, ValueError) as exc:
        policy_source = {'path':str(root/'.perry/safety.json'),'sha256':None}
        policy_fragments = []
        errors.append({'path':'.perry/safety.json','code':'policy_unavailable','error':str(exc)})
    fragments = list(dict.fromkeys(policy_fragments + [f for c in cards for f in c['must_escalate']['fragments']]))
    for card in cards:
        for key in ("accepted_by", "default_rung"):
            if not card[key] or "{{" in card[key]:
                errors.append({"path": card["path"], "code": "missing_" + key})
        if card["default_rung"] and not re.fullmatch(r"V[1-6]", card["default_rung"]):
            errors.append({"path": card["path"], "code": "invalid_default_rung"})
        for line in card["must_escalate"]["unextractable"]:
            errors.append({"path": card["path"], "code": "unextractable_escalation", "line": line})
    return {"contract": "perry-roles/read/2.0", "semantics": [], "project_root": str(root),
            "declared": len(cards), "cards": cards, "policy_source": policy_source,
            "escalation_union": fragments, "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    args = parser.parse_args(argv)
    try:
        result = report(explicit_directory(args.root))
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
