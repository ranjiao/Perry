#!/usr/bin/env python3
"""Generate a Python import map for any directory, without running its code.

JSON goes to stdout by default. --html FILE writes an offline interactive
report outside the analyzed project. See tools/architecture/README.md.
"""
import json
import os
from pathlib import Path
import sys

# Scanning this checkout must not create bytecode inside it.
if __name__ == "__main__":
    sys.dont_write_bytecode = True
import argparse
from architecture.scan import scan
from architecture.report import render
from architecture.model import bind
from architecture.facts import brief
from architecture.analysis import attach, changes
from architecture.audit import compare
from architecture.checkpoint import save as checkpoint, read as read_json, verify

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "checkpoint", "task", "store", "baseline", "review", "verify-checkpoint",
                 "focus", "analysis", "rules", "previous", "architecture", "source-roots", "exclude",
                 "html", "max-file-bytes"):
        parser.add_argument("--" + name)
    for name in ("brief", "json"):
        parser.add_argument("--" + name, action="store_true")
    # Help is always read-only, even alongside malformed or mutating arguments.
    if "--help" in argv or "-h" in argv:
        parser.print_help()
        return 0
    values = vars(parser.parse_args(argv))
    args = {"--" + key.replace("_", "-"): value for key, value in values.items() if value is not None and value is not False}
    parsed = {"seen": set(args)}
    try:
        special = {"--checkpoint", "--task", "--store", "--baseline", "--review", "--verify-checkpoint"}
        if special.intersection(args) and not ({"--checkpoint", "--verify-checkpoint"}.intersection(args)):
            raise ValueError("checkpoint options require --checkpoint")
        if "--checkpoint" in args:
            if not all(k in args for k in ("--task", "--store", "--analysis", "--review")):
                raise ValueError("checkpoint requires --task, --store, --analysis and --review")
            if any(k in parsed["seen"] for k in ("--brief", "--html", "--previous", "--architecture", "--verify-checkpoint")):
                raise ValueError("checkpoint cannot be combined with other output modes")
        if "--verify-checkpoint" in args and any(k in parsed["seen"] for k in
                ("--checkpoint", "--task", "--store", "--baseline", "--review", "--analysis", "--rules", "--html", "--brief", "--architecture", "--previous")):
            raise ValueError("verify-checkpoint is an independent output mode")
        if "--focus" in args and "--brief" not in parsed["seen"]:
            raise ValueError("--focus requires --brief")
        if "--architecture" in args and "--analysis" in args:
            raise ValueError("use --analysis or legacy --architecture, not both")
        if "--brief" in parsed["seen"] and any(k in args for k in ("--html", "--analysis", "--architecture", "--rules", "--previous")):
            raise ValueError("--brief is an independent facts-only output")
        root = Path(args.get("--root", os.environ.get("PERRY_PROJECT") or ".")).resolve(strict=True)
        max_bytes = int(args.get("--max-file-bytes", 2_000_000))
        if max_bytes < 1:
            raise ValueError("--max-file-bytes must be positive")
        output = Path(args["--html"]).resolve() if "--html" in args else None
        if output and output.is_relative_to(root):
            raise ValueError("--html must be outside the analyzed project")
        split = lambda value: [s.strip() for s in value.split(",") if s.strip()]
        data = scan(root, split(args.get("--source-roots", "")),
                    split(args.get("--exclude", "")), max_bytes)
        if "--verify-checkpoint" in args:
            print(json.dumps(verify(data, args["--verify-checkpoint"]), ensure_ascii=True, indent=2))
            return 0
        if "--checkpoint" in args:
            receipt = checkpoint(data, args["--checkpoint"], args["--task"], args["--store"],
                                 read_json(args["--analysis"]), read_json(args["--review"]),
                                 read_json(args["--rules"]) if "--rules" in args else None,
                                 args.get("--baseline"))
            print(json.dumps(receipt, ensure_ascii=True, indent=2))
            return 0
        if "--architecture" in args:
            bind(data, json.loads(Path(args["--architecture"]).read_text(encoding="utf-8")))
        if "--analysis" in args:
            attach(data, json.loads(Path(args["--analysis"]).read_text(encoding="utf-8")))
        if "--rules" in args:
            compare(data, json.loads(Path(args["--rules"]).read_text(encoding="utf-8")))
        if "--previous" in args:
            data["changes"] = changes(data, json.loads(Path(args["--previous"]).read_text(encoding="utf-8")))
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            # Refuse accidental overwrites. Regenerate to a new report path.
            with output.open("x", encoding="utf-8") as stream:
                stream.write(render(data))
            print(f"Report: {output}", file=sys.stderr)
        if "--json" in parsed["seen"] or not output:
            print(json.dumps(brief(data, split(args.get("--focus", ""))) if "--brief" in parsed["seen"] else data, ensure_ascii=True, indent=2))
    except (OSError, ValueError) as exc:
        print(f"perry-architecture: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
