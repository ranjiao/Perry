"""argv in, one JSON envelope out (§ 4, § 5.1, NN-K3 to NN-K8).

`invoke` takes the environment, the working directory and stdin as
arguments and returns `(exit, stdout, stderr)`. It reads nothing from the
process it runs in, so a test can call it in-process with a sandboxed
environment. `main` is the one place that touches `sys` and `os.environ`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from . import surface
from .commands import HANDLERS, Ctx
from .errors import KernelError
from .paths import resolve_path
from .values import (SURROGATE, ValueProblem, input_problem, json_type,
                     normalize_actor)

PROG = "perry-kernel"


# ── argv ───────────────────────────────────────────────────────────────────


class Help(Exception):
    def __init__(self, name):
        self.name = name


def _command_words(argv):
    """The non-flag tokens, skipping the values of flags that take one."""
    words, i = [], 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("-") and tok != "-":
            name = tok.split("=", 1)[0]
            if name in surface.VALUE_FLAGS and "=" not in tok:
                i += 1
        else:
            words.append(tok)
        i += 1
    return words


def _match(words):
    for size in (2, 1):
        name = " ".join(words[:size])
        if len(words) >= size and name in surface.BY_NAME:
            return name, words[size:]
    return None, words


def parse(argv):
    """`(command name, flags)`, or raises Help / a usage KernelError."""
    words = _command_words(argv)
    name, rest = _match(words)
    if any(tok in surface.HELP_FLAGS for tok in argv):
        raise Help(name)
    for n, tok in enumerate(argv):
        if SURROGATE.search(tok):
            # An undecodable byte in argv: no path or JSON can carry it.
            raise KernelError("usage", f"argument {n + 1} is not valid UTF-8",
                              {"index": n})
    if name is None:
        attempted = " ".join(words[:2]) if words else ""
        groups = sorted({c.split()[0] for c in surface.BY_NAME})
        raise KernelError("usage",
                          f"unknown command {attempted!r}" if attempted
                          else "no command given",
                          {"commands": list(surface.BY_NAME), "groups": groups})
    legal = surface.flags_of(surface.BY_NAME[name])
    if rest:
        raise KernelError("usage", f"{name} takes no positional argument; got "
                                   f"{rest[0]!r}",
                          {"positional": rest, "legal_flags": legal})
    flags, i = {}, 0
    while i < len(argv):
        tok = argv[i]
        i += 1
        if not tok.startswith("-") or tok == "-":
            continue
        flag, eq, value = tok.partition("=")
        if flag not in legal:
            known = flag in surface.GLOBAL_FLAGS or flag in surface.COMMAND_FLAGS
            raise KernelError("usage",
                              f"{name} does not take {flag}" if known
                              else f"undeclared flag {flag}",
                              {"flag": flag, "legal_flags": legal})
        if flag in surface.VALUE_FLAGS:
            if not eq:
                if i >= len(argv):
                    raise KernelError("usage", f"{flag} needs an argument",
                                      {"flag": flag})
                value = argv[i]
                i += 1
            if value == "":
                raise KernelError("usage", f"{flag} was given an empty value; "
                                           f"if it came from a shell variable, "
                                           f"the variable is unset",
                                  {"flag": flag})
        elif eq:
            raise KernelError("usage", f"{flag} takes no argument",
                              {"flag": flag})
        else:
            value = True
        if flag in flags:
            raise KernelError("usage", f"{flag} is given twice", {"flag": flag})
        flags[flag] = value
    return name, flags


# ── --input ────────────────────────────────────────────────────────────────


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"the key {key!r} appears twice")
        out[key] = value
    return out


def _no_constants(name):
    raise ValueError(f"{name} is not JSON")


def _decode(data, source: str) -> str:
    """Input text. Bytes (stdin, a file) must be UTF-8; a bad byte is input
    that is invalid, not an I/O fault."""
    if isinstance(data, str):
        return data
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise KernelError("input_invalid", f"{source} is not valid UTF-8 "
                                           f"(byte {exc.start})",
                          {"source": source, "byte": exc.start})


def read_input(raw, cwd, stdin):
    if raw is None:
        return {}
    if raw == "-":
        source = "stdin"
        text = _decode(stdin.read() if stdin is not None else "", source)
    elif raw.startswith("@"):
        if raw == "@":
            raise KernelError("usage", "--input @ names no file",
                              {"flag": "--input"})
        path = resolve_path(raw[1:], cwd, "--input")
        try:
            blob = path.read_bytes()
        except OSError as exc:
            raise KernelError("io_error", f"cannot read {path}: "
                                          f"{exc.strerror}",
                              {"path": str(path)})
        source = str(path)
        text = _decode(blob, source)
    else:
        text, source = raw, "--input"
    try:
        data = json.loads(text, object_pairs_hook=_no_duplicates,
                          parse_constant=_no_constants)
    except (ValueError, RecursionError) as exc:
        reason = ("it is nested too deeply" if isinstance(exc, RecursionError)
                  else str(exc))
        raise KernelError("input_invalid", f"{source} is not one JSON object: "
                                           f"{reason}", {"source": source})
    if not isinstance(data, dict):
        raise KernelError("input_invalid", f"{source} is a JSON "
                                           f"{json_type(data)}, not an object",
                          {"source": source})
    problem = input_problem(data)
    if problem:
        raise KernelError("input_invalid", f"{source}: {problem[0]}: "
                                           f"{problem[1]}",
                          {"source": source, "key": problem[0]})
    return data


def _unknown_keys(spec_keys: dict, value: dict, path: str, out: list):
    legal = list(spec_keys)
    for key, sub in value.items():
        if key not in spec_keys:
            out.append({"path": f"{path}{key}", "legal": legal})
            continue
        _unknown_in(spec_keys[key], sub, f"{path}{key}.", out)


def _unknown_in(spec: dict, value, path: str, out: list):
    if spec.get("keys") is not None and isinstance(value, dict):
        _unknown_keys(spec["keys"], value, path, out)
    elif spec.get("items") and isinstance(value, list):
        for n, element in enumerate(value):
            _unknown_in(spec["items"], element, f"{path[:-1]}[{n}].", out)


def _types(spec: dict, value, path: str):
    want = spec["type"]
    got = json_type(value)
    ok = got == want or (want == "number" and got == "integer")
    if not ok:
        raise KernelError("input_invalid", f"{path} is a {got}; it takes a "
                                           f"{want}", {"key": path,
                                                       "type": want})
    if spec.get("actor"):
        return  # its inside is the actor rule's (actor_invalid)
    if want == "object":
        if spec.get("keys") is not None:
            for key, sub in spec["keys"].items():
                if key in value:
                    _types(sub, value[key], f"{path}.{key}")
                elif sub.get("required"):
                    raise KernelError("input_invalid",
                                      f"{path}.{key} is required",
                                      {"key": f"{path}.{key}"})
        elif spec.get("values") is not None:
            for key, sub in value.items():
                _types(spec["values"], sub, f"{path}.{key}")
    elif want == "array" and spec.get("items"):
        for n, element in enumerate(value):
            _types(spec["items"], element, f"{path}[{n}]")


def check_input(cmd: dict, data: dict):
    keys = cmd["input"] or {}
    unknown = []
    _unknown_keys(keys, data, "", unknown)
    if unknown:
        first = unknown[0]
        raise KernelError("unknown_key",
                          f"{cmd['name']} does not declare {first['path']}; "
                          f"legal here: {', '.join(first['legal'])}",
                          {"keys": unknown})
    for key, spec in keys.items():
        if key in data:
            _types(spec, data[key], key)
        elif spec.get("required") and not spec.get("actor"):
            raise KernelError("input_invalid", f"{key} is required",
                              {"key": key})
    if "actor" in keys:
        if "actor" not in data:
            raise KernelError("actor_invalid", f"{cmd['name']} is a write and "
                                               f"needs an actor")

        try:
            return normalize_actor(data["actor"], code="actor_invalid")
        except ValueProblem as exc:
            raise KernelError("actor_invalid", exc.message)
    return None


# ── the envelope ───────────────────────────────────────────────────────────


def envelope(name, *, ok, effect, events=(), store_seq=None, warnings=(),
             result=None, error=None) -> dict:
    return {"ok": ok, "surface": surface.SURFACE, "command": name,
            "effect": effect, "events": list(events), "store_seq": store_seq,
            "warnings": list(warnings), "result": result, "error": error}


def _dump(obj) -> str:
    text = json.dumps(obj, ensure_ascii=False) + "\n"
    if SURROGATE.search(text):
        # A last resort that the input checks keep unreachable: an envelope
        # that UTF-8 cannot carry is escaped, never a traceback (NN-K6).
        text = json.dumps(obj, ensure_ascii=True) + "\n"
    return text


def invoke(argv, environ, cwd, stdin=None, prog: str = PROG):
    """Run one command. Returns `(exit code, stdout text, stderr text)`."""
    name = None
    ctx = None
    try:
        try:
            name, flags = parse(list(argv))
        except Help as h:
            return 0, surface.usage(prog, h.name), ""
        cmd = surface.BY_NAME[name]
        data = read_input(flags.get("--input"), cwd, stdin) \
            if cmd["input"] is not None else {}
        actor = check_input(cmd, data)
        ctx = Ctx(name, flags, data, actor, environ, cwd)
        outcome = HANDLERS[name](ctx)
        env = envelope(name, ok=True, effect=outcome.effect,
                       events=outcome.events,
                       store_seq=(None if name in surface.STORELESS
                                  else ctx.store_seq),
                       warnings=outcome.warnings, result=outcome.result)
        return 0, _dump(env), ""
    except KernelError as exc:
        err = exc
    except Exception as exc:  # NN-K6: no traceback reaches the caller
        err = KernelError("internal", f"{type(exc).__name__}: {exc}",
                          {"type": type(exc).__name__})
    env = envelope(name, ok=False, effect="refused",
                   store_seq=ctx.store_seq if ctx is not None else None,
                   error={"code": err.code, "message": err.message,
                          "details": err.details})
    return err.exit, _dump(env), f"{prog}: {err.code}: {err.message}\n"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    prog = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else PROG
    if not prog or SURROGATE.search(prog):
        prog = PROG
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = None  # the working directory was removed; paths.py says so
    stdin = getattr(sys.stdin, "buffer", sys.stdin)
    code, out, err = invoke(argv, os.environ, cwd, stdin, prog=prog)
    try:
        sys.stdout.buffer.write(out.encode("utf-8"))
        sys.stdout.flush()
        if err:
            sys.stderr.buffer.write(err.encode("utf-8", "backslashreplace"))
            sys.stderr.flush()
    except (BrokenPipeError, OSError):
        pass
    return code
