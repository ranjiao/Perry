"""`perry-lint`'s DEFAULT pass emits `NS-01` — DESIGN-002 decision #4.

Decision #4 was locked on 2026-08-16 and reads *"Lint warns, names it a
collision"*. `bin/perry-diagnose` grew the emitter and `reference/diagnose.md`
grew the catalog row; `bin/perry-lint` grew a comment mentioning `NS-01` and
nothing else, and `--claims` reported the collision in its own words without
the id. So the tool the design names as the one that "catches it early" was the
one tool that never said it.

What this suite pins, in the order the deliverable states it:

1. **One computation, not two.** `--claims` and the default pass ask the same
   question of the same `claims[]` list through the same function. Two collision
   checks that can disagree is the defect DESIGN-002 exists to close, and
   writing a second heuristic here would reintroduce it one level down.
2. **`warn`, always.** Decision #2 was taken strictly — no per-path opt-out —
   so a user who knowingly keeps one file in a claimed folder has no way to
   silence this. `error` would make a deliberate choice permanently red, which
   is the outcome DESIGN-002 rejects by name.
   `--strict` does not promote it either, for the same reason and on the same
   authority (§ 9, appended at lock: *"A collision never sets a non-zero
   exit."*). That narrows what `--strict` means tool-wide, so both directions
   are pinned below: `NS-01` alone exits 0, any other warning alongside it
   still exits 1.
3. **Nothing else moves.** A project with no collision and a project that was
   never adopted print byte-identically to what they printed before this
   existed, and `--claims` — a contract the setup and adopt flows read — is
   unchanged down to its JSON keys.

**The byte-identity assertions are built to be falsifiable.** "Identical to
today" is a claim about a binary that no longer exists, so it is reconstructed:
the driver loads `bin/perry-lint` twice, once with `check_ns_collisions` stubbed
to return nothing — which is exactly the pre-change default pass — and once
live, and compares the two. On a clean project they must match; on a colliding
project they must NOT, and that second assertion is what stops the first from
being a tautology about a check that never ran.

Run: python3 tests/parallel test_ns_collision
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINT = ROOT / "bin" / "perry-lint"
FIXTURE = ROOT / "tests" / "fixtures" / "sample-project"

# A file no rule in `looks_like_perry_state` can mistake for Perry's own: the
# stem is not `DESIGN-1`/`ADR-2`/`001-x`/a date, the name is in no `files[]`
# entry, and the body carries neither `$PERRY_HOME` nor an `Owner**: \`perry\``
# line. Spelled out because a fixture that accidentally looked Perry-shaped
# would make every assertion below pass by reporting nothing.
FOREIGN = """# Search rework proposal

Written by the project, in a folder Perry claimed. Nothing here is Perry state.
"""

# Loads the linter as a module so one run can be taken with the new check
# disabled. `spec_from_file_location` alone will not do it — `bin/perry-lint`
# has no `.py` suffix, so the extension-based loader lookup finds nothing.
DRIVER = r'''
import contextlib, importlib.machinery, importlib.util, io, sys, json

path, mode = sys.argv[1], sys.argv[2]
loader = importlib.machinery.SourceFileLoader("perry_lint_uut", path)
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)

if mode == "stub":
    # Fail loudly rather than creating the attribute. Assigning a name the
    # module does not have would stub nothing, and every comparison below would
    # then be a run of the live check against itself — green, and measuring
    # nothing.
    assert hasattr(mod, "check_ns_collisions"), (
        "bin/perry-lint has no check_ns_collisions to stub — this driver can "
        "no longer reconstruct the pre-change default pass")
    mod.check_ns_collisions = lambda *a, **k: []

if mode == "rows":
    # The raw rows, before the `--claims` boundary projects them. Proves the
    # projection has something to project.
    import pathlib
    root = pathlib.Path(sys.argv[3]).resolve()
    schema = json.loads(mod.SCHEMA_PATH.read_text())
    rows, _ = mod.check_claims(root, schema, mod.P.resolve_state_root(root))
    print(json.dumps({"rows": rows, "published": list(mod.CLAIM_ROW_KEYS)},
                     ensure_ascii=False))
    raise SystemExit(0)

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = mod.main(sys.argv[3:])
sys.stderr.write(str(rc))
sys.stdout.write(buf.getvalue())
'''


class Fixture(unittest.TestCase):

    def _tmp(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d

    def adopted_clean(self) -> pathlib.Path:
        """An adopted project with nothing foreign anywhere Perry claims.

        `sample-project` ships two directories that trip the shape check
        (`evidence/`, `inputs/` — see `TestTheShippedFixtureBoundary`), and one
        design doc that is missing three required sections. All three are
        removed so this fixture has **no findings at all**: the `--strict`
        assertions need a baseline where `NS-01` is the only warning there is,
        or they cannot tell a carve-out from a project that was already green.
        """
        d = self._tmp() / "clean"
        shutil.copytree(FIXTURE, d)
        shutil.rmtree(d / "evidence")
        shutil.rmtree(d / "inputs")
        (d / "design" / "DESIGN-002-flake-scoring.md").unlink()
        return d

    def adopted_colliding(self) -> pathlib.Path:
        """One foreign file, in a claimed directory that `files[]` does not
        validate.

        `inputs/` rather than `design/` deliberately. `design/*.md` IS a
        `files[]` entry, so a foreign file there ALSO produces the malformed-
        state findings DESIGN-002 § P4 describes — which is the true user
        story, and is pinned in `TestTheParseFindingsStillCoexist`, but which
        would make the exit-code assertions below unable to tell an `NS-01`
        carve-out from a project that was failing for another reason entirely.
        """
        d = self.adopted_clean()
        (d / "inputs").mkdir()
        (d / "inputs" / "vendor-notes.md").write_text(FOREIGN)
        return d

    def never_adopted(self) -> pathlib.Path:
        """A folder Perry has never touched that owns a `design/` directory.

        No `.perry/config.md`, no `BOARD.md`, no `OKR.md`, no `phase/` — the
        four things `is_adopted` looks for. The collision ingredients are all
        present, which is what makes "the check did not run" a real result
        rather than "there was nothing to find"; `test_the_ingredients_are_all
        _present` proves that separately.
        """
        d = self._tmp() / "someone-elses-project"
        (d / "design").mkdir(parents=True)
        (d / "design" / "proposal.md").write_text(FOREIGN)
        (d / "README.md").write_text("# Not a Perry project\n")
        return d

    # ── running the linter ────────────────────────────────────────────────

    def lint(self, d: pathlib.Path, *extra) -> tuple[int, dict]:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(d),
                               "--json", *extra],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertTrue(proc.stdout.strip().startswith("{"),
                        f"perry-lint printed no payload: "
                        f"{proc.stdout[-300:]}{proc.stderr[-400:]}")
        return proc.returncode, json.loads(proc.stdout)

    def lint_text(self, d: pathlib.Path, *extra) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(d),
                               *extra], capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, proc.stdout

    def drive(self, mode: str, *args) -> tuple[str, str]:
        """Run `main()` under the driver. Returns (stdout, exit code as text)."""
        proc = subprocess.run(
            [sys.executable, "-c", DRIVER, str(LINT), mode, *args],
            capture_output=True, text=True, cwd=ROOT)
        self.assertNotIn("Traceback", proc.stderr,
                         f"the driver failed: {proc.stderr[-800:]}")
        return proc.stdout, proc.stderr

    def ns(self, payload: dict) -> list[dict]:
        return [f for f in payload["findings"] if f["rule"] == "NS-01"]


class TestACollisionYieldsTheFinding(Fixture):
    """Verification 1: a flagless run, `NS-01`, at `warn`, with the path as
    evidence."""

    def test_a_flagless_run_emits_ns01(self):
        _, payload = self.lint(self.adopted_colliding())
        rows = self.ns(payload)
        self.assertEqual(len(rows), 1, payload["findings"])
        self.assertEqual(rows[0]["severity"], "warn")

    def test_the_offending_path_is_the_evidence(self):
        _, payload = self.lint(self.adopted_colliding())
        row = self.ns(payload)[0]
        self.assertIn("inputs/vendor-notes.md", row["message"],
                      "the finding does not say which file collided, so the "
                      "user cannot act on it")
        self.assertEqual(row["file"], "inputs",
                         "the finding does not name the claimed directory")

    def test_the_finding_says_what_it_is_and_why_it_bites(self):
        """Deliverable 3 — the catalog entry's own four parts."""
        _, payload = self.lint(self.adopted_colliding())
        msg = self.ns(payload)[0]["message"]
        self.assertIn("Perry did not write", msg)          # what it is
        self.assertIn("malformed", msg)                    # why it bites
        self.assertIn("/perry relocate", msg)              # remedy one
        self.assertIn("move these files out of", msg)      # remedy two

    def test_both_remedies_appear_and_only_those_two(self):
        """Decision #2 was taken strictly: the `Ignore:` list the third option
        would have added is not part of this design, so a third remedy here
        would be advice for a feature that does not exist."""
        _, payload = self.lint(self.adopted_colliding())
        msg = self.ns(payload)[0]["message"]
        self.assertNotIn("Ignore", msg)

    def test_the_text_output_carries_it_too(self):
        """`--json` is for callers; the flagless run is what a user sees."""
        _, out = self.lint_text(self.adopted_colliding())
        self.assertIn("[NS-01]", out)
        self.assertIn("inputs/vendor-notes.md", out)

    def test_several_collisions_are_several_findings(self):
        d = self.adopted_colliding()
        (d / "weekly" / "retro-notes.md").write_text(FOREIGN)
        _, payload = self.lint(d)
        paths = sorted(f["file"] for f in self.ns(payload))
        self.assertEqual(paths, ["inputs", "weekly"])

    def test_evidence_is_capped_and_says_so(self):
        """A directory someone else owns can hold hundreds of files. A finding
        that prints all of them is a finding nobody reads — but a cap that hides
        the count would understate the collision."""
        d = self.adopted_clean()
        (d / "inputs").mkdir()
        for n in range(14):
            (d / "inputs" / f"note-{n}.md").write_text(FOREIGN)
        msg = self.ns(self.lint(d)[1])[0]["message"]
        self.assertIn("holds 14 file(s)", msg)
        self.assertIn("+4 more", msg)
        self.assertEqual(msg.count("note-"), 10)


class TestTheExitCodeIsUnchanged(Fixture):
    """Verification 2, and decision #2's whole point: a user must be able to
    live with a collision."""

    def test_a_collision_alone_exits_zero(self):
        rc, payload = self.lint(self.adopted_colliding())
        self.assertEqual(rc, 0)
        self.assertEqual(payload["errors"], 0)
        self.assertEqual(payload["warnings"], 1)

    def test_it_is_never_promoted_to_error(self):
        """Not "is not an error today" — no reachable input makes it one."""
        d = self.adopted_colliding()
        (d / "weekly" / "retro-notes.md").write_text(FOREIGN)
        (d / "journal" / "2026-08" / "scratch.md").write_text(FOREIGN)
        for f in self.ns(self.lint(d)[1]):
            self.assertEqual(f["severity"], "warn", f)

    def test_strict_does_not_promote_it(self):
        """DESIGN-002 § 9: *"A collision never sets a non-zero exit."* With no
        per-path opt-out, promotion would mean permanently red CI and no way to
        accept a deliberate choice."""
        rc, _ = self.lint(self.adopted_colliding(), "--strict")
        self.assertEqual(
            rc, 0,
            "--strict promoted NS-01, so a project that knowingly keeps one "
            "file in a claimed folder has permanently red CI and no way out")

    def test_strict_still_promotes_every_other_warning(self):
        """The other direction, and the reason this pair exists. The carve-out
        narrows what `--strict` means tool-wide; it must be one rule wide, or a
        future reader will take it as licence to exempt the next warning too."""
        d = self.adopted_colliding()
        shutil.copy(FIXTURE / "design" / "DESIGN-002-flake-scoring.md",
                    d / "design" / "DESIGN-002-flake-scoring.md")
        rc, payload = self.lint(d, "--strict")
        rules = {f["rule"] for f in payload["findings"]}
        self.assertIn("NS-01", rules)
        self.assertIn("missing-section", rules)
        self.assertEqual(rc, 1,
                         "--strict stopped failing on ordinary warnings — the "
                         "NS-01 carve-out has widened into the whole flag")

    def test_the_baseline_fixture_is_green_without_the_collision(self):
        """Guards the two above from passing for the wrong reason: if
        `adopted_clean()` ever carries a warning of its own, `--strict`
        returning 1 would prove nothing about NS-01."""
        rc, payload = self.lint(self.adopted_clean(), "--strict")
        self.assertEqual(payload["findings"], [])
        self.assertEqual(rc, 0)


class TestNothingElseMoved(Fixture):
    """Verifications 3 and 4, reconstructed rather than asserted.

    The stub run IS the pre-change default pass: `check_ns_collisions` is the
    only thing the change adds to it. So "byte-identical to today" becomes a
    comparison the suite can actually make, and the colliding case proves the
    comparison is live."""

    def both(self, d: pathlib.Path, *args) -> tuple[str, str, str, str]:
        live, live_rc = self.drive("live", "--root", str(d), *args)
        stub, stub_rc = self.drive("stub", "--root", str(d), *args)
        return live, stub, live_rc, stub_rc

    def test_a_project_with_no_collision_is_byte_identical(self):
        d = self.adopted_clean()
        for args in ((), ("--json",), ("--strict",)):
            with self.subTest(args=args):
                live, stub, lrc, src = self.both(d, *args)
                self.assertEqual(stub, live)
                self.assertEqual(src, lrc)

    def test_the_comparison_is_not_vacuous(self):
        """The same comparison on a colliding project must come apart. Without
        this, a `check_ns_collisions` that returned nothing on every input would
        satisfy every byte-identity test in this class."""
        live, stub, _, _ = self.both(self.adopted_colliding())
        self.assertNotEqual(stub, live,
                            "the stub and the live run agree on a COLLIDING "
                            "project, so the byte-identity tests above are "
                            "comparing a check that never fires against itself")
        self.assertIn("[NS-01]", live)
        self.assertNotIn("[NS-01]", stub)

    def test_a_project_that_was_never_adopted_is_byte_identical(self):
        d = self.never_adopted()
        for args in ((), ("--json",)):
            with self.subTest(args=args):
                live, stub, lrc, src = self.both(d, *args)
                self.assertEqual(stub, live)
                self.assertEqual(src, lrc)

    def test_a_project_that_was_never_adopted_gets_no_finding(self):
        """Stated directly as well as by comparison. Reporting a collision on a
        folder Perry has never touched would be Perry claiming a namespace it
        was never given — the failure the `is_adopted` gate exists to prevent."""
        d = self.never_adopted()
        _, payload = self.lint(d)
        self.assertEqual(self.ns(payload), [])
        _, out = self.lint_text(d)
        self.assertIn("not a Perry project yet", out)

    def test_the_ingredients_are_all_present_on_the_unadopted_fixture(self):
        """So "no finding" means the gate held, not that there was nothing to
        find. `--claims` is deliberately outside the gate and sees the same
        `design/proposal.md` from the same computation."""
        _, out = self.lint_text(self.never_adopted(), "--claims")
        self.assertIn("1 collision(s)", out)
        self.assertIn("design/proposal.md", out)

    def test_adopting_that_same_folder_turns_the_finding_on(self):
        """The gate, from the other side."""
        d = self.never_adopted()
        (d / ".perry").mkdir()
        shutil.copy(FIXTURE / ".perry" / "config.md", d / ".perry" / "config.md")
        _, payload = self.lint(d)
        self.assertEqual(len(self.ns(payload)), 1, payload["findings"])


class TestClaimsIsUntouched(Fixture):
    """Verification 5. `--claims` is read by first-time setup and by adopt
    stage 3; its payload is a contract, not an implementation detail."""

    PUBLISHED = ["path", "state", "owner", "detail"]

    def claims(self, d: pathlib.Path, *extra) -> dict:
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(d),
                               "--claims", "--json", *extra],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
        return json.loads(proc.stdout)

    def test_the_payload_publishes_exactly_the_documented_keys(self):
        payload = self.claims(self.adopted_colliding())
        self.assertEqual(
            sorted(payload),
            sorted(["project_root", "state_root", "claimed", "collisions",
                    "suggested_state_root", "paths"]))
        for row in payload["paths"]:
            self.assertEqual(list(row), self.PUBLISHED, row)

    def test_the_projection_is_load_bearing(self):
        """The check above is only worth running if there is something to leak.
        `check_claims` grew `rel` and `foreign` for `NS-01`'s evidence, and the
        `--claims` boundary drops them; if the projection is deleted, the key
        assertion above goes red rather than quietly widening the contract."""
        out, _ = self.drive("rows", str(self.adopted_colliding()))
        got = json.loads(out)
        self.assertEqual(got["published"], self.PUBLISHED)
        extra = sorted(set(got["rows"][0]) - set(self.PUBLISHED))
        self.assertEqual(extra, ["foreign", "rel"],
                         "check_claims no longer carries the fields NS-01 cites "
                         "as evidence, so the projection guards nothing")

    def test_the_rows_still_read_the_way_they_did(self):
        payload = self.claims(self.adopted_colliding())
        row = next(r for r in payload["paths"] if r["path"] == "inputs/")
        self.assertEqual(row["state"], "collision")
        self.assertEqual(row["owner"], "work")
        self.assertEqual(
            row["detail"],
            "1 file(s) Perry did not write, e.g. inputs/vendor-notes.md")
        self.assertEqual(payload["collisions"], 1)

    def test_a_clean_project_still_reports_no_collision(self):
        payload = self.claims(self.adopted_clean())
        self.assertEqual(payload["collisions"], 0)
        self.assertEqual({r["state"] for r in payload["paths"]},
                         {"free", "perry"})

    def test_state_root_still_selects_a_candidate(self):
        """`--state-root` is how setup tests `perry/` before writing anything."""
        d = self.adopted_colliding()
        payload = self.claims(d, "--state-root", "perry")
        self.assertEqual(payload["state_root"], "perry")
        self.assertEqual(payload["collisions"], 0,
                         "an empty candidate root collides with nothing")
        self.assertIsNone(payload["suggested_state_root"],
                          "no alternative is proposed when one was named")

    def test_the_suggestion_still_appears_when_the_root_collides(self):
        payload = self.claims(self.adopted_colliding())
        self.assertEqual(payload["suggested_state_root"], "perry/")

    def test_claims_still_runs_before_adoption(self):
        """The one thing that must NOT pick up the default pass's gate."""
        payload = self.claims(self.never_adopted())
        self.assertEqual(payload["collisions"], 1)


class TestOneComputation(Fixture):
    """Deliverable 1's real requirement, and the one a later change can break
    without any test above noticing: the two modes must keep asking the same
    function. A second heuristic here is exactly the defect DESIGN-002 exists to
    close, one level down."""

    def source(self) -> str:
        return LINT.read_text()

    def test_the_default_pass_answers_through_check_claims(self):
        body = re.search(r"\ndef check_ns_collisions\(.*?\n(?=\ndef |\n# )",
                         self.source(), re.S)
        self.assertIsNotNone(body, "check_ns_collisions is gone")
        self.assertIn("check_claims(", body.group(0),
                      "the default pass computes collisions its own way. Two "
                      "collision checks that can disagree is the defect "
                      "DESIGN-002 exists to close")

    def test_there_is_still_only_one_shape_check(self):
        self.assertEqual(
            self.source().count("def looks_like_perry_state"), 1,
            "a second Perry-shaped predicate would let --claims and the "
            "default pass disagree about the same directory")

    def test_the_two_modes_agree_on_the_same_project(self):
        """Behavioural, not structural. The paths `--claims` calls collisions
        and the paths the default pass reports must be the same set."""
        d = self.adopted_colliding()
        (d / "weekly" / "retro-notes.md").write_text(FOREIGN)
        _, payload = self.lint(d)
        default_paths = {f["file"] + "/" for f in self.ns(payload)}
        proc = subprocess.run([sys.executable, str(LINT), "--root", str(d),
                               "--claims", "--json"],
                              capture_output=True, text=True, cwd=ROOT)
        claim_paths = {r["path"] for r in json.loads(proc.stdout)["paths"]
                       if r["state"] == "collision"}
        self.assertEqual(default_paths, claim_paths)


class TestTheParseFindingsStillCoexist(Fixture):
    """The P4 story end to end — and the half of it TASK-086 does not deliver.

    DESIGN-002 § "The post-setup collision (P4)" says the fix for a user's own
    `design/proposal.md` being reported as malformed Perry state is *"a distinct
    finding rather than a parse failure"*. TASK-086's deliverables ask for the
    distinct finding and say nothing about the parse failure, so this is what
    ships: `NS-01` now names the collision, and the malformed-state findings are
    still emitted beside it.

    That is a deliberate boundary, not an oversight. Suppressing `check_file`
    over foreign files inside a claimed directory would silence errors that fire
    today, and it reaches ADR-004's per-file conformance gate — a change of a
    different size, with none of it in this task's deliverable list. Recorded
    here so the remaining half is visible rather than assumed done.
    """

    def p4(self) -> pathlib.Path:
        d = self.adopted_clean()
        (d / "design" / "proposal.md").write_text(FOREIGN)
        return d

    def test_the_collision_is_named(self):
        rows = self.ns(self.lint(self.p4())[1])
        self.assertEqual([r["file"] for r in rows], ["design"])

    def test_the_users_file_is_still_also_called_malformed(self):
        _, payload = self.lint(self.p4())
        rules = {f["rule"] for f in payload["findings"]
                 if f["file"] == "design/proposal.md"}
        self.assertIn(
            "missing-header-field", rules,
            "the parse findings over a foreign file in a claimed directory are "
            "gone. If that was done on purpose, this test and its docstring are "
            "the record that says TASK-086 left it undone — update both")

    def test_and_they_still_set_the_exit_code(self):
        """Which is the user-visible consequence of the boundary: the collision
        itself costs nothing, but the parse errors it drags along cost a red
        run. `NS-01`'s carve-out does not and must not cover them."""
        self.assertEqual(self.lint(self.p4())[0], 1)


class TestTheShippedFixtureBoundary(Fixture):
    """Where `looks_like_perry_state` stops, pinned rather than fixed.

    `tests/fixtures/sample-project` holds two directories of files **Perry
    itself would have written** that the shape check does not recognise:
    `evidence/2026-08/REL-00{1,2}-spec.md` and `inputs/vendor-api.md`. None of
    them matches a `files[]` name, a `DESIGN-`/`ADR-`/`TASK-` stem, a bare date
    stem, or carries `$PERRY_HOME` in its first 2000 characters.

    `bin/perry-diagnose` has reported them as `NS-01` since it shipped, so the
    misfire is not new — but the default lint pass is where a user meets it, and
    that IS new. Widening the predicate would move `--claims` output, which
    deliverable 5 forbids, so this records the boundary exactly as it stands.
    When the heuristic is widened, this test is the one that should fail first
    and be updated deliberately.

    The consequence is the same on Perry's own repository, at greater scale:
    `perry/evidence/`, `perry/handoff/` and `perry/knowledge/` each hold one
    Perry-authored file whose name the predicate does not recognise, so
    `python3 bin/perry-lint` here now prints three `NS-01` warnings where it
    printed `✓ clean`. Reported with the task, not fixed by it.
    """

    def test_the_shipped_fixture_surfaces_two_known_false_positives(self):
        _, payload = self.lint(FIXTURE)
        paths = sorted(f["file"] for f in self.ns(payload))
        self.assertEqual(
            paths, ["evidence", "inputs"],
            "the default lint's collision set on the shipped fixture moved. If "
            "the shape check was widened on purpose, update this test and the "
            "docstring above it; if a fixture file moved, check whether the "
            "widening was accidental")

    def test_they_are_files_perry_would_have_written(self):
        """States the claim the assertion above rests on, so a later reader can
        check the argument rather than trust it."""
        for rel in ("evidence/2026-08/REL-001-spec.md",
                    "evidence/2026-08/REL-002-spec.md",
                    "inputs/vendor-api.md"):
            with self.subTest(rel=rel):
                self.assertTrue((FIXTURE / rel).exists())

    def test_the_false_positives_still_cost_nothing_at_the_exit_code(self):
        """The mitigation, and why this is a boundary rather than a regression:
        a user who has not asked for it pays no failing build."""
        self.assertEqual(self.lint(FIXTURE)[0], 0)
        self.assertEqual(self.lint(FIXTURE, "--strict")[0], 1,
                         "the fixture's three missing-section warnings still "
                         "fail --strict; only NS-01 is carved out")


class TestTheTwoStoreFilesAreReportable(Fixture):
    """TASK-100 — `tasks.jsonl` and `.perry/events.jsonl` are claimed.

    Perry has written both on every mutating command since ADR-007, and
    neither appeared in `claims[]`. Adding them grants no new write; it makes
    an existing write DECLARED, which is the only thing that makes a collision
    on those two paths reportable at all. Before this, a project owning either
    name got no `NS-01` and no question at setup — the collision was silent.

    Both halves are pinned here, and the second is what stops the first from
    being a licence to warn on Perry's own files:

      a FOREIGN file at the claimed path  → `NS-01`, `warn`, exit code unchanged
      Perry's OWN store or event log      → nothing, on every Perry project

    The second is not hypothetical. A `.jsonl` carries no heading, no
    `files[]` name and no `Owner**:` line, so every rule in
    `looks_like_perry_state` reads it as foreign; without
    `looks_like_perry_record` these two claims would emit two warnings on
    every adopted project there is, including this repository.
    """

    # Valid JSONL, and nothing Perry's record vocabulary can account for: the
    # store's fields are `perry_store.STORED` and an event carries `ts` and
    # `event`. Spelled out for the same reason `FOREIGN` is — a fixture that
    # accidentally looked Perry-shaped would make every assertion below pass
    # by reporting nothing.
    FOREIGN_JSONL = ('{"account": "acme", "region": "eu-west", "rows": 3}\n'
                     '{"account": "globex", "region": "us-east", "rows": 7}\n')

    # What Perry itself writes, in the shape its own writers produce.
    PERRY_STORE = ('{"id": "TASK-001", "title": "A task", "status": "done", '
                   '"owner": "", "priority": "P1", "track": "main"}\n')
    PERRY_EVENTS = ('{"ts": "2026-08-20T09:00:00", "event": "done", '
                    '"id": "TASK-001", "actor": "agent"}\n')

    def colliding_store(self) -> pathlib.Path:
        """The project's own `tasks.jsonl`, at the state root."""
        d = self.adopted_clean()
        (d / "tasks.jsonl").write_text(self.FOREIGN_JSONL)
        return d

    def colliding_events(self) -> pathlib.Path:
        """The project's own `.perry/events.jsonl`, at the project root."""
        d = self.adopted_clean()
        (d / ".perry" / "events.jsonl").write_text(self.FOREIGN_JSONL)
        return d

    # ── the store path ────────────────────────────────────────────────────

    def test_a_foreign_store_file_is_ns01_at_warn(self):
        _, payload = self.lint(self.colliding_store())
        rows = self.ns(payload)
        self.assertEqual([r["file"] for r in rows], ["tasks.jsonl"],
                         payload["findings"])
        self.assertEqual(rows[0]["severity"], "warn")

    def test_the_store_path_is_the_evidence(self):
        _, payload = self.lint(self.colliding_store())
        self.assertIn("tasks.jsonl", self.ns(payload)[0]["message"],
                      "the finding does not say which file collided")

    def test_the_store_collision_leaves_the_exit_code_alone(self):
        """Same commitment as every other `NS-01`: a user may live with it."""
        rc, payload = self.lint(self.colliding_store())
        self.assertEqual(rc, 0)
        self.assertEqual(payload["errors"], 0)

    def test_the_store_collision_is_what_explains_the_other_findings(self):
        """Why the gap mattered, in one fixture.

        A project's own `tasks.jsonl` at the state root is ALSO read as a
        broken store: `store-badly-typed` on the file and `store-drift` on
        every board row derived from it. Before this row those were the whole
        report — Perry calling the user's own file malformed, with nothing
        saying why, which is the exact outcome DESIGN-002 § P4 names. `NS-01`
        is the sentence that makes the rest legible."""
        _, payload = self.lint(self.colliding_store())
        rules = {f["rule"] for f in payload["findings"]}
        self.assertIn("store-badly-typed", rules)
        self.assertIn("NS-01", rules)

    # ── the event-log path ────────────────────────────────────────────────

    def test_a_foreign_event_log_is_ns01_at_warn(self):
        _, payload = self.lint(self.colliding_events())
        rows = self.ns(payload)
        self.assertEqual([r["file"] for r in rows], [".perry/events.jsonl"],
                         payload["findings"])
        self.assertEqual(rows[0]["severity"], "warn")

    def test_the_event_log_path_is_the_evidence(self):
        _, payload = self.lint(self.colliding_events())
        self.assertIn(".perry/events.jsonl", self.ns(payload)[0]["message"])

    def test_the_event_log_collision_leaves_the_exit_code_alone(self):
        self.assertEqual(self.lint(self.colliding_events())[0], 0)
        self.assertEqual(self.lint(self.colliding_events(), "--strict")[0], 0)

    # ── and Perry's own two files are not a collision ─────────────────────

    def test_perrys_own_store_and_event_log_are_not_reported(self):
        d = self.adopted_clean()
        (d / "tasks.jsonl").write_text(self.PERRY_STORE)
        (d / ".perry" / "events.jsonl").write_text(self.PERRY_EVENTS)
        _, payload = self.lint(d)
        self.assertEqual(
            self.ns(payload), [],
            "Perry's own store and event log were reported as a collision "
            "against Perry's own claim — every adopted project would carry "
            "two permanent warnings for files Perry wrote itself")

    def test_this_repository_gains_no_warning(self):
        """The measurement the row was written against, run on the repo.

        Perry keeps a real store and a real event log, so it is the sharpest
        available case of the false positive above. Only the three known
        `evidence/` `handoff/` `knowledge/` findings may appear — a fourth
        means the two new claims are firing on Perry's own files."""
        _, payload = self.lint(ROOT)
        paths = sorted(f["file"] for f in self.ns(payload))
        self.assertNotIn("perry/tasks.jsonl", paths)
        self.assertNotIn(".perry/events.jsonl", paths)

    def test_the_two_md_stores_are_not_reported_as_files_perry_did_not_write(self):
        """`looks_like_perry_record` knew the task and risk shapes only.

        `okr.jsonl` and `.perry/config.jsonl` are the other two stores Perry
        claims, and their records key on `kind` — a `setting` record carries
        `key` and a `track` record carries `track`, neither of which has an
        `id` — so the `id`-gated branch could not see them at all. Adding the
        `okr.jsonl` claim reproduced, one store over, exactly the false
        positive TASK-040 fixed for risks: a fourth NS-01 warning naming
        Perry's own file against Perry's own claim.

        One record per kind, built from `perry_md_store.STORED` rather than
        spelled out, so a field added there cannot leave this asserting a
        shape that no longer ships."""
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("perry_lint_rec", str(LINT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        lint = importlib.util.module_from_spec(spec)
        loader.exec_module(lint)

        md = lint._MD_STORE
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for kind, fields in md.STORED.items():
            rec = dict.fromkeys(fields, "")
            rec["kind"] = kind
            f = tmp / f"{kind}.jsonl"
            f.write_text(json.dumps(rec, ensure_ascii=False) + "\n",
                         encoding="utf-8")
            self.assertTrue(lint.looks_like_perry_record(f),
                            f"a stored `{kind}` record reads as foreign")

        # The other direction, or the check above is a rule that excuses
        # anything carrying a `kind`.
        alien = tmp / "alien.jsonl"
        alien.write_text(json.dumps({"kind": "kr", "wat": 1}) + "\n",
                         encoding="utf-8")
        self.assertFalse(lint.looks_like_perry_record(alien))

    def test_the_recognition_is_by_record_not_by_name(self):
        """`looks_like_perry_record` must not excuse a file for being called
        `tasks.jsonl`. Matching on the name would make the claim self-defeating:
        every file at the claimed path would be Perry's by definition, and the
        collision could never be reported."""
        live, _ = self.drive("live", "--root", str(self.colliding_store()))
        self.assertIn("[NS-01]", live)

    # ── and `--claims` lists them, under the right roots ──────────────────

    def test_claims_lists_both_paths(self):
        """The payload, not the text render: `render_claims` prints only the
        rows that are taken, and on a clean folder both of these are free —
        which is the answer setup needs and the reason the JSON is the
        contract."""
        proc = subprocess.run(
            [sys.executable, str(LINT), "--root", str(self.adopted_clean()),
             "--claims", "--json"], capture_output=True, text=True, cwd=ROOT)
        listed = {r["path"] for r in json.loads(proc.stdout)["paths"]}
        self.assertIn("tasks.jsonl", listed)
        self.assertIn(".perry/events.jsonl", listed)

    def test_each_path_resolves_under_its_declared_root(self):
        """The store is state-root relative and the event log is project-root
        relative. On this repository those are different directories, which is
        what makes the distinction checkable rather than cosmetic."""
        out, _ = self.drive("rows", str(ROOT))
        rows = {r["path"]: r for r in json.loads(out)["rows"]}
        self.assertEqual(rows["tasks.jsonl"]["rel"], "perry/tasks.jsonl")
        self.assertEqual(rows[".perry/events.jsonl"]["rel"],
                         ".perry/events.jsonl")


if __name__ == "__main__":
    unittest.main()
