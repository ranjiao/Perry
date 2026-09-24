"""Shared fixtures for the kernel suite.

Every invocation here names a temporary store (`--store`) and carries
`PERRY_KERNEL_TESTING=1`, so a call that forgot `--store` is refused rather
than reaching the shared store under the git common dir (§ 5.7, NN-K9).
Every actor carries this run's session, which is what `livestore` looks for.

The names in the fixture template are invented and mean nothing to the kernel.
"""

from __future__ import annotations

import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

KERNEL = Path(__file__).resolve().parents[1]
REPO = KERNEL.parent
WRAPPER = REPO / "bin" / "perry-kernel"
PACKAGE = KERNEL / "perry_kernel"
if str(KERNEL) not in sys.path:
    sys.path.insert(0, str(KERNEL))

from perry_kernel import cli  # noqa: E402

SESSION = (os.environ.get("PERRY_KERNEL_TEST_SESSION")
           or f"kernel-suite-{uuid.uuid4().hex[:12]}")
ACTOR = {"kind": "agent", "name": "kernel-suite", "session": SESSION}
HUMAN = {"kind": "human", "name": "Pat", "session": SESSION}
SCRUB = ("PERRY_STORE", "PERRY_PROJECT", "PERRY_KERNEL_TESTING", "GIT_DIR",
         "GIT_COMMON_DIR", "GIT_WORK_TREE")

TEMPLATE = {
    "format": 1, "name": "workshop", "version": 1,
    "types": {
        "widget": {
            "prefix": "W", "digits": 3,
            "states": ["queued", "cutting", "polished", "shipped", "scrapped"],
            "initial": "queued", "terminal": ["shipped", "scrapped"],
            "fields": {
                "size": {"kind": "enum", "values": ["XS", "S", "M", "L"],
                         "ordered": True},
                "bench": {"kind": "enum", "values": ["north", "south"]},
                "fragile": {"kind": "enum", "values": [False, True]},
                "inspector": {"kind": "actor"},
                "ship_by": {"kind": "date"},
                "made_from": {"kind": "ref", "to": ["widget"]},
                "colors": {"kind": "list", "of": {"kind": "text"}},
                "weight_g": {"kind": "number"},
                "pieces": {"kind": "int"},
                "label": {"kind": "text"}},
            "create_guards": [{"kind": "required", "fields": ["bench"]}],
            "transitions": {
                "start": {"from": ["queued"], "to": "cutting", "guards": [
                    {"kind": "relations_closed", "relation": "blocks",
                     "direction": "incoming"},
                    {"kind": "limit", "max": 2, "per": ["bench"],
                     "mode": "warn"}]},
                "polish": {"from": ["cutting"], "to": "polished",
                           "guards": []},
                "ship": {"from": ["polished"], "to": "shipped", "guards": [
                    {"kind": "required", "fields": ["inspector"],
                     "at_least": {"size": "S"}},
                    {"kind": "actor", "actor_kind": "human",
                     "when": {"fragile": [True]}},
                    {"kind": "relations_closed", "relation": "parent",
                     "direction": "incoming"}]},
                "scrap": {"from": ["queued", "cutting", "polished"],
                          "to": "scrapped", "guards": []}}},
        "gauge": {
            "prefix": "G", "states": ["live", "retired"], "initial": "live",
            "terminal": ["retired"],
            "fields": {"reading": {"kind": "metric"}},
            "transitions": {"retire": {"from": ["live"], "to": "retired",
                                       "guards": []}}}},
    "relations": {"pairs_with": {"from": ["widget"], "to": ["widget"]}},
}


def template(**changes) -> dict:
    out = copy.deepcopy(TEMPLATE)
    out.update(changes)
    return out


def clean_env(**extra) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in SCRUB}
    env["PERRY_KERNEL_TESTING"] = "1"
    for k, v in extra.items():  # a None value removes the variable
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    return env


class Result:
    def __init__(self, code: int, out: str, err: str):
        self.code, self.out, self.err = code, out, err
        try:
            self.env = json.loads(out)
        except ValueError:
            self.env = None

    @property
    def ok(self) -> bool:
        return bool(self.env and self.env["ok"])

    @property
    def result(self):
        return self.env["result"] if self.env else None

    @property
    def code_name(self):
        return self.env["error"]["code"] if self.env and self.env["error"] \
            else None

    @property
    def details(self):
        return self.env["error"]["details"] if self.env and self.env["error"] \
            else None

    def __repr__(self):
        return f"Result(exit={self.code}, out={self.out[:400]!r}, " \
               f"err={self.err[:200]!r})"


def mkdtemp(testcase, prefix="kernel-") -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
    testcase.addCleanup(shutil.rmtree, tmp, True)
    return tmp


class Sandbox:
    """A temporary project anchor and a temporary store for one test."""

    def __init__(self, testcase, *, state_root="state", tmp=None):
        self.t = testcase
        self.tmp = tmp or mkdtemp(testcase)
        self.root = self.tmp / "proj"
        (self.root / ".perry").mkdir(parents=True, exist_ok=True)
        self.store = self.tmp / "store.db"
        self.state_root = state_root

    # ── invocation ─────────────────────────────────────────────────────────

    def argv(self, words, data, flags, store, root):
        argv = list(words)
        if data is not None:
            argv += ["--input", data if isinstance(data, str)
                     else json.dumps(data)]
        if store:
            argv += ["--store", str(store if store is not True else self.store)]
        if root:
            argv += ["--root", str(root if root is not True else self.root)]
        return argv + list(flags)

    def run(self, *words, data=None, flags=(), store=True, root=True, env=None,
            cwd=None, stdin=None) -> Result:
        """In-process: `cli.invoke` with an explicit environment."""
        argv = self.argv(words, data, flags, store, root)
        code, out, err = cli.invoke(
            argv, env if env is not None else clean_env(),
            str(cwd or self.root), io.StringIO(stdin or ""))
        return Result(code, out, err)

    def cli(self, *words, data=None, flags=(), store=True, root=True, env=None,
            cwd=None, stdin=None) -> Result:
        """Through the executable, as a separate process."""
        argv = self.argv(words, data, flags, store, root)
        proc = subprocess.run(
            [str(WRAPPER), *argv], input=stdin or "",
            capture_output=True, text=True, cwd=str(cwd or self.root),
            env=env if env is not None else clean_env(), timeout=60)
        return Result(proc.returncode, proc.stdout, proc.stderr)

    def ok(self, *words, **kw) -> dict:
        r = self.run(*words, **kw)
        self.t.assertTrue(r.ok, r)
        self.t.assertEqual(r.code, 0, r)
        return r.result

    def refused(self, code: str, *words, **kw) -> Result:
        r = self.run(*words, **kw)
        self.t.assertFalse(r.ok, r)
        self.t.assertEqual(r.code_name, code, r)
        return r

    # ── common steps ───────────────────────────────────────────────────────

    def init(self, actor=None) -> dict:
        return self.ok("init", data={"actor": actor or ACTOR,
                                     "state_root": self.state_root})

    def apply(self, tpl=None, actor=None) -> dict:
        return self.ok("template apply",
                       data={"actor": actor or ACTOR,
                             "template": tpl or TEMPLATE})

    def ready(self, tpl=None) -> "Sandbox":
        self.init()
        self.apply(tpl)
        return self

    def create(self, type_name="widget", fields=None, *, actor=None,
               **extra) -> str:
        data = {"actor": actor or ACTOR, "type": type_name,
                "fields": fields if fields is not None else (
                    {"bench": "north"} if type_name == "widget" else {})}
        data.update(extra)
        return self.ok("item create", data=data)["item"]["id"]

    def get(self, item_id) -> dict:
        return self.ok("item get", data={"id": item_id})["item"]

    def move(self, item_id, transition, *, actor=None, **extra) -> dict:
        data = {"actor": actor or ACTOR, "id": item_id,
                "transition": transition}
        data.update(extra)
        return self.ok("item move", data=data)

    def events(self, **filters) -> list:
        filters.setdefault("limit", 0)
        return self.ok("events", data=filters)["events"]

    def seq(self) -> int:
        return self.run("events", data={"limit": 1}).env["store_seq"]
