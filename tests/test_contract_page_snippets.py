"""Every fenced block on `schema/task-list-contract.md` runs, or says why not.

TASK-412. That page is what a consumer of `perry-task list --json` reads before
it trusts a payload, and **nothing executed any of it.** Six fenced blocks, zero
run by this suite. The rule-3 snippet — the one that tells a front-end which
`semantics[]` entries apply to it — had shipped three defects, and each of them
is the kind only running it can find:

1. `SUPPORTED` was a set of `(major, minor)` pairs and the drift gate asked
   `(major, minor) > max(SUPPORTED)`. `max` of a set spanning two majors is one
   ceiling for both, so `(1, 19) > (2, 0)` is `False` and **no `1.x` minor drift
   was reportable at all**.
2. The `semantics` filter compared version **strings** — the error the page's
   own `semantics[].version` row warns about, committed on the same page.
   `"1.5" > "1.18"` is `True`, so a pin at 1.18 is warned about a change five
   minors older; and `"1.12" > "1.9"` is `False`, so a genuinely newer change is
   **dropped in silence**. The second direction is the dangerous one and the
   spec's prose does not name it.
3. `TESTED_MINOR_STR` was bound nowhere on the page. The block raised
   `NameError` before reaching any comparison. Nothing noticed, because nothing
   ran it — which is the whole row in one line.

All three were latent while `2.0` is the newest version that exists, which is
why reading the block for six minors never caught them.

**Why this module enumerates rather than samples.** Rule 1 of `review.md § 2`:
the deliverable is the category, not the instance. A fix covering only the two
lines the spec names would leave five other blocks on the page unexecuted and
reproduce the same asymmetry one page later. So the unit here is *a fenced
block*, found by sweeping the page, counted so a seventh cannot arrive unseen —
and note that the sweep has to match an INDENTED fence, because the block this
row is about sits three spaces deep inside a numbered list and `^```' does not
see it.

The marker convention is `bin/README.md`'s, held to the same bar by
`tests/test_bin_surface.py`: a block may go unrun only behind
`<!-- not-executable: <reason> -->`, and every reason is checked against the
block it excuses rather than believed.

Run: python3 tests/parallel test_contract_page_snippets
"""

from __future__ import annotations

COVERS = ("schema/task-list-contract.md", "bin/perry-task", "bin/README.md")

import ast
import builtins
import json
import os
import pathlib
import re
import subprocess
import symtable
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "schema" / "task-list-contract.md"
TOOL = ROOT / "bin" / "perry-task"
TEXT = PAGE.read_text(encoding="utf-8")

MARKER = "<!-- not-executable: "

#: The only reason a block on this page may go unrun. A second reason is a new
#: row here plus a check for it in `test_a_marker_cannot_hide_a_broken_block`,
#: not a new string in the page.
REASONS = ("historical transcript",)

#: Placeholders the page writes for a reader and this module substitutes to run
#: the block. A placeholder NOT listed here fails the run rather than being
#: quietly passed to a shell — see `test_no_undeclared_placeholder_survives`.
#: **The project the blocks are run against** (`USER-942`). The page is about
#: what `perry-task list --json` promises a consumer, not about Perry's own
#: board, so the blocks run against the shipped fixture project. Substituting
#: the checkout here made every block resolve Perry's own state root, which
#: put the whole of it into what this module covers.
PROJECT = ROOT / "tests" / "fixtures" / "sample-project"

PLACEHOLDERS = {"/path/to/project": str(PROJECT)}


def _live_payload(*flags):
    proc = subprocess.run(
        [sys.executable, str(TOOL), "list", *flags, "--json"],
        capture_output=True, text=True, cwd=str(ROOT),
        env={**os.environ, "PERRY_HOME": str(ROOT),
             "PERRY_PROJECT": str(PROJECT)})
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout)


def blocks():
    """`(lineno, lang, body, reason)` for EVERY fenced block on the page.

    Fences are matched with leading whitespace allowed and the closer is
    matched at the opener's indent, because rule 3's block is indented inside a
    list item — a `^```' sweep returns five blocks and misses the sixth, which
    is the one TASK-412 is about.
    """
    lines = TEXT.split("\n")
    out, i = [], 0
    open_re = re.compile(r"^(\s*)```(\w*)\s*$")
    while i < len(lines):
        m = open_re.match(lines[i])
        if m:
            indent, lang = m.group(1), m.group(2)
            prev = lines[i - 1].strip() if i else ""
            reason = (prev[len(MARKER):].removesuffix("-->").strip()
                      if prev.startswith(MARKER) else None)
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            body = "\n".join(ln[len(indent):] if ln.startswith(indent) else ln
                             for ln in lines[i + 1:j])
            out.append((i + 1, lang, body, reason))
            i = j
        i += 1
    return out


def strip_jsonc(text):
    """`jsonc` -> `json`. The page's comments are `// …` to end of line and
    `/* … */` inline; neither form appears inside a string value on this page,
    and `test_the_jsonc_blocks_parse` is what notices if that stops being true.
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def as_json(body):
    """A block may be a whole object or a `"key": {…}` fragment; wrap the
    fragment so both parse."""
    text = strip_jsonc(body).strip()
    if not text.startswith("{"):
        text = "{" + text + "}"
    return json.loads(text)


CHANGELOG_AT = TEXT.index("\n## Changelog\n")


def _lineno_of_offset(off):
    return TEXT.count("\n", 0, off) + 1


CHANGELOG_LINE = _lineno_of_offset(CHANGELOG_AT) + 1


# --------------------------------------------------------------------------
# the sweep and its bound
# --------------------------------------------------------------------------

class TestTheSweepIsBounded(unittest.TestCase):
    def test_the_indented_fence_is_found(self):
        """The sweep's whole reason for not being `^```'.

        Rule 3's python block is indented three spaces. A sweep anchored at
        column 0 returns five blocks, all of them prose furniture, and reports
        a clean page while the block carrying the defects is invisible to it.
        """
        found = [b for b in blocks() if b[1] == "python"]
        self.assertEqual(len(found), 1, "rule 3's python block went missing")
        naive = len(re.findall(r"^```\w*$", TEXT, flags=re.M))
        self.assertEqual(naive % 2, 0, "column-0 fences pair up")
        self.assertEqual(naive // 2, 5, "a `^```' sweep sees five blocks")
        self.assertEqual(len(blocks()), 6,
                         "the indent-aware sweep must find one more — and the "
                         "one more is the block TASK-412 is about")

    def test_the_blocks_are_counted_so_a_new_one_cannot_arrive_unnoticed(self):
        """The bound. Six today: four run, two carry a stated reason."""
        b = blocks()
        self.assertEqual(len(b), 6, "a fenced block was added or removed from "
                                    "schema/task-list-contract.md")
        self.assertEqual(sum(1 for *_, r in b if r), 2)
        self.assertEqual(sorted(lang for _, lang, _, _ in b),
                         ["", "", "bash", "json" + "c", "jsonc", "python"])

    def test_every_block_is_either_marked_or_has_a_runner(self):
        """Criterion 4 of the spec: no snippet on this page goes unrun.

        Dispatch is by language. A block in a language this module has no
        runner for is a failure here, not a silent skip — a skip is how the
        python block spent six minors unexecuted.
        """
        runners = {"bash", "python", "jsonc"}
        for lineno, lang, _, reason in blocks():
            with self.subTest(line=lineno):
                self.assertTrue(
                    reason or lang in runners,
                    f"task-list-contract.md:{lineno} is a {lang or 'plain'} "
                    f"block with no runner and no not-executable marker")

    def test_a_marker_cannot_hide_a_broken_block(self):
        """The marker is a fact about the block, not a way to silence this.

        Without this case the fix for the one above is to mark all six. The one
        reason this module knows is `historical transcript`, and it is checked:
        the block must sit inside the Changelog, under a `###` heading for a
        version that is NOT the one shipping. So a block in the live prose above
        the Changelog cannot wear it, and neither can one under the current
        version's own entry.
        """
        shipped = _live_payload()["contract"].rsplit("/", 1)[1]
        marked = [(n, r) for n, _, _, r in blocks() if r]
        self.assertGreaterEqual(len(marked), 1, "the marker went unused")
        heads = [(m.start(), m.group(1)) for m in
                 re.finditer(r"^### (\S+)", TEXT, flags=re.M)]
        for lineno, reason in marked:
            with self.subTest(line=lineno):
                self.assertIn(reason, REASONS,
                              f"task-list-contract.md:{lineno} gives a reason "
                              f"this module does not know how to check")
                self.assertGreater(
                    lineno, CHANGELOG_LINE,
                    f"task-list-contract.md:{lineno} claims to be a historical "
                    f"transcript but sits in the live prose — run it instead")
                above = [v for off, v in heads
                         if _lineno_of_offset(off) < lineno]
                self.assertTrue(above, "no ### heading above the block")
                self.assertNotEqual(
                    above[-1], shipped,
                    f"task-list-contract.md:{lineno} is excused as history "
                    f"under the entry for the version that ships today")


# --------------------------------------------------------------------------
# the runners
# --------------------------------------------------------------------------

class TestTheBlocksRun(unittest.TestCase):
    def test_the_bash_block_runs_and_returns_a_payload(self):
        """`:13` — the invocation the page opens with, run whole.

        It carries `/path/to/project`, which is substituted from
        `PLACEHOLDERS`. Running it is the only way to know the flag spelling on
        this page is still the flag spelling the tool takes: `--limit 0` in
        particular is a 2.0 flag, and the page describes it two paragraphs
        below in prose that nothing else checks against the binary.
        """
        got = [b for b in blocks() if b[1] == "bash"]
        self.assertEqual(len(got), 1)
        lineno, _, body, reason = got[0]
        self.assertIsNone(reason, "the bash block is runnable; do not mark it")
        for placeholder, real in PLACEHOLDERS.items():
            body = body.replace(placeholder, real)
        out = subprocess.run(
            ["bash", "-c", body], capture_output=True, text=True,
            cwd=str(ROOT),
            env={**os.environ, "PERRY_HOME": str(ROOT)})
        self.assertEqual(out.returncode, 0,
                         f"task-list-contract.md:{lineno} does not run:\n"
                         + out.stderr[-800:])
        payload = json.loads(out.stdout)
        self.assertTrue(payload["contract"].startswith("perry-task/list/"))
        self.assertIsNone(payload["bound"]["limit"],
                          "`--limit 0` must mean no ceiling, which is what the "
                          "flag table on this page promises")

    def test_no_undeclared_placeholder_survives(self):
        """A placeholder the page adds and this module does not know about must
        not be handed to a shell as a real path — that is how a doc example
        starts resolving the checkout. `bin/README.md` learned this by opening
        four real rows on Perry's own board."""
        for lineno, lang, body, reason in blocks():
            if reason or lang != "bash":
                continue
            for placeholder, real in PLACEHOLDERS.items():
                body = body.replace(placeholder, real)
            with self.subTest(line=lineno):
                self.assertNotRegex(body, r"/path/to/|<[a-z-]+>|…")

    def test_the_jsonc_blocks_describe_the_live_payload(self):
        """`:98` and `:120` — parsed, then checked key by key against a real
        call, rather than read.

        `test_count_fields` regexes two NUMBERS out of the first of these and
        checks their arithmetic; nothing has ever parsed either block or
        compared a declared type to a shipped one.
        """
        live = _live_payload()
        got = [b for b in blocks() if b[1] == "jsonc"]
        self.assertEqual(len(got), 2)
        for lineno, _, body, reason in got:
            with self.subTest(line=lineno):
                self.assertIsNone(reason)
                self._same_shape(as_json(body), live, lineno, "")

    def _same_shape(self, example, live, lineno, path):
        for key, want in example.items():
            here = f"{path}.{key}".lstrip(".")
            self.assertIn(key, live,
                          f"task-list-contract.md:{lineno} shows `{here}` and "
                          f"the payload has no such key")
            got = live[key]
            if want is None or got is None:
                continue          # the page spells `null` where a value is optional
            self.assertIs(
                type(want) if not isinstance(want, bool) else bool,
                type(got) if not isinstance(got, bool) else bool,
                f"task-list-contract.md:{lineno} types `{here}` as "
                f"{type(want).__name__}; the payload returns "
                f"{type(got).__name__}")
            if isinstance(want, dict):
                self._same_shape(want, got, lineno, here)
            # Lists are compared as lists and not recursed into: the page
            # illustrates an entry shape from one element and the live array may
            # be empty. `tests/test_contract_key_parity.py` is what holds entry
            # keys, with a witness project for the collections this board leaves
            # empty.


# --------------------------------------------------------------------------
# rule 3's snippet — the substance
# --------------------------------------------------------------------------

def snippet():
    got = [b for b in blocks() if b[1] == "python"]
    assert len(got) == 1, "rule 3's python block"
    return got[0][2]


def drive(version, semantics_versions):
    """Run the page's block on a synthetic payload and return `(namespace,
    versions warned about)`.

    **Everything below goes through this rather than restating the comparison
    in the test**, and that is not a stylistic preference — it is the finding of
    this row's own mutation round. The first draft of these cases recomputed
    `pair(a) > pair(b)` itself and checked the arithmetic; restoring the string
    compare at the block's *call site* left every one of them green, because
    they were testing a copy of the logic and not the page. A test that
    re-implements the snippet is the same mistake as a page whose snippet
    nothing runs, one layer in.

    `fields` and `note` carry the version so a warning is identifiable.
    """
    payload = {"contract": f"perry-task/list/{version}",
               "semantics": [{"version": v, "fields": [v], "note": v}
                             for v in semantics_versions]}
    warned = []
    ns = {"payload": payload,
          "warn": lambda fields, note: warned.append(note)}
    exec(compile(snippet(), "<task-list-contract.md rule 3>", "exec"), ns)
    return ns, warned


class TestRuleThreeSnippetExecutes(unittest.TestCase):
    """Criterion 3: the block runs against a live payload and exits 0."""

    def test_it_runs_on_the_live_payload_and_warns_about_nothing(self):
        live = _live_payload()
        warned = []
        ns = {"payload": live, "warn": lambda f, n: warned.append((f, n))}
        exec(compile(snippet(), "<task-list-contract.md rule 3>", "exec"), ns)
        self.assertEqual(
            warned, [],
            "a consumer pinned at the shipped version is warned about nothing")
        self.assertEqual(ns["version"], live["contract"].rsplit("/", 1)[1])

    def test_it_references_no_name_the_page_does_not_supply(self):
        """Defect 3, and the category it belongs to.

        `TESTED_MINOR_STR` was never bound anywhere on this page, so the block
        raised `NameError` on any payload that reached its last comparison. Read
        by six reviewers, caught by none, because a name that looks like a
        constant reads like one.

        The two free names left are the consumer's own and the page says so.
        """
        st = symtable.symtable(snippet(), "<snippet>", "exec")
        free = {s.get_name() for s in st.get_symbols()
                if s.is_referenced() and not s.is_assigned()}
        free -= set(dir(builtins))
        self.assertEqual(free, {"payload", "warn"},
                         "a free name the page neither defines nor declares")
        for name in sorted(free):
            self.assertIn(f"`{name}`", TEXT,
                          f"the page must tell a consumer to supply `{name}`")

    def test_supported_is_a_ceiling_per_major_not_one_across_all_of_them(self):
        """Defect 1 at the source. `max()` over a set spanning two majors is the
        shape that made `1.x` drift unreportable; a mapping cannot have it."""
        ns = {}
        exec(compile(snippet(), "<s>", "exec"),
             {"payload": _live_payload(), "warn": lambda *a: None}, ns)
        self.assertIsInstance(ns["SUPPORTED"], dict,
                              "SUPPORTED must be major -> minor")
        self.assertNotIn("max(SUPPORTED)", snippet(),
                         "one ceiling across every major is the defect")


class TestTheVersionSpaceIsEnumerated(unittest.TestCase):
    """Criterion 2: every pair in the version space the page defines, not three
    hand-picked ones. Three hand-picked versions is how this shipped.
    """

    #: The page's Changelog is newest-first, so DOCUMENT ORDER is a statement of
    #: the true version order made independently of any int parsing — the
    #: comparison under test cannot be used to confirm itself on these.
    @classmethod
    def setUpClass(cls):
        tail = TEXT[CHANGELOG_AT:]
        cls.declared = [m.group(1) for m in
                        re.finditer(r"^### (\d+\.\d+) —", tail, flags=re.M)]
        cls.rank = {v: i for i, v in enumerate(cls.declared)}   # 0 = newest

    def pair(self, v):
        """The snippet's own `pair`, lifted out of the page so the enumeration
        exercises the shipped text rather than a copy of it."""
        ns = {}
        exec(compile(snippet(), "<s>", "exec"),
             {"payload": _live_payload(), "warn": lambda *a: None}, ns)
        return ns["pair"](v)

    def test_the_changelog_gives_a_usable_independent_order(self):
        self.assertGreaterEqual(len(self.declared), 19,
                                "1.0 through 1.18 and 2.0 at least")
        # 2.4: TASK-262 round 4b's retired-board minor is now the newest entry.
        self.assertEqual(self.declared[0], "2.4", "newest first")
        self.assertEqual(self.declared[-1], "1.0", "oldest last")

    def test_every_declared_pair_agrees_with_document_order(self):
        """The enumeration, against the independent oracle. 20 versions ->
        400 ordered pairs, every one checked."""
        ns = {}
        exec(compile(snippet(), "<s>", "exec"),
             {"payload": _live_payload(), "warn": lambda *a: None}, ns)
        pair = ns["pair"]
        checked = 0
        for a in self.declared:
            for b in self.declared:
                newer = self.rank[a] < self.rank[b]       # earlier = newer
                self.assertEqual(
                    pair(a) > pair(b), newer,
                    f"{a} vs {b}: the snippet and the Changelog's own order "
                    f"disagree")
                checked += 1
        self.assertEqual(checked, len(self.declared) ** 2)
        self.assertGreaterEqual(checked, 400)

    def test_the_string_compare_is_wrong_on_this_very_space(self):
        """Defect 2 characterised, counted rather than sampled — both directions.

        **This case is a description of the defect, not the guard against it.**
        It computes the comparison itself, so it cannot see a regression at the
        block's call site; restoring the string compare on the page leaves it
        green. It is kept because it is the only place the *silence* direction
        is counted, and that direction is the one the row's spec does not name.
        `test_the_filter_warns_about_exactly_the_entries_newer_than_the_pin` is
        the guard, and it drives the page.

        The spec names the false-positive direction (`"1.5" > "1.18"`). The
        enumeration shows the other one, which is worse: pairs where the string
        compare says False and the change really IS newer are warnings a
        consumer never receives.
        """
        false_warn = false_silence = 0
        for a in self.declared:
            for b in self.declared:
                newer = self.rank[a] < self.rank[b]
                if (a > b) and not newer:
                    false_warn += 1
                if not (a > b) and newer:
                    false_silence += 1
        self.assertGreater(false_warn, 0)
        self.assertGreater(false_silence, 0,
                           "if this is 0 the space stopped containing a "
                           "two-digit minor and the test measures nothing")
        # the two the spec names, held as literals so the regression is legible
        self.assertTrue("1.5" > "1.18", "the reported wrong answer")
        self.assertFalse(self.pair("1.5") > self.pair("1.18"), "and gone")

    def supported(self):
        ns, _ = drive("2.0", [])
        return ns["SUPPORTED"]

    def space(self):
        """Every version in the Changelog, plus five minors past the highest in
        each major and three of the next major.

        The forward half is not decoration. `2.0` is the newest thing that
        exists, so **every version in the Changelog makes the old gate look
        fine** — the defect lives entirely in versions that do not exist yet,
        which is why six minors of readers walked past it.
        """
        highest = {}
        for v in self.declared:
            mj, mn = (int(x) for x in v.split("."))
            highest[mj] = max(mn, highest.get(mj, mn))
        out = [f"{mj}.{mn}" for mj, top in highest.items()
               for mn in range(0, top + 6)]
        out += [f"{max(highest) + 1}.{mn}" for mn in range(0, 3)]
        return out

    def test_the_drift_gate_is_a_ceiling_per_major_over_the_forward_space(self):
        """Defect 1, by **running the block** on every version in the space.

        `tested` is read out of the block's own namespace, so the ceiling the
        page computes is compared to the ceiling the page promises. The earlier
        draft of this case recomputed both and was green against a restored
        defect — see `drive`.
        """
        SUPPORTED = self.supported()
        checked = 0
        for version in self.space():
            mj, mn = (int(x) for x in version.split("."))
            with self.subTest(version=version):
                if mj not in SUPPORTED:
                    with self.assertRaises(SystemExit):
                        drive(version, [])
                    continue
                # one minor newer than this consumer's pin, so the gate has
                # something to report if and only if it opens
                probe = f"{mj}.{SUPPORTED[mj] + 1}"
                ns, warned = drive(version, [probe])
                self.assertEqual(
                    ns["tested"], (mj, SUPPORTED[mj]),
                    "the ceiling must be this major's, not one shared across "
                    "majors — `(1, 19) > (2, 0)` is False and that made every "
                    "1.x minor drift unreportable")
                self.assertEqual(
                    bool(warned), mn > SUPPORTED[mj],
                    f"payload {version} against a pin at {mj}.{SUPPORTED[mj]}")
                checked += 1
        self.assertGreaterEqual(checked, 24, "the forward space collapsed")
        # the pair the spec names, now through the page itself
        self.assertEqual(drive("1.19", [])[0]["tested"], (1, SUPPORTED[1]))
        self.assertTrue(drive("1.19", ["1.19"])[1] == ["1.19"],
                        "1.19 against a pin at 1.18 must report drift")

    def test_the_filter_warns_about_exactly_the_entries_newer_than_the_pin(self):
        """Defect 2, by running the block's own filter.

        For each major the page supports, a payload one minor past the pin —
        so the gate is open — carrying every declared version in `semantics[]`.
        What comes back through `warn` must be exactly the versions the
        Changelog's own ordering calls newer than the pin.

        Against the string compare this returns nine versions where one is
        correct, seven of them **older** than the pin.
        """
        SUPPORTED = self.supported()
        for mj, pin_minor in sorted(SUPPORTED.items()):
            pin = f"{mj}.{pin_minor}"
            self.assertIn(pin, self.declared,
                          "SUPPORTED names a version the Changelog does not")
            with self.subTest(pin=pin):
                _, warned = drive(f"{mj}.{pin_minor + 1}", self.declared)
                want = [v for v in self.declared
                        if self.rank[v] < self.rank[pin]]
                self.assertEqual(sorted(warned), sorted(want),
                                 f"a consumer pinned at {pin} must hear about "
                                 f"exactly what shipped after {pin}")

    def test_the_live_semantics_versions_are_all_inside_the_space(self):
        """The premise the two cases above rest on.

        `semantics[]` is the array rule 3 walks. If it ever names a version the
        Changelog does not, the enumeration is running against a space that
        does not contain the real inputs, and every case here passes on the
        wrong population. The filtering itself is checked by
        `test_the_filter_warns_about_exactly_the_entries_newer_than_the_pin`,
        which drives the page instead of restating it.
        """
        live = _live_payload()
        entries = [e["version"] for e in live["semantics"]]
        self.assertTrue(entries, "the payload carries no semantics entries; "
                                 "this case would pass on nothing")
        for v in entries:
            self.assertIn(v, self.declared,
                          f"semantics names {v}, which the Changelog does not")
        # and the payload's own version is in it too
        self.assertIn(live["contract"].rsplit("/", 1)[1], self.declared)


class TestTheRuleOneGateStillBehaves(unittest.TestCase):
    """Criterion 5, the control. The major gate is the half of this block a
    reviewer DID execute and found correct; the fix must not have moved it.

    It is run here as the page ships it, on synthetic payloads, so the answer
    is the block's and not a restatement of it.
    """

    def gate(self, contract):
        live = dict(_live_payload())
        live["contract"] = f"perry-task/list/{contract}"
        live["semantics"] = []
        ns = {"payload": live, "warn": lambda *a: None}
        exec(compile(snippet(), "<s>", "exec"), ns)
        return ns

    def test_it_accepts_two_zero(self):
        self.assertEqual(self.gate("2.0")["version"], "2.0")

    def test_it_accepts_one_eighteen(self):
        self.assertEqual(self.gate("1.18")["version"], "1.18")

    def test_it_rejects_three_zero(self):
        with self.assertRaises(SystemExit) as cm:
            self.gate("3.0")
        self.assertIn("3.0", str(cm.exception))
        self.assertIn("not supported", str(cm.exception))

    def test_it_still_rejects_on_the_major_and_not_on_a_minor(self):
        """Rule 3's own prose: *do not refuse on a minor*. A 1.x the consumer
        has never seen must pass the gate and be reported through `semantics`,
        not raised on."""
        self.assertEqual(self.gate("1.99")["version"], "1.99")


if __name__ == "__main__":
    unittest.main(verbosity=2)
