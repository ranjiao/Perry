#!/usr/bin/env python3
"""TASK-234's mutation harness — is every new guard load-bearing?

Uniquely named so it cannot collide with another round's harness in the same
tree. Run from the repository root:

    python3 tests/mutate_task_234.py

Each mutation:

  - anchors on the **exact text** of one line, resolves that line at run time
    and asserts the anchor is UNIQUE in the file — a mutation applied to the
    wrong line, or to two lines, measures nothing;
  - clears every `__pycache__` and sleeps to a whole-second boundary before and
    after, because `bin/lib/__pycache__` is real on this project and a stale
    `.pyc` from the same second is how a mutation "passes";
  - restores the file by `md5` and asserts the digest matches what was read;
  - asserts GREEN first. A mutation that reddens an already-red suite has
    measured nothing.

The harness REFUSES a dirty tree: it rewrites shipped files in place, and a
crash mid-run must not be indistinguishable from someone's uncommitted work.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: (id, file, exact anchor text, replacement, the test that must go red)
MUTATIONS = [
    # ── viewer/parsers.py § _declaration_from ─────────────────────────────
    ("M1", "viewer/parsers.py",
     '    if not isinstance(version, int) or isinstance(version, bool):',
     '    if False:',
     "tests.test_conformance.TestTheRecordIsAStore"
     ".test_a_line_that_is_not_a_declaration_is_reported_not_skipped"),

    ("M2", "viewer/parsers.py",
     '    if rec.get("kind") != CONFORMANCE_KIND:',
     '    if False:',
     "tests.test_conformance.TestTheRecordIsAStore"
     ".test_a_line_that_is_not_a_declaration_is_reported_not_skipped"),

    ("M3", "viewer/parsers.py",
     '    if not isinstance(rec, dict):',
     '    if False:',
     "tests.test_conformance.TestTheRecordIsAStore"
     ".test_a_line_that_is_not_a_declaration_is_reported_not_skipped"),

    # ── viewer/parsers.py § read_conformance ──────────────────────────────
    ("M4", "viewer/parsers.py",
     '        if decl is None or decl.path in rec.declarations:',
     '        if decl is None:',
     "tests.test_conformance.TestTheRecordIsAStore"
     ".test_two_lines_for_one_path_are_unreadable_rather_than_last_one_wins"),

    ("M5", "viewer/parsers.py",
     '            rec.unreadable.append((i, line.strip()))\n            continue\n'
     '        rec.declarations[decl.path] = decl',
     '            continue\n'
     '        rec.declarations[decl.path] = decl',
     "tests.test_conformance.TestTheRecordIsAStore"
     ".test_a_malformed_line_does_not_void_its_neighbours"),

    ("M6", "viewer/parsers.py",
     '        if not line.strip():',
     '        if False:',
     "tests.test_conformance.TestTheRecordIsAStore"
     ".test_a_blank_line_is_layout_and_not_a_finding"),

    # **The fallback that was deliberately NOT written.** If a later hand
    # reintroduces "read the markdown when there is no store", the project has
    # two live registers again and TASK-248's hole is back.
    ("M7", "viewer/parsers.py",
     '        if legacy.exists():\n            rec.legacy = legacy\n        return rec',
     '        if legacy.exists():\n'
     '            return read_legacy_conformance(project_root)\n        return rec',
     "tests.test_conformance.TestTheMarkdownRecordIsConvertedOnce"
     ".test_the_markdown_alone_declares_nothing"),

    ("M8", "viewer/parsers.py",
     '    if legacy.exists():\n        rec.stray_legacy = legacy',
     '    if False:\n        rec.stray_legacy = legacy',
     "tests.test_conformance.TestTheMarkdownRecordIsConvertedOnce"
     ".test_a_markdown_beside_a_store_is_reported_and_not_read"),

    # ── bin/perry-conform § migrate_record ────────────────────────────────
    ("M9", "bin/perry-conform",
     '    if canonical != text:',
     '    if False:',
     "tests.test_conformance.TestADecoratedRowIsNotADeclaration"
     ".test_a_canonical_row_inside_an_html_block_is_not_carried_across"),

    ("M10", "bin/perry-conform",
     '    if record.unreadable:',
     '    if False:',
     "tests.test_conformance.TestTheMarkdownRecordIsConvertedOnce"
     ".test_an_unreadable_row_is_refused_rather_than_deleted_at_the_door"),

    ("M11", "bin/perry-conform",
     '    if store.exists() or not legacy.exists():',
     '    if not legacy.exists():',
     "tests.test_conformance.TestTheMarkdownRecordIsConvertedOnce"
     ".test_a_stale_markdown_never_overwrites_a_store"),

    ("M12", "bin/perry-conform",
     '    legacy.unlink()',
     '    pass',
     "tests.test_conformance.TestTheMarkdownRecordIsConvertedOnce"
     ".test_the_conversion_carries_every_date_and_route_unchanged"),

    # ── bin/perry-conform § declare ───────────────────────────────────────
    ("M13", "bin/perry-conform",
     '    converted = (migrate_record(project_root, root_arg=root_arg)\n'
     '                 if not dry_run else None)',
     '    converted = None',
     "tests.test_conformance.TestTheMarkdownRecordIsConvertedOnce"
     ".test_declaring_converts_first_and_says_so"),

    ("M14", "bin/perry-conform",
     '            writer=writer, recorded_at=stamped_at, run=run)',
     '            writer="", recorded_at="", run="")',
     "tests.test_conformance.TestTheRecordIsAStore"
     ".test_a_declaration_records_who_wrote_it_and_when"),

    # ── bin/perry-conform § message_for ───────────────────────────────────
    ("M15", "bin/perry-conform",
     '    if v.legacy_record:',
     '    if False:',
     "tests.test_conformance.TestTheMarkdownRecordIsConvertedOnce"
     ".test_the_refusal_names_migrate_and_not_declare"),

    # ── bin/perry-migrate — the run id on a migrated declaration ──────────
    ("M16", "bin/perry-migrate",
     '                            writer="perry-migrate apply", run=run_id)',
     '                            writer="perry-migrate apply", run="")',
     "tests.test_migrate.TestTheUserDeclares"
     ".test_the_declaration_goes_through_perry_conform_and_is_the_only_record"),

    ("M17", "bin/perry-migrate",
     '    files[P.CONFORMANCE_LEGACY_FILE] = (file_image(legacy.read_bytes())\n'
     '                                        if legacy.exists() else absent_image())',
     '    pass',
     "tests.test_migrate.TestRecoverable"
     ".test_restore_also_withdraws_the_declarations_the_run_wrote"),

    ("M18", "bin/perry-migrate",
     '        preflight_file_object(\n'
     '            plan.project_root,\n'
     '            plan.project_root / P.CONFORMANCE_LEGACY_FILE,\n'
     '            P.CONFORMANCE_LEGACY_FILE,\n'
     '        )',
     '        pass',
     "tests.test_migrate.TestFileImageFidelity"
     ".test_a_symlinked_markdown_record_is_refused_before_state_writes"),

    ("M21", "bin/perry-migrate",
     '        except (OSError, Refused, C.Refused, ValueError) as exc:',
     '        except (OSError, Refused, ValueError) as exc:',
     "tests.test_migrate.TestTheUserDeclares"
     ".test_an_unconvertible_markdown_record_refuses_and_names_the_way_back"),

    # ── the V4 FAIL: the refusal has to name the line ─────────────────────

    ("M22", "bin/perry-conform",
     '            + record_diff(text, canonical)',
     '            + "    perry-conform status"',
     "tests.test_conformance.TestTheRefusalNamesTheLine"
     ".test_the_refusal_carries_a_diff_and_not_a_command_that_computes_none"),

    ("M23", "bin/perry-conform",
     '    dropped = max(0, len(lines) - DIFF_CAP)',
     '    dropped = len(lines) - DIFF_CAP',
     "tests.test_conformance.TestTheDefensiveBranchesAreLoadBearing"
     ".test_a_short_diff_does_not_claim_it_dropped_a_negative_number"),

    ("M24", "bin/perry-conform",
     '        shown.append(f"    … and {dropped} more diff line(s); the whole file "',
     '        shown.append(f"    … and 0 more diff line(s); the whole file "',
     "tests.test_conformance.TestTheRefusalNamesTheLine"
     ".test_a_wholly_rewritten_record_is_capped_and_says_how_much_it_dropped"),

    # ── the six defensive branches that survived their own deletion ───────

    ("M25", "viewer/parsers.py",
     '    if not isinstance(path, str) or not path.strip():\n        return None',
     '    if False:\n        return None',
     "tests.test_conformance.TestTheDefensiveBranchesAreLoadBearing"
     ".test_a_non_string_path_is_refused_rather_than_used_as_a_key"),

    ("M26", "viewer/parsers.py",
     '    if not isinstance(declared, str) or not isinstance(route, str):\n        return None',
     '    if False:\n        return None',
     "tests.test_conformance.TestTheDefensiveBranchesAreLoadBearing"
     ".test_a_non_string_declared_or_route_is_refused"),

    ("M27", "viewer/parsers.py",
     '        route=route or "declare", line=number,',
     '        route=route, line=number,',
     "tests.test_conformance.TestTheDefensiveBranchesAreLoadBearing"
     ".test_an_empty_route_reads_as_declare_rather_than_as_blank"),

    ("M28", "viewer/parsers.py",
     '    text = lambda key: (rec.get(key) if isinstance(rec.get(key), str) else "")',
     '    text = lambda key: rec.get(key) or ""',
     "tests.test_conformance.TestTheDefensiveBranchesAreLoadBearing"
     ".test_non_string_provenance_reads_as_empty_rather_than_as_itself"),

    ("M29", "viewer/parsers.py",
     '    try:\n        text = path.read_text(encoding="utf-8", errors="replace")\n    except OSError:\n        return rec',
     '    text = path.read_text(encoding="utf-8", errors="replace")',
     "tests.test_conformance.TestTheDefensiveBranchesAreLoadBearing"
     ".test_a_record_that_exists_but_cannot_be_read_is_not_a_crash"),

    # ── round 4: a refusal names the command with the ROOT THE CALLER USED
    #
    # `message_for` propagates it through `_root_flag()`; `migrate_record`'s
    # two refusals did not, and the command they handed back exits 0 with
    # "nothing to convert" about a different project. Each of these mutates the
    # SOURCE so one requirement has to fire on its own.

    ("M30", "bin/perry-conform",
     '              f"    perry-conform migrate{r}\\n"\n'
     '              f"**Nothing was written.**")',
     '              f"    perry-conform migrate\\n"\n'
     '              f"**Nothing was written.**")',
     "tests.test_conformance.TestTheCommandTheRefusalNamesIsTheOneTheReaderCanRun"
     ".test_the_named_command_converts_the_readers_project_from_elsewhere"),

    ("M31", "bin/perry-conform",
     '              f"    perry-conform migrate{r}\\n"\n'
     '              f"A row that is documentation',
     '              f"    perry-conform migrate\\n"\n'
     '              f"A row that is documentation',
     "tests.test_conformance.TestTheCommandTheRefusalNamesIsTheOneTheReaderCanRun"
     ".test_the_unreadable_rows_refusal_names_it_too"),

    # The runtime value, not the template — the source guard cannot see this
    # one, and the 16 helper invocations are what catch it.
    ("M32", "bin/perry-conform",
     "    r = _root_flag(root_arg)\n    root = Path(project_root)",
     "    r = _root_flag(None)\n    root = Path(project_root)",
     "tests.test_conformance.TestADecoratedRowIsNotADeclaration"
     ".test_a_backticked_path_cell_is_not_a_declaration"),

    ("M33", "bin/perry-conform",
     "    converted = (migrate_record(project_root, root_arg=root_arg)",
     "    converted = (migrate_record(project_root, root_arg=None)",
     "tests.test_conformance.TestTheCommandTheRefusalNamesIsTheOneTheReaderCanRun"
     ".test_the_declare_route_into_the_conversion_carries_the_root_too"),

    # **A root that is not the caller's.** Every assertion that reads the
    # message is still satisfiable by eye; only RUNNING the command notices.
    ("M34", "bin/perry-conform",
     '              f"    perry-conform migrate{r}\\n"\n'
     '              f"**Nothing was written.**")',
     '              f"    perry-conform migrate --root /nowhere-at-all\\n"\n'
     '              f"**Nothing was written.**")',
     "tests.test_conformance.TestTheCommandTheRefusalNamesIsTheOneTheReaderCanRun"
     ".test_the_named_command_converts_the_readers_project_from_elsewhere"),

    # **The one member of the class no test held**, found by this mutation
    # coming back GREEN in round 4 before the assertion below was written.
    ("M35", "bin/perry-migrate",
     "                            root_arg=root_arg,",
     "                            root_arg=None,",
     "tests.test_migrate.TestTheUserDeclares"
     ".test_an_unconvertible_markdown_record_refuses_and_names_the_way_back"),

    ("M36", "bin/perry-migrate",
     '    cmd = f"perry-migrate restore {point.stem}{_root_flag(root_arg)}"',
     '    cmd = f"perry-migrate restore {point.stem}"',
     "tests.test_migrate.TestRecoverable"
     ".test_every_way_back_this_tool_names_carries_the_root"),

    ("M37", "bin/perry-migrate",
     '            print(f"\\n   perry-migrate restore <run-id>'
     '{_root_flag(root_arg)}\\n")',
     '            print(f"\\n   perry-migrate restore <run-id>\\n")',
     "tests.test_migrate.TestRecoverable"
     ".test_every_way_back_this_tool_names_carries_the_root"),

    # ── round 4: the CRLF guard reaches `bin/README.md` and the reworded
    # overclaim, both of which the V4 round-3 reviewer measured it missing.

    ("M38", "bin/README.md",
     "It refuses rather than convert a file that is not line-for-line\n"
     "what `perry-conform declare` would have written",
     "It refuses rather than convert a file that is not byte-for-byte\n"
     "what `perry-conform declare` would have written",
     "tests.test_conformance.TestTheRefusalNamesTheLine"
     ".test_a_crlf_record_converts_and_the_wording_does_not_say_byte"),

    ("M39", "bin/README.md",
     "(Line-for-line, not byte-for-byte: the comparison applies Python's\n"
     "universal-newline translation, so a record saved with CRLF converts.)",
     "(A record saved with CRLF converts.)",
     "tests.test_conformance.TestTheRefusalNamesTheLine"
     ".test_a_crlf_record_converts_and_the_wording_does_not_say_byte"),

    # ── tests/test_one_header_rule.py — the vacuity guard ─────────────────
    ("M19", "viewer/parsers.py",
     '        if header_index([rel]).column("file", "path") == 0 or not rel:',
     '        if False:',
     "tests.test_one_header_rule.TestTheFifthCopy"
     ".test_a_bolded_header_is_not_reported_as_a_broken_row"),

    ("M20", "viewer/parsers.py",
     '        if canonical != line:',
     '        if False:',
     "tests.test_conformance.TestADecoratedRowIsNotADeclaration"
     ".test_a_backticked_path_cell_is_not_a_declaration"),
]


def clear_pycache() -> None:
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def whole_second() -> None:
    """Sleep to the next whole second.

    `.pyc` staleness is decided on a one-second mtime granularity on this
    platform (`knowledge/toolchain/pycache-staleness.md`), so a rewrite inside
    the same second as the last import can be read from a cache that predates
    it — which shows up as a mutation that changes nothing.
    """
    time.sleep(1.0 - (time.time() % 1.0) + 0.05)


def run(target: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-m", "unittest", target],
                       cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return r.returncode, (r.stderr or "") + (r.stdout or "")


def main() -> int:
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        print("REFUSED: the tree is dirty. This harness rewrites shipped files "
              "in place, and a crash mid-run must not be mistaken for "
              "somebody's uncommitted work.\n" + dirty)
        return 2

    bad = 0
    for mid, rel, anchor, replacement, test in MUTATIONS:
        path = ROOT / rel
        before = path.read_text()
        digest = hashlib.md5(before.encode()).hexdigest()
        if before.count(anchor) != 1:
            print(f"  ✗ {mid}: anchor appears {before.count(anchor)} times in "
                  f"{rel} — it must be unique or the mutation lands somewhere "
                  f"else")
            bad += 1
            continue
        line_no = before[:before.index(anchor)].count("\n") + 1

        clear_pycache(); whole_second()
        rc, _ = run(test)
        if rc != 0:
            print(f"  ✗ {mid}: {test} is ALREADY RED — a mutation that reddens "
                  f"a red test measures nothing")
            bad += 1
            continue

        path.write_text(before.replace(anchor, replacement))
        clear_pycache(); whole_second()
        try:
            rc, out = run(test)
        finally:
            path.write_text(before)
            got = hashlib.md5(path.read_text().encode()).hexdigest()
            assert got == digest, f"{mid}: {rel} was not restored"
            clear_pycache(); whole_second()

        if rc == 0:
            print(f"  ✗ {mid}  {rel}:{line_no}  GREEN under mutation — "
                  f"{test} does not hold this guard")
            bad += 1
        else:
            print(f"  ✓ {mid}  {rel}:{line_no}  red: {test.rsplit('.', 1)[-1]}")

    print(f"\n{len(MUTATIONS) - bad}/{len(MUTATIONS)} mutations reddened their "
          f"named test.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
