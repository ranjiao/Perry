"""No input class reaches `internal` (NN-K6; round 3, F-internal).

A lone surrogate in a text field used to return `internal`, exit 3. The
classes below were enumerated by driving every command with them and by
swapping the JSON type of every node of a template and of each command's
input. Each is now a typed refusal, and every envelope is valid UTF-8 JSON.

| class | where it enters | answer |
|---|---|---|
| a lone surrogate escaped in the JSON | any string or key in `--input` | input_invalid |
| a non-finite number (1e400) | any number in `--input` | input_invalid |
| an integer outside sqlite's 64 bits | any integer in `--input` | input_invalid |
| nesting past 64 levels, or past the parser's recursion limit | `--input` | input_invalid |
| bytes that are not UTF-8 | stdin, an `@file` | input_invalid |
| an undecodable byte in argv | any argument | usage |
| a variable that is not valid UTF-8 | PERRY_STORE, PERRY_PROJECT | usage |
| a symlink loop, `~` naming no user | --root, --store, `@file` | io_error |
| a working directory that is gone, or not UTF-8 | the walk, relative paths | io_error |
| a list or object where a template name belongs | template validate / apply | template_invalid |
| the same classes in an export line | import | export_invalid |
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest

from support import (ACTOR, TEMPLATE, WRAPPER, Sandbox, clean_env,
                     mkdtemp)

from perry_kernel import template as tpl
from perry_kernel.values import MAX_DEPTH

SURROGATE = "\ud800"


def envelope_ok(testcase, r):
    """Valid UTF-8, valid strict JSON, and never exit 3."""
    r.out.encode("utf-8")
    r.err.encode("utf-8")

    def strict(name):
        raise ValueError(f"{name} is not JSON")

    json.loads(r.out, parse_constant=strict)
    testcase.assertNotEqual(r.code, 3, r)


def nested(depth: int) -> str:
    return "[" * depth + "1" + "]" * depth


class TestJsonInput(unittest.TestCase):

    def setUp(self):
        self.sb = Sandbox(self).ready()
        self.item = self.sb.create()

    def refused(self, words, text, code="input_invalid", exit_code=2):
        r = self.sb.run(*words, data=text)
        envelope_ok(self, r)
        self.assertEqual((r.code, r.code_name), (exit_code, code), r)
        return r

    def test_a_lone_surrogate_anywhere(self):
        write = {"actor": ACTOR, "type": "widget",
                 "fields": {"bench": "north"}}
        cases = [
            (("item", "create"), {**write, "note": SURROGATE}),
            (("item", "create"), {**write, "fields": {
                "bench": "north", "label": "a" + SURROGATE}}),
            (("item", "create"), {**write, "fields": {SURROGATE: 1}}),
            (("item", "create"), {**write, SURROGATE: 1}),
            (("item", "create"), {**write, "actor": {
                **ACTOR, "name": SURROGATE}}),
            (("attach", "add"), {"actor": ACTOR, "id": self.item,
                                 "ref": SURROGATE}),
            (("item", "get"), {"id": SURROGATE}),
            (("query",), {"type": "widget", "where": {SURROGATE: [1]}}),
            (("template", "validate"), {"template": {**TEMPLATE,
                                                     "name": SURROGATE}}),
        ]
        for words, data in cases:
            # Escaped in the JSON it is input; raw in argv it can only have
            # come from an undecodable byte, which is a bad argument.
            for text, code in ((json.dumps(data), "input_invalid"),
                               (json.dumps(data, ensure_ascii=False),
                                "usage")):
                with self.subTest(command=words, code=code):
                    r = self.refused(words, text, code=code)
                    self.assertNotIn(SURROGATE, r.out)
        self.assertEqual(self.sb.ok("query")["total"], 1)

    def test_numbers(self):
        for text in ('{"limit": 1e400}', '{"limit": -1e400}',
                     '{"limit": 9223372036854775808}',
                     '{"limit": -9223372036854775809}',
                     '{"limit": 1' + "0" * 5000 + "}"):
            with self.subTest(text=text[:40]):
                self.refused(("query",), text)
        r = self.refused(("template", "apply"), json.dumps({
            "actor": ACTOR, "template": {**TEMPLATE, "version": 2 ** 63}}))
        self.assertEqual(r.details["key"], "template.version")
        ok = self.sb.run("template", "apply", data={
            "actor": ACTOR, "template": {**TEMPLATE, "version": 2 ** 63 - 1}})
        self.assertTrue(ok.ok, ok)

    def test_nesting(self):
        self.refused(("query",), '{"ids": ' + nested(100000) + "}")
        self.refused(("query",), '{"ids": ' + nested(MAX_DEPTH) + "}")
        r = self.sb.run("query", data='{"ids": ' + nested(MAX_DEPTH - 3) + "}")
        self.assertEqual(r.code_name, "input_invalid")  # wrong type, not depth
        self.assertIn("array", r.env["error"]["message"])

    def test_bytes_that_are_not_utf8(self):
        path = self.sb.tmp / "in.json"
        path.write_bytes(b'{"id": "\xff"}')
        r = self.refused(("item", "get"), f"@{path}")
        self.assertEqual(r.details["byte"], 8)
        proc = subprocess.run(
            [str(WRAPPER), "item", "get", "--input", "-", "--store",
             str(self.sb.store), "--root", str(self.sb.root)],
            input=b'{"id": "\xfe\xff"}', capture_output=True,
            env=clean_env(), timeout=60)
        env = json.loads(proc.stdout)
        self.assertEqual((proc.returncode, env["error"]["code"]),
                         (2, "input_invalid"), env)


class TestOtherChannels(unittest.TestCase):
    """argv, the environment and the file system, through the executable."""

    def run_bytes(self, argv, env=None, cwd=None):
        proc = subprocess.run([os.fsencode(str(WRAPPER)), *argv],
                              capture_output=True, env=env or clean_env(),
                              cwd=cwd, timeout=60)
        out = proc.stdout.decode("utf-8")
        err = proc.stderr.decode("utf-8")
        self.assertNotIn("Traceback", err)
        env_ = json.loads(out)
        self.assertNotEqual(proc.returncode, 3, out + err)
        return proc.returncode, env_

    def test_an_undecodable_argument(self):
        sb = Sandbox(self).ready()
        for argv in ([b"query", b"--store", b"/tmp/\xff.db"],
                     [b"item", b"get", b"--input", b'{"id": "\xff"}',
                      b"--store", os.fsencode(str(sb.store))],
                     [b"\xff"]):
            with self.subTest(argv=argv):
                code, env = self.run_bytes(argv)
                self.assertEqual((code, env["error"]["code"]), (2, "usage"),
                                 env)

    def test_an_undecodable_environment_variable(self):
        sb = Sandbox(self).ready()
        for name in ("PERRY_STORE", "PERRY_PROJECT"):
            with self.subTest(variable=name):
                env = {os.fsencode(k): os.fsencode(v)
                       for k, v in clean_env().items()}
                env[name.encode()] = b"/tmp/\xff"
                if name == "PERRY_PROJECT":
                    argv = [b"init", b"--input", json.dumps(
                        {"actor": ACTOR, "state_root": "state"}).encode(),
                        b"--store", os.fsencode(str(sb.store))]
                else:
                    argv = [b"query", b"--root", os.fsencode(str(sb.root))]
                code, out = self.run_bytes(argv, env=env)
                self.assertEqual((code, out["error"]["code"]), (2, "usage"),
                                 out)
                self.assertEqual(out["error"]["details"]["variable"], name)

    def test_paths_that_cannot_resolve(self):
        sb = Sandbox(self).ready()
        loop = sb.tmp / "loop"
        loop.symlink_to(loop)
        init = {"actor": ACTOR, "state_root": "state"}
        for words, extra, kw in (
                (("init",), ["--root", str(loop)], dict(root=False,
                                                        data=init)),
                (("query",), ["--store", str(loop)], dict(store=False)),
                (("init",), ["--root", "~no-such-user-here/x"],
                 dict(root=False, data=init)),
                (("item", "get"), ["--input", f"@{loop}"], {})):
            with self.subTest(flags=extra):
                r = sb.run(*words, flags=extra, **kw)
                envelope_ok(self, r)
                self.assertEqual((r.code, r.code_name), (1, "io_error"), r)

    def test_a_working_directory_that_is_gone(self):
        gone = mkdtemp(self) / "gone"
        gone.mkdir()
        script = (f"import os, subprocess, sys; os.chdir({str(gone)!r}); "
                  f"os.rmdir({str(gone)!r}); "
                  f"sys.exit(subprocess.run([{str(WRAPPER)!r}, 'query', "
                  f"'--store', 'relative.db']).returncode)")
        proc = subprocess.run([sys.executable, "-c", script],
                              capture_output=True, text=True,
                              env=clean_env(), timeout=60)
        self.assertNotIn("Traceback", proc.stderr)
        env = json.loads(proc.stdout)
        self.assertEqual((proc.returncode, env["error"]["code"]),
                         (1, "io_error"), env)

    def test_a_working_directory_that_is_not_utf8(self):
        base = mkdtemp(self)
        odd = os.path.join(os.fsencode(str(base)), b"odd-\xff")
        try:
            os.mkdir(odd)
        except OSError as exc:  # a file system that insists on UTF-8 names
            self.skipTest(f"cannot make a non-UTF-8 directory name: {exc}")
        os.mkdir(os.path.join(odd, b".perry"))
        code, env = self.run_bytes([b"query", b"--store", b"/tmp/never.db"],
                                   cwd=odd)
        self.assertEqual((code, env["error"]["code"]), (1, "io_error"), env)


class TestTheTemplateValidatorNeverRaises(unittest.TestCase):
    """Every node of the fixture template swapped for every JSON type."""

    SWAPS = (None, 7, 1.5, "x", [], {}, True, [None], {"x": 1})

    def paths(self, value, path=()):
        yield path
        if isinstance(value, dict):
            for k, v in value.items():
                yield from self.paths(v, path + (k,))
        elif isinstance(value, list):
            for n, v in enumerate(value):
                yield from self.paths(v, path + (n,))

    def test_every_swap_is_valid_or_a_list_of_problems(self):
        tried = 0
        for path in self.paths(TEMPLATE):
            for repl in self.SWAPS:
                candidate = copy.deepcopy(TEMPLATE)
                if path:
                    target = candidate
                    for step in path[:-1]:
                        target = target[step]
                    target[path[-1]] = repl
                else:
                    candidate = repl
                tried += 1
                with self.subTest(path=path, value=repl):
                    problems = tpl.validate(candidate)
                    self.assertIsInstance(problems, list)
                    if not problems:
                        tpl.normalize(candidate)
        self.assertGreater(tried, 1000)

    def test_an_unhashable_name_is_a_problem_not_a_type_error(self):
        for path in (("types", "widget", "initial"),
                     ("types", "widget", "transitions", "polish", "to"),
                     ("types", "widget", "fields", "label", "kind"),
                     ("types", "widget", "transitions", "start", "guards", 0,
                      "relation")):
            for repl in ([], {}):
                candidate = copy.deepcopy(TEMPLATE)
                target = candidate
                for step in path[:-1]:
                    target = target[step]
                target[path[-1]] = repl
                with self.subTest(path=path, value=repl):
                    problems = tpl.validate(candidate)
                    self.assertTrue(problems)
        candidate = copy.deepcopy(TEMPLATE)
        candidate["types"]["widget"]["fields"]["size"]["values"] = 7
        self.assertTrue(tpl.validate(candidate))


class TestExportLines(unittest.TestCase):
    """The same classes arriving through `import`: export_invalid, never
    `internal` and never `store_corrupt`, which would blame the store."""

    def planted(self, mutate):
        from test_relations import replay
        sb = Sandbox(self).ready()
        sb.create()
        sb.ok("export")
        return replay(self, sb, mutate)

    def test_each_class(self):
        def line(n, fn):
            def mutate(items, events):
                obj = json.loads(events[n])
                fn(obj)
                events = list(events)
                events[n] = json.dumps(obj) + "\n"
                return items, events
            return mutate

        def deep(o):
            o["note"] = None
            o["warnings"] = json.loads(nested(MAX_DEPTH + 5))

        cases = {
            "surrogate": line(2, lambda o: o.update(note=SURROGATE)),
            "huge id": line(2, lambda o: o.update(items=["W-" + "9" * 30])),
            "deep": line(2, deep),
            "state is a list": line(2, lambda o: o["changes"][1].update(
                after=[])),
            "actor is not an actor": line(2, lambda o: o.update(
                actor={"x": 1})),
            "hash is not a hash": line(2, lambda o: o["changes"].append(
                {"key": "attach:a", "before": None,
                 "after": {"hash": ["x"]}})),
        }
        for name, mutate in cases.items():
            with self.subTest(name):
                r = self.planted(mutate)
                envelope_ok(self, r)
                self.assertEqual((r.code, r.code_name), (1, "export_invalid"),
                                 r)

    def test_a_line_nested_past_the_parser_limit(self):
        def mutate(items, events):
            return items, events + ['{"x": ' + nested(100000) + "}\n"]
        r = self.planted(mutate)
        envelope_ok(self, r)
        self.assertEqual(r.code_name, "export_invalid", r)


if __name__ == "__main__":
    unittest.main()
